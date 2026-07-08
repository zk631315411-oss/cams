from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
KG_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(KG_ROOT / "lib"))

from kg_common import (  # noqa: E402
    BLOCKING_RISK_FLAGS,
    DEFAULT_KG_WORK_DIR,
    DEFAULT_UNITS_PATH,
    ensure_dir,
    load_units,
    ordered_chapters,
    summarize_counter,
    unit_sort_key,
    write_jsonl,
    write_text,
)


FORMAL_UNIT_ID_RE = re.compile(r"^v7u_N\d{6}$")


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 0 input normalization and hard gate for v7 KG units.")
    parser.add_argument("--units", type=Path, default=DEFAULT_UNITS_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_KG_WORK_DIR / "phase0_quality_gate")
    args = parser.parse_args()

    units = sorted(load_units(args.units), key=unit_sort_key)
    out_dir = ensure_dir(args.out_dir)

    duplicate_ids = _duplicate_ids(units)
    eligible: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for unit in units:
        reasons = _blocking_reasons(unit, duplicate_ids)
        record = _phase0_record(unit)
        if reasons:
            record["phase0_status"] = "blocked"
            record["blocked_reasons"] = reasons
            blocked.append(record)
        else:
            record["phase0_status"] = "eligible"
            eligible.append(record)

    write_jsonl(out_dir / "eligible_units.jsonl", eligible)
    write_jsonl(out_dir / "blocked_units.jsonl", blocked)
    write_text(out_dir / "unit_quality_report.md", _build_report(args.units, units, eligible, blocked))

    summary = {
        "input_units": len(units),
        "eligible_units": len(eligible),
        "blocked_units": len(blocked),
        "output_dir": str(out_dir),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def _duplicate_ids(units: list[dict[str, Any]]) -> set[str]:
    counter = Counter(unit.get("unit_id") for unit in units)
    return {unit_id for unit_id, count in counter.items() if unit_id and count > 1}


def _blocking_reasons(unit: dict[str, Any], duplicate_ids: set[str]) -> list[str]:
    reasons: list[str] = []
    unit_id = unit.get("unit_id")
    risk_flags = set(unit.get("risk_flags") or [])

    if not unit_id or not FORMAL_UNIT_ID_RE.match(str(unit_id)):
        reasons.append("non_formal_unit_id")
    if unit_id in duplicate_ids:
        reasons.append("duplicate_unit_id")
    if unit.get("unit_status") != "frozen":
        reasons.append("not_frozen")
    if not unit.get("chapter"):
        reasons.append("missing_chapter")
    if unit.get("unit_order") is None:
        reasons.append("missing_unit_order")
    if not unit.get("en_quote") and unit.get("type") != "context":
        reasons.append("missing_en_quote")

    blocking_flags = sorted(risk_flags & BLOCKING_RISK_FLAGS)
    reasons.extend([f"risk_flag:{flag}" for flag in blocking_flags])
    return reasons


def _phase0_record(unit: dict[str, Any]) -> dict[str, Any]:
    risk_flags = list(unit.get("risk_flags") or [])
    unit_type = unit.get("type") or unit.get("unit_type")

    return {
        "unit_id": unit.get("unit_id"),
        "unit_order": unit.get("unit_order"),
        "chapter": unit.get("chapter"),
        "heading_context": unit.get("heading_context") or [],
        "type": unit_type,
        "unit_type": unit.get("unit_type"),
        "evidence_status": unit.get("evidence_status"),
        "can_be_direct_evidence": unit.get("can_be_direct_evidence"),
        "knowledge_zh": unit.get("knowledge_zh"),
        "knowledge_en": unit.get("knowledge_en"),
        "zh_display_text": unit.get("zh_display_text"),
        "en_quote": unit.get("en_quote"),
        "terms": unit.get("terms") or [],
        "pdf_page": unit.get("pdf_page"),
        "printed_page": unit.get("printed_page"),
        "page_span": unit.get("page_span") or [],
        "printed_page_span": unit.get("printed_page_span") or [],
        "risk_flags": risk_flags,
    }


def _build_report(
    units_path: Path,
    units: list[dict[str, Any]],
    eligible: list[dict[str, Any]],
    blocked: list[dict[str, Any]],
) -> str:
    type_counter = Counter(u.get("type") or u.get("unit_type") or "UNKNOWN" for u in units)
    eligible_type_counter = Counter(u.get("type") or "UNKNOWN" for u in eligible)
    flag_counter = Counter(flag for u in units for flag in (u.get("risk_flags") or []))
    chapter_rows = ordered_chapters(eligible)

    lines = [
        "# Phase 0 Unit Quality Report",
        "",
        f"- input: `{units_path}`",
        f"- input_units: {len(units)}",
        f"- eligible_units: {len(eligible)}",
        f"- blocked_units: {len(blocked)}",
        "",
        "## Type Distribution",
        "",
        "| type | all_units | eligible_units |",
        "|---|---:|---:|",
    ]
    for item in summarize_counter(type_counter):
        lines.append(f"| {item['name']} | {item['count']} | {eligible_type_counter.get(item['name'], 0)} |")

    lines.extend(
        [
            "",
            "## Risk Flags",
            "",
            "| risk_flag | count |",
            "|---|---:|",
        ]
    )
    for item in summarize_counter(flag_counter, 30):
        lines.append(f"| {item['name']} | {item['count']} |")

    lines.extend(
        [
            "",
            "## Chapter Order",
            "",
            "| chapter_id | chapter | eligible_units | pdf_page_span | first_unit |",
            "|---|---|---:|---|---|",
        ]
    )
    for idx, chapter in enumerate(chapter_rows, start=1):
        lines.append(
            f"| CH{idx:02d} | {chapter['chapter']} | {chapter['unit_count']} | "
            f"{chapter['pdf_page_span']} | {chapter['first_unit_id']} |"
        )

    if blocked:
        lines.extend(
            [
                "",
                "## Blocked Samples",
                "",
                "| unit_id | reasons | knowledge_zh |",
                "|---|---|---|",
            ]
        )
        for unit in blocked[:20]:
            reasons = ", ".join(unit.get("blocked_reasons") or [])
            knowledge = (unit.get("knowledge_zh") or "").replace("|", "/")
            lines.append(f"| {unit.get('unit_id')} | {reasons} | {knowledge} |")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
