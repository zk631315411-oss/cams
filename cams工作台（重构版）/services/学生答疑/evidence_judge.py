from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evidence_retriever import get_agentic_module, get_run_step1_module, get_runtime

_HERE = Path(__file__).resolve().parent
_PROMPT_PATH = _HERE / "prompts" / "03_evidence_judge.md"


def judge_evidence(claim_plan: dict[str, Any], retrieval: dict[str, Any]) -> dict[str, Any]:
    rt = get_runtime()
    run_step1 = get_run_step1_module()
    agentic = get_agentic_module()
    prompt = _build_prompt(claim_plan, retrieval)
    raw = run_step1.call_llm(rt.base.client, prompt, max_tokens=7000)
    parsed = agentic.parse_json_object(raw)
    normalized = _normalize_judgements(parsed, claim_plan, retrieval)
    return {
        "prompt_excerpt": prompt[:5000],
        "raw_output": raw,
        "parsed_output": parsed if isinstance(parsed, dict) else None,
        "judgement": normalized,
        "parse_ok": isinstance(parsed, dict),
    }


def accepted_evidence_cards(judge_result: dict[str, Any]) -> list[dict[str, Any]]:
    judgement = judge_result.get("judgement", {})
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for item in judgement.get("judgements", []):
        for card in item.get("accepted_cards", []):
            cid = card.get("card_id")
            if cid and cid not in seen:
                seen.add(cid)
                rows.append(card)
    return rows


def _build_prompt(claim_plan: dict[str, Any], retrieval: dict[str, Any]) -> str:
    base = _PROMPT_PATH.read_text(encoding="utf-8").strip()
    payload = {
        "claims": claim_plan.get("claims", []),
        "candidate_cards_by_claim": {
            claim_id: [_prompt_card(row, index + 1) for index, row in enumerate(rows[:12])]
            for claim_id, rows in retrieval.get("candidates_by_claim", {}).items()
        },
    }
    return f"{base}\n\n本次输入：\n{json.dumps(payload, ensure_ascii=False, indent=2)}"


def _prompt_card(row: dict[str, Any], index: int) -> dict[str, Any]:
    quote = row.get("citation") or row.get("knowledge") or row.get("text") or ""
    context = " ".join(str(row.get(key, "") or "") for key in ("context_before", "context_after")).strip()
    return {
        "label": f"候选原文 {index}",
        "card_id": row.get("card_id"),
        "quote": _compact(quote, 260),
        "context": _compact(context, 240),
        "score": row.get("score"),
        "source": row.get("source", ""),
    }


def _normalize_judgements(parsed: dict[str, Any] | None, claim_plan: dict[str, Any], retrieval: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        row.get("card_id"): row
        for rows in retrieval.get("candidates_by_claim", {}).values()
        for row in rows
        if row.get("card_id")
    }
    raw_items = parsed.get("judgements", []) if isinstance(parsed, dict) else []
    if not isinstance(raw_items, list):
        raw_items = []
    by_claim = {str(item.get("claim_id", "")): item for item in raw_items if isinstance(item, dict)}
    rows: list[dict[str, Any]] = []
    for claim in claim_plan.get("claims", []):
        claim_id = claim.get("claim_id", "")
        raw = by_claim.get(claim_id, {})
        verdict = str(raw.get("verdict", "none")).strip()
        if verdict not in {"direct", "indirect", "none", "conflict", "needs_review"}:
            verdict = "needs_review"
        accepted = []
        for card in raw.get("accepted_cards", []) or []:
            if not isinstance(card, dict):
                continue
            cid = str(card.get("card_id", "")).strip()
            if cid not in allowed:
                continue
            source = allowed[cid]
            accepted.append(
                {
                    "claim_id": claim_id,
                    "card_id": cid,
                    "quote": str(card.get("quote") or source.get("citation") or source.get("knowledge") or "").strip(),
                    "support_type": str(card.get("support_type", "")).strip() or "support",
                    "reason": str(card.get("reason", "")).strip(),
                    "claim_role": claim.get("role", ""),
                    "option": claim.get("option", ""),
                }
            )
        needs_review = bool(raw.get("needs_teacher_review", False)) or verdict in {"indirect", "none", "conflict", "needs_review"}
        reason = str(raw.get("review_reason", "")).strip()
        if needs_review and not reason:
            reason = f"claim {claim_id} evidence verdict is {verdict}"
        rows.append(
            {
                "claim_id": claim_id,
                "claim": claim.get("claim", ""),
                "option": claim.get("option", ""),
                "role": claim.get("role", ""),
                "verdict": verdict,
                "accepted_cards": accepted,
                "rejected_card_ids": [cid for cid in raw.get("rejected_card_ids", []) or [] if isinstance(cid, str)],
                "needs_teacher_review": needs_review,
                "review_reason": reason,
            }
        )
    return {
        "judgements": rows,
        "overall_notes": str((parsed or {}).get("overall_notes", "")).strip() if isinstance(parsed, dict) else "",
        "allowed_card_count": len(allowed),
        "needs_teacher_review": any(row.get("needs_teacher_review") for row in rows),
    }


def _compact(text: str, limit: int) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"
