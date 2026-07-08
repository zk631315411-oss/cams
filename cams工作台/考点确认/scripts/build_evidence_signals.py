from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
WORK_DIR = SCRIPT_DIR.parent
APP_DIR = WORK_DIR.parent
DATA_DIR = APP_DIR / "data" / "teaching_assets"
APP_DATA_DIR = APP_DIR / "data"

BASIC_CARD_TYPES = {"定义", "流程", "风险指标", "法规", "分类"}
CARD_INDEX_FILES = [
    DATA_DIR / "cards_v6_sentence.json",
    APP_DATA_DIR / "cards_ch2_plus_v6_except_ch2_sentence.json",
    APP_DATA_DIR / "cards_ch2.json",
    APP_DATA_DIR / "cards_v6_except_ch2_sentence.json",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: Any, limit: int = 180) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def index_by_id(items: list[dict[str, Any]], key: str = "id") -> dict[str, dict[str, Any]]:
    return {str(item[key]): item for item in items if item.get(key)}


def load_inputs(data_dir: Path) -> dict[str, Any]:
    option_evidence = read_json(data_dir / "option_evidence_map.json")
    questions = read_json(data_dir / "questions.json")
    qa_bindings = read_json(data_dir / "qa_bindings.json")
    qa = read_json(data_dir / "qa.json")
    cards_by_id = load_card_index()

    return {
        "option_evidence": option_evidence,
        "questions_by_id": index_by_id(questions.get("questions", [])),
        "qa_bindings": qa_bindings.get("bindings", []),
        "qa_by_id": index_by_id(qa.get("records", []), "id"),
        "cards_by_id": cards_by_id,
    }


def card_text_weight(card: dict[str, Any]) -> int:
    fields = ["knowledge", "citation", "chapter_path", "type"]
    return sum(1 for field in fields if card.get(field))


def load_card_index() -> dict[str, dict[str, Any]]:
    cards_by_id: dict[str, dict[str, Any]] = {}

    for path in CARD_INDEX_FILES:
        if not path.exists():
            continue
        payload = read_json(path)
        cards = payload if isinstance(payload, list) else payload.get("cards", [])
        for card in cards:
            cid = card.get("card_id") or card.get("id")
            if not cid:
                continue
            existing = cards_by_id.get(cid)
            if not existing or card_text_weight(card) > card_text_weight(existing):
                cards_by_id[cid] = card

    return cards_by_id


def build_qa_indexes(bindings: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[dict[str, Any]]]]:
    by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_card: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for binding in bindings:
        qid = binding.get("bound_question_id")
        if qid:
            by_question[qid].append(binding)
        for cid in binding.get("inherited_card_ids") or []:
            by_card[cid].append(binding)

    return by_question, by_card


def score_signal(
    item: dict[str, Any],
    option: dict[str, Any],
    evidence_card: dict[str, Any],
    canonical_card: dict[str, Any],
    qa_for_question: list[dict[str, Any]],
    qa_for_card: list[dict[str, Any]],
    question: dict[str, Any] | None,
) -> tuple[int, list[str], list[str]]:
    score = 0
    reasons: list[str] = []
    warnings: list[str] = []

    is_correct = bool(option.get("is_correct_answer"))
    support_type = evidence_card.get("support_type") or ""
    evidence_status = option.get("evidence_status") or ""

    if is_correct and support_type == "direct":
        score += 5
        reasons.append("正确选项 direct 证据")
    elif is_correct and evidence_status == "direct":
        score += 4
        reasons.append("正确选项 direct 选项证据")
    elif is_correct:
        score += 2
        reasons.append("正确选项相关证据")

    if not is_correct and support_type in {"negative", "contradict"}:
        score += 2
        reasons.append("错误选项排除证据")
    elif not is_correct and support_type == "direct":
        score += 1
        reasons.append("错误选项相关证据")

    if option.get("common_trap"):
        if is_correct:
            score += 1
            reasons.append("正确选项带常见误区说明")
        else:
            score += 2
            reasons.append("错误选项常见误区候选")

    if qa_for_question:
        score += 2
        reasons.append("题目有关联学生答疑")

    if qa_for_card:
        score += 3
        reasons.append("证据卡被答疑继承引用")

    card_type = evidence_card.get("type") or canonical_card.get("type") or ""
    if card_type in BASIC_CARD_TYPES:
        score += 1
        reasons.append(f"教材句卡类型为{card_type}")

    if evidence_status == "indirect":
        score -= 1
        warnings.append("选项证据为 indirect")

    relevance = evidence_card.get("relevance") or ""
    if relevance == "low":
        score -= 2
        warnings.append("证据相关度 low")
    elif relevance == "medium":
        score -= 1
        warnings.append("证据相关度 medium")

    if option.get("needs_teacher_review"):
        score -= 1
        warnings.append("原证据标记 needs_teacher_review")

    if item.get("validation_issues") or item.get("source_data_issues"):
        score -= 2
        warnings.append("题目证据存在数据校验问题")

    analysis = (question or {}).get("explanation") or ""
    knowledge = evidence_card.get("knowledge") or canonical_card.get("knowledge") or ""
    quote = evidence_card.get("quote") or evidence_card.get("citation") or canonical_card.get("citation") or ""
    if knowledge and knowledge in analysis:
        score += 2
        reasons.append("题目解析直接包含句卡知识表述")
    elif quote and quote in analysis:
        score += 2
        reasons.append("题目解析直接包含句卡原文")

    if not reasons:
        reasons.append("弱相关候选")

    return score, reasons, warnings


def row_from_evidence(
    item: dict[str, Any],
    option: dict[str, Any],
    evidence_card: dict[str, Any],
    question: dict[str, Any] | None,
    canonical_card: dict[str, Any],
    qa_for_question: list[dict[str, Any]],
    qa_for_card: list[dict[str, Any]],
) -> dict[str, Any]:
    score, reasons, warnings = score_signal(
        item,
        option,
        evidence_card,
        canonical_card,
        qa_for_question,
        qa_for_card,
        question,
    )

    qa_ids_for_question = [b.get("qa_id") for b in qa_for_question if b.get("qa_id")]
    qa_ids_for_card = [b.get("qa_id") for b in qa_for_card if b.get("qa_id")]

    return {
        "question_id": item.get("question_id"),
        "section": (question or {}).get("section"),
        "stem": item.get("stem") or (question or {}).get("stem"),
        "answer": item.get("answer") or (question or {}).get("answer"),
        "option": option.get("option"),
        "option_text": option.get("option_text"),
        "is_correct_answer": bool(option.get("is_correct_answer")),
        "judgement": option.get("judgement"),
        "evidence_status": option.get("evidence_status"),
        "support_type": evidence_card.get("support_type"),
        "relevance": evidence_card.get("relevance"),
        "needs_teacher_review": bool(option.get("needs_teacher_review")),
        "card_id": evidence_card.get("card_id"),
        "card_type": evidence_card.get("type") or canonical_card.get("type"),
        "chapter_path": evidence_card.get("chapter_path") or canonical_card.get("chapter_path"),
        "source_line_start": evidence_card.get("source_line_start") or canonical_card.get("source_line_start"),
        "source_line_end": evidence_card.get("source_line_end") or canonical_card.get("source_line_end"),
        "card_knowledge": evidence_card.get("knowledge") or canonical_card.get("knowledge"),
        "card_quote": evidence_card.get("quote") or evidence_card.get("citation") or canonical_card.get("citation"),
        "evidence_reason": evidence_card.get("reason"),
        "option_explanation": option.get("explanation"),
        "common_trap": option.get("common_trap"),
        "qa_ids_for_question": sorted(set(qa_ids_for_question)),
        "qa_ids_for_card": sorted(set(qa_ids_for_card)),
        "qa_question_count": len(set(qa_ids_for_question)),
        "qa_card_count": len(set(qa_ids_for_card)),
        "signal_score": score,
        "signal_reasons": reasons,
        "signal_warnings": warnings,
    }


def fallback_evidence_cards(option: dict[str, Any], cards_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    cards = option.get("evidence_cards") or []
    if cards:
        return cards

    fallback = []
    for cid in option.get("card_ids") or []:
        card = cards_by_id.get(cid, {})
        fallback.append(
            {
                "card_id": cid,
                "support_type": "unknown",
                "relevance": "",
                "knowledge": card.get("knowledge"),
                "citation": card.get("citation"),
                "type": card.get("type"),
                "chapter_path": card.get("chapter_path"),
                "source_line_start": card.get("source_line_start"),
                "source_line_end": card.get("source_line_end"),
                "reason": "由 option.card_ids 回退生成，原 evidence_cards 缺失。",
            }
        )
    return fallback


def build_rows(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    option_evidence = inputs["option_evidence"]
    questions_by_id = inputs["questions_by_id"]
    cards_by_id = inputs["cards_by_id"]
    qa_by_question, qa_by_card = build_qa_indexes(inputs["qa_bindings"])

    rows: list[dict[str, Any]] = []

    for item in option_evidence.get("items", []):
        qid = item.get("question_id")
        question = questions_by_id.get(qid)
        qa_for_question = qa_by_question.get(qid, [])

        for option in item.get("options", []):
            for evidence_card in fallback_evidence_cards(option, cards_by_id):
                cid = evidence_card.get("card_id")
                if not cid:
                    continue
                canonical_card = cards_by_id.get(cid, {})
                rows.append(
                    row_from_evidence(
                        item=item,
                        option=option,
                        evidence_card=evidence_card,
                        question=question,
                        canonical_card=canonical_card,
                        qa_for_question=qa_for_question,
                        qa_for_card=qa_by_card.get(cid, []),
                    )
                )

    return rows


def role_hint(summary: dict[str, Any]) -> str:
    if summary["correct_direct_question_count"] and summary["final_score"] >= 6:
        return "core_candidate"
    if summary["trap_option_count"] and summary["final_score"] >= 4:
        return "trap_candidate"
    if summary["question_count"] >= 2 and summary["final_score"] >= 5:
        return "frequent_candidate"
    if summary["qa_card_count"] and summary["final_score"] >= 4:
        return "qa_candidate"
    if summary["final_score"] >= 4:
        return "support_candidate"
    return "weak_or_background"


def aggregate_cards(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["card_id"]].append(row)

    summaries: list[dict[str, Any]] = []

    for cid, card_rows in grouped.items():
        question_ids = sorted({r["question_id"] for r in card_rows if r.get("question_id")})
        correct_direct_questions = sorted(
            {
                r["question_id"]
                for r in card_rows
                if r.get("is_correct_answer") and r.get("support_type") == "direct" and r.get("question_id")
            }
        )
        correct_questions = sorted(
            {r["question_id"] for r in card_rows if r.get("is_correct_answer") and r.get("question_id")}
        )
        trap_rows = [r for r in card_rows if (not r.get("is_correct_answer")) and r.get("common_trap")]
        qa_ids_for_question = sorted({qid for r in card_rows for qid in r.get("qa_ids_for_question", [])})
        qa_ids_for_card = sorted({qid for r in card_rows for qid in r.get("qa_ids_for_card", [])})
        score_sum = sum(int(r.get("signal_score") or 0) for r in card_rows)
        multi_question_bonus = max(0, len(question_ids) - 1) * 2
        correct_direct_bonus = max(0, len(correct_direct_questions) - 1) * 2
        final_score = score_sum + multi_question_bonus + correct_direct_bonus

        first = card_rows[0]
        reasons = Counter(reason for r in card_rows for reason in r.get("signal_reasons", []))
        warnings = Counter(warning for r in card_rows for warning in r.get("signal_warnings", []))
        option_refs = [
            {
                "question_id": r.get("question_id"),
                "option": r.get("option"),
                "is_correct_answer": r.get("is_correct_answer"),
                "support_type": r.get("support_type"),
                "signal_score": r.get("signal_score"),
            }
            for r in sorted(card_rows, key=lambda row: (row.get("question_id") or "", row.get("option") or ""))
        ]

        summary = {
            "card_id": cid,
            "final_score": final_score,
            "raw_signal_score_sum": score_sum,
            "multi_question_bonus": multi_question_bonus,
            "correct_direct_bonus": correct_direct_bonus,
            "question_count": len(question_ids),
            "correct_question_count": len(correct_questions),
            "correct_direct_question_count": len(correct_direct_questions),
            "trap_option_count": len(trap_rows),
            "qa_question_count": len(qa_ids_for_question),
            "qa_card_count": len(qa_ids_for_card),
            "question_ids": question_ids,
            "correct_question_ids": correct_questions,
            "correct_direct_question_ids": correct_direct_questions,
            "qa_ids_for_question": qa_ids_for_question,
            "qa_ids_for_card": qa_ids_for_card,
            "card_type": first.get("card_type"),
            "chapter_path": first.get("chapter_path"),
            "source_line_start": first.get("source_line_start"),
            "source_line_end": first.get("source_line_end"),
            "card_knowledge": first.get("card_knowledge"),
            "card_quote": first.get("card_quote"),
            "top_reasons": [{"reason": k, "count": v} for k, v in reasons.most_common()],
            "warnings": [{"warning": k, "count": v} for k, v in warnings.most_common()],
            "option_refs": option_refs,
        }
        summary["role_hint"] = role_hint(summary)
        summaries.append(summary)

    return sorted(summaries, key=lambda item: (-item["final_score"], item["card_id"]))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_summary(rows: list[dict[str, Any]], cards: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "inputs": {
            "data_dir": str(DATA_DIR),
            "option_evidence": str(DATA_DIR / "option_evidence_map.json"),
            "questions": str(DATA_DIR / "questions.json"),
            "qa_bindings": str(DATA_DIR / "qa_bindings.json"),
            "qa": str(DATA_DIR / "qa.json"),
            "card_index_files": [str(path) for path in CARD_INDEX_FILES if path.exists()],
        },
        "row_count": len(rows),
        "card_count": len(cards),
        "question_count": len({r["question_id"] for r in rows if r.get("question_id")}),
        "correct_option_row_count": sum(1 for r in rows if r.get("is_correct_answer")),
        "direct_correct_row_count": sum(
            1 for r in rows if r.get("is_correct_answer") and r.get("support_type") == "direct"
        ),
        "role_hint_counts": Counter(card["role_hint"] for card in cards),
        "support_type_counts": Counter(str(r.get("support_type") or "") for r in rows),
        "evidence_status_counts": Counter(str(r.get("evidence_status") or "") for r in rows),
    }


def render_report(summary: dict[str, Any], card_scores: list[dict[str, Any]]) -> str:
    lines = [
        "# 证据信号样例报告",
        "",
        "## 统计",
        "",
        f"- 明细行数：{summary['row_count']}",
        f"- 证据卡数：{summary['card_count']}",
        f"- 题目数：{summary['question_count']}",
        f"- 正确选项证据行：{summary['correct_option_row_count']}",
        f"- 正确选项 direct 证据行：{summary['direct_correct_row_count']}",
        "",
        "## 角色提示分布",
        "",
    ]

    for name, count in summary["role_hint_counts"].most_common():
        lines.append(f"- {name}: {count}")

    lines += ["", "## Top 20 候选证据卡", ""]

    for idx, card in enumerate(card_scores[:20], start=1):
        reasons = "；".join(f"{item['reason']} x{item['count']}" for item in card["top_reasons"][:3])
        questions = "、".join(card["question_ids"][:5])
        lines += [
            f"### {idx}. {card['card_id']} | {card['role_hint']} | {card['final_score']} 分",
            "",
            f"- 题目：{questions}",
            f"- 类型：{card.get('card_type') or ''}",
            f"- 章节：{card.get('chapter_path') or ''}",
            f"- 知识：{compact(card.get('card_knowledge'), 140)}",
            f"- 原文：{compact(card.get('card_quote'), 180)}",
            f"- 主要理由：{reasons}",
            "",
        ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build evidence signal tables for exam point curation.")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--work-dir", type=Path, default=WORK_DIR)
    args = parser.parse_args()

    inputs = load_inputs(args.data_dir)
    rows = build_rows(inputs)
    card_scores = aggregate_cards(rows)
    summary = build_summary(rows, card_scores)

    outputs_dir = args.work_dir / "outputs"
    reports_dir = args.work_dir / "reports"

    write_jsonl(outputs_dir / "evidence_signals.jsonl", rows)
    write_json(outputs_dir / "evidence_card_scores.json", {"cards": card_scores})
    write_json(outputs_dir / "evidence_signal_summary.json", summary)
    (reports_dir / "evidence_signal_sample.md").write_text(
        render_report(summary, card_scores),
        encoding="utf-8",
    )

    print(f"wrote {len(rows)} signal rows")
    print(f"wrote {len(card_scores)} card summaries")
    print(outputs_dir)


if __name__ == "__main__":
    main()
