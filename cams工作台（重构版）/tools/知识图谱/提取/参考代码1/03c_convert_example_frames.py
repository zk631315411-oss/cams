"""
v4.3 Step 3C: convert ExampleFrame records into application-layer candidates.

This script does not overwrite formal nodes.jsonl or edges.jsonl. It produces
separate candidate files so example-derived methods, problem classes, and
USES/GETS edges can be reviewed before merging into the main KG.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "中间产物"
DEFAULT_FRAMES = DEFAULT_OUTPUT_DIR / "example_frames.jsonl"
DEFAULT_CORE_NODES = DEFAULT_OUTPUT_DIR / "nodes.jsonl"
DEFAULT_NODES_OUT = DEFAULT_OUTPUT_DIR / "example_application_nodes.jsonl"
DEFAULT_EDGES_OUT = DEFAULT_OUTPUT_DIR / "example_application_edges.jsonl"
DEFAULT_REVIEW_OUT = DEFAULT_OUTPUT_DIR / "example_application_review_queue.jsonl"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "example_application_report.md"

NODE_TYPES = {"Method", "ProblemClass"}
EDGE_TYPES = {"USES", "GETS"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert ExampleFrame records into app-layer candidates.")
    parser.add_argument("--frames", type=Path, default=DEFAULT_FRAMES)
    parser.add_argument("--core-nodes", type=Path, default=DEFAULT_CORE_NODES)
    parser.add_argument("--nodes-out", type=Path, default=DEFAULT_NODES_OUT)
    parser.add_argument("--edges-out", type=Path, default=DEFAULT_EDGES_OUT)
    parser.add_argument("--review-out", type=Path, default=DEFAULT_REVIEW_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--append", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"JSONL not found: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def open_output(path: Path, append: bool):
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("a" if append else "w", encoding="utf-8", newline="\n")


def stable_id(prefix: str, parts: list[str]) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:14]
    return f"{prefix}:{digest}"


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", "", str(name or "").strip())


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def build_core_node_index(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for node in nodes:
        names = [node.get("name", ""), *node.get("aliases", [])]
        for name in names:
            normalized = normalize_name(name)
            if normalized and normalized not in index:
                index[normalized] = node
    return index


def make_app_node(frame: dict[str, Any], name: str, node_type: str, evidence: str, confidence: float, reason: str) -> dict[str, Any]:
    textbook_id = clean_text(frame.get("textbook_id"))
    node_id = stable_id(f"{textbook_id}:app-node", [textbook_id, node_type, normalize_name(name)])
    return {
        "node_id": node_id,
        "name": name,
        "type": node_type,
        "aliases": [],
        "source_label": clean_text(frame.get("example_label")),
        "evidence_span": evidence,
        "definition": "",
        "description": reason,
        "attributes": [],
        "state_notes": [],
        "confidence": confidence,
        "reason": reason,
        "review_recommended": True,
        "review_reason": "由典型例题 ExampleFrame 转换，需人工确认可复用性。",
        "textbook_id": textbook_id,
        "textbook_name": frame.get("textbook_name", ""),
        "chapter": frame.get("chapter", ""),
        "section": frame.get("section", ""),
        "subsection": frame.get("subsection", ""),
        "section_node_id": frame.get("section_node_id", ""),
        "source_scope": frame.get("source_scope", ""),
        "line_start": frame.get("line_start", 0),
        "line_end": frame.get("line_end", 0),
        "layer": "example_application",
        "review_status": "review",
        "validation_warnings": ["example_application_node_requires_review"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_frame_id": frame.get("frame_id", ""),
    }


def make_edge(
    frame: dict[str, Any],
    source_node: dict[str, Any],
    target_node: dict[str, Any],
    edge_type: str,
    evidence: str,
    confidence: float,
    description: str,
    extra_warnings: list[str] | None = None,
) -> dict[str, Any]:
    textbook_id = clean_text(frame.get("textbook_id"))
    edge_id = stable_id(
        f"{textbook_id}:app-edge",
        [
            clean_text(source_node.get("node_id")),
            clean_text(target_node.get("node_id")),
            edge_type,
            clean_text(frame.get("frame_id")),
            evidence,
        ],
    )
    warnings = ["example_application_edge_requires_review", *(extra_warnings or [])]
    return {
        "edge_id": edge_id,
        "source_node_id": source_node.get("node_id", ""),
        "source_name": source_node.get("name", ""),
        "source_type": source_node.get("type", ""),
        "target_node_id": target_node.get("node_id", ""),
        "target_name": target_node.get("name", ""),
        "target_type": target_node.get("type", ""),
        "type": edge_type,
        "evidence_span": evidence,
        "evidence_spans": [{"role": "primary", "text": evidence}] if evidence else [],
        "description": description,
        "confidence": confidence,
        "review_recommended": True,
        "review_reason": "由典型例题 ExampleFrame 转换，需人工确认可复用性。",
        "textbook_id": textbook_id,
        "textbook_name": frame.get("textbook_name", ""),
        "chapter": frame.get("chapter", ""),
        "section": frame.get("section", ""),
        "subsection": frame.get("subsection", ""),
        "section_node_id": frame.get("section_node_id", ""),
        "source_scope": frame.get("source_scope", ""),
        "line_start": frame.get("line_start", 0),
        "line_end": frame.get("line_end", 0),
        "layer": "example_application",
        "review_status": "review",
        "validation_warnings": warnings,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_frame_id": frame.get("frame_id", ""),
    }


def main() -> None:
    args = parse_args()
    frames = read_jsonl(args.frames)
    core_nodes = read_jsonl(args.core_nodes)
    core_index = build_core_node_index(core_nodes)

    app_nodes_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    app_edges: list[dict[str, Any]] = []

    for frame in frames:
        problem_class = frame.get("problem_class", {})
        problem_node: dict[str, Any] | None = None
        problem_name = clean_text(problem_class.get("name"))
        if problem_name:
            problem_node = make_app_node(
                frame,
                problem_name,
                "ProblemClass",
                clean_text(problem_class.get("evidence_span")) or clean_text(frame.get("problem_text_span")),
                float(problem_class.get("confidence", 0) or 0),
                "由典型例题识别出的可复用题型。",
            )
            app_nodes_by_key[(problem_node["type"], normalize_name(problem_node["name"]))] = problem_node

        method_nodes: dict[str, dict[str, Any]] = {}
        for method in frame.get("methods", []):
            method_name = clean_text(method.get("name"))
            if not method_name:
                continue
            evidence = clean_text(method.get("method_marker_span")) or clean_text(method.get("operation_span"))
            node = make_app_node(
                frame,
                method_name,
                "Method",
                evidence,
                float(method.get("confidence", 0) or 0),
                "由典型例题识别出的可复用解题方法。",
            )
            key = (node["type"], normalize_name(node["name"]))
            app_nodes_by_key[key] = node
            method_nodes[normalize_name(method_name)] = node
            if problem_node:
                app_edges.append(make_edge(
                    frame,
                    problem_node,
                    node,
                    "USES",
                    evidence,
                    min(float(method.get("confidence", 0) or 0), float(problem_class.get("confidence", 0) or 0) or 1.0),
                    f"{problem_node['name']} 使用 {node['name']}。",
                ))

        for tool_use in frame.get("tool_uses", []):
            user_name = clean_text(tool_use.get("user_name"))
            tool_name = clean_text(tool_use.get("tool_name"))
            evidence = clean_text(tool_use.get("evidence_span"))
            if not user_name or not tool_name or not evidence:
                continue
            source_node = method_nodes.get(normalize_name(user_name))
            if source_node is None and problem_node and normalize_name(user_name) == normalize_name(problem_node.get("name", "")):
                source_node = problem_node
            if source_node is None:
                continue
            target_node = core_index.get(normalize_name(tool_name))
            extra_warnings: list[str] = []
            if target_node is None:
                target_node = make_app_node(
                    frame,
                    tool_name,
                    "Method" if tool_use.get("tool_type_hint") == "Method" else "ProblemClass",
                    evidence,
                    float(tool_use.get("confidence", 0) or 0),
                    "未能匹配正文核心节点，暂存为例题应用候选。",
                )
                app_nodes_by_key[(target_node["type"], normalize_name(target_node["name"]))] = target_node
                extra_warnings.append("target_not_matched_to_core_node")
            app_edges.append(make_edge(
                frame,
                source_node,
                target_node,
                "USES",
                evidence,
                float(tool_use.get("confidence", 0) or 0),
                f"{source_node['name']} 使用 {target_node['name']}。",
                extra_warnings,
            ))

    app_nodes = list(app_nodes_by_key.values())
    with (
        open_output(args.nodes_out, args.append) as nodes_f,
        open_output(args.edges_out, args.append) as edges_f,
        open_output(args.review_out, args.append) as review_f,
    ):
        for node in app_nodes:
            line = json.dumps(node, ensure_ascii=False)
            nodes_f.write(line + "\n")
            review_f.write(json.dumps({"kind": "node", **node}, ensure_ascii=False) + "\n")
        for edge in app_edges:
            line = json.dumps(edge, ensure_ascii=False)
            edges_f.write(line + "\n")
            review_f.write(json.dumps({"kind": "edge", **edge}, ensure_ascii=False) + "\n")

    report_lines = [
        "# v4.3 Step 3C Example Application Conversion Report",
        "",
        f"- frames: {len(frames)}",
        f"- application nodes: {len(app_nodes)}",
        f"- application edges: {len(app_edges)}",
        "",
        "## Node Types",
    ]
    type_counts: dict[str, int] = {}
    for node in app_nodes:
        type_counts[node["type"]] = type_counts.get(node["type"], 0) + 1
    for key in sorted(type_counts):
        report_lines.append(f"- {key}: {type_counts[key]}")
    report_lines.extend(["", "## Edge Types"])
    edge_counts: dict[str, int] = {}
    for edge in app_edges:
        edge_counts[edge["type"]] = edge_counts.get(edge["type"], 0) + 1
    for key in sorted(edge_counts):
        report_lines.append(f"- {key}: {edge_counts[key]}")
    args.report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"[OK] nodes -> {args.nodes_out}")
    print(f"[OK] edges -> {args.edges_out}")
    print(f"[OK] review -> {args.review_out}")
    print(f"[OK] report -> {args.report}")


if __name__ == "__main__":
    main()
