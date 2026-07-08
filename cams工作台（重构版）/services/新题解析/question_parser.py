"""
Question parser: rules-first with LLM fallback.

Parses unstructured pasted text into structured question fields:
stem, options (A-K), detected_answer, question_type, keywords, parse_warnings.

Strategy
--------
1. Regex-based rules handle ~90% of typical teacher-pasted formats.
2. If the rules fail (missing options, garbled format), a DeepSeek LLM call
   is made as fallback, using the prompt in ``prompts/01_parse_question.md``.
3. ``detected_answer`` is saved for teacher reference but **never** fed to the
   blind adjudicator.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Prompt file lives alongside the module under ../prompts/
_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_PARSE_PROMPT_PATH = _PROMPTS_DIR / "01_parse_question.md"

# Regex patterns
_RE_OPTION_LINE = re.compile(
    r"(?:^|\n)\s*([A-K])[\.\、\)）]\s*(.+?)(?=\n\s*[A-K][\.\、\)）]|\n\n|\n(?:答案|解析|标准答案|题目解析|正确答案)|\Z)",
    re.DOTALL | re.MULTILINE,
)
_RE_ANSWER = re.compile(
    r"(?:答案|标准答案|正确答案)[：:]\s*([A-K,，、/;；\s]+)",
    re.MULTILINE,
)
_RE_EXPLANATION = re.compile(
    r"(?:解析|题目解析|答案解析)[：:]\s*(.+)",
    re.DOTALL,
)
_RE_TYPE_MULTI = re.compile(r"(?:多选|多选题|多项选择|不定项)")
_RE_TYPE_TF = re.compile(r"(?:判断|判断题|对错)")
_RE_CJK = re.compile(r"[一-鿿]{2,}")
_RE_EN = re.compile(r"[A-Za-z][A-Za-z0-9_/\-.]{1,}")


def _extract_keywords(text: str, max_kw: int = 8) -> list[str]:
    """Extract CJK bigrams and English terms as keyword candidates."""
    cjk = _RE_CJK.findall(text)
    en = [t.lower() for t in _RE_EN.findall(text)]
    seen: set[str] = set()
    result: list[str] = []
    for token in cjk + en:
        if token not in seen:
            seen.add(token)
            result.append(token)
        if len(result) >= max_kw:
            break
    return result


def _infer_question_type(
    text: str, stem: str, option_count: int
) -> str:
    """Guess the question type from textual clues and option shape."""
    if any(token in text or token in stem for token in ("多选", "多项选择", "不定项")):
        return "multiple_choice"
    if any(token in text or token in stem for token in ("判断", "对错")):
        return "true_false"
    if _RE_TYPE_MULTI.search(text) or _RE_TYPE_MULTI.search(stem):
        return "multiple_choice"
    if _RE_TYPE_TF.search(text) or _RE_TYPE_TF.search(stem):
        return "true_false"
    if option_count >= 5:
        return "multiple_choice"  # heuristic: 5+ options → multi-select
    return "single_choice"


def _infer_question_subtype(
    text: str, stem: str, option_count: int, question_type: str
) -> str:
    if question_type == "single_choice":
        return "single_choice"
    if question_type == "true_false":
        return "true_false"
    if "不定项" in text or "不定项" in stem:
        return "unfixed_multiple_choice"
    if "多选" in text or "多项选择" in text or "多选" in stem or "多项选择" in stem:
        return "multiple_choice"
    if option_count >= 5:
        return "heuristic_multiple_choice"
    return "multiple_choice"


def parse_question_rules(text: str) -> dict[str, Any] | None:
    """Attempt regex-based parsing.

    Returns
    -------
    dict or None
        Parsed fields on success; ``None`` signals *rules failed, try LLM*.
    """
    matches = _RE_OPTION_LINE.findall(text)
    if not matches or len(matches) < 2:
        return None

    options: dict[str, str] = {}
    first_option_start: int | None = None
    for label, body in matches:
        label = label.strip()
        body = body.strip()
        if label not in options:
            options[label] = body
        # Record position of first option to split stem
        if first_option_start is None:
            idx = text.find(f"{label}.", 0)
            if idx == -1:
                idx = text.find(f"{label}、", 0)
            if idx == -1:
                idx = text.find(f"{label}）", 0)
            if idx == -1:
                idx = text.find(f"{label})", 0)
            if idx >= 0:
                first_option_start = idx

    if len(options) < 2:
        return None

    # Stem = everything before the first option label
    stem = text[:first_option_start] if first_option_start else ""
    stem = _clean_stem(stem)

    detected_answer_raw = _RE_ANSWER.search(text)
    detected_answer = ""
    if detected_answer_raw:
        raw = detected_answer_raw.group(1).strip()
        # Normalise to sorted comma-separated labels
        labels = re.findall(r"[A-K]", raw.upper())
        detected_answer = ",".join(sorted(set(labels)))

    question_type = _infer_question_type(text, stem, len(options))
    question_subtype = _infer_question_subtype(text, stem, len(options), question_type)
    keywords = _extract_keywords(stem)
    parse_warnings: list[str] = []

    # quality checks
    if not stem or len(stem) < 5:
        parse_warnings.append("题干过短或无法正确提取")
    if len(options) < 2:
        parse_warnings.append(f"仅识别到 {len(options)} 个选项")

    return {
        "stem": stem,
        "options": options,
        "detected_answer": detected_answer,
        "question_type": question_type,
        "question_subtype": question_subtype,
        "keywords": keywords,
        "parse_warnings": parse_warnings,
        "parse_method": "rules",
        "raw_text": text,
    }


def _clean_stem(stem: str) -> str:
    """Strip leading noisy prefixes from the stem text."""
    stem = stem.strip()
    stem = re.sub(r"^(?:单选题|多选题|不定项|判断题)[：:\s]*", "", stem)
    stem = re.sub(r"^(?:【[^】]+】|\[[^\]]+\]|\d+[\.\、]?\s*)+", "", stem)
    stem = re.sub(r"^(?:题目|题干)[：:]\s*", "", stem)
    stem = re.sub(r"^(?:单选题|多选题|判断题)[：:\s]*", "", stem)
    return stem.strip()


_RULES_FAILED_SENTINEL = "__RULES_FAILED__"


def parse_question_llm(client: Any, text: str) -> dict[str, Any]:
    """LLM fallback for garbled or unusual question formats.

    Reads the system prompt from ``prompts/01_parse_question.md`` and sends
    the raw text as a user message.
    """
    if _PARSE_PROMPT_PATH.exists():
        system_prompt = _PARSE_PROMPT_PATH.read_text(encoding="utf-8").strip()
    else:
        system_prompt = _fallback_parse_prompt()

    full_prompt = f"{system_prompt}\n\n待解析文本：\n{text}"

    # Import call_llm via the shared evidence_pool dependency chain
    import run_step1  # noqa: F811

    raw = run_step1.call_llm(client, full_prompt, max_tokens=2000)

    import run_agentic_search_experiment as agentic

    parsed = agentic.parse_json_object(raw)
    if not isinstance(parsed, dict):
        return _rules_failed_result(text, "LLM 输出无法解析为 JSON")

    # Normalise fields
    options = parsed.get("options", {})
    if isinstance(options, list):
        # Some models output [{option: "A", text: "..."}]
        options = {
            str(item.get("option", "")).strip(): str(item.get("text", item.get("option_text", ""))).strip()
            for item in options
            if isinstance(item, dict)
        }
    if not isinstance(options, dict) or len(options) < 2:
        return _rules_failed_result(text, "LLM 输出的选项不完整")

    options = {str(k).strip().upper(): str(v).strip() for k, v in options.items()}

    stem = str(parsed.get("stem", "")).strip()
    detected_answer = str(parsed.get("detected_answer", "")).strip()
    question_type = str(parsed.get("question_type", "single_choice")).strip()
    question_subtype = str(parsed.get("question_subtype", "")).strip()
    keywords = parsed.get("keywords", [])
    if not isinstance(keywords, list):
        keywords = []
    parse_warnings = parsed.get("parse_warnings", [])
    if not isinstance(parse_warnings, list):
        parse_warnings = []

    if not question_subtype:
        question_subtype = _infer_question_subtype(text, stem, len(options), question_type)

    if not stem or len(stem) < 5:
        parse_warnings.append("题干过短或提取失败")
    if len(options) < 2:
        parse_warnings.append(f"仅识别到 {len(options)} 个选项")

    return {
        "stem": stem,
        "options": options,
        "detected_answer": detected_answer,
        "question_type": question_type,
        "question_subtype": question_subtype,
        "keywords": [str(k) for k in keywords[:8]],
        "parse_warnings": parse_warnings,
        "parse_method": "llm_fallback",
        "raw_text": text,
    }


def _rules_failed_result(text: str, reason: str) -> dict[str, Any]:
    return {
        "stem": "",
        "options": {},
        "detected_answer": "",
        "question_type": "unknown",
        "question_subtype": "unknown",
        "keywords": [],
        "parse_warnings": [reason],
        "parse_method": "llm_fallback",
        "raw_text": text,
    }


def _fallback_parse_prompt() -> str:
    """Minimal prompt if the markdown prompt file is missing."""
    return """你是CAMS反洗钱考试题目解析器。请从一段文本中提取题目结构化信息，输出严格JSON。

格式：
{
  "stem": "题干文本",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "detected_answer": "原文中的答案标注，没有则填空字符串",
  "question_type": "single_choice / multiple_choice / true_false",
  "keywords": ["关键词1", "关键词2"],
  "parse_warnings": []
}

规则：stem不包含选项文本；options的key为大写字母A-K；不能编造内容。"""


def parse_question(client: Any, text: str) -> dict[str, Any]:
    """Parse pasted question text — rules first, LLM fallback.

    Parameters
    ----------
    client : OpenAI-compatible client or None
        If ``None``, only rules-based parsing is attempted.
    text : str
        Raw text pasted by the teacher.

    Returns
    -------
    dict
        Always returns a dict with at least ``stem``, ``options``,
        ``parse_method``, and ``parse_warnings``.
    """
    text = str(text or "").strip()
    if not text:
        return {
            "stem": "",
            "options": {},
            "detected_answer": "",
            "question_type": "unknown",
            "question_subtype": "unknown",
            "keywords": [],
            "parse_warnings": ["输入文本为空"],
            "parse_method": "rules",
            "raw_text": "",
        }

    # 1. Try rules
    rules_result = parse_question_rules(text)
    if rules_result is not None:
        return rules_result

    # 2. LLM fallback
    if client is None:
        return _rules_failed_result(text, "规则解析失败，且未提供 LLM 客户端")

    try:
        return parse_question_llm(client, text)
    except Exception as exc:
        return _rules_failed_result(text, f"LLM 解析异常: {exc}")
