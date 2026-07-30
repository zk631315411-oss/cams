"""V7 检索算法：保留重构版的 RAG、候选融合和 KG 扩展参数。"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from .assets import AssetError, RetrievalAssets, get_bge_model


@dataclass(frozen=True)
class RetrievalConfig:
    """重构版 Phase 4 的标准参数快照，不在业务代码中散落魔法数字。"""

    profile: str = "v7_legacy_202607"
    top_k: int = 20
    merge_top_k: int = 30
    kg_max_extra: int = 30
    per_option_limit: int = 3
    per_head_minimum: int = 2
    rrf_k: int = 60
    section_context_range: int = 4
    enable_kg: bool = True
    enable_p5: bool = True

    def snapshot(self) -> dict[str, Any]:
        return asdict(self)


def make_config(overrides: dict[str, Any] | None = None, *, question_mode: bool) -> RetrievalConfig:
    values = RetrievalConfig(enable_p5=question_mode).__dict__.copy()
    allowed = set(values)
    for key, value in (overrides or {}).items():
        if key not in allowed:
            raise ValueError(f"未知检索参数: {key}")
        values[key] = value
    if not question_mode:
        values["enable_p5"] = False
        values["per_option_limit"] = 0
    config = RetrievalConfig(**values)
    for name in ("top_k", "merge_top_k", "kg_max_extra", "per_option_limit", "per_head_minimum", "rrf_k", "section_context_range"):
        if int(getattr(config, name)) < 0:
            raise ValueError(f"检索参数 {name} 不能为负数")
    if config.rrf_k <= 0:
        raise ValueError("检索参数 rrf_k 必须大于 0")
    return config


def tokenize(text: str) -> list[str]:
    text = (text or "").lower()
    tokens = re.findall(r"[a-z0-9][a-z0-9_\-/.]*", text)
    for run in re.findall(r"[一-鿿]+", text):
        if len(run) == 1:
            tokens.append(run)
        else:
            for size in (2, 3):
                tokens.extend(run[index:index + size] for index in range(len(run) - size + 1))
    return tokens


class BM25:
    """与重构版一致的轻量 BM25 实现。"""

    def __init__(self, docs: list[dict[str, int]], df: dict[str, int], avgdl: float,
                 k1: float = 1.5, b: float = 0.75):
        self.docs, self.df, self.avgdl, self.k1, self.b = docs, df, avgdl, k1, b
        self.count = len(docs)
        self.doc_lengths = [sum(document.values()) for document in docs]
        self._idf: dict[str, float] = {}

    def idf(self, term: str) -> float:
        if term not in self._idf:
            document_count = self.df.get(term, 0)
            self._idf[term] = math.log((self.count - document_count + 0.5) / (document_count + 0.5) + 1.0)
        return self._idf[term]

    def search(self, query: str, top_k: int) -> list[tuple[int, float]]:
        query_counts: dict[str, int] = {}
        for term in tokenize(query):
            query_counts[term] = query_counts.get(term, 0) + 1
        if not query_counts:
            return []
        scores: list[tuple[int, float]] = []
        for index, document in enumerate(self.docs):
            score = 0.0
            length = self.doc_lengths[index]
            for term, query_frequency in query_counts.items():
                term_frequency = document.get(term, 0)
                if not term_frequency:
                    continue
                numerator = term_frequency * (self.k1 + 1)
                denominator = term_frequency + self.k1 * (1 - self.b + self.b * length / self.avgdl)
                score += self.idf(term) * (numerator / denominator) * query_frequency
            scores.append((index, score))
        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[:top_k]


def make_candidate(unit: dict[str, Any], route: str, score: float, **overrides: Any) -> dict[str, Any]:
    candidate: dict[str, Any] = {
        "unit_id": unit["unit_id"],
        "knowledge_zh": unit.get("knowledge_zh", ""),
        "knowledge_en": unit.get("knowledge_en", ""),
        "en_quote": unit.get("en_quote", ""),
        "heading_context": unit.get("heading_context", []),
        "type": unit.get("type", ""),
        "route": route,
        "score": round(float(score), 6),
        "printed_page": unit.get("printed_page", ""),
        "pdf_page": unit.get("pdf_page", ""),
    }
    candidate.update(overrides)
    return candidate


def build_question_heads(question: dict[str, Any]) -> list[dict[str, Any]]:
    heads: list[dict[str, Any]] = []
    stem = str(question.get("stem", "") or "").strip()
    stem_en = str(question.get("stem_en", "") or "").strip()
    options = question.get("options", {}) or {}
    options_en = question.get("options_en", {}) or {}
    if stem:
        heads.append({"head_id": "stem_zh", "head_kind": "stem", "option": None, "language": "zh", "query": stem})
    for label, text in options.items():
        query = f"{stem} {text}".strip()
        if query:
            heads.append({"head_id": f"option_{label}_zh", "head_kind": "option", "option": str(label), "language": "zh", "query": query})
    if stem_en:
        heads.append({"head_id": "stem_en", "head_kind": "stem", "option": None, "language": "en", "query": stem_en})
    for label, text in options_en.items():
        query = f"{stem_en} {text}".strip()
        if query:
            heads.append({"head_id": f"option_{label}_en", "head_kind": "option", "option": str(label), "language": "en", "query": query})
    return heads


def build_option_only_heads(question: dict[str, Any]) -> list[dict[str, Any]]:
    heads: list[dict[str, Any]] = []
    for language, key in (("zh", "options"), ("en", "options_en")):
        for label, text in (question.get(key, {}) or {}).items():
            query = str(text or "").strip()
            if query:
                heads.append({"head_id": f"option_only_{label}_{language}", "head_kind": "option_only_supplement", "option": str(label), "language": language, "query": query})
    return heads


def _normalise_term(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def p5_canonical_inline(query: str, p5: dict[str, Any] | None, language: str) -> str:
    if not p5:
        return query
    for group in p5.get("aliases", []):
        for term in group.get("terms", []):
            if term in query.lower():
                canonical = str(group.get("canonical_zh" if language == "zh" else "canonical_en", "") or "")
                if canonical and canonical.lower() not in query.lower():
                    return f"{query}（{canonical}）"
                break
    return query


def _bge_rows(heads: list[dict[str, Any]], assets: RetrievalAssets, top_k: int) -> list[dict[str, Any]]:
    if not heads:
        return []
    try:
        import numpy as np
    except ImportError as exc:
        raise AssetError("缺少 numpy；请按 backend/requirements.txt 创建正式版运行环境") from exc
    vectors = np.asarray(get_bge_model(assets.paths.root).encode([head["query"] for head in heads], normalize_embeddings=True))
    corpus = np.asarray(assets.index["bge_vecs"])
    denominators = np.linalg.norm(vectors, axis=1, keepdims=True) * np.linalg.norm(corpus, axis=1)
    similarities = np.divide(vectors @ corpus.T, denominators, out=np.zeros((len(vectors), len(corpus))), where=denominators != 0)
    rows: list[dict[str, Any]] = []
    card_ids, lookup = assets.index["card_ids"], assets.index["unit_lookup"]
    for head, scores in zip(heads, similarities):
        for rank, position in enumerate(np.argsort(scores)[::-1][:top_k], start=1):
            unit = lookup[card_ids[int(position)]]
            rows.append({**head, "route": "bge", "rank": rank,
                         "raw_score": round(float(scores[int(position)]), 6), "unit_id": unit["unit_id"]})
    return rows


def _bm25_rows(heads: list[dict[str, Any]], assets: RetrievalAssets, top_k: int) -> list[dict[str, Any]]:
    index = assets.index
    zh = BM25(index["zh_bm25_docs"], index["zh_bm25_df"], index["zh_bm25_avgdl"])
    en = BM25(index["en_bm25_docs"], index["en_bm25_df"], index["en_bm25_avgdl"])
    card_ids = index["card_ids"]
    rows: list[dict[str, Any]] = []
    for head in heads:
        bm25 = en if head["language"] == "en" else zh
        route = "bm25_en" if head["language"] == "en" else "bm25_zh"
        for rank, (position, score) in enumerate(bm25.search(head["query"], top_k), start=1):
            rows.append({**head, "route": route, "rank": rank,
                         "raw_score": round(float(score), 6), "unit_id": card_ids[position]})
    return rows


def _merge_rows(rows: list[dict[str, Any]], assets: RetrievalAssets, config: RetrievalConfig) -> list[dict[str, Any]]:
    routes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        routes[str(row["unit_id"])].append(row)
    merged: list[dict[str, Any]] = []
    lookup = assets.index["unit_lookup"]
    for unit_id, hits in routes.items():
        hit_records = [{"head_id": hit["head_id"], "language": hit["language"], "route": hit["route"],
                        "rank": int(hit["rank"]), "raw_score": hit["raw_score"], "query": hit["query"]} for hit in hits]
        hit_records.sort(key=lambda item: (item["rank"], item["head_id"], item["route"]))
        fusion_score = sum(1.0 / (config.rrf_k + item["rank"]) for item in hit_records)
        merged.append({**make_candidate(lookup[unit_id], route="rrf", score=fusion_score),
                       "fusion_score": round(fusion_score, 8),
                       "routes": sorted({item["route"] for item in hit_records}),
                       "languages": sorted({item["language"] for item in hit_records}),
                       "best_rank": min(item["rank"] for item in hit_records),
                       "retrieval_hits": hit_records})
    merged.sort(key=lambda item: (-float(item["fusion_score"]), -len(item["routes"]),
                                  -len(item["languages"]), int(item["best_rank"]), item["unit_id"]))
    return merged


def select_head_balanced_candidates(merged: list[dict[str, Any]], heads: list[dict[str, Any]],
                                    config: RetrievalConfig) -> list[dict[str, Any]]:
    if config.merge_top_k <= 0:
        return []
    selected: set[str] = set()
    for _ in range(config.per_head_minimum):
        for head in heads:
            if len(selected) >= config.merge_top_k:
                break
            ranked: list[tuple[float, float, str]] = []
            for candidate in merged:
                hits = [hit for hit in candidate["retrieval_hits"] if hit["head_id"] == head["head_id"]]
                if hits:
                    head_score = sum(1.0 / (config.rrf_k + int(hit["rank"])) for hit in hits)
                    ranked.append((head_score, max(float(hit["raw_score"]) for hit in hits), candidate["unit_id"]))
            for _, _, unit_id in sorted(ranked, key=lambda item: (-item[0], -item[1], item[2])):
                if unit_id not in selected:
                    selected.add(unit_id)
                    break
    for candidate in merged:
        if len(selected) >= config.merge_top_k:
            break
        selected.add(candidate["unit_id"])
    return [candidate for candidate in merged if candidate["unit_id"] in selected][:config.merge_top_k]


_ROUTE_WEIGHTS = {"kg_same_core_point": 1.0, "kg_same_section_cp": 0.70,
                  "kg_same_chapter_cp": 0.55, "kg_cross_chapter_cp": 0.42}
_SEMANTIC_REASONS = {"grounds": "证据 A 为证据 B 提供理论或定义基础",
                     "illustrates": "证据 A 是证据 B 所述概念的具体例证",
                     "summarizes": "证据 A 概括了证据 B 的详细阐述",
                     "contrasts": "证据 A 与证据 B 在概念上形成对比区分"}


def _kg_index(kg: dict[str, Any]) -> dict[str, Any]:
    cp_meta: dict[str, dict[str, Any]] = {}
    cp_to_units: dict[str, list[str]] = defaultdict(list)
    unit_to_cps: dict[str, list[str]] = defaultdict(list)
    relation_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
    section_to_cps: dict[str, list[str]] = defaultdict(list)
    for point in kg.get("core_points", []) or []:
        point_id = str(point.get("core_point_id", ""))
        if not point_id:
            continue
        cp_meta[point_id] = point
        if point.get("section_id"):
            section_to_cps[str(point["section_id"])].append(point_id)
        for key in ("key_unit_ids", "anchor_unit_ids", "support_unit_ids"):
            for unit_id in point.get(key, []) or []:
                unit_id = str(unit_id)
                if unit_id not in cp_to_units[point_id]:
                    cp_to_units[point_id].append(unit_id)
                if point_id not in unit_to_cps[unit_id]:
                    unit_to_cps[unit_id].append(point_id)
    for edge in kg.get("edges", []) or []:
        scope = edge.get("edge_scope")
        source, target = str(edge.get("source_id", "")), str(edge.get("target_id", ""))
        if scope == "core_point_unit":
            if target not in cp_to_units[source]:
                cp_to_units[source].append(target)
            if source not in unit_to_cps[target]:
                unit_to_cps[target].append(source)
        elif scope == "section_core_point" and target not in section_to_cps[source]:
            section_to_cps[source].append(target)
        elif scope in {"same_section_core_point", "same_chapter_core_point", "cross_chapter_core_point"}:
            relation_edges[source].append(edge)
            relation_edges[target].append(edge)
    return {"cp_meta": cp_meta, "cp_to_units": cp_to_units, "unit_to_cps": unit_to_cps,
            "relation_edges": relation_edges, "section_to_cps": section_to_cps}


def _relation_route(scope: str) -> str:
    return {"same_section_core_point": "kg_same_section_cp",
            "same_chapter_core_point": "kg_same_chapter_cp",
            "cross_chapter_core_point": "kg_cross_chapter_cp"}.get(scope, "kg_unknown")


def expand_with_kg(seeds: list[dict[str, Any]], assets: RetrievalAssets, query: str,
                   config: RetrievalConfig) -> list[dict[str, Any]]:
    if not assets.kg or not seeds or not config.enable_kg:
        return []
    graph, lookup = _kg_index(assets.kg), assets.index["unit_lookup"]
    existing = {seed["unit_id"] for seed in seeds}
    proposed: dict[str, dict[str, Any]] = {}
    query_parts = query.lower().split()

    def relevance(unit: dict[str, Any]) -> float:
        text = f"{unit.get('knowledge_zh', '')} {unit.get('en_quote', '')}".lower()
        return sum(1 for part in query_parts if part in text) / max(1, len(query_parts))

    def propose(unit_id: str, route: str, seed: dict[str, Any], source_cp: str, target_cp: str,
                edge: dict[str, Any] | None = None) -> None:
        if unit_id in existing or unit_id == seed["unit_id"] or unit_id not in lookup:
            return
        unit = lookup[unit_id]
        score = float(seed["fusion_score"]) * 0.48 + _ROUTE_WEIGHTS.get(route, 0.55) * 0.32 + relevance(unit) * 0.20
        candidate = make_candidate(unit, route=route, score=score, kg={
            "source_seed_unit_id": seed["unit_id"], "source_core_point_id": source_cp,
            "target_core_point_id": target_cp, "text_relevance": round(relevance(unit), 6),
            "seed_score": round(float(seed["fusion_score"]), 6),
        })
        if edge:
            candidate["kg"].update({"edge_id": edge.get("edge_id", ""), "edge_scope": edge.get("edge_scope", ""),
                                    "relation_type": edge.get("relation_type", ""),
                                    "reason": edge.get("reason") or _SEMANTIC_REASONS.get(edge.get("relation_type", ""), "")})
        if unit_id not in proposed or candidate["score"] > proposed[unit_id]["score"]:
            proposed[unit_id] = candidate

    for seed in seeds:
        for point_id in graph["unit_to_cps"].get(seed["unit_id"], []):
            for unit_id in graph["cp_to_units"].get(point_id, []):
                propose(unit_id, "kg_same_core_point", seed, point_id, point_id)
            for edge in graph["relation_edges"].get(point_id, []):
                target = edge["target_id"] if edge["source_id"] == point_id else edge["source_id"]
                for unit_id in graph["cp_to_units"].get(target, []):
                    propose(unit_id, _relation_route(edge.get("edge_scope", "")), seed, point_id, target, edge)
            section = graph["cp_meta"].get(point_id, {}).get("section_id", "")
            for target in graph["section_to_cps"].get(section, []):
                if target != point_id:
                    for unit_id in graph["cp_to_units"].get(target, []):
                        propose(unit_id, "kg_same_section_cp", seed, point_id, target)
    return sorted(proposed.values(), key=lambda item: (-float(item["score"]), item["unit_id"]))[:config.kg_max_extra]


def _run_rag(heads: list[dict[str, Any]], assets: RetrievalAssets, config: RetrievalConfig) -> list[dict[str, Any]]:
    return _merge_rows(_bge_rows(heads, assets, config.top_k) + _bm25_rows(heads, assets, config.top_k), assets, config)


def _option_supplements(question: dict[str, Any], assets: RetrievalAssets, excluded: set[str],
                        config: RetrievalConfig) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    heads = build_option_only_heads(question)
    for row in _bge_rows(heads, assets, config.top_k) + _bm25_rows(heads, assets, config.top_k):
        label, unit_id = str(row.get("option") or "").upper(), str(row["unit_id"])
        if label and unit_id not in excluded:
            grouped[label][unit_id].append(row)
    result: dict[str, list[dict[str, Any]]] = {}
    lookup = assets.index["unit_lookup"]
    for label, by_unit in sorted(grouped.items()):
        candidates: list[dict[str, Any]] = []
        for unit_id, rows in by_unit.items():
            hits = [{"head_id": row["head_id"], "language": row["language"], "route": row["route"],
                     "rank": int(row["rank"]), "raw_score": row["raw_score"], "query": row["query"]} for row in rows]
            hits.sort(key=lambda item: (item["rank"], item["head_id"], item["route"]))
            fusion_score = sum(1.0 / (config.rrf_k + item["rank"]) for item in hits)
            candidates.append(make_candidate(lookup[unit_id], route="supplement", score=fusion_score,
                                             supplement_only=True, fusion_score=round(fusion_score, 8),
                                             routes=sorted({item["route"] for item in hits}),
                                             languages=sorted({item["language"] for item in hits}),
                                             best_rank=min(item["rank"] for item in hits), retrieval_hits=hits))
        candidates.sort(key=lambda item: (-float(item["fusion_score"]), -len(item["routes"]),
                                          -len(item["languages"]), int(item["best_rank"]), item["unit_id"]))
        result[label] = candidates[:config.per_option_limit]
    return result


def retrieve_question(question: dict[str, Any], assets: RetrievalAssets, config: RetrievalConfig) -> dict[str, Any]:
    heads = build_question_heads(question)
    if config.enable_p5:
        for head in heads:
            head["original_query"] = head["query"]
            head["query"] = p5_canonical_inline(head["query"], assets.p5, head["language"])
    merged = _run_rag(heads, assets, config)
    main = select_head_balanced_candidates(merged, heads, config)
    stem_query = f"{question.get('stem', '')} {question.get('stem_en', '')}".strip()
    kg = expand_with_kg(main, assets, stem_query, config)
    return {"retrieval_kind": "question", "asset_versions": assets.version_snapshot(),
            "textbook_version": assets.textbook_version, "config": config.snapshot(), "query_heads": heads,
            "main_candidates": main, "kg_candidates": kg,
            "option_supplements": _option_supplements(question, assets, {item["unit_id"] for item in main}, config)}


def retrieve_general(query: str, assets: RetrievalAssets, config: RetrievalConfig,
                     language: str = "auto") -> dict[str, Any]:
    query = str(query or "").strip()
    if not query:
        raise ValueError("检索词不能为空")
    if language not in {"auto", "zh", "en"}:
        raise ValueError("language 只能是 auto、zh 或 en")
    detected = "zh" if language == "auto" and re.search(r"[一-鿿]", query) else ("en" if language == "auto" else language)
    heads = [{"head_id": "general_query", "head_kind": "general", "option": None, "language": detected, "query": query}]
    merged = _run_rag(heads, assets, config)
    main = merged[:config.merge_top_k]
    kg = expand_with_kg(main, assets, query, config)
    results = main + kg
    return {"retrieval_kind": "general", "query": query, "asset_versions": assets.version_snapshot(),
            "textbook_version": assets.textbook_version, "config": config.snapshot(), "results": results,
            "main_candidates": main, "kg_candidates": kg}
