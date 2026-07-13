from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


TEST_FILE = Path(__file__).resolve()
PHASE_DIR = next(parent for parent in TEST_FILE.parents if (parent / "scripts" / "validate_and_route_cards.py").exists())
VALIDATOR_PATH = PHASE_DIR / "scripts" / "validate_and_route_cards.py"
SPEC = importlib.util.spec_from_file_location("p7d_structure_validator", VALIDATOR_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)
SCHEMA = VALIDATOR.read_json(PHASE_DIR / "inputs" / "procedural_schema_v2.json")


def package() -> dict:
    return {
        "section_id": "TEST-S01",
        "section_title": "测试",
        "section_text_with_unit_anchors": "[u1|1] 事件后机构执行动作并形成结果。",
        "units": [{"unit_id": "u1", "en_quote": "After the event, the institution acts and produces a result."}],
        "__package_path": "TEST-S01/task.json",
    }


def card() -> dict:
    return {
        "card_id": "p7card_TEST-S01_001",
        "section_id": "TEST-S01",
        "card_nature": "execution",
        "title": "测试流程",
        "flow_nodes": [
            {"node_id": "e", "node_category": "entry", "node_type": "E1_event_signal", "label": "事件", "evidence_unit_ids": ["u1"], "evidence_strength": "explicit"},
            {"node_id": "p", "node_category": "process", "node_type": "P2_execution", "label": "机构执行动作", "evidence_unit_ids": ["u1"], "evidence_strength": "explicit"},
            {"node_id": "x", "node_category": "exit", "node_type": "X3_state_change", "label": "形成结果", "evidence_unit_ids": ["u1"], "evidence_strength": "explicit"},
        ],
        "flow_edges": [
            {"edge_id": "edge_1", "edge_type": "PRECEDES", "source": "e", "target": "p", "evidence_unit_ids": ["u1"], "evidence_strength": "explicit"},
            {"edge_id": "edge_2", "edge_type": "PRODUCES", "source": "p", "target": "x", "evidence_unit_ids": ["u1"], "evidence_strength": "explicit"},
        ],
        "source_unit_ids": ["u1"],
        "review_status": "accepted",
        "__source_path": "cards.raw.json",
    }


class P7DStructureValidatorTests(unittest.TestCase):
    def test_valid_card_passes_structure(self) -> None:
        result = VALIDATOR.validate_card_structure(card(), package(), SCHEMA)
        self.assertEqual(result["structure_status"], "pass")
        self.assertEqual(result["structure_errors"], [])

    def test_rule_validator_does_not_claim_semantic_direction_support(self) -> None:
        candidate = card()
        candidate["flow_edges"][0]["evidence_unit_ids"] = ["u1"]
        candidate["flow_edges"][0]["source_quote"] = "两个对象只是并列出现"
        result = VALIDATOR.validate_card_structure(candidate, package(), SCHEMA)
        self.assertEqual(result["structure_status"], "pass")

    def test_node_category_prefix_mismatch_fails(self) -> None:
        candidate = card()
        candidate["flow_nodes"][1]["node_category"] = "entry"
        result = VALIDATOR.validate_card_structure(candidate, package(), SCHEMA)
        self.assertEqual(result["structure_status"], "fail")
        self.assertIn("node_category_mismatch", {row["code"] for row in result["structure_errors"]})

    def test_out_of_section_evidence_fails(self) -> None:
        candidate = copy.deepcopy(card())
        candidate["flow_edges"][0]["evidence_unit_ids"] = ["u2"]
        result = VALIDATOR.validate_card_structure(candidate, package(), SCHEMA)
        self.assertEqual(result["structure_status"], "fail")
        self.assertIn("out_of_section_evidence", {row["code"] for row in result["structure_errors"]})

    def test_open_process_references_standard_relation_passes(self) -> None:
        candidate = {
            "card_id": "p7card_TEST-S01_open",
            "section_id": "TEST-S01",
            "card_nature": "control",
            "title": "受标准约束的动作",
            "flow_nodes": [
                {"node_id": "p", "node_category": "process", "node_type": "P8_constrained_action", "label": "机构执行动作", "evidence_unit_ids": ["u1"], "evidence_strength": "explicit"},
                {"node_id": "s", "node_category": "auxiliary", "node_type": "standard", "label": "适用标准", "evidence_unit_ids": ["u1"], "evidence_strength": "explicit"},
            ],
            "flow_edges": [
                {"edge_id": "edge_open", "edge_type": "REFERENCES", "source": "p", "target": "s", "relation_type": "standard_constrains_action", "evidence_unit_ids": ["u1"], "derivation": "explicit_text"}
            ],
            "source_unit_ids": ["u1"],
            "candidate_status": "candidate",
            "review_notes": "候选开放关系。",
            "__source_path": "cards.raw.json",
        }
        result = VALIDATOR.validate_card_structure(candidate, package(), SCHEMA)
        self.assertEqual(result["structure_status"], "pass")
        self.assertEqual(result["derived_graph_shape"], "open_relation")
        self.assertTrue(result["has_terminal_process"])


if __name__ == "__main__":
    unittest.main()
