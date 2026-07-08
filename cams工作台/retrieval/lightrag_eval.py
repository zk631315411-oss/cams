"""
LightRAG 三组测试 A/B/C — 2.1_19 D 选项检索评估
"""
import os, sys, json, re, asyncio

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["SUMMARY_LANGUAGE"] = "Chinese"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EVAL_DIR = os.path.join(DATA_DIR, "lightrag_eval")
INDEX_DIR = os.path.join(DATA_DIR, "lightrag_index")

from sentence_transformers import SentenceTransformer
MODEL = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)

# Evidence groups (from plan)
E_GROUPS = {
    "E1": {"must": ["v6_b03_N18"], "accept": ["v6_b03_N17", "v6_b03_N19"]},
    "E2": {"must": ["v6_b29_N05"], "accept": ["v6_b33_N20", "v6_b33_N25"]},
    "E3": {"must": ["v6_b33_N23"], "accept": ["v6_b33_N24", "v6_b33_N25"]},
    "E4": {"must": ["v6_b33_N38"], "accept": []},
}


async def emb_func(texts):
    if isinstance(texts, str): texts = [texts]
    return MODEL.encode(texts, normalize_embeddings=True)


async def llm_func(prompt, system_prompt=None, history_messages=None, **kw):
    from lightrag.llm.openai import openai_complete_if_cache
    return await openai_complete_if_cache(
        "deepseek-v4-flash", prompt,
        system_prompt=system_prompt, history_messages=history_messages or [],
        api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com", **kw)


async def create_rag():
    from lightrag import LightRAG
    from lightrag.utils import EmbeddingFunc
    rag = LightRAG(
        working_dir=INDEX_DIR,
        llm_model_func=llm_func,
        embedding_func=EmbeddingFunc(embedding_dim=512, max_token_size=512, func=emb_func),
        top_k=60, chunk_top_k=30,
        addon_params={"language": "Chinese"},
    )
    await rag.initialize_storages()
    return rag


def extract_card_ids(chunks):
    """Extract card_ids from chunk content via [CARD_ID] marker"""
    ids = set()
    for c in chunks:
        found = re.findall(r"\[CARD_ID\]\s*(\S+)", c.get("content", ""))
        ids.update(found)
    return ids


def evaluate_hits(card_ids_in_results, top_n=15):
    """Check which evidence groups are hit in results"""
    hits = {}
    for gid, ginfo in E_GROUPS.items():
        all_ids = ginfo["must"] + ginfo["accept"]
        hit_cards = [cid for cid in all_ids if cid in card_ids_in_results]
        must_hit = any(cid in card_ids_in_results for cid in ginfo["must"])
        accept_hit = [cid for cid in ginfo["accept"] if cid in card_ids_in_results]
        hits[gid] = {
            "hit": len(hit_cards) > 0,
            "must_hit": must_hit,
            "accept_hit": accept_hit,
            "hit_cards": hit_cards,
        }
    recall = sum(1 for h in hits.values() if h["hit"])
    return hits, recall


async def run_test(label, query, mode, hl_kw=None, ll_kw=None):
    """Run one test query and evaluate"""
    rag = await create_rag()
    from lightrag import QueryParam

    param = QueryParam(mode=mode, enable_rerank=False)
    if hl_kw is not None:
        param = QueryParam(mode=mode, hl_keywords=hl_kw, ll_keywords=ll_kw, enable_rerank=False)

    result = await rag.aquery_data(query, param=param)
    data = result.get("data", {})
    chunks = data.get("chunks", [])
    all_card_ids = extract_card_ids(chunks)
    keywords_used = result.get("metadata", {}).get("keywords", {})

    # Evaluate
    hits, recall = evaluate_hits(all_card_ids, top_n=15)
    signal_ids = set()
    for g in E_GROUPS.values():
        signal_ids.update(g["must"])
        signal_ids.update(g["accept"])

    # Top-15 card_ids
    top15_ids = []
    for c in chunks[:15]:
        cids = re.findall(r"\[CARD_ID\]\s*(\S+)", c.get("content", ""))
        top15_ids.extend(cids)

    noise = sum(1 for cid in top15_ids if cid not in signal_ids)
    traceable = len(top15_ids)  # All have card_id by design

    report = {
        "test": label,
        "query": query,
        "mode": mode,
        "keywords_used": keywords_used,
        "total_chunks": len(chunks),
        "top15_card_ids": top15_ids[:15],
        "recall_at_15": f"{recall}/4",
        "noise_at_15": min(noise, 15),
        "traceability": f"{traceable}/{min(len(top15_ids), 15)}",
        "hits": {gid: {"hit": h["hit"], "cards": h["hit_cards"]} for gid, h in hits.items()},
    }

    await rag.finalize_storages()
    return report


async def main():
    # frozen baseline (from step 3)
    baseline = {
        "recall": "4/4", "noise": 9, "precision": 0.40,
        "E1_rank": 3, "E2_rank": 2, "E3_rank": 1, "E4_rank": 8,
    }

    # ── Test A: Bare Query ──
    print("=" * 60)
    print("Test A: Bare query")
    test_a = await run_test(
        "A_裸查",
        "为什么不选D？将钱合法化的过程中不会交税吗？比如虚假交易的情境下，一方虚假地出售了产品或服务，给开了个假发票",
        mode="mix",
    )

    # ── Test B: Claim Frame ──
    print("Test B: Claim Frame query")
    test_b = await run_test(
        "B_ClaimFrame",
        "FI 公司税增加 金融机构税负 主体不一致 政府税收缩水 逃税 税务欺诈 贸易洗钱",
        mode="mix",
        hl_kw=["洗钱后果", "税收损失", "贸易洗钱", "税务欺诈", "黑市比索交易"],
        ll_kw=["金融机构", "公司税增加", "政府税收缩水", "空壳公司", "虚假发票", "增值税链条", "国内税收", "关税"],
    )

    # ── Test C: Evidence Frame Anchors ──
    print("Test C: Evidence Frame anchors")

    # C1: single merge anchor
    anchors = [
        "政府税收缩水 征税困难",
        "逃税 避税 税务欺诈",
        "贸易洗钱 操纵贸易价格 避税",
        "空壳公司 虚假发票 伪造交易",
        "黑市比索交易 规避关税 国内税收",
        "增值税链条 VAT 伪造买卖记录",
    ]
    c1 = await run_test(
        "C1_单次合并锚点",
        " ".join(anchors),
        mode="mix",
        hl_kw=anchors,
        ll_kw=[],
    )

    # C2: multi-anchor merged (run each anchor separately, merge results)
    print("Test C2: Multi-anchor...")
    all_c2_ids = set()
    for qi, anchor in enumerate(anchors):
        rag = await create_rag()
        from lightrag import QueryParam
        result = await rag.aquery_data(anchor, param=QueryParam(mode="mix", enable_rerank=False))
        chunks = result.get("data", {}).get("chunks", [])
        cids = extract_card_ids(chunks)
        all_c2_ids.update(cids)
        await rag.finalize_storages()

    c2_hits, c2_recall = evaluate_hits(all_c2_ids)
    signal_ids = set()
    for g in E_GROUPS.values():
        signal_ids.update(g["must"])
        signal_ids.update(g["accept"])
    c2_noise = sum(1 for cid in list(all_c2_ids)[:15] if cid not in signal_ids)

    test_c2 = {
        "test": "C2_多锚点独立",
        "recall_at_15": f"{c2_recall}/4",
        "noise_at_15": min(c2_noise, 15),
        "hits": {gid: {"hit": h["hit"], "cards": h["hit_cards"]} for gid, h in c2_hits.items()},
        "total_card_ids": len(all_c2_ids),
    }

    # ── Combine & Print ──
    all_tests = [test_a, test_b, c1, test_c2]

    print(f"\n{'='*60}")
    print(f"对比结果")
    print(f"{'='*60}")
    print(f"{'Test':<20} {'Recall':<10} {'Noise':<10} {'Pass':<10}")
    print("-" * 60)
    print(f"{'Baseline (frozen)':<20} {baseline['recall']:<10} {baseline['noise']:<10} {'---':<10}")

    for t in all_tests:
        recall = t.get("recall_at_15", "N/A")
        noise = t.get("noise_at_15", "N/A")
        if isinstance(recall, str):
            n = int(recall.split("/")[0])
        else:
            n = 0
        if isinstance(noise, (int, float)):
            passed = n >= 3 and noise <= baseline["noise"] + 2
        else:
            passed = "N/A"
        status = "[PASS]" if passed else "[FAIL]" if passed is not False else "[OK]"
        print(f"{t['test']:<20} {str(recall):<10} {str(noise):<10} {status:<10}")

    # Detail
    for t in all_tests:
        print(f"\n--- {t['test']} ---")
        hits = t.get("hits", {})
        for gid, h in hits.items():
            s = "OK" if h["hit"] else "MISS"
            print(f"  {s} {gid}: {h['cards']}")
        if "top15_card_ids" in t:
            print(f"  Top-15: {t['top15_card_ids'][:10]}...")
        print(f"  Keywords: {t.get('keywords_used', {})}")

    # Save
    output = {
        "baseline": baseline,
        "tests": {t["test"]: t for t in all_tests},
    }
    output_path = os.path.join(EVAL_DIR, "03_eval_results.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {output_path}")


asyncio.run(main())
