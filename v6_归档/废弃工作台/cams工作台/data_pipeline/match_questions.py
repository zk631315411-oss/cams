"""
Step 1b: Match questions to knowledge cards
Flow: Extract KP → Check precision → Fix imprecise KPs → Match → Review
"""
import json, os, re, time, random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

OUT = r"d:\守正公司工作区\cams考试\cams工作台\data"
POOLS = r"d:\守正公司工作区\cams考试\核心数据\pools"
DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DS_BASE = "https://api.deepseek.com/v1"
os.makedirs(OUT, exist_ok=True)

questions = json.load(open(os.path.join(OUT, "questions.json"), "r", encoding="utf-8"))["questions"]
cards = json.load(open(os.path.join(POOLS, "v6_cards.json"), "r", encoding="utf-8"))
client = OpenAI(api_key=DS_KEY, base_url=DS_BASE)
print(f"Questions: {len(questions)}, Cards: {len(cards)}")

# ── 1. Extract knowledge point ──
kps = {}
missing = []
for q in questions:
    expl = q["explanation"]
    m = re.search(r"(?:具体)?知识点\s*[：:]\s*\n?(.+?)(?:\n|选项|解析|$)", expl)
    if m:
        kp = m.group(1).strip()
        kp = re.sub(r"[。，；;]$", "", kp)
        if len(kp) > 80:
            kp = kp.split("\n")[0].strip()
        kps[q["id"]] = kp
    else:
        m2 = re.search(r"(?:具体)?知识点\s*\n(.+)", expl)
        if m2:
            kps[q["id"]] = m2.group(1).strip()[:100]
        else:
            kps[q["id"]] = q["stem"][:80]
            missing.append(q["id"])

print(f"Extracted: {179 - len(missing)}/179")

# ── 2. Flash: check KP precision ──
def check_kp(q):
    qid = q["id"]
    kp = kps.get(qid, "")
    q_stem, q_expl = q["stem"], q["explanation"]
    prompt = f"""题目: {q_stem}
知识点标签: 【{kp}】

这个标签和题目考察的内容是否明显不匹配? (主题完全不同才算)
返回JSON: {{"mismatch": true}} 或 {{"mismatch": false}}"""
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat", messages=[{"role":"user","content":prompt}],
                temperature=0.0, max_tokens=128
            )
            content = resp.choices[0].message.content.strip()
            if "```json" in content: content = content.split("```json")[1].split("```")[0]
            return qid, json.loads(content).get("mismatch", False)
        except:
            time.sleep(0.3)
    return qid, False

print("Checking KP precision...")
flags = {}
with ThreadPoolExecutor(max_workers=50) as ex:
    futures = {ex.submit(check_kp, q): q for q in questions}
    for i, future in enumerate(as_completed(futures)):
        qid, mismatch = future.result()
        if mismatch:
            flags[qid] = {"knowledge_point": kps[qid]}
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(questions)}")
print(f"Flagged: {len(flags)} questions with imprecise KP")

# ── 3. Flash: fix flagged KPs ──
fixed_kps = {}
if flags:
    print("Fixing KPs...")
    items = [(qid, info) for qid, info in flags.items()]
    def fix_kp(item):
        qid, info = item
        q = next(q for q in questions if q["id"] == qid)
        old_kp = info["knowledge_point"]
        q_stem, q_ans, q_expl = q["stem"], q["answer"], q["explanation"]
        prompt = f"""知识点标签【{old_kp}】与实际考察内容不匹配。
题目: {q_stem} | 答案: {q_ans}
解析: {q_expl}
请生成一个更精准的知识点名称（15字以内）。
返回JSON: {{"corrected_kp": "新标签"}}"""
        for attempt in range(2):
            try:
                resp = client.chat.completions.create(
                    model="deepseek-chat", messages=[{"role":"user","content":prompt}],
                    temperature=0.0, max_tokens=128
                )
                content = resp.choices[0].message.content.strip()
                if "```json" in content: content = content.split("```json")[1].split("```")[0]
                new_kp = json.loads(content).get("corrected_kp", old_kp)
                if new_kp and new_kp != old_kp:
                    return qid, old_kp, new_kp
                return qid, old_kp, old_kp
            except:
                time.sleep(0.3)
        return qid, old_kp, old_kp

    with ThreadPoolExecutor(max_workers=50) as ex:
        f_futures = {ex.submit(fix_kp, item): item for item in items}
        for future in as_completed(f_futures):
            qid, old_kp, new_kp = future.result()
            if new_kp != old_kp:
                kps[qid] = new_kp
                fixed_kps[qid] = {"old": old_kp, "new": new_kp}
                flags[qid]["old_kp"] = old_kp
                flags[qid]["new_kp"] = new_kp
                flags[qid]["kp_corrected_by_ai"] = True

    print(f"Fixed: {len(fixed_kps)} KPs")
    for qid, fix in list(fixed_kps.items())[:5]:
        print(f"  {qid}: [{fix['old'][:30]}] -> [{fix['new'][:30]}]")

# ── 4. String match (original KP) + BGE (AI-corrected KP) ──
stop_words = ["什么","是","的","了","在","和","与","及","或","等","如何","哪","哪些","以下","哪个","何种","何者","为","?","？","。","，","、"]
matches = {}

# Pre-load bge for AI-corrected KPs and long KPs
bge_needed_ids = [q["id"] for q in questions if len(kps.get(q["id"], "")) > 30 or q["id"] in fixed_kps]
if bge_needed_ids:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    model = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)
    card_knowledges = [c["knowledge"] for c in cards]
    card_embs = model.encode(card_knowledges, show_progress_bar=False)
    print(f"BGE pre-load: {len(bge_needed_ids)} questions need bge")

for q in questions:
    qid = q["id"]
    kp = kps.get(qid, "")
    if not kp:
        matches[qid] = []
    elif qid in fixed_kps or len(kp) > 30:
        # AI-corrected or long KP → bge
        query = q["stem"] + " " + kp
        q_emb = model.encode([query])
        scores = np.dot(card_embs, q_emb.T).flatten()
        top30 = np.argsort(scores)[-30:][::-1]
        found = []
        for idx in top30:
            if scores[idx] > 0.3:
                c = cards[idx]
                found.append((c["card_id"], float(scores[idx]), c["knowledge"][:120], c["citation"][:150]))
        matches[qid] = found
    else:
        # Original short KP → keyword match
        clean = kp
        for sw in stop_words: clean = clean.replace(sw, " ")
        keywords = [kw for kw in re.split(r"[，,、；;：:。\s（）()《》]+", clean) if len(kw) >= 2]
        found = []
        for c in cards:
            text = c["knowledge"] + " " + c["citation"]
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                found.append((c["card_id"], score, c["knowledge"][:120], c["citation"][:150]))
        found.sort(key=lambda x: -x[1])
        matches[qid] = [f for f in found if f[1] >= 1][:30]

print(f"String match: {sum(1 for qid in matches if matches[qid])}/179 with candidates")

# ── 5. Flash review (confirm matched cards) ──
def review_one(q):
    qid = q["id"]
    kp = kps.get(qid, "")
    candidates = matches.get(qid, [])[:10]
    if not candidates: return qid, {"confirmed": []}
    card_list = ""
    for i, (cid, score, know, cit) in enumerate(candidates):
        card_list += f"[{i}] {know}\n"
    q_stem, q_ans = q["stem"], q["answer"]
    prompt = f"""你是CAMS考试专家。知识点:【{kp}】

题目: {q_stem} | 答案: {q_ans}

候选卡片:
{card_list}
选出所有相关的卡片(通常1-5张)。返回JSON: {{"confirmed": [0, ...]}}"""
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat", messages=[{"role":"user","content":prompt}],
                temperature=0.0, max_tokens=256
            )
            content = resp.choices[0].message.content.strip()
            if "```json" in content: content = content.split("```json")[1].split("```")[0]
            elif "```" in content: content = content.split("```")[1].split("```")[0]
            return qid, json.loads(content)
        except:
            time.sleep(1)
    return qid, {"confirmed": []}

print(f"\nFlash review: {len(questions)} calls...")
t0 = time.time()
reviewed = {}
with ThreadPoolExecutor(max_workers=50) as ex:
    futures = {ex.submit(review_one, q): q for q in questions}
    for i, future in enumerate(as_completed(futures)):
        qid, result = future.result()
        reviewed[qid] = result
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(questions)} ({time.time()-t0:.0f}s)")

# ── 7. Build final map ──
final_map = {}
for q in questions:
    qid = q["id"]
    candidates = matches.get(qid, [])[:10]
    confirmed = []
    for idx in reviewed.get(qid, {}).get("confirmed", []):
        if isinstance(idx, int) and idx < len(candidates):
            confirmed.append(candidates[idx][0])

    entry = {
        "knowledge_point": kps.get(qid, ""),
        "num_candidates": len(candidates),
        "matched_card_ids": confirmed,
    }
    if qid in fixed_kps:
        entry["original_kp"] = fixed_kps[qid]["old"]
        entry["kp_corrected_by_ai"] = True
    final_map[qid] = entry

total_confirmed = sum(len(v["matched_card_ids"]) for v in final_map.values())
questions_with_match = sum(1 for v in final_map.values() if v["matched_card_ids"])
print(f"\nFinal: {questions_with_match}/179 matched, {total_confirmed} card links, {len(flags)} flagged ({len(fixed_kps)} fixed)")

# Save
output = {
    "mappings": final_map,
    "flagged": flags,
    "stats": {
        "total_questions": len(questions),
        "questions_with_matches": questions_with_match,
        "total_card_links": total_confirmed,
        "flagged_kp_mismatch": len(flags),
        "kps_fixed_by_ai": len(fixed_kps),
        "elapsed_s": time.time() - t0,
    }
}
with open(os.path.join(OUT, "question_card_map.json"), "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# ── 8. Review sample ──
random.seed(801)
sample_ids = random.sample([q["id"] for q in questions], 10)
with open(os.path.join(OUT, "step1b_review.txt"), "w", encoding="utf-8") as f:
    for qid in sample_ids:
        q = next(x for x in questions if x["id"] == qid)
        m = final_map[qid]
        f.write(f"========== {qid} ==========\n")
        f.write(f"知识点: {m['knowledge_point']}")
        if m.get("kp_corrected_by_ai"):
            f.write(f" [AI修正, 原: {m.get('original_kp', '')}]")
        f.write(f"\n题干: {q['stem'][:120]}\n")
        f.write(f"匹配: {len(m['matched_card_ids'])} 张\n")
        for cid in m['matched_card_ids']:
            c = next(x for x in cards if x["card_id"] == cid)
            f.write(f"  [{cid}] {c['knowledge'][:100]}\n")
        if not m['matched_card_ids']:
            f.write("  (无匹配)\n")
        f.write("\n")
print("Saved step1b_review.txt")
