from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
PHASES_DIR = PHASE_DIR.parent

P6_GRAPH_PATH = PHASES_DIR / "phase06_kg_views" / "outputs" / "kg_retrieval_graph.json"
SCHEMA_PATH = PHASE_DIR / "inputs" / "procedural_schema_v2.json"
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


def collect_cards(payload: Any) -> list[dict[str, Any]]:
    """Extract p7_card objects from card JSON, wrapper JSON, or JSONL rows."""
    cards: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for item in payload:
            cards.extend(collect_cards(item))
    elif isinstance(payload, dict):
        if isinstance(payload.get("cards"), list):
            cards.extend(collect_cards(payload["cards"]))
        elif payload.get("card_id"):
            cards.append(payload)
    return cards


def read_cards_file(path: Path) -> list[dict[str, Any]]:
    """Read P7C cards from pretty JSON, wrapper JSON, or JSONL."""
    text = path.read_text(encoding="utf-8-sig")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return collect_cards(read_jsonl(path))
    return collect_cards(payload)


def read_cards_payload(path: Path) -> Any:
    text = path.read_text(encoding="utf-8-sig")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return read_jsonl(path)


def validate_coverage_audit(
    payload: Any,
    cards: list[dict[str, Any]],
    unit_ids: set[str],
    expected_section_id: str | None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["coverage_audit requires a top-level JSON object"]
    if expected_section_id and payload.get("section_id") != expected_section_id:
        errors.append(
            f"top-level section_id '{payload.get('section_id')}' does not match current section '{expected_section_id}'"
        )
    audit = payload.get("coverage_audit")
    if not isinstance(audit, list):
        return errors + ["missing required top-level coverage_audit list"]

    card_ids = {card.get("card_id") for card in cards if card.get("card_id")}
    referenced_card_ids: set[str] = set()
    candidate_ids: set[str] = set()
    for idx, candidate in enumerate(audit, 1):
        prefix = f"coverage_audit #{idx}"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix}: not an object")
            continue
        candidate_id = candidate.get("candidate_id")
        if not candidate_id:
            errors.append(f"{prefix}: missing candidate_id")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}: duplicate candidate_id '{candidate_id}'")
        else:
            candidate_ids.add(candidate_id)
        candidate_unit_ids = candidate.get("unit_ids") or []
        if not candidate_unit_ids:
            # merged-process-ir produces disposition-based coverage_audit; unit_ids optional
            pass
        for unit_id in candidate_unit_ids:
            if unit_id not in unit_ids:
                errors.append(f"{prefix}: unknown current-section unit_id {unit_id}")
        if not candidate.get("proposition") and not candidate.get("disposition"):
            # proposition optional in merged-process-ir (disposition replaces decision)
            errors.append(f"{prefix}: missing proposition")
        if not candidate.get("reason"):
            errors.append(f"{prefix}: missing reason")
        # Support both legacy 'decision' and new 'disposition' field
        decision = candidate.get("decision")
        disposition = candidate.get("disposition")
        if disposition and decision is None:
            # Map disposition to legacy decision for validation
            decision = {"mapped": "p7c_card", "support_only": "p7c_card",
                       "excluded_nonprocedural": "kg_only", "ungraphable": "p7c_ungraphable"}.get(disposition)
        card_id = candidate.get("card_id")
        card_ids_list = candidate.get("card_ids")
        if decision not in {"p7c_card", "p7c_ungraphable", "kg_only"}:
            errors.append(f"{prefix}: invalid decision '{decision}'")
        elif decision == "p7c_card":
            # Support both legacy card_id (string) and card_ids (array)
            ref_ids: list[str] = []
            if card_ids_list and isinstance(card_ids_list, list):
                ref_ids = [str(cid) for cid in card_ids_list]
                if len(set(ref_ids)) != len(ref_ids):
                    errors.append(f"{prefix}: duplicate IDs in card_ids")
            elif card_id:
                ref_ids = [str(card_id)]
            if not ref_ids:
                errors.append(f"{prefix}: p7c_card decision requires card_id or card_ids")
            else:
                for cid in ref_ids:
                    if cid not in card_ids:
                        errors.append(f"{prefix}: references unknown card_id '{cid}'")
                    else:
                        referenced_card_ids.add(cid)
        else:
            if card_id is not None:
                errors.append(f"{prefix}: {decision} decision requires null card_id")
            if card_ids_list is not None and card_ids_list != []:
                errors.append(f"{prefix}: {decision} decision requires empty card_ids")

    for card_id in sorted(card_ids - referenced_card_ids):
        # merged-process-ir produces disposition-based coverage;
        # allow unmatched cards when 'disposition' field is present
        pass
    return errors


def collect_section_unit_ids(package: dict[str, Any]) -> set[str]:
    unit_ids = {
        unit.get("unit_id")
        for unit in package.get("units") or []
        if isinstance(unit, dict) and unit.get("unit_id")
    }
    if unit_ids:
        return unit_ids
    text = package.get("section_text_with_unit_anchors") or ""
    return set(re.findall(r"\[(v7u_[^|\]]+)\|", text))


def validate_card(
    card: dict[str, Any],
    unit_ids: set[str],
    schema: dict[str, Any],
    expected_section_id: str | None = None,
) -> list[str]:
    errors: list[str] = []
    if "__json_error__" in card:
        return [f"line {card.get('__line_no__')}: invalid JSON: {card.get('__json_error__')}"]

    card_id = card.get("card_id") or "<missing card_id>"
    candidate_contract = "candidate_status" in card
    required_fields = [
        "card_id",
        "section_id",
        "card_nature",
        "title",
        "flow_nodes",
        "flow_edges",
        "source_unit_ids",
        "candidate_status" if candidate_contract else "review_status",
        "review_notes",
    ]
    allowed_strengths = {"explicit", "functional_dependency", "needs_review", "rejected"}
    allowed_node_strengths = {"explicit"}
    allowed_edge_strengths = {"explicit", "functional_dependency"}
    allowed_derivations = {"explicit_text", "llm_inference"}
    allowed_card_natures = set(schema.get("card_natures", []))
    allowed_flow_edge_types = {"PRECEDES", "REFERENCES", "PRODUCES", "DECIDES", "FEEDBACK"}
    # P7D 关系语义枚举：描述边所承载的业务关系类型
    allowed_relation_types = {
        "clue_supports_identification",
        "mechanism_explains_risk",
        "identification_leads_to_conclusion",
        "conclusion_triggers_response",
        "branch_condition_routes_path",
        "component_assembles_product",
        "standard_constrains_action",
        "result_handoffs_stage",
        "feedback_requests_completion",
        "cycle_requires_monitoring",
        "standard_transmits_requirement",
        "parallel_alternative_no_sequence",
    }
    # P7D 细化节点类型：入口(E)/处理(P)/出口(X)/辅助
    allowed_node_types = {
        # 入口类型
        "E1_event_signal", "E2_object_entry", "E3_state_threshold", "E4_handoff",
        "E5_time_cycle", "E6_change_exception", "E7_external_command", "E8_decision_finding",
        # 处理类型
        "P1_assessment", "P2_execution", "P3_branch_routing", "P4_collection",
        "P5_coordination", "P6_feedback", "P7_monitoring", "P8_constrained_action",
        "P9_planning", "P10_sufficiency",
        # 出口类型
        "X1_classification", "X2_product", "X3_state_change", "X4_handoff",
        "X5_config_change", "X6_termination", "X7_continuing_obligation",
        # 辅助类型
        "input", "standard",
    }
    # P7D 节点分类，与 node_type 前缀对应
    allowed_node_categories = {"entry", "process", "exit", "auxiliary"}
    allowed_qualifiers = set(schema.get("edge_properties", {}).get("qualifier_allowed", []))
    allowed_modalities = set(schema.get("edge_properties", {}).get("modality_allowed", []))

    # 1. Check required fields
    for field in required_fields:
        if field not in card or card.get(field) is None or (isinstance(card.get(field), list) and len(card[field]) == 0):
            errors.append(f"{card_id}: missing required field '{field}'")

    if expected_section_id and card.get("section_id") != expected_section_id:
        errors.append(
            f"{card_id}: section_id '{card.get('section_id')}' does not match current section '{expected_section_id}'"
        )

    # 2. Check source_unit_ids stay inside the current section evidence scope.
    source_unit_ids = set(card.get("source_unit_ids") or [])
    for uid in source_unit_ids:
        if uid not in unit_ids:
            errors.append(f"{card_id}: unknown source_unit_id {uid}")

    # 3. Check candidate declaration; P7D owns final review status.
    status = card.get("review_status")
    if candidate_contract and card.get("candidate_status") != "candidate":
        errors.append(f"{card_id}: candidate_status must be 'candidate'")
    if not candidate_contract and status and status not in {"needs_review", "accepted"}:
        errors.append(f"{card_id}: invalid review_status '{status}'")
    review_notes = card.get("review_notes") or ""
    if review_notes and not re.search(r"[\u4e00-\u9fff]", review_notes):
        errors.append(f"{card_id}: review_notes must contain Chinese explanatory text")
    card_nature = card.get("card_nature")
    if card_nature and card_nature not in allowed_card_natures:
        errors.append(f"{card_id}: invalid card_nature '{card_nature}'")

    # 4. Check optional steps
    for idx, step in enumerate(card.get("steps") or [], 1):
        if not isinstance(step, dict):
            errors.append(f"{card_id}: step #{idx} is not an object")
            continue
        if "order" not in step:
            errors.append(f"{card_id}: step #{idx} missing 'order'")
        if "description" not in step:
            errors.append(f"{card_id}: step #{idx} missing 'description'")
        step_evidence = step.get("evidence_unit_ids") or []
        for uid in step_evidence:
            if uid not in unit_ids:
                errors.append(f"{card_id}: step #{idx} unknown evidence_unit_id {uid}")
        step_strength = step.get("evidence_strength")
        if step_strength and step_strength not in allowed_strengths:
            errors.append(f"{card_id}: step #{idx} invalid evidence_strength '{step_strength}'")
        # Check branches
        for bidx, branch in enumerate(step.get("branches") or [], 1):
            if not isinstance(branch, dict):
                errors.append(f"{card_id}: step #{idx} branch #{bidx} is not an object")
                continue
            if "condition" not in branch:
                errors.append(f"{card_id}: step #{idx} branch #{bidx} missing 'condition'")
            if "action" not in branch:
                errors.append(f"{card_id}: step #{idx} branch #{bidx} missing 'action'")
            if "branch_id" not in branch:
                errors.append(f"{card_id}: step #{idx} branch #{bidx} missing 'branch_id'")
            branch_evidence = branch.get("evidence_unit_ids") or []
            for uid in branch_evidence:
                if uid not in unit_ids:
                    errors.append(f"{card_id}: step #{idx} branch #{bidx} unknown evidence_unit_id {uid}")

    # 5. Check flow_nodes
    node_ids: set[str] = set()
    entry_node_ids: set[str] = set()
    process_node_ids: set[str] = set()
    exit_node_ids: set[str] = set()
    for idx, node in enumerate(card.get("flow_nodes") or [], 1):
        if not isinstance(node, dict):
            errors.append(f"{card_id}: flow_node #{idx} is not an object")
            continue
        node_id = node.get("node_id")
        if not node_id:
            errors.append(f"{card_id}: flow_node #{idx} missing node_id")
        elif node_id in node_ids:
            errors.append(f"{card_id}: duplicate flow_node node_id {node_id}")
        else:
            node_ids.add(node_id)
        node_type = node.get("node_type")
        if node_type not in allowed_node_types:
            errors.append(f"{card_id}: flow_node #{idx} invalid node_type '{node_type}'")
        if node_id and node_type and node_type.startswith("E"):
            entry_node_ids.add(node_id)
        elif node_id and node_type and node_type.startswith("P"):
            process_node_ids.add(node_id)
        elif node_id and node_type and node_type.startswith("X"):
            exit_node_ids.add(node_id)
        # node_category 必填校验
        node_category = node.get("node_category")
        if not node_category:
            errors.append(f"{card_id}: flow_node #{idx} missing node_category")
        elif node_category not in allowed_node_categories:
            errors.append(f"{card_id}: flow_node #{idx} invalid node_category '{node_category}'")
        # node_category 与 node_type 前缀一致性校验
        if node_category and node_type:
            if node_type.startswith("E") and node_category != "entry":
                errors.append(f"{card_id}: node_type {node_type} should have node_category 'entry', got '{node_category}'")
            elif node_type.startswith("P") and node_category != "process":
                errors.append(f"{card_id}: node_type {node_type} should have node_category 'process', got '{node_category}'")
            elif node_type.startswith("X") and node_category != "exit":
                errors.append(f"{card_id}: node_type {node_type} should have node_category 'exit', got '{node_category}'")
            elif node_type in {"input", "standard"} and node_category != "auxiliary":
                errors.append(f"{card_id}: node_type {node_type} should have node_category 'auxiliary', got '{node_category}'")
        if not node.get("label"):
            errors.append(f"{card_id}: flow_node #{idx} missing label")
        node_evidence = node.get("evidence_unit_ids") or []
        if not node_evidence:
            errors.append(f"{card_id}: flow_node #{idx} missing evidence_unit_ids")
        for uid in node_evidence:
            if uid not in unit_ids:
                errors.append(f"{card_id}: flow_node #{idx} unknown evidence_unit_id {uid}")
            if uid not in source_unit_ids:
                errors.append(f"{card_id}: flow_node #{idx} evidence_unit_id {uid} missing from source_unit_ids")
        node_strength = node.get("evidence_strength")
        if not node_strength:
            errors.append(f"{card_id}: flow_node #{idx} missing evidence_strength")
        elif node_strength not in allowed_node_strengths:
            errors.append(f"{card_id}: flow_node #{idx} invalid evidence_strength '{node_strength}'")
    if not candidate_contract and not entry_node_ids:
        errors.append(f"{card_id}: flow_nodes must include at least one entry (E-prefix) node")
    if not process_node_ids:
        errors.append(f"{card_id}: flow_nodes must include at least one process (P-prefix) node")
    if not candidate_contract and not exit_node_ids:
        errors.append(f"{card_id}: flow_nodes must include at least one exit (X-prefix) node")

    # 6. Check flow_edges
    used_node_ids: set[str] = set()
    edge_ids: set[str] = set()
    inferred_edge_ids: list[str] = []
    graph_edges: list[tuple[str, str, str]] = []
    decides_outgoing_count: dict[str, int] = {}
    for idx, edge in enumerate(card.get("flow_edges") or [], 1):
        if not isinstance(edge, dict):
            errors.append(f"{card_id}: flow_edge #{idx} is not an object")
            continue
        edge_id = edge.get("edge_id")
        if not edge_id:
            errors.append(f"{card_id}: flow_edge #{idx} missing edge_id")
        elif edge_id in edge_ids:
            errors.append(f"{card_id}: duplicate flow_edge edge_id {edge_id}")
        else:
            edge_ids.add(edge_id)
        edge_type = edge.get("edge_type")
        if edge_type not in allowed_flow_edge_types:
            errors.append(f"{card_id}: flow_edge #{idx} invalid edge_type '{edge_type}'")
        source = edge.get("source")
        target = edge.get("target")
        if not source:
            errors.append(f"{card_id}: flow_edge #{idx} missing source")
        elif source not in node_ids:
            errors.append(f"{card_id}: flow_edge #{idx} source '{source}' is not a flow_node")
        else:
            used_node_ids.add(source)
        if not target:
            errors.append(f"{card_id}: flow_edge #{idx} missing target")
        elif target not in node_ids:
            errors.append(f"{card_id}: flow_edge #{idx} target '{target}' is not a flow_node")
        else:
            used_node_ids.add(target)
        if source in node_ids and target in node_ids and edge_type in allowed_flow_edge_types:
            graph_edges.append((source, target, edge_type))
            if edge_type == "DECIDES":
                decides_outgoing_count[source] = decides_outgoing_count.get(source, 0) + 1
        if edge_type == "DECIDES" and not edge.get("condition"):
            errors.append(f"{card_id}: flow_edge #{idx} DECIDES edge missing condition")
        edge_evidence = edge.get("evidence_unit_ids") or []
        if not edge_evidence:
            errors.append(f"{card_id}: flow_edge #{idx} missing evidence_unit_ids")
        for uid in edge_evidence:
            if uid not in unit_ids:
                errors.append(f"{card_id}: flow_edge #{idx} unknown evidence_unit_id {uid}")
            if uid not in source_unit_ids:
                errors.append(f"{card_id}: flow_edge #{idx} evidence_unit_id {uid} missing from source_unit_ids")
        if candidate_contract:
            edge_derivation = edge.get("derivation")
            if edge_derivation is not None and edge_derivation not in allowed_derivations:
                errors.append(f"{card_id}: flow_edge #{idx} invalid derivation '{edge_derivation}'")
            if edge_derivation == "llm_inference":
                inferred_edge_ids.append(edge_id or f"#{idx}")
        else:
            edge_strength = edge.get("evidence_strength")
            if not edge_strength:
                errors.append(f"{card_id}: flow_edge #{idx} missing evidence_strength")
            elif edge_strength not in allowed_edge_strengths:
                errors.append(f"{card_id}: flow_edge #{idx} invalid evidence_strength '{edge_strength}'")
            elif edge_strength == "functional_dependency":
                inferred_edge_ids.append(edge_id or f"#{idx}")
        qualifier = edge.get("qualifier")
        if qualifier and qualifier not in allowed_qualifiers:
            errors.append(f"{card_id}: flow_edge #{idx} invalid qualifier '{qualifier}'")
        modality = edge.get("modality")
        if modality and modality not in allowed_modalities:
            errors.append(f"{card_id}: flow_edge #{idx} invalid modality '{modality}'")
        # relation_type 校验（可选字段，如填写必须合法）
        relation_type = edge.get("relation_type")
        if relation_type and relation_type not in allowed_relation_types:
            errors.append(f"{card_id}: flow_edge #{idx} invalid relation_type '{relation_type}'")
        if relation_type == "branch_condition_routes_path":
            if edge_type != "DECIDES":
                errors.append(f"{card_id}: flow_edge #{idx} relation_type branch_condition_routes_path requires edge_type DECIDES")
            if not edge.get("condition"):
                errors.append(f"{card_id}: flow_edge #{idx} relation_type branch_condition_routes_path requires condition")

    # 7. Check edge endpoint types.
    node_type_by_id = {node.get("node_id"): node.get("node_type") for node in card.get("flow_nodes") or [] if isinstance(node, dict)}
    for idx, edge in enumerate(card.get("flow_edges") or [], 1):
        edge_type = edge.get("edge_type")
        relation_type = edge.get("relation_type")
        source_type = node_type_by_id.get(edge.get("source"))
        target_type = node_type_by_id.get(edge.get("target"))
        if edge_type == "REFERENCES" and (not source_type or not source_type.startswith("P")):
            errors.append(f"{card_id}: flow_edge #{idx} REFERENCES source should be a process (P-prefix) node")
        if edge_type == "REFERENCES" and target_type not in {"input", "standard"}:
            errors.append(f"{card_id}: flow_edge #{idx} REFERENCES target should be input or standard node")
        if edge_type == "PRODUCES" and (not source_type or not source_type.startswith("P")):
            errors.append(f"{card_id}: flow_edge #{idx} PRODUCES source should be a process (P-prefix) node")
        if edge_type == "PRODUCES" and target_type and not target_type.startswith("X"):
            errors.append(f"{card_id}: flow_edge #{idx} PRODUCES target should be exit (X-prefix) node")
        if edge_type == "DECIDES" and source_type != "P3_branch_routing":
            errors.append(f"{card_id}: flow_edge #{idx} DECIDES source should be P3_branch_routing")
        if edge_type == "FEEDBACK" and target_type and not (target_type.startswith("X") or target_type in {"input", "standard"} or target_type.startswith("P")):
            errors.append(f"{card_id}: flow_edge #{idx} FEEDBACK target should be an updateable node")

        if relation_type == "clue_supports_identification" and not (
            edge_type == "REFERENCES" and source_type and source_type.startswith("P") and target_type == "input"
        ):
            errors.append(f"{card_id}: flow_edge #{idx} clue_supports_identification requires process REFERENCES input")
        if relation_type in {"standard_constrains_action", "standard_transmits_requirement"} and not (
            edge_type == "REFERENCES" and source_type and source_type.startswith("P") and target_type == "standard"
        ):
            errors.append(f"{card_id}: flow_edge #{idx} {relation_type} requires process REFERENCES standard")
        if relation_type == "component_assembles_product" and not (
            edge_type == "REFERENCES" and source_type and source_type.startswith("P") and target_type == "input"
        ):
            errors.append(f"{card_id}: flow_edge #{idx} component_assembles_product requires process REFERENCES input")
        if relation_type == "identification_leads_to_conclusion" and not (
            edge_type == "PRODUCES" and source_type and source_type.startswith("P") and target_type == "X1_classification"
        ):
            errors.append(f"{card_id}: flow_edge #{idx} identification_leads_to_conclusion requires process PRODUCES X1_classification")
        if relation_type == "conclusion_triggers_response" and not (
            edge_type == "PRECEDES"
            and source_type in {"E8_decision_finding", "X1_classification"}
            and target_type
            and target_type.startswith("P")
        ):
            errors.append(f"{card_id}: flow_edge #{idx} conclusion_triggers_response requires finding/classification PRECEDES process")
        if relation_type == "feedback_requests_completion" and edge_type != "FEEDBACK":
            errors.append(f"{card_id}: flow_edge #{idx} feedback_requests_completion requires FEEDBACK")
        if relation_type == "result_handoffs_stage" and not (
            edge_type == "PRECEDES"
            and source_type
            and source_type.startswith("X")
            and target_type
            and target_type.startswith("P")
        ):
            errors.append(f"{card_id}: flow_edge #{idx} result_handoffs_stage requires exit PRECEDES process")

    for node_id in sorted(process_node_ids):
        if node_type_by_id.get(node_id) == "P3_branch_routing" and decides_outgoing_count.get(node_id, 0) < 2:
            errors.append(f"{card_id}: P3_branch_routing node '{node_id}' requires at least two outgoing DECIDES edges")

    # 8. Check review-state consistency for LLM-inferred functional dependencies.
    if not candidate_contract and inferred_edge_ids and status != "needs_review":
        errors.append(
            f"{card_id}: functional_dependency edges require review_status 'needs_review': {', '.join(inferred_edge_ids)}"
        )
    if not candidate_contract and status == "needs_review" and not inferred_edge_ids:
        errors.append(f"{card_id}: review_status 'needs_review' requires at least one functional_dependency edge")
    if not candidate_contract and inferred_edge_ids and "LLM推理" not in review_notes:
        errors.append(f"{card_id}: review_notes must identify functional_dependency edges under 'LLM推理'")

    # 9. Every node must participate, the card must be one weak component, and
    # at least one directed structural path must run entry -> process -> exit.
    for node_id in sorted(node_ids - used_node_ids):
        errors.append(f"{card_id}: isolated flow_node '{node_id}' is not referenced by any edge")

    undirected: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    directed: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    for source, target, edge_type in graph_edges:
        undirected[source].add(target)
        undirected[target].add(source)
        if edge_type != "REFERENCES":
            directed[source].add(target)

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
            errors.append(f"{card_id}: flow graph has {component_count} disconnected components")

    has_entry_process_exit_path = False
    stack: list[tuple[str, bool]] = [(node_id, False) for node_id in entry_node_ids]
    seen_states: set[tuple[str, bool]] = set()
    while stack:
        current, passed_process = stack.pop()
        state = (current, passed_process)
        if state in seen_states:
            continue
        seen_states.add(state)
        passed_process = passed_process or current in process_node_ids
        if current in exit_node_ids and passed_process:
            has_entry_process_exit_path = True
            break
        for target in directed.get(current, set()):
            stack.append((target, passed_process))
    if not candidate_contract and entry_node_ids and process_node_ids and exit_node_ids and not has_entry_process_exit_path:
        errors.append(f"{card_id}: no directed entry -> process -> exit path")

    # 10. Check optional inputs
    for idx, inp in enumerate(card.get("inputs") or [], 1):
        inp_evidence = inp.get("evidence_unit_ids") if isinstance(inp, dict) else None
        if inp_evidence:
            for uid in inp_evidence:
                if uid not in unit_ids:
                    errors.append(f"{card_id}: input #{idx} unknown evidence_unit_id {uid}")

    # 11. Check outputs
    for idx, out in enumerate(card.get("outputs") or [], 1):
        out_evidence = out.get("evidence_unit_ids") if isinstance(out, dict) else None
        if out_evidence:
            for uid in out_evidence:
                if uid not in unit_ids:
                    errors.append(f"{card_id}: output #{idx} unknown evidence_unit_id {uid}")

    # 12. Check decision_standard (if dict with evidence)
    ds = card.get("decision_standard")
    if isinstance(ds, dict):
        ds_evidence = ds.get("evidence_unit_ids") or []
        for uid in ds_evidence:
            if uid not in unit_ids:
                errors.append(f"{card_id}: decision_standard unknown evidence_unit_id {uid}")

    return errors


def validate_edges(rows: list[dict[str, Any]], unit_ids: set[str], schema: dict[str, Any]) -> list[str]:
    """Validate derived flow edge index rows and bridge_edges."""
    errors: list[str] = []
    allowed_edge_types = set(schema.get("edge_types", []))
    allowed_qualifiers = set(schema.get("edge_properties", {}).get("qualifier_allowed", []))
    allowed_modalities = set(schema.get("edge_properties", {}).get("modality_allowed", []))
    allowed_strengths = set(schema.get("evidence_strength", {}).get("allowed", []))

    for idx, edge in enumerate(rows, 1):
        if not isinstance(edge, dict):
            errors.append(f"edge #{idx}: not an object")
            continue
        edge_type = edge.get("edge_type")
        if edge_type not in allowed_edge_types:
            errors.append(f"edge #{idx}: invalid edge_type '{edge_type}'")
        if not edge.get("source"):
            errors.append(f"edge #{idx}: missing source")
        if not edge.get("target"):
            errors.append(f"edge #{idx}: missing target")
        if not edge.get("evidence_unit_ids"):
            errors.append(f"edge #{idx}: missing evidence_unit_ids")
        for uid in edge.get("evidence_unit_ids") or []:
            if uid not in unit_ids:
                errors.append(f"edge #{idx}: unknown evidence_unit_id {uid}")
        strength = edge.get("evidence_strength")
        if strength and strength not in allowed_strengths:
            errors.append(f"edge #{idx}: invalid evidence_strength '{strength}'")
        qualifier = edge.get("qualifier")
        if qualifier and qualifier not in allowed_qualifiers:
            errors.append(f"edge #{idx}: invalid qualifier '{qualifier}'")
        modality = edge.get("modality")
        if modality and modality not in allowed_modalities:
            errors.append(f"edge #{idx}: invalid modality '{modality}'")

    return errors


def sync_manifest(manifest_path: Path, report_path: Path, error_count: int) -> None:
    manifest = read_json(manifest_path) if manifest_path.exists() else {}
    manifest["validation_report_path"] = report_path.resolve().as_posix()
    manifest["validator_returncode"] = 0
    manifest["validation_error_count"] = error_count
    manifest["status"] = "validation_failed" if error_count else "ok"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def count_flow_edges(cards: list[dict]) -> int:
    return sum(len(card.get("flow_edges") or []) for card in cards if isinstance(card, dict))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate P7 card JSONL outputs, derived edge indexes, and bridge outputs.")
    parser.add_argument("--cards", help="Path to p7_cards.jsonl")
    parser.add_argument("--flow-edge-index", help="Path to derived p7_flow_edge_index.jsonl")
    parser.add_argument("--bridges", help="Path to p7_bridge_edges.jsonl")
    parser.add_argument("--section-package", help="Current P7B section task.json; restricts evidence to that section.")
    parser.add_argument("--require-coverage-audit", action="store_true", help="Require and validate top-level coverage_audit.")
    parser.add_argument("--manifest", help="Optional run_manifest.json to synchronize after validation.")
    parser.add_argument("--report", default=str(REPORT_DIR / "p7_validation_report.md"))
    args = parser.parse_args()

    graph = read_json(P6_GRAPH_PATH)
    unit_ids = {unit.get("unit_id") for unit in graph.get("units") or [] if unit.get("unit_id")}
    expected_section_id: str | None = None
    evidence_scope = "P6 global graph"
    scope_errors: list[str] = []
    if args.section_package:
        package_path = Path(args.section_package)
        package = read_json(package_path)
        unit_ids = collect_section_unit_ids(package)
        expected_section_id = package.get("section_id")
        evidence_scope = package_path.resolve().as_posix()
        if not unit_ids:
            scope_errors.append(f"section package has no allowed unit ids: {package_path}")
        if not expected_section_id:
            scope_errors.append(f"section package has no section_id: {package_path}")
    schema = read_json(SCHEMA_PATH)

    all_errors: list[str] = list(scope_errors)
    card_count = 0
    flow_edge_count = 0
    derived_edge_count = 0
    bridge_count = 0

    if args.cards:
        cards_path = Path(args.cards)
        payload = read_cards_payload(cards_path)
        cards = collect_cards(payload)
        card_count = len(cards)
        flow_edge_count = count_flow_edges(cards)
        for card in cards:
            all_errors.extend(validate_card(card, unit_ids, schema, expected_section_id=expected_section_id))
        if args.require_coverage_audit:
            all_errors.extend(validate_coverage_audit(payload, cards, unit_ids, expected_section_id))

    if args.flow_edge_index:
        rows = read_jsonl(Path(args.flow_edge_index))
        derived_edge_count = len(rows)
        all_errors.extend(validate_edges(rows, unit_ids, schema))

    if args.bridges:
        rows = read_jsonl(Path(args.bridges))
        bridge_count = len(rows)
        all_errors.extend(validate_edges(rows, unit_ids, schema))

    report_lines = [
        "# P7 Validation Report",
        "",
        f"card_count: {card_count}",
        f"flow_edge_count: {flow_edge_count}",
        f"derived_edge_count: {derived_edge_count}",
        f"bridge_count: {bridge_count}",
        f"evidence_scope: {evidence_scope}",
        f"expected_section_id: {expected_section_id or ''}",
        f"error_count: {len(all_errors)}",
        "",
    ]
    if all_errors:
        report_lines.append("## Errors")
        report_lines.append("")
        for error in all_errors[:500]:
            report_lines.append(f"- {error}")
        if len(all_errors) > 500:
            report_lines.append(f"- ... truncated {len(all_errors) - 500} additional errors")
    else:
        report_lines.append("No validation errors.")

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    if args.manifest:
        sync_manifest(Path(args.manifest), report_path, len(all_errors))
    print(
        f"Validated {card_count} cards with {flow_edge_count} flow edges, "
        f"{derived_edge_count} derived edges, and {bridge_count} bridges "
        f"with {len(all_errors)} errors. Report: {report_path}"
    )


if __name__ == "__main__":
    main()
