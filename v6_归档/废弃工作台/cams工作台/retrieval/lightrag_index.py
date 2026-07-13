"""
LightRAG 索引脚本 — 小样本验证 + 全量索引
"""
import os, sys, json, re, asyncio

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["SUMMARY_LANGUAGE"] = "Chinese"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("[FAIL] DEEPSEEK_API_KEY not set")
    sys.exit(1)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EVAL_DIR = os.path.join(DATA_DIR, "lightrag_eval")
INDEX_DIR = os.path.join(DATA_DIR, "lightrag_index")

# ── Model (loaded once) ──────────────────────────────────────────
from sentence_transformers import SentenceTransformer
MODEL = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)


async def emb_func(texts):
    if isinstance(texts, str):
        texts = [texts]
    return MODEL.encode(texts, normalize_embeddings=True)


async def llm_func(prompt, system_prompt=None, history_messages=None, **kw):
    from lightrag.llm.openai import openai_complete_if_cache
    return await openai_complete_if_cache(
        "deepseek-v4-flash",
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages or [],
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
        **kw,
    )


async def create_rag():
    from lightrag import LightRAG
    from lightrag.utils import EmbeddingFunc

    rag = LightRAG(
        working_dir=INDEX_DIR,
        llm_model_func=llm_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=512, max_token_size=512, func=emb_func
        ),
        top_k=60,
        chunk_top_k=30,
        max_parallel_insert=10,
        addon_params={"language": "Chinese"},
    )
    await rag.initialize_storages()
    return rag


# ── 5.2 Pilot Index ──────────────────────────────────────────────
async def pilot_index():
    rag = await create_rag()

    # Load pilot docs
    pilot_path = os.path.join(EVAL_DIR, "pilot_docs.jsonl")
    with open(pilot_path, "r", encoding="utf-8") as f:
        docs = [json.loads(line) for line in f]

    print(f"Pilot indexing {len(docs)} cards ...")
    for d in docs:
        cid = d["card_id"]
        await rag.ainsert(d["text"], ids=[cid])

    # Verify queries
    queries = [
        ("政府税收缩水", "v6_b03_N18"),
        ("黑市比索 关税", "v6_b33_N38"),
        ("税务欺诈 VAT", "v6_b33_N25"),
        ("空壳公司 虚假发票", "v6_b33_N23"),
    ]

    from lightrag import QueryParam

    results = {}
    for query, target_card in queries:
        r = await rag.aquery_data(query, param=QueryParam(mode="mix", enable_rerank=False))
        data = r.get("data", {})
        chunks = data.get("chunks", [])
        entities = data.get("entities", [])
        relationships = data.get("relationships", [])

        # Extract card_ids from chunks
        card_ids = set()
        for c in chunks:
            found = re.findall(r"\[CARD_ID\]\s*(\S+)", c.get("content", ""))
            card_ids.update(found)

        target_found = target_card in card_ids

        results[query] = {
            "target_card": target_card,
            "target_in_chunks": target_found,
            "chunks_count": len(chunks),
            "entities_count": len(entities),
            "relationships_count": len(relationships),
            "card_ids_in_chunks": list(card_ids),
            "entity_sample": entities[0]["entity_name"] if entities else "N/A",
            "keywords": r.get("metadata", {}).get("keywords", {}),
        }

        status = "OK" if target_found else "MISS"
        print(f"  [{status}] '{query}' -> {target_card}")

    # Save report
    output_path = os.path.join(EVAL_DIR, "01_pilot_index_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    all_found = all(v["target_in_chunks"] for v in results.values())
    print(f"\nPilot result: {sum(1 for v in results.values() if v['target_in_chunks'])}/{len(results)} targets found")
    print(f"Saved: {output_path}")

    await rag.finalize_storages()
    return all_found


# ── 6.1 Full Index ────────────────────────────────────────────────
async def full_index():
    # Clear pilot data
    import shutil
    if os.path.exists(INDEX_DIR):
        shutil.rmtree(INDEX_DIR)
        os.makedirs(INDEX_DIR)

    rag = await create_rag()

    full_path = os.path.join(EVAL_DIR, "cards_lightrag_docs.jsonl")
    with open(full_path, "r", encoding="utf-8") as f:
        docs = [json.loads(line) for line in f]

    print(f"Full indexing {len(docs)} cards (batch enqueue + parallel process) ...")

    # Batch enqueue: 先全部入队
    texts = [d["text"] for d in docs]
    ids = [d["card_id"] for d in docs]

    track_id = "full_cams_ch2"
    await rag.apipeline_enqueue_documents(texts, ids, track_id=track_id)

    # 并行处理入队文档 (max_parallel_insert 控制并发)
    await rag.apipeline_process_enqueue_documents()

    failed = 0

    # Collect stats
    from lightrag.kg.shared_storage import get_namespace_data
    ns = await get_namespace_data("")
    text_chunks_db = ns.get("text_chunks_db")
    full_docs_db = ns.get("full_docs_db")
    full_entities_db = ns.get("full_entities_db")
    full_relations_db = ns.get("full_relations_db")

    chunks_count = len(await text_chunks_db.get_all()) if text_chunks_db else 0
    docs_indexed = len(await full_docs_db.get_all()) if full_docs_db else 0
    entities_count = len(await full_entities_db.get_all()) if full_entities_db else 0
    relations_count = len(await full_relations_db.get_all()) if full_relations_db else 0

    report = {
        "total_cards": len(docs),
        "docs_indexed": docs_indexed,
        "failed": failed,
        "chunks": chunks_count,
        "entities": entities_count,
        "relationships": relations_count,
        "index_rate": f"{docs_indexed}/{len(docs)} ({100*docs_indexed//len(docs)}%)" if len(docs) > 0 else "N/A",
    }

    output_path = os.path.join(EVAL_DIR, "02_index_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nFull index done: {report['docs_indexed']} docs, "
          f"{report['entities']} entities, {report['relationships']} relations, "
          f"{report['chunks']} chunks")
    print(f"Failed: {failed}")
    print(f"Saved: {output_path}")

    await rag.finalize_storages()
    return rag


# ── Main ──────────────────────────────────────────────────────────
async def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "pilot"

    if mode == "pilot":
        await pilot_index()
    elif mode == "full":
        await full_index()
    else:
        print(f"Unknown mode: {mode}. Use 'pilot' or 'full'.")


if __name__ == "__main__":
    asyncio.run(main())
