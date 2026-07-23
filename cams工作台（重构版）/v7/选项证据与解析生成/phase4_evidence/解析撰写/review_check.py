# -*- coding: utf-8 -*-
"""复核检测：扫描 question JSON，输出需要人工复核的题目清单。不做导出。"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import generate_evidence_explanations as master


HERE = Path(__file__).resolve().parent
REVIEW_SCHEMA_VERSION = "review_check_v1_0"


def _append_unique(values: list[str], message: str) -> None:
    if message and message not in values:
        values.append(message)


def _reference_conflicts(
    answer: list[str], reference: dict[str, Any]
) -> list[str]:
    answer_set = set(answer)
    conflicts: list[str] = []
    for field, label in (
        ("final_answer", "题库最终参考答案"),
        ("cn_answer", "中文参考答案"),
        ("en_answer", "英文参考答案"),
    ):
        values = [str(x).strip().upper() for x in reference.get(field, []) or []]
        if values and set(values) != answer_set:
            conflicts.append(f"AI答案与{label}冲突")
    return conflicts


def validate_for_software(result: dict[str, Any]) -> tuple[list[str], list[str]]:
    """软件导出门禁校验，返回 (阻断原因, 风险标记)。"""
    blockers: list[str] = []
    explanation = result.get("generated_explanation", {}) or {}
    readiness = explanation.get("software_readiness", {}) or {}

    if explanation.get("schema_version") != master.SCHEMA_VERSION:
        _append_unique(blockers, "解析母版不是V3.1 schema")

    _internal_markers = [
        "需教研复核",
        "现有教材证据不足，需教研复核",
    ]
    for field_name, field_value in [
        ("考点", (explanation.get("exam_point", {}) or {}).get("text", "")),
        ("核心解析", (explanation.get("core_analysis", {}) or {}).get("text", "")),
    ]:
        for marker in _internal_markers:
            if marker in str(field_value or ""):
                _append_unique(blockers, f"{field_name}包含内部备注'{marker}'")
                break
    for row in explanation.get("option_explanations", []) or []:
        label = str(row.get("option", ""))
        analysis = str(row.get("analysis", "") or "")
        for marker in _internal_markers:
            if marker in analysis:
                _append_unique(blockers, f"选项{label}分析包含内部备注'{marker}'")
                break

    predicted = [str(x).strip().upper() for x in result.get("predicted_answer", []) or []]
    answer = [str(x).strip().upper() for x in explanation.get("answer", []) or []]
    if not answer:
        _append_unique(blockers, "AI答案为空")
    if answer != predicted:
        _append_unique(blockers, "软件版答案与盲判答案不一致")

    option_rows = explanation.get("option_explanations", []) or []
    for row in option_rows:
        label = str(row.get("option", "")).strip().upper()
        expected = "correct" if label in answer else "incorrect"
        if row.get("judgement") != expected:
            _append_unique(blockers, f"选项{label}正误未按AI答案锁定")
        if row.get("basis_type") not in {
            "textbook_direct", "textbook_definition_application",
            "stem_contrast", "stem_entailment", "insufficient",
        }:
            _append_unique(blockers, f"选项{label}basis_type非法")
        if (row.get("basis_type") in {"textbook_direct", "textbook_definition_application"}
                and not row.get("source_claims")):
            _append_unique(blockers, f"选项{label}教材判断缺少source_claims")

    core = explanation.get("core_analysis", {}) or {}
    source_quote = core.get("source_quote", {}) or {}
    uid = str(source_quote.get("unit_id", "") or "")
    excerpt = str(source_quote.get("exact_excerpt", "") or "")
    if uid or excerpt:
        cited_core = core.get("cited_unit_ids", []) or []
        if not cited_core:
            _append_unique(blockers, "纯题干推导的核心解析不应有教材短引")
        elif uid not in cited_core:
            _append_unique(blockers, "教材英文短引unit未被核心解析引用")
        else:
            unit_map = master.candidate_by_unit(result)
            unit = unit_map.get(uid, {})
            original = str(unit.get("en_quote") or unit.get("knowledge_en", "") or "")
            if excerpt not in original:
                _append_unique(blockers, "教材英文短引不是对应原文的连续子串")
            if not master.SOURCE_QUOTE_MIN_LENGTH <= len(excerpt) <= master.SOURCE_QUOTE_MAX_LENGTH:
                _append_unique(blockers, "教材英文短引长度不合规")

    reference = explanation.get("reference_appendix", {}) or {}
    for conflict in _reference_conflicts(answer, reference):
        _append_unique(blockers, conflict)

    risk_flags = [
        str(flag)
        for flag in readiness.get("risk_flags", []) or reference.get("risk_flags", []) or []
        if str(flag).strip()
    ]
    return blockers, list(dict.fromkeys(risk_flags))


def run_review(output_dir: Path) -> dict[str, Any]:
    """扫描所有 question JSON，输出复核清单。"""
    question_dir = output_dir / "questions"
    if not question_dir.exists():
        raise RuntimeError(f"questions目录不存在: {question_dir}")

    _NOISE_FLAGS = {"ocr_fixed", "manual_reviewed", "missing_options"}
    needs_review: list[dict[str, Any]] = []
    total = 0

    for path in sorted(question_dir.glob("q_*.json")):
        result = master.load_question_result(path)
        qid = str(result.get("question_id", ""))
        total += 1

        exp = (result.get("generated_explanation", {}) or {})
        reasons: list[str] = []

        # 1. 门禁阻断
        blockers, risk_flags = validate_for_software(result)
        reasons.extend(blockers)

        # 2. 证据不足选项
        for opt_row in (exp.get("option_explanations", []) or []):
            if opt_row.get("basis_type") == "insufficient":
                reasons.append(f"选项{opt_row.get('option', '?')}证据不足")

        # 3. 非噪声风险标记
        for flag in risk_flags:
            if isinstance(flag, str) and flag not in _NOISE_FLAGS:
                reasons.append(flag)

        # 去重
        seen: set[str] = set()
        unique: list[str] = []
        for r in reasons:
            key = r.strip().rstrip("。；，,;.")
            if key not in seen:
                seen.add(key)
                unique.append(r)

        if unique:
            needs_review.append({"qid": qid, "reasons": unique})

    # 输出
    review_dir = output_dir / "software_export"
    review_dir.mkdir(parents=True, exist_ok=True)

    review_lines = [
        "# 待复核清单\n\n",
        f"总题数：{total} | 需复核：{len(needs_review)}\n\n",
    ]
    for i, item in enumerate(needs_review, 1):
        review_lines.append(f"## {i}. {item['qid']}\n\n")
        for reason in item["reasons"]:
            review_lines.append(f"- {reason}\n")
        review_lines.append("\n")
    review_path = review_dir / "review_required.md"
    review_path.write_text("".join(review_lines), encoding="utf-8")

    # 终端汇总
    print(f"\n总题数：{total} | 需复核：{len(needs_review)}")
    if needs_review:
        print("-" * 40)
        for i, item in enumerate(needs_review, 1):
            reasons_text = "；".join(item["reasons"])
            print(f"{i}. {item['qid']} — {reasons_text}")
    print("-" * 40)

    summary = {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "total": total,
        "needs_review": len(needs_review),
        "review_markdown": str(review_path),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    summary_path = review_dir / "review_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="扫描 question JSON，生成待复核清单。不做导出。"
    )
    parser.add_argument("--output-dir", required=True, help="phase4_evidence/output 目录")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    summary = run_review(output_dir)
    print(f"\n[output] review={summary['review_markdown']}")
    print(f"[output] summary={output_dir / 'software_export' / 'review_summary.json'}")


if __name__ == "__main__":
    main()
