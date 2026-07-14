from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


TEST_FILE = Path(__file__).resolve()
PHASE_DIR = next(parent for parent in TEST_FILE.parents if (parent / "scripts" / "run_p7d_edge_review_ds.py").exists())
SCRIPTS_DIR = PHASE_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load_module("p7d_edge_review_runner", SCRIPTS_DIR / "run_p7d_edge_review_ds.py")
HUMAN = load_module("p7d_human_decisions", SCRIPTS_DIR / "apply_p7d_human_decisions.py")
VALIDATOR = load_module("p7d_structure_for_runner", SCRIPTS_DIR / "validate_and_route_cards.py")
SCHEMA = VALIDATOR.read_json(PHASE_DIR / "inputs" / "procedural_schema_v2.json")
REVIEW_SCHEMA = VALIDATOR.read_json(PHASE_DIR / "phases" / "P7D" / "inputs" / "p7d_edge_review_schema_v1.json")


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


def check(status: str = "supported") -> dict:
    return {"status": status, "reason": "测试依据。"}


def payload(*, first_derivation: str = "explicit_text", first_direction: str = "supported", omit_last: bool = False) -> dict:
    reviews = []
    for edge_id in ("edge_1", "edge_2"):
        direction = first_direction if edge_id == "edge_1" else "supported"
        recommendation = "rejected" if direction == "unsupported" else "accepted"
        reviews.append(
            {
                "edge_id": edge_id,
                "derivation": first_derivation if edge_id == "edge_1" else "explicit_text",
                "llm_recommendation": recommendation,
                "checks": {
                    "source_node_support": check(),
                    "target_node_support": check(),
                    "direction_support": check(direction),
                    "condition_support": check("not_applicable"),
                    "qualifier_support": check("not_applicable"),
                    "parallel_or_correlation_check": check(),
                },
                "evidence_unit_ids": ["u1"],
                "source_quotes": ["事件后机构执行动作并形成结果。"],
                "reason": "逐边审核测试。",
            }
        )
    if omit_last:
        reviews.pop()
    return {"section_id": "TEST-S01", "card_id": "p7card_TEST-S01_001", "edge_reviews": reviews}


def run_with_payload(candidate: dict, response: dict) -> dict:
    structure = VALIDATOR.validate_card_structure(candidate, package(), SCHEMA)

    def fake_call(prompt: str, model: str, max_tokens: int, timeout: float, thinking_effort: str):
        return json.dumps(response, ensure_ascii=False), {"model": model, "elapsed_seconds": 0}

    with tempfile.TemporaryDirectory() as temp_dir:
        return RUNNER.review_card(
            run_id="test_run",
            card=candidate,
            package=package(),
            structure=structure,
            prompt_template="<section_id>\n<SECTION_TEXT>\n<P7C_CARD>\n<SECTION_UNITS>\n<ALLOWED_UNIT_IDS>",
            review_schema=REVIEW_SCHEMA,
            model="fake-model",
            thinking_effort="none",
            max_tokens=1000,
            timeout=1,
            retries=0,
            retry_delay=0,
            artifact_dir=Path(temp_dir),
            call_model_fn=fake_call,
        )


class P7DEdgeReviewRunnerTests(unittest.TestCase):
    def test_llm_prompt_keeps_full_section_and_strips_internal_review_hints(self) -> None:
        candidate = card()
        candidate["candidate_status"] = "candidate"
        candidate["review_notes"] = "不应发送给审核LLM"
        candidate["flow_edges"][0]["derivation"] = "llm_inference"
        candidate["flow_edges"][0]["source_quote"] = "候选提取器预选引文"
        before = copy.deepcopy(candidate)
        prompt = RUNNER.build_prompt(
            "<SECTION_TEXT>\n<SECTION_UNITS>\n<ALLOWED_UNIT_IDS>\n<P7C_CARD>",
            candidate,
            package(),
        )
        self.assertIn("事件后机构执行动作并形成结果", prompt)
        self.assertIn('"edge_id": "edge_1"', prompt)
        self.assertNotIn("en_quote", prompt)
        self.assertNotIn("candidate_status", prompt)
        self.assertNotIn("review_notes", prompt)
        self.assertNotIn("evidence_strength", prompt)
        self.assertNotIn("review_status", prompt)
        self.assertNotIn("llm_inference", prompt)
        self.assertNotIn("候选提取器预选引文", prompt)
        self.assertEqual(candidate, before)

    def test_explicit_supported_edges_are_answer_eligible(self) -> None:
        result = run_with_payload(card(), payload())
        self.assertEqual([row["review_status"] for row in result["edge_reviews"]], ["accepted", "accepted"])
        self.assertEqual(result["card_manifest"]["card_result"], "pass")
        self.assertTrue(all(row["answer_eligible"] for row in result["edge_reviews"]))

    def test_legacy_declared_inference_is_audit_only(self) -> None:
        candidate = card()
        candidate["flow_edges"][0]["evidence_strength"] = "functional_dependency"
        result = run_with_payload(candidate, payload())
        self.assertEqual(result["edge_reviews"][0]["declared_derivation"], "llm_inference")
        self.assertEqual(result["edge_reviews"][0]["derivation"], "explicit_text")
        self.assertEqual(result["edge_reviews"][0]["review_status"], "accepted")
        self.assertTrue(result["edge_reviews"][0]["answer_eligible"])

    def test_current_p7c_derivation_is_audit_only(self) -> None:
        candidate = card()
        candidate["flow_edges"][0].pop("evidence_strength")
        candidate["flow_edges"][0]["derivation"] = "llm_inference"
        result = run_with_payload(candidate, payload())
        self.assertEqual(result["edge_reviews"][0]["declared_derivation"], "llm_inference")
        self.assertEqual(result["edge_reviews"][0]["review_status"], "accepted")

    def test_missing_p7c_derivation_is_null_and_p7d_inference_is_pending(self) -> None:
        candidate = card()
        for edge in candidate["flow_edges"]:
            edge.pop("evidence_strength", None)
            edge.pop("derivation", None)
        result = run_with_payload(candidate, payload(first_derivation="llm_inference"))
        self.assertIsNone(result["edge_reviews"][0]["declared_derivation"])
        self.assertEqual(result["edge_reviews"][0]["review_status"], "pending")

    def test_unsupported_direction_rejects_edge(self) -> None:
        result = run_with_payload(card(), payload(first_direction="unsupported"))
        self.assertEqual(result["edge_reviews"][0]["review_status"], "rejected")
        self.assertFalse(result["edge_reviews"][0]["retrieval_eligible"])

    def test_incomplete_llm_contract_keeps_all_edges_pending(self) -> None:
        result = run_with_payload(card(), payload(omit_last=True))
        self.assertEqual(result["card_manifest"]["review_execution_status"], "review_failed")
        self.assertTrue(all(row["review_status"] == "pending" for row in result["edge_reviews"]))

    def test_runner_does_not_mutate_p7c_card(self) -> None:
        candidate = card()
        before = copy.deepcopy(candidate)
        run_with_payload(candidate, payload())
        self.assertEqual(candidate, before)

    def test_human_decision_appends_history_and_can_complete_card(self) -> None:
        candidate = card()
        result = run_with_payload(candidate, payload(first_derivation="llm_inference"))
        decisions = [{"section_id": "TEST-S01", "card_id": candidate["card_id"], "edge_id": "edge_1", "decision": "accepted", "decided_by": "reviewer", "reason": "人工确认方向成立。"}]
        reviews, history = HUMAN.apply_decisions(result["edge_reviews"], list(result["history"]), decisions, "human_run")
        manifests = HUMAN.rebuild_card_manifests([result["card_manifest"]], reviews, "human_run")
        self.assertEqual(reviews[0]["review_status"], "accepted")
        self.assertEqual(len(reviews[0]["review_history"]), 2)
        self.assertEqual(history[-1]["actor_type"], "human")
        self.assertEqual(manifests[0]["card_result"], "pass")


if __name__ == "__main__":
    unittest.main()
