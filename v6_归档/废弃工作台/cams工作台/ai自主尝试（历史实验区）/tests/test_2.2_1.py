"""
测试 2.2_1 — 代理银行尽职调查（多选题，规则应用型）
策略：题干别名定位节点 → 拿卡片证据 → LLM 判断选项
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
card_context = {c["card_id"]: " ".join(filter(None, [c.get("context_before", ""), c.get("knowledge", ""), c.get("context_after", "")])) for c in cards}
section_to_cards = cs_map["section_to_cards"]

# ── Question ────────────────────────────────────────────────────
stem = "当代理银行客户不受其母公司控制时，哪些实体需要做尽职调查?（选择两个）"
options = {
    "A": "代理银行客户的母公司",
    "B": "代理银行客户的客户",
    "C": "具有较高风险特征的实体",
    "D": "向代理行提供服务的第三方",
    "E": "代理银行客户本身"
}
answer = "A,E"

print("=" * 60)
print("Test: 2.2_1 — 代理银行尽职调查")
print("=" * 60)

# ── Step 1: Alias-aware stem concept extraction ─────────────────
alias_to_section = {}
section_titles = [s.get("subsection_title", "") for s in sections]
for s in sections:
    title = s.get("subsection_title", "")
    for alias in s.get("aliases", []):
        alias_to_section[alias.lower()] = title
    alias_to_section[title.lower()] = title

stem_matched = set()
for alias, section_title in alias_to_section.items():
    if alias.lower() in stem.lower():
        stem_matched.add(section_title)
        print(f"  Stem alias: '{alias}' -> {section_title}")

# Also try BGE match for stem to catch concepts not covered by aliases
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)

section_defs = [s.get("definition", "") for s in sections]
queries = [(f"{t} {d} {' '.join(s.get('aliases', []))}") for s, t, d in zip(sections, section_titles, section_defs)]
query_vecs = model.encode(queries, normalize_embeddings=True)

stem_vec = model.encode([stem], normalize_embeddings=True)
stem_scores = (stem_vec @ query_vecs.T).flatten()
stem_top5 = list(reversed(stem_scores.argsort()))[:5]
print(f"  Stem BGE top-5:")
for idx in stem_top5:
    score = float(stem_scores[idx])
    if score > 0.5:
        stem_matched.add(section_titles[idx])
    print(f"    [{score:.3f}] {section_titles[idx]}")

# ── Step 2: Get evidence cards from matched sections (sorted by BGE score) ──
graph_context = []
# Sort matched sections by BGE score
stem_matched_sorted = sorted(stem_matched, key=lambda t: float(stem_scores[section_titles.index(t)]), reverse=True)

if stem_matched_sorted:
    graph_context.append("题干定位到的图谱节点及挂载卡片（按相关度排序）：")
    for sec_title in stem_matched_sorted[:3]:
        cards_ids = section_to_cards.get(sec_title, [])[:15]
        score = float(stem_scores[section_titles.index(sec_title)])
        graph_context.append(f"  [{sec_title}] (score={score:.3f})")
        for cid in cards_ids:
            know = (card_context.get(cid, "") or card_knowledge.get(cid, ""))[:300]
            graph_context.append(f"    {cid}: {know}")
    print(f"  Evidence sections: {stem_matched_sorted[:3]}")
    print(f"  Total cards fed to LLM: {sum(len(section_to_cards.get(t, [])[:15]) for t in stem_matched_sorted[:3])}")
else:
    print("  WARNING: No stem-matched sections")
    # fallback: try option-level matching...

# Also find relevant edges
edge_lines = []
for e in edges:
    fsub = e.get("from_subsection", "")
    tsub = e.get("to_subsection", "")
    if fsub in stem_matched or tsub in stem_matched:
        edge_lines.append(f"  {fsub} --[{e.get('relation_type')}]--> {tsub}: {e.get('relation_detail', '')[:80]}")

# ── Step 3: LLM generates reasoning ─────────────────────────────
from openai import OpenAI
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

prompt = f"""请基于以下知识图谱证据，为一道CAMS多选题生成推理链。

【题目】
{stem}
A. {options['A']}
B. {options['B']}
C. {options['C']}
D. {options['D']}
E. {options['E']}
正确答案：{answer}

【图谱证据】
{chr(10).join(graph_context)}

【关联边】
{chr(10).join(edge_lines) if edge_lines else '(无)'}

请写推理链：说明为什么{answer}正确，并引用具体card_id。不超过120字。"""

resp = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.2, max_tokens=300)

chain = resp.choices[0].message.content.strip()

with open(os.path.join(OUT_DIR, "test_2.2_1_chain.txt"), "w", encoding="utf-8") as f:
    f.write(f"Prompt:\n{prompt}\n\n---\nChain:\n{chain}")

print(f"\n  LLM推理链: {chain[:300]}")

# Compare with teacher
with open(os.path.join(OUT_DIR, "q_2.2_1.txt"), "r", encoding="utf-8") as f:
    teacher = f.read()
import re
teacher_why = re.findall(r'[AE]选项正确[，,](.*?)(?:。|$)', teacher)
print(f"\n  教研核心: {teacher_why[:2] if teacher_why else 'N/A'}")

has_card = any(cid in chain for cid in ["v6_b", "N0"])
has_correct = "母公司" in chain and "客户本身" in chain
print(f"\n  Has card_id: {has_card}, Has correct entities: {has_correct}")
print(f"  PASS: {has_card and has_correct}")
