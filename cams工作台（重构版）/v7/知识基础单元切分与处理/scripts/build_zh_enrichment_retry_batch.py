from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DEFAULT_BATCH = BASE_UNITS_DIR / "llm_batches" / "zh_enrichment" / "v7_zh_enrichment_batch.v1.jsonl"
DEFAULT_MANIFEST = BASE_UNITS_DIR / "llm_runs" / "ds_zh_enrichment_v1_full" / "run_manifest.json"
DEFAULT_OUT = BASE_UNITS_DIR / "llm_batches" / "zh_enrichment" / "v7_zh_enrichment_batch.v1.retry_split5.jsonl"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def failed_request_ids(manifest: dict[str, Any]) -> list[str]:
    return [
        str(item.get("request_id"))
        for item in manifest.get("results", [])
        if str(item.get("status")) != "passed"
    ]


def build_retry_rows(batch_file: Path, manifest_file: Path, split_size: int) -> list[dict[str, Any]]:
    rows = read_jsonl(batch_file)
    manifest = read_json(manifest_file)
    failed = set(failed_request_ids(manifest))
    retry_rows = []
    for row in rows:
        if str(row.get("request_id")) not in failed:
            continue
        units = row.get("payload", {}).get("units", [])
        for idx in range(0, len(units), split_size):
            chunk = units[idx : idx + split_size]
            retry = dict(row)
            retry["request_id"] = f"{row['request_id']}_retry_{idx // split_size + 1:02d}"
            retry["unit_count"] = len(chunk)
            retry["unit_ids"] = [unit.get("tmp_unit_id") for unit in chunk]
            retry["payload"] = dict(row.get("payload") or {})
            retry["payload"]["units"] = chunk
            retry["payload"]["retry_of"] = row.get("request_id")
            retry_rows.append(retry)
    return retry_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build smaller retry batch for failed zh enrichment requests.")
    parser.add_argument("--batch-file", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--manifest-file", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-file", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--split-size", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_retry_rows(args.batch_file.resolve(), args.manifest_file.resolve(), args.split_size)
    write_jsonl(args.out_file, rows)
    print(f"retry requests: {len(rows)}")
    print(f"units: {sum(row['unit_count'] for row in rows)}")
    print(f"split_size: {args.split_size}")
    print(f"wrote: {args.out_file}")


if __name__ == "__main__":
    main()
