from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
SCHEMA_PATH = PHASE_DIR / "inputs" / "procedural_schema_v2.json"
DEFAULT_PACKAGES_DIR = PHASE_DIR / "phases" / "P7B" / "section_packages"
DEFAULT_OUTPUT_DIR = PHASE_DIR / "phases" / "P7D" / "outputs" / "structure_validation"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def collect_card_files(card_paths: list[str], input_dirs: list[str]) -> list[Path]:
    files = [Path(path) for path in card_paths]
    for raw_dir in input_dirs:
        root = Path(raw_dir)
        if root.is_file():
            files.append(root)
        else:
            files.extend(sorted(root.rglob("cards.raw.json")))
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in files:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def collect_cards(payload: Any, source_path: Path) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for item in payload:
            cards.extend(collect_cards(item, source_path))
    elif isinstance(payload, dict):
        if isinstance(payload.get("cards"), list):
            cards.extend(collect_cards(payload["cards"], source_path))
        elif payload.get("card_id"):
            card = dict(payload)
            card["__source_path"] = source_path.resolve().as_posix()
            cards.append(card)
    return cards


def read_cards_file(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        return collect_cards(read_json(path), path), []
    except Exception as exc:  # noqa: BLE001 - malformed P7C input is a structure failure.
        return [], [{"code": "invalid_json", "message": str(exc), "source_path": path.resolve().as_posix()}]


def collect_allowed_unit_ids(package: dict[str, Any]) -> set[str]:
    return {
        unit.get("unit_id")
        for unit in package.get("units") or []
        if isinstance(unit, dict) and unit.get("unit_id")
    }


def issue(code: str, message: str, **extra: Any) -> dict[str, Any]:
    row = {"code": code, "message": message}
    row.update({key: value for key, value in extra.items() if value is not None})
    return row


def missing(value: Any) -> bool:
    return value is None or value == "" or (isinstance(value, list) and not value)


def validate_evidence_ids(
    owner: str,
    evidence_unit_ids: Any,
    allowed_unit_ids: set[str],
    errors: list[dict[str, Any]],
) -> None:
    if not isinstance(evidence_unit_ids, list) or not evidence_unit_ids:
        errors.append(issue("missing_evidence_reference", f"{owner} missing evidence_unit_ids"))
        return
    for unit_id in evidence_unit_ids:
        if unit_id not in allowed_unit_ids:
            errors.append(issue("out_of_section_evidence", f"{owner} references unit outside current P7B section: {unit_id}", unit_id=unit_id))


def expected_node_category(node_type: str | None) -> str | None:
    if not node_type:
        return None
    if node_type.startswith("E"):
        return "entry"
    if node_type.startswith("P"):
        return "process"
    if node_type.startswith("X"):
        return "exit"
    if node_type in {"input", "standard"}:
        return "auxiliary"
    return None


def graph_structure_errors(card_id: str, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    node_ids = {node.get("node_id") for node in nodes if isinstance(node, dict) and node.get("node_id")}
    categories = {node.get("node_id"): node.get("node_category") for node in nodes if isinstance(node, dict)}
    used: set[str] = set()
    undirected = {node_id: set() for node_id in node_ids}
    directed = {node_id: set() for node_id in node_ids}

    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = edge.get("source")
        target = edge.get("target")
        if source not in node_ids or target not in node_ids:
            continue
        used.update({source, target})
        undirected[source].add(target)
        undirected[target].add(source)
        if edge.get("edge_type") != "REFERENCES":
            directed[source].add(target)

    for node_id in sorted(node_ids - used):
        errors.append(issue("isolated_node", f"{card_id} node {node_id} is not referenced by any edge", node_id=node_id))

    if node_ids:
        remaining = set(node_ids)
        component_count = 0
        while remaining:
            component_count += 1
            stack = [next(iter(remaining))]
            seen: set[str] = set()
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                stack.extend(undirected[current] - seen)
            remaining -= seen
        if component_count > 1:
            errors.append(issue("disconnected_graph", f"{card_id} has {component_count} disconnected components", component_count=component_count))

    entries = [node_id for node_id, category in categories.items() if category == "entry"]
    exits = {node_id for node_id, category in categories.items() if category == "exit"}
    processes = {node_id for node_id, category in categories.items() if category == "process"}
    stack = [(node_id, False) for node_id in entries]
    seen_states: set[tuple[str, bool]] = set()
    found_path = False
    while stack:
        current, passed_process = stack.pop()
        state = (current, passed_process)
        if state in seen_states:
            continue
        seen_states.add(state)
        passed_process = passed_process or current in processes
        if current in exits and passed_process:
            found_path = True
            break
        stack.extend((target, passed_process) for target in directed.get(current, set()))
    if entries and processes and exits and not found_path:
        errors.append(issue("missing_entry_process_exit_path", f"{card_id} has no directed entry -> process -> exit path"))
    return errors


def derive_graph_shape(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    categories = {
        node.get("node_id"): node.get("node_category")
        for node in nodes
        if isinstance(node, dict) and node.get("node_id")
    }
    entries = {node_id for node_id, category in categories.items() if category == "entry"}
    processes = {node_id for node_id, category in categories.items() if category == "process"}
    exits = {node_id for node_id, category in categories.items() if category == "exit"}
    directed = {node_id: set() for node_id in categories}
    for edge in edges:
        if not isinstance(edge, dict) or edge.get("edge_type") == "REFERENCES":
            continue
        source = edge.get("source")
        target = edge.get("target")
        if source in directed and target in directed:
            directed[source].add(target)
    seen: set[tuple[str, bool]] = set()
    stack = [(node_id, False) for node_id in entries]
    has_closed_path = False
    while stack:
        current, passed_process = stack.pop()
        state = (current, passed_process)
        if state in seen:
            continue
        seen.add(state)
        passed_process = passed_process or current in processes
        if current in exits and passed_process:
            has_closed_path = True
            break
        stack.extend((target, passed_process) for target in directed.get(current, set()))
    return {
        "has_entry_process_exit_path": has_closed_path,
        "has_terminal_process": bool(processes and not exits),
        "derived_graph_shape": "closed_flow" if has_closed_path else "open_relation",
    }


def validate_card_structure(
    card: dict[str, Any],
    package: dict[str, Any] | None,
    schema: dict[str, Any],
    *,
    duplicate_card_id: bool = False,
) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    card_id = card.get("card_id") or "<missing card_id>"
    section_id = card.get("section_id")
    source_path = card.get("__source_path")
    package_path = None
    allowed_unit_ids: set[str] = set()

    if package is None:
        errors.append(issue("missing_section_package", f"No P7B section package found for {section_id}"))
    else:
        package_path = package.get("__package_path")
        if section_id != package.get("section_id"):
            errors.append(issue("section_id_mismatch", f"Card section_id {section_id} does not match P7B package {package.get('section_id')}"))
        allowed_unit_ids = collect_allowed_unit_ids(package)

    card_schema = schema.get("object_schemas", {}).get("p7_card", {})
    node_schema = schema.get("object_schemas", {}).get("flow_node", {})
    edge_schema = schema.get("object_schemas", {}).get("flow_edge", {})
    required_card_fields = list(card_schema.get("required", []))
    if "candidate_status" in required_card_fields and "candidate_status" not in card and card.get("review_status") is not None:
        required_card_fields.remove("candidate_status")
    for field in required_card_fields:
        if missing(card.get(field)):
            errors.append(issue("missing_required_field", f"{card_id} missing required field {field}", field=field))

    if duplicate_card_id:
        errors.append(issue("duplicate_card_id", f"Duplicate card_id in current validation run: {card_id}"))
    if card.get("card_nature") and card.get("card_nature") not in set(schema.get("card_natures", [])):
        errors.append(issue("invalid_card_nature", f"{card_id} invalid card_nature {card.get('card_nature')}"))
    if card.get("candidate_status") is not None and card.get("candidate_status") not in set(schema.get("candidate_statuses", ["candidate"])):
        errors.append(issue("invalid_candidate_status", f"{card_id} invalid candidate_status {card.get('candidate_status')}"))
    if card.get("review_status") and card.get("review_status") not in set(schema.get("review_statuses", [])):
        errors.append(issue("invalid_declared_review_status", f"{card_id} invalid P7C review_status {card.get('review_status')}"))
    if package is not None:
        validate_evidence_ids(f"{card_id}.source_unit_ids", card.get("source_unit_ids"), allowed_unit_ids, errors)

    nodes = card.get("flow_nodes") if isinstance(card.get("flow_nodes"), list) else []
    edges = card.get("flow_edges") if isinstance(card.get("flow_edges"), list) else []
    node_ids: set[str] = set()
    node_by_id: dict[str, dict[str, Any]] = {}
    allowed_node_types = set(schema.get("flow_node_types", []))
    allowed_edge_types = set(schema.get("flow_edge_types", []))
    evidence_strength_schema = schema.get("evidence_strength", {})
    allowed_strengths = set(
        evidence_strength_schema.get("p7c_current_allowed")
        or evidence_strength_schema.get("allowed", [])
    )
    allowed_relations = set(schema.get("relation_types", []))

    for index, node in enumerate(nodes, 1):
        owner = f"{card_id}.flow_nodes[{index}]"
        if not isinstance(node, dict):
            errors.append(issue("invalid_node_object", f"{owner} is not an object"))
            continue
        for field in node_schema.get("required", []):
            if missing(node.get(field)):
                errors.append(issue("missing_required_field", f"{owner} missing required field {field}", field=field))
        node_id = node.get("node_id")
        if node_id in node_ids:
            errors.append(issue("duplicate_node_id", f"{owner} duplicate node_id {node_id}", node_id=node_id))
        elif node_id:
            node_ids.add(node_id)
            node_by_id[node_id] = node
        node_type = node.get("node_type")
        if node_type not in allowed_node_types:
            errors.append(issue("invalid_node_type", f"{owner} invalid node_type {node_type}"))
        expected_category = expected_node_category(node_type)
        if expected_category and node.get("node_category") != expected_category:
            errors.append(issue("node_category_mismatch", f"{owner} node_category {node.get('node_category')} does not match {node_type}", expected=expected_category))
        if node.get("evidence_strength") not in allowed_strengths:
            errors.append(issue("invalid_evidence_strength", f"{owner} invalid evidence_strength {node.get('evidence_strength')}"))
        if package is not None:
            validate_evidence_ids(owner, node.get("evidence_unit_ids"), allowed_unit_ids, errors)

    edge_ids: set[str] = set()
    for index, edge in enumerate(edges, 1):
        owner = f"{card_id}.flow_edges[{index}]"
        if not isinstance(edge, dict):
            errors.append(issue("invalid_edge_object", f"{owner} is not an object"))
            continue
        required_edge_fields = list(edge_schema.get("required", []))
        if "derivation" in required_edge_fields and "derivation" not in edge and edge.get("evidence_strength") is not None:
            required_edge_fields.remove("derivation")
        for field in required_edge_fields:
            if missing(edge.get(field)):
                errors.append(issue("missing_required_field", f"{owner} missing required field {field}", field=field))
        edge_id = edge.get("edge_id")
        if edge_id in edge_ids:
            errors.append(issue("duplicate_edge_id", f"{owner} duplicate edge_id {edge_id}", edge_id=edge_id))
        elif edge_id:
            edge_ids.add(edge_id)
        edge_type = edge.get("edge_type")
        if edge_type not in allowed_edge_types:
            errors.append(issue("invalid_edge_type", f"{owner} invalid edge_type {edge_type}"))
        source = edge.get("source")
        target = edge.get("target")
        if source not in node_ids:
            errors.append(issue("invalid_edge_reference", f"{owner} source {source} is not a node in this card"))
        if target not in node_ids:
            errors.append(issue("invalid_edge_reference", f"{owner} target {target} is not a node in this card"))
        if edge_type == "DECIDES" and missing(edge.get("condition")):
            errors.append(issue("missing_decides_condition", f"{owner} DECIDES edge missing condition"))
        source_category = (node_by_id.get(source) or {}).get("node_category")
        target_category = (node_by_id.get(target) or {}).get("node_category")
        target_type = (node_by_id.get(target) or {}).get("node_type")
        source_type = (node_by_id.get(source) or {}).get("node_type")
        if edge_type == "REFERENCES" and (source_category != "process" or target_type not in {"input", "standard"}):
            errors.append(issue("invalid_edge_endpoint_shape", f"{owner} REFERENCES must be process -> input/standard"))
        if edge_type == "PRODUCES" and (source_category != "process" or target_category != "exit"):
            errors.append(issue("invalid_edge_endpoint_shape", f"{owner} PRODUCES must be process -> exit"))
        if edge_type == "DECIDES" and source_type != "P3_branch_routing":
            errors.append(issue("invalid_edge_endpoint_shape", f"{owner} DECIDES source must be P3_branch_routing"))
        if edge.get("relation_type") and edge.get("relation_type") not in allowed_relations:
            errors.append(issue("invalid_relation_type", f"{owner} invalid relation_type {edge.get('relation_type')}"))
        edge_derivation = edge.get("derivation")
        if edge_derivation is not None:
            if edge_derivation not in set(schema.get("edge_derivations", ["explicit_text", "llm_inference"])):
                errors.append(issue("invalid_derivation", f"{owner} invalid derivation {edge_derivation}"))
        elif edge.get("evidence_strength") not in allowed_strengths:
            errors.append(issue("invalid_evidence_strength", f"{owner} missing derivation or invalid legacy evidence_strength {edge.get('evidence_strength')}"))
        if package is not None:
            validate_evidence_ids(owner, edge.get("evidence_unit_ids"), allowed_unit_ids, errors)

    if nodes and edges:
        errors.extend(graph_structure_errors(card_id, nodes, edges))
    graph_shape = derive_graph_shape(nodes, edges)
    return {
        "source_cards_path": source_path,
        "section_package_path": package_path,
        "section_id": section_id,
        "card_id": card_id,
        "title": card.get("title"),
        "structure_status": "fail" if errors else "pass",
        "structure_errors": errors,
        "node_count": len(nodes),
        "edge_count": len(edges),
        **graph_shape,
    }


def load_section_package(packages_dir: Path, section_id: str | None) -> dict[str, Any] | None:
    if not section_id:
        return None
    path = packages_dir / section_id / "task.json"
    if not path.exists():
        return None
    package = read_json(path)
    package["__package_path"] = path.resolve().as_posix()
    return package


def make_file_error(error: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_cards_path": error.get("source_path"),
        "section_package_path": None,
        "section_id": None,
        "card_id": None,
        "title": None,
        "structure_status": "validator_error",
        "structure_errors": [error],
        "node_count": 0,
        "edge_count": 0,
    }


def write_report(path: Path, results: list[dict[str, Any]], input_files: list[Path]) -> None:
    counts = Counter(row["structure_status"] for row in results)
    error_counts = Counter(error["code"] for row in results for error in row.get("structure_errors", []))
    lines = [
        "# P7D Structure Validation Report",
        "",
        "This report covers deterministic schema, ID, reference, evidence-scope, and graph-shape checks only. It does not confirm edge semantics.",
        "",
        f"input_file_count: {len(input_files)}",
        f"result_count: {len(results)}",
        f"pass: {counts.get('pass', 0)}",
        f"fail: {counts.get('fail', 0)}",
        f"validator_error: {counts.get('validator_error', 0)}",
    ]
    if error_counts:
        lines.extend(["", "## Error Types", ""])
        lines.extend(f"- {code}: {count}" for code, count in error_counts.most_common())
    failures = [row for row in results if row["structure_status"] != "pass"]
    if failures:
        lines.extend(["", "## Failures", ""])
        for row in failures[:200]:
            lines.append(f"- {row.get('section_id') or '<file>'} | {row.get('card_id') or row.get('source_cards_path')}")
            for error in row.get("structure_errors", [])[:5]:
                lines.append(f"  - {error['code']}: {error['message']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic P7D structure validation without semantic approval.")
    parser.add_argument("--cards", action="append", default=[], help="Path to cards.raw.json; repeatable.")
    parser.add_argument("--input-dir", action="append", default=[], help="Directory containing cards.raw.json; repeatable.")
    parser.add_argument("--packages-dir", default=str(DEFAULT_PACKAGES_DIR))
    parser.add_argument("--schema", default=str(SCHEMA_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()

    input_files = collect_card_files(args.cards, args.input_dir)
    if not input_files:
        raise SystemExit("No cards.raw.json inputs found. Use --cards or --input-dir.")

    schema = read_json(Path(args.schema))
    packages_dir = Path(args.packages_dir)
    cards: list[dict[str, Any]] = []
    file_errors: list[dict[str, Any]] = []
    for path in input_files:
        loaded, errors = read_cards_file(path)
        cards.extend(loaded)
        file_errors.extend(errors)
    card_id_counts = Counter(card.get("card_id") for card in cards if card.get("card_id"))

    results = [make_file_error(error) for error in file_errors]
    for card in cards:
        package = load_section_package(packages_dir, card.get("section_id"))
        results.append(
            validate_card_structure(
                card,
                package,
                schema,
                duplicate_card_id=card_id_counts.get(card.get("card_id"), 0) > 1,
            )
        )

    output_dir = Path(args.output_dir)
    manifest_path = output_dir / "p7d_structure_manifest.jsonl"
    queue_path = output_dir / "p7d_structure_error_queue.jsonl"
    report_path = output_dir / "p7d_structure_report.md"
    write_jsonl(manifest_path, results)
    write_jsonl(queue_path, [row for row in results if row["structure_status"] != "pass"])
    write_report(report_path, results, input_files)

    counts = Counter(row["structure_status"] for row in results)
    print(
        f"P7D structure validation: results={len(results)}, pass={counts.get('pass', 0)}, "
        f"fail={counts.get('fail', 0)}, validator_error={counts.get('validator_error', 0)}. "
        f"Report: {report_path}"
    )


if __name__ == "__main__":
    main()
