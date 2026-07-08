"""
Plan B / Step 5 v2：句卡到知识节点的证据挂载候选生成。

为什么新增本脚本：
- 旧版 05_mount_cards.py 以 citation 长串匹配 + BGE top1 为主，短句卡容易因缺少实体锚点而挂错。
- 典型问题：句卡“巩固各成员国之间的合作”本应挂到“GIABA的目标”，但旧版因 BGE 泛语义相似被挂到“金融行动特别工作组”。

本脚本的核心原则：
1. 原文证据优先：句卡 citation/knowledge 若出现在节点 evidence_span 中，直接作为强证据候选。
2. 教材位置优先：使用 card.source_line_start、card.chapter_path 与 node.section_node_id/section/subsection 对齐。
3. BGE 只做候选召回，不做最终裁决：保留 top-k 候选，并给出 source alignment 与 rerank 分。
4. 产物与主线分离：默认写入 work/planb_mounts/，不会覆盖 work/ch*/card_mounts*.jsonl。

输出：
- work/planb_mounts/card_candidates.jsonl
  每张句卡的候选节点列表，便于排查“为什么挂到这里”。
- work/planb_mounts/ch{n}/card_mounts_candidates.jsonl
  按节点聚合的候选挂载，供后续审核脚本或人工抽查使用。
- work/planb_mounts/ch{n}/card_mounts_strong.jsonl
  仅包含 evidence_span 命中的强证据挂载，可作为高精度子集。
- work/planb_mounts/summary.json
  统计信息。

用法：
    python 05_mount_cards_v2.py
    python 05_mount_cards_v2.py --no-bge
    python 05_mount_cards_v2.py --chapters 3 --top-k 8
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

_ROOT = Path(__file__).resolve().parent
_WORK = _ROOT / "work"
_WORKSPACE = Path(__file__).resolve().parents[3]
_CARDS_PATH = _WORKSPACE / "data" / "cards" / "cards_v6_sentence.json"
_OUT_ROOT = _WORK / "planb_mounts"


@dataclass
class Candidate:
    node_id: str
    method: str
    score: float
    source_alignment: str
    reason: str
    bge_score: float | None = None
    rank: int | None = None

    def to_dict(self) -> dict[str, Any]:
        row: dict[str, Any] = {
            "node_id": self.node_id,
            "method": self.method,
            "score": round(float(self.score), 4),
            "source_alignment": self.source_alignment,
            "reason": self.reason,
        }
        if self.bge_score is not None:
            row["bge_score"] = round(float(self.bge_score), 4)
        if self.rank is not None:
            row["rank"] = self.rank
        return row


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def norm(text: Any) -> str:
    s = unicodedata.normalize("NFKC", str(text or "")).lower()
    return re.sub(r"[\s·•。，“”\"'、；;：:（）()\[\]【】《》<>/\\\-—_]+", "", s)


def load_cards() -> list[dict[str, Any]]:
    data = read_json(_CARDS_PATH)
    cards = data.get("cards", [])
    if not isinstance(cards, list):
        raise ValueError(f"cards_v6_sentence.json 格式异常: {_CARDS_PATH}")
    return cards


def load_nodes(chapters: list[int]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for ch in chapters:
        nodes.extend(read_jsonl(_WORK / f"ch{ch}" / "nodes_accepted.jsonl"))
    return nodes


def load_leaf_sections(chapters: list[int]) -> dict[str, dict[str, Any]]:
    leaves: dict[str, dict[str, Any]] = {}
    for ch in chapters:
        for row in read_jsonl(_WORK / f"ch{ch}" / "leaf_sections.jsonl"):
            sid = row.get("section_node_id", "")
            if sid:
                leaves[sid] = row
    return leaves


def source_alignment(card: dict[str, Any], node: dict[str, Any], leaf: dict[str, Any] | None) -> str:
    line = card.get("source_line_start")
    if leaf and isinstance(line, int):
        start = leaf.get("line_start")
        end = leaf.get("line_end")
        if isinstance(start, int) and isinstance(end, int) and start <= line <= end:
            return "same_leaf"

    card_path = norm(card.get("chapter_path", ""))
    subsection = norm(node.get("subsection", ""))
    section = norm(node.get("section", ""))
    chapter = norm(node.get("chapter", ""))
    if subsection and subsection in card_path:
        return "same_subsection"
    if section and section in card_path:
        return "same_section"
    if chapter and chapter in card_path:
        return "same_chapter"
    return "none"


def alignment_bonus(alignment: str) -> float:
    return {
        "same_leaf": 0.22,
        "same_subsection": 0.16,
        "same_section": 0.08,
        "same_chapter": 0.03,
        "none": 0.0,
    }.get(alignment, 0.0)


def node_text_for_evidence(node: dict[str, Any]) -> str:
    return norm(" ".join([
        node.get("evidence_span", ""),
        node.get("definition", ""),
        node.get("title", ""),
    ]))


def node_text_for_bge(node: dict[str, Any]) -> str:
    return " ".join([
        node.get("title", ""),
        node.get("definition", ""),
        node.get("evidence_span", ""),
        node.get("section", ""),
        node.get("subsection", ""),
    ]).strip()


def card_text_for_bge(card: dict[str, Any]) -> str:
    return " ".join([
        card.get("knowledge", ""),
        card.get("citation", ""),
        card.get("context_before", ""),
        card.get("context_after", ""),
        card.get("chapter_path", ""),
    ]).strip()


def deterministic_candidates(
    card: dict[str, Any],
    nodes: list[dict[str, Any]],
    leaves: dict[str, dict[str, Any]],
) -> list[Candidate]:
    citation = norm(card.get("citation", ""))
    knowledge = norm(card.get("knowledge", ""))
    result: list[Candidate] = []

    for node in nodes:
        evidence = node_text_for_evidence(node)
        if not evidence:
            continue
        align = source_alignment(card, node, leaves.get(node.get("section_node_id", "")))

        if len(citation) >= 8 and citation in evidence:
            score = 1.0 if align != "none" else 0.98
            result.append(Candidate(
                node_id=node["node_id"],
                method="evidence_span_citation",
                score=score,
                source_alignment=align,
                reason="card.citation appears in node.evidence_span/definition/title",
            ))
            continue

        if len(knowledge) >= 10 and knowledge in evidence:
            score = 0.97 if align != "none" else 0.94
            result.append(Candidate(
                node_id=node["node_id"],
                method="evidence_span_knowledge",
                score=score,
                source_alignment=align,
                reason="card.knowledge appears in node.evidence_span/definition/title",
            ))

    return result


def merge_candidates(candidates: list[Candidate]) -> list[Candidate]:
    by_node: dict[str, Candidate] = {}
    for cand in candidates:
        old = by_node.get(cand.node_id)
        if old is None or cand.score > old.score:
            by_node[cand.node_id] = cand
    ranked = sorted(
        by_node.values(),
        key=lambda c: (
            c.method.startswith("evidence_span"),
            c.score,
            alignment_bonus(c.source_alignment),
            -(c.rank or 999),
        ),
        reverse=True,
    )
    for idx, cand in enumerate(ranked, start=1):
        cand.rank = idx
    return ranked


def bge_candidates(
    cards: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    leaves: dict[str, dict[str, Any]],
    top_k: int,
    min_score: float,
) -> dict[str, list[Candidate]]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)
    node_texts = [node_text_for_bge(n) for n in nodes]
    node_vecs = model.encode(node_texts, normalize_embeddings=True, batch_size=64)

    usable_cards = [
        card for card in cards
        if card.get("card_id", "") and card_text_for_bge(card)
    ]
    card_queries = [card_text_for_bge(card) for card in usable_cards]
    card_vecs = model.encode(card_queries, normalize_embeddings=True, batch_size=64)

    result: dict[str, list[Candidate]] = {}
    all_scores = card_vecs @ node_vecs.T
    for card_idx, card in enumerate(usable_cards):
        cid = card.get("card_id", "")
        scores = all_scores[card_idx]
        top_indices = np.argsort(scores)[::-1][:top_k]
        rows: list[Candidate] = []
        for rank, idx in enumerate(top_indices, start=1):
            bge_score = float(scores[idx])
            if bge_score < min_score:
                continue
            node = nodes[int(idx)]
            align = source_alignment(card, node, leaves.get(node.get("section_node_id", "")))
            final_score = min(1.0, bge_score + alignment_bonus(align))
            rows.append(Candidate(
                node_id=node["node_id"],
                method="bge_topk_rerank",
                score=final_score,
                bge_score=bge_score,
                source_alignment=align,
                rank=rank,
                reason="BGE top-k candidate reranked by source alignment",
            ))
        result[cid] = rows
    return result


def parse_chapters(value: str) -> list[int]:
    chapters = []
    for part in value.split(","):
        part = part.strip()
        if part:
            chapters.append(int(part))
    return chapters or [2, 3, 4, 5]


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan B 句卡挂载候选生成")
    parser.add_argument("--chapters", default="2,3,4,5", help="章节列表，如 3 或 2,3,4,5")
    parser.add_argument("--top-k", type=int, default=5, help="BGE 召回候选数")
    parser.add_argument("--min-score", type=float, default=0.5, help="BGE 最低召回分")
    parser.add_argument("--no-bge", action="store_true", help="只跑 evidence/source 规则，不加载 BGE")
    parser.add_argument("--out-dir", default=str(_OUT_ROOT), help="输出目录，默认 work/planb_mounts")
    args = parser.parse_args()

    chapters = parse_chapters(args.chapters)
    out_root = Path(args.out_dir)
    cards = load_cards()
    nodes = load_nodes(chapters)
    leaves = load_leaf_sections(chapters)
    node_map = {n["node_id"]: n for n in nodes}

    if not cards or not nodes:
        raise SystemExit("[FAIL] cards 或 nodes 为空")

    print(f"Plan B mount: cards={len(cards)}, nodes={len(nodes)}, chapters={chapters}")

    det_by_card: dict[str, list[Candidate]] = {}
    for card in cards:
        cid = card.get("card_id", "")
        if not cid:
            continue
        det_by_card[cid] = deterministic_candidates(card, nodes, leaves)

    bge_by_card: dict[str, list[Candidate]] = {}
    if not args.no_bge:
        try:
            bge_by_card = bge_candidates(cards, nodes, leaves, args.top_k, args.min_score)
        except Exception as exc:
            print(f"[WARN] BGE 召回失败，仅输出规则候选: {exc}")
            bge_by_card = {}

    card_rows: list[dict[str, Any]] = []
    node_candidates: dict[str, list[dict[str, Any]]] = defaultdict(list)
    node_strong: dict[str, list[dict[str, Any]]] = defaultdict(list)
    stats = Counter()

    for card in cards:
        cid = card.get("card_id", "")
        if not cid:
            continue
        candidates = merge_candidates(det_by_card.get(cid, []) + bge_by_card.get(cid, []))
        if not candidates:
            stats["unmatched_cards"] += 1
            continue

        card_rows.append({
            "card_id": cid,
            "citation": card.get("citation", ""),
            "chapter_path": card.get("chapter_path", ""),
            "source_line_start": card.get("source_line_start"),
            "candidates": [c.to_dict() for c in candidates],
        })
        stats["cards_with_candidates"] += 1
        if any(c.method.startswith("evidence_span") for c in candidates):
            stats["cards_with_strong_evidence"] += 1

        for cand in candidates:
            node = node_map.get(cand.node_id, {})
            row = {
                "card_id": cid,
                **cand.to_dict(),
                "node_title": node.get("title", ""),
                "node_section": node.get("section", ""),
                "node_subsection": node.get("subsection", ""),
            }
            node_candidates[cand.node_id].append(row)
            if cand.method.startswith("evidence_span"):
                node_strong[cand.node_id].append(row)

    write_jsonl(out_root / "card_candidates.jsonl", card_rows)

    for ch in chapters:
        ch_node_ids = [n["node_id"] for n in nodes if f":C{ch:02d}:" in n["node_id"]]
        candidate_rows = [
            {"node_id": nid, "cards": node_candidates[nid]}
            for nid in ch_node_ids
            if node_candidates.get(nid)
        ]
        strong_rows = [
            {"node_id": nid, "cards": node_strong[nid]}
            for nid in ch_node_ids
            if node_strong.get(nid)
        ]
        write_jsonl(out_root / f"ch{ch}" / "card_mounts_candidates.jsonl", candidate_rows)
        write_jsonl(out_root / f"ch{ch}" / "card_mounts_strong.jsonl", strong_rows)

    summary = {
        "cards": len(cards),
        "nodes": len(nodes),
        "chapters": chapters,
        "out_root": str(out_root),
        "top_k": args.top_k,
        "min_score": args.min_score,
        "bge_enabled": not args.no_bge and bool(bge_by_card),
        **dict(stats),
    }
    (out_root / "summary.json").parent.mkdir(parents=True, exist_ok=True)
    (out_root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
