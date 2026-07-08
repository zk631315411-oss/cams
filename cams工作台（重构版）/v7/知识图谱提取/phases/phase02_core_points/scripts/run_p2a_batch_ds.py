from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
KG_DIR = PHASE_DIR.parent.parent
DEFAULT_UNITS = KG_DIR / "phases" / "phase01_chapter_index" / "outputs" / "all_chapters_units.jsonl"
SINGLE_RUNNER = SCRIPT_DIR / "run_p2a_section_ds.py"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def discover_sections(units_file: Path) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in read_jsonl(units_file):
        grouped.setdefault(str(row.get("section_id")), []).append(row)

    sections: list[dict[str, Any]] = []
    for section_id, rows in grouped.items():
        rows = sorted(rows, key=lambda row: int(row.get("unit_order") or 0))
        sections.append(
            {
                "section_id": section_id,
                "chapter_id": rows[0].get("chapter_id"),
                "section_order": rows[0].get("section_order"),
                "section_title": rows[0].get("section_title"),
                "first_unit_order": int(rows[0].get("unit_order") or 0),
                "last_unit_order": int(rows[-1].get("unit_order") or 0),
                "unit_count": len(rows),
            }
        )
    return sorted(sections, key=lambda row: row["first_unit_order"])


def select_sections(args: argparse.Namespace) -> list[dict[str, Any]]:
    sections = discover_sections(args.units_file)
    start = 0
    if args.after_section_id:
        for index, row in enumerate(sections):
            if row["section_id"] == args.after_section_id:
                start = index + 1
                break
        else:
            raise ValueError(f"after_section_id not found: {args.after_section_id}")
    if args.start_section_id:
        for index, row in enumerate(sections):
            if row["section_id"] == args.start_section_id:
                start = index
                break
        else:
            raise ValueError(f"start_section_id not found: {args.start_section_id}")
    return sections[start : start + args.limit]


def run_one(args: argparse.Namespace, section: dict[str, Any]) -> dict[str, Any]:
    section_id = str(section["section_id"])
    run_slug = f"{args.run_prefix}{section_id}"
    cmd = [
        sys.executable,
        str(SINGLE_RUNNER),
        "--section-id",
        section_id,
        "--units-file",
        str(args.units_file),
        "--run-slug",
        run_slug,
        "--model",
        args.model,
        "--max-tokens",
        str(args.max_tokens),
        "--no-copy-outputs",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    status = "passed" if proc.returncode == 0 else "failed"
    cp_count = None
    label_count = None
    run_dir = PHASE_DIR / "runs" / run_slug
    parsed_path = run_dir / "parsed_response.json"
    manifest_path = run_dir / "run_manifest.json"
    if parsed_path.exists():
        parsed = read_json(parsed_path)
        cp_count = len(parsed.get("core_points") or [])
        label_count = len(parsed.get("unit_function_labels") or [])
    manifest_status = None
    if manifest_path.exists():
        manifest_status = read_json(manifest_path).get("status")
    return {
        **section,
        "run_slug": run_slug,
        "status": status,
        "manifest_status": manifest_status,
        "returncode": proc.returncode,
        "core_point_count": cp_count,
        "label_count": label_count,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--units-file", type=Path, default=DEFAULT_UNITS)
    parser.add_argument("--after-section-id", default=None)
    parser.add_argument("--start-section-id", default=None)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--run-prefix", default=None)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--max-tokens", type=int, default=32768)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.units_file = args.units_file.resolve()
    if args.run_prefix is None:
        args.run_prefix = "p2a_batch_" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_"

    selected = select_sections(args)
    if not selected:
        raise SystemExit("No sections selected for P2A batch.")

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        future_map = {executor.submit(run_one, args, section): section for section in selected}
        for future in as_completed(future_map):
            result = future.result()
            results.append(result)
            print(
                json.dumps(
                    {
                        "status": result["status"],
                        "manifest_status": result.get("manifest_status"),
                        "section_id": result["section_id"],
                        "core_points": result.get("core_point_count"),
                    },
                    ensure_ascii=False,
                )
            )

    order = {row["section_id"]: index for index, row in enumerate(selected)}
    results.sort(key=lambda row: order[row["section_id"]])
    summary = {
        "schema_version": "p2a_batch_ds_summary_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_prefix": args.run_prefix,
        "model": args.model,
        "max_tokens": args.max_tokens,
        "concurrency": args.concurrency,
        "after_section_id": args.after_section_id,
        "start_section_id": args.start_section_id,
        "selected_count": len(selected),
        "passed_count": sum(1 for row in results if row["status"] == "passed"),
        "failed_count": sum(1 for row in results if row["status"] != "passed"),
        "total_core_points": sum(row.get("core_point_count") or 0 for row in results),
        "results": results,
    }
    summary_path = PHASE_DIR / "reports" / f"{args.run_prefix.rstrip('_')}_summary.json"
    write_json(summary_path, summary)
    print(json.dumps({"summary_path": str(summary_path), "passed": summary["passed_count"], "failed": summary["failed_count"]}, ensure_ascii=False))
    if summary["failed_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
