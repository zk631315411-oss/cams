"""
v4.4 Step 7D: apply validated review decisions.

This step produces approved candidate packages, merge plans, archives, deferred
items, and decision traces. It does not generate KnowledgeGroup records and
does not write to Neo4j.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from review_pipeline_utils import (
    edge_identity,
    ensure_source_code,
    node_identity,
    now_iso,
    read_jsonl,
    rule_case_identity,
    stable_id,
    write_jsonl,
)


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_LAYER_DIR = SCRIPT_DIR / "中间产物" / "step6_layers"
DEFAULT_REVIEW_DIR = SCRIPT_DIR / "中间产物" / "step7_review"
DEFAULT_DECISIONS = DEFAULT_REVIEW_DIR / "validated_review_decisions.jsonl"
DEFAULT_OUT_DIR = SCRIPT_DIR / "中间产物" / "step7_approved_package"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply v4.4 Step 7D validated review decisions.")
    parser.add_argument("--layer-dir", type=Path, default=DEFAULT_LAYER_DIR)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--approval-label", default="step7_validated")
    return parser.parse_args()


def add_unique(rows: list[dict[str, Any]], row: dict[str, Any], key_func) -> bool:
    existing = {key_func(item) for item in rows}
    key = key_func(row)
    if key in existing:
        return False
    rows.append(row)
    return True


def final_node(row: dict[str, Any], final_layer: str, status: str, decision: dict[str, Any] | None = None) -> dict[str, Any]:
    item = dict(row)
    item["kg_layer"] = final_layer
    item["step7_status"] = status
    item["step7_layer"] = final_layer
    item["approved_for_step8"] = True
    item["step7_generated_at"] = now_iso()
    if decision:
        item["step7_decision_id"] = decision.get("decision_id", "")
        item["step7_basis"] = decision.get("reason", "")
        item["step7_approval_label"] = decision.get("approval_label", "")
    return ensure_source_code(item)


def final_edge(row: dict[str, Any], final_layer: str, status: str, decision: dict[str, Any] | None = None) -> dict[str, Any]:
    item = dict(row)
    item["kg_layer"] = final_layer
    item["step7_status"] = status
    item["step7_layer"] = final_layer
    item["approved_for_step8"] = True
    item["step7_generated_at"] = now_iso()
    if decision:
        item["step7_decision_id"] = decision.get("decision_id", "")
        item["step7_basis"] = decision.get("reason", "")
        item["step7_approval_label"] = decision.get("approval_label", "")
    return ensure_source_code(item)


def final_rule_case(row: dict[str, Any], status: str, decision: dict[str, Any] | None = None) -> dict[str, Any]:
    item = dict(row)
    item["kg_layer"] = "rule_case"
    item["step7_status"] = status
    item["step7_layer"] = "rule_case"
    item["approved_for_step8"] = True
    item["step7_generated_at"] = now_iso()
    if not item.get("rule_case_id"):
        item["rule_case_id"] = rule_case_identity(item)
    if decision:
        item["step7_decision_id"] = decision.get("decision_id", "")
        item["step7_basis"] = decision.get("reason", "")
        item["step7_approval_label"] = decision.get("approval_label", "")
    return ensure_source_code(item)


def archive_item(source: dict[str, Any], status: str, decision: dict[str, Any] | None, kind: str) -> dict[str, Any]:
    item = dict(source)
    item["item_kind"] = kind
    item["archive_status"] = status
    item["approved_for_step8"] = False
    item["step7_generated_at"] = now_iso()
    if decision:
        item["step7_decision_id"] = decision.get("decision_id", "")
        item["step7_action"] = decision.get("action", "")
        item["step7_reason"] = decision.get("reason", "")
        item["step7_approval_label"] = decision.get("approval_label", "")
    return item


def trace(decision: dict[str, Any], result: str, note: str = "", imported_id: str = "", archived_id: str = "") -> dict[str, Any]:
    return {
        "decision_id": decision.get("decision_id", ""),
        "review_item_id": decision.get("review_item_id", ""),
        "item_kind": decision.get("item_kind", ""),
        "item_id": decision.get("item_id", ""),
        "item_name": decision.get("item_name", ""),
        "action": decision.get("action", ""),
        "target_layer": decision.get("target_layer", ""),
        "result": result,
        "note": note,
        "imported_id": imported_id,
        "archived_id": archived_id,
        "generated_at": now_iso(),
    }


def source_item(decision: dict[str, Any]) -> dict[str, Any]:
    review_item = decision.get("source_review_item") or {}
    return dict(review_item.get("source_item") or {})


def node_layer(target_layer: str) -> str:
    return "example_application" if target_layer == "example_application" else "core"


def edge_layer(target_layer: str) -> str:
    return "example_application" if target_layer == "example_application" else "core"


def build_merge_plan(decision: dict[str, Any]) -> dict[str, Any]:
    source = source_item(decision)
    main_id = str(source.get("main_node_id") or "")
    merge_id = str(source.get("merge_node_id") or "")
    return {
        "merge_plan_id": stable_id("merge-plan", [main_id, merge_id, decision.get("decision_id", "")]),
        "review_item_id": decision.get("review_item_id", ""),
        "decision_id": decision.get("decision_id", ""),
        "main_node_id": main_id,
        "main_name": source.get("main_name", ""),
        "merge_node_id": merge_id,
        "merge_name": source.get("merge_name", ""),
        "merge_policy": "no_physical_delete",
        "actions": [
            "add_alias",
            "merge_description",
            "merge_source_codes",
            "migrate_edges_after_step8_validation",
            "mark_merged",
        ],
        "reason": decision.get("reason", ""),
        "approved_for_step8": True,
        "generated_at": now_iso(),
    }


def write_report(path: Path, counts: dict[str, int]) -> None:
    lines = ["# v4.4 Step 7D Apply Review Results Report", ""]
    for key, value in sorted(counts.items()):
        lines.append(f"- {key}: {value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    final_core_nodes = [final_node(row, "core", "accepted_from_step6") for row in read_jsonl(args.layer_dir / "explicit_core_nodes.jsonl", required=False)]
    final_core_edges = [final_edge(row, "core", "accepted_from_step6") for row in read_jsonl(args.layer_dir / "explicit_core_edges.jsonl", required=False)]
    final_app_nodes = [final_node(row, "example_application", "accepted_from_step6") for row in read_jsonl(args.layer_dir / "example_application_nodes.jsonl", required=False)]
    final_app_edges = [final_edge(row, "example_application", "accepted_from_step6") for row in read_jsonl(args.layer_dir / "example_application_edges.jsonl", required=False)]
    final_rule_cases = [final_rule_case(row, "accepted_from_step6") for row in read_jsonl(args.layer_dir / "rule_cases.jsonl", required=False)]
    archived = [archive_item(row, "rejected_before_step7", None, str(row.get("item_kind") or "unknown")) for row in read_jsonl(args.layer_dir / "rejected_archive.jsonl", required=False)]
    deferred: list[dict[str, Any]] = []
    merge_plans: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []

    decisions = []
    for row in read_jsonl(args.decisions, required=False):
        item = dict(row)
        item["approval_label"] = args.approval_label
        decisions.append(item)

    for decision in decisions:
        kind = str(decision.get("item_kind") or "")
        action = str(decision.get("action") or "")
        target_layer = str(decision.get("target_layer") or "")
        source = source_item(decision)

        if kind == "node":
            if action == "accept":
                item = final_node(source, node_layer(target_layer), "accepted_by_step7", decision)
                added = add_unique(final_app_nodes if item["kg_layer"] == "example_application" else final_core_nodes, item, node_identity)
                traces.append(trace(decision, "accept", "node_imported" if added else "duplicate_node_skipped", node_identity(item)))
            elif action == "reject":
                archived.append(archive_item(source, "rejected_by_step7", decision, "node"))
                traces.append(trace(decision, "reject", archived_id=node_identity(source)))
            elif action == "rewrite":
                archived.append(archive_item(source, "rewrite_deferred_to_step8_or_manual", decision, "node"))
                traces.append(trace(decision, "rewrite", "node_rewrite_archived_for_manual_followup", archived_id=node_identity(source)))
            else:
                deferred.append(archive_item(source, "deferred_after_step7", decision, "node"))
                traces.append(trace(decision, "defer", archived_id=node_identity(source)))

        elif kind == "edge":
            if action == "accept":
                item = final_edge(source, edge_layer(target_layer), "accepted_by_step7", decision)
                added = add_unique(final_app_edges if item["kg_layer"] == "example_application" else final_core_edges, item, edge_identity)
                traces.append(trace(decision, "accept", "edge_imported" if added else "duplicate_edge_skipped", edge_identity(item)))
            elif action == "rewrite":
                rewrite = decision.get("rewritten_item") or {}
                if rewrite.get("operation") == "replace_edge":
                    item = final_edge(rewrite, edge_layer(str(rewrite.get("kg_layer") or target_layer)), "rewritten_by_step7", decision)
                    added = add_unique(final_app_edges if item["kg_layer"] == "example_application" else final_core_edges, item, edge_identity)
                    archived.append(archive_item(source, "rewritten_original_not_imported", decision, "edge"))
                    traces.append(trace(decision, "rewrite", "rewritten_edge_imported" if added else "rewritten_edge_duplicate_skipped", edge_identity(item), edge_identity(source)))
                else:
                    deferred.append(archive_item(source, "deferred_invalid_edge_rewrite", decision, "edge"))
                    traces.append(trace(decision, "defer", "invalid_edge_rewrite", archived_id=edge_identity(source)))
            elif action == "reject":
                archived.append(archive_item(source, "rejected_by_step7", decision, "edge"))
                traces.append(trace(decision, "reject", archived_id=edge_identity(source)))
            else:
                deferred.append(archive_item(source, "deferred_after_step7", decision, "edge"))
                traces.append(trace(decision, "defer", archived_id=edge_identity(source)))

        elif kind == "rule_case":
            if action == "accept":
                item = final_rule_case(source, "accepted_by_step7", decision)
                added = add_unique(final_rule_cases, item, rule_case_identity)
                traces.append(trace(decision, "accept", "rule_case_imported" if added else "duplicate_rule_case_skipped", rule_case_identity(item)))
            elif action == "rewrite":
                rewrite = decision.get("rewritten_item") or {}
                if rewrite.get("operation") == "replace_rule_case":
                    new_case = dict(source)
                    new_case.update({key: value for key, value in rewrite.items() if key != "operation"})
                    item = final_rule_case(new_case, "rewritten_by_step7", decision)
                    added = add_unique(final_rule_cases, item, rule_case_identity)
                    archived.append(archive_item(source, "rewritten_original_not_imported", decision, "rule_case"))
                    traces.append(trace(decision, "rewrite", "rewritten_rule_case_imported" if added else "rewritten_rule_case_duplicate_skipped", rule_case_identity(item), rule_case_identity(source)))
                else:
                    deferred.append(archive_item(source, "deferred_invalid_rule_case_rewrite", decision, "rule_case"))
                    traces.append(trace(decision, "defer", "invalid_rule_case_rewrite", archived_id=rule_case_identity(source)))
            elif action == "reject":
                archived.append(archive_item(source, "rejected_by_step7", decision, "rule_case"))
                traces.append(trace(decision, "reject", archived_id=rule_case_identity(source)))
            else:
                deferred.append(archive_item(source, "deferred_after_step7", decision, "rule_case"))
                traces.append(trace(decision, "defer", archived_id=rule_case_identity(source)))

        elif kind == "merge_candidate":
            if action == "accept_merge":
                plan = build_merge_plan(decision)
                add_unique(merge_plans, plan, lambda row: str(row.get("merge_plan_id") or ""))
                traces.append(trace(decision, "accept_merge", "merge_plan_created", imported_id=plan["merge_plan_id"]))
            elif action == "reject_merge":
                archived.append(archive_item(source, "merge_candidate_rejected_by_step7", decision, "merge_candidate"))
                traces.append(trace(decision, "reject_merge", archived_id=str(source.get("candidate_id") or "")))
            else:
                deferred.append(archive_item(source, "merge_candidate_deferred_after_step7", decision, "merge_candidate"))
                traces.append(trace(decision, "defer", archived_id=str(source.get("candidate_id") or "")))

    write_jsonl(out_dir / "approved_core_nodes.jsonl", final_core_nodes)
    write_jsonl(out_dir / "approved_core_edges.jsonl", final_core_edges)
    write_jsonl(out_dir / "approved_application_nodes.jsonl", final_app_nodes)
    write_jsonl(out_dir / "approved_application_edges.jsonl", final_app_edges)
    write_jsonl(out_dir / "approved_rule_cases.jsonl", final_rule_cases)
    write_jsonl(out_dir / "merge_plans.jsonl", merge_plans)
    write_jsonl(out_dir / "review_archive.jsonl", archived)
    write_jsonl(out_dir / "deferred_items.jsonl", deferred)
    write_jsonl(out_dir / "decision_trace.jsonl", traces)
    write_report(
        out_dir / "apply_review_results_report.md",
        {
            "approved_core_nodes": len(final_core_nodes),
            "approved_core_edges": len(final_core_edges),
            "approved_application_nodes": len(final_app_nodes),
            "approved_application_edges": len(final_app_edges),
            "approved_rule_cases": len(final_rule_cases),
            "merge_plans": len(merge_plans),
            "archived": len(archived),
            "deferred": len(deferred),
            "traces": len(traces),
        },
    )
    print(f"[OK] approved package -> {out_dir}")


if __name__ == "__main__":
    main()
