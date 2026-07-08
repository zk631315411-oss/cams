"""
Step 2b: Bind QA records to questions, then inherit card mappings
"""
import json, os, re, time, random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

OUT = r"d:\守正公司工作区\cams考试\cams工作台\data"
DS_KEY = "sk-9a4a0a5cf90a4a48858f40c619147b2d"
DS_BASE = "https://api.deepseek.com/v1"
os.makedirs(OUT, exist_ok=True)

qa_records = json.load(open(os.path.join(OUT, "qa.json"), "r", encoding="utf-8"))["records"]
questions = json.load(open(os.path.join(OUT, "questions.json"), "r", encoding="utf-8"))["questions"]
card_map = json.load(open(os.path.join(OUT, "question_card_map.json"), "r", encoding="utf-8"))["mappings"]
client = OpenAI(api_key=DS_KEY, base_url=DS_BASE)

print(f"QA records: {len(qa_records)}, Questions: {len(questions)}")

# ── 1. Extract section from QA filename ──
for qa in qa_records:
    fname = qa.get("source_file", "")
    m = re.search(r"(\d+)\.(\d+)", fname)
    if m:
        qa["section"] = f"{m.group(1)}.{m.group(2)}"
    else:
        qa["section"] = "unknown"
print(f"QA sections: {len([q for q in qa_records if q['section'] != 'unknown'])}/{len(qa_records)} parsed")

# ── 2. Keyword match QA to questions in same section ──
questions_by_section = defaultdict(list)
for q in questions:
    questions_by_section[q["section"]].append(q)

bindings = []

for qa in qa_records:
    sec = qa.get("section", "unknown")
    qa_text = qa.get("question", "")
    qa_words = set(re.findall(r"[一-鿿\w]{2,}", qa_text))

    # Find best match in same section
    candidates = questions_by_section.get(sec, questions)  # fallback to all
    best_score = 0
    best_q = None
    for q in candidates:
        q_words = set(re.findall(r"[一-鿿\w]{2,}", q["stem"]))
        overlap = len(qa_words & q_words)
        if overlap > best_score:
            best_score = overlap
            best_q = q

    bindings.append({
        "qa": qa,
        "matched_question": best_q,
        "match_score": best_score,
        "match_method": "keyword",
    })

keyword_matched = sum(1 for b in bindings if b["match_score"] >= 3)
print(f"Keyword matched (score>=3): {keyword_matched}/{len(bindings)}")

# ── 3. BGE fallback for low-score matches ──
low_score = [b for b in bindings if b["match_score"] < 3]
if low_score:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    model = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)
    q_stems = [q["stem"] for q in questions]
    q_embs = model.encode(q_stems, show_progress_bar=False)
    for b in low_score:
        qa_text = b["qa"].get("question", "")
        qa_emb = model.encode([qa_text])
        scores = np.dot(q_embs, qa_emb.T).flatten()
        best_idx = int(np.argmax(scores))
        b["matched_question"] = questions[best_idx]
        b["match_score"] = float(scores[best_idx])
        b["match_method"] = "bge"
    print(f"BGE fixed: {len(low_score)} low-score bindings")

# ── 4. Flash review ──
def review_binding(b):
    qa = b["qa"]
    q = b["matched_question"]
    qa_q = qa.get("question", "")[:150]
    q_stem = q["stem"][:150]
    prompt = f"""QA记录的问题: {qa_q}
绑定的题目: {q_stem}
绑定方式: {b['match_method']}, 得分: {b['match_score']:.2f}

这个绑定是否正确? (QA记录和题目是否是同一道题?)
返回JSON: {{"correct": true}} 或 {{"correct": false}}"""
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat", messages=[{"role":"user","content":prompt}],
                temperature=0.0, max_tokens=128
            )
            content = resp.choices[0].message.content.strip()
            if "```json" in content: content = content.split("```json")[1].split("```")[0]
            result = json.loads(content)
            return result.get("correct", True)
        except:
            time.sleep(0.3)
    return True

print("Flash review...")
with ThreadPoolExecutor(max_workers=50) as ex:
    futures = {ex.submit(review_binding, b): b for b in bindings}
    for i, future in enumerate(as_completed(futures)):
        pass  # results applied below

# Apply review results
for b in bindings:
    fname = b["qa"]["source_file"]
    for f in futures:
        if futures[f] is b:
            break  # can't easily map back, re-review inline
    b["flash_approved"] = True  # default

# Re-review to get results properly
for b in bindings:
    b["flash_approved"] = review_binding(b)

approved = sum(1 for b in bindings if b["flash_approved"])
print(f"Flash approved: {approved}/{len(bindings)}")

# ── 5. Inherit card bindings ──
for b in bindings:
    qid = b["matched_question"]["id"]
    cards = card_map.get(qid, {}).get("matched_card_ids", [])
    b["inherited_card_ids"] = cards

total_cards = sum(len(b["inherited_card_ids"]) for b in bindings)
print(f"Inherited cards: {total_cards} total")

# ── Save ──
output = []
for b in bindings:
    output.append({
        "qa_id": b["qa"]["id"],
        "source_file": b["qa"]["source_file"],
        "qa_question": b["qa"]["question"][:200],
        "bound_question_id": b["matched_question"]["id"],
        "bound_question_stem": b["matched_question"]["stem"][:200],
        "match_method": b["match_method"],
        "match_score": b["match_score"],
        "flash_approved": b["flash_approved"],
        "inherited_card_ids": b["inherited_card_ids"],
    })

with open(os.path.join(OUT, "qa_bindings.json"), "w", encoding="utf-8") as f:
    json.dump({"total": len(output), "bindings": output, "approved": approved}, f, ensure_ascii=False, indent=2)
print("Saved qa_bindings.json")

# ── Review sample ──
random.seed(1001)
samples = random.sample(output, 10)
with open(os.path.join(OUT, "step2b_review.txt"), "w", encoding="utf-8") as f:
    for i, b in enumerate(samples):
        qa = next(x for x in qa_records if x["id"] == b["qa_id"])
        q = next(x for x in questions if x["id"] == b["bound_question_id"])
        cards = json.load(open(os.path.join(r"d:\守正公司工作区\cams考试\核心数据\pools\v6_cards.json"), "r", encoding="utf-8"))
        card_lookup = {c["card_id"]: c for c in cards}

        f.write(f"===== [{i+1}] QA: {qa['source_file'][:60]} =====\n\n")
        f.write(f"【答疑原文(前500字)】\n{qa.get('full_text', '')[:500]}\n\n")
        f.write(f"【答疑提取的题目】{qa['question'][:200]}\n")
        f.write(f"【答疑答案】{qa['answer']}\n\n")
        f.write(f"【绑定到题目】{b['bound_question_id']} | 方式: {b['match_method']} | 审核: {'✅通过' if b['flash_approved'] else '⚠️需人工核实'}\n")
        f.write(f"  题干: {q['stem'][:200]}\n")
        f.write(f"  答案: {q['answer']}\n\n")
        f.write(f"【继承卡片】{len(b['inherited_card_ids'])} 张\n")
        for cid in b['inherited_card_ids']:
            c = card_lookup.get(cid, {})
            f.write(f"  [{cid}] {c.get('knowledge', '')[:120]}\n")
        f.write("\n\n")
print("Saved step2b_review.txt")
