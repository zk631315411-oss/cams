# -*- coding: utf-8 -*-
"""
Phase 4.0 — 检索质量验证脚本
==============================

从 clean tier 题目中按章节比例抽样，对每道题执行三路检索（BGE / bm25_zh / bm25_en），
输出 JSONL 候选记录 + Markdown 人读报告，用于人工验证检索质量。

用法:
    python retrieval_validation.py [--seed 42] [--limit 15]

依赖:
    pip install rank_bm25 scikit-learn numpy
"""

from __future__ import annotations

import argparse
import json
import math
import os
import pickle
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# ── 路径 ─────────────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent  # phase4_evidence/
PHASE4 = HERE
V7_ROOT = HERE.parent  # 选项证据与解析生成/
PROJECT_ROOT = HERE.parents[1]  # v7/

QUESTIONS_PATH = (
    V7_ROOT / "phase3.5_questions" / "output" / "v7_questions.json"
)
INDEX_PKL = (
    V7_ROOT
    / "phase3_index"
    / "output"
    / "index"
    / "v7_index_5614abb1c4bf.pkl"
)
OUTPUT_DIR = PHASE4 / "output"

# ── 分词器（与 phase3 build_index 一致） ──────────────────────────


def tokenize(text: str) -> list[str]:
    """与 v6 / phase3 一致的 tokenizer：英文按单词，中文按 2/3-gram 子串。

    与 phase3/build_index.py 中 tokenize() 完全一致。
    """
    text = (text or "").lower()
    tokens: list[str] = []
    # 英文/数字 token：连续字母数字，允许 _ - / .
    tokens.extend(re.findall(r"[a-z0-9][a-z0-9_\-/.]*", text))
    # 中文 token：CJK 字符的 2-gram 和 3-gram 子串
    cjk_runs = re.findall(r"[一-鿿]+", text)
    for run in cjk_runs:
        if len(run) == 1:
            tokens.append(run)
            continue
        for n in (2, 3):
            if len(run) >= n:
                tokens.extend(run[i: i + n] for i in range(len(run) - n + 1))
    return tokens


# ── BM25（手动实现，适配预分词 Counter 文档） ────────────────────────


class BM25:
    """Okapi BM25 实现，适配 phase3 已预分词的 Counter 文档。"""

    def __init__(
        self,
        docs: list[Counter],
        df: dict[str, int],
        avgdl: float,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        self.docs = docs
        self.df = df
        self.avgdl = avgdl
        self.k1 = k1
        self.b = b
        self.N = len(docs)
        self.doc_lens = [sum(doc.values()) for doc in docs]
        # 计算 idf 缓存
        self.idf_cache: dict[str, float] = {}

    def idf(self, term: str) -> float:
        if term not in self.idf_cache:
            n = self.df.get(term, 0)
            self.idf_cache[term] = math.log(
                (self.N - n + 0.5) / (n + 0.5) + 1.0
            )
        return self.idf_cache[term]

    def score(self, query_tokens: list[str], doc_idx: int) -> float:
        doc = self.docs[doc_idx]
        doc_len = self.doc_lens[doc_idx]
        score = 0.0
        qtf = Counter(query_tokens)
        for term, qf in qtf.items():
            tf = doc.get(term, 0)
            if tf == 0:
                continue
            idf_val = self.idf(term)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * doc_len / self.avgdl
            )
            score += idf_val * (numerator / denominator) * qf
        return score

    def search(self, query: str, top_k: int = 20) -> list[tuple[int, float]]:
        q_tokens = tokenize(query)
        if not q_tokens:
            return []
        scores = [(i, self.score(q_tokens, i)) for i in range(self.N)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ── 数据加载 ─────────────────────────────────────────────────────────


def load_index(pkl_path: str | Path) -> dict[str, Any]:
    """加载 phase3 索引 PKL 文件。"""
    print(f"[load] 读取索引: {pkl_path}")
    with open(pkl_path, "rb") as f:
        idx = pickle.load(f)
    print(
        f"[load] 索引加载完成 | card_ids={len(idx['card_ids'])}"
        f" | bge_vecs={idx['bge_vecs'].shape}"
        f" | unit_lookup={len(idx['unit_lookup'])}"
    )
    return idx


def load_questions(json_path: str | Path) -> list[dict[str, Any]]:
    """加载 v7 题库 JSON，返回 items 列表。"""
    print(f"[load] 读取题库: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data["items"]
    print(f"[load] 题库加载完成 | 共 {len(items)} 题")
    return items


# ── 抽样 ─────────────────────────────────────────────────────────────


def sample_questions(
    questions: list[dict[str, Any]],
    limit: int = 15,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """从 clean tier 按章节比例抽样，优先单选。

    章节比例: CH01=7, CH03=4, CH04=1, CH05=3
    """
    # 过滤 clean tier
    clean = [q for q in questions if q.get("tier") == "clean"]
    print(f"[sample] clean tier 共 {len(clean)} 题")

    # 每章按单选/多选分组
    chapter_pool: dict[str, dict[str, list[dict]]] = {}
    for q in clean:
        ch = q.get("chapter_code", "?")
        if ch not in chapter_pool:
            chapter_pool[ch] = {"single": [], "multiple": []}
        qt = q.get("question_type", "unknown")
        key = "single" if qt == "single" else "multiple"
        chapter_pool[ch][key].append(q)

    for ch, pools in chapter_pool.items():
        print(
            f"  {ch}: single={len(pools['single'])}, multiple={len(pools['multiple'])}"
        )

    # 目标各章节抽取数量（默认比例）
    default_target: dict[str, int] = {
        "CH01": 7,
        "CH03": 4,
        "CH04": 1,
        "CH05": 3,
    }
    total_default = sum(default_target.values())
    # 按 limit 缩放比例
    target: dict[str, int] = {}
    for ch, num in default_target.items():
        scaled = max(1, round(num * limit / total_default))
        target[ch] = scaled
    # 确保总和等于 limit（微调）
    while sum(target.values()) < limit:
        # 给比例损失最大的章节加 1
        deficits = {
            ch: (num * limit / total_default) - target[ch]
            for ch, num in default_target.items()
        }
        ch_to_bump = max(deficits, key=deficits.get)
        target[ch_to_bump] += 1
    while sum(target.values()) > limit:
        ch_to_cut = max(target, key=lambda ch: target[ch])
        if target[ch_to_cut] > 1:
            target[ch_to_cut] -= 1
        else:
            break

    rng = random.Random(seed)
    sampled: list[dict] = []

    for ch, num in target.items():
        pools = chapter_pool.get(ch, {})
        singles = pools.get("single", [])
        multiples = pools.get("multiple", [])

        # 优先从单选抽
        take_from_single = min(num, len(singles))
        take_from_multi = num - take_from_single

        chosen = []
        if take_from_single > 0:
            chosen.extend(rng.sample(singles, take_from_single))
        if take_from_multi > 0:
            chosen.extend(rng.sample(multiples, take_from_multi))

        # 如果该章可选数量不足，从另一类补
        if len(chosen) < num:
            deficit = num - len(chosen)
            other_type = "multiple" if take_from_single < len(singles) else "single"
            other_pool = pools.get(other_type, [])
            # 排除已选的
            remaining = [q for q in other_pool if q not in chosen]
            rng.shuffle(remaining)
            chosen.extend(remaining[:deficit])

        sampled.extend(chosen)
        print(
            f"[sample] {ch}: 抽取 {len(chosen)} 题"
            f" (single={sum(1 for q in chosen if q['question_type']=='single')},"
            f" multiple={sum(1 for q in chosen if q['question_type']!='single')})"
        )

    print(f"[sample] 共抽样 {len(sampled)} 题")
    return sampled


# ── 查询构建 ─────────────────────────────────────────────────────────


def build_queries(
    question: dict[str, Any],
) -> tuple[str, str | None]:
    """为一道题构建中文和英文查询。

    返回:
        query_zh: 中文查询 (stem + options)
        query_en: 英文查询 (stem_en + options_en)，若无 stem_en 则返回 None
    """
    stem = question.get("stem", "")
    options = question.get("options", {})
    opt_text = " ".join(options.values())
    query_zh = f"{stem} {opt_text}".strip()

    stem_en = question.get("stem_en", "")
    if not stem_en:
        return query_zh, None

    options_en = question.get("options_en", {})
    opt_en_text = " ".join(options_en.values())
    query_en = f"{stem_en} {opt_en_text}".strip()
    return query_zh, query_en


# ── BGE 模型（全局单例） ────────────────────────────────────────────

_BGE_MODEL: Any = None


def get_bge_model() -> Any:
    """延迟加载 BGE-M3 模型，全局复用。"""
    global _BGE_MODEL
    if _BGE_MODEL is not None:
        return _BGE_MODEL
    print("[bge] 加载 BGE-M3 编码模型 ...")
    from sentence_transformers import SentenceTransformer

    # 禁用自动联网转换检查
    import os
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    _BGE_MODEL = SentenceTransformer(
        "BAAI/bge-m3", local_files_only=True
    )
    dim = _BGE_MODEL.get_embedding_dimension()
    print(f"[bge] BGE-M3 就绪 | dim={dim}")
    return _BGE_MODEL


# ── 检索函数 ─────────────────────────────────────────────────────────


def bge_search(
    query: str,
    bge_vecs: np.ndarray,
    card_ids: list[str],
    unit_lookup: dict[str, dict],
    top_k: int = 20,
) -> list[dict[str, Any]]:
    """BGE-M3 余弦相似度检索。"""
    if not query.strip():
        return []

    model = get_bge_model()
    q_vec = model.encode([query], normalize_embeddings=True)
    sims = cosine_similarity(q_vec, bge_vecs)[0]

    # 取 top-k
    top_indices = np.argsort(sims)[::-1][:top_k]
    results = []
    for rank, idx in enumerate(top_indices, start=1):
        cid = card_ids[idx]
        unit = unit_lookup.get(cid, {})
        results.append(
            {
                "rank": rank,
                "score": round(float(sims[idx]), 6),
                "unit_id": cid,
                "knowledge_zh": unit.get("knowledge_zh", ""),
                "knowledge_en": unit.get("knowledge_en", ""),
                "en_quote": unit.get("en_quote", ""),
                "heading_context": unit.get("heading_context", []),
                "type": unit.get("type", ""),
                "terms": unit.get("terms", []),
            }
        )
    return results


def bm25_search(
    query: str,
    bm25_index: BM25,
    card_ids: list[str],
    unit_lookup: dict[str, dict],
    top_k: int = 20,
) -> list[dict[str, Any]]:
    """BM25 检索。"""
    if not query.strip():
        return []
    results = bm25_index.search(query, top_k=top_k)
    rows = []
    for rank, (doc_idx, score) in enumerate(results, start=1):
        cid = card_ids[doc_idx]
        unit = unit_lookup.get(cid, {})
        rows.append(
            {
                "rank": rank,
                "score": round(score, 6),
                "unit_id": cid,
                "knowledge_zh": unit.get("knowledge_zh", ""),
                "knowledge_en": unit.get("knowledge_en", ""),
                "en_quote": unit.get("en_quote", ""),
                "heading_context": unit.get("heading_context", []),
                "type": unit.get("type", ""),
                "terms": unit.get("terms", []),
            }
        )
    return rows


# ── 对一道题执行全部三路检索 ─────────────────────────────────────


def search_question(
    question: dict[str, Any],
    bge_vecs: np.ndarray,
    card_ids: list[str],
    unit_lookup: dict[str, dict],
    bm25_zh_index: BM25,
    bm25_en_index: BM25,
    top_k: int = 20,
) -> list[dict[str, Any]]:
    """对一道题执行三路检索，返回所有候选记录。"""
    qid = question["question_id"]
    query_zh, query_en = build_queries(question)
    all_records: list[dict] = []

    # 1. BGE 检索
    bge_results = bge_search(query_zh, bge_vecs, card_ids, unit_lookup, top_k)
    for r in bge_results:
        all_records.append(
            {
                "question_id": qid,
                "query_zh": query_zh,
                "query_en": query_en,
                "route": "bge",
                "no_en_query": query_en is None,
                **r,
            }
        )

    # 2. 中文 BM25
    bm25_zh_results = bm25_search(
        query_zh, bm25_zh_index, card_ids, unit_lookup, top_k
    )
    for r in bm25_zh_results:
        all_records.append(
            {
                "question_id": qid,
                "query_zh": query_zh,
                "query_en": query_en,
                "route": "bm25_zh",
                "no_en_query": query_en is None,
                **r,
            }
        )

    # 3. 英文 BM25（如有英文查询）
    if query_en:
        bm25_en_results = bm25_search(
            query_en, bm25_en_index, card_ids, unit_lookup, top_k
        )
        for r in bm25_en_results:
            all_records.append(
                {
                    "question_id": qid,
                    "query_zh": query_zh,
                    "query_en": query_en,
                    "route": "bm25_en",
                    "no_en_query": False,
                    **r,
                }
            )

    return all_records


# ── 输出 JSONL ───────────────────────────────────────────────────────


def write_jsonl(
    records: list[dict[str, Any]],
    path: str | Path,
) -> None:
    """写入 JSONL 文件。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[output] JSONL 已写入: {path} ({len(records)} 行)")


# ── 输出 Markdown 报告 ──────────────────────────────────────────────


def write_markdown(
    questions: list[dict[str, Any]],
    all_records: list[dict[str, Any]],
    output_path: str | Path,
) -> None:
    """生成人读 Markdown 报告。"""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 按 question_id 分组记录
    by_qid: dict[str, list[dict]] = {}
    for rec in all_records:
        by_qid.setdefault(rec["question_id"], []).append(rec)

    lines: list[str] = []
    lines.append("# Phase 4.0 — 检索质量验证报告\n")
    lines.append(
        f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    lines.append(
        f"抽样题数: {len(questions)}"
        f" | 总候选记录: {len(all_records)}\n"
    )
    lines.append("---\n")

    for q in questions:
        qid = q["question_id"]
        ch = q.get("chapter_code", "?")
        qtype = q.get("question_type", "?")
        tier = q.get("tier", "?")
        stem = q.get("stem", "")
        options = q.get("options", {})
        stem_en = q.get("stem_en", "")
        options_en = q.get("options_en", {})

        lines.append(f"\n## {qid} | {ch} | {qtype} | tier={tier}\n")
        lines.append(f"**中文题干**: {stem}\n")
        opt_lines = " ".join(
            f"{k}: {v}" for k, v in options.items()
        )
        lines.append(f"**中文选项**: {opt_lines}\n")

        if stem_en:
            lines.append(f"**英文题干**: {stem_en}\n")
            opt_en_lines = " ".join(
                f"{k}: {v}" for k, v in options_en.items()
            )
            lines.append(f"**英文选项**: {opt_en_lines}\n")
        else:
            lines.append("**英文题干**: （无）\n")

        records = by_qid.get(qid, [])

        for route_label, route_key in [
            ("BGE", "bge"),
            ("中文 BM25", "bm25_zh"),
            ("英文 BM25", "bm25_en"),
        ]:
            route_records = [
                r for r in records if r["route"] == route_key
            ]
            if not route_records:
                lines.append(f"\n### {route_label} 检索\n\n（无结果）\n")
                continue

            # 显示 top-5
            top5 = route_records[:5]
            lines.append(f"\n### {route_label} 检索 (top-5)\n")
            lines.append(
                "| rank | score | unit_id | knowledge_zh | type |\n"
            )
            lines.append(
                "|------|-------|---------|-------------|------|\n"
            )
            for r in top5:
                kzh = (r.get("knowledge_zh") or "")[:40]
                lines.append(
                    f"| {r['rank']} | {r['score']:.4f}"
                    f" | {r['unit_id']}"
                    f" | {kzh}"
                    f" | {r.get('type', '')} |\n"
                )

        lines.append("\n---\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"[output] Markdown 已写入: {output_path}")


# ── 主流程 ───────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 4.0 — 检索质量验证"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="随机种子（默认 42）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=15,
        help="抽样题数（默认 15）",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="每路检索 top-k（默认 20）",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Phase 4.0 — 检索质量验证")
    print("=" * 60)
    print(f"seed={args.seed}, limit={args.limit}, top_k={args.top_k}\n")

    # 1. 加载数据
    questions = load_questions(QUESTIONS_PATH)
    index = load_index(INDEX_PKL)

    card_ids: list[str] = index["card_ids"]
    bge_vecs: np.ndarray = index["bge_vecs"]
    unit_lookup: dict[str, dict] = index["unit_lookup"]
    zh_bm25_docs: list[Counter] = index["zh_bm25_docs"]
    zh_bm25_df: dict[str, int] = index["zh_bm25_df"]
    zh_bm25_avgdl: float = index["zh_bm25_avgdl"]
    en_bm25_docs: list[Counter] = index["en_bm25_docs"]
    en_bm25_df: dict[str, int] = index["en_bm25_df"]
    en_bm25_avgdl: float = index["en_bm25_avgdl"]

    # 2. 构建 BM25 索引
    print("\n[bm25] 构建中文 BM25 检索器 ...")
    bm25_zh = BM25(zh_bm25_docs, zh_bm25_df, zh_bm25_avgdl)
    print(f"[bm25] 中文 BM25 就绪 | N={bm25_zh.N}, avgdl={bm25_zh.avgdl:.2f}")

    print("[bm25] 构建英文 BM25 检索器 ...")
    bm25_en = BM25(en_bm25_docs, en_bm25_df, en_bm25_avgdl)
    print(f"[bm25] 英文 BM25 就绪 | N={bm25_en.N}, avgdl={bm25_en.avgdl:.2f}")

    # 3. 预加载 BGE 模型（全局单例）
    print()
    get_bge_model()

    # 4. 抽样
    print()
    sampled = sample_questions(questions, limit=args.limit, seed=args.seed)

    # 5. 对每道题检索
    all_records: list[dict] = []
    for i, q in enumerate(sampled, start=1):
        qid = q["question_id"]
        ch = q.get("chapter_code", "?")
        qt = q.get("question_type", "?")
        print(f"\n[{i}/{len(sampled)}] {qid} | {ch} | {qt}")

        records = search_question(
            q,
            bge_vecs=bge_vecs,
            card_ids=card_ids,
            unit_lookup=unit_lookup,
            bm25_zh_index=bm25_zh,
            bm25_en_index=bm25_en,
            top_k=args.top_k,
        )
        all_records.extend(records)
        print(f"  -> 候选 {len(records)} 条 (bge={args.top_k}, bm25_zh={args.top_k}, bm25_en={args.top_k})")

    # 6. 输出
    print("\n" + "=" * 60)
    print("输出结果")
    print("=" * 60)

    output_dir = Path(OUTPUT_DIR)
    jsonl_path = output_dir / "retrieval_validation.jsonl"
    md_path = output_dir / "retrieval_validation_report.md"

    write_jsonl(all_records, jsonl_path)
    write_markdown(sampled, all_records, md_path)

    # 统计
    routes = Counter(r["route"] for r in all_records)
    print(f"\n[stats] 各路由候选数: {dict(routes)}")
    print(f"[stats] 共 {len(all_records)} 条候选记录")
    print("\n完成。")


if __name__ == "__main__":
    import random
    main()
