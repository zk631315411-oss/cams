#!/usr/bin/env python3
"""Repair missing English MinerU text from PDF-verified frozen V7 units.

The tool is intentionally conservative. A sentence is inserted only when it
appears in the page-aligned English PDF text and its position is bounded by
ordered, already-present direct-evidence unit quotes. Existing OCR variants
are replaced only when their normalized span has a near-exact match.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


class RepairError(ValueError):
    pass


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RepairError(f"Missing required input: {path}") from exc


def canonical(value: str) -> str:
    value = str(value or "").lower()
    value = value.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return "".join(character for character in value if character.isalnum())


def canonical_with_offsets(value: str) -> tuple[str, list[int]]:
    chars = []
    offsets = []
    for index, character in enumerate(value.lower()):
        if character.isalnum():
            chars.append(character)
            offsets.append(index)
    return "".join(chars), offsets


def block_num(unit: dict[str, Any]) -> int:
    for value in [(unit.get("source") or {}).get("en_block_id"), *(unit.get("en_sentence_ids") or [])]:
        match = re.search(r"b(\d+)", str(value or ""))
        if match:
            return int(match.group(1))
    return 10**9


def direct_units(units_path: Path) -> list[dict[str, Any]]:
    units = read_json(units_path).get("units") or []
    result = [unit for unit in units if unit.get("can_be_direct_evidence")]
    if len(result) != 4702:
        raise RepairError(f"Expected 4702 direct frozen units, found {len(result)}")
    return sorted(result, key=lambda unit: (block_num(unit), int(unit.get("unit_order") or 0), str(unit.get("unit_id") or "")))


def occurrences(haystack: str, needle: str, after: int) -> list[int]:
    starts = []
    index = haystack.find(needle, after)
    while index >= 0:
        starts.append(index)
        index = haystack.find(needle, index + 1)
    return starts


@dataclass(frozen=True)
class ExistingAnchor:
    unit_id: str
    norm_start: int
    norm_end: int
    raw_start: int


def ordered_anchors(units: list[dict[str, Any]], md_norm: str, raw_offsets: list[int]) -> tuple[dict[str, ExistingAnchor], list[dict[str, Any]]]:
    anchors: dict[str, ExistingAnchor] = {}
    missing = []
    for unit in units:
        quote = canonical(str(unit.get("en_quote") or ""))
        if not quote:
            raise RepairError(f"{unit.get('unit_id')}: missing English quote")
        candidates = occurrences(md_norm, quote, 0)
        if not candidates:
            missing.append(unit)
            continue
        start = candidates[0]
        end = start + len(quote)
        anchors[str(unit["unit_id"])] = ExistingAnchor(str(unit["unit_id"]), start, end, raw_offsets[start])
    return anchors, missing


def pdf_pages(aligned_pages_path: Path) -> dict[int, str]:
    payload = read_json(aligned_pages_path)
    return {int(item["pdf_page"]): canonical(str(item.get("en_text") or "")) for item in payload.get("items") or []}


def pdf_contains_quote(unit: dict[str, Any], pages: dict[int, str]) -> bool:
    quote = canonical(str(unit.get("en_quote") or ""))
    page = int(unit.get("pdf_page") or 0)
    nearby = "".join(pages.get(number, "") for number in range(max(1, page - 1), page + 3))
    return quote in nearby


def nearby_ocr_span(md_norm: str, quote: str) -> tuple[int, int] | None:
    if len(quote) < 80:
        return None
    prefix = quote[:80]
    suffix = quote[-80:]
    for start in occurrences(md_norm, prefix, 0):
        suffix_start = md_norm.find(suffix, start + len(prefix))
        if suffix_start < 0:
            continue
        end = suffix_start + len(suffix)
        candidate = md_norm[start:end]
        ratio = SequenceMatcher(a=quote, b=candidate, autojunk=False).ratio()
        if ratio >= 0.995:
            return start, end
    return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_repair(md_path: Path, units_path: Path, aligned_pages_path: Path) -> tuple[str, dict[str, Any]]:
    raw = md_path.read_text(encoding="utf-8-sig")
    md_norm, offsets = canonical_with_offsets(raw)
    all_units = read_json(units_path).get("units") or []
    units = direct_units(units_path)
    anchors, missing = ordered_anchors(units, md_norm, offsets)
    pages = pdf_pages(aligned_pages_path)
    unit_index = {str(unit["unit_id"]): index for index, unit in enumerate(units)}
    operations: list[tuple[int, int, str, dict[str, Any]]] = []
    insertions: dict[int, list[tuple[str, dict[str, Any]]]] = {}
    rejected = []
    inserted = []
    replaced = []
    changes = []

    for unit in missing:
        unit_id = str(unit["unit_id"])
        quote = str(unit.get("en_quote") or "").strip()
        quote_norm = canonical(quote)
        if not pdf_contains_quote(unit, pages):
            rejected.append({"unit_id": unit_id, "reason": "quote_not_found_in_pdf_page_window"})
            continue
        ocr_span = nearby_ocr_span(md_norm, quote_norm)
        if ocr_span:
            start, end = ocr_span
            operations.append((offsets[start], offsets[end - 1] + 1, quote, {"unit_id": unit_id, "method": "replace_near_exact_ocr_span"}))
            replaced.append(unit_id)
            changes.append({"unit_id": unit_id, "pdf_page": unit.get("pdf_page"), "printed_page": unit.get("printed_page"), "method": "replace_near_exact_ocr_span"})
            continue
        position = unit_index[unit_id]
        previous = next(
            (anchors.get(str(units[index]["unit_id"])) for index in range(position - 1, -1, -1) if str(units[index]["unit_id"]) in anchors),
            None,
        )
        following = next(
            (anchors.get(str(units[index]["unit_id"])) for index in range(position + 1, len(units)) if str(units[index]["unit_id"]) in anchors),
            None,
        )
        if previous is None or following is None or previous.norm_start >= following.norm_start:
            rejected.append({"unit_id": unit_id, "reason": "ordered_markdown_anchors_unavailable"})
            continue
        insertions.setdefault(following.raw_start, []).append(
            (quote, {"unit_id": unit_id, "method": "insert_before_next_verified_anchor", "previous_anchor": previous.unit_id, "next_anchor": following.unit_id})
        )
        inserted.append(unit_id)
        changes.append({
            "unit_id": unit_id,
            "pdf_page": unit.get("pdf_page"),
            "printed_page": unit.get("printed_page"),
            "method": "insert_before_next_verified_anchor",
            "previous_anchor": previous.unit_id,
            "next_anchor": following.unit_id,
        })

    if rejected:
        return raw, {
            "valid": False,
            "missing_direct_units": len(missing),
            "inserted_unit_ids": inserted,
            "replaced_unit_ids": replaced,
            "changes": changes,
            "rejected": rejected,
        }
    for raw_start, entries in insertions.items():
        text = "\n\n".join(quote for quote, _ in entries) + "\n\n"
        operations.append((raw_start, raw_start, text, {"unit_ids": [meta["unit_id"] for _, meta in entries], "method": "insert_before_next_verified_anchor"}))
    # Apply from right to left so raw offsets remain valid. Exact-span replacements
    # and insertions at the same offset are deterministically ordered by unit id.
    for start, end, replacement, _ in sorted(operations, key=lambda operation: (operation[0], operation[1]), reverse=True):
        raw = raw[:start] + replacement + raw[end:]
    final_norm, _ = canonical_with_offsets(raw)
    still_missing = [unit["unit_id"] for unit in all_units if canonical(str(unit.get("en_quote") or "")) not in final_norm]
    if still_missing:
        return raw, {
            "valid": False,
            "missing_direct_units": len(missing),
            "inserted_unit_ids": inserted,
            "replaced_unit_ids": replaced,
            "changes": changes,
            "rejected": [{"unit_id": unit_id, "reason": "quote_still_absent_after_repair"} for unit_id in still_missing],
        }
    return raw, {
        "valid": True,
        "missing_direct_units": len(missing),
        "inserted_unit_ids": inserted,
        "replaced_unit_ids": replaced,
        "changes": changes,
        "rejected": [],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--md", type=Path, required=True)
    parser.add_argument("--units", type=Path, required=True)
    parser.add_argument("--aligned-pages", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    md_path = args.md.resolve()
    repaired, audit = build_repair(md_path, args.units.resolve(), args.aligned_pages.resolve())
    audit.update({
        "schema_version": "v7_en_pdf_backfill_audit/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "english_markdown": {"path": str(md_path), "sha256_before": sha256(md_path)},
            "frozen_units": {"path": str(args.units.resolve()), "sha256": sha256(args.units.resolve())},
            "aligned_pages": {"path": str(args.aligned_pages.resolve()), "sha256": sha256(args.aligned_pages.resolve())},
        },
    })
    if args.write and audit["valid"]:
        backup = Path(str(md_path) + ".before_pdf_backfill.bak")
        if not backup.exists():
            shutil.copy2(md_path, backup)
        md_path.write_text(repaired, encoding="utf-8")
        audit["source"]["english_markdown"]["sha256_after"] = sha256(md_path)
        audit["backup"] = str(backup)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": audit["valid"], "missing_direct_units": audit["missing_direct_units"], "inserted": len(audit["inserted_unit_ids"]), "replaced": len(audit["replaced_unit_ids"]), "rejected": len(audit["rejected"])}, ensure_ascii=False))
    return 0 if audit["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
