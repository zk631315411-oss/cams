"""
v4.3 Step 3D: normalize example-derived application candidates.

Default behavior preserves the previous development-run behavior for
reproducibility. Use --clean-flow for a strict v4.3 run: Step 3D only performs
traceable normalization and does not delete or rewrite candidates as a
substitute for Step 7 review.
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
DEFAULT_APP_NODES = DEFAULT_OUTPUT_DIR / "example_application_nodes.jsonl"
DEFAULT_APP_EDGES = DEFAULT_OUTPUT_DIR / "example_application_edges.jsonl"
DEFAULT_CORE_NODES = DEFAULT_OUTPUT_DIR / "nodes.jsonl"
DEFAULT_NODES_OUT = DEFAULT_OUTPUT_DIR / "normalized_example_application_nodes.jsonl"
DEFAULT_EDGES_OUT = DEFAULT_OUTPUT_DIR / "normalized_example_application_edges.jsonl"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "normalized_example_application_report.md"


METHOD_ALIAS_MAP = {
    "按一列展开法": "按行列展开法",
    "按一列展开": "按行列展开法",
    "行列式按一列展开": "按行列展开法",
    "行列式按第1行展开": "按行列展开法",
    "行列式按一行(列)展开": "按行列展开法",
}

DELETE_NODE_NAMES = {
    "行列式性质3",
    "行列式的性质3",
    "行列式性质：行加法",
    "组合数性质",
}

CORE_TARGET_MAP = {
    "范德蒙行列式公式": "范德蒙行列式公式",
    "代数余子式": "代数余子式",
    "行列式性质3": "一行是两组数和时可拆成两个行列式之和",
    "行列式的性质3": "一行是两组数和时可拆成两个行列式之和",
    "行列式性质：行加法": "把一行的倍数加到另一行上值不变",
    "拆分行列式法": "利用性质3拆分行列式",
    "行列式按一列展开": "行列式按第j列展开公式",
    "行列式按一行(列)展开": "行列式按第j列展开公式",
    "行列式按第1行展开": "行列式按第i行展开公式",
    "按第1行展开": "行列式按第i行展开公式",
}

DELETE_EDGE_PAIRS = {
    ("按行列展开法", "行列式性质3"),
    ("按一列展开", "行列式性质3"),
    ("行减法转化法", "行列式按一行(列)展开"),
    ("利用组合数性质降阶", "组合数性质"),
}

CORE_TARGET_TYPES = {
    "Concept",
    "Formula",
    "Theorem",
}

APP_TARGET_TYPES = {
    "Method",
    "ProblemClass",
}

FORCE_CORE_METHOD_TARGETS = {
    "拆分行列式法",
}

SOURCE_CORE_METHOD_MAP = {
    "拆分行列式法": "利用性质3拆分行列式",
}

METHOD_TOOL_TO_CORE_TARGETS = {
    "行列式按一列展开",
    "行列式按一行(列)展开",
    "行列式按第1行展开",
    "按第1行展开",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize ExampleFrame-derived application candidates.")
    parser.add_argument("--app-nodes", type=Path, default=DEFAULT_APP_NODES)
    parser.add_argument("--app-edges", type=Path, default=DEFAULT_APP_EDGES)
    parser.add_argument("--core-nodes", type=Path, default=DEFAULT_CORE_NODES)
    parser.add_argument("--nodes-out", type=Path, default=DEFAULT_NODES_OUT)
    parser.add_argument("--edges-out", type=Path, default=DEFAULT_EDGES_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--clean-flow",
        action="store_true",
        help="Disable early review decisions. Preserve questionable candidates for Step 5/Step 7.",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"JSONL not found: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def normalize_key(name: str) -> str:
    return re.sub(r"\s+", "", str(name or "").strip())


def stable_id(prefix: str, parts: list[str]) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:14]
    return f"{prefix}:{digest}"


def build_core_index(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for node in nodes:
        for name in [node.get("name", ""), *node.get("aliases", [])]:
            key = normalize_key(name)
            if key and key not in index:
                index[key] = node
    return index


def build_core_id_index(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(node.get("node_id") or ""): node for node in nodes if node.get("node_id")}


def canonical_method_name(name: str) -> str:
    return METHOD_ALIAS_MAP.get(str(name or "").strip(), str(name or "").strip())


def merge_node(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    evidence_list = base.setdefault("evidence_spans_merged", [])
    for evidence in [base.get("evidence_span", ""), incoming.get("evidence_span", "")]:
        if evidence and evidence not in evidence_list:
            evidence_list.append(evidence)
    labels = set(base.get("source_labels", []))
    if base.get("source_label"):
        labels.add(base["source_label"])
    if incoming.get("source_label"):
        labels.add(incoming["source_label"])
    base["source_labels"] = sorted(labels)
    base["confidence"] = max(float(base.get("confidence", 0) or 0), float(incoming.get("confidence", 0) or 0))
    return base


def normalize_app_nodes(
    app_nodes: list[dict[str, Any]],
    clean_flow: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], dict[str, int]]:
    normalized: dict[tuple[str, str], dict[str, Any]] = {}
    id_map: dict[str, dict[str, Any]] = {}
    counts = {"kept": 0, "deleted": 0, "merged": 0}

    for node in app_nodes:
        original_name = str(node.get("name") or "").strip()
        if not clean_flow and original_name in DELETE_NODE_NAMES:
            counts["deleted"] += 1
            continue
        node_type = node.get("type", "")
        name = canonical_method_name(original_name) if node_type == "Method" else original_name
        normalized_node = dict(node)
        normalized_node["original_name"] = original_name
        normalized_node["name"] = name
        normalized_node["review_status"] = "review"
        normalized_node["normalization_status"] = "normalized"
        normalized_node["normalized_at"] = datetime.now().isoformat(timespec="seconds")
        normalized_node["validation_warnings"] = sorted(set([
            *normalized_node.get("validation_warnings", []),
            "normalized_example_application_node",
        ]))
        normalized_node["node_id"] = stable_id(
            f"{node.get('textbook_id', '')}:norm-app-node",
            [str(node.get("textbook_id") or ""), node_type, normalize_key(name)],
        )
        key = (node_type, normalize_key(name))
        if key in normalized:
            normalized[key] = merge_node(normalized[key], normalized_node)
            counts["merged"] += 1
        else:
            normalized[key] = normalized_node
            counts["kept"] += 1
        id_map[str(node.get("node_id") or "")] = normalized[key]
    return list(normalized.values()), id_map, counts


def core_target_for_name(name: str, core_index: dict[str, dict[str, Any]], clean_flow: bool = False) -> dict[str, Any] | None:
    if clean_flow:
        return core_index.get(normalize_key(name))
    mapped = CORE_TARGET_MAP.get(str(name or "").strip(), str(name or "").strip())
    return core_index.get(normalize_key(mapped))


def expansion_formula_name_from_evidence(original_target_name: str, target_name: str, evidence: str) -> str | None:
    names = {str(original_target_name or "").strip(), str(target_name or "").strip()}
    if not (names & {"行列式按一行(列)展开", "行列式按一列展开", "行列式按第1行展开", "按第1行展开", "按行列展开法"}):
        return None

    text = str(evidence or "")
    has_row = bool(re.search(r"按第?\s*\$?\s*[\w一二三四五六七八九十0-9]+\s*\$?\s*行|按.*行展开", text))
    has_col = bool(re.search(r"按第?\s*\$?\s*[\w一二三四五六七八九十0-9]+\s*\$?\s*列|按.*列展开", text))

    if has_row and not has_col:
        return "行列式按第i行展开公式"
    if has_col and not has_row:
        return "行列式按第j列展开公式"
    if "行列式按第1行展开" in names or "按第1行展开" in names:
        return "行列式按第i行展开公式"
    if "行列式按一列展开" in names:
        return "行列式按第j列展开公式"
    return None


def should_delete_edge(source_name: str, target_name: str, original_source_name: str, original_target_name: str) -> bool:
    candidate_pairs = {
        (source_name, target_name),
        (original_source_name, original_target_name),
        (canonical_method_name(original_source_name), original_target_name),
        (source_name, original_target_name),
    }
    return any(pair in DELETE_EDGE_PAIRS for pair in candidate_pairs)


def target_should_map_to_core(edge: dict[str, Any], target_name: str) -> bool:
    original_target_name = str(edge.get("target_name") or "").strip()
    target_type = str(edge.get("target_type") or "").strip()
    source_type = str(edge.get("source_type") or "").strip()

    if target_type in CORE_TARGET_TYPES:
        return True
    if original_target_name in FORCE_CORE_METHOD_TARGETS:
        return True
    if original_target_name in CORE_TARGET_MAP and original_target_name in DELETE_NODE_NAMES:
        return True
    if source_type == "Method" and original_target_name in METHOD_TOOL_TO_CORE_TARGETS:
        return True
    if source_type == "Method" and target_name in METHOD_TOOL_TO_CORE_TARGETS:
        return True
    if target_type not in APP_TARGET_TYPES and original_target_name in CORE_TARGET_MAP:
        return True
    return False


def resolve_target_node(
    edge: dict[str, Any],
    target_name: str,
    app_node_id_map: dict[str, dict[str, Any]],
    core_index: dict[str, dict[str, Any]],
    core_id_index: dict[str, dict[str, Any]],
    clean_flow: bool = False,
) -> tuple[dict[str, Any] | None, str, str]:
    target_id = str(edge.get("target_node_id") or "")
    original_target_name = str(edge.get("target_name") or "").strip()

    if target_id in core_id_index:
        return core_id_index[target_id], "core", "target_core_mapped"

    if clean_flow:
        target_node = app_node_id_map.get(target_id)
        if target_node:
            return target_node, "example_application", "target_app_mapped"
        target_node = core_target_for_name(target_name, core_index, clean_flow=True)
        if target_node and str(edge.get("target_type") or "").strip() in CORE_TARGET_TYPES:
            return target_node, "core", "target_core_mapped"
        return None, "", "unresolved_target"

    if target_should_map_to_core(edge, target_name):
        formula_name = expansion_formula_name_from_evidence(
            original_target_name,
            target_name,
            str(edge.get("evidence_span") or ""),
        )
        target_node = core_target_for_name(formula_name, core_index) if formula_name else None
        if not target_node:
            target_node = core_target_for_name(original_target_name, core_index)
        if not target_node:
            target_node = core_target_for_name(target_name, core_index)
        if target_node:
            return target_node, "core", "target_core_mapped"

    target_node = app_node_id_map.get(target_id)
    if target_node:
        return target_node, "example_application", "target_app_mapped"

    target_node = core_target_for_name(target_name, core_index)
    if target_node and str(edge.get("target_type") or "").strip() in CORE_TARGET_TYPES:
        return target_node, "core", "target_core_mapped"

    return None, "", ""


def resolve_source_node(
    edge: dict[str, Any],
    source_name: str,
    app_node_id_map: dict[str, dict[str, Any]],
    core_index: dict[str, dict[str, Any]],
    clean_flow: bool = False,
) -> tuple[dict[str, Any] | None, str]:
    source_node = app_node_id_map.get(str(edge.get("source_node_id") or ""))
    if not source_node:
        return None, ""

    if clean_flow:
        return source_node, "example_application"

    original_source_name = str(edge.get("source_name") or "").strip()
    if str(edge.get("source_type") or "").strip() == "Method":
        core_name = SOURCE_CORE_METHOD_MAP.get(original_source_name) or SOURCE_CORE_METHOD_MAP.get(source_name)
        if core_name:
            core_node = core_target_for_name(core_name, core_index)
            if core_node:
                return core_node, "core"

    return source_node, "example_application"


def normalize_edges(
    app_edges: list[dict[str, Any]],
    app_node_id_map: dict[str, dict[str, Any]],
    core_index: dict[str, dict[str, Any]],
    core_id_index: dict[str, dict[str, Any]],
    clean_flow: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    normalized: dict[tuple[str, str, str], dict[str, Any]] = {}
    counts = {
        "kept": 0,
        "deleted": 0,
        "merged": 0,
        "target_core_mapped": 0,
        "target_app_mapped": 0,
        "unresolved_preserved": 0,
    }

    for edge in app_edges:
        original_source_name = str(edge.get("source_name") or "").strip()
        original_target_name = str(edge.get("target_name") or "").strip()
        source_name = canonical_method_name(edge.get("source_name", "")) if edge.get("source_type") == "Method" else str(edge.get("source_name") or "")
        target_name = canonical_method_name(edge.get("target_name", "")) if edge.get("target_type") == "Method" else str(edge.get("target_name") or "")
        if not clean_flow and should_delete_edge(source_name, target_name, original_source_name, original_target_name):
            counts["deleted"] += 1
            continue

        source_node, source_layer = resolve_source_node(edge, source_name, app_node_id_map, core_index, clean_flow)
        if not source_node:
            if not clean_flow:
                counts["deleted"] += 1
                continue
            normalized_edge = dict(edge)
            normalized_edge["source_layer"] = ""
            normalized_edge["target_layer"] = ""
            normalized_edge["review_status"] = "review"
            normalized_edge["normalization_status"] = "normalized_unresolved"
            normalized_edge["normalized_at"] = datetime.now().isoformat(timespec="seconds")
            normalized_edge["validation_warnings"] = sorted(set([
                *normalized_edge.get("validation_warnings", []),
                "normalized_example_application_edge",
                "source_not_resolved_in_clean_flow",
            ]))
            normalized_edge["edge_id"] = stable_id(
                f"{edge.get('textbook_id', '')}:norm-app-edge",
                [
                    str(edge.get("source_node_id") or edge.get("source_name") or ""),
                    str(edge.get("target_node_id") or edge.get("target_name") or ""),
                    edge.get("type", ""),
                    str(edge.get("source_frame_id") or ""),
                    "clean-unresolved",
                ],
            )
            key = (
                normalized_edge.get("source_node_id", ""),
                normalized_edge.get("target_node_id", ""),
                normalized_edge.get("type", ""),
            )
            normalized[key] = normalized_edge
            counts["unresolved_preserved"] += 1
            continue

        target_node, target_layer, target_count_key = resolve_target_node(
            edge,
            target_name,
            app_node_id_map,
            core_index,
            core_id_index,
            clean_flow,
        )
        if not target_node:
            if not clean_flow:
                counts["deleted"] += 1
                continue
            normalized_edge = dict(edge)
            normalized_edge["source_node_id"] = source_node.get("node_id", "")
            normalized_edge["source_name"] = source_node.get("name", "")
            normalized_edge["source_type"] = source_node.get("type", "")
            normalized_edge["source_layer"] = source_layer
            normalized_edge["target_layer"] = ""
            normalized_edge["review_status"] = "review"
            normalized_edge["normalization_status"] = "normalized_unresolved"
            normalized_edge["normalized_at"] = datetime.now().isoformat(timespec="seconds")
            normalized_edge["validation_warnings"] = sorted(set([
                *normalized_edge.get("validation_warnings", []),
                "normalized_example_application_edge",
                "target_not_resolved_in_clean_flow",
            ]))
            normalized_edge["edge_id"] = stable_id(
                f"{edge.get('textbook_id', '')}:norm-app-edge",
                [
                    normalized_edge.get("source_node_id", ""),
                    str(edge.get("target_node_id") or edge.get("target_name") or ""),
                    normalized_edge.get("type", ""),
                    str(edge.get("source_frame_id") or ""),
                    "clean-unresolved",
                ],
            )
            key = (
                normalized_edge.get("source_node_id", ""),
                normalized_edge.get("target_node_id", ""),
                normalized_edge.get("type", ""),
            )
            normalized[key] = normalized_edge
            counts["unresolved_preserved"] += 1
            continue
        if target_count_key:
            counts[target_count_key] += 1

        normalized_edge = dict(edge)
        normalized_edge["source_node_id"] = source_node.get("node_id", "")
        normalized_edge["source_name"] = source_node.get("name", "")
        normalized_edge["source_type"] = source_node.get("type", "")
        normalized_edge["source_layer"] = source_layer
        normalized_edge["target_node_id"] = target_node.get("node_id", "")
        normalized_edge["target_name"] = target_node.get("name", "")
        normalized_edge["target_type"] = target_node.get("type", "")
        normalized_edge["target_layer"] = target_layer
        normalized_edge["review_status"] = "review"
        normalized_edge["normalization_status"] = "normalized"
        normalized_edge["normalized_at"] = datetime.now().isoformat(timespec="seconds")
        normalized_edge["validation_warnings"] = sorted(set([
            *normalized_edge.get("validation_warnings", []),
            "normalized_example_application_edge",
        ]))
        normalized_edge["edge_id"] = stable_id(
            f"{edge.get('textbook_id', '')}:norm-app-edge",
            [
                normalized_edge["source_node_id"],
                normalized_edge["target_node_id"],
                normalized_edge.get("type", ""),
                str(edge.get("source_frame_id") or ""),
            ],
        )

        key = (
            normalized_edge["source_node_id"],
            normalized_edge["target_node_id"],
            normalized_edge.get("type", ""),
        )
        if key in normalized:
            existing = normalized[key]
            evidence_list = existing.setdefault("evidence_spans_merged", [])
            for evidence in [existing.get("evidence_span", ""), normalized_edge.get("evidence_span", "")]:
                if evidence and evidence not in evidence_list:
                    evidence_list.append(evidence)
            counts["merged"] += 1
        else:
            normalized[key] = normalized_edge
            counts["kept"] += 1
    return list(normalized.values()), counts


def write_report(
    path: Path,
    node_counts: dict[str, int],
    edge_counts: dict[str, int],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    clean_flow: bool = False,
) -> None:
    lines = [
        "# v4.3 Step 3D Normalized Example Application Report",
        "",
        f"- clean_flow: {str(clean_flow).lower()}",
        "",
        "## Node Normalization",
    ]
    for key in sorted(node_counts):
        lines.append(f"- {key}: {node_counts[key]}")
    lines.extend(["", "## Edge Normalization"])
    for key in sorted(edge_counts):
        lines.append(f"- {key}: {edge_counts[key]}")
    lines.extend(["", "## Output Counts"])
    lines.append(f"- normalized nodes: {len(nodes)}")
    lines.append(f"- normalized edges: {len(edges)}")
    lines.extend(["", "## Node Types"])
    type_counts: dict[str, int] = {}
    for node in nodes:
        type_counts[node.get("type", "")] = type_counts.get(node.get("type", ""), 0) + 1
    for key in sorted(type_counts):
        lines.append(f"- {key}: {type_counts[key]}")
    lines.extend(["", "## Edge Types"])
    rel_counts: dict[str, int] = {}
    for edge in edges:
        rel_counts[edge.get("type", "")] = rel_counts.get(edge.get("type", ""), 0) + 1
    for key in sorted(rel_counts):
        lines.append(f"- {key}: {rel_counts[key]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    app_nodes = read_jsonl(args.app_nodes)
    app_edges = read_jsonl(args.app_edges)
    core_nodes = read_jsonl(args.core_nodes)
    core_index = build_core_index(core_nodes)
    core_id_index = build_core_id_index(core_nodes)

    normalized_nodes, app_node_id_map, node_counts = normalize_app_nodes(app_nodes, args.clean_flow)
    normalized_edges, edge_counts = normalize_edges(app_edges, app_node_id_map, core_index, core_id_index, args.clean_flow)

    write_jsonl(args.nodes_out, normalized_nodes)
    write_jsonl(args.edges_out, normalized_edges)
    write_report(args.report, node_counts, edge_counts, normalized_nodes, normalized_edges, args.clean_flow)

    print(f"[OK] normalized nodes -> {args.nodes_out}")
    print(f"[OK] normalized edges -> {args.edges_out}")
    print(f"[OK] report -> {args.report}")


if __name__ == "__main__":
    main()
