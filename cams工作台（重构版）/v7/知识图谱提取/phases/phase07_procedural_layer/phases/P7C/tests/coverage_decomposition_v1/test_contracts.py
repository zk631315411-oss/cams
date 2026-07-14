from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


RUNNER_PATH = Path(__file__).resolve().parent / "run_coverage_decomposition.py"
SPEC = importlib.util.spec_from_file_location("coverage_decomposition_runner_tests", RUNNER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load coverage decomposition runner")
RUNNER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNNER
SPEC.loader.exec_module(RUNNER)


def node(node_id: str, category: str, node_type: str) -> dict:
    return {
        "node_id": node_id,
        "node_category": category,
        "node_type": node_type,
        "label": node_id,
        "evidence_unit_ids": ["u1"],
        "evidence_strength": "explicit",
    }


def original_payload() -> dict:
    return {
        "section_id": "TEST-S01",
        "cards": [{
            "card_id": "p7card_TEST-S01_001",
            "section_id": "TEST-S01",
            "card_nature": "assessment",
            "title": "existing",
            "flow_nodes": [
                node("n1", "process", "P1_assessment"),
                node("n2", "auxiliary", "input"),
            ],
            "flow_edges": [{
                "edge_id": "e1",
                "edge_type": "REFERENCES",
                "source": "n1",
                "target": "n2",
                "evidence_unit_ids": ["u1"],
                "derivation": "explicit_text",
            }],
            "source_unit_ids": ["u1"],
            "candidate_status": "candidate",
            "review_notes": "test",
        }],
        "coverage_audit": [],
    }


def valid_audit() -> dict:
    return {
        "section_id": "TEST-S01",
        "scan_summary": "发现一个部分覆盖命题。",
        "claims": [{
            "claim_id": "claim_001",
            "unit_ids": ["u1"],
            "proposition": "评估有助于形成分类",
            "kg_boundary": "p7_incremental",
            "coverage_status": "partially_covered",
            "matched_card_ids": ["p7card_TEST-S01_001"],
            "missing_part": "缺少带限定词的分类出口",
            "condition": None,
            "qualifier": "有助于",
            "reason": "KG不能表达动作到限定性结果。",
        }],
    }


def valid_patch() -> dict:
    return {
        "section_id": "TEST-S01",
        "claim_resolutions": [{
            "claim_id": "claim_001",
            "resolution": "card_supplement",
            "card_id": "p7card_TEST-S01_001",
            "reason": "补充分类型结果。",
        }],
        "new_cards": [],
        "card_supplements": [{
            "patch_id": "coverage_patch_001",
            "card_id": "p7card_TEST-S01_001",
            "coverage_claim_ids": ["claim_001"],
            "reason": "补充分类型结果。",
            "add_flow_nodes": [node("n3", "exit", "X1_classification")],
            "add_flow_edges": [{
                "edge_id": "e2",
                "edge_type": "PRODUCES",
                "source": "n1",
                "target": "n3",
                "evidence_unit_ids": ["u1"],
                "derivation": "explicit_text",
                "qualifier": "有助于",
            }],
            "add_source_unit_ids": [],
        }],
    }


class CoverageDecompositionContractTests(unittest.TestCase):
    def test_valid_audit_and_patch_merge(self) -> None:
        original = original_payload()
        audit = valid_audit()
        patch = valid_patch()
        self.assertEqual(RUNNER.validate_audit(original, audit, {"u1"}), [])
        self.assertEqual(RUNNER.validate_patch(original, audit["claims"], patch, {"u1"}), [])
        merged = RUNNER.merge_patch(original, audit, patch)
        self.assertEqual(len(merged["cards"][0]["flow_nodes"]), 3)
        self.assertEqual(len(merged["cards"][0]["flow_edges"]), 2)
        self.assertEqual(original["cards"][0]["flow_edges"], original_payload()["cards"][0]["flow_edges"])

    def test_audit_rejects_topic_only_covered_claim(self) -> None:
        audit = valid_audit()
        audit["claims"][0]["coverage_status"] = "covered"
        audit["claims"][0]["missing_part"] = "仍缺少出口"
        errors = RUNNER.validate_audit(original_payload(), audit, {"u1"})
        self.assertTrue(any("covered status contract failed" in error for error in errors))

    def test_patch_rejects_missing_gap_resolution(self) -> None:
        patch = valid_patch()
        patch["claim_resolutions"] = []
        errors = RUNNER.validate_patch(original_payload(), valid_audit()["claims"], patch, {"u1"})
        self.assertTrue(any("must cover every" in error for error in errors))

    def test_patch_rejects_rewrite_and_out_of_section_evidence(self) -> None:
        patch = valid_patch()
        patch["card_supplements"][0]["add_flow_nodes"][0]["node_id"] = "n1"
        patch["card_supplements"][0]["add_flow_edges"][0]["evidence_unit_ids"] = ["u2"]
        errors = RUNNER.validate_patch(original_payload(), valid_audit()["claims"], patch, {"u1"})
        self.assertTrue(any("reuses existing node IDs" in error for error in errors))
        self.assertTrue(any("invalid evidence" in error for error in errors))

    def test_merge_is_additive(self) -> None:
        original = original_payload()
        before = copy.deepcopy(original)
        RUNNER.merge_patch(original, valid_audit(), valid_patch())
        self.assertEqual(original, before)


if __name__ == "__main__":
    unittest.main()
