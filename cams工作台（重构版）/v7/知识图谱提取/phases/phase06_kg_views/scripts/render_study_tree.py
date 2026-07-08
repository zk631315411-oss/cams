from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
DEFAULT_GRAPH = PHASE_DIR / "outputs" / "kg_retrieval_graph.json"
PREVIEW_DIR = PHASE_DIR / "previews"
TREE_PATH = PREVIEW_DIR / "kg_study_tree.md"
VAULT_DIR = PREVIEW_DIR / "kg_reading_vault"
REPORT_DIR = PHASE_DIR / "reports"

RELATION_LABELS = {
    "prepares": "铺垫",
    "contains": "包含",
    "parallels": "并列",
    "contrasts": "对比",
    "illustrates": "例示",
    "grounds": "支撑",
    "summarizes": "总结",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def compact(text: str | None, limit: int = 120) -> str:
    value = re.sub(r"\s+", " ", text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def cp_title(cp: dict[str, Any]) -> str:
    zh = cp.get("title_zh") or ""
    en = cp.get("title_en") or ""
    if zh and en and zh != en:
        return f"{zh} / {en}"
    return zh or en or cp.get("core_point_id") or "untitled"


def unit_line(unit: dict[str, Any]) -> str:
    bits = [unit.get("unit_id") or ""]
    if unit.get("type"):
        bits.append(str(unit.get("type")))
    if unit.get("printed_page"):
        bits.append(f"p.{unit.get('printed_page')}")
    prefix = " | ".join(bit for bit in bits if bit)
    return f"`{prefix}` {compact(unit.get('knowledge_zh') or unit.get('en_quote'), 140)}"


def relation_text(edge: dict[str, Any], cp_by_id: dict[str, dict[str, Any]], current_cp_id: str) -> str:
    direction = "->" if edge.get("source_id") == current_cp_id else "<-"
    other_id = edge.get("target_id") if direction == "->" else edge.get("source_id")
    other = cp_by_id.get(other_id or "", {})
    rel_type = str(edge.get("relation_type") or "relation")
    label = RELATION_LABELS.get(rel_type, rel_type)
    scope = edge.get("edge_scope") or ""
    phase = edge.get("source_phase") or ""
    return f"`{label}` {direction} `{other_id}` {compact(cp_title(other), 80)} [{scope}; {phase}]"


def build_indexes(graph: dict[str, Any]) -> dict[str, Any]:
    chapters = sorted(graph["chapters"], key=lambda row: row.get("chapter_id") or "")
    sections = sorted(graph["sections"], key=lambda row: (row.get("chapter_id") or "", row.get("section_order") or 10**9))
    core_points = graph["core_points"]
    units = graph["units"]
    edges = graph["edges"]

    section_by_id = {row["section_id"]: row for row in sections}
    cp_by_id = {row["core_point_id"]: row for row in core_points}
    unit_by_id = {row["unit_id"]: row for row in units}
    sections_by_chapter: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cps_by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    relation_edges_by_cp: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for section in sections:
        sections_by_chapter[section.get("chapter_id") or ""].append(section)
    for cp in core_points:
        cps_by_section[cp.get("section_id") or ""].append(cp)
    for cp_list in cps_by_section.values():
        cp_list.sort(key=lambda cp: min([unit_order(uid) for uid in cp.get("key_unit_ids") or cp.get("anchor_unit_ids") or []] or [10**9]))
    for edge in edges:
        if edge.get("edge_scope") in {"same_section_core_point", "same_chapter_core_point", "cross_chapter_core_point"}:
            if edge.get("source_id"):
                relation_edges_by_cp[edge["source_id"]].append(edge)
            if edge.get("target_id"):
                relation_edges_by_cp[edge["target_id"]].append(edge)

    return {
        "chapters": chapters,
        "section_by_id": section_by_id,
        "cp_by_id": cp_by_id,
        "unit_by_id": unit_by_id,
        "sections_by_chapter": sections_by_chapter,
        "cps_by_section": cps_by_section,
        "relation_edges_by_cp": relation_edges_by_cp,
    }


def unit_order(unit_id: str) -> int:
    match = re.search(r"(\d+)$", unit_id or "")
    return int(match.group(1)) if match else 10**9


def render_chapter(chapter: dict[str, Any], indexes: dict[str, Any], *, heading_level: int = 1) -> list[str]:
    chapter_id = chapter.get("chapter_id")
    heading = "#" * heading_level
    lines = [f"{heading} {chapter_id} {chapter.get('chapter_title') or ''}".rstrip(), ""]
    for section in indexes["sections_by_chapter"].get(chapter_id, []):
        lines.append(f"{heading}# {section.get('section_id')} {section.get('section_title') or ''}".rstrip())
        lines.append("")
        cps = indexes["cps_by_section"].get(section.get("section_id") or "", [])
        if not cps:
            lines.append("- 无 core_point")
            lines.append("")
            continue
        for cp in cps:
            cp_id = cp.get("core_point_id")
            lines.append(f"- `{cp_id}` {cp_title(cp)}")
            key_unit_ids = cp.get("key_unit_ids") or cp.get("anchor_unit_ids") or []
            if key_unit_ids:
                lines.append("  - key units:")
                for unit_id in key_unit_ids[:5]:
                    unit = indexes["unit_by_id"].get(unit_id)
                    if unit:
                        lines.append(f"    - {unit_line(unit)}")
            relations = indexes["relation_edges_by_cp"].get(cp_id, [])
            if relations:
                scoped = sorted(relations, key=lambda edge: (str(edge.get("edge_scope")), str(edge.get("relation_type")), str(edge.get("edge_id"))))
                lines.append("  - relations:")
                for edge in scoped[:8]:
                    lines.append(f"    - {relation_text(edge, indexes['cp_by_id'], cp_id)}")
                if len(scoped) > 8:
                    lines.append(f"    - ... 还有 {len(scoped) - 8} 条关系")
        lines.append("")
    return lines


def render_tree(graph: dict[str, Any], indexes: dict[str, Any]) -> str:
    metadata = graph.get("metadata") or {}
    lines = [
        "# v7 KG study tree",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- source_graph_generated_at: {graph.get('generated_at')}",
        f"- chapters: {len(graph.get('chapters') or [])}",
        f"- sections: {len(graph.get('sections') or [])}",
        f"- core_points: {len(graph.get('core_points') or [])}",
        f"- edges: {len(graph.get('edges') or [])}",
        f"- P3: {(metadata.get('p3') or {}).get('status')} ({(metadata.get('p3') or {}).get('relation_count')} relation evidence edges)",
        f"- P4: {(metadata.get('p4') or {}).get('status')} ({(metadata.get('p4') or {}).get('relation_count')} relation evidence edges)",
        "",
    ]
    for chapter in indexes["chapters"]:
        lines.extend(render_chapter(chapter, indexes, heading_level=2))
    return "\n".join(lines).rstrip() + "\n"


def render_vault(graph: dict[str, Any], indexes: dict[str, Any]) -> None:
    chapter_dir = VAULT_DIR / "chapters"
    chapter_dir.mkdir(parents=True, exist_ok=True)
    index_lines = ["# v7 KG reading vault", ""]
    for chapter in indexes["chapters"]:
        chapter_id = chapter.get("chapter_id")
        filename = f"{chapter_id}.md"
        index_lines.append(f"- [[chapters/{chapter_id}|{chapter_id} {chapter.get('chapter_title') or ''}]]")
        chapter_lines = render_chapter(chapter, indexes, heading_level=1)
        write_text(chapter_dir / filename, "\n".join(chapter_lines).rstrip() + "\n")
    write_text(VAULT_DIR / "00_index.md", "\n".join(index_lines).rstrip() + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", default=str(DEFAULT_GRAPH))
    args = parser.parse_args()
    graph = read_json(Path(args.graph))
    indexes = build_indexes(graph)
    write_text(TREE_PATH, render_tree(graph, indexes))
    render_vault(graph, indexes)
    report = [
        "# P6 render report",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- study_tree: {TREE_PATH}",
        f"- vault: {VAULT_DIR}",
        f"- chapter_files: {len(indexes['chapters'])}",
    ]
    write_text(REPORT_DIR / "p6_render_report.md", "\n".join(report).rstrip() + "\n")
    print(json.dumps({"study_tree": str(TREE_PATH), "vault": str(VAULT_DIR), "chapter_files": len(indexes["chapters"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
