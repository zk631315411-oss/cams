from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


TEST_FILE = Path(__file__).resolve()
PHASE_DIR = next(
    parent
    for parent in TEST_FILE.parents
    if (parent / "scripts" / "run_p7c_batch_ds.py").exists()
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load_module("p7c_s2_projection_runner", PHASE_DIR / "scripts" / "run_p7c_batch_ds.py")
AB_RUNNER = load_module("p7c_s2_ab_runner", PHASE_DIR / "scripts" / "run_s2_boundary_ab.py")
P7C_PROMPTS = PHASE_DIR / "phases" / "P7C" / "prompts"
CH07_TASK_PATH = PHASE_DIR / "phases" / "P7B" / "section_packages" / "CH07-S03" / "task.json"


def proposition(candidate_id: str = "candidate_001") -> dict:
    return {
        "candidate_id": candidate_id,
        "unit_ids": ["v7u_N000554"],
        "proposition": "若银行怀疑还贷资金非法，则不应接受。",
        "relation_cues": ["if", "should not"],
    }


def arm_score(decision: str = "p7c_candidate") -> dict:
    return {
        "status": "ok",
        "correct": 1,
        "wrong_kg_only": 0,
        "wrong_p7c_candidate": 0,
        "wrong_kg_only_ids": [],
        "wrong_p7c_candidate_ids": [],
        "missing_decisions": [],
        "actual": {"candidate_001": decision},
    }


class S2KgProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.task = json.loads(CH07_TASK_PATH.read_text(encoding="utf-8"))

    def test_projection_retains_all_units_in_original_order(self) -> None:
        projection = RUNNER.build_kg_projection(self.task)
        original_ids = [row["unit_id"] for row in self.task["units"]]
        projected_ids = [row["unit_id"] for row in projection["units"]]
        assigned_ids = {
            edge["target_id"]
            for edge in self.task["core_point_unit_edges"]
            if isinstance(edge, dict) and edge.get("target_id")
        }
        unassigned_ids = set(original_ids) - assigned_ids

        self.assertTrue(unassigned_ids, "fixture must contain units not assigned to a CP")
        self.assertEqual(projected_ids, original_ids)
        self.assertTrue(unassigned_ids.issubset(projected_ids))

    def test_projection_filters_exact_fields_and_preserves_row_order(self) -> None:
        projection = RUNNER.build_kg_projection(self.task)
        contracts = {
            "units": ("unit_id", "type"),
            "core_points": ("core_point_id", "title_zh", "title_en"),
            "core_point_unit_edges": ("source_id", "target_id", "relation_type"),
            "same_section_core_point_edges": ("source_id", "target_id", "relation_type"),
        }
        for collection, fields in contracts.items():
            expected = [
                {field: row.get(field) for field in fields}
                for row in self.task.get(collection, [])
                if isinstance(row, dict)
            ]
            self.assertEqual(projection[collection], expected)
            for row in projection[collection]:
                self.assertEqual(tuple(row), fields)
        self.assertEqual(projection["kg_capability_profile"], "base_kg_atomic_cp_v1")

    def test_build_s2_prompt_rejects_unknown_input_version(self) -> None:
        template = (P7C_PROMPTS / "kg_boundary_adjudication_v1.md").read_text(
            encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "Unsupported S2 KG input version"):
            RUNNER.build_s2_prompt(
                template,
                self.task,
                [proposition()],
                kg_input_version="future_version",
            )

    def test_v1_and_v2_prompts_render_without_placeholders(self) -> None:
        cases = (
            ("kg_boundary_adjudication_v1.md", "summary_v1", "base_kg_section_summary"),
            ("kg_boundary_adjudication_v2.md", "projection_v1", "kg_projection"),
        )
        for prompt_file, version, expected_marker in cases:
            with self.subTest(version=version):
                template = (P7C_PROMPTS / prompt_file).read_text(encoding="utf-8")
                rendered = RUNNER.build_s2_prompt(
                    template,
                    self.task,
                    [proposition()],
                    kg_input_version=version,
                )
                self.assertEqual(rendered.count("## 当前section"), 1)
                self.assertIn(expected_marker, rendered)
                self.assertIn("candidate_001", rendered)
                for placeholder in (
                    "<BASE_KG_SUMMARY_JSON>",
                    "<KG_PROJECTION_JSON>",
                    "<SECTION_TEXT>",
                    "<ALLOWED_UNIT_IDS>",
                    "<S1_PROPOSITIONS_JSON>",
                ):
                    self.assertNotIn(placeholder, rendered)

    def test_v2_prompt_defines_relation_priority_and_strict_s2_scope(self) -> None:
        prompt = (P7C_PROMPTS / "kg_boundary_adjudication_v2.md").read_text(
            encoding="utf-8"
        )
        for required_text in (
            "唯一职责",
            "不得新增、删除、合并或改写 S1 候选",
            "一条或多条核心关系",
            "拆成不可再分的关系逐条独立裁决",
            "先拆分为不可再分的关系并逐条用 2.1 定义判断",
            "单个 unit、关系较短、没有独立出口",
            "被认定、被识别、被归类",
            "一般结果不是程序步骤",
            "若全部关系均不满足 2.1 定义，直接判为 kg_only",
            "kg_projection 是判断 KG 结构覆盖的唯一依据",
            "任意一条核心关系属于 P7",
            "只输出严格 JSON",
        ):
            self.assertIn(required_text, prompt)
        self.assertNotIn("以下通常不是 P7 关系", prompt)
        self.assertNotIn("将适用阈值从 25% 调整", prompt)
        self.assertNotIn("据此采取风险控制", prompt)


class S2AbContractTests(unittest.TestCase):
    def test_nonempty_output_directory_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "existing_run"
            output_dir.mkdir()
            (output_dir / "evaluation.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be empty"):
                AB_RUNNER.prepare_output_dir(output_dir)

    def test_expected_and_frozen_candidate_mismatch_is_rejected(self) -> None:
        cases = {
            "TEST-S01": {
                "split": "development",
                "decisions": {"candidate_001": "p7c_candidate"},
            }
        }
        errors = AB_RUNNER.validate_preflight(
            cases,
            {"TEST-S01": [proposition("different_candidate")]},
        )
        self.assertTrue(any("expected IDs do not match frozen S1" in error for error in errors))

    def test_conflicting_frozen_s1_artifacts_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            runs = [root / "run_a", root / "run_b"]
            for run, text in zip(runs, ("first", "second"), strict=True):
                section_dir = run / "TEST-S01"
                section_dir.mkdir(parents=True)
                payload = {
                    "section_id": "TEST-S01",
                    "propositions": [
                        {"candidate_id": "candidate_001", "proposition": text}
                    ],
                }
                (section_dir / "s1_propositions.json").write_text(
                    json.dumps(payload, ensure_ascii=False),
                    encoding="utf-8",
                )

            with self.assertRaisesRegex(ValueError, "conflicting frozen S1 artifacts"):
                AB_RUNNER.load_s1_propositions(
                    [str(run) for run in runs],
                    {"TEST-S01"},
                )

    def test_unknown_candidate_and_section_mismatch_are_rejected(self) -> None:
        payload = {
            "section_id": "WRONG-S01",
            "boundary_decisions": [
                {
                    "candidate_id": "unknown_candidate",
                    "decision": "kg_only",
                    "reason": "测试",
                }
            ],
        }
        errors = AB_RUNNER.validate_arm_payload(
            payload,
            [proposition()],
            "TEST-S01",
        )
        self.assertIn("S2 section_id mismatch", errors)
        self.assertTrue(any("unknown candidate IDs" in error for error in errors))

    def test_missing_decision_cannot_score_as_passing(self) -> None:
        score = AB_RUNNER.score_arm(
            {"status": "ok", "boundary_decisions": []},
            {"candidate_001": "p7c_candidate"},
        )
        self.assertEqual(score["status"], "contract_error")
        self.assertEqual(score["correct"], 0)
        self.assertEqual(score["missing_decisions"], ["candidate_001"])

    def test_failed_arm_makes_experiment_inconclusive(self) -> None:
        failed = dict(arm_score())
        failed["status"] = "failed"
        comparison = {
            "section_id": "TEST-S01",
            "split": "development",
            "A_summary_v1": failed,
            "B_projection_v1": arm_score(),
            "regressions": [],
        }
        evaluation = AB_RUNNER.evaluate([comparison], required_holdout_sections=0)
        self.assertEqual(evaluation["verdict"], "inconclusive")
        self.assertTrue(evaluation["primary_results"]["arm_failures"])

    def test_development_only_evaluation_is_inconclusive(self) -> None:
        comparison = {
            "section_id": "TEST-S01",
            "split": "development",
            "A_summary_v1": arm_score(),
            "B_projection_v1": arm_score(),
            "regressions": [],
        }
        evaluation = AB_RUNNER.evaluate([comparison], required_holdout_sections=3)
        self.assertEqual(evaluation["verdict"], "inconclusive")
        self.assertFalse(evaluation["holdout_result"]["passed"])


if __name__ == "__main__":
    unittest.main()
