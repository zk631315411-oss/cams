# -*- coding: utf-8 -*-
"""Merge IMA's plain-text polish back into frozen software-export sections.

The IMA web client commonly strips Markdown emphasis when copied.  This tool
uses the frozen section Markdown as the source of truth for questions, options,
answers and headings.  It only replaces the four editable explanation blocks.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


EDITABLE_SECTIONS = ("考点", "核心解析", "错误项分析", "易错提醒")
QUESTION_HEADER_RE = re.compile(r"(?m)^##\s+(v7_q_\d{6})\s*$")
RAW_QUESTION_ID_RE = re.compile(
    r"(?mi)^\s*(?:#{1,6}\s*)?(v7[\s_-]*q[\s_-]*\d{6})\s*$"
)
SECTION_HEADER_RE = re.compile(r"(?m)^【(考点|核心解析|错误项分析|易错提醒)】\s*$")
PAGE_REF_RE = re.compile(r"<sup>\s*P(\d+(?:-\d+)?)\s*</sup>", re.IGNORECASE)


@dataclass
class ParsedQuestion:
    question_id: str
    sections: dict[str, str]


def normalize_question_id(value: str) -> str:
    """Normalize the variants IMA may display, such as ``v7 q 000037``."""
    digits = re.sub(r"\D", "", value)
    if len(digits) != 7 or not digits.startswith("7"):
        raise ValueError(f"无法识别题号：{value!r}")
    return f"v7_q_{digits[-6:]}"


def _parse_sections(text: str) -> dict[str, str]:
    matches = list(SECTION_HEADER_RE.finditer(text))
    parsed: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = match.group(1)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[match.end() : end].strip()
        if name in parsed:
            raise ValueError(f"解析区块重复：{name}")
        parsed[name] = content
    return parsed


def parse_raw_ima_text(text: str, source: str) -> tuple[dict[str, ParsedQuestion], list[str]]:
    """Parse all questions from one IMA copied text file."""
    matches = list(RAW_QUESTION_ID_RE.finditer(text))
    rows: dict[str, ParsedQuestion] = {}
    warnings: list[str] = []
    for index, match in enumerate(matches):
        question_id = normalize_question_id(match.group(1))
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections = _parse_sections(text[match.end() : end])
        if not sections:
            warnings.append(f"{source}: {question_id} 未找到四个解析区块")
            continue
        if question_id in rows:
            warnings.append(f"{source}: {question_id} 重复出现，已忽略后一次")
            continue
        rows[question_id] = ParsedQuestion(question_id, sections)
    if not matches:
        warnings.append(f"{source}: 未找到题号，文件已忽略")
    return rows, warnings


def load_ima_directory(raw_dir: Path) -> tuple[dict[str, ParsedQuestion], list[str]]:
    rows: dict[str, ParsedQuestion] = {}
    warnings: list[str] = []
    paths = sorted(
        path for path in raw_dir.iterdir()
        if path.is_file()
        and path.name.lower() != "readme.md"
        and path.suffix.lower() in {".md", ".txt"}
    )
    if not paths:
        raise RuntimeError(f"IMA 回贴目录中没有 .md 或 .txt 文件：{raw_dir}")
    for path in paths:
        parsed, file_warnings = parse_raw_ima_text(path.read_text(encoding="utf-8"), path.name)
        warnings.extend(file_warnings)
        for question_id, row in parsed.items():
            if question_id in rows:
                warnings.append(f"{path.name}: {question_id} 已由另一份回贴提供，已忽略")
                continue
            rows[question_id] = row
    return rows, warnings


def parse_base_questions(markdown: str) -> dict[str, ParsedQuestion]:
    rows: dict[str, ParsedQuestion] = {}
    matches = list(QUESTION_HEADER_RE.finditer(markdown))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        question_id = match.group(1)
        rows[question_id] = ParsedQuestion(question_id, _parse_sections(markdown[match.end() : end]))
    return rows


def page_refs(text: str) -> Counter[str]:
    return Counter(PAGE_REF_RE.findall(text))


def validate_question(base: ParsedQuestion, polished: ParsedQuestion) -> list[str]:
    issues: list[str] = []
    base_names = set(base.sections)
    polished_names = set(polished.sections)
    missing = sorted(base_names - polished_names)
    unknown = sorted(polished_names - base_names)
    if missing:
        issues.append(f"缺少区块：{'、'.join(missing)}")
    if unknown:
        issues.append(f"存在原文没有的区块：{'、'.join(unknown)}")
    for name in sorted(base_names & polished_names):
        before = page_refs(base.sections[name])
        after = page_refs(polished.sections[name])
        if before != after:
            issues.append(
                f"【{name}】页码引用变化：原={dict(before)}，IMA={dict(after)}"
            )
    return issues


def replace_sections(markdown: str, question_id: str, replacements: dict[str, str]) -> str:
    """Replace only a question's editable block bodies and retain all layout."""
    question_match = re.search(rf"(?m)^##\s+{re.escape(question_id)}\s*$", markdown)
    if not question_match:
        raise RuntimeError(f"母版中找不到题号：{question_id}")
    next_match = QUESTION_HEADER_RE.search(markdown, question_match.end())
    question_end = next_match.start() if next_match else len(markdown)
    block = markdown[question_match.end() : question_end]
    headers = list(SECTION_HEADER_RE.finditer(block))
    chunks: list[str] = []
    cursor = 0
    for index, header in enumerate(headers):
        name = header.group(1)
        body_end = headers[index + 1].start() if index + 1 < len(headers) else len(block)
        chunks.append(block[cursor : header.end()])
        if name in replacements:
            chunks.append("\n" + replacements[name].strip() + "\n")
        else:
            chunks.append(block[header.end() : body_end])
        cursor = body_end
    chunks.append(block[cursor:])
    return markdown[: question_match.end()] + "".join(chunks) + markdown[question_end:]


def section_files(base_dir: Path) -> Iterable[Path]:
    return sorted(path for path in base_dir.glob("p*-ch*-h*.md") if path.is_file())


def merge(
    base_dir: Path,
    raw_dir: Path,
    output_dir: Path,
    report_path: Path,
    dry_run: bool,
) -> int:
    polished_rows, warnings = load_ima_directory(raw_dir)
    report: dict[str, object] = {
        "schema_version": "ima_polish_merge_v1",
        "base_dir": str(base_dir),
        "raw_dir": str(raw_dir),
        "output_dir": str(output_dir),
        "dry_run": dry_run,
        "warnings": warnings,
        "sections": [],
    }
    used_ids: set[str] = set()

    for base_path in section_files(base_dir):
        markdown = base_path.read_text(encoding="utf-8")
        base_questions = parse_base_questions(markdown)
        row: dict[str, object] = {
            "file": base_path.name,
            "question_ids": sorted(base_questions),
            "status": "copied_unpolished",
            "issues": [],
        }
        replacements: dict[str, dict[str, str]] = {}
        for question_id, base_question in base_questions.items():
            polished = polished_rows.get(question_id)
            if not polished:
                row["issues"].append(f"{question_id}: 未找到 IMA 回贴")
                continue
            issues = validate_question(base_question, polished)
            if issues:
                row["issues"].append(f"{question_id}: {'；'.join(issues)}")
                continue
            replacements[question_id] = polished.sections

        if replacements and len(replacements) == len(base_questions):
            row["status"] = "merged_needs_emphasis"
            for question_id, blocks in replacements.items():
                markdown = replace_sections(markdown, question_id, blocks)
            used_ids.update(replacements)
        elif replacements:
            row["status"] = "copied_incomplete_ima"
            row["issues"].append("为避免同一小节新旧解析混用，本小节未合并")

        report["sections"].append(row)
        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / base_path.name).write_text(markdown, encoding="utf-8")

    unknown_ids = sorted(set(polished_rows) - used_ids)
    report["unmatched_ima_question_ids"] = unknown_ids
    report["summary"] = {
        "raw_questions": len(polished_rows),
        "merged_questions": len(used_ids),
        "unmatched_ima_questions": len(unknown_ids),
        "warnings": len(warnings),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    print(f"[report] {report_path}")
    if dry_run:
        print("[dry-run] 未写入合并后的 Markdown")
    return 0


def main() -> int:
    here = Path(__file__).resolve().parent
    software_export = here.parent / "output" / "software_export"
    parser = argparse.ArgumentParser(
        description="将 IMA 网页回贴合并回冻结的题库软件版小节 Markdown。"
    )
    parser.add_argument("--base-dir", type=Path, default=software_export / "sections")
    parser.add_argument("--ima-dir", type=Path, default=software_export / "ima_polished_raw")
    parser.add_argument("--output-dir", type=Path, default=software_export / "ima_merged_sections")
    parser.add_argument(
        "--report", type=Path, default=software_export / "ima_merge_report.json"
    )
    parser.add_argument("--dry-run", action="store_true", help="只生成校验报告，不写入 Markdown")
    args = parser.parse_args()
    if not args.base_dir.is_dir():
        parser.error(f"母版小节目录不存在：{args.base_dir}")
    if not args.ima_dir.is_dir():
        parser.error(f"IMA 回贴目录不存在：{args.ima_dir}")
    return merge(args.base_dir, args.ima_dir, args.output_dir, args.report, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
