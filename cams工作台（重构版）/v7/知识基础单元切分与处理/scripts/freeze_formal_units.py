from __future__ import annotations

import argparse
import hashlib
import json
import re
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
DEFAULT_INPUT = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock_toobroad_policy_zh_enriched.json"
DEFAULT_OUT_DIR = BASE_UNITS_DIR / "units"


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: str, limit: int = 360) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def block_num(unit: dict[str, Any]) -> int:
    source = unit.get("source") or {}
    candidates = [source.get("en_block_id"), *(unit.get("en_sentence_ids") or [])]
    for candidate in candidates:
        match = re.search(r"b(\d+)", str(candidate or ""))
        if match:
            return int(match.group(1))
    return 10**9


def sentence_num(unit: dict[str, Any]) -> int:
    for sentence_id in unit.get("en_sentence_ids") or []:
        match = re.search(r"_s(\d+)", str(sentence_id))
        if match:
            return int(match.group(1))
    return 0


def unit_sort_key(unit: dict[str, Any]) -> tuple[int, int, int, str]:
    direct_rank = 0 if unit.get("can_be_direct_evidence") else 1
    return (block_num(unit), sentence_num(unit), direct_rank, str(unit.get("unit_id") or ""))


def duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def citation(unit: dict[str, Any]) -> str:
    printed = unit.get("printed_page")
    pdf = unit.get("pdf_page")
    if printed and pdf:
        return f"CAMS v7 p.{printed} / PDF p.{pdf}"
    if printed:
        return f"CAMS v7 p.{printed}"
    if pdf:
        return f"CAMS v7 PDF p.{pdf}"
    return "CAMS v7"


def validate_ready(units: list[dict[str, Any]], allow_missing_zh: bool) -> list[dict[str, Any]]:
    issues = []
    for unit in units:
        unit_id = unit.get("unit_id")
        if not unit.get("en_quote"):
            issues.append({"unit_id": unit_id, "issue": "missing_en_quote"})
        if not unit.get("knowledge_en"):
            issues.append({"unit_id": unit_id, "issue": "missing_knowledge_en"})
        if not allow_missing_zh and not unit.get("knowledge_zh"):
            issues.append({"unit_id": unit_id, "issue": "missing_knowledge_zh"})
        if unit.get("can_be_direct_evidence") and unit.get("evidence_status") != "direct":
            issues.append({"unit_id": unit_id, "issue": "direct_unit_not_direct_status"})
    return issues


def freeze_unit(unit: dict[str, Any], formal_id: str, order: int) -> dict[str, Any]:
    out = deepcopy(unit)
    tmp_unit_id = str(out.get("unit_id"))
    out["unit_id"] = formal_id
    out["unit_status"] = "frozen"
    out["unit_order"] = order
    out.setdefault("source", {})["tmp_unit_id"] = tmp_unit_id
    out.setdefault("source", {})["freeze_method"] = "v7_formal_units_freeze_v1"
    if not out.get("zh_display_text") and out.get("knowledge_zh"):
        out["zh_display_text"] = out["knowledge_zh"]
        out["zh_display_mode"] = "generated_summary"
    for sentence in out.get("en_sentences") or []:
        sentence["parent_unit_id"] = formal_id
    return out


def as_card(unit: dict[str, Any]) -> dict[str, Any]:
    return {
        "card_id": unit.get("unit_id"),
        "unit_id": unit.get("unit_id"),
        "unit_status": unit.get("unit_status"),
        "unit_order": unit.get("unit_order"),
        "quote": unit.get("en_quote"),
        "knowledge": unit.get("knowledge_zh") or unit.get("knowledge_en"),
        "knowledge_zh": unit.get("knowledge_zh"),
        "knowledge_en": unit.get("knowledge_en"),
        "citation": citation(unit),
        "type": unit.get("type"),
        "focus_type": unit.get("type"),
        "unit_type": unit.get("unit_type"),
        "evidence_status": unit.get("evidence_status"),
        "can_be_direct_evidence": unit.get("can_be_direct_evidence"),
        "heading_context": unit.get("heading_context", []),
        "pdf_page": unit.get("pdf_page"),
        "printed_page": unit.get("printed_page"),
        "page_span": unit.get("page_span", []),
        "printed_page_span": unit.get("printed_page_span", []),
        "en_sentence_ids": unit.get("en_sentence_ids", []),
        "terms": unit.get("terms", []),
        "risk_flags": unit.get("risk_flags", []),
        "source_tmp_unit_id": (unit.get("source") or {}).get("tmp_unit_id"),
    }


def build_excluded(review_items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "v7_excluded_or_review_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "policy": "review_items are not frozen as formal v7 units; they may be repaired later and added through a new version.",
        "review_count": len(review_items),
        "items": [
            {
                "tmp_unit_id": unit.get("unit_id"),
                "chapter": unit.get("chapter"),
                "heading_context": unit.get("heading_context", []),
                "printed_page": unit.get("printed_page"),
                "pdf_page": unit.get("pdf_page"),
                "en_quote": unit.get("en_quote"),
                "knowledge_en": unit.get("knowledge_en"),
                "decision_reason": unit.get("decision_reason"),
                "risk_flags": unit.get("risk_flags", []),
                "source": unit.get("source", {}),
            }
            for unit in review_items
        ],
    }


def build_report(units: list[dict[str, Any]], cards: list[dict[str, Any]], excluded: dict[str, Any], manifest: dict[str, Any]) -> str:
    direct_count = sum(1 for unit in units if unit.get("can_be_direct_evidence"))
    parent_count = len(units) - direct_count
    lines = [
        "# v7 Formal Knowledge Units Build Report",
        "",
        f"Generated at: {manifest['generated_at']}",
        "",
        "## Summary",
        "",
        f"- formal units: {len(units)}",
        f"- direct leaf units: {direct_count}",
        f"- parent/context units: {parent_count}",
        f"- cards exported: {len(cards)}",
        f"- excluded/review items: {excluded['review_count']}",
        f"- duplicate unit_ids: {len(manifest['duplicate_unit_ids'])}",
        f"- duplicate direct sentence_ids: {len(manifest['duplicate_direct_sentence_ids'])}",
        f"- input sha256: `{manifest['input_sha256']}`",
        "",
        "## Output Files",
        "",
        "- `v7_bilingual_units.json`",
        "- `v7_units_as_cards.json`",
        "- `unit_freeze_manifest.json`",
        "- `excluded_or_review_manifest.json`",
        "- `unit_build_report.md`",
        "",
        "## Samples",
        "",
    ]
    for unit in units[:24]:
        lines.extend(
            [
                f"### {unit.get('unit_id')}",
                "",
                f"- tmp: {(unit.get('source') or {}).get('tmp_unit_id')}",
                f"- type: {unit.get('unit_type')} / evidence: {unit.get('evidence_status')}",
                f"- page: {unit.get('printed_page')} / pdf {unit.get('pdf_page')}",
                f"- heading: {' / '.join(unit.get('heading_context', []))}",
                f"- zh: {unit.get('knowledge_zh')}",
                f"- en: {compact(unit.get('en_quote'), 420)}",
                "",
            ]
        )
    if excluded["items"]:
        lines.extend(["## Excluded Review Samples", ""])
        for item in excluded["items"][:10]:
            lines.extend(
                [
                    f"### {item.get('tmp_unit_id')}",
                    "",
                    f"- reason: {item.get('decision_reason')}",
                    f"- en: {compact(item.get('en_quote'), 420)}",
                    "",
                ]
            )
    return "\n".join(lines)


def freeze(input_file: Path, out_dir: Path, allow_missing_zh: bool) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any], str]:
    payload = read_json(input_file)
    source_units = [*payload.get("items", []), *payload.get("parent_items", [])]
    source_units.sort(key=unit_sort_key)
    ready_issues = validate_ready(source_units, allow_missing_zh)
    if ready_issues:
        raise RuntimeError(f"formal unit readiness check failed: {len(ready_issues)} issues")

    formal_units = [
        freeze_unit(unit, f"v7u_N{idx:06d}", idx)
        for idx, unit in enumerate(source_units, start=1)
    ]
    cards = [as_card(unit) for unit in formal_units]
    excluded = build_excluded(payload.get("review_items", []))
    direct_sentence_ids = [
        str(sentence_id)
        for unit in formal_units
        if unit.get("can_be_direct_evidence")
        for sentence_id in unit.get("en_sentence_ids", [])
        if sentence_id
    ]
    unit_ids = [str(unit.get("unit_id")) for unit in formal_units]
    tmp_to_formal = {
        (unit.get("source") or {}).get("tmp_unit_id"): unit.get("unit_id")
        for unit in formal_units
        if (unit.get("source") or {}).get("tmp_unit_id")
    }
    generated_at = datetime.now().isoformat(timespec="seconds")
    manifest = {
        "schema_version": "v7_unit_freeze_manifest_v1",
        "generated_at": generated_at,
        "input_file": str(input_file),
        "input_sha256": sha256_text(canonical_json(payload)),
        "policy": {
            "formal_id_sequence": "single shared sequence for direct and parent/context units, sorted by source block order",
            "review_items": "excluded from formal units and written to excluded_or_review_manifest.json",
            "zh_display": "generated summary; not asserted to be a Chinese source-text subspan",
        },
        "unit_count": len(formal_units),
        "direct_unit_count": sum(1 for unit in formal_units if unit.get("can_be_direct_evidence")),
        "parent_context_unit_count": sum(1 for unit in formal_units if not unit.get("can_be_direct_evidence")),
        "excluded_review_count": len(payload.get("review_items", [])),
        "duplicate_unit_ids": duplicate_values(unit_ids),
        "duplicate_direct_sentence_ids": duplicate_values(direct_sentence_ids),
        "tmp_to_formal": tmp_to_formal,
    }
    units_payload = {
        "schema_version": "v7_bilingual_units_v1",
        "generated_at": generated_at,
        "status": "frozen_formal_knowledge_units",
        "source_file": str(input_file),
        "unit_count": len(formal_units),
        "units": formal_units,
    }
    cards_payload = {
        "schema_version": "v7_units_as_cards_v1",
        "generated_at": generated_at,
        "status": "frozen_formal_knowledge_units_card_adapter",
        "card_count": len(cards),
        "cards": cards,
    }
    report = build_report(formal_units, cards, excluded, manifest)
    return units_payload, cards_payload, excluded, manifest, report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze v7 prefreeeze QA draft into formal v7u_N knowledge units.")
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--allow-missing-zh", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.out_dir.resolve()
    units_payload, cards_payload, excluded, manifest, report = freeze(
        args.input_file.resolve(),
        out_dir,
        args.allow_missing_zh,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "v7_bilingual_units.json", units_payload)
    write_json(out_dir / "v7_units_as_cards.json", cards_payload)
    write_json(out_dir / "excluded_or_review_manifest.json", excluded)
    write_json(out_dir / "unit_freeze_manifest.json", manifest)
    (out_dir / "unit_build_report.md").write_text(report, encoding="utf-8")
    print(f"formal units: {manifest['unit_count']}")
    print(f"direct units: {manifest['direct_unit_count']}")
    print(f"parent/context units: {manifest['parent_context_unit_count']}")
    print(f"excluded review: {manifest['excluded_review_count']}")
    print(f"duplicate unit_ids: {len(manifest['duplicate_unit_ids'])}")
    print(f"duplicate direct sentence_ids: {len(manifest['duplicate_direct_sentence_ids'])}")
    print(f"wrote: {out_dir / 'v7_bilingual_units.json'}")
    print(f"wrote: {out_dir / 'v7_units_as_cards.json'}")
    print(f"wrote: {out_dir / 'unit_freeze_manifest.json'}")
    print(f"wrote: {out_dir / 'excluded_or_review_manifest.json'}")
    print(f"wrote: {out_dir / 'unit_build_report.md'}")


if __name__ == "__main__":
    main()
