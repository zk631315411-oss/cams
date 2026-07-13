"""
P4: Agentic Search Controller — D 选项多步证据搜索
"""
import os, sys, json, re, asyncio

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["SUMMARY_LANGUAGE"] = "Chinese"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EVAL_DIR = os.path.join(DATA_DIR, "agentic_search_eval", "04_agentic_D_search")
INDEX_DIR = os.path.join(DATA_DIR, "lightrag_index")

from sentence_transformers import SentenceTransformer
MODEL = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)

# Ground truth
E_GROUPS = {
    "E1": {"must": ["v6_b03_N18"], "accept": ["v6_b03_N17", "v6_b03_N19"]},
    "E2": {"must": ["v6_b29_N05"], "accept": ["v6_b33_N20", "v6_b33_N25"]},
    "E3": {"must": ["v6_b33_N23"], "accept": ["v6_b33_N24", "v6_b33_N25"]},
    "E4": {"must": ["v6_b33_N38"], "accept": []},
}
SIGNAL_IDS = set()
for g in E_GROUPS.values():
    SIGNAL_IDS.update(g["must"] + g["accept"])

ORACLE_WORDS = ["政府税收缩水", "贸易洗钱", "虚假发票", "BMPE", "黑市比索", "空壳公司",
                "v6_b03_N18", "v6_b33_N23", "v6_b33_N25", "v6_b33_N38"]


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


async def search_cards(rag, query, mode="mix"):
    """Search and return card_ids + content"""
    from lightrag import QueryParam
    r = await rag.aquery_data(query, param=QueryParam(mode=mode, enable_rerank=False))
    chunks = r.get("data", {}).get("chunks", [])
    results = []
    for c in chunks:
        cids = re.findall(r"\[CARD_ID\]\s*(\S+)", c.get("content", ""))
        results.append({
            "card_id": cids[0] if cids else "unknown",
            "content": c.get("content", "")[:200],
        })
    keywords = r.get("metadata", {}).get("keywords", {})
    return results, keywords


def leakage_check(text):
    """Check if text contains oracle words"""
    for w in ORACLE_WORDS:
        if w in text:
            return True, w
    return False, None


GAP_PROMPT = """你是CAMS反洗钱证据搜索助手。你正在为一道考题的D选项搜索教材证据。

题目的D选项声称：洗钱会导致金融机构FI的公司税增加。
已知正确答案是A和E，D是错误选项。

目前已完成的搜索步骤：
{history}

已找到的教材证据卡片：
{found_evidence}

当前证据缺口：
{gaps}

当前是第 {step} 步（总共最多 {max_steps} 步）。

请决定下一步搜索策略并生成查询。输出JSON，不要markdown包裹：
{{
  "step": {step},
  "strategy": "specialization | generalization | exploration | verification",
  "strategy_reason": "为什么选这个策略",
  "gap_analysis": "当前还缺什么证据",
  "query": "新的检索query（中文关键词，空格分隔）",
  "observable_source": {{"词": "retrieved_text | controller_inference"}},
  "decision": "continue | stop_evidence_sufficient | stop_budget_exhausted"
}}

规则：
- query不能使用已知的教材专业术语黑话（"政府税收缩水""贸易洗钱""黑市比索""空壳公司""BMPE"）
- query中的词必须能在已召回证据文本或你的合理推理中找到来源
- 如果证据已足够反证D（主体错配+方向错配），选stop_evidence_sufficient
- 如果已到第{max_steps}步，选stop_budget_exhausted"""


def build_gap_prompt(step, max_steps, trajectory, found_cards):
    """Build the gap detection + query generation prompt"""
    history_lines = []
    for t in trajectory:
        history_lines.append(
            f"Step {t['step']}: query='{t['query']}' strategy={t['strategy']} "
            f"found={t['new_card_ids'][:5]} gaps={t['gaps_after']}"
        )
    history_text = "\n".join(history_lines) if history_lines else "(首轮搜索)"

    found_lines = []
    for cid in list(found_cards)[:10]:
        found_lines.append(f"- {cid}")
    found_text = "\n".join(found_lines) if found_lines else "(尚未找到相关证据)"

    # Determine gaps based on found cards
    missing = []
    for gid, ginfo in E_GROUPS.items():
        all_ids = ginfo["must"] + ginfo["accept"]
        if not any(cid in found_cards for cid in all_ids):
            missing.append(gid)
    gaps_text = ", ".join(missing) if missing else "需确认主体和方向归因"

    return GAP_PROMPT.format(
        step=step,
        max_steps=max_steps,
        history=history_text,
        found_evidence=found_text,
        gaps=gaps_text,
    )


def check_attribution(found_cards, read_texts):
    """Check if found evidence is sufficient for D refutation"""
    # Simple check: do we have E1 (政府税收缩水)?
    has_e1 = any(cid in found_cards for cid in E_GROUPS["E1"]["must"] + E_GROUPS["E1"]["accept"])
    # Combined text for subject/direction analysis
    all_text = " ".join(read_texts)
    has_subject_mismatch = any(w in all_text for w in ["政府", "犯罪分子", "进口商"])
    has_direction_mismatch = any(w in all_text for w in ["缩水", "减少", "规避", "逃避", "逃税", "避税"])

    return {
        "has_e1": has_e1,
        "subject_mismatch_evidence": has_subject_mismatch,
        "direction_mismatch_evidence": has_direction_mismatch,
        "can_refute": has_e1 and has_subject_mismatch and has_direction_mismatch,
    }


async def main():
    os.makedirs(EVAL_DIR, exist_ok=True)
    rag = await create_rag()

    # P3 query from claim decomposition
    initial_query = "洗钱 金融机构 公司税 逃税 避税 税收欺诈 政府税收损失"
    print(f"[Step 1] Initial query: {initial_query}")

    # Leakage check on initial query
    leaked, leaked_word = leakage_check(initial_query)
    if leaked:
        print(f"[FAIL] Oracle word leakage in initial query: {leaked_word}")
        return
    print("[PASS] No leakage in initial query")

    # Step 1: Search
    results, keywords = await search_cards(rag, initial_query)
    card_ids = set(r["card_id"] for r in results if r["card_id"] != "unknown")
    print(f"  Found {len(card_ids)} unique cards")
    for gid, ginfo in E_GROUPS.items():
        hit = [cid for cid in ginfo["must"] + ginfo["accept"] if cid in card_ids]
        if hit:
            print(f"    {gid}: {hit}")

    trajectory = [{
        "step": 1,
        "query": initial_query,
        "strategy": "exploration",
        "keywords_used": keywords,
        "new_card_ids": list(card_ids)[:10],
        "gaps_after": ["E2", "E3", "E4"],
    }]

    found_cards = set(card_ids)
    read_texts = [r["content"] for r in results[:10]]

    # Step 2-4: Gap-driven search
    max_steps = 4
    from openai import OpenAI
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    for step in range(2, max_steps + 1):
        # Build prompt
        prompt = build_gap_prompt(step, max_steps, trajectory, found_cards)

        # Get LLM decision
        resp = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2, max_tokens=1000,
        )
        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        try:
            decision = json.loads(raw)
        except json.JSONDecodeError:
            import json_repair
            decision = json.loads(json_repair.repair_json(raw))

        # Leakage check
        query = decision.get("query", "")
        leaked, leaked_word = leakage_check(query)
        if leaked:
            print(f"[FAIL] Step {step} leakage: {leaked_word}")
            trajectory.append({"step": step, "error": f"leakage: {leaked_word}"})
            break

        strategy = decision.get("strategy", "exploration")
        print(f"\n[Step {step}] strategy={strategy}")
        print(f"  Gap analysis: {decision.get('gap_analysis', 'N/A')[:100]}")
        print(f"  Query: {query}")

        # Search
        results, keywords = await search_cards(rag, query)
        new_ids = set(r["card_id"] for r in results if r["card_id"] != "unknown")
        new_unique = new_ids - found_cards
        found_cards.update(new_ids)
        read_texts.extend(r["content"] for r in results[:5])

        print(f"  New unique cards: {len(new_unique)}")
        for gid, ginfo in E_GROUPS.items():
            hit_new = [cid for cid in ginfo["must"] + ginfo["accept"] if cid in new_unique]
            if hit_new:
                print(f"    {gid} NEW: {hit_new}")

        # Record
        traj_entry = {
            "step": step,
            "query": query,
            "strategy": strategy,
            "keywords_used": keywords,
            "new_card_ids": list(new_unique)[:10],
            "gaps_after": decision.get("gap_analysis", ""),
        }
        trajectory.append(traj_entry)

        if decision.get("decision") in ("stop_evidence_sufficient", "stop_budget_exhausted"):
            print(f"  Decision: {decision['decision']}")
            break

    # Final evaluation
    print(f"\n{'='*60}")
    print("P4 Final Evaluation")
    print(f"{'='*60}")

    attribution = check_attribution(found_cards, read_texts)
    print(f"E1 found: {attribution['has_e1']}")
    print(f"Subject mismatch evidence: {attribution['subject_mismatch_evidence']}")
    print(f"Direction mismatch evidence: {attribution['direction_mismatch_evidence']}")
    print(f"Can refute D: {attribution['can_refute']}")

    # Recall per evidence group
    hits = {}
    for gid, ginfo in E_GROUPS.items():
        all_ids = ginfo["must"] + ginfo["accept"]
        hit_cards = [cid for cid in all_ids if cid in found_cards]
        hits[gid] = {"hit": len(hit_cards) > 0, "cards": hit_cards}
        print(f"  {gid}: {'OK' if hits[gid]['hit'] else 'MISS'} {hit_cards}")

    recall = sum(1 for h in hits.values() if h["hit"])
    noise = sum(1 for cid in list(found_cards)[:15] if cid not in SIGNAL_IDS)
    traceability = len([cid for cid in found_cards if cid != "unknown"])

    # Determine pass class
    if attribution["can_refute"]:
        if recall >= 4:
            pass_class = "B — 强证据通过"
        else:
            pass_class = "A — 判错通过"
    else:
        pass_class = "FAIL"

    report = {
        "pass_class": pass_class,
        "recall": f"{recall}/4",
        "can_refute": attribution["can_refute"],
        "subject_mismatch": attribution["subject_mismatch_evidence"],
        "direction_mismatch": attribution["direction_mismatch_evidence"],
        "total_steps": len(trajectory),
        "total_cards_found": len(found_cards),
        "traceability": f"{traceability}/{len(found_cards)}",
        "hits": hits,
        "trajectory": trajectory,
    }

    out_path = os.path.join(EVAL_DIR, "report.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Trajectory log
    traj_path = os.path.join(EVAL_DIR, "trajectory_log.jsonl")
    with open(traj_path, "w", encoding="utf-8") as f:
        for t in trajectory:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    print(f"\nResult: {pass_class}")
    print(f"Recall: {recall}/4 | Steps: {len(trajectory)} | Refutable: {attribution['can_refute']}")
    print(f"Saved: {out_path}")

    await rag.finalize_storages()


asyncio.run(main())
