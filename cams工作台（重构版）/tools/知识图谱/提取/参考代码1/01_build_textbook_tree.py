"""
v4.3 Step 1: build a Tree-KG-style textbook tree from structured markdown.

Outputs:
  - textbook_tree.json
  - tree_nodes.jsonl
  - tree_edges.jsonl
  - leaf_sections.jsonl
  - tree_report.md
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR / "v4_3_config.json"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "中间产物"

HEADING_RE = re.compile(r"^(#{1,5})\s+(.+?)\s*$")
CHAPTER_NO_RE = re.compile(r"第\s*(\d+)\s*章")
SECTION_NO_RE = re.compile(r"^(\d+)\.(\d+)")
SUBSECTION_NO_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)")
PSEUDO_SUBSECTION_RE = re.compile(r"^\*\*(应用小天地[^*]*|补充题[^*]*|思考题[^*]*)\*\*\s*$")
BARE_EXAMPLE_RE = re.compile(r"^例\s*([0-9一二三四五六七八九十]+)")
PURE_NUMBERED_ANCHOR_RE = re.compile(r"^[\u4e00-\u9fffA-Za-z]+[0-9一二三四五六七八九十]+$")


@dataclass
class Heading:
    line_index: int
    level: int
    title: str


@dataclass
class Anchor:
    anchor_id: str
    title: str
    anchor_type: str
    source_label: str
    line_start: int
    line_end: int
    text: str


@dataclass
class LeafSection:
    section_node_id: str
    textbook_id: str
    textbook_name: str
    chapter_node_id: str
    section_parent_id: str
    chapter: str
    chapter_order: int
    section: str
    section_order: int
    subsection: str
    subsection_order: int
    source_scope: str
    line_start: int
    line_end: int
    text: str
    anchors: list[Anchor] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build v4.3 textbook tree.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input", type=Path, default=None, help="Override config input path.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Override config output dir.")
    parser.add_argument("--max-chars", type=int, default=18000)
    return parser.parse_args()


def read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}. Run 00_prepare_config.py first.")
    return json.loads(path.read_text(encoding="utf-8"))


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Input markdown not found: {path}")
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def previous_nonblank_is_anchor(lines: list[str], line_index: int, title: str) -> bool:
    for idx in range(line_index - 1, -1, -1):
        stripped = lines[idx].strip()
        if not stripped:
            continue
        return stripped == f"##### {title}"
    return False


def collect_headings(lines: list[str]) -> list[Heading]:
    headings: list[Heading] = []
    for idx, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if match:
            headings.append(Heading(idx, len(match.group(1)), match.group(2).strip()))
            continue
        pseudo = PSEUDO_SUBSECTION_RE.match(line.strip())
        if pseudo:
            headings.append(Heading(idx, 3, pseudo.group(1).strip()))
            continue
        bare_example = BARE_EXAMPLE_RE.match(line.strip())
        if bare_example and not previous_nonblank_is_anchor(lines, idx, f"例{bare_example.group(1)}"):
            headings.append(Heading(idx, 5, f"例{bare_example.group(1)}"))
    return headings


def iter_heading_spans(headings: list[Heading], total_lines: int) -> Iterable[tuple[Heading, int]]:
    for idx, heading in enumerate(headings):
        next_line = headings[idx + 1].line_index if idx + 1 < len(headings) else total_lines
        yield heading, next_line


def line_text(lines: list[str], start: int, end: int) -> str:
    return "".join(lines[start:end]).strip()


def chapter_order(title: str) -> int:
    match = CHAPTER_NO_RE.search(title)
    return int(match.group(1)) if match else 0


def section_order(title: str) -> int:
    match = SECTION_NO_RE.match(title)
    return int(match.group(2)) if match else 0


def subsection_order(title: str, fallback: int) -> int:
    match = SUBSECTION_NO_RE.match(title)
    return int(match.group(3)) if match else fallback


def classify_source_scope(title: str) -> str:
    normalized = re.sub(r"\s+", "", title)
    if "应用小天地" in normalized or "应用举例" in normalized:
        return "example"
    if normalized.startswith("补充题") or normalized.startswith("思考题"):
        return "exercise"
    if "习题" in normalized:
        return "exercise"
    if "典型例题" in normalized or "例题" in normalized or "应用小天地" in normalized:
        return "example"
    return "core_content"


def anchor_type(title: str) -> str:
    if title.startswith("定义"):
        return "definition"
    if title.startswith("定理"):
        return "theorem"
    if title.startswith("推论"):
        return "corollary"
    if title.startswith("命题"):
        return "proposition"
    if title.startswith("引理"):
        return "lemma"
    if title.startswith("性质"):
        return "property"
    if title.startswith("公式"):
        return "formula"
    if title.startswith("例"):
        return "example"
    if title.startswith("题"):
        return "exercise"
    return "anchor"


def safe_anchor_slug(title: str, counter: int) -> str:
    compact = re.sub(r"\s+", "", title)
    compact = re.sub(r"[:：/\\|?*\"<>]", "_", compact)
    if PURE_NUMBERED_ANCHOR_RE.match(compact):
        return f"{compact}_{counter}"
    return compact or f"anchor_{counter}"


def make_node(node_id: str, node_type: str, title: str, level: int, order: int, parent_id: str = "") -> dict[str, Any]:
    return {
        "node_id": node_id,
        "node_type": node_type,
        "title": title,
        "level": level,
        "order": order,
        "parent_id": parent_id,
    }


def build_tree(
    lines: list[str],
    headings: list[Heading],
    textbook_id: str,
    textbook_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[LeafSection], list[str]]:
    nodes: list[dict[str, Any]] = [
        make_node(f"{textbook_id}:BOOK", "Book", textbook_name, 0, 0, "")
    ]
    edges: list[dict[str, Any]] = []
    leaves: list[LeafSection] = []
    warnings: list[str] = []

    chapter = ""
    chapter_num = 0
    chapter_node_id = ""
    section = ""
    section_num = 0
    section_node_id = ""
    subsection = ""
    subsection_num = 0
    subsection_node_id = ""
    subsection_counter_by_section: dict[str, int] = {}
    anchor_counter: dict[tuple[str, str], int] = {}
    pending_anchors: list[Anchor] = []
    leaf_start: int | None = None

    def add_edge(source: str, target: str, edge_type: str = "HAS_SUBSECTION") -> None:
        edges.append({
            "edge_id": f"{source}->{edge_type}->{target}",
            "source": source,
            "target": target,
            "type": edge_type,
        })

    def flush_leaf(end_line: int) -> None:
        nonlocal leaf_start, pending_anchors
        if leaf_start is None:
            return
        text = line_text(lines, leaf_start, end_line)
        if not text:
            leaf_start = None
            pending_anchors = []
            return
        if not subsection_node_id:
            warnings.append(f"leaf_without_subsection line={leaf_start + 1}")
            leaf_start = None
            pending_anchors = []
            return
        leaves.append(
            LeafSection(
                section_node_id=subsection_node_id,
                textbook_id=textbook_id,
                textbook_name=textbook_name,
                chapter_node_id=chapter_node_id,
                section_parent_id=section_node_id,
                chapter=chapter,
                chapter_order=chapter_num,
                section=section,
                section_order=section_num,
                subsection=subsection,
                subsection_order=subsection_num,
                source_scope=classify_source_scope(subsection),
                line_start=leaf_start + 1,
                line_end=end_line,
                text=text,
                anchors=pending_anchors,
            )
        )
        leaf_start = None
        pending_anchors = []

    for heading, next_line in iter_heading_spans(headings, len(lines)):
        if heading.level == 1:
            flush_leaf(heading.line_index)
            chapter = heading.title
            chapter_num = chapter_order(chapter)
            chapter_node_id = f"{textbook_id}:C{chapter_num:02d}"
            nodes.append(make_node(chapter_node_id, "Chapter", chapter, 1, chapter_num, f"{textbook_id}:BOOK"))
            add_edge(f"{textbook_id}:BOOK", chapter_node_id)
            section = ""
            section_num = 0
            section_node_id = ""
            subsection = ""
            subsection_num = 0
            subsection_node_id = ""
            subsection_counter_by_section.clear()
            anchor_counter.clear()
            continue

        if heading.level == 2:
            flush_leaf(heading.line_index)
            section = heading.title
            section_num = section_order(section)
            section_node_id = f"{textbook_id}:C{chapter_num:02d}:S{section_num:02d}"
            nodes.append(make_node(section_node_id, "Section", section, 2, section_num, chapter_node_id))
            add_edge(chapter_node_id, section_node_id)
            subsection = ""
            subsection_num = 0
            subsection_node_id = ""
            subsection_counter_by_section.clear()
            anchor_counter.clear()

            prose = line_text(lines, heading.line_index + 1, next_line)
            if prose and next_line > heading.line_index + 1:
                subsection = ""
                subsection_num = 0
                subsection_node_id = f"{textbook_id}:C{chapter_num:02d}:S{section_num:02d}:U00"
                nodes.append(make_node(subsection_node_id, "Subsection", f"{section} 导入", 3, 0, section_node_id))
                add_edge(section_node_id, subsection_node_id)
                leaf_start = heading.line_index + 1
                flush_leaf(next_line)
            continue

        if heading.level == 3:
            flush_leaf(heading.line_index)
            section_key = f"C{chapter_num:02d}:S{section_num:02d}"
            subsection_counter_by_section[section_key] = subsection_counter_by_section.get(section_key, 0) + 1
            subsection = heading.title
            subsection_num = subsection_order(subsection, subsection_counter_by_section[section_key])
            subsection_node_id = f"{textbook_id}:C{chapter_num:02d}:S{section_num:02d}:U{subsection_num:02d}"
            nodes.append(make_node(subsection_node_id, "Subsection", subsection, 3, subsection_num, section_node_id))
            add_edge(section_node_id, subsection_node_id)
            leaf_start = heading.line_index
            continue

        if heading.level == 5:
            if leaf_start is None:
                if not section_node_id:
                    section = f"{chapter} 导入"
                    section_num = 0
                    section_node_id = f"{textbook_id}:C{chapter_num:02d}:S00"
                    if not any(node["node_id"] == section_node_id for node in nodes):
                        nodes.append(make_node(section_node_id, "Section", section, 2, section_num, chapter_node_id))
                        add_edge(chapter_node_id, section_node_id)
                subsection = subsection or section or f"{chapter} 导入"
                subsection_num = subsection_num or 0
                subsection_node_id = subsection_node_id or f"{textbook_id}:C{chapter_num:02d}:S{section_num:02d}:U00"
                if not any(node["node_id"] == subsection_node_id for node in nodes):
                    nodes.append(make_node(subsection_node_id, "Subsection", subsection, 3, subsection_num, section_node_id))
                    add_edge(section_node_id, subsection_node_id)
                leaf_start = heading.line_index
            key = (subsection_node_id, heading.title)
            anchor_counter[key] = anchor_counter.get(key, 0) + 1
            slug = safe_anchor_slug(heading.title, anchor_counter[key])
            anchor_id = f"{subsection_node_id}:{slug}"
            pending_anchors.append(
                Anchor(
                    anchor_id=anchor_id,
                    title=heading.title,
                    anchor_type=anchor_type(heading.title),
                    source_label=f"{heading.title}(§{section or chapter})",
                    line_start=heading.line_index + 1,
                    line_end=next_line,
                    text=line_text(lines, heading.line_index, next_line),
                )
            )

    flush_leaf(len(lines))

    for leaf in leaves:
        if leaf.source_scope != "exercise" and not leaf.anchors:
            warnings.append(f"{leaf.section_node_id} has no anchors: {leaf.subsection or leaf.section}")

    return nodes, edges, leaves, warnings


def leaf_to_dict(leaf: LeafSection) -> dict[str, Any]:
    return {
        "section_node_id": leaf.section_node_id,
        "textbook_id": leaf.textbook_id,
        "textbook_name": leaf.textbook_name,
        "chapter_node_id": leaf.chapter_node_id,
        "section_parent_id": leaf.section_parent_id,
        "chapter": leaf.chapter,
        "chapter_order": leaf.chapter_order,
        "section": leaf.section,
        "section_order": leaf.section_order,
        "subsection": leaf.subsection,
        "subsection_order": leaf.subsection_order,
        "source_scope": leaf.source_scope,
        "line_start": leaf.line_start,
        "line_end": leaf.line_end,
        "char_count": len(leaf.text),
        "anchor_count": len(leaf.anchors),
        "anchors": [
            {
                "anchor_id": anchor.anchor_id,
                "title": anchor.title,
                "anchor_type": anchor.anchor_type,
                "source_label": anchor.source_label,
                "line_start": anchor.line_start,
                "line_end": anchor.line_end,
                "char_count": len(anchor.text),
                "text": anchor.text,
            }
            for anchor in leaf.anchors
        ],
        "text": leaf.text,
    }


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def write_report(path: Path, input_path: Path, nodes: list[dict[str, Any]], edges: list[dict[str, Any]], leaves: list[LeafSection], warnings: list[str], max_chars: int) -> None:
    scope_counts: dict[str, int] = {}
    for leaf in leaves:
        scope_counts[leaf.source_scope] = scope_counts.get(leaf.source_scope, 0) + 1
    long_leaves = [leaf for leaf in leaves if len(leaf.text) > max_chars]
    lines = [
        "# v4.3 Step 1 Textbook Tree Report",
        "",
        f"- input: `{input_path}`",
        f"- tree_nodes: {len(nodes)}",
        f"- tree_edges: {len(edges)}",
        f"- leaf_sections: {len(leaves)}",
        f"- core_content: {scope_counts.get('core_content', 0)}",
        f"- example: {scope_counts.get('example', 0)}",
        f"- exercise: {scope_counts.get('exercise', 0)}",
        f"- long_leaf_sections(>{max_chars} chars): {len(long_leaves)}",
        "",
        "## Long Leaf Sections",
    ]
    if long_leaves:
        for leaf in long_leaves[:30]:
            lines.append(f"- {leaf.section_node_id} `{leaf.subsection or leaf.section}` chars={len(leaf.text)}")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings"])
    lines.extend(f"- {w}" for w in warnings[:200]) if warnings else lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    input_path = args.input or Path(config["source"]["input_path"])
    output_dir = args.output_dir or Path(config["output"]["intermediate_dir"])
    textbook_id = config["source"]["textbook_id"]
    textbook_name = config["source"]["textbook_name"]

    lines = read_lines(input_path)
    headings = collect_headings(lines)
    nodes, edges, leaves, warnings = build_tree(lines, headings, textbook_id, textbook_name)

    output_dir.mkdir(parents=True, exist_ok=True)
    tree_path = output_dir / "textbook_tree.json"
    nodes_path = output_dir / "tree_nodes.jsonl"
    edges_path = output_dir / "tree_edges.jsonl"
    leaves_path = output_dir / "leaf_sections.jsonl"
    report_path = output_dir / "tree_report.md"

    tree_path.write_text(
        json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    node_count = write_jsonl(nodes_path, nodes)
    edge_count = write_jsonl(edges_path, edges)
    leaf_count = write_jsonl(leaves_path, (leaf_to_dict(leaf) for leaf in leaves))
    write_report(report_path, input_path, nodes, edges, leaves, warnings, args.max_chars)

    print(f"[OK] tree -> {tree_path}")
    print(f"[OK] nodes={node_count} -> {nodes_path}")
    print(f"[OK] edges={edge_count} -> {edges_path}")
    print(f"[OK] leaf_sections={leaf_count} -> {leaves_path}")
    print(f"[OK] report -> {report_path}")
    if warnings:
        print(f"[WARN] {len(warnings)} warnings; see tree_report.md")


if __name__ == "__main__":
    main()
