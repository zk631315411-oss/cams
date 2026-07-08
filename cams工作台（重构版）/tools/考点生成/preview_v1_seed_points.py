"""
Preview v1: build stable seed points from q_*.json without LLM merging.

This script is intentionally conservative:
- Only non-flagged questions enter formal seed points.
- Only strong evidence cards enter seed points.
- Flagged questions and missing-key-evidence cases are written to reports.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
QUESTIONS_DIR = (
    HERE.parent
    / "选项证据生成"
    / "新题解析模块复用"
    / "output"
    / "questions"
)
SOURCE_SUMMARY = (
    HERE.parent
    / "选项证据生成"
    / "新题解析模块复用"
    / "output"
    / "summary.json"
)
OUT_DIR = HERE / "work" / "preview_v1"

STRONG_GRADES = {
    "direct_single",
    "direct_multi",
    "semantic_direct",
    "negative_direct",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_answer(answer: Any, option_labels: set[str]) -> set[str]:
    if isinstance(answer, list):
        return {str(item).strip().upper() for item in answer if str(item).strip()}
    text = str(answer or "").strip().upper()
    if not text:
        return set()
    for sep in ["，", ",", "、", "/", "|", ";", "；", " "]:
        text = text.replace(sep, ",")
    parts = [part.strip() for part in text.split(",") if part.strip()]
    if len(parts) == 1 and len(parts[0]) > 1:
        chars = set(parts[0])
        if chars and chars <= option_labels:
            return chars
    return {part for part in parts if part in option_labels or len(part) == 1}


def compact(text: str, limit: int = 120) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def question_validation(data: dict[str, Any], key_answer: set[str], ai_answer: set[str]) -> tuple[bool, list[str]]:
    final = data.get("final") or {}
    validate = (data.get("pipeline") or {}).get("validate") or {}
    validation_status = str(validate.get("validation_status") or "").strip()
    needs_teacher_review = bool(final.get("needs_teacher_review"))

    reasons: list[str] = []
    if key_answer != ai_answer:
        reasons.append("ai_answer_differs_from_key")
    if validation_status and validation_status != "passed":
        reasons.append(f"validation_status={validation_status}")
    if needs_teacher_review:
        reasons.append("needs_teacher_review=true")
    return not reasons, reasons


def card_meta_from_evidence(card: dict[str, Any]) -> dict[str, str]:
    return {
        "card_id": str(card.get("card_id") or ""),
        "quote": compact(card.get("quote") or card.get("citation") or "", 240),
        "knowledge": compact(card.get("knowledge") or "", 160),
        "citation": compact(card.get("citation") or "", 240),
        "support_type": str(card.get("support_type") or ""),
        "relevance": str(card.get("relevance") or ""),
        "reason": compact(card.get("reason") or "", 180),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(QUESTIONS_DIR.glob("q_*.json"))

    source_summary = {}
    if SOURCE_SUMMARY.exists():
        source_summary = read_json(SOURCE_SUMMARY)

    seed_by_card: dict[str, dict[str, Any]] = {}
    strong_edges: list[dict[str, Any]] = []
    flagged_questions: list[dict[str, Any]] = []
    evidence_gaps: list[dict[str, Any]] = []
    weak_signal_rows: list[dict[str, Any]] = []

    stats = Counter()
    validation_counter = Counter()
    grade_counter = Counter()
    flagged_reason_counter = Counter()

    for path in files:
        data = read_json(path)
        qid = str(data.get("question_id") or path.stem.replace("q_", ""))
        options = data.get("options") or {}
        option_labels = {str(label).strip().upper() for label in options}
        final = data.get("final") or {}
        option_rows = final.get("option_explanations") or []
        key_answer = normalize_answer(data.get("answer"), option_labels)
        ai_answer = normalize_answer(final.get("ai_answer"), option_labels)
        is_passed, flag_reasons = question_validation(data, key_answer, ai_answer)

        stats["questions_total"] += 1
        stats["options_total"] += len(option_rows)
        if is_passed:
            stats["questions_passed_preview"] += 1
        else:
            stats["questions_flagged_preview"] += 1
            for reason in flag_reasons:
                flagged_reason_counter[reason] += 1

        validation_status = str(((data.get("pipeline") or {}).get("validate") or {}).get("validation_status") or "")
        validation_counter[validation_status or "missing"] += 1

        flagged_strong_edges: list[dict[str, Any]] = []

        for row in option_rows:
            label = str(row.get("option") or "").strip().upper()
            if not label:
                continue
            is_key_option = label in key_answer
            grade = str(row.get("evidence_grade") or "").strip()
            status = str(row.get("evidence_status") or "").strip()
            judgement = str(row.get("judgement") or "").strip()
            focus_type = str(row.get("focus_type") or "").strip()
            cards = row.get("evidence_cards") or []
            grade_counter[grade or "missing"] += 1

            is_strong = grade in STRONG_GRADES and bool(cards)
            if is_key_option and not is_strong:
                evidence_gaps.append({
                    "question_id": qid,
                    "section": data.get("section", ""),
                    "option": label,
                    "option_text": row.get("option_text") or options.get(label, ""),
                    "evidence_grade": grade,
                    "evidence_status": status,
                    "judgement": judgement,
                    "card_count": len(cards),
                    "question_flagged": not is_passed,
                    "flag_reasons": flag_reasons,
                    "stem": compact(data.get("stem", ""), 160),
                })

            if not is_strong:
                if cards or status in {"indirect", "none"}:
                    weak_signal_rows.append({
                        "question_id": qid,
                        "section": data.get("section", ""),
                        "option": label,
                        "option_text": row.get("option_text") or options.get(label, ""),
                        "is_key_option": is_key_option,
                        "evidence_grade": grade,
                        "evidence_status": status,
                        "card_ids": [c.get("card_id") for c in cards if c.get("card_id")],
                        "question_flagged": not is_passed,
                    })
                continue

            role = "core" if is_key_option else "contrast"
            for card in cards:
                cid = str(card.get("card_id") or "").strip()
                if not cid:
                    continue
                edge = {
                    "question_id": qid,
                    "section": data.get("section", ""),
                    "option": label,
                    "option_text": row.get("option_text") or options.get(label, ""),
                    "role": role,
                    "key_is_correct": is_key_option,
                    "judgement": judgement,
                    "evidence_grade": grade,
                    "evidence_status": status,
                    "focus_type": focus_type,
                    "card_id": cid,
                    "quote": compact(card.get("quote") or card.get("citation") or "", 240),
                    "support_type": str(card.get("support_type") or ""),
                    "relevance": str(card.get("relevance") or ""),
                    "question_flagged": not is_passed,
                }

                if not is_passed:
                    flagged_strong_edges.append(edge)
                    continue

                strong_edges.append(edge)
                seed = seed_by_card.setdefault(cid, {
                    "id": f"SEED-{cid}",
                    "card_id": cid,
                    "card": card_meta_from_evidence(card),
                    "question_ids": [],
                    "core_question_ids": [],
                    "contrast_question_ids": [],
                    "sections": Counter(),
                    "focus_types": Counter(),
                    "evidence_grades": Counter(),
                    "roles": Counter(),
                    "edges": [],
                })
                if qid not in seed["question_ids"]:
                    seed["question_ids"].append(qid)
                if role == "core" and qid not in seed["core_question_ids"]:
                    seed["core_question_ids"].append(qid)
                if role == "contrast" and qid not in seed["contrast_question_ids"]:
                    seed["contrast_question_ids"].append(qid)
                seed["sections"][str(data.get("section", ""))] += 1
                seed["focus_types"][focus_type or "missing"] += 1
                seed["evidence_grades"][grade or "missing"] += 1
                seed["roles"][role] += 1
                seed["edges"].append(edge)

        if not is_passed:
            flagged_questions.append({
                "question_id": qid,
                "section": data.get("section", ""),
                "stem": compact(data.get("stem", ""), 180),
                "key_answer": sorted(key_answer),
                "ai_answer": sorted(ai_answer),
                "flag_reasons": flag_reasons,
                "validation_status": validation_status,
                "needs_teacher_review": bool(final.get("needs_teacher_review")),
                "strong_evidence_edges": flagged_strong_edges[:20],
                "strong_evidence_edge_count": len(flagged_strong_edges),
            })

    seed_points: list[dict[str, Any]] = []
    for seed in seed_by_card.values():
        question_count = len(seed["question_ids"])
        point = {
            "id": seed["id"],
            "card_id": seed["card_id"],
            "seed_title": seed["card"]["knowledge"] or seed["card"]["quote"],
            "card": seed["card"],
            "question_ids": seed["question_ids"],
            "question_count": question_count,
            "core_question_ids": seed["core_question_ids"],
            "core_question_count": len(seed["core_question_ids"]),
            "contrast_question_ids": seed["contrast_question_ids"],
            "contrast_question_count": len(seed["contrast_question_ids"]),
            "sections": dict(sorted(seed["sections"].items())),
            "cross_chapter": len(seed["sections"]) >= 2,
            "focus_type_distribution": dict(seed["focus_types"].most_common()),
            "evidence_grade_distribution": dict(seed["evidence_grades"].most_common()),
            "role_distribution": dict(seed["roles"].most_common()),
            "is_high_frequency_preview": question_count >= 3,
            "sample_edges": seed["edges"][:12],
        }
        seed_points.append(point)

    seed_points.sort(key=lambda p: (-p["question_count"], p["card_id"]))

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_questions_dir": str(QUESTIONS_DIR),
        "source_question_files": len(files),
        "source_summary_total_questions": source_summary.get("total_questions"),
        "note_on_missing_questions": (
            "Source summary reports total_questions=720 while q_*.json files currently available "
            f"are {len(files)}. Preview v1 uses available q_*.json only."
        ),
        "gating_policy": {
            "formal_seed_requires_question_not_flagged": True,
            "flagged_if": [
                "ai_answer differs from key answer",
                "validation_status is present and not passed",
                "final.needs_teacher_review is true",
            ],
            "strong_evidence_grades": sorted(STRONG_GRADES),
            "weak_signals_not_used_for_seed": [
                "indirect_context",
                "none",
                "needs_manual",
                "candidate_card_ids",
                "mixed card_ids",
            ],
        },
        "stats": dict(stats),
        "validation_status_distribution": dict(validation_counter.most_common()),
        "evidence_grade_distribution": dict(grade_counter.most_common()),
        "flagged_reason_distribution": dict(flagged_reason_counter.most_common()),
        "seed_point_count": len(seed_points),
        "high_frequency_seed_count_preview": sum(1 for p in seed_points if p["is_high_frequency_preview"]),
        "strong_edge_count": len(strong_edges),
        "flagged_question_count": len(flagged_questions),
        "evidence_gap_count": len(evidence_gaps),
        "weak_signal_row_count": len(weak_signal_rows),
    }

    write_json(OUT_DIR / "summary.json", summary)
    write_json(OUT_DIR / "seed_points.json", {"items": seed_points})
    write_json(OUT_DIR / "strong_edges.json", {"items": strong_edges})
    write_json(OUT_DIR / "flagged_questions.json", {"items": flagged_questions})
    write_json(OUT_DIR / "evidence_gaps.json", {"items": evidence_gaps})
    write_json(OUT_DIR / "weak_signals.json", {"items": weak_signal_rows})

    top_lines = [
        "# Preview v1 种子考点报告",
        "",
        f"- 生成时间：{summary['generated_at']}",
        f"- 输入 q_*.json：{len(files)} 个",
        f"- source summary total_questions：{source_summary.get('total_questions', '未知')}",
        f"- 正式种子考点：{len(seed_points)} 个",
        f"- 高频种子预览（题目数 >= 3）：{summary['high_frequency_seed_count_preview']} 个",
        f"- 强证据边：{len(strong_edges)} 条",
        f"- 待审题：{len(flagged_questions)} 道",
        f"- 标准答案选项证据缺口：{len(evidence_gaps)} 条",
        "",
        "## 口径",
        "",
        "- 待审题不进入正式种子。",
        "- 正式种子只使用强证据：direct_single、direct_multi、semantic_direct、negative_direct。",
        "- 错误选项强证据进入 contrast 角色，用于后续辨析型考点。",
        "- indirect_context、none、needs_manual、candidate_card_ids、混合 card_ids 只作为弱信号保留。",
        "",
        "## Top 种子考点",
        "",
    ]
    for point in seed_points[:30]:
        title = point["seed_title"] or point["card_id"]
        top_lines.extend([
            f"### {point['card_id']}｜{title}",
            f"- 题目数：{point['question_count']}（core {point['core_question_count']} / contrast {point['contrast_question_count']}）",
            f"- 章节：{', '.join(point['sections'].keys())}",
            f"- 题目：{', '.join(point['question_ids'][:12])}",
            f"- 原文：{point['card']['quote']}",
            "",
        ])
    (OUT_DIR / "report.md").write_text("\n".join(top_lines), encoding="utf-8")

    print("Preview v1 complete")
    print(f"  questions: {len(files)}")
    print(f"  seed points: {len(seed_points)}")
    print(f"  high-frequency seeds: {summary['high_frequency_seed_count_preview']}")
    print(f"  strong edges: {len(strong_edges)}")
    print(f"  flagged questions: {len(flagged_questions)}")
    print(f"  evidence gaps: {len(evidence_gaps)}")
    print(f"  output: {OUT_DIR}")


if __name__ == "__main__":
    main()
