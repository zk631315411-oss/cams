"""
P1.2: 检索后候选富集

对标 WeKnora processSearchResults → collectEnrichmentChunkIDs
[knowledgebase_search_results.go:129]

对合并后的候选列表补:
  1. nearby 邻卡 (window=1, 沿 Prev/Next 各取一张)
  2. KG node definition (通过 card_id → node_ids 反查节点定义)
  3. KG neighbor mounted cards (沿 KG 邻居取挂载句卡, 限制2邻居)
"""
from __future__ import annotations

from typing import Any


def enrich_candidates(
    candidates: list[dict[str, Any]],
    adjacency: dict[str, dict[str, str | None]],
    card_by_id: dict[str, dict[str, Any]],
    kg_nodes: dict[str, dict[str, Any]] | None = None,
    card_to_nodes: dict[str, list[str]] | None = None,
    node_cards: dict[str, list[str]] | None = None,
    neighbors: dict[str, list[tuple[str, dict[str, Any]]]] | None = None,
    *,
    nearby_window: int = 1,
    max_card_nodes: int = 3,
    max_kg_neighbors: int = 2,
    max_neighbor_cards: int = 3,
) -> list[dict[str, Any]]:
    """对标 WeKnora collectEnrichmentChunkIDs + assembleSearchResults。"""
    for card in candidates:
        card.setdefault("enrichment_sources", [])
        enrichment_parts: list[str] = []

        # 1. nearby 邻卡
        adj = adjacency.get(card.get("card_id", ""))
        nearby_ids: list[str] = []
        if adj:
            for direction in ("prev", "next"):
                cursor = adj.get(direction)
                for _ in range(nearby_window):
                    if cursor is None:
                        break
                    nc = card_by_id.get(cursor)
                    if nc:
                        nearby_ids.append(cursor)
                        knowledge = str(nc.get("knowledge", "") or "").strip()
                        citation = str(nc.get("citation", "") or "").strip()
                        if knowledge:
                            enrichment_parts.append(f"[近邻 {knowledge}] {citation}")
                        else:
                            enrichment_parts.append(f"[近邻] {citation}")
                    cursor = adjacency.get(cursor, {}).get(direction) if cursor in adjacency else None
        card["nearby_card_ids"] = nearby_ids
        card["enrichment_sources"].extend(
            {"type": "nearby", "card_id": cid} for cid in nearby_ids
        )

        # 2. KG node definitions. One card can mount to multiple KG nodes; cap
        # the fan-out so the adjudicator context stays readable.
        cid = card.get("card_id", "")
        kg_node_ids: list[str] = []
        if kg_nodes and card_to_nodes and cid in card_to_nodes:
            kg_node_ids = list(card_to_nodes.get(cid, []) or [])[:max_card_nodes]
            for node_id in kg_node_ids:
                node = kg_nodes.get(node_id)
                if not node:
                    continue
                definition = str(node.get("definition", "") or "").strip()
                if definition:
                    enrichment_parts.append(f"[知识点] {definition}")
                    card["enrichment_sources"].append({"type": "kg_node", "node_id": node_id})
            if kg_node_ids:
                card["kg_node_ids"] = kg_node_ids
                card["kg_node_id"] = kg_node_ids[0]

        # 3. KG neighbor mounted cards
        if kg_node_ids and neighbors and node_cards:
            kg_neighbor_ids: list[str] = []
            for kg_node_id in kg_node_ids:
                neighbor_list = neighbors.get(kg_node_id, [])[:max_kg_neighbors]
                for edge_dict in neighbor_list:
                    neighbor_id = edge_dict.get("node_id", "") if isinstance(edge_dict, dict) else ""
                    mounted = node_cards.get(neighbor_id, [])[:max_neighbor_cards]
                    for mc in mounted:
                        mc_id = mc.get("card_id", "") if isinstance(mc, dict) else str(mc)
                        if mc_id and mc_id not in kg_neighbor_ids:
                            kg_neighbor_ids.append(mc_id)
                        nc = card_by_id.get(mc_id)
                        if nc:
                            knowledge = str(nc.get("knowledge", "") or "").strip()
                            citation = str(nc.get("citation", "") or "").strip()
                            if knowledge:
                                enrichment_parts.append(f"[关联 {knowledge}] {citation}")
                            else:
                                enrichment_parts.append(f"[关联] {citation}")
            card["kg_neighbor_card_ids"] = kg_neighbor_ids

        if enrichment_parts:
            card["enrichment_context"] = "\n".join(enrichment_parts)

    return candidates
