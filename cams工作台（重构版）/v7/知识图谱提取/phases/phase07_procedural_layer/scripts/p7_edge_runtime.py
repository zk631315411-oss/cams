from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable


EDGE_RUNTIME_POLICIES = {
    "PRECEDES": {
        "storage_direction": "forward",
        "render_direction": "forward",
        "reasoning_traversal": "forward_only",
        "causal": False,
        "temporal": True,
    },
    "REFERENCES": {
        "storage_direction": "process_to_auxiliary",
        "render_direction": "auxiliary_to_process",
        "reasoning_traversal": "bidirectional",
        "causal": False,
        "temporal": False,
    },
    "PRODUCES": {
        "storage_direction": "forward",
        "render_direction": "forward",
        "reasoning_traversal": "forward_only",
        "causal": True,
        "temporal": False,
    },
    "DECIDES": {
        "storage_direction": "forward",
        "render_direction": "forward",
        "reasoning_traversal": "forward_only_with_condition",
        "causal": False,
        "temporal": False,
    },
    "FEEDBACK": {
        "storage_direction": "forward",
        "render_direction": "forward",
        "reasoning_traversal": "forward_only",
        "causal": False,
        "temporal": False,
    },
}


LEGACY_NODE_ROLES = {
    "start": "entry",
    "trigger": "entry",
    "action": "process",
    "decision": "process",
    "output": "exit",
    "end": "exit",
    "input": "auxiliary",
    "standard": "auxiliary",
}


REFERENCE_REVERSE_READINGS = {
    "clue_supports_identification": "作为识别线索",
    "standard_constrains_action": "作为判定标准或规范依据",
    "standard_transmits_requirement": "作为上位要求",
    "component_assembles_product": "作为组成要素",
    "parallel_alternative_no_sequence": "作为并列参照要素",
}


def node_role(node: dict[str, Any]) -> str:
    category = node.get("node_category")
    if category in {"entry", "process", "exit", "auxiliary"}:
        return str(category)
    node_type = str(node.get("node_type") or "")
    if node_type in LEGACY_NODE_ROLES:
        return LEGACY_NODE_ROLES[node_type]
    if node_type.startswith("E"):
        return "entry"
    if node_type.startswith("P"):
        return "process"
    if node_type.startswith("X"):
        return "exit"
    return "auxiliary"


def node_render_kind(node: dict[str, Any]) -> str:
    node_type = str(node.get("node_type") or "")
    if node_type in LEGACY_NODE_ROLES:
        return node_type
    role = node_role(node)
    if role == "entry":
        return "trigger"
    if role == "process":
        return "decision" if node_type == "P3_branch_routing" else "action"
    if role == "exit":
        return "end" if node_type == "X6_termination" else "output"
    return "standard" if node_type == "standard" else "input"


def render_edge_endpoints(edge: dict[str, Any]) -> tuple[str | None, str | None]:
    if edge.get("edge_type") == "REFERENCES":
        return edge.get("target"), edge.get("source")
    return edge.get("source"), edge.get("target")


def reference_reverse_reading(edge: dict[str, Any], auxiliary_node: dict[str, Any] | None) -> str:
    relation_type = edge.get("relation_type")
    if relation_type in REFERENCE_REVERSE_READINGS:
        return REFERENCE_REVERSE_READINGS[relation_type]
    if (auxiliary_node or {}).get("node_type") == "standard":
        return "作为判定标准或规范依据"
    return "作为输入或线索"


def render_edge_label(edge: dict[str, Any], nodes_by_id: dict[str, dict[str, Any]]) -> str:
    if edge.get("edge_type") == "REFERENCES":
        parts = [reference_reverse_reading(edge, nodes_by_id.get(edge.get("target")))]
    else:
        parts = [str(edge.get("edge_type") or "")]
    if edge.get("condition"):
        parts.append(str(edge["condition"]))
    if edge.get("review_status") == "needs_review":
        parts.append("review")
    return " / ".join(part for part in parts if part)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def section_summary_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("manifests", "results", "sections"):
        value = payload.get(key)
        if isinstance(value, list) and any(isinstance(row, dict) for row in value):
            return [row for row in value if isinstance(row, dict)]
    return [
        {"section_id": section_id, **row}
        for section_id, row in payload.items()
        if isinstance(row, dict) and (row.get("section_id") or str(section_id).startswith("CH"))
    ]


def index_edge_reviews(rows: Iterable[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("card_id") or ""), str(row.get("edge_id") or "")): row
        for row in rows
        if row.get("card_id") and row.get("edge_id")
    }


def edge_is_eligible(review: dict[str, Any] | None, mode: str) -> bool:
    if not review:
        return False
    status = review.get("review_status")
    if mode == "final":
        return status == "accepted" and review.get("answer_eligible") is True
    if mode == "retrieval":
        return status in {"accepted", "pending"} and review.get("retrieval_eligible") is True
    raise ValueError(f"Unknown proof mode: {mode}")


def edge_review_matches(edge: dict[str, Any], review: dict[str, Any] | None) -> bool:
    if not review:
        return False
    snapshot = review.get("source_edge_snapshot")
    if not isinstance(snapshot, dict):
        return False
    for field in ("edge_id", "edge_type", "source", "target"):
        if snapshot.get(field) != edge.get(field):
            return False
    for field in ("condition", "relation_type", "qualifier", "modality", "derivation"):
        if field in snapshot and snapshot.get(field) != edge.get(field):
            return False
    if "evidence_unit_ids" in snapshot:
        if sorted(snapshot.get("evidence_unit_ids") or []) != sorted(edge.get("evidence_unit_ids") or []):
            return False
    return True


def _proof_reading(
    edge: dict[str, Any],
    nodes_by_id: dict[str, dict[str, Any]],
    traversal_direction: str,
) -> str:
    stored_source = nodes_by_id.get(edge.get("source"), {})
    stored_target = nodes_by_id.get(edge.get("target"), {})
    source_label = str(stored_source.get("label") or edge.get("source") or "")
    target_label = str(stored_target.get("label") or edge.get("target") or "")
    edge_type = edge.get("edge_type")
    if edge_type == "REFERENCES":
        reading = reference_reverse_reading(edge, stored_target)
        if traversal_direction == "reverse":
            return f"{target_label}{reading}，供{source_label}参照"
        return f"{source_label}参照{target_label}"
    if edge_type == "PRECEDES":
        return f"{source_label}先于或进入{target_label}"
    if edge_type == "PRODUCES":
        return f"{source_label}产生{target_label}"
    if edge_type == "DECIDES":
        return f"{source_label}在“{edge.get('condition')}”条件下进入{target_label}"
    if edge_type == "FEEDBACK":
        return f"{source_label}反馈至{target_label}"
    return f"{source_label}连接到{target_label}"


def _make_proof_step(
    card: dict[str, Any],
    edge: dict[str, Any],
    review: dict[str, Any],
    nodes_by_id: dict[str, dict[str, Any]],
    traversal_direction: str,
) -> dict[str, Any]:
    reverse = traversal_direction == "reverse"
    source = edge.get("target") if reverse else edge.get("source")
    target = edge.get("source") if reverse else edge.get("target")
    policy = EDGE_RUNTIME_POLICIES.get(str(edge.get("edge_type") or ""), {})
    return {
        "card_id": card.get("card_id"),
        "edge_id": edge.get("edge_id"),
        "edge_type": edge.get("edge_type"),
        "source": source,
        "target": target,
        "stored_source": edge.get("source"),
        "stored_target": edge.get("target"),
        "traversal_direction": traversal_direction,
        "proof_reading": _proof_reading(edge, nodes_by_id, traversal_direction),
        "relation_type": edge.get("relation_type"),
        "condition": edge.get("condition"),
        "review_status": review.get("review_status"),
        "answer_eligible": review.get("answer_eligible") is True,
        "retrieval_eligible": review.get("retrieval_eligible") is True,
        "causal": bool(policy.get("causal", False)),
        "temporal": bool(policy.get("temporal", False)),
    }


def build_proof_adjacency(
    card: dict[str, Any],
    edge_reviews: Iterable[dict[str, Any]],
    mode: str = "final",
) -> dict[str, list[dict[str, Any]]]:
    nodes_by_id = {
        str(node.get("node_id")): node
        for node in card.get("flow_nodes") or []
        if node.get("node_id")
    }
    reviews_by_edge = index_edge_reviews(edge_reviews)
    card_id = str(card.get("card_id") or "")
    adjacency: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in card.get("flow_edges") or []:
        review = reviews_by_edge.get((card_id, str(edge.get("edge_id") or "")))
        if not edge_review_matches(edge, review) or not edge_is_eligible(review, mode):
            continue
        forward = _make_proof_step(card, edge, review, nodes_by_id, "forward")
        adjacency[str(forward["source"])].append(forward)
        if edge.get("edge_type") == "REFERENCES":
            reverse = _make_proof_step(card, edge, review, nodes_by_id, "reverse")
            adjacency[str(reverse["source"])].append(reverse)
    return dict(adjacency)


def find_proof_paths(
    adjacency: dict[str, list[dict[str, Any]]],
    start_node_id: str,
    target_node_id: str,
    satisfied_conditions: Iterable[str] = (),
    max_hops: int = 8,
    max_paths: int = 20,
    require_result_edge: bool = False,
) -> list[list[dict[str, Any]]]:
    conditions = {str(condition).strip() for condition in satisfied_conditions}
    queue: deque[tuple[str, list[dict[str, Any]], set[str]]] = deque(
        [(start_node_id, [], {start_node_id})]
    )
    paths: list[list[dict[str, Any]]] = []
    while queue and len(paths) < max_paths:
        node_id, path, visited = queue.popleft()
        if len(path) >= max_hops:
            continue
        for step in adjacency.get(node_id, []):
            condition = str(step.get("condition") or "").strip()
            if step.get("edge_type") == "DECIDES" and not condition:
                continue
            if condition and condition not in conditions:
                continue
            next_node = str(step.get("target") or "")
            if not next_node or next_node in visited:
                continue
            next_path = [*path, step]
            if next_node == target_node_id:
                if not require_result_edge or step.get("edge_type") in {"PRODUCES", "DECIDES"}:
                    paths.append(next_path)
                continue
            queue.append((next_node, next_path, {*visited, next_node}))
    return paths


def collect_cards(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("cards"), list):
        return payload["cards"]
    if isinstance(payload, dict) and payload.get("card_id"):
        return [payload]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict) and row.get("card_id")]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Find reviewed card-local P7 proof paths.")
    parser.add_argument("--cards", required=True, help="P7C cards.raw.json")
    parser.add_argument("--edge-reviews", required=True, help="P7D p7d_edge_reviews.jsonl")
    parser.add_argument("--card-id", required=True)
    parser.add_argument("--start-node", required=True)
    parser.add_argument("--target-node", required=True)
    parser.add_argument("--mode", choices=["final", "retrieval"], default="final")
    parser.add_argument("--condition", action="append", default=[])
    parser.add_argument("--max-hops", type=int, default=8)
    parser.add_argument("--output")
    args = parser.parse_args()

    cards = collect_cards(read_json(Path(args.cards)))
    card = next((row for row in cards if row.get("card_id") == args.card_id), None)
    if card is None:
        raise SystemExit(f"Card not found: {args.card_id}")
    reviews = read_jsonl(Path(args.edge_reviews))
    adjacency = build_proof_adjacency(card, reviews, mode=args.mode)
    nodes_by_id = {node.get("node_id"): node for node in card.get("flow_nodes") or []}
    require_result_edge = node_role(nodes_by_id.get(args.target_node, {})) == "exit"
    paths = find_proof_paths(
        adjacency,
        args.start_node,
        args.target_node,
        satisfied_conditions=args.condition,
        max_hops=args.max_hops,
        require_result_edge=require_result_edge,
    )
    result = {
        "card_id": args.card_id,
        "mode": args.mode,
        "start_node": args.start_node,
        "target_node": args.target_node,
        "satisfied_conditions": args.condition,
        "paths": paths,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
