"""
LightRAG Smoke Test — 验证环境 + API + raw chunks 可追溯性
"""
import os
import sys
import asyncio
import json
from datetime import datetime

# 强制离线模式
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("[FAIL] DEEPSEEK_API_KEY 环境变量未设置")
    sys.exit(1)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EVAL_DIR = os.path.join(DATA_DIR, "lightrag_eval")
INDEX_DIR = os.path.join(DATA_DIR, "lightrag_index")


# ── 1. LLM Function (DeepSeek v4-flash, OpenAI compatible) ────────
async def llm_func(prompt, system_prompt=None, history_messages=None, **kwargs):
    from lightrag.llm.openai import openai_complete_if_cache
    return await openai_complete_if_cache(
        "deepseek-v4-flash",
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages or [],
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
        **kwargs,
    )


# ── 2. Embedding Function (BGE-small-zh-v1.5) ─────────────────────
async def embedding_func(texts):
    """使用本地 BGE 模型做 embedding"""
    from sentence_transformers import SentenceTransformer
    import numpy as np

    model = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)
    if isinstance(texts, str):
        texts = [texts]
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings


# ── 3. Smoke Test ─────────────────────────────────────────────────
async def main():
    from lightrag import LightRAG, QueryParam
    from lightrag.utils import EmbeddingFunc

    # Init
    rag = LightRAG(
        working_dir=INDEX_DIR,
        llm_model_func=llm_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=512,
            max_token_size=512,
            func=embedding_func,
        ),
        top_k=30,
        chunk_top_k=15,
    )

    await rag.initialize_storages()

    # Insert test card
    test_card = """[CARD_ID] v6_b03_N18
[TYPE] 事实
[KNOWLEDGE] 洗钱使政府税收缩水，从而间接危害诚实的纳税人
[CITATION] 洗钱使政府税收缩水，从而间接危害诚实的纳税人。
[CONTEXT_BEFORE] 税收损失在非法活动的多种基本形式中，逃税对宏观经济的影响可能最为明显。
[CONTEXT_AFTER] 它也使政府征税变得更加困难。"""

    print("插入测试卡片...")
    await rag.ainsert(test_card, ids=["test_v6_b03_N18"])

    # Query with aquery_data to get raw chunks
    print("查询: 洗钱对政府税收有什么影响 ...")
    result = await rag.aquery_data(
        "洗钱对政府税收有什么影响",
        param=QueryParam(mode="mix"),
    )

    report = {
        "timestamp": datetime.now().isoformat(),
        "test": "smoke_test",
        "result_type": type(result).__name__,
    }

    if hasattr(result, "__dict__"):
        for key in ["chunks", "entities", "relationships", "references"]:
            val = getattr(result, key, None)
            if val is not None:
                if isinstance(val, list):
                    report[f"{key}_count"] = len(val)
                    if len(val) > 0:
                        report[f"{key}_sample"] = str(val[0])[:200]
                else:
                    report[f"{key}_type"] = type(val).__name__
    elif isinstance(result, dict):
        for key, val in result.items():
            if isinstance(val, list):
                report[f"{key}_count"] = len(val)
                if len(val) > 0:
                    report[f"{key}_sample"] = str(val[0])[:200]

    # Check: can we see the card_id in results?
    result_str = json.dumps(report, ensure_ascii=False, indent=2)

    card_id_found = "v6_b03_N18" in json.dumps(
        {k: str(v)[:500] for k, v in report.items()}
    )

    report["card_id_traceable"] = card_id_found

    # Save
    output_path = os.path.join(EVAL_DIR, "00_smoke_test.json")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result_str)

    print(f"\n--- Smoke Test 结果 ---")
    print(f"结果类型: {report['result_type']}")
    print(f"Card ID 可追溯: {card_id_found}")
    print(f"\n详细结果: {output_path}")

    if card_id_found:
        print("\n[PASS] Smoke test 通过 — raw chunks 可追溯 card_id")
    else:
        print("\n[FAIL] 无法从 raw data 反查 card_id — 需要检查返回结构")

    await rag.finalize_storages()


asyncio.run(main())
