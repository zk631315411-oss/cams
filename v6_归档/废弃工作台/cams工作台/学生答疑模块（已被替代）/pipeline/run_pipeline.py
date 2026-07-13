from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import uuid
from pathlib import Path
from typing import Any

from pipeline.evidence_retriever import get_agentic_module, get_run_step1_module, get_runtime, retrieve_evidence
from pipeline.input_parser import parse_student_input
from pipeline.question_matcher import match_question


_MODULE_DIR = Path(__file__).resolve().parents[1]
_DRAFTS_DIR = _MODULE_DIR / "outputs" / "drafts"
_PROMPT_PATH = _MODULE_DIR / "prompts" / "02_generate_reply.md"
_INTERNAL_ID_RE = re.compile(r"\b(?:v\d+s?_N\d+|v\d+_b\d+_N\d+|N\d{4,6})\b")


def run_student_qa_pipeline(text: str, top_k: int = 16, skip_generation: bool = False) -> dict[str, Any]:
    started_at = dt.datetime.now().isoformat(timespec="seconds")
    parsed = parse_student_input(text)
    qmatch = match_question(parsed)
    retrieval = retrieve_evidence(parsed, qmatch, top_k=top_k)

    draft: dict[str, Any] = {
        "draft_id": _new_draft_id(),
        "status": "draft",
        "created_at": started_at,
        "raw_input": text,
        "pipeline": {
            "parse_student_input": parsed,
            "match_question": qmatch,
            "retrieve_evidence": retrieval,
            "generation": {},
            "validation": {},
        },
        "final": _empty_final(),
    }

    if skip_generation:
        draft["status"] = "retrieval_only"
        draft["pipeline"]["generation"] = {"skipped": True}
        draft["final"]["needs_teacher_review"] = True
        draft["final"]["review_reason"] = "LLM generation skipped"
        _save_draft(draft)
        return draft

    generation = _generate_reply(parsed, qmatch, retrieval)
    draft["pipeline"]["generation"] = generation
    final = _sanitize_final(generation.get("parsed_output"), retrieval)
    validation = _validate_final(final, retrieval)
    final["needs_teacher_review"] = bool(final.get("needs_teacher_review") or validation.get("needs_teacher_review"))
    if validation.get("review_reason") and not final.get("review_reason"):
        final["review_reason"] = validation["review_reason"]
    draft["pipeline"]["validation"] = validation
    draft["final"] = final
    if final.get("confidence") == "insufficient" or final.get("needs_teacher_review"):
        draft["status"] = "needs_review"

    _save_draft(draft)
    return draft


def _generate_reply(parsed_input: dict[str, Any], question_match: dict[str, Any], retrieval: dict[str, Any]) -> dict[str, Any]:
    rt = get_runtime()
    run_step1 = get_run_step1_module()
    agentic = get_agentic_module()
    prompt = _build_generation_prompt(parsed_input, question_match, retrieval)
    raw = run_step1.call_llm(rt.base.client, prompt, max_tokens=5000)
    parsed = agentic.parse_json_object(raw)
    return {
        "prompt_excerpt": prompt[:3000],
        "raw_output": raw,
        "parsed_output": parsed if isinstance(parsed, dict) else None,
        "parse_ok": isinstance(parsed, dict),
    }


def _build_generation_prompt(parsed_input: dict[str, Any], question_match: dict[str, Any], retrieval: dict[str, Any]) -> str:
    base_prompt = _PROMPT_PATH.read_text(encoding="utf-8").strip()
    matched_question = _matched_question(question_match)
    question_context = {
        "matched": bool(matched_question),
        "question_id": matched_question.get("id"),
        "stem": matched_question.get("stem") or parsed_input.get("stem", ""),
        "options": matched_question.get("options") or parsed_input.get("options", {}),
        "standard_answer": matched_question.get("answer", ""),
    }
    evidence_cards = [_prompt_card(row, index + 1) for index, row in enumerate(retrieval.get("evidence", [])[:18])]
    payload = {
        "student_question": parsed_input.get("student_question", ""),
        "mentioned_options": parsed_input.get("mentioned_options", []),
        "question_context": question_context,
        "textbook_evidence_cards": evidence_cards,
    }
    return f"{base_prompt}\n\n本次输入：\n{json.dumps(payload, ensure_ascii=False, indent=2)}"


def _prompt_card(row: dict[str, Any], index: int) -> dict[str, Any]:
    quote = row.get("citation") or row.get("knowledge") or row.get("text") or ""
    context = " ".join(str(row.get(key, "") or "") for key in ("context_before", "context_after")).strip()
    return {
        "label": f"教材原文 {index}",
        "card_id": row.get("card_id"),
        "quote": _compact(quote, 260),
        "context": _compact(context, 260),
    }


def _sanitize_final(output: dict[str, Any] | None, retrieval: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(output, dict):
        final = _empty_final()
        final["needs_teacher_review"] = True
        final["review_reason"] = "LLM output was not valid JSON"
        return final

    allowed = {row.get("card_id"): row for row in retrieval.get("evidence", []) if row.get("card_id")}
    evidence_cards = []
    for item in output.get("evidence_cards", []) or []:
        if not isinstance(item, dict):
            continue
        cid = str(item.get("card_id", "")).strip()
        if cid not in allowed:
            continue
        source = allowed[cid]
        quote = str(item.get("quote") or source.get("citation") or source.get("knowledge") or "").strip()
        evidence_cards.append(
            {
                "card_id": cid,
                "display_label": f"教材原文 {len(evidence_cards) + 1}",
                "quote": _strip_internal_ids(_compact(quote, 220)),
                "use": str(item.get("use", "")).strip() or "support_answer",
            }
        )

    final = {
        "student_stuck_point": _clean_display_text(str(output.get("student_stuck_point", "")).strip()),
        "reply_to_student": _clean_display_text(str(output.get("reply_to_student", "")).strip()),
        "teacher_notes": _clean_display_text(str(output.get("teacher_notes", "")).strip()),
        "evidence_cards": evidence_cards,
        "confidence": _normalize_confidence(output.get("confidence")),
        "needs_teacher_review": bool(output.get("needs_teacher_review", False)),
        "review_reason": _clean_display_text(str(output.get("review_reason", "")).strip()),
    }
    if not evidence_cards:
        final["needs_teacher_review"] = True
        final["review_reason"] = final["review_reason"] or "No valid textbook evidence card was cited"
    return final


def _validate_final(final: dict[str, Any], retrieval: dict[str, Any]) -> dict[str, Any]:
    allowed = {row.get("card_id") for row in retrieval.get("evidence", []) if row.get("card_id")}
    cited = [row.get("card_id") for row in final.get("evidence_cards", [])]
    invalid = [cid for cid in cited if cid not in allowed]
    text_blob = "\n".join(str(final.get(key, "")) for key in ("student_stuck_point", "reply_to_student", "teacher_notes"))
    leaks_internal_id = bool(_INTERNAL_ID_RE.search(text_blob))
    needs_review = bool(invalid or leaks_internal_id or not final.get("reply_to_student") or retrieval.get("evidence_count", 0) == 0)
    reasons = []
    if invalid:
        reasons.append(f"invalid cited cards: {','.join(invalid[:5])}")
    if leaks_internal_id:
        reasons.append("internal card id leaked in display text")
    if not final.get("reply_to_student"):
        reasons.append("reply_to_student missing")
    if retrieval.get("evidence_count", 0) == 0:
        reasons.append("no textbook evidence retrieved")

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
    }


def _save_draft(draft: dict[str, Any]) -> Path:
    _DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    path = _DRAFTS_DIR / f"{draft['draft_id']}.json"
    draft["saved_path"] = str(path)
    path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _new_draft_id() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"qa_{stamp}_{uuid.uuid4().hex[:8]}"


def _normalize_confidence(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if text in {"high", "medium", "low", "insufficient"} else "low"


def _strip_internal_ids(text: str) -> str:
    return _INTERNAL_ID_RE.sub("教材原文", text or "")


def _clean_display_text(text: str) -> str:
    text = _strip_internal_ids(text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"(?m)^\s*[-*]\s+", "", text)
    return text.strip()


def _compact(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one student-QA draft pipeline.")
    parser.add_argument("text", nargs="?", help="Raw pasted student QA text.")
    parser.add_argument("--file", "-f", help="Read raw input from a UTF-8 text file.")
    parser.add_argument("--top-k", type=int, default=16, help="Candidate cards per retrieval target.")
    parser.add_argument("--skip-generation", action="store_true", help="Only parse/match/retrieve and save a draft.")
    args = parser.parse_args()

    if args.file:
        raw_text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        raw_text = args.text
    else:
        raw_text = input("Paste student QA text: ").strip()

    draft = run_student_qa_pipeline(raw_text, top_k=args.top_k, skip_generation=args.skip_generation)
    print(json.dumps(_cli_summary(draft), ensure_ascii=False, indent=2))


def _cli_summary(draft: dict[str, Any]) -> dict[str, Any]:
    match = draft.get("pipeline", {}).get("match_question", {})
    best = match.get("best") if match.get("matched") else None
    question = best.get("question", {}) if isinstance(best, dict) else {}
    return {
        "draft_id": draft.get("draft_id"),
        "status": draft.get("status"),
        "saved_path": draft.get("saved_path"),
        "matched_question_id": question.get("id"),
        "matched_score": best.get("score") if isinstance(best, dict) else None,
        "evidence_count": draft.get("pipeline", {}).get("retrieve_evidence", {}).get("evidence_count"),
        "confidence": draft.get("final", {}).get("confidence"),
        "needs_teacher_review": draft.get("final", {}).get("needs_teacher_review"),
    }


if __name__ == "__main__":
    main()
