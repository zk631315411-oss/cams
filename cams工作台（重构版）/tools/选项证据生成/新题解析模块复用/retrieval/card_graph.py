"""
P0.1 + P0.2 + P0.3 + P1.5: 句卡链表、父块索引、短文本扩展、父块替换

对标 WeKnora:
  P0.1 build_card_adjacency  → Chunk.PreChunkID / NextChunkID  [chunk.go:113]
  P0.2 build_parent_blocks   → parent_text chunks              [knowledge_process.go:379]
  P0.3 expand_short_cards    → expandShortContextWithNeighbors [merge_expand.go:10]
  P1.5 resolve_parent_block  → resolveParentChunks             [merge.go:210]
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


# ========================================================================
# P0.1: 句卡链表索引
# ========================================================================

def build_card_adjacency(cards: list[dict[str, Any]]) -> dict[str, dict[str, str | None]]:
    """从 card_id 序列推导相邻关系，对标 WeKnora Chunk.PreChunkID/NextChunkID。

    规则：
    - 按 chapter_path 分组
    - 组内按 source_line_start 升序
    - 排序后依次链接: cards[i].next = cards[i+1].id
    - 跨 chapter 边界不断链 (prev/next = None)
    """
    from collections import defaultdict

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        cp = card.get("chapter_path", "") or ""
        groups[cp].append(card)

    adjacency: dict[str, dict[str, str | None]] = {}
    for cp, group in groups.items():
        sorted_group = sorted(group, key=lambda c: int(c.get("source_line_start", 0) or 0))
        for i, card in enumerate(sorted_group):
            cid = card["card_id"]
            prev_id = sorted_group[i - 1]["card_id"] if i > 0 else None
            next_id = sorted_group[i + 1]["card_id"] if i < len(sorted_group) - 1 else None
            adjacency[cid] = {"prev": prev_id, "next": next_id}

    return adjacency


# ========================================================================
# P0.2: 父块索引
# ========================================================================

def build_parent_blocks(cards: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """按 chapter_path (H4 节) 分组，构建父块索引。

    每个父块：
    - parent_id = chapter_path
    - content = 该节下所有句卡的 citation 按 source_line_start 顺序拼接
    - child_ids = 该节下所有 card_id

    对标 WeKnora 的 parent_text Chunk（存 DB、不建索引、只用于替换）。
    """
    from collections import defaultdict

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for card in cards:
        cp = card.get("chapter_path", "") or ""
        groups[cp].append(card)

    parent_blocks: dict[str, dict[str, Any]] = {}
    for cp, group in groups.items():
        sorted_group = sorted(group, key=lambda c: int(c.get("source_line_start", 0) or 0))
        parent_content = "\n".join(
            c.get("citation", "") for c in sorted_group if c.get("citation")
        )
        parent_blocks[cp] = {
            "parent_id": cp,
            "content": parent_content,
            "child_ids": [c["card_id"] for c in sorted_group],
            "title": cp.split(" > ")[-1] if " > " in cp else cp,
        }

    return parent_blocks

# card_id → parent_id 的反向查找
def build_card_to_parent(cards: list[dict[str, Any]]) -> dict[str, str]:
    """构建 card_id → chapter_path (parent_id) 的映射。"""
    return {c["card_id"]: (c.get("chapter_path", "") or "") for c in cards}


# ========================================================================
# P0.3: 短句卡沿链表扩展
# ========================================================================

def _current_context_text(card: dict[str, Any]) -> str:
    return str(card.get("expanded_text", "") or card.get("citation", "") or "")

def expand_short_cards(
    candidates: list[dict[str, Any]],
    adjacency: dict[str, dict[str, str | None]],
    card_by_id: dict[str, dict[str, Any]],
    *,
    min_chars: int = 350,
    target_chars: int = 850,
    max_window: int = 3,
) -> list[dict[str, Any]]:
    """对标 WeKnora expandShortContextWithNeighbors [merge_expand.go:10]。

    对 content < min_chars(350) 的文本块，沿 prev/next 链表扩展，
    直到达到 target_chars(850) 或耗尽邻居。同 chapter_path 约束。

    结果存入 expanded_text 和 expanded_card_ids 字段。
    原始 citation 保持不变。

    WeKnora 原版 minLen=350 针对英文段落。中文句卡普遍 30-150 字，
    350 阈值意味着大部分句卡不会被扩展，与 WeKnora 行为一致。
    """
    for card in candidates:
        citation = str(card.get("citation", "") or "")
        base_text = _current_context_text(card)
        if len(base_text) >= min_chars:
            continue

        adj = adjacency.get(card["card_id"])
        if adj is None:
            continue

        # 向前扩展
        prev_texts: list[str] = []
        prev_ids: list[str] = []
        cursor = adj["prev"]
        for _ in range(max_window):
            if cursor is None:
                break
            pc = card_by_id.get(cursor)
            if pc is None:
                break
            t = str(pc.get("citation", "") or "")
            prev_texts.insert(0, t)
            prev_ids.insert(0, cursor)
            if len("".join(prev_texts) + citation) >= target_chars:
                break
            cursor = adjacency.get(cursor, {}).get("prev") if cursor in adjacency else None

        # 向后扩展
        next_texts: list[str] = []
        next_ids: list[str] = []
        cursor = adj["next"]
        current_len = len("".join(prev_texts) + citation)
        for _ in range(max_window):
            if cursor is None:
                break
            nc = card_by_id.get(cursor)
            if nc is None:
                break
            t = str(nc.get("citation", "") or "")
            next_texts.append(t)
            next_ids.append(cursor)
            if current_len + len("".join(next_texts)) >= target_chars:
                break
            cursor = adjacency.get(cursor, {}).get("next") if cursor in adjacency else None

        if prev_texts or next_texts:
            card["expanded_text"] = "".join(prev_texts) + base_text + "".join(next_texts)
            card["expanded_card_ids"] = prev_ids + [card["card_id"]] + next_ids

    return candidates


# ========================================================================
# P1.5: 父块替换 (re-rank 之后, 裁判之前)
# ========================================================================

def resolve_parent_block(
    candidates: list[dict[str, Any]],
    parent_blocks: dict[str, dict[str, Any]],
    card_to_parent: dict[str, str],
) -> list[dict[str, Any]]:
    """对标 WeKnora resolveParentChunks [merge.go:210]。

    精排后的候选，将子块内容替换为整个 H4 父块段落的完整文本。
    子块 card_id 记入 source_card_id 溯源。

    严格按 WeKnora 计划：即使此前已有兄弟链扩展，rerank 后也用父块
    段落作为裁判上下文。原始句卡 citation 保持在候选对象中用于最终引用。
    """
    for card in candidates:
        cid = card.get("card_id", "")
        parent_id = card_to_parent.get(cid, "")
        if not parent_id:
            continue
        parent = parent_blocks.get(parent_id)
        if parent is None:
            continue
        card["source_card_id"] = cid
        if card.get("expanded_text"):
            card["sibling_expanded_text"] = card.get("expanded_text")
            card["sibling_expanded_card_ids"] = card.get("expanded_card_ids", [])
        card["expanded_text"] = parent["content"]
        card["parent_id"] = parent_id

    return candidates


def expand_with_neighbors(
    candidates: list[dict[str, Any]],
    adjacency: dict[str, dict[str, str | None]],
    card_by_id: dict[str, dict[str, Any]],
    *,
    window: int = 5,
    score_discount: float = 0.5,
) -> list[dict[str, Any]]:
    """沿兄弟链扩展邻居卡，将段落级上下文注入候选池。

    对每张候选卡沿 prev/next 各取 window 张邻居，作为新候选加入池中。
    邻居分数 = 源卡分数 × score_discount。
    对标 WeKnora collectEnrichmentChunkIDs 的 nearby 扩展。
    """
    existing_ids: set[str] = {c["card_id"] for c in candidates if c.get("card_id")}
    new_candidates: dict[str, dict[str, Any]] = {}

    for src_card in candidates:
        src_id = src_card.get("card_id", "")
        adj = adjacency.get(src_id)
        if adj is None:
            continue
        src_score = float(src_card.get("score", 0) or 0)

        for direction in ("prev", "next"):
            cursor = adj[direction]
            for _ in range(window):
                if cursor is None:
                    break
                if cursor in existing_ids or cursor in new_candidates:
                    cursor = adjacency.get(cursor, {}).get(direction)
                    continue
                nc = card_by_id.get(cursor)
                if nc is None:
                    break
                discounted = src_score * score_discount
                text_parts = [
                    nc.get("context_before", ""),
                    nc.get("knowledge", ""),
                    nc.get("citation", ""),
                    nc.get("context_after", ""),
                ]
                new_candidates[cursor] = {
                    "card_id": cursor,
                    "score": discounted,
                    "source": f"{src_card.get('source', '')}+neighbor",
                    "sources": [{"source": "neighbor_expand", "score": round(discounted, 4),
                                 "via": src_id, "direction": direction}],
                    "type": nc.get("type", ""),
                    "knowledge": nc.get("knowledge", ""),
                    "citation": nc.get("citation", ""),
                    "context_before": nc.get("context_before", ""),
                    "context_after": nc.get("context_after", ""),
                    "text": " ".join(x for x in text_parts if x),
                }
                cursor = adjacency.get(cursor, {}).get(direction)

    return candidates + list(new_candidates.values())
