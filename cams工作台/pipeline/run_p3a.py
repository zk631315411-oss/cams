"""
P3a: 题干级分析 + 主考点证据检索
不要一上来就按选项搜。先判断这题考的是教材里哪个总表/列表/流程/定义。
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

# ── LLM / Embedding ────────────────────────────────────────────
from sentence_transformers import SentenceTransformer
MODEL = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)

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
    from lightrag import LightRAG; from lightrag.utils import EmbeddingFunc
    rag = LightRAG(working_dir=INDEX_DIR, llm_model_func=llm_func,
                   embedding_func=EmbeddingFunc(embedding_dim=512, max_token_size=512, func=emb_func),
                   top_k=60, chunk_top_k=30, addon_params={"language": "Chinese"})
    await rag.initialize_storages(); return rag

# ── P3a: Question-level Analysis ──────────────────────────────────

def p3a_analyze_question():
    """Step 1: LLM analyzes the question at the question level, NOT option level."""
    from openai import OpenAI
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    prompt = """你是一位CAMS考试教研专家。请分析下面这道题，做**题干级分析**，不要一上来就按选项搜。

题目：洗钱会对金融机构FI造成哪些后果？（选择两个。）
选项：
A. 盈利业务的减少或损失
B. 代理银行设施的增加
C. 雇员人数减少
D. 公司税的增加
E. 调查费用和罚金的增加
正确答案：A, E

请回答三个问题：
1. **题干意图**：这道题在问什么？一句话概括。
2. **考点定位**：这属于教材里哪个考点？是列表型/流程型/定义型/辨析型？
3. **主考点检索**：如果要找教材里对应这道题的"总表"或"答案卡"，应该用什么关键词搜？

重要规则：
- 考点类型判断：教材里有"洗钱对金融机构的负面影响列表"这类总表的就是列表型
- 检索query要能直接找到这个总表卡
- query应使用通用术语，不要使用生僻的专有名词

输出JSON（不要markdown包裹）：
{
  "question_intent": "题干一句话概括",
  "exam_point_type": "列表型|流程型|定义型|辨析型",
  "exam_point_name": "考点名称",
  "main_evidence_query": "检索关键词（空格分隔）",
  "rationale": "为什么这个query能找到主考点总表",
  "observable_source": {
    "词1": "question_text|controller_inference",
    "词2": "question_text|controller_inference"
  }
}"""

    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1, max_tokens=1000)

    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import json_repair
        result = json.loads(json_repair.repair_json(raw))

    # Leakage check
    query = result.get("main_evidence_query", "")
    for w in ORACLE_WORDS:
        if w in query:
            print(f"  [LEAK] Oracle word '{w}' in query: {query}")
            return None

    return result

async def p3a_search_main_evidence(rag, p3a_result):
    """Step 2: Search LightRAG with the main evidence query."""
    from lightrag import QueryParam

    query = p3a_result["main_evidence_query"]
    print(f"\n  Search query: {query}")

    r = await rag.aquery_data(query, param=QueryParam(mode="mix", enable_rerank=False))
    chunks = r.get("data", {}).get("chunks", [])

    card_ids = []
    card_texts = {}
    for c in chunks[:30]:
        cids = re.findall(r"\[CARD_ID\]\s*(\S+)", c.get("content", ""))
        for cid in cids:
            if cid not in card_ids:
                card_ids.append(cid)
                card_texts[cid] = c.get("content", "")[:300]

    return card_ids, card_texts

# ── Main ──────────────────────────────────────────────────────────

async def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    print("=" * 60)
    print("P3a: Question-level Analysis + Main Evidence Search")
    print("=" * 60)

    # Step 1: LLM analysis
    p3a = p3a_analyze_question()
    if p3a is None:
        print("[FAIL] P3a leakage detected")
        return

    print(f"  Question intent: {p3a.get('question_intent', 'N/A')}")
    print(f"  Exam point type: {p3a.get('exam_point_type', 'N/A')}")
    print(f"  Exam point name: {p3a.get('exam_point_name', 'N/A')}")
    print(f"  Main query: {p3a.get('main_evidence_query', 'N/A')}")

    # Step 2: Search
    rag = await create_rag()
    card_ids, card_texts = await p3a_search_main_evidence(rag, p3a)
    p3a["top30_card_ids"] = card_ids[:30]
    p3a["total_cards_found"] = len(card_ids)

    print(f"\n  Top 15 cards found:")
    for i, cid in enumerate(card_ids[:15]):
        marker = ""
        if cid == "v6_b04_N09":
            marker = " ★★★ TARGET: FI后果总表卡"
        elif "v6_b04" in cid:
            marker = " ★ v6_b04 section"
        print(f"    {i+1}. {cid}{marker}")

    # Step 3: Check if v6_b04_N09 is found
    fi_card_found = "v6_b04_N09" in card_ids
    fi_card_rank = card_ids.index("v6_b04_N09") + 1 if fi_card_found else -1
    v6_b04_cards = [c for c in card_ids if "v6_b04" in c]

    p3a["fi_card_v6_b04_N09_found"] = fi_card_found
    p3a["fi_card_rank"] = fi_card_rank
    p3a["v6_b04_cards_found"] = v6_b04_cards[:10]

    print(f"\n  ── P3a Results ──")
    print(f"  v6_b04_N09 found: {fi_card_found}")
    print(f"  v6_b04_N09 rank: {fi_card_rank if fi_card_found else 'NOT FOUND'}")
    print(f"  Other v6_b04 cards: {v6_b04_cards[:5]}")

    # Check if v6_b04_N09 content has FI consequences list
    if fi_card_found:
        n09_text = card_texts.get("v6_b04_N09", "")
        has_consequences = any(w in n09_text for w in ["盈利", "代理银行", "调查费用", "罚金", "罚款", "后果"])
        p3a["v6_b04_N09_has_fi_consequences"] = has_consequences
        print(f"  v6_b04_N09 has FI consequences content: {has_consequences}")
        clean = n09_text[:200].encode('gbk', errors='replace').decode('gbk')
        print(f"  Preview: {clean}...")

    # Save
    out_path = os.path.join(OUT_DIR, "p3a_question_framework.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(p3a, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved to {out_path}")

    # Pass/fail
    passed = fi_card_found and p3a.get("v6_b04_N09_has_fi_consequences", False)
    print(f"\n  P3a PASS: {passed}")
    await rag.finalize_storages()

asyncio.run(main())
