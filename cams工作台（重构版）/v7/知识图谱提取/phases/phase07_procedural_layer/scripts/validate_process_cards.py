from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
PHASES_DIR = PHASE_DIR.parent

P6_GRAPH_PATH = PHASES_DIR / "phase06_kg_views" / "outputs" / "kg_retrieval_graph.json"
SCHEMA_PATH = PHASE_DIR / "inputs" / "procedural_schema_v1.json"
REPORT_DIR = PHASE_DIR / "reports"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            rows.append({"__json_error__": str(exc), "__line_no__": line_no})
            continue
        rows.append(row)
    return rows


def iter_cards(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in rows:
        if "__json_error__" in row:
            cards.append(row)
            continue
        if isinstance(row.get("process_cards"), list):
            for card in row["process_cards"]:
                if isinstance(card, dict):
                    card.setdefault("__task_id__", row.get("task_id"))
                    card.setdefault("__reader_role__", row.get("reader_role"))
                    cards.append(card)
        else:
            cards.append(row)
    return cards


def node_type_by_id(card: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for node in card.get("nodes") or []:
        if isinstance(node, dict) and node.get("node_id") and node.get("node_type"):
            result[node["node_id"]] = node["node_type"]
    return result


def validate_card(card: dict[str, Any], unit_ids: set[str], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if "__json_error__" in card:
        return [f"line {card.get('__line_no__')}: invalid JSON: {card.get('__json_error__')}"]

    card_id = card.get("process_card_id") or "<missing card id>"
    scope = card.get("scope") or {}
    scope_units = scope.get("unit_ids") or []
    if not scope_units:
        errors.append(f"{card_id}: missing scope.unit_ids")
    for unit_id in scope_units:
        if unit_id not in unit_ids:
            errors.append(f"{card_id}: unknown scope unit_id {unit_id}")

    allowed_node_types = set(schema.get("node_types") or [])
    relation_schema = schema.get("relation_types") or {}
    allowed_families = set(schema.get("edge_families") or [])
    node_types = node_type_by_id(card)

    for node in card.get("nodes") or []:
        if not isinstance(node, dict):
            errors.append(f"{card_id}: node is not an object")
            continue
        node_id = node.get("node_id")
        node_type = node.get("node_type")
        if not node_id:
            errors.append(f"{card_id}: node missing node_id")
        if node_type not in allowed_node_types:
            errors.append(f"{card_id}: invalid node_type {node_type} for {node_id}")

    for idx, edge in enumerate(card.get("edges") or [], 1):
        if not isinstance(edge, dict):
            errors.append(f"{card_id}: edge #{idx} is not an object")
            continue
        rel = edge.get("relation_type")
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        edge_family = edge.get("edge_family")
        derivation = edge.get("derivation")
        evidence_units = edge.get("evidence_unit_ids") or []

        if rel not in relation_schema:
            errors.append(f"{card_id}: invalid relation_type {rel}")
        if edge_family not in allowed_families:
            errors.append(f"{card_id}: invalid edge_family {edge_family}")
        elif rel in relation_schema and edge_family != relation_schema[rel].get("edge_family"):
            errors.append(f"{card_id}: edge_family {edge_family} does not match relation_type {rel}")
        if not source_id or not target_id:
            errors.append(f"{card_id}: edge #{idx} missing source_id or target_id")
        if derivation not in schema.get("derivation_levels", []):
            errors.append(f"{card_id}: invalid derivation {derivation}")
        if derivation != "derived_from_edges" and not evidence_units:
            errors.append(f"{card_id}: edge #{idx} missing evidence_unit_ids")
        for unit_id in evidence_units:
            if unit_id not in unit_ids:
                errors.append(f"{card_id}: edge #{idx} unknown evidence_unit_id {unit_id}")

        if rel in relation_schema:
            source_type = node_types.get(source_id)
            target_type = node_types.get(target_id)
            allowed_source = set(relation_schema[rel].get("source_types") or [])
            allowed_target = set(relation_schema[rel].get("target_types") or [])
            if source_type and source_type not in allowed_source:
                errors.append(f"{card_id}: {rel} source type {source_type} not allowed for {source_id}")
            if target_type and target_type not in allowed_target:
                errors.append(f"{card_id}: {rel} target type {target_type} not allowed for {target_id}")
        if rel in {"FEEDBACK_UPDATES", "ADJUSTS_THRESHOLD", "UPDATES_RISK_PROFILE", "TRIGGERS_REVIEW"} and edge_family != "feedback_loop":
            errors.append(f"{card_id}: feedback relation {rel} must use feedback_loop family")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate P7 process card JSONL output.")
    parser.add_argument("input", help="Path to a process-card JSONL file or reader output JSONL file.")
    parser.add_argument("--report", default=str(REPORT_DIR / "p7_process_card_validation_report.md"))
    args = parser.parse_args()

    graph = read_json(P6_GRAPH_PATH)
    unit_ids = {unit.get("unit_id") for unit in graph.get("units") or [] if unit.get("unit_id")}
    schema = read_json(SCHEMA_PATH)
    rows = read_jsonl(Path(args.input))
    cards = iter_cards(rows)

    all_errors: list[str] = []
    relation_counts: Counter[str] = Counter()
    derivation_counts: Counter[str] = Counter()
    for card in cards:
        all_errors.extend(validate_card(card, unit_ids, schema))
        for edge in card.get("edges") or [] if isinstance(card, dict) else []:
            if isinstance(edge, dict):
                relation_counts[edge.get("relation_type") or "<missing>"] += 1
                derivation_counts[edge.get("derivation") or "<missing>"] += 1

    report_lines = [
        "# P7 Process Card Validation Report",
        "",
        f"input: {args.input}",
        f"row_count: {len(rows)}",
        f"card_count: {len(cards)}",
        f"error_count: {len(all_errors)}",
        "",
        "## Relation Types",
        "",
    ]
    for key, count in relation_counts.most_common():
        report_lines.append(f"- {key}: {count}")
    report_lines.extend(["", "## Derivation Levels", ""])
    for key, count in derivation_counts.most_common():
        report_lines.append(f"- {key}: {count}")
    report_lines.extend(["", "## Errors", ""])
    if all_errors:
        for error in all_errors[:500]:
            report_lines.append(f"- {error}")
        if len(all_errors) > 500:
            report_lines.append(f"- ... truncated {len(all_errors) - 500} additional errors")
    else:
        report_lines.append("No validation errors.")

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(f"Validated {len(cards)} cards with {len(all_errors)} errors. Report: {report_path}")


if __name__ == "__main__":
    main()

