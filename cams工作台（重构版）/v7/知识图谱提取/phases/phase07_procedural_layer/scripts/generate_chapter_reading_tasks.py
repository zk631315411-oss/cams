from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
PHASES_DIR = PHASE_DIR.parent

P6_GRAPH_PATH = PHASES_DIR / "phase06_kg_views" / "outputs" / "kg_retrieval_graph.json"
P5_ALIAS_PATH = PHASES_DIR / "phase05_terms" / "outputs" / "p5c_alias_index.json"

OUT_DIR = PHASE_DIR / "outputs"
REPORT_DIR = PHASE_DIR / "reports"

DEFAULT_READERS = ["reader_a_explicit", "reader_b_process"]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def unit_sort_key(unit: dict[str, Any]) -> tuple[int, str]:
    order = unit.get("unit_order")
    return (order if isinstance(order, int) else 10**9, unit.get("unit_id") or "")


def cp_sort_key(cp: dict[str, Any], unit_order_by_id: dict[str, int]) -> tuple[int, str]:
    unit_ids = cp.get("key_unit_ids") or cp.get("anchor_unit_ids") or []
    orders = [unit_order_by_id.get(uid, 10**9) for uid in unit_ids]
    return (min(orders) if orders else 10**9, cp.get("core_point_id") or "")


def load_alias_metadata() -> dict[str, Any]:
    if not P5_ALIAS_PATH.exists():
        return {"status": "missing", "path": str(P5_ALIAS_PATH)}
    payload = read_json(P5_ALIAS_PATH)
    if isinstance(payload, dict):
        count = len(payload.get("alias_groups") or payload.get("terms") or payload)
    elif isinstance(payload, list):
        count = len(payload)
    else:
        count = 0
    return {"status": "available", "path": str(P5_ALIAS_PATH), "estimated_entry_count": count}


def build_tasks(chapter_filter: set[str] | None, readers: list[str]) -> list[dict[str, Any]]:
    graph = read_json(P6_GRAPH_PATH)
    chapters = graph.get("chapters") or []
    sections = {row.get("section_id"): row for row in graph.get("sections") or [] if row.get("section_id")}
    units_by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unit_order_by_id: dict[str, int] = {}
    for unit in graph.get("units") or []:
        unit_id = unit.get("unit_id")
        if unit_id and isinstance(unit.get("unit_order"), int):
            unit_order_by_id[unit_id] = unit["unit_order"]
        section_id = unit.get("section_id")
        if section_id:
            units_by_section[section_id].append(unit)
    for rows in units_by_section.values():
        rows.sort(key=unit_sort_key)

    cps_by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cp in graph.get("core_points") or []:
        section_id = cp.get("section_id")
        if section_id:
            cps_by_section[section_id].append(cp)
    for rows in cps_by_section.values():
        rows.sort(key=lambda cp: cp_sort_key(cp, unit_order_by_id))

    alias_metadata = load_alias_metadata()
    generated_at = datetime.now().isoformat(timespec="seconds")
    tasks: list[dict[str, Any]] = []

    for chapter in chapters:
        chapter_id = chapter.get("chapter_id")
        if not chapter_id or (chapter_filter and chapter_id not in chapter_filter):
            continue
        section_rows: list[dict[str, Any]] = []
        for section_id in chapter.get("section_ids") or []:
            section = sections.get(section_id)
            if not section:
                continue
            cps = cps_by_section.get(section_id, [])
            units = units_by_section.get(section_id, [])
            section_rows.append(
                {
                    "section_id": section_id,
                    "section_order": section.get("section_order"),
                    "section_title": section.get("section_title"),
                    "core_points": [
                        {
                            "core_point_id": cp.get("core_point_id"),
                            "title_en": cp.get("title_en"),
                            "title_zh": cp.get("title_zh"),
                            "reason": cp.get("reason"),
                            "key_unit_ids": cp.get("key_unit_ids") or [],
                            "anchor_unit_ids": cp.get("anchor_unit_ids") or [],
                            "support_unit_ids": cp.get("support_unit_ids") or [],
                        }
                        for cp in cps
                    ],
                    "units": [
                        {
                            "unit_id": unit.get("unit_id"),
                            "unit_order": unit.get("unit_order"),
                            "knowledge_zh": unit.get("knowledge_zh"),
                            "en_quote": unit.get("en_quote"),
                            "printed_page": unit.get("printed_page"),
                            "pdf_page": unit.get("pdf_page"),
                        }
                        for unit in units
                    ],
                }
            )
        section_rows.sort(key=lambda row: (row.get("section_order") or 10**9, row.get("section_id") or ""))
        for reader_role in readers:
            tasks.append(
                {
                    "task_id": f"p7read_{chapter_id}_{reader_role}",
                    "schema_version": "p7_chapter_reading_task_v1",
                    "generated_at": generated_at,
                    "reader_role": reader_role,
                    "chapter_id": chapter_id,
                    "chapter_title": chapter.get("chapter_title"),
                    "unit_count": chapter.get("unit_count"),
                    "required_sections": section_rows,
                    "allowed_bridge_context": [],
                    "alias_index": alias_metadata,
                    "output_schema": "process_card_v1",
                    "instructions": {
                        "read_in_textbook_order": True,
                        "preserve_full_chapter_context": True,
                        "output_chapter_flow_overview_zh": True,
                        "output_section_process_cards": True,
                        "short_edges_only": True,
                        "do_not_generate_full_book_workflow": True,
                    },
                }
            )
    return tasks


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate P7 chapter reading tasks from the P6 base KG.")
    parser.add_argument("--chapters", nargs="*", help="Optional chapter IDs, e.g. CH42 CH47. Defaults to all chapters.")
    parser.add_argument("--readers", nargs="*", default=DEFAULT_READERS, help="Reader roles to generate.")
    parser.add_argument("--output", default=str(OUT_DIR / "p7_chapter_reading_tasks.jsonl"))
    args = parser.parse_args()

    chapter_filter = set(args.chapters) if args.chapters else None
    tasks = build_tasks(chapter_filter, args.readers)
    out_path = Path(args.output)
    write_jsonl(out_path, tasks)

    chapter_counts = defaultdict(int)
    for task in tasks:
        chapter_counts[task["chapter_id"]] += 1

    report_lines = [
        "# P7 Chapter Reading Task Report",
        "",
        f"generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"task_count: {len(tasks)}",
        f"chapter_count: {len(chapter_counts)}",
        f"reader_roles: {', '.join(args.readers)}",
        f"output: {out_path}",
        "",
        "## Chapters",
        "",
    ]
    for chapter_id in sorted(chapter_counts):
        report_lines.append(f"- {chapter_id}: {chapter_counts[chapter_id]} tasks")
    write_text(REPORT_DIR / "p7_chapter_reading_task_report.md", "\n".join(report_lines) + "\n")

    print(f"Wrote {len(tasks)} tasks to {out_path}")


if __name__ == "__main__":
    main()

