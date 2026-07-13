# -*- coding: utf-8 -*-
"""B line intent-first blind adjudication experiment.

This runner reuses the production retrieval, LLM calling, parsing, and
validation helpers from phase4_evidence/scripts/blind_adjudication.py, but
replaces only the adjudication prompt. Reference answers are used only after
the blind run for comparison output.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PHASE4 = HERE.parents[1]
SCRIPTS_DIR = PHASE4 / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import blind_adjudication as base  # noqa: E402


PROMPT_VERSION = "intent_v1"
PROMPT_TEMPLATE = HERE / "prompt_intent_v1.md"
DEFAULT_OUTPUT_DIR = HERE / "output" / PROMPT_VERSION
DEFAULT_REFERENCE_SUMMARY = (
    PHASE4 / "output" / "总输出" / "q001_q050_ai_reference_audit_summary.csv"
)
DEFAULT_QUESTION_IDS = [
    "v7_q_000006",
    "v7_q_000009",
    "v7_q_000012",
    "v7_q_000026",
    "v7_q_000039",
    "v7_q_000001",
    "v7_q_000003",
    "v7_q_000016",
    "v7_q_000030",
    "v7_q_000045",
]


def load_prompt_template() -> str:
    return PROMPT_TEMPLATE.read_text(encoding="utf-8")


def build_intent_prompt(
    question: dict[str, Any],
    candidates: list[dict[str, Any]],
    template: str,
) -> str:
    stem = question.get("stem", "")
    options = question.get("options", {})
    qtype = question.get("question_type", "single")
    qtype_label = "单选题" if qtype == "single" else "多选题"
    opt_lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
    candidates_text = base.format_candidates(candidates)

    return (
        template.replace("{{STEM}}", stem)
        .replace("{{OPTIONS}}", opt_lines)
        .replace("{{QUESTION_TYPE}}", qtype_label)
        .replace("{{CANDIDATES}}", candidates_text)
    )


def normalize_intent_result(parsed: dict[str, Any]) -> dict[str, Any]:
    parsed = base.normalize_llm_result(parsed)
    parsed.setdefault("prompt_version", PROMPT_VERSION)
    parsed.setdefault("question_intent", {})
    parsed.setdefault("judgment_standard", {})
    parsed.setdefault("competing_option_analysis", [])
    parsed.setdefault("teacher_review_note", "")
    return parsed


def validate_intent_fields(result: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    intent = result.get("question_intent", {})
    standard = result.get("judgment_standard", {})
    competing = result.get("competing_option_analysis", [])
    predicted_answer = result.get("predicted_answer", [])
    option_analysis = result.get("option_analysis", [])
    options = result.get("options", {})

    if not isinstance(intent, dict) or not intent.get("intent_type"):
        issues.append("缺少 question_intent.intent_type")
    if not isinstance(standard, dict) or not standard.get("standard_type"):
        issues.append("缺少 judgment_standard.standard_type")
    if not isinstance(competing, list):
        issues.append("competing_option_analysis 不是数组")
    if not isinstance(predicted_answer, list) or not predicted_answer:
        issues.append("缺少 predicted_answer")
    else:
        option_keys = set(options.keys()) if isinstance(options, dict) else set()
        for answer in predicted_answer:
            if answer not in option_keys:
                issues.append(f"predicted_answer 包含非法选项: {answer}")

    correct_options: list[str] = []
    for opt in option_analysis:
        if isinstance(opt, dict) and not opt.get("intent_fit"):
            issues.append(f"选项{opt.get('option', '?')}: 缺少 intent_fit")
        if isinstance(opt, dict) and opt.get("judgement") == "correct":
            correct_options.append(str(opt.get("option", "")))

    if predicted_answer and correct_options:
        predicted_set = {str(x) for x in predicted_answer}
        correct_set = {x for x in correct_options if x}
        if predicted_set != correct_set:
            issues.append(
                "predicted_answer 与 option_analysis.correct 不一致: "
                f"predicted={sorted(predicted_set)}, correct={sorted(correct_set)}"
            )

    return issues


def process_question_intent(
    question: dict[str, Any],
    bge_vecs: Any,
    card_ids: list[str],
    unit_lookup: dict[str, dict],
    bm25_zh_index: Any,
    bm25_en_index: Any,
    api_key: str,
    base_url: str,
    model: str,
    prompt_template: str,
    top_k: int = 20,
    merge_top_k: int = 30,
    kg_index: dict[str, Any] | None = None,
    kg_max_extra: int = 30,
    p5_index: dict[str, Any] | None = None,
    max_tokens: int = 20000,
    store_prompt: bool = False,
) -> dict[str, Any]:
    qid = question["question_id"]
    result: dict[str, Any] = {
        "question_id": qid,
        "stem": question.get("stem", ""),
        "options": question.get("options", {}),
        "question_type": question.get("question_type", "single"),
        "tier": question.get("tier", ""),
        "prompt_version": PROMPT_VERSION,
        "pipeline_status": "ok",
    }

    try:
        candidates = base.search_and_merge(
            question,
            bge_vecs=bge_vecs,
            card_ids=card_ids,
            unit_lookup=unit_lookup,
            bm25_zh_index=bm25_zh_index,
            bm25_en_index=bm25_en_index,
            top_k=top_k,
            merge_top_k=merge_top_k,
            kg_index=kg_index,
            kg_max_extra=kg_max_extra,
            p5_index=p5_index,
        )
        result["candidate_pool"] = candidates
        result["candidate_route_counts"] = dict(
            Counter(c.get("route", "unknown") for c in candidates)
        )
        result["kg_enabled"] = kg_index is not None
        result["p5_enabled"] = p5_index is not None

        prompt = build_intent_prompt(question, candidates, prompt_template)
        if store_prompt:
            result["prompt"] = prompt

        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        llm_output = base.call_llm(
            client,
            prompt,
            model=model,
            max_tokens=max_tokens,
        )
        result["llm_output"] = llm_output

        parsed = base.parse_llm_output(llm_output)
        if parsed is None:
            result["pipeline_status"] = "llm_parse_failed"
            result["option_analysis"] = []
            result["predicted_answer"] = []
            result["question_intent"] = {}
            result["judgment_standard"] = {}
            result["competing_option_analysis"] = []
            result["teacher_review_note"] = ""
            result["validation_checks"] = ["LLM 输出无法解析为 JSON"]
            return result

        parsed = normalize_intent_result(parsed)
        result["option_analysis"] = parsed.get("option_analysis", [])
        result["predicted_answer"] = parsed.get("predicted_answer", [])
        result["question_intent"] = parsed.get("question_intent", {})
        result["judgment_standard"] = parsed.get("judgment_standard", {})
        result["competing_option_analysis"] = parsed.get(
            "competing_option_analysis", []
        )
        result["teacher_review_note"] = parsed.get("teacher_review_note", "")

        validation_issues = base.validate_result(result, candidates, unit_lookup)
        validation_issues.extend(validate_intent_fields(result))
        result["validation_checks"] = validation_issues
        if validation_issues:
            result["pipeline_status"] = "validation_failed"

    except Exception as exc:
        result["pipeline_status"] = "llm_parse_failed"
        result["option_analysis"] = []
        result["predicted_answer"] = []
        result["question_intent"] = {}
        result["judgment_standard"] = {}
        result["competing_option_analysis"] = []
        result["teacher_review_note"] = ""
        result["validation_checks"] = [f"处理异常: {str(exc)[:200]}"]
        result["error_traceback"] = traceback.format_exc()

    return result


def write_question_json(result: dict[str, Any], output_dir: Path) -> None:
    qid = result["question_id"]
    path = output_dir / "questions" / f"q_{qid}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


def write_results_jsonl(results: list[dict[str, Any]], output_dir: Path) -> None:
    path = output_dir / "intent_judgment_results.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in results:
            intent = r.get("question_intent", {}) or {}
            standard = r.get("judgment_standard", {}) or {}
            summary = {
                "question_id": r.get("question_id"),
                "prompt_version": r.get("prompt_version", PROMPT_VERSION),
                "pipeline_status": r.get("pipeline_status"),
                "predicted_answer": r.get("predicted_answer", []),
                "intent_type": intent.get("intent_type", ""),
                "standard_type": standard.get("standard_type", ""),
                "competing_option_analysis": r.get("competing_option_analysis", []),
                "teacher_review_note": r.get("teacher_review_note", ""),
                "validation_checks": r.get("validation_checks", []),
            }
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")


def format_competing(competing: Any) -> str:
    if not isinstance(competing, list) or not competing:
        return ""
    parts: list[str] = []
    for item in competing:
        if not isinstance(item, dict):
            continue
        options = item.get("options", [])
        if isinstance(options, list):
            opt_text = "/".join(str(x) for x in options)
        else:
            opt_text = str(options)
        winner = item.get("winner", "")
        dimension = item.get("decisive_dimension", "")
        review = item.get("needs_human_review", "")
        parts.append(f"{opt_text} -> {winner}; {dimension}; review={review}")
    return " | ".join(parts)


def write_report(results: list[dict[str, Any]], output_dir: Path) -> None:
    path = output_dir / "intent_judgment_report.md"
    lines: list[str] = []
    lines.append("# B线 intent_v1 盲判测试报告\n\n")
    lines.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    status_counts = Counter(r.get("pipeline_status", "?") for r in results)
    lines.append(f"总题数: {len(results)} | 状态分布: {dict(status_counts)}\n\n")
    lines.append("| 题号 | 状态 | 答案 | 意图 | 标准 | 双合理/竞争项 |\n")
    lines.append("|---|---|---|---|---|---|\n")
    for r in results:
        qid = r.get("question_id", "")
        predicted = "".join(r.get("predicted_answer", [])) or "(无)"
        intent = (r.get("question_intent", {}) or {}).get("intent_type", "")
        standard = (r.get("judgment_standard", {}) or {}).get("standard_type", "")
        competing = format_competing(r.get("competing_option_analysis", []))
        lines.append(
            f"| {qid} | {r.get('pipeline_status', '')} | {predicted} | "
            f"{intent} | {standard} | {competing} |\n"
        )

    for r in results:
        qid = r.get("question_id", "")
        lines.append(f"\n## {qid}\n\n")
        lines.append(f"题干: {r.get('stem', '')}\n\n")
        lines.append(f"预测答案: {''.join(r.get('predicted_answer', [])) or '(无)'}\n\n")

        intent = r.get("question_intent", {}) or {}
        standard = r.get("judgment_standard", {}) or {}
        lines.append("### 题干意图\n\n")
        lines.append(f"- intent_type: {intent.get('intent_type', '')}\n")
        lines.append(f"- asked_object: {intent.get('asked_object', '')}\n")
        lines.append(f"- key_constraint: {intent.get('key_constraint', '')}\n")
        lines.append(f"- intent_reasoning: {intent.get('intent_reasoning', '')}\n")

        lines.append("\n### 判断标准\n\n")
        lines.append(f"- standard_type: {standard.get('standard_type', '')}\n")
        lines.append(f"- standard_explanation: {standard.get('standard_explanation', '')}\n")
        lines.append(f"- decisive_rule: {standard.get('decisive_rule', '')}\n")

        competing = r.get("competing_option_analysis", [])
        if competing:
            lines.append("\n### 竞争选项分析\n\n")
            for item in competing:
                lines.append(f"- {json.dumps(item, ensure_ascii=False)}\n")

        lines.append("\n### 选项分析\n\n")
        lines.append("| 选项 | 判断 | 意图命中 | 证据状态 | 依据 |\n")
        lines.append("|---|---|---|---|---|\n")
        for opt in r.get("option_analysis", []):
            basis = str(opt.get("basis", "")).replace("\n", " ")
            lines.append(
                f"| {opt.get('option', '')} | {opt.get('judgement', '')} | "
                f"{opt.get('intent_fit', '')} | {opt.get('evidence_status', '')} | {basis} |\n"
            )

        teacher_note = r.get("teacher_review_note", "")
        if teacher_note:
            lines.append(f"\n### 教研复核提示\n\n{teacher_note}\n")

        checks = r.get("validation_checks", [])
        if checks:
            lines.append("\n### 校验问题\n\n")
            for issue in checks:
                lines.append(f"- {issue}\n")

    path.write_text("".join(lines), encoding="utf-8")


def load_reference_summary(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return {row["question_id"]: row for row in csv.DictReader(f)}


def answer_text(answer: Any) -> str:
    if isinstance(answer, list):
        return "".join(str(x) for x in answer)
    return str(answer or "")


def write_reference_comparison(
    results: list[dict[str, Any]],
    output_dir: Path,
    reference_summary_path: Path,
) -> None:
    refs = load_reference_summary(reference_summary_path)
    rows: list[dict[str, str]] = []
    for r in results:
        qid = r.get("question_id", "")
        ref = refs.get(qid, {})
        predicted = answer_text(r.get("predicted_answer", []))
        final_ref = ref.get("reference_answer_final_text", ref.get("ref_final", ""))
        baseline_ai = ref.get("ai_answer_text", ref.get("ai_answer", ""))
        intent = r.get("question_intent", {}) or {}
        standard = r.get("judgment_standard", {}) or {}
        rows.append(
            {
                "question_id": qid,
                "baseline_ai_answer": baseline_ai,
                "intent_ai_answer": predicted,
                "reference_final": final_ref,
                "intent_reference_conflict": str(bool(final_ref and predicted != final_ref)),
                "baseline_reference_conflict": ref.get("ai_reference_conflict", ""),
                "cn_en_answer_conflict": ref.get("cn_en_answer_conflict", ""),
                "pipeline_status": r.get("pipeline_status", ""),
                "intent_type": intent.get("intent_type", ""),
                "standard_type": standard.get("standard_type", ""),
                "competing_options": format_competing(
                    r.get("competing_option_analysis", [])
                ),
                "teacher_review_note": r.get("teacher_review_note", ""),
            }
        )

    csv_path = output_dir / "reference_comparison.csv"
    fieldnames = list(rows[0].keys()) if rows else []
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    md_path = output_dir / "reference_comparison.md"
    lines = ["# B线 intent_v1 后置参考对照\n\n"]
    lines.append("参考答案只用于跑后对照，未进入盲判 prompt。\n\n")
    lines.append(
        "| 题号 | baseline AI | intent_v1 AI | final参考 | intent冲突 | baseline冲突 | 中英冲突 | 意图 | 标准 |\n"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|\n")
    for row in rows:
        lines.append(
            f"| {row['question_id']} | {row['baseline_ai_answer']} | "
            f"{row['intent_ai_answer']} | {row['reference_final']} | "
            f"{row['intent_reference_conflict']} | {row['baseline_reference_conflict']} | "
            f"{row['cn_en_answer_conflict']} | {row['intent_type']} | "
            f"{row['standard_type']} |\n"
        )
    md_path.write_text("".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="B线 intent_v1 盲判测试")
    parser.add_argument(
        "--question-id",
        action="append",
        default=[],
        help="指定题号，可重复传入；默认跑 B 线测试题组",
    )
    parser.add_argument(
        "--first-n",
        type=int,
        default=0,
        help="按 question_id 顺序跑前 N 题；指定 question-id 时该参数无效",
    )
    parser.add_argument("--concurrency", type=int, default=5, help="并发数")
    parser.add_argument("--model", type=str, default="deepseek-v4-pro", help="模型名称")
    parser.add_argument("--top-k", type=int, default=20, help="每路检索 top-k")
    parser.add_argument("--merge-top-k", type=int, default=30, help="合并候选池大小")
    parser.add_argument("--kg-max-extra", type=int, default=30, help="KG 最大追加候选数")
    parser.add_argument("--disable-kg", action="store_true", help="关闭 KG 扩展")
    parser.add_argument("--disable-p5", action="store_true", help="关闭 P5 辅助")
    parser.add_argument("--max-tokens", type=int, default=20000, help="LLM 最大输出 token")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="输出目录",
    )
    parser.add_argument(
        "--reference-summary",
        type=str,
        default=str(DEFAULT_REFERENCE_SUMMARY),
        help="后置参考对照 summary CSV 路径",
    )
    parser.add_argument("--store-prompt", action="store_true", help="在每题 JSON 中保存 prompt")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.question_id:
        selection_desc = ", ".join(args.question_id)
    elif args.first_n:
        selection_desc = f"first_n={args.first_n}"
    else:
        selection_desc = ", ".join(DEFAULT_QUESTION_IDS)
    prompt_template = load_prompt_template()

    print("=" * 60)
    print("B线 intent_v1 盲判测试")
    print("=" * 60)
    print(f"model={args.model}, concurrency={args.concurrency}")
    print(f"top_k={args.top_k}, merge_top_k={args.merge_top_k}")
    print(f"kg_enabled={not args.disable_kg}, p5_enabled={not args.disable_p5}")
    print(f"output_dir={output_dir}")
    print(f"selection={selection_desc}")

    questions = base.load_questions(base.QUESTIONS_PATH)
    index = base.load_index(base.INDEX_PKL)

    card_ids: list[str] = index["card_ids"]
    bge_vecs = index["bge_vecs"]
    unit_lookup: dict[str, dict] = index["unit_lookup"]

    print("\n[bm25] 构建中文 BM25 检索器 ...")
    bm25_zh = base.BM25(
        index["zh_bm25_docs"], index["zh_bm25_df"], index["zh_bm25_avgdl"]
    )
    print("[bm25] 构建英文 BM25 检索器 ...")
    bm25_en = base.BM25(
        index["en_bm25_docs"], index["en_bm25_df"], index["en_bm25_avgdl"]
    )

    base.get_bge_model()
    kg_index = None if args.disable_kg else base.load_kg_graph(base.KG_GRAPH_PATH)
    p5_index = None if args.disable_p5 else base.load_p5_alias_index(base.P5_ALIAS_INDEX_PATH)
    api_key, base_url, env_name = base.get_llm_config()
    print(f"\n[api] 使用 {env_name} | base_url={base_url}")

    if args.question_id:
        question_ids = args.question_id
        wanted = set(question_ids)
        sampled = [q for q in questions if q.get("question_id") in wanted]
        sampled.sort(key=lambda x: x["question_id"])
        found = {q["question_id"] for q in sampled}
        missing = sorted(wanted - found)
        if missing:
            raise RuntimeError(f"指定题号不存在: {', '.join(missing)}")
    elif args.first_n:
        sampled = sorted(questions, key=lambda x: x["question_id"])[: args.first_n]
    else:
        wanted = set(DEFAULT_QUESTION_IDS)
        sampled = [q for q in questions if q.get("question_id") in wanted]
        sampled.sort(key=lambda x: x["question_id"])
        found = {q["question_id"] for q in sampled}
        missing = sorted(wanted - found)
        if missing:
            raise RuntimeError(f"默认题号不存在: {', '.join(missing)}")

    print(f"\n[sample] 共 {len(sampled)} 题")
    for q in sampled:
        print(f"  {q['question_id']} | {q.get('chapter_code', '?')} | {q.get('question_type', '?')}")

    results: list[dict[str, Any]] = []
    print(f"\n[run] 开始并发处理（{args.concurrency} 线程）...")
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        future_map = {
            executor.submit(
                process_question_intent,
                q,
                bge_vecs,
                card_ids,
                unit_lookup,
                bm25_zh,
                bm25_en,
                api_key,
                base_url,
                args.model,
                prompt_template,
                args.top_k,
                args.merge_top_k,
                kg_index,
                args.kg_max_extra,
                p5_index,
                args.max_tokens,
                args.store_prompt,
            ): q
            for q in sampled
        }

        for i, future in enumerate(as_completed(future_map), start=1):
            q = future_map[future]
            qid = q["question_id"]
            try:
                result = future.result()
            except Exception as exc:
                result = {
                    "question_id": qid,
                    "stem": q.get("stem", ""),
                    "options": q.get("options", {}),
                    "question_type": q.get("question_type", ""),
                    "prompt_version": PROMPT_VERSION,
                    "pipeline_status": "llm_parse_failed",
                    "candidate_pool": [],
                    "option_analysis": [],
                    "predicted_answer": [],
                    "question_intent": {},
                    "judgment_standard": {},
                    "competing_option_analysis": [],
                    "teacher_review_note": "",
                    "validation_checks": [f"线程异常: {str(exc)[:200]}"],
                    "error_traceback": traceback.format_exc(),
                }

            results.append(result)
            write_question_json(result, output_dir)

            intent = (result.get("question_intent", {}) or {}).get("intent_type", "?")
            standard = (result.get("judgment_standard", {}) or {}).get("standard_type", "?")
            predicted = answer_text(result.get("predicted_answer", [])) or "?"
            print(
                f"[{i}/{len(sampled)}] {qid} | status={result.get('pipeline_status')} "
                f"| predicted={predicted} | intent={intent} | standard={standard} "
                f"| issues={len(result.get('validation_checks', []))}"
            )

    results.sort(key=lambda x: x["question_id"])
    write_results_jsonl(results, output_dir)
    write_report(results, output_dir)
    write_reference_comparison(results, output_dir, Path(args.reference_summary))

    status_counts = Counter(r.get("pipeline_status", "?") for r in results)
    print("\n" + "=" * 60)
    print("输出完成")
    print("=" * 60)
    print(f"状态分布: {dict(status_counts)}")
    print(f"报告: {output_dir / 'intent_judgment_report.md'}")
    print(f"参考对照: {output_dir / 'reference_comparison.md'}")


if __name__ == "__main__":
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    main()
