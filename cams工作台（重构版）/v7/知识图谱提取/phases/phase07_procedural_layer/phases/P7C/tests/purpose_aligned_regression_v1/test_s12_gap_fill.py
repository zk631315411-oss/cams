from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


TEST_FILE = Path(__file__).resolve()
PHASE_DIR = next(parent for parent in TEST_FILE.parents if (parent / "scripts" / "run_p7c_batch_ds.py").exists())
RUNNER_PATH = PHASE_DIR / "scripts" / "run_p7c_batch_ds.py"
PROMPTS_DIR = PHASE_DIR / "phases" / "P7C" / "prompts"


def load_runner():
    spec = importlib.util.spec_from_file_location("p7c_s12_runner", RUNNER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load_runner()


def task() -> dict:
    return {
        "section_id": "TEST-S01",
        "section_title": "测试",
        "section_text_with_unit_anchors": (
            "[u1|1] 当事件发生时，机构执行初步调查。\n\n"
            "[u2|2] 初步调查发现高风险安排。"
        ),
        "units": [
            {"unit_id": "u1", "en_quote": "当事件发生时，机构执行初步调查。"},
            {"unit_id": "u2", "en_quote": "初步调查发现高风险安排。"},
        ],
        "core_points": [],
    }


def candidate(candidate_id: str = "s1c_001", *, gap: bool = False) -> dict:
    result = {
        "candidate_id": candidate_id,
        "unit_ids": ["u1" if not gap else "u2"],
        "proposition": "事件发生时机构执行初步调查。" if not gap else "初步调查发现高风险安排。",
        "source_quotes": ["当事件发生时" if not gap else "初步调查发现高风险安排"],
        "relation_cues": ["当" if not gap else "发现"],
        "candidate_frame": {
            "trigger_or_context": ["事件发生"] if not gap else [],
            "basis_or_condition": [],
            "focal_handling_or_judgment": "机构执行初步调查",
            "outcomes_or_paths": [] if not gap else ["发现高风险安排"],
        },
        "evidence_spans": [
            {
                "unit_id": "u1" if not gap else "u2",
                "quote": "当事件发生时" if not gap else "初步调查发现高风险安排",
            }
        ],
        "induction": None,
        "cross_unit_basis": None,
    }
    if gap:
        result["gap_evidence"] = {
            "compared_with_candidate_ids": ["s1c_001"],
            "gap_reason": "已有候选覆盖调查触发，但未覆盖调查得出的发现。",
        }
    return result


def write_task(packages_dir: Path) -> None:
    section_dir = packages_dir / "TEST-S01"
    section_dir.mkdir(parents=True)
    (section_dir / "task.json").write_text(json.dumps(task(), ensure_ascii=False), encoding="utf-8")


def run_s1_pair(run_dir: Path, packages_dir: Path, fake_call) -> dict:
    s1_template = (PROMPTS_DIR / "proposition_discovery_v1.md").read_text(encoding="utf-8")
    s12_template = (PROMPTS_DIR / "proposition_gap_fill_v1.md").read_text(encoding="utf-8")
    with patch.object(RUNNER, "call_model", side_effect=fake_call):
        return RUNNER.run_section_three_stage(
            "TEST-S01",
            run_dir,
            packages_dir,
            s1_template,
            "unused-s2",
            "unused-s3",
            "downstream-model",
            "none",
            4000,
            30.0,
            1,
            0.0,
            0,
            False,
            s12_template,
            "s11-model",
            "high",
            "s12-model",
            "none",
            True,
        )


class S12GapFillTests(unittest.TestCase):
    def test_rendered_prompt_is_self_contained_and_omits_internal_inputs(self) -> None:
        template = (PROMPTS_DIR / "proposition_gap_fill_v1.md").read_text(encoding="utf-8")
        rendered = RUNNER.build_s12_prompt(template, task(), [candidate()])

        self.assertEqual(rendered.count("## 当前section"), 1)
        self.assertIn(task()["section_text_with_unit_anchors"], rendered)
        self.assertIn("开放候选", rendered)
        self.assertIn("案例法律适用链", rendered)
        self.assertIn("调查发现链", rendered)
        self.assertIn("同中心判断链", rendered)
        self.assertNotIn("allowed_unit_ids:", rendered)
        self.assertNotIn("base_kg_section_summary:", rendered)
        self.assertNotIn("<SECTION_TEXT>", rendered)
        self.assertNotIn("<S11_PROPOSITIONS_JSON>", rendered)

    def test_valid_gap_passes_full_evidence_contract(self) -> None:
        errors = RUNNER.validate_s12_gap_payload(
            {"section_id": "TEST-S01", "gap_propositions": [candidate("s1c_gap_001", gap=True)]},
            "TEST-S01",
            {"u1", "u2"},
            {"u1": "当事件发生时，机构执行初步调查。", "u2": "初步调查发现高风险安排。"},
            [candidate()],
        )
        self.assertEqual(errors, [])

    def test_gap_contract_rejects_wrong_section_bad_prefix_and_unknown_comparison(self) -> None:
        gap = candidate("bad_id", gap=True)
        gap["gap_evidence"]["compared_with_candidate_ids"] = ["missing"]
        errors = RUNNER.validate_s12_gap_payload(
            {"section_id": "OTHER", "gap_propositions": [gap]},
            "TEST-S01",
            {"u1", "u2"},
            {"u1": "当事件发生时，机构执行初步调查。", "u2": "初步调查发现高风险安排。"},
            [candidate()],
        )
        self.assertTrue(any("section_id mismatch" in error for error in errors), errors)
        self.assertTrue(any("must start with s1c_gap_" in error for error in errors), errors)
        self.assertTrue(any("unknown S1.1 candidates" in error for error in errors), errors)

    def test_gap_contract_rejects_out_of_section_or_unlocatable_evidence(self) -> None:
        gap = candidate("s1c_gap_001", gap=True)
        gap["unit_ids"] = ["outside"]
        gap["evidence_spans"] = [{"unit_id": "outside", "quote": "不存在的引文"}]
        gap["source_quotes"] = ["不存在的引文"]
        errors = RUNNER.validate_s12_gap_payload(
            {"section_id": "TEST-S01", "gap_propositions": [gap]},
            "TEST-S01",
            {"u1", "u2"},
            {"u1": "当事件发生时，机构执行初步调查。", "u2": "初步调查发现高风险安排。"},
            [candidate()],
        )
        self.assertTrue(any("out-of-section evidence" in error for error in errors), errors)

    def test_s11_and_s12_use_independent_model_settings_and_write_merged_canonical_artifact(self) -> None:
        calls: list[tuple[str, str]] = []

        def fake_call(prompt, model, max_tokens, timeout, thinking_effort):
            calls.append((model, thinking_effort))
            if "P7C-S1.1" in prompt:
                payload = {
                    "section_id": "TEST-S01",
                    "section_title": "测试",
                    "propositions": [candidate()],
                    "skip_reason": None,
                }
            else:
                payload = {
                    "section_id": "TEST-S01",
                    "gap_propositions": [candidate("s1c_gap_001", gap=True)],
                }
            return json.dumps(payload, ensure_ascii=False), {
                "model": model,
                "thinking_effort": thinking_effort,
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packages_dir = root / "packages"
            run_dir = root / "run"
            write_task(packages_dir)
            manifest = run_s1_pair(run_dir, packages_dir, fake_call)

            self.assertEqual(manifest["status"], "ok")
            self.assertEqual(manifest["completed_through"], "s12")
            self.assertEqual(calls, [("s11-model", "high"), ("s12-model", "none")])
            section_dir = run_dir / "TEST-S01"
            s11 = json.loads((section_dir / "s11_propositions.json").read_text(encoding="utf-8"))
            merged = json.loads((section_dir / "s1_propositions.json").read_text(encoding="utf-8"))
            self.assertEqual(len(s11["propositions"]), 1)
            self.assertEqual([row["candidate_id"] for row in merged["propositions"]], ["s1c_001", "s1c_gap_001"])

    def test_s12_contract_failure_stops_section_without_fallback(self) -> None:
        def fake_call(prompt, model, max_tokens, timeout, thinking_effort):
            if "P7C-S1.1" in prompt:
                payload = {
                    "section_id": "TEST-S01",
                    "section_title": "测试",
                    "propositions": [candidate()],
                    "skip_reason": None,
                }
            else:
                payload = {"section_id": "OTHER", "gap_propositions": []}
            return json.dumps(payload, ensure_ascii=False), {
                "model": model,
                "thinking_effort": thinking_effort,
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packages_dir = root / "packages"
            run_dir = root / "run"
            write_task(packages_dir)
            manifest = run_s1_pair(run_dir, packages_dir, fake_call)

            self.assertEqual(manifest["status"], "s12_failed")
            self.assertFalse((run_dir / "TEST-S01" / "s1_propositions.json").exists())
            self.assertFalse((run_dir / "TEST-S01" / "s2_prompt.md").exists())


if __name__ == "__main__":
    unittest.main()
