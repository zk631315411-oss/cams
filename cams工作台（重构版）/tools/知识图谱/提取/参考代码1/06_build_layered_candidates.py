"""
v4.4 Step 6: build layered candidate packages.

This step does not decide review items and does not write to Neo4j. It only
separates Step 5 outputs into stable phase-one layers:
explicit_core, example_application, review_pending, and rejected_archive.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DIR = SCRIPT_DIR / "中间产物"

DEFAULT_MAIN_NODES = DEFAULT_DIR / "kg_main_nodes.jsonl"
DEFAULT_MAIN_EDGES = DEFAULT_DIR / "kg_main_edges.jsonl"
DEFAULT_RULE_CASES = DEFAULT_DIR / "kg_rule_cases.jsonl"
DEFAULT_REVIEW_NODES = DEFAULT_DIR / "step5_review_nodes.jsonl"
DEFAULT_REVIEW_EDGES = DEFAULT_DIR / "step5_review_edges.jsonl"
DEFAULT_REVIEW_RULE_CASES = DEFAULT_DIR / "step5_review_rule_cases.jsonl"
DEFAULT_REJECTED = DEFAULT_DIR / "step5_rejected_items.jsonl"
DEFAULT_AGGR_CANDIDATES = DEFAULT_DIR / "step5b_aggr_candidates.jsonl"

DEFAULT_LAYER_DIR = DEFAULT_DIR / "step6_layers"
DEFAULT_REPORT = DEFAULT_LAYER_DIR / "step6_layer_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build v4.4 phase-one KG layers from Step 5 outputs.")
    parser.add_argument("--main-nodes", type=Path, default=DEFAULT_MAIN_NODES)
    parser.add_argument("--main-edges", type=Path, default=DEFAULT_MAIN_EDGES)
    parser.add_argument("--rule-cases", type=Path, default=DEFAULT_RULE_CASES)
    parser.add_argument("--review-nodes", type=Path, default=DEFAULT_REVIEW_NODES)
    parser.add_argument("--review-edges", type=Path, default=DEFAULT_REVIEW_EDGES)
    parser.add_argument("--review-rule-cases", type=Path, default=DEFAULT_REVIEW_RULE_CASES)
    parser.add_argument("--rejected", type=Path, default=DEFAULT_REJECTED)
    parser.add_argument("--aggr-candidates", type=Path, default=DEFAULT_AGGR_CANDIDATES)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_LAYER_DIR)
    return parser.parse_args()


def read_jsonl(path: Path, required: bool = True) -> list[dict[str, Any]]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"JSONL not found: {path}")
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def with_step6(row: dict[str, Any], layer: str, status: str) -> dict[str, Any]:
    item = dict(row)
    item["step6_layer"] = layer
    item["step6_status"] = status
    item["step6_generated_at"] = datetime.now().isoformat(timespec="seconds")
    return item


def type_counts(rows: list[dict[str, Any]], field: str = "type") -> Counter[str]:
    return Counter(str(row.get(field) or "") for row in rows)


def write_report(
    path: Path,
    explicit_nodes: list[dict[str, Any]],
    explicit_edges: list[dict[str, Any]],
    app_nodes: list[dict[str, Any]],
    app_edges: list[dict[str, Any]],
    review_nodes: list[dict[str, Any]],
    review_edges: list[dict[str, Any]],
    rule_cases: list[dict[str, Any]],
    review_rule_cases: list[dict[str, Any]],
    aggr_candidates: list[dict[str, Any]],
    rejected: list[dict[str, Any]],
) -> None:
    lines = [
        "# v4.4 Step 6 Layer Report",
        "",
        "## Layer Counts",
        f"- explicit_core_nodes: {len(explicit_nodes)}",
        f"- explicit_core_edges: {len(explicit_edges)}",
        f"- example_application_nodes: {len(app_nodes)}",
        f"- example_application_edges: {len(app_edges)}",
        f"- rule_cases: {len(rule_cases)}",
        f"- review_pending_nodes: {len(review_nodes)}",
        f"- review_pending_edges: {len(review_edges)}",
        f"- review_pending_rule_cases: {len(review_rule_cases)}",
        f"- review_pending_merge_candidates: {len(aggr_candidates)}",
        f"- rejected_archive_items: {len(rejected)}",
        f"- implicit_deferred_items: 0",
        "",
        "## Explicit Core Node Types",
    ]
    for key, value in sorted(type_counts(explicit_nodes).items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Explicit Core Edge Types"])
    for key, value in sorted(type_counts(explicit_edges).items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Review Pending Node Types"])
    for key, value in sorted(type_counts(review_nodes).items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Review Pending Edge Types"])
    for key, value in sorted(type_counts(review_edges).items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Review Pending Rule Case Owners"])
    for key, value in sorted(type_counts(review_rule_cases, "owner_type").items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Review Pending Merge Candidate Types"])
    for key, value in sorted(type_counts(aggr_candidates, "main_type").items()):
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Notes",
            "- 阶段一只构建 explicit_core、example_application、review_pending、rejected_archive。",
            "- implicit_deferred 本轮不生成，等待核心显式图稳定后再做。",
            "- example_application 当前全部处于 review_pending，需 Step 7 决策后才能进入应用层最终包。",
            "- review_pending_merge_candidates 来自 Step 5B Aggr，只是聚合候选；现有 Step 7B 不会自动执行节点合并。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    main_nodes = read_jsonl(args.main_nodes)
    main_edges = read_jsonl(args.main_edges)
    rule_cases_raw = read_jsonl(args.rule_cases, required=False)
    review_nodes_raw = read_jsonl(args.review_nodes)
    review_edges_raw = read_jsonl(args.review_edges)
    review_rule_cases_raw = read_jsonl(args.review_rule_cases, required=False)
    aggr_candidates_raw = read_jsonl(args.aggr_candidates, required=False)
    rejected_raw = read_jsonl(args.rejected, required=False)

    explicit_nodes = [with_step6(row, "explicit_core", "candidate") for row in main_nodes if row.get("kg_layer") == "core"]
    explicit_edges = [with_step6(row, "explicit_core", "candidate") for row in main_edges if row.get("kg_layer") == "core"]

    app_nodes = [with_step6(row, "example_application", "candidate") for row in main_nodes if row.get("kg_layer") == "example_application"]
    app_edges = [with_step6(row, "example_application", "candidate") for row in main_edges if row.get("kg_layer") == "example_application"]
    rule_cases = [with_step6(row, "rule_case", "candidate") for row in rule_cases_raw]

    review_nodes = [with_step6(row, "review_pending", "needs_decision") for row in review_nodes_raw]
    review_edges = [with_step6(row, "review_pending", "needs_decision") for row in review_edges_raw]
    review_rule_cases = [with_step6(row, "review_pending_rule_case", "needs_decision") for row in review_rule_cases_raw]
    aggr_candidates = [with_step6(row, "review_pending_merge_candidate", "needs_decision") for row in aggr_candidates_raw]
    rejected = [with_step6(row, "rejected_archive", "archived") for row in rejected_raw]

    write_jsonl(out_dir / "explicit_core_nodes.jsonl", explicit_nodes)
    write_jsonl(out_dir / "explicit_core_edges.jsonl", explicit_edges)
    write_jsonl(out_dir / "example_application_nodes.jsonl", app_nodes)
    write_jsonl(out_dir / "example_application_edges.jsonl", app_edges)
    write_jsonl(out_dir / "rule_cases.jsonl", rule_cases)
    write_jsonl(out_dir / "review_pending_nodes.jsonl", review_nodes)
    write_jsonl(out_dir / "review_pending_edges.jsonl", review_edges)
    write_jsonl(out_dir / "review_pending_rule_cases.jsonl", review_rule_cases)
    write_jsonl(out_dir / "review_pending_merge_candidates.jsonl", aggr_candidates)
    write_jsonl(out_dir / "rejected_archive.jsonl", rejected)
    write_jsonl(out_dir / "implicit_deferred.jsonl", [])
    report_path = out_dir / "step6_layer_report.md"
    write_report(report_path, explicit_nodes, explicit_edges, app_nodes, app_edges, review_nodes, review_edges, rule_cases, review_rule_cases, aggr_candidates, rejected)

    print(f"[OK] Step 6 layers -> {out_dir}")
    print(f"[OK] report -> {report_path}")


if __name__ == "__main__":
    main()
