# -*- coding: utf-8 -*-
"""
v4.4 Step 8B: import the final assembled KG package into Neo4j.

Default policy:
  - Import final_core_*, final_application_*, and final_knowledge_group_* records.
  - Do not import final_archived_items / decision_trace into the visible graph.
  - Refuse execution when Step 8A hard warnings exist.
  - Clear only existing KGNode records for involved textbook_id values when
    --clear-textbook is supplied. This avoids deleting unrelated local data.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parents[1]
REPO_ROOT = SCRIPT_DIR.parents[2]
FINAL_DIR = SCRIPT_DIR / "中间产物" / "step8_final_graph"
DEFAULT_REPORT_PATH = SCRIPT_DIR / "中间产物" / "neo4j_v4_4_import_report.md"
DEFAULT_CYPHER_PATH = SCRIPT_DIR / "中间产物" / "import_neo4j_v4_4.cypher"
ENV_PATHS = [REPO_ROOT / ".env", MODULE_DIR / ".env"]

VALID_NODE_TYPES = {
    "Concept",
    "Definition",
    "Theorem",
    "Formula",
    "Method",
    "ProblemClass",
    "RuleCase",
    "ConditionExpression",
    "Outcome",
    "LogicGroup",
    "KnowledgeGroup",
}
VALID_EDGE_TYPES = {
    "SUPERIOR",
    "EQUATIVE",
    "PART_OF",
    "HAS_PROPERTY",
    "USES",
    "GETS",
    "DERIVES",
    "HAS_RULE_CASE",
    "APPLIES_TO",
    "HAS_CONDITION",
    "HAS_CONDITION_AND",
    "HAS_CONDITION_OR",
    "HAS_OUTCOME",
    "HAS_OUTCOME_AND",
    "HAS_OUTCOME_OR",
    "PREREQUISITE_OF",
    "HAS_POSSIBLE_STATE",
    "HAS_MEMBER",
    "HAS_ANCHOR",
    "RELATES_TO_GROUP",
    "REFERS_TO",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import v4.4 final KG package into Neo4j.")
    parser.add_argument("--final-dir", type=Path, default=FINAL_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--cypher", type=Path, default=DEFAULT_CYPHER_PATH)
    parser.add_argument("--uri", default=load_env_value("NEO4J_URI") or "neo4j://127.0.0.1:7687")
    parser.add_argument("--user", default=load_env_value("NEO4J_USER") or "neo4j")
    parser.add_argument("--password", default=load_env_value("NEO4J_PASSWORD") or "zhang2004")
    parser.add_argument("--database", default=load_env_value("NEO4J_DATABASE") or "neo4j")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--clear-textbook", action="store_true")
    parser.add_argument("--import-batch", default="")
    return parser.parse_args()


def read_jsonl(path: Path, required: bool = True) -> list[dict[str, Any]]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"JSONL not found: {path}")
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def load_env_value(key: str) -> str:
    if os.environ.get(key):
        return os.environ[key]
    for env_path in ENV_PATHS:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            name, value = stripped.split("=", 1)
            if name.strip() == key:
                return value.strip().strip('"').strip("'")
    return ""


def cypher_key(value: Any) -> str:
    return "`" + str(value).replace("`", "``") + "`"


def cypher_label(value: Any) -> str:
    label = str(value or "")
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", label):
        return label
    return cypher_key(label)


def cypher_literal(value: Any) -> str:
    if isinstance(value, dict):
        return "{" + ", ".join(f"{cypher_key(k)}: {cypher_literal(v)}" for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(cypher_literal(item) for item in value) + "]"
    return json.dumps(value, ensure_ascii=False)


def safe_scalar(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return value
    return json.dumps(value, ensure_ascii=False)


def safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        result: list[Any] = []
        for item in value:
            if isinstance(item, (str, int, float, bool)):
                result.append(item)
            else:
                result.append(json.dumps(item, ensure_ascii=False))
        return result
    if value in (None, ""):
        return []
    return [safe_scalar(value)]


def stable_generated_id(prefix: str, parts: list[str]) -> str:
    import hashlib

    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:14]
    return f"{prefix}:{digest}"


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


def is_referrable_node(node: dict[str, Any]) -> bool:
    if node.get("type") not in {"Concept", "Formula", "Theorem", "Method", "ProblemClass"}:
        return False
    name = str(node.get("name") or "").strip()
    if len(name) < 2:
        return False
    if name in {"有解", "无解", "零解", "非零解", "唯一解", "秩", "解", "行", "列"}:
        return False
    return True


def mentioned_nodes(text: str, nodes: list[dict[str, Any]], textbook_id: str, limit: int = 6) -> list[dict[str, Any]]:
    normalized = str(text or "")
    if not normalized:
        return []
    hits: list[dict[str, Any]] = []
    for node in nodes:
        if str(node.get("textbook_id") or "") != textbook_id:
            continue
        if not is_referrable_node(node):
            continue
        name = str(node.get("name") or "").strip()
        if name and name in normalized:
            hits.append(node)
    hits.sort(key=lambda row: len(str(row.get("name") or "")), reverse=True)
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for hit in hits:
        node_id = str(hit.get("node_id") or "")
        if not node_id or node_id in seen:
            continue
        seen.add(node_id)
        unique.append(hit)
        if len(unique) >= limit:
            break
    return unique


def refers_to_edges(
    source_node_id: str,
    source_name: str,
    source_type: str,
    text: str,
    nodes: list[dict[str, Any]],
    base_meta: dict[str, Any],
    evidence_span: str,
) -> list[dict[str, Any]]:
    textbook_id = str(base_meta.get("textbook_id") or "")
    result: list[dict[str, Any]] = []
    for target in mentioned_nodes(text, nodes, textbook_id):
        target_id = str(target.get("node_id") or "")
        if not target_id or target_id == source_node_id:
            continue
        result.append(
            ensure_source_code(
                {
                    "edge_id": stable_generated_id(f"{textbook_id}:refedge", [source_node_id, target_id, "REFERS_TO"]),
                    "type": "REFERS_TO",
                    "source_node_id": source_node_id,
                    "source_name": source_name,
                    "source_type": source_type,
                    "target_node_id": target_id,
                    "target_name": target.get("name", ""),
                    "target_type": target.get("type", ""),
                    **base_meta,
                    "kg_layer": "rule_case",
                    "evidence_span": evidence_span,
                    "description": "条件或结论表达式中提及该核心知识点。",
                    "confidence": 0.8,
                    "final_import_ready": True,
                }
            )
        )
    return result


def compact_node_props(node: dict[str, Any], import_batch: str) -> dict[str, Any]:
    return {
        "node_id": node.get("node_id", ""),
        "name": node.get("name", ""),
        "type": node.get("type", ""),
        "group_id": node.get("group_id", ""),
        "group_type": node.get("group_type", ""),
        "kg_layer": node.get("kg_layer", ""),
        "textbook_id": node.get("textbook_id", ""),
        "textbook_name": node.get("textbook_name", ""),
        "chapter": node.get("chapter", ""),
        "section": node.get("section", ""),
        "subsection": node.get("subsection", ""),
        "section_node_id": node.get("section_node_id", ""),
        "source_scope": node.get("source_scope", ""),
        "source_code": node.get("source_code", ""),
        "source_label": node.get("source_label", ""),
        "aliases": safe_list(node.get("aliases", [])),
        "definition": node.get("definition", ""),
        "description": node.get("description", ""),
        "evidence_span": node.get("evidence_span", ""),
        "confidence": safe_scalar(node.get("confidence", 0.0)),
        "line_start": safe_scalar(node.get("line_start", 0)),
        "line_end": safe_scalar(node.get("line_end", 0)),
        "review_status": node.get("review_status", ""),
        "step7_status": node.get("step7_status", ""),
        "final_import_ready": bool(node.get("final_import_ready", False)),
        "validation_warnings": safe_list(node.get("validation_warnings", [])),
        "source_labels": safe_list(node.get("source_labels", [])),
        "evidence_spans_merged": safe_list(node.get("evidence_spans_merged", [])),
        "attributes_json": json.dumps(node.get("attributes", []), ensure_ascii=False),
        "state_notes_json": json.dumps(node.get("state_notes", []), ensure_ascii=False),
        "rule_cases_json": json.dumps(node.get("rule_cases", []), ensure_ascii=False),
        "owner_node_id": node.get("owner_node_id", ""),
        "owner_name": node.get("owner_name", ""),
        "anchor_node_id": node.get("anchor_node_id", ""),
        "anchor_name": node.get("anchor_name", ""),
        "member_count": safe_scalar(node.get("member_count", 0)),
        "creation_policy": node.get("creation_policy", ""),
        "applies_to": node.get("applies_to", ""),
        "conditions": safe_list(node.get("conditions", [])),
        "condition_logic": node.get("condition_logic", ""),
        "outcomes": safe_list(node.get("outcomes", [])),
        "raw_json": json.dumps(node, ensure_ascii=False),
        "import_batch": import_batch,
        "imported_at": datetime.now().isoformat(timespec="seconds"),
    }


def compact_edge_props(edge: dict[str, Any], import_batch: str) -> dict[str, Any]:
    return {
        "edge_id": edge.get("edge_id", ""),
        "type": edge.get("type", ""),
        "kg_layer": edge.get("kg_layer", ""),
        "source_group_id": edge.get("source_group_id", ""),
        "textbook_id": edge.get("textbook_id", ""),
        "textbook_name": edge.get("textbook_name", ""),
        "source_node_id": edge.get("source_node_id", ""),
        "source_name": edge.get("source_name", ""),
        "source_type": edge.get("source_type", ""),
        "target_node_id": edge.get("target_node_id", ""),
        "target_name": edge.get("target_name", ""),
        "target_type": edge.get("target_type", ""),
        "chapter": edge.get("chapter", ""),
        "section": edge.get("section", ""),
        "subsection": edge.get("subsection", ""),
        "section_node_id": edge.get("section_node_id", ""),
        "source_scope": edge.get("source_scope", ""),
        "source_code": edge.get("source_code", ""),
        "evidence_span": edge.get("evidence_span", ""),
        "description": edge.get("description", ""),
        "confidence": safe_scalar(edge.get("confidence", 0.0)),
        "review_status": edge.get("review_status", ""),
        "step7_status": edge.get("step7_status", ""),
        "final_import_ready": bool(edge.get("final_import_ready", False)),
        "validation_warnings": safe_list(edge.get("validation_warnings", [])),
        "evidence_spans_json": json.dumps(edge.get("evidence_spans", []), ensure_ascii=False),
        "raw_json": json.dumps(edge, ensure_ascii=False),
        "import_batch": import_batch,
        "imported_at": datetime.now().isoformat(timespec="seconds"),
    }


def normalize_group_node(group: dict[str, Any]) -> dict[str, Any]:
    item = dict(group)
    item["node_id"] = item.get("group_id", "")
    item["type"] = "KnowledgeGroup"
    item["kg_layer"] = "knowledge_group"
    item["final_import_ready"] = True
    return item


def load_step8_hard_warnings(final_dir: Path) -> list[dict[str, Any]]:
    return read_jsonl(final_dir / "step8_assembly_hard_warnings.jsonl", required=False)


def load_final_package(final_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    group_nodes = [normalize_group_node(row) for row in read_jsonl(final_dir / "final_knowledge_groups.jsonl", required=False)]
    group_edges = read_jsonl(final_dir / "final_knowledge_group_edges.jsonl", required=False)
    nodes = (
        read_jsonl(final_dir / "final_core_nodes.jsonl")
        + read_jsonl(final_dir / "final_application_nodes.jsonl", required=False)
        + group_nodes
    )
    edges = (
        read_jsonl(final_dir / "final_core_edges.jsonl")
        + read_jsonl(final_dir / "final_application_edges.jsonl", required=False)
        + group_edges
    )
    rule_cases = read_jsonl(final_dir / "final_rule_cases.jsonl", required=False)
    return nodes, edges, rule_cases


def expand_rule_cases(
    nodes: list[dict[str, Any]],
    rule_cases: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    generated_nodes: list[dict[str, Any]] = []
    generated_edges: list[dict[str, Any]] = []
    node_by_id = {str(node.get("node_id") or ""): node for node in nodes if node.get("node_id")}
    node_by_name = {str(node.get("name") or ""): node for node in nodes if node.get("name")}

    for case_index, case in enumerate(rule_cases, start=1):
        if not isinstance(case, dict):
            continue
        owner_id = str(case.get("owner_node_id") or "")
        owner = node_by_id.get(owner_id)
        if not owner:
            owner_name = str(case.get("owner_name") or "")
            owner = node_by_name.get(owner_name)
        if not owner:
            continue
        owner_id = str(owner.get("node_id") or "")
        case_name = str(case.get("case_name") or f"{owner.get('name', '')}规则案例{case_index}").strip()
        case_id = str(case.get("rule_case_id") or stable_generated_id(
            f"{owner.get('textbook_id', '')}:rulecase",
            [owner_id, case_name, str(case.get("evidence_span") or ""), str(case_index)],
        ))
        base_meta = {k: owner.get(k, "") for k in ["textbook_id", "textbook_name", "chapter", "section", "subsection", "section_node_id", "source_scope"]}
        rule_node = {
            **owner,
            "node_id": case_id,
            "name": case_name,
            "type": "RuleCase",
            "kg_layer": "rule_case",
            "owner_node_id": owner_id,
            "owner_name": owner.get("name", ""),
            "applies_to": case.get("applies_to", ""),
            "conditions": case.get("conditions", []),
            "condition_logic": case.get("condition_logic", "UNKNOWN"),
            "outcomes": case.get("outcomes", []),
            "evidence_span": case.get("evidence_span", owner.get("evidence_span", "")),
            "description": case.get("reason", ""),
            "rule_cases": [],
            "final_import_ready": True,
        }
        generated_nodes.append(rule_node)
        generated_edges.append({
            "edge_id": stable_generated_id(f"{owner.get('textbook_id', '')}:ruleedge", [owner_id, case_id, "HAS_RULE_CASE"]),
            "type": "HAS_RULE_CASE",
            "source_node_id": owner_id,
            "source_name": owner.get("name", ""),
            "source_type": owner.get("type", ""),
            "target_node_id": case_id,
            "target_name": case_name,
            "target_type": "RuleCase",
            **base_meta,
            "kg_layer": "rule_case",
            "evidence_span": rule_node.get("evidence_span", ""),
            "description": "定理/公式/方法包含该条件判断规则案例。",
            "confidence": owner.get("confidence", 0.0),
            "final_import_ready": True,
        })

        applies_to = str(case.get("applies_to") or "").strip()
        if applies_to:
            target = node_by_name.get(applies_to)
            if target:
                generated_edges.append({
                    "edge_id": stable_generated_id(f"{owner.get('textbook_id', '')}:ruleedge", [case_id, target.get("node_id", ""), "APPLIES_TO"]),
                    "type": "APPLIES_TO",
                    "source_node_id": case_id,
                    "source_name": case_name,
                    "source_type": "RuleCase",
                    "target_node_id": target.get("node_id", ""),
                    "target_name": applies_to,
                    "target_type": target.get("type", ""),
                    **base_meta,
                    "kg_layer": "rule_case",
                    "evidence_span": rule_node.get("evidence_span", ""),
                    "description": "规则案例适用于该核心知识点。",
                    "confidence": owner.get("confidence", 0.0),
                    "final_import_ready": True,
                })

        logic = str(case.get("condition_logic") or "UNKNOWN").upper()
        condition_rel = "HAS_CONDITION"
        if logic == "AND":
            condition_rel = "HAS_CONDITION_AND"
        elif logic == "OR":
            condition_rel = "HAS_CONDITION_OR"
        for cond_index, condition in enumerate(case.get("conditions") or [], start=1):
            cond_text = str(condition).strip()
            if not cond_text:
                continue
            cond_id = stable_generated_id(f"{owner.get('textbook_id', '')}:condition", [case_id, cond_text, str(cond_index)])
            generated_nodes.append({
                **owner,
                "node_id": cond_id,
                "name": cond_text,
                "type": "ConditionExpression",
                "kg_layer": "rule_case",
                "description": "条件判断规则中的条件表达式。",
                "evidence_span": rule_node.get("evidence_span", ""),
                "rule_cases": [],
                "final_import_ready": True,
            })
            generated_edges.append({
                "edge_id": stable_generated_id(f"{owner.get('textbook_id', '')}:ruleedge", [case_id, cond_id, condition_rel]),
                "type": condition_rel,
                "source_node_id": case_id,
                "source_name": case_name,
                "source_type": "RuleCase",
                "target_node_id": cond_id,
                "target_name": cond_text,
                "target_type": "ConditionExpression",
                **base_meta,
                "kg_layer": "rule_case",
                "evidence_span": rule_node.get("evidence_span", ""),
                "description": "规则案例包含该条件。",
                "confidence": owner.get("confidence", 0.0),
                "final_import_ready": True,
            })
            generated_edges.extend(
                refers_to_edges(
                    cond_id,
                    cond_text,
                    "ConditionExpression",
                    cond_text,
                    nodes,
                    base_meta,
                    rule_node.get("evidence_span", ""),
                )
            )

        for outcome_index, outcome in enumerate(case.get("outcomes") or [], start=1):
            outcome_text = str(outcome).strip()
            if not outcome_text:
                continue
            outcome_id = stable_generated_id(f"{owner.get('textbook_id', '')}:outcome", [case_id, outcome_text, str(outcome_index)])
            generated_nodes.append({
                **owner,
                "node_id": outcome_id,
                "name": outcome_text,
                "type": "Outcome",
                "kg_layer": "rule_case",
                "description": "条件判断规则中的结论或状态结果。",
                "evidence_span": rule_node.get("evidence_span", ""),
                "rule_cases": [],
                "final_import_ready": True,
            })
            generated_edges.append({
                "edge_id": stable_generated_id(f"{owner.get('textbook_id', '')}:ruleedge", [case_id, outcome_id, "HAS_OUTCOME"]),
                "type": "HAS_OUTCOME",
                "source_node_id": case_id,
                "source_name": case_name,
                "source_type": "RuleCase",
                "target_node_id": outcome_id,
                "target_name": outcome_text,
                "target_type": "Outcome",
                **base_meta,
                "kg_layer": "rule_case",
                "evidence_span": rule_node.get("evidence_span", ""),
                "description": "规则案例得到该结论或状态结果。",
                "confidence": owner.get("confidence", 0.0),
                "final_import_ready": True,
            })
            generated_edges.extend(
                refers_to_edges(
                    outcome_id,
                    outcome_text,
                    "Outcome",
                    outcome_text,
                    nodes,
                    base_meta,
                    rule_node.get("evidence_span", ""),
                )
            )
    return generated_nodes, generated_edges


def with_expanded_rule_cases(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    rule_cases: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rule_nodes, rule_edges = expand_rule_cases(nodes, rule_cases)
    return [*nodes, *rule_nodes], [*edges, *rule_edges]


def validate_rule_cases_before_expansion(nodes: list[dict[str, Any]], rule_cases: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    node_ids = {str(node.get("node_id") or "") for node in nodes if node.get("node_id")}
    node_names = {str(node.get("name") or "") for node in nodes if node.get("name")}
    for case in rule_cases:
        case_id = str(case.get("rule_case_id") or case.get("case_name") or "unknown")
        owner_id = str(case.get("owner_node_id") or "")
        owner_name = str(case.get("owner_name") or "")
        if not owner_id and not owner_name:
            warnings.append(f"rule_case_missing_owner:{case_id}")
        elif owner_id and owner_id not in node_ids:
            warnings.append(f"rule_case_owner_id_not_found:{case_id}:{owner_id}")
        elif not owner_id and owner_name not in node_names:
            warnings.append(f"rule_case_owner_name_not_found:{case_id}:{owner_name}")
        if not case.get("conditions"):
            warnings.append(f"rule_case_missing_conditions:{case_id}")
        if not case.get("outcomes"):
            warnings.append(f"rule_case_missing_outcomes:{case_id}")
        if not case.get("evidence_span"):
            warnings.append(f"rule_case_missing_evidence_span:{case_id}")
    return warnings


def validate_package(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    node_ids = {str(node.get("node_id") or "") for node in nodes}
    for node in nodes:
        if not node.get("node_id"):
            warnings.append(f"node_missing_id:{node.get('name', '')}")
        if node.get("type") not in VALID_NODE_TYPES:
            warnings.append(f"unknown_node_type:{node.get('type', '')}:{node.get('name', '')}")
    for edge in edges:
        if edge.get("type") not in VALID_EDGE_TYPES:
            warnings.append(f"unknown_edge_type:{edge.get('type', '')}:{edge.get('edge_id', '')}")
        if edge.get("source_node_id") not in node_ids:
            warnings.append(f"missing_source:{edge.get('source_name', '')}:{edge.get('edge_id', '')}")
        if edge.get("target_node_id") not in node_ids:
            warnings.append(f"missing_target:{edge.get('target_name', '')}:{edge.get('edge_id', '')}")
    return warnings


def build_cypher(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], clear_textbook: bool, import_batch: str) -> str:
    textbook_ids = sorted({str(node.get("textbook_id") or "") for node in nodes if node.get("textbook_id")})
    lines = [
        "// v4.4 KG final package import",
        "CREATE CONSTRAINT kg_node_id IF NOT EXISTS FOR (n:KGNode) REQUIRE n.node_id IS UNIQUE;",
    ]
    if clear_textbook and textbook_ids:
        lines.append(f"WITH {cypher_literal(textbook_ids)} AS textbook_ids")
        lines.append("MATCH (n:KGNode) WHERE n.textbook_id IN textbook_ids DETACH DELETE n;")
        lines.append(f"WITH {cypher_literal(textbook_ids)} AS textbook_ids")
        lines.append("MATCH (a:KGAttribute) WHERE a.textbook_id IN textbook_ids DETACH DELETE a;")
    for node in nodes:
        props = compact_node_props(node, import_batch)
        node_type = node.get("type", "")
        labels = ":KGNode" + (f":{cypher_label(node_type)}" if node_type else "")
        lines.append(f"MERGE (n{labels} {{node_id: {cypher_literal(props['node_id'])}}})")
        lines.append(f"SET n += {cypher_literal(props)};")
    for edge in edges:
        rel_type = str(edge.get("type") or "")
        if rel_type not in VALID_EDGE_TYPES:
            continue
        props = compact_edge_props(edge, import_batch)
        lines.append(
            "MATCH (s:KGNode {node_id: "
            + cypher_literal(edge.get("source_node_id", ""))
            + "}), (t:KGNode {node_id: "
            + cypher_literal(edge.get("target_node_id", ""))
            + "})"
        )
        lines.append(f"MERGE (s)-[r:{cypher_label(rel_type)} {{edge_id: {cypher_literal(props['edge_id'])}}}]->(t)")
        lines.append(f"SET r += {cypher_literal(props)};")
    return "\n".join(lines) + "\n"


def execute_import(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    uri: str,
    user: str,
    password: str,
    database: str | None,
    clear_textbook: bool,
    import_batch: str,
) -> dict[str, Any]:
    from neo4j import GraphDatabase

    stats: dict[str, Any] = {}
    textbook_ids = sorted({str(node.get("textbook_id") or "") for node in nodes if node.get("textbook_id")})
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        driver.verify_connectivity()
        # Bolt 6 在显式指定默认数据库时会触发路由表查找失败；
        # 当 database 为空或等于默认数据库时传 None，让 driver 走默认数据库。
        session_db = database if database and database not in {"neo4j", "default"} else None
        with driver.session(database=session_db) as session:
            before_nodes = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
            before_edges = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]

            session.run("CREATE CONSTRAINT kg_node_id IF NOT EXISTS FOR (n:KGNode) REQUIRE n.node_id IS UNIQUE").consume()

            deleted_nodes = 0
            deleted_attributes = 0
            if clear_textbook and textbook_ids:
                result = session.run(
                    "MATCH (n:KGNode) WHERE n.textbook_id IN $textbook_ids WITH collect(n) AS nodes "
                    "FOREACH (n IN nodes | DETACH DELETE n) RETURN size(nodes) AS deleted",
                    textbook_ids=textbook_ids,
                ).single()
                deleted_nodes = result["deleted"] if result else 0
                result = session.run(
                    "MATCH (a:KGAttribute) WHERE a.textbook_id IN $textbook_ids WITH collect(a) AS attrs "
                    "FOREACH (a IN attrs | DETACH DELETE a) RETURN size(attrs) AS deleted",
                    textbook_ids=textbook_ids,
                ).single()
                deleted_attributes = result["deleted"] if result else 0

            for node in nodes:
                node_type = str(node.get("type") or "")
                labels = ":KGNode" + (f":{cypher_label(node_type)}" if node_type else "")
                props = compact_node_props(node, import_batch)
                session.run(
                    f"MERGE (n{labels} {{node_id: $node_id}}) SET n += $props",
                    node_id=props["node_id"],
                    props=props,
                ).consume()

            imported_edges = 0
            skipped_edges: list[str] = []
            for edge in edges:
                rel_type = str(edge.get("type") or "")
                if rel_type not in VALID_EDGE_TYPES:
                    skipped_edges.append(str(edge.get("edge_id") or edge.get("type") or "unknown"))
                    continue
                props = compact_edge_props(edge, import_batch)
                result = session.run(
                    "MATCH (s:KGNode {node_id: $source_node_id}), (t:KGNode {node_id: $target_node_id}) "
                    f"MERGE (s)-[r:{cypher_label(rel_type)} {{edge_id: $edge_id}}]->(t) "
                    "SET r += $props RETURN count(r) AS count",
                    source_node_id=edge.get("source_node_id", ""),
                    target_node_id=edge.get("target_node_id", ""),
                    edge_id=props["edge_id"],
                    props=props,
                ).single()
                if result and result["count"]:
                    imported_edges += 1
                else:
                    skipped_edges.append(str(edge.get("edge_id") or "unknown"))

            after_nodes = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
            after_edges = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]
            kg_nodes = session.run(
                "MATCH (n:KGNode) WHERE n.import_batch = $import_batch RETURN count(n) AS count",
                import_batch=import_batch,
            ).single()["count"]
            kg_edges = session.run(
                "MATCH ()-[r]->() WHERE r.import_batch = $import_batch RETURN count(r) AS count",
                import_batch=import_batch,
            ).single()["count"]
            stats = {
                "before_nodes": before_nodes,
                "before_edges": before_edges,
                "deleted_nodes": deleted_nodes,
                "deleted_attributes": deleted_attributes,
                "after_nodes": after_nodes,
                "after_edges": after_edges,
                "imported_batch_nodes": kg_nodes,
                "imported_batch_edges": kg_edges,
                "edge_write_attempts": imported_edges,
                "skipped_edges": skipped_edges,
            }
    finally:
        driver.close()
    return stats


def write_report(
    path: Path,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    warnings: list[str],
    executed: bool,
    clear_textbook: bool,
    database: str,
    import_batch: str,
    stats: dict[str, Any],
) -> None:
    node_types = Counter(str(node.get("type") or "") for node in nodes)
    edge_types = Counter(str(edge.get("type") or "") for edge in edges)
    layers = Counter(str(row.get("kg_layer") or "") for row in [*nodes, *edges])
    lines = [
        "# v4.4 Step 8B Neo4j Import Report",
        "",
        f"- executed: {str(executed).lower()}",
        f"- database: `{database}`",
        f"- clear_textbook: {str(clear_textbook).lower()}",
        f"- import_batch: `{import_batch}`",
        f"- nodes: {len(nodes)}",
        f"- edges: {len(edges)}",
        f"- warnings: {len(warnings)}",
        "",
        "## Import Stats",
    ]
    if stats:
        for key, value in stats.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- not executed")
    lines.extend(["", "## Node Types"])
    for key, count in sorted(node_types.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Edge Types"])
    for key, count in sorted(edge_types.items()):
        lines.append(f"- {key}: {count}")
    lines.extend(["", "## Layers"])
    for key, count in sorted(layers.items()):
        lines.append(f"- {key}: {count}")
    if warnings:
        lines.extend(["", "## Warnings"])
        for warning in warnings[:100]:
            lines.append(f"- {warning}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    import_batch = args.import_batch or f"v4.4-preview-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    step8_hard_warnings = load_step8_hard_warnings(args.final_dir)
    if step8_hard_warnings:
        raise RuntimeError(
            "Refuse to import package because Step 8A hard warnings exist: "
            + json.dumps(step8_hard_warnings[:5], ensure_ascii=False)
        )
    source_nodes, source_edges, rule_cases = load_final_package(args.final_dir)
    rule_case_warnings = validate_rule_cases_before_expansion(source_nodes, rule_cases)
    nodes, edges = with_expanded_rule_cases(source_nodes, source_edges, rule_cases)
    warnings = [*rule_case_warnings, *validate_package(nodes, edges)]
    cypher = build_cypher(nodes, edges, args.clear_textbook, import_batch)
    args.cypher.parent.mkdir(parents=True, exist_ok=True)
    args.cypher.write_text(cypher, encoding="utf-8")

    stats: dict[str, Any] = {}
    if args.execute:
        if warnings:
            raise RuntimeError(f"Refuse to import package with validation warnings: {warnings[:5]}")
        stats = execute_import(
            nodes,
            edges,
            args.uri,
            args.user,
            args.password,
            args.database or None,
            args.clear_textbook,
            import_batch,
        )

    write_report(
        args.report,
        nodes,
        edges,
        warnings,
        args.execute,
        args.clear_textbook,
        args.database,
        import_batch,
        stats,
    )
    print(f"[OK] cypher -> {args.cypher}")
    print(f"[OK] report -> {args.report}")
    print(
        f"[INFO] source_nodes={len(source_nodes)} source_edges={len(source_edges)} "
        f"rule_cases={len(rule_cases)} expanded_nodes={len(nodes)} expanded_edges={len(edges)} "
        f"warnings={len(warnings)} executed={args.execute}"
    )
    if stats:
        print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
