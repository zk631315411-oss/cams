"""
验证泛化能力：用 2.1_4（处置阶段，教材直给型）测试图谱
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
with open(os.path.join(OUT_DIR, "edges.json"), "r", encoding="utf-8") as f:
    edges = json.load(f)
with open(os.path.join(OUT_DIR, "card_section_map.json"), "r", encoding="utf-8") as f:
    cs_map = json.load(f)
with open(os.path.join(DATA_DIR, "cards_ch2.json"), "r", encoding="utf-8") as f:
    cards = json.load(f)

card_knowledge = {c["card_id"]: c.get("knowledge", "") for c in cards}
section_to_cards = cs_map["section_to_cards"]
card_to_section = cs_map["card_to_section"]

from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)

# ── 2.1_4: 处置阶段 ──────────────────────────────────────────────
print("=" * 60)
print("Test: 2.1_4 — 处置阶段（教材直给型）")
print("=" * 60)
print("Stem: 哪一种方法最容易被洗钱者用来完成'处置'阶段?")
print("Answer: A (将洗钱者的银行账户存入现金)")

options = {
    "A": "将洗钱者的银行账户存入现金",
    "B": "在不同金融机构账户之间做大量转账交易",
    "C": "从洗钱者的银行账户中支取大额现金",
    "D": "向洗钱者的账户签发支票和汇票"
}
correct = "A"

section_titles = [s.get("subsection_title", "") for s in sections]
section_defs = [s.get("definition", "") for s in sections]
queries = [f"{t} {d}" for t, d in zip(section_titles, section_defs)]
query_vecs = model.encode(queries, normalize_embeddings=True)

opt_texts = list(options.values())
opt_vecs = model.encode(opt_texts, normalize_embeddings=True)
scores_matrix = opt_vecs @ query_vecs.T

# Print mapping for each option
for idx, (label, text) in enumerate(options.items()):
    row = scores_matrix[idx]
    top_idx = list(reversed(row.argsort()))[:3]
    print(f"\n{label}. '{text}':")
    for rank, i in enumerate(top_idx):
        marker = " <- TARGET" if ("洗钱" in section_titles[i] and "阶段" in section_titles[i]) else ""
        print(f"  {rank+1}. [{row[i]:.4f}] {section_titles[i]}{marker}")
        print(f"     def: {section_defs[i][:80]}")

# Check: does the correct answer (A) match 洗钱的三个阶段?
a_scores = scores_matrix[0]  # A is index 0
a_top3_idx = list(reversed(a_scores.argsort()))[:3]
a_hit_stages = any("洗钱" in section_titles[i] and "阶段" in section_titles[i] for i in a_top3_idx)
print(f"\nA -> 洗钱的三个阶段 in top-3: {a_hit_stages}")

# Check: does 洗钱的三个阶段 have card evidence?
stages_title = None
for s in sections:
    if "洗钱" in s.get("subsection_title","") and "阶段" in s.get("subsection_title",""):
        stages_title = s["subsection_title"]
        break

if stages_title:
    stage_cards = section_to_cards.get(stages_title, [])
    print(f"'{stages_title}' mounted cards: {stage_cards[:5]}")
    for cid in stage_cards[:3]:
        know = card_knowledge.get(cid, "")[:120]
        print(f"  {cid}: {know}")

# ── Generate reasoning chain ──────────────────────────────────────
evidence_lines = []
evidence_lines.append(f"A选项匹配到: {stages_title}")
for cid in section_to_cards.get(stages_title, [])[:3]:
    know = card_knowledge.get(cid, "")[:150]
    evidence_lines.append(f"  {cid}: {know}")

from openai import OpenAI
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

prompt = f"""你是CAMS教研专家。请为下面这道题生成推理链。

题目：下列哪一种方法最容易被洗钱者用来完成"处置"阶段？
A. 将现金存入银行账户
B. 在不同金融机构账户之间做大量转账交易
C. 从银行账户中支取大额现金
D. 向账户签发支票和汇票
正确答案：A

【图谱匹配结果】
{chr(10).join(evidence_lines)}

请写一句话推理链，说明为什么A正确，引用card_id。不超过80字。"""

resp = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.2, max_tokens=200)

chain = resp.choices[0].message.content.strip()
print(f"\nReasoning chain: {chain}")

# Check: does chain include card_id and mention 处置/现金/存入?
has_card = any(cid in chain for cid in ["v6_b", "N0"])
has_placement = any(w in chain for w in ["处置", "现金", "存入", "存放"])
print(f"\nHas card_id: {has_card}, Has placement logic: {has_placement}")
print(f"PASS: {a_hit_stages and has_card and has_placement}")
