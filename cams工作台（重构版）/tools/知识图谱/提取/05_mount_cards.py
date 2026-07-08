"""
Step 5：句卡挂载候选生成（纯机械，不调 LLM）。

两路挂载：
- 路 A：citation 字符串包含匹配（确定性，score=1.0）
- 路 B：BGE 向量搜索（兜底，score≥0.5）

产出的挂载候选后续由 05a_audit_mount.py 审核。

输入：cards_v6_sentence.json + 各章的 nodes_accepted.jsonl
输出：各章的 card_mounts.jsonl
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

_WORK = Path(__file__).resolve().parent / "work"
_WORKSPACE = Path(__file__).resolve().parents[3]
_CARDS_PATH = _WORKSPACE / "data" / "cards" / "cards_v6_sentence.json"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    cards = read_json(_CARDS_PATH).get("cards", [])
    if not cards:
        print("[FAIL] cards_v6_sentence.json 为空")
        return 1

    # 加载所有通过节点
    all_nodes: list[dict] = []
    for ch in [2, 3, 4, 5]:
        nodes = read_jsonl(_WORK / f"ch{ch}" / "nodes_accepted.jsonl")
        all_nodes.extend(nodes)
    print(f"句卡: {len(cards)} 张, 节点: {len(all_nodes)} 个")

    # 路 A：citation 字符串匹配
    card_to_node: dict[str, list[dict]] = {}  # card_id → [{node_id, method, score}]
    unmatched_cards: list[dict] = []

    for card in cards:
        cid = card.get("card_id", "")
        citation = (card.get("citation") or "").strip()
        knowledge = (card.get("knowledge") or "").strip()
        if not cid or not citation:
            continue

        matched = []
        for node in all_nodes:
            node_text = (node.get("evidence_span") or "") + " " + (node.get("definition") or "")
            if len(citation) >= 30 and citation[:30] in node_text:
                matched.append({"node_id": node["node_id"], "method": "citation", "score": 1.0})
                break
            elif len(knowledge) >= 15 and knowledge[:15] in node_text:
                matched.append({"node_id": node["node_id"], "method": "citation_knowledge", "score": 0.95})
                break

        if matched:
            card_to_node[cid] = matched
        else:
            unmatched_cards.append(card)

    # 路 B：BGE 兜底
    if unmatched_cards:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)
        node_texts = [n.get("definition", "") + " " + n.get("title", "") for n in all_nodes]
        node_vecs = model.encode(node_texts, normalize_embeddings=True)

        for card in unmatched_cards:
            cid = card.get("card_id", "")
            query = (card.get("knowledge") or "") + " " + (card.get("citation") or "")[:200]
            q_vec = model.encode([query], normalize_embeddings=True)
            scores = (node_vecs @ q_vec.T).flatten()
            best_idx = int(np.argmax(scores))
            best_score = float(scores[best_idx])
            if best_score >= 0.5:
                card_to_node[cid] = [{"node_id": all_nodes[best_idx]["node_id"],
                                       "method": "bge", "score": round(best_score, 4)}]

    # 按节点汇总
    node_mounts: dict[str, list[dict]] = {}
    for cid, mounts in card_to_node.items():
        for m in mounts:
            nid = m["node_id"]
            node_mounts.setdefault(nid, []).append({
                "card_id": cid, "method": m["method"], "score": m["score"]
            })

    # 按章节写入
    node_chapter: dict[str, int] = {}
    for n in all_nodes:
        # node_id format: cams_v6:C02:S01:U01:N000
        m = re.match(r"cams_v6:C(\d+)", n.get("node_id", ""))
        if m:
            node_chapter[n["node_id"]] = int(m.group(1))

    by_chapter: dict[int, list[dict]] = {}
    for nid, cards_list in node_mounts.items():
        ch = node_chapter.get(nid, 0)
        by_chapter.setdefault(ch, []).append({"node_id": nid, "cards": cards_list})

    total = 0
    for ch in [2, 3, 4, 5]:
        mounts = by_chapter.get(ch, [])
        out_path = _WORK / f"ch{ch}" / "card_mounts.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for m in mounts:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
        card_count = sum(len(m["cards"]) for m in mounts)
        total += card_count
        print(f"  ch{ch}: {len(mounts)} 节点, {card_count} 张卡挂载 → {out_path}")

    # 统计
    citation_count = sum(1 for mounts in card_to_node.values()
                         for m in mounts if m["method"] == "citation")
    bge_direct = sum(1 for mounts in card_to_node.values()
                     for m in mounts if m["score"] >= 0.7)
    bge_weak = sum(1 for mounts in card_to_node.values()
                   for m in mounts if 0.5 <= m["score"] < 0.7)
    print(f"\n路A(citation): {citation_count}")
    print(f"路B BGE≥0.7: {bge_direct}")
    print(f"路B BGE 0.5-0.7: {bge_weak}")
    print(f"总计: {total} 条挂载, {len(card_to_node)} 张句卡已挂载")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
