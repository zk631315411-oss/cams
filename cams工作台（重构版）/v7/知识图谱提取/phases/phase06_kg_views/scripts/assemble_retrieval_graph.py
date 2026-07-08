from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
PHASES_DIR = PHASE_DIR.parent

P1_DIR = PHASES_DIR / "phase01_chapter_index"
P2_DIR = PHASES_DIR / "phase02_core_points"
P3_DIR = PHASES_DIR / "phase03_intra_chapter_relations"
P4_DIR = PHASES_DIR / "phase04_cross_chapter_relations"
P5_DIR = PHASES_DIR / "phase05_terms"

OUT_DIR = PHASE_DIR / "outputs"
REPORT_DIR = PHASE_DIR / "reports"

EDGE_PRIORITY = {
    "defines": 0,
    "classifies": 1,
    "states_rule": 2,
    "describes_process": 3,
    "explains": 4,
    "indicates_risk": 5,
    "prescribes_measure": 6,
    "states_consequence": 7,
    "illustrates": 8,
    "provides_context": 9,
    "exclude": 99,
}

P2B_POSITIVE_EDGE_TYPES = set(EDGE_PRIORITY) - {"exclude"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def section_id_from_cp_id(core_point_id: str) -> str:
    match = re.match(r"cp_(CH\d+)_S(\d+)", core_point_id)
    if not match:
        return ""
    return f"{match.group(1)}-S{match.group(2)}"


def unit_order_from_id(unit_id: str) -> int:
    match = re.search(r"(\d+)$", unit_id or "")
    return int(match.group(1)) if match else 10**9


def load_p1() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    chapters: list[dict[str, Any]] = []
    sections: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(P1_DIR / "outputs" / "chapter_skeleton.jsonl"):
        chapter_id = row.get("chapter_id")
        chapters.append(
            {
                "chapter_id": chapter_id,
                "chapter_title": row.get("chapter_title"),
                "unit_count": row.get("unit_count"),
                "pdf_page_span": row.get("pdf_page_span") or [],
                "printed_page_span": row.get("printed_page_span") or [],
                "section_ids": [section.get("section_id") for section in row.get("heading_sections") or []],
            }
        )
        for section in row.get("heading_sections") or []:
            section_id = section.get("section_id")
            if not section_id:
                continue
            sections[section_id] = {
                "section_id": section_id,
                "chapter_id": chapter_id,
                "section_order": section.get("section_order"),
                "section_title": section.get("section_title"),
                "unit_ids": section.get("unit_ids") or [],
                "unit_count": section.get("unit_count"),
                "unit_order_span": section.get("unit_order_span") or [],
                "pdf_page_span": section.get("pdf_page_span") or [],
                "printed_page_span": section.get("printed_page_span") or [],
            }

    units: dict[str, dict[str, Any]] = {}
    for unit in read_jsonl(P1_DIR / "outputs" / "all_chapters_units.jsonl"):
        unit_id = unit.get("unit_id")
        if not unit_id:
            continue
        units[unit_id] = {
            "unit_id": unit_id,
            "chapter_id": unit.get("chapter_id"),
            "section_id": unit.get("section_id"),
            "unit_order": unit.get("unit_order"),
            "type": unit.get("type"),
            "knowledge_zh": unit.get("knowledge_zh"),
            "en_quote": unit.get("en_quote"),
            "printed_page": unit.get("printed_page"),
            "pdf_page": unit.get("pdf_page"),
            "risk_flags": unit.get("risk_flags") or [],
        }
    return chapters, sections, units


def load_p2a_reviewed() -> tuple[dict[str, dict[str, Any]], dict[str, list[str]]]:
    core_points: dict[str, dict[str, Any]] = {}
    section_to_cp_ids: dict[str, list[str]] = defaultdict(list)
    for path in sorted((P2_DIR / "outputs").glob("p2a_reviewed_core_points.CH*-S*.json")):
        reviewed = read_json(path)
        section_id = reviewed.get("section_id") or path.stem.replace("p2a_reviewed_core_points.", "", 1)
        chapter_id = section_id.split("-")[0]
        for cp in reviewed.get("core_points") or []:
            cp_id = cp.get("draft_core_point_id") or cp.get("core_point_id")
            if not cp_id:
                continue
            row = {
                "core_point_id": cp_id,
                "chapter_id": chapter_id,
                "section_id": section_id,
                "title_en": cp.get("title_en"),
                "title_zh": cp.get("title_zh"),
                "anchor_unit_ids": cp.get("anchor_unit_ids") or [],
                "support_unit_ids": cp.get("support_unit_ids") or [],
                "review_flags": cp.get("review_flags") or [],
                "reason": cp.get("reason"),
                "source_phase": "P2A_review",
            }
            core_points[cp_id] = row
            section_to_cp_ids[section_id].append(cp_id)
    for cp_ids in section_to_cp_ids.values():
        cp_ids.sort(key=lambda cp_id: min([unit_order_from_id(uid) for uid in core_points[cp_id].get("anchor_unit_ids") or []] or [10**9]))
    return core_points, dict(section_to_cp_ids)


def resolve_p2b_run_dir(core_point_id: str) -> Path | None:
    matches = sorted(
        [path for path in (P2_DIR / "runs").glob(f"*{core_point_id}") if (path / "parsed_response.json").exists()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def load_p2b_edges(core_points: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    skipped_exclude_count = 0
    skipped_unknown_count = 0
    for cp_id in sorted(core_points):
        run_dir = resolve_p2b_run_dir(cp_id)
        if not run_dir:
            continue
        parsed = read_json(run_dir / "parsed_response.json")
        for edge in parsed.get("core_point_unit_edges") or []:
            unit_id = edge.get("unit_id")
            if not unit_id:
                continue
            edge_type = edge.get("edge_type")
            if edge_type == "exclude":
                skipped_exclude_count += 1
                continue
            if edge_type not in P2B_POSITIVE_EDGE_TYPES:
                skipped_unknown_count += 1
                continue
            edges.append(
                {
                    "edge_id": f"p2b:{cp_id}:{unit_id}",
                    "edge_scope": "core_point_unit",
                    "source_id": cp_id,
                    "target_id": unit_id,
                    "relation_type": edge_type,
                    "source_phase": "P2B",
                    "reason": edge.get("reason"),
                }
            )
    return edges, {"skipped_exclude_edge_count": skipped_exclude_count, "skipped_unknown_edge_count": skipped_unknown_count}


def load_p2c_edges() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    aggregate_path = P2_DIR / "outputs" / "p2c_core_point_relations.jsonl"
    if aggregate_path.exists():
        rows = read_jsonl(aggregate_path)
        for rel in rows:
            rel_id = rel.get("relation_id") or f"p2c:{rel.get('source_core_point_id')}:{rel.get('target_core_point_id')}"
            edges.append(
                {
                    "edge_id": rel_id,
                    "edge_scope": "same_section_core_point",
                    "source_id": rel.get("source_core_point_id"),
                    "target_id": rel.get("target_core_point_id"),
                    "relation_type": rel.get("relation_type"),
                    "source_phase": "P2C",
                    "source_evidence_unit_ids": rel.get("source_evidence_unit_ids") or [],
                    "target_evidence_unit_ids": rel.get("target_evidence_unit_ids") or [],
                    "evidence_summary": rel.get("evidence_summary"),
                    "reason": rel.get("reason"),
                    "source_kind": rel.get("source_kind"),
                }
            )
        edges = [edge for edge in edges if edge.get("source_id") and edge.get("target_id")]
        return edges, {"source_file_count": 1, "source_file": str(aggregate_path), "deleted_relation_count": 0, "relation_count": len(edges)}

    files = sorted((P2_DIR / "outputs").glob("p2c_reviewed_relations.CH*-S*.json"))
    deleted_relation_count = 0
    for path in files:
        payload = read_json(path)
        deleted_relation_ids = set(payload.get("deleted_relation_ids") or [])
        deleted_relation_count += len(deleted_relation_ids)
        relations = payload.get("core_point_relations") or payload.get("relations") or payload.get("reviewed_relations") or []
        for rel in relations:
            rel_id = rel.get("relation_id") or f"p2c:{rel.get('source_core_point_id')}:{rel.get('target_core_point_id')}"
            if rel_id in deleted_relation_ids:
                continue
            edges.append(
                {
                    "edge_id": rel_id,
                    "edge_scope": "same_section_core_point",
                    "source_id": rel.get("source_core_point_id"),
                    "target_id": rel.get("target_core_point_id"),
                    "relation_type": rel.get("relation_type"),
                    "source_phase": "P2C",
                    "source_evidence_unit_ids": rel.get("source_evidence_unit_ids") or [],
                    "target_evidence_unit_ids": rel.get("target_evidence_unit_ids") or [],
                    "evidence_summary": rel.get("evidence_summary"),
                    "reason": rel.get("reason"),
                }
            )
    edges = [edge for edge in edges if edge.get("source_id") and edge.get("target_id")]
    return edges, {"source_file_count": len(files), "deleted_relation_count": deleted_relation_count, "relation_count": len(edges)}


def load_p3_edges() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    aggregate_path = P3_DIR / "outputs" / "p3_relation_unit_evidence.jsonl"
    if aggregate_path.exists():
        files = [aggregate_path]
        status = "available"
    else:
        files = sorted((P3_DIR / "outputs").glob("p3b_relation_unit_evidence_batch*.jsonl"))
        status = "partial" if files else "missing"
    for path in files:
        for rel in read_jsonl(path):
            rel_id = rel.get("p3_relation_id") or rel.get("relation_id")
            edges.append(
                {
                    "edge_id": rel_id,
                    "edge_scope": "same_chapter_core_point",
                    "source_id": rel.get("source_core_point_id"),
                    "target_id": rel.get("target_core_point_id"),
                    "relation_type": rel.get("relation_type"),
                    "source_phase": "P3B",
                    "source_evidence_unit_ids": rel.get("source_evidence_unit_ids") or [],
                    "target_evidence_unit_ids": rel.get("target_evidence_unit_ids") or [],
                    "support_strength": rel.get("support_strength"),
                    "evidence_summary": rel.get("evidence_summary"),
                }
            )
    metadata = {
        "status": status,
        "source_files": [path.name for path in files],
        "relation_count": len(edges),
    }
    if files and not aggregate_path.exists():
        chapters = sorted({part for path in files for part in re.findall(r"CH\d+", path.name)})
        metadata["covered_chapter_markers"] = chapters
    if aggregate_path.exists():
        metadata["source_file"] = str(aggregate_path)
    return edges, metadata


def load_p4_edges() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = P4_DIR / "outputs" / "p4c_reviewed_cross_chapter_relation_evidence.jsonl"
    rows = read_jsonl(path)
    edges = []
    for rel in rows:
        edges.append(
            {
                "edge_id": rel.get("p4_relation_id"),
                "edge_scope": "cross_chapter_core_point",
                "source_id": rel.get("source_core_point_id"),
                "target_id": rel.get("target_core_point_id"),
                "relation_type": rel.get("relation_type"),
                "source_phase": "P4C",
                "source_evidence_unit_ids": rel.get("source_evidence_unit_ids") or [],
                "target_evidence_unit_ids": rel.get("target_evidence_unit_ids") or [],
                "support_strength": rel.get("support_strength"),
                "evidence_summary": rel.get("evidence_summary"),
                "source_title_en": (rel.get("p4_relation") or {}).get("source_title_en"),
                "target_title_en": (rel.get("p4_relation") or {}).get("target_title_en"),
            }
        )
    return edges, {"status": "available" if path.exists() else "missing", "relation_count": len(edges), "source_file": str(path)}


def load_p5_metadata() -> dict[str, Any]:
    path = P5_DIR / "outputs" / "p5c_alias_index.json"
    if not path.exists():
        return {"status": "missing", "alias_group_count": 0, "term_count": 0}
    index = json.loads(path.read_text(encoding="utf-8-sig"))
    alias_groups = index.get("alias_groups") or []
    unique_terms = {
        term
        for group in alias_groups
        for term in (group.get("all_terms") or [])
        if isinstance(term, str) and term.strip()
    }
    summary = index.get("summary") or {}
    return {
        "status": "available",
        "alias_group_count": summary.get("alias_group_count", len(alias_groups)),
        "term_count": len(unique_terms),
        "source_file": str(path),
        "usage": "option_evidence_retrieval_index",
        "not_kg_edge": True,
    }


def key_unit_ids(cp: dict[str, Any], p2b_edges_by_cp: dict[str, list[dict[str, Any]]]) -> list[str]:
    cp_id = cp["core_point_id"]
    unit_ids = list(cp.get("anchor_unit_ids") or [])
    if len(unit_ids) >= 5:
        return unit_ids[:5]
    candidates = sorted(
        p2b_edges_by_cp.get(cp_id, []),
        key=lambda edge: (EDGE_PRIORITY.get(str(edge.get("relation_type")), 50), unit_order_from_id(edge.get("target_id") or "")),
    )
    for edge in candidates:
        uid = edge.get("target_id")
        if uid and uid not in unit_ids and edge.get("relation_type") != "exclude":
            unit_ids.append(uid)
        if len(unit_ids) >= 5:
            break
    return unit_ids


def build_graph() -> tuple[dict[str, Any], dict[str, Any]]:
    chapters, sections, units = load_p1()
    core_points, section_to_cp_ids = load_p2a_reviewed()
    p2b_edges, p2b_meta = load_p2b_edges(core_points)
    p2c_edges, p2c_meta = load_p2c_edges()
    p3_edges, p3_meta = load_p3_edges()
    p4_edges, p4_meta = load_p4_edges()
    p5_meta = load_p5_metadata()

    p2b_by_cp: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in p2b_edges:
        p2b_by_cp[edge["source_id"]].append(edge)

    for section_id, cp_ids in section_to_cp_ids.items():
        if section_id in sections:
            sections[section_id]["core_point_ids"] = cp_ids
    for cp in core_points.values():
        cp["key_unit_ids"] = key_unit_ids(cp, p2b_by_cp)

    structure_edges: list[dict[str, Any]] = []
    for section in sections.values():
        structure_edges.append(
            {
                "edge_id": f"structure:{section['chapter_id']}:{section['section_id']}",
                "edge_scope": "chapter_section",
                "source_id": section["chapter_id"],
                "target_id": section["section_id"],
                "relation_type": "contains",
                "source_phase": "P1",
            }
        )
        for cp_id in section.get("core_point_ids") or []:
            structure_edges.append(
                {
                    "edge_id": f"structure:{section['section_id']}:{cp_id}",
                    "edge_scope": "section_core_point",
                    "source_id": section["section_id"],
                    "target_id": cp_id,
                    "relation_type": "contains",
                    "source_phase": "P2A_review",
                }
            )

    edges = structure_edges + p2b_edges + p2c_edges + p3_edges + p4_edges
    known_limits = []
    if p3_meta.get("status") != "available":
        known_limits.append("P3 is treated as partial until all chapter batches are present.")
    known_limits.append("P4 is based on reviewed Top300 cross-chapter candidates, not exhaustive all-pairs coverage.")

    graph = {
        "schema_version": "v7_kg_retrieval_graph_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "chapters": chapters,
        "sections": sorted(sections.values(), key=lambda row: (row["chapter_id"], row.get("section_order") or 10**9)),
        "core_points": sorted(core_points.values(), key=lambda row: (row["chapter_id"], row["section_id"], min([unit_order_from_id(uid) for uid in row.get("anchor_unit_ids") or []] or [10**9]))),
        "units": sorted(units.values(), key=lambda row: row.get("unit_order") or 10**9),
        "edges": edges,
        "metadata": {
            "pipeline": "P0-P6",
            "p1": {"status": "available", "chapter_count": len(chapters), "section_count": len(sections), "unit_count": len(units)},
            "p2": {
                "status": "available",
                "core_point_count": len(core_points),
                "core_point_unit_edge_count": len(p2b_edges),
                "same_section_relation_count": len(p2c_edges),
                "p2b": p2b_meta,
                "p2c": p2c_meta,
            },
            "p3": p3_meta,
            "p4": p4_meta,
            "p5": p5_meta,
            "known_limits": known_limits,
        },
    }
    report = build_light_check(graph)
    return graph, report


def build_light_check(graph: dict[str, Any]) -> dict[str, Any]:
    cp_ids = {cp["core_point_id"] for cp in graph["core_points"]}
    unit_ids = {unit["unit_id"] for unit in graph["units"]}
    section_ids = {section["section_id"] for section in graph["sections"]}
    missing_edge_refs: list[dict[str, Any]] = []
    duplicate_edge_ids = [edge_id for edge_id, count in Counter(edge.get("edge_id") for edge in graph["edges"]).items() if edge_id and count > 1]
    blank_edge_id_count = sum(1 for edge in graph["edges"] if not edge.get("edge_id"))
    exclude_edge_count = sum(1 for edge in graph["edges"] if edge.get("relation_type") == "exclude")
    cp_unit_edges_by_cp: dict[str, int] = defaultdict(int)
    relation_edges = []
    for edge in graph["edges"]:
        scope = edge.get("edge_scope")
        source = edge.get("source_id")
        target = edge.get("target_id")
        if scope == "section_core_point":
            if source not in section_ids or target not in cp_ids:
                missing_edge_refs.append(edge)
        elif scope == "core_point_unit":
            if source not in cp_ids or target not in unit_ids:
                missing_edge_refs.append(edge)
            cp_unit_edges_by_cp[source] += 1
        elif scope in {"same_section_core_point", "same_chapter_core_point", "cross_chapter_core_point"}:
            relation_edges.append(edge)
            if source not in cp_ids or target not in cp_ids:
                missing_edge_refs.append(edge)
    cp_without_unit_edges = sorted(cp_id for cp_id in cp_ids if cp_unit_edges_by_cp.get(cp_id, 0) == 0)
    sections_without_cp = sorted(section["section_id"] for section in graph["sections"] if not section.get("core_point_ids"))
    return {
        "core_point_count": len(cp_ids),
        "unit_count": len(unit_ids),
        "section_count": len(section_ids),
        "edge_count": len(graph["edges"]),
        "relation_edge_count": len(relation_edges),
        "cp_without_unit_edges": cp_without_unit_edges,
        "sections_without_cp": sections_without_cp,
        "missing_edge_ref_count": len(missing_edge_refs),
        "missing_edge_refs_sample": missing_edge_refs[:20],
        "duplicate_edge_id_count": len(duplicate_edge_ids),
        "duplicate_edge_ids_sample": duplicate_edge_ids[:20],
        "blank_edge_id_count": blank_edge_id_count,
        "exclude_edge_count": exclude_edge_count,
    }


def render_light_check(report: dict[str, Any], graph: dict[str, Any]) -> str:
    metadata = graph["metadata"]
    lines = [
        "# P6 light check",
        "",
        f"- generated_at: {graph['generated_at']}",
        f"- chapters: {metadata['p1']['chapter_count']}",
        f"- sections: {metadata['p1']['section_count']}",
        f"- units: {metadata['p1']['unit_count']}",
        f"- core_points: {metadata['p2']['core_point_count']}",
        f"- edges: {report['edge_count']}",
        f"- relation_edges: {report['relation_edge_count']}",
        f"- p5_alias_groups: {metadata['p5'].get('alias_group_count', 0)} (external retrieval index)",
        f"- p5_terms: {metadata['p5'].get('term_count', 0)} (external retrieval terms)",
        "",
        "## Input Status",
        "",
        f"- P3: {metadata['p3']['status']} ({metadata['p3']['relation_count']} relation evidence edges)",
        f"- P4: {metadata['p4']['status']} ({metadata['p4']['relation_count']} relation evidence edges)",
        f"- P5: {metadata['p5']['status']} ({metadata['p5'].get('alias_group_count', 0)} alias groups, external retrieval index)",
        "",
        "## Checks",
        "",
        f"- cp_without_unit_edges: {len(report['cp_without_unit_edges'])}",
        f"- sections_without_cp: {len(report['sections_without_cp'])}",
        f"- missing_edge_ref_count: {report['missing_edge_ref_count']}",
        f"- duplicate_edge_id_count: {report['duplicate_edge_id_count']}",
        f"- blank_edge_id_count: {report['blank_edge_id_count']}",
        f"- exclude_edge_count: {report['exclude_edge_count']}",
        f"- p2b_skipped_exclude_edges: {metadata['p2']['p2b']['skipped_exclude_edge_count']}",
        f"- p2c_source_files: {metadata['p2']['p2c']['source_file_count']}",
        f"- p2c_deleted_relations: {metadata['p2']['p2c']['deleted_relation_count']}",
        "",
    ]
    if report["sections_without_cp"]:
        lines.append("## Sections Without CP")
        lines.append("")
        lines.extend(f"- {section_id}" for section_id in report["sections_without_cp"][:80])
        lines.append("")
    if report["cp_without_unit_edges"]:
        lines.append("## CP Without Unit Edges")
        lines.append("")
        lines.extend(f"- {cp_id}" for cp_id in report["cp_without_unit_edges"][:80])
        lines.append("")
    if report["missing_edge_refs_sample"]:
        lines.append("## Missing Edge Ref Sample")
        lines.append("")
        for edge in report["missing_edge_refs_sample"]:
            lines.append(f"- {edge.get('edge_id')}: {edge.get('source_id')} -> {edge.get('target_id')}")
    return "\n".join(lines) + "\n"


def main() -> None:
    graph, report = build_graph()
    write_json(OUT_DIR / "kg_retrieval_graph.json", graph)
    write_json(REPORT_DIR / "p6_light_check.json", report)
    write_text(REPORT_DIR / "p6_light_check.md", render_light_check(report, graph))
    print(json.dumps({"output": str(OUT_DIR / "kg_retrieval_graph.json"), "core_points": len(graph["core_points"]), "edges": len(graph["edges"]), "p5_alias_groups": graph["metadata"]["p5"].get("alias_group_count", 0)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
