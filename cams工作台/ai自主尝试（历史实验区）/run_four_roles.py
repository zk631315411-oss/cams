"""
四角色分离检索法实验

角色：
  AI #1 (联想者) — 允许自由回答，可以跨章节联想
  AI #2 (核查员) — 从 AI #1 回答中提取需要查教材验证的事实主张
  LightRAG  — 按核查清单搜教材
  AI #3 (裁判官) — 只看教材证据 + 原题，写最终解析

关键约束：AI #3 绝不能看到 AI #1 的回答。
"""
import os, sys, json, re, asyncio

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["SUMMARY_LANGUAGE"] = "Chinese"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("[FAIL] DEEPSEEK_API_KEY not set"); sys.exit(1)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.join(DATA_DIR, "agentic_search_eval_v2")
INDEX_DIR = os.path.join(DATA_DIR, "lightrag_index")

ORACLE_WORDS = ["政府税收缩水", "贸易洗钱", "虚假发票", "BMPE", "黑市比索", "空壳公司"]

from openai import OpenAI
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
MODEL = "deepseek-v4-pro"

# ── Step 1: AI #1 自由回答 ──────────────────────────────────────

def step1_free_answer():
    """AI #1: 拿到CAMS教材第2章全文，基于教材内容自由回答。"""
    print("=" * 60)
    print("Step 1: AI #1 — 自由回答（拿到教材全文）")
    print("=" * 60)

    # Load full textbook
    text_path = os.path.join(DATA_DIR, "agentic_search_eval_v2", "ch2_full_text.txt")
    with open(text_path, "r", encoding="utf-8") as f:
        textbook = f.read()
    print(f"  Textbook loaded: {len(textbook)} chars, ~{len(textbook)//3} tokens")

    prompt = f"""你是一位CAMS反洗钱考试专家。以下是CAMS教材第2章《{textbook[:50]}...》的完整原文：

```
{textbook}
```

请基于以上教材原文，分析下面这道题：

题目：洗钱会对金融机构FI造成哪些后果？（选择两个。）
A. 盈利业务的减少或损失
B. 代理银行设施的增加
C. 雇员人数减少
D. 公司税的增加
E. 调查费用和罚金的增加
正确答案：A, E

请逐一分析每个选项为什么对或为什么错。要求：每个判断必须引用教材中的具体小节名称和相关原文。直接输出分析文本。"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, max_tokens=1000)

    answer = resp.choices[0].message.content.strip()
    print(f"  AI #1 output ({len(answer)} chars):")
    for line in answer.split("\n")[:5]:
        clean = line[:120].encode('gbk', errors='replace').decode('gbk')
        print(f"    {clean}")
    print("    ...")

    # Save
    out_path = os.path.join(OUT_DIR, "four_roles_step1_free_answer.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(answer)
    print(f"  Saved to {out_path}")
    return answer


# ── Step 2: AI #2 核查员 ────────────────────────────────────────
def step2_extract_claims(free_answer):
    """AI #2: 从 AI #1 的回答中提取需要查教材验证的事实主张。"""
    print("\n" + "=" * 60)
    print("Step 2: AI #2 — 提取待核查事实")
    print("=" * 60)

    prompt = f"""你是一位严谨的教研审核员。下面是另一位专家对一道CAMS考题的分析。

【专家分析】
{free_answer}

你的任务：从这份分析中，对**每一个选项（A/B/C/D/E）**提取需要查教材验证的事实主张。

重要：分析中可能用教材证据支持正确选项，也可能用教材证据反驳错误选项——这两种都是需要在教材中核实的事实主张，都必须提取。

规则：
1. 每个选项至少提取一条主张。即使分析中某选项的论证简短，也把其中引用的教材事实提取出来
2. 只提取客观事实主张（如"教材指出洗钱导致X"），不提取主观判断
3. 每条主张写明：涉及哪个选项、主张什么、应该搜什么关键词
4. 特别关注：如果分析引用了教材特定小节（如"税收损失"小节），务必提取

输出JSON（不要markdown包裹）：
{{
  "claims_to_verify": [
    {{
      "option": "A|B|C|D|E",
      "claim": "需要核实的具体主张",
      "search_query": "检索关键词（空格分隔）",
      "search_purpose": "查什么"
    }}
  ]
}}"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1, max_tokens=1500)

    raw = resp.choices[0].message.content.strip()
    if not raw:
        print("  [ERROR] AI #2 returned empty response")
        return {"claims_to_verify": [], "leakage": False, "error": "empty_response"}
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        claims = json.loads(raw)
    except json.JSONDecodeError:
        import json_repair
        try:
            claims = json.loads(json_repair.repair_json(raw))
        except:
            print(f"  [ERROR] Cannot parse AI #2 JSON. Raw: {raw[:300]}")
            return {"claims_to_verify": [], "leakage": False, "error": "json_parse_failed"}

    # Leakage check
    for c in claims.get("claims_to_verify", []):
        q = c.get("search_query", "")
        for w in ORACLE_WORDS:
            if w in q:
                print(f"  [LEAK] Oracle word '{w}' in query: {q}")
                claims["leakage"] = True
                return claims

    claims["leakage"] = False

    print(f"  Extracted {len(claims.get('claims_to_verify', []))} claims to verify:")
    for c in claims.get("claims_to_verify", []):
        opt = c.get('option', '?')
        cl = c.get('claim', c.get('claim_text', 'N/A'))
        q = c.get('search_query', c.get('query', ''))[:60]
        print(f"    [{opt}] {cl[:80]}")
        print(f"         query: {q}")

    out_path = os.path.join(OUT_DIR, "four_roles_step2_claims.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(claims, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {out_path}")
    return claims


# ── Step 3: LightRAG 搜索 ────────────────────────────────────────
async def step3_search(claims):
    """LightRAG: 按核查清单搜教材。"""
    print("\n" + "=" * 60)
    print("Step 3: LightRAG — 搜教材证据")
    print("=" * 60)

    if claims.get("leakage"):
        print("  [FAIL] Leakage detected, aborting search")
        return None

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)

    async def emb_func(texts):
        if isinstance(texts, str): texts = [texts]
        return model.encode(texts, normalize_embeddings=True)

    async def llm_func(prompt, system_prompt=None, history_messages=None, **kw):
        from lightrag.llm.openai import openai_complete_if_cache
        return await openai_complete_if_cache(
            MODEL, prompt, system_prompt=system_prompt, history_messages=history_messages or [],
            api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com", **kw)

    from lightrag import LightRAG, QueryParam
    from lightrag.utils import EmbeddingFunc
    rag = LightRAG(working_dir=INDEX_DIR, llm_model_func=llm_func,
                   embedding_func=EmbeddingFunc(embedding_dim=512, max_token_size=512, func=emb_func),
                   top_k=60, chunk_top_k=30, addon_params={"language": "Chinese"})
    await rag.initialize_storages()

    all_results = {}
    for c in claims.get("claims_to_verify", []):
        query = c["search_query"]
        option = c["option"]
        print(f"\n  Searching [{option}]: {query[:60]}")

        r = await rag.aquery_data(query, param=QueryParam(mode="mix", enable_rerank=False))
        chunks = r.get("data", {}).get("chunks", [])

        card_ids = []
        card_texts = {}
        for chunk in chunks[:15]:
            cids = re.findall(r"\[CARD_ID\]\s*(\S+)", chunk.get("content", ""))
            for cid in cids:
                if cid not in card_ids:
                    card_ids.append(cid)
                    card_texts[cid] = chunk.get("content", "")[:300]

        key = f"{option}: {c['claim'][:40]}"
        all_results[key] = {
            "option": option,
            "claim": c["claim"],
            "query": query,
            "top_card_ids": card_ids[:10],
            "card_count": len(card_ids),
        }
        print(f"    Found {len(card_ids)} cards: {card_ids[:5]}")

    await rag.finalize_storages()

    out_path = os.path.join(OUT_DIR, "four_roles_step3_search_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved to {out_path}")
    return all_results


# ── Step 4: AI #3 最终回答 ─────────────────────────────────────
def step4_final_answer(search_results):
    """AI #3: 只看教材证据 + 原题，不看 AI #1 的回答。"""
    print("\n" + "=" * 60)
    print("Step 4: AI #3 — 基于教材证据的最终解析")
    print("=" * 60)

    # Build evidence summary from search results
    evidence_text = ""
    for key, result in search_results.items():
        cards = result.get("top_card_ids", [])[:5]
        evidence_text += f"\n关于'{key}': 找到卡片 {cards}"

    prompt = f"""你是CAMS教研专家。请基于以下教材检索结果，为一道CAMS考题写解析。

【题目】
题干：洗钱会对金融机构FI造成哪些后果？（选择两个。）
A. 盈利业务的减少或损失
B. 代理银行设施的增加
C. 雇员人数减少
D. 公司税的增加
E. 调查费用和罚金的增加
正确答案：A, E

【教材检索结果】
以下是通过不同关键词搜索教材找到的相关卡片ID：
{evidence_text}

请写解析。要求：
1. 仅基于上述教材检索结果做判断。如果某个选项缺乏教材证据支持，说明"教材证据不足"。
2. 每个判断必须引用具体的card_id。
3. 不超过250字。
直接输出解析文本。

注意：你看到的只有教材检索结果和原题，没有其他参考资料。"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2, max_tokens=600)

    explanation = resp.choices[0].message.content.strip()

    out_path = os.path.join(OUT_DIR, "four_roles_step4_explanation.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(explanation)

    clean = explanation[:400].encode('gbk', errors='replace').decode('gbk')
    print(f"  {clean}...")
    print(f"  Saved to {out_path}")
    return explanation


# ── Main ──────────────────────────────────────────────────────────
async def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("四角色分离检索法实验")
    print(f"Model: {MODEL}")
    print()

    # Step 1: AI #1 自由回答
    free_answer = step1_free_answer()

    # Step 2: AI #2 提取待核查事实
    claims = step2_extract_claims(free_answer)
    if claims.get("leakage"):
        print("\n[FAIL] Leakage in Step 2, stopping")
        return

    # Step 3: LightRAG 搜索
    search_results = await step3_search(claims)
    if search_results is None:
        return

    # Step 4: AI #3 最终解析
    explanation = step4_final_answer(search_results)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  AI #1 分析长度: {len(free_answer)} chars")
    print(f"  AI #2 提取主张数: {len(claims.get('claims_to_verify', []))}")
    print(f"  LightRAG 搜索组数: {len(search_results)}")
    print(f"  AI #3 解析长度: {len(explanation)} chars")

    # Check if E1 found
    all_cards = set()
    for r in search_results.values():
        all_cards.update(r.get("top_card_ids", []))
    e1_found = "v6_b03_N18" in all_cards
    fi_card_found = "v6_b04_N09" in all_cards
    print(f"  v6_b04_N09 (FI总表) found: {fi_card_found}")
    print(f"  v6_b03_N18 (E1税收) found: {e1_found}")

asyncio.run(main())
