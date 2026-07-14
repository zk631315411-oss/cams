from __future__ import annotations

import argparse
import html
import json
import re
import time
import uuid
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
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


TYPE_PREFIX = {
    "start": "开始",
    "trigger": "触发",
    "action": "步骤",
    "decision": "判断",
    "input": "输入",
    "standard": "标准",
    "output": "产出",
    "end": "结束",
}

MAIN_EDGE_TYPES = {"PRECEDES", "DECIDES", "PRODUCES", "FEEDBACK"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def xml_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def clean_text(value: Any, limit: int = 120) -> str:
    text = " ".join(str(value or "").split())
    if len(text) > limit:
        return text[: limit - 1] + "..."
    return text


def wrap_label(text: str, width: int = 26) -> str:
    text = clean_text(text, 260)
    chunks: list[str] = []
    line = ""
    for part in re.split(r"(\s+|/|,|;|:)", text):
        if not part:
            continue
        next_line = f"{line}{part}"
        if len(next_line) > width and line:
            chunks.append(line.strip())
            line = part.strip()
        else:
            line = next_line
    if line.strip():
        chunks.append(line.strip())
    return "<br>".join(html.escape(chunk) for chunk in chunks[:6])


def node_label(node: dict[str, Any]) -> str:
    node_type = node.get("node_type", "")
    prefix = TYPE_PREFIX.get(node_render_kind(node), node_type or "节点")
    label = wrap_label(node.get("label"), 28)
    units = ", ".join(node.get("evidence_unit_ids") or [])
    if units:
        return f"<b>{html.escape(prefix)}：</b>{label}<br><font color=\"#666666\">{html.escape(units)}</font>"
    return f"<b>{html.escape(prefix)}：</b>{label}"


def edge_label(edge: dict[str, Any], nodes_by_id: dict[str, dict[str, Any]]) -> str:
    return html.escape(render_edge_label(edge, nodes_by_id))


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
    def __init__(self, name: str, width: int = 1800, height: int = 1400):
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
        cell = ET.SubElement(
            self.root,
            "mxCell",
            {"id": cell_id, "value": value, "style": style or edge_style({}), "edge": "1", "parent": "1", "source": source, "target": target},
        )
        ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
        return cell_id

    def diagram_element(self) -> ET.Element:
        diagram = ET.Element("diagram", {"name": self.name, "id": xml_id("page")})
        diagram.append(self.model)
        return diagram


def title_style(fill: str = "#ffffff", stroke: str = "none") -> str:
    return (
        "rounded=0;whiteSpace=wrap;html=1;fillColor="
        f"{fill};strokeColor={stroke};fontStyle=1;align=center;verticalAlign=middle;fontSize=18;"
    )


def note_style(fill: str = "#fff2cc", stroke: str = "#d6b656") -> str:
    return (
        "shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;"
        f"fillColor={fill};strokeColor={stroke};fontSize=12;spacing=8;"
    )


def node_style(node_type: str, review_status: str | None = None) -> str:
    stroke = "#8f8f8f"
    width = "1.5"
    if review_status == "needs_review":
        stroke = "#d6b656"
        width = "2"

    if node_type == "start":
        shape = "ellipse"
        fill = "#dae8fc"
        stroke = "#6c8ebf" if review_status != "needs_review" else stroke
    elif node_type == "trigger":
        shape = "shape=hexagon;perimeter=hexagonPerimeter2"
        fill = "#f8cecc"
        stroke = "#b85450" if review_status != "needs_review" else stroke
    elif node_type == "action":
        shape = "rounded=1;arcSize=8"
        fill = "#e1d5e7"
        stroke = "#9673a6" if review_status != "needs_review" else stroke
    elif node_type == "decision":
        shape = "rhombus"
        fill = "#fff2cc"
        stroke = "#d79b00" if review_status != "needs_review" else stroke
    elif node_type == "standard":
        shape = "shape=parallelogram;perimeter=parallelogramPerimeter"
        fill = "#fff2cc"
        stroke = "#d6b656" if review_status != "needs_review" else stroke
    elif node_type == "input":
        shape = "shape=parallelogram;perimeter=parallelogramPerimeter"
        fill = "#ffe6cc"
        stroke = "#d79b00" if review_status != "needs_review" else stroke
    elif node_type == "output":
        shape = "shape=document;whiteSpace=wrap;boundedLbl=1"
        fill = "#d5e8d4"
        stroke = "#82b366" if review_status != "needs_review" else stroke
    elif node_type == "end":
        shape = "ellipse"
        fill = "#d5e8d4"
        stroke = "#82b366" if review_status != "needs_review" else stroke
    else:
        shape = "rounded=1;arcSize=8"
        fill = "#f5f5f5"

    return (
        f"{shape};whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
        f"strokeWidth={width};fontSize=12;align=center;verticalAlign=middle;spacing=8;"
    )


def edge_style(edge: dict[str, Any]) -> str:
    edge_type = edge.get("edge_type")
    color = "#666666"
    if edge_type == "REFERENCES":
        color = "#d6b656"
    elif edge_type == "DECIDES":
        color = "#b85450"
    elif edge_type == "PRODUCES":
        color = "#82b366"
    elif edge_type == "FEEDBACK":
        color = "#9673a6"

    dashed = ""
    if edge.get("evidence_strength") in {"functional_dependency", "needs_review"} or edge.get("review_status") == "needs_review":
        dashed = "dashed=1;"
    return f"endArrow=block;html=1;rounded=0;strokeWidth=1.5;strokeColor={color};fontSize=10;{dashed}"


def overview_page(sections: list[dict[str, Any]]) -> PageBuilder:
    page = PageBuilder("00_overview", 1800, max(1100, 180 + len(sections) * 52))
    page.vertex("P7C 人读版流程图总览", 60, 30, 680, 50, title_style())
    y = 110
    for section in sections:
        status = section["status"]
        cards = section["cards"]
        fill = "#d5e8d4" if cards and status == "ok" else "#eeeeee"
        stroke = "#82b366" if cards and status == "ok" else "#999999"
        if status == "validation_failed":
            fill, stroke = "#f8cecc", "#b85450"
        label = html.escape(
            f"{section['section_id']} | {section['section_title']} | status={status}, cards={len(cards)}, errors={section['validation_error_count']}"
        )
        page.vertex(label, 70, y, 1360, 34, f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize=12;align=left;spacing=8;")
        y += 46
    return page


def build_main_ranks(card: dict[str, Any]) -> dict[str, int]:
    nodes = {node.get("node_id"): node for node in card.get("flow_nodes") or [] if node.get("node_id")}
    main_ids = [node_id for node_id, node in nodes.items() if node_role(node) != "auxiliary"]
    outgoing: dict[str, list[str]] = defaultdict(list)
    indegree: dict[str, int] = {node_id: 0 for node_id in main_ids}
    for edge in card.get("flow_edges") or []:
        if edge.get("edge_type") not in MAIN_EDGE_TYPES:
            continue
        source = edge.get("source")
        target = edge.get("target")
        if source in indegree and target in indegree:
            outgoing[source].append(target)
            indegree[target] += 1

    queue = deque([node_id for node_id in main_ids if indegree.get(node_id, 0) == 0])
    if not queue and main_ids:
        queue.append(main_ids[0])
    ranks: dict[str, int] = {node_id: 0 for node_id in queue}
    seen: set[str] = set()
    while queue:
        source = queue.popleft()
        if source in seen:
            continue
        seen.add(source)
        for target in outgoing.get(source, []):
            ranks[target] = max(ranks.get(target, 0), ranks.get(source, 0) + 1)
            indegree[target] -= 1
            if indegree[target] <= 0:
                queue.append(target)

    next_rank = max(ranks.values(), default=-1) + 1
    for node_id in main_ids:
        if node_id not in ranks:
            ranks[node_id] = next_rank
            next_rank += 1
    return ranks


def branch_column(card: dict[str, Any], ranks: dict[str, int]) -> dict[str, int]:
    column: dict[str, int] = {node_id: 0 for node_id in ranks}
    for edge in card.get("flow_edges") or []:
        if edge.get("edge_type") != "DECIDES":
            continue
        target = edge.get("target")
        condition = str(edge.get("condition") or "").lower()
        if target not in column:
            continue
        if condition in {"no", "false", "otherwise", "if needed"} or "not" in condition:
            column[target] = max(column[target], 1)
        elif condition and condition not in {"yes", "true"}:
            column[target] = max(column[target], 1)
    return column


def card_height(card: dict[str, Any]) -> int:
    ranks = build_main_ranks(card)
    main_levels = max(ranks.values(), default=0) + 1
    aux_count = len([node for node in card.get("flow_nodes") or [] if node_role(node) == "auxiliary"])
    return max(520, 150 + main_levels * 125 + max(0, aux_count - 1) * 32)


def make_section_page(section: dict[str, Any]) -> PageBuilder:
    heights = [card_height(card) for card in section["cards"]] or [360]
    page = PageBuilder(section["section_id"], 1800, max(1100, 130 + sum(heights) + 80 * len(heights)))
    page.vertex(
        html.escape(f"{section['section_id']} {section['section_title']}"),
        250,
        30,
        1050,
        42,
        title_style(),
    )
    page.vertex(
        html.escape(f"status={section['status']} | cards={len(section['cards'])} | errors={section['validation_error_count']}"),
        430,
        78,
        680,
        28,
        "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=none;fontSize=11;align=center;fontColor=#666666;",
    )
    if not section["cards"]:
        page.vertex(
            f"<b>SKIPPED</b><br>{html.escape(clean_text(section['skip_reason'], 600))}",
            360,
            180,
            780,
            130,
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#eeeeee;strokeColor=#999999;fontSize=13;spacing=10;",
        )
        return page

    y_cursor = 145
    for card_index, card in enumerate(section["cards"], 1):
        draw_card(page, card, card_index, y_cursor)
        y_cursor += card_height(card) + 80
    return page


def draw_card(page: PageBuilder, card: dict[str, Any], card_index: int, y0: int) -> None:
    card_title = html.escape(f"{card.get('section_id')} / card {card_index}: {card.get('title')}")
    page.vertex(card_title, 320, y0, 920, 32, "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=none;fontStyle=1;fontSize=14;align=center;")
    page.vertex(
        html.escape(f"nature={card.get('card_nature')} | review={card.get('review_status')}"),
        460,
        y0 + 34,
        640,
        24,
        "rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=none;fontSize=10;fontColor=#666666;align=center;",
    )

    nodes = {node.get("node_id"): node for node in card.get("flow_nodes") or [] if node.get("node_id")}
    ranks = build_main_ranks(card)
    columns = branch_column(card, ranks)

    main_x = 655
    branch_x = 1080
    aux_x = 120
    top_y = y0 + 82
    y_gap = 125
    aux_gap = 105
    cell_ids: dict[str, str] = {}

    aux_nodes = [node for node in card.get("flow_nodes") or [] if node_role(node) == "auxiliary"]
    for idx, node in enumerate(aux_nodes):
        node_id = node.get("node_id")
        if not node_id:
            continue
        x = aux_x
        y = top_y + idx * aux_gap
        cell_ids[node_id] = page.vertex(node_label(node), x, y, 330, 74, node_style(node_render_kind(node), node.get("review_status")))

    rank_counts: dict[tuple[int, int], int] = defaultdict(int)
    for node_id, rank in sorted(ranks.items(), key=lambda item: (item[1], list(nodes).index(item[0]) if item[0] in nodes else 999)):
        node = nodes[node_id]
        col = columns.get(node_id, 0)
        offset = rank_counts[(rank, col)]
        rank_counts[(rank, col)] += 1
        x = branch_x if col else main_x
        y = top_y + rank * y_gap + offset * 92
        w, h = (260, 76)
        render_kind = node_render_kind(node)
        if render_kind == "decision":
            w, h = (270, 96)
        elif render_kind in {"start", "trigger", "output", "end"}:
            w, h = (290, 76)
        cell_ids[node_id] = page.vertex(node_label(node), x, y, w, h, node_style(render_kind, node.get("review_status")))

    for edge in card.get("flow_edges") or []:
        render_source, render_target = render_edge_endpoints(edge)
        source = cell_ids.get(render_source)
        target = cell_ids.get(render_target)
        if not source or not target:
            continue
        page.edge(source, target, edge_label(edge, nodes), edge_style(edge))

    if card.get("review_notes"):
        note_y = top_y + max(ranks.values(), default=0) * y_gap + 120
        page.vertex(
            f"<b>review_notes</b><br>{html.escape(clean_text(card.get('review_notes'), 520))}",
            1120,
            note_y,
            410,
            110,
            "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=11;align=left;verticalAlign=top;spacing=8;",
        )


def legend_page() -> PageBuilder:
    page = PageBuilder("legend", 1600, 900)
    page.vertex("图例", 580, 40, 300, 42, title_style())
    samples = [
        ("start", "开始 / 背景入口"),
        ("trigger", "触发条件 / 情境入口"),
        ("action", "处理步骤"),
        ("decision", "判断条件"),
        ("input", "输入材料"),
        ("standard", "判断标准"),
        ("output", "产出 / 记录 / 结果"),
    ]
    x, y = 110, 130
    ids: list[str] = []
    for idx, (node_type, label) in enumerate(samples):
        cx = x + (idx % 3) * 450
        cy = y + (idx // 3) * 150
        ids.append(page.vertex(f"<b>{html.escape(label)}</b>", cx, cy, 270, 78, node_style(node_type)))
    page.edge(ids[0], ids[2], "PRECEDES", edge_style({"edge_type": "PRECEDES"}))
    page.edge(ids[5], ids[2], "作为判定标准或规范依据", edge_style({"edge_type": "REFERENCES"}))
    page.edge(ids[2], ids[6], "PRODUCES", edge_style({"edge_type": "PRODUCES"}))
    page.edge(ids[3], ids[2], "DECIDES / yes", edge_style({"edge_type": "DECIDES"}))
    page.vertex("虚线 = functional_dependency 或 needs_review，需要 P7D 复核", 110, 650, 780, 56, "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;fontSize=13;align=left;spacing=10;")
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
    parser = argparse.ArgumentParser(description="Generate a readable draw.io flowchart from P7C cards.")
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR))
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    output_path = Path(args.output) if args.output else run_dir / f"{run_dir.name}_flow_readable.drawio"
    sections = load_sections(run_dir)
    pages = [overview_page(sections), legend_page()]
    pages.extend(make_section_page(section) for section in sections)
    mxfile = build_mxfile(pages)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(mxfile).write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {len(pages)} readable draw.io pages: {output_path}")


if __name__ == "__main__":
    main()

