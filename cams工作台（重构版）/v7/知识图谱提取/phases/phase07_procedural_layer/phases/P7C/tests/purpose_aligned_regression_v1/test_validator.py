from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


TEST_FILE = Path(__file__).resolve()
PHASE_DIR = next(parent for parent in TEST_FILE.parents if (parent / "scripts" / "validate_process_cards.py").exists())
VALIDATOR_PATH = PHASE_DIR / "scripts" / "validate_process_cards.py"
SPEC = importlib.util.spec_from_file_location("validate_process_cards", VALIDATOR_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

SCHEMA = {
    "card_natures": ["execution", "assessment", "risk_indicator", "control"],
    "edge_properties": {"qualifier_allowed": [], "modality_allowed": []},
}


def base_card() -> dict:
    return {
        "card_id": "p7card_TEST_001",
        "section_id": "TEST-S01",
        "card_nature": "execution",
        "title": "测试流程",
        "flow_nodes": [
            {
                "node_id": "n_entry",
                "node_category": "entry",
                "node_type": "E1_event_signal",
                "label": "机构收到事件信号",
                "evidence_unit_ids": ["u1"],
                "evidence_strength": "explicit",
            },
            {
                "node_id": "n_process",
                "node_category": "process",
                "node_type": "P2_execution",
                "label": "机构：执行处理",
                "evidence_unit_ids": ["u1"],
                "evidence_strength": "explicit",
            },
            {
                "node_id": "n_exit",
                "node_category": "exit",
                "node_type": "X3_state_change",
                "label": "状态发生变化",
                "evidence_unit_ids": ["u1"],
                "evidence_strength": "explicit",
            },
        ],
        "flow_edges": [
            {
                "edge_id": "e1",
                "edge_type": "PRECEDES",
                "source": "n_entry",
                "target": "n_process",
                "evidence_unit_ids": ["u1"],
                "evidence_strength": "explicit",
            },
            {
                "edge_id": "e2",
                "edge_type": "PRODUCES",
                "source": "n_process",
                "target": "n_exit",
                "evidence_unit_ids": ["u1"],
                "evidence_strength": "explicit",
            },
        ],
        "source_unit_ids": ["u1"],
        "review_status": "accepted",
        "review_notes": "增量命题：事件导向处理并产生状态变化；KG不足：不能表达有向流程；选项判断：可判断顺序；LLM推理：无。",
    }


def validate(card: dict, unit_ids: set[str] | None = None, section_id: str = "TEST-S01") -> list[str]:
    return VALIDATOR.validate_card(card, unit_ids or {"u1"}, SCHEMA, expected_section_id=section_id)


class PurposeAlignedValidatorTests(unittest.TestCase):
    def assert_has_error(self, errors: list[str], fragment: str) -> None:
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_explicit_connected_card_is_valid(self) -> None:
        self.assertEqual(validate(base_card()), [])

    def test_functional_dependency_requires_review(self) -> None:
        card = base_card()
        card["flow_edges"][0]["evidence_strength"] = "functional_dependency"
        errors = validate(card)
        self.assert_has_error(errors, "functional_dependency edges require review_status 'needs_review'")

    def test_reviewed_functional_dependency_is_valid(self) -> None:
        card = base_card()
        card["flow_edges"][0]["evidence_strength"] = "functional_dependency"
        card["review_status"] = "needs_review"
        card["review_notes"] = "增量命题：事件导向处理；KG不足：不能表达方向；选项判断：可判断顺序；LLM推理：e1为必要功能先后，待人工复核。"
        self.assertEqual(validate(card), [])

    def test_nodes_cannot_be_llm_inferences(self) -> None:
        card = base_card()
        card["flow_nodes"][0]["evidence_strength"] = "functional_dependency"
        self.assert_has_error(validate(card), "flow_node #1 invalid evidence_strength 'functional_dependency'")

    def test_isolated_node_is_rejected(self) -> None:
        card = base_card()
        card["flow_nodes"].append(
            {
                "node_id": "n_aux",
                "node_category": "auxiliary",
                "node_type": "input",
                "label": "孤立输入",
                "evidence_unit_ids": ["u1"],
                "evidence_strength": "explicit",
            }
        )
        self.assert_has_error(validate(card), "isolated flow_node 'n_aux'")

    def test_directed_entry_process_exit_path_is_required(self) -> None:
        card = base_card()
        card["flow_edges"][0]["source"] = "n_process"
        card["flow_edges"][0]["target"] = "n_entry"
        self.assert_has_error(validate(card), "no directed entry -> process -> exit path")

    def test_multiple_components_are_rejected(self) -> None:
        card = base_card()
        card["flow_nodes"].extend(
            [
                {
                    "node_id": "n_entry_2",
                    "node_category": "entry",
                    "node_type": "E2_object_entry",
                    "label": "第二入口",
                    "evidence_unit_ids": ["u1"],
                    "evidence_strength": "explicit",
                },
                {
                    "node_id": "n_process_2",
                    "node_category": "process",
                    "node_type": "P1_assessment",
                    "label": "机构：第二处理",
                    "evidence_unit_ids": ["u1"],
                    "evidence_strength": "explicit",
                },
                {
                    "node_id": "n_exit_2",
                    "node_category": "exit",
                    "node_type": "X1_classification",
                    "label": "第二结论",
                    "evidence_unit_ids": ["u1"],
                    "evidence_strength": "explicit",
                },
            ]
        )
        card["flow_edges"].extend(
            [
                {
                    "edge_id": "e3",
                    "edge_type": "PRECEDES",
                    "source": "n_entry_2",
                    "target": "n_process_2",
                    "evidence_unit_ids": ["u1"],
                    "evidence_strength": "explicit",
                },
                {
                    "edge_id": "e4",
                    "edge_type": "PRODUCES",
                    "source": "n_process_2",
                    "target": "n_exit_2",
                    "evidence_unit_ids": ["u1"],
                    "evidence_strength": "explicit",
                },
            ]
        )
        self.assert_has_error(validate(card), "flow graph has 2 disconnected components")

    def test_references_must_start_at_process(self) -> None:
        card = base_card()
        card["flow_nodes"].append(
            {
                "node_id": "n_input",
                "node_category": "auxiliary",
                "node_type": "input",
                "label": "判断线索",
                "evidence_unit_ids": ["u1"],
                "evidence_strength": "explicit",
            }
        )
        card["flow_edges"].append(
            {
                "edge_id": "e3",
                "edge_type": "REFERENCES",
                "source": "n_entry",
                "target": "n_input",
                "evidence_unit_ids": ["u1"],
                "evidence_strength": "explicit",
            }
        )
        self.assert_has_error(validate(card), "REFERENCES source should be a process")

    def test_produces_must_start_at_process(self) -> None:
        card = base_card()
        card["flow_edges"][1]["source"] = "n_entry"
        self.assert_has_error(validate(card), "PRODUCES source should be a process")

    def test_decides_must_start_at_branch_routing_process(self) -> None:
        card = base_card()
        card["flow_edges"][1]["edge_type"] = "DECIDES"
        card["flow_edges"][1]["condition"] = "满足测试条件"
        self.assert_has_error(validate(card), "DECIDES source should be P3_branch_routing")

    def test_branch_routing_requires_two_explicit_paths(self) -> None:
        card = base_card()
        card["flow_nodes"][1]["node_type"] = "P3_branch_routing"
        card["flow_edges"][1]["edge_type"] = "DECIDES"
        card["flow_edges"][1]["condition"] = "满足测试条件"
        self.assert_has_error(validate(card), "requires at least two outgoing DECIDES edges")

    def test_needs_review_requires_an_inferred_edge(self) -> None:
        card = base_card()
        card["review_status"] = "needs_review"
        self.assert_has_error(validate(card), "requires at least one functional_dependency edge")

    def test_standard_relation_requires_references_to_standard(self) -> None:
        card = base_card()
        card["flow_edges"][0]["relation_type"] = "standard_constrains_action"
        self.assert_has_error(validate(card), "standard_constrains_action requires process REFERENCES standard")

    def test_identification_relation_requires_classification_result(self) -> None:
        card = base_card()
        card["flow_edges"][1]["relation_type"] = "identification_leads_to_conclusion"
        self.assert_has_error(validate(card), "requires process PRODUCES X1_classification")

    def test_conclusion_trigger_requires_finding_to_process(self) -> None:
        card = base_card()
        card["flow_edges"][1]["relation_type"] = "conclusion_triggers_response"
        self.assert_has_error(validate(card), "requires finding/classification PRECEDES process")

    def test_evidence_must_stay_inside_current_section(self) -> None:
        card = base_card()
        card["flow_edges"][0]["evidence_unit_ids"] = ["u2"]
        card["source_unit_ids"].append("u2")
        self.assert_has_error(validate(card, unit_ids={"u1"}), "unknown evidence_unit_id u2")

    def test_source_units_must_cover_node_and_edge_evidence(self) -> None:
        card = base_card()
        card["flow_edges"][0]["evidence_unit_ids"] = ["u2"]
        self.assert_has_error(validate(card, unit_ids={"u1", "u2"}), "evidence_unit_id u2 missing from source_unit_ids")

    def test_section_id_must_match_current_package(self) -> None:
        card = base_card()
        self.assert_has_error(validate(card, section_id="OTHER-S01"), "does not match current section")

    def test_valid_coverage_audit_references_card(self) -> None:
        card = base_card()
        payload = {
            "section_id": "TEST-S01",
            "coverage_audit": [
                {
                    "candidate_id": "cand_001",
                    "unit_ids": ["u1"],
                    "proposition": "事件触发处理并产生状态变化",
                    "decision": "p7c_card",
                    "card_id": card["card_id"],
                    "reason": "基础KG不能表达该有向流程。",
                }
            ],
            "cards": [card],
        }
        self.assertEqual(
            VALIDATOR.validate_coverage_audit(payload, [card], {"u1"}, "TEST-S01"),
            [],
        )

    def test_missing_coverage_audit_is_rejected(self) -> None:
        card = base_card()
        errors = VALIDATOR.validate_coverage_audit({"section_id": "TEST-S01", "cards": [card]}, [card], {"u1"}, "TEST-S01")
        self.assert_has_error(errors, "missing required top-level coverage_audit list")

    def test_coverage_audit_must_reference_every_card(self) -> None:
        card = base_card()
        payload = {"section_id": "TEST-S01", "coverage_audit": [], "cards": [card]}
        errors = VALIDATOR.validate_coverage_audit(payload, [card], {"u1"}, "TEST-S01")
        self.assert_has_error(errors, "does not reference output card_id")

    def test_flow_edge_count_uses_edges_inside_cards(self) -> None:
        first = base_card()
        second = base_card()
        second["flow_edges"] = []
        self.assertEqual(VALIDATOR.count_flow_edges([first, second]), len(first["flow_edges"]))


if __name__ == "__main__":
    unittest.main()
