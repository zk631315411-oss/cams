"""
第一步：LLM 读教材全文，标注跨节关系（边）+ 补 definition
节点 = 教材目录小节，LLM 不造节点，只标边和写 definition
"""
import os, sys, json, re

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("[FAIL] DEEPSEEK_API_KEY not set"); sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
MODEL = "deepseek-v4-pro"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.join(DATA_DIR, "agentic_search_eval_v2", "kg")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load inputs ────────────────────────────────────────────────────
with open(os.path.join(DATA_DIR, "agentic_search_eval_v2", "ch2_full_text.txt"), "r", encoding="utf-8") as f:
    textbook = f.read()

with open(os.path.join(DATA_DIR, "agentic_search_eval_v2", "toc_ch2_compact.txt"), "r", encoding="utf-8") as f:
    toc = f.read()

print(f"Textbook: {len(textbook)} chars (~{len(textbook)//3} tokens)")
print(f"TOC: {len(toc)} chars")

# ── Prompt ─────────────────────────────────────────────────────────
prompt = f"""你是CAMS教材的教学设计专家。以下是教材第2章的目录和完整原文。

【教材目录】
{toc}

【教材全文】
{textbook}

你的任务：

一、为每个小节写一句 definition（从教材原文概括，不超过30字）。

二、找出小节之间存在有意义的关联。关联必须是客观的教材层面的关系。

优先级从高到低：
1. 平级关系（最优先）：同一节/不同节的两个小节，讨论同一现象但角度不同。
   - 主体不同：同一现象对不同主体（如"税收损失"讨论政府、"削弱金融组织"讨论FI）
   - 方向相反：对同一件事结论方向相反（如某处说"增加"另一处说"减少/终止"）
   - 互为因果/互为前提
2. 跨节关联：不同节的小节之间存在机制上的联系。
3. 层级关系（最低优先级）：一个小节是另一个小节的下位概念。这种关系目录已经体现，不需要大量标注。只标注有教学意义的——如"声誉风险"是"洗钱的社会成本"的一种。

注意：
- 目录已经体现了层级结构，不要把精力花在标注层级关系上
- 重点挖掘：哪些小节讨论的其实是同一件事但换了个角度？哪些小节的结论和另一个小节相反？
- 只标注教材中确实存在的关系，不臆造
- 标注的是"两个知识点之间的客观关系"，不是"学生会不会搞混"

输出JSON（不要markdown包裹）：
{{
  "sections": [
    {{
      "section_id": "2.1",
      "subsection_title": "小节标题",
      "definition": "一句话概括"
    }}
  ],
  "edges": [
    {{
      "from_section": "2.1",
      "from_subsection": "税收损失",
      "to_section": "2.1",
      "to_subsection": "削弱金融组织",
      "relation_type": "主体不同",
      "relation_detail": "税收损失的主体是政府（政府税收缩水），FI后果的主体是金融机构（盈利业务流失等），两者都涉及洗钱的经济影响但承受主体不同",
      "key_cards_hint": ["税收缩水", "盈利业务流失", "代理银行业务终止"]
    }}
  ]
}}"""

# ── Call LLM ────────────────────────────────────────────────────────
print("\nCalling LLM...")
resp = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.05,
    max_tokens=8000)

raw = resp.choices[0].message.content.strip()

# Save raw response for audit
with open(os.path.join(OUT_DIR, "step1_raw_response.txt"), "w", encoding="utf-8") as f:
    f.write(raw)
print(f"Raw response: {len(raw)} chars")

# Parse JSON
raw_clean = re.sub(r"^```(?:json)?\s*", "", raw)
raw_clean = re.sub(r"\s*```$", "", raw_clean)
try:
    result = json.loads(raw_clean)
except json.JSONDecodeError:
    import json_repair
    result = json.loads(json_repair.repair_json(raw_clean))

sections = result.get("sections", [])
edges = result.get("edges", [])

print(f"\nSections: {len(sections)}")
for s in sections[:5]:
    clean = s.get('subsection_title', '')[:30].encode('gbk', errors='replace').decode('gbk')
    print(f"  {s.get('section_id', '?')} {clean}: {s.get('definition', '')[:60]}")

print(f"\nEdges: {len(edges)}")
for e in edges[:10]:
    fsub = e.get('from_subsection', '')[:20]
    tsub = e.get('to_subsection', '')[:20]
    rtype = e.get('relation_type', '?')
    print(f"  {fsub} --[{rtype}]--> {tsub}")

# ── Save ────────────────────────────────────────────────────────────
with open(os.path.join(OUT_DIR, "sections.json"), "w", encoding="utf-8") as f:
    json.dump(sections, f, ensure_ascii=False, indent=2)
with open(os.path.join(OUT_DIR, "edges.json"), "w", encoding="utf-8") as f:
    json.dump(edges, f, ensure_ascii=False, indent=2)

# ── Acceptance checks ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("ACCEPTANCE CHECKS")
print("=" * 60)

# 1.1: All TOC sections have definition
toc_subsections = set()
for line in toc.split("\n"):
    line = line.strip()
    if line.startswith("- ") or line.startswith("├ "):
        name = line.lstrip("- ├").strip()
        if name:
            toc_subsections.add(name)

defined = {s.get("subsection_title", "") for s in sections}
missing = toc_subsections - defined
check_1_1 = len(missing) == 0
print(f"1.1 All sections defined: {check_1_1} (missing: {len(missing)})")
if missing:
    print(f"     Missing: {list(missing)[:5]}")

# 1.2: All definitions non-empty
check_1_2 = all(s.get("definition", "").strip() for s in sections)
print(f"1.2 All definitions non-empty: {check_1_2}")

# 1.3: Edge count reasonable
check_1_3 = 15 <= len(edges) <= 80
print(f"1.3 Edge count {len(edges)} in [15,80]: {check_1_3}")

# 1.4: Key edge exists (税收损失 ↔ 削弱金融组织)
key_edge = None
for e in edges:
    fsub = e.get("from_subsection", "")
    tsub = e.get("to_subsection", "")
    if ("税收损失" in fsub or "税收损失" in tsub) and ("削弱" in fsub or "金融" in fsub or "削弱" in tsub or "金融" in tsub):
        key_edge = e
        break
check_1_4 = key_edge is not None
print(f"1.4 Key edge (税收损失↔FI后果) exists: {check_1_4}")
if key_edge:
    print(f"     type={key_edge.get('relation_type')}, detail={key_edge.get('relation_detail', '')[:80]}")

# 1.5: All edges have relation_detail
check_1_5 = all(e.get("relation_detail", "").strip() for e in edges)
print(f"1.5 All edges have detail: {check_1_5}")

# 1.6: Spot-check - random 5 edges, need manual inspection
import random
if len(edges) >= 5:
    samples = random.sample(edges, min(5, len(edges)))
    print(f"1.6 Spot-check samples (manual inspection needed):")
    for i, e in enumerate(samples):
        print(f"     [{i+1}] {e.get('from_subsection','')} --[{e.get('relation_type','')}]--> {e.get('to_subsection','')}")
        print(f"         {e.get('relation_detail','')[:100]}")

all_pass = check_1_1 and check_1_2 and check_1_3 and check_1_4 and check_1_5
print(f"\n  STEP 1 PASS: {all_pass}")
