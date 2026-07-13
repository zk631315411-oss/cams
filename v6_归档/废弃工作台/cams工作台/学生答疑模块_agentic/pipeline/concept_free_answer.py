from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.evidence_retriever import get_agentic_module, get_run_step1_module, get_runtime


_MODULE_DIR = Path(__file__).resolve().parents[1]
_PROMPT_PATH = _MODULE_DIR / "prompts" / "01_concept_free_answer.md"


def run_concept_free_answer(parsed_input: dict[str, Any], question_match: dict[str, Any]) -> dict[str, Any]:
    rt = get_runtime()
    run_step1 = get_run_step1_module()
    agentic = get_agentic_module()
    prompt = _build_prompt(parsed_input, question_match)
    raw = run_step1.call_llm(rt.base.client, prompt, max_tokens=3500)
    parsed = agentic.parse_json_object(raw)
    return {
        "prompt_excerpt": prompt[:3000],
        "raw_output": raw,
        "parsed_output": parsed if isinstance(parsed, dict) else None,
        "parse_ok": isinstance(parsed, dict),
        "free_answer_mode": "concept",
    }


def _build_prompt(parsed_input: dict[str, Any], question_match: dict[str, Any]) -> str:
    base = _PROMPT_PATH.read_text(encoding="utf-8").strip()
    matched = _matched_question(question_match)
    payload = {
        "input_mode": parsed_input.get("input_mode", "concept_only"),
        "raw_text": parsed_input.get("raw_text", ""),
        "student_question": parsed_input.get("student_question", ""),
        "mentioned_options": parsed_input.get("mentioned_options", []),
        "question_context": {
            "matched": bool(matched),
            "question_id": matched.get("id"),
            "stem": matched.get("stem") or parsed_input.get("stem", ""),
            "options": matched.get("options") or parsed_input.get("options", {}),
            "standard_answer": matched.get("answer", ""),
        },
    }
    return f"{base}\n\n本次输入：\n{json.dumps(payload, ensure_ascii=False, indent=2)}"


def _matched_question(question_match: dict[str, Any]) -> dict[str, Any]:
    best = question_match.get("best") if question_match.get("matched") else None
    if not isinstance(best, dict):
        return {}
    question = best.get("question")
    return question if isinstance(question, dict) else {}
