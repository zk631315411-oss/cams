from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DRAFT_DIR = BASE_UNITS_DIR / "draft" / "v2_fullbook"
BATCH_DIR = BASE_UNITS_DIR / "llm_batches" / "too_broad_resplit"

DEFAULT_INPUT = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.prefreeze_qa_crossblock.json"
DEFAULT_OUT = BATCH_DIR / "v7_toobroad_resplit_batch.jsonl"

ALLOWED_UNIT_TYPES = [
    "definition",
    "classification",
    "rule",
    "obligation",
    "process",
    "red_flag",
    "risk_indicator",
    "case_fact",
    "example",
    "fact",
    "needs_review",
]


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def source_batch_path(unit: dict[str, Any]) -> Path | None:
    value = (unit.get("source") or {}).get("batch_file")
    if not value:
        return None
    return BASE_UNITS_DIR / Path(str(value).replace("\\", "/"))


def load_source_row(unit: dict[str, Any], cache: dict[Path, list[dict[str, Any]]]) -> dict[str, Any] | None:
    path = source_batch_path(unit)
    request_id = str((unit.get("source") or {}).get("request_id") or "")
    if not path or not path.exists() or not request_id:
        return None
    if path not in cache:
        cache[path] = read_jsonl(path)
    for row in cache[path]:
        if str(row.get("request_id")) == request_id:
            return row
    return None


def sentence_lookup_from_row(row: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not row:
        return {}
    return {
        str(item.get("sentence_id")): item
        for item in row.get("payload", {}).get("window", {}).get("sentences", [])
        if item.get("sentence_id")
    }


def fallback_sentence_items(unit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for item in unit.get("en_sentences") or []:
        sid = str(item.get("sentence_id") or "")
        if not sid:
            continue
        out[sid] = {
            "sentence_id": sid,
            "text": item.get("text"),
            "role": "retrieval_slice",
            "parent_unit_id": unit.get("unit_id"),
        }
    return out


def build_row(unit: dict[str, Any], source_row: dict[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    sentence_by_id = sentence_lookup_from_row(source_row)
    fallback_by_id = fallback_sentence_items(unit)
    missing = []
    sentences = []
    for sid in unit.get("en_sentence_ids") or []:
        sid = str(sid)
        item = sentence_by_id.get(sid) or fallback_by_id.get(sid)
        if not item:
            missing.append(sid)
            continue
        sentences.append(dict(item))

    source = unit.get("source") or {}
    payload = (source_row or {}).get("payload", {})
    block_risk_flags = [
        flag
        for flag in payload.get("block_risk_flags", [])
        if flag not in {"block_may_continue_next", "paragraph_continues_across_page_candidate"}
    ]
    row = {
        "request_id": f"too_broad_resplit::{unit.get('unit_id')}",
        "block_id": source.get("en_block_id") or unit.get("source", {}).get("en_block_id"),
        "pdf_page": unit.get("pdf_page"),
        "printed_page": unit.get("printed_page"),
        "chapter": unit.get("chapter"),
        "payload": {
            "task": "group_english_sentences_into_base_knowledge_units",
            "prompt_version": "v7_unit_split_v2_too_broad_resplit",
            "constraints": [
                "Only group existing sentence_ids.",
                "Do not rewrite or invent source text.",
                "Split the prior too-broad unit into smaller citable textbook knowledge units.",
                "Prefer 1-2 sentences per group unless multiple sentences are inseparable.",
                "Do not isolate a sentence that begins with This, These, They, Such, or Their if it depends on the previous sentence; group it with the antecedent when the combined group is still one knowledge unit and no more than 3 sentences.",
                "If a sentence is teaching metadata, non-content, or unsafe as evidence, return needs_review.",
                "Return valid JSON only.",
            ],
            "allowed_unit_types": ALLOWED_UNIT_TYPES,
            "block_id": source.get("en_block_id"),
            "pdf_page": unit.get("pdf_page"),
            "printed_page": unit.get("printed_page"),
            "heading_stack": unit.get("heading_context", []),
            "block_text": unit.get("en_quote"),
            "route_reason": "too_broad_review_unit_requires_resplit",
            "block_risk_flags": block_risk_flags,
            "resplit_context": {
                "source_unit_id": unit.get("unit_id"),
                "source_unit_type": unit.get("unit_type"),
                "source_knowledge_en": unit.get("knowledge_en"),
                "source_decision_reason": unit.get("decision_reason"),
                "source_risk_flags": unit.get("risk_flags", []),
            },
            "window": {
                "window_index": 1,
                "sentence_ids": [item.get("sentence_id") for item in sentences],
                "sentences": sentences,
            },
            "expected_output_schema": {
                "sentence_groups": [
                    {
                        "sentence_ids": ["v7en_b000001_s001"],
                        "unit_type": "definition",
                        "knowledge_hint_en": "short English label",
                        "reason": "brief reason",
                        "risk_flags": [],
                    }
                ],
                "window_risk_flags": [],
            },
        },
    }
    return row, missing


def compact(text: str | None, limit: int = 220) -> str:
    value = " ".join(str(text or "").split())
    return value[:limit] + ("..." if len(value) > limit else "")


def build_report(rows: list[dict[str, Any]], manifest: dict[str, Any]) -> str:
    lines = [
        "# v7 Too-broad Resplit Batch",
        "",
        f"Generated at: {manifest['generated_at']}",
        "",
        "## Summary",
        "",
        f"- source: `{manifest['input_file']}`",
        f"- requests: {manifest['request_count']}",
        f"- missing sentence ids: {manifest['missing_sentence_id_count']}",
        f"- by chapter: {json.dumps(manifest['chapter_counts'], ensure_ascii=False)}",
        "",
        "## Samples",
        "",
    ]
    for row in rows[:12]:
        ctx = row["payload"]["resplit_context"]
        lines.extend(
            [
                f"### {ctx['source_unit_id']}",
                "",
                f"- chapter: {row.get('chapter')}",
                f"- page: {row.get('printed_page')} / pdf {row.get('pdf_page')}",
                f"- heading: {' / '.join(row['payload'].get('heading_stack', []))}",
                f"- source_knowledge_en: {ctx.get('source_knowledge_en')}",
                f"- sentence_ids: {', '.join(row['payload']['window']['sentence_ids'])}",
                f"- block_text: {compact(row['payload'].get('block_text'))}",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build DS batch for resplitting too-broad v7 review units.")
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-file", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_file = args.input_file.resolve()
    payload = read_json(input_file)
    source_cache: dict[Path, list[dict[str, Any]]] = {}
    rows = []
    missing_records = []
    for unit in payload.get("review_items", []):
        if "llm_group_too_broad_needs_review" not in set(unit.get("risk_flags", [])):
            continue
        source_row = load_source_row(unit, source_cache)
        row, missing = build_row(unit, source_row)
        rows.append(row)
        if missing:
            missing_records.append({"unit_id": unit.get("unit_id"), "sentence_ids": missing})

    write_jsonl(args.out_file, rows)
    manifest = {
        "schema_version": "v7_too_broad_resplit_batch_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(input_file),
        "out_file": str(args.out_file.resolve()),
        "request_count": len(rows),
        "missing_sentence_id_count": sum(len(item["sentence_ids"]) for item in missing_records),
        "missing_sentence_records": missing_records,
        "chapter_counts": dict(Counter(row.get("chapter") for row in rows).most_common()),
    }
    manifest_path = args.out_file.with_suffix(".manifest.json")
    report_path = args.out_file.with_suffix(".report.md")
    write_json(manifest_path, manifest)
    report_path.write_text(build_report(rows, manifest), encoding="utf-8")
    print(f"requests: {len(rows)}")
    print(f"missing sentence ids: {manifest['missing_sentence_id_count']}")
    print(f"wrote: {args.out_file}")
    print(f"wrote: {manifest_path}")
    print(f"wrote: {report_path}")


if __name__ == "__main__":
    main()
