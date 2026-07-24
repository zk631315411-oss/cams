# -*- coding: utf-8 -*-
"""机械合规检查：扫描 question JSON，输出需人工复核的题目清单。

独立运行：
    python review_check.py --output-dir ../output

配合质量复核（仅检查 quality_review 通过的题）：
    python review_check.py --output-dir ../output --quality-review-dir ../output/quality_reviews
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
_SRC = HERE.parent / "解析撰写"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import generate_evidence_explanations as master

REVIEW_SCHEMA_VERSION = "review_check_v2_0"


def _append_unique(values: list[str], message: str) -> None:
    if message and message not in values:
        values.append(message)


def _reference_conflicts(answer: list[str], reference: dict[str, Any]) -> list[str]:
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


def _collect_all_cited_unit_ids(result: dict[str, Any]) -> set[str]:
    exp = result.get("generated_explanation", {}) or {}
    uids: set[str] = set()
    core = exp.get("core_analysis", {}) or {}
    for uid in (core.get("cited_unit_ids", []) or []):
        uids.add(str(uid))
    for row in (exp.get("option_explanations", []) or []):
        for uid in (row.get("cited_unit_ids", []) or []):
            uids.add(str(uid))
        for sc in (row.get("source_claims", []) or []):
            uid = str(sc.get("unit_id", "") or "")
            if uid:
                uids.add(uid)
    easy = exp.get("easy_mistake", {}) or {}
    for uid in (easy.get("cited_unit_ids", []) or []):
        uids.add(str(uid))
    return uids


def _check_page_validity(result: dict[str, Any]) -> list[str]:
    """检测 AI 解析中引用的页码是否真实存在于 candidate_pool。"""
    flags: list[str] = []
    exp = result.get("generated_explanation", {}) or {}

    texts: list[str] = []
    for field in ["exam_point", "core_analysis", "easy_mistake"]:
        t = (exp.get(field, {}) or {}).get("text", "")
        if t:
            texts.append(str(t))
    for row in (exp.get("option_explanations", []) or []):
        texts.append(str(row.get("analysis", "") or ""))

    unit_map = master.candidate_by_unit(result)
    valid_pages: set[int] = set()
    for uid, unit in unit_map.items():
        for key in ("pdf_page", "printed_page"):
            v = unit.get(key)
            if isinstance(v, (int, float)) and v > 0:
                valid_pages.add(int(v))
            elif isinstance(v, str) and v.strip().isdigit():
                valid_pages.add(int(v.strip()))

    for se in (exp.get("source_evidence", []) or []):
        for key in ("pdf_page", "printed_page"):
            v = se.get(key)
            if isinstance(v, (int, float)) and v > 0:
                valid_pages.add(int(v))
            elif isinstance(v, str) and v.strip().isdigit():
                valid_pages.add(int(v.strip()))

    if not valid_pages:
        return flags

    page_refs: set[int] = set()
    for text in texts:
        for m in __import__("re").finditer(r"(?:P|p|书内第|PDF第)\s*(\d+)", text):
            page_refs.add(int(m.group(1)))

    hallucinated = page_refs - valid_pages
    for p in sorted(hallucinated):
        flags.append(f"页码幻觉：P{p}不在candidate_pool中")

    return flags


def validate_for_software(result: dict[str, Any]) -> tuple[list[str], list[str]]:
    """软件导出门禁校验，返回 (阻断原因, 风险标记)。"""
    blockers: list[str] = []
    explanation = result.get("generated_explanation", {}) or {}
    readiness = explanation.get("software_readiness", {}) or {}

    if explanation.get("schema_version") != master.SCHEMA_VERSION:
        _append_unique(blockers, "解析母版不是V3.1 schema")

    _internal_markers = ["需教研复核", "现有教材证据不足，需教研复核"]
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


def check_single_question(result: dict[str, Any]) -> list[str]:
    """对单题执行全部机械检查，返回原因列表。"""
    exp = result.get("generated_explanation", {}) or {}
    reasons: list[str] = []

    blockers, risk_flags = validate_for_software(result)
    reasons.extend(blockers)

    for opt_row in (exp.get("option_explanations", []) or []):
        if opt_row.get("basis_type") == "insufficient":
            reasons.append(f"选项{opt_row.get('option', '?')}证据不足")

    _NOISE_FLAGS = {"ocr_fixed", "manual_reviewed", "missing_options"}
    for flag in risk_flags:
        if isinstance(flag, str) and flag not in _NOISE_FLAGS:
            reasons.append(flag)

    reasons.extend(_check_page_validity(result))

    seen: set[str] = set()
    unique: list[str] = []
    for r in reasons:
        key = r.strip().rstrip("。；，,;.")
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def _load_quality_pass_list(quality_review_dir: Path) -> set[str] | None:
    """从质量复核结果中提取 verdict 为 pass 或 minor_issue 的题目 ID。"""
    if not quality_review_dir.exists():
        print(f"  警告：质量复核目录不存在：{quality_review_dir}")
        return None
    passed: set[str] = set()
    for path in sorted(quality_review_dir.glob("v7_q_*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            verdict = data.get("verdict", "")
            if verdict in ("pass", "minor_issue"):
                passed.add(data.get("question_id", ""))
        except Exception:
            continue
    return passed if passed else None


def run_review(
    output_dir: Path,
    question_ids: list[str] | None = None,
    quality_review_dir: Path | None = None,
) -> dict[str, Any]:
    question_dir = output_dir / "questions"
    if not question_dir.exists():
        raise RuntimeError(f"questions目录不存在: {question_dir}")

    allowed_ids: set[str] | None = None
    if quality_review_dir:
        allowed_ids = _load_quality_pass_list(quality_review_dir)
        if allowed_ids is None:
            return {"total": 0, "needs_review": 0}
    if question_ids:
        id_set = set(question_ids)
        allowed_ids = id_set if allowed_ids is None else (allowed_ids & id_set)
    filter_msg = f"（质量复核通过筛选：{len(allowed_ids)}题）" if allowed_ids else "（全量）"

    needs_review: list[dict[str, Any]] = []
    total = 0

    for path in sorted(question_dir.glob("q_*.json")):
        result = master.load_question_result(path)
        qid = str(result.get("question_id", ""))
        if allowed_ids is not None and qid not in allowed_ids:
            continue
        total += 1
        reasons = check_single_question(result)
        if reasons:
            needs_review.append({"qid": qid, "reasons": reasons})

    review_dir = output_dir / "software_export"
    review_dir.mkdir(parents=True, exist_ok=True)

    review_lines = [
        "# 机械合规检查报告\n\n",
        f"检查范围：{filter_msg}\n",
        f"检查题数：{total} | 需复核：{len(needs_review)}\n\n",
    ]
    for i, item in enumerate(needs_review, 1):
        review_lines.append(f"## {i}. {item['qid']}\n\n")
        for reason in item["reasons"]:
            review_lines.append(f"- {reason}\n")
        review_lines.append("\n")
    review_path = review_dir / "review_check_report.md"
    review_path.write_text("".join(review_lines), encoding="utf-8")

    print(f"\n检查范围：{filter_msg}")
    print(f"检查题数：{total} | 需复核：{len(needs_review)}")
    if needs_review:
        print("-" * 40)
        for i, item in enumerate(needs_review, 1):
            reasons_text = "；".join(item["reasons"])
            print(f"{i}. {item['qid']} — {reasons_text}")
    print("-" * 40)

    summary = {
        "schema_version": REVIEW_SCHEMA_VERSION, "total": total,
        "needs_review": len(needs_review),
        "review_markdown": str(review_path),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    summary_path = review_dir / "review_check_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="机械合规检查：扫描 question JSON，生成复核清单。")
    parser.add_argument("--output-dir", required=True, help="phase4_evidence/output 目录")
    parser.add_argument("--quality-review-dir", default="", help="质量复核结果目录。指定后只检查通过质量复核的题")
    parser.add_argument("--question-ids", default="", help="限定检查的题目ID（逗号分隔）")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    qids = [q.strip() for q in args.question_ids.split(",") if q.strip()] if args.question_ids else None
    qr_dir = Path(args.quality_review_dir) if args.quality_review_dir else None

    summary = run_review(output_dir, question_ids=qids, quality_review_dir=qr_dir)
    print(f"\n[output] review={summary['review_markdown']}")
    print(f"[output] summary={output_dir / 'software_export' / 'review_check_summary.json'}")


if __name__ == "__main__":
    main()
