# -*- coding: utf-8 -*-
"""Merge one IMA-polished section while retaining local evidence metadata."""

from __future__ import annotations

import argparse
import difflib
import re
import shutil
from collections import OrderedDict
from pathlib import Path


SECTION_NAMES = ("考点", "核心解析", "错误项分析", "易错提醒")
BASE_QUESTION_RE = re.compile(r"(?m)^##\s+(v7_q_\d{6})\s*$")
RAW_QUESTION_RE = re.compile(r"(?mi)^\s*(v7_q_\d{6})\s*$")
ANSWER_RE = re.compile(r"(?m)^答案：\s*([A-E]+)\s*$")
SECTION_RE = re.compile(r"(?m)^【(考点|核心解析|错误项分析|易错提醒)】\s*$")
PAGE_REF_RE = re.compile(r"（书内第[^）\n]+页）|<sup>P\d+(?:-\d+)?</sup>")
SOURCE_QUOTE_RE = re.compile(r"(?m)^教材原句[：:].+$")


def parse_sections(text: str) -> dict[str, str]:
    headers = list(SECTION_RE.finditer(text))
    result: dict[str, str] = {}
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
        result[header.group(1)] = text[header.end() : end].strip()
    return result


def parse_questions(text: str, header_re: re.Pattern[str]) -> OrderedDict[str, dict[str, object]]:
    matches = list(header_re.finditer(text))
    rows: OrderedDict[str, dict[str, object]] = OrderedDict()
    for index, header in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[header.start() : end]
        answer = ANSWER_RE.search(block)
        rows[header.group(1)] = {
            "block": block,
            "answer": answer.group(1) if answer else "",
            "sections": parse_sections(block),
        }
    return rows


def normalize_ima_text(text: str) -> str:
    """IMA web copies may wrap labels and IDs in Markdown bold markers."""
    return text.replace("**", "")


def _claim_before_reference(text: str, reference_start: int) -> str:
    boundary = max(text.rfind(mark, 0, reference_start) for mark in "。！？\n")
    return text[boundary + 1 : reference_start].strip()


def _candidate_sentences(text: str) -> list[tuple[int, int, str]]:
    return [
        (match.start(), match.end(), match.group(0))
        for match in re.finditer(r"[^。！？\n]+[。！？]?", text)
        if match.group(0).strip()
    ]


def _normalise_for_match(text: str) -> str:
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", text).lower()


def _reference_anchor(claim: str) -> list[str]:
    quoted = re.findall(r"[「“\"]([^」”\"]{3,})[」”\"]", claim)
    anchors = sorted(quoted, key=len, reverse=True)
    compact = _normalise_for_match(claim)
    if compact:
        anchors.append(compact)
    return anchors


def reinsert_references(base_text: str, polished_text: str) -> str:
    """Attach every source page marker to the IMA sentence with the same claim."""
    records = [
        (_claim_before_reference(base_text, match.start()), match.group(0))
        for match in PAGE_REF_RE.finditer(base_text)
    ]
    if not records:
        return polished_text

    sentences = _candidate_sentences(polished_text)
    if not sentences:
        raise RuntimeError("IMA 解析中没有可插入页码的句子")
    insertions: dict[int, list[str]] = {}
    for claim, reference in records:
        best_index = -1
        best_score = 0.0
        for index, (_, _, sentence) in enumerate(sentences):
            sentence_compact = _normalise_for_match(sentence)
            score = 0.0
            for anchor in _reference_anchor(claim):
                anchor_compact = _normalise_for_match(anchor)
                if len(anchor_compact) >= 3 and anchor_compact in sentence_compact:
                    score = max(score, 2.0 + len(anchor_compact) / 1000)
                elif anchor_compact:
                    score = max(score, difflib.SequenceMatcher(None, anchor_compact, sentence_compact).ratio())
            if score > best_score:
                best_index = index
                best_score = score
        if best_index < 0 or best_score < 0.18:
            raise RuntimeError(f"无法为页码 {reference} 定位对应论断：{claim}")
        insertions.setdefault(best_index, []).append(reference)

    parts: list[str] = []
    cursor = 0
    for index, (start, end, _) in enumerate(sentences):
        parts.append(polished_text[cursor:end])
        if index in insertions:
            parts.append("".join(OrderedDict.fromkeys(insertions[index])))
        cursor = end
    parts.append(polished_text[cursor:])
    return "".join(parts)


def replace_question_sections(block: str, replacements: dict[str, str]) -> str:
    headers = list(SECTION_RE.finditer(block))
    chunks: list[str] = []
    cursor = 0
    for index, header in enumerate(headers):
        name = header.group(1)
        end = headers[index + 1].start() if index + 1 < len(headers) else len(block)
        chunks.append(block[cursor : header.end()])
        trailing_separator = ""
        if index == len(headers) - 1:
            separator_match = re.search(r"(\n---\s*)$", block[header.end() : end])
            if separator_match:
                trailing_separator = separator_match.group(1)
        chunks.append("\n" + replacements[name].strip() + "\n" + trailing_separator)
        cursor = end
    chunks.append(block[cursor:])
    return "".join(chunks)


def build_replacements(base: dict[str, object], polished: dict[str, object]) -> dict[str, str]:
    base_sections = base["sections"]
    polished_sections = polished["sections"]
    if set(base_sections) != set(SECTION_NAMES) or set(polished_sections) != set(SECTION_NAMES):
        raise RuntimeError("每题必须完整包含四个解析区块")

    replacements: dict[str, str] = {}
    for name in SECTION_NAMES:
        content = reinsert_references(str(base_sections[name]), str(polished_sections[name]).strip())
        if name == "核心解析":
            quotes = SOURCE_QUOTE_RE.findall(str(base_sections[name]))
            if quotes:
                content += "\n\n" + "\n".join(quotes)
        replacements[name] = content
    return replacements


def main() -> int:
    here = Path(__file__).resolve().parent
    software_export = here.parent / "output" / "software_export"
    parser = argparse.ArgumentParser(description="合并单个小节的 IMA 润色稿，保留本地页码与教材原句")
    parser.add_argument("--base", type=Path, required=True, help="原始 sections 中的同名 Markdown")
    parser.add_argument("--ima", type=Path, required=True, help="IMA 网页复制的单小节文本")
    parser.add_argument("--output", type=Path, required=True, help="合并后的同名 Markdown")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    base_text = args.base.read_text(encoding="utf-8")
    ima_text = normalize_ima_text(args.ima.read_text(encoding="utf-8"))
    base_questions = parse_questions(base_text, BASE_QUESTION_RE)
    ima_questions = parse_questions(ima_text, RAW_QUESTION_RE)
    if list(base_questions) != list(ima_questions):
        raise RuntimeError(
            f"题号或顺序不一致：母版={list(base_questions)}；IMA={list(ima_questions)}"
        )

    merged_parts: list[str] = []
    cursor = 0
    for question_id, base in base_questions.items():
        polished = ima_questions[question_id]
        if base["answer"] != polished["answer"]:
            raise RuntimeError(
                f"{question_id} 答案不一致：母版={base['answer']}；IMA={polished['answer']}"
            )
        position = base_text.find(str(base["block"]), cursor)
        merged_parts.append(base_text[cursor:position])
        replacements = build_replacements(base, polished)
        merged_parts.append(replace_question_sections(str(base["block"]), replacements))
        cursor = position + len(str(base["block"]))
    merged_parts.append(base_text[cursor:])
    merged = "".join(merged_parts)

    print(f"题目数：{len(base_questions)}；页码标签：{len(PAGE_REF_RE.findall(merged))}")
    if args.dry_run:
        print("[dry-run] 未写入文件")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    backup = args.output.with_name(args.output.stem + ".before_ima_polish.md")
    if args.output.exists() and not backup.exists():
        shutil.copy2(args.output, backup)
    args.output.write_text(merged, encoding="utf-8")
    print(f"[output] {args.output}")
    if backup.exists():
        print(f"[backup] {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
