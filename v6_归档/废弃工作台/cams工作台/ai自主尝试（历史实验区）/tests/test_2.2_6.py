"""
干净测试：2.2_6 PEP风险重分类
只给LLM：题目+答案+图谱匹配结果（节点名+卡片ID）
不给：教研解析、概念解释、推理提示
"""
import os, sys, json, numpy as np

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("[FAIL] DEEPSEEK_API_KEY not set"); sys.exit(1)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.join(DATA_DIR, "agentic_search_eval_v2", "kg")

# Load graph
with open(os.path.join(OUT_DIR, "sections.json"), "r", encoding="utf-8") as f:
    sections = json.load(f)
with open(os.path.join(OUT_DIR, "edges.json"), "r", encoding="utf-8") as f:
    edges = json.load(f)
with open(os.path.join(OUT_DIR, "card_section_map.json"), "r", encoding="utf-8") as f:
    cs_map = json.load(f)
with open(os.path.join(DATA_DIR, "cards_ch2.json"), "r", encoding="utf-8") as f:
    cards = json.load(f)

card_knowledge = {c["card_id"]: c.get("knowledge", "") for c in cards}
card_context = {c["card_id"]: " ".join(filter(None, [c.get("context_before", ""), c.get("knowledge", ""), c.get("context_after", "")])) for c in cards}
section_to_cards = cs_map["section_to_cards"]

from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)

# ── Question ────────────────────────────────────────────────────
stem = "在对一个中等风险客户进行审查时，分析员注意到一个新增加的授权签字人是一个外国政治公众人物（PEP）。该分析员下一步应该采取什么措施?"
options = {
    "A": "审查实际所有权，最终确定客户的风险类别",
    "B": "取消PEP作为授权签字人的身份",
    "C": "将客户重新归类为高风险",
    "D": "将授权的PEP签字人归类为高风险"
}
answer = "C"

print("=" * 60)
print("Test: 2.2_6 — PEP风险重分类")
print("=" * 60)
print(f"Stem: {stem[:80]}...")
print(f"Answer: {answer}")

# ── Step 0: Alias-aware concept extraction from stem ────────────
# First, check if stem/options contain known aliases or section titles
alias_to_section = {}
section_titles = [s.get("subsection_title", "") for s in sections]
for s in sections:
    title = s.get("subsection_title", "")
    for alias in s.get("aliases", []):
        alias_to_section[alias.lower()] = title
    # Also map the section title itself
    alias_to_section[title.lower()] = title

# Check stem for known aliases
stem_matched_sections = set()
for alias, section_title in alias_to_section.items():
    if alias.lower() in stem.lower():
        stem_matched_sections.add(section_title)
        print(f'  Stem alias match: \"{alias}\" -> {section_title}')

# ── BGE match each option to graph nodes ────────────────────────
# Use stem-matched sections to boost or directly target
section_defs = [s.get("definition", "") for s in sections]
queries = [f"{t} {d} {(' '.join(s.get('aliases', [])))}" for s, t, d in zip(sections, section_titles, section_defs)]
query_vecs = model.encode(queries, normalize_embeddings=True)

opt_texts = list(options.values())
opt_vecs = model.encode(opt_texts, normalize_embeddings=True)
scores_matrix = opt_vecs @ query_vecs.T

# ── Strategy: use stem-matched sections to get evidence cards ──
# For each stem-matched section, get mounted cards and build evidence
graph_context = []
if stem_matched_sections:
    graph_context.append(f"题干关键概念定位到以下图谱节点:")
    for sec_title in stem_matched_sections:
        cards = section_to_cards.get(sec_title, [])[:5]
        card_info = []
        for cid in cards:
            know = (card_context.get(cid, "") or card_knowledge.get(cid, ""))[:300]
            card_info.append(f"    {cid}: {know}")
        graph_context.append(f"  [{sec_title}]")
        graph_context.extend(card_info)
else:
    # Fallback: option-level matching
    for idx, (label, text) in enumerate(options.items()):
        row = scores_matrix[idx]
        top_idx = int(np.argmax(row))
        top_section = section_titles[top_idx]
        top_cards = section_to_cards.get(top_section, [])[:3]
        card_ids_str = ", ".join(top_cards) if top_cards else "(无挂载卡片)"
        graph_context.append(f"{label}. '{text}' --> [{top_section}] cards: {card_ids_str}")
        print(f"  {label} -> {top_section} ({float(row[top_idx]):.3f})")

# ── Also check edges involving matched sections ─────────────────
matched_sections = set()
for idx in range(4):
    top_idx = int(np.argmax(scores_matrix[idx]))
    matched_sections.add(section_titles[top_idx])

edge_lines = []
for e in edges:
    fsub = e.get("from_subsection", "")
    tsub = e.get("to_subsection", "")
    if fsub in matched_sections or tsub in matched_sections:
        edge_lines.append(f"  {fsub} --[{e.get('relation_type')}]--> {tsub}")
        edge_lines.append(f"    {e.get('relation_detail', '')[:100]}")

# ── Call LLM: only question + graph data, no teacher hints ──────
from openai import OpenAI
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

prompt = f"""请基于以下知识图谱匹配结果，为一道CAMS考题生成推理链。

【题目】
{stem}
A. {options['A']}
B. {options['B']}
C. {options['C']}
D. {options['D']}
正确答案：{answer}

【图谱匹配结果】
{chr(10).join(graph_context)}

【图谱中的关联边】
{chr(10).join(edge_lines) if edge_lines else '(未找到匹配节点间的关联边)'}

请写一句推理链说明为什么正确答案是{answer}。引用具体的card_id。不超过80字。"""

resp = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.2, max_tokens=200)

chain = resp.choices[0].message.content.strip()

# Save
with open(os.path.join(OUT_DIR, "test_2.2_6_chain.txt"), "w", encoding="utf-8") as f:
    f.write(f"Prompt:\n{prompt}\n\n---\nChain:\n{chain}")

print(f"\n  LLM推理链: {chain}")

# Compare with teacher
with open(os.path.join(OUT_DIR, "q_2.2_6.txt"), "r", encoding="utf-8") as f:
    teacher = f.read()
# Extract key line from teacher
import re
teacher_why = re.findall(r'C选项正确[，,](.*?)(?:。|$)', teacher)
if teacher_why:
    print(f"\n  教研解析: {teacher_why[0][:120]}")

# Quick check
has_card = any(cid in chain for cid in ["v6_b", "N0"])
has_pep = "PEP" in chain or "政治公众" in chain or "高风险" in chain
print(f"\n  Has card_id: {has_card}, Has PEP/高风险: {has_pep}")
print(f"  PASS: {has_card and has_pep}")
