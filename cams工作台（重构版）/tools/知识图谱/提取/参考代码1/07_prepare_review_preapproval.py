"""
v4.3 Step 7A: prepare review pre-approval records.

This script is generic and advisory. It reads Step 6 review_pending items and
writes a structured decision draft. By default every review item is deferred,
so the pipeline cannot silently import uncertain nodes, edges, or rule cases.
The user or Codex can edit the decisions before running Step 7B.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_LAYER_DIR = SCRIPT_DIR / "中间产物" / "step6_layers"
DEFAULT_OUT_DIR = SCRIPT_DIR / "中间产物" / "step7_preapproval"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare v4.3 Step 7 review decision draft.")
    parser.add_argument("--layer-dir", type=Path, default=DEFAULT_LAYER_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--suggest-clean-rule-cases",
        action="store_true",
        help="Recommend accepting complete rule cases. Default keeps them deferred.",
    )
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


def stable_id(prefix: str, parts: list[str]) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:14]
    return f"{prefix}:{digest}"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def excerpt(text: Any, limit: int = 100) -> str:
    value = " ".join(str(text or "").split())
    return value if len(value) <= limit else value[: limit - 1] + "…"


def warning_text(item: dict[str, Any]) -> str:
    warnings = item.get("validation_warnings") or []
    if isinstance(warnings, list):
        return "；".join(str(row) for row in warnings if row)
    return str(warnings or "")


def base_decision(
    item_kind: str,
    item_id: str,
    item_name: str,
    item_type: str,
    kg_layer: str,
    source_item: dict[str, Any],
    basis: str,
    target_layer: str,
    recommendation: str = "defer",
    action_detail: str = "needs_user_review",
    rewritten_item: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decision = {
        "decision_id": stable_id("step7-pre", [item_kind, item_id, item_name, item_type, kg_layer]),
        "item_kind": item_kind,
        "item_id": item_id,
        "item_name": item_name,
        "item_type": item_type,
        "kg_layer": kg_layer,
        "recommendation": recommendation,
        "action_detail": action_detail,
        "target_layer": target_layer,
        "basis": basis,
        "evidence_excerpt": excerpt(source_item.get("evidence_span", "")),
        "rewritten_item": rewritten_item,
        "source_item": source_item,
        "generated_at": now_iso(),
    }
    if extra:
        decision.update(extra)
    return decision


def node_decision(node: dict[str, Any]) -> dict[str, Any]:
    layer = str(node.get("kg_layer") or node.get("step6_layer") or "")
    name = str(node.get("name") or "")
    reason = str(node.get("review_reason") or "").strip()
    warnings = warning_text(node)
    basis_parts = []
    if reason:
        basis_parts.append(reason)
    if warnings:
        basis_parts.append(f"校验提示：{warnings}")
    if not basis_parts:
        basis_parts.append("该节点处于 Step 6 待审层，需确认是否作为正式知识点入图。")

    target_layer = "example_application" if layer == "example_application" else "core"
    return base_decision(
        item_kind="node",
        item_id=str(node.get("node_id") or ""),
        item_name=name,
        item_type=str(node.get("type") or ""),
        kg_layer=layer,
        source_item=node,
        basis="；".join(basis_parts),
        target_layer=target_layer,
    )


def edge_decision(edge: dict[str, Any]) -> dict[str, Any]:
    layer = str(edge.get("kg_layer") or edge.get("step6_layer") or "")
    source_name = str(edge.get("source_name") or "")
    target_name = str(edge.get("target_name") or "")
    reason = str(edge.get("review_reason") or "").strip()
    warnings = warning_text(edge)
    basis_parts = []
    if edge.get("semantic_inferred"):
        basis_type = str(edge.get("basis_type") or "unknown")
        basis_parts.append(
            f"语义增强候选：basis_type={basis_type}，表示该边不是 LLM 自由补漏，而是根据小节主题、节点类型和原文证据生成的保守候选。"
        )
    if reason:
        basis_parts.append(reason)
    if warnings:
        basis_parts.append(f"校验提示：{warnings}")
    if not basis_parts:
        basis_parts.append("该关系处于 Step 6 待审层，需确认关系类型、方向和证据是否成立。")

    target_layer = "example_application" if layer == "example_application" else "core"
    return base_decision(
        item_kind="edge",
        item_id=str(edge.get("edge_id") or ""),
        item_name=f"{source_name} -> {target_name}",
        item_type=str(edge.get("type") or ""),
        kg_layer=layer,
        source_item=edge,
        basis="；".join(basis_parts),
        target_layer=target_layer,
        extra={
            "source_name": source_name,
            "target_name": target_name,
        },
    )


def rule_case_complete(case: dict[str, Any]) -> bool:
    return bool(case.get("owner_node_id")) and bool(case.get("conditions")) and bool(case.get("outcomes")) and bool(case.get("evidence_span"))


def rule_case_decision(case: dict[str, Any], suggest_clean: bool) -> dict[str, Any]:
    case_name = str(case.get("case_name") or "")
    owner_name = str(case.get("owner_name") or "")
    recommendation = "defer"
    action_detail = "needs_user_review"
    target_layer = "rule_case"
    basis = "条件判断规则案例默认需确认条件、结论、适用对象和证据是否准确。"
    if suggest_clean and rule_case_complete(case) and not warning_text(case):
        recommendation = "accept"
        action_detail = "keep_as_rule_case"
        basis = "规则案例字段完整，建议接受；仍建议抽样核对条件与结论是否对应原文。"

    return base_decision(
        item_kind="rule_case",
        item_id=str(case.get("rule_case_id") or ""),
        item_name=case_name,
        item_type="RuleCase",
        kg_layer="rule_case",
        source_item=case,
        basis=basis,
        target_layer=target_layer,
        recommendation=recommendation,
        action_detail=action_detail,
        extra={
            "owner_node_id": case.get("owner_node_id", ""),
            "owner_name": owner_name,
            "owner_type": case.get("owner_type", ""),
            "applies_to": case.get("applies_to", ""),
            "conditions": case.get("conditions", []),
            "outcomes": case.get("outcomes", []),
        },
    )


def write_summary(path: Path, decisions: list[dict[str, Any]]) -> None:
    counts = Counter(
        (
            str(decision.get("item_kind") or ""),
            str(decision.get("kg_layer") or ""),
            str(decision.get("recommendation") or ""),
        )
        for decision in decisions
    )
    lines = [
        "# v4.3 Step 7A 审核决策草稿",
        "",
        "本文件是通用审核草稿，不是最终入库结果。默认策略是保守暂缓：待审节点、待审边、待审条件判断规则案例都需要复核后才能进入 Step 7B 最终包。",
        "",
        "## 统计",
        "",
    ]
    for (kind, layer, recommendation), count in sorted(counts.items()):
        lines.append(f"- {kind} / {layer} / {recommendation}: {count}")

    lines.extend(
        [
            "",
            "## 审核口径",
            "",
            "1. 节点：确认是否是学生可理解、可检索、可复习的正式知识点；过细、一次性结果或例题临时对象应拒绝或降级为证据。",
            "2. 普通边：确认关系类型、方向和 evidence 是否支持；尤其检查 DERIVES 必须是“推导依据 -> 被推出结论”。",
            "3. 条件判断规则案例：确认适用对象、条件、结论是否对应同一条教材规则；它不是普通边，接受后由 Step 8 展开为规则层节点和边。",
            "4. 被拒绝或改写的项目不会消失；Step 7B 会写入 archive 和 decision_trace。",
            "",
            "## 决策字段说明",
            "",
            "- recommendation: accept / rewrite / reject / defer",
            "- target_layer: core / example_application / rule_case / rejected_archive / review_pending",
            "- rewritten_item: 仅在 rewrite 时填写，可用于 replace_edge、merge_node 或 replace_rule_case。",
            "",
            "## 明细",
            "",
        ]
    )
    for index, decision in enumerate(decisions, start=1):
        if decision["item_kind"] == "edge":
            title = f"{decision['item_type']} {decision.get('source_name', '')} -> {decision.get('target_name', '')}"
        elif decision["item_kind"] == "rule_case":
            title = f"RuleCase {decision.get('owner_name', '')} / {decision.get('item_name', '')}"
        else:
            title = f"{decision['item_type']} {decision['item_name']}"
        lines.append(f"{index}. [{decision['recommendation']}] {title}：{decision['basis']}")
        if decision.get("evidence_excerpt"):
            lines.append(f"   - evidence: {decision['evidence_excerpt']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    review_nodes = read_jsonl(args.layer_dir / "review_pending_nodes.jsonl", required=False)
    review_edges = read_jsonl(args.layer_dir / "review_pending_edges.jsonl", required=False)
    review_rule_cases = read_jsonl(args.layer_dir / "review_pending_rule_cases.jsonl", required=False)

    decisions: list[dict[str, Any]] = []
    decisions.extend(node_decision(node) for node in review_nodes)
    decisions.extend(edge_decision(edge) for edge in review_edges)
    decisions.extend(rule_case_decision(case, args.suggest_clean_rule_cases) for case in review_rule_cases)

    write_jsonl(out_dir / "preapproval_decisions.jsonl", decisions)
    write_summary(out_dir / "preapproval_summary.md", decisions)

    print(f"[OK] preapproval decisions -> {out_dir / 'preapproval_decisions.jsonl'}")
    print(f"[OK] preapproval summary -> {out_dir / 'preapproval_summary.md'}")
    print(f"[INFO] decisions={len(decisions)}")


if __name__ == "__main__":
    main()
