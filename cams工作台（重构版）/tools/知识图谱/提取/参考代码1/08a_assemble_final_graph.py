"""
v4.4 Step 8A: assemble final graph package.

This step executes approved merge plans, migrates edges/rule-case owners,
generates deterministic KnowledgeGroup records, and writes the final package
consumed by Step 8B import. Merged secondary nodes are not imported as visible
KG nodes; their aliases, sources, evidence, and relations are preserved through
the main node and merge traces.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_APPROVED_DIR = SCRIPT_DIR / "中间产物" / "step7_approved_package"
DEFAULT_OUT_DIR = SCRIPT_DIR / "中间产物" / "step8_final_graph"

VALID_NODE_TYPES = {"Concept", "Theorem", "Formula", "Method", "ProblemClass"}
VALID_EDGE_TYPES = {"SUPERIOR", "EQUATIVE", "PART_OF", "HAS_PROPERTY", "USES", "GETS", "DERIVES"}
VALID_GROUP_EDGE_TYPES = {"HAS_MEMBER", "HAS_ANCHOR"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble v4.4 Step 8A final graph package.")
    parser.add_argument("--approved-dir", type=Path, default=DEFAULT_APPROVED_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--allow-soft-warnings", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path, required: bool = True) -> list[dict[str, Any]]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"JSONL not found: {path}")
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def stable_id(prefix: str, parts: list[str]) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:14]
    return f"{prefix}:{digest}"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def source_code(row: dict[str, Any]) -> str:
    section_node_id = str(row.get("section_node_id") or "").strip()
    textbook_id = str(row.get("textbook_id") or "").strip()
    base = section_node_id or textbook_id or "unknown-source"
    line_start = row.get("line_start")
    line_end = row.get("line_end")
    if line_start not in (None, "", 0) or line_end not in (None, "", 0):
        return f"{base}:L{line_start or ''}-L{line_end or ''}"
    return base


def ensure_source_code(item: dict[str, Any]) -> dict[str, Any]:
    item.setdefault("source_code", source_code(item))
    return item


def unique_list(values: list[Any]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def list_values(row: dict[str, Any], field: str) -> list[Any]:
    value = row.get(field)
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def merge_list_field(target: dict[str, Any], source: dict[str, Any], field: str) -> None:
    target[field] = unique_list([*list_values(target, field), *list_values(source, field)])


def merge_text_field(target: dict[str, Any], source: dict[str, Any], field: str) -> None:
    target_text = str(target.get(field) or "").strip()
    source_text = str(source.get(field) or "").strip()
    if not source_text or source_text == target_text:
        return
    if not target_text:
        target[field] = source_text
    elif source_text not in target_text:
        target[field] = f"{target_text}\n{source_text}"


def normalize_node(node: dict[str, Any]) -> dict[str, Any]:
    item = ensure_source_code(dict(node))
    item.setdefault("aliases", [])
    item.setdefault("source_codes", unique_list([item.get("source_code", "")]))
    evidence = str(item.get("evidence_span") or "")
    item.setdefault("evidence_spans_merged", [evidence] if evidence else [])
    item["final_import_ready"] = True
    return item


def normalize_edge(edge: dict[str, Any]) -> dict[str, Any]:
    item = ensure_source_code(dict(edge))
    if not item.get("edge_id"):
        item["edge_id"] = stable_id(
            f"{item.get('textbook_id', '')}:edge",
            [str(item.get("source_node_id") or ""), str(item.get("target_node_id") or ""), str(item.get("type") or ""), str(item.get("kg_layer") or "")],
        )
    item["final_import_ready"] = True
    return item


def node_key(row: dict[str, Any]) -> str:
    return str(row.get("node_id") or "")


def edge_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("source_node_id") or ""),
        str(row.get("target_node_id") or ""),
        str(row.get("type") or ""),
        str(row.get("kg_layer") or ""),
    )


def rule_case_key(row: dict[str, Any]) -> str:
    if row.get("rule_case_id"):
        return str(row.get("rule_case_id"))
    return stable_id("rule-case-key", [str(row.get("owner_node_id") or ""), str(row.get("case_name") or ""), str(row.get("evidence_span") or "")])


def dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: dict[str, dict[str, Any]] = {}
    for node in nodes:
        key = node_key(node)
        if not key:
            continue
        if key in kept:
            merge_node_payload(kept[key], node)
        else:
            kept[key] = node
    return list(kept.values())


def dedupe_edges(edges: list[dict[str, Any]], archived_edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for edge in edges:
        key = edge_key(edge)
        if key in kept:
            merge_list_field(kept[key], edge, "source_codes")
            merge_list_field(kept[key], edge, "evidence_spans_merged")
            archived = dict(edge)
            archived["archive_status"] = "duplicate_edge_after_step8_merge"
            archived_edges.append(archived)
            continue
        kept[key] = edge
    return list(kept.values())


def archive_edges_with_missing_endpoints(
    edges: list[dict[str, Any]],
    node_ids: set[str],
    archived_edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    kept: list[dict[str, Any]] = []
    for edge in edges:
        source_id = str(edge.get("source_node_id") or "")
        target_id = str(edge.get("target_node_id") or "")
        missing: list[str] = []
        if source_id not in node_ids:
            missing.append("source")
        if target_id not in node_ids:
            missing.append("target")
        if not missing:
            kept.append(edge)
            continue
        archived = dict(edge)
        archived["archive_status"] = "endpoint_missing_after_step7_or_merge"
        archived["missing_endpoint_roles"] = missing
        archived["missing_source_node_id"] = source_id if "source" in missing else ""
        archived["missing_target_node_id"] = target_id if "target" in missing else ""
        archived_edges.append(archived)
    return kept


def merge_node_payload(main: dict[str, Any], secondary: dict[str, Any]) -> None:
    secondary_name = str(secondary.get("name") or "")
    aliases = list_values(main, "aliases")
    if secondary_name and secondary_name != main.get("name") and secondary_name not in aliases:
        aliases.append(secondary_name)
    for alias in list_values(secondary, "aliases"):
        if alias and alias != main.get("name"):
            aliases.append(alias)
    main["aliases"] = unique_list(aliases)
    merge_text_field(main, secondary, "definition")
    merge_text_field(main, secondary, "description")
    merge_text_field(main, secondary, "evidence_span")
    for field in ["source_codes", "source_labels", "evidence_spans_merged", "attributes", "state_notes"]:
        merge_list_field(main, secondary, field)
    merged = list_values(main, "step8_merged_nodes")
    merged.append(
        {
            "node_id": secondary.get("node_id", ""),
            "name": secondary.get("name", ""),
            "type": secondary.get("type", ""),
            "source_code": secondary.get("source_code", ""),
        }
    )
    main["step8_merged_nodes"] = unique_list(merged)


def apply_merge_plans(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    rule_cases: list[dict[str, Any]],
    merge_plans: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    node_by_id = {node_key(node): node for node in nodes if node_key(node)}
    merge_id_map: dict[str, str] = {}
    merged_nodes: list[dict[str, Any]] = []
    merge_trace: list[dict[str, Any]] = []

    for plan in merge_plans:
        main_id = str(plan.get("main_node_id") or "")
        merge_id = str(plan.get("merge_node_id") or "")
        main = node_by_id.get(main_id)
        secondary = node_by_id.get(merge_id)
        if not main:
            warnings.append(f"merge_main_node_missing:{plan.get('merge_plan_id', '')}:{main_id}")
            continue
        if not secondary:
            warnings.append(f"merge_secondary_node_missing:{plan.get('merge_plan_id', '')}:{merge_id}")
            continue
        if main.get("type") != secondary.get("type"):
            warnings.append(f"merge_type_mismatch:{main_id}:{merge_id}")
            continue
        merge_node_payload(main, secondary)
        merge_id_map[merge_id] = main_id
        merged_record = dict(secondary)
        merged_record["step8_status"] = "merged_into"
        merged_record["merged_into_node_id"] = main_id
        merged_record["merged_into_name"] = main.get("name", "")
        merged_record["final_import_ready"] = False
        merged_nodes.append(merged_record)
        merge_trace.append(
            {
                "merge_plan_id": plan.get("merge_plan_id", ""),
                "main_node_id": main_id,
                "main_name": main.get("name", ""),
                "merge_node_id": merge_id,
                "merge_name": secondary.get("name", ""),
                "actions": plan.get("actions", []),
                "reason": plan.get("reason", ""),
                "applied_at": now_iso(),
            }
        )

    final_nodes = [node for node in nodes if node_key(node) not in merge_id_map]
    archived_edges_after_merge: list[dict[str, Any]] = []
    migrated_edges: list[dict[str, Any]] = []
    node_by_id = {node_key(node): node for node in final_nodes if node_key(node)}
    for edge in edges:
        item = dict(edge)
        original_source = str(item.get("source_node_id") or "")
        original_target = str(item.get("target_node_id") or "")
        if original_source in merge_id_map:
            new_source = node_by_id.get(merge_id_map[original_source], {})
            item["source_node_id"] = merge_id_map[original_source]
            item["source_name"] = new_source.get("name", item.get("source_name", ""))
            item["source_type"] = new_source.get("type", item.get("source_type", ""))
            item["step8_migrated_from_source_node_id"] = original_source
        if original_target in merge_id_map:
            new_target = node_by_id.get(merge_id_map[original_target], {})
            item["target_node_id"] = merge_id_map[original_target]
            item["target_name"] = new_target.get("name", item.get("target_name", ""))
            item["target_type"] = new_target.get("type", item.get("target_type", ""))
            item["step8_migrated_from_target_node_id"] = original_target
        if item.get("source_node_id") == item.get("target_node_id"):
            item["archive_status"] = "self_loop_after_merge"
            archived_edges_after_merge.append(item)
            continue
        migrated_edges.append(item)

    for case in rule_cases:
        owner_id = str(case.get("owner_node_id") or "")
        if owner_id in merge_id_map:
            main = node_by_id.get(merge_id_map[owner_id], {})
            case["owner_node_id"] = merge_id_map[owner_id]
            case["owner_name"] = main.get("name", case.get("owner_name", ""))
            case["owner_type"] = main.get("type", case.get("owner_type", ""))
            case["step8_migrated_from_owner_node_id"] = owner_id

    return final_nodes, migrated_edges, rule_cases, merged_nodes, merge_trace, archived_edges_after_merge, warnings


def build_section_groups(nodes: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        section_node_id = str(node.get("section_node_id") or "")
        if not section_node_id:
            continue
        grouped[section_node_id].append(node)
    groups: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for section_node_id, members in sorted(grouped.items()):
        first = members[0]
        group_id = stable_id(f"{first.get('textbook_id', '')}:group", [section_node_id, "SectionGroup"])
        name_parts = [str(first.get("chapter") or ""), str(first.get("section") or ""), str(first.get("subsection") or "")]
        group_name = " ".join(part for part in name_parts if part).strip() or section_node_id
        group = ensure_source_code(
            {
                "group_id": group_id,
                "name": f"{group_name}知识组",
                "type": "KnowledgeGroup",
                "group_type": "SectionGroup",
                "kg_layer": "knowledge_group",
                "textbook_id": first.get("textbook_id", ""),
                "textbook_name": first.get("textbook_name", ""),
                "chapter": first.get("chapter", ""),
                "section": first.get("section", ""),
                "subsection": first.get("subsection", ""),
                "section_node_id": section_node_id,
                "source_scope": first.get("source_scope", ""),
                "member_count": len(members),
                "creation_policy": "auto_by_section_node_id",
                "final_import_ready": True,
                "step8_generated_at": now_iso(),
            }
        )
        groups.append(group)
        for member in members:
            member_id = str(member.get("node_id") or "")
            if not member_id:
                continue
            edges.append(
                ensure_source_code(
                    {
                        "edge_id": stable_id(f"{first.get('textbook_id', '')}:groupedge", [group_id, member_id, "HAS_MEMBER"]),
                        "type": "HAS_MEMBER",
                        "kg_layer": "knowledge_group",
                        "source_group_id": group_id,
                        "source_node_id": group_id,
                        "source_name": group["name"],
                        "source_type": "KnowledgeGroup",
                        "target_node_id": member_id,
                        "target_name": member.get("name", ""),
                        "target_type": member.get("type", ""),
                        "textbook_id": member.get("textbook_id", ""),
                        "textbook_name": member.get("textbook_name", ""),
                        "chapter": member.get("chapter", ""),
                        "section": member.get("section", ""),
                        "subsection": member.get("subsection", ""),
                        "section_node_id": member.get("section_node_id", ""),
                        "source_scope": member.get("source_scope", ""),
                        "description": "知识点属于该小节知识组。",
                        "evidence_span": member.get("evidence_span", ""),
                        "confidence": 1.0,
                        "final_import_ready": True,
                        "step8_generated_at": now_iso(),
                    }
                )
            )
    return groups, edges


def build_rule_groups(rule_cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in rule_cases:
        owner_id = str(case.get("owner_node_id") or "")
        if owner_id:
            grouped[owner_id].append(case)
    groups: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for owner_id, cases in sorted(grouped.items()):
        first = cases[0]
        owner_name = str(first.get("owner_name") or owner_id)
        group_id = stable_id(f"{first.get('textbook_id', '')}:group", [owner_id, "RuleGroup"])
        group = ensure_source_code(
            {
                "group_id": group_id,
                "name": f"{owner_name}规则组",
                "type": "KnowledgeGroup",
                "group_type": "RuleGroup",
                "kg_layer": "knowledge_group",
                "textbook_id": first.get("textbook_id", ""),
                "textbook_name": first.get("textbook_name", ""),
                "chapter": first.get("chapter", ""),
                "section": first.get("section", ""),
                "subsection": first.get("subsection", ""),
                "section_node_id": first.get("section_node_id", ""),
                "source_scope": first.get("source_scope", ""),
                "member_count": len(cases),
                "anchor_node_id": owner_id,
                "anchor_name": owner_name,
                "creation_policy": "auto_by_rule_case_owner",
                "final_import_ready": True,
                "step8_generated_at": now_iso(),
            }
        )
        groups.append(group)
        edges.append(
            ensure_source_code(
                {
                    "edge_id": stable_id(f"{first.get('textbook_id', '')}:groupedge", [group_id, owner_id, "HAS_ANCHOR"]),
                    "type": "HAS_ANCHOR",
                    "kg_layer": "knowledge_group",
                    "source_group_id": group_id,
                    "source_node_id": group_id,
                    "source_name": group["name"],
                    "source_type": "KnowledgeGroup",
                    "target_node_id": owner_id,
                    "target_name": owner_name,
                    "target_type": first.get("owner_type", ""),
                    "textbook_id": first.get("textbook_id", ""),
                    "textbook_name": first.get("textbook_name", ""),
                    "chapter": first.get("chapter", ""),
                    "section": first.get("section", ""),
                    "subsection": first.get("subsection", ""),
                    "section_node_id": first.get("section_node_id", ""),
                    "source_scope": first.get("source_scope", ""),
                    "description": "规则组的锚点知识节点。",
                    "evidence_span": first.get("evidence_span", ""),
                    "confidence": 1.0,
                    "final_import_ready": True,
                    "step8_generated_at": now_iso(),
                }
            )
        )
        for case in cases:
            case_id = str(case.get("rule_case_id") or "")
            if not case_id:
                continue
            edges.append(
                ensure_source_code(
                    {
                        "edge_id": stable_id(f"{first.get('textbook_id', '')}:groupedge", [group_id, case_id, "HAS_MEMBER"]),
                        "type": "HAS_MEMBER",
                        "kg_layer": "knowledge_group",
                        "source_group_id": group_id,
                        "source_node_id": group_id,
                        "source_name": group["name"],
                        "source_type": "KnowledgeGroup",
                        "target_node_id": case_id,
                        "target_name": case.get("case_name", ""),
                        "target_type": "RuleCase",
                        "textbook_id": case.get("textbook_id", ""),
                        "textbook_name": case.get("textbook_name", ""),
                        "chapter": case.get("chapter", ""),
                        "section": case.get("section", ""),
                        "subsection": case.get("subsection", ""),
                        "section_node_id": case.get("section_node_id", ""),
                        "source_scope": case.get("source_scope", ""),
                        "description": "规则案例属于该规则组。",
                        "evidence_span": case.get("evidence_span", ""),
                        "confidence": 1.0,
                        "final_import_ready": True,
                        "step8_generated_at": now_iso(),
                    }
                )
            )
    return groups, edges


def rule_case_text(case: dict[str, Any]) -> str:
    parts: list[str] = []
    for field in ["applies_to", "case_name", "evidence_span", "owner_name"]:
        value = case.get(field)
        if value:
            parts.append(str(value))
    for field in ["conditions", "outcomes", "conclusions"]:
        for value in list_values(case, field):
            if value:
                parts.append(str(value))
    return "\n".join(parts)


def reroute_rule_cases_with_missing_owner(
    rule_cases: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    node_by_id = {str(node.get("node_id") or ""): node for node in nodes if node.get("node_id")}
    candidates = sorted(
        [node for node in nodes if node.get("kg_layer") == "core" and node.get("type") in {"Concept", "Theorem", "Formula"}],
        key=lambda row: len(str(row.get("name") or "")),
        reverse=True,
    )
    rerouted: list[dict[str, Any]] = []
    for case in rule_cases:
        owner_id = str(case.get("owner_node_id") or "")
        if owner_id in node_by_id:
            continue
        text = rule_case_text(case)
        for node in candidates:
            name = str(node.get("name") or "").strip()
            if not name or len(name) < 2 or name not in text:
                continue
            old_owner_id = owner_id
            old_owner_name = str(case.get("owner_name") or "")
            case["owner_node_id"] = str(node.get("node_id") or "")
            case["owner_name"] = name
            case["owner_type"] = str(node.get("type") or "")
            case["step8_rerouted_from_owner_node_id"] = old_owner_id
            case["step8_rerouted_from_owner_name"] = old_owner_name
            case["step8_reroute_reason"] = "owner_missing_after_review_and_rule_case_text_contains_core_node_name"
            rerouted.append(
                {
                    "rule_case_id": case.get("rule_case_id", ""),
                    "old_owner_node_id": old_owner_id,
                    "old_owner_name": old_owner_name,
                    "new_owner_node_id": case["owner_node_id"],
                    "new_owner_name": name,
                    "reason": case["step8_reroute_reason"],
                }
            )
            break
    return rule_cases, rerouted


def validate_final_package(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    rule_cases: list[dict[str, Any]],
    groups: list[dict[str, Any]],
    group_edges: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    hard: list[dict[str, Any]] = []
    soft: list[dict[str, Any]] = []
    node_ids = {str(node.get("node_id") or "") for node in nodes if node.get("node_id")}
    group_ids = {str(group.get("group_id") or "") for group in groups if group.get("group_id")}
    rule_case_ids = {str(case.get("rule_case_id") or "") for case in rule_cases if case.get("rule_case_id")}
    visible_ids = node_ids | group_ids | rule_case_ids

    for node in nodes:
        if not node.get("node_id"):
            hard.append({"warning": "node_missing_id", "name": node.get("name", "")})
        if node.get("type") not in VALID_NODE_TYPES:
            hard.append({"warning": "invalid_node_type", "node_id": node.get("node_id", ""), "type": node.get("type", "")})
    for edge in edges:
        if edge.get("type") not in VALID_EDGE_TYPES:
            hard.append({"warning": "invalid_edge_type", "edge_id": edge.get("edge_id", ""), "type": edge.get("type", "")})
        if edge.get("source_node_id") not in node_ids:
            hard.append({"warning": "edge_source_missing", "edge_id": edge.get("edge_id", ""), "source_node_id": edge.get("source_node_id", "")})
        if edge.get("target_node_id") not in node_ids:
            hard.append({"warning": "edge_target_missing", "edge_id": edge.get("edge_id", ""), "target_node_id": edge.get("target_node_id", "")})
        if edge.get("source_node_id") == edge.get("target_node_id"):
            hard.append({"warning": "edge_self_loop", "edge_id": edge.get("edge_id", "")})
    for case in rule_cases:
        case_id = str(case.get("rule_case_id") or case.get("case_name") or "")
        if not case.get("owner_node_id") or case.get("owner_node_id") not in node_ids:
            hard.append({"warning": "rule_case_owner_missing", "rule_case_id": case_id, "owner_node_id": case.get("owner_node_id", "")})
        if not case.get("conditions"):
            hard.append({"warning": "rule_case_missing_conditions", "rule_case_id": case_id})
        if not case.get("outcomes"):
            hard.append({"warning": "rule_case_missing_outcomes", "rule_case_id": case_id})
    for edge in group_edges:
        if edge.get("type") not in VALID_GROUP_EDGE_TYPES:
            hard.append({"warning": "invalid_group_edge_type", "edge_id": edge.get("edge_id", ""), "type": edge.get("type", "")})
        if edge.get("source_node_id") not in group_ids:
            hard.append({"warning": "group_edge_source_missing", "edge_id": edge.get("edge_id", ""), "source_node_id": edge.get("source_node_id", "")})
        if edge.get("target_node_id") not in visible_ids:
            hard.append({"warning": "group_edge_target_missing", "edge_id": edge.get("edge_id", ""), "target_node_id": edge.get("target_node_id", "")})
    for group in groups:
        if not group.get("group_id"):
            hard.append({"warning": "group_missing_id", "name": group.get("name", "")})
    return hard, soft


def write_report(path: Path, counts: dict[str, int], hard_warnings: list[dict[str, Any]], soft_warnings: list[dict[str, Any]]) -> None:
    lines = ["# v4.4 Step 8A Final Graph Assembly Report", "", "## Counts"]
    for key, value in sorted(counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Hard Warnings"])
    if hard_warnings:
        for warning in hard_warnings[:100]:
            lines.append(f"- {json.dumps(warning, ensure_ascii=False)}")
    else:
        lines.append("- none")
    lines.extend(["", "## Soft Warnings"])
    if soft_warnings:
        for warning in soft_warnings[:100]:
            lines.append(f"- {json.dumps(warning, ensure_ascii=False)}")
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    core_nodes = [normalize_node(row) for row in read_jsonl(args.approved_dir / "approved_core_nodes.jsonl", required=False)]
    app_nodes = [normalize_node(row) for row in read_jsonl(args.approved_dir / "approved_application_nodes.jsonl", required=False)]
    core_edges = [normalize_edge(row) for row in read_jsonl(args.approved_dir / "approved_core_edges.jsonl", required=False)]
    app_edges = [normalize_edge(row) for row in read_jsonl(args.approved_dir / "approved_application_edges.jsonl", required=False)]
    rule_cases = [ensure_source_code(dict(row)) for row in read_jsonl(args.approved_dir / "approved_rule_cases.jsonl", required=False)]
    merge_plans = read_jsonl(args.approved_dir / "merge_plans.jsonl", required=False)

    all_nodes = dedupe_nodes([*core_nodes, *app_nodes])
    all_edges = [*core_edges, *app_edges]
    all_nodes, all_edges, rule_cases, merged_nodes, merge_trace, archived_edges_after_merge, merge_warnings = apply_merge_plans(all_nodes, all_edges, rule_cases, merge_plans)

    final_core_nodes = [node for node in all_nodes if node.get("kg_layer") == "core"]
    final_app_nodes = [node for node in all_nodes if node.get("kg_layer") == "example_application"]
    archived_edges: list[dict[str, Any]] = [*archived_edges_after_merge]
    all_edges = dedupe_edges([normalize_edge(edge) for edge in all_edges], archived_edges)
    visible_node_ids = {node_key(node) for node in [*final_core_nodes, *final_app_nodes] if node_key(node)}
    all_edges = archive_edges_with_missing_endpoints(all_edges, visible_node_ids, archived_edges)
    final_core_edges = [edge for edge in all_edges if edge.get("kg_layer") == "core"]
    final_app_edges = [edge for edge in all_edges if edge.get("kg_layer") == "example_application"]

    rule_cases, rerouted_rule_case_owners = reroute_rule_cases_with_missing_owner(rule_cases, [*final_core_nodes, *final_app_nodes])
    section_groups, section_group_edges = build_section_groups([*final_core_nodes, *final_app_nodes])
    rule_groups, rule_group_edges = build_rule_groups(rule_cases)
    groups = [*section_groups, *rule_groups]
    group_edges = [*section_group_edges, *rule_group_edges]

    hard_warnings, soft_warnings = validate_final_package(
        [*final_core_nodes, *final_app_nodes],
        [*final_core_edges, *final_app_edges],
        rule_cases,
        groups,
        group_edges,
    )
    for warning in merge_warnings:
        soft_warnings.append({"warning": warning})

    write_jsonl(out_dir / "final_core_nodes.jsonl", final_core_nodes)
    write_jsonl(out_dir / "final_core_edges.jsonl", final_core_edges)
    write_jsonl(out_dir / "final_application_nodes.jsonl", final_app_nodes)
    write_jsonl(out_dir / "final_application_edges.jsonl", final_app_edges)
    write_jsonl(out_dir / "final_rule_cases.jsonl", rule_cases)
    write_jsonl(out_dir / "final_knowledge_groups.jsonl", groups)
    write_jsonl(out_dir / "final_knowledge_group_edges.jsonl", group_edges)
    write_jsonl(out_dir / "merged_nodes.jsonl", merged_nodes)
    write_jsonl(out_dir / "merge_trace.jsonl", merge_trace)
    write_jsonl(out_dir / "rerouted_rule_case_owners.jsonl", rerouted_rule_case_owners)
    write_jsonl(out_dir / "archived_edges_after_merge.jsonl", archived_edges)
    write_jsonl(out_dir / "step8_assembly_hard_warnings.jsonl", hard_warnings)
    write_jsonl(out_dir / "step8_assembly_soft_warnings.jsonl", soft_warnings)
    write_report(
        out_dir / "step8_assembly_report.md",
        {
            "final_core_nodes": len(final_core_nodes),
            "final_core_edges": len(final_core_edges),
            "final_application_nodes": len(final_app_nodes),
            "final_application_edges": len(final_app_edges),
            "final_rule_cases": len(rule_cases),
            "knowledge_groups": len(groups),
            "knowledge_group_edges": len(group_edges),
            "merged_nodes": len(merged_nodes),
            "rerouted_rule_case_owners": len(rerouted_rule_case_owners),
            "merge_trace_rows": len(merge_trace),
            "archived_edges_after_merge": len(archived_edges),
            "hard_warnings": len(hard_warnings),
            "soft_warnings": len(soft_warnings),
        },
        hard_warnings,
        soft_warnings,
    )
    print(f"[OK] final graph package -> {out_dir}")
    print(f"[INFO] hard_warnings={len(hard_warnings)} soft_warnings={len(soft_warnings)}")
    if hard_warnings:
        print("[ERROR] Step 8A hard warnings exist; stop before Neo4j import.", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
