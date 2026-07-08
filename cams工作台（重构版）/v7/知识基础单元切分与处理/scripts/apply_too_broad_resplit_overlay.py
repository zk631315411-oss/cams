from __future__ import annotations

import argparse
import json
from collections import Counter
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DRAFT_DIR = BASE_UNITS_DIR / "draft" / "v2_fullbook"
AUDIT_DIR = BASE_UNITS_DIR / "audit" / "too_broad_resplit_overlay"

DEFAULT_BASE = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock.json"
DEFAULT_BATCH = BASE_UNITS_DIR / "llm_batches" / "too_broad_resplit" / "v7_toobroad_resplit_batch.jsonl"
DEFAULT_RESPLIT = BASE_UNITS_DIR / "draft" / "v7_units_draft.pilot_toobroad_resplit_ds_v1.llm.json"
DEFAULT_OUT = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock_toobroad.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def source_unit_by_request(batch_rows: list[dict[str, Any]]) -> dict[str, str]:
    mapping = {}
    for row in batch_rows:
        context = row.get("payload", {}).get("resplit_context", {})
        source_unit_id = context.get("source_unit_id")
        if row.get("request_id") and source_unit_id:
            mapping[str(row["request_id"])] = str(source_unit_id)
    return mapping


def annotate_resplit_unit(unit: dict[str, Any], request_to_source: dict[str, str]) -> dict[str, Any]:
    out = deepcopy(unit)
    request_id = str((out.get("source") or {}).get("request_id") or "")
    source_unit_id = request_to_source.get(request_id)
    out.setdefault("source", {})["materialization_method"] = "too_broad_resplit_overlay_v1"
    if source_unit_id:
        out["source"]["original_too_broad_unit_id"] = source_unit_id
    flags = set(out.get("risk_flags", []))
    flags.add("derived_from_too_broad_resplit_overlay")
    out["risk_flags"] = sorted(flag for flag in flags if flag)
    return out


def recompute_audit(payload: dict[str, Any], overlay_audit: dict[str, Any]) -> dict[str, Any]:
    items = payload.get("items", [])
    review_items = payload.get("review_items", [])
    parent_items = payload.get("parent_items", [])
    all_units = [*items, *review_items, *parent_items]
    unit_ids = [str(unit.get("unit_id")) for unit in all_units if unit.get("unit_id")]
    direct_sentence_ids = [
        str(sentence_id)
        for unit in items
        for sentence_id in unit.get("en_sentence_ids", [])
        if sentence_id
    ]
    audit = dict(payload.get("audit") or {})
    audit.update(
        {
            "direct_items": len(items),
            "review_items": len(review_items),
            "parent_items": len(parent_items),
            "duplicate_unit_ids": duplicate_values(unit_ids),
            "duplicate_direct_sentence_ids": duplicate_values(direct_sentence_ids),
            "too_broad_resplit_overlay": overlay_audit,
        }
    )
    return audit


def apply_overlay(base_file: Path, batch_file: Path, resplit_file: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = deepcopy(read_json(base_file))
    batch_rows = read_jsonl(batch_file)
    resplit = read_json(resplit_file)
    request_to_source = source_unit_by_request(batch_rows)
    processed_source_ids = set(request_to_source.values())
    base_review_ids = {str(unit.get("unit_id")) for unit in payload.get("review_items", [])}
    missing_source_ids = sorted(processed_source_ids - base_review_ids)

    new_direct = [annotate_resplit_unit(unit, request_to_source) for unit in resplit.get("items", [])]
    new_review = [annotate_resplit_unit(unit, request_to_source) for unit in resplit.get("review_items", [])]

    payload["items"] = [*payload.get("items", []), *new_direct]
    payload["review_items"] = [
        unit
        for unit in payload.get("review_items", [])
        if str(unit.get("unit_id")) not in processed_source_ids
    ] + new_review
    payload["schema_version"] = "v7_units_draft_fullbook_ds_v2_prefreeze_qa_crossblock_toobroad_overlay_v1"
    payload["status"] = "draft_prefreeze_qa_crossblock_toobroad_overlay_not_for_downstream_binding"
    payload["generated_at"] = datetime.now().isoformat(timespec="seconds")
    payload.setdefault("sources", {})["too_broad_resplit_base"] = str(base_file.relative_to(BASE_UNITS_DIR))
    payload.setdefault("sources", {})["too_broad_resplit_units"] = str(resplit_file.relative_to(BASE_UNITS_DIR))
    payload.setdefault("notes", []).append(
        "Too-broad review units were resplit from DS sentence-grouping decisions; IDs remain temporary."
    )

    overlay_audit = {
        "base_file": str(base_file.relative_to(BASE_UNITS_DIR)),
        "batch_file": str(batch_file.relative_to(BASE_UNITS_DIR)),
        "resplit_file": str(resplit_file.relative_to(BASE_UNITS_DIR)),
        "processed_source_review_units": len(processed_source_ids),
        "missing_source_review_units": missing_source_ids,
        "direct_units_added": len(new_direct),
        "review_units_added": len(new_review),
        "source_review_units_removed": len(processed_source_ids) - len(missing_source_ids),
        "resplit_audit_issues": len((resplit.get("audit") or {}).get("issues", [])),
    }
    payload["audit"] = recompute_audit(payload, overlay_audit)
    manifest = {
        "schema_version": "v7_too_broad_resplit_overlay_manifest_v1",
        "generated_at": payload["generated_at"],
        **overlay_audit,
    }
    return payload, manifest


def build_report(payload: dict[str, Any], manifest: dict[str, Any]) -> str:
    lines = [
        "# v7 Too-broad Resplit Overlay",
        "",
        f"Generated at: {manifest['generated_at']}",
        "",
        "## Summary",
        "",
        f"- direct items: {len(payload.get('items', []))}",
        f"- review items: {len(payload.get('review_items', []))}",
        f"- parent/context items: {len(payload.get('parent_items', []))}",
        f"- processed source review units: {manifest['processed_source_review_units']}",
        f"- source review units removed: {manifest['source_review_units_removed']}",
        f"- direct units added: {manifest['direct_units_added']}",
        f"- review units added: {manifest['review_units_added']}",
        f"- resplit audit issues: {manifest['resplit_audit_issues']}",
        f"- duplicate unit_ids: {len(payload['audit'].get('duplicate_unit_ids', []))}",
        f"- duplicate direct sentence_ids: {len(payload['audit'].get('duplicate_direct_sentence_ids', []))}",
        "",
    ]
    if manifest["missing_source_review_units"]:
        lines.extend(["## Missing Source Review Units", ""])
        for unit_id in manifest["missing_source_review_units"]:
            lines.append(f"- {unit_id}")
        lines.append("")
    lines.extend(["## Direct Samples", ""])
    samples = [
        unit
        for unit in payload.get("items", [])
        if "derived_from_too_broad_resplit_overlay" in set(unit.get("risk_flags", []))
    ]
    for unit in samples[:20]:
        lines.extend(
            [
                f"### {unit.get('unit_id')} · {unit.get('unit_type')}",
                "",
                f"- original: {(unit.get('source') or {}).get('original_too_broad_unit_id')}",
                f"- page: {unit.get('printed_page')} / pdf {unit.get('pdf_page')}",
                f"- knowledge_en: {unit.get('knowledge_en')}",
                f"- sentence_ids: {', '.join(unit.get('en_sentence_ids', []))}",
                f"- en_quote: {unit.get('en_quote')}",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply DS resplit results for too-broad review units as an overlay.")
    parser.add_argument("--base-file", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--batch-file", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--resplit-file", type=Path, default=DEFAULT_RESPLIT)
    parser.add_argument("--out-file", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--out-dir", type=Path, default=AUDIT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, manifest = apply_overlay(args.base_file.resolve(), args.batch_file.resolve(), args.resplit_file.resolve())
    write_json(args.out_file, payload)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out_dir / "too_broad_resplit_overlay_manifest.json"
    report_path = args.out_dir / "too_broad_resplit_overlay_report.md"
    write_json(manifest_path, manifest)
    report_path.write_text(build_report(payload, manifest), encoding="utf-8")
    print(f"direct items: {len(payload.get('items', []))}")
    print(f"review items: {len(payload.get('review_items', []))}")
    print(f"processed source review units: {manifest['processed_source_review_units']}")
    print(f"direct units added: {manifest['direct_units_added']}")
    print(f"review units added: {manifest['review_units_added']}")
    print(f"duplicate unit_ids: {len(payload['audit'].get('duplicate_unit_ids', []))}")
    print(f"duplicate direct sentence_ids: {len(payload['audit'].get('duplicate_direct_sentence_ids', []))}")
    print(f"wrote: {args.out_file}")
    print(f"wrote: {manifest_path}")
    print(f"wrote: {report_path}")


if __name__ == "__main__":
    main()
