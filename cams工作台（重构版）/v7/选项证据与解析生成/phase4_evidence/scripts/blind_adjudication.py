# -*- coding: utf-8 -*-
"""
Phase 4.1 — 小批量盲判脚本（Blind Adjudication）
================================================

从 manual_reviewed 标记的题目中抽样（默认前 10 题），对每道题执行：

  1. 3 路检索（BGE + BM25_zh + BM25_en），合并去重取 top-30 候选池
  2. 构建裁判 prompt（不含参考答案），调用 LLM 裁判
  3. 解析 LLM 响应并做机械校验 (validation checks)
  4. 输出每题详情 JSON + 汇总 JSONL + Markdown 报告

用法:
    python blind_adjudication.py --limit 10 --concurrency 10 --model deepseek-v4-pro

依赖:
    pip install openai rank_bm25 scikit-learn numpy
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
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# ── 路径 ───────────────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent
PHASE4 = HERE.parent  # phase4_evidence/
V7_ROOT = HERE.parents[1]  # v7/
PROJECT_ROOT = HERE.parents[2]  # cams工作台（重构版）

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
KG_GRAPH_PATH = (
    PROJECT_ROOT
    / "知识图谱提取"
    / "phases"
    / "phase06_kg_views"
    / "outputs"
    / "kg_retrieval_graph.json"
)
P5_ALIAS_INDEX_PATH = (
    PROJECT_ROOT
    / "知识图谱提取"
    / "phases"
    / "phase05_terms"
    / "outputs"
    / "p5c_alias_index.json"
)
OUTPUT_DIR = PHASE4 / "output"

API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


# ── Tokenizer（复用 P4.0 / phase3 实现） ──────────────────────────────


def tokenize(text: str) -> list[str]:
    """与 v6 / phase3 一致的 tokenizer：英文按单词，中文按 2/3-gram 子串。"""
    text = (text or "").lower()
    tokens: list[str] = []
    tokens.extend(re.findall(r"[a-z0-9][a-z0-9_\-/.]*", text))
    cjk_runs = re.findall(r"[\u4e00-\u9fff]+", text)
    for run in cjk_runs:
        if len(run) == 1:
            tokens.append(run)
            continue
        for n in (2, 3):
            if len(run) >= n:
                tokens.extend(run[i: i + n] for i in range(len(run) - n + 1))
    return tokens


# ── BM25（复用 P4.0 实现） ────────────────────────────────────────────


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


# ── 数据加载 ──────────────────────────────────────────────────────────


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


def _append_unique(bucket: list[str], value: str) -> None:
    """Append value while preserving insertion order and uniqueness."""
    if value and value not in bucket:
        bucket.append(value)


def load_kg_graph(json_path: str | Path) -> dict[str, Any]:
    """Load the P6 KG graph and build lightweight navigation indexes.

    KG is used only to expand candidate units from retrieval seed units. It does
    not replace evidence judgement, and it must not introduce unit ids outside
    the phase3 unit index.
    """
    json_path = Path(json_path)
    print(f"[kg] 读取 KG 母版: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        kg = json.load(f)

    cp_meta: dict[str, dict[str, Any]] = {}
    unit_meta: dict[str, dict[str, Any]] = {}
    cp_to_units: dict[str, list[str]] = defaultdict(list)
    unit_to_cps: dict[str, list[str]] = defaultdict(list)
    relation_edges_by_cp: dict[str, list[dict[str, Any]]] = defaultdict(list)
    section_to_cps: dict[str, list[str]] = defaultdict(list)

    for unit in kg.get("units", []):
        uid = unit.get("unit_id", "")
        if uid:
            unit_meta[uid] = unit

    for cp in kg.get("core_points", []):
        cp_id = cp.get("core_point_id", "")
        if not cp_id:
            continue
        cp_meta[cp_id] = cp
        section_id = cp.get("section_id", "")
        if section_id:
            _append_unique(section_to_cps[section_id], cp_id)
        for key in ("key_unit_ids", "anchor_unit_ids", "support_unit_ids"):
            for uid in cp.get(key, []) or []:
                _append_unique(cp_to_units[cp_id], uid)
                _append_unique(unit_to_cps[uid], cp_id)

    relation_scopes = {
        "same_section_core_point",
        "same_chapter_core_point",
        "cross_chapter_core_point",
    }
    for edge in kg.get("edges", []):
        scope = edge.get("edge_scope", "")
        source_id = edge.get("source_id", "")
        target_id = edge.get("target_id", "")
        if scope == "core_point_unit":
            _append_unique(cp_to_units[source_id], target_id)
            _append_unique(unit_to_cps[target_id], source_id)
        elif scope == "section_core_point":
            _append_unique(section_to_cps[source_id], target_id)
        elif scope in relation_scopes:
            relation_edges_by_cp[source_id].append(edge)
            relation_edges_by_cp[target_id].append(edge)

    def unit_sort_key(uid: str) -> tuple[str, int, str]:
        meta = unit_meta.get(uid, {})
        return (
            meta.get("chapter_id", ""),
            int(meta.get("unit_order") or 0),
            uid,
        )

    for cp_id, unit_ids in list(cp_to_units.items()):
        cp_to_units[cp_id] = sorted(unit_ids, key=unit_sort_key)

    print(
        "[kg] KG 导航索引就绪"
        f" | chapters={len(kg.get('chapters', []))}"
        f" | core_points={len(cp_meta)}"
        f" | units={len(unit_meta)}"
        f" | edges={len(kg.get('edges', []))}"
    )
    return {
        "raw": kg,
        "cp_meta": cp_meta,
        "unit_meta": unit_meta,
        "cp_to_units": dict(cp_to_units),
        "unit_to_cps": dict(unit_to_cps),
        "relation_edges_by_cp": dict(relation_edges_by_cp),
        "section_to_cps": dict(section_to_cps),
    }


def _normalize_term(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _term_in_query(term: str, query: str) -> bool:
    """Match P5 terms conservatively; short Latin aliases need word bounds."""
    term = _normalize_term(term)
    query = _normalize_term(query)
    if not term or not query:
        return False
    if re.fullmatch(r"[a-z0-9][a-z0-9_\-/. ]*", term):
        escaped = re.escape(term).replace(r"\ ", r"\s+")
        return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", query) is not None
    return term in query


def load_p5_alias_index(json_path: str | Path) -> dict[str, Any]:
    """Load P5C alias groups as an external retrieval helper."""
    json_path = Path(json_path)
    print(f"[p5] 读取 P5 术语索引: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    aliases: list[dict[str, Any]] = []
    for group in data.get("alias_groups", []) or []:
        terms: list[str] = []
        for key in ("canonical_en", "canonical_zh"):
            value = group.get(key, "")
            if value:
                terms.append(value)
        for key in ("aliases_en", "aliases_zh", "all_terms"):
            terms.extend(group.get(key, []) or [])
        normalized_terms = sorted(
            {_normalize_term(t) for t in terms if len(_normalize_term(t)) >= 2},
            key=len,
            reverse=True,
        )
        unit_ids = [uid for uid in group.get("evidence_unit_ids", []) or [] if uid]
        if normalized_terms and unit_ids:
            aliases.append(
                {
                    "alias_group_id": group.get("alias_group_id", ""),
                    "canonical_en": group.get("canonical_en", ""),
                    "canonical_zh": group.get("canonical_zh", ""),
                    "terms": normalized_terms,
                    "unit_ids": unit_ids,
                    "alias_scope": group.get("alias_scope", ""),
                }
            )

    print(f"[p5] P5 术语索引就绪 | alias_groups={len(aliases)}")
    return {"aliases": aliases, "raw": data}


# ── API 配置 ──────────────────────────────────────────────────────────


def get_llm_config() -> tuple[str, str, str]:
    """获取 LLM API 配置：api_key, base_url, env_name。"""
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


# ── 查询构建 ──────────────────────────────────────────────────────────


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


# ── BGE 模型（全局单例） ─────────────────────────────────────────────

_BGE_MODEL: Any = None


def get_bge_model() -> Any:
    """延迟加载 BGE-M3 模型，全局复用。"""
    global _BGE_MODEL
    if _BGE_MODEL is not None:
        return _BGE_MODEL
    print("[bge] 加载 BGE-M3 编码模型 ...")
    from sentence_transformers import SentenceTransformer

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    _BGE_MODEL = SentenceTransformer(
        "BAAI/bge-m3", local_files_only=True
    )
    dim = _BGE_MODEL.get_embedding_dimension()
    print(f"[bge] BGE-M3 就绪 | dim={dim}")
    return _BGE_MODEL


# ── 检索函数 ──────────────────────────────────────────────────────────


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
            }
        )
    return rows


def _candidate_from_unit(
    unit_id: str,
    unit_lookup: dict[str, dict],
    route: str,
    score: float,
    kg_info: dict[str, Any],
) -> dict[str, Any] | None:
    unit = unit_lookup.get(unit_id)
    if not unit:
        return None
    return {
        "unit_id": unit_id,
        "knowledge_zh": unit.get("knowledge_zh", ""),
        "en_quote": unit.get("en_quote", ""),
        "knowledge_en": unit.get("knowledge_en", ""),
        "heading_context": unit.get("heading_context", []),
        "type": unit.get("type", ""),
        "route": route,
        "score": round(score, 6),
        "kg": kg_info,
    }


def _relation_route(edge_scope: str) -> str:
    if edge_scope == "same_section_core_point":
        return "kg_same_section_cp"
    if edge_scope == "same_chapter_core_point":
        return "kg_same_chapter_cp"
    if edge_scope == "cross_chapter_core_point":
        return "kg_cross_chapter_cp"
    return "kg_related_cp"


def _normalize_route_scores(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize scores inside a route so heterogeneous retrievers can merge."""
    if not records:
        return []
    scores = [float(r.get("score") or 0.0) for r in records]
    min_score = min(scores)
    max_score = max(scores)
    out: list[dict[str, Any]] = []
    for r in records:
        rank = int(r.get("rank") or 0)
        if max_score > min_score:
            norm = (float(r.get("score") or 0.0) - min_score) / (max_score - min_score)
        else:
            norm = 1.0 if float(r.get("score") or 0.0) > 0 else 0.0
        rank_boost = 1.0 / (rank + 1.0) if rank else 0.0
        row = dict(r)
        row["raw_score"] = round(float(r.get("score") or 0.0), 6)
        row["score"] = round((0.85 * norm) + (0.15 * rank_boost), 6)
        out.append(row)
    return out


def p5_alias_search(
    query_zh: str,
    query_en: str | None,
    p5_index: dict[str, Any] | None,
    unit_lookup: dict[str, dict],
    top_k: int = 12,
) -> list[dict[str, Any]]:
    """Use P5 alias groups as external term-to-unit recall."""
    if not p5_index or top_k <= 0:
        return []
    haystack = _normalize_term(f"{query_zh} {query_en or ''}")
    matched: list[dict[str, Any]] = []
    for group in p5_index.get("aliases", []) or []:
        hit_terms = [
            term for term in group.get("terms", [])
            if term and _term_in_query(term, haystack)
        ]
        if not hit_terms:
            continue
        best_term = max(hit_terms, key=len)
        matched.append({"group": group, "term": best_term, "score": len(best_term)})
    matched.sort(key=lambda x: x["score"], reverse=True)

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in matched[:8]:
        group = match["group"]
        for uid in group.get("unit_ids", [])[:5]:
            if uid in seen or uid not in unit_lookup:
                continue
            unit = unit_lookup[uid]
            seen.add(uid)
            rows.append(
                {
                    "rank": len(rows) + 1,
                    "score": round(0.45 + min(match["score"], 40) / 200.0, 6),
                    "raw_score": match["score"],
                    "unit_id": uid,
                    "knowledge_zh": unit.get("knowledge_zh", ""),
                    "knowledge_en": unit.get("knowledge_en", ""),
                    "en_quote": unit.get("en_quote", ""),
                    "heading_context": unit.get("heading_context", []),
                    "type": unit.get("type", ""),
                    "route": "p5_alias",
                    "p5": {
                        "alias_group_id": group.get("alias_group_id", ""),
                        "canonical_en": group.get("canonical_en", ""),
                        "canonical_zh": group.get("canonical_zh", ""),
                        "matched_term": match["term"],
                        "alias_scope": group.get("alias_scope", ""),
                    },
                }
            )
            if len(rows) >= top_k:
                return rows
    return rows


def expand_with_kg(
    direct_candidates: list[dict[str, Any]],
    kg_index: dict[str, Any] | None,
    unit_lookup: dict[str, dict],
    query_zh: str = "",
    query_en: str | None = None,
    max_extra: int = 30,
    seed_limit: int = 12,
    per_seed_limit: int = 3,
) -> list[dict[str, Any]]:
    """Expand retrieved seed units through KG core-point neighborhoods."""
    if not kg_index or max_extra <= 0:
        return []

    cp_to_units: dict[str, list[str]] = kg_index["cp_to_units"]
    unit_to_cps: dict[str, list[str]] = kg_index["unit_to_cps"]
    cp_meta: dict[str, dict[str, Any]] = kg_index["cp_meta"]
    relation_edges_by_cp: dict[str, list[dict[str, Any]]] = kg_index[
        "relation_edges_by_cp"
    ]

    query_tokens = set(tokenize(f"{query_zh} {query_en or ''}"))
    existing = {c["unit_id"] for c in direct_candidates}
    proposed: dict[str, dict[str, Any]] = {}

    route_weight = {
        "kg_same_core_point": 1.0,
        "kg_same_section_cp": 0.86,
        "kg_same_chapter_cp": 0.72,
        "kg_cross_chapter_cp": 0.62,
        "kg_related_cp": 0.55,
    }

    def text_relevance(unit: dict[str, Any]) -> float:
        tokens = set(
            tokenize(
                " ".join(
                    [
                        unit.get("knowledge_zh", ""),
                        unit.get("knowledge_en", ""),
                        unit.get("en_quote", ""),
                        " ".join(unit.get("heading_context", []) or []),
                    ]
                )
            )
        )
        if not query_tokens or not tokens:
            return 0.0
        overlap = len(query_tokens & tokens)
        return min(overlap / max(len(query_tokens), 1), 1.0)

    def add_unit(
        uid: str,
        route: str,
        seed: dict[str, Any],
        source_cp_id: str,
        target_cp_id: str,
        edge: dict[str, Any] | None = None,
    ) -> None:
        if uid in existing or uid == seed["unit_id"]:
            return
        unit = unit_lookup.get(uid)
        if not unit:
            return
        target_cp = cp_meta.get(target_cp_id, {})
        source_cp = cp_meta.get(source_cp_id, {})
        seed_score = float(seed.get("score") or 0.0)
        relevance = text_relevance(unit)
        kg_info = {
            "source_seed_unit_id": seed["unit_id"],
            "source_core_point_id": source_cp_id,
            "source_core_point_title_zh": source_cp.get("title_zh", ""),
            "target_core_point_id": target_cp_id,
            "target_core_point_title_zh": target_cp.get("title_zh", ""),
            "text_relevance": round(relevance, 6),
        }
        if edge:
            kg_info.update(
                {
                    "edge_id": edge.get("edge_id", ""),
                    "edge_scope": edge.get("edge_scope", ""),
                    "relation_type": edge.get("relation_type", ""),
                    "reason": edge.get("reason", ""),
                }
            )
        score = (
            seed_score * 0.48
            + route_weight.get(route, 0.55) * 0.32
            + relevance * 0.20
        )
        candidate = _candidate_from_unit(uid, unit_lookup, route, score, kg_info)
        if candidate:
            candidate["kg"]["seed_score"] = round(seed_score, 6)
            existing_candidate = proposed.get(uid)
            if not existing_candidate or candidate["score"] > existing_candidate["score"]:
                proposed[uid] = candidate

    seed_candidates = [
        c for c in direct_candidates
        if c.get("route") in {"bge", "bm25_zh", "bm25_en"}
    ]
    if len(seed_candidates) < seed_limit:
        seed_candidates.extend(
            c for c in direct_candidates
            if c.get("route") not in {"bge", "bm25_zh", "bm25_en"}
        )

    for seed in seed_candidates[:seed_limit]:
        seed_added_before = len(proposed)
        seed_uid = seed["unit_id"]
        for cp_id in unit_to_cps.get(seed_uid, [])[:3]:
            # First: siblings inside the same core point.
            for uid in cp_to_units.get(cp_id, [])[:10]:
                add_unit(uid, "kg_same_core_point", seed, cp_id, cp_id)
                if len(proposed) - seed_added_before >= per_seed_limit:
                    break
            if len(proposed) - seed_added_before >= per_seed_limit:
                break

            # Then: units attached to related core points.
            for edge in relation_edges_by_cp.get(cp_id, [])[:6]:
                other_cp_id = (
                    edge.get("target_id")
                    if edge.get("source_id") == cp_id
                    else edge.get("source_id")
                )
                route = _relation_route(edge.get("edge_scope", ""))
                for uid in cp_to_units.get(other_cp_id, [])[:4]:
                    add_unit(uid, route, seed, cp_id, other_cp_id, edge=edge)
                    if len(proposed) - seed_added_before >= per_seed_limit:
                        break
                if len(proposed) - seed_added_before >= per_seed_limit:
                    break

    extras = list(proposed.values())
    extras.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return extras[:max_extra]


# ── 对一道题执行三路检索并合并去重 ────────────────────────────────────


def search_and_merge(
    question: dict[str, Any],
    bge_vecs: np.ndarray,
    card_ids: list[str],
    unit_lookup: dict[str, dict],
    bm25_zh_index: BM25,
    bm25_en_index: BM25,
    top_k: int = 20,
    merge_top_k: int = 30,
    kg_index: dict[str, Any] | None = None,
    kg_max_extra: int = 30,
    p5_index: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """3 路检索 -> 合并去重 -> KG 可选扩展。

    返回的每条记录包含: unit_id, knowledge_zh, en_quote, knowledge_en,
    heading_context, type, route, score。
    """
    query_zh, query_en = build_queries(question)

    # 1. BGE 检索（中英混合查询）
    query_bge = query_zh
    if query_en:
        query_bge = query_zh + " " + query_en
    bge_results = _normalize_route_scores(
        bge_search(query_bge, bge_vecs, card_ids, unit_lookup, top_k)
    )
    route_map: dict[str, list[dict]] = {}
    for r in bge_results:
        r["route"] = "bge"
        route_map.setdefault(r["unit_id"], []).append(r)

    # 2. 中文 BM25
    bm25_zh_results = _normalize_route_scores(
        bm25_search(query_zh, bm25_zh_index, card_ids, unit_lookup, top_k)
    )
    for r in bm25_zh_results:
        r["route"] = "bm25_zh"
        route_map.setdefault(r["unit_id"], []).append(r)

    # 3. 英文 BM25（如有英文查询）
    if query_en:
        bm25_en_results = _normalize_route_scores(
            bm25_search(query_en, bm25_en_index, card_ids, unit_lookup, top_k)
        )
        for r in bm25_en_results:
            r["route"] = "bm25_en"
            route_map.setdefault(r["unit_id"], []).append(r)

    # 4. P5 术语/别名索引（外部检索辅助，不作为 KG 边）
    p5_results = p5_alias_search(query_zh, query_en, p5_index, unit_lookup, top_k=12)
    for r in p5_results:
        route_map.setdefault(r["unit_id"], []).append(r)

    # 合并去重：取每条 unit_id 下的最高分
    merged: list[dict[str, Any]] = []
    for uid, records in route_map.items():
        best = max(records, key=lambda x: x["score"])
        merged.append(
            {
                "unit_id": uid,
                "knowledge_zh": best.get("knowledge_zh", ""),
                "en_quote": best.get("en_quote", ""),
                "knowledge_en": best.get("knowledge_en", ""),
                "heading_context": best.get("heading_context", []),
                "type": best.get("type", ""),
                "route": best["route"],
                "score": best["score"],
                "raw_score": best.get("raw_score", best.get("score", 0.0)),
            }
        )
        if best.get("p5"):
            merged[-1]["p5"] = best["p5"]

    # 按 score 降序，取 top-merge_top_k
    merged.sort(key=lambda x: x["score"], reverse=True)
    direct_candidates = merged[:merge_top_k]

    kg_candidates = expand_with_kg(
        direct_candidates,
        kg_index=kg_index,
        unit_lookup=unit_lookup,
        query_zh=query_zh,
        query_en=query_en,
        max_extra=kg_max_extra,
    )
    return direct_candidates + kg_candidates


# ── 构建裁判 prompt ───────────────────────────────────────────────────


def format_candidates(candidates: list[dict[str, Any]]) -> str:
    """将候选池格式化为易读文本。"""
    lines: list[str] = []
    for i, c in enumerate(candidates, start=1):
        zh = c.get("knowledge_zh", "")
        en = c.get("en_quote", "") or c.get("knowledge_en", "")
        lines.append(f"[知识单元 {i}]")
        lines.append(f"  unit_id: {c['unit_id']}")
        if zh:
            lines.append(f"  中文: {zh}")
        if en:
            lines.append(f"  英文: {en}")
        kg_info = c.get("kg") or {}
        if kg_info:
            lines.append(
                "  KG导航: "
                f"route={c.get('route', '')}; "
                f"seed={kg_info.get('source_seed_unit_id', '')}; "
                f"target_cp={kg_info.get('target_core_point_id', '')}; "
                f"target_cp_title={kg_info.get('target_core_point_title_zh', '')}; "
                f"relation={kg_info.get('relation_type', '')}"
            )
        lines.append("  " + "-" * 60)
    return "\n".join(lines)


def build_prompt(question: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    """构建裁判 prompt，不包含参考答案。"""
    stem = question.get("stem", "")
    options = question.get("options", {})
    qtype = question.get("question_type", "single")
    qtype_label = "单选题" if qtype == "single" else "多选题"

    opt_lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
    candidates_text = format_candidates(candidates)

    prompt = f"""你是一个 CAMS 反洗钱考试题目裁判。你需要判断每道题的每个选项是否正确。

### 题目信息
题干: {stem}
选项:
{opt_lines}
题型: {qtype_label}

### 教材证据
以下是教材中与本题相关的知识单元（候选池），请基于这些单元判断每个选项：
其中 `KG导航` 只表示该单元与检索命中的单元在教材知识图谱中同属或相邻；它不是答案依据。最终判断必须回到知识单元的中英文原文。

{candidates_text}

### 输出要求
以 JSON 格式输出，不要包含其他内容：
- `evidence_status=direct` 表示教材直接支持该选项；`indirect` 表示只能间接支持；`negative` 表示教材证据反驳该选项；`none` 表示没有可引用证据，且 evidence_cards 必须为空。
{{
  "predicted_answer": ["A"],
  "option_analysis": [
    {{
      "option": "A",
      "judgement": "correct|incorrect|insufficient",
      "evidence_status": "direct|indirect|negative|none",
      "evidence_cards": [
        {{"unit_id": "v7u_N000001", "support_type": "direct|indirect|negative", "reason": "为什么这个单元支持或反驳该选项"}}
      ]
    }}
  ]
}}"""
    return prompt


# ── LLM 调用 ──────────────────────────────────────────────────────────


def call_llm(
    client: Any,
    prompt: str,
    model: str = "deepseek-v4-pro",
    max_tokens: int = 20000,
    timeout: float = 120.0,
) -> str:
    """调用 LLM，返回响应文本。"""
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "timeout": timeout,
    }
    response = client.chat.completions.create(**kwargs)
    return (response.choices[0].message.content or "").strip()


# ── 解析 LLM 响应 ─────────────────────────────────────────────────────


def strip_json_fence(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def parse_llm_output(raw_text: str) -> dict[str, Any] | None:
    """从 LLM 返回中提取 JSON。"""
    if not raw_text:
        return None

    cleaned = strip_json_fence(raw_text)

    # 尝试直接解析
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 尝试用正则提取 JSON 对象
    match = re.search(r"\{[\s\S]*\"option_analysis\"[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # 尝试 json_repair
    try:
        import json_repair
        return json.loads(json_repair.repair_json(cleaned))
    except Exception:
        pass

    return None


def normalize_llm_result(parsed: dict[str, Any]) -> dict[str, Any]:
    """对 LLM JSON 做最小 schema 归一化，不改判断和引用内容。"""
    option_analysis = parsed.get("option_analysis", [])
    if not isinstance(option_analysis, list):
        return parsed

    for opt in option_analysis:
        if not isinstance(opt, dict):
            continue
        evidence_cards = opt.get("evidence_cards", [])
        if not isinstance(evidence_cards, list):
            continue

        has_negative_card = any(
            isinstance(card, dict) and card.get("support_type") == "negative"
            for card in evidence_cards
        )
        if opt.get("evidence_status") == "none" and has_negative_card:
            opt["evidence_status"] = "negative"

    return parsed


# ── 机械校验 ──────────────────────────────────────────────────────────


def validate_result(
    result: dict[str, Any],
    candidates: list[dict[str, Any]],
    unit_lookup: dict[str, dict],
) -> list[str]:
    """执行机械校验，返回问题列表。"""
    issues: list[str] = []

    # 候选池 unit_id 集合
    candidate_unit_ids = {c["unit_id"] for c in candidates}
    # 真实 unit_id 集合（索引中存在）
    valid_unit_ids = set(unit_lookup.keys())

    option_analysis = result.get("option_analysis", [])
    options = result.get("options", {})

    # 检查 option_analysis 长度
    if len(option_analysis) != len(options):
        issues.append(
            f"选项数量不匹配: analysis={len(option_analysis)} vs options={len(options)}"
        )

    for opt in option_analysis:
        label = opt.get("option", "?")
        judgement = opt.get("judgement", "")
        evidence_status = opt.get("evidence_status", "")
        evidence_cards = opt.get("evidence_cards", [])

        # 选项完整性：每个选项都有 judgement 和 evidence_status
        if not judgement:
            issues.append(f"选项{label}: 缺少 judgement")
        if not evidence_status:
            issues.append(f"选项{label}: 缺少 evidence_status")
        elif evidence_status not in {"direct", "indirect", "negative", "none"}:
            issues.append(f"选项{label}: 非法 evidence_status={evidence_status}")

        # direct 有据：evidence_status=direct 时必须至少有一条 evidence_cards
        if evidence_status == "direct" and not evidence_cards:
            issues.append(f"选项{label}: evidence_status=direct 但 evidence_cards 为空")

        # negative 有据：evidence_status=negative 时必须至少有一条反证 evidence_card
        if evidence_status == "negative":
            if not evidence_cards:
                issues.append(f"选项{label}: evidence_status=negative 但 evidence_cards 为空")
            elif not any(card.get("support_type") == "negative" for card in evidence_cards):
                issues.append(f"选项{label}: evidence_status=negative 但没有 negative evidence_card")

        # none 无据：evidence_status=none 时 evidence_cards 必须为空
        if evidence_status == "none" and evidence_cards:
            issues.append(f"选项{label}: evidence_status=none 但 evidence_cards 不为空")

        # evidence_cards 无重复
        seen_uids: set[str] = set()
        for card in evidence_cards:
            uid = card.get("unit_id", "")
            support_type = card.get("support_type", "")
            if support_type and support_type not in {"direct", "indirect", "negative"}:
                issues.append(f"选项{label}: 非法 support_type={support_type}")

            if not uid:
                issues.append(f"选项{label}: evidence_card 缺少 unit_id")
                continue

            # unit_id 真实性
            if uid not in valid_unit_ids:
                issues.append(f"选项{label}: 幻觉 unit_id={uid}（不在索引中）")

            # 候选集来源
            if uid not in candidate_unit_ids:
                issues.append(f"选项{label}: unit_id={uid} 不在本题候选池中")

            # 重复
            if uid in seen_uids:
                issues.append(f"选项{label}: unit_id={uid} 重复引用")
            seen_uids.add(uid)

    return issues


# ── 单题处理流程 ──────────────────────────────────────────────────────


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
    """对一道题执行完整盲判流程。"""
    qid = question["question_id"]
    qtype = question.get("question_type", "single")
    tier = question.get("tier", "")

    result: dict[str, Any] = {
        "question_id": qid,
        "stem": question.get("stem", ""),
        "options": question.get("options", {}),
        "question_type": qtype,
        "tier": tier,
        "pipeline_status": "ok",
    }

    try:
        # Step 1: 检索 -> 候选池
        candidates = search_and_merge(
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

        # Step 2: 构建 prompt
        prompt = build_prompt(question, candidates)

        # Step 3: LLM 调用（每个线程独立的 client）
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        llm_output = call_llm(client, prompt, model=model)
        result["llm_output"] = llm_output

        # Step 4: 解析 LLM 响应
        parsed = parse_llm_output(llm_output)
        if parsed is None:
            result["pipeline_status"] = "llm_parse_failed"
            result["option_analysis"] = []
            result["validation_checks"] = ["LLM 输出无法解析为 JSON"]
            result["predicted_answer"] = []
            return result
        parsed = normalize_llm_result(parsed)

        result["option_analysis"] = parsed.get("option_analysis", [])
        result["predicted_answer"] = parsed.get("predicted_answer", [])

        # Step 5: 机械校验
        validation_issues = validate_result(result, candidates, unit_lookup)
        result["validation_checks"] = validation_issues
        if validation_issues:
            result["pipeline_status"] = "validation_failed"

    except Exception as exc:
        result["pipeline_status"] = "llm_parse_failed"
        result["option_analysis"] = []
        result["validation_checks"] = [f"处理异常: {str(exc)[:200]}"]
        result["predicted_answer"] = []
        result["error_traceback"] = traceback.format_exc()

    return result


# ── 输出 ──────────────────────────────────────────────────────────────


def write_question_json(
    result: dict[str, Any],
    output_dir: Path,
) -> None:
    """将每题详情写入 output/questions/q_{question_id}.json。"""
    qid = result["question_id"]
    path = output_dir / "questions" / f"q_{qid}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def write_summary_jsonl(
    results: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """写入汇总 JSONL。"""
    path = output_dir / "blind_judgment_results.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for r in results:
            summary = {
                "question_id": r["question_id"],
                "tier": r.get("tier", ""),
                "question_type": r.get("question_type", ""),
                "predicted_answer": r.get("predicted_answer", []),
                "option_analysis": r.get("option_analysis", []),
                "validation_passed": r.get("pipeline_status") == "ok",
                "pipeline_status": r.get("pipeline_status", "error"),
            }
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")
    print(f"[output] JSONL 已写入: {path} ({len(results)} 行)")


def write_markdown_report(
    results: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """写入人读 Markdown 报告。"""
    path = output_dir / "blind_judgment_report.md"
    lines: list[str] = []
    lines.append("# Phase 4.1 — 盲判结果报告\n")
    lines.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    total = len(results)
    ok_count = sum(1 for r in results if r.get("pipeline_status") == "ok")
    vf_count = sum(1 for r in results if r.get("pipeline_status") == "validation_failed")
    pf_count = sum(1 for r in results if r.get("pipeline_status") == "llm_parse_failed")
    lines.append(f"总题数: {total} | ✅ ok: {ok_count} | ⚠️ validation_failed: {vf_count} | ❌ llm_parse_failed: {pf_count}\n")
    lines.append("---\n")

    for r in results:
        qid = r["question_id"]
        status = r.get("pipeline_status", "?")
        stem = r.get("stem", "")[:80]
        qtype = r.get("question_type", "?")
        predicted = r.get("predicted_answer", [])
        checks = r.get("validation_checks", [])

        lines.append(f"\n## {qid} | {qtype} | status={status}\n")
        lines.append(f"**题干**: {stem}...\n")
        lines.append(f"**预测答案**: {', '.join(predicted) if predicted else '(无)'}\n")

        # 候选池统计
        candidates = r.get("candidate_pool", [])
        lines.append(f"**候选池**: {len(candidates)} 个知识单元\n")
        route_counts = r.get("candidate_route_counts", {})
        if route_counts:
            route_text = ", ".join(f"{k}={v}" for k, v in route_counts.items())
            lines.append(f"**候选来源**: {route_text}\n")

        # 选项分析
        option_analysis = r.get("option_analysis", [])
        if option_analysis:
            lines.append("### 选项分析\n")
            lines.append("| 选项 | 判断 | 证据状态 | 证据数 |\n")
            lines.append("|------|------|----------|--------|\n")
            for opt in option_analysis:
                label = opt.get("option", "?")
                judgement = opt.get("judgement", "?")
                ev_status = opt.get("evidence_status", "?")
                n_cards = len(opt.get("evidence_cards", []))
                lines.append(f"| {label} | {judgement} | {ev_status} | {n_cards} |\n")

        # 校验结果
        if checks:
            lines.append("\n### 校验问题\n")
            for issue in checks:
                lines.append(f"- {issue}\n")

        lines.append("\n---\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"[output] Markdown 已写入: {path}")


# ── 主流程 ────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 4.1 — 小批量盲判脚本"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="处理题数（默认 10）",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="并发数（默认 10）",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-v4-pro",
        help="模型名称（默认 deepseek-v4-pro）",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="每路检索 top-k（默认 20）",
    )
    parser.add_argument(
        "--merge-top-k",
        type=int,
        default=30,
        help="合并后候选池大小（默认 30）",
    )
    parser.add_argument(
        "--question-id",
        action="append",
        default=[],
        help="指定题号，可重复传入；例如 --question-id v7_q_000009",
    )
    parser.add_argument(
        "--enable-kg",
        action="store_true",
        help="启用 KG 候选扩展（默认关闭）",
    )
    parser.add_argument(
        "--kg-graph-path",
        type=str,
        default=str(KG_GRAPH_PATH),
        help="P6 KG 母版路径",
    )
    parser.add_argument(
        "--kg-max-extra",
        type=int,
        default=30,
        help="每题最多追加的 KG 候选数（默认 30）",
    )
    parser.add_argument(
        "--enable-p5",
        action="store_true",
        help="启用 P5 术语/别名检索辅助（默认关闭）",
    )
    parser.add_argument(
        "--p5-alias-path",
        type=str,
        default=str(P5_ALIAS_INDEX_PATH),
        help="P5C alias index 路径",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="输出目录（默认 phase4_evidence/output）",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Phase 4.1 — 小批量盲判脚本")
    print("=" * 60)
    print(f"limit={args.limit}, concurrency={args.concurrency}, model={args.model}")
    print(f"top_k={args.top_k}, merge_top_k={args.merge_top_k}\n")
    print(
        f"kg_enabled={args.enable_kg}, kg_max_extra={args.kg_max_extra}, "
        f"kg_graph_path={args.kg_graph_path}\n"
    )
    print(
        f"p5_enabled={args.enable_p5}, p5_alias_path={args.p5_alias_path}\n"
    )

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

    # 2. 构建 BM25 检索器
    print("\n[bm25] 构建中文 BM25 检索器 ...")
    bm25_zh = BM25(zh_bm25_docs, zh_bm25_df, zh_bm25_avgdl)
    print(f"[bm25] 中文 BM25 就绪 | N={bm25_zh.N}, avgdl={bm25_zh.avgdl:.2f}")

    print("[bm25] 构建英文 BM25 检索器 ...")
    bm25_en = BM25(en_bm25_docs, en_bm25_df, en_bm25_avgdl)
    print(f"[bm25] 英文 BM25 就绪 | N={bm25_en.N}, avgdl={bm25_en.avgdl:.2f}")

    # 3. 预加载 BGE 模型
    print()
    get_bge_model()

    # 3.5 可选加载 KG 导航索引
    kg_index = load_kg_graph(args.kg_graph_path) if args.enable_kg else None
    p5_index = load_p5_alias_index(args.p5_alias_path) if args.enable_p5 else None

    # 4. 获取 API 配置
    api_key, base_url, env_name = get_llm_config()
    print(f"\n[api] 使用 {env_name} | base_url={base_url}")

    # 5. 筛选题目
    if args.question_id:
        wanted = set(args.question_id)
        sampled = [q for q in questions if q.get("question_id") in wanted]
        sampled.sort(key=lambda x: x["question_id"])
        found = {q["question_id"] for q in sampled}
        missing = sorted(wanted - found)
        if missing:
            raise RuntimeError(f"指定题号不存在: {', '.join(missing)}")
        print(f"\n[sample] 指定题号 {len(sampled)} 题")
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
        print(f"  {q['question_id']} | {q.get('chapter_code','?')} | {q.get('question_type','?')}")

    # 6. 并发处理
    print(f"\n[run] 开始并发处理（{args.concurrency} 线程）...")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []

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

                # 进度打印
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

                # 写入每题 JSON
                write_question_json(result, output_dir)

            except Exception as exc:
                print(f"[{i}/{len(sampled)}] {qid} | ERROR: {str(exc)[:100]}")
                error_result = {
                    "question_id": qid,
                    "stem": q.get("stem", ""),
                    "options": q.get("options", {}),
                    "question_type": q.get("question_type", ""),
                    "tier": q.get("tier", ""),
                    "pipeline_status": "llm_parse_failed",
                    "candidate_pool": [],
                    "option_analysis": [],
                    "validation_checks": [f"线程异常: {str(exc)[:200]}"],
                    "predicted_answer": [],
                }
                results.append(error_result)
                write_question_json(error_result, output_dir)

    # 按 question_id 排序结果
    results.sort(key=lambda x: x["question_id"])

    # 7. 输出汇总
    print("\n" + "=" * 60)
    print("输出汇总结果")
    print("=" * 60)

    write_summary_jsonl(results, output_dir)
    write_markdown_report(results, output_dir)

    # 统计
    status_counts = Counter(r.get("pipeline_status", "?") for r in results)
    print(f"\n[stats] 状态分布: {dict(status_counts)}")
    print(f"[stats] 共处理 {len(results)} 题")

    ok_count = status_counts.get("ok", 0)
    vf_count = status_counts.get("validation_failed", 0)
    pf_count = status_counts.get("llm_parse_failed", 0)
    print(f"  [OK] ok: {ok_count}")
    print(f"  [WARN] validation_failed: {vf_count}")
    print(f"  [ERR] llm_parse_failed: {pf_count}")
    print("\nDone.")


if __name__ == "__main__":
    # 确保 sentence_transformers 的离线环境
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    main()
