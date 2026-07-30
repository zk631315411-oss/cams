from __future__ import annotations

from api.content import (
    apply_content_patch,
    carry_option_ids,
    compute_structured_changes,
    normalize_stem,
    parse_markdown,
    stable_option_ids,
)


SAMPLE = """# v7_q_test

题型：single

题干：中文题干

英文题干：English stem

选项：

- A. 选项甲
  English: Option A
- B. 选项乙
  English: Option B

## 【AI答案】

A

## 【核心解析】

原始解析。

## 【教材原文依据】

核心引用单元：`v7u_N000001`
"""


def test_parser_and_structured_patch_preserve_evidence():
    parsed = parse_markdown(SAMPLE)
    assert parsed["stem_en"] == "English stem"
    assert parsed["answer_letters"] == ["A"]
    assert parsed["evidence_unit_ids"] == ["v7u_N000001"]
    changed = apply_content_patch(SAMPLE, {"fields": {"stem_en": "Polished English stem", "answer_letters": ["B"]}})
    changed_parsed = parse_markdown(changed)
    assert changed_parsed["stem_en"] == "Polished English stem"
    assert changed_parsed["answer_letters"] == ["B"]
    assert "v7u_N000001" in changed


def test_option_ids_follow_content_when_options_move():
    old = parse_markdown(SAMPLE)
    ids = stable_option_ids("v7_q_test", old)
    moved = parse_markdown(SAMPLE.replace("- A. 选项甲", "- B. 选项甲").replace("- B. 选项乙", "- A. 选项乙"))
    moved_ids = carry_option_ids("v7_q_test", old, ids, moved)
    assert moved_ids["B"] == ids["A"]
    assert moved_ids["A"] == ids["B"]


def test_normalization_and_change_record():
    assert normalize_stem(" AML 风险！") == normalize_stem("AML风险")
    before = parse_markdown(SAMPLE)
    after = parse_markdown(SAMPLE.replace("中文题干", "修改后题干"))
    changes = compute_structured_changes(before, after)
    assert "stem_zh" in changes
