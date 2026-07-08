from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
RUNS_DIR = PHASE_DIR / "runs"
OUTPUTS_DIR = PHASE_DIR / "outputs"
REPORTS_DIR = PHASE_DIR / "reports"
PREVIEWS_DIR = PHASE_DIR / "previews"

RELATION_TYPES = {"contains", "illustrates", "prepares", "parallels", "contrasts"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(text + ("\n" if rows else ""), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def section_id_from_run_name(name: str) -> str | None:
    match = re.search(r"(CH\d+-S\d+)$", name)
    return match.group(1) if match else None


def latest_p2c_run_by_section() -> dict[str, Path]:
    latest: dict[str, Path] = {}
    for run_dir in RUNS_DIR.glob("p2c*"):
        if not run_dir.is_dir() or not (run_dir / "parsed_response.json").exists():
            continue
        section_id = section_id_from_run_name(run_dir.name)
        if not section_id:
            continue
        if section_id not in latest or run_dir.stat().st_mtime > latest[section_id].stat().st_mtime:
            latest[section_id] = run_dir
    return latest


def reviewed_relations_by_section() -> dict[str, dict[str, Any]]:
    reviewed: dict[str, dict[str, Any]] = {}
    for path in sorted(OUTPUTS_DIR.glob("p2c_reviewed_relations.CH*-S*.json")):
        payload = read_json(path)
        section_id = payload.get("section_id") or path.stem.replace("p2c_reviewed_relations.", "", 1)
        reviewed[section_id] = {"path": path, "payload": payload}
    return reviewed


def normalize_relation(rel: dict[str, Any], section_id: str, source_run: str, source_path: str, source_kind: str) -> dict[str, Any]:
    return {
        "relation_id": rel.get("relation_id")
        or f"p2c_rel_{section_id.replace('-', '_')}_{rel.get('source_core_point_id')}_{rel.get('target_core_point_id')}",
        "section_id": section_id,
        "source_core_point_id": rel.get("source_core_point_id"),
        "target_core_point_id": rel.get("target_core_point_id"),
        "relation_type": rel.get("relation_type"),
        "reason": rel.get("reason"),
        "source_kind": source_kind,
        "source_run": source_run,
        "source_path": source_path,
    }


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    latest_runs = latest_p2c_run_by_section()
    reviewed = reviewed_relations_by_section()
    rows: list[dict[str, Any]] = []
    selected_sources: dict[str, str] = {}
    invalid_rows: list[dict[str, Any]] = []

    for section_id in sorted(latest_runs):
        run_dir = latest_runs[section_id]
        if section_id in reviewed:
            payload = reviewed[section_id]["payload"]
            relations = payload.get("core_point_relations") or []
            deleted_ids = set(payload.get("deleted_relation_ids") or [])
            source_path = str(reviewed[section_id]["path"])
            source_kind = "p2c_reviewed_output"
            source_run = payload.get("source_p2c_run") or run_dir.name
        else:
            payload = read_json(run_dir / "parsed_response.json")
            relations = payload.get("core_point_relations") or []
            deleted_ids = set()
            source_path = str(run_dir / "parsed_response.json")
            source_kind = "p2c_run_latest"
            source_run = run_dir.name
        selected_sources[section_id] = source_kind
        for rel in relations:
            rel_id = rel.get("relation_id")
            if rel_id and rel_id in deleted_ids:
                continue
            row = normalize_relation(rel, section_id, source_run, source_path, source_kind)
            if (
                not row.get("relation_id")
                or not row.get("source_core_point_id")
                or not row.get("target_core_point_id")
                or row.get("relation_type") not in RELATION_TYPES
            ):
                invalid_rows.append(row)
            rows.append(row)

    relation_id_counts = Counter(row["relation_id"] for row in rows)
    duplicate_relation_ids = sorted(rel_id for rel_id, count in relation_id_counts.items() if count > 1)
    meta = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "section_run_count": len(latest_runs),
        "reviewed_section_count": len(reviewed),
        "relation_count": len(rows),
        "relation_type_counts": dict(Counter(row.get("relation_type") for row in rows)),
        "source_kind_counts": dict(Counter(selected_sources.values())),
        "invalid_row_count": len(invalid_rows),
        "invalid_rows_sample": invalid_rows[:20],
        "duplicate_relation_id_count": len(duplicate_relation_ids),
        "duplicate_relation_ids_sample": duplicate_relation_ids[:20],
    }
    return rows, meta


def render_report(meta: dict[str, Any]) -> str:
    lines = [
        "# P2C materialization report",
        "",
        f"- generated_at: {meta['generated_at']}",
        f"- section_run_count: {meta['section_run_count']}",
        f"- reviewed_section_count: {meta['reviewed_section_count']}",
        f"- relation_count: {meta['relation_count']}",
        f"- invalid_row_count: {meta['invalid_row_count']}",
        f"- duplicate_relation_id_count: {meta['duplicate_relation_id_count']}",
        "",
        "## Source Kinds",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in sorted(meta["source_kind_counts"].items()))
    lines.extend(["", "## Relation Types", ""])
    lines.extend(f"- {key}: {value}" for key, value in sorted(meta["relation_type_counts"].items()))
    if meta["invalid_rows_sample"]:
        lines.extend(["", "## Invalid Row Sample", ""])
        for row in meta["invalid_rows_sample"]:
            lines.append(f"- {row.get('relation_id')}: {row.get('source_core_point_id')} -> {row.get('target_core_point_id')} ({row.get('relation_type')})")
    if meta["duplicate_relation_ids_sample"]:
        lines.extend(["", "## Duplicate Relation IDs", ""])
        lines.extend(f"- {rel_id}" for rel_id in meta["duplicate_relation_ids_sample"])
    return "\n".join(lines) + "\n"


def render_preview(rows: list[dict[str, Any]]) -> str:
    lines = ["# P2C core point relations preview", ""]
    current_section = None
    for row in rows:
        if row["section_id"] != current_section:
            current_section = row["section_id"]
            lines.extend(["", f"## {current_section}", ""])
        lines.append(
            f"- `{row['relation_type']}`: `{row['source_core_point_id']}` -> `{row['target_core_point_id']}`"
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    rows, meta = build_rows()
    write_jsonl(OUTPUTS_DIR / "p2c_core_point_relations.jsonl", rows)
    write_json(REPORTS_DIR / "p2c_materialization_report.json", meta)
    write_text(REPORTS_DIR / "p2c_materialization_report.md", render_report(meta))
    write_text(PREVIEWS_DIR / "p2c_core_point_relations_preview.md", render_preview(rows))
    print(json.dumps(meta, ensure_ascii=False))


if __name__ == "__main__":
    main()
