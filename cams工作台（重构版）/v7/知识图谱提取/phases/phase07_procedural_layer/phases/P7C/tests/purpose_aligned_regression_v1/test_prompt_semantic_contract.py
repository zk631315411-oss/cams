from pathlib import Path
import unittest


P7C_DIR = Path(__file__).resolve().parents[2]
S1_PROMPT = P7C_DIR / "prompts" / "proposition_discovery_v1.md"
S2_PROMPT = P7C_DIR / "prompts" / "kg_boundary_and_graph_v1.md"


class PromptSemanticContractTests(unittest.TestCase):
    """Semantic contract tests — verify key rules exist in prompts."""

    def test_s1_output_contract_includes_induction_field(self) -> None:
        text = S1_PROMPT.read_text(encoding="utf-8")
        self.assertIn('"induction"', text)
        self.assertIn("cross_unit", text)

    def test_s2_cross_unit_induction_per_edge_not_blanket(self) -> None:
        text = S2_PROMPT.read_text(encoding="utf-8")
        # Must have per-edge judgment, not blanket llm_inference
        self.assertIn("不要因命题整体是归纳的就一律标", text)

    def test_s2_because_is_semantic_not_lexical_rule(self) -> None:
        text = S2_PROMPT.read_text(encoding="utf-8")
        self.assertIn("按语义区分", text)
        self.assertIn("属于基础 KG", text)

    def test_s2_p2_obligation_not_duplicated_as_x7(self) -> None:
        text = S2_PROMPT.read_text(encoding="utf-8")
        # P2 must/shall obligation should not be copied as X7
        self.assertIn("动作本身的", text)
        self.assertIn("不是 X7", text)

    def test_s2_independently_verifies_s1_propositions(self) -> None:
        text = S2_PROMPT.read_text(encoding="utf-8")
        self.assertIn("以原文为准，不以 S1 命题文本为准", text)


if __name__ == "__main__":
    unittest.main()
