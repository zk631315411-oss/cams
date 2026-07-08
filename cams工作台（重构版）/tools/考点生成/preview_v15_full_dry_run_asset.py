from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_V10_DIR = HERE / "work" / "preview_v10_full828"
DEFAULT_V8_NAMED_FILE = (
    HERE
    / "work"
    / "preview_v8_naming_sample"
    / "named_exam_points_sample_v10_full831_all_prompt_v2.json"
)
DEFAULT_V9_DIR = HERE / "work" / "preview_v9_admission_gate"
DEFAULT_V9_ADMISSION_FILE = DEFAULT_V9_DIR / "admission_decisions_v10_full831_all_prompt_v2_rules_v3.json"
DEFAULT_V9_SUMMARY_FILE = DEFAULT_V9_DIR / "summary_v10_full831_all_prompt_v2_rules_v3.json"
DEFAULT_V14_LAYER_FILE = (
    HERE
    / "work"
    / "preview_v14_relation_layer"
    / "relation_layer_strict_trace_all100_review_merged.json"
)
DEFAULT_OUT_DIR = HERE / "work" / "preview_v15_full_dry_run"


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


def compact(text: Any, limit: int = 180) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)] + "..."


def point_brief(point: dict[str, Any] | None) -> dict[str, Any] | None:
    if not point:
        return None
    return {
        "id": point.get("id") or point.get("exam_point_id"),
        "title": compact(point.get("title"), 100),
        "point_type": point.get("point_type"),
        "question_count": point.get("question_count"),
        "core_question_count": point.get("core_question_count"),
        "contrast_question_count": point.get("contrast_question_count"),
        "card_ids": point.get("card_ids", []),
        "tags": point.get("tags", []),
    }


def edge_view(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "question_id": edge.get("question_id"),
        "section": edge.get("section"),
        "option": edge.get("option"),
        "option_text": edge.get("option_text"),
        "role": edge.get("role"),
        "key_is_correct": edge.get("key_is_correct"),
        "judgement": edge.get("judgement"),
        "evidence_grade": edge.get("evidence_grade"),
        "evidence_status": edge.get("evidence_status"),
        "focus_type": edge.get("focus_type"),
        "card_id": edge.get("card_id"),
        "quote": edge.get("quote"),
        "support_type": edge.get("support_type"),
        "relevance": edge.get("relevance"),
        "source_edge_key": edge.get("source_edge_key"),
    }


def relation_edge_view(edge: dict[str, Any], direction: str) -> dict[str, Any]:
    return {
        "edge_id": edge.get("edge_id"),
        "direction": direction,
        "parent_point_id": edge.get("parent_point_id"),
        "child_point_id": edge.get("child_point_id"),
        "parent_card_ids": edge.get("parent_card_ids") or [edge.get("parent_card_id")],
        "child_card_ids": edge.get("child_card_ids") or [edge.get("child_card_id")],
        "quality_status": edge.get("quality_status"),
        "quality_reason": edge.get("quality_reason"),
        "graph_flags": edge.get("graph_flags", []),
        "source_pair_ids": [
            src.get("pair_id")
            for src in (edge.get("source_decisions") or [edge.get("source_decision", {})])
            if src
        ],
        "source_decision_count": edge.get("source_decision_count", 1),
    }


def relation_pair_view(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "edge_id": edge.get("edge_id"),
        "point_ids": edge.get("point_ids", []),
        "card_ids": edge.get("card_ids", []),
        "relation_label": edge.get("relation_label"),
        "quality_status": edge.get("quality_status"),
        "quality_reason": edge.get("quality_reason"),
        "needs_human_reason": edge.get("needs_human_reason"),
        "source_pair_id": (edge.get("source_decision") or {}).get("pair_id"),
        "confidence": (edge.get("source_decision") or {}).get("confidence"),
    }


def build_relation_indexes(layer: dict[str, Any]) -> dict[str, Any]:
    parent_edges_by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    parent_edges_by_child: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in layer.get("parent_child_edges", []):
        parent_edges_by_parent[edge["parent_point_id"]].append(edge)
        parent_edges_by_child[edge["child_point_id"]].append(edge)

    sibling_groups_by_point: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for group in layer.get("sibling_groups", []):
        for point_id in group.get("point_ids", []):
            sibling_groups_by_point[point_id].append(group)

    merge_groups_by_point: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for group in layer.get("merge_groups", []):
        for point_id in group.get("point_ids", []):
            merge_groups_by_point[point_id].append(group)

    keep_separate_by_point: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in layer.get("keep_separate_edges", []):
        for point_id in edge.get("point_ids", []):
            keep_separate_by_point[point_id].append(edge)

    needs_review_by_point: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in layer.get("needs_review_edges", []):
        for point_id in edge.get("point_ids", []):
            needs_review_by_point[point_id].append(edge)

    multi_parent_by_child = {
        item.get("child_point_id"): item
        for item in layer.get("multi_parent_children", [])
    }

    return {
        "parent_edges_by_parent": parent_edges_by_parent,
        "parent_edges_by_child": parent_edges_by_child,
        "sibling_groups_by_point": sibling_groups_by_point,
        "merge_groups_by_point": merge_groups_by_point,
        "keep_separate_by_point": keep_separate_by_point,
        "needs_review_by_point": needs_review_by_point,
        "multi_parent_by_child": multi_parent_by_child,
    }


def queue_item(point: dict[str, Any], admission: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": point.get("id"),
        "title": compact(point.get("title"), 80),
        "point_type": point.get("point_type"),
        "question_count": point.get("question_count"),
        "core_question_count": point.get("core_question_count"),
        "contrast_question_count": point.get("contrast_question_count"),
        "card_count": len(point.get("card_ids", [])),
        "admission_status": (admission or {}).get("admission_status"),
        "review_priority": (admission or {}).get("review_priority"),
        "risk_flags": (admission or {}).get("risk_flags", []),
        "engineering_risk_flags": (admission or {}).get("engineering_risk_flags", []),
    }


def mismatch_point_view(point: dict[str, Any] | None) -> dict[str, Any] | None:
    if not point:
        return None
    return {
        "id": point.get("id"),
        "title": compact(point.get("title"), 100),
        "point_type": point.get("point_type"),
        "question_count": point.get("question_count"),
        "core_question_count": point.get("core_question_count"),
        "contrast_question_count": point.get("contrast_question_count"),
        "card_ids": point.get("card_ids", []),
        "sections": point.get("sections", {}),
        "review_status": point.get("review_status"),
    }


def source_drift_flags(
    point: dict[str, Any],
    named: dict[str, Any] | None,
    admission: dict[str, Any] | None,
) -> list[str]:
    flags: list[str] = []
    if named:
        if set(point.get("card_ids", [])) != set(named.get("card_ids", [])):
            flags.append("named_card_ids_changed")
        if set(point.get("question_ids", [])) != set(named.get("question_ids", [])):
            flags.append("named_question_ids_changed")
        if point.get("question_count") != named.get("question_count"):
            flags.append("named_question_count_changed")
        if point.get("point_type") != named.get("point_type"):
            flags.append("named_point_type_changed")
    if admission:
        if point.get("question_count") != admission.get("question_count"):
            flags.append("admission_question_count_changed")
        if point.get("point_type") != admission.get("point_type"):
            flags.append("admission_point_type_changed")
        if len(point.get("card_ids", [])) != admission.get("card_count"):
            flags.append("admission_card_count_changed")
    return flags


def build_asset() -> tuple[dict[str, Any], str]:
    v10_dir = env_path("PREVIEW_V15_V10_DIR", DEFAULT_V10_DIR)
    named_file = env_path("PREVIEW_V15_NAMED_FILE", DEFAULT_V8_NAMED_FILE)
    admission_file = env_path("PREVIEW_V15_ADMISSION_FILE", DEFAULT_V9_ADMISSION_FILE)
    admission_summary_file = env_path("PREVIEW_V15_ADMISSION_SUMMARY_FILE", DEFAULT_V9_SUMMARY_FILE)
    relation_layer_file = env_path("PREVIEW_V15_RELATION_LAYER_FILE", DEFAULT_V14_LAYER_FILE)

    v10_points_payload = read_json(v10_dir / "exam_point_system_full828.json")
    v10_edges_payload = read_json(v10_dir / "exam_point_question_card_edges.json")
    v10_summary = read_json(v10_dir / "summary.json")
    review_only_payload = read_json(v10_dir / "review_only_points.json")
    named_payload = read_json(named_file)
    admission_payload = read_json(admission_file)
    admission_summary = read_json(admission_summary_file)
    relation_layer = read_json(relation_layer_file)

    base_points = v10_points_payload.get("items", [])
    edges = v10_edges_payload.get("items", [])
    named_by_id = {item.get("id"): item for item in named_payload.get("items", []) if item.get("id")}
    admission_by_id = {
        item.get("exam_point_id"): item
        for item in admission_payload.get("items", [])
        if item.get("exam_point_id")
    }
    edges_by_point: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        edges_by_point[edge.get("exam_point_id")].append(edge)

    relation_indexes = build_relation_indexes(relation_layer)

    items: list[dict[str, Any]] = []
    status_queues: dict[str, list[dict[str, Any]]] = defaultdict(list)
    missing_named: list[str] = []
    missing_admission: list[str] = []
    source_drift_points: list[dict[str, Any]] = []

    for point in base_points:
        point_id = point["id"]
        named = named_by_id.get(point_id)
        admission = admission_by_id.get(point_id)
        if not named:
            missing_named.append(point_id)
        if not admission:
            missing_admission.append(point_id)
        drift_flags = source_drift_flags(point, named, admission)
        if drift_flags:
            source_drift_points.append(
                {
                    "id": point_id,
                    "title": compact(point.get("title"), 100),
                    "named_title": compact((named or {}).get("title"), 100),
                    "v10_question_count": point.get("question_count"),
                    "named_question_count": (named or {}).get("question_count"),
                    "admission_question_count": (admission or {}).get("question_count"),
                    "v10_card_ids": point.get("card_ids", []),
                    "named_card_ids": (named or {}).get("card_ids", []),
                    "drift_flags": drift_flags,
                    "old_admission_status": (admission or {}).get("admission_status"),
                }
            )
        usable_named = named if named and not drift_flags else None
        usable_admission = admission if admission and not drift_flags else None
        title = (usable_named or {}).get("title") or point.get("title")

        parent_edges = relation_indexes["parent_edges_by_child"].get(point_id, [])
        child_edges = relation_indexes["parent_edges_by_parent"].get(point_id, [])
        sibling_groups = relation_indexes["sibling_groups_by_point"].get(point_id, [])
        merge_groups = relation_indexes["merge_groups_by_point"].get(point_id, [])
        keep_separate_edges = relation_indexes["keep_separate_by_point"].get(point_id, [])
        needs_review_edges = relation_indexes["needs_review_by_point"].get(point_id, [])

        item = {
            "id": point_id,
            "title": title,
            "title_source": "v8_named" if named else "v10_placeholder",
            "title_before_naming": (named or {}).get("title_before_naming") or point.get("title"),
            "point_type": point.get("point_type"),
            "is_high_frequency": point.get("is_high_frequency"),
            "tags": point.get("tags", []),
            "question_count": point.get("question_count"),
            "core_question_count": point.get("core_question_count"),
            "contrast_question_count": point.get("contrast_question_count"),
            "needs_review_contrast_question_count": point.get("needs_review_contrast_question_count"),
            "subtree_question_count": point.get("subtree_question_count"),
            "card_ids": point.get("card_ids", []),
            "card_count": len(point.get("card_ids", [])),
            "question_ids": point.get("question_ids", []),
            "core_question_ids": point.get("core_question_ids", []),
            "contrast_question_ids": point.get("contrast_question_ids", []),
            "sections": point.get("sections", {}),
            "cross_chapter": point.get("cross_chapter"),
            "evidence_quotes": point.get("evidence_quotes", []),
            "question_edges": [edge_view(edge) for edge in edges_by_point.get(point_id, [])],
            "teaching_focus": (usable_named or {}).get("teaching_focus"),
            "relation_summary": (usable_named or {}).get("relation_summary"),
            "card_roles": (usable_named or {}).get("card_roles", []),
            "question_roles": (usable_named or {}).get("question_roles", []),
            "split_recommendation": (usable_named or {}).get("split_recommendation"),
            "naming_risk_flags": (usable_named or {}).get("naming_risk_flags", []),
            "naming_confidence": (usable_named or {}).get("naming_confidence"),
            "admission": {
                "status": (
                    "stale_naming_or_admission"
                    if drift_flags
                    else (usable_admission or {}).get("admission_status", "missing_admission")
                ),
                "review_priority": (usable_admission or {}).get("review_priority"),
                "risk_flags": (
                    ["source_alignment_drift"]
                    if drift_flags
                    else (usable_admission or {}).get("risk_flags", [])
                ),
                "engineering_risk_flags": (
                    drift_flags
                    if drift_flags
                    else (usable_admission or {}).get("engineering_risk_flags", [])
                ),
                "recommended_actions": (
                    ["rerun_v8_naming_and_v9_admission_for_current_v10_point"]
                    if drift_flags
                    else (usable_admission or {}).get("recommended_actions", [])
                ),
                "decision_reasons": (
                    ["v8/v9 source fields no longer match current v10 strict base"]
                    if drift_flags
                    else (usable_admission or {}).get("decision_reasons", [])
                ),
            },
            "relations": {
                "parents": [relation_edge_view(edge, "as_child") for edge in parent_edges],
                "children": [relation_edge_view(edge, "as_parent") for edge in child_edges],
                "sibling_group_ids": [group.get("sibling_group_id") for group in sibling_groups],
                "sibling_group_flags": {
                    group.get("sibling_group_id"): group.get("graph_flags", [])
                    for group in sibling_groups
                },
                "merge_group_ids": [group.get("merge_group_id") for group in merge_groups],
                "keep_separate_edges": [relation_pair_view(edge) for edge in keep_separate_edges],
                "needs_review_edges": [relation_pair_view(edge) for edge in needs_review_edges],
                "multi_parent_graph": point_id in relation_indexes["multi_parent_by_child"],
                "multi_parent_detail": relation_indexes["multi_parent_by_child"].get(point_id),
            },
            "source": {
                "v10_build_method": point.get("build_method"),
                "v10_review_status": point.get("review_status"),
                "relation_trace_pair_ids": point.get("relation_trace_pair_ids", []),
                "materialize_relation_pair_ids": point.get("materialize_relation_pair_ids", []),
                "source_point_ids": point.get("source_point_ids", []),
            },
        }
        items.append(item)
        status_queues[item["admission"]["status"]].append(queue_item(item, admission))

    point_ids = {point["id"] for point in base_points}
    base_by_id = {point["id"]: point for point in base_points}
    extra_named_ids = sorted(set(named_by_id) - point_ids)
    extra_admission_ids = sorted(set(admission_by_id) - point_ids)
    ready_statuses = {"ready_candidate", "ready_candidate_with_children"}

    summary = {
        "source_point_count": len(base_points),
        "edge_count": len(edges),
        "review_only_point_count": len(review_only_payload.get("items", [])),
        "named_count": len(named_by_id),
        "admission_count": len(admission_by_id),
        "matched_named_count": len(point_ids & set(named_by_id)),
        "matched_admission_count": len(point_ids & set(admission_by_id)),
        "missing_named_count": len(missing_named),
        "missing_admission_count": len(missing_admission),
        "extra_named_count": len(extra_named_ids),
        "extra_admission_count": len(extra_admission_ids),
        "source_drift_count": len(source_drift_points),
        "point_type_distribution": dict(Counter(point.get("point_type") for point in base_points)),
        "question_count_distribution": dict(Counter(str(point.get("question_count")) for point in base_points)),
        "card_count_distribution": dict(Counter(str(len(point.get("card_ids", []))) for point in base_points)),
        "admission_status_distribution_matched": dict(
            Counter(item["admission"]["status"] for item in items)
        ),
        "ready_candidate_count_matched": sum(
            1 for item in items if item["admission"]["status"] in ready_statuses
        ),
        "relation_layer_summary": relation_layer.get("summary", {}),
        "v10_summary": v10_summary,
        "v9_summary": admission_summary,
    }

    risk_queues = {
        "by_admission_status": dict(sorted(status_queues.items())),
        "multi_parent_children": relation_layer.get("multi_parent_children", []),
        "duplicate_parent_child_edges": relation_layer.get("duplicate_parent_child_edges", []),
        "broad_sibling_groups": [
            group
            for group in relation_layer.get("sibling_groups", [])
            if group.get("sibling_group_id") in set(relation_layer.get("broad_sibling_group_ids", []))
        ],
        "merge_boundary_review_groups": [
            group
            for group in relation_layer.get("merge_groups", [])
            if group.get("quality_status") == "merge_boundary_review"
        ],
        "relation_needs_review_edges": relation_layer.get("needs_review_edges", []),
        "source_mismatch": {
            "missing_named_ids": missing_named,
            "missing_admission_ids": missing_admission,
            "missing_base_points": [
                mismatch_point_view(base_by_id.get(point_id))
                for point_id in sorted(set(missing_named) | set(missing_admission))
            ],
            "extra_named_ids": extra_named_ids,
            "extra_admission_ids": extra_admission_ids,
            "extra_named_points": [
                mismatch_point_view(named_by_id.get(point_id))
                for point_id in extra_named_ids
            ],
            "source_drift_points": source_drift_points,
        },
    }

    asset = {
        "schema_version": "preview_v15_full_dry_run_asset",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "finality": "full_dry_run_not_for_html_publish",
        "note": "This package combines v10 exam-point base, v8/v11 naming, v9 admission gate, and v14.1 reviewed relation layer. It is for review/dry-run only.",
        "sources": {
            "v10_dir": str(v10_dir),
            "named_file": str(named_file),
            "admission_file": str(admission_file),
            "admission_summary_file": str(admission_summary_file),
            "relation_layer_file": str(relation_layer_file),
        },
        "summary": summary,
        "items": items,
        "risk_queues": risk_queues,
    }
    return asset, report_text(asset)


def sample_items(items: list[dict[str, Any]], status: str, limit: int = 5) -> list[dict[str, Any]]:
    selected = [item for item in items if item.get("admission", {}).get("status") == status]
    selected.sort(key=lambda item: (-int(item.get("question_count") or 0), item.get("id") or ""))
    return selected[:limit]


def report_point_line(item: dict[str, Any]) -> str:
    admission = item.get("admission", {})
    return (
        f"- `{item.get('id')}` {item.get('title')} | "
        f"{item.get('point_type')} | q={item.get('question_count')} "
        f"core={item.get('core_question_count')} contrast={item.get('contrast_question_count')} | "
        f"cards={item.get('card_count')} | priority={admission.get('review_priority') or 'n/a'}"
    )


def report_text(asset: dict[str, Any]) -> str:
    summary = asset["summary"]
    relation_summary = summary.get("relation_layer_summary", {})
    lines = [
        "# Preview v15 full dry-run asset",
        "",
        f"- generated_at: {asset.get('generated_at')}",
        f"- finality: {asset.get('finality')}",
        "",
        "## Summary",
        "",
        f"- v10 exam-point base: {summary['source_point_count']}",
        f"- question-card edges: {summary['edge_count']}",
        f"- review-only points outside formal base: {summary['review_only_point_count']}",
        f"- matched named points: {summary['matched_named_count']} / {summary['source_point_count']}",
        f"- matched admission decisions: {summary['matched_admission_count']} / {summary['source_point_count']}",
        f"- stale named/admission matches: {summary['source_drift_count']}",
        f"- ready candidates matched: {summary['ready_candidate_count_matched']}",
        f"- relation raw parent-child: {relation_summary.get('raw_parent_child_edge_count')}",
        f"- relation deduped parent-child: {relation_summary.get('parent_child_edge_count')}",
        f"- multi-parent child points: {relation_summary.get('multi_parent_child_count')}",
        f"- broad sibling groups: {relation_summary.get('broad_sibling_group_count')}",
        "",
        "## Admission Status",
        "",
    ]
    for status, count in sorted(summary["admission_status_distribution_matched"].items()):
        lines.append(f"- `{status}`: {count}")

    lines.extend(["", "## Samples", ""])
    for status in [
        "ready_candidate",
        "ready_candidate_with_children",
        "single_question_candidate",
        "contrast_review",
        "evidence_supplement_candidate",
        "parent_child_review",
        "merge_boundary_review",
    ]:
        samples = sample_items(asset["items"], status, limit=5)
        lines.extend([f"### {status}", ""])
        if not samples:
            lines.append("- none")
        else:
            lines.extend(report_point_line(item) for item in samples)
        lines.append("")

    lines.extend(["## Relation Risk Queues", ""])
    lines.append(f"- duplicate parent-child pairs: {len(asset['risk_queues']['duplicate_parent_child_edges'])}")
    for edge in asset["risk_queues"]["duplicate_parent_child_edges"][:5]:
        lines.append(
            f"  - {edge.get('parent_point_id')} -> {edge.get('child_point_id')}: "
            f"{', '.join(edge.get('source_pair_ids') or [])}"
        )
    lines.append(f"- multi-parent children: {len(asset['risk_queues']['multi_parent_children'])}")
    for item in asset["risk_queues"]["multi_parent_children"][:5]:
        child = item.get("child_point") or {}
        lines.append(
            f"  - {item.get('child_point_id')} <- {', '.join(item.get('parent_point_ids') or [])}: "
            f"{child.get('title', '')}"
        )
    lines.append(f"- broad sibling groups: {len(asset['risk_queues']['broad_sibling_groups'])}")
    for group in asset["risk_queues"]["broad_sibling_groups"][:5]:
        lines.append(
            f"  - {group.get('sibling_group_id')}: "
            f"{', '.join(group.get('point_ids') or [])} | "
            f"{', '.join(group.get('proposed_parent_titles') or [])}"
        )
    lines.append(f"- merge boundary groups: {len(asset['risk_queues']['merge_boundary_review_groups'])}")
    for group in asset["risk_queues"]["merge_boundary_review_groups"][:5]:
        lines.append(
            f"  - {group.get('merge_group_id')}: {', '.join(group.get('point_ids') or [])}"
        )
    lines.append(f"- relation needs-review edges: {len(asset['risk_queues']['relation_needs_review_edges'])}")

    mismatch = asset["risk_queues"]["source_mismatch"]
    lines.extend(
        [
            "",
            "## Source Alignment",
            "",
            f"- missing named ids: {len(mismatch['missing_named_ids'])}",
            f"- missing admission ids: {len(mismatch['missing_admission_ids'])}",
            f"- extra named ids: {len(mismatch['extra_named_ids'])}",
            f"- extra admission ids: {len(mismatch['extra_admission_ids'])}",
            f"- stale named/admission points: {len(mismatch['source_drift_points'])}",
            "",
            "### Stale Source Examples",
            "",
        ]
    )
    for item in mismatch["source_drift_points"][:8]:
        lines.append(
            f"- `{item['id']}` v10=`{item['title']}` named=`{item.get('named_title')}` "
            f"flags={', '.join(item.get('drift_flags') or [])}"
        )
    if not mismatch["source_drift_points"]:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            "- This dry-run asset is suitable for batch quality review and front-end review-page prototyping.",
            "- It should not replace the production HTML asset until review queues are sampled and accepted.",
            "- The first front-end integration should expose filters by admission status and relation flags, not a flat final list.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    out = env_path("PREVIEW_V15_OUT_DIR", DEFAULT_OUT_DIR)
    asset, report = build_asset()
    asset_path = out / "full_dry_run_asset.json"
    report_path = out / "full_dry_run_report.md"
    queues_path = out / "risk_queues.json"
    summary_path = out / "summary.json"
    write_json(asset_path, asset)
    write_text(report_path, report)
    write_json(queues_path, asset["risk_queues"])
    write_json(summary_path, asset["summary"])
    print(f"wrote: {asset_path}")
    print(json.dumps(asset["summary"], ensure_ascii=False, indent=2)[:4000])


if __name__ == "__main__":
    main()
