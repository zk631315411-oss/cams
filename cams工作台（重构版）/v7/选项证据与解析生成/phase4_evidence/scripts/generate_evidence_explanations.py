# -*- coding: utf-8 -*-
"""
Generate evidence-based Markdown explanations from Phase 4 blind judgments.

This is a post-processing step: it reads existing q_*.json files produced by
blind_adjudication.py, asks the LLM to turn the adjudicated evidence cards into
teacher-facing explanations, and writes Markdown files. It does not re-judge the
answer and does not use official/reference answers.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PHASE4 = HERE.parent
DEFAULT_OUTPUT_DIR = PHASE4 / "output"

API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


def get_llm_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = (
                os.environ.get("DEEPSEEK_BASE_URL")
                or os.environ.get("DS_BASE_URL")
                or DEFAULT_DEEPSEEK_BASE_URL
            )
            return value, base_url, env_name
    names = " / ".join(API_KEY_ENV_NAMES)
    raise RuntimeError(f"{names} 环境变量均未设置，不能调用 LLM API。")


def strip_json_fence(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def parse_json_object(raw_text: str) -> dict[str, Any] | None:
    cleaned = strip_json_fence(raw_text)
    if not cleaned:
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    try:
        import json_repair

        return json.loads(json_repair.repair_json(cleaned))
    except Exception:
        return None


def call_llm(
    client: Any,
    prompt: str,
    model: str = "deepseek-v4-pro",
    max_tokens: int = 6000,
    timeout: float = 120.0,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    return (response.choices[0].message.content or "").strip()


def load_question_result(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def candidate_by_unit(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for candidate in result.get("candidate_pool", []) or []:
        if isinstance(candidate, dict) and candidate.get("unit_id"):
            mapping[str(candidate["unit_id"])] = candidate
    return mapping


def compact_text(value: Any, max_len: int = 420) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def enriched_option_material(result: dict[str, Any]) -> list[dict[str, Any]]:
    options = result.get("options", {}) or {}
    unit_map = candidate_by_unit(result)
    rows: list[dict[str, Any]] = []

    by_label = {
        str(row.get("option", "")).strip().upper(): row
        for row in result.get("option_analysis", []) or []
        if isinstance(row, dict)
    }

    for label, option_text in options.items():
        label = str(label).strip().upper()
        analysis = by_label.get(label, {})
        evidence_cards: list[dict[str, Any]] = []
        for card in analysis.get("evidence_cards", []) or []:
            if not isinstance(card, dict):
                continue
            uid = str(card.get("unit_id", "")).strip()
            unit = unit_map.get(uid, {})
            evidence_cards.append(
                {
                    "unit_id": uid,
                    "support_type": card.get("support_type", ""),
                    "reason": card.get("reason", ""),
                    "knowledge_zh": unit.get("knowledge_zh", ""),
                    "en_quote": unit.get("en_quote", ""),
                    "knowledge_en": unit.get("knowledge_en", ""),
                    "heading_context": unit.get("heading_context", []),
                    "route": unit.get("route", ""),
                }
            )
        rows.append(
            {
                "option": label,
                "option_text": option_text,
                "judgement": analysis.get("judgement", ""),
                "evidence_status": analysis.get("evidence_status", ""),
                "evidence_cards": evidence_cards,
            }
        )
    return rows


def build_prompt(result: dict[str, Any]) -> str:
    stem = result.get("stem", "")
    qtype = result.get("question_type", "")
    predicted = ",".join(result.get("predicted_answer", []) or []) or "未形成答案"
    options = result.get("options", {}) or {}
    option_lines = "\n".join(f"{label}. {text}" for label, text in options.items())

    material_lines: list[str] = []
    for row in enriched_option_material(result):
        material_lines.append(
            f"选项{row['option']}：{row['option_text']}\n"
            f"系统判断：{row.get('judgement', '')} | 证据状态：{row.get('evidence_status', '')}"
        )
        cards = row.get("evidence_cards", []) or []
        if not cards:
            material_lines.append("证据卡：无")
            continue
        material_lines.append("证据卡：")
        for card in cards:
            heading = " > ".join(card.get("heading_context", []) or [])
            quote = card.get("en_quote") or card.get("knowledge_en") or ""
            material_lines.append(
                f"- {card.get('unit_id', '')} | {card.get('support_type', '')}\n"
                f"  中文要点：{compact_text(card.get('knowledge_zh', ''))}\n"
                f"  英文原文：{compact_text(quote)}\n"
                f"  章节：{heading}\n"
                f"  裁判理由：{compact_text(card.get('reason', ''))}"
            )

    return f"""你是CAMS新题解析教研助理。请把已经完成的选项级证据裁判结果，整理成可读的中文解析。

你的任务不是重新判题，而是基于给定的系统判断和证据卡，写出“解答思路”和“各选项依据”。

要求：
1. 只使用下面给出的题干、选项、系统预测答案和证据卡。
2. 不要引用未给出的参考答案、官方解析或外部知识。
3. 正确项说明为什么能由证据推出；错误项说明是被证据反驳、证据不足，还是与题干关键限定不匹配。
4. 每个选项都要写依据；证据卡为空时要明确写“本轮证据未提供直接依据”。
5. 引用依据时必须保留 unit_id。
6. 语言面向教研复核，简洁、可检查，避免泛泛而谈。

题型：{qtype}
题干：{stem}

选项：
{option_lines}

系统预测答案：{predicted}

选项级证据材料：
{chr(10).join(material_lines)}

请输出严格 JSON，不要 Markdown：
{{
  "answer": ["A"],
  "solution_logic": "2-4句话说明解题抓手和为什么选该答案",
  "option_explanations": [
    {{
      "option": "A",
      "judgement": "correct/incorrect/insufficient",
      "basis": "该选项的依据说明，必须包含相关unit_id；无证据则说明本轮证据不足",
      "cited_unit_ids": ["v7u_N000001"]
    }}
  ],
  "teacher_review_note": "如存在证据不足、参考答案可能分歧或需要人工复核，在这里说明；否则为空字符串"
}}"""


def normalize_explanation(parsed: dict[str, Any] | None, result: dict[str, Any]) -> dict[str, Any]:
    options = result.get("options", {}) or {}
    predicted = [str(x).strip().upper() for x in result.get("predicted_answer", []) or []]
    if not isinstance(parsed, dict):
        parsed = {}

    answer = parsed.get("answer", predicted)
    if not isinstance(answer, list):
        answer = predicted
    answer = [str(x).strip().upper() for x in answer if str(x).strip().upper() in options]
    if not answer:
        answer = predicted

    source_rows = {
        row["option"]: row for row in enriched_option_material(result)
    }
    raw_rows = parsed.get("option_explanations", [])
    if not isinstance(raw_rows, list):
        raw_rows = []
    raw_by_label = {
        str(row.get("option", "")).strip().upper(): row
        for row in raw_rows
        if isinstance(row, dict)
    }

    option_explanations: list[dict[str, Any]] = []
    for label in options:
        label = str(label).strip().upper()
        source = source_rows.get(label, {})
        raw = raw_by_label.get(label, {})
        cards = source.get("evidence_cards", []) or []
        fallback_ids = [c.get("unit_id") for c in cards if c.get("unit_id")]
        basis = str(raw.get("basis", "") or "").strip()
        if not basis:
            if fallback_ids:
                reasons = "；".join(compact_text(c.get("reason", ""), 120) for c in cards[:2])
                basis = f"依据 {', '.join(fallback_ids)}：{reasons}"
            else:
                basis = "本轮证据未提供直接依据。"
        cited = raw.get("cited_unit_ids", fallback_ids)
        if not isinstance(cited, list):
            cited = fallback_ids
        cited = [str(uid).strip() for uid in cited if str(uid).strip()]
        option_explanations.append(
            {
                "option": label,
                "judgement": str(raw.get("judgement", source.get("judgement", "")) or ""),
                "evidence_status": source.get("evidence_status", ""),
                "basis": basis,
                "cited_unit_ids": cited,
            }
        )

    return {
        "answer": answer,
        "solution_logic": str(parsed.get("solution_logic", "") or "").strip(),
        "option_explanations": option_explanations,
        "teacher_review_note": str(parsed.get("teacher_review_note", "") or "").strip(),
    }


def markdown_escape_table(text: Any) -> str:
    value = str(text or "").replace("\n", "<br>")
    return value.replace("|", "\\|")


def render_markdown(result: dict[str, Any], explanation: dict[str, Any]) -> str:
    qid = result.get("question_id", "")
    predicted = ", ".join(explanation.get("answer", []) or result.get("predicted_answer", []) or [])
    lines: list[str] = []
    lines.append(f"# {qid} 证据解析\n\n")
    lines.append(f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    lines.append(f"题型：{result.get('question_type', '')}\n\n")
    lines.append(f"题干：{result.get('stem', '')}\n\n")
    lines.append("## 选项\n\n")
    for label, text in (result.get("options", {}) or {}).items():
        lines.append(f"- {label}. {text}\n")
    lines.append(f"\n## 系统答案\n\n{predicted or '未形成答案'}\n\n")
    lines.append("## 解答思路\n\n")
    logic = explanation.get("solution_logic") or "本题依据各选项的证据卡判断正误；证据为空的选项不作为直接支持。"
    lines.append(f"{logic}\n\n")
    lines.append("## 各选项依据\n\n")
    lines.append("| 选项 | 判断 | 证据状态 | 依据 | 引用单元 |\n")
    lines.append("|---|---|---|---|---|\n")
    for row in explanation.get("option_explanations", []) or []:
        cited = ", ".join(row.get("cited_unit_ids", []) or [])
        lines.append(
            f"| {markdown_escape_table(row.get('option', ''))} "
            f"| {markdown_escape_table(row.get('judgement', ''))} "
            f"| {markdown_escape_table(row.get('evidence_status', ''))} "
            f"| {markdown_escape_table(row.get('basis', ''))} "
            f"| {markdown_escape_table(cited)} |\n"
        )

    note = explanation.get("teacher_review_note", "")
    if note:
        lines.append("\n## 教研复核提示\n\n")
        lines.append(f"{note}\n")
    return "".join(lines)


def process_file(
    path: Path,
    output_dir: Path,
    api_key: str,
    base_url: str,
    model: str,
    write_back: bool,
) -> dict[str, Any]:
    result = load_question_result(path)
    qid = result.get("question_id", path.stem)
    prompt = build_prompt(result)

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    raw = call_llm(client, prompt, model=model)
    parsed = parse_json_object(raw)
    explanation = normalize_explanation(parsed, result)

    md = render_markdown(result, explanation)
    explanations_dir = output_dir / "explanations"
    explanations_dir.mkdir(parents=True, exist_ok=True)
    md_path = explanations_dir / f"{qid}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    if write_back:
        result["generated_explanation"] = explanation
        result["generated_explanation_raw_output"] = raw
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return {
        "question_id": qid,
        "status": "ok",
        "answer": explanation.get("answer", []),
        "markdown_path": str(md_path),
    }


def select_question_files(output_dir: Path, question_ids: list[str], limit: int | None) -> list[Path]:
    questions_dir = output_dir / "questions"
    if not questions_dir.exists():
        raise RuntimeError(f"questions 目录不存在: {questions_dir}")
    if question_ids:
        files = [questions_dir / f"q_{qid}.json" for qid in question_ids]
        missing = [str(p) for p in files if not p.exists()]
        if missing:
            raise RuntimeError("指定题号输出不存在: " + ", ".join(missing))
        return files
    files = sorted(questions_dir.glob("q_*.json"))
    if limit is not None and limit > 0:
        files = files[:limit]
    return files


def write_index(rows: list[dict[str, Any]], output_dir: Path) -> Path:
    path = output_dir / "explanations" / "index.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# 证据解析索引\n\n", f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"]
    lines.append("| 题号 | 状态 | 答案 | Markdown |\n")
    lines.append("|---|---|---|---|\n")
    for row in sorted(rows, key=lambda x: x.get("question_id", "")):
        qid = row.get("question_id", "")
        answer = ", ".join(row.get("answer", []) or [])
        md_path = row.get("markdown_path", "")
        rel = Path(md_path).name if md_path else ""
        link = f"[打开]({rel})" if rel else ""
        lines.append(f"| {qid} | {row.get('status', '')} | {answer} | {link} |\n")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate evidence-based Markdown explanations.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="blind_adjudication 输出目录")
    parser.add_argument("--question-id", action="append", default=[], help="指定题号，可重复传入")
    parser.add_argument("--limit", type=int, default=0, help="未指定题号时处理前 N 个 q_*.json；0 表示全部")
    parser.add_argument("--concurrency", type=int, default=5, help="并发数")
    parser.add_argument("--model", default="deepseek-v4-pro", help="模型名称")
    parser.add_argument("--write-back", action="store_true", help="把 generated_explanation 写回每题 JSON")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    files = select_question_files(output_dir, args.question_id, args.limit or None)
    api_key, base_url, env_name = get_llm_config()

    print(f"[input] output_dir={output_dir}")
    print(f"[input] questions={len(files)}")
    print(f"[api] 使用 {env_name} | base_url={base_url} | model={args.model}")

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        future_map = {
            executor.submit(process_file, path, output_dir, api_key, base_url, args.model, args.write_back): path
            for path in files
        }
        for i, future in enumerate(as_completed(future_map), start=1):
            path = future_map[future]
            try:
                row = future.result()
                rows.append(row)
                print(f"[{i}/{len(files)}] {row['question_id']} | ok | answer={','.join(row.get('answer', []))}")
            except Exception as exc:
                qid = path.stem.removeprefix("q_")
                row = {
                    "question_id": qid,
                    "status": "error",
                    "answer": [],
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
                rows.append(row)
                print(f"[{i}/{len(files)}] {qid} | ERROR: {str(exc)[:160]}")

    index_path = write_index(rows, output_dir)
    summary_path = output_dir / "explanations" / "generation_results.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"[output] index={index_path}")
    print(f"[output] summary={summary_path}")


if __name__ == "__main__":
    main()
