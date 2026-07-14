from __future__ import annotations

import argparse
import json
import re
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from p7_edge_runtime import (
    node_render_kind,
    node_role,
    render_edge_endpoints,
    render_edge_label,
    section_summary_rows,
)


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
P7C_DIR = PHASE_DIR / "phases" / "P7C"
DEFAULT_RUN_DIR = P7C_DIR / "outputs" / "p7c_ds_none_c16_v1"


NATURE_COLORS = {
    "execution": ("#dae8fc", "#6c8ebf"),
    "assessment": ("#e1d5e7", "#9673a6"),
    "control": ("#d5e8d4", "#82b366"),
    "risk_indicator": ("#ffe6cc", "#d79b00"),
    "SKIP": ("#eeeeee", "#999999"),
}

NODE_COLORS = {
    "start": ("#e1d5e7", "#9673a6"),
    "trigger": ("#fff2cc", "#d6b656"),
    "action": ("#dae8fc", "#6c8ebf"),
    "decision": ("#f8cecc", "#b85450"),
    "input": ("#f5f5f5", "#666666"),
    "standard": ("#d5e8d4", "#82b366"),
    "output": ("#d5e8d4", "#82b366"),
    "end": ("#e1d5e7", "#9673a6"),
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def xml_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def clean_label(value: Any, limit: int = 90) -> str:
    text = " ".join(str(value or "").split())
    if len(text) > limit:
        return text[: limit - 1] + "..."
    return text


def card_summary(card: dict[str, Any]) -> str:
    nature = card.get("card_nature", "")
    title = card.get("title", "")
    review = card.get("review_status", "")
    node_count = len(card.get("flow_nodes") or [])
    edge_count = len(card.get("flow_edges") or [])
    return f"{nature}: {title}\nreview={review}, nodes={node_count}, edges={edge_count}"


def load_sections(run_dir: Path) -> list[dict[str, Any]]:
    summary_path = run_dir / "run_summary.json"
    summary_by_section: dict[str, dict[str, Any]] = {}
    if summary_path.exists():
        for row in section_summary_rows(read_json(summary_path)):
            summary_by_section[row.get("section_id")] = row

    sections: list[dict[str, Any]] = []
    for section_dir in sorted(path for path in run_dir.iterdir() if path.is_dir()):
        cards_path = section_dir / "cards.raw.json"
        payload = read_json(cards_path) if cards_path.exists() else {"section_id": section_dir.name, "cards": []}
        section_id = payload.get("section_id") or section_dir.name
        summary = summary_by_section.get(section_id, {})
        sections.append(
            {
                "section_id": section_id,
                "section_title": payload.get("section_title") or summary.get("section_title") or "",
                "status": summary.get("status") or "missing_summary",
                "validation_error_count": summary.get("validation_error_count"),
                "cards": payload.get("cards") or [],
                "skip_reason": payload.get("skip_reason") or summary.get("skip_reason") or "",
            }
        )
    return sections


class PageBuilder:
    def __init__(self, name: str, width: int = 2600, height: int = 1800):
        self.name = name
        self.width = width
        self.height = height
        self.model = ET.Element(
            "mxGraphModel",
            {
                "dx": "1422",
                "dy": "794",
                "grid": "1",
                "gridSize": "10",
                "guides": "1",
                "tooltips": "1",
                "connect": "1",
                "arrows": "1",
                "fold": "1",
                "page": "1",
                "pageScale": "1",
                "pageWidth": str(width),
                "pageHeight": str(height),
                "math": "0",
                "shadow": "0",
            },
        )
        self.root = ET.SubElement(self.model, "root")
        ET.SubElement(self.root, "mxCell", {"id": "0"})
        ET.SubElement(self.root, "mxCell", {"id": "1", "parent": "0"})

    def vertex(self, value: str, x: int, y: int, w: int, h: int, style: str) -> str:
        cell_id = xml_id("v")
        cell = ET.SubElement(
            self.root,
            "mxCell",
            {"id": cell_id, "value": value, "style": style, "vertex": "1", "parent": "1"},
        )
        ET.SubElement(cell, "mxGeometry", {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "as": "geometry"})
        return cell_id

    def edge(self, source: str, target: str, value: str = "", style: str = "") -> str:
        cell_id = xml_id("e")
        edge_style = style or "endArrow=block;html=1;rounded=0;strokeWidth=1.5;"
        cell = ET.SubElement(
            self.root,
            "mxCell",
            {"id": cell_id, "value": value, "style": edge_style, "edge": "1", "parent": "1", "source": source, "target": target},
        )
        ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
        return cell_id

    def diagram_element(self) -> ET.Element:
        diagram = ET.Element("diagram", {"name": self.name, "id": xml_id("page")})
        diagram.append(self.model)
        return diagram


def title_style(fill: str = "#f5f5f5", stroke: str = "#666666") -> str:
    return f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontStyle=1;align=left;verticalAlign=top;spacing=8;"


def node_style(node_type: str, review_status: str | None = None) -> str:
    fill, stroke = NODE_COLORS.get(node_type, ("#ffffff", "#666666"))
    if review_status == "needs_review":
        stroke = "#d6b656"
    shape = "rhombus" if node_type == "decision" else "rounded=1"
    if shape == "rhombus":
        return f"rhombus;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth=2;"
    return f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth=2;"


def edge_style(edge: dict[str, Any]) -> str:
    style = "endArrow=block;html=1;rounded=0;strokeWidth=1.5;"
    if edge.get("evidence_strength") in {"functional_dependency", "needs_review"} or edge.get("review_status") == "needs_review":
        style += "dashed=1;"
    if edge.get("edge_type") == "REFERENCES":
        style += "strokeColor=#82b366;"
    elif edge.get("edge_type") == "DECIDES":
        style += "strokeColor=#b85450;"
    elif edge.get("edge_type") == "PRODUCES":
        style += "strokeColor=#6c8ebf;"
    elif edge.get("edge_type") == "FEEDBACK":
        style += "strokeColor=#9673a6;"
    return style


def make_overview_page(sections: list[dict[str, Any]]) -> PageBuilder:
    page = PageBuilder("00_overview", width=2600, height=1800)
    page.vertex("P7C batch overview\np7c_ds_none_c16_v1", 40, 30, 520, 70, title_style())
    x0, y0 = 40, 140
    w, h = 280, 90
    gap_x, gap_y = 35, 35
    cols = 4
    for idx, section in enumerate(sections):
        row = idx // cols
        col = idx % cols
        x = x0 + col * (w + gap_x)
        y = y0 + row * (h + gap_y)
        cards = section["cards"]
        status = section["status"]
        errors = section["validation_error_count"]
        skip = bool(section["skip_reason"]) and not cards
        if status == "validation_failed":
            fill, stroke = "#f8cecc", "#b85450"
        elif skip:
            fill, stroke = NATURE_COLORS["SKIP"]
        elif any((card.get("review_status") == "needs_review") for card in cards):
            fill, stroke = "#fff2cc", "#d6b656"
        else:
            fill, stroke = "#d5e8d4", "#82b366"
        label = f"{section['section_id']}\n{clean_label(section['section_title'], 60)}\nstatus={status}, cards={len(cards)}, errors={errors}"
        page.vertex(label, x, y, w, h, title_style(fill, stroke))
    return page


def make_legend_page() -> PageBuilder:
    page = PageBuilder("legend", width=1600, height=1100)
    page.vertex("Legend", 40, 30, 300, 60, title_style())
    y = 130
    for label, color_key in [
        ("execution card", "execution"),
        ("assessment card", "assessment"),
        ("control card", "control"),
        ("risk indicator card", "risk_indicator"),
        ("skipped section", "SKIP"),
    ]:
        fill, stroke = NATURE_COLORS[color_key]
        page.vertex(label, 60, y, 260, 50, title_style(fill, stroke))
        y += 70
    y += 30
    node_ids: dict[str, str] = {}
    x = 60
    for node_type in ["trigger", "action", "decision", "standard", "output"]:
        node_ids[node_type] = page.vertex(node_type, x, y, 160, 60, node_style(node_type))
        x += 190
    page.edge(node_ids["trigger"], node_ids["action"], "PRECEDES", edge_style({"edge_type": "PRECEDES", "evidence_strength": "explicit"}))
    page.edge(node_ids["action"], node_ids["decision"], "DECIDES", edge_style({"edge_type": "DECIDES", "evidence_strength": "explicit"}))
    page.edge(node_ids["standard"], node_ids["action"], "作为判定标准或规范依据", edge_style({"edge_type": "REFERENCES", "evidence_strength": "explicit"}))
    page.edge(node_ids["action"], node_ids["output"], "PRODUCES", edge_style({"edge_type": "PRODUCES", "evidence_strength": "explicit"}))
    page.vertex("Dashed edge = functional_dependency / needs_review\nRed overview box = validation_failed\nYellow overview box = one or more cards need review", 60, y + 140, 700, 90, title_style("#fff2cc", "#d6b656"))
    return page


def review_reason(section: dict[str, Any]) -> bool:
    if section["status"] == "validation_failed":
        return True
    if section["section_id"] in {"CH47-S04", "CH49-S10"}:
        return True
    if section["skip_reason"] and section["section_id"] in {"CH47-S03", "CH49-S16"}:
        return True
    return any(card.get("review_status") == "needs_review" for card in section["cards"])


def make_review_queue_page(sections: list[dict[str, Any]]) -> PageBuilder:
    review_sections = [section for section in sections if review_reason(section)]
    page = PageBuilder("review_queue", width=2600, height=max(1200, 120 + len(review_sections) * 110))
    page.vertex("Review queue\nvalidation_failed, needs_review, or possible missed judgement cards", 40, 30, 760, 70, title_style("#fff2cc", "#d6b656"))
    y = 140
    for section in review_sections:
        cards = section["cards"]
        if section["status"] == "validation_failed":
            fill, stroke = "#f8cecc", "#b85450"
        elif not cards:
            fill, stroke = "#eeeeee", "#999999"
        else:
            fill, stroke = "#fff2cc", "#d6b656"
        card_titles = "; ".join(clean_label(card.get("title"), 60) for card in cards) or clean_label(section["skip_reason"], 120)
        label = f"{section['section_id']} - {clean_label(section['section_title'], 80)}\nstatus={section['status']}, cards={len(cards)}, errors={section['validation_error_count']}\n{card_titles}"
        page.vertex(label, 50, y, 1150, 85, title_style(fill, stroke))
        y += 110
    return page


def layout_nodes(nodes: list[dict[str, Any]], x0: int, y0: int) -> dict[str, tuple[int, int]]:
    main_nodes = [node for node in nodes if node_role(node) != "auxiliary"]
    aux_nodes = [node for node in nodes if node_role(node) == "auxiliary"]
    positions: dict[str, tuple[int, int]] = {}
    for idx, node in enumerate(main_nodes):
        positions[node["node_id"]] = (x0 + (idx % 5) * 260, y0 + (idx // 5) * 140)
    aux_y = y0 + ((len(main_nodes) + 4) // 5) * 140 + 90
    for idx, node in enumerate(aux_nodes):
        positions[node["node_id"]] = (x0 + (idx % 5) * 260, aux_y + (idx // 5) * 120)
    return positions


def make_section_page(section: dict[str, Any]) -> PageBuilder:
    card_count = max(1, len(section["cards"]))
    page = PageBuilder(section["section_id"], width=2600, height=max(1400, card_count * 820 + 180))
    page.vertex(
        f"{section['section_id']}\n{section['section_title']}\nstatus={section['status']}, cards={len(section['cards'])}, errors={section['validation_error_count']}",
        40,
        30,
        1000,
        80,
        title_style("#f5f5f5", "#666666"),
    )
    if not section["cards"]:
        page.vertex(f"SKIPPED\n{clean_label(section['skip_reason'], 500)}", 60, 160, 1100, 160, title_style("#eeeeee", "#999999"))
        return page

    y_base = 150
    for card_idx, card in enumerate(section["cards"], 1):
        card_y = y_base + (card_idx - 1) * 820
        nature = card.get("card_nature", "")
        fill, stroke = NATURE_COLORS.get(nature, ("#ffffff", "#666666"))
        if section["status"] == "validation_failed":
            stroke = "#b85450"
        elif card.get("review_status") == "needs_review":
            stroke = "#d6b656"
        page.vertex(card_summary(card), 60, card_y, 1050, 90, title_style(fill, stroke))
        if card.get("review_notes"):
            page.vertex(f"review_notes:\n{clean_label(card.get('review_notes'), 420)}", 1140, card_y, 900, 90, title_style("#fff2cc", "#d6b656"))

        nodes = card.get("flow_nodes") or []
        node_positions = layout_nodes(nodes, 80, card_y + 150)
        node_cell_ids: dict[str, str] = {}
        for node in nodes:
            node_id = node.get("node_id")
            if not node_id:
                continue
            x, y = node_positions.get(node_id, (80, card_y + 150))
            label = f"{node.get('node_type')}\n{clean_label(node.get('label'), 70)}\n{', '.join(node.get('evidence_unit_ids') or [])}"
            render_kind = node_render_kind(node)
            w, h = (190, 90) if render_kind == "decision" else (220, 85)
            node_cell_ids[node_id] = page.vertex(label, x, y, w, h, node_style(render_kind, node.get("review_status")))
        nodes_by_id = {node.get("node_id"): node for node in nodes if node.get("node_id")}
        for edge in card.get("flow_edges") or []:
            render_source, render_target = render_edge_endpoints(edge)
            source = node_cell_ids.get(render_source)
            target = node_cell_ids.get(render_target)
            if not source or not target:
                continue
            page.edge(source, target, render_edge_label(edge, nodes_by_id), edge_style(edge))
    return page


def build_mxfile(pages: list[PageBuilder]) -> ET.Element:
    mxfile = ET.Element(
        "mxfile",
        {
            "host": "app.diagrams.net",
            "modified": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "agent": "Codex",
            "version": "24.7.17",
            "type": "device",
        },
    )
    for page in pages:
        mxfile.append(page.diagram_element())
    return mxfile


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a multi-page draw.io review diagram from P7C cards.")
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR))
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    output_path = Path(args.output) if args.output else run_dir / f"{run_dir.name}_review.drawio"
    sections = load_sections(run_dir)
    pages = [make_overview_page(sections), make_review_queue_page(sections), make_legend_page()]
    pages.extend(make_section_page(section) for section in sections)
    mxfile = build_mxfile(pages)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(mxfile).write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {len(pages)} draw.io pages: {output_path}")


if __name__ == "__main__":
    main()

