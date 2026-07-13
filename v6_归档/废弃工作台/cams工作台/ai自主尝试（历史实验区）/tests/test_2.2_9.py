"""
测试 2.2_9 — 巢状交易（概念定义型）
"""
import os, sys, json, numpy as np

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("[FAIL] DEEPSEEK_API_KEY not set"); sys.exit(1)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.join(DATA_DIR, "agentic_search_eval_v2", "kg")

with open(os.path.join(OUT_DIR, "sections.json"), "r", encoding="utf-8") as f:
    sections = json.load(f)
with open(os.path.join(OUT_DIR, "card_section_map.json"), "r", encoding="utf-8") as f:
    cs_map = json.load(f)
with open(os.path.join(DATA_DIR, "cards_ch2.json"), "r", encoding="utf-8") as f:
    cards = json.load(f)

card_knowledge = {c["card_id"]: c.get("knowledge", "") for c in cards}
card_context = {c["card_id"]: " ".join(filter(None, [c.get("context_before", ""), c.get("knowledge", ""), c.get("context_after", "")])) for c in cards}
section_to_cards = cs_map["section_to_cards"]

stem = "什么是巢状交易？"
options = {
    "A": "对应银行向其他金融机构提供上游通汇服务",
    "B": "对应银行向其他金融机构提供下游通汇服务",
    "C": "银行与其他当地银行共有许多客户",
    "D": "客户在多家当地银行开有帐户"
}
answer = "B"

print("=" * 60)
print("Test: 2.2_9 — 巢状交易")
print("=" * 60)

# ── Alias match + BGE ──────────────────────────────────────────
alias_to_section = {}
section_titles = [s.get("subsection_title", "") for s in sections]
for s in sections:
    for alias in s.get("aliases", []):
        alias_to_section[alias.lower()] = s["subsection_title"]
    alias_to_section[s["subsection_title"].lower()] = s["subsection_title"]

from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)

section_defs = [s.get("definition", "") for s in sections]
queries = [(f"{t} {d} {' '.join(s.get('aliases', []))}") for s, t, d in zip(sections, section_titles, section_defs)]
query_vecs = model.encode(queries, normalize_embeddings=True)

stem_vec = model.encode([stem], normalize_embeddings=True)
stem_scores = (stem_vec @ query_vecs.T).flatten()
stem_top5 = list(reversed(stem_scores.argsort()))[:5]

stem_matched = set()
for idx in stem_top5:
    score = float(stem_scores[idx])
    if score > 0.5:
        stem_matched.add(section_titles[idx])
    print(f"  [{score:.3f}] {section_titles[idx]}")

# ── Evidence ───────────────────────────────────────────────────
stem_matched_sorted = sorted(stem_matched, key=lambda t: float(stem_scores[section_titles.index(t)]), reverse=True)

graph_context = []
if stem_matched_sorted:
    graph_context.append("题干定位到的图谱节点及挂载卡片：")
    for sec_title in stem_matched_sorted[:3]:
        cards_ids = section_to_cards.get(sec_title, [])[:15]
        score = float(stem_scores[section_titles.index(sec_title)])
        graph_context.append(f"  [{sec_title}] (score={score:.3f})")
        for cid in cards_ids:
            know = (card_context.get(cid, "") or card_knowledge.get(cid, ""))[:300]
            graph_context.append(f"    {cid}: {know}")

# ── LLM ────────────────────────────────────────────────────────
from openai import OpenAI
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

prompt = f"""请基于以下知识图谱证据，为一道CAMS考题生成推理链。

【题目】
{stem}
A. {options['A']}
B. {options['B']}
C. {options['C']}
D. {options['D']}
正确答案：{answer}

【图谱证据】
{chr(10).join(graph_context)}

请写推理链：说明为什么{answer}正确，引用具体card_id。不超过80字。"""

resp = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.2, max_tokens=200)

chain = resp.choices[0].message.content.strip()

with open(os.path.join(OUT_DIR, "test_2.2_9_chain.txt"), "w", encoding="utf-8") as f:
    f.write(f"Prompt:\n{prompt}\n\n---\nChain:\n{chain}")

print(f"\n  LLM: {chain[:300]}")

has_card = any(cid in chain for cid in ["v6_b", "N0"])
has_nesting = "巢" in chain or "下游" in chain or "嵌套" in chain
print(f"\n  Has card_id: {has_card}, Has nesting logic: {has_nesting}")
print(f"  PASS: {has_card and has_nesting}")
