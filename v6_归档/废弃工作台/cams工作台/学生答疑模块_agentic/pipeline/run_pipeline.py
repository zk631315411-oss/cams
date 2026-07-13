from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import uuid
from pathlib import Path
from typing import Any

from pipeline.claim_planner import plan_claims
from pipeline.concept_free_answer import run_concept_free_answer
from pipeline.evidence_judge import judge_evidence
from pipeline.evidence_selector import select_display_evidence
from pipeline.evidence_retriever import get_agentic_module, get_run_step1_module, get_runtime, retrieve_evidence_for_claims
from pipeline.free_answer import run_free_answer
from pipeline.input_parser import parse_student_input
from pipeline.reply_reviewer import review_reply
from pipeline.question_matcher import match_question


_MODULE_DIR = Path(__file__).resolve().parents[1]
_DRAFTS_DIR = _MODULE_DIR / "outputs" / "drafts"
_PROMPT_PATH = _MODULE_DIR / "prompts" / "04_generate_reply.md"
_INTERNAL_ID_RE = re.compile(r"\b(?:v\d+s?_N\d+|v\d+_b\d+_N\d+|N\d{4,6})\b")


def run_student_qa_pipeline(
    text: str,
    top_k: int = 12,
    max_claims: int = 12,
    skip_generation: bool = False,
) -> dict[str, Any]:
    started_at = dt.datetime.now().isoformat(timespec="seconds")
    parsed = parse_student_input(text)
    qmatch = match_question(parsed)
    input_mode = parsed.get("input_mode", "unclear")

    draft: dict[str, Any] = {
        "draft_id": _new_draft_id(),
        "status": "draft",
        "created_at": started_at,
        "raw_input": text,
        "pipeline_version": "student_qa_agentic_v2",
        "input_mode": input_mode,
        "pipeline": {
            "input_mode": input_mode,
            "parse_student_input": parsed,
            "match_question": qmatch,
            "free_answer": {},
            "claim_planner": {},
            "retrieve_evidence": {},
            "evidence_judge": {},
            "generation": {},
            "reply_review": {},
            "validation": {},
        },
        "final": _empty_final(),
    }

    try:
        if input_mode == "full_question":
            free = run_free_answer(parsed, qmatch)
        else:
            free = run_concept_free_answer(parsed, qmatch)
        draft["pipeline"]["free_answer"] = free
        plan_result = plan_claims(parsed, qmatch, free, max_claims=max_claims)
        draft["pipeline"]["claim_planner"] = plan_result
        claim_plan = plan_result.get("plan", {})
        retrieval = retrieve_evidence_for_claims(parsed, qmatch, claim_plan, top_k=top_k)
        draft["pipeline"]["retrieve_evidence"] = retrieval

        if skip_generation:
            draft["status"] = "retrieval_only"
            draft["final"]["review_reason"] = "LLM generation skipped after retrieval"
            _save_draft(draft)
            return draft

        judge = judge_evidence(claim_plan, retrieval)
        draft["pipeline"]["evidence_judge"] = judge
        generation = _generate_reply(parsed, qmatch, free, claim_plan, judge)
        draft["pipeline"]["generation"] = generation
        final = _sanitize_final(generation.get("parsed_output"), judge)
        sanitize_needs_review = bool(final.pop("_sanitize_needs_teacher_review", False))
        sanitize_review_reason = str(final.pop("_sanitize_review_reason", "")).strip()
        model_needs_review = bool(final.pop("_model_needs_teacher_review", False))
        model_review_reason = str(final.pop("_model_review_reason", "")).strip()
        validation = _validate_final(final, judge)
        review_policy = _review_policy(judge)
        reply_review = review_reply(parsed, qmatch, free, claim_plan, judge, final)
        draft["pipeline"]["reply_review"] = reply_review
        final = _apply_reply_review(final, reply_review.get("review", {}), judge)
        final = _apply_evidence_selection(final, claim_plan, judge)
        validation = _validate_final(final, judge)
        review_policy = _review_policy(judge)
        final["needs_teacher_review"] = bool(
            sanitize_needs_review
            or validation.get("needs_teacher_review")
            or review_policy.get("needs_teacher_review")
        )
        review_reasons = [
            sanitize_review_reason,
            validation.get("review_reason", ""),
            review_policy.get("review_reason", ""),
        ]
        final["review_reason"] = "; ".join(reason for reason in review_reasons if reason)
        review_advisories = list(review_policy.get("advisories", []))
        if model_needs_review or model_review_reason:
            review_advisories.append(
                "generation_model: "
                + (model_review_reason or "model suggested teacher review, but no hard local review reason was found")
            )
        final["review_advisories"] = review_advisories[:10]
        draft["pipeline"]["validation"] = validation
        draft["pipeline"]["review_policy"] = review_policy
        draft["final"] = final
        if final.get("confidence") == "insufficient" or final.get("needs_teacher_review"):
            draft["status"] = "needs_review"
    except Exception as exc:
        draft["status"] = "failed"
        draft["pipeline"]["error"] = {"type": type(exc).__name__, "message": str(exc)}
        draft["final"] = _empty_final()
        draft["final"]["review_reason"] = f"agentic pipeline failed: {exc}"

    _save_draft(draft)
    return draft


def _generate_reply(
    parsed_input: dict[str, Any],
    question_match: dict[str, Any],
    free_answer: dict[str, Any],
    claim_plan: dict[str, Any],
    judge_result: dict[str, Any],
) -> dict[str, Any]:
    rt = get_runtime()
    run_step1 = get_run_step1_module()
    agentic = get_agentic_module()
    prompt = _build_generation_prompt(parsed_input, question_match, free_answer, claim_plan, judge_result)
    raw = run_step1.call_llm(rt.base.client, prompt, max_tokens=6000)
    parsed = agentic.parse_json_object(raw)
    return {
        "prompt_excerpt": prompt[:4500],
        "raw_output": raw,
        "parsed_output": parsed if isinstance(parsed, dict) else None,
        "parse_ok": isinstance(parsed, dict),
    }


def _build_generation_prompt(
    parsed_input: dict[str, Any],
    question_match: dict[str, Any],
    free_answer: dict[str, Any],
    claim_plan: dict[str, Any],
    judge_result: dict[str, Any],
) -> str:
    base = _PROMPT_PATH.read_text(encoding="utf-8").strip()
    matched = _matched_question(question_match)
    payload = {
        "input_mode": parsed_input.get("input_mode", "unclear"),
        "student_question": parsed_input.get("student_question", ""),
        "mentioned_options": parsed_input.get("mentioned_options", []),
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
        "judge_overall_notes": judge_result.get("judgement", {}).get("overall_notes", ""),
    }
    return f"{base}\n\n本次输入：\n{json.dumps(payload, ensure_ascii=False, indent=2)}"


def _sanitize_final(output: dict[str, Any] | None, judge_result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(output, dict):
        final = _empty_final()
        final["needs_teacher_review"] = False
        final["_sanitize_needs_teacher_review"] = True
        final["_sanitize_review_reason"] = "LLM output was not valid JSON"
        return final

    allowed = _accepted_card_map(judge_result)
    evidence_cards = []
    for item in output.get("evidence_cards", []) or []:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("card_id", "")).strip()
        if cid not in allowed:
            continue
        source = allowed[cid]
        quote = str(item.get("quote") or source.get("quote") or "").strip()
        evidence_cards.append(
            {
                "card_id": cid,
                "display_label": f"教材原文 {len(evidence_cards) + 1}",
                "quote": _clean_display_text(_compact(quote, 220)),
                "use": str(item.get("use", "")).strip() or "support_answer",
            }
        )

    final = {
        "student_stuck_point": _clean_display_text(str(output.get("student_stuck_point", "")).strip()),
        "reply_to_student": _clean_display_text(str(output.get("reply_to_student", "")).strip()),
        "teacher_notes": _clean_display_text(str(output.get("teacher_notes", "")).strip()),
        "evidence_cards": evidence_cards,
        "confidence": _normalize_confidence(output.get("confidence")),
        "needs_teacher_review": False,
        "review_reason": "",
        "_model_needs_teacher_review": bool(output.get("needs_teacher_review", False)),
        "_model_review_reason": _clean_display_text(str(output.get("review_reason", "")).strip()),
        "_sanitize_needs_teacher_review": False,
        "_sanitize_review_reason": "",
    }
    if not evidence_cards:
        final["_sanitize_needs_teacher_review"] = True
        final["_sanitize_review_reason"] = "No accepted textbook evidence card was cited"
    return final


def _apply_reply_review(final: dict[str, Any], review: dict[str, Any], judge_result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(review, dict):
        return final
    status = str(review.get("review_status", "")).strip().lower()
    revised = review.get("revised_final")
    if status == "revised" and isinstance(revised, dict):
        merged = dict(final)
        for key in ("student_stuck_point", "reply_to_student", "teacher_notes", "confidence", "needs_teacher_review", "review_reason"):
            if key in revised:
                value = revised.get(key, merged.get(key))
                if key in {"student_stuck_point", "reply_to_student", "teacher_notes", "review_reason"}:
                    value = _clean_display_text(str(value or ""))
                merged[key] = value
        if "evidence_cards" in revised:
            merged["evidence_cards"] = _sanitize_review_evidence_cards(revised.get("evidence_cards"), judge_result)
            if not merged["evidence_cards"]:
                merged["evidence_cards"] = final.get("evidence_cards", [])[:3]
        else:
            merged["evidence_cards"] = (merged.get("evidence_cards", []) or [])[:3]
        merged["review_advisories"] = list(merged.get("review_advisories", []))
        merged["review_advisories"].append("reply_reviewer: revised")
        return merged
    if status == "needs_teacher_review":
        merged = dict(final)
        merged["needs_teacher_review"] = True
        reason = str(review.get("review_summary", "")).strip() or "reply reviewer requested teacher review"
        merged["review_reason"] = "; ".join(part for part in [str(merged.get("review_reason", "")).strip(), reason] if part)
        merged["review_advisories"] = list(merged.get("review_advisories", []))
        merged["review_advisories"].append("reply_reviewer: needs_teacher_review")
        return merged
    if status == "pass":
        merged = dict(final)
        merged["review_advisories"] = list(merged.get("review_advisories", []))
        merged["review_advisories"].append("reply_reviewer: pass")
        return merged
    return final


def _apply_evidence_selection(
    final: dict[str, Any],
    claim_plan: dict[str, Any],
    judge_result: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(final)
    selection = select_display_evidence(merged, claim_plan, judge_result)
    merged["evidence_cards"] = selection["default_cards"]
    merged["evidence_cards_all"] = selection["all_cards"]
    merged["evidence_default_limit"] = selection["default_limit"]
    merged["evidence_total_count"] = selection["total_count"]
    return merged


def _sanitize_review_evidence_cards(cards: Any, judge_result: dict[str, Any]) -> list[dict[str, Any]]:
    allowed = _accepted_card_map(judge_result)
    rows: list[dict[str, Any]] = []
    if not isinstance(cards, list):
        return rows
    for item in cards:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("card_id", "")).strip()
        if cid not in allowed:
            continue
        source = allowed[cid]
        quote = str(item.get("quote") or source.get("quote") or "").strip()
        rows.append(
            {
                "card_id": cid,
                "display_label": f"教材原文 {len(rows) + 1}",
                "quote": _clean_display_text(_compact(quote, 220)),
                "use": str(item.get("use", "")).strip() or "support_answer",
            }
        )
    return rows


def _validate_final(final: dict[str, Any], judge_result: dict[str, Any]) -> dict[str, Any]:
    allowed = set(_accepted_card_map(judge_result))
    cited = [row.get("card_id") for row in final.get("evidence_cards", [])]
    invalid = [cid for cid in cited if cid not in allowed]
    text_blob = "\n".join(str(final.get(key, "")) for key in ("student_stuck_point", "reply_to_student", "teacher_notes"))
    leaks_internal_id = bool(_INTERNAL_ID_RE.search(text_blob))
    needs_review = bool(invalid or leaks_internal_id or not final.get("reply_to_student") or not cited or not allowed)
    reasons = []
    if invalid:
        reasons.append(f"invalid cited cards: {','.join(invalid[:5])}")
    if leaks_internal_id:
        reasons.append("internal card id leaked in display text")
    if not final.get("reply_to_student"):
        reasons.append("reply_to_student missing")
    if not cited:
        reasons.append("no accepted textbook evidence card was cited")
    if not allowed:
        reasons.append("no accepted textbook evidence")
    return {
        "allowed_card_count": len(allowed),
        "cited_card_count": len(cited),
        "invalid_citations": invalid,
        "leaks_internal_id": leaks_internal_id,
        "uses_historical_qa": False,
        "uses_question_explanation": False,
        "needs_teacher_review": needs_review,
        "review_reason": "; ".join(reasons),
    }


def _accepted_card_map(judge_result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for item in judge_result.get("judgement", {}).get("judgements", []):
        if item.get("verdict") not in {"direct", "indirect"}:
            continue
        for card in item.get("accepted_cards", []):
            cid = card.get("card_id")
            if cid:
                rows.setdefault(cid, card)
    return rows


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
                "claim": item.get("claim", ""),
                "verdict": verdict,
                "accepted_cards": accepted_cards,
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


def _judge_review_reason(judge_result: dict[str, Any]) -> str:
    reasons = []
    for row in judge_result.get("judgement", {}).get("judgements", []):
        if row.get("needs_teacher_review") and row.get("review_reason"):
            reasons.append(f"{row.get('claim_id')}: {row.get('review_reason')}")
    return "; ".join(reasons[:6])


def _review_policy(judge_result: dict[str, Any]) -> dict[str, Any]:
    hard_reasons: list[str] = []
    advisories: list[str] = []
    direct_or_indirect = {"direct", "indirect"}
    concept_roles = {"define_concept", "distinguish_concepts", "apply_rule", "explain_boundary", "needs_context"}
    for row in judge_result.get("judgement", {}).get("judgements", []):
        role = row.get("role", "")
        verdict = row.get("verdict", "")
        option = row.get("option", "")
        claim_id = row.get("claim_id", "")
        reason = row.get("review_reason", "") or f"claim {claim_id} evidence verdict is {verdict}"
        is_core = role == "support_correct"
        is_student_asked_exclusion = role in {"exclude_wrong", "clarify_confusion"} and option

        if is_core and verdict not in direct_or_indirect:
            hard_reasons.append(f"{claim_id}: correct-option evidence insufficient ({verdict})")
        elif is_core and verdict == "indirect":
            advisories.append(f"{claim_id}: correct-option evidence is indirect; teacher may review wording")
        elif is_student_asked_exclusion and verdict in {"none", "conflict", "needs_review"}:
            advisories.append(f"{claim_id}: exclusion evidence weak ({verdict}); {reason}")
        elif is_student_asked_exclusion and verdict == "indirect":
            advisories.append(f"{claim_id}: exclusion evidence is indirect; keep wording cautious")
        elif role in concept_roles and verdict not in direct_or_indirect:
            advisories.append(f"{claim_id}: concept evidence weak ({verdict}); {reason}")
        elif row.get("needs_teacher_review") and verdict not in direct_or_indirect:
            advisories.append(f"{claim_id}: {reason}")

    return {
        "needs_teacher_review": bool(hard_reasons),
        "review_reason": "; ".join(hard_reasons),
        "advisories": advisories[:8],
    }


def _matched_question(question_match: dict[str, Any]) -> dict[str, Any]:
    best = question_match.get("best") if question_match.get("matched") else None
    if not isinstance(best, dict):
        return {}
    question = best.get("question")
    return question if isinstance(question, dict) else {}


def _empty_final() -> dict[str, Any]:
    return {
        "student_stuck_point": "",
        "reply_to_student": "",
        "teacher_notes": "",
        "evidence_cards": [],
        "confidence": "insufficient",
        "needs_teacher_review": True,
        "review_reason": "",
        "review_advisories": [],
    }


def _save_draft(draft: dict[str, Any]) -> Path:
    _DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    path = _DRAFTS_DIR / f"{draft['draft_id']}.json"
    draft["saved_path"] = str(path)
    path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _new_draft_id() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"qa_agentic_{stamp}_{uuid.uuid4().hex[:8]}"


def _normalize_confidence(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if text in {"high", "medium", "low", "insufficient"} else "low"


def _strip_internal_ids(text: str) -> str:
    return _INTERNAL_ID_RE.sub("教材原文", text or "")


def _clean_display_text(text: str) -> str:
    text = _strip_internal_ids(text)
    text = re.sub(r"\bC\d+\s*[：:、，,]?\s*", "", text)
    text = re.sub(r"\bclaim\s*\d*\s*[：:、，,]?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(?:verdict|direct|indirect|none|conflict|needs_review)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"(?m)^\s*[-*]\s+", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _compact(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one agentic student-QA draft pipeline.")
    parser.add_argument("text", nargs="?", help="Raw pasted student QA text.")
    parser.add_argument("--file", "-f", help="Read raw input from a UTF-8 text file.")
    parser.add_argument("--top-k", type=int, default=12, help="Candidate cards per claim.")
    parser.add_argument("--max-claims", type=int, default=12, help="Maximum claims from planner.")
    parser.add_argument("--skip-generation", action="store_true", help="Run through retrieval and save a draft.")
    args = parser.parse_args()

    if args.file:
        raw_text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        raw_text = args.text
    else:
        raw_text = input("Paste student QA text: ").strip()

    draft = run_student_qa_pipeline(raw_text, top_k=args.top_k, max_claims=args.max_claims, skip_generation=args.skip_generation)
    print(json.dumps(_cli_summary(draft), ensure_ascii=False, indent=2))


def _cli_summary(draft: dict[str, Any]) -> dict[str, Any]:
    match = draft.get("pipeline", {}).get("match_question", {})
    best = match.get("best") if match.get("matched") else None
    question = best.get("question", {}) if isinstance(best, dict) else {}
    return {
        "draft_id": draft.get("draft_id"),
        "status": draft.get("status"),
        "input_mode": draft.get("input_mode") or draft.get("pipeline", {}).get("input_mode"),
        "saved_path": draft.get("saved_path"),
        "matched_question_id": question.get("id"),
        "matched_score": best.get("score") if isinstance(best, dict) else None,
        "claim_count": len(draft.get("pipeline", {}).get("claim_planner", {}).get("plan", {}).get("claims", [])),
        "evidence_count": draft.get("pipeline", {}).get("retrieve_evidence", {}).get("evidence_count"),
        "confidence": draft.get("final", {}).get("confidence"),
        "needs_teacher_review": draft.get("final", {}).get("needs_teacher_review"),
    }


if __name__ == "__main__":
    main()
