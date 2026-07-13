from pathlib import Path
import unittest


P7D_DIR = Path(__file__).resolve().parents[2]
REVIEW_PROMPT = P7D_DIR / "prompts" / "edge_evidence_review_v1.md"


class P7DPromptSemanticContractTests(unittest.TestCase):
    def test_single_condition_is_a_logical_precondition(self) -> None:
        text = REVIEW_PROMPT.read_text(encoding="utf-8")
        self.assertIn("逻辑前提", text)
        self.assertIn("不要求钟表式时间顺序", text)
        self.assertIn("condition", text)

    def test_synonymous_outputs_and_requirements_are_unsupported(self) -> None:
        text = REVIEW_PROMPT.read_text(encoding="utf-8")
        self.assertIn("主动式/被动式", text)
        self.assertIn("理由、批准、标准或义务", text)
        self.assertIn("unsupported", text)

    def test_missing_condition_is_not_treated_as_not_applicable(self) -> None:
        text = REVIEW_PROMPT.read_text(encoding="utf-8")
        self.assertIn("原文关系本身是`if/when/unless`等条件关系", text)
        self.assertIn("edge遗漏`condition`", text)
        self.assertIn("填`unsupported`", text)

    def test_references_condition_is_only_applicability(self) -> None:
        text = REVIEW_PROMPT.read_text(encoding="utf-8")
        self.assertIn("REFERENCES", text)
        self.assertIn("适用范围", text)
        self.assertIn("条件分支", text)

    def test_x7_must_be_an_independent_continuing_obligation(self) -> None:
        text = REVIEW_PROMPT.read_text(encoding="utf-8")
        self.assertIn("X7_continuing_obligation", text)
        self.assertIn("语义独立的持续义务", text)
        self.assertIn("复制成义务出口", text)

    def test_prompt_declares_full_section_as_only_evidence_and_hides_review_hints(self) -> None:
        text = REVIEW_PROMPT.read_text(encoding="utf-8")
        self.assertIn("section_text_with_unit_anchors`是唯一事实证据", text)
        self.assertNotIn("section_units:", text)
        self.assertIn("已移除P7C声明的`derivation`", text)
        self.assertIn("Runner会在LLM审核完成后", text)

    def test_contextual_parameter_reference_can_be_inference(self) -> None:
        text = REVIEW_PROMPT.read_text(encoding="utf-8")
        self.assertIn("设定、应用或比较某项参数", text)
        self.assertIn("审核为`llm_inference`", text)
        self.assertIn("不是直接判为`unsupported`", text)

    def test_qualified_control_effect_does_not_become_certain(self) -> None:
        text = REVIEW_PROMPT.read_text(encoding="utf-8")
        self.assertIn("help mitigate/may reduce/can improve", text)
        self.assertIn("结构类型本身不把限定性效果强化", text)
        self.assertIn("有助于/可能/可以", text)


if __name__ == "__main__":
    unittest.main()
