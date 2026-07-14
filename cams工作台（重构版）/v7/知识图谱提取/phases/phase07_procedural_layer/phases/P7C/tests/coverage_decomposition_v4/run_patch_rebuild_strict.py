from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


TEST_DIR = Path(__file__).resolve().parent
PHASE_DIR = next(parent for parent in TEST_DIR.parents if (parent / "scripts" / "run_p7c_batch_ds.py").exists())
V3_RUNNER_PATH = PHASE_DIR / "phases" / "P7C" / "tests" / "coverage_decomposition_v3" / "run_patch_rebuild.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V3 = load_module("coverage_decomposition_v3_for_strict_contract", V3_RUNNER_PATH)
BASE_VALIDATE_PATCH = V3.V1.validate_patch

ALLOWED_RELATION_TYPES = {
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


def strict_validate_patch(
    original: dict[str, Any],
    gap_claims: list[dict[str, Any]],
    patch: dict[str, Any],
    allowed_unit_ids: set[str],
) -> list[str]:
    errors = BASE_VALIDATE_PATCH(original, gap_claims, patch, allowed_unit_ids)
    original_cards = {
        str(card.get("card_id")): card
        for card in original.get("cards") or []
        if isinstance(card, dict) and card.get("card_id")
    }

    def check_edges(owner: str, nodes: list[Any], edges: list[Any]) -> None:
        node_map = {
            str(node.get("node_id")): node
            for node in nodes
            if isinstance(node, dict) and node.get("node_id")
        }
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            edge_id = edge.get("edge_id") or "<missing>"
            relation_type = edge.get("relation_type")
            if relation_type is not None and relation_type not in ALLOWED_RELATION_TYPES:
                errors.append(f"{owner} edge {edge_id} has invalid relation_type {relation_type}")
            if relation_type == "branch_condition_routes_path" and (
                edge.get("edge_type") != "DECIDES" or not edge.get("condition")
            ):
                errors.append(f"{owner} edge {edge_id} invalid branch_condition_routes_path usage")
            source = node_map.get(str(edge.get("source")))
            target = node_map.get(str(edge.get("target")))
            edge_evidence = set(edge.get("evidence_unit_ids") or [])
            if source and not edge_evidence.intersection(source.get("evidence_unit_ids") or []):
                errors.append(f"{owner} edge {edge_id} evidence does not cover source node")
            if target and not edge_evidence.intersection(target.get("evidence_unit_ids") or []):
                errors.append(f"{owner} edge {edge_id} evidence does not cover target node")

    for card in patch.get("new_cards") or []:
        check_edges(
            f"new card {card.get('card_id')}",
            card.get("flow_nodes") or [],
            card.get("flow_edges") or [],
        )
    for supplement in patch.get("card_supplements") or []:
        original_card = original_cards.get(str(supplement.get("card_id")), {})
        check_edges(
            f"supplement {supplement.get('patch_id')}",
            [
                *(original_card.get("flow_nodes") or []),
                *(supplement.get("add_flow_nodes") or []),
            ],
            supplement.get("add_flow_edges") or [],
        )
    return errors


V3.V1.validate_patch = strict_validate_patch


if __name__ == "__main__":
    raise SystemExit(V3.main())
