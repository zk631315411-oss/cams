"""
Step 5：最终组装 → kg_data.json

对标高代 08a_assemble_final_graph.py + 08_import_neo4j.py 精简版。
不需要 Neo4j，直接输出前端可读的 JSON。

流程：
1. 收集各章通过审核的节点 + 边
2. 跨章去重（同名节点合并、同 source+target+type 边去重）
3. 句卡挂载到节点（citation 匹配 + BGE 兜底）
4. 输出 data/derived/kg_data.json
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

_WORK = Path(__file__).resolve().parent / "work"
_WORKSPACE = Path(__file__).resolve().parents[3]
_CARDS_PATH = _WORKSPACE / "data" / "cards" / "cards_v6_sentence.json"
_OUT_PATH = _WORKSPACE / "data" / "derived" / "kg_data.json"

# 6 种关系类型
EDGE_TYPES = {"包含", "并列", "导致", "缓解", "前提", "依据"}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# ── Step 1: 收集各章节点 + 边 ──

def collect_all() -> tuple[list[dict], list[dict]]:
    """收集所有章节通过审核的节点和边"""
    all_nodes: list[dict] = []
    all_edges: list[dict] = []

    for ch in [2, 3, 4, 5]:
        # 04b 终裁后 accepted 池包含 03a 初裁 accept + 04b 终裁 accept
        nodes = read_jsonl(_WORK / f"ch{ch}" / "nodes_accepted.jsonl")
        edges = read_jsonl(_WORK / f"ch{ch}" / "edges_accepted.jsonl")
        all_nodes.extend(nodes)
        all_edges.extend(edges)
        print(f"  ch{ch}: {len(nodes)} 节点, {len(edges)} 边")

    return all_nodes, all_edges


# ── Step 2: 跨章去重 ──

def deduplicate_nodes(nodes: list[dict]) -> list[dict]:
    """同名节点去重，保留第一个"""
    seen: set[str] = set()
    result: list[dict] = []
    for n in nodes:
        key = n.get("title", "").strip()
        if not key:
            result.append(n)
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(n)
    return result


def deduplicate_edges(edges: list[dict]) -> list[dict]:
    """同 source+target+type 边去重"""
    seen: set[str] = set()
    result: list[dict] = []
    for e in edges:
        key = f'{e.get("source_node_id","")}|{e.get("target_node_id","")}|{e.get("type","")}'
        if key in seen:
            continue
        seen.add(key)
        result.append(e)
    return result


# ── Step 3: 句卡挂载 ──

def mount_cards(nodes: list[dict]) -> dict[str, str]:
    """
    从审核后的挂载文件读取，只用 accept 的挂载。
    返回 {card_id: node_title}
    """
    node_titles = {n["node_id"]: n.get("title", "") for n in nodes}
    card_to_section: dict[str, str] = {}

    for ch in [2, 3, 4, 5]:
        path = _WORK / f"ch{ch}" / "card_mounts_audited.jsonl"
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                m = json.loads(line)
                nid = m["node_id"]
                title = node_titles.get(nid, "")
                if not title:
                    continue
                for c in m.get("cards", []):
                    if c.get("decision") == "accept":
                        card_to_section[c["card_id"]] = title

    return card_to_section


# ── Step 4: 构建 kg_data.json ──

def build_kg_data(
    nodes: list[dict],
    edges: list[dict],
    card_to_section: dict[str, str],
) -> dict:
    """输出前端兼容的 kg_data.json 格式"""
    # card_id → section
    result: dict[str, Any] = {}
    for cid, section in card_to_section.items():
        result[cid] = {"section": section, "edges": []}

    # _edges：概念间关系
    _edges: list[dict] = []
    node_title_set = {n.get("title", "") for n in nodes}

    for e in edges:
        src_id = e.get("source_node_id", "")
        tgt_id = e.get("target_node_id", "")

        # 从 node_id 找 title
        src_title = ""
        tgt_title = ""
        for n in nodes:
            if n.get("node_id") == src_id:
                src_title = n.get("title", "")
            if n.get("node_id") == tgt_id:
                tgt_title = n.get("title", "")

        if src_title and tgt_title:
            _edges.append({
                "from": src_title,
                "to": tgt_title,
                "type": e.get("type", ""),
                "detail": e.get("detail", ""),
            })
            # 把边也挂到两端节点相关的句卡上
            for cid, section in card_to_section.items():
                if section in (src_title, tgt_title):
                    if cid in result:
                        result[cid]["edges"].append({
                            "from": src_title,
                            "to": tgt_title,
                            "type": e.get("type", ""),
                        })

    result["_edges"] = _edges
    result["_stats"] = {
        "nodes": len(nodes),
        "edges": len(_edges),
        "cards_mounted": len(card_to_section),
        "total_cards": 5199,
    }
    return result


# ── 主流程 ──

def main(mock: bool = False) -> int:
    print("=== Step 5: 最终组装 ===")
    print()

    # 1. 收集
    print("[1/4] 收集各章节点 + 边")
    nodes, edges = collect_all()
    print(f"  总计: {len(nodes)} 节点, {len(edges)} 边")

    # 2. 去重
    print("[2/4] 跨章去重")
    nodes = deduplicate_nodes(nodes)
    edges = deduplicate_edges(edges)
    print(f"  去重后: {len(nodes)} 节点, {len(edges)} 边")
    type_counts = Counter(e.get("type", "") for e in edges)
    print(f"  边类型分布: {dict(type_counts)}")

    # 3. 挂载
    if mock:
        card_to_section = {}
        print("[3/4] 挂载跳过 (--mock)")
    else:
        print("[3/4] 句卡挂载")
        card_to_section = mount_cards(nodes)
        print(f"  挂载: {len(card_to_section)} 张卡")

    # 4. 构建
    print("[4/4] 构建 kg_data.json")
    kg = build_kg_data(nodes, edges, card_to_section)

    _OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _OUT_PATH.write_text(json.dumps(kg, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  -> {_OUT_PATH}")
    print(f"  stats: {json.dumps(kg['_stats'], ensure_ascii=False)}")

    return 0


if __name__ == "__main__":
    import sys
    mock = "--mock" in sys.argv
    raise SystemExit(main(mock=mock))
