from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


TEST_FILE = Path(__file__).resolve()
PHASE_DIR = next(parent for parent in TEST_FILE.parents if (parent / "scripts" / "run_p7c_batch_ds.py").exists())


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load_module("p7c_three_stage_runner", PHASE_DIR / "scripts" / "run_p7c_batch_ds.py")
VALIDATOR = load_module("p7c_three_stage_validator", PHASE_DIR / "scripts" / "validate_process_cards.py")
SUMMARIZER = load_module("p7_pipeline_summarizer", PHASE_DIR / "scripts" / "summarize_p7_pipeline.py")
P7C_PROMPTS = PHASE_DIR / "phases" / "P7C" / "prompts"


def task() -> dict:
    return {
        "section_id": "TEST-S01",
        "section_title": "测试",
        "section_text_with_unit_anchors": "[u1|1] 当事件发生时，机构执行动作。",
        "units": [{"unit_id": "u1"}],
        "core_points": [],
    }


def proposition() -> dict:
    return {
        "candidate_id": "prop_001",
        "unit_ids": ["u1"],
        "proposition": "当事件发生时，机构执行动作。",
        "source_quotes": ["当事件发生时"],
        "relation_cues": ["when"],
        "candidate_frame": {
            "trigger_or_context": ["事件发生"],
            "basis_or_condition": [],
            "focal_handling_or_judgment": "机构执行动作",
            "outcomes_or_paths": [],
        },
        "evidence_spans": [{"unit_id": "u1", "quote": "当事件发生时"}],
        "induction": None,
        "cross_unit_basis": None,
    }


def card() -> dict:
    return {
        "card_id": "p7card_TEST-S01_001",
        "section_id": "TEST-S01",
        "card_nature": "execution",
        "title": "测试流程",
        "flow_nodes": [
            {
                "node_id": "e",
                "node_category": "entry",
                "node_type": "E1_event_signal",
                "label": "事件发生",
                "evidence_unit_ids": ["u1"],
                "evidence_strength": "explicit",
            },
            {
                "node_id": "p",
                "node_category": "process",
                "node_type": "P2_execution",
                "label": "机构执行动作",
                "evidence_unit_ids": ["u1"],
                "evidence_strength": "explicit",
            },
        ],
        "flow_edges": [
            {
                "edge_id": "e1",
                "edge_type": "PRECEDES",
                "source": "e",
                "target": "p",
                "condition": "当事件发生时",
                "evidence_unit_ids": ["u1"],
            }
        ],
        "source_unit_ids": ["u1"],
        "candidate_status": "candidate",
        "review_notes": "增量命题：事件触发动作；KG不足：不能表达方向；选项判断：可判断条件。",
    }


class ThreeStageContractTests(unittest.TestCase):
    def test_rendered_prompts_are_self_contained_and_have_no_placeholders(self) -> None:
        s1_template = (P7C_PROMPTS / "proposition_discovery_v1.md").read_text(encoding="utf-8")
        s2_template = (P7C_PROMPTS / "kg_boundary_adjudication_v1.md").read_text(encoding="utf-8")
        s3_template = (P7C_PROMPTS / "semantic_graph_construction_v1.md").read_text(encoding="utf-8")
        prop = proposition()
        passed = [{"candidate": prop, "boundary_decision": {"decision": "p7c_candidate", "reason": "增量"}}]
        prompts = [
            RUNNER.build_s1_prompt(s1_template, task()),
            RUNNER.build_s2_prompt(s2_template, task(), [prop]),
            RUNNER.build_s3_prompt(s3_template, task(), passed),
        ]
        for prompt in prompts:
            for placeholder in (
                "<SECTION_TEXT>",
                "<ALLOWED_UNIT_IDS>",
                "<S1_PROPOSITIONS_JSON>",
                "<S2_PASSED_CANDIDATES_JSON>",
            ):
                self.assertNotIn(placeholder, prompt)
            self.assertEqual(prompt.count("## 当前section"), 1)
            self.assertIn("[u1|1]", prompt)
        self.assertIn("E1_event_signal", prompts[2])
        self.assertIn("branch_condition_routes_path", prompts[2])
        self.assertIn("candidate_status", prompts[2])

    def test_stage_contracts_require_exact_candidate_coverage(self) -> None:
        prop = proposition()
        self.assertEqual(RUNNER.validate_s1_discovery_payload({"propositions": [prop]}, {"u1"}), [])
        missing_s2 = RUNNER.validate_s2_boundary_payload({"boundary_decisions": []}, [prop])
        self.assertTrue(any("missing S1 candidates" in error for error in missing_s2), missing_s2)
        passed = [{"candidate": prop, "boundary_decision": {"decision": "p7c_candidate", "reason": "增量"}}]
        missing_s3 = RUNNER.validate_s3_construction_payload(
            {"construction_audit": [], "cards": []}, passed, "TEST-S01", {"u1"}
        )
        self.assertTrue(any("cover every passed candidate" in error for error in missing_s3), missing_s3)

    def test_s3_contract_rejects_derivation_and_unknown_card_reference(self) -> None:
        prop = proposition()
        passed = [{"candidate": prop, "boundary_decision": {"decision": "p7c_candidate", "reason": "增量"}}]
        candidate_card = card()
        candidate_card["flow_edges"][0]["derivation"] = "explicit_text"
        errors = RUNNER.validate_s3_construction_payload(
            {
                "construction_audit": [
                    {
                        "candidate_id": "prop_001",
                        "construction_status": "graphed",
                        "card_ids": ["missing"],
                        "reason": "成图",
                    }
                ],
                "cards": [candidate_card],
            },
            passed,
            "TEST-S01",
            {"u1"},
        )
        self.assertTrue(any("must not declare derivation" in error for error in errors), errors)
        self.assertTrue(any("unknown card_id missing" in error for error in errors), errors)

    def test_coverage_merge_maps_internal_decisions_to_final_contract(self) -> None:
        prop = proposition()
        graphed = RUNNER._merge_coverage_audit(
            [{"candidate_id": "prop_001", "decision": "p7c_candidate", "reason": "增量"}],
            [
                {
                    "candidate_id": "prop_001",
                    "construction_status": "graphed",
                    "card_ids": ["p7card_TEST-S01_001"],
                    "reason": "成图",
                }
            ],
            {"prop_001": prop},
        )
        self.assertEqual(graphed[0]["decision"], "p7c_card")
        self.assertEqual(
            VALIDATOR.validate_coverage_audit(
                {"section_id": "TEST-S01", "coverage_audit": graphed, "cards": [card()]},
                [card()],
                {"u1"},
                "TEST-S01",
            ),
            [],
        )
        ungraphable = RUNNER._merge_coverage_audit(
            [{"candidate_id": "prop_001", "decision": "p7c_candidate", "reason": "增量"}],
            [
                {
                    "candidate_id": "prop_001",
                    "construction_status": "ungraphable",
                    "card_ids": [],
                    "reason": "方向不确定",
                }
            ],
            {"prop_001": prop},
        )
        self.assertEqual(ungraphable[0]["decision"], "p7c_ungraphable")
        self.assertEqual(
            VALIDATOR.validate_coverage_audit(
                {"section_id": "TEST-S01", "coverage_audit": ungraphable, "cards": []},
                [],
                {"u1"},
                "TEST-S01",
            ),
            [],
        )

    def test_three_stage_normalization_removes_edge_review_hints(self) -> None:
        payload = {"cards": [card()]}
        payload["cards"][0]["flow_edges"][0].update(
            {"derivation": "llm_inference", "evidence_strength": "functional_dependency", "review_status": "accepted"}
        )
        RUNNER.normalize_three_stage_candidate_payload(payload)
        edge = payload["cards"][0]["flow_edges"][0]
        self.assertNotIn("derivation", edge)
        self.assertNotIn("evidence_strength", edge)
        self.assertNotIn("review_status", edge)

    def test_pipeline_summary_reads_actual_p7d_edge_counts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            p7c = root / "p7c"
            p7d = root / "p7d"
            section = p7c / "TEST-S01"
            section.mkdir(parents=True)
            p7d.mkdir()
            (section / "boundary_decisions.json").write_text(
                json.dumps({"boundary_decisions": [{"candidate_id": "prop_001", "decision": "p7c_candidate"}]}),
                encoding="utf-8",
            )
            (section / "construction_audit.json").write_text(
                json.dumps(
                    {
                        "construction_audit": [
                            {
                                "candidate_id": "prop_001",
                                "construction_status": "graphed",
                                "card_ids": ["p7card_TEST-S01_001"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (section / "cards.raw.json").write_text(json.dumps({"cards": [card()]}), encoding="utf-8")
            (p7d / "p7d_edge_reviews.jsonl").write_text("", encoding="utf-8")
            (p7d / "p7d_review_manifest.jsonl").write_text(
                json.dumps(
                    {
                        "card_id": "p7card_TEST-S01_001",
                        "edge_counts": {"accepted": 1, "pending": 0, "rejected": 0},
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            output = root / "summary.jsonl"
            SUMMARIZER.summarize(p7c, p7d, output)
            row = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(row["pipeline_status"], "ready")
            self.assertEqual(row["stages"]["P7D"]["accepted"], 1)


if __name__ == "__main__":
    unittest.main()
