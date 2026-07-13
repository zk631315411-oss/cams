"""
P4: 跨节补查 — 只对 P3b 标记为 need_cross_section_search 的选项做 Agentic Search
当前只有 D 选项（公司税的增加）需要跨节反证。

关键原则：
- 初始 query 由 P3b 的 cross_section_direction（LLM 自己生成的）驱动
- 每步 gap prompt 只给已找到的证据，让 LLM 自己判断缺口和下一步方向
- 不给任何预设结论
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

E_GROUPS = {
    "E1": {"must": ["v6_b03_N18"], "accept": ["v6_b03_N17", "v6_b03_N19"]},
    "E2": {"must": ["v6_b29_N05"], "accept": ["v6_b33_N20", "v6_b33_N25"]},
    "E3": {"must": ["v6_b33_N23"], "accept": ["v6_b33_N24", "v6_b33_N25"]},
    "E4": {"must": ["v6_b33_N38"], "accept": []},
}

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


def generate_initial_query(cross_section_direction):
    """基于 P3b LLM 生成的 cross_section_direction 生成首轮检索 query。
    注意：cross_section_direction 是 P3b 的 LLM 自己的输出，不是人手写的。"""
    from openai import OpenAI
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    prompt = f"""你是CAMS教研专家。需要为一道CAMS多选题的D选项"公司税的增加"找跨节反证证据。

D选项声称洗钱会导致金融机构FI的公司税增加。但教材"洗钱对金融机构的负面影响"总表（v6_b04_N09）中没有公司税条目。

P3b已确定补查方向：{cross_section_direction}

请生成一个检索query，去教材中找相关证据。注意：
- query用空格分隔的关键词，使用通用术语

输出JSON（不要markdown包裹）：
{{
  "search_purpose": "这个查询想验证什么",
  "query": "检索关键词",
  "observable_source": {{"词1": "question_text|retrieved_text|p3b_output", "词2": "同上"}}
}}"""

    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1, max_tokens=600)

    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import json_repair
        result = json.loads(json_repair.repair_json(raw))

    q = result.get("query", "")
    for w in ORACLE_WORDS:
        if w in q:
            print(f"  [LEAK] Oracle word '{w}' in query: {q}")
            return None

    return result


def generate_next_query(step, found_cards, card_texts):
    """基于已找到的证据，让 LLM 自己判断缺口并生成下一步 query。
    不给任何预设结论，只给证据原文。"""
    from openai import OpenAI
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    found_summary = "\n".join(
        f"- {cid}: {card_texts.get(cid, '...')[:120]}" for cid in list(found_cards)[:10]
    )

    prompt = f"""当前第{step}步（共3步）。已找到的教材证据：
{found_summary if found_summary else '(无)'}

D选项声称"洗钱会导致金融机构FI的公司税增加"。

请基于已找到的证据回答：
1. 当前证据是否足以判断D选项的对错？如果够，为什么？（decision: stop）
2. 如果不够，还缺什么证据？（gap_analysis）
3. 下一步应该用什么关键词搜？（query）
4. 搜索策略是什么？（strategy: specialization|generalization|exploration|verification）

重要：
- 不要预设结论。仅基于已找到的证据做判断。
- query使用通用术语

输出JSON（不要markdown包裹）：
{{"gap_analysis": "还缺什么证据", "strategy": "specialization|generalization|exploration|verification", "query": "检索关键词", "decision": "continue|stop"}}"""

    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2, max_tokens=500)
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        decision = json.loads(raw)
    except json.JSONDecodeError:
        import json_repair
        decision = json.loads(json_repair.repair_json(raw))

    q = decision.get("query", "")
    for w in ORACLE_WORDS:
        if w in q:
            print(f"  [LEAK] Step {step}: '{w}' in query")
            return None

    return decision


async def p4_cross_section_search(rag, p3b):
    from lightrag import QueryParam

    d_option = [o for o in p3b["options"] if o["option"] == "D"]
    if not d_option or not d_option[0].get("need_cross_section_search"):
        print("[FAIL] D option not marked for cross-section search")
        return None, None, None

    direction = d_option[0].get("cross_section_direction", "")
    if not direction:
        print("[FAIL] P3b did not provide cross_section_direction for D")
        return None, None, None

    print(f"\n  P3b cross_section_direction (LLM-generated): {direction}")

    init = generate_initial_query(direction)
    if init is None:
        return None, None, None

    initial_query = init["query"]
    print(f"  Step 1 query: {initial_query}")
    print(f"  Purpose: {init.get('search_purpose', 'N/A')}")

    all_cards = set()
    all_texts = {}
    trajectory = []

    for step in range(1, 4):
        if step == 1:
            query = initial_query
            strategy = "exploration"
        else:
            decision = generate_next_query(step, all_cards, all_texts)
            if decision is None:
                trajectory.append({"step": step, "error": "leakage"})
                return trajectory, all_cards, all_texts

            query = decision.get("query", "")
            strategy = decision.get("strategy", "exploration")

            print(f"  Step {step} gap_analysis: {decision.get('gap_analysis', 'N/A')[:100]}")

            if decision.get("decision") == "stop":
                print(f"  Step {step}: LLM decided to stop — evidence sufficient")
                break

        print(f"  Step {step} [{strategy}]: {query[:80]}")

        r = await rag.aquery_data(query, param=QueryParam(mode="mix", enable_rerank=False))
        chunks = r.get("data", {}).get("chunks", [])
        step_cards = set()
        for c in chunks[:20]:
            cids = re.findall(r"\[CARD_ID\]\s*(\S+)", c.get("content", ""))
            for cid in cids:
                if cid not in all_texts and len(c.get("content", "")) > 50:
                    all_texts[cid] = c.get("content", "")[:250]
                step_cards.add(cid)

        new_cards = step_cards - all_cards
        all_cards.update(step_cards)

        traj = {
            "step": step, "strategy": strategy, "query": query,
            "new_card_ids": sorted(list(new_cards))[:15],
            "total_cards_so_far": len(all_cards),
        }
        trajectory.append(traj)

        for gid, ginfo in E_GROUPS.items():
            hit = [cid for cid in ginfo["must"] + ginfo["accept"] if cid in new_cards]
            if hit:
                print(f"    {gid} NEW: {hit}")

    return trajectory, all_cards, all_texts


async def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    p3b_path = os.path.join(OUT_DIR, "p3b_option_mapping.json")
    with open(p3b_path, "r", encoding="utf-8") as f:
        p3b = json.load(f)

    print("=" * 60)
    print("P4: Cross-Section Agentic Search (D option only)")
    print("=" * 60)

    rag = await create_rag()

    trajectory, all_cards, all_texts = await p4_cross_section_search(rag, p3b)
    if trajectory is None:
        print("[FAIL] P4 leakage detected")
        await rag.finalize_storages()
        return

    print(f"\n  Total cards found: {len(all_cards)}")

    p4_hits = {}
    for gid, ginfo in E_GROUPS.items():
        all_ids = ginfo["must"] + ginfo["accept"]
        hit_cards = [cid for cid in all_ids if cid in all_cards]
        p4_hits[gid] = {"hit": len(hit_cards) > 0, "cards": hit_cards}

    p4_recall = sum(1 for h in p4_hits.values() if h["hit"])

    all_text = " ".join(all_texts.values())
    subject_ok = any(w in all_text for w in ["政府", "犯罪分子", "进口商", "征税"])
    direction_ok = any(w in all_text for w in ["缩水", "减少", "规避", "逃税", "避税", "流失"])
    can_refute = p4_hits["E1"]["hit"] and subject_ok and direction_ok

    p4_report = {
        "trajectory": trajectory,
        "total_cards": len(all_cards),
        "recall": f"{p4_recall}/4",
        "hits": {gid: h["cards"] for gid, h in p4_hits.items()},
        "subject_mismatch_evidence": subject_ok,
        "direction_mismatch_evidence": direction_ok,
        "can_refute_D": can_refute,
        "e1_found": p4_hits["E1"]["hit"],
        "e1_cards": p4_hits["E1"]["cards"],
    }

    out_path = os.path.join(OUT_DIR, "p4_cross_section_search.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(p4_report, f, ensure_ascii=False, indent=2)

    print(f"\n  --- P4 Results ---")
    for gid in ["E1", "E2", "E3", "E4"]:
        print(f"  {gid}: {'OK' if p4_hits[gid]['hit'] else 'MISS'} {p4_hits[gid]['cards']}")
    print(f"  Recall: {p4_recall}/4")
    print(f"  Subject OK: {subject_ok}, Direction OK: {direction_ok}")
    print(f"  Can refute D: {can_refute}")

    await rag.finalize_storages()

asyncio.run(main())
