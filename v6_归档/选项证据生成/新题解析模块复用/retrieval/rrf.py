"""
P3 (Phase 1.5): RRF 融合 — 对标 WeKnora fuseWithRRF [fusion.go:84].

对同一查询的 BGE + BM25 排名做倒数排名融合。
exact_phrase / adjacent_card 不参与 RRF，直接 append + 去重。
"""
from __future__ import annotations

from typing import Any


def rrf_fuse(
    source_rankings: dict[str, list[tuple[str, float, int]]],
    *,
    k: int = 60,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
) -> dict[str, float]:
    """对标 WeKnora fuseWithRRF [fusion.go:84].

    RRF(card) = vectorWeight/(k + vRank) + keywordWeight/(k + kRank)

    source_rankings: {"card_bge": [(card_id, score, rank), ...],
                       "bm25": [(card_id, score, rank), ...]}
    Returns: {card_id: rrf_score}
    """
    # Build rank lookup: card_id → best rank per source
    bge_ranks: dict[str, int] = {}
    for cid, _score, rank in source_rankings.get("card_bge", []):
        if cid not in bge_ranks or rank < bge_ranks[cid]:
            bge_ranks[cid] = rank

    bm25_ranks: dict[str, int] = {}
    for cid, _score, rank in source_rankings.get("bm25", []):
        if cid not in bm25_ranks or rank < bm25_ranks[cid]:
            bm25_ranks[cid] = rank

    all_ids: set[str] = set(bge_ranks) | set(bm25_ranks)
    rrf: dict[str, float] = {}
    for cid in all_ids:
        score = 0.0
        if cid in bge_ranks:
            score += vector_weight / float(k + bge_ranks[cid])
        if cid in bm25_ranks:
            score += keyword_weight / float(k + bm25_ranks[cid])
        rrf[cid] = score

    return rrf


def merge_rrf_with_append(
    rrf_scores: dict[str, float],
    source_lists: dict[str, list[tuple[str, float, int]]],
    card_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """RRF 融合 BGE+BM25，然后 append exact_phrase + adjacent_card，去重排序。

    对标 WeKnora search_parallel.go:156 — entity/graph 结果直接 append + 去重。
    不做 top_k 截断 — 全部送入下游 cross-encoder/composite/MMR 处理。
    """
    merged: dict[str, dict[str, Any]] = {}

    # RRF candidates (BGE + BM25)
    for cid, rrf_score in rrf_scores.items():
        card = card_by_id.get(cid)
        if card is None:
            continue
        text_parts = [
            card.get("context_before", ""),
            card.get("knowledge", ""),
            card.get("citation", ""),
            card.get("context_after", ""),
        ]
        merged[cid] = {
            "card_id": cid,
            "score": rrf_score,
            "source": "rrf",
            "sources": [{"source": "rrf", "score": round(rrf_score, 6)}],
            "type": card.get("type", ""),
            "knowledge": card.get("knowledge", ""),
            "citation": card.get("citation", ""),
            "context_before": card.get("context_before", ""),
            "context_after": card.get("context_after", ""),
            "text": " ".join(x for x in text_parts if x),
        }

    # Append exact_phrase results
    for cid, score, _rank in source_lists.get("exact_phrase", []):
        if cid in merged:
            merged[cid]["score"] += score * 0.5
            merged[cid]["source"] += "+exact_phrase"
            merged[cid].setdefault("sources", []).append({"source": "exact_phrase", "score": round(score, 4)})
        else:
            card = card_by_id.get(cid)
            if card is None:
                continue
            merged[cid] = {
                "card_id": cid,
                "score": score,
                "source": "exact_phrase",
                "sources": [{"source": "exact_phrase", "score": round(score, 4)}],
                "type": card.get("type", ""),
                "knowledge": card.get("knowledge", ""),
                "citation": card.get("citation", ""),
                "context_before": card.get("context_before", ""),
                "context_after": card.get("context_after", ""),
                "text": " ".join(x for x in [card.get("context_before", ""), card.get("knowledge", ""), card.get("citation", ""), card.get("context_after", "")] if x),
            }

    # Append adjacent_card results
    for cid, score, _rank in source_lists.get("adjacent_card", []):
        if cid in merged:
            merged[cid]["score"] += score * 0.5
            merged[cid]["source"] += "+adjacent_card"
            merged[cid].setdefault("sources", []).append({"source": "adjacent_card", "score": round(score, 4)})
        else:
            card = card_by_id.get(cid)
            if card is None:
                continue
            merged[cid] = {
                "card_id": cid,
                "score": score,
                "source": "adjacent_card",
                "sources": [{"source": "adjacent_card", "score": round(score, 4)}],
                "type": card.get("type", ""),
                "knowledge": card.get("knowledge", ""),
                "citation": card.get("citation", ""),
                "context_before": card.get("context_before", ""),
                "context_after": card.get("context_after", ""),
                "text": " ".join(x for x in [card.get("context_before", ""), card.get("knowledge", ""), card.get("citation", ""), card.get("context_after", "")] if x),
            }

    return sorted(merged.values(), key=lambda c: c["score"], reverse=True)
