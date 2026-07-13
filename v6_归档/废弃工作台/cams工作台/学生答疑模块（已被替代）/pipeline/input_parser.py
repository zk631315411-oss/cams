from __future__ import annotations

import re
from typing import Any


_OPTION_RE = re.compile(
    r"(?ms)^\s*([A-K])[\.\、\)）:：]\s*(.+?)(?=^\s*[A-K][\.\、\)）:：]\s*|^\s*(?:学生|学员|用户|疑问|问题|问|老师|答疑)\s*[:：]|^\s*(?:答案|标准答案|正确答案|解析)\s*[:：]|\Z)"
)
_ANSWER_RE = re.compile(r"(?im)^\s*(?:答案|标准答案|正确答案)\s*[:：]\s*([A-K,，、;；\s]+)")
_STUDENT_MARKER_RE = re.compile(
    r"(?is)(?:学生(?:问|疑问|提问)?|学员(?:问|疑问|提问)?|用户(?:问|疑问)?|疑问|问题|问|老师|答疑)\s*[:：]\s*(.+)$"
)
_EXPLANATION_MARKER_RE = re.compile(r"(?is)^\s*(?:解析|答案解析|教研解析)\s*[:：].*$")
_INTERNAL_SPACE_RE = re.compile(r"[ \t]+")


def parse_student_input(text: str) -> dict[str, Any]:
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    warnings: list[str] = []
    if not raw:
        return {
            "raw_text": "",
            "stem": "",
            "options": {},
            "student_question": "",
            "mentioned_options": [],
            "detected_answer_in_input": "",
            "parse_method": "rules",
            "warnings": ["empty_input"],
        }

    options, first_option_start, last_option_end = _parse_options(raw)
    stem = _clean_stem(raw[:first_option_start].strip()) if first_option_start is not None else ""

    trailing = raw[last_option_end:].strip() if last_option_end is not None else raw
    student_question = _extract_student_question(trailing)
    if not student_question:
        student_question = _extract_student_question(raw)

    detected_answer = _extract_answer(raw)
    if detected_answer:
        student_question = _remove_answer_lines(student_question)

    if not stem and options:
        warnings.append("stem_missing")
    if len(options) < 2:
        warnings.append("options_missing_or_incomplete")
    if not student_question:
        warnings.append("student_question_missing")

    mentioned = _detect_mentioned_options(student_question, set(options))

    return {
        "raw_text": raw,
        "stem": stem,
        "options": options,
        "student_question": student_question,
        "mentioned_options": mentioned,
        "detected_answer_in_input": detected_answer,
        "parse_method": "rules",
        "warnings": warnings,
    }


def _parse_options(text: str) -> tuple[dict[str, str], int | None, int | None]:
    options: dict[str, str] = {}
    first_start: int | None = None
    last_end: int | None = None
    for match in _OPTION_RE.finditer(text):
        label = match.group(1).upper()
        body = _clean_option(match.group(2))
        if not body:
            continue
        if first_start is None:
            first_start = match.start()
        last_end = match.end()
        options.setdefault(label, body)
    return options, first_start, last_end


def _clean_stem(stem: str) -> str:
    stem = _remove_answer_lines(stem)
    stem = re.sub(r"(?im)^\s*(?:题目|题干|单选题|多选题|不定项|判断题)\s*[:：]?\s*", "", stem)
    stem = re.sub(r"(?m)^\s*\d+[\.\、]\s*", "", stem)
    return _squash(stem)


def _clean_option(option: str) -> str:
    option = _remove_answer_lines(option)
    option = _EXPLANATION_MARKER_RE.sub("", option)
    return _squash(option)


def _extract_student_question(text: str) -> str:
    if not text:
        return ""
    match = _STUDENT_MARKER_RE.search(text)
    if match:
        return _clean_student_question(match.group(1))

    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^(?:答案|标准答案|正确答案|解析|答案解析|教研解析)\s*[:：]", stripped):
            continue
        if re.match(r"^[A-K][\.\、\)）:：]", stripped):
            continue
        lines.append(stripped)
    joined = "\n".join(lines).strip()
    if any(token in joined for token in ("为什么", "怎么", "不理解", "疑问", "不是", "区别", "哪里")):
        return _clean_student_question(joined)
    return ""


def _clean_student_question(text: str) -> str:
    text = _remove_answer_lines(text)
    text = re.sub(r"(?is)(?:解析|答案解析|教研解析)\s*[:：].*$", "", text)
    return _squash(text)


def _extract_answer(text: str) -> str:
    match = _ANSWER_RE.search(text)
    if not match:
        return ""
    labels = re.findall(r"[A-K]", match.group(1).upper())
    return ",".join(sorted(set(labels)))


def _remove_answer_lines(text: str) -> str:
    return re.sub(r"(?im)^\s*(?:答案|标准答案|正确答案)\s*[:：].*$", "", text or "").strip()


def _detect_mentioned_options(text: str, valid_labels: set[str]) -> list[str]:
    if not text or not valid_labels:
        return []
    found: set[str] = set()
    for match in re.finditer(r"(?:选项\s*)?([A-K])(?:\s*选项)?", text.upper()):
        label = match.group(1)
        start, end = match.span(1)
        before = text.upper()[max(0, start - 1) : start]
        after = text.upper()[end : end + 1]
        if before.isalpha() or after.isalpha():
            continue
        if label in valid_labels:
            found.add(label)
    return sorted(found)


def _squash(text: str) -> str:
    lines = [_INTERNAL_SPACE_RE.sub(" ", line).strip() for line in str(text or "").splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()
