from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pipeline.evidence_retriever import get_agentic_module, get_run_step1_module, get_runtime


_MODULE_DIR = Path(__file__).resolve().parents[1]
_PROMPT_PATH = _MODULE_DIR / "prompts" / "02_claim_planner.md"


def plan_claims(
    parsed_input: dict[str, Any],
    question_match: dict[str, Any],
    free_answer: dict[str, Any],
    max_claims: int = 12,
) -> dict[str, Any]:
    rt = get_runtime()
    run_step1 = get_run_step1_module()
    agentic = get_agentic_module()
    prompt = _build_prompt(parsed_input, question_match, free_answer, max_claims)
    raw = run_step1.call_llm(rt.base.client, prompt, max_tokens=4200)
    parsed = agentic.parse_json_object(raw)
    normalized = _normalize_plan(parsed, parsed_input, question_match, free_answer, max_claims)
    return {
        "prompt_excerpt": prompt[:3500],
        "raw_output": raw,
        "parsed_output": parsed if isinstance(parsed, dict) else None,
        "plan": normalized,
        "parse_ok": isinstance(parsed, dict),
    }


def _build_prompt(
    parsed_input: dict[str, Any],
    question_match: dict[str, Any],
    free_answer: dict[str, Any],
    max_claims: int,
) -> str:
    base = _PROMPT_PATH.read_text(encoding="utf-8").strip()
    matched = _matched_question(question_match)
    payload = {
        "max_claims": max_claims,
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
        "free_answer": free_answer.get("parsed_output") or {},
    }
    return f"{base}\n\n本次输入：\n{json.dumps(payload, ensure_ascii=False, indent=2)}"


def _normalize_plan(
    parsed: dict[str, Any] | None,
    parsed_input: dict[str, Any],
    question_match: dict[str, Any],
    free_answer: dict[str, Any],
    max_claims: int,
) -> dict[str, Any]:
    matched = _matched_question(question_match)
    input_mode = str(parsed_input.get("input_mode", "unclear")).strip() or "unclear"
    is_question_mode = input_mode == "full_question"
    options = matched.get("options") or parsed_input.get("options", {}) or {}
    answer_labels = _answer_labels(matched.get("answer", ""), set(options))
    mentioned = [label for label in parsed_input.get("mentioned_options", []) if label in options]
    raw_claims = parsed.get("claims", []) if isinstance(parsed, dict) else []
    if not isinstance(raw_claims, list):
        raw_claims = []

    claims: list[dict[str, Any]] = []
    for index, item in enumerate(raw_claims[:max_claims], start=1):
        if not isinstance(item, dict):
            continue
        option = str(item.get("option", "")).strip().upper()
        role = str(item.get("role", "needs_context")).strip()
        if role not in {
            "support_correct",
            "exclude_wrong",
            "clarify_confusion",
            "define_concept",
            "distinguish_concepts",
            "apply_rule",
            "explain_boundary",
            "needs_context",
        }:
            role = "needs_context"
        if not is_question_mode and role in {"support_correct", "exclude_wrong"}:
            role = "clarify_confusion" if option else "define_concept"
        if not is_question_mode and option not in options:
            option = ""
        claim = str(item.get("claim", "")).strip()
        if not claim:
            continue
        queries = _string_list(item.get("search_queries", []))[:6]
        must_terms = _string_list(item.get("must_terms", []))[:10]
        success = str(item.get("success_criteria", "")).strip()
        claims.append(
            {
                "claim_id": str(item.get("claim_id") or f"C{index}").strip(),
                "option": option,
                "role": role,
                "claim": claim,
                "search_queries": queries,
                "must_terms": must_terms,
                "success_criteria": success,
            }
        )

    if is_question_mode:
        existing_keys = {(c.get("option"), c.get("role")) for c in claims}
        for label in answer_labels:
            if (label, "support_correct") not in existing_keys:
                claims.append(_fallback_claim(label, "support_correct", options.get(label, ""), parsed_input.get("student_question", "")))
        for label in mentioned:
            if label not in answer_labels and (label, "exclude_wrong") not in existing_keys:
                claims.append(_fallback_claim(label, "exclude_wrong", options.get(label, ""), parsed_input.get("student_question", "")))
    elif not claims:
        claims.append(_fallback_concept_claim(parsed_input, free_answer=free_answer))

    for index, claim in enumerate(claims[:max_claims], start=1):
        claim["claim_id"] = f"C{index}"
    return {
        "input_mode": input_mode,
        "student_confusion": (parsed or {}).get("student_confusion", parsed_input.get("student_question", "")) if isinstance(parsed, dict) else parsed_input.get("student_question", ""),
        "claims": claims[:max_claims],
        "max_claims": max_claims,
    }


def _fallback_concept_claim(parsed_input: dict[str, Any], free_answer: dict[str, Any]) -> dict[str, Any]:
    parsed_free = free_answer.get("parsed_output") if isinstance(free_answer, dict) else {}
    concepts = _string_list((parsed_free or {}).get("core_concepts", []))
    question = parsed_input.get("student_question", "") or parsed_input.get("raw_text", "")
    base_text = " ".join(concepts[:4] + [question]).strip()
    return {
        "claim_id": "",
        "option": "",
        "role": "define_concept",
        "claim": f"说明学生提问涉及的教材概念和判断边界：{question}",
        "search_queries": _dedupe([base_text, question] + _string_list((parsed_free or {}).get("search_directions", [])))[:6],
        "must_terms": _simple_terms(base_text or question),
        "success_criteria": "找到能解释学生提问涉及概念、适用场景或判断边界的教材原文。",
    }


def _fallback_claim(option: str, role: str, option_text: str, student_question: str) -> dict[str, Any]:
    action = "说明该正确选项为什么成立" if role == "support_correct" else "说明该错误选项为什么不能成立"
    return {
        "claim_id": "",
        "option": option,
        "role": role,
        "claim": f"{action}：{option}. {option_text}",
        "search_queries": [f"{option_text} {student_question}", option_text],
        "must_terms": _simple_terms(option_text),
        "success_criteria": "找到能直接支撑或排除该选项的教材原文",
    }


def _simple_terms(text: str) -> list[str]:
    tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_/-]{1,}", text or "")
    seen: set[str] = set()
    result = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            result.append(token)
    return result[:8]


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    rows: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        rows.append(text)
    return rows


def _answer_labels(answer: str, valid_labels: set[str]) -> list[str]:
    labels = []
    for label in re.findall(r"[A-K]", str(answer or "").upper()):
        if label in valid_labels and label not in labels:
            labels.append(label)
    return labels


def _matched_question(question_match: dict[str, Any]) -> dict[str, Any]:
    best = question_match.get("best") if question_match.get("matched") else None
    if not isinstance(best, dict):
        return {}
    question = best.get("question")
    return question if isinstance(question, dict) else {}
