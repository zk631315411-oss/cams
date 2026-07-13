from pathlib import Path
import unittest


P7C_DIR = Path(__file__).resolve().parents[2]
EXTRACTION_PROMPT = P7C_DIR / "prompts" / "section_card_extraction_v1.md"
ADJUDICATION_PROMPT = P7C_DIR / "prompts" / "coverage_adjudication_v1.md"


class PromptSemanticContractTests(unittest.TestCase):
    def test_extraction_prompt_preserves_normative_modality(self) -> None:
        text = EXTRACTION_PROMPT.read_text(encoding="utf-8")
        self.assertIn("不等于动作已经完成", text)
        self.assertIn("把情态保留在process label中", text)
        self.assertIn("才可以增加相应限定", text)

    def test_both_prompts_disambiguate_escalation_from_reporting(self) -> None:
        for prompt_path in (EXTRACTION_PROMPT, ADJUDICATION_PROMPT):
            with self.subTest(prompt=prompt_path.name):
                text = prompt_path.read_text(encoding="utf-8")
                self.assertIn("升级处理/升级处置", text)
                self.assertIn("不得翻译为“上报/报告”", text)

    def test_adjudication_prompt_rejects_invented_continuity(self) -> None:
        text = ADJUDICATION_PROMPT.read_text(encoding="utf-8")
        self.assertIn("不证明义务是持续、定期、永久或反复的", text)

    def test_both_prompts_do_not_use_rule_simplicity_as_a_skip_reason(self) -> None:
        for prompt_path in (EXTRACTION_PROMPT, ADJUDICATION_PROMPT):
            with self.subTest(prompt=prompt_path.name):
                text = prompt_path.read_text(encoding="utf-8")
                self.assertIn("纯义务陈述", text)
                self.assertIn("没有复杂步骤", text)
                self.assertIn("风险偏好", text)

    def test_extraction_prompt_allows_open_candidate_relations(self) -> None:
        text = EXTRACTION_PROMPT.read_text(encoding="utf-8")
        self.assertIn("允许保留开放式局部关系", text)
        self.assertIn("不得补造X7义务出口", text)
        self.assertIn("candidate_status", text)
        self.assertIn("derivation", text)

    def test_both_prompts_treat_static_objects_as_references(self) -> None:
        for prompt_path in (EXTRACTION_PROMPT, ADJUDICATION_PROMPT):
            with self.subTest(prompt=prompt_path.name):
                text = prompt_path.read_text(encoding="utf-8")
                self.assertIn("静态适用对象", text)
                self.assertIn("REFERENCES", text)

    def test_both_prompts_reject_synonymous_outputs_and_obligation_products(self) -> None:
        for prompt_path in (EXTRACTION_PROMPT, ADJUDICATION_PROMPT):
            with self.subTest(prompt=prompt_path.name):
                text = prompt_path.read_text(encoding="utf-8")
                self.assertIn("主动式和被动式", text)
                self.assertIn("PRODUCES", text)
                self.assertIn("要求/义务", text)

    def test_both_prompts_encode_single_conditions_without_fake_branches(self) -> None:
        for prompt_path in (EXTRACTION_PROMPT, ADJUDICATION_PROMPT):
            with self.subTest(prompt=prompt_path.name):
                text = prompt_path.read_text(encoding="utf-8")
                self.assertIn("逻辑前提", text)
                self.assertIn("condition", text)
                self.assertIn("PRECEDES", text)

    def test_extraction_prompt_has_no_legacy_obligation_or_synonym_examples(self) -> None:
        text = EXTRACTION_PROMPT.read_text(encoding="utf-8")
        self.assertNotIn("并产生监控/KYC配置变化或升级义务", text)
        self.assertNotIn("出口表达“通常需要理由和批准”", text)
        self.assertNotIn("母国监管政策是`E7_external_command`起点", text)
        self.assertNotIn("exit X1_classification：控制人或名义受益所有人被识别", text)
        self.assertNotIn("functional_dependency边", text)

    def test_extraction_prompt_preserves_kg_only_coverage_records(self) -> None:
        text = EXTRACTION_PROMPT.read_text(encoding="utf-8")
        self.assertIn("没有合格card时也必须保留", text)
        self.assertIn("只有完整扫描后确实没有任何候选命题时", text)

    def test_adjudication_prompt_does_not_claim_p7d_validation(self) -> None:
        text = ADJUDICATION_PROMPT.read_text(encoding="utf-8")
        self.assertNotIn("通过结构校验的card", text)
        self.assertIn("尚未经过P7D正式结构校验和边级审核", text)

    def test_adjudication_evidence_is_limited_to_candidate_units(self) -> None:
        text = ADJUDICATION_PROMPT.read_text(encoding="utf-8")
        self.assertIn("只能引用对应候选原有的`unit_ids`", text)
        self.assertIn("不得借裁决轮追加其他unit", text)

    def test_adjudication_returns_patch_without_echoing_original_truth(self) -> None:
        text = ADJUDICATION_PROMPT.read_text(encoding="utf-8")
        self.assertIn("original_json", text)
        self.assertIn("无记忆API调用", text)
        self.assertIn("promoted_cards", text)
        self.assertIn("只返回补丁对象", text)
        self.assertIn("不得输出`coverage_audit`、既有`cards`", text)

    def test_references_condition_only_limits_applicability(self) -> None:
        for prompt_path in (EXTRACTION_PROMPT, ADJUDICATION_PROMPT):
            with self.subTest(prompt=prompt_path.name):
                text = prompt_path.read_text(encoding="utf-8")
                self.assertIn("REFERENCES.condition", text)
                self.assertIn("适用范围", text)
                self.assertIn("条件分支", text)

    def test_all_relation_types_have_usage_guidance(self) -> None:
        text = EXTRACTION_PROMPT.read_text(encoding="utf-8")
        for relation_type in (
            "mechanism_explains_risk",
            "cycle_requires_monitoring",
            "parallel_alternative_no_sequence",
        ):
            with self.subTest(relation_type=relation_type):
                self.assertGreaterEqual(text.count(relation_type), 2)

    def test_both_prompts_limit_x7_to_independent_obligations(self) -> None:
        for prompt_path in (EXTRACTION_PROMPT, ADJUDICATION_PROMPT):
            with self.subTest(prompt=prompt_path.name):
                text = prompt_path.read_text(encoding="utf-8")
                self.assertIn("X7_continuing_obligation", text)
                self.assertIn("独立", text)
                self.assertIn("process", text)


if __name__ == "__main__":
    unittest.main()
