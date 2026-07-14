# -*- coding: utf-8 -*-
"""Run the recorded q140 V3 baseline or a unit-text-only prompt variant."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "phase4_evidence" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import generate_evidence_explanations as master


def unit_only_prompt(result: dict[str, Any]) -> str:
    sanitized = copy.deepcopy(result)
    for row in sanitized.get("option_analysis", []) or []:
        row["decision_reason"] = ""
        for card in row.get("evidence_cards", []) or []:
            card["reason"] = ""
    framework = sanitized.get("decision_framework", {}) or {}
    framework["rule_summary"] = ""
    framework["required_conditions"] = []
    prompt = _ORIGINAL_BUILD_PROMPT(sanitized)
    marker = "边界：\n"
    rule = (
        "本次只提供盲判标签和真实unit原文；盲判生成的理由、证据卡理由、"
        "框架摘要和必要条件均不是教材原文，禁止猜测、恢复或引用其中的事实。"
        "核心解析必须区分决定性题干信号与伴随事实：只有被引用unit原文直接覆盖的"
        "题干信号才能写成定义要素或匹配条件；其他题干事实只能标为背景，不得用"
        "‘这一模式’‘完全符合’等表述把两者合并。所有text字段不得出现v7u_开头的"
        "内部unit_id，ID只能写入结构化的cited_unit_ids和source_quote.unit_id。"
        "任何概念间的分类、包含、等同、阶段、程度、频率、范围或关联关系，都必须"
        "由所引unit的knowledge_zh或en_quote明确陈述；原文未明确写出时必须省略，"
        "不得自行使用‘属于’‘是某种形式’‘极端形式’‘典型’‘通常关联’等关系词补全。\n"
    )
    return prompt.replace(marker, marker + rule, 1)


_ORIGINAL_BUILD_PROMPT = master.build_prompt


def write_baseline(source_question: Path, artifact_dir: Path) -> None:
    question_dir = artifact_dir / "questions"
    question_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_question, question_dir / source_question.name)
    data = master.load_question_result(source_question)
    qid = str(data.get("question_id", ""))
    source_markdown = source_question.parents[1] / "explanations" / f"{qid}.md"
    if source_markdown.exists():
        explanation_dir = artifact_dir / "explanations"
        explanation_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_markdown, explanation_dir / source_markdown.name)


def run_variant(source_question: Path, artifact_dir: Path) -> None:
    result = master.load_question_result(source_question)
    for key in (
        "generated_explanation",
        "generated_explanation_prompt",
        "generated_explanation_raw_output",
    ):
        result.pop(key, None)
    question_dir = artifact_dir / "questions"
    question_dir.mkdir(parents=True, exist_ok=True)
    target = question_dir / source_question.name
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    qid = str(result.get("question_id", ""))
    standards = master.load_standard_questions(master.DEFAULT_QUESTIONS_PATH)
    references = master.load_reference_workbook(master.DEFAULT_REFERENCE_WORKBOOK)
    api_key, base_url, _ = master.get_llm_config()
    master.build_prompt = unit_only_prompt
    master.process_file(
        target,
        artifact_dir,
        api_key,
        base_url,
        "deepseek-v4-pro",
        True,
        standards[qid],
        references[qid],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=("baseline", "variant"), required=True)
    parser.add_argument("--source-question", required=True)
    parser.add_argument("--artifact-dir", required=True)
    args = parser.parse_args()

    source_question = Path(args.source_question).resolve()
    artifact_dir = Path(args.artifact_dir).resolve()
    if args.arm == "baseline":
        write_baseline(source_question, artifact_dir)
    else:
        run_variant(source_question, artifact_dir)
    print(f"[output] arm={args.arm} | artifact_dir={artifact_dir}")


if __name__ == "__main__":
    main()
