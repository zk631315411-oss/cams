# -*- coding: utf-8 -*-
"""s2 — 检索：BGE/BM25搜索、检索头、KG扩展、补充池、RRF融合、候选格式化。"""

from __future__ import annotations

import json, re
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import sys as _sys
from pathlib import Path as _Path
_PARENT = str(_Path(__file__).resolve().parent.parent)
if _PARENT not in _sys.path:
    _sys.path.insert(0, _PARENT)

from 公共函数.retrieval import bge_search, bm25_search
from s1_indexing import (BM25, _compact_text, _load_kg_units, _section_context_cards,
    _format_context_block, build_option_only_heads, build_retrieval_heads,
    get_bge_model, load_kg_graph, KG_GRAPH_PATH)
from s3_candidate import make_candidate

# ── 常量 ──

SEMANTIC_FORCE_REASONS = {
    "grounds": "证据A为证据B提供理论或定义基础",
    "illustrates": "证据A是证据B所述概念的具体例证",
    "summarizes": "证据A概括了证据B中的详细阐述",
    "contrasts": "证据A与证据B在概念上形成对比区分",
}

_TYPE_LABELS: dict[str, str] = {
    "definition": "概念定义", "rule": "规则/规定", "fact": "事实陈述",
    "case": "案例", "process": "流程", "classification": "分类",
    "risk_indicator": "风险指标", "context": "背景说明",
}

# ── 补充池 ──

def aggregate_option_supplements(retrieval_rows: list[dict[str, Any]],
    unit_lookup: dict[str, dict[str, Any]], excluded_unit_ids: set[str],
    per_option_limit: int=3) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for row in retrieval_rows:
        option = str(row.get("option","") or "").strip().upper()
        uid = str(row.get("unit_id","") or "").strip()
        if option and uid and uid not in excluded_unit_ids and uid in unit_lookup:
            grouped[option][uid].append(row)
    result: dict[str, list[dict[str, Any]]] = {}
    for option, by_uid in sorted(grouped.items()):
        ranked: list[dict[str, Any]] = []
        for uid, rows in by_uid.items():
            hits = [{"head_id": r["head_id"], "language": r["language"],
                "route": r["route"], "rank": int(r.get("rank") or 0),
                "raw_score": r.get("raw_score", r.get("score", 0.0)),
                "query": r.get("query","")} for r in rows]
            hits.sort(key=lambda h: (h["rank"], h["head_id"], h["route"]))
            routes = sorted({h["route"] for h in hits})
            languages = sorted({h["language"] for h in hits})
            fusion_score = sum(1.0/(60+int(h.get("rank") or 1)) for h in hits)
            best_rank = min(int(h.get("rank") or 999999) for h in hits)
            unit = unit_lookup[uid]
            ranked.append(make_candidate(unit, route="supplement",
                score=round(fusion_score, 8), supplement_only=True,
                fusion_score=round(fusion_score, 8), routes=routes,
                languages=languages, best_rank=best_rank, retrieval_hits=hits))
        ranked.sort(key=lambda r: (-float(r["fusion_score"]), -len(r["routes"]),
            -len(r["languages"]), int(r["best_rank"]), r["unit_id"]))
        result[option] = ranked[:max(0, per_option_limit)]
    return result

def retrieve_option_supplements(question: dict[str, Any], bge_vecs: np.ndarray,
    card_ids: list[str], unit_lookup: dict[str, dict[str, Any]],
    bm25_zh_index: BM25, bm25_en_index: BM25, excluded_unit_ids: set[str],
    top_k: int=20, per_option_limit: int=3) -> dict[str, list[dict[str, Any]]]:
    heads = build_option_only_heads(question)
    retrieval_rows: list[dict[str, Any]] = []
    if heads:
        model = get_bge_model()
        vectors = model.encode([h["query"] for h in heads], normalize_embeddings=True)
        similarities = cosine_similarity(vectors, bge_vecs)
        for head, scores in zip(heads, similarities):
            for rank, idx in enumerate(np.argsort(scores)[::-1][:top_k], start=1):
                retrieval_rows.append({**head, "route": "bge", "rank": rank,
                    "raw_score": round(float(scores[idx]), 6), "unit_id": card_ids[idx]})
    for head in heads:
        bm25_index = bm25_en_index if head["language"] == "en" else bm25_zh_index
        route = "bm25_en" if head["language"] == "en" else "bm25_zh"
        for row in bm25_search(head["query"], bm25_index, card_ids, unit_lookup, top_k):
            retrieval_rows.append({**head, "route": route, "rank": int(row["rank"]),
                "raw_score": float(row["score"]), "unit_id": row["unit_id"]})
    return aggregate_option_supplements(retrieval_rows, unit_lookup, excluded_unit_ids, per_option_limit)

# ── 候选平衡 ──

def select_head_balanced_candidates(merged: list[dict[str, Any]],
    heads: list[dict[str, Any]], limit: int, per_head_minimum: int=2) -> list[dict[str, Any]]:
    if limit <= 0: return []
    selected_ids: set[str] = set()
    for _ in range(per_head_minimum):
        for head in heads:
            if len(selected_ids) >= limit: break
            ranked: list[tuple[float, float, str, dict]] = []
            for c in merged:
                hits = [h for h in c.get("retrieval_hits",[]) if h.get("head_id")==head["head_id"]]
                if not hits: continue
                head_score = sum(1.0/(60+int(h.get("rank") or 1)) for h in hits)
                best_raw = max(float(h.get("raw_score") or 0.0) for h in hits)
                ranked.append((head_score, best_raw, c["unit_id"], c))
            ranked.sort(key=lambda r: (-r[0], -r[1], r[2]))
            for _, _, uid, _ in ranked:
                if uid not in selected_ids: selected_ids.add(uid); break
    for c in merged:
        if len(selected_ids) >= limit: break
        selected_ids.add(c["unit_id"])
    return [c for c in merged if c["unit_id"] in selected_ids][:limit]

# ── KG 扩展 ──

def _relation_route(edge_scope: str) -> str:
    if edge_scope == "same_section_core_point": return "kg_same_section_cp"
    if edge_scope == "same_chapter_core_point": return "kg_same_chapter_cp"
    if edge_scope == "cross_chapter_core_point": return "kg_cross_chapter_cp"
    return "kg_unknown"

ROUTE_WEIGHT = {"kg_same_core_point": 1.0, "kg_same_section_cp": 0.70,
    "kg_same_chapter_cp": 0.55, "kg_cross_chapter_cp": 0.42}

def _normalize_route_scores(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows: return rows
    scores = [r["score"] for r in rows]
    mn, mx = min(scores), max(scores)
    denom = mx - mn
    for r in rows:
        norm = (r["score"] - mn) / denom if denom > 0 else 0.5
        r["raw_score"] = r["score"]
        r["norm_score"] = round(norm, 6)
        r["score"] = round(norm + (1.0 / (60 + r["rank"])), 6)
    return rows

def p5_canonical_inline(query: str, p5_index: dict[str, Any], lang: str="zh") -> str:
    if not p5_index: return query
    for alias in p5_index.get("aliases", []):
        for term in alias.get("terms", []):
            if term.lower() in query.lower():
                canonical = alias.get("canonical_zh" if lang=="zh" else "canonical_en", "")
                if canonical and canonical.lower() not in query.lower():
                    query += f"（{canonical}）"; break
    return query

def expand_with_kg(seeds: list[dict[str, Any]], unit_lookup: dict[str, dict],
    kg_index: dict[str, Any], query_zh: str, query_en: str|None, max_extra: int=30,
    existing_ids: set[str]|None=None) -> list[dict[str, Any]]:
    if not kg_index or not seeds: return []
    existing = set(existing_ids or [])
    cp_meta = kg_index["cp_meta"]
    unit_to_cps = kg_index["unit_to_cps"]
    cp_to_units = kg_index["cp_to_units"]
    relation_edges = kg_index["relation_edges_by_cp"]
    section_to_cps = kg_index["section_to_cps"]
    proposed: dict[str, dict[str, Any]] = {}

    query_text = f"{query_zh} {query_en or ''}".lower()
    def text_relevance(unit):
        text = f"{unit.get('knowledge_zh','')} {unit.get('en_quote','')}".lower()
        return sum(1 for q in query_text.split() if q in text) / max(1, len(query_text.split()))

    def add_unit(uid, route, seed, source_cp_id, target_cp_id, edge=None):
        if uid in existing or uid == seed["unit_id"]: return
        unit = unit_lookup.get(uid)
        if not unit: return
        relevance = text_relevance(unit)
        seed_score = float(seed.get("score") or 0.0)
        score = seed_score*0.48 + ROUTE_WEIGHT.get(route, 0.55)*0.32 + relevance*0.20
        c = make_candidate(unit, route=route, score=round(score, 6),
            kg={"source_seed_unit_id": seed["unit_id"],
                "source_core_point_id": source_cp_id,
                "target_core_point_id": target_cp_id,
                "text_relevance": round(relevance, 6),
                "seed_score": round(seed_score, 6)})
        if edge:
            c["kg"].update({"edge_id": edge.get("edge_id",""), "edge_scope": edge.get("edge_scope",""),
                "relation_type": edge.get("relation_type",""),
                "reason": edge.get("reason","") or SEMANTIC_FORCE_REASONS.get(edge.get("relation_type",""),"")})
        if uid not in proposed or c["score"] > proposed[uid]["score"]:
            proposed[uid] = c

    for seed in seeds:
        seed_uid = seed["unit_id"]
        for cp_id in unit_to_cps.get(seed_uid, []):
            for uid in cp_to_units.get(cp_id, []):
                add_unit(uid, "kg_same_core_point", seed, cp_id, cp_id)
            for edge in relation_edges.get(cp_id, []):
                target_cp = edge["target_id"] if edge["source_id"]==cp_id else edge["source_id"]
                route = _relation_route(edge.get("edge_scope",""))
                for uid in cp_to_units.get(target_cp, []):
                    add_unit(uid, route, seed, cp_id, target_cp, edge)
            section_id = cp_meta.get(cp_id, {}).get("section_id","")
            for other_cp in section_to_cps.get(section_id, []):
                if other_cp != cp_id:
                    for uid in cp_to_units.get(other_cp, []):
                        add_unit(uid, "kg_same_section_cp", seed, cp_id, other_cp)

    expanded = sorted(proposed.values(), key=lambda c: -c["score"])[:max_extra]
    return expanded

# ── 主检索流程 ──

def search_and_merge(question: dict[str, Any], bge_vecs: np.ndarray,
    card_ids: list[str], unit_lookup: dict[str, dict], bm25_zh_index: BM25,
    bm25_en_index: BM25, top_k: int=20, merge_top_k: int=30,
    kg_index: dict[str, Any]|None=None, kg_max_extra: int=30,
    p5_index: dict[str, Any]|None=None) -> list[dict[str, Any]]:
    heads = build_retrieval_heads(question)
    query_zh, query_en = "", ""
    route_map: dict[str, list[dict]] = {}

    if p5_index:
        for head in heads:
            head["query"] = p5_canonical_inline(head["query"], p5_index, lang=head["language"])

    if heads:
        model = get_bge_model()
        query_vectors = model.encode([h["query"] for h in heads], normalize_embeddings=True)
        similarities = cosine_similarity(query_vectors, bge_vecs)
        for head, scores in zip(heads, similarities):
            for rank, idx in enumerate(np.argsort(scores)[::-1][:top_k], start=1):
                unit = unit_lookup.get(card_ids[idx], {})
                row = make_candidate(unit, route="bge", score=round(float(scores[idx]), 6), rank=rank)
                row.update({"head_id": head["head_id"], "head_kind": head["head_kind"],
                    "option": head["option"], "language": head["language"],
                    "route": "bge"})
                route_map.setdefault(row["unit_id"], []).append(row)

    for head in heads:
        bm25_index = bm25_en_index if head["language"]=="en" else bm25_zh_index
        route = "bm25_en" if head["language"]=="en" else "bm25_zh"
        for row in _normalize_route_scores(bm25_search(head["query"], bm25_index, card_ids, unit_lookup, top_k)):
            row.update({"route": route, "head_id": head["head_id"], "head_kind": head["head_kind"],
                "option": head["option"], "language": head["language"]})
            route_map.setdefault(row["unit_id"], []).append(row)

    merged: list[dict[str, Any]] = []
    for uid, rows in route_map.items():
        hits = [{"head_id": r["head_id"], "language": r["language"], "route": r["route"],
            "rank": int(r.get("rank") or 0), "raw_score": r.get("raw_score", r.get("score",0.0)),
            "query": r.get("query","")} for r in rows]
        hits.sort(key=lambda h: (h["rank"], h["head_id"], h["route"]))
        fusion_score = sum(1.0/(60+int(h.get("rank") or 1)) for h in hits)
        routes = sorted({h["route"] for h in hits})
        languages = sorted({h["language"] for h in hits})
        best_rank = min(int(h.get("rank") or 999999) for h in hits)
        best_row = rows[0]
        merged.append({**{k: v for k, v in best_row.items() if k not in ("rank","score","route","head_id","head_kind","option","language")},
            "fusion_score": round(fusion_score, 8), "routes": routes, "languages": languages,
            "best_rank": best_rank, "retrieval_hits": hits})
    merged.sort(key=lambda r: (-float(r["fusion_score"]), -len(r["routes"]), -len(r["languages"]), int(r["best_rank"])))

    selected = select_head_balanced_candidates(merged, heads, merge_top_k)
    existing_ids = {c["unit_id"] for c in selected}

    if kg_index:
        query_zh, query_en = "", ""
        try:
            stem = question.get("stem",""); opts = question.get("options",{})
            query_zh = f"{stem} {' '.join(opts.values())}".strip()
            stem_en = question.get("stem_en","")
            if stem_en:
                opts_en = question.get("options_en",{})
                query_en = f"{stem_en} {' '.join(opts_en.values())}".strip()
        except: pass
        kg_extras = expand_with_kg(selected, unit_lookup, kg_index, query_zh, query_en, kg_max_extra, existing_ids)
        selected = selected + kg_extras
    return selected

# ── 格式化 ──

def format_candidates(candidates: list[dict[str, Any]]) -> str:
    by_unit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in candidates:
        by_unit[c["unit_id"]].append(c)

    main_units: list[dict[str, Any]] = []
    supplement_units: list[dict[str, Any]] = []
    for uid, rows in by_unit.items():
        main = [r for r in rows if not r.get("supplement_only")]; supp = [r for r in rows if r.get("supplement_only")]
        if main: main_units.append(main[0])
        if supp: supplement_units.append(supp[0])

    parts: list[str] = []
    for unit in main_units:
        uid = unit["unit_id"]
        cards = _section_context_cards(uid, set())
        if cards: parts.append(_format_context_block(cards))
    if supplement_units:
        parts.append("【补充候选】")
        for unit in supplement_units:
            uid = unit["unit_id"]
            zh = _compact_text(unit.get("knowledge_zh",""))
            en = _compact_text(unit.get("en_quote",""))
            page_str = f" | P{unit['printed_page']}" if unit.get("printed_page") else ""
            parts.append(f"[{uid}] 补充{page_str}\n  中文要点：{zh}\n  英文原文：{en}\n")
    return "\n".join(parts)

def format_option_supplements(question: dict[str, Any],
    supplement_pool: dict[str, list[dict[str, Any]]]) -> str:
    parts: list[str] = []
    for label in sorted(question.get("options", {}).keys()):
        cards = supplement_pool.get(label, [])
        if not cards: continue
        parts.append(f"【选项{label} 补充候选】")
        for card in cards:
            zh = _compact_text(card.get("knowledge_zh",""))
            en = _compact_text(card.get("en_quote",""))
            page_str = f" | P{card['printed_page']}" if card.get("printed_page") else ""
            type_label = _TYPE_LABELS.get(str(card.get("type","")).strip(), "")
            parts.append(f"[{card['unit_id']}] 补充{page_str} | 教材类型：{type_label}")
            if zh: parts.append(f"  中文要点：{zh}")
            if en: parts.append(f"  英文原文：{en}")
        parts.append("")
    return "\n".join(parts)
