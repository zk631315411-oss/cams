from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evidence_retriever import get_agentic_module, get_run_step1_module, get_runtime

_HERE = Path(__file__).resolve().parent
_PROMPT_PATH = _HERE / "prompts" / "05_reply_reviewer.md"


def review_reply(
    parsed_input: dict[str, Any],
    question_match: dict[str, Any],
    free_answer: dict[str, Any],
    claim_plan: dict[str, Any],
    judge_result: dict[str, Any],
    current_final: dict[str, Any],
) -> dict[str, Any]:
    rt = get_runtime()
    run_step1 = get_run_step1_module()
    agentic = get_agentic_module()
    prompt = _build_prompt(parsed_input, question_match, free_answer, claim_plan, judge_result, current_final)
    raw = run_step1.call_llm(rt.base.client, prompt, max_tokens=4500)
    parsed = agentic.parse_json_object(raw)
    normalized = _normalize_review(parsed, current_final)
    return {
        "prompt_excerpt": prompt[:5000],
        "raw_output": raw,
        "parsed_output": parsed if isinstance(parsed, dict) else None,
        "parse_ok": isinstance(parsed, dict),
        "review": normalized,
    }


def _build_prompt(
    parsed_input: dict[str, Any],
    question_match: dict[str, Any],
    free_answer: dict[str, Any],
    claim_plan: dict[str, Any],
    judge_result: dict[str, Any],
    current_final: dict[str, Any],
) -> str:
    base = _PROMPT_PATH.read_text(encoding="utf-8").strip()
    matched = _matched_question(question_match)
    payload = {
        "input_mode": parsed_input.get("input_mode", "unclear"),
        "student_question": parsed_input.get("student_question", ""),
        "question_context": {
            "matched": bool(matched),
            "question_id": matched.get("id"),
            "stem": matched.get("stem") or parsed_input.get("stem", ""),
            "options": matched.get("options") or parsed_input.get("options", {}),
            "standard_answer": matched.get("answer", ""),
        },
        "student_confusion_from_free_answer": (free_answer.get("parsed_output") or {}).get("student_confusion", ""),
        "claims": claim_plan.get("claims", []),
        "usable_evidence_judgements": _usable_generation_judgements(judge_result),
        "unsupported_claims": _unsupported_claim_summaries(judge_result),
        "current_final": current_final,
        "judge_overall_notes": judge_result.get("judgement", {}).get("overall_notes", ""),
    }
    return f"{base}\n\n本次输入：\n{json.dumps(payload, ensure_ascii=False, indent=2)}"


def _normalize_review(parsed: dict[str, Any] | None, current_final: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(parsed, dict):
        return {
            "review_status": "failed",
            "issues": ["reviewer returned invalid JSON"],
            "review_summary": "reviewer failed to parse output",
            "revised_final": current_final,
        }
    review_status = str(parsed.get("review_status", "")).strip().lower()
    if review_status not in {"pass", "revised", "needs_teacher_review", "failed"}:
        review_status = "failed"
    issues = _as_string_list(parsed.get("issues", []), limit=8)
    summary = _clean_text(str(parsed.get("review_summary", "")).strip())
    revised_final = parsed.get("revised_final")
    if not isinstance(revised_final, dict):
        revised_final = current_final
    return {
        "review_status": review_status,
        "issues": issues,
        "review_summary": summary,
        "revised_final": revised_final,
    }


def _usable_generation_judgements(judge_result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in judge_result.get("judgement", {}).get("judgements", []):
        verdict = item.get("verdict")
        accepted_cards = item.get("accepted_cards", []) or []
        if verdict not in {"direct", "indirect"} or not accepted_cards:
            continue
        rows.append(
            {
                "claim_id": item.get("claim_id", ""),
                "option": item.get("option", ""),
                "role": item.get("role", ""),
                "verdict": verdict,
                "claim": item.get("claim", ""),
                "accepted_cards": accepted_cards[:3],
            }
        )
    return rows


def _unsupported_claim_summaries(judge_result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in judge_result.get("judgement", {}).get("judgements", []):
        verdict = item.get("verdict")
        accepted_cards = item.get("accepted_cards", []) or []
        if verdict in {"direct", "indirect"} and accepted_cards:
            continue
        rows.append(
            {
                "claim_id": item.get("claim_id", ""),
                "option": item.get("option", ""),
                "role": item.get("role", ""),
                "verdict": verdict or "none",
                "instruction": "Do not state this claim as fact. If needed, only say accepted textbook evidence was not found for this direction.",
            }
        )
    return rows


def _as_string_list(value: Any, limit: int = 8) -> list[str]:
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, list):
        items = [str(item) for item in value if str(item).strip()]
    else:
        items = []
    cleaned = [_clean_text(item) for item in items if _clean_text(item)]
    return cleaned[:limit]


def _clean_text(text: str) -> str:
    return " ".join(str(text or "").split()).strip()


def _matched_question(question_match: dict[str, Any]) -> dict[str, Any]:
    best = question_match.get("best") if question_match.get("matched") else None
    if not isinstance(best, dict):
        return {}
    question = best.get("question")
    return question if isinstance(question, dict) else {}
