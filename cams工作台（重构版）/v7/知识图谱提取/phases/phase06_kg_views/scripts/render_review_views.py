from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
GRAPH_PATH = PHASE_DIR / "outputs" / "kg_retrieval_graph.json"
PREVIEW_DIR = PHASE_DIR / "previews"
VAULT_DIR = PREVIEW_DIR / "kg_reading_vault"

UNIT_EDGE_LABELS = {
    "defines": "定义",
    "classifies": "分类",
    "explains": "解释",
    "states_rule": "规则",
    "describes_process": "流程",
    "indicates_risk": "风险",
    "prescribes_measure": "措施",
    "illustrates": "案例",
    "states_consequence": "后果",
    "provides_context": "背景",
}

CP_RELATION_LABELS = {
    "contains": "包含",
    "prepares": "铺垫",
    "parallels": "并列",
    "contrasts": "对比",
    "summarizes": "总结",
    "grounds": "奠基",
    "illustrates": "例证",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def clean_text(value: Any) -> str:
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    return re.sub(r"\s+", " ", text)


def short_text(value: Any, limit: int = 180) -> str:
    text = clean_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def cp_title(cp: dict[str, Any]) -> str:
    zh = clean_text(cp.get("title_zh"))
    en = clean_text(cp.get("title_en"))
    if zh and en:
        return f"{zh} / {en}"
    return zh or en or cp.get("core_point_id", "")


def cp_heading(cp: dict[str, Any]) -> str:
    return f"{cp['core_point_id']} {cp_title(cp)}"


def cp_anchor(cp: dict[str, Any]) -> str:
    return cp_heading(cp)


def cp_link(cp: dict[str, Any], cp_by_id: dict[str, dict[str, Any]]) -> str:
    chapter_id = cp.get("chapter_id") or ""
    return f"[[chapters/{chapter_id}#{cp_anchor(cp)}|{cp_title(cp)}]]"


def relation_label(relation_type: str | None) -> str:
    if not relation_type:
        return "关系"
    return CP_RELATION_LABELS.get(relation_type, relation_type)


def unit_edge_label(edge_type: str | None) -> str:
    if not edge_type:
        return "证据"
    return UNIT_EDGE_LABELS.get(edge_type, edge_type)


class GraphView:
    def __init__(self, graph: dict[str, Any]) -> None:
        self.graph = graph
        self.chapters = {row["chapter_id"]: row for row in graph["chapters"]}
        self.sections = {row["section_id"]: row for row in graph["sections"]}
        self.core_points = {row["core_point_id"]: row for row in graph["core_points"]}
        self.units = {row["unit_id"]: row for row in graph["units"]}
        self.edges = graph["edges"]
        self.cp_unit_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.cp_rel_out: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.cp_rel_in: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._index_edges()

    def _index_edges(self) -> None:
        for edge in self.edges:
            scope = edge.get("edge_scope")
            if scope == "core_point_unit":
                self.cp_unit_edges[edge.get("source_id")].append(edge)
            elif scope in {"same_section_core_point", "same_chapter_core_point", "cross_chapter_core_point"}:
                self.cp_rel_out[edge.get("source_id")].append(edge)
                self.cp_rel_in[edge.get("target_id")].append(edge)
        for edge_list in self.cp_unit_edges.values():
            edge_list.sort(key=lambda edge: self.units.get(edge.get("target_id"), {}).get("unit_order") or 10**9)
        for edge_list in list(self.cp_rel_out.values()) + list(self.cp_rel_in.values()):
            edge_list.sort(key=lambda edge: (edge.get("edge_scope") or "", edge.get("relation_type") or "", edge.get("target_id") or ""))

    def chapter_list(self) -> list[dict[str, Any]]:
        return sorted(self.graph["chapters"], key=lambda row: row["chapter_id"])

    def section_list(self, chapter: dict[str, Any]) -> list[dict[str, Any]]:
        return [self.sections[sid] for sid in chapter.get("section_ids") or [] if sid in self.sections]

    def section_cp_list(self, section: dict[str, Any]) -> list[dict[str, Any]]:
        return [self.core_points[cp_id] for cp_id in section.get("core_point_ids") or [] if cp_id in self.core_points]

    def relation_summary(self, edge: dict[str, Any], outgoing: bool, obsidian: bool = False) -> str:
        other_id = edge.get("target_id") if outgoing else edge.get("source_id")
        other = self.core_points.get(other_id)
        if not other:
            other_text = f"`{other_id}`"
        elif obsidian:
            other_text = cp_link(other, self.core_points)
        else:
            other_text = f"`{other_id}` {cp_title(other)}"
        direction = "->" if outgoing else "<-"
        scope = edge.get("edge_scope") or ""
        reason = short_text(edge.get("evidence_summary") or edge.get("reason"), 160)
        suffix = f"：{reason}" if reason else ""
        return f"{direction} **{relation_label(edge.get('relation_type'))}** ({scope}) {other_text}{suffix}"

    def unit_line(self, edge: dict[str, Any]) -> str:
        unit = self.units.get(edge.get("target_id"), {})
        text = short_text(unit.get("knowledge_zh") or unit.get("zh_display_text") or unit.get("en_quote"), 150)
        page = unit.get("printed_page") or unit.get("pdf_page") or ""
        page_text = f", p.{page}" if page else ""
        return f"`{edge.get('target_id')}` [{unit_edge_label(edge.get('relation_type'))}{page_text}] {text}"


def render_cp_block(view: GraphView, cp: dict[str, Any], level: int, obsidian: bool = False) -> list[str]:
    prefix = "#" * level
    lines = [f"{prefix} {cp_heading(cp)}", ""]
    reason = short_text(cp.get("reason"), 220)
    if reason:
        lines.extend([f"- CP 说明：{reason}"])
    key_unit_ids = cp.get("key_unit_ids") or cp.get("anchor_unit_ids") or []
    if key_unit_ids:
        lines.append(f"- key_units: {', '.join(f'`{uid}`' for uid in key_unit_ids[:5])}")
    unit_edges = view.cp_unit_edges.get(cp["core_point_id"], [])
    if unit_edges:
        lines.extend(["", "证据 units："])
        for edge in unit_edges:
            lines.append(f"- {view.unit_line(edge)}")
    outgoing = view.cp_rel_out.get(cp["core_point_id"], [])
    incoming = view.cp_rel_in.get(cp["core_point_id"], [])
    if outgoing or incoming:
        lines.extend(["", "关系边："])
        for edge in outgoing:
            lines.append(f"- {view.relation_summary(edge, outgoing=True, obsidian=obsidian)}")
        for edge in incoming:
            lines.append(f"- {view.relation_summary(edge, outgoing=False, obsidian=obsidian)}")
    lines.append("")
    return lines


def render_study_tree(view: GraphView) -> str:
    meta = view.graph.get("metadata") or {}
    lines = [
        "# v7 KG Study Tree",
        "",
        f"- generated_at: {view.graph.get('generated_at')}",
        f"- chapters: {len(view.graph['chapters'])}",
        f"- sections: {len(view.graph['sections'])}",
        f"- core_points: {len(view.graph['core_points'])}",
        f"- units: {len(view.graph['units'])}",
        f"- edges: {len(view.graph['edges'])}",
        f"- P3: {meta.get('p3', {}).get('status')} ({meta.get('p3', {}).get('relation_count')} relations)",
        f"- P4: {meta.get('p4', {}).get('status')} ({meta.get('p4', {}).get('relation_count')} relations)",
        f"- P5: {meta.get('p5', {}).get('status')} ({meta.get('p5', {}).get('alias_group_count')} alias groups, external retrieval index)",
        "",
    ]
    for chapter in view.chapter_list():
        lines.extend([f"# {chapter['chapter_id']} {chapter.get('chapter_title') or ''}", ""])
        for section in view.section_list(chapter):
            cp_list = view.section_cp_list(section)
            lines.extend([f"## {section['section_id']} {section.get('section_title') or ''}", ""])
            if not cp_list:
                lines.extend(["- 无 core_point。", ""])
                continue
            for cp in cp_list:
                lines.extend(render_cp_block(view, cp, level=3, obsidian=False))
    return "\n".join(lines).rstrip() + "\n"


def render_vault_index(view: GraphView) -> str:
    lines = [
        "# v7 KG Reading Vault",
        "",
        "## 审阅顺序",
        "",
        "1. 先按章通读 CP 是否像教材复习骨架。",
        "2. 再抽查 CP 下的 unit 是否支撑该 CP。",
        "3. 最后看关系边是否对复习有帮助，弱关系直接记下待删。",
        "",
        "## 入口",
        "",
        "- [[99_review_dashboard|Review Dashboard]]",
        "",
        "## Chapters",
        "",
    ]
    for chapter in view.chapter_list():
        title = chapter.get("chapter_title") or ""
        lines.append(f"- [[chapters/{chapter['chapter_id']}|{chapter['chapter_id']} {title}]]")
    return "\n".join(lines).rstrip() + "\n"


def render_dashboard(view: GraphView) -> str:
    empty_sections = [section for section in view.graph["sections"] if not section.get("core_point_ids")]
    lines = [
        "# Review Dashboard",
        "",
        "## 总量",
        "",
        f"- chapters: {len(view.graph['chapters'])}",
        f"- sections: {len(view.graph['sections'])}",
        f"- core_points: {len(view.graph['core_points'])}",
        f"- units: {len(view.graph['units'])}",
        f"- edges: {len(view.graph['edges'])}",
        "",
        "## 需要注意",
        "",
    ]
    if empty_sections:
        lines.append("### Sections Without CP")
        lines.append("")
        for section in empty_sections:
            chapter_id = section.get("chapter_id")
            lines.append(f"- [[chapters/{chapter_id}#{section['section_id']} {section.get('section_title') or ''}|{section['section_id']}]] {section.get('section_title') or ''}")
        lines.append("")
    lines.extend([
        "### Relation Edge Counts",
        "",
        f"- same section CP relations: {sum(1 for e in view.edges if e.get('edge_scope') == 'same_section_core_point')}",
        f"- same chapter CP relations: {sum(1 for e in view.edges if e.get('edge_scope') == 'same_chapter_core_point')}",
        f"- cross chapter CP relations: {sum(1 for e in view.edges if e.get('edge_scope') == 'cross_chapter_core_point')}",
        "",
    ])
    return "\n".join(lines).rstrip() + "\n"


def render_chapter_file(view: GraphView, chapter: dict[str, Any]) -> str:
    lines = [f"# {chapter['chapter_id']} {chapter.get('chapter_title') or ''}", "", "[[../00_index|Index]]", ""]
    for section in view.section_list(chapter):
        lines.extend([f"## {section['section_id']} {section.get('section_title') or ''}", ""])
        cp_list = view.section_cp_list(section)
        if not cp_list:
            lines.extend(["- 无 core_point。", ""])
            continue
        for cp in cp_list:
            lines.extend(render_cp_block(view, cp, level=3, obsidian=True))
    return "\n".join(lines).rstrip() + "\n"


def render_vault(view: GraphView) -> None:
    if VAULT_DIR.exists():
        shutil.rmtree(VAULT_DIR)
    write_text(VAULT_DIR / "00_index.md", render_vault_index(view))
    write_text(VAULT_DIR / "99_review_dashboard.md", render_dashboard(view))
    for chapter in view.chapter_list():
        write_text(VAULT_DIR / "chapters" / f"{chapter['chapter_id']}.md", render_chapter_file(view, chapter))


def main() -> None:
    graph = read_json(GRAPH_PATH)
    view = GraphView(graph)
    write_text(PREVIEW_DIR / "kg_study_tree.md", render_study_tree(view))
    render_vault(view)
    print(json.dumps({"study_tree": str(PREVIEW_DIR / "kg_study_tree.md"), "vault": str(VAULT_DIR)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
