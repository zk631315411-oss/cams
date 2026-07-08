from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from materialize_stratified_table_units import is_non_content_table, parse_table


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DRY_RUN_DIR = BASE_UNITS_DIR / "fullbook_dry_run"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: str, limit: int = 260) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def is_list_parent(block: dict, next_block: dict | None) -> bool:
    if block.get("block_type") != "paragraph" or not next_block:
        return False
    if next_block.get("block_type") not in {"list_item", "numbered_item"}:
        return False
    text = str(block.get("text", "")).strip()
    text_l = text.lower()
    if text.endswith(":"):
        return True
    parent_markers = [
        "include the following",
        "includes the following",
        "include:",
        "includes:",
        "as follows",
        "following:",
        "examples include",
        "common red flags",
        "red flags include",
    ]
    return any(marker in text_l for marker in parent_markers)


def is_front_matter_noise(block: dict) -> bool:
    heading = " / ".join(block.get("heading_stack", [])).lower()
    text = str(block.get("text", "")).strip()
    text_l = text.lower()
    pdf_page = block.get("pdf_page")
    front_heading_markers = [
        "certified anti-money laundering specialist task force",
        "acams product staff",
        "acams",
        "credits",
        "copyright",
    ]
    if block.get("printed_page") is not None:
        return False
    if isinstance(pdf_page, int) and pdf_page > 12:
        return False
    if any(marker in heading for marker in front_heading_markers):
        return True
    if "©" in text or "copyright" in text_l or "all rights reserved" in text_l:
        return True
    credential_hits = sum(token in text for token in ["CAMS", "CAFS", "CGSS", "CCAS", "CTMA", "CKYCA"])
    comma_count = text.count(",")
    return credential_hits >= 2 and comma_count >= 2


def is_learning_objective_parent(block: dict) -> bool:
    text_l = str(block.get("text", "")).strip().lower()
    return "after completing this learning experience" in text_l and "able to" in text_l


def is_learning_objective_item(block: dict, prev_block: dict | None) -> bool:
    if block.get("block_type") not in {"list_item", "numbered_item"}:
        return False
    text_l = re.sub(r"^\s*[•*\-]\s*", "", str(block.get("text", "")).strip().lower())
    objective_verbs = (
        "describe ",
        "explain ",
        "identify ",
        "define ",
        "discuss ",
        "recognize ",
        "understand ",
        "compare ",
        "distinguish ",
        "assess ",
        "apply ",
    )
    if not text_l.startswith(objective_verbs):
        return False
    if prev_block and is_learning_objective_parent(prev_block):
        return True
    heading = " / ".join(block.get("heading_stack", [])).lower()
    return "learning objectives" in heading


def is_student_note_cross_reference(block: dict) -> bool:
    heading = " / ".join(block.get("heading_stack", [])).lower()
    text_l = str(block.get("text", "")).strip().lower()
    if "student note" not in heading:
        return False
    cross_reference_markers = [
        "please refer to ",
        "refer to ",
        "see ",
        "see also ",
    ]
    return any(text_l.startswith(marker) for marker in cross_reference_markers)


def is_glossary_heading(block: dict) -> bool:
    text = str(block.get("text", "")).strip().lower().lstrip("#").strip()
    heading = " / ".join(block.get("heading_stack", [])).lower()
    return block.get("block_type") == "heading" and (text == "glossary" or heading.endswith("/ glossary"))


def has_terminal_punctuation(text: str) -> bool:
    return text.strip().rstrip("\"'”’)]}").endswith((".", "!", "?", ";", ":", "。", "！", "？", "；"))


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9/]+", text))


def is_visual_text_fragment(block: dict, prev_block: dict | None, next_block: dict | None) -> bool:
    if block.get("block_type") != "paragraph":
        return False
    text = str(block.get("text", "")).strip()
    if not text or has_terminal_punctuation(text):
        return False
    if len(block.get("sentences", [])) > 1:
        return False
    if word_count(text) > 8:
        return False

    risk_flags = set(block.get("risk_flags", []))
    if {"block_may_continue_next", "previous_block_may_continue_here", "cross_block_sentence_candidate"} & risk_flags:
        return True

    nearby_short_fragment = False
    for nearby in [prev_block, next_block]:
        if not nearby or nearby.get("block_type") != "paragraph":
            continue
        nearby_text = str(nearby.get("text", "")).strip()
        if nearby_text and not has_terminal_punctuation(nearby_text) and word_count(nearby_text) <= 8:
            nearby_short_fragment = True
    return nearby_short_fragment


def is_short_context_label(block: dict) -> bool:
    if block.get("block_type") != "paragraph":
        return False
    text = str(block.get("text", "")).strip()
    if not text or has_terminal_punctuation(text):
        return False
    if len(block.get("sentences", [])) > 1:
        return False
    if word_count(text) > 6:
        return False
    risk_flags = set(block.get("risk_flags", []))
    if {"block_may_continue_next", "previous_block_may_continue_here", "cross_block_sentence_candidate"} & risk_flags:
        return False
    return True


def continuation_risk_flags_from_visual_fragments(
    block: dict,
    prev_block: dict | None,
    next_block: dict | None,
    risk_flags: list[str],
) -> list[str]:
    cleaned = list(risk_flags)
    if "previous_block_may_continue_here" in cleaned and prev_block and is_visual_text_fragment(prev_block, None, block):
        cleaned = [flag for flag in cleaned if flag != "previous_block_may_continue_here"]
    if (
        ("block_may_continue_next" in cleaned or "cross_block_sentence_candidate" in cleaned)
        and next_block
        and is_visual_text_fragment(next_block, block, None)
    ):
        cleaned = [
            flag
            for flag in cleaned
            if flag not in {"block_may_continue_next", "cross_block_sentence_candidate"}
        ]
    return cleaned


def llm_window_estimate(sentence_count: int) -> int:
    if sentence_count <= 0:
        return 1
    if sentence_count <= 8:
        return 1
    # Long paragraphs use a 6-sentence sliding window with 1-sentence overlap.
    return max(1, math.ceil((sentence_count - 1) / 5))


def route_block(
    block: dict,
    prev_block: dict | None,
    next_block: dict | None,
    in_learning_objectives: bool = False,
    in_glossary: bool = False,
) -> dict:
    block_type = block.get("block_type")
    content_status = block.get("content_status")
    text = str(block.get("text", ""))
    sentence_count = len(block.get("sentences", []))
    risk_flags = continuation_risk_flags_from_visual_fragments(
        block,
        prev_block,
        next_block,
        list(block.get("risk_flags", [])),
    )
    route = ""
    evidence_status = "ignored"
    reason = ""
    estimated_llm_windows = 0
    table_rows = 0
    table_cells = 0

    if in_glossary or is_glossary_heading(block):
        route = "ignored_glossary"
        reason = "glossary/acronym list is reference metadata, not a textbook knowledge unit"
    elif is_front_matter_noise(block):
        route = "ignored_front_matter_noise"
        reason = "front matter credits/staff/name-list block without printed page"
    elif is_learning_objective_parent(block) or in_learning_objectives or is_learning_objective_item(block, prev_block):
        route = "ignored_learning_objective"
        reason = "learning objective text is teaching metadata, not a textbook knowledge unit"
    elif is_student_note_cross_reference(block):
        route = "ignored_student_note_cross_reference"
        reason = "student note cross-reference is teaching navigation, not a standalone evidence unit"
    elif content_status != "content_candidate":
        route = "ignored_non_content"
        reason = f"content_status={content_status}"
    elif block_type == "heading":
        route = "ignored_heading_context"
        reason = "heading is context, not a direct evidence unit"
    elif is_visual_text_fragment(block, prev_block, next_block):
        route = "ignored_visual_text_fragment"
        reason = "short phrase appears to be figure/table/OCR text, not a standalone textbook knowledge unit"
    elif is_short_context_label(block):
        route = "ignored_short_context_label"
        reason = "short label without terminal punctuation is structural context, not a standalone evidence unit"
    elif block_type in {"list_item", "numbered_item"}:
        route = "direct_list_item_candidate"
        evidence_status = "direct_candidate"
        reason = "list item can be materialized by rule"
        if not prev_block or prev_block.get("block_type") not in {"paragraph", "list_item", "numbered_item"}:
            risk_flags.append("orphan_list_item_context_check")
    elif block_type == "table":
        rows = parse_table(str(block.get("raw_md", "")))
        table_rows = max(0, len(rows) - 1)
        if rows:
            table_cells = sum(max(0, len(row) - 1) for row in rows[1:])
        if is_non_content_table(block):
            route = "ignored_non_content_table"
            reason = "table appears to be acknowledgements/credits/contents"
        elif len(rows) >= 2 and len(rows[0]) >= 2:
            route = "needs_parser_table"
            evidence_status = "needs_parser"
            reason = "content table requires table parser before direct evidence"
        else:
            route = "needs_review_table"
            evidence_status = "needs_review"
            reason = "table structure is not parseable as a simple header table"
    elif block_type == "paragraph" and is_list_parent(block, next_block):
        route = "direct_list_parent_candidate"
        evidence_status = "direct_candidate"
        reason = "paragraph introduces following list items"
    elif block_type == "paragraph":
        route = "needs_llm_paragraph"
        evidence_status = "needs_llm"
        estimated_llm_windows = llm_window_estimate(sentence_count)
        reason = "prose paragraph requires sentence grouping before direct evidence"
        if sentence_count == 0:
            risk_flags.append("paragraph_without_sentence_slices")
        if sentence_count > 8:
            risk_flags.append("long_paragraph_sliding_window_required")
    else:
        route = "needs_review_unknown_block"
        evidence_status = "needs_review"
        reason = f"unhandled block_type={block_type}"

    return {
        "block_id": block.get("block_id"),
        "route": route,
        "evidence_status": evidence_status,
        "reason": reason,
        "block_type": block_type,
        "content_status": content_status,
        "pdf_page": block.get("pdf_page"),
        "printed_page": block.get("printed_page"),
        "heading_context": block.get("heading_stack", []),
        "sentence_count": sentence_count,
        "estimated_llm_windows": estimated_llm_windows,
        "table_rows": table_rows,
        "table_cells": table_cells,
        "risk_flags": sorted(set(risk_flags)),
        "text_head": compact(text),
    }


def build_rows(blocks: list[dict]) -> list[dict]:
    rows = []
    in_learning_objectives = False
    in_glossary = False
    glossary_chapter: str | None = None
    for idx, block in enumerate(blocks):
        prev_block = blocks[idx - 1] if idx > 0 else None
        next_block = blocks[idx + 1] if idx + 1 < len(blocks) else None
        chapter = (block.get("heading_stack") or [None])[0]
        if in_glossary and chapter != glossary_chapter:
            in_glossary = False
            glossary_chapter = None
        if is_glossary_heading(block):
            in_glossary = True
            glossary_chapter = chapter
        if in_learning_objectives and block.get("block_type") not in {"list_item", "numbered_item"}:
            in_learning_objectives = False
        row = route_block(block, prev_block, next_block, in_learning_objectives, in_glossary)
        rows.append(row)
        if is_learning_objective_parent(block):
            in_learning_objectives = True
    return rows


def build_report(rows: list[dict]) -> str:
    by_route = Counter(row["route"] for row in rows)
    by_status = Counter(row["evidence_status"] for row in rows)
    by_block_type = Counter(row["block_type"] for row in rows)
    llm_rows = [row for row in rows if row["evidence_status"] == "needs_llm"]
    parser_rows = [row for row in rows if row["evidence_status"] == "needs_parser"]
    review_rows = [row for row in rows if row["evidence_status"] == "needs_review"]
    direct_rows = [row for row in rows if row["evidence_status"] == "direct_candidate"]
    estimated_llm_windows = sum(row.get("estimated_llm_windows", 0) for row in llm_rows)
    parseable_table_cells = sum(row.get("table_cells", 0) for row in parser_rows)

    lines = [
        "# v7 Fullbook Base Unit Routing Dry Run",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Summary",
        "",
        f"- total blocks: {len(rows)}",
        f"- direct rule candidates: {len(direct_rows)}",
        f"- needs LLM paragraphs: {len(llm_rows)}",
        f"- estimated LLM windows: {estimated_llm_windows}",
        f"- needs parser tables: {len(parser_rows)}",
        f"- parseable table cells: {parseable_table_cells}",
        f"- needs review: {len(review_rows)}",
        f"- by route: {json.dumps(dict(by_route), ensure_ascii=False)}",
        f"- by evidence_status: {json.dumps(dict(by_status), ensure_ascii=False)}",
        f"- by block_type: {json.dumps(dict(by_block_type), ensure_ascii=False)}",
        "",
        "## Needs Review Examples",
        "",
    ]
    for row in review_rows[:25]:
        lines.extend(
            [
                f"### {row['block_id']} · {row['route']}",
                "",
                f"- page: {row.get('printed_page')} / pdf {row.get('pdf_page')}",
                f"- heading: {' / '.join(row.get('heading_context', []))}",
                f"- reason: {row.get('reason')}",
                f"- text: {row.get('text_head')}",
                f"- risk_flags: {json.dumps(row.get('risk_flags', []), ensure_ascii=False)}",
                "",
            ]
        )
    lines.extend(["## Large Route Examples", ""])
    for route in ["needs_llm_paragraph", "needs_parser_table", "direct_list_parent_candidate", "direct_list_item_candidate"]:
        examples = [row for row in rows if row["route"] == route][:10]
        lines.extend([f"### {route}", ""])
        for row in examples:
            lines.extend(
                [
                    f"- `{row['block_id']}` P{row.get('printed_page')} / pdf {row.get('pdf_page')}: {row.get('text_head')}",
                ]
            )
        lines.append("")
    return "\n".join(lines)


def build_chapter_summary(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        heading = row.get("heading_context", [])
        top = heading[0] if heading else "(no heading)"
        grouped[top].append(row)
    summary = []
    for top, items in grouped.items():
        summary.append(
            {
                "chapter": top,
                "blocks": len(items),
                "routes": dict(Counter(row["route"] for row in items)),
                "estimated_llm_windows": sum(row.get("estimated_llm_windows", 0) for row in items),
                "direct_candidates": sum(1 for row in items if row["evidence_status"] == "direct_candidate"),
                "needs_review": sum(1 for row in items if row["evidence_status"] == "needs_review"),
            }
        )
    return sorted(summary, key=lambda item: item["chapter"])


def main() -> None:
    blocks = read_json(BASE_UNITS_DIR / "patched" / "v7_en_blocks.patched.json")["items"]
    rows = build_rows(blocks)
    payload = {
        "schema_version": "v7_fullbook_routing_dry_run_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "dry_run_no_units_no_llm_calls",
        "items": rows,
        "chapter_summary": build_chapter_summary(rows),
    }
    write_json(DRY_RUN_DIR / "v7_fullbook_routing_dry_run.json", payload)
    (DRY_RUN_DIR / "v7_fullbook_routing_dry_run_report.md").write_text(
        build_report(rows),
        encoding="utf-8",
    )
    print(f"routed blocks: {len(rows)}")
    print(f"wrote: {DRY_RUN_DIR / 'v7_fullbook_routing_dry_run.json'}")
    print(f"wrote: {DRY_RUN_DIR / 'v7_fullbook_routing_dry_run_report.md'}")


if __name__ == "__main__":
    main()
