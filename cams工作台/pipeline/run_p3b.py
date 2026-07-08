"""
P3b: 选项对照主考点
基于 P3a LLM 的实际输出（考点类型、考点名称、主考点卡片内容），
让 LLM 把每个选项映射到框架卡片上。

原则：prompt 只用 P3a 的输出 + 卡片原文 + 归因定义。
不给任何选项的具体结论。
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

from sentence_transformers import SentenceTransformer
MODEL = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)

async def emb_func(texts):
    if isinstance(texts, str): texts = [texts]
    return MODEL.encode(texts, normalize_embeddings=True)

async def llm_func(prompt, system_prompt=None, history_messages=None, **kw):
    from lightrag.llm.openai import openai_complete_if_cache
    return await openai_complete_if_cache(
        "deepseek-v4-pro", prompt,
        system_prompt=system_prompt, history_messages=history_messages or [],
        api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com", **kw)

async def create_rag():
    from lightrag import LightRAG; from lightrag.utils import EmbeddingFunc
    rag = LightRAG(working_dir=INDEX_DIR, llm_model_func=llm_func,
                   embedding_func=EmbeddingFunc(embedding_dim=512, max_token_size=512, func=emb_func),
                   top_k=60, chunk_top_k=30, addon_params={"language": "Chinese"})
    await rag.initialize_storages(); return rag


def p3b_map_options(p3a, main_card_text, neighbor_texts):
    """LLM maps each option to the framework card.
    Prompt 用 P3a 的 LLM 输出构造，不手写任何选项结论。"""
    from openai import OpenAI
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    neighbor_context = ""
    for cid, text in neighbor_texts.items():
        if cid != "v6_b04_N09":
            neighbor_context += f"\n--- [{cid}] ---\n{text[:300]}\n"

    # Load TOC
    toc_path = os.path.join(DATA_DIR, "agentic_search_eval_v2", "toc_ch2_compact.txt")
    with open(toc_path, "r", encoding="utf-8") as f:
        toc = f.read()

    prompt = f"""你是CAMS教研专家。以下是教材第2章目录，供你了解教材整体结构：

【教材目录】
{toc}

P3a已将本题定位为"{p3a['exam_point_type']}"，考点为"{p3a['exam_point_name']}"。

以下是教材中该考点的对应卡片：

【主考点卡片 v6_b04_N09】
{main_card_text}

【相邻卡片参考】
{neighbor_context if neighbor_context else "(无)"}

【题目】
题干：洗钱会对金融机构FI造成哪些后果？（选择两个。）
A. 盈利业务的减少或损失
B. 代理银行设施的增加
C. 雇员人数减少
D. 公司税的增加
E. 调查费用和罚金的增加
正确答案：A, E

请逐一判断每个选项，仅基于卡片内容：

1. 卡片中有直接对应吗？（framework_match: true/false）
2. 如有，对应卡片里哪句话？（framework_evidence）
3. 归因判断（严格四选一）：
   - support_correct_option: 卡片明确支持此选项说法
   - direction_mismatch: 卡片提到相关概念但方向/描述相反
   - no_textbook_support: 卡片完全没提到此概念
   - pending_cross_section: 卡片没提到，且此概念不属于本考点框架，可能涉及其他章节知识点，需跨节补查
4. need_cross_section_search: 只有归因为pending_cross_section时才为true
5. cross_section_direction: 如需跨节补查，描述应查什么方向（这是你给下一步P4的指示）。如不需要，留空。

重要：请综合卡片内容和教材目录做判断。如果选项概念在卡片中没提到，但目录显示教材有其他小节可能涉及此概念，应归为pending_cross_section并指明方向。只有在目录中也找不到相关小节时，才归为no_textbook_support。

归因判断方法（请严格按以下步骤）：
第一步：看卡片里有没有直接对应？
  有 → framework_match=true，根据对应关系选 support_correct_option 或 direction_mismatch
  没有 → 进入第二步
第二步：看教材目录里有没有相关小节可能涉及此概念？
  目录里有 → pending_cross_section（需要跨节补查），cross_section_direction写明去哪个小节查什么
  目录里也没有 → no_textbook_support（教材无支持）

输出JSON（不要markdown包裹）：
{{
  "framework_card": "v6_b04_N09",
  "options": [
    {{
      "option": "A",
      "claim": "盈利业务的减少或损失",
      "framework_match": true/false,
      "framework_evidence": "卡片原文片段",
      "attribution": "support_correct_option|direction_mismatch|no_textbook_support|pending_cross_section",
      "need_cross_section_search": true/false,
      "cross_section_direction": "给P4的补查方向指示，或留空"
    }}
  ]
}}"""

    resp = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1, max_tokens=2000)

    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import json_repair
        result = json.loads(json_repair.repair_json(raw))

    return result


async def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    p3a_path = os.path.join(OUT_DIR, "p3a_question_framework.json")
    with open(p3a_path, "r", encoding="utf-8") as f:
        p3a = json.load(f)

    print("=" * 60)
    print("P3b: Option-to-Framework Mapping")
    print(f"  P3a says: {p3a['exam_point_type']} — {p3a['exam_point_name']}")
    print("=" * 60)

    rag = await create_rag()

    # Read framework cards
    main_cards = ["v6_b04_N09"] + p3a.get("v6_b04_cards_found", [])
    main_cards = list(dict.fromkeys(main_cards))

    card_texts = {}
    for cid in main_cards:
        doc = await rag.full_docs.get_by_id(cid)
        if doc:
            card_texts[cid] = doc.get("content", "")
            print(f"  Loaded {cid}: {len(card_texts[cid])} chars")
        else:
            print(f"  MISS: {cid}")

    main_text = card_texts.get("v6_b04_N09", "")
    if not main_text:
        print("[FAIL] Cannot read v6_b04_N09")
        await rag.finalize_storages()
        return

    p3b = p3b_map_options(p3a, main_text, card_texts)

    print(f"\n  --- LLM Output ---")
    for opt in p3b.get("options", []):
        direction = opt.get("cross_section_direction", "")[:80]
        print(f"  {opt['option']}: match={opt.get('framework_match')}, attr={opt.get('attribution')}, cross={opt.get('need_cross_section_search')}")
        if direction:
            print(f"         P4方向(LLM生成): {direction}")

    out_path = os.path.join(OUT_DIR, "p3b_option_mapping.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(p3b, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved to {out_path}")
    await rag.finalize_storages()

asyncio.run(main())
