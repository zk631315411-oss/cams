# -*- coding: utf-8 -*-
"""Phase 4.1 — 小批量盲判脚本（Blind Adjudication）。
用法: python blind_adjudication.py --limit 10 --concurrency 10 --model deepseek-v4-pro
"""

from __future__ import annotations

import argparse, json, sys, time, traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np

from s1_indexing import (
    BM25, INDEX_PKL, KG_GRAPH_PATH, P5_ALIAS_INDEX_PATH, QUESTIONS_PATH,
    get_bge_model, get_llm_config, load_index, load_kg_graph,
    load_p5_alias_index, load_questions, load_chapter_mapping_index,
)
from s2_retrieval import search_and_merge, retrieve_option_supplements
from s4_llm import build_prompt, call_llm, parse_llm_output, normalize_llm_result, filter_llm_citations
from s5_validation import validate_result
from s6_output import write_question_json, write_summary_jsonl, write_markdown_report

HERE = Path(__file__).resolve().parent
PHASE4 = HERE.parent
OUTPUT_DIR = PHASE4 / "output"


def process_question(question, bge_vecs, card_ids, unit_lookup, bm25_zh_index,
                     bm25_en_index, api_key, base_url, model, top_k=20, merge_top_k=30,
                     kg_index=None, kg_max_extra=30, p5_index=None):
    """对一道题执行完整盲判流程。"""
    qid = question["question_id"]
    result = {"question_id": qid, "stem": question.get("stem",""), "options": question.get("options",{}),
              "question_type": question.get("question_type","single"), "tier": question.get("tier",""),
              "pipeline_status": "ok"}
    if question.get("_chapter_mappings") is not None: result["chapter_mappings"] = question.get("_chapter_mappings",[])
    if question.get("_question_text_override") is not None: result["question_text_override"] = question.get("_question_text_override",{})

    try:
        candidates = search_and_merge(question, bge_vecs=bge_vecs, card_ids=card_ids,
            unit_lookup=unit_lookup, bm25_zh_index=bm25_zh_index, bm25_en_index=bm25_en_index,
            top_k=top_k, merge_top_k=merge_top_k, kg_index=kg_index, kg_max_extra=kg_max_extra, p5_index=p5_index)
        result["candidate_pool"] = candidates
        result["candidate_route_counts"] = dict(Counter(c.get("route","unknown") for c in candidates))
        result["kg_enabled"] = kg_index is not None; result["p5_enabled"] = p5_index is not None

        supplement_pool = retrieve_option_supplements(question, bge_vecs=bge_vecs, card_ids=card_ids,
            unit_lookup=unit_lookup, bm25_zh_index=bm25_zh_index, bm25_en_index=bm25_en_index,
            excluded_unit_ids={r["unit_id"] for r in candidates}, top_k=top_k, per_option_limit=3)
        result["option_supplement_pool"] = supplement_pool
        result["option_supplement_counts"] = {l: len(rs) for l, rs in supplement_pool.items()}

        prompt = build_prompt(question, candidates, supplement_pool)
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        llm_output = call_llm(client, prompt, model=model, reasoning_effort="high")
        result["llm_output"] = llm_output

        parsed = parse_llm_output(llm_output)
        if parsed is None:
            result["pipeline_status"] = "llm_parse_failed"
            result["option_analysis"] = []; result["validation_checks"] = ["LLM 输出无法解析为 JSON"]
            result["predicted_answer"] = []; return result
        parsed = normalize_llm_result(parsed)

        allowed_unit_ids = {r["unit_id"] for r in candidates}
        allowed_unit_ids.update(row["unit_id"] for rows in supplement_pool.values() for row in rows)
        parsed, citation_drops = filter_llm_citations(parsed, allowed_unit_ids)
        result["citation_filter_drops"] = citation_drops

        # 确定性修复
        framework_ids = {str(uid) for uid in (parsed.get("decision_framework") or {}).get("cited_unit_ids",[]) or []}
        for opt in (parsed.get("option_analysis",[]) or []):
            cards = opt.get("evidence_cards",[])
            if not isinstance(cards, list): cards = []; opt["evidence_cards"] = cards
            # (a) evidence_status=negative 但没有 negative card
            if opt.get("evidence_status")=="negative" and not any(c.get("support_type")=="negative" for c in cards if isinstance(c,dict)):
                if cards:
                    for c in cards:
                        if isinstance(c,dict): c["support_type"] = "negative"; break
                else: opt["evidence_status"] = "none"
            # (b) decision_reason 提到但未绑定的 unit_id
            reason = str(opt.get("decision_reason","") or "")
            mentioned = set(re.findall(r"v7u_N\d+", reason))
            bound = {str(c.get("unit_id","")) for c in cards if isinstance(c,dict)}
            bound.update(framework_ids)
            for uid in sorted(mentioned - bound):
                if uid in allowed_unit_ids:
                    cards.append({"unit_id":uid,"support_type":"indirect","reason":"从 decision_reason 自动绑定"})
            # (c) 有 cards 但 evidence_status=none
            if cards and opt.get("evidence_status")=="none": opt["evidence_status"] = "indirect"

        result["option_analysis"] = parsed.get("option_analysis",[])
        result["predicted_answer"] = parsed.get("predicted_answer",[])
        result["decision_framework"] = parsed.get("decision_framework")
    except Exception as exc:
        result["pipeline_status"] = "llm_parse_failed"; result["option_analysis"] = []
        result["validation_checks"] = [f"处理异常: {str(exc)[:200]}"]
        result["predicted_answer"] = []; result["error_traceback"] = traceback.format_exc()
    return result


def main():
    parser = argparse.ArgumentParser(description="Phase 4.1 — 小批量盲判脚本")
    parser.add_argument("--limit", type=int, default=10); parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--model", type=str, default="deepseek-v4-pro")
    parser.add_argument("--top-k", type=int, default=20); parser.add_argument("--merge-top-k", type=int, default=30)
    parser.add_argument("--all", action="store_true"); parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--question-id", action="append", default=[])
    parser.add_argument("--chapter-map", type=str, default=""); parser.add_argument("--chapter-id", type=str, default="")
    parser.add_argument("--enable-kg", action="store_true"); parser.add_argument("--kg-graph-path", type=str, default=str(KG_GRAPH_PATH))
    parser.add_argument("--kg-max-extra", type=int, default=30)
    parser.add_argument("--enable-p5", action="store_true"); parser.add_argument("--p5-alias-path", type=str, default=str(P5_ALIAS_INDEX_PATH))
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR))
    args = parser.parse_args()

    if args.question_id and args.chapter_id: parser.error("--question-id 与 --chapter-id 不能同时使用")
    if args.chapter_id and not args.chapter_map: parser.error("使用 --chapter-id 时必须同时提供 --chapter-map")

    print("="*60); print("Phase 4.1 — 小批量盲判脚本"); print("="*60)
    print(f"limit={args.limit}, concurrency={args.concurrency}, model={args.model}")
    print(f"top_k={args.top_k}, merge_top_k={args.merge_top_k}\n")
    print(f"kg_enabled={args.enable_kg}, kg_max_extra={args.kg_max_extra}, kg_graph_path={args.kg_graph_path}\n")
    print(f"p5_enabled={args.enable_p5}, p5_alias_path={args.p5_alias_path}\n")

    questions = load_questions(QUESTIONS_PATH)
    index = load_index(INDEX_PKL)
    chapter_mapping_index = load_chapter_mapping_index(args.chapter_map) if args.chapter_map else {}
    if chapter_mapping_index:
        enriched = []
        for q in questions:
            row = chapter_mapping_index.get(q["question_id"])
            eq = dict(q); eq["_chapter_mappings"] = row.get("chapter_mappings",[]) if row else []
            enriched.append(eq)
        questions = enriched

    card_ids = index["card_ids"]; bge_vecs = index["bge_vecs"]; unit_lookup = index["unit_lookup"]
    bm25_zh = BM25(index["zh_bm25_docs"], index["zh_bm25_df"], index["zh_bm25_avgdl"])
    print(f"\n[bm25] 中文 BM25 就绪 | N={bm25_zh.N}, avgdl={bm25_zh.avgdl:.2f}")
    bm25_en = BM25(index["en_bm25_docs"], index["en_bm25_df"], index["en_bm25_avgdl"])
    print(f"[bm25] 英文 BM25 就绪 | N={bm25_en.N}, avgdl={bm25_en.avgdl:.2f}")
    print(); get_bge_model()

    kg_index = load_kg_graph(args.kg_graph_path) if args.enable_kg else None
    p5_index = load_p5_alias_index(args.p5_alias_path) if args.enable_p5 else None

    api_key, base_url, env_name = get_llm_config()
    print(f"\n[api] 使用 {env_name} | base_url={base_url}")

    if args.question_id:
        wanted = set(args.question_id)
        sampled = sorted([q for q in questions if q.get("question_id") in wanted], key=lambda x: x["question_id"])
        found = {q["question_id"] for q in sampled}
        missing = sorted(wanted - found)
        if missing: raise RuntimeError(f"指定题号不存在: {', '.join(missing)}")
        print(f"\n[sample] 指定题号 {len(sampled)} 题")
    elif args.chapter_id:
        cid = args.chapter_id.strip()
        sampled = sorted([q for q in questions if any(m.get("chapter_id")==cid.upper() or m.get("real_chapter")==cid for m in q.get("_chapter_mappings",[]) or [])], key=lambda x: x["question_id"])
        if not sampled: raise RuntimeError(f"章节 {cid} 没有已确认题目")
        print(f"\n[sample] 教材章节 {cid} 共 {len(sampled)} 题")
    elif args.all:
        sampled = sorted(questions, key=lambda x: x["question_id"])[:args.limit]
        print(f"\n[sample] 全部 {len(questions)} 题，取前 {len(sampled)} 题")
    else:
        manual_qs = sorted([q for q in questions if "manual_reviewed" in q.get("risk_flags",[])], key=lambda x: x["question_id"])
        sampled = manual_qs[:args.limit]
        print(f"\n[sample] manual_reviewed 共 {len(manual_qs)} 题，取前 {len(sampled)} 题")

    for q in sampled:
        print(f"  {q['question_id']} | {q.get('_chapter_mappings',[{}])[0].get('real_chapter','unmapped') if q.get('_chapter_mappings') else 'unmapped'} | {q.get('question_type','single')}")

    print(f"\n[run] 开始并发处理（{args.concurrency} 线程）...")
    results = []
    output_dir = Path(args.output_dir)
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {ex.submit(process_question, q, bge_vecs, card_ids, unit_lookup, bm25_zh, bm25_en, api_key, base_url, args.model, args.top_k, args.merge_top_k, kg_index, args.kg_max_extra, p5_index): q["question_id"] for q in sampled}
        for i, f in enumerate(as_completed(futures), 1):
            qid = futures[f]
            try:
                r = f.result(); results.append(r)
                status = r.get("pipeline_status","?")
                predicted = "、".join(str(x) for x in r.get("predicted_answer",[]) or [])
                issues = len(r.get("validation_checks",[]) or [])
                print(f"  [{i}/{len(sampled)}] {qid} | status={status} | candidates={len(r.get('candidate_pool',[]))} | predicted={predicted} | issues={issues}")
                write_question_json(r, output_dir)
            except Exception as exc:
                print(f"  [{i}/{len(sampled)}] {qid} | ERROR: {exc}")
                error_result = {"question_id": qid, "pipeline_status": "llm_parse_failed", "predicted_answer": [], "validation_checks": [f"处理异常: {str(exc)[:200]}"], "error_traceback": traceback.format_exc()}
                results.append(error_result)
                write_question_json(error_result, output_dir)

    write_summary_jsonl(results, output_dir)
    write_markdown_report(results, output_dir)

    status_counts = Counter(r.get("pipeline_status","?") for r in results)
    print("\n"+"="*60); print("盲判总览"); print("="*60)
    print(f"[stats] 状态分布: {dict(status_counts)}")
    print(f"[stats] 共处理 {len(results)} 题")
    print(f"  [OK] ok: {status_counts.get('ok',0)}")
    print(f"  [WARN] validation_failed: {status_counts.get('validation_failed',0)}")
    print(f"  [ERR] llm_parse_failed: {status_counts.get('llm_parse_failed',0)}")
    print(f"\n[output] JSONL 已写入: {output_dir / 'blind_judgment_results.jsonl'} ({len(results)} 题)")
    print(f"[output] Markdown 已写入: {output_dir / 'blind_judgment_report.md'}")
    print("\nDone.")


if __name__ == "__main__":
    import re  # needed for process_question's auto-fix
    main()
