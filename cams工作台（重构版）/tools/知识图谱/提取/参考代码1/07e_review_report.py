"""
v4.4 Step 7E: write review closure report.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from review_pipeline_utils import read_jsonl


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_REVIEW_DIR = SCRIPT_DIR / "中间产物" / "step7_review"
DEFAULT_APPROVED_DIR = SCRIPT_DIR / "中间产物" / "step7_approved_package"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write v4.4 Step 7E review closure report.")
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--approved-dir", type=Path, default=DEFAULT_APPROVED_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_APPROVED_DIR / "review_closure_report.md")
    return parser.parse_args()


def count(path: Path) -> int:
    return len(read_jsonl(path, required=False))


def action_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(f"{row.get('item_kind', '')}:{row.get('action', '')}" for row in rows)


def main() -> None:
    args = parse_args()
    decisions = read_jsonl(args.review_dir / "validated_review_decisions.jsonl", required=False)
    conflicts = read_jsonl(args.review_dir / "conflict_review_items.jsonl", required=False)
    forced = read_jsonl(args.review_dir / "decision_validation_errors.jsonl", required=False)
    traces = read_jsonl(args.approved_dir / "decision_trace.jsonl", required=False)
    lines = [
        "# v4.4 Step 7E 审核闭环报告",
        "",
        "## 输入与决策",
        f"- review_items: {count(args.review_dir / 'review_items.jsonl')}",
        f"- ai_review_decisions: {count(args.review_dir / 'ai_review_decisions.jsonl')}",
        f"- validated_review_decisions: {len(decisions)}",
        f"- conflict_review_items: {len(conflicts)}",
        f"- forced_safe_decisions: {len(forced)}",
        "",
        "## 最终审核产物",
        f"- approved_core_nodes: {count(args.approved_dir / 'approved_core_nodes.jsonl')}",
        f"- approved_core_edges: {count(args.approved_dir / 'approved_core_edges.jsonl')}",
        f"- approved_application_nodes: {count(args.approved_dir / 'approved_application_nodes.jsonl')}",
        f"- approved_application_edges: {count(args.approved_dir / 'approved_application_edges.jsonl')}",
        f"- approved_rule_cases: {count(args.approved_dir / 'approved_rule_cases.jsonl')}",
        f"- merge_plans: {count(args.approved_dir / 'merge_plans.jsonl')}",
        f"- review_archive: {count(args.approved_dir / 'review_archive.jsonl')}",
        f"- deferred_items: {count(args.approved_dir / 'deferred_items.jsonl')}",
        f"- decision_trace: {len(traces)}",
        "",
        "## 决策分布",
    ]
    for key, value in sorted(action_counts(decisions).items()):
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## 说明",
            "- Step 7 只完成审核闭环，不生成 KnowledgeGroup，不导入 Neo4j。",
            "- `merge_plans.jsonl` 只是合并计划，真正执行应在 Step 8A 最终图谱组装阶段完成。",
            "- 所有 reject/defer/rewrite 原始项都会保留在 archive、deferred 或 decision_trace 中。",
        ]
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] review closure report -> {args.output}")


if __name__ == "__main__":
    main()
