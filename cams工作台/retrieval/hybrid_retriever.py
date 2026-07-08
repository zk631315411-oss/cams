"""
证据检索器 MVP — 混合检索 (BM25 + Embedding → RRF) + LLM 题目拆解
用法: python hybrid_retriever.py           # 人工锚点
      python hybrid_retriever.py --llm     # LLM 生成锚点
      python hybrid_retriever.py --both    # 两种锚点对比
"""
import json
import os
import re
import sys
import numpy as np

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from openai import OpenAI

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CARDS_FILE = os.path.join(DATA_DIR, "cards_ch2.json")
QUESTIONS_FILE = os.path.join(DATA_DIR, "questions.json")
OUTPUT_DIR = DATA_DIR

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# ── 1. 字符 n-gram 分词 ────────────────────────────────────────────
def char_ngrams(text, n_range=(2, 3)):
    text = text.strip()
    tokens = []
    for n in range(n_range[0], n_range[1] + 1):
        tokens.extend(text[i:i + n] for i in range(len(text) - n + 1))
    return tokens


# ── 2. 加载数据 ────────────────────────────────────────────────────
def load_cards(min_citation_len=0):
    """加载卡片，可选择过滤短 citation"""
    with open(CARDS_FILE, "r", encoding="utf-8") as f:
        cards = json.load(f)
    if min_citation_len > 0:
        before = len(cards)
        cards = [c for c in cards if len(c.get("citation", "").strip()) >= min_citation_len]
        print(f"加载 {before} 张卡片，过滤 citation<{min_citation_len}字后保留 {len(cards)} 张")
    else:
        print(f"加载 {len(cards)} 张卡片")
    return cards


def load_question(qid="2.1_19"):
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 兼容两种格式: 顶层数组 或 {"questions": [...]}
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict) and "questions" in data:
        questions = data["questions"]
    else:
        questions = [data]
    for q in questions:
        if not isinstance(q, dict):
            continue
        if q.get("id") == qid or q.get("question_id") == qid:
            return q
    for q in questions:
        if not isinstance(q, dict):
            continue
        qid_field = q.get("id", "") or q.get("question_id", "")
        if "2.1_19" in qid_field:
            return q
    return None


def build_card_text(card):
    parts = []
    for field in ["knowledge", "citation", "context_before", "context_after"]:
        val = card.get(field, "").strip()
        if val:
            parts.append(val)
    return " ".join(parts)


# ── 3. BM25 检索器 ─────────────────────────────────────────────────
class BM25Retriever:
    def __init__(self, cards):
        self.cards = cards
        self.texts = [build_card_text(c) for c in cards]
        self.tokenized = [char_ngrams(t) for t in self.texts]
        self.bm25 = BM25Okapi(self.tokenized)

    def search(self, query, top_k=20):
        query_tokens = char_ngrams(query)
        scores = self.bm25.get_scores(query_tokens)
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(int(i), float(scores[i])) for i in top_indices if scores[i] > 0]


# ── 4. Embedding 检索器 ─────────────────────────────────────────────
class EmbeddingRetriever:
    def __init__(self, cards, model_name="BAAI/bge-small-zh-v1.5"):
        self.cards = cards
        self.texts = [build_card_text(c) for c in cards]
        print(f"加载 embedding 模型: {model_name} ...")
        self.model = SentenceTransformer(model_name, local_files_only=True)
        print("向量化卡片 ...")
        self.embeddings = self.model.encode(
            self.texts, normalize_embeddings=True, show_progress_bar=True)

    def search(self, query, top_k=20):
        q_emb = self.model.encode([query], normalize_embeddings=True)
        scores = np.dot(self.embeddings, q_emb.T).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(int(i), float(scores[i])) for i in top_indices]


# ── 5. RRF 融合 ────────────────────────────────────────────────────
def rrf_fuse(result_lists, k=60):
    rrf_scores = {}
    for results in result_lists:
        for rank, (idx, _) in enumerate(results):
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1.0 / (k + rank + 1)
    return sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)


# ── 6. 人工锚点（修复版：D选项证据区拆分更细） ─────────────────────
MANUAL_ANCHORS = {
    "stem": ["洗钱 金融机构 FI 后果 负面影响"],
    "answer_A": ["盈利业务减少 盈利业务损失 盈利业务流失"],
    "answer_E": ["调查费用 罚金 罚款 调查成本 罚款增加"],
    "distractor_B": ["代理银行设施增加 代理银行业务终止"],
    "distractor_C": ["雇员人数减少 裁员 合规人员"],
    "distractor_D": [
        # D1: 公司税/税收主体问题
        "公司税增加 税收 税务 政府税收缩水 逃税 避税",
        # D2: 税收损失核心段
        "税收损失 政府税收缩水 征税困难 收入损失 税率",
        # D3: 贸易洗钱中的避税行为
        "贸易洗钱 操纵贸易价格 避税活动 高开发票 低开发票",
        # D4a: 空壳公司（独立锚点）
        "空壳公司 壳公司 前台公司 降低所有权透明度",
        # D4b: 虚假发票（独立锚点）
        "虚假发票 假发票 伪造发票 双重发票 发票欺诈",
        # D4c: 税务欺诈/增值税链条（独立锚点）
        "税务欺诈 增值税 VAT链条 伪造买卖记录 逃税骗税",
        # D5: 黑市比索规避税收
        "黑市比索交易 规避税收 规避关税 国内税收 哥伦比亚",
    ],
}

# 教研四段证据（不变）
TEACHER_EVIDENCE = {
    "E1_税收损失": {
        "keywords": ["税收缩水", "政府税收", "税收损失", "征税变得更加困难", "税收缩水"],
        "description": "洗钱使政府税收缩水，征税变得困难"
    },
    "E2_贸易洗钱避税": {
        "keywords": ["贸易洗钱", "操纵贸易价格", "避税", "高开发票", "低开发票"],
        "description": "操纵贸易价格的做法表明存在洗钱、避税活动"
    },
    "E3_空壳虚假发票税务欺诈": {
        "keywords": ["空壳公司", "虚假发票", "税务欺诈", "增值税", "VAT", "伪造买卖记录"],
        "description": "空壳公司和虚假发票是常见手段；伪造买卖记录文件包括增值税链条"
    },
    "E4_黑市比索规避税收": {
        "keywords": ["黑市比索", "规避", "国内税收", "关税", "哥伦比亚进口商"],
        "description": "黑市比索交易规避从官方渠道购买美元的国内税收和关税"
    },
}

# ── 7. 两阶段检索：种子 → LLM扩展 → 精细检索 ──────────────────
STAGE2_EXPAND_PROMPT = """你是CAMS反洗钱教研专家。现在有一道CAMS考题，系统已经用题干和选项做了一轮粗检索，从教材中找出了以下候选概念：

---
{seed_concepts}
---

你的任务是基于这些**教材中实际存在的概念**，为每个选项生成扩展检索锚点。

要求：
1. 对照题目选项，判断种子概念中哪些与哪个选项相关（支持正确答案/反证干扰项/无关）
2. 对于干扰项D（如果有），基于种子概念中出现的相关内容，扩展更多检索方向
3. 锚点必须是种子概念中出现过的术语，或者是它们的近义词/上下位概念
4. 锚点用中文关键词/短语，空格分隔
5. 不要凭空编造教材中不存在的概念

输出JSON格式，不要markdown包裹：
{{
  "seed_analysis": "种子概念中哪些与题目相关、哪些无关",
  "missing_directions": "种子中缺少了哪些方向的证据",
  "expanded_anchors": {{
    "correct": ["扩展的正确答案锚点"],
    "distractor_B": ["扩展的B选项锚点"],
    "distractor_C": ["扩展的C选项锚点"],
    "distractor_D": ["扩展的D选项锚点1", "扩展的D选项锚点2", "扩展的D选项锚点3", "扩展的D选项锚点4", "扩展的D选项锚点5"]
  }}
}}"""


# ── 8. LLM 题目拆解（旧版，不会先看种子） ─────────────────────────
QUESTION_DECOMPOSE_PROMPT = """你是CAMS反洗钱教研专家。分析下面这道CAMS考试题，为证据检索生成检索锚点。

要求：
1. 先分析题目：题干在问什么、每个选项声称了什么、正确答案需要什么证据、错误选项需要什么反证
2. 然后生成检索锚点。锚点必须是中文关键词/短语，用空格分隔。
3. 锚点要覆盖：题干核心概念、正确答案的证据关键词、每个干扰项需要反证的关键词
4. 对每个干扰项，至少给出3组锚点（从不同角度检索反证材料）
5. 锚点要包含同义表达、上位概念、下位概念
6. 不要用现有解析，不要猜测答案

输出JSON格式，不要markdown包裹：
{
  "analysis": {
    "stem_question": "题干在问什么",
    "correct_claims": ["正确答案A声称什么", "正确答案E声称什么"],
    "distractor_claims": {"B": "声称什么", "C": "声称什么", "D": "声称什么"},
    "evidence_needed": "需要找什么类型的教材证据"
  },
  "anchors": {
    "stem": ["题干锚点"],
    "correct": ["正确答案锚点"],
    "distractor_B": ["B选项反证锚点1", "B选项反证锚点2"],
    "distractor_C": ["C选项反证锚点1", "C选项反证锚点2"],
    "distractor_D": ["D选项反证锚点1", "D选项反证锚点2", "D选项反证锚点3", "D选项反证锚点4", "D选项反证锚点5"]
  }
}"""


def llm_decompose_question(question):
    """用 DeepSeek v4-pro 分析题目并生成检索锚点"""
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    stem = question.get("stem", "")
    options = question.get("options", {})
    answer = question.get("answer", "")

    # 兼容 options 是 dict 或 list
    options_text = ""
    if isinstance(options, dict):
        for label, text in options.items():
            options_text += f"{label}. {text}\n"
    elif isinstance(options, list):
        for opt in options:
            if isinstance(opt, dict):
                options_text += f"{opt.get('label', opt.get('key', ''))}. {opt.get('text', opt.get('value', ''))}\n"
            else:
                options_text += f"{opt}\n"
    elif isinstance(options, str):
        options_text = options

    question_text = f"题干：{stem}\n选项：\n{options_text}\n正确答案：{answer}"

    print(f"调用 DeepSeek v4-pro 拆解题目...")
    resp = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": QUESTION_DECOMPOSE_PROMPT},
            {"role": "user", "content": question_text},
        ],
        temperature=0.1,
        max_tokens=2000,
    )

    raw = resp.choices[0].message.content.strip()
    # 清理 markdown 包裹
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        print(f"LLM 返回格式错误，尝试修复...")
        print(f"原始返回: {raw[:500]}...")
        # 尝试提取 JSON 块
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            result = json.loads(m.group())
        else:
            raise

    return result


# ── 8. 评估（增加最佳匹配追踪） ────────────────────────────────────
def evaluate_detailed(results, cards, all_bm25_results, all_emb_results, all_queries):
    """详细评估：整体覆盖 + 每证据最佳匹配排名"""
    top_n = results[:15]
    top_texts = []
    for idx, _ in top_n:
        top_texts.append(build_card_text(cards[idx]))
    combined = " ".join(top_texts)

    # 整体覆盖
    details = {}
    for ev_id, ev_info in TEACHER_EVIDENCE.items():
        hits = []
        for kw in ev_info["keywords"]:
            if kw in combined:
                hits.append(kw)
        details[ev_id] = {
            "recalled": len(hits) > 0,
            "hit_keywords": hits,
            "description": ev_info["description"],
        }

    # 最佳匹配排名追踪：在整个结果中找每证据的最佳排名
    all_ranked = results  # 已按 RRF 排序
    best_matches = {}
    for ev_id, ev_info in TEACHER_EVIDENCE.items():
        best_rank = None
        best_card = None
        for rank, (idx, score) in enumerate(all_ranked[:50]):  # 看 top-50
            text = build_card_text(cards[idx])
            for kw in ev_info["keywords"]:
                if kw in text:
                    if best_rank is None or rank < best_rank:
                        best_rank = rank + 1  # 1-indexed
                        best_card = cards[idx]["card_id"]
                        best_kw = kw
        best_matches[ev_id] = {
            "best_rank": best_rank,
            "best_card": best_card,
            "matched_keyword": best_kw if best_rank else None,
        }
        # 为 E3 单独追踪子关键词
        if ev_id == "E3_空壳虚假发票税务欺诈":
            sub_matches = {}
            sub_kw_groups = {
                "空壳公司": ["空壳公司", "壳公司"],
                "虚假发票": ["虚假发票", "假发票", "伪造发票"],
                "税务欺诈/VAT": ["税务欺诈", "增值税", "VAT"],
            }
            for sub_name, sub_kws in sub_kw_groups.items():
                for rank, (idx, _) in enumerate(all_ranked[:50]):
                    text = build_card_text(cards[idx])
                    for kw in sub_kws:
                        if kw in text:
                            sub_matches[sub_name] = {
                                "best_rank": rank + 1,
                                "best_card": cards[idx]["card_id"],
                                "matched_keyword": kw,
                            }
                            break
                    if sub_name in sub_matches:
                        break
                if sub_name not in sub_matches:
                    sub_matches[sub_name] = {"best_rank": None, "best_card": None, "matched_keyword": None}
            best_matches[ev_id]["sub_matches"] = sub_matches

    recalled_count = sum(1 for d in details.values() if d["recalled"])
    return details, recalled_count, best_matches


# ── 9. 两阶段检索主流程 ──────────────────────────────────────────
def stage1_seed_retrieval(cards, question):
    """第一阶段：多锚点多路召回，拼成多样化种子集"""
    bm25 = BM25Retriever(cards)
    emb = EmbeddingRetriever(cards)

    stem = question.get("stem", "")
    options = question.get("options", {})

    # 为每个选项构建独立 query
    queries = [stem]  # 题干
    if isinstance(options, dict):
        for label, text in options.items():
            queries.append(f"{label} {text}")
    elif isinstance(options, list):
        for opt in options:
            if isinstance(opt, dict):
                queries.append(f"{opt.get('label', '')} {opt.get('text', '')}")

    print(f"种子检索: {len(queries)} 个锚点, BM25+Embedding 双路召回 ...")

    # 第一阶段：收集所有命中，按 block 分组
    block_hits = {}  # block -> [(idx, score, card)]
    for qi, query in enumerate(queries):
        bm25_hits = bm25.search(query, top_k=15)
        emb_hits = emb.search(query, top_k=15)
        for idx, score in bm25_hits + emb_hits:
            card = cards[idx]
            block = card["card_id"].split("_")[1]
            if block not in block_hits:
                block_hits[block] = []
            block_hits[block].append((idx, score, card, query[:50]))

    # 第二阶段：跨 block 采样 — 每个 block 取 top-3，确保多样性
    seed_cards = []
    seen_ids = set()
    for block in sorted(block_hits.keys()):
        # 去重并取 top-3
        block_unique = []
        block_seen = set()
        for idx, score, card, query in sorted(block_hits[block], key=lambda x: x[1], reverse=True):
            if idx not in block_seen:
                block_seen.add(idx)
                block_unique.append((idx, score, card, query))
        for idx, score, card, query in block_unique[:3]:
            if idx not in seen_ids:
                seen_ids.add(idx)
                seed_cards.append({
                    "card_id": card["card_id"],
                    "knowledge": card["knowledge"],
                    "citation": card["citation"][:80],
                    "source_query": query,
                })

    # 如果还不够 40 个，用最高分补足
    if len(seed_cards) < 40:
        all_remaining = []
        for block in block_hits:
            for idx, score, card, query in block_hits[block]:
                if idx not in seen_ids:
                    all_remaining.append((idx, score, card, query))
        all_remaining.sort(key=lambda x: x[1], reverse=True)
        for idx, score, card, query in all_remaining:
            if len(seed_cards) >= 40:
                break
            seed_cards.append({
                "card_id": card["card_id"],
                "knowledge": card["knowledge"],
                "citation": card["citation"][:80],
                "source_query": query,
            })
    print(f"种子检索: 召回 {len(seed_cards)} 张独特卡片 (共 {len(queries)} 锚点)")

    # 统计种子覆盖的 block
    blocks = set(c["card_id"].split("_")[1] for c in seed_cards)
    print(f"种子覆盖 block: {sorted(blocks)}")

    return seed_cards


def stage2_llm_expand(question, seed_cards):
    """第二阶段：LLM 看着种子概念扩展锚点"""
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)

    # 构建种子概念列表
    concepts = []
    for sc in seed_cards:
        concepts.append(f"- [{sc['card_id']}] {sc['knowledge']}")
    seed_text = "\n".join(concepts)

    # 题目文本
    stem = question.get("stem", "")
    options = question.get("options", {})
    answer = question.get("answer", "")
    options_text = ""
    if isinstance(options, dict):
        for label, text in options.items():
            options_text += f"{label}. {text}\n"

    question_text = f"题干：{stem}\n选项：\n{options_text}\n正确答案：{answer}"

    prompt = STAGE2_EXPAND_PROMPT.format(seed_concepts=seed_text)

    print(f"调用 DeepSeek v4-pro (种子 {len(seed_cards)} 概念 → 扩展锚点)...")
    resp = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": question_text},
        ],
        temperature=0.1,
        max_tokens=2000,
    )

    raw = resp.choices[0].message.content.strip()
    # 保存原始返回用于调试
    with open(os.path.join(OUTPUT_DIR, "llm_raw_response.txt"), "w", encoding="utf-8") as f:
        f.write(raw)

    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    if not raw:
        print("LLM 返回空响应，回退使用人工锚点")
        return {"expanded_anchors": MANUAL_ANCHORS, "seed_analysis": "LLM返回空", "missing_directions": "未知"}

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        print(f"LLM 返回格式错误，原始内容已保存到 llm_raw_response.txt")
        print(f"原始返回前200字符: {raw[:200]}")
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            try:
                result = json.loads(m.group())
            except json.JSONDecodeError:
                print("JSON提取失败，回退使用人工锚点")
                return {"expanded_anchors": MANUAL_ANCHORS, "seed_analysis": raw[:200], "missing_directions": "JSON解析失败"}
        else:
            print("未找到JSON块，回退使用人工锚点")
            return {"expanded_anchors": MANUAL_ANCHORS, "seed_analysis": raw[:200], "missing_directions": "JSON解析失败"}

    return result


def two_stage_retrieval(cards, question):
    """两阶段检索：种子 → LLM扩展 → 精细检索"""
    print("\n" + "=" * 60)
    print("两阶段检索: 种子BM25 → LLM扩展锚点 → 混合检索")
    print("=" * 60)

    # Stage 1: 种子检索
    seed_cards = stage1_seed_retrieval(cards, question)

    # Stage 2: LLM 扩展
    llm_result = stage2_llm_expand(question, seed_cards)

    # 保存 LLM 输出
    with open(os.path.join(OUTPUT_DIR, "llm_expansion_result.json"), "w", encoding="utf-8") as f:
        json.dump({
            "seed_cards": seed_cards,
            "llm_output": llm_result,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n种子分析: {llm_result.get('seed_analysis', 'N/A')[:100]}...")
    print(f"缺失方向: {llm_result.get('missing_directions', 'N/A')[:100]}...")

    expanded_anchors = llm_result.get("expanded_anchors", {})
    if not expanded_anchors:
        print("LLM 未返回 expanded_anchors，回退使用人工锚点")
        expanded_anchors = MANUAL_ANCHORS

    # 合并原始种子锚点（题干+选项原文）和 LLM 扩展锚点
    # 构建题干/选项的原文锚点
    stem = question.get("stem", "")
    options = question.get("options", {})
    stem_anchor = {"stem": [stem]}
    option_anchors = {}
    if isinstance(options, dict):
        for label, text in options.items():
            option_anchors[f"option_{label}"] = [text]

    # 合并
    combined_anchors = {}
    combined_anchors.update(stem_anchor)
    combined_anchors.update(option_anchors)
    combined_anchors.update(expanded_anchors)

    # Stage 3: 精细检索
    result = run_retrieval(cards, combined_anchors, label="两阶段检索")
    result["seed_cards_count"] = len(seed_cards)
    result["llm_analysis"] = {
        "seed_analysis": llm_result.get("seed_analysis", ""),
        "missing_directions": llm_result.get("missing_directions", ""),
    }
    return result


# ── 10. 检索主流程（单阶段） ──────────────────────────────────────
def run_retrieval(cards, anchors, label="manual"):
    """运行一次完整的检索+评估"""
    bm25 = BM25Retriever(cards)
    emb = EmbeddingRetriever(cards)

    # 展开锚点
    all_queries = []
    if isinstance(anchors, dict):
        for category, items in anchors.items():
            if isinstance(items, list):
                all_queries.extend(items)
            else:
                all_queries.append(items)
    else:
        all_queries = list(anchors)

    total_anchors = len(all_queries)
    print(f"\n[{label}] 检索锚点: {total_anchors} 个")

    # 检索
    all_bm25_results = {}
    all_emb_results = {}
    for i, query in enumerate(all_queries):
        all_bm25_results[i] = bm25.search(query, top_k=20)
        all_emb_results[i] = emb.search(query, top_k=20)

    # 全局 RRF
    all_lists = []
    for i in range(total_anchors):
        all_lists.append(all_bm25_results[i])
        all_lists.append(all_emb_results[i])

    final_results = rrf_fuse(all_lists)
    top_n = final_results[:15]

    # 构建输出
    output_results = []
    for idx, score in top_n:
        card = cards[idx]
        retrieved_by = []
        for i, query in enumerate(all_queries):
            bm25_indices = {h[0] for h in all_bm25_results.get(i, [])[:20]}
            emb_indices = {h[0] for h in all_emb_results.get(i, [])[:20]}
            if idx in bm25_indices:
                retrieved_by.append(f"BM25-A{i}:{query[:50]}")
            if idx in emb_indices:
                retrieved_by.append(f"Emb-A{i}:{query[:50]}")
        output_results.append({
            "card_id": card["card_id"],
            "knowledge": card["knowledge"],
            "citation": card["citation"],
            "rrf_score": round(score, 6),
            "retrieved_by": retrieved_by[:5],
        })

    # 评估
    eval_details, recalled_count, best_matches = evaluate_detailed(
        final_results, cards, all_bm25_results, all_emb_results, all_queries)

    # 噪声
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

    return {
        "label": label,
        "total_anchors": total_anchors,
        "top_15": output_results,
        "evaluation": {
            "recalled": f"{recalled_count}/4",
            "passed": recalled_count >= 3,
            "details": eval_details,
            "best_matches": best_matches,
            "noise_in_top15": noise_count,
            "noise_acceptable": noise_count <= 7,
        },
        "recalled_count": recalled_count,
        "noise_count": noise_count,
    }


# ── 10. 打印结果 ──────────────────────────────────────────────────
def print_result(result):
    print(f"\n{'='*60}")
    print(f"结果: {result['label']} ({result['total_anchors']} 锚点)")
    print(f"{'='*60}")
    print(f"Top-15:")
    for i, r in enumerate(result["top_15"]):
        print(f"  [{i+1}] {r['card_id']} | {r['knowledge'][:70]}")

    print(f"\n--- 证据覆盖 ---")
    for ev_id, detail in result["evaluation"]["details"].items():
        status = "[OK]" if detail["recalled"] else "[MISS]"
        print(f"  {status} {ev_id}: {detail['description']}")
        if detail["recalled"]:
            print(f"       命中: {detail['hit_keywords']}")

    print(f"\n--- 最佳匹配排名 (越低越好) ---")
    for ev_id, bm in result["evaluation"]["best_matches"].items():
        rank_str = f"#{bm['best_rank']}" if bm['best_rank'] else "未命中"
        print(f"  {ev_id}: {rank_str} | {bm['best_card']} ({bm['matched_keyword']})")
        if "sub_matches" in bm:
            for sub_name, sm in bm["sub_matches"].items():
                r_str = f"#{sm['best_rank']}" if sm['best_rank'] else "未命中"
                print(f"    -> {sub_name}: {r_str} | {sm['best_card']}")

    print(f"\n召回: {result['evaluation']['recalled']} {'[PASS]' if result['evaluation']['passed'] else '[FAIL]'}")
    print(f"噪声: {result['noise_count']}/15 {'[OK]' if result['evaluation']['noise_acceptable'] else '[TOO MUCH]'}")


# ── 11. 主入口 ─────────────────────────────────────────────────────
def main():
    mode = "manual"
    if "--llm" in sys.argv:
        mode = "llm"
    elif "--both" in sys.argv:
        mode = "both"
    elif "--two-stage" in sys.argv:
        mode = "two_stage"

    # 过滤 citation < 20 字的索引卡片
    cards = load_cards(min_citation_len=20)

    question = load_question("2.1_19")
    if not question:
        print("未找到题目 2.1_19")
        return

    if mode == "two_stage":
        result = two_stage_retrieval(cards, question)
        print_result(result)
        with open(os.path.join(OUTPUT_DIR, "retrieval_two_stage.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    if mode in ("manual", "both"):
        result_manual = run_retrieval(cards, MANUAL_ANCHORS, label="人工锚点")
        print_result(result_manual)
        with open(os.path.join(OUTPUT_DIR, "retrieval_manual.json"), "w", encoding="utf-8") as f:
            json.dump(result_manual, f, ensure_ascii=False, indent=2)

    if mode in ("llm", "both"):
        print("\n" + "=" * 60)
        print("LLM 拆解题目...")
        llm_result_raw = llm_decompose_question(question)

        # 保存 LLM 分析
        with open(os.path.join(OUTPUT_DIR, "llm_decomposition.json"), "w", encoding="utf-8") as f:
            json.dump(llm_result_raw, f, ensure_ascii=False, indent=2)

        print(f"题目分析: {llm_result_raw.get('analysis', {}).get('stem_question', 'N/A')[:80]}...")

        llm_anchors = llm_result_raw.get("anchors", {})
        result_llm = run_retrieval(cards, llm_anchors, label="LLM锚点")
        print_result(result_llm)

        with open(os.path.join(OUTPUT_DIR, "retrieval_llm.json"), "w", encoding="utf-8") as f:
            json.dump(result_llm, f, ensure_ascii=False, indent=2)

    if mode == "both":
        print("\n" + "=" * 60)
        print("对比: 人工锚点 vs LLM锚点")
        print(f"  人工: 召回={result_manual['evaluation']['recalled']}, 噪声={result_manual['noise_count']}")
        print(f"  LLM: 召回={result_llm['evaluation']['recalled']}, 噪声={result_llm['noise_count']}")


if __name__ == "__main__":
    main()
