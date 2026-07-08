from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DRAFT_DIR = BASE_UNITS_DIR / "draft"
REPORT_DIR = BASE_UNITS_DIR / "reports"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def summarize_file(path: Path) -> dict:
    payload = read_json(path)
    items = payload.get("items", [])
    review_items = payload.get("review_items", [])
    parent_items = payload.get("parent_items", [])
    all_units = [*items, *review_items, *parent_items]
    risk_flags = Counter(
        flag
        for unit in all_units
        for flag in unit.get("risk_flags", [])
    )
    audit = payload.get("audit", {})
    issues = audit.get("issues", [])
    return {
        "file": str(path.relative_to(BASE_UNITS_DIR)),
        "pilot_slug": payload.get("pilot_slug"),
        "chapter": payload.get("chapter"),
        "direct_units": len(items),
        "review_items": len(review_items),
        "parent_items": len(parent_items),
        "audit_issues": len(issues),
        "by_unit_type": dict(Counter(unit.get("unit_type") for unit in items)),
        "top_risk_flags": dict(risk_flags.most_common(12)),
        "has_blocking_issue": bool(issues),
    }


def build_summary(pattern: str, include_experiments: bool = False) -> dict:
    files = sorted(DRAFT_DIR.glob(pattern))
    if not include_experiments:
        files = [path for path in files if "_max4" not in path.name]
    rows = [summarize_file(path) for path in files]
    return {
        "schema_version": "v7_pilot_output_summary_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "pattern": pattern,
        "include_experiments": include_experiments,
        "files": len(files),
        "total_direct_units": sum(row["direct_units"] for row in rows),
        "total_review_items": sum(row["review_items"] for row in rows),
        "total_parent_items": sum(row["parent_items"] for row in rows),
        "total_audit_issues": sum(row["audit_issues"] for row in rows),
        "items": rows,
    }


def build_report(payload: dict) -> str:
    lines = [
        "# v7 Pilot Output Summary",
        "",
        f"Generated at: {payload['generated_at']}",
        "",
        f"- pattern: `{payload['pattern']}`",
        f"- include experiments: {payload['include_experiments']}",
        f"- files: {payload['files']}",
        f"- total direct units: {payload['total_direct_units']}",
        f"- total review items: {payload['total_review_items']}",
        f"- total parent/context items: {payload['total_parent_items']}",
        f"- total audit issues: {payload['total_audit_issues']}",
        "",
        "## Files",
        "",
    ]
    for row in payload["items"]:
        lines.extend(
            [
                f"### {row['pilot_slug']}",
                "",
                f"- file: `{row['file']}`",
                f"- chapter: {row.get('chapter')}",
                f"- direct/review/parent: {row['direct_units']} / {row['review_items']} / {row['parent_items']}",
                f"- audit issues: {row['audit_issues']}",
                f"- by unit_type: {json.dumps(row['by_unit_type'], ensure_ascii=False)}",
                f"- top risk flags: {json.dumps(row['top_risk_flags'], ensure_ascii=False)}",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", default="v7_units_draft.pilot_*.combined.json")
    parser.add_argument("--include-experiments", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_summary(args.pattern, args.include_experiments)
    out_json = args.out_dir / "pilot_output_summary.json"
    out_report = args.out_dir / "pilot_output_summary_report.md"
    write_json(out_json, payload)
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_report.write_text(build_report(payload), encoding="utf-8")
    print(f"files: {payload['files']}")
    print(f"total direct units: {payload['total_direct_units']}")
    print(f"total review items: {payload['total_review_items']}")
    print(f"total audit issues: {payload['total_audit_issues']}")
    print(f"wrote: {out_json}")
    print(f"wrote: {out_report}")


if __name__ == "__main__":
    main()
