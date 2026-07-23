#!/usr/bin/env python3
"""Rebuild V7 textbook structure from corrected bilingual MinerU Markdown.

This tool deliberately preserves frozen V7 unit identities. It uses each
unit's existing English source quote only to locate the unit under the repaired
Markdown heading tree; it does not group sentences, call a model, or alter PDF
assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


class StructureError(ValueError):
    """Raised when the corrected Markdown cannot safely replace the old structure."""


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
EN_PAGE_RE = re.compile(r"\s*\(Page\s+\d+\)\s*$", re.IGNORECASE)
ZH_PAGE_RE = re.compile(r"\s*\(第\s*\d+\s*页\)\s*$")
UNIT_ID_RE = re.compile(r"^v7u_N\d+$")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise StructureError(f"Missing required input: {path}") from exc


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StructureError(f"Missing required input: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StructureError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_text(value: str) -> str:
    value = str(value or "").lower()
    value = value.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    value = re.sub(r"[\u2010\u2011\u2012\u2013\u2014]", "-", value)
    value = re.sub(r"(?<=\w)-(?=\w)", "", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+([,.;:!?])", r"\1", value)
    return value.strip()


def canonical_match_text(value: str) -> str:
    return "".join(character for character in normalize_text(value) if character.isalnum())


def title_without_page(title: str, language: str) -> str:
    return (EN_PAGE_RE if language == "en" else ZH_PAGE_RE).sub("", title).strip()


def normalize_title(value: str) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", normalize_text(value))


@dataclass(frozen=True)
class Heading:
    line: int
    level: int
    title: str


@dataclass(frozen=True)
class TextBlock:
    index: int
    line_start: int
    line_end: int
    text: str
    normalized: str
    canonical: str
    heading_indices: tuple[int, ...]


def parse_headings(lines: list[str]) -> list[Heading]:
    headings = []
    for index, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            headings.append(Heading(index, len(match.group(1)), match.group(2)))
    return headings


def body_start(headings: list[Heading], language: str) -> int:
    """Find the repeated, page-free first module heading after the Markdown TOC."""
    prior: set[str] = set()
    for heading in headings:
        bare = title_without_page(heading.title, language)
        page_annotated = bare != heading.title
        if heading.level == 1 and not page_annotated and bare in prior:
            return heading.line
        prior.add(bare)
    raise StructureError(f"Cannot identify the {language} Markdown body after its table of contents")


def body_headings(lines: list[str], language: str) -> list[Heading]:
    headings = parse_headings(lines)
    start = body_start(headings, language)
    return [Heading(item.line, item.level, title_without_page(item.title, language)) for item in headings if item.line >= start]


def semantic_heading_anchors(
    en: list[Heading], zh: list[Heading], alignment_path: Path, semantic_audit_path: Path
) -> dict[int, str]:
    """Load verified semantic titles only as anchors for the current Markdown."""
    alignment = read_json(alignment_path).get("alignment") or []
    inserted = {
        str(row.get("english") or ""): str(row.get("chinese") or "")
        for row in read_json(semantic_audit_path).get("inserted_chinese_headings") or []
    }
    anchors: dict[int, str] = {}
    for row in alignment:
        index = row.get("target_index")
        if index is None:
            continue
        if not isinstance(index, int) or index < 0 or index >= len(en):
            raise StructureError("Semantic heading ledger contains an invalid English node index")
        if normalize_title(str(row.get("english") or "")) != normalize_title(en[index].title):
            raise StructureError(f"Semantic heading ledger no longer matches English node {index + 1}")
        chinese = str(row.get("chinese") or inserted.get(str(row.get("english") or "")) or "")
        # The historical ledger occasionally matched an OCR fragment to a
        # same-named heading far away in the book. A current-MD anchor must be
        # a local occurrence; distant lookalikes are not evidence of pairing.
        if chinese and any(
            normalize_title(chinese) == normalize_title(item.title) and abs(zh_index - index) <= 30
            for zh_index, item in enumerate(zh)
        ):
            anchors[index] = chinese
    return anchors


def align_bilingual_headings(
    en: list[Heading],
    zh: list[Heading],
    semantic_alignment_path: Path,
    semantic_audit_path: Path,
) -> tuple[dict[int, int], list[dict[str, Any]], list[dict[str, Any]], int]:
    """Align the current body structure, using semantic titles only as exact anchors.

    The former translation audit contains placeholder glossary entries and cannot
    describe the corrected Markdown tree. A semantic title helps only when it is
    an exact match to a heading in the current Chinese Markdown.
    """
    anchors = semantic_heading_anchors(en, zh, semantic_alignment_path, semantic_audit_path)
    current_zh = [normalize_title(item.title) for item in zh]
    rows_count = len(en)
    cols_count = len(zh)
    negative = -10**9
    scores = [[negative] * (cols_count + 1) for _ in range(rows_count + 1)]
    moves: list[list[str | None]] = [[None] * (cols_count + 1) for _ in range(rows_count + 1)]
    scores[0][0] = 0
    for column in range(1, cols_count + 1):
        scores[0][column] = scores[0][column - 1] - 5
        moves[0][column] = "skip"
    for row in range(1, rows_count + 1):
        for column in range(row, cols_count + 1):
            en_index = row - 1
            same_level = en[en_index].level == zh[column - 1].level
            match_score = 15 if same_level else -15
            take = scores[row - 1][column - 1] + match_score
            skip = scores[row][column - 1] - 6 if scores[row][column - 1] != negative else negative
            if take >= skip:
                scores[row][column] = take
                moves[row][column] = "take"
            else:
                scores[row][column] = skip
                moves[row][column] = "skip"
    if scores[rows_count][cols_count] == negative:
        raise StructureError("Chinese heading sequence cannot cover every English structural node")

    baseline_pairs: dict[int, int] = {}
    row = rows_count
    column = cols_count
    while row:
        move = moves[row][column]
        if move == "take":
            baseline_pairs[row - 1] = column - 1
            row -= 1
            column -= 1
        elif move == "skip":
            column -= 1
        else:
            raise StructureError("Bilingual heading alignment has no valid backtracking route")
    # Lock every local, same-level semantic anchor independently. This permits
    # the two language editions to order sibling headings differently while
    # preventing a nearby OCR fragment from displacing a verified title.
    anchor_candidates: dict[int, list[int]] = {}
    for en_index, expected in anchors.items():
        candidates = [
            zh_index
            for zh_index, title in enumerate(current_zh)
            if title == normalize_title(expected)
            and en[en_index].level == zh[zh_index].level
            and abs(zh_index - en_index) <= 30
        ]
        if candidates:
            anchor_candidates[en_index] = sorted(candidates, key=lambda item: (abs(item - en_index), item))

    pairs: dict[int, int] = {}
    used_zh: set[int] = set()
    for en_index in sorted(anchor_candidates, key=lambda item: (len(anchor_candidates[item]), abs(anchor_candidates[item][0] - item), item)):
        candidate = next((item for item in anchor_candidates[en_index] if item not in used_zh), None)
        if candidate is not None:
            pairs[en_index] = candidate
            used_zh.add(candidate)

    # The remaining nodes have no current-MD semantic title anchor. Keep their
    # original structural placement where possible, then select the closest
    # available node of the same level.
    for en_index in range(rows_count):
        if en_index in pairs:
            continue
        preferred = baseline_pairs[en_index]
        if preferred not in used_zh:
            candidate = preferred
        else:
            available = [index for index in range(cols_count) if index not in used_zh]
            candidate = min(
                available,
                key=lambda index: (
                    0 if en[en_index].level == zh[index].level else 1,
                    abs(index - preferred),
                    abs(index - en_index),
                ),
            )
        pairs[en_index] = candidate
        used_zh.add(candidate)

    anchor_mismatches = [
        en_index
        for en_index, expected in anchors.items()
        if en_index in pairs and normalize_title(expected) != current_zh[pairs[en_index]]
    ]
    heading_changes = [
        {
            "english_node_id": f"node-{index + 1:04d}",
            "expected_chinese_title": anchors[index],
            "selected_chinese_node_id": f"node-{pairs[index] + 1:04d}",
            "selected_chinese_title": zh[pairs[index]].title,
            "reason": "no_unique_local_semantic_anchor_in_current_markdown",
        }
        for index in anchor_mismatches
    ]
    chinese_only = [
        {
            "chinese_node_id": f"node-{index + 1:04d}",
            "title_zh": zh[index].title,
            "level": zh[index].level,
        }
        for index in range(len(zh))
        if index not in used_zh
    ]
    verified_anchor_pairs = sum(
        1
        for en_index, expected in anchors.items()
        if normalize_title(expected) == current_zh[pairs[en_index]]
    )
    return pairs, chinese_only, heading_changes, verified_anchor_pairs


def heading_stacks(headings: list[Heading]) -> list[tuple[int, ...]]:
    stack: list[int] = []
    out = []
    for index, heading in enumerate(headings):
        stack = [item for item in stack if headings[item].level < heading.level]
        stack.append(index)
        out.append(tuple(stack))
    return out


def is_content_line(line: str) -> bool:
    value = line.strip()
    return bool(value and not value.startswith("<!--") and not value.startswith("![](") and not value.startswith("<img"))


def english_text_blocks(lines: list[str], headings: list[Heading]) -> list[TextBlock]:
    by_line = {heading.line: index for index, heading in enumerate(headings)}
    stacks = heading_stacks(headings)
    blocks: list[TextBlock] = []
    current: list[str] = []
    line_start = 0
    current_stack: tuple[int, ...] = ()

    def flush(line_end: int) -> None:
        nonlocal current
        text = "\n".join(current).strip()
        normalized = normalize_text(text)
        if normalized:
            blocks.append(TextBlock(len(blocks) + 1, line_start, line_end, text, normalized, canonical_match_text(text), current_stack))
        current = []

    active_stack: tuple[int, ...] = ()
    for line_number, line in enumerate(lines, start=1):
        if line_number in by_line:
            flush(line_number - 1)
            active_stack = stacks[by_line[line_number]]
            continue
        if not active_stack:
            continue
        if not line.strip():
            flush(line_number - 1)
            continue
        if not current:
            line_start = line_number
            current_stack = active_stack
        if is_content_line(line):
            current.append(line.strip())
    flush(len(lines))
    merged: list[TextBlock] = []
    for block in blocks:
        if (
            merged
            and merged[-1].heading_indices == block.heading_indices
            and merged[-1].text.rstrip()[-1:] not in ".?!:;"
        ):
            previous = merged.pop()
            text = previous.text + "\n" + block.text
            merged.append(TextBlock(previous.index, previous.line_start, block.line_end, text, normalize_text(text), canonical_match_text(text), previous.heading_indices))
        else:
            merged.append(block)
    return [TextBlock(index, block.line_start, block.line_end, block.text, block.normalized, block.canonical, block.heading_indices) for index, block in enumerate(merged, start=1)]


def block_num(unit: dict[str, Any]) -> int:
    candidates = [(unit.get("source") or {}).get("en_block_id"), *(unit.get("en_sentence_ids") or [])]
    for candidate in candidates:
        match = re.search(r"b(\d+)", str(candidate or ""))
        if match:
            return int(match.group(1))
    return 10**9


def unit_sort_key(unit: dict[str, Any]) -> tuple[int, int, str]:
    return (block_num(unit), int(unit.get("unit_order") or 0), str(unit.get("unit_id") or ""))


def matching_blocks(unit: dict[str, Any], blocks: list[TextBlock]) -> list[tuple[TextBlock, str]]:
    quote = normalize_text(str(unit.get("en_quote") or ""))
    if not quote:
        return []
    quote_canonical = canonical_match_text(str(unit.get("en_quote") or ""))
    exact = [(block, "canonical_quote") for block in blocks if quote_canonical in block.canonical]
    if exact:
        return exact
    quote_words = re.findall(r"[a-z0-9]+", quote)
    if len(quote_words) < 12:
        return []
    anchor = quote_words[:8]
    tail = quote_words[-8:]
    near_matches = []
    for block in blocks:
        words = re.findall(r"[a-z0-9]+", block.normalized)
        for start in range(max(0, len(words) - len(anchor) + 1)):
            if words[start : start + len(anchor)] != anchor:
                continue
            candidate = words[start : start + len(quote_words)]
            if len(candidate) != len(quote_words) or candidate[-len(tail) :] != tail:
                continue
            ratio = SequenceMatcher(a=" ".join(quote_words), b=" ".join(candidate), autojunk=False).ratio()
            if ratio >= 0.995:
                near_matches.append((block, "near_exact_ocr_variation"))
    return near_matches


def choose_block(unit: dict[str, Any], candidates: list[TextBlock], previous_line: int) -> tuple[TextBlock, bool]:
    forward = [candidate for candidate in candidates if candidate.line_start >= previous_line]
    if not forward:
        raise StructureError(f"{unit.get('unit_id')}: English quote has no match after its prior source block")
    first_line = min(candidate.line_start for candidate in forward)
    earliest = [candidate for candidate in forward if candidate.line_start == first_line]
    if len(earliest) != 1:
        raise StructureError(f"{unit.get('unit_id')}: English quote has multiple matches at Markdown line {first_line}")
    return earliest[0], len(candidates) > 1


def title_for_stack(headings: list[Heading], stack: tuple[int, ...]) -> list[str]:
    return [headings[index].title for index in stack]


def chapter_tree(
    en: list[Heading],
    zh: list[Heading],
    en_to_zh: dict[int, int],
    unit_nodes: dict[str, tuple[int, ...]],
) -> list[dict[str, Any]]:
    stacks = heading_stacks(zh)
    en_for_zh = {zh_index: en_index for en_index, zh_index in en_to_zh.items()}
    children: dict[int | None, list[int]] = {}
    for index, stack in enumerate(stacks):
        parent = stack[-2] if len(stack) > 1 else None
        children.setdefault(parent, []).append(index)
    units_by_node: dict[int, list[str]] = {index: [] for index in range(len(zh))}
    for unit_id, stack in unit_nodes.items():
        units_by_node[en_to_zh[stack[-1]]].append(unit_id)

    def build(index: int, top_index: int) -> dict[str, Any]:
        nested = [build(child, top_index) for child in children.get(index, [])]
        direct_ids = units_by_node[index]
        all_ids = list(direct_ids)
        for child in nested:
            all_ids.extend(child["unit_ids"])
        item = {
            "node_id": f"node-{index + 1:04d}",
            "title": en[en_for_zh[index]].title if index in en_for_zh else zh[index].title,
            "title_en": en[en_for_zh[index]].title if index in en_for_zh else "",
            "title_zh": zh[index].title,
            "level": zh[index].level,
            "unit_ids": all_ids,
            "direct_unit_ids": direct_ids,
        }
        if nested:
            item["children"] = nested
        if index == top_index:
            item["chapter_id"] = f"chapter-{top_index + 1:02d}"
        return item

    return [build(index, index) for index in children.get(None, [])]


def validate_units(units: list[dict[str, Any]], page_map: dict[str, Any]) -> None:
    ids = [str(unit.get("unit_id") or "") for unit in units]
    if len(ids) != 4973:
        raise StructureError(f"Expected 4973 frozen units, found {len(ids)}")
    if any(not UNIT_ID_RE.fullmatch(unit_id) for unit_id in ids):
        raise StructureError("Frozen units include a non-V7 identifier")
    if len(set(ids)) != len(ids):
        raise StructureError("Frozen units contain duplicate unit_id values")
    pages = {item.get("en_pdf_page") for item in page_map.get("items") or []}
    invalid = [unit["unit_id"] for unit in units if unit.get("pdf_page") not in pages]
    if invalid:
        raise StructureError(f"Units point to pages outside the bilingual PDF map: {', '.join(invalid[:5])}")


def remap(
    units_path: Path,
    en_md: Path,
    zh_md: Path,
    page_map_path: Path,
    semantic_alignment_path: Path,
    semantic_audit_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    units_payload = read_json(units_path)
    units = deepcopy(units_payload.get("units") or [])
    page_map = read_json(page_map_path)
    validate_units(units, page_map)
    en_lines = read_text(en_md).splitlines()
    zh_lines = read_text(zh_md).splitlines()
    en_headings = body_headings(en_lines, "en")
    zh_headings = body_headings(zh_lines, "zh")
    try:
        en_content_end = next(index for index, item in enumerate(en_headings) if item.title == "Glossary")
    except StopIteration as exc:
        raise StructureError("English Markdown body has no Glossary boundary") from exc
    glossary_starts = [index for index, item in enumerate(zh_headings) if item.level == 2]
    if not glossary_starts:
        raise StructureError("Chinese Markdown body has no level-2 Glossary boundary")
    zh_content_end = glossary_starts[-1]
    en_content = en_headings[:en_content_end]
    zh_content = zh_headings[:zh_content_end]
    en_to_zh, chinese_only_nodes, heading_changes, semantic_anchor_count = align_bilingual_headings(
        en_content, zh_content, semantic_alignment_path, semantic_audit_path
    )
    zh_stacks = heading_stacks(zh_content)
    blocks = english_text_blocks(en_lines, en_headings)
    if not blocks:
        raise StructureError("The English Markdown body contains no text blocks")

    unit_nodes: dict[str, tuple[int, ...]] = {}
    mapping_rows = []
    previous_line = 0
    order_disambiguated_count = 0
    for unit in sorted(units, key=unit_sort_key):
        candidate_rows = matching_blocks(unit, blocks)
        if not candidate_rows:
            raise StructureError(f"{unit.get('unit_id')}: English quote is absent from the corrected Markdown")
        candidates = [row[0] for row in candidate_rows]
        methods = {block.index: method for block, method in candidate_rows}
        block, order_disambiguated = choose_block(unit, candidates, previous_line)
        match_method = methods[block.index]
        order_disambiguated_count += int(order_disambiguated)
        previous_line = max(previous_line, block.line_start)
        stack = block.heading_indices
        if not stack:
            raise StructureError(f"{unit.get('unit_id')}: matched Markdown block has no heading context")
        if max(stack) >= en_content_end:
            raise StructureError(f"{unit.get('unit_id')}: points into the excluded English glossary")
        unit["chapter"] = en_headings[stack[1] if len(stack) > 1 else stack[0]].title
        unit["heading_context"] = title_for_stack(en_headings, stack)
        unit["heading_context_zh"] = title_for_stack(zh_headings, zh_stacks[en_to_zh[stack[-1]]])
        unit.setdefault("source", {})["structure_mapping"] = {
            "method": "corrected_bilingual_markdown_exact_quote_v1",
            "markdown_match_method": match_method,
            "en_markdown_block": f"v7en_struct_b{block.index:05d}",
            "en_markdown_lines": [block.line_start, block.line_end],
            "heading_node_ids": [f"node-{index + 1:04d}" for index in stack],
            "order_disambiguated": order_disambiguated,
        }
        unit_nodes[str(unit["unit_id"])] = stack
        mapping_rows.append({
            "unit_id": unit["unit_id"],
            "en_markdown_block": f"v7en_struct_b{block.index:05d}",
            "en_markdown_lines": [block.line_start, block.line_end],
            "heading_node_ids": [f"node-{index + 1:04d}" for index in stack],
            "markdown_match_method": match_method,
            "order_disambiguated": order_disambiguated,
        })

    chapters = chapter_tree(en_content, zh_content, en_to_zh, unit_nodes)
    all_tree_ids = {unit_id for chapter in chapters for unit_id in chapter["unit_ids"]}
    source_ids = {str(unit["unit_id"]) for unit in units}
    if all_tree_ids != source_ids:
        raise StructureError("The rebuilt chapter tree does not cover every frozen unit exactly once")
    snapshot = {
        "schema_version": "cams-v7-textbook-structure-snapshot/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mapping_method": "corrected_bilingual_markdown_exact_quote_v1",
        "source": {
            "frozen_units": {"path": str(units_path.resolve()), "sha256": sha256_file(units_path)},
            "english_markdown": {"path": str(en_md.resolve()), "sha256": sha256_file(en_md)},
            "chinese_markdown": {"path": str(zh_md.resolve()), "sha256": sha256_file(zh_md)},
            "semantic_alignment": {"path": str(semantic_alignment_path.resolve()), "sha256": sha256_file(semantic_alignment_path)},
            "semantic_audit": {"path": str(semantic_audit_path.resolve()), "sha256": sha256_file(semantic_audit_path)},
            "page_map": {"path": str(page_map_path.resolve()), "sha256": sha256_file(page_map_path)},
        },
        "counts": {
            "units": len(units),
            "english_heading_nodes": len(en_headings),
            "chinese_heading_nodes": len(zh_headings),
            "english_content_heading_nodes": len(en_content),
            "chinese_content_heading_nodes": len(zh_content),
            "excluded_english_glossary_nodes": len(en_headings) - en_content_end,
            "excluded_chinese_glossary_nodes": len(zh_headings) - zh_content_end,
            "chinese_only_heading_nodes": len(chinese_only_nodes),
            "changed_or_releveled_bilingual_headings": len(heading_changes),
            "verified_semantic_heading_anchors": semantic_anchor_count,
            "english_blocks": len(blocks),
            "order_disambiguated_quote_matches": order_disambiguated_count,
            "noncanonical_quote_matches": sum(1 for row in mapping_rows if row["markdown_match_method"] != "canonical_quote"),
            "chapters": len(chapters),
        },
        "validation": {"valid": True, "errors": [], "unmapped_units": 0, "ambiguous_units": 0},
        "chinese_only_heading_nodes": chinese_only_nodes,
        "excluded_structure": {
            "english": {"start_node_id": f"node-{en_content_end + 1:04d}", "reason": "glossary_not_part_of_knowledge_unit_tree"},
            "chinese": {"start_node_id": f"node-{zh_content_end + 1:04d}", "reason": "glossary_ocr_headings_not_part_of_knowledge_unit_tree"},
        },
        "heading_changes": heading_changes,
    }
    remapped_payload = {
        **units_payload,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "frozen_formal_knowledge_units_remapped_to_corrected_bilingual_markdown",
        "source_file": str(units_path.resolve()),
        "structure_snapshot": snapshot["source"],
        "units": units,
    }
    chapter_payload = {
        "schema_version": "cams-v7-workbench-release/v1",
        "items": chapters,
    }
    mapping_payload = {
        "schema_version": "cams-v7-textbook-structure-map/v1",
        "items": mapping_rows,
    }
    return remapped_payload, chapter_payload, {"snapshot": snapshot, "mapping": mapping_payload}


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--units", required=True, type=Path)
    parser.add_argument("--en-md", required=True, type=Path)
    parser.add_argument("--zh-md", required=True, type=Path)
    parser.add_argument("--semantic-alignment", required=True, type=Path, help="Verified semantic alignment ledger for body-heading anchors")
    parser.add_argument("--semantic-audit", required=True, type=Path, help="Semantic rebuild audit with inserted Chinese body headings")
    parser.add_argument("--page-map", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv or sys.argv[1:])
        units, chapters, extras = remap(
            args.units.resolve(),
            args.en_md.resolve(),
            args.zh_md.resolve(),
            args.page_map.resolve(),
            args.semantic_alignment.resolve(),
            args.semantic_audit.resolve(),
        )
        output = args.output_dir.resolve()
        output.mkdir(parents=True, exist_ok=True)
        write_json(output / "v7_bilingual_units.json", units)
        write_json(output / "chapters.json", chapters)
        write_json(output / "structure_snapshot.json", extras["snapshot"])
        write_json(output / "unit_structure_map.json", extras["mapping"])
    except StructureError as exc:
        print(f"Textbook structure rebuild failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(extras["snapshot"]["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
