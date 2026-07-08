# -*- coding: utf-8 -*-
"""
v4.4 Step 9: application-oriented validation for the imported KG.

This step does not extract, normalize, review, or import data. It asks a small
set of product-facing questions against Neo4j and records whether the current
graph can support the intended 智学助手 scenarios: lookup, tracing, learning
path, method recommendation, and rule-case based condition judgment.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parents[1]
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_OUT_DIR = SCRIPT_DIR / "中间产物" / "step9_application_validation"
ENV_PATHS = [REPO_ROOT / ".env", MODULE_DIR / ".env"]


DEFAULT_TESTS: list[dict[str, Any]] = [
    # === 节点查找：覆盖学生最常查询的核心知识点 ===
    {
        "id": "node_linear_system",
        "kind": "node_lookup",
        "question": "能否定位核心知识点：线性方程组？",
        "keyword": "线性方程组",
        "exact": True,
        "node_types": ["Concept"],
        "min_results": 1,
        "expected_terms_all": ["线性方程组"],
    },
    {
        "id": "node_determinant",
        "kind": "node_lookup",
        "question": "能否定位核心知识点：n阶行列式？",
        "keyword": "n阶行列式",
        "exact": True,
        "node_types": ["Concept"],
        "min_results": 1,
        "expected_terms_all": ["n阶行列式"],
    },
    {
        "id": "node_matrix_rank",
        "kind": "node_lookup",
        "question": "能否定位核心知识点：矩阵的秩？",
        "keyword": "矩阵的秩",
        "exact": True,
        "node_types": ["Concept"],
        "min_results": 1,
        "expected_terms_all": ["矩阵的秩"],
    },
    {
        "id": "node_solution_count_theorem",
        "kind": "node_lookup",
        "question": "能否定位用于判断线性方程组解的个数的核心定理？",
        "keyword": "线性方程组解的个数判定定理",
        "exact": True,
        "node_types": ["Theorem"],
        "min_results": 1,
        "expected_terms_all": ["线性方程组解的个数判定定理"],
    },
    {
        "id": "node_cramer",
        "kind": "node_lookup",
        "question": "能否定位克莱姆法则相关知识点？",
        "keyword": "克莱姆",
        "node_types": ["Formula", "Theorem"],
        "min_results": 1,
        "expected_terms_any": ["克莱姆", "Cramer"],
    },
    {
        "id": "node_eigenvalue",
        "kind": "node_lookup",
        "question": "能否定位矩阵特征值相关知识点？",
        "keyword": "特征值",
        "node_types": ["Concept", "Theorem", "Method"],
        "min_results": 2,
        "expected_terms_any": ["矩阵的特征值", "线性变换的特征值", "特征值与特征向量求解"],
    },
    # === 邻域追溯：学生不会某知识点时，能否找到邻近支撑知识 ===
    {
        "id": "trace_cramer",
        "kind": "neighborhood",
        "question": "学生不会克莱姆法则时，能否找到线性方程组、行列式、系数行列式、唯一解等邻近支撑知识？",
        "anchor": "克莱姆",
        "anchor_types": ["Formula", "Theorem"],
        "max_depth": 3,
        "min_results": 2,
        "expected_terms_any": ["线性方程组", "行列式", "系数行列式", "唯一解"],
    },
    {
        "id": "trace_matrix_rank",
        "kind": "neighborhood",
        "question": "学生学习矩阵的秩时，能否追溯到行秩、列秩、阶梯形矩阵、子式等支撑概念？",
        "anchor": "矩阵的秩",
        "anchor_types": ["Concept"],
        "max_depth": 2,
        "min_results": 2,
        "expected_terms_any": ["矩阵的行秩", "矩阵的列秩", "阶梯形矩阵", "子式", "满秩矩阵"],
    },
    # === 规则案例：条件判断类问题能否整体返回规则卡片 ===
    {
        "id": "rulecase_linear_system_solvability",
        "kind": "rulecase_by_owner",
        "question": "学生问“线性方程组什么时候有解”时，能否整体返回判定规则卡片？",
        "owner": "线性方程组有解判别定理",
        "owner_exact": True,
        "condition_keywords": ["系数矩阵", "增广矩阵", "秩"],
        "outcome_keywords": ["有解"],
        "min_results": 1,
        "expected_terms_all": ["线性方程组有解判定", "系数矩阵", "增广矩阵", "秩", "有解"],
    },
    {
        "id": "rulecase_linear_system_solution_count",
        "kind": "rulecase_by_owner",
        "question": "学生问“线性方程组什么时候唯一解或无穷多解”时，能否整体返回分情况规则卡片？",
        "owner": "线性方程组解的个数判定定理",
        "owner_exact": True,
        "condition_keywords": ["秩"],
        "outcome_keywords": ["唯一解", "无穷多个解"],
        "min_results": 1,
        "expected_terms_all": ["线性方程组解的个数分情况判定", "秩", "唯一解", "无穷多个解"],
    },
    {
        "id": "rulecase_cramer_unique_solution",
        "kind": "rulecase_by_owner",
        "question": "学生问“克莱姆法则何时给出唯一解”时，能否返回系数行列式不为零的判定卡片？",
        "owner": "n元线性方程组唯一解判定定理",
        "owner_exact": True,
        "condition_keywords": ["系数行列式"],
        "outcome_keywords": ["唯一解"],
        "min_results": 1,
        "expected_terms_all": ["唯一解判定", "系数行列式", "唯一解"],
    },
    {
        "id": "rulecase_no_solution",
        "kind": "rulecase_by_owner",
        "question": "学生问“线性方程组何时无解”时，能否返回矛盾方程判定卡片？",
        "owner": "矩阵消元法解线性方程组",
        "owner_exact": True,
        "condition_keywords": ["阶梯形"],
        "outcome_keywords": ["无解"],
        "min_results": 1,
        "expected_terms_all": ["无解判定", "阶梯形", "无解"],
    },
    {
        "id": "rulecase_bridge_linear_system_rank",
        "kind": "rulecase_bridge",
        "question": "学生问“线性方程组为什么和矩阵的秩有关”时，能否通过 RuleCase 解释二者关系？",
        "source": "线性方程组",
        "bridge_keywords": ["矩阵的秩", "系数矩阵", "增广矩阵", "秩"],
        "min_results": 1,
        "expected_terms_any": ["系数矩阵与增广矩阵的秩相等", "系数矩阵", "增广矩阵", "秩"],
    },
    # === 前置知识追溯：从规则案例条件反推学生可能缺失的知识 ===
    {
        "id": "prerequisite_solution_count_from_rulecase",
        "kind": "prerequisite_from_rulecase",
        "question": "学生不会判断线性方程组解的个数时，能否从 RuleCase 条件追溯可能缺的知识？",
        "anchor": "线性方程组解的个数判定",
        "condition_keywords": ["秩", "有解"],
        "min_results": 2,
        "expected_terms_any": ["系数矩阵", "秩", "有解"],
        "expected_enhanced_terms_any": ["矩阵的秩", "系数矩阵", "增广矩阵"],
    },
    # === 方法推荐：学习某知识点时能否推荐相关方法/公式/定理 ===
    {
        "id": "recommend_matrix_rank_methods",
        "kind": "method_recommendation",
        "question": "学生学习矩阵的秩时，能否推荐相关方法、公式或定理？",
        "anchor": "矩阵的秩",
        "max_depth": 3,
        "min_results": 2,
        "expected_terms_any": ["矩阵秩求解方法", "最高阶非零子式", "阶梯形矩阵"],
    },
    {
        "id": "recommend_determinant_methods",
        "kind": "method_recommendation",
        "question": "学习行列式时，能否推荐相关方法、公式或性质？",
        "anchor": "n阶行列式",
        "max_depth": 2,
        "min_results": 3,
        "expected_terms_any": ["化为上三角形", "公因子提出", "行列式拆成", "两行互换", "按一行或一列展开"],
    },
    {
        "id": "recommend_eigenvalue_methods",
        "kind": "method_recommendation",
        "question": "学习矩阵特征值时，能否推荐特征多项式、特征向量求解方法？",
        "anchor": "矩阵的特征值",
        "max_depth": 2,
        "min_results": 2,
        "expected_terms_any": ["特征多项式", "特征值与特征向量求解方法", "特征子空间"],
    },
    # === 规则结论反查：从结论反查满足条件 ===
    {
        "id": "rule_unique_solution",
        "kind": "rule_outcome",
        "question": "能否回答：什么时候有唯一解？",
        "outcome_keyword": "唯一解",
        "min_results": 1,
        "expected_terms_any": ["系数行列式", "秩", "|A|", "不等于0"],
    },
    {
        "id": "rule_no_solution",
        "kind": "rule_outcome",
        "question": "能否回答：什么时候无解？",
        "outcome_keyword": "无解",
        "min_results": 1,
        "expected_terms_any": ["0=d", "阶梯形", "非零数"],
    },
    {
        "id": "rule_determinant_zero",
        "kind": "rule_outcome",
        "question": "能否回答：哪些条件会得到行列式为零？",
        "outcome_keywords": ["行列式为零"],
        "min_results": 1,
        "expected_terms_any": ["两行相同", "两行成比例"],
    },
    {
        "id": "rule_infinite_solutions",
        "kind": "rule_outcome",
        "question": "能否回答：什么时候线性方程组有无穷多个解？",
        "outcome_keyword": "无穷多个解",
        "min_results": 1,
        "expected_terms_any": ["秩", "系数矩阵", "小于"],
    },
]


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate v4.4 KG with application-facing Neo4j tests.")
    parser.add_argument("--uri", default=load_env_value("NEO4J_URI") or "neo4j://127.0.0.1:7687")
    parser.add_argument("--user", default=load_env_value("NEO4J_USER") or "neo4j")
    parser.add_argument("--password", default=load_env_value("NEO4J_PASSWORD") or "zhang2004")
    parser.add_argument("--database", default=load_env_value("NEO4J_DATABASE") or "neo4j")
    parser.add_argument("--import-batch", default="", help="Optional import_batch filter. Empty means all imported KGNode rows.")
    parser.add_argument("--tests", type=Path, default=None, help="Optional JSON file containing a list of tests.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--limit", type=int, default=20)
    return parser.parse_args()


def load_tests(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return DEFAULT_TESTS
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise ValueError("--tests must point to a JSON list")
    return data


def safe_depth(value: Any, default: int = 3) -> int:
    try:
        depth = int(value)
    except Exception:
        return default
    return max(1, min(depth, 8))


def compact_text(value: Any, limit: int = 180) -> str:
    text = "" if value is None else str(value)
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def markdown_escape(value: Any) -> str:
    return compact_text(value).replace("|", "\\|").replace("\n", " ")


def run_records(session: Any, query: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    result = session.run(query, **params)
    return [dict(record) for record in result]


def node_lookup(session: Any, test: dict[str, Any], import_batch: str, limit: int) -> list[dict[str, Any]]:
    query = """
    MATCH (n:KGNode)
    WHERE ($import_batch = "" OR n.import_batch = $import_batch)
      AND ($node_types = [] OR n.type IN $node_types)
      AND (
        ($exact = true AND (
          n.name = $keyword
          OR any(alias IN coalesce(n.aliases, []) WHERE alias = $keyword)
        ))
        OR
        ($exact = false AND (
          n.name CONTAINS $keyword
          OR any(alias IN coalesce(n.aliases, []) WHERE alias CONTAINS $keyword)
        ))
      )
    RETURN n.name AS name,
           n.type AS type,
           n.chapter AS chapter,
           n.section AS section,
           left(coalesce(n.evidence_span, ""), 240) AS evidence
    ORDER BY CASE WHEN n.name = $keyword THEN 0 ELSE 1 END, n.type, n.name
    LIMIT $limit
    """
    return run_records(session, query, {
        "keyword": test.get("keyword", ""),
        "exact": bool(test.get("exact", False)),
        "node_types": test.get("node_types", []),
        "import_batch": import_batch,
        "limit": int(test.get("limit") or limit),
    })


def neighborhood(session: Any, test: dict[str, Any], import_batch: str, limit: int) -> list[dict[str, Any]]:
    depth = safe_depth(test.get("max_depth"), 3)
    query = f"""
    MATCH (a:KGNode)
    WHERE ($import_batch = "" OR a.import_batch = $import_batch)
      AND ($anchor_types = [] OR a.type IN $anchor_types)
      AND (
        a.name CONTAINS $anchor
        OR any(alias IN coalesce(a.aliases, []) WHERE alias CONTAINS $anchor)
      )
    MATCH p=(a)-[*1..{depth}]-(b:KGNode)
    WHERE ($import_batch = "" OR b.import_batch = $import_batch)
    RETURN a.name AS anchor,
           b.name AS target,
           b.type AS target_type,
           [node IN nodes(p) | coalesce(node.name, "")] AS path_nodes,
           [rel IN relationships(p) | type(rel)] AS rels,
           left(coalesce(head([rel IN relationships(p) WHERE coalesce(rel.evidence_span, "") <> "" | rel.evidence_span]), ""), 240) AS evidence
    ORDER BY length(p), b.type, b.name
    LIMIT $limit
    """
    return run_records(session, query, {
        "anchor": test.get("anchor", ""),
        "anchor_types": test.get("anchor_types", []),
        "import_batch": import_batch,
        "limit": int(test.get("limit") or limit),
    })


def method_recommendation(session: Any, test: dict[str, Any], import_batch: str, limit: int) -> list[dict[str, Any]]:
    depth = safe_depth(test.get("max_depth"), 2)
    query = f"""
    MATCH (a:KGNode)
    WHERE ($import_batch = "" OR a.import_batch = $import_batch)
      AND ($anchor_types = [] OR a.type IN $anchor_types)
      AND a.name CONTAINS $anchor
    MATCH p=(a)-[*1..{depth}]-(m:KGNode)
    WHERE ($import_batch = "" OR m.import_batch = $import_batch)
      AND m.type IN ["Method", "Formula", "Theorem"]
    RETURN DISTINCT a.name AS anchor,
           m.name AS recommended,
           m.type AS recommended_type,
           [rel IN relationships(p) | type(rel)] AS rels,
           [node IN nodes(p) | coalesce(node.name, "")] AS path_nodes,
           left(coalesce(m.evidence_span, ""), 240) AS evidence,
           size([rel IN relationships(p) WHERE type(rel) IN ["USES", "HAS_PROPERTY", "GETS", "DERIVES", "SUPERIOR", "PART_OF", "EQUATIVE"]]) AS semantic_edge_count,
           size([rel IN relationships(p) WHERE type(rel) IN ["HAS_MEMBER", "HAS_ANCHOR"]]) AS group_edge_count,
           length(p) AS path_length,
           CASE WHEN any(keyword IN $expected_terms WHERE m.name CONTAINS keyword OR coalesce(m.evidence_span, "") CONTAINS keyword)
             THEN 0 ELSE 1 END AS expected_term_rank
    ORDER BY expected_term_rank, semantic_edge_count DESC, group_edge_count ASC, path_length, m.type, m.name
    LIMIT $limit
    """
    return run_records(session, query, {
        "anchor": test.get("anchor", ""),
        "anchor_types": test.get("anchor_types", []),
        "expected_terms": [str(term) for term in test.get("expected_terms_any", []) if str(term)],
        "import_batch": import_batch,
        "limit": int(test.get("limit") or limit),
    })


def path_between(session: Any, test: dict[str, Any], import_batch: str, limit: int) -> list[dict[str, Any]]:
    depth = safe_depth(test.get("max_depth"), 5)
    query = f"""
    MATCH (a:KGNode), (b:KGNode)
    WHERE ($import_batch = "" OR a.import_batch = $import_batch)
      AND ($import_batch = "" OR b.import_batch = $import_batch)
      AND ($source_types = [] OR a.type IN $source_types)
      AND ($target_types = [] OR b.type IN $target_types)
      AND (($source_exact = true AND a.name = $source) OR ($source_exact = false AND a.name CONTAINS $source))
      AND (($target_exact = true AND b.name = $target) OR ($target_exact = false AND b.name CONTAINS $target))
      AND a.node_id <> b.node_id
    MATCH p=shortestPath((a)-[*1..{depth}]-(b))
    RETURN a.name AS source,
           b.name AS target,
           [node IN nodes(p) | coalesce(node.name, "")] AS path_nodes,
           [rel IN relationships(p) | type(rel)] AS rels,
           length(p) AS path_length
    ORDER BY path_length, source, target
    LIMIT $limit
    """
    return run_records(session, query, {
        "source": test.get("source", ""),
        "target": test.get("target", ""),
        "source_exact": bool(test.get("source_exact", False)),
        "target_exact": bool(test.get("target_exact", False)),
        "source_types": test.get("source_types", []),
        "target_types": test.get("target_types", []),
        "import_batch": import_batch,
        "limit": int(test.get("limit") or limit),
    })


def rulecase_by_owner(session: Any, test: dict[str, Any], import_batch: str, limit: int) -> list[dict[str, Any]]:
    query = """
    MATCH (owner:KGNode)-[:HAS_RULE_CASE]->(r:RuleCase)
    WHERE ($import_batch = "" OR owner.import_batch = $import_batch)
      AND ($import_batch = "" OR r.import_batch = $import_batch)
      AND (($owner_exact = true AND owner.name = $owner) OR ($owner_exact = false AND owner.name CONTAINS $owner))
    OPTIONAL MATCH (r)-[condition_rel]->(c:ConditionExpression)
    WHERE type(condition_rel) IN ["HAS_CONDITION", "HAS_CONDITION_AND", "HAS_CONDITION_OR"]
    WITH owner, r, collect(DISTINCT c.name) AS conditions
    OPTIONAL MATCH (r)-[:HAS_OUTCOME]->(o:Outcome)
    WITH owner, r, conditions, collect(DISTINCT o.name) AS outcomes
    WITH owner, r, conditions, outcomes,
         coalesce(r.name, "") + " " +
         coalesce(r.applies_to, "") + " " +
         coalesce(r.evidence_span, "") + " " +
         reduce(text = "", item IN conditions | text + " " + coalesce(item, "")) + " " +
         reduce(text = "", item IN outcomes | text + " " + coalesce(item, "")) AS rule_text
    WHERE ($condition_keywords = [] OR any(keyword IN $condition_keywords WHERE rule_text CONTAINS keyword))
      AND ($outcome_keywords = [] OR any(keyword IN $outcome_keywords WHERE rule_text CONTAINS keyword))
    RETURN owner.name AS owner,
           owner.type AS owner_type,
           r.name AS rule_case,
           r.applies_to AS applies_to,
           r.condition_logic AS condition_logic,
           conditions AS conditions,
           outcomes AS outcomes,
           left(coalesce(r.evidence_span, ""), 280) AS evidence
    ORDER BY owner.name, rule_case
    LIMIT $limit
    """
    return run_records(session, query, {
        "owner": test.get("owner", ""),
        "owner_exact": bool(test.get("owner_exact", False)),
        "condition_keywords": [str(keyword) for keyword in test.get("condition_keywords", []) if str(keyword)],
        "outcome_keywords": [str(keyword) for keyword in test.get("outcome_keywords", []) if str(keyword)],
        "import_batch": import_batch,
        "limit": int(test.get("limit") or limit),
    })


def rulecase_bridge(session: Any, test: dict[str, Any], import_batch: str, limit: int) -> list[dict[str, Any]]:
    query = """
    MATCH (owner:KGNode)-[:HAS_RULE_CASE]->(r:RuleCase)
    WHERE ($import_batch = "" OR owner.import_batch = $import_batch)
      AND ($import_batch = "" OR r.import_batch = $import_batch)
      AND (
        owner.name CONTAINS $source
        OR coalesce(r.applies_to, "") CONTAINS $source
        OR coalesce(r.evidence_span, "") CONTAINS $source
      )
    OPTIONAL MATCH (r)-[condition_rel]->(c:ConditionExpression)
    WHERE type(condition_rel) IN ["HAS_CONDITION", "HAS_CONDITION_AND", "HAS_CONDITION_OR"]
    WITH owner, r, collect(DISTINCT c.name) AS conditions
    OPTIONAL MATCH (r)-[:HAS_OUTCOME]->(o:Outcome)
    WITH owner, r, conditions, collect(DISTINCT o.name) AS outcomes
    WITH owner, r, conditions, outcomes,
         coalesce(owner.name, "") + " " +
         coalesce(r.name, "") + " " +
         coalesce(r.applies_to, "") + " " +
         coalesce(r.evidence_span, "") + " " +
         reduce(text = "", item IN conditions | text + " " + coalesce(item, "")) + " " +
         reduce(text = "", item IN outcomes | text + " " + coalesce(item, "")) AS bridge_text
    WHERE any(keyword IN $bridge_keywords WHERE bridge_text CONTAINS keyword)
    RETURN owner.name AS owner,
           owner.type AS owner_type,
           r.name AS rule_case,
           r.condition_logic AS condition_logic,
           r.applies_to AS applies_to,
           conditions AS conditions,
           outcomes AS outcomes,
           [keyword IN $bridge_keywords WHERE bridge_text CONTAINS keyword] AS matched_bridge_keywords,
           left(coalesce(r.evidence_span, ""), 280) AS evidence
    ORDER BY size([keyword IN $bridge_keywords WHERE bridge_text CONTAINS keyword]) DESC, owner.name, rule_case
    LIMIT $limit
    """
    return run_records(session, query, {
        "source": test.get("source", ""),
        "bridge_keywords": [str(keyword) for keyword in test.get("bridge_keywords", []) if str(keyword)],
        "import_batch": import_batch,
        "limit": int(test.get("limit") or limit),
    })


def prerequisite_from_rulecase(session: Any, test: dict[str, Any], import_batch: str, limit: int) -> list[dict[str, Any]]:
    query = """
    MATCH (owner:KGNode)-[:HAS_RULE_CASE]->(r:RuleCase)-[condition_rel]->(c:ConditionExpression)
    WHERE type(condition_rel) IN ["HAS_CONDITION", "HAS_CONDITION_AND", "HAS_CONDITION_OR"]
      AND ($import_batch = "" OR owner.import_batch = $import_batch)
      AND ($import_batch = "" OR r.import_batch = $import_batch)
      AND ($import_batch = "" OR c.import_batch = $import_batch)
      AND (
        owner.name CONTAINS $anchor
        OR r.name CONTAINS $anchor
        OR coalesce(r.applies_to, "") CONTAINS $anchor
      )
      AND ($condition_keywords = [] OR any(keyword IN $condition_keywords WHERE c.name CONTAINS keyword OR coalesce(r.evidence_span, "") CONTAINS keyword))
    OPTIONAL MATCH (c)-[:REFERS_TO]-(mapped_ref:KGNode)
    WHERE ($import_batch = "" OR mapped_ref.import_batch = $import_batch)
    WITH owner, r, c, collect(DISTINCT mapped_ref.name) AS ref_nodes
    OPTIONAL MATCH (mapped_kw:KGNode)
    WHERE ($import_batch = "" OR mapped_kw.import_batch = $import_batch)
      AND mapped_kw.type IN ["Concept", "Theorem", "Formula", "Method"]
      AND (
        $enhanced_terms = []
        OR any(term IN $enhanced_terms WHERE
          c.name CONTAINS term
          OR mapped_kw.name = term
          OR mapped_kw.name CONTAINS term
          OR c.name CONTAINS mapped_kw.name
        )
      )
      AND (
        c.name CONTAINS mapped_kw.name
        OR any(term IN $enhanced_terms WHERE mapped_kw.name = term OR mapped_kw.name CONTAINS term)
      )
    WITH owner, r, c, ref_nodes, collect(DISTINCT mapped_kw.name) AS keyword_nodes
    WITH owner, r, c, ref_nodes + keyword_nodes AS raw_mapped_nodes
    WITH owner, r, c, [name IN raw_mapped_nodes WHERE name IS NOT NULL AND name <> ""] AS mapped_nodes
    RETURN owner.name AS owner,
           r.name AS rule_case,
           r.condition_logic AS condition_logic,
           c.name AS prerequisite_condition,
           mapped_nodes AS mapped_core_nodes,
           left(coalesce(r.evidence_span, ""), 260) AS evidence,
           CASE WHEN size(mapped_nodes) > 0 THEN "enhanced" ELSE "basic" END AS trace_level
    ORDER BY trace_level DESC, owner, rule_case, prerequisite_condition
    LIMIT $limit
    """
    return run_records(session, query, {
        "anchor": test.get("anchor", ""),
        "condition_keywords": [str(keyword) for keyword in test.get("condition_keywords", []) if str(keyword)],
        "enhanced_terms": [str(term) for term in test.get("expected_enhanced_terms_any", []) if str(term)],
        "import_batch": import_batch,
        "limit": int(test.get("limit") or limit),
    })


def rule_outcome(session: Any, test: dict[str, Any], import_batch: str, limit: int) -> list[dict[str, Any]]:
    query = """
    MATCH (r:RuleCase)-[:HAS_OUTCOME]->(o:Outcome)
    WHERE ($import_batch = "" OR r.import_batch = $import_batch)
      AND ($import_batch = "" OR o.import_batch = $import_batch)
      AND any(keyword IN $outcome_keywords WHERE o.name CONTAINS keyword OR r.name CONTAINS keyword)
    OPTIONAL MATCH (owner:KGNode)-[:HAS_RULE_CASE]->(r)
    OPTIONAL MATCH (r)-[condition_rel]->(c:ConditionExpression)
    WHERE type(condition_rel) IN ["HAS_CONDITION", "HAS_CONDITION_AND", "HAS_CONDITION_OR"]
    RETURN r.name AS rule_case,
           owner.name AS owner,
           r.applies_to AS applies_to,
           r.condition_logic AS condition_logic,
           collect(DISTINCT c.name) AS conditions,
           collect(DISTINCT o.name) AS outcomes,
           left(coalesce(r.evidence_span, ""), 260) AS evidence
    ORDER BY owner, rule_case
    LIMIT $limit
    """
    outcome_keywords = test.get("outcome_keywords") or [test.get("outcome_keyword", "")]
    return run_records(session, query, {
        "outcome_keywords": [str(keyword) for keyword in outcome_keywords if str(keyword)],
        "import_batch": import_batch,
        "limit": int(test.get("limit") or limit),
    })


def run_test(session: Any, test: dict[str, Any], import_batch: str, limit: int) -> dict[str, Any]:
    handlers = {
        "node_lookup": node_lookup,
        "neighborhood": neighborhood,
        "method_recommendation": method_recommendation,
        "path_between": path_between,
        "rulecase_by_owner": rulecase_by_owner,
        "rulecase_bridge": rulecase_bridge,
        "prerequisite_from_rulecase": prerequisite_from_rulecase,
        "rule_outcome": rule_outcome,
    }
    kind = str(test.get("kind") or "")
    if kind not in handlers:
        raise ValueError(f"Unknown test kind: {kind}")
    rows = handlers[kind](session, test, import_batch, limit)
    return evaluate_test(test, rows)


def evaluate_test(test: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    min_results = int(test.get("min_results") or 1)
    result_text = json_text(rows)
    missing_all = [term for term in test.get("expected_terms_all", []) if str(term) not in result_text]
    any_terms = [str(term) for term in test.get("expected_terms_any", [])]
    matched_any = [term for term in any_terms if term in result_text]
    enhanced_terms = [str(term) for term in test.get("expected_enhanced_terms_any", [])]
    if test.get("kind") == "prerequisite_from_rulecase":
        mapped_text = json_text([row.get("mapped_core_nodes", []) for row in rows])
        matched_enhanced = [term for term in enhanced_terms if term in mapped_text]
    else:
        matched_enhanced = [term for term in enhanced_terms if term in result_text]

    enough = len(rows) >= min_results
    all_ok = not missing_all
    any_ok = not any_terms or bool(matched_any)

    enhanced_required = bool(enhanced_terms)
    enhanced_ok = not enhanced_required or bool(matched_enhanced)

    if enough and all_ok and any_ok and enhanced_ok:
        status = "pass"
    elif enough and all_ok and any_ok and enhanced_required and not enhanced_ok:
        status = "partial"
    elif rows:
        status = "partial"
    else:
        status = "fail"

    reasons: list[str] = []
    if not enough:
        reasons.append(f"结果数不足：期望至少 {min_results}，实际 {len(rows)}")
    if missing_all:
        reasons.append("缺少必要词：" + "、".join(missing_all))
    if any_terms and not matched_any:
        reasons.append("未命中任一关键提示词：" + "、".join(any_terms))
    if enhanced_terms and not matched_enhanced:
        reasons.append("基础结果可用，但未命中增强映射提示词：" + "、".join(enhanced_terms))
    if not reasons:
        if enhanced_terms:
            reasons.append("命中数量、关键提示词和增强映射提示词均满足当前验收条件")
        else:
            reasons.append("命中数量和关键提示词均满足当前验收条件")

    return {
        "id": test.get("id", ""),
        "kind": test.get("kind", ""),
        "question": test.get("question", ""),
        "status": status,
        "result_count": len(rows),
        "matched_any_terms": matched_any,
        "matched_enhanced_terms": matched_enhanced,
        "missing_all_terms": missing_all,
        "reasons": reasons,
        "rows": rows,
        "test": test,
    }


def fetch_graph_summary(session: Any, import_batch: str) -> dict[str, Any]:
    params = {"import_batch": import_batch}
    node_rows = run_records(session, """
    MATCH (n:KGNode)
    WHERE ($import_batch = "" OR n.import_batch = $import_batch)
    RETURN n.type AS type, count(n) AS count
    ORDER BY type
    """, params)
    edge_rows = run_records(session, """
    MATCH ()-[r]->()
    WHERE ($import_batch = "" OR r.import_batch = $import_batch)
    RETURN type(r) AS type, count(r) AS count
    ORDER BY type
    """, params)
    isolated = run_records(session, """
    MATCH (n:KGNode)
    WHERE ($import_batch = "" OR n.import_batch = $import_batch)
      AND NOT (n)--()
    RETURN n.type AS type, count(n) AS count
    ORDER BY type
    """, params)
    semantic_isolated = run_records(session, """
    MATCH (n:KGNode)
    WHERE ($import_batch = "" OR n.import_batch = $import_batch)
      AND NOT (n)-[:APPLIES_TO|DERIVES|GETS|HAS_CONDITION|HAS_CONDITION_AND|HAS_OUTCOME|HAS_PROPERTY|HAS_RULE_CASE|REFERS_TO|SUPERIOR|USES]-()
    RETURN n.type AS type, count(n) AS count
    ORDER BY type
    """, params)
    core_semantic_isolated = run_records(session, """
    MATCH (n:KGNode)
    WHERE ($import_batch = "" OR n.import_batch = $import_batch)
      AND n.type IN ["Concept", "Theorem", "Formula", "Method"]
      AND NOT (n)-[:APPLIES_TO|DERIVES|GETS|HAS_CONDITION|HAS_CONDITION_AND|HAS_OUTCOME|HAS_PROPERTY|HAS_RULE_CASE|REFERS_TO|SUPERIOR|USES]-()
    RETURN n.type AS type, count(n) AS count
    ORDER BY type
    """, params)
    return {
        "node_types": node_rows,
        "edge_types": edge_rows,
        "isolated_node_types": isolated,
        "semantic_isolated_node_types": semantic_isolated,
        "core_semantic_isolated_node_types": core_semantic_isolated,
        "node_total": sum(row["count"] for row in node_rows),
        "edge_total": sum(row["count"] for row in edge_rows),
        "isolated_total": sum(row["count"] for row in isolated),
        "semantic_isolated_total": sum(row["count"] for row in semantic_isolated),
        "core_semantic_isolated_total": sum(row["count"] for row in core_semantic_isolated),
    }


def write_outputs(out_dir: Path, results: list[dict[str, Any]], summary: dict[str, Any], args: argparse.Namespace) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path = out_dir / "step9_application_validation_results.json"
    report_path = out_dir / "step9_application_validation_report.md"
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "database": args.database,
        "import_batch": args.import_batch,
        "summary": summary,
        "results": results,
    }
    result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(build_report(payload), encoding="utf-8")


def build_report(payload: dict[str, Any]) -> str:
    results = payload["results"]
    status_counts = Counter(row["status"] for row in results)
    summary = payload["summary"]
    lines = [
        "# v4.4 Step 9 应用验证报告",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- database: `{payload['database']}`",
        f"- import_batch: `{payload['import_batch'] or '(all KGNode)'}`",
        f"- graph_nodes: {summary['node_total']}",
        f"- graph_edges: {summary['edge_total']}",
        f"- structural_isolated_nodes: {summary['isolated_total']}",
        f"- semantic_isolated_nodes_ignoring_groups: {summary['semantic_isolated_total']}",
        f"- core_semantic_isolated_nodes_ignoring_groups: {summary['core_semantic_isolated_total']}",
        f"- tests: {len(results)}",
        f"- pass / partial / fail: {status_counts.get('pass', 0)} / {status_counts.get('partial', 0)} / {status_counts.get('fail', 0)}",
        "",
        "## 图谱结构概览",
        "",
        "### 节点类型",
    ]
    for row in summary["node_types"]:
        lines.append(f"- {row['type']}: {row['count']}")
    lines.extend(["", "### 关系类型"])
    for row in summary["edge_types"]:
        lines.append(f"- {row['type']}: {row['count']}")
    lines.extend(["", "### 孤立节点"])
    if summary["isolated_node_types"]:
        for row in summary["isolated_node_types"]:
            lines.append(f"- {row['type']}: {row['count']}")
    else:
        lines.append("- 0")

    lines.extend(["", "### 忽略知识组边后的语义孤立节点"])
    lines.append("- 口径：不把 `HAS_MEMBER`、`HAS_ANCHOR` 计为数学语义关系。")
    if summary["semantic_isolated_node_types"]:
        for row in summary["semantic_isolated_node_types"]:
            lines.append(f"- {row['type']}: {row['count']}")
    else:
        lines.append("- 0")

    lines.extend(["", "### 核心知识点语义孤立节点"])
    lines.append("- 口径：只统计 Concept、Theorem、Formula、Method，且忽略知识组边。")
    if summary["core_semantic_isolated_node_types"]:
        for row in summary["core_semantic_isolated_node_types"]:
            lines.append(f"- {row['type']}: {row['count']}")
    else:
        lines.append("- 0")

    lines.extend([
        "",
        "## 测试结果总表",
        "",
        "| ID | 任务 | 结果 | 命中数 | 判断依据 |",
        "|---|---|---:|---:|---|",
    ])
    for result in results:
        lines.append(
            f"| {markdown_escape(result['id'])} | {markdown_escape(result['question'])} | "
            f"{result['status']} | {result['result_count']} | {markdown_escape('; '.join(result['reasons']))} |"
        )

    lines.extend(["", "## 逐项结果"])
    for result in results:
        lines.extend([
            "",
            f"### {result['id']}：{result['status']}",
            "",
            f"- 问题：{result['question']}",
            f"- 类型：`{result['kind']}`",
            f"- 命中数：{result['result_count']}",
            f"- 判断依据：{'；'.join(result['reasons'])}",
        ])
        rows = result["rows"][:8]
        if not rows:
            lines.append("- 返回：无")
            continue
        lines.extend(["", "| 返回摘要 |", "|---|"])
        for row in rows:
            lines.append(f"| {markdown_escape(row)} |")

    lines.extend([
        "",
        "## 解释原则",
        "",
        "- pass：结果数量达到最低要求，并命中预设关键提示词。",
        "- partial：能返回结果，但数量或关键提示词不足，需要人工判断是否可接受。",
        "- fail：没有返回结果，说明当前图谱不能支撑该应用问题。",
        "- Step 9 只验证应用可用性，不反向修改图谱；修正应回到抽取、关系定义或审核环节。",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    tests = load_tests(args.tests)
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    try:
        driver.verify_connectivity()
        # Bolt 6 在显式指定默认数据库时会触发路由表查找失败；
        # 当 database 为空或等于默认数据库时传 None，让 driver 走默认数据库。
        session_db = args.database if args.database and args.database not in {"neo4j", "default"} else None
        with driver.session(database=session_db) as session:
            summary = fetch_graph_summary(session, args.import_batch)
            results = [run_test(session, test, args.import_batch, args.limit) for test in tests]
    finally:
        driver.close()

    write_outputs(args.out_dir, results, summary, args)
    counts = Counter(row["status"] for row in results)
    print(f"[OK] Step 9 report -> {args.out_dir / 'step9_application_validation_report.md'}")
    print(f"[OK] Step 9 results -> {args.out_dir / 'step9_application_validation_results.json'}")
    print(json.dumps({
        "tests": len(results),
        "pass": counts.get("pass", 0),
        "partial": counts.get("partial", 0),
        "fail": counts.get("fail", 0),
        "graph_nodes": summary["node_total"],
        "graph_edges": summary["edge_total"],
        "structural_isolated_nodes": summary["isolated_total"],
        "semantic_isolated_nodes_ignoring_groups": summary["semantic_isolated_total"],
        "core_semantic_isolated_nodes_ignoring_groups": summary["core_semantic_isolated_total"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
