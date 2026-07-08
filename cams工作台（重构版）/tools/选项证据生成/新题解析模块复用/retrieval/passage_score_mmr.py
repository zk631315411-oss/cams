"""
P1.3 + P1.4 + P2: Passage 构建, 复合分合成, Jaccard MMR

对标 WeKnora:
  P1.3 clean_passage → cleanPassageForRerank  [rerank.go:613]
       build_passage → getEnrichedPassage      [rerank.go:664]
  P1.4 compute_composite → compositeScore      [rerank.go:453]
  P2   jaccard_mmr      → applyMMR             [rerank.go:477]

插入位置: run_bindings.py, plan_for_query_type() 之前 (line ~2587)
"""
from __future__ import annotations

import re
from typing import Any


# ========================================================================
# P1.3: Passage 构建
# ========================================================================

def clean_card_text(text: str) -> str:
    """对标 WeKnora cleanPassageForRerank [rerank.go:613].

    精简版：句卡 citation 已是从 v6_clean.md 提取的原文，比较干净。
    只做基础清洗：去多余换行、连续空格、首尾空白。
    """
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def build_passage(card: dict[str, Any]) -> str:
    """对标 WeKnora getEnrichedPassage [rerank.go:664].

    构建裁判和 cross-encoder 看到的完整 passage 文本。
    WeKnora 合并 Content + ImageInfo + GeneratedQuestions。
    对应我们：knowledge + 主文本 + enrichment_context。

    主文本优先级：expanded_text > citation
    """
    parts: list[str] = []

    knowledge = str(card.get("knowledge", "") or "").strip()
    if knowledge:
        parts.append(f"[{knowledge}]")

    expanded = str(card.get("expanded_text", "") or "").strip()
    if expanded:
        parts.append(expanded)
    else:
        citation = str(card.get("citation", "") or "").strip()
        if citation:
            parts.append(citation)

    enrichment = str(card.get("enrichment_context", "") or "").strip()
    if enrichment:
        parts.append(enrichment)

    return clean_card_text("\n".join(parts))


def build_ce_passage(card: dict[str, Any]) -> str:
    """CE 专用精简版：只含 knowledge + citation，不含父块/expansion/enrichment。

    对标 WeKnora getEnrichedPassage[rerank.go:664] — CE 仅使用子块原始 content
    （+ imageInfo + generatedQuestions），父块替换在 merge 阶段（CE 之后）。
    """
    parts: list[str] = []

    knowledge = str(card.get("knowledge", "") or "").strip()
    if knowledge:
        parts.append(f"[{knowledge}]")

    citation = str(card.get("citation", "") or "").strip()
    if citation:
        parts.append(citation)

    return clean_card_text("\n".join(parts))


# ========================================================================
# P1.4: 复合分合成
# ========================================================================

# source_weight 映射。对标 WeKnora 的 sourceWeight 逻辑。
# direct/bridge/sufficiency 是直接检索意图 → 最高权重
# kg 来自图谱导航 → 略降权
# base 是通用检索 → 再降
# negative 是反证 → 最低（用于排除而非支持）
_SOURCE_WEIGHTS: dict[str, float] = {
    "direct": 1.0,
    "bridge": 1.0,
    "sufficiency": 1.0,
    "kg": 0.95,
    "kg_direct": 0.95,
    "kg_bridge": 0.95,
    "kg_sufficiency": 0.95,
    "kg_negative": 0.95,
    "base": 0.9,
    "negative": 0.85,
}


def _best_source_weight(retrieval_types: list[str] | None) -> float:
    if not retrieval_types:
        return 0.9
    return max((_SOURCE_WEIGHTS.get(t, 0.9) for t in retrieval_types), default=0.9)


def compute_composite_score(
    rerank_score: float | None,
    retrieval_score: float,
    retrieval_types: list[str] | None = None,
) -> float:
    """对标 WeKnora compositeScore [rerank.go:453].

    composite = 0.6 * rerank + 0.3 * retrieval + 0.1 * source_weight
    无 re-rank 时直接返回检索分。
    """
    if rerank_score is None:
        return retrieval_score
    sw = _best_source_weight(retrieval_types)
    composite = 0.6 * rerank_score + 0.3 * retrieval_score + 0.1 * sw
    return max(0.0, min(1.0, composite))


# ========================================================================
# P2: Jaccard MMR
# ========================================================================

def _tokenize(text: str) -> set[str]:
    """中文 bigram token 化。对标 WeKnora TokenizeSimple。

    bigram 对中文兼顾词边界鲁棒性和区分度。
    "起诉追究责任" → {"起诉", "诉追", "追究", "究责", "责任"}
    同时保留单字，防极短文本无 bigram。
    """
    cleaned = clean_card_text(text)
    if not cleaned:
        return set()
    chars = list(cleaned)
    bigrams: set[str] = set()
    for i in range(len(chars) - 1):
        bigrams.add(chars[i] + chars[i + 1])
    bigrams.update(chars)  # 保留单字
    return bigrams


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def jaccard_mmr(
    candidates: list[dict[str, Any]],
    *,
    lambda_: float = 0.7,
    top_k: int = 45,
) -> list[dict[str, Any]]:
    """对标 WeKnora applyMMR [rerank.go:477].

    使用 Jaccard 相似度 (token 级词集合) 做 greedy MMR:
    MMR = lambda_ * relevance - (1 - lambda_) * max(Jaccard(c, selected))

    对比 BGE 余弦 MMR 的优势:
    - Jaccard 只看词集重叠，不依赖向量质量
    - 对中文短文本更鲁棒（bigram 级匹配）
    - 计算 token 集合操作比向量点积更快

    score 来源：final_score（如果已合成）否则 retrieval score。
    """
    if not candidates or len(candidates) <= 1:
        return list(candidates)

    k = min(top_k, len(candidates))

    # 预计算每条候选的 token set 和分数
    token_sets: list[set[str]] = []
    scores: list[float] = []
    for c in candidates:
        text = str(c.get("passage", "") or c.get("expanded_text", "") or c.get("citation", "") or "")
        token_sets.append(_tokenize(text))
        scores.append(float(c.get("final_score", c.get("score", 0)) or 0))

    # 归一化分数到 [0, 1]
    max_score = max(scores) if scores else 1.0
    if max_score > 0:
        scores = [s / max_score for s in scores]

    # Greedy MMR 选择
    selected: list[int] = [0]  # 最高分先入选
    remaining: set[int] = set(range(1, len(candidates)))

    for _ in range(1, k):
        best_idx = -1
        best_mmr = -1.0
        for i in remaining:
            relevance = scores[i]
            max_sim = max(
                (_jaccard(token_sets[i], token_sets[s]) for s in selected),
                default=0.0,
            )
            mmr = lambda_ * relevance - (1.0 - lambda_) * max_sim
            if mmr > best_mmr:
                best_mmr = mmr
                best_idx = i
        if best_idx < 0:
            break
        selected.append(best_idx)
        remaining.discard(best_idx)

    return [candidates[i] for i in selected]
