from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


_WORKBENCH_DIR = Path(__file__).resolve().parents[1]  # services/
_QUESTIONS_PATH = _WORKBENCH_DIR.parent / "data" / "source" / "questions.json"


def load_questions(path: Path | None = None) -> list[dict[str, Any]]:
    source = path or _QUESTIONS_PATH
    data = json.loads(source.read_text(encoding="utf-8"))
    questions = data.get("questions", data) if isinstance(data, dict) else data
    if not isinstance(questions, list):
        raise ValueError(f"Invalid questions file: {source}")
    return questions


def match_question(parsed_input: dict[str, Any], questions: list[dict[str, Any]] | None = None, top_n: int = 5) -> dict[str, Any]:
    questions = questions or load_questions()
    stem = parsed_input.get("stem", "")
    options = parsed_input.get("options", {}) or {}
    raw = parsed_input.get("raw_text", "")

    exact_id = _extract_question_id(raw)
    scored: list[dict[str, Any]] = []
    for question in questions:
        score, parts = _score_question(stem, options, question)
        if exact_id and str(question.get("id")) == exact_id:
            score = max(score, 1.0)
            parts["id_exact"] = 1.0
        scored.append({"score": round(score, 4), "parts": parts, "question": _public_question(question)})

    scored.sort(key=lambda item: item["score"], reverse=True)
    top = scored[:top_n]
    best = top[0] if top else None
    matched = bool(best and best["score"] >= 0.52)
    if not matched and best and best["score"] >= 0.44 and len(options) >= 2:
        matched = True

    return {
        "matched": matched,
        "best": best if matched else None,
        "top_candidates": top,
        "threshold": 0.52,
        "question_count": len(questions),
    }


def _public_question(question: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": question.get("id"),
        "section": question.get("section"),
        "number": question.get("number"),
        "stem": question.get("stem", ""),
        "options": question.get("options", {}) or {},
        "answer": question.get("answer", ""),
    }


def _score_question(stem: str, options: dict[str, str], question: dict[str, Any]) -> tuple[float, dict[str, float]]:
    q_stem = str(question.get("stem", ""))
    q_options = question.get("options", {}) or {}

    stem_ratio = _ratio(stem, q_stem)
    stem_jaccard = _ngram_jaccard(stem, q_stem)
    option_score = _score_options(options, q_options)
    option_label_overlap = _label_overlap(options, q_options)

    score = stem_ratio * 0.42 + stem_jaccard * 0.24 + option_score * 0.28 + option_label_overlap * 0.06
    return score, {
        "stem_ratio": round(stem_ratio, 4),
        "stem_jaccard": round(stem_jaccard, 4),
        "option_score": round(option_score, 4),
        "option_label_overlap": round(option_label_overlap, 4),
    }


def _score_options(left: dict[str, str], right: dict[str, str]) -> float:
    if not left or not right:
        return 0.0
    scores: list[float] = []
    for label, text in left.items():
        if label in right:
            scores.append(_ratio(str(text), str(right[label])) * 0.65 + _ngram_jaccard(str(text), str(right[label])) * 0.35)
        else:
            scores.append(max((_ratio(str(text), str(candidate)) for candidate in right.values()), default=0.0) * 0.75)
    return sum(scores) / max(len(scores), 1)


def _label_overlap(left: dict[str, str], right: dict[str, str]) -> float:
    if not left or not right:
        return 0.0
    a = set(left)
    b = set(right)
    return len(a & b) / len(a | b)


def _ratio(left: str, right: str) -> float:
    a = _normalize(left)
    b = _normalize(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


def _ngram_jaccard(left: str, right: str, n: int = 2) -> float:
    a = _ngrams(_normalize(left), n)
    b = _ngrams(_normalize(right), n)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _ngrams(text: str, n: int) -> set[str]:
    if len(text) <= n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def _normalize(text: str) -> str:
    text = str(text or "").lower()
    return re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE)


def _extract_question_id(text: str) -> str:
    match = re.search(r"\b\d+\.\d+_\d+\b", text or "")
    return match.group(0) if match else ""
