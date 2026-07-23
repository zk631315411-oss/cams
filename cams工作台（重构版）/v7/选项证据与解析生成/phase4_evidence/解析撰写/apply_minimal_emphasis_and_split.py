# -*- coding: utf-8 -*-
"""Apply restrained Markdown emphasis to a merged software-export file.

The source text is never rewritten semantically.  The only source-file change
is insertion of ``**`` around direct answer evidence, compact obligations and
numeric thresholds.  The result is then split back into section Markdown files.
"""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


QUESTION_RE = re.compile(r"(?m)^##\s+(v7_q_\d{6})\s*$")
OPTION_RE = re.compile(r"(?m)^-\s+([A-E])\.\s+(.+)$")
ANSWER_RE = re.compile(r"(?m)^答案：\s*([A-E]+)\s*$")
EDITABLE_SECTION_RE = re.compile(r"(?m)^【(核心解析|错误项分析|易错提醒)】\s*$")
QUOTED_RE = re.compile(r"[「『]([^「」『』\n]{2,70})[」』]")
THRESHOLD_RE = re.compile(
    r"(?:超过|不超过|不少于|低于|高于|达到|每笔|至少|最多)?\s*"
    r"\d[\d,]*(?:\.\d+)?\s*(?:美元|元|%|个月|天|年|次|项)"
)
OBLIGATION_RE = re.compile(
    r"(?:机构|组织|金融机构|员工|董事会|管理层|当局|各辖区|报告实体)"
    r"(?:应|必须|不得|需要)(?:[^，。；：\n<]{2,35})"
)
SECTION_BREAK = "<!-- SECTION_BREAK -->"


def _question_options(block: str) -> tuple[dict[str, str], set[str]]:
    answer_match = ANSWER_RE.search(block)
    answer = set(answer_match.group(1)) if answer_match else set()
    options = {match.group(1): match.group(2).strip() for match in OPTION_RE.finditer(block)}
    return options, answer


def _non_overlapping_spans(text: str, candidates: list[tuple[int, int]]) -> list[tuple[int, int]]:
    selected: list[tuple[int, int]] = []
    for start, end in sorted(set(candidates), key=lambda span: (span[0], -(span[1] - span[0]))):
        if start == end or any(start < old_end and end > old_start for old_start, old_end in selected):
            continue
        selected.append((start, end))
    return selected


def _emphasize_text(text: str, correct_options: list[str]) -> tuple[str, int]:
    candidates: list[tuple[int, int]] = []
    for option in correct_options:
        if len(option) < 4:
            continue
        for match in re.finditer(re.escape(option), text):
            candidates.append(match.span())
    for pattern in (QUOTED_RE, THRESHOLD_RE, OBLIGATION_RE):
        for match in pattern.finditer(text):
            if pattern is QUOTED_RE:
                candidates.append((match.start(1), match.end(1)))
            else:
                candidates.append(match.span())

    spans = _non_overlapping_spans(text, candidates)
    if not spans:
        return text, 0
    parts: list[str] = []
    cursor = 0
    for start, end in spans:
        parts.append(text[cursor:start])
        parts.append("**" + text[start:end] + "**")
        cursor = end
    parts.append(text[cursor:])
    return "".join(parts), len(spans)


def emphasize_question(block: str) -> tuple[str, int]:
    options, answer = _question_options(block)
    correct_options = [options[label] for label in sorted(answer) if label in options]
    headers = list(EDITABLE_SECTION_RE.finditer(block))
    if not headers:
        return block, 0

    chunks: list[str] = []
    cursor = 0
    total = 0
    for index, header in enumerate(headers):
        body_end = headers[index + 1].start() if index + 1 < len(headers) else len(block)
        chunks.append(block[cursor:header.end()])
        body, count = _emphasize_text(block[header.end():body_end], correct_options)
        chunks.append(body)
        cursor = body_end
        total += count
    chunks.append(block[cursor:])
    return "".join(chunks), total


def emphasize_markdown(markdown: str) -> tuple[str, int, int]:
    matches = list(QUESTION_RE.finditer(markdown))
    if not matches:
        raise RuntimeError("未找到题号，无法加粗")
    chunks: list[str] = []
    cursor = 0
    total_marks = 0
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        chunks.append(markdown[cursor:match.start()])
        processed, count = emphasize_question(markdown[match.start():end])
        chunks.append(processed)
        cursor = end
        total_marks += count
    chunks.append(markdown[cursor:])
    return "".join(chunks), len(matches), total_marks


def split_sections(markdown: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_section in markdown.split(SECTION_BREAK):
        section = raw_section.strip()
        if not section:
            continue
        heading = re.search(r"(?m)^#\s+(p\d+-ch\d+-h\d+)\s+题库软件版解析预览\s*$", section)
        if not heading:
            raise RuntimeError("存在无法识别的小节标题")
        section_code = heading.group(1)
        if section_code in result:
            raise RuntimeError(f"小节重复：{section_code}")
        result[section_code] = section + "\n"
    return result


def main() -> int:
    here = Path(__file__).resolve().parent
    software_export = here.parent / "output" / "software_export"
    parser = argparse.ArgumentParser(description="按最小必要原则加粗并拆分 IMA 合并 Markdown")
    parser.add_argument("--source", type=Path, default=software_export / "merged_for_ima.md")
    parser.add_argument("--output-dir", type=Path, default=software_export / "ima_merged_sections")
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=software_export / "ima_merged_sections_before_merged_for_ima",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = args.source.read_text(encoding="utf-8")
    emphasized, question_count, mark_count = emphasize_markdown(source)
    sections = split_sections(emphasized)
    print(f"题目数：{question_count}；新增加粗：{mark_count}；小节数：{len(sections)}")
    if args.dry_run:
        print("[dry-run] 未写入文件")
        return 0

    backup_source = args.source.with_name(args.source.stem + ".before_emphasis.md")
    if not backup_source.exists():
        shutil.copy2(args.source, backup_source)
    if args.output_dir.exists() and not args.backup_dir.exists():
        shutil.copytree(args.output_dir, args.backup_dir)

    args.source.write_text(emphasized, encoding="utf-8")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for section_code, section_text in sections.items():
        (args.output_dir / f"{section_code}.md").write_text(section_text, encoding="utf-8")
    print(f"[source] {args.source}")
    print(f"[sections] {args.output_dir}")
    print(f"[backup] {backup_source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
