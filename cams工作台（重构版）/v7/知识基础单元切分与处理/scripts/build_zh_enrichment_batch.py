from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DRAFT_DIR = BASE_UNITS_DIR / "draft" / "v2_fullbook"
DEFAULT_INPUT = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock_toobroad_policy.json"
DEFAULT_OUT = BASE_UNITS_DIR / "llm_batches" / "zh_enrichment" / "v7_zh_enrichment_batch.v1.jsonl"
DEFAULT_TERMS = MODULE_DIR / "terms_map.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def compact(text: str, limit: int = 900) -> str:
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


def unit_sort_key(unit: dict[str, Any]) -> tuple[int, int, str]:
    return (block_num(unit), sentence_num(unit), str(unit.get("unit_id") or ""))


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


def relevant_terms(unit: dict[str, Any], terms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    haystack = " ".join(
        [
            str(unit.get("en_quote") or ""),
            str(unit.get("knowledge_en") or ""),
            " ".join(str(item) for item in unit.get("heading_context", [])),
        ]
    ).lower()
    out = []
    for term in terms:
        if term.get("category") == "money_laundering_stage" and not has_ml_stage_context(haystack):
            continue
        en_values = [term.get("en"), *(term.get("aliases_en") or [])]
        if any(term_matches(haystack, str(value or "")) for value in en_values if value):
            out.append(
                {
                    "en": term.get("en"),
                    "aliases_en": term.get("aliases_en", []),
                    "zh": term.get("zh"),
                    "aliases_zh": term.get("aliases_zh", []),
                }
            )
    return out[:8]


def unit_payload(unit: dict[str, Any], terms: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "tmp_unit_id": unit.get("unit_id"),
        "unit_type": unit.get("unit_type"),
        "type": unit.get("type"),
        "evidence_status": unit.get("evidence_status"),
        "can_be_direct_evidence": bool(unit.get("can_be_direct_evidence")),
        "heading_context": unit.get("heading_context", []),
        "knowledge_en": compact(unit.get("knowledge_en"), 420),
        "en_quote": compact(unit.get("en_quote"), 1100),
        "risk_flags": unit.get("risk_flags", []),
        "controlled_terms": relevant_terms(unit, terms),
    }


def build_rows(input_file: Path, batch_size: int, terms_file: Path) -> list[dict[str, Any]]:
    payload = read_json(input_file)
    terms = load_terms(terms_file)
    units = [*payload.get("items", []), *payload.get("parent_items", [])]
    units.sort(key=unit_sort_key)
    rows = []
    for idx in range(0, len(units), batch_size):
        chunk = units[idx : idx + batch_size]
        request_index = idx // batch_size + 1
        rows.append(
            {
                "schema_version": "v7_zh_enrichment_request_v1",
                "request_id": f"zh_enrich_v1_{request_index:04d}",
                "source_file": str(input_file.relative_to(BASE_UNITS_DIR)),
                "unit_count": len(chunk),
                "unit_ids": [unit.get("unit_id") for unit in chunk],
                "payload": {
                    "instructions": "Generate Chinese display summaries and core bilingual terms for these fixed v7 units.",
                    "units": [unit_payload(unit, terms) for unit in chunk],
                },
            }
        )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build DeepSeek batch requests for v7 unit Chinese enrichment.")
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-file", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--terms-file", type=Path, default=DEFAULT_TERMS)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_rows(args.input_file.resolve(), args.batch_size, args.terms_file.resolve())
    write_jsonl(args.out_file, rows)
    print(f"generated_at: {datetime.now().isoformat(timespec='seconds')}")
    print(f"requests: {len(rows)}")
    print(f"units: {sum(row['unit_count'] for row in rows)}")
    print(f"batch_size: {args.batch_size}")
    print(f"wrote: {args.out_file}")


if __name__ == "__main__":
    main()
