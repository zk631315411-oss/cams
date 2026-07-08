from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
KG_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(KG_ROOT / "lib"))

from kg_common import (  # noqa: E402
    DEFAULT_KG_WORK_DIR,
    ensure_dir,
    ordered_chapters,
    read_jsonl,
    unit_sort_key,
    write_jsonl,
    write_text,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 1 chapter/section index for v7 KG.")
    parser.add_argument(
        "--eligible-units",
        type=Path,
        default=DEFAULT_KG_WORK_DIR / "phase0_quality_gate" / "eligible_units.jsonl",
    )
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_KG_WORK_DIR / "phase1_chapter_skeleton")
    parser.add_argument("--chapter-limit", type=int, default=5)
    parser.add_argument(
        "--sample-units-out",
        type=Path,
        default=None,
        help="Defaults to phase01_chapter_index/outputs/first_{n}_chapters_units.jsonl.",
    )
    args = parser.parse_args()

    units = sorted(read_jsonl(args.eligible_units), key=unit_sort_key)
    chapters = ordered_chapters(units)[: args.chapter_limit]
    out_dir = ensure_dir(args.out_dir)

    skeletons = [_chapter_skeleton(idx, chapter) for idx, chapter in enumerate(chapters, start=1)]
    write_jsonl(out_dir / "chapter_skeleton.jsonl", skeletons)

    sample_units = _sample_units(skeletons, chapters)
    sample_units_out = args.sample_units_out or DEFAULT_KG_WORK_DIR / "samples" / _sample_filename(args.chapter_limit)
    write_jsonl(sample_units_out, sample_units)
    if args.chapter_limit >= 5 and len(chapters) >= 2:
        write_jsonl(
            DEFAULT_KG_WORK_DIR / "samples" / _sample_filename(2),
            _sample_units(skeletons[:2], chapters[:2]),
        )
    write_text(DEFAULT_KG_WORK_DIR / "markdown" / "phase1_chapter_skeleton_preview.md", _preview_markdown(skeletons))

    summary = {
        "chapter_limit": args.chapter_limit,
        "chapters": [s["chapter_title"] for s in skeletons],
        "sample_units": str(sample_units_out),
        "output_dir": str(out_dir),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _chapter_skeleton(index: int, chapter: dict[str, Any]) -> dict[str, Any]:
    chapter_units = sorted(chapter["units"], key=unit_sort_key)
    chapter_id = f"CH{index:02d}"
    heading_sections = _heading_sections(chapter_id, chapter_units)
    type_counter = Counter(unit.get("type") or "UNKNOWN" for unit in chapter_units)

    return {
        "chapter_id": chapter_id,
        "chapter_title": chapter["chapter"],
        "source": "phase0_eligible_units",
        "unit_count": chapter["unit_count"],
        "pdf_page_span": chapter["pdf_page_span"],
        "printed_page_span": chapter["printed_page_span"],
        "first_unit_id": chapter["first_unit_id"],
        "first_unit_order": chapter["first_unit_order"],
        "type_distribution": dict(type_counter),
        "heading_sections": heading_sections,
        "core_point_ids": [],
        "status": "skeleton_only",
        "notes": [
            "Phase 1 only establishes the chapter/section index and pilot scope.",
            "Core points are generated in Phase 2.",
        ],
    }


def _sample_units(skeletons: list[dict[str, Any]], chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sample_units = []
    for skeleton, chapter in zip(skeletons, chapters):
        section_by_unit_id = _section_index_by_unit_id(skeleton["heading_sections"])
        for unit in chapter["units"]:
            section = section_by_unit_id.get(unit.get("unit_id"), {})
            sample_units.append(
                {
                    "chapter_id": skeleton["chapter_id"],
                    "section_id": section.get("section_id"),
                    "section_order": section.get("section_order"),
                    "section_title": section.get("section_title"),
                    "unit_id": unit.get("unit_id"),
                    "unit_order": unit.get("unit_order"),
                    "type": unit.get("type"),
                    "heading_context": unit.get("heading_context") or [],
                    "knowledge_zh": unit.get("knowledge_zh"),
                    "en_quote": unit.get("en_quote"),
                    "printed_page": unit.get("printed_page"),
                    "pdf_page": unit.get("pdf_page"),
                    "risk_flags": unit.get("risk_flags") or [],
                }
            )
    return sample_units


def _section_index_by_unit_id(sections: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index = {}
    for section in sections:
        for unit_id in section.get("unit_ids", []):
            index[unit_id] = section
    return index


def _heading_sections(chapter_id: str, units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    units = sorted(units, key=unit_sort_key)
    sections = []
    current_title = None
    current_units: list[dict[str, Any]] = []

    for unit in units:
        section_title = _section_title(unit)
        if current_title is None:
            current_title = section_title
            current_units = [unit]
            continue
        if section_title == current_title:
            current_units.append(unit)
            continue
        sections.append(_section_record(chapter_id, len(sections) + 1, current_title, current_units))
        current_title = section_title
        current_units = [unit]

    if current_units and current_title is not None:
        sections.append(_section_record(chapter_id, len(sections) + 1, current_title, current_units))

    return sections


def _section_title(unit: dict[str, Any]) -> str:
    heading = unit.get("heading_context") or []
    return " > ".join(str(part) for part in heading[:3]) if heading else unit.get("chapter") or "UNKNOWN"


def _section_record(
    chapter_id: str,
    section_order: int,
    section_title: str,
    section_units: list[dict[str, Any]],
) -> dict[str, Any]:
    types = Counter(unit.get("type") or "UNKNOWN" for unit in section_units)
    unit_order_span = _ordered_value_span(section_units, "unit_order")
    pdf_page_span = _ordered_page_span(section_units, "page_span", "pdf_page")
    printed_page_span = _ordered_page_span(section_units, "printed_page_span", "printed_page")
    return {
        "section_id": f"{chapter_id}-S{section_order:02d}",
        "section_order": section_order,
        "section_title": section_title,
        "unit_count": len(section_units),
        "unit_ids": [unit.get("unit_id") for unit in section_units],
        "first_unit_id": section_units[0].get("unit_id"),
        "last_unit_id": section_units[-1].get("unit_id"),
        "first_unit_order": section_units[0].get("unit_order"),
        "last_unit_order": section_units[-1].get("unit_order"),
        "unit_order_span": unit_order_span,
        "pdf_page_span": pdf_page_span,
        "printed_page_span": printed_page_span,
        "type_distribution": dict(types),
    }


def _ordered_value_span(units: list[dict[str, Any]], field: str) -> list[Any]:
    values = [unit.get(field) for unit in units if unit.get(field) is not None]
    return _first_last(values)


def _ordered_page_span(units: list[dict[str, Any]], span_field: str, single_field: str) -> list[Any]:
    values: list[Any] = []
    for unit in units:
        span = unit.get(span_field)
        if isinstance(span, list) and span:
            values.extend(value for value in span if value is not None)
        elif unit.get(single_field) is not None:
            values.append(unit.get(single_field))
    return _first_last(values)


def _first_last(values: list[Any]) -> list[Any]:
    if not values:
        return []
    return [values[0]] if values[0] == values[-1] else [values[0], values[-1]]


def _preview_markdown(skeletons: list[dict[str, Any]]) -> str:
    lines = [
        "# Phase 1 Chapter/Section Index Preview",
        "",
        f"本文件展示前 {len(skeletons)} 个教材顺序主题的章节/小节索引，不代表最终 core point。",
        "",
    ]
    for skeleton in skeletons:
        lines.extend(
            [
                f"## {skeleton['chapter_id']} {skeleton['chapter_title']}",
                "",
                f"- eligible units: {skeleton['unit_count']}",
                f"- pdf page span: {skeleton['pdf_page_span']}",
                f"- printed page span: {skeleton['printed_page_span']}",
                "",
                "| section_id | section | units | unit span | pages |",
                "|---|---|---:|---|---|",
            ]
        )
        for section in skeleton["heading_sections"]:
            lines.append(
                f"| {section['section_id']} | {section['section_title']} | {section['unit_count']} | "
                f"{section['first_unit_id']} -> {section['last_unit_id']} | "
                f"PDF {section['pdf_page_span']} / printed {section['printed_page_span']} |"
            )
        lines.append("")
    return "\n".join(lines)


def _sample_filename(chapter_limit: int) -> str:
    names = {
        2: "first_two_chapters_units.jsonl",
        5: "first_five_chapters_units.jsonl",
    }
    return names.get(chapter_limit, f"first_{chapter_limit}_chapters_units.jsonl")


if __name__ == "__main__":
    main()
