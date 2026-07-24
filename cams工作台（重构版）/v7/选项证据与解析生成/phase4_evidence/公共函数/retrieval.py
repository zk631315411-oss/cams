# -*- coding: utf-8 -*-
"""公共检索 — BGE/BM25 搜索原语。"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from 公共函数.index import BM25, get_bge_model
from 公共函数.candidate import make_candidate


def bge_search(query: str, bge_vecs: np.ndarray, card_ids: list[str],
               unit_lookup: dict[str, dict], top_k: int=20) -> list[dict[str, Any]]:
    if not query.strip(): return []
    model = get_bge_model()
    sims = cosine_similarity(model.encode([query], normalize_embeddings=True), bge_vecs)[0]
    results = []
    for rank, idx in enumerate(np.argsort(sims)[::-1][:top_k], start=1):
        unit = unit_lookup.get(card_ids[idx], {})
        results.append(make_candidate(unit, route="bge", score=round(float(sims[idx]), 6),
            rank=rank))
    return results


def bm25_search(query: str, bm25_index: BM25, card_ids: list[str],
                unit_lookup: dict[str, dict], top_k: int=20) -> list[dict[str, Any]]:
    if not query.strip(): return []
    results = []
    for rank, (doc_idx, score) in enumerate(bm25_index.search(query, top_k=top_k), start=1):
        unit = unit_lookup.get(card_ids[doc_idx], {})
        results.append(make_candidate(unit, route="bm25", score=round(score, 6), rank=rank))
    return results
