from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DEFAULT_BATCH = BASE_UNITS_DIR / "llm_batches" / "zh_enrichment" / "v7_zh_enrichment_batch.v1.jsonl"
DEFAULT_FULL = BASE_UNITS_DIR / "llm_batches" / "zh_enrichment" / "v7_zh_enrichment_decisions.v1.ds.jsonl"
DEFAULT_RETRY = BASE_UNITS_DIR / "llm_batches" / "zh_enrichment" / "v7_zh_enrichment_decisions.v1.retry_split5.ds.jsonl"
DEFAULT_OUT = BASE_UNITS_DIR / "llm_batches" / "zh_enrichment" / "v7_zh_enrichment_decisions.v1.final.ds.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def original_request_id(retry_request_id: str) -> str:
    return re.sub(r"_retry_\d+$", "", retry_request_id)


def merge(batch_file: Path, full_file: Path, retry_file: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    batch_rows = read_jsonl(batch_file)
    expected_ids_by_request = {
        str(row.get("request_id")): [str(unit_id) for unit_id in row.get("unit_ids", [])]
        for row in batch_rows
    }
    full_rows = read_jsonl(full_file)
    retry_rows = read_jsonl(retry_file)
    retry_units_by_original: dict[str, dict[str, dict[str, Any]]] = {}
    retry_meta_by_original: dict[str, list[dict[str, Any]]] = {}
    for row in retry_rows:
        retry_request_id = str(row.get("request_id"))
        original_id = original_request_id(retry_request_id)
        retry_units_by_original.setdefault(original_id, {})
        retry_meta_by_original.setdefault(original_id, [])
        retry_meta = dict(row.get("_meta") or {})
        retry_meta["request_id"] = retry_request_id
        retry_meta_by_original[original_id].append(retry_meta)
        for unit in row.get("units", []):
            retry_units_by_original[original_id][str(unit.get("tmp_unit_id"))] = unit

    merged = []
    replaced = []
    kept = 0
    for row in full_rows:
        request_id = str(row.get("request_id"))
        status = str((row.get("_meta") or {}).get("status") or "")
        if status == "passed":
            merged.append(row)
            kept += 1
            continue
        expected_ids = expected_ids_by_request.get(request_id, [])
        retry_units = retry_units_by_original.get(request_id, {})
        missing = [unit_id for unit_id in expected_ids if unit_id not in retry_units]
        if missing:
            raise RuntimeError(f"retry results missing units for {request_id}: {missing[:5]}")
        merged_row = {
            "request_id": request_id,
            "units": [retry_units[unit_id] for unit_id in expected_ids],
            "_meta": {
                **(row.get("_meta") or {}),
                "status": "passed",
                "merged_from_retry": True,
                "original_status": status,
                "retry_request_ids": [meta.get("request_id") for meta in retry_meta_by_original.get(request_id, [])],
                "retry_meta": retry_meta_by_original.get(request_id, []),
            },
        }
        merged.append(merged_row)
        replaced.append(request_id)
    return merged, {"kept": kept, "replaced": replaced, "retry_rows": len(retry_rows)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge passed full zh enrichment decisions with smaller retry decisions.")
    parser.add_argument("--batch-file", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--full-decisions-file", type=Path, default=DEFAULT_FULL)
    parser.add_argument("--retry-decisions-file", type=Path, default=DEFAULT_RETRY)
    parser.add_argument("--out-file", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    merged, summary = merge(
        args.batch_file.resolve(),
        args.full_decisions_file.resolve(),
        args.retry_decisions_file.resolve(),
    )
    write_jsonl(args.out_file, merged)
    print(f"merged requests: {len(merged)}")
    print(f"kept: {summary['kept']}")
    print(f"replaced: {len(summary['replaced'])} {summary['replaced']}")
    print(f"retry rows: {summary['retry_rows']}")
    print(f"wrote: {args.out_file}")


if __name__ == "__main__":
    main()
