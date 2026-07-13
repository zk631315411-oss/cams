# -*- coding: utf-8 -*-
"""Summarize s1 direct retrieval A/B outputs.

This script does not run retrieval. It reads existing s1 JSON files and writes
compact head-level and question-level summaries for s2/s3 inspection.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
OUTPUT_DIR = HERE / "output" / "s1_direct_unit_retrieval"
SUMMARY_DIR = HERE / "output" / "s1_summary"
EXPERIMENTS = ("s0a", "s0b", "s0c")


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def qid_num(qid: str) -> int | None:
    try:
        return int(qid.rsplit("_", 1)[1])
    except Exception:
        return None


def doc_path(input_dir: Path, experiment: str, qid: str) -> Path:
    return input_dir / experiment / f"{qid}.s1.{experiment}.json"


def available_question_ids(input_dir: Path, experiment: str) -> list[str]:
    ids: list[str] = []
    for path in (input_dir / experiment).glob(f"*.s1.{experiment}.json"):
        ids.append(path.name.split(".s1.", 1)[0])
    return sorted(ids)


def select_question_ids(
    input_dir: Path,
    experiments: list[str],
    question_ids: list[str],
    limit: int | None,
    offset: int,
) -> list[str]:
    if question_ids:
        return sorted(question_ids)
    id_sets = [set(available_question_ids(input_dir, experiment)) for experiment in experiments]
    if not id_sets:
        return []
    ids = sorted(set.intersection(*id_sets), key=lambda qid: (qid_num(qid) is None, qid_num(qid) or 0, qid))
    if limit is None and offset <= 0:
        return ids
    start = max(offset, 0)
    end = None if limit is None else start + max(limit, 0)
    return ids[start:end]


def one_line(text: str, max_len: int = 90) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def unit_brief(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "unit_id": row.get("unit_id", ""),
        "best_route": row.get("best_route", ""),
        "best_score_norm": row.get("best_score_norm", ""),
        "summary": one_line(row.get("knowledge_zh") or row.get("en_quote"), 120),
    }


def variant_units(head: dict[str, Any], variant: str) -> list[dict[str, Any]]:
    return head.get("variants", {}).get(variant, {}).get("merged_units", []) or []


def unit_ids(rows: list[dict[str, Any]]) -> set[str]:
    return {str(row.get("unit_id")) for row in rows if row.get("unit_id")}


def has_query_change(head: dict[str, Any]) -> bool:
    variants = head.get("variants", {}) or {}
    baseline = str(variants.get("query_baseline", {}).get("query", "")).strip()
    test = str(variants.get("query_test", {}).get("query", "")).strip()
    return baseline != test


def head_summary(doc: dict[str, Any], head: dict[str, Any], top_units: int) -> dict[str, Any]:
    diff = head.get("variant_diff", {}) or {}
    baseline = variant_units(head, "query_baseline")
    test = variant_units(head, "query_test")
    added = diff.get("added_by_test", []) or []
    dropped = diff.get("dropped_by_test", []) or []
    common = diff.get("common_unit_ids", []) or []
    union_count = len(unit_ids(baseline) | unit_ids(test))
    change_ratio = round((len(added) + len(dropped)) / union_count, 4) if union_count else 0.0
    return {
        "question_id": doc.get("question_id", ""),
        "experiment": doc.get("source_experiment", ""),
        "head_id": head.get("head_id", ""),
        "head_kind": head.get("head_kind", ""),
        "option": head.get("option", ""),
        "baseline_label": head.get("baseline_label", ""),
        "test_label": head.get("test_label", ""),
        "has_p5_change": has_query_change(head),
        "baseline_count": len(baseline),
        "test_count": len(test),
        "common_count": len(common),
        "added_count": len(added),
        "dropped_count": len(dropped),
        "union_count": union_count,
        "change_ratio": change_ratio,
        "top_added_units": [unit_brief(row) for row in added[:top_units]],
        "top_dropped_units": [unit_brief(row) for row in dropped[:top_units]],
    }


def aggregate_question(question_id: str, rows: list[dict[str, Any]], docs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"question_id": question_id}
    flags: list[str] = []
    for experiment in EXPERIMENTS:
        erows = [row for row in rows if row["experiment"] == experiment]
        out[f"{experiment}_heads"] = len(erows)
        out[f"{experiment}_changed_heads"] = sum(1 for row in erows if row["added_count"] or row["dropped_count"])
        out[f"{experiment}_added"] = sum(int(row["added_count"]) for row in erows)
        out[f"{experiment}_dropped"] = sum(int(row["dropped_count"]) for row in erows)
        out[f"{experiment}_common"] = sum(int(row["common_count"]) for row in erows)
        if erows:
            out[f"{experiment}_avg_change_ratio"] = round(
                sum(float(row["change_ratio"]) for row in erows) / len(erows), 4
            )
        else:
            out[f"{experiment}_avg_change_ratio"] = 0.0

    s0c_doc = docs.get("s0c")
    if s0c_doc:
        baseline_ids: set[str] = set()
        test_ids: set[str] = set()
        for head in s0c_doc.get("heads", []) or []:
            baseline_ids |= unit_ids(variant_units(head, "query_baseline"))
            test_ids |= unit_ids(variant_units(head, "query_test"))
        out["recommended_pool"] = "baseline_union_s0c"
        out["recommended_pool_unit_count"] = len(baseline_ids | test_ids)
        out["recommended_common_unit_count"] = len(baseline_ids & test_ids)
    else:
        out["recommended_pool"] = "missing_s0c"
        out["recommended_pool_unit_count"] = 0
        out["recommended_common_unit_count"] = 0

    if out.get("s0a_avg_change_ratio", 0) >= 0.7:
        flags.append("s0a_high_disruption")
    if out.get("s0b_avg_change_ratio", 0) >= 0.6:
        flags.append("s0b_high_disruption")
    if out.get("s0c_avg_change_ratio", 0) >= 0.5:
        flags.append("s0c_high_disruption")
    if out.get("recommended_common_unit_count", 0) < 5 and out.get("recommended_pool_unit_count", 0) > 0:
        flags.append("low_baseline_s0c_overlap")
    out["risk_flags"] = flags
    return out


def render_markdown(question_rows: list[dict[str, Any]], head_rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("# s1 Summary\n\n")
    lines.append("## Experiment Totals\n\n")
    lines.append("| experiment | questions | heads | changed_heads | added | dropped | common | avg_change_ratio |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|\n")
    for experiment in EXPERIMENTS:
        erows = [row for row in head_rows if row["experiment"] == experiment]
        questions = {row["question_id"] for row in erows}
        changed = sum(1 for row in erows if row["added_count"] or row["dropped_count"])
        avg = round(sum(float(row["change_ratio"]) for row in erows) / len(erows), 4) if erows else 0.0
        lines.append(
            f"| {experiment} | {len(questions)} | {len(erows)} | {changed} | "
            f"{sum(int(row['added_count']) for row in erows)} | "
            f"{sum(int(row['dropped_count']) for row in erows)} | "
            f"{sum(int(row['common_count']) for row in erows)} | {avg} |\n"
        )

    lines.append("\n## High Change Questions\n\n")
    lines.append("| question_id | s0a_change | s0b_change | s0c_change | pool_units | flags |\n")
    lines.append("|---|---:|---:|---:|---:|---|\n")
    ranked = sorted(
        question_rows,
        key=lambda row: (
            row.get("s0c_avg_change_ratio", 0),
            row.get("s0b_avg_change_ratio", 0),
            row.get("s0a_avg_change_ratio", 0),
        ),
        reverse=True,
    )
    for row in ranked[:30]:
        lines.append(
            f"| {row['question_id']} | {row.get('s0a_avg_change_ratio', 0)} | "
            f"{row.get('s0b_avg_change_ratio', 0)} | {row.get('s0c_avg_change_ratio', 0)} | "
            f"{row.get('recommended_pool_unit_count', 0)} | {', '.join(row.get('risk_flags', []))} |\n"
        )
    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="summarize existing s1 retrieval outputs")
    parser.add_argument("--experiment", choices=["s0a", "s0b", "s0c", "all"], default="all")
    parser.add_argument("--question-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--input-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--output-dir", default=str(SUMMARY_DIR))
    parser.add_argument("--top-units", type=int, default=5)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    experiments = list(EXPERIMENTS) if args.experiment == "all" else [args.experiment]
    question_ids = select_question_ids(input_dir, experiments, args.question_id, args.limit, args.offset)
    if not question_ids:
        raise RuntimeError("no s1 outputs selected")

    head_rows: list[dict[str, Any]] = []
    question_docs: dict[str, dict[str, dict[str, Any]]] = {qid: {} for qid in question_ids}
    missing: list[str] = []
    for qid in question_ids:
        for experiment in experiments:
            path = doc_path(input_dir, experiment, qid)
            if not path.exists():
                missing.append(str(path))
                continue
            doc = load_json(path)
            question_docs[qid][experiment] = doc
            for head in doc.get("heads", []) or []:
                head_rows.append(head_summary(doc, head, top_units=args.top_units))
    if missing:
        raise FileNotFoundError("missing s1 output files: " + "; ".join(missing[:20]))

    question_rows = [
        aggregate_question(qid, [row for row in head_rows if row["question_id"] == qid], question_docs[qid])
        for qid in question_ids
    ]

    write_json(output_dir / "summary_heads.json", head_rows)
    write_json(output_dir / "summary_questions.json", question_rows)
    write_csv(output_dir / "summary_heads.csv", head_rows)
    write_csv(output_dir / "summary_questions.csv", question_rows)
    write_text(output_dir / "summary.md", render_markdown(question_rows, head_rows))
    print(f"[ok] questions={len(question_rows)} heads={len(head_rows)} -> {output_dir}")


if __name__ == "__main__":
    main()
