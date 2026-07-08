"""
v4.4 Step 7C: validate review decisions and resolve conflicts.

This step validates Step 7B decisions against engineering constraints. Clean
decisions pass through. Conflicting decisions are optionally sent to an AI
conflict resolver, then checked again. Hard constraints cannot be bypassed.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from review_pipeline_utils import (
    VALID_EDGE_TYPES,
    VALID_NODE_TYPES,
    VALID_RULE_LOGIC,
    call_llm,
    load_env_value,
    now_iso,
    read_jsonl,
    stable_id,
    write_jsonl,
)


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_LAYER_DIR = SCRIPT_DIR / "中间产物" / "step6_layers"
DEFAULT_REVIEW_DIR = SCRIPT_DIR / "中间产物" / "step7_review"
DEFAULT_DECISIONS = DEFAULT_REVIEW_DIR / "ai_review_decisions.jsonl"
DEFAULT_PROMPT = SCRIPT_DIR / "prompts" / "conflict_resolution_audit.md"
DEFAULT_MODEL = "gpt-5.5"
DEFAULT_BASE_URL = load_env_value("LLM_API_BASE") or "https://api.openai.com/v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate v4.4 Step 7B decisions and resolve conflicts.")
    parser.add_argument("--layer-dir", type=Path, default=DEFAULT_LAYER_DIR)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--batch-size", type=int, default=6)
    parser.add_argument("--max-workers", type=int, default=6)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--skip-ai-conflict-resolution", action="store_true")
    return parser.parse_args()


def load_context(layer_dir: Path) -> dict[str, Any]:
    nodes = [
        *read_jsonl(layer_dir / "explicit_core_nodes.jsonl", required=False),
        *read_jsonl(layer_dir / "example_application_nodes.jsonl", required=False),
        *read_jsonl(layer_dir / "review_pending_nodes.jsonl", required=False),
    ]
    edges = [
        *read_jsonl(layer_dir / "explicit_core_edges.jsonl", required=False),
        *read_jsonl(layer_dir / "example_application_edges.jsonl", required=False),
        *read_jsonl(layer_dir / "review_pending_edges.jsonl", required=False),
    ]
    return {
        "nodes": nodes,
        "edges": edges,
        "node_ids": {str(node.get("node_id") or "") for node in nodes if node.get("node_id")},
        "node_names": {str(node.get("name") or "") for node in nodes if node.get("name")},
        "edge_block_pairs": {
            frozenset([str(edge.get("source_node_id") or ""), str(edge.get("target_node_id") or "")])
            for edge in edges
            if edge.get("type") in {"SUPERIOR", "PART_OF"}
        },
    }


def source_item(decision: dict[str, Any]) -> dict[str, Any]:
    review_item = decision.get("source_review_item") or {}
    return dict(review_item.get("source_item") or {})


def node_exists_by_id_or_name(node_id: str, name: str, context: dict[str, Any]) -> bool:
    return bool((node_id and node_id in context["node_ids"]) or (name and name in context["node_names"]))


def validate_rewrite(rewrite: Any, kind: str, context: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(rewrite, dict):
        return ["missing_rewritten_item"]
    operation = str(rewrite.get("operation") or "")
    if kind == "edge":
        if operation != "replace_edge":
            errors.append("edge_rewrite_requires_replace_edge")
        if str(rewrite.get("type") or "") not in VALID_EDGE_TYPES:
            errors.append("invalid_rewrite_edge_type")
        if not node_exists_by_id_or_name(str(rewrite.get("source_node_id") or ""), str(rewrite.get("source_name") or ""), context):
            errors.append("rewrite_source_endpoint_not_found")
        if not node_exists_by_id_or_name(str(rewrite.get("target_node_id") or ""), str(rewrite.get("target_name") or ""), context):
            errors.append("rewrite_target_endpoint_not_found")
    elif kind == "rule_case":
        if operation != "replace_rule_case":
            errors.append("rule_case_rewrite_requires_replace_rule_case")
        if rewrite.get("condition_logic") and str(rewrite.get("condition_logic")) not in VALID_RULE_LOGIC:
            errors.append("invalid_rewrite_condition_logic")
    elif kind == "node":
        if operation not in {"replace_node", "merge_node"}:
            errors.append("node_rewrite_requires_replace_or_merge_node")
        if operation == "replace_node" and str(rewrite.get("type") or "") not in VALID_NODE_TYPES:
            errors.append("invalid_rewrite_node_type")
    return errors


def validate_decision(decision: dict[str, Any], context: dict[str, Any]) -> tuple[str, list[str]]:
    errors: list[str] = []
    kind = str(decision.get("item_kind") or "")
    action = str(decision.get("action") or decision.get("final_action") or "")
    source = source_item(decision)

    if kind == "edge" and action == "accept":
        if not node_exists_by_id_or_name(str(source.get("source_node_id") or ""), str(source.get("source_name") or ""), context):
            errors.append("edge_source_endpoint_not_found")
        if not node_exists_by_id_or_name(str(source.get("target_node_id") or ""), str(source.get("target_name") or ""), context):
            errors.append("edge_target_endpoint_not_found")
        if str(source.get("type") or "") not in VALID_EDGE_TYPES:
            errors.append("invalid_edge_type")
    if kind == "rule_case" and action == "accept":
        if not node_exists_by_id_or_name(str(source.get("owner_node_id") or ""), str(source.get("owner_name") or ""), context):
            errors.append("rule_case_owner_not_found")
        if not source.get("conditions"):
            errors.append("rule_case_missing_conditions")
        if not source.get("outcomes"):
            errors.append("rule_case_missing_outcomes")
    if kind == "merge_candidate" and action == "accept_merge":
        if str(source.get("main_type") or "") != str(source.get("merge_type_name") or ""):
            errors.append("merge_node_type_mismatch")
        pair = frozenset([str(source.get("main_node_id") or ""), str(source.get("merge_node_id") or "")])
        if pair in context["edge_block_pairs"]:
            errors.append("merge_blocked_by_superior_or_part_of")
    if action == "rewrite":
        errors.extend(validate_rewrite(decision.get("rewritten_item") or decision.get("final_rewritten_item"), kind, context))
    return ("conflict" if errors else "validated"), errors


def force_safe_decision(decision: dict[str, Any], errors: list[str], reason: str = "") -> dict[str, Any]:
    row = dict(decision)
    kind = str(row.get("item_kind") or "")
    if kind == "merge_candidate":
        row["action"] = "reject_merge" if any("blocked" in error or "mismatch" in error for error in errors) else "defer"
    else:
        row["action"] = "defer"
    row["target_layer"] = "review_pending" if row["action"] == "defer" else "rejected_archive"
    row["validation_status"] = "forced_safe"
    row["validation_errors"] = errors
    row["conflict_resolution"] = reason or "存在硬约束冲突，不能按原建议放行，已按保守策略处理。"
    row["validated_at"] = now_iso()
    return row


def normalize_conflict_decisions(raw: dict[str, Any], conflicts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    conflict_by_id = {str(item.get("review_item_id") or ""): item for item in conflicts}
    result: dict[str, dict[str, Any]] = {}
    for item in raw.get("decisions") if isinstance(raw.get("decisions"), list) else []:
        if not isinstance(item, dict):
            continue
        review_item_id = str(item.get("review_item_id") or "")
        original = conflict_by_id.get(review_item_id)
        if not original:
            continue
        row = dict(original)
        row["action"] = str(item.get("final_action") or original.get("action") or "defer")
        row["target_layer"] = str(item.get("final_target_layer") or original.get("target_layer") or "review_pending")
        row["rewritten_item"] = item.get("final_rewritten_item") if isinstance(item.get("final_rewritten_item"), dict) else original.get("rewritten_item")
        row["conflict_resolution"] = str(item.get("conflict_resolution") or "")
        row["reason"] = str(item.get("reason") or original.get("reason") or "")
        row["confidence"] = item.get("confidence", original.get("confidence", 0.0))
        row["resolved_by"] = "ai_conflict_review"
        result[review_item_id] = row
    return result


def batched(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    size = max(1, size)
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def conflict_payload(conflicts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "conflict_items": [
            {
                "review_item_id": row.get("review_item_id", ""),
                "item_kind": row.get("item_kind", ""),
                "step7b_decision": {
                    "action": row.get("action", ""),
                    "target_layer": row.get("target_layer", ""),
                    "reason": row.get("reason", ""),
                    "confidence": row.get("confidence", 0.0),
                    "rewritten_item": row.get("rewritten_item"),
                },
                "rule_check_result": {
                    "status": row.get("validation_status", ""),
                    "conflict_reasons": row.get("validation_errors", []),
                },
                "source_item": source_item(row),
            }
            for row in conflicts
        ]
    }


def process_conflict_batch(batch: list[dict[str, Any]], prompt: str, args: argparse.Namespace, api_key: str) -> dict[str, dict[str, Any]]:
    if args.mock or args.skip_ai_conflict_resolution:
        return {}
    raw = call_llm(api_key, args.base_url, args.model, prompt, conflict_payload(batch), args.temperature, args.timeout)
    return normalize_conflict_decisions(raw, batch)


def write_report(path: Path, validated: list[dict[str, Any]], conflicts: list[dict[str, Any]], forced: list[dict[str, Any]]) -> None:
    lines = [
        "# v4.4 Step 7C Validation Report",
        "",
        f"- validated_decisions: {len(validated)}",
        f"- conflict_items: {len(conflicts)}",
        f"- forced_safe_decisions: {len(forced)}",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    context = load_context(args.layer_dir)
    decisions = read_jsonl(args.decisions, required=False)

    clean: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for decision in decisions:
        status, errors = validate_decision(decision, context)
        row = dict(decision)
        row["validation_status"] = status
        row["validation_errors"] = errors
        row["validated_at"] = now_iso()
        if status == "validated":
            clean.append(row)
        else:
            conflicts.append(row)

    resolved_by_id: dict[str, dict[str, Any]] = {}
    if conflicts and not args.skip_ai_conflict_resolution and not args.mock:
        api_key = load_env_value(args.api_key_env)
        if not api_key:
            raise RuntimeError(f"{args.api_key_env} not found. Use --mock or --skip-ai-conflict-resolution for local validation.")
        prompt = args.prompt.read_text(encoding="utf-8")
        with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
            future_to_batch = {executor.submit(process_conflict_batch, batch, prompt, args, api_key): batch for batch in batched(conflicts, args.batch_size)}
            for future in as_completed(future_to_batch):
                try:
                    resolved_by_id.update(future.result())
                except Exception as exc:
                    message = str(exc)[:1000]
                    for conflict in future_to_batch[future]:
                        row = dict(conflict)
                        errors = list(row.get("validation_errors") or ["conflict_resolution_failed"])
                        if "conflict_resolution_failed" not in errors:
                            errors.append("conflict_resolution_failed")
                        row["conflict_resolution"] = f"AI冲突复核调用失败，按硬规则保守处理：{message}"
                        row["validation_errors"] = errors
                        resolved_by_id[str(row.get("review_item_id") or "")] = row

    resolved: list[dict[str, Any]] = []
    forced: list[dict[str, Any]] = []
    for conflict in conflicts:
        candidate = resolved_by_id.get(str(conflict.get("review_item_id") or ""), conflict)
        status, errors = validate_decision(candidate, context)
        if status == "validated":
            candidate["validation_status"] = "resolved"
            candidate["validation_errors"] = []
            candidate["validated_at"] = now_iso()
            resolved.append(candidate)
        else:
            safe = force_safe_decision(candidate, errors, str(candidate.get("conflict_resolution") or "冲突复核后仍违反硬约束。"))
            forced.append(safe)

    final_decisions = [*clean, *resolved, *forced]
    write_jsonl(out_dir / "validated_review_decisions.jsonl", final_decisions)
    write_jsonl(out_dir / "conflict_review_items.jsonl", conflicts)
    write_jsonl(out_dir / "conflict_resolved_decisions.jsonl", resolved)
    write_jsonl(out_dir / "decision_validation_errors.jsonl", forced)
    write_report(out_dir / "validation_report.md", final_decisions, conflicts, forced)
    print(f"[OK] validated decisions -> {out_dir / 'validated_review_decisions.jsonl'}")
    print(f"[INFO] clean={len(clean)} conflicts={len(conflicts)} resolved={len(resolved)} forced={len(forced)}")


if __name__ == "__main__":
    main()
