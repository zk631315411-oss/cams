#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Audit teaching_assets trust levels.

The script is intentionally non-mutating: it reads assets, classifies relationship
trust, and writes JSON/Markdown reports.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "data" / "teaching_assets"
REPORT_JSON = ASSET_DIR / "asset_trust_report.json"
REPORT_MD = ASSET_DIR / "asset_trust_report.md"


TRUST_ORDER = {
    "trusted": 5,
    "high_candidate": 4,
    "medium_candidate": 3,
    "low_candidate": 2,
    "invalid_or_blocked": 1,
}


def read_json(name: str) -> Any:
    return json.loads((ASSET_DIR / name).read_text(encoding="utf-8"))


def normalize_cards(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("cards") or []
    return []


def unique(values):
    return list(dict.fromkeys(v for v in values if v))


def option_labels(question: dict) -> set[str]:
    return set((question.get("options") or {}).keys())


def answer_labels(answer: Any, question: dict | None = None) -> set[str]:
    if answer is None:
        return set()
    raw = str(answer).strip()
    options = (question or {}).get("options") or {}
    if raw in options:
        return {raw}
    matched_by_text = {label for label, text in options.items() if raw == str(text).strip()}
    if matched_by_text:
        return matched_by_text
    return {ch for ch in raw if ch.isalpha()}


def compact_text(value: str) -> str:
    return "".join(str(value or "").split())


def quote_in_text(quote: str, text: str) -> bool:
    quote = (quote or "").strip()
    text = text or ""
    if not quote:
        return False
    if quote in text:
        return True
    if len(quote) > 22 and quote[:40] in text:
        return True
    c_quote = compact_text(quote)
    if len(c_quote) < 8:
        return False
    return c_quote in compact_text(text)


def iter_paragraphs(chapter: dict):
    for section in chapter.get("sections", []):
        for subsection in section.get("subsections", []):
            for paragraph in subsection.get("paragraphs", []):
                yield section, subsection, paragraph


def collect_reader_card_ids(chapter: dict) -> set[str]:
    ids = set()
    for _, _, paragraph in iter_paragraphs(chapter):
        for cid in (paragraph.get("card_ids") or []) + (paragraph.get("highlight_card_ids") or []):
            if cid:
                ids.add(cid)
    return ids


def collect_reader_texts(chapter: dict) -> list[str]:
    return [paragraph.get("text") or "" for _, _, paragraph in iter_paragraphs(chapter)]


def add_issue(issues: list[dict], severity: str, category: str, message: str, **extra):
    issues.append({
        "severity": severity,
        "category": category,
        "message": message,
        **extra,
    })


def derive_option_trust(option: dict, item: dict) -> tuple[str, list[str]]:
    reasons = []
    if item.get("source_data_issues") or item.get("validation_issues"):
        return "invalid_or_blocked", ["question_or_source_data_issue"]
    if option.get("needs_teacher_review"):
        reasons.append("needs_teacher_review")
    status = option.get("evidence_status") or "none"
    card_ids = option.get("card_ids") or option.get("evidence_card_ids") or []
    if status == "direct" and card_ids:
        trust = "high_candidate"
    elif status == "indirect" and card_ids:
        trust = "medium_candidate"
    elif status in {"none", "needs_manual", "conflict"}:
        trust = "invalid_or_blocked"
        reasons.append("no_usable_direct_evidence")
    else:
        trust = "low_candidate"
        reasons.append("unknown_evidence_status")
    if option.get("is_correct_answer") and status != "direct":
        trust = min_trust(trust, "medium_candidate")
        reasons.append("correct_option_without_direct_evidence")
    return trust, reasons


def min_trust(a: str, b: str) -> str:
    return a if TRUST_ORDER[a] <= TRUST_ORDER[b] else b


def derive_exam_point_trust(ep: dict, card_by_id: dict[str, dict], reader_card_ids: set[str], reader_texts: list[str]) -> tuple[str, list[str]]:
    reasons = []
    if ep.get("source_data_issues") or ep.get("validation_issues"):
        return "invalid_or_blocked", ["source_or_validation_issue"]

    source_types = set(ep.get("source_types") or [])
    details = ep.get("source_card_details") or []
    source_card_ids = ep.get("source_card_ids") or []

    if "question_derived_point" in source_types:
        bindings = ep.get("option_bindings") or []
        statuses = [b.get("evidence_status") or "none" for b in bindings]
        if statuses and all(status == "direct" for status in statuses):
            trust = "high_candidate"
        elif any(status == "direct" for status in statuses):
            trust = "medium_candidate"
            reasons.append("mixed_option_evidence")
        else:
            trust = "low_candidate"
            reasons.append("no_direct_option_evidence")
    elif "basic_textbook_point" in source_types:
        trust = "medium_candidate"
        reasons.append("basic_candidate_not_teacher_confirmed")
    else:
        trust = "low_candidate"
        reasons.append("unknown_source_type")

    if not source_card_ids and not details:
        return "invalid_or_blocked", reasons + ["no_source_cards_or_details"]

    missing_cards = [cid for cid in source_card_ids if cid not in card_by_id and not cid.startswith(("ch2s_", "v6x_"))]
    if missing_cards:
        trust = min_trust(trust, "low_candidate")
        reasons.append("source_card_not_in_current_card_pool")

    can_backproject = False
    for cid in source_card_ids:
        if cid in reader_card_ids:
            can_backproject = True
            break
    if not can_backproject:
        for detail in details:
            quote = detail.get("quote") or detail.get("citation") or ""
            if any(quote_in_text(quote, text) for text in reader_texts):
                can_backproject = True
                break
    if not can_backproject:
        trust = min_trust(trust, "low_candidate")
        reasons.append("cannot_backproject_to_current_reader")

    if ep.get("status") in {"needs_evidence", "needs_manual"}:
        trust = min_trust(trust, "low_candidate")
        reasons.append("status_requires_manual_review")
    if ep.get("status") == "needs_teacher_attention":
        trust = min_trust(trust, "medium_candidate")
        reasons.append("trap_attention_candidate")
    return trust, reasons


def main() -> None:
    chapter = read_json("chapters/ch2_extracted.json")
    cards_payload = read_json("cards_v6_sentence.json")
    questions_payload = read_json("questions.json")
    option_evidence = read_json("option_evidence_map.json")
    exam_points_payload = read_json("exam_points_teaching_mvp.json")
    sentence_map = read_json("sentence_exam_point_map.json")
    qa_bindings = read_json("qa_bindings.json")
    kg_data = read_json("kg_data.json")
    question_card_map = read_json("question_card_map.json")

    cards = normalize_cards(cards_payload)
    card_by_id = {card.get("card_id"): card for card in cards if card.get("card_id")}
    questions = questions_payload.get("questions") or []
    question_by_id = {q.get("id"): q for q in questions if q.get("id")}
    reader_card_ids = collect_reader_card_ids(chapter)
    reader_texts = collect_reader_texts(chapter)

    issues: list[dict] = []
    relation_rows: list[dict] = []

    # Question internal consistency.
    question_issue_count = 0
    for q in questions:
        labels = option_labels(q)
        answers = answer_labels(q.get("answer"), q)
        missing = sorted(answers - labels)
        if missing:
            question_issue_count += 1
            add_issue(
                issues,
                "blocker",
                "question_source_data",
                "题库答案包含不存在的选项。",
                question_id=q.get("id"),
                missing_answer_options=missing,
                option_labels=sorted(labels),
            )

    # Option evidence trust.
    option_trust_counter = Counter()
    question_option_summary = {}
    for item in option_evidence.get("items", []):
        qid = item.get("question_id")
        q_summary = Counter()
        for option in item.get("options") or []:
            trust, reasons = derive_option_trust(option, item)
            option_trust_counter[trust] += 1
            q_summary[trust] += 1
            relation_rows.append({
                "relation_type": "option_to_card",
                "trust": trust,
                "reasons": reasons,
                "question_id": qid,
                "option": option.get("option"),
                "evidence_status": option.get("evidence_status"),
                "card_ids": option.get("card_ids") or option.get("evidence_card_ids") or [],
            })
        question_option_summary[qid] = dict(q_summary)

    # Exam point trust.
    exam_point_trust_counter = Counter()
    exam_point_samples = defaultdict(list)
    for ep in exam_points_payload.get("exam_points") or []:
        trust, reasons = derive_exam_point_trust(ep, card_by_id, reader_card_ids, reader_texts)
        exam_point_trust_counter[trust] += 1
        if len(exam_point_samples[trust]) < 8:
            exam_point_samples[trust].append({
                "id": ep.get("id"),
                "title": ep.get("title"),
                "status": ep.get("status"),
                "source_types": ep.get("source_types") or [],
                "reasons": reasons,
            })
        relation_rows.append({
            "relation_type": "exam_point",
            "trust": trust,
            "reasons": reasons,
            "exam_point_id": ep.get("id"),
            "title": ep.get("title"),
            "source_types": ep.get("source_types") or [],
            "source_card_ids": ep.get("source_card_ids") or [],
            "question_ids": ep.get("question_ids") or [],
        })

    # Sentence map checks.
    mapped_ep_ids = {row.get("exam_point_id") for row in sentence_map.get("sentences") or [] if row.get("exam_point_id")}
    all_ep_ids = {ep.get("id") for ep in exam_points_payload.get("exam_points") or [] if ep.get("id")}
    unmapped_ep_ids = sorted(all_ep_ids - mapped_ep_ids)
    for ep_id in unmapped_ep_ids[:50]:
        add_issue(
            issues,
            "warning",
            "sentence_map",
            "考点未映射到当前第二章阅读区。",
            exam_point_id=ep_id,
        )

    # QA and KG are auxiliary in this audit.
    qa_binding_count = len(qa_bindings.get("bindings") or [])
    low_qa_bindings = [
        b for b in qa_bindings.get("bindings") or []
        if (b.get("match_method") != "manual" and not b.get("teacher_confirmed"))
    ]
    kg_node_count = len([key for key in kg_data.keys() if not key.startswith("_")])
    kg_section_count = len(kg_data.get("_sections") or {})
    question_card_map_count = len((question_card_map.get("mappings") or {}).keys())

    report = {
        "version": "0.1",
        "generated_at": date.today().isoformat(),
        "scope": "cams工作台/data/teaching_assets",
        "trust_policy": {
            "trusted": "only teacher-confirmed relationships",
            "high_candidate": "direct evidence and no blocking issue",
            "medium_candidate": "usable candidate but needs review",
            "low_candidate": "weak/auxiliary/indirect relationship",
            "invalid_or_blocked": "source conflict, missing evidence, or validation issue",
        },
        "asset_counts": {
            "chapter_sections": len(chapter.get("sections") or []),
            "reader_card_ids": len(reader_card_ids),
            "cards": len(cards),
            "questions": len(questions),
            "option_evidence_questions": len(option_evidence.get("items") or []),
            "exam_points": len(exam_points_payload.get("exam_points") or []),
            "sentence_map_rows": len(sentence_map.get("sentences") or []),
            "qa_bindings": qa_binding_count,
            "kg_nodes": kg_node_count,
            "kg_sections": kg_section_count,
            "question_card_map_questions": question_card_map_count,
        },
        "summaries": {
            "question_source_data_issues": question_issue_count,
            "option_trust_counts": dict(option_trust_counter),
            "exam_point_trust_counts": dict(exam_point_trust_counter),
            "mapped_exam_points": len(mapped_ep_ids),
            "unmapped_exam_points": len(unmapped_ep_ids),
            "qa_bindings_auxiliary_only": qa_binding_count,
            "qa_bindings_not_teacher_confirmed": len(low_qa_bindings),
        },
        "exam_point_samples": dict(exam_point_samples),
        "issues": issues,
        "relations": relation_rows,
    }

    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "wrote": [str(REPORT_JSON), str(REPORT_MD)],
        "summaries": report["summaries"],
    }, ensure_ascii=False, indent=2))


def render_markdown(report: dict) -> str:
    summaries = report["summaries"]
    counts = report["asset_counts"]
    ep_counts = summaries["exam_point_trust_counts"]
    option_counts = summaries["option_trust_counts"]
    lines = []
    lines.append("# Teaching Assets 可信度审查报告")
    lines.append("")
    lines.append(f"生成日期：{report['generated_at']}")
    lines.append(f"审查范围：`{report['scope']}`")
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append(f"- 教材阅读区卡片 ID：{counts['reader_card_ids']}")
    lines.append(f"- 全书句卡：{counts['cards']}")
    lines.append(f"- 题目：{counts['questions']}")
    lines.append(f"- 已有选项级证据题目：{counts['option_evidence_questions']}")
    lines.append(f"- 统一候选考点：{counts['exam_points']}")
    lines.append(f"- 原文-考点映射行：{counts['sentence_map_rows']}")
    lines.append(f"- 答疑绑定：{counts['qa_bindings']}（本轮仅作辅助线索）")
    lines.append(f"- KG 节点/章节：{counts['kg_nodes']} / {counts['kg_sections']}（本轮仅作概念辅助）")
    lines.append("")
    lines.append("## 可信度分布")
    lines.append("")
    lines.append("### 选项 -> 教材证据")
    lines.append("")
    for key in ["trusted", "high_candidate", "medium_candidate", "low_candidate", "invalid_or_blocked"]:
        lines.append(f"- `{key}`：{option_counts.get(key, 0)}")
    lines.append("")
    lines.append("### 考点候选")
    lines.append("")
    for key in ["trusted", "high_candidate", "medium_candidate", "low_candidate", "invalid_or_blocked"]:
        lines.append(f"- `{key}`：{ep_counts.get(key, 0)}")
    lines.append("")
    lines.append("## 关键风险")
    lines.append("")
    lines.append(f"- 题库内部冲突：{summaries['question_source_data_issues']} 条。题干/选项/答案原则上可信，但互相冲突时必须标红，不能自动修。")
    lines.append(f"- 未映射到当前第二章阅读区的考点：{summaries['unmapped_exam_points']} 条。可能是跨章节证据或 quote 无法回贴。")
    lines.append(f"- QA 绑定未人工确认：{summaries['qa_bindings_not_teacher_confirmed']} 条。本轮不能直接作为正式错因来源。")
    lines.append("")
    lines.append("## 样例：不可直接使用的关系")
    lines.append("")
    blocked = [r for r in report["relations"] if r["trust"] == "invalid_or_blocked"][:10]
    if not blocked:
        lines.append("暂无。")
    for row in blocked:
        if row["relation_type"] == "option_to_card":
            lines.append(f"- 选项证据 `{row.get('question_id')} {row.get('option')}`：{', '.join(row.get('reasons') or [])}")
        else:
            lines.append(f"- 考点 `{row.get('exam_point_id')}`：{', '.join(row.get('reasons') or [])}")
    lines.append("")
    lines.append("## 样例：低可信候选")
    lines.append("")
    low = [r for r in report["relations"] if r["trust"] == "low_candidate"][:10]
    if not low:
        lines.append("暂无。")
    for row in low:
        if row["relation_type"] == "option_to_card":
            lines.append(f"- 选项证据 `{row.get('question_id')} {row.get('option')}`：{', '.join(row.get('reasons') or [])}")
        else:
            lines.append(f"- 考点 `{row.get('exam_point_id')}`：{', '.join(row.get('reasons') or [])}")
    lines.append("")
    lines.append("## 下一步建议")
    lines.append("")
    lines.append("- HTML 默认显示全部候选，但必须按可信度显示标识和筛选。")
    lines.append("- `trusted` 只从未来的 `teaching_review_decisions.json` 读取，不由脚本自动生成。")
    lines.append("- 先处理 `invalid_or_blocked`：题目数据冲突、正确选项无 direct 证据、无法回贴原文。")
    lines.append("- QA/KG 继续作为辅助面板，不参与正式考点确认。")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
