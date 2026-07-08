"""
Build option-level question-card mappings from step1 outputs.

Step1 is the LLM/agentic search stage. This script is intentionally mechanical:
it does not infer new evidence and does not upgrade evidence status. It only
validates real textbook card ids and reshapes option_analysis for audit/front-end
consumption.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


BASE = Path(r"D:\守正公司工作区\cams考试\cams工作台（重构版）")
STEP1_DIR = BASE / "tools" / "选项证据生成" / "output" / "step1_ai_responses"
OUTPUT_DIR = BASE / "tools" / "选项证据生成" / "output" / "step2_option_mapping"
FRONTEND_OUTPUT = BASE / "data" / "derived" / "option_evidence_map.json"

EVIDENCE_FILES = {
    "v6-sentence": BASE / "data" / "cards" / "cards_v6_sentence.json",
}

REQUIRED_OPTION_FIELDS = {
    "option",
    "option_text",
    "judgement",
    "evidence_status",
    "evidence_cards",
    "explanation",
    "common_trap",
    "needs_teacher_review",
}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cards_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        cards = payload.get("cards", [])
    else:
        cards = payload
    if not isinstance(cards, list):
        raise ValueError("card payload must be a list or an object with cards list")
    return [card for card in cards if isinstance(card, dict) and card.get("card_id")]


def load_card_index(scope: str) -> dict[str, dict[str, Any]]:
    path = EVIDENCE_FILES.get(scope)
    if not path:
        raise ValueError(f"unknown evidence scope: {scope}")
    cards = cards_from_payload(read_json(path))
    return {card["card_id"]: card for card in cards}


def normalize_answer(answer: Any) -> set[str]:
    return {item for item in str(answer or "").replace(" ", "").split(",") if item}


def option_sort_key(label: str) -> tuple[int, str]:
    order = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    idx = order.find(str(label or "").strip())
    return (idx if idx >= 0 else 999, str(label or ""))


def canonical_option_text(options: Any, label: Any, fallback: Any) -> str:
    if isinstance(options, dict):
        original_text = options.get(label)
        if isinstance(original_text, str):
            return original_text
    return str(fallback or "")


def canonical_validation_issues(issues: Any) -> list[str]:
    if not isinstance(issues, list):
        return []
    return [str(issue) for issue in issues if "option_text 与原题不一致" not in str(issue)]


def output_path_for_question(path: Path) -> str:
    return str(path)


def iter_step1_outputs(
    step1_dir: Path,
    scope: str | None = None,
    ids: set[str] | None = None,
) -> list[tuple[Path, dict[str, Any]]]:
    rows: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(step1_dir.glob("q_*.json")):
        data = read_json(path)
        qid = data.get("question_id")
        if ids and qid not in ids:
            continue
        if scope and data.get("evidence_scope", "ch2") != scope:
            continue
        rows.append((path, data))
    return rows


def build_maps(
    step1_dir: Path,
    scope: str | None = None,
    ids: set[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    outputs = iter_step1_outputs(step1_dir=step1_dir, scope=scope, ids=ids)
    card_indexes: dict[str, dict[str, dict[str, Any]]] = {}

    question_items: list[dict[str, Any]] = []
    card_option_map: dict[str, list[dict[str, Any]]] = {}
    issues: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()
    hallucinated: list[dict[str, Any]] = []
    option_mismatch: list[dict[str, Any]] = []
    parse_failed: list[str] = []
    correct_without_direct: list[dict[str, Any]] = []

    for path, result in outputs:
        qid = result.get("question_id") or path.stem.removeprefix("q_")
        result_scope = result.get("evidence_scope", "ch2")
        if result_scope not in card_indexes:
            card_indexes[result_scope] = load_card_index(result_scope)
        card_index = card_indexes[result_scope]

        options = result.get("options", {})
        option_analysis = result.get("option_analysis", [])
        if not isinstance(option_analysis, list):
            option_analysis = []
            parse_failed.append(qid)

        expected_labels = list(options.keys()) if isinstance(options, dict) else []
        actual_labels = [item.get("option") for item in option_analysis if isinstance(item, dict)]
        if len(option_analysis) != len(expected_labels) or actual_labels != expected_labels:
            option_mismatch.append(
                {
                    "question_id": qid,
                    "expected": expected_labels,
                    "actual": actual_labels,
                }
            )

        correct = normalize_answer(result.get("answer", ""))
        item_options = []
        option_card_set: set[str] = set()

        for opt in sorted([x for x in option_analysis if isinstance(x, dict)], key=lambda row: option_sort_key(row.get("option", ""))):
            label = opt.get("option", "")
            option_text = canonical_option_text(options, label, opt.get("option_text", ""))
            missing_fields = sorted(REQUIRED_OPTION_FIELDS - set(opt))
            if missing_fields:
                issues.append({"question_id": qid, "option": label, "type": "missing_fields", "fields": missing_fields})

            evidence_cards = opt.get("evidence_cards", [])
            if not isinstance(evidence_cards, list):
                evidence_cards = []
                issues.append({"question_id": qid, "option": label, "type": "evidence_cards_not_list"})

            normalized_cards = []
            for evidence in evidence_cards:
                if not isinstance(evidence, dict):
                    continue
                cid = evidence.get("card_id", "")
                card = card_index.get(cid)
                if not card:
                    hallucinated.append({"question_id": qid, "option": label, "card_id": cid, "scope": result_scope})
                    continue
                option_card_set.add(cid)
                normalized = {
                    "card_id": cid,
                    "support_type": evidence.get("support_type", ""),
                    "source": evidence.get("source", ""),
                    "quote": evidence.get("quote", ""),
                    "reason": evidence.get("reason", ""),
                    "relevance": evidence.get("relevance", ""),
                    "knowledge": card.get("knowledge", ""),
                    "citation": card.get("citation", ""),
                    "type": card.get("type", ""),
                    "chapter_path": card.get("chapter_path", ""),
                    "source_line_start": card.get("source_line_start"),
                    "source_line_end": card.get("source_line_end"),
                }
                normalized_cards.append(normalized)
                card_option_map.setdefault(cid, []).append(
                    {
                        "question_id": qid,
                        "option": label,
                        "option_text": option_text,
                        "judgement": opt.get("judgement", ""),
                        "is_correct_answer": label in correct,
                        "evidence_status": opt.get("evidence_status", ""),
                        "support_type": evidence.get("support_type", ""),
                        "source": evidence.get("source", ""),
                        "relevance": evidence.get("relevance", ""),
                    }
                )

            evidence_status = opt.get("evidence_status", "")
            counters["total_options"] += 1
            counters[f"options_status_{evidence_status or 'missing'}"] += 1
            if evidence_status == "direct":
                counters["options_with_direct_evidence"] += 1
            elif evidence_status == "indirect":
                counters["options_with_indirect_evidence"] += 1
            elif evidence_status == "none":
                counters["options_with_no_evidence"] += 1
            elif evidence_status == "needs_manual":
                counters["options_needs_manual"] += 1

            if evidence_status == "direct" and not normalized_cards:
                issues.append({"question_id": qid, "option": label, "type": "direct_without_cards"})
            if evidence_status == "none" and normalized_cards:
                issues.append({"question_id": qid, "option": label, "type": "none_with_cards"})
            if label in correct and evidence_status != "direct":
                correct_without_direct.append(
                    {
                        "question_id": qid,
                        "option": label,
                        "evidence_status": evidence_status,
                        "needs_teacher_review": bool(opt.get("needs_teacher_review")),
                    }
                )

            item_options.append(
                {
                    "option": label,
                    "option_text": option_text,
                    "is_correct_answer": label in correct,
                    "judgement": opt.get("judgement", ""),
                    "judgement_confidence": opt.get("judgement_confidence", ""),
                    "evidence_status": evidence_status,
                    "card_ids": [card["card_id"] for card in normalized_cards],
                    "evidence_cards": normalized_cards,
                    "explanation": opt.get("explanation", ""),
                    "common_trap": opt.get("common_trap", ""),
                    "needs_teacher_review": bool(opt.get("needs_teacher_review")),
                    "teacher_review_reason": opt.get("teacher_review_reason", ""),
                    "kg_concepts": opt.get("kg_concepts", []),
                }
            )

        counters["total_questions"] += 1
        counters[f"question_status_{result.get('status', 'missing')}"] += 1
        if result.get("status") == "answered":
            counters["questions_answered"] += 1
        elif result.get("status") == "partial":
            counters["questions_partial"] += 1

        cited = set(result.get("cited_cards", []) or [])
        if cited != option_card_set:
            issues.append(
                {
                    "question_id": qid,
                    "type": "cited_cards_mismatch",
                    "cited_cards": sorted(cited),
                    "option_cards": sorted(option_card_set),
                }
            )

        validation_issues = canonical_validation_issues(result.get("validation_issues", []))
        quality = dict(result.get("quality", {}) or {})
        quality["validation_issues"] = canonical_validation_issues(quality.get("validation_issues", []))

        question_items.append(
            {
                "question_id": qid,
                "stem": result.get("stem", ""),
                "answer": result.get("answer", ""),
                "status": result.get("status", ""),
                "evidence_scope": result_scope,
                "evidence_file": result.get("evidence_file", ""),
                "source_step1_file": output_path_for_question(path),
                "validation_issues": validation_issues,
                "quality": quality,
                "options": item_options,
            }
        )

    stats = {
        "asset_note": "Stats for option-level textbook evidence binding.",
        "total_questions": counters["total_questions"],
        "total_options": counters["total_options"],
        "questions_answered": counters["questions_answered"],
        "questions_partial": counters["questions_partial"],
        "options_with_direct_evidence": counters["options_with_direct_evidence"],
        "options_with_indirect_evidence": counters["options_with_indirect_evidence"],
        "options_with_no_evidence": counters["options_with_no_evidence"],
        "options_needs_manual": counters["options_needs_manual"],
        "status_counts": {key.removeprefix("options_status_"): value for key, value in sorted(counters.items()) if key.startswith("options_status_")},
        "question_status_counts": {key.removeprefix("question_status_"): value for key, value in sorted(counters.items()) if key.startswith("question_status_")},
        "hallucinated_card_ids": hallucinated,
        "option_count_mismatch": option_mismatch,
        "parse_failed_questions": parse_failed,
        "correct_options_without_direct": correct_without_direct,
        "issues": issues,
    }

    question_map = {
        "asset_note": "Option-level candidate textbook evidence binding for teacher review. It is not final teaching approval.",
        "schema_version": "question_option_card_map_v1",
        "evidence_scopes": sorted({item["evidence_scope"] for item in question_items}),
        "items": question_items,
    }
    reverse_map = {
        "asset_note": "Reverse index from textbook sentence card to question options.",
        "schema_version": "card_option_question_map_v1",
        "items": card_option_map,
    }
    frontend_map = {
        "asset_note": "Front-end copy of option-level candidate textbook evidence binding.",
        "schema_version": question_map["schema_version"],
        "items": question_items,
        "stats": stats,
    }
    return question_map, reverse_map, stats, frontend_map


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build option-level question/card mappings from step1 outputs.")
    parser.add_argument("--scope", choices=sorted(EVIDENCE_FILES), help="Only include step1 outputs from this evidence scope.")
    parser.add_argument("--ids", nargs="*", help="Only include these question ids, for example 2.1_1 2.1_2.")
    parser.add_argument("--step1-dir", type=Path, default=STEP1_DIR, help="Directory containing q_*.json step1 outputs.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Directory for step2 mapping outputs.")
    parser.add_argument("--write-frontend", action="store_true", help="Also write cams工作台/data/option_evidence_map.json.")
    args = parser.parse_args(argv)

    ids = set(args.ids) if args.ids else None
    question_map, reverse_map, stats, frontend_map = build_maps(step1_dir=args.step1_dir, scope=args.scope, ids=ids)

    write_json(args.output_dir / "question_option_card_map.json", question_map)
    write_json(args.output_dir / "card_option_question_map.json", reverse_map)
    write_json(args.output_dir / "stats.json", stats)
    if args.write_frontend:
        write_json(FRONTEND_OUTPUT, frontend_map)

    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"Wrote {args.output_dir}")
    if args.write_frontend:
        print(f"Wrote {FRONTEND_OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
