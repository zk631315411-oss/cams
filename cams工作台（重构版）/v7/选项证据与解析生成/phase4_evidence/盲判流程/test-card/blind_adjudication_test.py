# -*- coding: utf-8 -*-
"""Phase 4.1 盲判测试 — 带 P7E 流程卡片上下文。

与主流程 blind_adjudication.py 的区别：
- 加载 P7C 流程卡片 + P7E 桥接关系
- BGE 匹配相关流程卡片，1-hop 邻居展开
- 流程上下文注入裁判 prompt（业务逻辑链路辅助）
- 输出到 output/test_flow/ 独立目录
- 支持 --no-flow / --dry-run-flow 开关

用法:
    python blind_adjudication_test.py --limit 10 --concurrency 5 --model deepseek-v4-pro
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import traceback
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# ── 导入路径设置 ───────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent          # test-card/
_PARENT = _HERE.parent                            # 盲判流程/
_PHASE4 = _PARENT.parent                          # phase4_evidence/
_PROJECT_ROOT = _PHASE4.parents[1]                # v7/

if str(_PHASE4) not in sys.path:
    sys.path.insert(0, str(_PHASE4))
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

# ── 公共模块 ───────────────────────────────────────────────────────────
from 公共函数.index import (
    BM25, INDEX_PKL, KG_GRAPH_PATH, P5_ALIAS_INDEX_PATH, QUESTIONS_PATH,
    get_bge_model, get_llm_config, load_index, load_kg_graph,
    load_p5_alias_index, load_questions, load_chapter_mapping_index,
    _load_kg_units,
)
from 公共函数.llm_utils import call_llm, parse_llm_output

# ── s1-s6 阶段模块 ─────────────────────────────────────────────────────
from s1_indexing import _section_context_cards
from s2_retrieval import (
    search_and_merge, retrieve_option_supplements,
    format_candidates, format_option_supplements,
)
from s4_llm import process_question as _process_question_base
from s6_output import write_question_json, write_summary_jsonl, write_markdown_report

# ── P7E 路径常量 ───────────────────────────────────────────────────────
P7C_CARDS_DIR = (
    _PROJECT_ROOT / "知识图谱提取" / "phases" / "phase07_procedural_layer"
    / "phases" / "P7C" / "outputs"
)
P7E_BRIDGES_PATH = (
    _PROJECT_ROOT / "知识图谱提取" / "phases" / "phase07_procedural_layer"
    / "phases" / "P7E" / "outputs" / "p7e_review_v9_merged" / "p7e_accepted_bridges.jsonl"
)
OUTPUT_DIR = _PHASE4 / "output" / "test_flow"

# ── P7E Flow 全局状态 ──────────────────────────────────────────────────

_FLOW_CARDS: dict[str, Any] = {}
_FLOW_BRIDGES: list[dict[str, Any]] = []
_FLOW_CARD_IDS: list[str] = []
_FLOW_CARD_VECS: Any = None  # np.ndarray | None
_FLOW_LOADED: bool = False


# ═════════════════════════════════════════════════════════════════════════
# P7E 流程卡片：加载 / 嵌入 / 上下文匹配
# ═════════════════════════════════════════════════════════════════════════

def _flow_load() -> list[str]:
    """加载 P7C 流程卡片和 P7E 桥接关系，返回卡片文本列表供 BGE 嵌入。"""
    global _FLOW_CARDS, _FLOW_BRIDGES, _FLOW_CARD_IDS, _FLOW_LOADED
    if _FLOW_LOADED:
        return []
    if P7C_CARDS_DIR.exists():
        for cf in sorted(P7C_CARDS_DIR.rglob("cards.raw.json")):
            if "_archived" in str(cf):
                continue
            try:
                payload = json.loads(cf.read_text(encoding="utf-8-sig"))
                for card in payload.get("cards") or []:
                    cid = card.get("card_id")
                    if cid:
                        _FLOW_CARDS[cid] = card
            except Exception:
                pass
    if P7E_BRIDGES_PATH.exists():
        with open(P7E_BRIDGES_PATH, "r", encoding="utf-8-sig") as f:
            for line in f:
                if line.strip():
                    _FLOW_BRIDGES.append(json.loads(line))
    _FLOW_CARD_IDS = []
    _card_texts = []
    for cid, card in sorted(_FLOW_CARDS.items()):
        title = card.get("title") or ""
        nodes = " ".join(n.get("label", "") for n in (card.get("flow_nodes") or []))
        _FLOW_CARD_IDS.append(cid)
        _card_texts.append(title + " " + nodes)
    _FLOW_LOADED = True
    return _card_texts


def _flow_build_embs(card_texts: list[str]) -> None:
    """为流程卡片文本构建 BGE 向量。"""
    global _FLOW_CARD_VECS
    if _FLOW_CARD_VECS is not None or not card_texts:
        return
    model = get_bge_model()
    _FLOW_CARD_VECS = model.encode(card_texts, normalize_embeddings=True, show_progress_bar=False)
    print(f"[flow] 卡片 BGE 向量构建完成 | cards={len(card_texts)} dim={_FLOW_CARD_VECS.shape[1]}")


def _flow_context(question: dict[str, Any], max_cards: int = 6, max_nbr: int = 4) -> str:
    """为题目匹配流程卡片上下文：每题 + 选项独立 BGE 匹配 → 合并 → 1-hop 桥接展开。"""
    if _FLOW_CARD_VECS is None or len(_FLOW_CARD_IDS) == 0:
        return ""

    stem = (question.get("stem") or "") + " " + (question.get("stem_en") or "")
    options = question.get("options", {}) or {}
    options_en = question.get("options_en", {}) or {}

    model = get_bge_model()
    queries = [stem.strip()]
    for label in sorted(options.keys()):
        opt_text = str(options.get(label, "")) + " " + str(options_en.get(label, ""))
        queries.append(opt_text.strip())
    q_vecs = model.encode(queries, normalize_embeddings=True)

    # 每题 + 选项独立匹配，取 max 相似度
    card_scores: dict[str, float] = {}
    for qv in q_vecs:
        sims = cosine_similarity(qv.reshape(1, -1), _FLOW_CARD_VECS)[0]
        for idx in np.argsort(sims)[::-1][:3]:
            sim = float(sims[idx])
            if sim < 0.4:
                continue
            cid = _FLOW_CARD_IDS[idx]
            if sim > card_scores.get(cid, -1.0):
                card_scores[cid] = sim

    scored: list[tuple[float, str, dict[str, Any]]] = []
    for cid, sim in sorted(card_scores.items(), key=lambda x: x[1], reverse=True):
        card = _FLOW_CARDS.get(cid)
        if card:
            scored.append((sim, cid, card))
        if len(scored) >= max_cards:
            break
    if not scored:
        return ""

    matched_ids = {cid for _, cid, _ in scored}

    # 桥接邻居
    outgoing: dict[str, list[str]] = {}
    incoming: dict[str, list[str]] = {}
    for b in _FLOW_BRIDGES:
        outgoing.setdefault(b["source_card_id"], []).append(b["target_card_id"])
        incoming.setdefault(b["target_card_id"], []).append(b["source_card_id"])

    nbr_ids: set[str] = set()
    for _, cid, _ in scored:
        for nid in outgoing.get(cid, []) + incoming.get(cid, []):
            if nid not in matched_ids:
                nbr_ids.add(nid)

    stem_sims = cosine_similarity(q_vecs[0:1], _FLOW_CARD_VECS)[0]
    nbr_scored: list[tuple[float, str]] = []
    for nid in nbr_ids:
        if nid in _FLOW_CARD_IDS:
            idx = _FLOW_CARD_IDS.index(nid)
            nbr_scored.append((float(stem_sims[idx]), nid))
    nbr_scored.sort(key=lambda x: x[0], reverse=True)
    nbr_kept = {nid for sim_val, nid in nbr_scored[:max_nbr] if sim_val > 0.3}

    all_ids = matched_ids | nbr_kept
    bridge_edges = [b for b in _FLOW_BRIDGES
                    if b["source_card_id"] in all_ids and b["target_card_id"] in all_ids]

    # 格式化输出
    lines: list[str] = ["### 业务流程上下文"]
    lines.append("以下流程卡片由各选项独立语义匹配后合并，展示了教材中与本题相关的业务逻辑链路。")
    lines.append("这些流程不直接作为选项判断的证据，但可帮助理解概念间的因果关系和流程位置。")
    lines.append("")

    for sim, cid, card in scored:
        sec = card.get("section_id", "?")
        title = card.get("title", "?") or "?"
        lines.append(f"**[{sec}] {title}** (相似度 {sim:.2f})")
        for n in (card.get("flow_nodes") or []):
            nt = n.get("node_type", "?")
            label = (n.get("label") or "?")[:150]
            lines.append(f"  [{nt}] {label}")
        out_edges = [b for b in bridge_edges if b["source_card_id"] == cid]
        for b in out_edges:
            tgt_card = _FLOW_CARDS.get(b["target_card_id"], {})
            tgt_node = next(
                (n for n in (tgt_card.get("flow_nodes") or [])
                 if n["node_id"] == b["target_node_id"]),
                {},
            )
            lines.append(
                f"  -> [{b['bridge_semantics']}] "
                f"[{tgt_card.get('section_id', '?')}] {tgt_node.get('label', '?')[:100]}"
            )
        lines.append("")

    if nbr_kept:
        lines.append("**桥接邻居:**")
        for nid in nbr_kept:
            card = _FLOW_CARDS.get(nid, {})
            lines.append(f"  [{card.get('section_id', '?')}] {card.get('title', '?')[:100]}")
        lines.append("")

    lines.append("")
    lines.append("**重要提示：以上流程板块仅展示业务逻辑关系，不直接作为选项判断的证据。**")
    return "\n".join(lines)

def process_question(
    question: dict[str, Any],
    bge_vecs: np.ndarray,
    card_ids: list[str],
    unit_lookup: dict[str, dict],
    bm25_zh_index: BM25,
    bm25_en_index: BM25,
    api_key: str,
    base_url: str,
    model: str,
    top_k: int = 20,
    merge_top_k: int = 30,
    kg_index: dict[str, Any] | None = None,
    kg_max_extra: int = 30,
    p5_index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """测试版流程包装：注入 P7E 流程上下文后调用公共 process_question。"""
    flow_context = _flow_context(question) if _FLOW_CARD_VECS is not None else ""
    return _process_question_base(
        question, bge_vecs, card_ids, unit_lookup, bm25_zh_index, bm25_en_index,
        api_key, base_url, model, top_k, merge_top_k, kg_index, kg_max_extra, p5_index,
        flow_context=flow_context,
    )


# ═════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4.1 — 盲判测试（含 P7E 流程卡片）")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--model", type=str, default="deepseek-v4-pro")
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--merge-top-k", type=int, default=30)
    parser.add_argument("--all", action="store_true",
                        help="处理全部题目（覆盖 manual_reviewed 默认筛选）")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--question-id", action="append", default=[])
    parser.add_argument("--chapter-map", type=str, default="")
    parser.add_argument("--chapter-id", type=str, default="")
    parser.add_argument("--enable-kg", action="store_true")
    parser.add_argument("--kg-graph-path", type=str, default=str(KG_GRAPH_PATH))
    parser.add_argument("--kg-max-extra", type=int, default=30)
    parser.add_argument("--enable-p5", action="store_true")
    parser.add_argument("--p5-alias-path", type=str, default=str(P5_ALIAS_INDEX_PATH))
    parser.add_argument("--no-flow", action="store_true", help="禁用流程卡片上下文")
    parser.add_argument("--dry-run-flow", action="store_true", help="仅打印流程上下文，不调用LLM")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR))
    args = parser.parse_args()

    if args.question_id and args.chapter_id:
        parser.error("--question-id 与 --chapter-id 不能同时使用")
    if args.chapter_id and not args.chapter_map:
        parser.error("使用 --chapter-id 时必须同时提供 --chapter-map")

    print("=" * 60)
    print("Phase 4.1 — 盲判测试（含 P7E 流程卡片）")
    print("=" * 60)
    print(f"limit={args.limit}, concurrency={args.concurrency}, model={args.model}")
    print(f"top_k={args.top_k}, merge_top_k={args.merge_top_k}")
    print(f"no_flow={args.no_flow}, dry_run_flow={args.dry_run_flow}")
    print(f"kg_enabled={args.enable_kg}, p5_enabled={args.enable_p5}\n")

    # 加载数据
    questions = load_questions(QUESTIONS_PATH)
    index = load_index(INDEX_PKL)
    chapter_mapping_index = (
        load_chapter_mapping_index(args.chapter_map) if args.chapter_map else {}
    )
    if chapter_mapping_index:
        enriched: list[dict[str, Any]] = []
        for question in questions:
            row = chapter_mapping_index.get(question["question_id"])
            enriched_q = dict(question)
            enriched_q["_chapter_mappings"] = (
                row.get("chapter_mappings", []) if row else []
            )
            enriched.append(enriched_q)
        questions = enriched

    card_ids: list[str] = index["card_ids"]
    bge_vecs: np.ndarray = index["bge_vecs"]
    unit_lookup: dict[str, dict] = index["unit_lookup"]
    zh_bm25_docs: list[Counter] = index["zh_bm25_docs"]
    zh_bm25_df: dict[str, int] = index["zh_bm25_df"]
    zh_bm25_avgdl: float = index["zh_bm25_avgdl"]
    en_bm25_docs: list[Counter] = index["en_bm25_docs"]
    en_bm25_df: dict[str, int] = index["en_bm25_df"]
    en_bm25_avgdl: float = index["en_bm25_avgdl"]

    # BM25
    bm25_zh = BM25(zh_bm25_docs, zh_bm25_df, zh_bm25_avgdl)
    print(f"\n[bm25] 中文 BM25 就绪 | N={bm25_zh.N}, avgdl={bm25_zh.avgdl:.2f}")
    bm25_en = BM25(en_bm25_docs, en_bm25_df, en_bm25_avgdl)
    print(f"[bm25] 英文 BM25 就绪 | N={bm25_en.N}, avgdl={bm25_en.avgdl:.2f}")

    print()
    get_bge_model()

    # 流程卡片
    card_texts = _flow_load()
    print(f"[flow] 流程卡片加载完成 | cards={len(_FLOW_CARDS)} bridges={len(_FLOW_BRIDGES)}")
    if card_texts and not args.no_flow:
        _flow_build_embs(card_texts)

    kg_index = load_kg_graph(args.kg_graph_path) if args.enable_kg else None
    p5_index = load_p5_alias_index(args.p5_alias_path) if args.enable_p5 else None

    api_key, base_url, env_name = get_llm_config()
    print(f"\n[api] 使用 {env_name} | base_url={base_url}")

    # 筛选题目
    if args.question_id:
        wanted = set(args.question_id)
        sampled = [q for q in questions if q.get("question_id") in wanted]
        sampled.sort(key=lambda x: x["question_id"])
        found = {q["question_id"] for q in sampled}
        missing = sorted(wanted - found)
        if missing:
            raise RuntimeError(f"指定题号不存在: {', '.join(missing)}")
        print(f"\n[sample] 指定题号 {len(sampled)} 题")
    elif args.chapter_id:
        chapter_id = args.chapter_id.strip()
        sampled = [
            q for q in questions
            if any(
                mapping.get("chapter_id") == chapter_id.upper()
                or mapping.get("real_chapter") == chapter_id
                or (isinstance(mapping.get("real_chapter"), list)
                    and chapter_id in mapping.get("real_chapter", []))
                for mapping in q.get("_chapter_mappings", []) or []
            )
        ]
        sampled.sort(key=lambda x: x["question_id"])
        if not sampled:
            raise RuntimeError(f"章节 {chapter_id} 没有已确认题目")
        print(f"\n[sample] 教材章节 {chapter_id} 共 {len(sampled)} 题")
    else:
        if args.all or args.limit != 10:
            sampled = sorted(questions, key=lambda x: x["question_id"])[:args.limit]
            print(f"\n[sample] 全部 {len(questions)} 题，取前 {len(sampled)} 题")
        else:
            manual_questions = [
                q for q in questions
                if "manual_reviewed" in q.get("risk_flags", [])
            ]
            manual_questions.sort(key=lambda x: x["question_id"])
            sampled = manual_questions[:args.limit]
            print(
                f"\n[sample] manual_reviewed 共 {len(manual_questions)} 题，"
                f"取前 {len(sampled)} 题"
            )

    for q in sampled:
        mapped = ",".join(
            row.get("real_chapter") or row.get("chapter_id", "")
            for row in q.get("_chapter_mappings", []) or []
        ) or "unmapped"
        print(f"  {q['question_id']} | {mapped} | {q.get('question_type', '?')}")

    # 跳过已有
    output_dir = Path(args.output_dir)
    if args.skip_existing:
        questions_dir = output_dir / "questions"
        before = len(sampled)
        sampled = [
            q for q in sampled
            if not (questions_dir / f"q_{q['question_id']}.json").exists()
        ]
        skipped = before - len(sampled)
        if skipped:
            print(f"\n[skip] 跳过已存在 {skipped} 题，剩余 {len(sampled)} 题")
    if not sampled:
        print("全部题目已处理完毕，无需运行。")
        return

    # 并发处理
    print(f"\n[run] 开始并发处理（{args.concurrency} 线程）...")
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []

    if args.dry_run_flow:
        print("\n=== DRY RUN FLOW（仅打印流程上下文，不调用 LLM） ===\n")
        for q in sampled:
            qid = q["question_id"]
            print(f"\n{'='*60}")
            print(f"题目: {qid}")
            print(f"题干: {q.get('stem', '')[:120]}")
            flow_text = _flow_context(q)
            if flow_text:
                print(flow_text)
            else:
                print("（无匹配的流程卡片）")
        print(f"\n[dry-run] 完成，共 {len(sampled)} 题")
        return

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        future_map = {
            executor.submit(
                process_question,
                q,
                bge_vecs,
                card_ids,
                unit_lookup,
                bm25_zh,
                bm25_en,
                api_key,
                base_url,
                args.model,
                args.top_k,
                args.merge_top_k,
                kg_index,
                args.kg_max_extra,
                p5_index,
            ): q
            for q in sampled
        }

        for i, future in enumerate(as_completed(future_map), start=1):
            q = future_map[future]
            qid = q["question_id"]
            try:
                result = future.result()
                results.append(result)

                status = result.get("pipeline_status", "?")
                n_issues = len(result.get("validation_checks", []))
                n_candidates = len(result.get("candidate_pool", []))
                predicted = result.get("predicted_answer", [])
                print(
                    f"[{i}/{len(sampled)}] {qid}"
                    f" | status={status}"
                    f" | candidates={n_candidates}"
                    f" | predicted={' '.join(predicted) if predicted else '?'}"
                    f" | issues={n_issues}"
                )
                write_question_json(result, output_dir)

            except Exception as exc:
                print(f"[{i}/{len(sampled)}] {qid} | ERROR: {str(exc)[:100]}")
                error_result: dict[str, Any] = {
                    "question_id": qid,
                    "stem": q.get("stem", ""),
                    "options": q.get("options", {}),
                    "question_type": q.get("question_type", ""),
                    "tier": q.get("tier", ""),
                    "pipeline_status": "llm_parse_failed",
                    "candidate_pool": [],
                    "option_supplement_pool": {},
                    "option_supplement_counts": {},
                    "option_analysis": [],
                    "validation_checks": [f"线程异常: {str(exc)[:200]}"],
                    "predicted_answer": [],
                    "chapter_mappings": q.get("_chapter_mappings", []),
                    "question_text_override": q.get("_question_text_override", {}),
                    "decision_framework": None,
                }
                results.append(error_result)
                write_question_json(error_result, output_dir)

    results.sort(key=lambda x: x["question_id"])

    # 输出汇总
    print("\n" + "=" * 60)
    print("输出汇总结果")
    print("=" * 60)

    write_summary_jsonl(results, output_dir)
    write_markdown_report(results, output_dir)

    status_counts = Counter(r.get("pipeline_status", "?") for r in results)
    print(f"\n[stats] 状态分布: {dict(status_counts)}")
    print(f"[stats] 共处理 {len(results)} 题")
    print(f"  [OK] ok: {status_counts.get('ok', 0)}")
    print(f"  [ERR] llm_parse_failed: {status_counts.get('llm_parse_failed', 0)}")
    print(f"\n[output] JSONL: {output_dir / 'blind_judgment_results.jsonl'}")
    print(f"[output] Markdown: {output_dir / 'blind_judgment_report.md'}")
    print("\nDone.")


if __name__ == "__main__":
    import os
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    main()
