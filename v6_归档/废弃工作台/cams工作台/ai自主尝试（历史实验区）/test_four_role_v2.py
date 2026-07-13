"""四角色法测试 v2：巢状交易 — 用BGE替代关键词搜索"""
import json, os, sys, re, numpy as np

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from openai import OpenAI
from sentence_transformers import SentenceTransformer

client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
OUT = os.path.join(DATA, "agentic_search_eval_v2", "kg")

# Load KG
with open(os.path.join(OUT, "sections.json"), "r", encoding="utf-8") as f:
    sections = json.load(f)
with open(os.path.join(OUT, "card_section_map.json"), "r", encoding="utf-8") as f:
    cs_map = json.load(f)
with open(os.path.join(DATA, "cards_ch2.json"), "r", encoding="utf-8") as f:
    cards = json.load(f)
with open(os.path.join(DATA, "questions.json"), "r", encoding="utf-8") as f:
    questions = json.load(f)["questions"]

# Build card context
card_ctx = {}
for c in cards:
    parts = [c.get("context_before",""), c.get("knowledge",""), c.get("context_after","")]
    card_ctx[c["card_id"]] = " ".join(filter(None, parts))

section_titles = [s.get("subsection_title", "") for s in sections]
section_defs = [s.get("definition", "") for s in sections]
section_to_cards = cs_map["section_to_cards"]

alias_to_section = {}
for s in sections:
    for alias in s.get("aliases", []):
        alias_to_section[alias.lower()] = s["subsection_title"]
    alias_to_section[s["subsection_title"].lower()] = s["subsection_title"]

# Load BGE
bge = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)
queries_bge = [t + " " + d + " " + " ".join(s.get("aliases", []))
               for s, t, d in zip(sections, section_titles, section_defs)]
section_vecs = bge.encode(queries_bge, normalize_embeddings=True)

# Find question 2.2_9
q = None
for qq in questions:
    if qq["id"] == "2.2_9":
        q = qq
        break

stem = q["stem"]
options = q["options"]
answer = q["answer"]
opt_text = " ".join(f"{k}. {v}" for k, v in options.items())

print("题目:", stem)
print("选项:", opt_text)
print("答案:", answer)
print()

# ====== AI #1: 联想者 ======
print("=" * 60)
print("AI #1 联想者")
print("=" * 60)

ai1_prompt = f"""你是CAMS反洗钱考试专家。请基于你的知识自由回答以下问题。

题目：{stem}
选项：{opt_text}
正确答案：{answer}

请做三件事：
1. 这道题考的是教材里哪个知识点？在哪个章节？
2. 每个选项为什么对或错？把你所有能想到的理由都写出来，可以跨章节联想。
3. 你的回答中哪些地方是"需要查教材原文验证的具体事实主张"？请明确标出。"""

resp = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": ai1_prompt}],
    max_tokens=8000
)
ai1_output = resp.choices[0].message.content.strip()
print(ai1_output[:2000])

# ====== AI #2: 核查员 ======
print()
print("=" * 60)
print("AI #2 核查员")
print("=" * 60)

ai2_prompt = f"""以下是AI对一道CAMS题目的分析。请从中提取所有"需要查教材原文验证的具体事实主张"。

规则：每条一行，格式为"需要验证：[具体主张]"。提取完后为每条生成教材搜索query。

AI分析：
{ai1_output}"""

resp = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": ai2_prompt}],
    max_tokens=8000
)
ai2_output = resp.choices[0].message.content.strip()
print(ai2_output[:1500])

# ====== BGE Search (代替关键词搜索) ======
print()
print("=" * 60)
print("BGE语义搜索证据")
print("=" * 60)

# Extract search queries from AI #2 claims
claims = re.findall(r'需要验证：(.+)', ai2_output)
# Also use the question stem + each option as queries
search_queries = [stem] + [f"{k}. {v}" for k, v in options.items()]
if claims:
    search_queries.extend(claims[:5])

evidence_parts = []
seen_cids = set()

for query in search_queries[:10]:
    query_clean = query.strip()[:200]
    print(f"\nBGE搜索: {query_clean[:80]}...")

    # BGE encode the query
    q_vec = bge.encode([query_clean], normalize_embeddings=True)

    # Match against sections
    scores = (q_vec @ section_vecs.T).flatten()
    top_idx = list(reversed(scores.argsort()))[:5]

    for idx in top_idx[:3]:
        if float(scores[idx]) < 0.4:
            continue
        sec = section_titles[idx]
        cids = section_to_cards.get(sec, [])[:5]
        for cid in cids[:3]:
            if cid not in seen_cids:
                seen_cids.add(cid)
                ctx = card_ctx.get(cid, "")[:250]
                evidence_parts.append(f"[{cid}] [{sec}] {ctx}")
                print(f"  {cid} (BGE={float(scores[idx]):.3f}) [{sec}]")

print(f"\n总证据: {len(evidence_parts)} 条")

# ====== AI #3: 裁判官 ======
print()
print("=" * 60)
print("AI #3 裁判官（仅基于BGE检索证据）")
print("=" * 60)

evidence_text = "\n---\n".join(evidence_parts[:20])

ai3_prompt = f"""你是CAMS反洗钱考试专家。以下是教材中检索到的相关证据。请仅基于这些证据回答问题。

题目：{stem}
选项：{opt_text}
正确答案：{answer}

教材证据：
{evidence_text[:6000]}

请逐一分析每个选项为什么对或错。每个判断必须引用来源（card_id）。
证据不足时明确说"证据不足"。

格式：
## 选项分析
### A. ...
判断：正确/错误
证据：...

### B. ...
判断：正确/错误
证据：..."""

resp = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[{"role": "user", "content": ai3_prompt}],
    max_tokens=8000
)
ai3_output = resp.choices[0].message.content.strip()
print(ai3_output)

# Save
out_dir = f"{DATA}/agentic_search_eval_v2/kg"
with open(f"{out_dir}/four_role_bge_nested.txt", "w", encoding="utf-8") as f:
    f.write(f"=== AI #1 联想者 ===\n{ai1_output}\n\n")
    f.write(f"=== AI #2 核查员 ===\n{ai2_output}\n\n")
    f.write(f"=== BGE证据 ({len(evidence_parts)}条) ===\n{evidence_text[:3000]}\n\n")
    f.write(f"=== AI #3 裁判官 ===\n{ai3_output}\n")

print(f"\n结果已保存")
