from __future__ import annotations

import re
from typing import Any


DEFAULT_LIMIT = 3
MAX_ALL = 10

_ROLE_PRIORITY = {
    "support_correct": 100,
    "define_concept": 90,
    "apply_rule": 82,
    "distinguish_concepts": 70,
    "clarify_confusion": 65,
    "exclude_wrong": 60,
    "explain_boundary": 55,
    "needs_context": 20,
}

_SUPPORT_TYPE_PRIORITY = {
    "define": 30,
    "support": 25,
    "clarify": 20,
    "exclude": 18,
}


def select_display_evidence(
    final: dict[str, Any],
    claim_plan: dict[str, Any],
    judge_result: dict[str, Any],
    default_limit: int = DEFAULT_LIMIT,
    max_all: int = MAX_ALL,
) -> dict[str, Any]:
    """Pick display evidence with claim coverage before raw score/order."""
    accepted_by_claim = _collect_accepted_by_claim(judge_result)
    if not accepted_by_claim:
        return {
            "default_cards": [],
            "all_cards": [],
            "default_limit": default_limit,
            "total_count": 0,
        }

    ranked_claims = _rank_claims(claim_plan, judge_result, final)
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    for claim in ranked_claims:
        claim_id = claim.get("claim_id", "")
        cards = accepted_by_claim.get(claim_id, [])
        best = _pick_best_card_for_claim(cards)
        if best and best.get("card_id") not in seen:
            selected.append(best)
            seen.add(best["card_id"])

    rest = [
        card
        for cards in accepted_by_claim.values()
        for card in cards
        if card.get("card_id") not in seen
    ]
    rest.sort(key=_score_card, reverse=True)
    for card in rest:
        cid = card.get("card_id")
        if not cid or cid in seen:
            continue
        selected.append(card)
        seen.add(cid)

    selected = _prefer_numbered_stage_coverage(selected)
    all_cards = _relabel_cards(selected[:max_all])
    return {
        "default_cards": all_cards[:default_limit],
        "all_cards": all_cards,
        "default_limit": default_limit,
        "total_count": len(all_cards),
    }


def _collect_accepted_by_claim(judge_result: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {}
    for item in judge_result.get("judgement", {}).get("judgements", []):
        verdict = item.get("verdict", "")
        if verdict not in {"direct", "indirect"}:
            continue
        claim_id = str(item.get("claim_id", "")).strip()
        if not claim_id:
            continue
        for card in item.get("accepted_cards", []) or []:
            if not isinstance(card, dict):
                continue
            cid = str(card.get("card_id", "")).strip()
            if not cid:
                continue
            rows.setdefault(claim_id, []).append(
                {
                    "card_id": cid,
                    "quote": _clean_quote(card.get("quote", ""), 220),
                    "use": _display_use(item.get("role", ""), card.get("support_type", "")),
                    "claim_id": claim_id,
                    "claim": str(item.get("claim", "") or ""),
                    "role": str(item.get("role", "") or ""),
                    "verdict": verdict,
                    "support_type": str(card.get("support_type", "") or ""),
                    "option": str(item.get("option", "") or ""),
                }
            )
    return rows


def _rank_claims(
    claim_plan: dict[str, Any],
    judge_result: dict[str, Any],
    final: dict[str, Any],
) -> list[dict[str, Any]]:
    by_id = {
        str(item.get("claim_id", "")): item
        for item in judge_result.get("judgement", {}).get("judgements", [])
        if isinstance(item, dict)
    }
    reply_text = " ".join(
        str(final.get(key, "") or "")
        for key in ("student_stuck_point", "reply_to_student", "teacher_notes")
    )
    claims = [claim for claim in claim_plan.get("claims", []) if isinstance(claim, dict)]

    def claim_score(claim: dict[str, Any]) -> tuple[int, int, int]:
        claim_id = str(claim.get("claim_id", "") or "")
        judgement = by_id.get(claim_id, {})
        role = str(claim.get("role", "") or judgement.get("role", "") or "")
        verdict = str(judgement.get("verdict", "") or "")
        accepted_count = len(judgement.get("accepted_cards", []) or [])
        score = _ROLE_PRIORITY.get(role, 10)
        if verdict == "direct":
            score += 40
        elif verdict == "indirect":
            score += 15
        score += min(accepted_count, 3) * 3
        if _claim_is_reflected_in_reply(claim, reply_text):
            score += 20
        if _is_overview_claim(claim):
            score -= 60
        return (score, -_claim_index(claim_id), accepted_count)

    return sorted(claims, key=claim_score, reverse=True)


def _pick_best_card_for_claim(cards: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not cards:
        return None
    return sorted(cards, key=_score_card, reverse=True)[0]


def _score_card(card: dict[str, Any]) -> int:
    score = 0
    if card.get("verdict") == "direct":
        score += 100
    elif card.get("verdict") == "indirect":
        score += 40
    score += _SUPPORT_TYPE_PRIORITY.get(str(card.get("support_type", "")), 0)
    quote = str(card.get("quote", "") or "")
    claim = str(card.get("claim", "") or "")
    if _has_claim_overlap(quote, claim):
        score += 35
    if _looks_like_definition(quote):
        score += 25
    if len(quote) <= 120:
        score += 10
    elif len(quote) > 220:
        score -= 8
    return score


def _claim_is_reflected_in_reply(claim: dict[str, Any], reply_text: str) -> bool:
    claim_text = str(claim.get("claim", "") or "")
    return _has_claim_overlap(reply_text, claim_text, minimum=2)


def _has_claim_overlap(text: str, claim: str, minimum: int = 1) -> bool:
    text_terms = set(_terms(text))
    claim_terms = set(_terms(claim))
    if not text_terms or not claim_terms:
        return False
    return len(text_terms & claim_terms) >= minimum


def _terms(text: str) -> list[str]:
    return [
        term
        for term in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z\-]{2,}", str(text or ""))
        if term.lower() not in {"the", "and", "with", "for", "that", "this"}
    ]


def _looks_like_definition(quote: str) -> bool:
    quote = str(quote or "")
    markers = (
        "阶段一",
        "阶段二",
        "阶段三",
        "定义",
        "指",
        "是",
        "通常认为",
        "通常指",
        "包括",
    )
    return any(marker in quote for marker in markers)


def _is_overview_claim(claim: dict[str, Any]) -> bool:
    text = str(claim.get("claim", "") or "")
    strong_markers = (
        "分别",
        "有哪些",
        "哪几",
        "四种",
        "四个",
        "阶段名称",
    )
    weak_markers = (
        "包括",
        "包含",
        "几种",
        "三种",
        "三个",
        "类型",
        "类别",
    )
    return any(marker in text for marker in strong_markers) or sum(marker in text for marker in weak_markers) >= 2


def _display_use(role: str, support_type: str) -> str:
    role = str(role or "")
    support_type = str(support_type or "")
    if role == "exclude_wrong" or support_type == "exclude":
        return "exclude_option"
    if role in {"clarify_confusion", "distinguish_concepts", "explain_boundary"}:
        return "clarify_confusion"
    if role in {"define_concept", "needs_context"} or support_type == "define":
        return "explain_concept"
    return "support_answer"


def _prefer_numbered_stage_coverage(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stage_cards: dict[int, dict[str, Any]] = {}
    for card in cards:
        stage = _stage_number(card.get("quote", ""))
        if not stage:
            continue
        current = stage_cards.get(stage)
        if current is None or _score_card(card) > _score_card(current):
            stage_cards[stage] = card

    if len(stage_cards) < 3 or not all(stage in stage_cards for stage in (1, 2, 3)):
        return cards

    stage_set = [stage_cards[1], stage_cards[2], stage_cards[3]]
    used = {card.get("card_id") for card in stage_set}
    rest = [card for card in cards if card.get("card_id") not in used]
    return stage_set + rest


def _stage_number(text: Any) -> int | None:
    value = str(text or "")
    match = re.search(r"阶段([一二三四五六七八九十0-9]+)[：:]", value)
    if not match:
        return None
    raw = match.group(1)
    if raw.isdigit():
        return int(raw)
    mapping = {
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    return mapping.get(raw)


def _relabel_cards(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, card in enumerate(cards, 1):
        rows.append(
            {
                "card_id": card.get("card_id", ""),
                "display_label": f"教材原文 {index}",
                "quote": card.get("quote", ""),
                "use": card.get("use", "") or "support_answer",
            }
        )
    return rows


def _claim_index(claim_id: str) -> int:
    match = re.search(r"\d+", claim_id or "")
    return int(match.group(0)) if match else 999


def _compact(text: Any, limit: int) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _clean_quote(text: Any, limit: int) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    match = re.search(r"阶段[一二三四五六七八九十0-9]+[：:]", value)
    if match and match.start() > 0:
        value = value[match.start():].strip()
    return _compact(value, limit)
