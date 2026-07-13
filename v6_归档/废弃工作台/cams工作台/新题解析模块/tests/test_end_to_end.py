"""
End-to-end smoke tests for the new-question analysis pipeline.

These tests validate the three core modules:
    pipeline.evidence_pool   — Runtime initialisation
    pipeline.question_parser — Question text parsing
    pipeline.run_pipeline    — 5-step blind pipeline

Usage:
    cd 新题解析模块
    python tests/test_end_to_end.py              # all tests (needs API key + BGE)
    python tests/test_end_to_end.py --parser-only  # parser only (no API/BGE needed)
    python tests/test_end_to_end.py --pipeline     # full pipeline (needs everything)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parents[1]  # 新题解析模块/
sys.path.insert(0, str(_MODULE_DIR))

_FOUR_ROLE_DIR = Path(__file__).resolve().parents[3] / "题目与kg关系建立流水线（四角色法）"
if str(_FOUR_ROLE_DIR) not in sys.path:
    sys.path.insert(0, str(_FOUR_ROLE_DIR))

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# ---------------------------------------------------------------------------
# Sample questions for testing
# ---------------------------------------------------------------------------
SAMPLE_STANDARD = """单选题
资金转移的危险信号是什么?
A. 从相关行业的实体收到大量小额的资金转移
B. 资金转账重复发送给同一受益人，与业务目的不符
C. 资金转移是重复性的，符合预期模式
D. 资金转移到已知同行业内位于风险地区的供应商发起人
答案：B"""

SAMPLE_A_E = """以下哪些属于反洗钱可疑交易特征？
A. 短期内资金频繁转入转出
B. 交易金额与客户身份不符
C. 正常的工资发放
D. 与风险地区频繁交易
E. 符合预期的定期转账"""

SAMPLE_GARBLED = """以下哪个选项不属于反洗钱义务主体？1、银行 2、证券公司 3、个人 4、保险公司"""

SAMPLE_NO_ANSWER = """CAMS考试中，客户尽职调查的核心要求是什么？
A. 只需要在开户时做一次
B. 持续监控并更新客户信息
C. 仅对大额客户执行
D. 由第三方代为完成"""


# ---------------------------------------------------------------------------
# Test 1: Question parser (rules only, no LLM / BGE needed)
# ---------------------------------------------------------------------------
def test_parser_standard():
    from pipeline.question_parser import parse_question_rules

    result = parse_question_rules(SAMPLE_STANDARD)
    assert result is not None, "Standard format should be parsed by rules"
    assert "资金转移的危险信号" in result["stem"], f"Stem mismatch: {result['stem']}"
    assert len(result["options"]) == 4, f"Expected 4 options, got {len(result['options'])}"
    assert result["options"]["A"], "Option A should not be empty"
    assert result["detected_answer"] == "B", f"Expected answer B, got {result['detected_answer']}"
    assert result["parse_method"] == "rules"
    print("  [PASS] test_parser_standard")


def test_parser_a_e():
    from pipeline.question_parser import parse_question_rules

    result = parse_question_rules(SAMPLE_A_E)
    assert result is not None, "A-E format should be parsed by rules"
    assert len(result["options"]) == 5, f"Expected 5 options, got {len(result['options'])}"
    assert "E" in result["options"], "Option E should be present"
    print("  [PASS] test_parser_a_e")


def test_parser_garbled():
    from pipeline.question_parser import parse_question_rules

    result = parse_question_rules(SAMPLE_GARBLED)
    # Garbled format (数字编号而非字母) should fail rules
    assert result is None, "Garbled format should return None (trigger LLM fallback)"
    print("  [PASS] test_parser_garbled")


def test_parser_empty():
    from pipeline.question_parser import parse_question

    result = parse_question(None, "")
    assert result["parse_method"] == "rules"
    assert "输入文本为空" in result["parse_warnings"][0]
    print("  [PASS] test_parser_empty")


def test_parser_detected_answer_saved():
    """detected_answer must be saved but NOT control judgement."""
    from pipeline.question_parser import parse_question_rules

    result = parse_question_rules(SAMPLE_STANDARD)
    assert result["detected_answer"] == "B"
    # The detected_answer is saved for reference, but the caller
    # (run_pipeline) must NOT feed it to the blind adjudicator.
    print("  [PASS] test_parser_detected_answer_saved")


def test_blind_isolation_prompt_signatures():
    """Verify the blind planner/adjudicator functions do NOT accept an answer
    parameter — this is the structural guarantee that detected_answer can't
    leak into the LLM prompt."""
    import inspect

    import run_blind_q212_experiment as blind_mod

    planner_sig = inspect.signature(blind_mod.build_blind_planner_prompt)
    adjudicator_sig = inspect.signature(blind_mod.build_blind_adjudicator_prompt)

    # Both functions take (stem, options) — no answer / detected_answer param
    planner_params = set(planner_sig.parameters)
    adjudicator_params = set(adjudicator_sig.parameters)

    for name in ("answer", "detected_answer", "standard_answer"):
        assert name not in planner_params, (
            f"build_blind_planner_prompt accepts '{name}' — blind isolation broken!"
        )
        assert name not in adjudicator_params, (
            f"build_blind_adjudicator_prompt accepts '{name}' — blind isolation broken!"
        )

    print("  [PASS] test_blind_isolation_prompt_signatures")


def test_blind_isolation_prompt_content():
    """Generate a planner + adjudicator prompt and assert detected_answer text
    does NOT appear in either."""
    import run_blind_q212_experiment as blind_mod

    stem = "资金转移的危险信号是什么?"
    options = {"A": "大量小额转账", "B": "重复转账与目的不符", "C": "符合预期模式", "D": "转至风险地区供应商"}
    detected = "B"

    planner_prompt = blind_mod.build_blind_planner_prompt(stem, options)
    adjudicator_prompt = blind_mod.build_blind_adjudicator_prompt(
        stem, options, {"options": []}, {"A": [], "B": [], "C": [], "D": []}
    )

    # detected_answer must be absent from both prompts
    # (The prompts DO contain prohibition text like "不要说'标准答案'" —
    #  that is correct and expected.  We only flag if the *actual answer
    #  content* leaks in, e.g. "答案：B" or "正确答案 B".)
    for prompt_name, prompt_text in [
        ("planner", planner_prompt),
        ("adjudicator", adjudicator_prompt),
    ]:
        # Check that the specific answer label-value combination doesn't appear
        answer_leak_patterns = [
            f"答案:{detected}",
            f"答案：{detected}",
            f"答案 {detected}",
            f"正确答案{detected}",
            f"正确答案 {detected}",
            f"标准答案{detected}",
            f"标准答案 {detected}",
        ]
        for pattern in answer_leak_patterns:
            assert pattern not in prompt_text, (
                f"BLIND ISOLATION VIOLATION: {prompt_name} prompt contains '{pattern}'"
            )

    print("  [PASS] test_blind_isolation_prompt_content")
    print("  [PASS] test_parser_detected_answer_saved")


# ---------------------------------------------------------------------------
# Test 2: Runtime loading (needs BGE model + data files)
# ---------------------------------------------------------------------------
def test_runtime_load():
    from pipeline.evidence_pool import load_new_question_runtime

    rt = load_new_question_runtime(evidence_scope="v6-sentence")
    assert rt is not None
    assert len(rt.card_ids) > 1000, f"Expected 1000+ cards, got {len(rt.card_ids)}"
    assert len(rt.base.sections) > 0, "Expected KG sections to be loaded"
    assert rt.base.questions == [], "questions should be empty for blind mode"
    assert rt.card_vecs is not None, "card_vecs should be computed"
    assert rt.bm25_docs is not None, "BM25 index should be built"
    print(f"  [PASS] test_runtime_load ({len(rt.card_ids)} cards, {len(rt.base.sections)} sections)")


# ---------------------------------------------------------------------------
# Test 3: Full pipeline (needs API key + BGE + LLM)
# ---------------------------------------------------------------------------
def test_full_pipeline():
    from pipeline.evidence_pool import load_new_question_runtime
    from pipeline.run_pipeline import run_new_question_pipeline

    rt = load_new_question_runtime(evidence_scope="v6-sentence")
    result = run_new_question_pipeline(SAMPLE_NO_ANSWER, rt=rt, top_k=30)

    # Structural checks
    assert result.get("draft_id", "").startswith("nq_"), "Missing or malformed draft_id"
    assert "pipeline" in result, "Missing pipeline section"
    assert "final" in result, "Missing final section"

    # Step 1
    p1 = result["pipeline"]["parse_question"]
    assert p1["stem"], "Empty stem"
    assert len(p1["options"]) >= 2, f"Expected >=2 options, got {len(p1['options'])}"

    # Step 2
    p2 = result["pipeline"]["retrieve_evidence"]
    assert "search_plan" in p2
    assert "candidates_by_option" in p2
    assert p2["evidence_count"] >= 0

    # Step 3
    p3 = result["pipeline"]["judge_answer"]
    assert "predicted_answer" in p3
    assert "predicted_answer_confidence" in p3

    # Step 4
    p4 = result["pipeline"]["explain_options"]
    assert isinstance(p4["option_analysis"], list)
    assert len(p4["option_analysis"]) == len(p1["options"])
    # No "标准答案" leakage
    leakage = p4.get("leakage_issues", [])
    assert not leakage, f"Answer leakage detected: {leakage}"

    # Step 5
    p5 = result["pipeline"]["validate"]
    assert p5["validation_status"] in ("passed", "needs_review")
    assert len(p5["checks"]) >= 5

    # Final
    f = result["final"]
    assert "ai_answer" in f
    assert "confidence" in f
    assert len(f["option_explanations"]) == len(p1["options"])

    # Card ID hallucination check
    cited = p4.get("cited_cards", [])
    valid = rt.base.valid_card_ids
    for cid in cited:
        assert cid in valid, f"Hallucinated card_id: {cid}"

    # Draft file saved
    draft_path = _MODULE_DIR / "outputs" / "drafts" / f"{result['draft_id']}.json"
    assert draft_path.exists(), f"Draft not saved at {draft_path}"

    print(f"  [PASS] test_full_pipeline")
    print(f"    draft_id:        {result['draft_id']}")
    print(f"    ai_answer:       {f['ai_answer']}")
    print(f"    confidence:      {f['confidence']}")
    print(f"    evidence_count:  {p2['evidence_count']}")
    print(f"    cited_cards:     {len(cited)}")
    print(f"    validation:      {p5['validation_status']}")
    for c in p5["checks"]:
        print(f"      [{c['status']}] {c['name']}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="End-to-end tests for 新题解析模块")
    parser.add_argument("--parser-only", action="store_true", help="Only run parser tests (no BGE/API)")
    parser.add_argument("--runtime", action="store_true", help="Also test runtime loading")
    parser.add_argument("--pipeline", action="store_true", help="Run full pipeline test")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    args = parser.parse_args()

    run_all = args.all or (not args.parser_only and not args.runtime and not args.pipeline)

    print("=== 新题解析模块 End-to-End Tests ===\n")

    # Parser tests (always safe, no API/BGE needed)
    print("[Parser Tests]")
    try:
        test_parser_standard()
        test_parser_a_e()
        test_parser_garbled()
        test_parser_empty()
        test_parser_detected_answer_saved()
    except Exception as exc:
        print(f"  [FAIL] Parser tests: {exc}")
        return 1

    # Blind isolation tests (always safe, no API/BGE needed)
    print("\n[Blind Isolation Tests]")
    try:
        test_blind_isolation_prompt_signatures()
        test_blind_isolation_prompt_content()
    except Exception as exc:
        print(f"  [FAIL] Blind isolation tests: {exc}")
        import traceback
        traceback.print_exc()
        return 1

    if run_all or args.runtime:
        print("\n[Runtime Test] (needs BGE model + data files)")
        try:
            test_runtime_load()
        except Exception as exc:
            print(f"  [FAIL] Runtime test: {exc}")
            return 1

    if run_all or args.pipeline:
        print("\n[Pipeline Test] (needs API key + BGE + LLM, ~60-120s)")
        try:
            test_full_pipeline()
        except Exception as exc:
            print(f"  [FAIL] Pipeline test: {exc}")
            import traceback
            traceback.print_exc()
            return 1

    print("\n=== All tests passed ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
