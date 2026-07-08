"""
v4.4 Step 7A: build unified review items.

This step converts Step 6 review layers into one schema for AI/human review.
It does not call an LLM and does not decide whether items enter the graph.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from review_pipeline_utils import compact_text, now_iso, read_jsonl, stable_id, write_jsonl


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_LAYER_DIR = SCRIPT_DIR / "中间产物" / "step6_layers"
DEFAULT_OUT_DIR = SCRIPT_DIR / "中间产物" / "step7_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build v4.4 Step 7A unified review items.")
    parser.add_argument("--layer-dir", type=Path, default=DEFAULT_LAYER_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def item_context(item: dict[str, Any], kind: str) -> dict[str, Any]:
    if kind == "node":
        return {
            "name": item.get("name", ""),
            "type": item.get("type", ""),
            "definition": compact_text(item.get("definition", ""), 1200),
            "description": compact_text(item.get("description", ""), 1200),
            "evidence_span": compact_text(item.get("evidence_span", ""), 1600),
            "source_code": item.get("source_code", ""),
            "validation_warnings": item.get("validation_warnings", []),
            "review_reason": item.get("review_reason", ""),
        }
    if kind == "edge":
        return {
            "source_name": item.get("source_name", ""),
            "source_type": item.get("source_type", ""),
            "target_name": item.get("target_name", ""),
            "target_type": item.get("target_type", ""),
            "type": item.get("type", ""),
            "description": compact_text(item.get("description", ""), 1000),
            "evidence_span": compact_text(item.get("evidence_span", ""), 1600),
            "validation_warnings": item.get("validation_warnings", []),
            "review_reason": item.get("review_reason", ""),
        }
    if kind == "rule_case":
        return {
            "owner_name": item.get("owner_name", ""),
            "owner_type": item.get("owner_type", ""),
            "case_name": item.get("case_name", ""),
            "applies_to": item.get("applies_to", ""),
            "conditions": item.get("conditions", []),
            "condition_logic": item.get("condition_logic", ""),
            "outcomes": item.get("outcomes", []),
            "evidence_span": compact_text(item.get("evidence_span", ""), 1800),
            "validation_warnings": item.get("validation_warnings", []),
            "review_reason": item.get("review_reason", ""),
        }
    return {
        "main_name": item.get("main_name", ""),
        "main_type": item.get("main_type", ""),
        "merge_name": item.get("merge_name", ""),
        "merge_type_name": item.get("merge_type_name", ""),
        "score": item.get("score", 0),
        "name_similarity": item.get("name_similarity", 0),
        "context_similarity": item.get("context_similarity", 0),
        "role_similarity": item.get("role_similarity", 0),
        "review_reason": item.get("review_reason", ""),
        "source_node": item.get("source_node", {}),
        "target_node": item.get("target_node", {}),
    }


def make_item(kind: str, item: dict[str, Any]) -> dict[str, Any]:
    raw_id = (
        item.get("node_id")
        or item.get("edge_id")
        or item.get("rule_case_id")
        or item.get("candidate_id")
        or item.get("item_id")
        or ""
    )
    if kind == "merge_candidate":
        allowed = ["accept_merge", "reject_merge", "defer"]
        target_layer = "review_pending"
        name = f"{item.get('main_name', '')} <- {item.get('merge_name', '')}"
        item_type = "MergeCandidate"
    elif kind == "rule_case":
        allowed = ["accept", "reject", "rewrite", "defer"]
        target_layer = "rule_case"
        name = str(item.get("case_name") or "")
        item_type = "RuleCase"
    else:
        allowed = ["accept", "reject", "rewrite", "defer"]
        target_layer = "example_application" if item.get("kg_layer") == "example_application" else "core"
        name = str(item.get("name") or f"{item.get('source_name', '')} -> {item.get('target_name', '')}")
        item_type = str(item.get("type") or "")

    review_item_id = stable_id("review-item", [kind, str(raw_id), name, item_type])
    risk_flags = []
    warnings = item.get("validation_warnings") or []
    if warnings:
        risk_flags.extend(str(warning) for warning in warnings)
    if kind == "edge" and item.get("type") == "DERIVES":
        risk_flags.append("derives_direction_sensitive")
    if kind == "merge_candidate":
        risk_flags.append("semantic_merge_requires_explicit_approval")

    return {
        "review_item_id": review_item_id,
        "item_kind": kind,
        "item_id": str(raw_id),
        "item_name": name,
        "item_type": item_type,
        "kg_layer": item.get("kg_layer", item.get("step6_layer", "")),
        "source_item": item,
        "context": item_context(item, kind),
        "allowed_actions": allowed,
        "default_action": "defer",
        "default_target_layer": target_layer,
        "risk_flags": risk_flags,
        "generated_at": now_iso(),
    }


def write_report(path: Path, review_items: list[dict[str, Any]]) -> None:
    counts = Counter(str(item.get("item_kind") or "") for item in review_items)
    lines = [
        "# v4.4 Step 7A Review Items Report",
        "",
        f"- review_items: {len(review_items)}",
        "",
        "## Item Kinds",
    ]
    for key, value in sorted(counts.items()):
        lines.append(f"- {key}: {value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    review_items: list[dict[str, Any]] = []
    review_items.extend(make_item("node", row) for row in read_jsonl(args.layer_dir / "review_pending_nodes.jsonl", required=False))
    review_items.extend(make_item("edge", row) for row in read_jsonl(args.layer_dir / "review_pending_edges.jsonl", required=False))
    review_items.extend(make_item("rule_case", row) for row in read_jsonl(args.layer_dir / "review_pending_rule_cases.jsonl", required=False))
    review_items.extend(make_item("merge_candidate", row) for row in read_jsonl(args.layer_dir / "review_pending_merge_candidates.jsonl", required=False))

    write_jsonl(out_dir / "review_items.jsonl", review_items)
    write_report(out_dir / "review_items_report.md", review_items)
    print(f"[OK] review items -> {out_dir / 'review_items.jsonl'}")
    print(f"[INFO] review_items={len(review_items)}")


if __name__ == "__main__":
    main()
