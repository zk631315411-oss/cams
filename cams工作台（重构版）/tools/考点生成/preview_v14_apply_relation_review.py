from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_V10_DIR = HERE / "work" / "preview_v10_full828"
DEFAULT_V13_DIR = HERE / "work" / "preview_v13_relation_review"
DEFAULT_OUT_DIR = HERE / "work" / "preview_v14_relation_layer"

FINAL_DECISION_LABELS = {
    "confirmed_parent_child",
    "direction_reversed",
    "confirmed_sibling",
    "merge_same_point",
    "keep_separate",
    "needs_review",
}


def decision_quality(decision: dict[str, Any]) -> dict[str, Any]:
    label = str(decision.get("decision_label") or "")
    confidence = str(decision.get("confidence") or "")
    risk_flags = [str(flag) for flag in decision.get("risk_flags", []) if flag]
    if "baseline_not_final" in risk_flags:
        return {
            "quality_status": "pipeline_test_only",
            "quality_reason": "baseline decision is not publishable",
        }
    if label == "needs_review" or confidence == "low":
        return {
            "quality_status": "needs_review",
            "quality_reason": "reviewer marked low confidence or needs human review",
        }
    if label == "keep_separate":
        return {
            "quality_status": "accepted_keep_separate",
            "quality_reason": "reviewer explicitly rejected the structural relation",
        }
    if label == "merge_same_point":
        if confidence == "high" and not risk_flags:
            return {
                "quality_status": "ready_relation",
                "quality_reason": "high-confidence same-point merge with no risk flags",
            }
        return {
            "quality_status": "merge_boundary_review",
            "quality_reason": "merge label has medium confidence or boundary risk flags",
        }
    if label in {"confirmed_parent_child", "direction_reversed"}:
        if confidence == "high" and not risk_flags:
            return {
                "quality_status": "ready_relation",
                "quality_reason": "high-confidence parent-child relation with no risk flags",
            }
        return {
            "quality_status": "parent_child_light_review",
            "quality_reason": "parent-child relation is useful but direction/scope should be spot-checked",
        }
    if label == "confirmed_sibling":
        if confidence == "high" and not risk_flags:
            return {
                "quality_status": "ready_relation",
                "quality_reason": "high-confidence sibling relation with no risk flags",
            }
        return {
            "quality_status": "sibling_light_review",
            "quality_reason": "sibling relation is useful but parent grouping/name should be spot-checked",
        }
    return {
        "quality_status": "needs_review",
        "quality_reason": "unclassified relation quality",
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else HERE / path


def env_path(name: str, default: Path) -> Path:
    raw = os.getenv(name, "").strip().strip('"')
    return resolve_path(raw) if raw else default


def batch_name_from_file(path: Path) -> str:
    stem = path.stem
    prefix = "relation_review_decisions_"
    if stem.startswith(prefix):
        stem = stem[len(prefix) :]
    return stem


def compact(text: Any, limit: int = 240) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)] + "..."


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(v for v in values if v))


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, value: str) -> str:
        self.parent.setdefault(value, value)
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, a: str, b: str) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def groups(self) -> list[list[str]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for value in self.parent:
            grouped[self.find(value)].append(value)
        return [sorted(values) for values in grouped.values() if len(values) > 1]


def build_indexes(points: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    points_by_id = {str(point["id"]): point for point in points}
    card_to_point: dict[str, str] = {}
    for point in points:
        point_id = str(point["id"])
        for card_id in point.get("card_ids", []):
            card_to_point[str(card_id)] = point_id
    return points_by_id, card_to_point


def point_view(point: dict[str, Any] | None) -> dict[str, Any] | None:
    if not point:
        return None
    return {
        "exam_point_id": point.get("id"),
        "title": compact(point.get("title"), 120),
        "point_type": point.get("point_type"),
        "question_count": point.get("question_count"),
        "core_question_count": point.get("core_question_count"),
        "contrast_question_count": point.get("contrast_question_count"),
        "card_ids": point.get("card_ids", []),
        "tags": point.get("tags", []),
    }


def relation_source(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_id": decision.get("review_id"),
        "pair_id": decision.get("pair_id"),
        "decision_label": decision.get("decision_label"),
        "confidence": decision.get("confidence"),
        "rationale": decision.get("rationale"),
        "risk_flags": decision.get("risk_flags", []),
        "question_signal_used": decision.get("question_signal_used"),
        "evidence_card_ids": decision.get("evidence_card_ids", []),
        **decision_quality(decision),
    }


def parent_child_output_quality(sources: list[dict[str, Any]]) -> dict[str, str]:
    if any(src.get("quality_status") == "pipeline_test_only" for src in sources):
        return {
            "quality_status": "pipeline_test_only",
            "quality_reason": "one or more source decisions are baseline-only",
        }
    if sources and all(src.get("quality_status") == "ready_relation" for src in sources):
        reason = "high-confidence parent-child relation with no risk flags"
        if len(sources) > 1:
            reason = f"{reason}; deduplicated from {len(sources)} reviewed card pairs"
        return {
            "quality_status": "ready_relation",
            "quality_reason": reason,
        }
    reason = "parent-child relation is useful but direction/scope should be spot-checked"
    if len(sources) > 1:
        reason = f"{reason}; deduplicated from {len(sources)} reviewed card pairs"
    return {
        "quality_status": "parent_child_light_review",
        "quality_reason": reason,
    }


def dedupe_parent_child_edges(raw_edges: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for edge in raw_edges:
        grouped[(edge["parent_point_id"], edge["child_point_id"])].append(edge)

    edges: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    for index, ((parent_point_id, child_point_id), rows) in enumerate(grouped.items(), start=1):
        first = rows[0]
        sources = [row["source_decision"] for row in rows]
        graph_flags: list[str] = []
        if len(rows) > 1:
            graph_flags.append("deduplicated_parent_child_sources")
            duplicates.append(
                {
                    "parent_point_id": parent_point_id,
                    "child_point_id": child_point_id,
                    "source_edge_ids": [row["edge_id"] for row in rows],
                    "source_pair_ids": [src.get("pair_id") for src in sources],
                    "card_pairs": [
                        {
                            "parent_card_id": row["parent_card_id"],
                            "child_card_id": row["child_card_id"],
                        }
                        for row in rows
                    ],
                }
            )
        quality = parent_child_output_quality(sources)
        edges.append(
            {
                "edge_id": f"PC-{index:04d}",
                "parent_point_id": parent_point_id,
                "child_point_id": child_point_id,
                "parent_card_id": first["parent_card_id"],
                "child_card_id": first["child_card_id"],
                "parent_card_ids": unique([row["parent_card_id"] for row in rows]),
                "child_card_ids": unique([row["child_card_id"] for row in rows]),
                "card_pairs": [
                    {
                        "parent_card_id": row["parent_card_id"],
                        "child_card_id": row["child_card_id"],
                    }
                    for row in rows
                ],
                "relation_label": "parent_child",
                **quality,
                "graph_flags": graph_flags,
                "source_decision": sources[0],
                "source_decisions": sources,
                "source_decision_count": len(sources),
                "parent_point": first["parent_point"],
                "child_point": first["child_point"],
            }
        )

    child_to_parent_ids: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        child_to_parent_ids[edge["child_point_id"]].add(edge["parent_point_id"])
    multi_parent_children = {
        child_id: sorted(parent_ids)
        for child_id, parent_ids in child_to_parent_ids.items()
        if len(parent_ids) > 1
    }
    for edge in edges:
        parent_ids = multi_parent_children.get(edge["child_point_id"])
        if not parent_ids:
            continue
        flags = edge.setdefault("graph_flags", [])
        if "multi_parent_graph" not in flags:
            flags.append("multi_parent_graph")
        edge["multi_parent_parent_ids"] = parent_ids
        edge["display_guidance"] = "graph_relation; choose one primary parent only if rendering a tree"

    return edges, duplicates


def is_baseline_payload(payload: dict[str, Any]) -> bool:
    reviewer = str(payload.get("llm_or_reviewer") or "")
    if "baseline" in reviewer:
        return True
    for decision in payload.get("decisions", []):
        if "baseline_not_final" in (decision.get("risk_flags") or []):
            return True
    return False


def build_relation_layer(
    points: list[dict[str, Any]],
    decisions_payload: dict[str, Any],
) -> dict[str, Any]:
    points_by_id, card_to_point = build_indexes(points)
    raw_parent_child_edges: list[dict[str, Any]] = []
    sibling_edges: list[dict[str, Any]] = []
    keep_separate_edges: list[dict[str, Any]] = []
    needs_review_edges: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    merge_uf = UnionFind()
    sibling_uf = UnionFind()
    merge_sources: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    sibling_sources: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    label_counts = Counter()
    confidence_counts = Counter()
    quality_counts = Counter()

    for decision in decisions_payload.get("decisions", []):
        label = str(decision.get("decision_label") or "")
        confidence = str(decision.get("confidence") or "")
        quality = decision_quality(decision)
        label_counts[label] += 1
        confidence_counts[confidence] += 1
        quality_counts[quality["quality_status"]] += 1
        if label not in FINAL_DECISION_LABELS:
            rejected.append({**relation_source(decision), "reason": "invalid_decision_label"})
            continue

        evidence_card_ids = [str(card_id) for card_id in decision.get("evidence_card_ids", []) if card_id]
        point_ids = unique([card_to_point.get(card_id, "") for card_id in evidence_card_ids])
        if label in {"confirmed_parent_child", "direction_reversed"}:
            parent_card_id = str(decision.get("parent_card_id") or "")
            child_card_id = str(decision.get("child_card_id") or "")
            parent_point_id = card_to_point.get(parent_card_id)
            child_point_id = card_to_point.get(child_card_id)
            if not parent_point_id or not child_point_id or parent_point_id == child_point_id:
                rejected.append({**relation_source(decision), "reason": "invalid_parent_child_endpoint"})
                continue
            raw_parent_child_edges.append(
                {
                    "edge_id": f"RAW-PC-{len(raw_parent_child_edges) + 1:04d}",
                    "parent_point_id": parent_point_id,
                    "child_point_id": child_point_id,
                    "parent_card_id": parent_card_id,
                    "child_card_id": child_card_id,
                    "relation_label": "parent_child",
                    **quality,
                    "source_decision": relation_source(decision),
                    "parent_point": point_view(points_by_id.get(parent_point_id)),
                    "child_point": point_view(points_by_id.get(child_point_id)),
                }
            )
        elif label == "confirmed_sibling":
            if len(point_ids) < 2:
                rejected.append({**relation_source(decision), "reason": "sibling_missing_two_points"})
                continue
            a, b = sorted(point_ids[:2])
            sibling_uf.union(a, b)
            sibling_sources[(a, b)].append(relation_source(decision))
            sibling_edges.append(
                {
                    "edge_id": f"SB-{len(sibling_edges) + 1:04d}",
                    "point_ids": [a, b],
                    "card_ids": evidence_card_ids,
                    "relation_label": "sibling_under_parent",
                    **quality,
                    "proposed_parent_title": decision.get("proposed_parent_title"),
                    "source_decision": relation_source(decision),
                    "points": [point_view(points_by_id.get(a)), point_view(points_by_id.get(b))],
                }
            )
        elif label == "merge_same_point":
            if len(point_ids) < 2:
                rejected.append({**relation_source(decision), "reason": "merge_missing_two_points"})
                continue
            a, b = sorted(point_ids[:2])
            merge_uf.union(a, b)
            merge_sources[(a, b)].append(relation_source(decision))
        elif label == "keep_separate":
            keep_separate_edges.append(
                {
                    "edge_id": f"KS-{len(keep_separate_edges) + 1:04d}",
                    "point_ids": point_ids,
                    "card_ids": evidence_card_ids,
                    "relation_label": "keep_separate",
                    **quality,
                    "source_decision": relation_source(decision),
                }
            )
        elif label == "needs_review":
            needs_review_edges.append(
                {
                    "edge_id": f"NR-{len(needs_review_edges) + 1:04d}",
                    "point_ids": point_ids,
                    "card_ids": evidence_card_ids,
                    "relation_label": "needs_review",
                    **quality,
                    "needs_human_reason": decision.get("needs_human_reason"),
                    "source_decision": relation_source(decision),
                }
            )

    merge_groups = []
    for index, group in enumerate(merge_uf.groups(), start=1):
        sources = [
            src
            for pair, rows in merge_sources.items()
            if pair[0] in group and pair[1] in group
            for src in rows
        ]
        merge_groups.append(
            {
                "merge_group_id": f"MG-{index:04d}",
                "point_ids": group,
                "points": [point_view(points_by_id.get(point_id)) for point_id in group],
                "quality_status": (
                    "ready_relation"
                    if sources and all(src.get("quality_status") == "ready_relation" for src in sources)
                    else "merge_boundary_review"
                ),
                "quality_reason": "derived from merge_same_point source decisions",
                "source_decisions": sources,
            }
        )

    sibling_groups = []
    for index, group in enumerate(sibling_uf.groups(), start=1):
        sources = [
            src
            for pair, rows in sibling_sources.items()
            if pair[0] in group and pair[1] in group
            for src in rows
        ]
        proposed_titles = unique(
            [
                str(edge.get("proposed_parent_title") or "")
                for edge in sibling_edges
                if set(edge.get("point_ids", [])).issubset(set(group))
            ]
        )
        sibling_groups.append(
            {
                "sibling_group_id": f"SG-{index:04d}",
                "point_ids": group,
                "points": [point_view(points_by_id.get(point_id)) for point_id in group],
                "quality_status": (
                    "ready_relation"
                    if sources and all(src.get("quality_status") == "ready_relation" for src in sources)
                    else "sibling_light_review"
                ),
                "quality_reason": "derived from sibling source decisions",
                "proposed_parent_titles": proposed_titles,
                "source_decisions": sources,
            }
        )

    parent_child_edges, duplicate_parent_child_edges = dedupe_parent_child_edges(raw_parent_child_edges)
    multi_parent_child_ids = sorted(
        {
            edge["child_point_id"]
            for edge in parent_child_edges
            if "multi_parent_graph" in edge.get("graph_flags", [])
        }
    )
    broad_sibling_group_ids = [
        group["sibling_group_id"]
        for group in sibling_groups
        if len(group.get("point_ids", [])) >= 3
    ]
    for group in sibling_groups:
        if group["sibling_group_id"] not in broad_sibling_group_ids:
            continue
        flags = group.setdefault("graph_flags", [])
        if "broad_sibling_group_review" not in flags:
            flags.append("broad_sibling_group_review")
        group["display_guidance"] = "review parent grouping/name before publishing as a visible group"

    output_quality_counts = Counter()
    for row in (
        parent_child_edges
        + sibling_edges
        + sibling_groups
        + merge_groups
        + keep_separate_edges
        + needs_review_edges
    ):
        output_quality_counts[row.get("quality_status")] += 1

    baseline = is_baseline_payload(decisions_payload)
    return {
        "schema_version": "preview_v14_relation_layer",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_batch_name": decisions_payload.get("batch_name"),
        "source_reviewer": decisions_payload.get("llm_or_reviewer"),
        "finality": "pipeline_test_only" if baseline else "reviewed_relation_layer",
        "warning": (
            "This output was built from deterministic baseline decisions and must not be published."
            if baseline
            else None
        ),
        "summary": {
            "decision_count": len(decisions_payload.get("decisions", [])),
            "decision_label_counts": dict(label_counts),
            "confidence_counts": dict(confidence_counts),
            "quality_status_counts": dict(output_quality_counts),
            "decision_quality_status_counts": dict(quality_counts),
            "output_quality_status_counts": dict(output_quality_counts),
            "raw_parent_child_edge_count": len(raw_parent_child_edges),
            "parent_child_edge_count": len(parent_child_edges),
            "deduplicated_parent_child_edge_count": len(duplicate_parent_child_edges),
            "multi_parent_child_count": len(multi_parent_child_ids),
            "broad_sibling_group_count": len(broad_sibling_group_ids),
            "sibling_edge_count": len(sibling_edges),
            "sibling_group_count": len(sibling_groups),
            "merge_group_count": len(merge_groups),
            "keep_separate_edge_count": len(keep_separate_edges),
            "needs_review_edge_count": len(needs_review_edges),
            "rejected_count": len(rejected),
        },
        "parent_child_edges": parent_child_edges,
        "duplicate_parent_child_edges": duplicate_parent_child_edges,
        "multi_parent_children": [
            {
                "child_point_id": child_id,
                "parent_point_ids": next(
                    edge.get("multi_parent_parent_ids", [])
                    for edge in parent_child_edges
                    if edge["child_point_id"] == child_id
                ),
                "child_point": next(
                    edge.get("child_point")
                    for edge in parent_child_edges
                    if edge["child_point_id"] == child_id
                ),
            }
            for child_id in multi_parent_child_ids
        ],
        "broad_sibling_group_ids": broad_sibling_group_ids,
        "sibling_edges": sibling_edges,
        "sibling_groups": sibling_groups,
        "merge_groups": merge_groups,
        "keep_separate_edges": keep_separate_edges,
        "needs_review_edges": needs_review_edges,
        "rejected": rejected,
    }


def report_text(layer: dict[str, Any]) -> str:
    summary = layer["summary"]
    lines = [
        f"# Preview v14 relation layer - {layer.get('source_batch_name')}",
        "",
        f"- created_at: {layer.get('created_at')}",
        f"- source_reviewer: {layer.get('source_reviewer')}",
        f"- finality: {layer.get('finality')}",
        f"- warning: {layer.get('warning') or 'none'}",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Parent Child Examples", ""])
    for edge in layer.get("parent_child_edges", [])[:8]:
        sources = edge.get("source_decisions") or [edge.get("source_decision", {})]
        source_text = ", ".join(
            f"{src.get('pair_id')} / {src.get('confidence')}"
            for src in sources
            if src
        )
        flags = ", ".join(edge.get("graph_flags") or [])
        lines.extend(
            [
                f"### {edge['edge_id']} {edge['parent_point_id']} -> {edge['child_point_id']}",
                f"- parent card: {edge['parent_card_id']} | {edge['parent_point']['title'] if edge.get('parent_point') else ''}",
                f"- child card: {edge['child_card_id']} | {edge['child_point']['title'] if edge.get('child_point') else ''}",
                f"- source: {source_text}",
                f"- graph_flags: {flags or 'none'}",
                "",
            ]
        )

    lines.extend(["", "## Duplicate Parent Child Edges", ""])
    for item in layer.get("duplicate_parent_child_edges", [])[:8]:
        lines.append(
            f"- {item['parent_point_id']} -> {item['child_point_id']}: "
            f"{', '.join(item.get('source_pair_ids') or [])}"
        )
    if not layer.get("duplicate_parent_child_edges"):
        lines.append("- none")

    lines.extend(["", "## Multi Parent Children", ""])
    for item in layer.get("multi_parent_children", [])[:8]:
        child = item.get("child_point") or {}
        lines.append(
            f"- {item['child_point_id']} <- {', '.join(item.get('parent_point_ids') or [])}: "
            f"{child.get('title', '')}"
        )
    if not layer.get("multi_parent_children"):
        lines.append("- none")

    lines.extend(["", "## Sibling Group Examples", ""])
    for group in layer.get("sibling_groups", [])[:8]:
        lines.extend(
            [
                f"### {group['sibling_group_id']}",
                f"- point_ids: {', '.join(group['point_ids'])}",
                f"- proposed_titles: {', '.join(group.get('proposed_parent_titles') or [])}",
                f"- graph_flags: {', '.join(group.get('graph_flags') or []) or 'none'}",
                "",
            ]
        )
        for point in group.get("points", [])[:5]:
            lines.append(f"  - {point['exam_point_id']}: {point['title']}" if point else "  - missing")
        lines.append("")

    lines.extend(["", "## Needs Review Examples", ""])
    for edge in layer.get("needs_review_edges", [])[:8]:
        lines.append(f"- {edge['source_decision'].get('pair_id')}: {edge.get('needs_human_reason')}")

    return "\n".join(lines) + "\n"


def main() -> None:
    v10_dir = env_path("PREVIEW_V14_V10_DIR", DEFAULT_V10_DIR)
    decisions_raw = os.getenv("PREVIEW_V14_DECISIONS_FILE", "").strip().strip('"')
    if decisions_raw:
        decisions_file = resolve_path(decisions_raw)
    else:
        batch = os.getenv("PREVIEW_V14_BATCH_NAME", "strict_trace_all100").strip()
        decisions_file = DEFAULT_V13_DIR / f"relation_review_decisions_{batch}_baseline.json"
    out = env_path("PREVIEW_V14_OUT_DIR", DEFAULT_OUT_DIR)
    batch_name = batch_name_from_file(decisions_file)

    points_payload = read_json(v10_dir / "exam_point_system_full828.json")
    decisions_payload = read_json(decisions_file)
    layer = build_relation_layer(points_payload.get("items", []), decisions_payload)
    out_file = out / f"relation_layer_{batch_name}.json"
    report_file = out / f"relation_layer_report_{batch_name}.md"
    write_json(out_file, layer)
    write_text(report_file, report_text(layer))
    print(f"wrote: {out_file}")
    print(json.dumps(layer["summary"], ensure_ascii=False, indent=2))
    if layer.get("warning"):
        print(f"WARNING: {layer['warning']}")


if __name__ == "__main__":
    main()
