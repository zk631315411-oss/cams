from __future__ import annotations

import argparse
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
AUDIT_DIR = BASE_UNITS_DIR / "audit" / "zh_enrichment_overlay"

DEFAULT_BASE = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock_toobroad_policy.json"
DEFAULT_DECISIONS = BASE_UNITS_DIR / "llm_batches" / "zh_enrichment" / "v7_zh_enrichment_decisions.v1.ds.jsonl"
DEFAULT_VALIDATION = BASE_UNITS_DIR / "llm_batches" / "zh_enrichment" / "v7_zh_enrichment_validation.v1.json"
DEFAULT_OUT = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock_toobroad_policy_zh_enriched.json"
DEFAULT_TERMS = MODULE_DIR / "terms_map.json"


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


def compact(text: str, limit: int = 360) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def load_decisions(decisions_file: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    by_unit_id = {}
    meta_by_request = {}
    for row in read_jsonl(decisions_file):
        meta = row.get("_meta") or {}
        meta_by_request[str(row.get("request_id"))] = meta
        for unit in row.get("units", []):
            tmp_unit_id = str(unit.get("tmp_unit_id") or "")
            if tmp_unit_id:
                by_unit_id[tmp_unit_id] = {
                    "request_id": row.get("request_id"),
                    "knowledge_zh": str(unit.get("knowledge_zh") or "").strip(),
                    "terms": unit.get("terms") or [],
                    "notes": str(unit.get("notes") or "").strip(),
                    "meta": meta,
                }
    return by_unit_id, meta_by_request


def load_terms(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = read_json(path)
    return data.get("terms", []) if isinstance(data, dict) else []


def term_matches(haystack: str, value: str) -> bool:
    value = str(value or "").strip()
    if not value:
        return False
    escaped = re.escape(value.lower())
    if re.fullmatch(r"[a-z0-9]+", value.lower()):
        return bool(re.search(rf"\b{escaped}\b", haystack))
    return bool(re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", haystack))


def has_ml_stage_context(haystack: str) -> bool:
    return any(
        token in haystack
        for token in (
            "money laundering",
            "launder",
            "laundering",
            "criminal proceeds",
            "illicit proceeds",
            "illicit funds",
            "dirty money",
        )
    )


def source_mentions_term(unit: dict[str, Any], term: dict[str, Any]) -> bool:
    haystack = " ".join(
        [
            str(unit.get("en_quote") or ""),
            str(unit.get("knowledge_en") or ""),
            " ".join(str(item) for item in unit.get("heading_context", [])),
        ]
    ).lower()
    if term.get("category") == "money_laundering_stage" and not has_ml_stage_context(haystack):
        return False
    values = [term.get("en"), *(term.get("aliases_en") or [])]
    return any(term_matches(haystack, str(value or "")) for value in values if value)


def replacement_pairs_for_unit(unit: dict[str, Any], controlled_terms: list[dict[str, Any]]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for term in controlled_terms:
        if not source_mentions_term(unit, term):
            continue
        preferred = str(term.get("zh") or "").strip()
        if not preferred:
            continue
        aliases = [str(item).strip() for item in term.get("aliases_zh", []) if str(item).strip()]
        if preferred.endswith("阶段"):
            aliases.append(preferred.removesuffix("阶段"))
            for alias in list(aliases):
                if alias.endswith("阶段"):
                    aliases.append(alias.removesuffix("阶段"))
        for alias in aliases:
            if alias and alias != preferred:
                pairs.append((alias, preferred))
    pairs.sort(key=lambda item: len(item[0]), reverse=True)
    return pairs


def apply_controlled_zh(text: str, unit: dict[str, Any], controlled_terms: list[dict[str, Any]]) -> str:
    out = str(text or "")
    for before, after in replacement_pairs_for_unit(unit, controlled_terms):
        out = out.replace(before, after)
    out = out.replace("阶段阶段", "阶段")
    return out


def normalize_terms(raw_terms: list[Any], unit: dict[str, Any], controlled_terms: list[dict[str, Any]]) -> list[dict[str, str]]:
    terms = []
    seen = set()
    for term in raw_terms[:5]:
        if not isinstance(term, dict):
            continue
        en = str(term.get("en") or "").strip()
        zh = apply_controlled_zh(str(term.get("zh") or "").strip(), unit, controlled_terms)
        if not en or not zh:
            continue
        for controlled in controlled_terms:
            values = [controlled.get("en"), *(controlled.get("aliases_en") or [])]
            if any(en.lower() == str(value or "").lower() for value in values if value) and controlled.get("zh"):
                zh = str(controlled["zh"])
                en = str(controlled.get("en") or en)
                break
        key = (en.lower(), zh)
        if key in seen:
            continue
        seen.add(key)
        terms.append({"en": en, "zh": zh, "source": "llm"})
    for controlled in controlled_terms:
        if len(terms) >= 5:
            break
        if not source_mentions_term(unit, controlled):
            continue
        en = str(controlled.get("en") or "").strip()
        zh = str(controlled.get("zh") or "").strip()
        key = (en.lower(), zh)
        if en and zh and key not in seen:
            seen.add(key)
            terms.append({"en": en, "zh": zh, "source": "term_map"})
    return terms


def enrich_unit(unit: dict[str, Any], decision: dict[str, Any], controlled_terms: list[dict[str, Any]]) -> dict[str, Any]:
    out = deepcopy(unit)
    knowledge_zh = apply_controlled_zh(decision["knowledge_zh"], unit, controlled_terms)
    out["knowledge_zh"] = knowledge_zh
    out["zh_display_text"] = knowledge_zh
    out["zh_display_mode"] = "generated_summary"
    out["zh_search_text"] = None
    out["zh_search_text_status"] = "not_available"
    out["terms"] = normalize_terms(decision.get("terms") or [], unit, controlled_terms)
    source = out.setdefault("source", {})
    meta = decision.get("meta") or {}
    source["zh_enrichment"] = {
        "provider": meta.get("provider"),
        "model": meta.get("model"),
        "request_id": decision.get("request_id"),
        "prompt_sha256": meta.get("prompt_sha256"),
        "input_sha256": meta.get("input_sha256"),
        "message_sha256": meta.get("message_sha256"),
        "raw_response_sha256": meta.get("raw_response_sha256"),
        "raw_response_path": meta.get("raw_response_path"),
        "notes": decision.get("notes") or "",
        "term_map_applied": bool(replacement_pairs_for_unit(unit, controlled_terms)),
    }
    flags = set(str(flag) for flag in out.get("risk_flags", []) if flag)
    flags.add("zh_summary_generated_ds_v1")
    if out["terms"]:
        flags.add("zh_terms_generated_ds_v1")
    out["risk_flags"] = sorted(flags)
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
            "zh_enrichment_overlay": overlay_audit,
        }
    )
    return audit


def apply_overlay(
    base_file: Path,
    decisions_file: Path,
    validation_file: Path,
    terms_file: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = deepcopy(read_json(base_file))
    validation = read_json(validation_file)
    if validation.get("issue_count"):
        raise RuntimeError(f"zh enrichment validation has issues: {validation.get('issue_count')}")
    decisions, _ = load_decisions(decisions_file)
    controlled_terms = load_terms(terms_file)
    missing = []
    enriched_count = 0
    term_count = 0
    for section in ("items", "parent_items"):
        updated = []
        for unit in payload.get(section, []):
            unit_id = str(unit.get("unit_id"))
            decision = decisions.get(unit_id)
            if not decision:
                missing.append(unit_id)
                updated.append(unit)
                continue
            enriched = enrich_unit(unit, decision, controlled_terms)
            term_count += len(enriched.get("terms") or [])
            enriched_count += 1
            updated.append(enriched)
        payload[section] = updated
    if missing:
        raise RuntimeError(f"missing zh enrichment decisions for {len(missing)} units")

    payload["schema_version"] = "v7_units_draft_fullbook_ds_v2_policy_zh_enriched_v1"
    payload["status"] = "draft_prefreeze_policy_zh_enriched_not_for_downstream_binding"
    payload["generated_at"] = datetime.now().isoformat(timespec="seconds")
    payload.setdefault("sources", {})["zh_enrichment_base"] = str(base_file.relative_to(BASE_UNITS_DIR))
    payload.setdefault("sources", {})["zh_enrichment_decisions"] = str(decisions_file.relative_to(BASE_UNITS_DIR))
    payload.setdefault("sources", {})["zh_enrichment_validation"] = str(validation_file.relative_to(BASE_UNITS_DIR))
    payload.setdefault("sources", {})["zh_enrichment_terms_map"] = str(terms_file)
    payload.setdefault("notes", []).append(
        "Chinese display summaries and term hints were generated by DS; English evidence spans remain unchanged."
    )
    overlay_audit = {
        "base_file": str(base_file.relative_to(BASE_UNITS_DIR)),
        "decisions_file": str(decisions_file.relative_to(BASE_UNITS_DIR)),
        "validation_file": str(validation_file.relative_to(BASE_UNITS_DIR)),
        "terms_file": str(terms_file),
        "enriched_units": enriched_count,
        "term_count": term_count,
        "validation_issue_count": validation.get("issue_count"),
    }
    payload["audit"] = recompute_audit(payload, overlay_audit)
    manifest = {
        "schema_version": "v7_zh_enrichment_overlay_manifest_v1",
        "generated_at": payload["generated_at"],
        **overlay_audit,
    }
    return payload, manifest


def build_report(payload: dict[str, Any], manifest: dict[str, Any]) -> str:
    lines = [
        "# v7 zh Enrichment Overlay",
        "",
        f"Generated at: {manifest['generated_at']}",
        "",
        "## Summary",
        "",
        f"- enriched units: {manifest['enriched_units']}",
        f"- term count: {manifest['term_count']}",
        f"- direct items: {len(payload.get('items', []))}",
        f"- parent/context items: {len(payload.get('parent_items', []))}",
        f"- review items: {len(payload.get('review_items', []))}",
        f"- validation issue count: {manifest['validation_issue_count']}",
        f"- duplicate unit_ids: {len(payload['audit'].get('duplicate_unit_ids', []))}",
        f"- duplicate direct sentence_ids: {len(payload['audit'].get('duplicate_direct_sentence_ids', []))}",
        "",
        "## Samples",
        "",
    ]
    samples = [*payload.get("items", [])[:12], *payload.get("parent_items", [])[:8]]
    for unit in samples:
        lines.extend(
            [
                f"### {unit.get('unit_id')}",
                "",
                f"- type: {unit.get('unit_type')} / evidence: {unit.get('evidence_status')}",
                f"- heading: {' / '.join(unit.get('heading_context', []))}",
                f"- en: {compact(unit.get('en_quote'), 420)}",
                f"- knowledge_zh: {unit.get('knowledge_zh')}",
                f"- terms: {json.dumps(unit.get('terms', []), ensure_ascii=False)}",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply DS Chinese enrichment decisions to v7 units.")
    parser.add_argument("--base-file", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--decisions-file", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--validation-file", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--terms-file", type=Path, default=DEFAULT_TERMS)
    parser.add_argument("--out-file", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--out-dir", type=Path, default=AUDIT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload, manifest = apply_overlay(
        args.base_file.resolve(),
        args.decisions_file.resolve(),
        args.validation_file.resolve(),
        args.terms_file.resolve(),
    )
    write_json(args.out_file, payload)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out_dir / "zh_enrichment_overlay_manifest.json"
    report_path = args.out_dir / "zh_enrichment_overlay_report.md"
    write_json(manifest_path, manifest)
    report_path.write_text(build_report(payload, manifest), encoding="utf-8")
    print(f"enriched units: {manifest['enriched_units']}")
    print(f"term count: {manifest['term_count']}")
    print(f"direct items: {len(payload.get('items', []))}")
    print(f"parent/context items: {len(payload.get('parent_items', []))}")
    print(f"review items: {len(payload.get('review_items', []))}")
    print(f"duplicate unit_ids: {len(payload['audit'].get('duplicate_unit_ids', []))}")
    print(f"duplicate direct sentence_ids: {len(payload['audit'].get('duplicate_direct_sentence_ids', []))}")
    print(f"wrote: {args.out_file}")
    print(f"wrote: {manifest_path}")
    print(f"wrote: {report_path}")


if __name__ == "__main__":
    main()
