"""
Run cumulative Higher Algebra v4.4 Step 5-8A from one or more Step-4C run dirs.

Each source run dir must contain a combined/ folder produced by
run_gaodai_full_to_step7.py. This script concatenates those pre-Step-5
artifacts and then runs global normalization, layering, review, and final graph
assembly. It does not import into Neo4j.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from run_gaodai_full_to_step7 import (
    SCRIPT_DIR,
    concat_jsonl,
    count_jsonl,
    py_cmd,
    run_cmd,
    run_env,
    write_run_summary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run cumulative gaodai v4.4 Step 5-8A.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--source-run-dirs", type=Path, nargs="+", required=True)
    parser.add_argument("--audit-workers", type=int, default=12)
    parser.add_argument("--audit-timeout", type=float, default=240)
    parser.add_argument("--review-batch-size", type=int, default=8)
    parser.add_argument("--conflict-batch-size", type=int, default=8)
    parser.add_argument("--audit-model", default=os.environ.get("LLM_AUDIT_MODEL", "gpt-5.5"))
    parser.add_argument("--conflict-model", default=os.environ.get("LLM_CONFLICT_MODEL", "gpt-5.5"))
    parser.add_argument("--base-url", default="")
    parser.add_argument("--audit-reasoning", default="high")
    parser.add_argument("--conflict-reasoning", default="max")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--no-audit", action="store_true", help="Use Step 7A draft decisions directly.")
    return parser.parse_args()


def require_combined_dirs(source_run_dirs: list[Path]) -> list[Path]:
    combined_dirs: list[Path] = []
    missing: list[str] = []
    for run_dir in source_run_dirs:
        combined = run_dir / "combined"
        if not combined.exists():
            missing.append(str(combined))
        else:
            combined_dirs.append(combined)
    if missing:
        raise FileNotFoundError("Missing combined dirs: " + "; ".join(missing))
    return combined_dirs


def combine_step4_outputs(combined_dir: Path, source_combined_dirs: list[Path]) -> dict[str, int]:
    combined_dir.mkdir(parents=True, exist_ok=True)
    files = [
        "leaf_sections.jsonl",
        "tree_nodes.jsonl",
        "tree_edges.jsonl",
        "nodes_pre_audit.jsonl",
        "node_audit_decisions.jsonl",
        "nodes.jsonl",
        "nodes_for_step4.jsonl",
        "node_review_queue.jsonl",
        "example_app_nodes.jsonl",
        "example_app_edges.jsonl",
        "edges_pre_audit.jsonl",
        "edge_pre_audit_review_queue.jsonl",
        "rule_cases_pre_audit.jsonl",
        "rule_case_pre_audit_review_queue.jsonl",
        "edge_rule_case_audit_decisions.jsonl",
        "edges.jsonl",
        "edge_review_queue.jsonl",
        "rule_cases.jsonl",
        "rule_case_review_queue.jsonl",
    ]
    counts: dict[str, int] = {}
    for filename in files:
        output = combined_dir / filename
        inputs = [source_dir / filename for source_dir in source_combined_dirs]
        counts[filename] = concat_jsonl(output, inputs)
    return counts


def main() -> None:
    args = parse_args()
    run_dir: Path = args.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = run_dir / "logs"
    combined_dir = run_dir / "combined"
    step5_dir = run_dir / "step5_normalized"
    step6_dir = run_dir / "step6_layers"
    step7_review_dir = run_dir / "step7_review"
    step7_approved_dir = run_dir / "step7_approved_package"
    step8_dir = run_dir / "step8_final_graph"
    logs_dir.mkdir(parents=True, exist_ok=True)

    source_combined_dirs = require_combined_dirs(args.source_run_dirs)
    combined_counts = combine_step4_outputs(combined_dir, source_combined_dirs)

    step5_dir.mkdir(parents=True, exist_ok=True)
    run_cmd(
        py_cmd(
            "05_global_normalize_and_review.py",
            "--nodes", combined_dir / "nodes.jsonl",
            "--edges", combined_dir / "edges.jsonl",
            "--node-review", combined_dir / "node_review_queue.jsonl",
            "--edge-review", combined_dir / "edge_review_queue.jsonl",
            "--app-nodes", combined_dir / "example_app_nodes.jsonl",
            "--app-edges", combined_dir / "example_app_edges.jsonl",
            "--rule-cases-in", combined_dir / "rule_cases.jsonl",
            "--review-rule-cases-in", combined_dir / "rule_case_review_queue.jsonl",
            "--main-nodes-out", step5_dir / "main_nodes.jsonl",
            "--main-edges-out", step5_dir / "main_edges.jsonl",
            "--rule-cases-out", step5_dir / "rule_cases.jsonl",
            "--review-nodes-out", step5_dir / "review_nodes.jsonl",
            "--review-edges-out", step5_dir / "review_edges.jsonl",
            "--review-rule-cases-out", step5_dir / "review_rule_cases.jsonl",
            "--rejected-out", step5_dir / "rejected_archive.jsonl",
            "--report", step5_dir / "global_normalize_report.md",
            "--review-md", step5_dir / "global_review_queue.md",
            "--include-reviewed-app",
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step5_global_normalize.log",
    )

    run_cmd(
        py_cmd(
            "05b_generate_aggr_candidates.py",
            "--main-nodes", step5_dir / "main_nodes.jsonl",
            "--review-nodes", step5_dir / "review_nodes.jsonl",
            "--main-edges", step5_dir / "main_edges.jsonl",
            "--review-edges", step5_dir / "review_edges.jsonl",
            "--output", step5_dir / "aggr_candidates.jsonl",
            "--report", step5_dir / "aggr_report.md",
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step5b_aggr.log",
    )

    run_cmd(
        py_cmd(
            "06_build_layered_candidates.py",
            "--main-nodes", step5_dir / "main_nodes.jsonl",
            "--main-edges", step5_dir / "main_edges.jsonl",
            "--rule-cases", step5_dir / "rule_cases.jsonl",
            "--review-nodes", step5_dir / "review_nodes.jsonl",
            "--review-edges", step5_dir / "review_edges.jsonl",
            "--review-rule-cases", step5_dir / "review_rule_cases.jsonl",
            "--rejected", step5_dir / "rejected_archive.jsonl",
            "--aggr-candidates", step5_dir / "aggr_candidates.jsonl",
            "--out-dir", step6_dir,
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step6_build_layers.log",
    )

    run_cmd(
        py_cmd(
            "07a_build_review_items.py",
            "--layer-dir", step6_dir,
            "--out-dir", step7_review_dir,
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step7a_build_review_items.log",
    )

    review_cmd = py_cmd(
        "07b_ai_review_items.py",
        "--review-items", step7_review_dir / "review_items.jsonl",
        "--out-dir", step7_review_dir,
        "--batch-size", str(args.review_batch_size),
        "--max-workers", str(args.audit_workers),
        "--timeout", str(args.audit_timeout),
        "--api-key-env", "LLM_API_KEY",
        "--resume",
        "--max-budget-usd", "200",
    )
    if args.audit_model:
        review_cmd += ["--model", args.audit_model]
    if args.base_url:
        review_cmd += ["--base-url", args.base_url]
    if args.mock or args.no_audit:
        review_cmd.append("--mock")
    run_cmd(review_cmd, cwd=SCRIPT_DIR, log_path=logs_dir / "step7b_ai_review.log", env=run_env(args.audit_reasoning))

    validate_cmd = py_cmd(
        "07c_validate_and_resolve_conflicts.py",
        "--layer-dir", step6_dir,
        "--decisions", step7_review_dir / "ai_review_decisions.jsonl",
        "--out-dir", step7_review_dir,
        "--batch-size", str(args.conflict_batch_size),
        "--max-workers", str(args.audit_workers),
        "--timeout", str(args.audit_timeout),
        "--api-key-env", "LLM_API_KEY",
    )
    if args.conflict_model:
        validate_cmd += ["--model", args.conflict_model]
    if args.base_url:
        validate_cmd += ["--base-url", args.base_url]
    if args.mock or args.no_audit:
        validate_cmd.append("--mock")
        validate_cmd.append("--skip-ai-conflict-resolution")
    run_cmd(validate_cmd, cwd=SCRIPT_DIR, log_path=logs_dir / "step7c_validate_conflicts.log", env=run_env(args.conflict_reasoning))

    run_cmd(
        py_cmd(
            "07d_apply_review_results.py",
            "--layer-dir", step6_dir,
            "--decisions", step7_review_dir / "validated_review_decisions.jsonl",
            "--out-dir", step7_approved_dir,
            "--approval-label", "cumulative-run-before-step8-assembly",
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step7d_apply_review_results.log",
    )

    run_cmd(
        py_cmd(
            "07e_review_report.py",
            "--review-dir", step7_review_dir,
            "--approved-dir", step7_approved_dir,
            "--output", step7_approved_dir / "review_closure_report.md",
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step7e_review_report.log",
    )

    step8a_returncode = run_cmd(
        py_cmd(
            "08a_assemble_final_graph.py",
            "--approved-dir", step7_approved_dir,
            "--out-dir", step8_dir,
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step8a_assemble_final_graph.log",
        allowed_returncodes={0, 2},
    )

    summary = {
        "run_dir": str(run_dir),
        "source_run_dirs": [str(path) for path in args.source_run_dirs],
        "source_count": len(args.source_run_dirs),
        "combined_at": datetime.now().isoformat(timespec="seconds"),
        "stopped_before": "08_import_neo4j.py",
        "step8a_returncode": step8a_returncode,
        "combined_counts": combined_counts,
        "combined_nodes_pre_audit": count_jsonl(combined_dir / "nodes_pre_audit.jsonl"),
        "combined_node_audit_decisions": count_jsonl(combined_dir / "node_audit_decisions.jsonl"),
        "combined_nodes": count_jsonl(combined_dir / "nodes.jsonl"),
        "combined_nodes_for_step4": count_jsonl(combined_dir / "nodes_for_step4.jsonl"),
        "combined_node_review_queue": count_jsonl(combined_dir / "node_review_queue.jsonl"),
        "combined_edges_pre_audit": count_jsonl(combined_dir / "edges_pre_audit.jsonl"),
        "combined_rule_cases_pre_audit": count_jsonl(combined_dir / "rule_cases_pre_audit.jsonl"),
        "combined_edge_rule_case_audit_decisions": count_jsonl(combined_dir / "edge_rule_case_audit_decisions.jsonl"),
        "combined_edges": count_jsonl(combined_dir / "edges.jsonl"),
        "combined_edge_review_queue": count_jsonl(combined_dir / "edge_review_queue.jsonl"),
        "combined_rule_cases": count_jsonl(combined_dir / "rule_cases.jsonl"),
        "combined_rule_case_review_queue": count_jsonl(combined_dir / "rule_case_review_queue.jsonl"),
        "example_app_nodes": count_jsonl(combined_dir / "example_app_nodes.jsonl"),
        "example_app_edges": count_jsonl(combined_dir / "example_app_edges.jsonl"),
        "step5_main_nodes": count_jsonl(step5_dir / "main_nodes.jsonl"),
        "step5_main_edges": count_jsonl(step5_dir / "main_edges.jsonl"),
        "step5_rule_cases": count_jsonl(step5_dir / "rule_cases.jsonl"),
        "step5_review_nodes": count_jsonl(step5_dir / "review_nodes.jsonl"),
        "step5_review_edges": count_jsonl(step5_dir / "review_edges.jsonl"),
        "step5_review_rule_cases": count_jsonl(step5_dir / "review_rule_cases.jsonl"),
        "step7_review_items": count_jsonl(step7_review_dir / "review_items.jsonl"),
        "step7_ai_review_decisions": count_jsonl(step7_review_dir / "ai_review_decisions.jsonl"),
        "step7_validated_decisions": count_jsonl(step7_review_dir / "validated_review_decisions.jsonl"),
        "approved_core_nodes": count_jsonl(step7_approved_dir / "approved_core_nodes.jsonl"),
        "approved_core_edges": count_jsonl(step7_approved_dir / "approved_core_edges.jsonl"),
        "approved_rule_cases": count_jsonl(step7_approved_dir / "approved_rule_cases.jsonl"),
        "merge_plans": count_jsonl(step7_approved_dir / "merge_plans.jsonl"),
        "deferred_items": count_jsonl(step7_approved_dir / "deferred_items.jsonl"),
        "review_archive": count_jsonl(step7_approved_dir / "review_archive.jsonl"),
        "final_core_nodes": count_jsonl(step8_dir / "final_core_nodes.jsonl"),
        "final_core_edges": count_jsonl(step8_dir / "final_core_edges.jsonl"),
        "final_application_nodes": count_jsonl(step8_dir / "final_application_nodes.jsonl"),
        "final_application_edges": count_jsonl(step8_dir / "final_application_edges.jsonl"),
        "final_rule_cases": count_jsonl(step8_dir / "final_rule_cases.jsonl"),
        "final_knowledge_groups": count_jsonl(step8_dir / "final_knowledge_groups.jsonl"),
        "final_knowledge_group_edges": count_jsonl(step8_dir / "final_knowledge_group_edges.jsonl"),
        "merged_nodes": count_jsonl(step8_dir / "merged_nodes.jsonl"),
        "step8_hard_warnings": count_jsonl(step8_dir / "step8_assembly_hard_warnings.jsonl"),
        "step8_soft_warnings": count_jsonl(step8_dir / "step8_assembly_soft_warnings.jsonl"),
    }
    write_run_summary(run_dir, summary)
    print("[DONE] assembled cumulative Step 8A final graph package and stopped before Neo4j import")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
