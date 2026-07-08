"""
v4.4 Step 5B: Aggr semantic aggregation candidate generation.

This step proposes possible node aggregation decisions after Step 5A. It does
not merge nodes, migrate edges, or modify the main graph candidates. Every
candidate is written as review-only evidence for a later explicit decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DIR = SCRIPT_DIR / "中间产物"
DEFAULT_MAIN_NODES = DEFAULT_DIR / "kg_main_nodes.jsonl"
DEFAULT_REVIEW_NODES = DEFAULT_DIR / "step5_review_nodes.jsonl"
DEFAULT_MAIN_EDGES = DEFAULT_DIR / "kg_main_edges.jsonl"
DEFAULT_REVIEW_EDGES = DEFAULT_DIR / "step5_review_edges.jsonl"
DEFAULT_OUT = DEFAULT_DIR / "step5b_aggr_candidates.jsonl"
DEFAULT_REPORT = DEFAULT_DIR / "step5b_aggr_report.md"

AGGREGATABLE_TYPES = {"Concept", "Method", "Formula", "Theorem", "ProblemClass"}
BLOCKING_EDGE_TYPES = {"SUPERIOR", "PART_OF"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate v4.4 Step 5B Aggr merge candidates.")
    parser.add_argument("--main-nodes", type=Path, default=DEFAULT_MAIN_NODES)
    parser.add_argument("--review-nodes", type=Path, default=DEFAULT_REVIEW_NODES)
    parser.add_argument("--main-edges", type=Path, default=DEFAULT_MAIN_EDGES)
    parser.add_argument("--review-edges", type=Path, default=DEFAULT_REVIEW_EDGES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-name-sim", type=float, default=0.72)
    parser.add_argument("--min-context-sim", type=float, default=0.35)
    parser.add_argument("--min-role-sim", type=float, default=0.45)
    parser.add_argument("--min-score", type=float, default=0.68)
    parser.add_argument("--max-candidates", type=int, default=1000)
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


def normalize_text(text: Any) -> str:
    value = str(text or "").lower()
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[，。；：、“”‘’（）()\[\]{}<>《》,.;:!?！？]", "", value)
    return value


def char_ngrams(text: str, n: int = 2) -> set[str]:
    text = normalize_text(text)
    if not text:
        return set()
    if len(text) <= n:
        return {text}
    return {text[index : index + n] for index in range(len(text) - n + 1)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cosine(counter_a: Counter[str], counter_b: Counter[str]) -> float:
    if not counter_a or not counter_b:
        return 0.0
    common = set(counter_a) & set(counter_b)
    dot = sum(counter_a[key] * counter_b[key] for key in common)
    norm_a = math.sqrt(sum(value * value for value in counter_a.values()))
    norm_b = math.sqrt(sum(value * value for value in counter_b.values()))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def text_counter(text: Any) -> Counter[str]:
    grams = char_ngrams(str(text or ""), 2)
    return Counter(grams)


def aliases_text(node: dict[str, Any]) -> str:
    aliases = node.get("aliases") if isinstance(node.get("aliases"), list) else []
    return " ".join(str(alias) for alias in aliases if alias)


def node_context_text(node: dict[str, Any]) -> str:
    fields = [
        node.get("name", ""),
        aliases_text(node),
        node.get("definition", ""),
        node.get("description", ""),
        node.get("evidence_span", ""),
        " ".join(str(item) for item in node.get("attributes", []) or []),
        " ".join(str(item) for item in node.get("state_notes", []) or []),
    ]
    return " ".join(str(field) for field in fields if field)


def name_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    names_a = [str(a.get("name") or ""), *[str(alias) for alias in (a.get("aliases") or [])]]
    names_b = [str(b.get("name") or ""), *[str(alias) for alias in (b.get("aliases") or [])]]
    best = 0.0
    for name_a in names_a:
        for name_b in names_b:
            if not name_a or not name_b:
                continue
            norm_a = normalize_text(name_a)
            norm_b = normalize_text(name_b)
            if norm_a == norm_b:
                return 1.0
            containment = 0.0
            if norm_a and norm_b and (norm_a in norm_b or norm_b in norm_a):
                containment = min(len(norm_a), len(norm_b)) / max(len(norm_a), len(norm_b))
            best = max(best, jaccard(char_ngrams(name_a), char_ngrams(name_b)), containment)
    return best


def role_signature(node_id: str, edges: list[dict[str, Any]]) -> Counter[str]:
    role = Counter()
    for edge in edges:
        edge_type = str(edge.get("type") or "")
        if str(edge.get("source_node_id") or "") == node_id:
            role[f"out:{edge_type}:{edge.get('target_type', '')}"] += 1
        if str(edge.get("target_node_id") or "") == node_id:
            role[f"in:{edge_type}:{edge.get('source_type', '')}"] += 1
    return role


def has_blocking_relation(a_id: str, b_id: str, edges: list[dict[str, Any]]) -> bool:
    for edge in edges:
        if str(edge.get("type") or "") not in BLOCKING_EDGE_TYPES:
            continue
        source = str(edge.get("source_node_id") or "")
        target = str(edge.get("target_node_id") or "")
        if {source, target} == {a_id, b_id}:
            return True
    return False


def choose_main_node(a: dict[str, Any], b: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], str]:
    def richness(node: dict[str, Any]) -> tuple[int, int, int]:
        text_len = len(str(node.get("definition") or "")) + len(str(node.get("description") or "")) + len(str(node.get("evidence_span") or ""))
        alias_len = len(node.get("aliases") or [])
        accepted = 1 if node.get("review_status") == "auto_accept" or node.get("step5_status") == "main" else 0
        return (accepted, text_len, alias_len)

    if richness(a) >= richness(b):
        return a, b, "主实体选择依据：节点 A 已准入或描述信息更完整。"
    return b, a, "主实体选择依据：节点 B 已准入或描述信息更完整。"


def candidate_reason(name_sim: float, context_sim: float, role_sim: float) -> str:
    return (
        f"名称相似度={name_sim:.2f}，上下文相似度={context_sim:.2f}，"
        f"局部角色相似度={role_sim:.2f}；仅作为 Aggr 聚合候选，需 Step 7/人工确认。"
    )


def make_candidate(a: dict[str, Any], b: dict[str, Any], edges: list[dict[str, Any]], score: float, name_sim: float, context_sim: float, role_sim: float) -> dict[str, Any]:
    main, merge, main_reason = choose_main_node(a, b)
    candidate_id = stable_id("aggr", [str(main.get("node_id") or ""), str(merge.get("node_id") or ""), str(score)])
    return {
        "candidate_id": candidate_id,
        "item_kind": "merge_candidate",
        "merge_type": "alias_or_entity_merge",
        "main_node_id": main.get("node_id", ""),
        "main_name": main.get("name", ""),
        "main_type": main.get("type", ""),
        "merge_node_id": merge.get("node_id", ""),
        "merge_name": merge.get("name", ""),
        "merge_type_name": merge.get("type", ""),
        "name_similarity": round(name_sim, 4),
        "context_similarity": round(context_sim, 4),
        "role_similarity": round(role_sim, 4),
        "score": round(score, 4),
        "review_status": "review",
        "review_reason": candidate_reason(name_sim, context_sim, role_sim),
        "aggregation_policy": "review_only_no_auto_merge",
        "proposed_actions": [
            "保留主实体",
            "将被聚合实体名称加入 aliases",
            "合并定义、描述、来源和 evidence",
            "复核通过后再迁移被聚合实体的关系",
            "被聚合实体标记为 merged，不能物理删除",
        ],
        "blocking_relation_checked": not has_blocking_relation(str(a.get("node_id") or ""), str(b.get("node_id") or ""), edges),
        "main_selection_reason": main_reason,
        "source_node": {
            "node_id": a.get("node_id", ""),
            "name": a.get("name", ""),
            "type": a.get("type", ""),
            "definition": a.get("definition", ""),
            "description": a.get("description", ""),
            "section_node_id": a.get("section_node_id", ""),
        },
        "target_node": {
            "node_id": b.get("node_id", ""),
            "name": b.get("name", ""),
            "type": b.get("type", ""),
            "definition": b.get("definition", ""),
            "description": b.get("description", ""),
            "section_node_id": b.get("section_node_id", ""),
        },
        "generated_at": now_iso(),
    }


def generate_candidates(nodes: list[dict[str, Any]], edges: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    usable = [
        node for node in nodes
        if node.get("type") in AGGREGATABLE_TYPES and node.get("node_id") and node.get("name")
    ]
    role_by_id = {str(node.get("node_id")): role_signature(str(node.get("node_id")), edges) for node in usable}
    candidates: list[dict[str, Any]] = []

    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in usable:
        by_type[str(node.get("type") or "")].append(node)

    for same_type_nodes in by_type.values():
        for i, a in enumerate(same_type_nodes):
            for b in same_type_nodes[i + 1:]:
                a_id = str(a.get("node_id") or "")
                b_id = str(b.get("node_id") or "")
                if a_id == b_id or has_blocking_relation(a_id, b_id, edges):
                    continue
                n_sim = name_similarity(a, b)
                if n_sim < args.min_name_sim:
                    continue
                c_sim = cosine(text_counter(node_context_text(a)), text_counter(node_context_text(b)))
                if c_sim < args.min_context_sim:
                    continue
                r_sim = cosine(role_by_id.get(a_id, Counter()), role_by_id.get(b_id, Counter()))
                if not role_by_id.get(a_id) and not role_by_id.get(b_id):
                    r_sim = 0.5
                if r_sim < args.min_role_sim:
                    continue
                score = 0.45 * n_sim + 0.35 * c_sim + 0.20 * r_sim
                if score < args.min_score:
                    continue
                candidates.append(make_candidate(a, b, edges, score, n_sim, c_sim, r_sim))

    candidates.sort(key=lambda row: (-float(row.get("score", 0.0)), row.get("main_name", ""), row.get("merge_name", "")))
    if args.max_candidates > 0:
        candidates = candidates[: args.max_candidates]
    return candidates


def write_report(path: Path, candidates: list[dict[str, Any]]) -> None:
    type_counts = Counter(str(row.get("main_type") or "") for row in candidates)
    lines = [
        "# v4.4 Step 5B Aggr Report",
        "",
        f"- merge candidates: {len(candidates)}",
        "- policy: review_only_no_auto_merge",
        "",
        "## Candidate Types",
    ]
    if type_counts:
        for key, value in sorted(type_counts.items()):
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")
    lines.extend(["", "## Top Candidates"])
    for index, row in enumerate(candidates[:30], start=1):
        lines.append(
            f"{index}. {row.get('main_name')} <- {row.get('merge_name')} "
            f"score={row.get('score')} name={row.get('name_similarity')} "
            f"context={row.get('context_similarity')} role={row.get('role_similarity')}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    nodes = [*read_jsonl(args.main_nodes, required=False), *read_jsonl(args.review_nodes, required=False)]
    edges = [*read_jsonl(args.main_edges, required=False), *read_jsonl(args.review_edges, required=False)]
    candidates = generate_candidates(nodes, edges, args)
    write_jsonl(args.output, candidates)
    write_report(args.report, candidates)
    print(f"[OK] aggr candidates -> {args.output}")
    print(f"[OK] report -> {args.report}")
    print(f"[INFO] candidates={len(candidates)}")


if __name__ == "__main__":
    main()
