from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


RUNNER_PATH = Path(__file__).resolve().parent / "run_patch_rebuild_strict.py"
SPEC = importlib.util.spec_from_file_location("coverage_decomposition_v4_tests", RUNNER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load strict patch runner")
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


def node(node_id: str, category: str, node_type: str, unit_id: str) -> dict:
    return {
        "node_id": node_id,
        "node_category": category,
        "node_type": node_type,
        "label": node_id,
        "evidence_unit_ids": [unit_id],
        "evidence_strength": "explicit",
    }


def payloads() -> tuple[dict, list[dict], dict]:
    original = {"section_id": "TEST-S01", "cards": [], "coverage_audit": []}
    claims = [{
        "claim_id": "claim_001",
        "unit_ids": ["u1", "u2"],
        "proposition": "test",
        "kg_boundary": "p7_incremental",
        "coverage_status": "missing",
        "matched_card_ids": [],
        "missing_part": "all",
        "condition": None,
        "qualifier": None,
        "reason": "test",
    }]
    patch = {
        "section_id": "TEST-S01",
        "claim_resolutions": [{
            "claim_id": "claim_001",
            "resolution": "new_card",
            "card_id": "p7card_TEST-S01_001",
            "reason": "test",
        }],
        "new_cards": [{
            "card_id": "p7card_TEST-S01_001",
            "section_id": "TEST-S01",
            "card_nature": "assessment",
            "title": "test",
            "flow_nodes": [
                node("n1", "process", "P1_assessment", "u1"),
                node("n2", "exit", "X1_classification", "u2"),
            ],
            "flow_edges": [{
                "edge_id": "e1",
                "edge_type": "PRODUCES",
                "source": "n1",
                "target": "n2",
                "evidence_unit_ids": ["u1", "u2"],
                "derivation": "explicit_text",
            }],
            "source_unit_ids": ["u1", "u2"],
            "candidate_status": "candidate",
            "review_notes": "test",
            "coverage_claim_ids": ["claim_001"],
        }],
        "card_supplements": [],
    }
    return original, claims, patch


class StrictPatchContractTests(unittest.TestCase):
    def test_valid_patch_passes(self) -> None:
        original, claims, patch = payloads()
        self.assertEqual(RUNNER.strict_validate_patch(original, claims, patch, {"u1", "u2"}), [])

    def test_unknown_relation_type_is_rejected(self) -> None:
        original, claims, patch = payloads()
        patch["new_cards"][0]["flow_edges"][0]["relation_type"] = "invented_type"
        errors = RUNNER.strict_validate_patch(original, claims, patch, {"u1", "u2"})
        self.assertTrue(any("invalid relation_type" in error for error in errors))

    def test_edge_evidence_must_cover_both_endpoints(self) -> None:
        original, claims, patch = payloads()
        patch["new_cards"][0]["flow_edges"][0]["evidence_unit_ids"] = ["u2"]
        errors = RUNNER.strict_validate_patch(original, claims, patch, {"u1", "u2"})
        self.assertTrue(any("does not cover source" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
