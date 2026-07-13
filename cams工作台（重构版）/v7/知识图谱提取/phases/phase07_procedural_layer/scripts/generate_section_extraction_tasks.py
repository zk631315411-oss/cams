from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
PHASES_DIR = PHASE_DIR.parent

P6_GRAPH_PATH = PHASES_DIR / "phase06_kg_views" / "outputs" / "kg_retrieval_graph.json"
P5_ALIAS_PATH = PHASES_DIR / "phase05_terms" / "outputs" / "p5c_alias_index.json"

# schema 路径定义（类型值在 make_instructions() 中动态读取）
SCHEMA_PATH = PHASE_DIR / "inputs" / "procedural_schema_v2.json"

OUT_DIR = PHASE_DIR / "outputs"
REPORT_DIR = PHASE_DIR / "reports"
REPORT_PATH = REPORT_DIR / "p7_section_extraction_task_report.md"
DEFAULT_PACKAGE_DIR = PHASE_DIR / "phases" / "P7B" / "section_packages"

TASK_SCHEMA_VERSION = "p7_section_extraction_task_v1"
TARGET_OUTPUT_SCHEMA = "p7_procedural_schema_v2"

CANDIDATE_UNIT_TYPES = {"process", "rule", "risk_indicator", "case"}
CANDIDATE_RELATION_TYPES = {
    "describes_process",
    "prescribes_measure",
    "states_rule",
    "indicates_risk",
}
CANDIDATE_TEXT_PATTERN = re.compile(
    r"monitoring|investigation|review|report|escalation|due diligence|"
    r"screening|risk assessment|alert|SAR|KYC|EDD|transaction",
    re.IGNORECASE,
)


def read_json(path: Path) -> Any:
    """读取 JSON 文件，失败时抛出可读错误。"""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise FileNotFoundError(f"P6 图文件不存在: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"P6 图文件 JSON 格式错误: {path}\n{e}")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_output_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return PHASE_DIR / path


def safe_dir_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def unit_sort_key(unit: dict[str, Any]) -> tuple[int, str]:
    order = unit.get("unit_order")
    return (order if isinstance(order, int) else 10**9, unit.get("unit_id") or "")


def section_sort_key(section: dict[str, Any]) -> tuple[int, str]:
    order = section.get("section_order")
    return (order if isinstance(order, int) else 10**9, section.get("section_id") or "")


def cp_sort_key(cp: dict[str, Any], unit_order_by_id: dict[str, int]) -> tuple[int, str]:
    unit_ids = cp.get("key_unit_ids") or cp.get("anchor_unit_ids") or cp.get("support_unit_ids") or []
    orders = [unit_order_by_id.get(uid, 10**9) for uid in unit_ids]
    return (min(orders) if orders else 10**9, cp.get("core_point_id") or "")


def load_alias_metadata() -> dict[str, Any]:
    if not P5_ALIAS_PATH.exists():
        return {
            "status": "missing",
            "path": str(P5_ALIAS_PATH),
            "usage": "normalization_only_not_evidence",
        }

    payload = read_json(P5_ALIAS_PATH)
    alias_groups = payload.get("alias_groups") if isinstance(payload, dict) else []
    normalization_groups = []
    for group in alias_groups or []:
        normalization_groups.append(
            {
                "alias_group_id": group.get("alias_group_id"),
                "canonical_en": group.get("canonical_en"),
                "canonical_zh": group.get("canonical_zh"),
                "aliases_en": group.get("aliases_en") or [],
                "aliases_zh": group.get("aliases_zh") or [],
                "alias_scope": group.get("alias_scope"),
            }
        )

    return {
        "status": "available",
        "path": str(P5_ALIAS_PATH),
        "usage": "normalization_only_not_evidence",
        "not_kg_edge": True,
        "summary": payload.get("summary") if isinstance(payload, dict) else None,
        "alias_group_count": len(normalization_groups),
        "alias_groups": normalization_groups,
    }


def pick_unit_fields(unit: dict[str, Any]) -> dict[str, Any]:
    return {
        "unit_id": unit.get("unit_id"),
        "unit_order": unit.get("unit_order"),
        "type": unit.get("type"),
        "knowledge_zh": unit.get("knowledge_zh"),
        "en_quote": unit.get("en_quote"),
        "printed_page": unit.get("printed_page"),
        "pdf_page": unit.get("pdf_page"),
    }


def pick_core_point_fields(cp: dict[str, Any]) -> dict[str, Any]:
    return {
        "core_point_id": cp.get("core_point_id"),
        "title_en": cp.get("title_en"),
        "title_zh": cp.get("title_zh"),
        "reason": cp.get("reason"),
        "key_unit_ids": cp.get("key_unit_ids") or [],
        "anchor_unit_ids": cp.get("anchor_unit_ids") or [],
        "support_unit_ids": cp.get("support_unit_ids") or [],
    }


def pick_edge_fields(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "edge_id": edge.get("edge_id"),
        "edge_scope": edge.get("edge_scope"),
        "source_id": edge.get("source_id"),
        "target_id": edge.get("target_id"),
        "relation_type": edge.get("relation_type"),
        "source_phase": edge.get("source_phase"),
        "reason": edge.get("reason"),
        "evidence_summary": edge.get("evidence_summary"),
        "source_evidence_unit_ids": edge.get("source_evidence_unit_ids") or [],
        "target_evidence_unit_ids": edge.get("target_evidence_unit_ids") or [],
        "support_strength": edge.get("support_strength"),
    }


def build_section_text_with_unit_anchors(units: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for unit in units:
        unit_id = unit.get("unit_id") or "unknown_unit"
        unit_order = unit.get("unit_order")
        anchor = f"[{unit_id}|{unit_order}]"
        en_quote = (unit.get("en_quote") or "").strip()
        knowledge_zh = (unit.get("knowledge_zh") or "").strip()
        if en_quote and knowledge_zh:
            text = f"{en_quote}\nZH: {knowledge_zh}"
        else:
            text = en_quote or knowledge_zh
        lines.append(f"{anchor} {text}".rstrip())
    return "\n\n".join(lines)


def make_instructions() -> dict[str, Any]:
    """生成 instructions 字典，从 schema 动态读取类型。"""
    # 在函数内部读取 schema，确保路径正确
    schema_data: dict[str, Any] = {}
    if SCHEMA_PATH.exists():
        try:
            # utf-8-sig 自动跳过 BOM 头，避免带 BOM 的 schema 文件解码失败
            schema_data = json.loads(SCHEMA_PATH.read_text(encoding="utf-8-sig"))
            print(f"[DEBUG] 成功读取 schema: {SCHEMA_PATH}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"警告：无法读取 schema 文件 {SCHEMA_PATH}: {e}")
    else:
        print(f"警告：schema 文件不存在: {SCHEMA_PATH}")
    
    # 从 schema 提取类型，若失败则使用默认值
    node_categories = schema_data.get("node_categories", ["entry", "process", "exit", "auxiliary"])
    flow_node_types = schema_data.get("flow_node_types", [])
    relation_types = schema_data.get("relation_types", [])
    flow_edge_types = schema_data.get("flow_edge_types", ["PRECEDES", "REFERENCES", "PRODUCES", "DECIDES", "FEEDBACK"])
    
    print(f"[DEBUG] node_categories: {node_categories}")
    print(f"[DEBUG] flow_node_types: {flow_node_types}")
    print(f"[DEBUG] relation_types: {relation_types}")
    print(f"[DEBUG] flow_edge_types: {flow_edge_types}")
    
    return {
        # 标识与约定
        "schema_file": "inputs/procedural_schema_v2.json",
        "p7a_contract": "minimal_flow_graph_contract",

        # 从 schema 动态读取的类型定义，确保与 schema 保持一致
        "node_categories": node_categories,
        "flow_node_types": flow_node_types,
        "relation_types": relation_types,
        "flow_edge_types": flow_edge_types,

        # 必填字段约束
        "required_card_fields": [
            "card_id",
            "section_id",
            "title",
            "flow_nodes",
            "flow_edges",
            "source_unit_ids",
            "review_status",
        ],
        "optional_card_fields": [
            "summary",
            "scenario",
            "trigger",
            "actor",
            "objective",
            "inputs",
            "decision_standard",
            "outputs",
            "steps",
            "review_notes",
            "metadata",
        ],

        # 流程元素定义说明
        "flow_element_definitions": {
            "start": "Local entry point of the current card; not the start of the whole customer lifecycle or textbook process.",
            "end": "Local exit, stable result, or handoff point of the current card; not necessarily the end of the business matter.",
            "decision": "Conditional branching point based on facts, standards, thresholds, evidence sufficiency, or compliance requirements.",
            "action": "Real executable step in the formal flow graph.",
            "steps": "Human-readable summary derived from flow_nodes and flow_edges; not the source of truth.",
            "summary": "Optional human-readable card description; it does not replace flow_nodes or flow_edges.",
        },

        # 卡片结构约束
        "card_must_not_cross_section": True,
        "card_must_have_start_or_trigger_node": True,
        "output_zero_or_more_cards": True,
        "json_flow_graph_is_source_of_truth": True,

        # 边类型约束
        "use_only_card_internal_edge_types": flow_edge_types,

        # 禁止行为
        "do_not_create_bridge_edges": True,
        "do_not_create_clusters": True,
        "do_not_create_scenario_paths": True,
        "do_not_create_render_files": True,

        # 字段语义说明
        "cite_unit_evidence_for_every_node_and_edge": True,
        "steps_are_human_readable_summary_not_source_of_truth": True,
        "summary_scenario_trigger_objective_are_optional": True,
        "trigger_field_does_not_replace_trigger_node": True,
        "decides_edges_must_have_condition_labels": True,
        "drawio_mermaid_svg_png_are_render_views_not_evidence_source": True,

        # 跨阶段数据使用说明
        "p5_alias_is_normalization_only": True,
        "p2b_relation_type_is_candidate_only_not_edge_filter": True,
        "include_all_section_core_point_unit_edges": True,
    }


def candidate_reason(
    section: dict[str, Any],
    units: list[dict[str, Any]],
    cps: list[dict[str, Any]],
    cp_unit_edges: list[dict[str, Any]],
) -> str | None:
    """
    判断 section 是否值得生成 task。
    
    注意：risk_indicator 和 case 类型单独命中时可能误判非流程 section，
    因为这两个类型在纯定义章节也大量存在。
    保留它们是因为流程章节也可能包含这些类型，不做过度过滤。
    实际使用时建议配合 --candidate-only 和人工复核。
    """
    for unit in units:
        if unit.get("type") in CANDIDATE_UNIT_TYPES:
            return f"unit_type:{unit.get('type')}"

    for edge in cp_unit_edges:
        if edge.get("relation_type") in CANDIDATE_RELATION_TYPES:
            return f"cp_unit_relation:{edge.get('relation_type')}"

    text_parts = [section.get("section_title") or ""]
    for cp in cps:
        text_parts.extend([cp.get("title_en") or "", cp.get("title_zh") or "", cp.get("reason") or ""])
    if CANDIDATE_TEXT_PATTERN.search("\n".join(text_parts)):
        return "text_keyword"

    return None


def build_indexes(graph: dict[str, Any]) -> dict[str, Any]:
    """构建 chapter/section/unit/CP/边 的索引，用于后续 task 生成。"""
    chapters = {row.get("chapter_id"): row for row in graph.get("chapters") or [] if row.get("chapter_id")}
    sections = {row.get("section_id"): row for row in graph.get("sections") or [] if row.get("section_id")}

    units_by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    unit_section_by_id: dict[str, str] = {}
    unit_order_by_id: dict[str, int] = {}
    for unit in graph.get("units") or []:
        section_id = unit.get("section_id")
        unit_id = unit.get("unit_id")
        if section_id:
            units_by_section[section_id].append(unit)
        if unit_id and section_id:
            unit_section_by_id[unit_id] = section_id
        if unit_id and isinstance(unit.get("unit_order"), int):
            unit_order_by_id[unit_id] = unit["unit_order"]
    for rows in units_by_section.values():
        rows.sort(key=unit_sort_key)

    cps_by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cp_section_by_id: dict[str, str] = {}
    for cp in graph.get("core_points") or []:
        section_id = cp.get("section_id")
        cp_id = cp.get("core_point_id")
        if section_id:
            cps_by_section[section_id].append(cp)
        if cp_id and section_id:
            cp_section_by_id[cp_id] = section_id
    for rows in cps_by_section.values():
        rows.sort(key=lambda cp: cp_sort_key(cp, unit_order_by_id))

    cp_unit_edges_by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    same_cp_edges_by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in graph.get("edges") or []:
        scope = edge.get("edge_scope")
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        if scope == "core_point_unit":
            cp_section = cp_section_by_id.get(source_id)
            unit_section = unit_section_by_id.get(target_id)
            if cp_section and cp_section == unit_section:
                cp_unit_edges_by_section[cp_section].append(edge)
        elif scope == "same_section_core_point":
            source_section = cp_section_by_id.get(source_id)
            target_section = cp_section_by_id.get(target_id)
            if source_section and source_section == target_section:
                same_cp_edges_by_section[source_section].append(edge)

    return {
        "chapters": chapters,
        "sections": sections,
        "units_by_section": units_by_section,
        "cps_by_section": cps_by_section,
        "cp_unit_edges_by_section": cp_unit_edges_by_section,
        "same_cp_edges_by_section": same_cp_edges_by_section,
    }


def selected_sections(
    chapters: dict[str, dict[str, Any]],
    sections: dict[str, dict[str, Any]],
    chapter_filter: set[str] | None,
    section_filter: set[str] | None,
) -> list[dict[str, Any]]:
    """根据 chapter_filter 和 section_filter 筛选目标 section。"""
    rows = []
    if section_filter:
        for section_id in sorted(section_filter):
            section = sections.get(section_id)
            if section and (not chapter_filter or section.get("chapter_id") in chapter_filter):
                rows.append(section)
        return sorted(rows, key=lambda row: (row.get("chapter_id") or "", *section_sort_key(row)))

    for chapter_id in sorted(chapters):
        if chapter_filter and chapter_id not in chapter_filter:
            continue
        chapter = chapters[chapter_id]
        for section_id in chapter.get("section_ids") or []:
            section = sections.get(section_id)
            if section:
                rows.append(section)
    return sorted(rows, key=lambda row: (row.get("chapter_id") or "", *section_sort_key(row)))


def build_tasks(
    chapter_filter: set[str] | None,
    section_filter: set[str] | None,
    candidate_only: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """读取 P6 KG，按 section 生成 task 包。"""
    graph = read_json(P6_GRAPH_PATH)
    indexes = build_indexes(graph)
    alias_index = load_alias_metadata()
    generated_at = datetime.now().isoformat(timespec="seconds")

    tasks: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    candidate_reason_counts: Counter[str] = Counter()
    skip_reason_counts: Counter[str] = Counter()

    for section in selected_sections(indexes["chapters"], indexes["sections"], chapter_filter, section_filter):
        section_id = section.get("section_id")
        chapter_id = section.get("chapter_id")
        chapter = indexes["chapters"].get(chapter_id, {})
        units = indexes["units_by_section"].get(section_id, [])
        cps = indexes["cps_by_section"].get(section_id, [])
        cp_unit_edges = indexes["cp_unit_edges_by_section"].get(section_id, [])
        same_cp_edges = indexes["same_cp_edges_by_section"].get(section_id, [])

        reason = candidate_reason(section, units, cps, cp_unit_edges)
        if candidate_only and not reason:
            skip_reason = "not_candidate_section"
            skipped.append({"section_id": section_id, "reason": skip_reason})
            skip_reason_counts[skip_reason] += 1
            continue
        if reason:
            candidate_reason_counts[reason] += 1

        tasks.append(
            {
                "task_id": f"p7sec_{section_id}",
                "schema_version": TASK_SCHEMA_VERSION,
                "target_output_schema": TARGET_OUTPUT_SCHEMA,
                "generated_at": generated_at,
                "chapter_id": chapter_id,
                "chapter_title": chapter.get("chapter_title"),
                "section_id": section_id,
                "section_title": section.get("section_title"),
                "section_order": section.get("section_order"),
                "task_goal": (
                    "Extract zero or more section-bounded P7 flow cards from this section only. "
                    "Each card must follow the minimal P7A contract: title, flow_nodes, flow_edges, source_unit_ids, and review_status. "
                    "Use the provided units as evidence and the provided core points and edges as retrieval context."
                ),
                "section_text_with_unit_anchors": build_section_text_with_unit_anchors(units),
                "units": [pick_unit_fields(unit) for unit in units],
                "core_points": [pick_core_point_fields(cp) for cp in cps],
                "core_point_unit_edges": [pick_edge_fields(edge) for edge in cp_unit_edges],
                "same_section_core_point_edges": [pick_edge_fields(edge) for edge in same_cp_edges],
                "alias_index": alias_index,
                "instructions": make_instructions(),
            }
        )

    report_data = {
        "task_count": len(tasks),
        "section_count": len({task["section_id"] for task in tasks}),
        "candidate_only": candidate_only,
        "skipped_count": len(skipped),
        "skip_reason_counts": dict(sorted(skip_reason_counts.items())),
        "candidate_reason_counts": dict(sorted(candidate_reason_counts.items())),
        "chapters": sorted({task["chapter_id"] for task in tasks if task.get("chapter_id")}),
        "skipped": skipped,
    }
    return tasks, report_data


def write_report(report_data: dict[str, Any], out_path: Path, requested_chapters: list[str] | None) -> None:
    """生成 task 统计报告。"""
    lines = [
        "# P7 Section Extraction Task Report",
        "",
        f"generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"task_count: {report_data['task_count']}",
        f"section_count: {report_data['section_count']}",
        f"candidate_only: {report_data['candidate_only']}",
        f"output: {out_path}",
        f"section_package_dir: {report_data.get('section_package_dir', 'not_written')}",
        f"chapters: {', '.join(requested_chapters or report_data['chapters']) if (requested_chapters or report_data['chapters']) else 'all'}",
        f"skipped_count: {report_data['skipped_count']}",
        "",
        "## Skip Reasons",
        "",
    ]
    if report_data["skip_reason_counts"]:
        for reason, count in report_data["skip_reason_counts"].items():
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- none: 0")

    lines.extend(["", "## Candidate Reasons", ""])
    if report_data["candidate_reason_counts"]:
        for reason, count in report_data["candidate_reason_counts"].items():
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- none: 0")

    lines.extend(["", "## Skipped Sections", ""])
    if report_data["skipped"]:
        for row in report_data["skipped"][:200]:
            lines.append(f"- {row['section_id']}: {row['reason']}")
        remaining = len(report_data["skipped"]) - 200
        if remaining > 0:
            lines.append(f"- ... {remaining} more")
    else:
        lines.append("- none")

    write_text(REPORT_PATH, "\n".join(lines) + "\n")


def write_section_packages(tasks: list[dict[str, Any]], package_dir: Path) -> None:
    package_dir.mkdir(parents=True, exist_ok=True)
    index_rows: list[dict[str, Any]] = []
    for task in tasks:
        section_id = task.get("section_id") or task.get("task_id") or "unknown_section"
        section_dir = package_dir / safe_dir_name(section_id)
        section_dir.mkdir(parents=True, exist_ok=True)

        write_json(section_dir / "task.json", task)
        write_text(section_dir / "section_text.md", task.get("section_text_with_unit_anchors") or "")
        write_json(section_dir / "units.json", task.get("units") or [])
        write_json(section_dir / "core_points.json", task.get("core_points") or [])
        write_json(section_dir / "cp_unit_edges.json", task.get("core_point_unit_edges") or [])
        write_json(section_dir / "same_section_cp_edges.json", task.get("same_section_core_point_edges") or [])
        write_json(section_dir / "instructions.json", task.get("instructions") or {})
        write_json(section_dir / "alias_metadata.json", task.get("alias_index") or {})

        index_rows.append(
            {
                "task_id": task.get("task_id"),
                "chapter_id": task.get("chapter_id"),
                "section_id": section_id,
                "section_title": task.get("section_title"),
                "package_dir": str(section_dir),
            }
        )
    write_json(package_dir / "index.json", index_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate P7 section-level extraction tasks from the P6 base KG.")
    parser.add_argument("--chapters", nargs="*", help="Optional chapter IDs, e.g. CH47 CH49. Defaults to all chapters.")
    parser.add_argument("--sections", nargs="*", help="Optional section IDs, e.g. CH47-S01 CH47-S06.")
    parser.add_argument("--candidate-only", action="store_true", help="Keep only sections likely to contain process cards.")
    parser.add_argument("--output", default=str(OUT_DIR / "p7_section_extraction_tasks.jsonl"))
    parser.add_argument("--write-section-packages", action="store_true", help="Also write one directory per section for P7C/agentic reading.")
    parser.add_argument("--package-dir", default=str(DEFAULT_PACKAGE_DIR), help="Directory for section packages, relative paths resolve from the P7 phase directory.")
    args = parser.parse_args()

    chapter_filter = set(args.chapters) if args.chapters else None
    section_filter = set(args.sections) if args.sections else None
    out_path = resolve_output_path(args.output)
    package_dir = resolve_output_path(args.package_dir)

    tasks, report_data = build_tasks(chapter_filter, section_filter, args.candidate_only)
    write_jsonl(out_path, tasks)
    if args.write_section_packages:
        write_section_packages(tasks, package_dir)
        report_data["section_package_dir"] = str(package_dir)
    write_report(report_data, out_path, args.chapters)

    print(f"Wrote {len(tasks)} tasks to {out_path}")
    if args.write_section_packages:
        print(f"Wrote section packages to {package_dir}")
    print(f"Wrote report to {REPORT_PATH}")


if __name__ == "__main__":
    main()

