"""
Claim 中间层原型 — 验证"题目 claim → evidence frame → 检索锚点"链路
只针对 2.1_19 D 选项手工建模
"""
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from hybrid_retriever import (
    load_cards, BM25Retriever, EmbeddingRetriever,
    rrf_fuse, build_card_text, TEACHER_EVIDENCE,
    evaluate_detailed, print_result,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ── 1. Claim 结构定义 ─────────────────────────────────────────────
CLAIM_2_1_19_D = {
    "option": "D",
    "claim_text": "公司税的增加",
    "full_context": "洗钱会对金融机构FI造成公司税的增加",
    "decomposition": {
        "subject": "金融机构 (FI)",
        "object": "公司税/企业所得税",
        "direction": "增加",
    },
    "claim_type": "后果归因 — 将洗钱后果归因到FI的税务负担",
    "misunderstanding": {
        "type": "税务主体/方向误配",
        "description": "学生把洗钱过程中的税务现象（犯罪分子逃税、政府税收减少）错误归因到FI身上，且方向相反",
        "student_typical_question": "虚假交易不会交税吗？为什么D不选？",
    },
    "evidence_frames": [
        {
            "frame_id": "F1",
            "frame_name": "直接反证：洗钱的税收后果不是FI公司税增加，而是政府税收减少",
            "rationale": "教材明确指出洗钱的经济影响是政府税收缩水，与FI公司税增加主体不同、方向相反",
            "anchors": [
                "税收损失 政府税收缩水 征税困难 税率上升",
                "洗钱使政府税收缩水 收入损失 危害纳税人",
            ],
            "expected_card": "v6_b03_N18",
        },
        {
            "frame_id": "F2",
            "frame_name": "机制解释1：贸易洗钱中的避税行为",
            "rationale": "贸易洗钱的核心手段（高/低开发票）目的之一是避税，说明洗钱关联的是逃税而非增税",
            "anchors": [
                "贸易洗钱 TBML 操纵贸易价格 避税活动",
                "高开发票 低开发票 虚报价格 避税",
            ],
            "expected_card": "v6_b29_N05",
        },
        {
            "frame_id": "F3",
            "frame_name": "机制解释2：空壳公司/虚假发票/税务欺诈",
            "rationale": "空壳公司和虚假发票是洗钱常用手段，用于伪造交易和税务欺诈，犯罪分子借此逃税",
            "anchors": [
                "空壳公司 壳公司 降低透明度",
                "虚假发票 假发票 伪造发票 发票欺诈",
                "税务欺诈 增值税链条 VAT 伪造买卖记录",
            ],
            "expected_card": "v6_b33_N23",
        },
        {
            "frame_id": "F4",
            "frame_name": "具体案例：黑市比索交易规避税收和关税",
            "rationale": "BMPE机制的设计初衷就是规避国内税收和关税，直接说明洗钱活动逃税而非增税",
            "anchors": [
                "黑市比索交易 BMPE 规避关税 规避国内税收",
                "哥伦比亚进口商 黑市美元 规避税收 关税",
            ],
            "expected_card": "v6_b33_N38",
        },
    ],
}


# ── 2. Claim → Anchors 展开 ──────────────────────────────────────
def claim_to_anchors(claim):
    """把结构化 claim 展开为三层检索锚点"""
    anchors = {}

    # 第一层：词面锚点（从 claim_text 和选项原文）
    anchors["lexical"] = [
        claim["claim_text"],
        f"{claim['decomposition']['subject']} {claim['decomposition']['object']} {claim['decomposition']['direction']}",
    ]

    # 第二层：结构锚点（主体/方向对比）
    anchors["structural"] = [
        f"洗钱 税收 政府 减少 缩水 损失",
        f"逃税 避税 税务欺诈 犯罪分子 规避",
    ]

    # 第三层：机制锚点（从 evidence_frames 汇总）
    mechanism_anchors = []
    for frame in claim["evidence_frames"]:
        mechanism_anchors.extend(frame["anchors"])
    anchors["mechanism"] = mechanism_anchors

    return anchors


# ── 3. 检索 + 评估 ──────────────────────────────────────────────
def run_claim_retrieval(cards, anchors_dict):
    """运行检索，每层分开跑然后对比"""
    results = {}
    for layer_name, queries in anchors_dict.items():
        bm25 = BM25Retriever(cards)
        emb = EmbeddingRetriever(cards)

        all_lists = []
        for q in queries:
            all_lists.append(bm25.search(q, top_k=20))
            all_lists.append(emb.search(q, top_k=20))

        final = rrf_fuse(all_lists)
        top_n = final[:15]

        # 构建结果
        top_results = []
        for idx, score in top_n:
            card = cards[idx]
            top_results.append({
                "card_id": card["card_id"],
                "knowledge": card["knowledge"],
                "citation": card["citation"],
                "rrf_score": round(score, 6),
            })

        eval_details, recalled_count, best_matches = evaluate_detailed(
            final, cards, {}, {}, queries)

        noise_count = 0
        for idx, _ in top_n:
            text = build_card_text(cards[idx])
            is_signal = any(
                kw in text
                for ev_info in TEACHER_EVIDENCE.values()
                for kw in ev_info["keywords"]
            )
            if not is_signal:
                noise_count += 1

        results[layer_name] = {
            "num_queries": len(queries),
            "top_15": top_results,
            "recalled": f"{recalled_count}/4",
            "passed": recalled_count >= 3,
            "best_matches": best_matches,
            "noise": noise_count,
            "details": eval_details,
        }

    return results


# ── 4. 主流程 ─────────────────────────────────────────────────────
def main():
    cards = load_cards(min_citation_len=20)

    # 展开 claim → anchors
    anchors = claim_to_anchors(CLAIM_2_1_19_D)

    print("=" * 60)
    print("Claim 中间层验证: 2.1_19 D")
    print("=" * 60)
    print(f"Misunderstanding: {CLAIM_2_1_19_D['misunderstanding']['type']}")
    print(f"Evidence frames: {len(CLAIM_2_1_19_D['evidence_frames'])}")
    for f in CLAIM_2_1_19_D["evidence_frames"]:
        print(f"  {f['frame_id']}: {f['frame_name'][:50]}...")

    print(f"\n三层锚点:")
    for layer, queries in anchors.items():
        print(f"  {layer}: {len(queries)} 个")

    # 逐层检索
    layer_results = run_claim_retrieval(cards, anchors)

    # 打印结果
    for layer, result in layer_results.items():
        print(f"\n--- {layer} 层 ---")
        print(f"  锚点数: {result['num_queries']}, 召回: {result['recalled']}, 噪声: {result['noise']}/15")
        for ev_id, detail in result["details"].items():
            s = "[OK]" if detail["recalled"] else "[MISS]"
            print(f"  {s} {ev_id}: {detail['hit_keywords'][:3]}")

    # 全层合并效果
    print(f"\n--- 三层合并 (mechanism层=全量evidence frame锚点) ---")
    mech = layer_results.get("mechanism", {})
    print(f"  召回: {mech.get('recalled', 'N/A')}, 噪声: {mech.get('noise', 'N/A')}/15")

    # 保存
    output = {
        "claim": CLAIM_2_1_19_D,
        "anchors": {k: v for k, v in anchors.items()},
        "results": {},
    }
    for layer, result in layer_results.items():
        output["results"][layer] = {
            "recalled": result["recalled"],
            "noise": result["noise"],
            "best_matches": result["best_matches"],
            "details": result["details"],
        }

    with open(os.path.join(DATA_DIR, "claim_layer_result.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n详细结果: data/claim_layer_result.json")


if __name__ == "__main__":
    main()
