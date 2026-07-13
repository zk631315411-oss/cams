from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


TEST_FILE = Path(__file__).resolve()
PHASE_DIR = next(parent for parent in TEST_FILE.parents if (parent / "scripts" / "run_p7c_batch_ds.py").exists())
RUNNER_PATH = PHASE_DIR / "scripts" / "run_p7c_batch_ds.py"
SPEC = importlib.util.spec_from_file_location("run_p7c_batch_ds", RUNNER_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def payload(include_node_categories: bool) -> dict:
    nodes = [
        {
            "node_id": "e",
            "node_type": "E1_event_signal",
            "label": "事件",
            "evidence_unit_ids": ["u1"],
            "evidence_strength": "explicit",
        },
        {
            "node_id": "p",
            "node_type": "P2_execution",
            "label": "机构：处理",
            "evidence_unit_ids": ["u1"],
            "evidence_strength": "explicit",
        },
        {
            "node_id": "x",
            "node_type": "X3_state_change",
            "label": "结果",
            "evidence_unit_ids": ["u1"],
            "evidence_strength": "explicit",
        },
    ]
    if include_node_categories:
        for node, category in zip(nodes, ("entry", "process", "exit"), strict=True):
            node["node_category"] = category
    card = {
        "card_id": "p7card_TEST-S01_001",
        "section_id": "TEST-S01",
        "card_nature": "execution",
        "title": "测试卡",
        "flow_nodes": nodes,
        "flow_edges": [
            {
                "edge_id": "ep",
                "edge_type": "PRECEDES",
                "source": "e",
                "target": "p",
                "evidence_unit_ids": ["u1"],
                "evidence_strength": "explicit",
            },
            {
                "edge_id": "px",
                "edge_type": "PRODUCES",
                "source": "p",
                "target": "x",
                "evidence_unit_ids": ["u1"],
                "evidence_strength": "explicit",
            },
        ],
        "source_unit_ids": ["u1"],
        "review_status": "accepted",
        "review_notes": "增量命题：事件导向处理和结果；KG不足：不能表达方向；选项判断：可判断顺序；LLM推理：无。",
    }
    return {
        "section_id": "TEST-S01",
        "section_title": "测试",
        "coverage_audit": [
            {
                "candidate_id": "cand_001",
                "unit_ids": ["u1"],
                "proposition": "事件导向处理和结果",
                "decision": "p7c_card",
                "card_id": card["card_id"],
                "reason": "基础KG不能表达方向。",
            }
        ],
        "cards": [card],
        "skip_reason": None,
    }


def coverage_promotion_payloads() -> tuple[dict, dict]:
    card_payload = payload(True)
    card = card_payload["cards"][0]
    original = {
        "section_id": "TEST-S01",
        "section_title": "测试",
        "coverage_audit": [
            {
                "candidate_id": "cand_kg_001",
                "unit_ids": ["u1"],
                "proposition": "事件导向处理和结果",
                "decision": "kg_only",
                "card_id": None,
                "reason": "首次判断交给KG。",
            }
        ],
        "cards": [],
        "skip_reason": "首次抽取未成卡。",
    }
    adjudication_patch = {
        "section_id": "TEST-S01",
        "coverage_adjudication": [
            {
                "candidate_id": "cand_kg_001",
                "original_decision": "kg_only",
                "final_decision": "p7c_card",
                "card_id": card["card_id"],
                "reason": "基础KG不能表达内部有向关系。",
            }
        ],
        "promoted_cards": [card],
    }
    return original, adjudication_patch


class RunnerValidationRepairTests(unittest.TestCase):
    def test_initial_parse_failure_is_retried(self) -> None:
        valid_response = json.dumps(payload(True), ensure_ascii=False)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packages_dir = root / "packages"
            package_dir = packages_dir / "TEST-S01"
            package_dir.mkdir(parents=True)
            (package_dir / "task.json").write_text(
                json.dumps(
                    {
                        "section_id": "TEST-S01",
                        "section_title": "测试",
                        "units": [{"unit_id": "u1"}],
                        "section_text_with_unit_anchors": "[u1|1] test",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            def fake_validate(cards_path: Path, report_path: Path, section_package_path: Path):
                report_path.write_text("error_count: 0\n", encoding="utf-8")
                return 0, "errors=0", 0

            with (
                patch.object(
                    RUNNER,
                    "call_model",
                    side_effect=[("", {"attempt": 0}), (valid_response, {"attempt": 1})],
                ) as call_model,
                patch.object(RUNNER, "validate_cards", side_effect=fake_validate),
            ):
                manifest = RUNNER.run_section(
                    section_id="TEST-S01",
                    run_dir=root / "run",
                    packages_dir=packages_dir,
                    prompt_template="# test prompt",
                    model="test-model",
                    thinking_effort="none",
                    max_tokens=1000,
                    timeout=10,
                    retries=1,
                    retry_delay=0,
                    validation_retries=0,
                )

            self.assertEqual(call_model.call_count, 2)
            self.assertEqual(manifest["status"], "ok")
            self.assertEqual(manifest["call_attempts"][0]["status"], "parse_failed")
            self.assertEqual(manifest["call_attempts"][1]["status"], "ok")

    def test_validation_failure_is_repaired_once(self) -> None:
        invalid_response = json.dumps(payload(False), ensure_ascii=False)
        valid_response = json.dumps(payload(True), ensure_ascii=False)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packages_dir = root / "packages"
            package_dir = packages_dir / "TEST-S01"
            package_dir.mkdir(parents=True)
            (package_dir / "task.json").write_text(
                json.dumps(
                    {
                        "section_id": "TEST-S01",
                        "section_title": "测试",
                        "units": [{"unit_id": "u1"}],
                        "section_text_with_unit_anchors": "[u1|1] test",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            def fake_validate(cards_path: Path, report_path: Path, section_package_path: Path):
                current = json.loads(cards_path.read_text(encoding="utf-8"))
                missing = sum(
                    1
                    for card in current["cards"]
                    for node in card["flow_nodes"]
                    if "node_category" not in node
                )
                report_path.write_text(f"error_count: {missing}\n", encoding="utf-8")
                return 0, f"errors={missing}", missing

            with (
                patch.object(
                    RUNNER,
                    "call_model",
                    side_effect=[(invalid_response, {"attempt": 0}), (valid_response, {"attempt": 1})],
                ) as call_model,
                patch.object(RUNNER, "validate_cards", side_effect=fake_validate),
            ):
                manifest = RUNNER.run_section(
                    section_id="TEST-S01",
                    run_dir=root / "run",
                    packages_dir=packages_dir,
                    prompt_template="# test prompt",
                    model="test-model",
                    thinking_effort="none",
                    max_tokens=1000,
                    timeout=10,
                    retries=0,
                    retry_delay=0,
                    validation_retries=1,
                )

            self.assertEqual(call_model.call_count, 2)
            self.assertEqual(manifest["status"], "ok")
            self.assertEqual(manifest["validation_error_count"], 0)
            self.assertEqual(len(manifest["validation_attempts"]), 2)
            self.assertTrue((root / "run" / "TEST-S01" / "raw_response.initial.txt").exists())
            final_payload = json.loads((root / "run" / "TEST-S01" / "cards.raw.json").read_text(encoding="utf-8"))
            self.assertEqual(final_payload["cards"][0]["flow_nodes"][0]["node_category"], "entry")

    def test_coverage_adjudication_promotes_kg_candidate(self) -> None:
        original, adjudication_patch = coverage_promotion_payloads()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packages_dir = root / "packages"
            package_dir = packages_dir / "TEST-S01"
            package_dir.mkdir(parents=True)
            (package_dir / "task.json").write_text(
                json.dumps(
                    {
                        "section_id": "TEST-S01",
                        "section_title": "测试",
                        "units": [{"unit_id": "u1"}],
                        "section_text_with_unit_anchors": "[u1|1] test",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            def fake_validate(cards_path: Path, report_path: Path, section_package_path: Path):
                report_path.write_text("error_count: 0\n", encoding="utf-8")
                return 0, "errors=0", 0

            with (
                patch.object(
                    RUNNER,
                    "call_model",
                    side_effect=[
                        (json.dumps(original, ensure_ascii=False), {"attempt": 0}),
                        (json.dumps(adjudication_patch, ensure_ascii=False), {"attempt": 1}),
                    ],
                ) as call_model,
                patch.object(RUNNER, "validate_cards", side_effect=fake_validate),
            ):
                manifest = RUNNER.run_section(
                    section_id="TEST-S01",
                    run_dir=root / "run",
                    packages_dir=packages_dir,
                    prompt_template="# extraction prompt",
                    model="test-model",
                    thinking_effort="none",
                    max_tokens=1000,
                    timeout=10,
                    retries=0,
                    retry_delay=0,
                    validation_retries=1,
                    coverage_adjudication=True,
                    coverage_adjudication_prompt_template="# adjudication prompt",
                )

            self.assertEqual(call_model.call_count, 2)
            self.assertEqual(manifest["status"], "ok")
            self.assertEqual(manifest["coverage_adjudication_status"], "accepted")
            self.assertEqual(manifest["coverage_adjudication_promoted_card_count"], 1)
            final_payload = json.loads((root / "run" / "TEST-S01" / "cards.raw.json").read_text(encoding="utf-8"))
            self.assertEqual(len(final_payload["cards"]), 1)

    def test_coverage_adjudication_validation_failure_is_repaired(self) -> None:
        original, adjudication_patch = coverage_promotion_payloads()
        invalid_adjudication = copy.deepcopy(adjudication_patch)
        invalid_adjudication["promoted_cards"][0]["flow_edges"][0]["relation_type"] = "invented_relation"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packages_dir = root / "packages"
            package_dir = packages_dir / "TEST-S01"
            package_dir.mkdir(parents=True)
            (package_dir / "task.json").write_text(
                json.dumps(
                    {
                        "section_id": "TEST-S01",
                        "section_title": "测试",
                        "units": [{"unit_id": "u1"}],
                        "section_text_with_unit_anchors": "[u1|1] test",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            def fake_validate(cards_path: Path, report_path: Path, section_package_path: Path):
                current = json.loads(cards_path.read_text(encoding="utf-8"))
                invalid_fields = sum(
                    1
                    for card in current.get("cards") or []
                    for edge in card.get("flow_edges") or []
                    if edge.get("relation_type") not in {None, ""}
                )
                report_path.write_text(f"error_count: {invalid_fields}\n", encoding="utf-8")
                return 0, f"errors={invalid_fields}", invalid_fields

            with (
                patch.object(
                    RUNNER,
                    "call_model",
                    side_effect=[
                        (json.dumps(original, ensure_ascii=False), {"attempt": 0}),
                        (json.dumps(invalid_adjudication, ensure_ascii=False), {"attempt": 1}),
                        (json.dumps(adjudication_patch, ensure_ascii=False), {"attempt": 2}),
                    ],
                ) as call_model,
                patch.object(RUNNER, "validate_cards", side_effect=fake_validate),
            ):
                manifest = RUNNER.run_section(
                    section_id="TEST-S01",
                    run_dir=root / "run",
                    packages_dir=packages_dir,
                    prompt_template="# extraction prompt",
                    model="test-model",
                    thinking_effort="none",
                    max_tokens=1000,
                    timeout=10,
                    retries=0,
                    retry_delay=0,
                    validation_retries=1,
                    coverage_adjudication=True,
                    coverage_adjudication_prompt_template="# adjudication prompt",
                )

            self.assertEqual(call_model.call_count, 3)
            self.assertEqual(manifest["status"], "ok")
            self.assertEqual(manifest["coverage_adjudication_status"], "accepted")
            self.assertEqual(len(manifest["coverage_adjudication_validation_attempts"]), 2)
            self.assertEqual(
                manifest["coverage_adjudication_validation_attempts"][1]["status"],
                "ok",
            )


class CoverageAdjudicationContractTests(unittest.TestCase):
    def test_base_kg_summary_is_compact_and_has_no_internal_cp_fields(self) -> None:
        summary = RUNNER.build_base_kg_section_summary(
            {
                "units": [{"unit_id": "u1", "type": "fact"}],
                "core_points": [
                    {
                        "core_point_id": "cp1",
                        "title_zh": "主题一",
                        "title_en": "Topic one",
                        "anchor_unit_ids": ["u1"],
                        "key_unit_ids": ["u1"],
                        "support_unit_ids": [],
                    },
                    {
                        "core_point_id": "cp2",
                        "title_zh": "主题二",
                        "title_en": "Topic two",
                        "anchor_unit_ids": [],
                        "key_unit_ids": [],
                        "support_unit_ids": [],
                    },
                ],
                "core_point_unit_edges": [
                    {"source_id": "cp1", "target_id": "u1", "relation_type": "fact"}
                ],
                "same_section_core_point_edges": [
                    {
                        "source_id": "cp1",
                        "target_id": "cp2",
                        "relation_type": "contains",
                        "reason": "不应发送给LLM的内部关系解释",
                    }
                ],
            }
        )
        encoded = json.dumps(summary, ensure_ascii=False)
        self.assertIn("covered_topics", summary)
        self.assertIn("covered_relations", summary)
        self.assertNotIn("core_point_id", encoded)
        self.assertNotIn("anchor_unit_ids", encoded)
        self.assertNotIn("key_unit_ids", encoded)
        self.assertNotIn("support_unit_ids", encoded)
        self.assertNotIn("不应发送给LLM", encoded)

    def test_coverage_prompt_repeats_full_context_and_focuses_review_targets(self) -> None:
        original, _ = coverage_promotion_payloads()
        task = {
            "section_id": "TEST-S01",
            "section_title": "测试",
            "units": [{"unit_id": "u1"}],
            "section_text_with_unit_anchors": "[u1|1] 完整section原文",
        }
        prompt = RUNNER.build_coverage_adjudication_prompt("# coverage", task, original)
        self.assertIn("完整section原文", prompt)
        self.assertIn('"candidate_id": "cand_kg_001"', prompt)
        self.assertIn("review_target_candidate_ids", prompt)
        self.assertIn('"cand_kg_001"', prompt)

    def test_valid_promotion_passes_contract(self) -> None:
        original, adjudication_patch = coverage_promotion_payloads()
        self.assertEqual(RUNNER.validate_coverage_adjudication(original, adjudication_patch), [])

    def test_existing_card_cannot_be_changed(self) -> None:
        original, adjudication_patch = coverage_promotion_payloads()
        adjudication_patch["cards"] = [{"card_id": "attempted_rewrite"}]
        errors = RUNNER.validate_coverage_adjudication(original, adjudication_patch)
        self.assertTrue(any("unsupported fields" in error for error in errors), errors)

    def test_promoted_card_cannot_use_out_of_candidate_evidence(self) -> None:
        original, adjudication_patch = coverage_promotion_payloads()
        adjudication_patch["promoted_cards"][0]["flow_edges"][0]["evidence_unit_ids"].append("u2")
        errors = RUNNER.validate_coverage_adjudication(original, adjudication_patch)
        self.assertTrue(any("uses evidence outside promoted candidate" in error for error in errors), errors)

    def test_two_candidates_cannot_share_one_promoted_card_id(self) -> None:
        original, adjudication_patch = coverage_promotion_payloads()
        second_candidate = copy.deepcopy(original["coverage_audit"][0])
        second_candidate["candidate_id"] = "cand_kg_002"
        original["coverage_audit"].append(second_candidate)
        second_row = copy.deepcopy(adjudication_patch["coverage_adjudication"][0])
        second_row["candidate_id"] = "cand_kg_002"
        adjudication_patch["coverage_adjudication"].append(second_row)
        errors = RUNNER.validate_coverage_adjudication(original, adjudication_patch)
        self.assertTrue(any("assigned card_id" in error for error in errors), errors)

    def test_new_card_derived_fields_are_normalized(self) -> None:
        original, adjudication_patch = coverage_promotion_payloads()
        merged = RUNNER.merge_coverage_adjudication_patch(original, adjudication_patch)
        new_card = merged["cards"][0]
        new_card["review_status"] = "approved"
        del new_card["flow_nodes"][0]["node_category"]
        changes = RUNNER.normalize_new_adjudicated_cards(original, merged)
        self.assertEqual(new_card["candidate_status"], "candidate")
        self.assertNotIn("review_status", new_card)
        self.assertEqual(new_card["flow_nodes"][0]["node_category"], "entry")
        self.assertTrue(all(edge.get("derivation") == "explicit_text" for edge in new_card["flow_edges"]))
        self.assertIn("candidate_status", {change["field"] for change in changes})

    def test_patch_merge_preserves_original_and_updates_only_reviewed_candidates(self) -> None:
        original, adjudication_patch = coverage_promotion_payloads()
        before = copy.deepcopy(original)
        merged = RUNNER.merge_coverage_adjudication_patch(original, adjudication_patch)
        self.assertEqual(original, before)
        self.assertEqual(merged["coverage_audit"][0]["decision"], "p7c_card")
        self.assertEqual(merged["coverage_audit"][0]["card_id"], "p7card_TEST-S01_001")
        self.assertEqual(len(merged["cards"]), 1)
        self.assertIsNone(merged["skip_reason"])


if __name__ == "__main__":
    unittest.main()
