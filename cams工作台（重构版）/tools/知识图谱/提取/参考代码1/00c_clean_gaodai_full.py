"""
Clean the full Higher Algebra structured markdown sources for the v4.4 pipeline.

The generic cleaner was written for a different textbook family.  The Higher
Algebra sources already have usable markdown headings, but they contain front
matter, a table of contents, and exercise-answer material after the main text.
This script keeps the main teaching body only and records coverage warnings.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


CHAPTER_HEADING_RE = re.compile(r"^#\s*第\s*([0-9一二三四五六七八九十百]+)\s*章\s*(.*?)\s*$")
STAR_CHAPTER_RE = re.compile(r"^\*+\s*第\s*([0-9一二三四五六七八九十百]+)\s*章\s*(.*?)\**\s*$")
SECTION_RE = re.compile(r"^(#{1,6})\s*(\*?)\s*(\d+)\.(\d+)\s+(.+?)\s*$")
SUBSECTION_RE = re.compile(r"^(#{1,6})\s*(\d+)\.(\d+)\.(\d+)\.?\s+(.+?)\s*$")
BARE_SECTION_RE = re.compile(r"^(\*?)\s*(\d+)\.(\d+)\s+(.+?)\s*$")
BARE_SUBSECTION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)\.?\s+(.+?)\s*$")
STAR_SECTION_RE = re.compile(r"^\*+\s*(\d+)\.(\d+)\s+(.+?)\*+\s*$")
EXERCISE_RE = re.compile(r"^(#{1,6})?\s*习题\s*(\d+)\.(\d+)\s*$")
SUPPLEMENT_RE = re.compile(r"^\**\s*补充题\s*([一二三四五六七八九十百0-9]+).*?\**\s*$")
APP_WORLD_RE = re.compile(r"^\**\s*(\*?\s*)?应用小天地[：:].+?\**\s*$")
ANSWER_START_RE = re.compile(r"^#\s*习题答案与提示(?:\s|$)")
REFERENCE_RE = re.compile(r"^\**\s*参考文献.*?\**\s*$")
BLANK_HEADING_RE = re.compile(r"^#{1,6}\s*$")

CN_DIGITS = {
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


@dataclass
class CleanReport:
    input_path: str
    output_path: str
    source_lines: int
    clean_lines: int
    body_start_line: int
    body_end_line: int
    skipped_front_lines: int
    skipped_tail_lines: int
    chapters: list[int]
    sections: list[str]
    subsections: list[str]
    exercises: list[str]
    warnings: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean full Higher Algebra markdown.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-chapters", default="", help="Comma-separated chapter numbers, e.g. 1,2,3,4,5,6.")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def cn_number_to_int(text: str) -> int:
    text = text.strip()
    if text.isdigit():
        return int(text)
    if text == "十":
        return 10
    if "十" in text:
        left, _, right = text.partition("十")
        tens = CN_DIGITS.get(left, 1) if left else 1
        ones = CN_DIGITS.get(right, 0) if right else 0
        return tens * 10 + ones
    return CN_DIGITS.get(text, 0)


def clean_title(title: str) -> str:
    title = title.strip()
    title = title.strip("*")
    title = re.sub(r"\s*[.…·。]+\s*\(?\d+\)?\s*$", "", title).strip()
    title = re.sub(r"\s*\(\s*\d+\s*\)\s*$", "", title).strip()
    title = re.sub(r"\s+\d+\s*$", "", title).strip()
    title = re.sub(r"\s*[.…·。]+\s*$", "", title).strip()
    title = title.replace("，", ",")
    return title.strip()


def normalize_chapter_line(line: str) -> str | None:
    stripped = line.strip()
    match = CHAPTER_HEADING_RE.match(stripped) or STAR_CHAPTER_RE.match(stripped)
    if not match:
        return None
    chapter_no = cn_number_to_int(match.group(1))
    title = clean_title(match.group(2))
    return f"# 第{chapter_no}章 {title}".rstrip()


def chapter_no_from_line(line: str) -> int | None:
    normalized = normalize_chapter_line(line)
    if not normalized:
        return None
    match = re.search(r"第(\d+)章", normalized)
    return int(match.group(1)) if match else None


def find_body_start(lines: list[str], expected_chapters: set[int]) -> int:
    first_expected = min(expected_chapters) if expected_chapters else None
    if first_expected is not None:
        first_subsection = re.compile(r"^###\s*%s\.1\.1\.?\s+内容精华\s*$" % first_expected)
        for idx, line in enumerate(lines):
            if not first_subsection.match(line.strip()):
                continue
            for back in range(idx, -1, -1):
                chapter_no = chapter_no_from_line(lines[back])
                if chapter_no == first_expected:
                    return back

    for idx, line in enumerate(lines):
        chapter_no = chapter_no_from_line(line)
        if chapter_no is None:
            continue
        if first_expected is not None and chapter_no != first_expected:
            continue
        lookahead = "\n".join(lines[idx : min(len(lines), idx + 500)])
        if re.search(
            r"^###\s*%s\.1\.1\.?\s+内容精华\s*$" % chapter_no,
            lookahead,
            flags=re.MULTILINE,
        ):
            return idx
    for idx, line in enumerate(lines):
        chapter_no = chapter_no_from_line(line)
        if chapter_no is not None:
            return idx
    return 0


def find_body_end(lines: list[str], start: int) -> int:
    for idx in range(start + 1, len(lines)):
        stripped = lines[idx].strip()
        if ANSWER_START_RE.match(stripped) or REFERENCE_RE.match(stripped):
            return idx
    return len(lines)


def normalize_line(line: str, current_chapter: int | None) -> tuple[str, int | None]:
    stripped = line.rstrip()
    compact = stripped.strip()
    if not compact:
        return "", current_chapter
    if BLANK_HEADING_RE.match(compact):
        return "", current_chapter

    chapter = normalize_chapter_line(compact)
    if chapter:
        return chapter, chapter_no_from_line(compact)

    subsection = SUBSECTION_RE.match(compact) or BARE_SUBSECTION_RE.match(compact)
    if subsection:
        groups = subsection.groups()
        if len(groups) == 5:
            _, chap, sec, subsec, title = groups
        else:
            chap, sec, subsec, title = groups
        return f"### {int(chap)}.{int(sec)}.{int(subsec)} {clean_title(title)}", current_chapter

    star_section = STAR_SECTION_RE.match(compact)
    if star_section:
        chap, sec, title = star_section.groups()
        return f"## {int(chap)}.{int(sec)} * {clean_title(title)}", current_chapter

    section = SECTION_RE.match(compact) or BARE_SECTION_RE.match(compact)
    if section:
        groups = section.groups()
        if len(groups) == 5:
            _, star, chap, sec, title = groups
        else:
            star, chap, sec, title = groups
        marker = " *" if star else ""
        return f"## {int(chap)}.{int(sec)}{marker} {clean_title(title)}", current_chapter

    exercise = EXERCISE_RE.match(compact)
    if exercise:
        _, chap, sec = exercise.groups()
        return f"### 习题{int(chap)}.{int(sec)}", current_chapter

    supplement = SUPPLEMENT_RE.match(compact)
    if supplement:
        label = clean_title(compact)
        label = re.sub(r"^\*+", "", label).strip()
        return f"### {label}", current_chapter

    if APP_WORLD_RE.match(compact):
        label = clean_title(compact)
        label = re.sub(r"^\*+", "", label).strip()
        return f"### {label}", current_chapter

    return stripped, current_chapter


def unique_in_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def collect_report(
    input_path: Path,
    output_path: Path,
    source_lines: list[str],
    clean_lines: list[str],
    body_start: int,
    body_end: int,
    expected_chapters: set[int],
) -> CleanReport:
    chapters: list[int] = []
    sections: list[str] = []
    subsections: list[str] = []
    exercises: list[str] = []
    warnings: list[str] = []
    for line in clean_lines:
        chapter_match = re.match(r"^# 第(\d+)章", line)
        if chapter_match:
            chapters.append(int(chapter_match.group(1)))
        section_match = re.match(r"^##\s+(\d+\.\d+)", line)
        if section_match:
            sections.append(section_match.group(1))
        subsection_match = re.match(r"^###\s+(\d+\.\d+\.\d+)", line)
        if subsection_match:
            subsections.append(subsection_match.group(1))
        exercise_match = re.match(r"^###\s+习题(\d+\.\d+)", line)
        if exercise_match:
            exercises.append(exercise_match.group(1))

    chapter_set = set(chapters)
    missing_chapters = sorted(expected_chapters - chapter_set)
    extra_chapters = sorted(chapter_set - expected_chapters) if expected_chapters else []
    if missing_chapters:
        warnings.append(f"missing expected chapters: {missing_chapters}")
    if extra_chapters:
        warnings.append(f"unexpected chapters: {extra_chapters}")

    for chapter in sorted(chapter_set):
        chapter_sections = [s for s in sections if s.startswith(f"{chapter}.")]
        if not chapter_sections:
            warnings.append(f"chapter {chapter} has no section headings")

    if expected_chapters and max(expected_chapters) == 11:
        existing_11_sections = [s for s in sections if s.startswith("11.")]
        if existing_11_sections == ["11.1"]:
            warnings.append("chapter 11 source body only exposes section 11.1; TOC lists 11.2-11.4 but body headings are absent in this structured markdown")

    return CleanReport(
        input_path=str(input_path),
        output_path=str(output_path),
        source_lines=len(source_lines),
        clean_lines=len(clean_lines),
        body_start_line=body_start + 1,
        body_end_line=body_end,
        skipped_front_lines=body_start,
        skipped_tail_lines=len(source_lines) - body_end,
        chapters=sorted(set(chapters)),
        sections=unique_in_order(sections),
        subsections=unique_in_order(subsections),
        exercises=unique_in_order(exercises),
        warnings=warnings,
    )


def write_markdown_report(path: Path, report: CleanReport) -> None:
    lines = [
        "# 高等代数全书数据清理报告",
        "",
        f"- 输入文件：`{report.input_path}`",
        f"- 输出文件：`{report.output_path}`",
        f"- 源文件行数：{report.source_lines}",
        f"- 清理后行数：{report.clean_lines}",
        f"- 正文起止行：{report.body_start_line} - {report.body_end_line}",
        f"- 跳过前置行数：{report.skipped_front_lines}",
        f"- 跳过尾部行数：{report.skipped_tail_lines}",
        "",
        "## 覆盖范围",
        "",
        f"- 章节：{', '.join(str(x) for x in report.chapters) if report.chapters else '无'}",
        f"- 节数量：{len(report.sections)}",
        f"- 小节数量：{len(report.subsections)}",
        f"- 习题节数量：{len(report.exercises)}",
        "",
        "## 节列表",
        "",
        *[f"- {section}" for section in report.sections],
        "",
        "## 风险与备注",
        "",
    ]
    if report.warnings:
        lines.extend(f"- {warning}" for warning in report.warnings)
    else:
        lines.append("- 未发现覆盖范围风险。")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.output.exists() and not args.overwrite:
        raise FileExistsError(f"{args.output} exists. Use --overwrite.")
    if args.report.exists() and not args.overwrite:
        raise FileExistsError(f"{args.report} exists. Use --overwrite.")

    expected_chapters = {int(item) for item in args.expected_chapters.split(",") if item.strip()}
    source_lines = args.input.read_text(encoding="utf-8").splitlines()
    body_start = find_body_start(source_lines, expected_chapters)
    body_end = find_body_end(source_lines, body_start)

    cleaned: list[str] = []
    current_chapter: int | None = None
    blank_pending = False
    for raw in source_lines[body_start:body_end]:
        normalized, current_chapter = normalize_line(raw, current_chapter)
        if not normalized:
            blank_pending = True
            continue
        if blank_pending and cleaned and not cleaned[-1].startswith("#") and not normalized.startswith("#"):
            cleaned.append("")
        cleaned.append(normalized)
        blank_pending = False

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(cleaned).rstrip() + "\n", encoding="utf-8")

    report = collect_report(
        input_path=args.input,
        output_path=args.output,
        source_lines=source_lines,
        clean_lines=cleaned,
        body_start=body_start,
        body_end=body_end,
        expected_chapters=expected_chapters,
    )
    write_markdown_report(args.report, report)
    json_report = args.report.with_suffix(".json")
    json_report.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[OK] clean markdown -> {args.output}")
    print(f"[OK] report -> {args.report}")
    print(f"[OK] json report -> {json_report}")
    if report.warnings:
        print("[WARN] " + " | ".join(report.warnings))
    print(f"[INFO] chapters={report.chapters} sections={len(report.sections)} subsections={len(report.subsections)}")


if __name__ == "__main__":
    main()
