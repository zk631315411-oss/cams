"""
方案B：四角色法预处理 → 题目选项→教材节点映射表（查询层）
图谱冻结，逐题LLM分析，BGE对齐到图谱节点名
"""
import os, sys, json, re, time, numpy as np

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    print("[FAIL] DEEPSEEK_API_KEY not set"); sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
MODEL = "deepseek-v4-pro"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.join(DATA_DIR, "agentic_search_eval_v2", "kg")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load ───────────────────────────────────────────────────────────
with open(os.path.join(DATA_DIR, "agentic_search_eval_v2", "ch2_full_text.txt"), "r", encoding="utf-8") as f:
    textbook = f.read()

with open(os.path.join(OUT_DIR, "sections.json"), "r", encoding="utf-8") as f:
    graph_sections = json.load(f)
section_titles = [s.get("subsection_title", "") for s in graph_sections]

with open(os.path.join(DATA_DIR, "questions.json"), "r", encoding="utf-8") as f:
    all_questions = json.load(f)["questions"]

test_ids = ["2.1_4", "2.1_19", "2.1_30", "2.2_1", "2.2_6", "2.2_9"]
test_questions = [q for q in all_questions if q["id"] in test_ids]

# ── BGE setup (once) ───────────────────────────────────────────────
from sentence_transformers import SentenceTransformer
bge = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)
section_vecs = bge.encode(section_titles, normalize_embeddings=True)

print(f"Processing {len(test_questions)} questions")
print(f"Textbook: {len(textbook)} chars, Sections: {len(section_titles)}")
print()

all_mappings = []

for qi, q in enumerate(test_questions):
    qid = q["id"]
    stem = q["stem"]
    options = q["options"]

    q_text = f"题干：{stem}\n"
    for k, v in options.items():
        q_text += f"  {k}. {v}\n"

    prompt = f"""你是CAMS教材的教学专家。以下是教材第2章全文和一道CAMS考题。

【教材全文】
{textbook}

【考题】
{q_text}

为这道题的每个选项，找出教材中最相关的小节名称。如果教材没有对应内容，subsection填"NONE"。

输出JSON（不要markdown包裹）：
{{"question_id": "{qid}", "options": [{{"label": "A", "subsection": "小节名或NONE", "rationale": "教材依据"}}]}}"""

    print(f"[{qi+1}/{len(test_questions)}] {qid}: {stem[:60]}...")

    raw = None
    for attempt in range(4):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.05, max_tokens=1000)
            raw = resp.choices[0].message.content.strip()
            if raw:
                break
            print(f"  Empty, retry {attempt+1}...")
            time.sleep(10)
        except Exception as e:
            print(f"  Error: {e}, retry {attempt+1}...")
            time.sleep(10)

    if not raw:
        print(f"  FAILED after all retries")
        continue

    # Save raw
    with open(os.path.join(OUT_DIR, f"query_{qid}_raw.txt"), "w", encoding="utf-8") as f:
        f.write(raw)

    # Parse
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        import json_repair
        result = json.loads(json_repair.repair_json(raw))

    # BGE-align each option's subsection to actual graph node name
    for opt in result.get("options", []):
        sub_name = opt.get("subsection", "")
        if sub_name and sub_name != "NONE":
            sub_vec = bge.encode([sub_name], normalize_embeddings=True)
            scores = (section_vecs @ sub_vec.T).flatten()
            best_idx = int(scores.argmax())
            best_score = float(scores[best_idx])
            if best_score >= 0.5:
                opt["subsection_graph"] = section_titles[best_idx]
                opt["subsection_score"] = best_score
            else:
                opt["subsection_graph"] = "NONE"
                opt["subsection_score"] = best_score
                opt["rationale"] += f" [原始:{sub_name}]"
        else:
            opt["subsection_graph"] = "NONE"
            opt["subsection_score"] = 0.0

        print(f"    {opt['label']} -> [{opt.get('subsection_graph','NONE')}] ({opt.get('subsection_score',0):.2f}) {opt.get('rationale','')[:60]}")

    all_mappings.append(result)
    print()

# ── Save ───────────────────────────────────────────────────────────
with open(os.path.join(OUT_DIR, "question_section_map.json"), "w", encoding="utf-8") as f:
    json.dump(all_mappings, f, ensure_ascii=False, indent=2)
print(f"Saved {len(all_mappings)} mappings")

# ── Validate ───────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("VALIDATION")
print(f"{'='*60}")
checks = {
    "2.1_4": {"A": "阶段|处置|洗钱的三个"},
    "2.1_19": {"D": "税收", "A": "金融|FI|削弱", "E": "金融|FI|削弱"},
    "2.2_6": {"C": "政治|PEP"},
    "2.2_1": {"A": "代理|通汇|委托", "E": "代理|通汇|委托"},
    "2.2_9": {"B": "通汇"},
    "2.1_30": {"A": "证券|市场"},
}
all_ok = True
for q_map in all_mappings:
    qid = q_map.get("question_id", "?")
    if qid in checks:
        for opt in q_map.get("options", []):
            label = opt["label"]
            if label in checks[qid]:
                sub = opt.get("subsection_graph", opt.get("subsection", ""))
                ok = bool(re.search(checks[qid][label], sub))
                if not ok:
                    print(f"  {qid} {label}: FAIL [{sub}] expected /{checks[qid][label]}/")
                    all_ok = False
if all_ok:
    print("  ALL PASS")
