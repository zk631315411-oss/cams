from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
OUTPUT_DIR = PHASE_DIR / "outputs"
REPORT_DIR = PHASE_DIR / "reports"
PREVIEW_DIR = PHASE_DIR / "previews"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists() or path.stat().st_size == 0:
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL row in {path}:{line_no}: {exc}") from exc
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def batch_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"batch(\d+)", path.name)
    return (int(match.group(1)) if match else 9999, path.name)


def chapter_from_relation_id(relation_id: str | None) -> str | None:
    if not relation_id:
        return None
    match = re.search(r"p3a_rel_(CH\d{2})_", relation_id)
    return match.group(1) if match else None


def relation_id(row: dict[str, Any]) -> str | None:
    return row.get("relation_id") or row.get("p3_relation_id")


def collect(pattern: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    source_files: list[str] = []
    for path in sorted(OUTPUT_DIR.glob(pattern), key=batch_sort_key):
        source_files.append(path.name)
        rows.extend(read_jsonl(path))
    return rows, source_files


def dedupe_by_relation_id(rows: list[dict[str, Any]], label: str) -> tuple[list[dict[str, Any]], list[str]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    duplicates: list[str] = []
    for row in rows:
        rid = relation_id(row)
        if not rid:
            duplicates.append(f"{label}:missing_relation_id")
            continue
        if rid in seen:
            duplicates.append(rid)
            continue
        seen.add(rid)
        deduped.append(row)
    return deduped, duplicates


def normalize_evidence_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        rid = relation_id(item)
        if rid and "p3_relation_id" not in item:
            item["p3_relation_id"] = rid
        if rid and "chapter_id" not in item:
            chapter_id = chapter_from_relation_id(rid)
            if chapter_id:
                item["chapter_id"] = chapter_id
        normalized.append(item)
    return normalized


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts = Counter(str(row.get(key) or "missing") for row in rows)
    return dict(sorted(counts.items()))


def build_preview(accepted: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> str:
    evidence_by_id = {relation_id(row): row for row in evidence}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rel in accepted:
        grouped[str(rel.get("chapter_id") or chapter_from_relation_id(relation_id(rel)) or "UNKNOWN")].append(rel)

    lines = ["# P3 core point relations preview", ""]
    for chapter_id in sorted(grouped):
        rels = grouped[chapter_id]
        lines.append(f"## {chapter_id}")
        lines.append("")
        for rel in rels:
            rid = relation_id(rel)
            ev = evidence_by_id.get(rid) or {}
            lines.append(f"- `{rid}` `{rel.get('relation_type')}` {rel.get('source_core_point_id')} -> {rel.get('target_core_point_id')}")
            if rel.get("review_reason"):
                lines.append(f"  - review: {rel.get('review_reason')}")
            elif rel.get("reason"):
                lines.append(f"  - reason: {rel.get('reason')}")
            if ev.get("support_strength"):
                lines.append(f"  - evidence: {ev.get('support_strength')}; source_units={len(ev.get('source_evidence_unit_ids') or [])}; target_units={len(ev.get('target_evidence_unit_ids') or [])}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="Fail if accepted relations and P3B evidence do not match exactly.")
    args = parser.parse_args()

    candidates, candidate_files = collect("p3a_candidates_batch*_CH*.jsonl")
    accepted, accepted_files = collect("p3a_reviewed_relations_batch*_CH*.jsonl")
    rejected, rejected_files = collect("p3a_rejected_relations_batch*_CH*.jsonl")
    evidence_raw, evidence_files = collect("p3b_relation_unit_evidence_batch*_CH*.jsonl")
    evidence = normalize_evidence_rows(evidence_raw)

    candidates, duplicate_candidates = dedupe_by_relation_id(candidates, "candidates")
    accepted, duplicate_accepted = dedupe_by_relation_id(accepted, "accepted")
    rejected, duplicate_rejected = dedupe_by_relation_id(rejected, "rejected")
    evidence, duplicate_evidence = dedupe_by_relation_id(evidence, "evidence")

    accepted_ids = {relation_id(row) for row in accepted}
    evidence_ids = {relation_id(row) for row in evidence}
    missing_evidence = sorted(str(rid) for rid in accepted_ids - evidence_ids if rid)
    extra_evidence = sorted(str(rid) for rid in evidence_ids - accepted_ids if rid)

    write_jsonl(OUTPUT_DIR / "p3_core_point_relation_candidates.jsonl", candidates)
    write_jsonl(OUTPUT_DIR / "p3_core_point_relations.jsonl", accepted)
    write_jsonl(OUTPUT_DIR / "p3_rejected_core_point_relations.jsonl", rejected)
    write_jsonl(OUTPUT_DIR / "p3_relation_unit_evidence.jsonl", evidence)

    relation_type_counts = count_by(accepted, "relation_type")
    evidence_strength_counts = count_by(evidence, "support_strength")
    accepted_by_chapter = count_by(accepted, "chapter_id")
    rejected_by_chapter = count_by(rejected, "chapter_id")

    generated_at = datetime.now().isoformat(timespec="seconds")
    report = {
        "schema_version": "p3_full_book_materialization_report_v1",
        "generated_at": generated_at,
        "source_files": {
            "candidates": candidate_files,
            "accepted": accepted_files,
            "rejected": rejected_files,
            "evidence": evidence_files,
        },
        "counts": {
            "candidate_relation_count": len(candidates),
            "accepted_relation_count": len(accepted),
            "rejected_relation_count": len(rejected),
            "evidence_binding_count": len(evidence),
            "missing_evidence_count": len(missing_evidence),
            "extra_evidence_count": len(extra_evidence),
        },
        "relation_type_counts": relation_type_counts,
        "evidence_strength_counts": evidence_strength_counts,
        "accepted_by_chapter": accepted_by_chapter,
        "rejected_by_chapter": rejected_by_chapter,
        "issues": {
            "duplicate_candidates": duplicate_candidates,
            "duplicate_accepted": duplicate_accepted,
            "duplicate_rejected": duplicate_rejected,
            "duplicate_evidence": duplicate_evidence,
            "missing_evidence": missing_evidence,
            "extra_evidence": extra_evidence,
        },
        "outputs": {
            "candidate_relations": "outputs/p3_core_point_relation_candidates.jsonl",
            "accepted_relations": "outputs/p3_core_point_relations.jsonl",
            "rejected_relations": "outputs/p3_rejected_core_point_relations.jsonl",
            "relation_unit_evidence": "outputs/p3_relation_unit_evidence.jsonl",
            "preview": "previews/p3_core_point_relations_preview.md",
        },
    }
    write_json(REPORT_DIR / "p3_materialization_report.json", report)

    report_lines = [
        "# P3 materialization report",
        "",
        f"- generated_at: {generated_at}",
        f"- candidate_relation_count: {len(candidates)}",
        f"- accepted_relation_count: {len(accepted)}",
        f"- rejected_relation_count: {len(rejected)}",
        f"- evidence_binding_count: {len(evidence)}",
        f"- missing_evidence_count: {len(missing_evidence)}",
        f"- extra_evidence_count: {len(extra_evidence)}",
        "",
        "## Relation Types",
        "",
    ]
    report_lines.extend(f"- {key}: {value}" for key, value in relation_type_counts.items())
    report_lines.extend(["", "## Evidence Strength", ""])
    report_lines.extend(f"- {key}: {value}" for key, value in evidence_strength_counts.items())
    report_lines.extend(["", "## Source Files", ""])
    report_lines.extend(f"- {kind}: {len(files)}" for kind, files in report["source_files"].items())
    report_lines.extend(["", "## Issues", ""])
    if missing_evidence or extra_evidence or duplicate_candidates or duplicate_accepted or duplicate_rejected or duplicate_evidence:
        report_lines.append(f"- duplicate_candidates: {len(duplicate_candidates)}")
        report_lines.append(f"- duplicate_accepted: {len(duplicate_accepted)}")
        report_lines.append(f"- duplicate_rejected: {len(duplicate_rejected)}")
        report_lines.append(f"- duplicate_evidence: {len(duplicate_evidence)}")
        report_lines.append(f"- missing_evidence: {len(missing_evidence)}")
        report_lines.append(f"- extra_evidence: {len(extra_evidence)}")
    else:
        report_lines.append("- none")
    (REPORT_DIR / "p3_materialization_report.md").write_text("\n".join(report_lines).rstrip() + "\n", encoding="utf-8")
    (PREVIEW_DIR / "p3_core_point_relations_preview.md").write_text(build_preview(accepted, evidence), encoding="utf-8")

    if args.strict and (missing_evidence or extra_evidence or duplicate_accepted or duplicate_evidence):
        return 1
    print(json.dumps(report["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
