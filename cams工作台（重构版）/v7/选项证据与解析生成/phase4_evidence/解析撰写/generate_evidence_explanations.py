# -*- coding: utf-8 -*-
"""从正式盲判结果生成有据可查的 V3.1 教研解析母版（精简入口）。

V3 正文仅使用盲判证据。参考答案和原始参考解析单独加载并确定性地追加；
它们绝不进入生成 prompt，也绝不替代 ``predicted_answer``。

用法示例：
    python generate_evidence_explanations.py --output-dir ../output --question-id v7_q_000072
    python generate_evidence_explanations.py --output-dir ../output --limit 100 --concurrency 20 --write-back
"""

from __future__ import annotations

import argparse, json, sys, time, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

_PARENT = str(Path(__file__).resolve().parent.parent)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from openai import OpenAI

from 解析撰写.s1_explanation_data import (
    load_question_result, build_reference_context, load_standard_questions,
    load_reference_workbook, DEFAULT_QUESTIONS_PATH, DEFAULT_REFERENCE_WORKBOOK,
    DEFAULT_OUTPUT_DIR, get_llm_config,
)
from 解析撰写.s3_explanation_prompt import build_prompt
from 解析撰写.s4_explanation_normalize import normalize_explanation, parse_json_object
from 解析撰写.s6_explanation_output import (
    render_markdown, select_question_files, collect_generated_rows,
    write_index, write_chapter_drafts,
)
from 公共函数.llm_utils import call_llm


def process_file(
    path: Path, output_dir: Path, api_key: str, base_url: str, model: str,
    write_back: bool, standard_question: dict[str, Any], workbook_row: dict[str, Any],
    reasoning_effort: str = "high", enable_thinking: bool = True,
) -> dict[str, Any]:
    result = load_question_result(path)
    qid = result.get("question_id", path.stem.removeprefix("q_"))
    prompt = build_prompt(result, standard_question)
    client = OpenAI(api_key=api_key, base_url=base_url)
    raw = call_llm(client, prompt, model=model, reasoning_effort=reasoning_effort, enable_thinking=enable_thinking)
    parsed = parse_json_object(raw)
    if parsed is None:
        return {
            "question_id": qid, "status": "parse_failed", "answer": [],
            "chapter_mappings": result.get("chapter_mappings", []),
            "reference_conflict": False, "markdown_path": "",
            "deferral_reason": "LLM输出无法解析为JSON，请重跑",
        }
    reference = build_reference_context(qid, result.get("predicted_answer", []), standard_question, workbook_row)
    explanation = normalize_explanation(parsed, result, reference, model)

    deferral = explanation.get("deferral") if isinstance(explanation.get("deferral"), dict) else None
    is_deferred = bool(deferral and deferral.get("reason"))

    explanations_dir = output_dir / "explanations"
    explanations_dir.mkdir(parents=True, exist_ok=True)
    md_path = explanations_dir / f"{qid}.md"
    md_path.write_text(render_markdown(result, explanation, standard_question), encoding="utf-8")

    if write_back:
        result["generated_explanation"] = explanation
        result["generated_explanation_prompt"] = prompt
        result["generated_explanation_raw_output"] = raw
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    return {
        "question_id": qid, "status": "deferred" if is_deferred else "ok",
        "answer": explanation["answer"],
        "chapter_mappings": result.get("chapter_mappings", []),
        "reference_conflict": reference["cn_en_conflict"] or reference["blind_final_conflict"],
        "markdown_path": str(md_path),
        "deferral_reason": deferral.get("reason", "") if is_deferred else "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="从盲判结果生成有据可查的 V3.1 教研解析。")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--question-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--reasoning-effort", default="high", choices=["high", "max"])
    parser.add_argument("--no-thinking", action="store_true")
    parser.add_argument("--write-back", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--questions-path", default=str(DEFAULT_QUESTIONS_PATH))
    parser.add_argument("--reference-workbook", default=str(DEFAULT_REFERENCE_WORKBOOK))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    files = select_question_files(output_dir, args.question_id, args.limit or None, resume=args.resume)
    standard = load_standard_questions(args.questions_path)
    references = load_reference_workbook(args.reference_workbook)
    selected_qids = [path.stem.removeprefix("q_") for path in files]
    missing_standard = [qid for qid in selected_qids if qid not in standard]
    missing_reference = [qid for qid in selected_qids if qid not in references]
    if missing_standard or missing_reference:
        raise RuntimeError(f"生成前置校验失败: 标准题库缺失={missing_standard[:10]}，参考工作簿缺失={missing_reference[:10]}")

    api_key, base_url, env_name = get_llm_config()
    print(f"[input] output_dir={output_dir} | questions={len(files)}")
    print(f"[api] 使用 {env_name} | base_url={base_url} | model={args.model}")

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        future_map = {}
        for path in files:
            qid = path.stem.removeprefix("q_")
            future = executor.submit(process_file, path, output_dir, api_key, base_url,
                                     args.model, args.write_back, standard[qid], references[qid],
                                     args.reasoning_effort, not args.no_thinking)
            future_map[future] = path
        for i, future in enumerate(as_completed(future_map), start=1):
            path = future_map[future]
            try:
                row = future.result()
                rows.append(row)
                status = row.get('status', 'ok')
                print(f"[{i}/{len(files)}] {row['question_id']} | {status}")
            except Exception as exc:
                qid = path.stem.removeprefix("q_")
                rows.append({"question_id": qid, "status": "error", "answer": [], "error": str(exc), "traceback": traceback.format_exc()})
                print(f"[{i}/{len(files)}] {qid} | ERROR: {str(exc)[:160]}")

    cumulative_rows = collect_generated_rows(output_dir)
    index_path = write_index(cumulative_rows, output_dir)
    chapter_paths = write_chapter_drafts(cumulative_rows, output_dir)
    summary_path = output_dir / "explanations" / "generation_results.json"
    summary_path.write_text(json.dumps(cumulative_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[output] index={index_path}")
    print(f"[output] chapter_drafts={len(chapter_paths)}")
    print(f"[output] summary={summary_path}")


if __name__ == "__main__":
    main()