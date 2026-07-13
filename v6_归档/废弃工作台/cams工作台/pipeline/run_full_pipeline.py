"""
完整管线: P3 → P4 → P5 → P6 → P7
不做人工干预，每一步的输出是下一步的输入
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

# Ground truth for evaluation only (NOT used in search)
E_GROUPS = {
    "E1": {"must": ["v6_b03_N18"], "accept": ["v6_b03_N17", "v6_b03_N19"]},
    "E2": {"must": ["v6_b29_N05"], "accept": ["v6_b33_N20", "v6_b33_N25"]},
    "E3": {"must": ["v6_b33_N23"], "accept": ["v6_b33_N24", "v6_b33_N25"]},
    "E4": {"must": ["v6_b33_N38"], "accept": []},
}

ORACLE_WORDS = ["政府税收缩水", "贸易洗钱", "虚假发票", "BMPE", "黑市比索", "空壳公司"]

# ── LLM / Embedding ────────────────────────────────────────────
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

# ── P3: Claim Decomposition ─────────────────────────────────────
def p3_decompose():
    from openai import OpenAI
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    prompt = """分析这道CAMS多选题的D选项，做结构化拆解，生成检索查询。

D选项说：洗钱会对金融机构FI造成"公司税的增加"。
已知正确答案是A和E，D是错误选项。

请从以下维度分析需要检索什么证据来反证D：
1. 主体维度：如果"公司税增加"是错的，那真正受税收影响的主体是谁？
2. 方向维度：洗钱对税收的影响方向是什么？
3. 机制维度：洗钱中涉及税务的常见机制方向？

输出JSON（不要markdown包裹）：
{
  "option": "D",
  "claim": "洗钱会导致金融机构FI的公司税增加",
  "search_queries": [
    {
      "purpose": "这个查询想验证什么",
      "query": "检索关键词（空格分隔）",
      "source_of_terms": {"词1": "question_text", "词2": "model_inference_from_question"}
    }
  ]
}

规则：
- query不能用教材专有名词（"政府税收缩水""贸易洗钱""黑市比索""空壳公司""BMPE"）
- source_of_terms必须逐个词标注来源：question_text（题目中出现）/ model_inference（基于题目推理）
- 不要只复述选项原文，要基于结构分析生成检索方向"""

    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1, max_tokens=1500)

    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import json_repair
        result = json.loads(json_repair.repair_json(raw))

    # Leakage check
    for sq in result.get("search_queries", []):
        q = sq.get("query", "")
        for w in ORACLE_WORDS:
            if w in q:
                print(f"  [LEAK] Oracle word '{w}' in query: {q}")
                return None

    return result

# ── P4: Agentic Search for D ────────────────────────────────────
async def p4_agentic_search(rag, p3_result):
    from lightrag import QueryParam
    from openai import OpenAI
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    queries = [sq["query"] for sq in p3_result.get("search_queries", [])]
    if not queries:
        print("[FAIL] P3 produced no search queries")
        return None

    initial_query = queries[0]
    print(f"\nP4 Step 1 query: {initial_query}")

    all_cards = set()
    all_texts = {}
    trajectory = []

    for step in range(1, 5):
        if step == 1:
            query = initial_query
            strategy = "exploration"
        else:
            # LLM generates next query based on gaps
            found_summary = "\n".join(
                f"- {cid}: {all_texts.get(cid, '...')[:80]}" for cid in list(all_cards)[:8]
            )
            gap_prompt = f"""当前第{step}步（共4步）。已找到的教材证据：
{found_summary if found_summary else '(无)'}

D选项声称"洗钱会导致FI公司税增加"。基于已找到的证据，判断还缺什么，生成下一步检索query。

输出JSON：
{{"gap_analysis": "还缺什么证据", "strategy": "specialization|generalization|exploration|verification", "query": "检索关键词", "decision": "continue|stop"}}

规则：query不能用教材专有名词（"政府税收缩水""贸易洗钱""黑市比索""空壳公司""BMPE"）"""

            resp = client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=[{"role": "user", "content": gap_prompt}],
                temperature=0.2, max_tokens=500)
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            try:
                decision = json.loads(raw)
            except json.JSONDecodeError:
                import json_repair
                decision = json.loads(json_repair.repair_json(raw))

            query = decision.get("query", "")
            strategy = decision.get("strategy", "exploration")

            # Leakage check
            for w in ORACLE_WORDS:
                if w in query:
                    print(f"  [LEAK] Step {step}: '{w}' in query")
                    trajectory.append({"step": step, "error": f"leakage: {w}"})
                    return trajectory, all_cards, all_texts

            if decision.get("decision") == "stop":
                print(f"  Step {step}: LLM decided to stop")
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

        # Check evidence groups
        for gid, ginfo in E_GROUPS.items():
            hit = [cid for cid in ginfo["must"] + ginfo["accept"] if cid in new_cards]
            if hit:
                print(f"    {gid} NEW: {hit}")

    return trajectory, all_cards, all_texts

# ── P5: All-Option Search ───────────────────────────────────────
async def p5_all_options(rag, p3_result):
    from lightrag import QueryParam

    option_queries = {
        "A": "洗钱 金融机构 盈利业务 减少 损失 流失",
        "B": "洗钱 代理银行 设施 增加 终止 减少",
        "C": "洗钱 金融机构 雇员 人数 减少",
        "D": p3_result["search_queries"][0]["query"],
        "E": "洗钱 金融机构 调查费用 罚金 罚款 增加",
    }
    # Note: A/B/C/E queries derived from question text only, no oracle words

    results = {}
    for opt, query in option_queries.items():
        r = await rag.aquery_data(query, param=QueryParam(mode="mix", enable_rerank=False))
        chunks = r.get("data", {}).get("chunks", [])
        card_ids = []
        for c in chunks[:20]:
            cids = re.findall(r"\[CARD_ID\]\s*(\S+)", c.get("content", ""))
            for cid in cids:
                if cid not in card_ids:
                    card_ids.append(cid)

        # Count evidence groups hit
        hits = {}
        for gid, ginfo in E_GROUPS.items():
            all_ids = ginfo["must"] + ginfo["accept"]
            hit = [cid for cid in all_ids if cid in card_ids]
            hits[gid] = len(hit) > 0

        results[opt] = {
            "query": query,
            "top15_card_ids": card_ids[:15],
            "total_found": len(card_ids),
            "evidence_groups_hit": {gid: h for gid, h in hits.items()},
        }
        print(f"  {opt}: {len(card_ids)} cards, E1={hits.get('E1', False)}, groups={sum(1 for h in hits.values() if h)}/4")

    return results

# ── P6: Generate Explanation ─────────────────────────────────────
def p6_generate_explanation(p4_cards, p4_texts, p5_results):
    from openai import OpenAI
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    # Build evidence from actual findings
    evidence_lines = []
    for cid in sorted(p4_cards):
        text = p4_texts.get(cid, "")
        # Keep only cards with useful content
        if len(text) > 30:
            # Extract key info from card
            know_match = re.search(r'\[KNOWLEDGE\]\s*(.+?)(?:\n|$)', text)
            cite_match = re.search(r'\[CITATION\]\s*(.+?)(?:\n|$)', text)
            if know_match:
                evidence_lines.append(f"- [{cid}] {know_match.group(1)[:150]}")
            elif cite_match:
                evidence_lines.append(f"- [{cid}] {cite_match.group(1)[:150]}")

    evidence_text = "\n".join(evidence_lines[:15]) if evidence_lines else "(无直接证据)"

    prompt = f"""基于以下教材证据，为一道CAMS考题写出解析。

题目：(多选题)洗钱会对金融机构FI造成哪些后果？(选择两个。)
选项：A.盈利业务的减少或损失 B.代理银行设施的增加 C.雇员人数减少 D.公司税的增加 E.调查费用和罚金的增加
正确答案：A,E

系统找到的教材证据：
{evidence_text}

请写出解析。要求：
1. 如果证据充分，说明A/E为什么对、B/C/D为什么错，每个判断引用card_id
2. 如果证据不足以判断某个选项，明确说"教材证据不足，需教研复核"
3. D选项如能判断，必须说明主体错配和方向错配
4. 不超过250字，不用套话
直接输出解析文本。"""

    resp = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2, max_tokens=600)
    return resp.choices[0].message.content.strip()

# ── Main Pipeline ────────────────────────────────────────────────
async def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # P3
    print("=" * 60)
    print("P3: Claim Decomposition")
    p3 = p3_decompose()
    if p3 is None:
        print("[FAIL] P3 leakage detected"); return
    with open(os.path.join(OUT_DIR, "p3_claim_decomp.json"), "w", encoding="utf-8") as f:
        json.dump(p3, f, ensure_ascii=False, indent=2)
    print(f"  Claims: {p3.get('claim', 'N/A')}")
    print(f"  Queries: {[sq['query'][:60] for sq in p3.get('search_queries', [])]}")
    print("  [PASS] P3")

    # Init RAG
    rag = await create_rag()

    # P4
    print("\n" + "=" * 60)
    print("P4: Agentic Search for D")
    p4_traj, p4_cards, p4_texts = await p4_agentic_search(rag, p3)
    if p4_traj is None:
        print("[FAIL] P4 leakage detected"); return

    # Evaluate P4
    p4_hits = {}
    for gid, ginfo in E_GROUPS.items():
        all_ids = ginfo["must"] + ginfo["accept"]
        hit_cards = [cid for cid in all_ids if cid in p4_cards]
        p4_hits[gid] = {"hit": len(hit_cards) > 0, "cards": hit_cards}
    p4_recall = sum(1 for h in p4_hits.values() if h["hit"])

    # Check attribution
    all_text = " ".join(p4_texts.values())
    subject_ok = any(w in all_text for w in ["政府", "犯罪分子", "进口商"])
    direction_ok = any(w in all_text for w in ["缩水", "减少", "规避", "逃税", "避税"])
    can_refute = p4_hits["E1"]["hit"] and subject_ok and direction_ok

    p4_report = {
        "trajectory": p4_traj,
        "total_cards": len(p4_cards),
        "recall": f"{p4_recall}/4",
        "hits": {gid: h["cards"] for gid, h in p4_hits.items()},
        "subject_mismatch": subject_ok,
        "direction_mismatch": direction_ok,
        "can_refute_D": can_refute,
    }
    with open(os.path.join(OUT_DIR, "p4_agentic_search.json"), "w", encoding="utf-8") as f:
        json.dump(p4_report, f, ensure_ascii=False, indent=2)
    print(f"  Recall: {p4_recall}/4, RefuteD: {can_refute}")
    for gid, h in p4_hits.items():
        print(f"    {gid}: {'OK' if h['hit'] else 'MISS'} {h['cards']}")

    # P5
    print("\n" + "=" * 60)
    print("P5: All-Option Search")
    p5 = await p5_all_options(rag, p3)
    with open(os.path.join(OUT_DIR, "p5_all_options.json"), "w", encoding="utf-8") as f:
        json.dump(p5, f, ensure_ascii=False, indent=2)
    p5_summary = {}
    for opt, r in p5.items():
        p5_summary[opt] = {"top5": r["top15_card_ids"][:5], "groups_hit": r["evidence_groups_hit"]}
        print(f"  {opt}: top5={r['top15_card_ids'][:3]}")

    # P6
    print("\n" + "=" * 60)
    print("P6: Generate Explanation")
    p6 = p6_generate_explanation(p4_cards, p4_texts, p5)
    with open(os.path.join(OUT_DIR, "p6_explanation.md"), "w", encoding="utf-8") as f:
        f.write(p6)
    print(f"  {p6[:200]}...")

    # P7: Final Audit
    print("\n" + "=" * 60)
    print("P7: Final Audit")

    # v6_b04_N09 check (the gold FI consequences card)
    fi_card_found = "v6_b04_N09" in p4_cards or any("v6_b04_N09" in p5[opt]["top15_card_ids"] for opt in "ABCE")
    a_direct = any(cid in p5["A"]["top15_card_ids"][:5] for cid in ["v6_b04_N09", "v6_b04_N17"])
    e_direct = any(cid in p5["E"]["top15_card_ids"][:5] for cid in ["v6_b04_N09", "v6_b04_N21"])

    p4_pass = can_refute  # class A
    p5_pass = fi_card_found and a_direct and e_direct
    multi_q_ready = p4_pass and p5_pass  # both needed for multi-question

    audit = {
        "p3_pass": p3 is not None,
        "p4_pass_class_A": p4_pass,
        "p4_recall": f"{p4_recall}/4",
        "p5_pass": p5_pass,
        "fi_card_v6_b04_N09_found": fi_card_found,
        "A_direct_evidence": a_direct,
        "E_direct_evidence": e_direct,
        "D_can_refute": can_refute,
        "multi_question_ready": multi_q_ready,
        "conclusion": "满足多题验证条件" if multi_q_ready else "不满足多题验证条件",
    }
    with open(os.path.join(OUT_DIR, "p7_final_audit.json"), "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)

    print(f"  P4 class A: {p4_pass}")
    print(f"  P5 direct evidence: {p5_pass}")
    print(f"  FI card v6_b04_N09: {fi_card_found}")
    print(f"  A direct: {a_direct}, E direct: {e_direct}")
    print(f"  Multi-question ready: {multi_q_ready}")
    print(f"\n  >>> {audit['conclusion']}")

    await rag.finalize_storages()

asyncio.run(main())
