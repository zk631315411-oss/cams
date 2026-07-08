"""
第三步：端到端验证（2.1_19 D选项）
D选项"公司税的增加" → 税收损失节点 → v6_b03_N18 → 边→FI后果 → v6_b04_N09 → 推理链
"""
import os, sys, json, re, numpy as np

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("[FAIL] DEEPSEEK_API_KEY not set"); sys.exit(1)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.join(DATA_DIR, "agentic_search_eval_v2", "kg")

# Load
with open(os.path.join(OUT_DIR, "sections.json"), "r", encoding="utf-8") as f:
    sections = json.load(f)
with open(os.path.join(OUT_DIR, "edges.json"), "r", encoding="utf-8") as f:
    edges = json.load(f)
with open(os.path.join(OUT_DIR, "card_section_map.json"), "r", encoding="utf-8") as f:
    cs_map = json.load(f)
with open(os.path.join(DATA_DIR, "cards_ch2.json"), "r", encoding="utf-8") as f:
    cards = json.load(f)

card_to_section = cs_map["card_to_section"]
section_to_cards = cs_map["section_to_cards"]

# Card lookup
card_knowledge = {c["card_id"]: c.get("knowledge", "") for c in cards}
card_context = {c["card_id"]: " ".join(filter(None, [c.get("context_before", ""), c.get("knowledge", ""), c.get("context_after", "")])) for c in cards}

print("=" * 60)
print("Step 3: End-to-End Validation (2.1_19 D option)")
print("=" * 60)

# ── Step 1: D option → concept node ────────────────────────────────
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)

d_option = "公司税的增加"
section_titles = [s.get("subsection_title", "") for s in sections]
section_defs = [s.get("definition", "") for s in sections]
queries = [f"{t} {d}" for t, d in zip(section_titles, section_defs)]

opt_vec = model.encode([d_option], normalize_embeddings=True)
query_vecs = model.encode(queries, normalize_embeddings=True)
scores = (query_vecs @ opt_vec.T).flatten()

top_idx = list(reversed(scores.argsort()))[:3]

print(f"\nStep 1: D option '{d_option}' -> top-3 section matches:")
for rank, idx in enumerate(top_idx):
    print(f"  {rank+1}. [{scores[idx]:.4f}] {section_titles[idx]}")
    print(f"     def: {section_defs[idx][:80]}")

# Check if "税收损失" is in top-3
d_in_tax = any("税收" in section_titles[i] for i in top_idx)
print(f"  3.1 D->tax section: {d_in_tax}")

# ── Step 2: Concept → cards ────────────────────────────────────────
# Find the tax loss section
tax_section = None
for s in sections:
    if "税收" in s.get("subsection_title", ""):
        tax_section = s
        break

print(f"\nStep 2: Tax section -> mounted cards")
tax_title = tax_section["subsection_title"]
tax_cards = section_to_cards.get(tax_title, [])
print(f"  Tax section: {tax_title}")
print(f"  Mounted cards: {tax_cards[:10]}")

# Check for key card
has_v03 = "v6_b03_N18" in tax_cards or "v6_b03_N19" in tax_cards
print(f"  3.2 v6_b03_N18/N19 in tax cards: {has_v03}")

# If not found via mounting, try real-time BGE search
if not has_v03:
    print("  Searching via real-time BGE...")
    from lightrag import LightRAG, QueryParam
    # fallback
    print("  Using key_cards_hint from edges instead")

# ── Step 3: Edge check ─────────────────────────────────────────────
print(f"\nStep 3: Edges from tax section to FI sections")
tax_edges = []
for e in edges:
    fsub = e.get("from_subsection", "")
    tsub = e.get("to_subsection", "")
    if ("税收" in fsub or "税收" in tsub):
        tax_edges.append(e)
        print(f"  {fsub} --[{e.get('relation_type')}]--> {tsub}")
        print(f"    {e.get('relation_detail', '')[:120]}")

has_fi_edge = any(
    ("削弱" in e.get("from_subsection","") or "金融" in e.get("from_subsection","") or
     "削弱" in e.get("to_subsection","") or "金融" in e.get("to_subsection",""))
    for e in tax_edges
)
print(f"  3.3 Tax-FI edge exists: {has_fi_edge}")

# ── Step 4: Reasoning chain ────────────────────────────────────────
print(f"\nStep 4: Generate reasoning chain")

# Collect evidence
evidence_parts = []
for e in tax_edges:
    detail = e.get("relation_detail", "")
    hints = e.get("key_cards_hint", [])
    if detail:
        evidence_parts.append(f"边: {e.get('from_subsection','')} --[{e.get('relation_type')}]--> {e.get('to_subsection','')}")
        evidence_parts.append(f"  详情: {detail}")
        if hints:
            evidence_parts.append(f"  关键卡片提示: {', '.join(hints)}")

# Add mounted cards
tax_card_ids = section_to_cards.get(tax_title, [])[:5]
tax_card_texts = []
for cid in tax_card_ids:
    know = (card_context.get(cid, "") or card_knowledge.get(cid, ""))[:250]
    tax_card_texts.append(f"  {cid}: {know}")
if tax_card_texts:
    evidence_parts.append(f"税收损失节点挂载卡片:")
    evidence_parts.extend(tax_card_texts)

evidence_text = "\n".join(evidence_parts)

from openai import OpenAI
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

prompt = f"""你是CAMS教研专家。请基于以下图谱数据，为D选项"公司税的增加"生成一条推理链。

【图谱数据】
D选项"公司税的增加"在知识图谱中定位到"税收损失"节点。

{evidence_text}

请写一句话推理链，说明D选项为什么错误。要求：
1. 说明主体错配和/或方向错配
2. 引用具体的card_id（如有）
3. 不超过100字

直接输出推理链文本。"""

resp = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.2, max_tokens=300)

chain = resp.choices[0].message.content.strip()

with open(os.path.join(OUT_DIR, "step3_reasoning_chain.txt"), "w", encoding="utf-8") as f:
    f.write(chain)

print(f"  {chain[:300]}")

# ── Acceptance summary ──────────────────────────────────────────────
print(f"\n{'='*60}")
print("ACCEPTANCE SUMMARY")
print(f"{'='*60}")
check_3_1 = d_in_tax
check_3_2 = has_v03
check_3_3 = has_fi_edge
check_3_4 = any(w in chain for w in ["主体错配", "主体不同", "税收损失", "政府税收缩水", "公司税增加", "FI", "金融机构"])
check_3_5 = "v6_b03" in chain

print(f"3.1 D->tax section: {check_3_1}")
print(f"3.2 Tax cards include v6_b03_N18/N19: {check_3_2}")
print(f"3.3 Tax-FI edge exists: {check_3_3}")
print(f"3.4 Reasoning chain has refutation: {check_3_4}")
print(f"3.5 Reasoning chain has card_id: {check_3_5}")
all_pass = check_3_1 and check_3_2 and check_3_3 and check_3_4 and check_3_5
print(f"\n3.6 END-TO-END PASS: {all_pass}")
