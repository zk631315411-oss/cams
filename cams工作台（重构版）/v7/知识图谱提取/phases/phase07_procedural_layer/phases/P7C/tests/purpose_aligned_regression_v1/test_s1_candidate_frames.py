from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


TEST_FILE = Path(__file__).resolve()
PHASE_DIR = next(parent for parent in TEST_FILE.parents if (parent / "scripts" / "run_p7c_batch_ds.py").exists())
RUNNER_PATH = PHASE_DIR / "scripts" / "run_p7c_batch_ds.py"
S1_PROMPT_PATH = PHASE_DIR / "phases" / "P7C" / "prompts" / "proposition_discovery_v1.md"
P7B_PACKAGES = PHASE_DIR / "phases" / "P7B" / "section_packages"


def load_runner():
    spec = importlib.util.spec_from_file_location("p7c_s1_runner", RUNNER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load_runner()


def load_task(section_id: str) -> dict:
    return json.loads((P7B_PACKAGES / section_id / "task.json").read_text(encoding="utf-8"))


def validate(task: dict, proposition: dict) -> list[str]:
    return RUNNER.validate_s1_discovery_payload(
        {"propositions": [proposition]},
        set(RUNNER.collect_allowed_unit_ids(task)),
        RUNNER.collect_unit_evidence_text(task),
    )


def ch06_s10_cross_unit_candidate() -> dict:
    return {
        "candidate_id": "s1c_ch06_s10_ubo_threshold",
        "unit_ids": ["v7u_N000489", "v7u_N000493", "v7u_N000494", "v7u_N000495"],
        "proposition": "合计直接和间接持股达到适用阈值时认定为UBO，未达到时不认定为UBO。",
        "source_quotes": [
            "identified at a threshold of 25% or more",
            "In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership.",
            "Individual D is then considered a UBO with 82% shareholding of Company A.",
            "Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO.",
        ],
        "relation_cues": ["threshold", "direct", "indirect", "considered", "not"],
        "candidate_frame": {
            "trigger_or_context": ["需要判断持股是否达到适用阈值"],
            "basis_or_condition": ["受益所有权识别阈值"],
            "focal_handling_or_judgment": "合计直接和间接持股，并根据阈值判断是否认定为UBO",
            "outcomes_or_paths": ["达到阈值：认定为UBO", "未达到阈值：不认定为UBO"],
        },
        "evidence_spans": [
            {"unit_id": "v7u_N000489", "quote": "identified at a threshold of 25% or more"},
            {
                "unit_id": "v7u_N000493",
                "quote": "In order to identify the UBOs of Company A, you need to identify indirect ownership stakes in addition to direct ownership.",
            },
            {"unit_id": "v7u_N000494", "quote": "Individual D is then considered a UBO with 82% shareholding of Company A."},
            {
                "unit_id": "v7u_N000495",
                "quote": "Individual C, who owns 10% of Company A directly and an additional 8% indirectly via their 10% ownership of Company B, is not a UBO.",
            },
        ],
        "induction": "cross_unit",
        "cross_unit_basis": {
            "rule_unit_ids": ["v7u_N000489"],
            "positive_example_unit_ids": ["v7u_N000494"],
            "negative_example_unit_ids": ["v7u_N000495"],
        },
    }


def ch06_s10_risk_threshold_exception_candidate() -> dict:
    quotes = [
        "Your organization will set the appropriate threshold using a riskbased approach.",
        "For certain high-risk customers, the beneficial ownership threshold might be as low as 10% and could go as low as 5% for customers who pose a significantly higher risk.",
        "For example, high-risk financial institutions with correspondent banking relationships in a high-risk jurisdiction might set their threshold at 5%.",
    ]
    return {
        "candidate_id": "s1c_ch06_s10_risk_threshold_exception",
        "unit_ids": ["v7u_N000490", "v7u_N000491", "v7u_N000492"],
        "proposition": "机构采用风险为本方法设定受益所有权阈值；高风险客户阈值可能降至10%或5%。",
        "source_quotes": quotes,
        "relation_cues": ["riskbased", "might", "could", "for example"],
        "candidate_frame": {
            "trigger_or_context": ["客户为高风险或显著更高风险"],
            "basis_or_condition": ["机构采用风险为本的方法设定适当阈值"],
            "focal_handling_or_judgment": "设定或调整适用的受益所有权阈值",
            "outcomes_or_paths": ["阈值可能降至10%或5%"],
        },
        "evidence_spans": [
            {"unit_id": "v7u_N000490", "quote": quotes[0]},
            {"unit_id": "v7u_N000491", "quote": quotes[1]},
            {"unit_id": "v7u_N000492", "quote": quotes[2]},
        ],
        "induction": None,
        "cross_unit_basis": None,
    }


def ch02_s04_legal_candidate() -> dict:
    quote = "It applies to any company with a UK connection and also holds parent firms liable for corrupt activities by subsidiaries, regardless of location."
    return {
        "candidate_id": "s1c_ch02_s04_legal_applicability",
        "unit_ids": ["v7u_N000136"],
        "proposition": "与英国有关联的公司适用该法，母公司可能对子公司的腐败行为承担责任。",
        "source_quotes": [quote],
        "relation_cues": ["applies to", "liable"],
        "candidate_frame": {
            "trigger_or_context": ["公司与英国有关联"],
            "basis_or_condition": [],
            "focal_handling_or_judgment": "该法适用于公司并规定母公司的责任",
            "outcomes_or_paths": ["母公司可能对子公司的腐败行为承担责任"],
        },
        "evidence_spans": [{"unit_id": "v7u_N000136", "quote": quote}],
        "induction": None,
        "cross_unit_basis": None,
    }


def ch02_s04_case_applicability_candidate() -> dict:
    quotes = [
        "One day, she came across negative news concerning their customer FullTechGlobal Services, which is incorporated and headquartered in the US and is a subsidiary of a UK company.",
        "The company faced serious accusations of widespread bribery and corruption due to its overseas sales practices.",
        "This raised concerns under the extraterritorial provisions of the UK Bribery Act 2010.",
    ]
    return {
        "candidate_id": "s1c_ch02_s04_case_applicability",
        "unit_ids": ["v7u_N000132", "v7u_N000133", "v7u_N000134"],
        "proposition": "FullTechGlobal的主体关系和海外贿赂腐败指控引发对英国《反贿赂法》域外条款适用的关切。",
        "source_quotes": quotes,
        "relation_cues": ["subsidiary", "accusations", "raised concerns", "extraterritorial"],
        "candidate_frame": {
            "trigger_or_context": ["FullTechGlobal是英国公司子公司，并面临海外贿赂腐败指控"],
            "basis_or_condition": ["英国《反贿赂法》域外条款"],
            "focal_handling_or_judgment": "引发对该法域外适用的法律关切",
            "outcomes_or_paths": [],
        },
        "evidence_spans": [
            {"unit_id": "v7u_N000132", "quote": quotes[0]},
            {"unit_id": "v7u_N000133", "quote": quotes[1]},
            {"unit_id": "v7u_N000134", "quote": quotes[2]},
        ],
        "induction": None,
        "cross_unit_basis": None,
    }


def ch02_s04_investigation_finding_candidate() -> dict:
    quote = "Sophie’s initial investigation revealed that FullTechGlobal had strategically employed intermediaries in high-risk jurisdictions to secure lucrative contracts."
    return {
        "candidate_id": "s1c_ch02_s04_initial_investigation",
        "unit_ids": ["v7u_N000138"],
        "proposition": "Sophie的初步调查发现FullTechGlobal在高风险司法管辖区策略性使用中间人获取合同。",
        "source_quotes": [quote],
        "relation_cues": ["initial investigation", "revealed"],
        "candidate_frame": {
            "trigger_or_context": [],
            "basis_or_condition": [],
            "focal_handling_or_judgment": "Sophie进行初步调查",
            "outcomes_or_paths": ["发现FullTechGlobal在高风险司法管辖区策略性使用中间人"],
        },
        "evidence_spans": [{"unit_id": "v7u_N000138", "quote": quote}],
        "induction": None,
        "cross_unit_basis": None,
    }


class S1CandidateFrameContractTests(unittest.TestCase):
    def test_rendered_s1_prompt_uses_only_metadata_and_anchored_text(self) -> None:
        task = load_task("CH06-S10")
        rendered = RUNNER.build_s1_prompt(S1_PROMPT_PATH.read_text(encoding="utf-8"), task)

        self.assertEqual(rendered.count("## 当前section"), 1)
        self.assertIn(task["section_text_with_unit_anchors"], rendered)
        self.assertIn(f"section_id: `{task['section_id']}`", rendered)
        self.assertNotIn("allowed_unit_ids", rendered)
        self.assertNotIn("base_kg_section_summary:", rendered)
        self.assertNotIn("<SECTION_TEXT>", rendered)

    def test_ch06_s10_cross_unit_frame_has_required_evidence_groups(self) -> None:
        task = load_task("CH06-S10")
        self.assertEqual(validate(task, ch06_s10_cross_unit_candidate()), [])
        self.assertEqual(validate(task, ch06_s10_risk_threshold_exception_candidate()), [])

    def test_ch02_s04_legal_frame_is_a_valid_open_candidate(self) -> None:
        task = load_task("CH02-S04")
        self.assertEqual(validate(task, ch02_s04_legal_candidate()), [])

    def test_ch02_s04_case_applicability_and_investigation_frames_are_valid(self) -> None:
        task = load_task("CH02-S04")
        self.assertEqual(validate(task, ch02_s04_case_applicability_candidate()), [])
        self.assertEqual(validate(task, ch02_s04_investigation_finding_candidate()), [])

    def test_s1_prompt_requires_case_applicability_and_investigation_discovery(self) -> None:
        prompt = S1_PROMPT_PATH.read_text(encoding="utf-8")
        self.assertIn("案例特有的法律适用 frame", prompt)
        self.assertIn("案例调查到发现 frame", prompt)
        self.assertIn("风险为本阈值例外 frame", prompt)
        self.assertIn("前一个候选不成为跳过后文", prompt)
        self.assertIn("一般规则的候选不能替代", prompt)

    def test_validator_requires_a_role_around_the_focal_handling_or_judgment(self) -> None:
        task = load_task("CH02-S04")
        candidate = ch02_s04_legal_candidate()
        candidate["candidate_frame"]["trigger_or_context"] = []
        candidate["candidate_frame"]["basis_or_condition"] = []
        candidate["candidate_frame"]["outcomes_or_paths"] = []

        errors = validate(task, candidate)
        self.assertTrue(any("requires a trigger, basis, outcome, or path" in error for error in errors), errors)

    def test_validator_rejects_out_of_section_unit(self) -> None:
        task = load_task("CH02-S04")
        candidate = ch02_s04_legal_candidate()
        candidate["unit_ids"] = ["v7u_not_in_section"]
        candidate["evidence_spans"][0]["unit_id"] = "v7u_not_in_section"

        errors = validate(task, candidate)
        self.assertTrue(any("out-of-section evidence" in error for error in errors), errors)

    def test_validator_rejects_source_quote_not_tied_to_an_evidence_span(self) -> None:
        task = load_task("CH02-S04")
        candidate = ch02_s04_legal_candidate()
        candidate["source_quotes"] = ["It applies to any company with a UK connection"]

        errors = validate(task, candidate)
        self.assertTrue(any("must match an evidence_spans quote" in error for error in errors), errors)

    def test_validator_rejects_unlocatable_quote_and_missing_cross_unit_basis_group(self) -> None:
        task = load_task("CH06-S10")
        candidate = ch06_s10_cross_unit_candidate()
        candidate["evidence_spans"][0]["quote"] = "not in the source unit"
        candidate["cross_unit_basis"]["negative_example_unit_ids"] = []

        errors = validate(task, candidate)
        self.assertTrue(any("quote is not found" in error for error in errors), errors)
        self.assertTrue(any("negative_example_unit_ids must be a non-empty list" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
