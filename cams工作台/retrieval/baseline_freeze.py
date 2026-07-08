"""
Baseline 冻结 — 用现有 BM25+BGE+RRF 跑 2.1_19 D 并记录指标
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from hybrid_retriever import (
    load_cards, BM25Retriever, EmbeddingRetriever,
    rrf_fuse, build_card_text, evaluate_detailed,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EVAL_DIR = os.path.join(DATA_DIR, "lightrag_eval")

# Load claim_evidence_frames
with open(os.path.join(DATA_DIR, "claim_evidence_frames.json"), "r", encoding="utf-8") as f:
    frames = json.load(f)

anchors = frames["frame_alignment"]["retrieval_verification_anchors"]
target_cards = {ef["card_id"]: ef["citation"][:80] for ef in frames["target_evidence_frames"]}

# Evidence groups (from plan)
EVIDENCE_GROUPS = {
    "E1_税收损失": {"must": ["v6_b03_N18"], "accept": ["v6_b03_N17", "v6_b03_N19"]},
    "E2_贸易洗钱避税": {"must": ["v6_b29_N05"], "accept": ["v6_b33_N20", "v6_b33_N25"]},
    "E3_空壳虚假发票": {"must": ["v6_b33_N23"], "accept": ["v6_b33_N24", "v6_b33_N25"]},
    "E4_BMPE规避关税": {"must": ["v6_b33_N38"], "accept": []},
}


def main():
    cards = load_cards(min_citation_len=0)

    bm25 = BM25Retriever(cards)
    emb = EmbeddingRetriever(cards)

    # Multi-anchor retrieval
    all_lists = []
    for q in anchors:
        all_lists.append(bm25.search(q, top_k=20))
        all_lists.append(emb.search(q, top_k=20))

    final = rrf_fuse(all_lists)

    # Eval at top-15
    top15 = final[:15]
    top15_cards = []
    for idx, score in top15:
        card = cards[idx]
        top15_cards.append({
            "card_id": card["card_id"],
            "knowledge": card["knowledge"][:80],
            "citation": card["citation"][:100],
            "rrf_score": round(score, 6),
        })

    # Hit analysis per evidence group
    hit_analysis = {}
    for group_id, group_info in EVIDENCE_GROUPS.items():
        all_ids = [group_info["must"][0]] + group_info["accept"]
        best_rank = None
        best_card = None
        for rank, (idx, score) in enumerate(final[:60]):
            card = cards[idx]
            if card["card_id"] in all_ids:
                if best_rank is None:
                    best_rank = rank + 1
                    best_card = card["card_id"]
        hit_analysis[group_id] = {
            "best_rank": best_rank,
            "best_card": best_card,
            "in_top15": best_rank is not None and best_rank <= 15,
        }

    # Noise
    signal_ids = set()
    for gi in EVIDENCE_GROUPS.values():
        signal_ids.update(gi["must"])
        signal_ids.update(gi["accept"])
    noise_count = sum(1 for idx, _ in top15 if cards[idx]["card_id"] not in signal_ids)

    recall = sum(1 for h in hit_analysis.values() if h["in_top15"])
    precision = 1 - noise_count / 15

    # Traceability: all cards in top15 have card_id
    traceable = sum(
        1 for idx, _ in top15
        if cards[idx]["card_id"] and len(cards[idx]["card_id"]) > 0
    )

    report = {
        "timestamp": "2026-06-03",
        "method": "BM25+BGE+RRF (multi-anchor)",
        "num_anchors": len(anchors),
        "recall_at_15": f"{recall}/4",
        "noise_at_15": noise_count,
        "precision_at_15": round(precision, 3),
        "traceability": f"{traceable}/{len(top15)}",
        "hit_analysis": hit_analysis,
        "top15_candidates": top15_cards,
        "anchors_used": anchors,
        "evidence_groups": {k: v for k, v in EVIDENCE_GROUPS.items()},
    }

    # Save
    output_path = os.path.join(EVAL_DIR, "baseline_2.1_19_D.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"Recall@15: {recall}/4")
    print(f"Noise@15: {noise_count}")
    print(f"Precision@15: {precision:.2f}")
    for gid, ha in hit_analysis.items():
        rank_str = f"#{ha['best_rank']}" if ha['best_rank'] else "未命中"
        print(f"  {gid}: {rank_str} | {ha['best_card']}")

    print(f"\nTop-15:")
    for i, tc in enumerate(top15_cards):
        signal = "S" if tc["card_id"] in signal_ids else "N"
        print(f"  [{i+1}] {signal} {tc['card_id']} | {tc['knowledge'][:60]}")

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
