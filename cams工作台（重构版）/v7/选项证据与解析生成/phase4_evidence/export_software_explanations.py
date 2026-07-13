# -*- coding: utf-8 -*-
"""将校验通过的 V3.1 解析母版导出为题库软件版 Markdown。"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import generate_evidence_explanations as master


EXPORT_SCHEMA_VERSION = "software_explanation_export_v1_1"
HERE = Path(__file__).resolve().parent  # phase4_evidence/
PHASE4 = HERE


def _append_unique(values: list[str], message: str) -> None:
    """去重追加消息。"""
    if message and message not in values:
        values.append(message)


def _reference_conflicts(
    answer: list[str], reference: dict[str, Any]
) -> list[str]:
    """检查 AI 答案与各参考答案之间的冲突。"""
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
    """软件导出门禁：只检查导出必需的完整性，不重复盲判/解析层的校验。

    返回 (阻断原因列表, 风险标记列表)。
    """
    blockers: list[str] = []
    explanation = result.get("generated_explanation", {}) or {}
    readiness = explanation.get("software_readiness", {}) or {}

    # schema 版本
    if explanation.get("schema_version") != master.SCHEMA_VERSION:
        _append_unique(blockers, "解析母版不是V3.1 schema")

    # 答案一致性
    options = result.get("options", {}) or {}
    predicted = [str(x).strip().upper() for x in result.get("predicted_answer", []) or []]
    answer = [str(x).strip().upper() for x in explanation.get("answer", []) or []]
    if not answer:
        _append_unique(blockers, "AI答案为空")
    if answer != predicted:
        _append_unique(blockers, "软件版答案与盲判答案不一致")

    # 选项完整性
    option_rows = explanation.get("option_explanations", []) or []
    if [row.get("option") for row in option_rows] != list(options):
        _append_unique(blockers, "选项解析缺失或顺序不一致")
    for row in option_rows:
        label = str(row.get("option", "")).strip().upper()
        expected = "correct" if label in answer else "incorrect"
        if row.get("judgement") != expected:
            _append_unique(blockers, f"选项{label}正误未按AI答案锁定")
        if row.get("basis_type") not in {
            "textbook_direct", "textbook_definition_application",
            "stem_contrast", "insufficient",
        }:
            _append_unique(blockers, f"选项{label}basis_type非法")
        if (row.get("basis_type") in {"textbook_direct", "textbook_definition_application"}
                and not row.get("source_claims")):
            _append_unique(blockers, f"选项{label}教材判断缺少source_claims")

    # 核心解析：教材英文短引（可选，有则校验）
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

    # 答案冲突
    reference = explanation.get("reference_appendix", {}) or {}
    for conflict in _reference_conflicts(answer, reference):
        _append_unique(blockers, conflict)

    risk_flags = [
        str(flag)
        for flag in readiness.get("risk_flags", []) or reference.get("risk_flags", []) or []
        if str(flag).strip()
    ]
    return blockers, list(dict.fromkeys(risk_flags))


def render_software_analysis(explanation: dict[str, Any]) -> str:
    """将解析母版渲染为题库软件使用的解析文本。"""
    answer = "、".join(explanation.get("answer", []) or [])
    exam_point = explanation.get("exam_point", {}) or {}
    core = explanation.get("core_analysis", {}) or {}
    easy = explanation.get("easy_mistake", {}) or {}
    quote = (core.get("source_quote", {}) or {}).get("exact_excerpt", "")

    lines = [f"答案：{answer}\n\n", "解析：\n\n"]
    lines.append("【考点】\n")
    lines.append(f"{exam_point.get('text', '')}\n\n")
    lines.append("【核心解析】\n")
    lines.append(f"{core.get('text', '')}\n")
    if quote:
        lines.append(f"教材原句：\"{quote}\"\n")
    lines.append("\n")
    lines.append("【选项分析】\n")
    for row in explanation.get("option_explanations", []) or []:
        judgement = "正确" if row.get("judgement") == "correct" else "错误"
        error_tag = f"（{row['error_type']}）" if row.get("error_type") else ""
        lines.append(f"{row.get('option', '')}项{judgement}{error_tag}：{row.get('analysis', '')}\n")
    lines.append("\n【易错提醒】\n")
    lines.append(f"{easy.get('text', '')}\n")
    return "".join(lines)


def render_question_preview(
    result: dict[str, Any], standard_question: dict[str, Any]
) -> str:
    """渲染单题的完整预览（题目 + 英文 + 解析）。"""
    qid = result.get("question_id", "")
    qtype = "单选题" if result.get("question_type") == "single" else "多选题"
    stem_en = str(standard_question.get("stem_en", "") or "").strip()
    options_en = standard_question.get("options_en", {}) or {}
    lines = [f"## {qid}\n\n", f"题型：{qtype}\n\n"]
    lines.append(f"题目：{result.get('stem', '')}\n\n")
    if stem_en:
        lines.append(f"English: {stem_en}\n\n")
    lines.append("选项：\n\n")
    for label, text in (result.get("options", {}) or {}).items():
        lines.append(f"- {label}. {text}\n")
        if options_en.get(label):
            lines.append(f"  English: {options_en[label]}\n")
    lines.append("\n" + render_software_analysis(result["generated_explanation"]))
    return "".join(lines)


def belongs_to_chapter(
    result: dict[str, Any],
    chapter_id: str,
    mapping_index: dict[str, dict[str, Any]] | None = None,
) -> bool:
    """判断题目是否属于指定章节。优先用 JSON 内嵌映射，其次用外部映射文件。"""
    embedded = result.get("chapter_mappings", []) or []
    if embedded:
        return any(m.get("chapter_id") == chapter_id for m in embedded)
    if mapping_index:
        qid = str(result.get("question_id", "")).strip()
        row = mapping_index.get(qid)
        if row:
            return any(
                m.get("chapter_id") == chapter_id
                for m in (row.get("chapter_mappings", []) or [])
            )
    return False


def export_chapter(
    output_dir: Path,
    chapter_id: str,
    standard_questions: dict[str, dict[str, Any]],
    output_subdir: str = "software_export",
    chapter_map: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """按章节导出可入库的软件版解析预览与待复核清单。

    返回包含选中数、导出数、阻断数的汇总字典。
    """
    question_dir = output_dir / "questions"
    if not question_dir.exists():
        raise RuntimeError(f"questions目录不存在: {question_dir}")

    selected: list[dict[str, Any]] = []
    for path in sorted(question_dir.glob("q_*.json")):
        result = master.load_question_result(path)
        if belongs_to_chapter(result, chapter_id, chapter_map):
            selected.append(result)

    export_dir = output_dir / output_subdir
    chapter_dir = export_dir / "chapters"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    exported: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for result in selected:
        qid = str(result.get("question_id", ""))
        blockers, risk_flags = validate_for_software(result)
        row = {
            "question_id": qid,
            "risk_flags": risk_flags,
        }
        if blockers:
            row["blocking_reasons"] = blockers
            blocked.append(row)
            continue
        row["answer"] = result["generated_explanation"]["answer"]
        row["preview"] = render_question_preview(
            result, standard_questions.get(qid, {})
        )
        exported.append(row)

    # 写章节预览 Markdown
    chapter_lines = [
        f"# {chapter_id} 题库软件版解析预览\n\n",
        f"可导出题目数：{len(exported)}\n\n",
    ]
    for row in exported:
        chapter_lines.append(row.pop("preview").rstrip() + "\n\n---\n\n")
    chapter_path = chapter_dir / f"{chapter_id}.md"
    chapter_path.write_text("".join(chapter_lines), encoding="utf-8")

    # 写待复核清单
    review_lines = [
        "# 题库软件版待复核清单\n\n",
        f"章节：{chapter_id}\n\n",
        f"待复核题目数：{len(blocked)}\n\n",
    ]
    for row in blocked:
        review_lines.append(f"## {row['question_id']}\n\n")
        for reason in row["blocking_reasons"]:
            review_lines.append(f"- {reason}\n")
        if row["risk_flags"]:
            review_lines.append(f"- 风险标记：{'、'.join(row['risk_flags'])}\n")
        review_lines.append("\n")
    review_path = export_dir / "review_required.md"
    review_path.write_text("".join(review_lines), encoding="utf-8")

    # 写导出结果汇总 JSON
    summary = {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "chapter_id": chapter_id,
        "selected_count": len(selected),
        "exported_count": len(exported),
        "blocked_count": len(blocked),
        "exported": exported,
        "blocked": blocked,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "chapter_markdown": str(chapter_path),
        "review_markdown": str(review_path),
    }
    summary_path = export_dir / "export_results.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="将 V3 解析母版导出为题库软件版格式。"
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--chapter-id", required=True)
    parser.add_argument("--questions-path", default=str(master.DEFAULT_QUESTIONS_PATH))
    parser.add_argument("--chapter-map", default="")
    parser.add_argument("--output-subdir", default="software_export")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    standards = master.load_standard_questions(args.questions_path)

    chapter_map: dict[str, dict[str, Any]] | None = None
    if args.chapter_map:
        chapter_map = {}
        with open(args.chapter_map, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                qid = str(row.get("question_id", "")).strip()
                if qid:
                    chapter_map[qid] = row

    summary = export_chapter(
        output_dir,
        args.chapter_id,
        standards,
        output_subdir=args.output_subdir,
        chapter_map=chapter_map,
    )
    print(
        f"[output] chapter={args.chapter_id} | selected={summary['selected_count']} | "
        f"exported={summary['exported_count']} | blocked={summary['blocked_count']}"
    )
    print(f"[output] preview={summary['chapter_markdown']}")
    print(f"[output] review={summary['review_markdown']}")


if __name__ == "__main__":
    main()
