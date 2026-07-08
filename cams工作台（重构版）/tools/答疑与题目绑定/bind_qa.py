"""
将学生答疑记录绑定到正式题库题目，继承选项证据句卡。

输入: data/source/qa.json + data/source/questions.json + data/derived/option_evidence_map.json
输出: data/derived/qa_bindings.json
"""
import json
import os
import random
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

_HERE = Path(__file__).resolve().parent
_WORKSPACE = _HERE.parent
_SOURCE = _WORKSPACE / "data" / "source"
_DERIVED = _WORKSPACE / "data" / "derived"

# --- 加载数据 ---
qa_records = json.loads((_SOURCE / "qa.json").read_text(encoding="utf-8"))
if isinstance(qa_records, dict):
    qa_records = qa_records.get("records", [])
questions = json.loads((_SOURCE / "questions.json").read_text(encoding="utf-8"))
if isinstance(questions, dict):
    questions = questions.get("questions", [])
option_evidence = json.loads((_DERIVED / "option_evidence_map.json").read_text(encoding="utf-8"))
op_items = option_evidence.get("items", []) if isinstance(option_evidence, dict) else []

# 构建 API 客户端
api_key = os.environ.get("DEEPSEEK_API_KEY", "")
base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
if not api_key:
    raise RuntimeError("DEEPSEEK_API_KEY 未设置")
client = OpenAI(api_key=api_key, base_url=base_url)

print(f"QA records: {len(qa_records)}, Questions: {len(questions)}, OptionEvidence items: {len(op_items)}")

# --- 1. 从 QA 文件名提取 section ---
for qa in qa_records:
    fname = qa.get("source_file", "")
    m = re.search(r"(\d+)\.(\d+)", fname)
    if m:
        qa["section"] = f"{m.group(1)}.{m.group(2)}"
    else:
        qa["section"] = "unknown"

# --- 2. 按 section 分组题目 ---
questions_by_section = defaultdict(list)
for q in questions:
    questions_by_section[q["section"]].append(q)

# --- 3. 关键词匹配 QA → 题目 ---
bindings = []
for qa in qa_records:
    sec = qa.get("section", "unknown")
    qa_text = qa.get("question", "")
    qa_words = set(re.findall(r"[一-鿿\w]{2,}", qa_text))

    candidates = questions_by_section.get(sec, questions)
    best_score = 0
    best_q = None
    for q_item in candidates:
        q_words = set(re.findall(r"[一-鿿\w]{2,}", q_item["stem"]))
        overlap = len(qa_words & q_words)
        if overlap > best_score:
            best_score = overlap
            best_q = q_item

    bindings.append({
        "qa": qa,
        "matched_question": best_q,
        "match_score": best_score,
        "match_method": "keyword",
    })

keyword_matched = sum(1 for b in bindings if b["match_score"] >= 3)
print(f"Keyword matched (score>=3): {keyword_matched}/{len(bindings)}")

# --- 4. BGE 兜底 ---
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

# --- 5. LLM 审核 ---
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
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=128,
            )
            content = resp.choices[0].message.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            result = json.loads(content)
            return result.get("correct", True)
        except Exception:
            time.sleep(0.3)
    return True

print("Flash review...")
for b in bindings:
    b["flash_approved"] = review_binding(b)

approved = sum(1 for b in bindings if b["flash_approved"])
print(f"Flash approved: {approved}/{len(bindings)}")

# --- 6. 从 option_evidence_map 继承句卡 ---
# 构建 question_id → set(card_ids)
question_cards: dict[str, set[str]] = {}
for item in op_items:
    qid = item.get("question_id", "")
    if not qid:
        continue
    for opt in item.get("options", []) or []:
        for card in opt.get("evidence_cards", []) or []:
            cid = card.get("card_id", "")
            if cid:
                question_cards.setdefault(qid, set()).add(cid)

for b in bindings:
    if b.get("matched_question"):
        qid = b["matched_question"]["id"]
        cards = sorted(question_cards.get(qid, set()))
        b["inherited_card_ids"] = cards

total_cards = sum(len(b["inherited_card_ids"]) for b in bindings)
print(f"Inherited cards from option_evidence_map: {total_cards} total")

# --- 7. 保存 ---
output = [{
    "qa_id": b["qa"]["id"],
    "source_file": b["qa"]["source_file"],
    "qa_question": b["qa"]["question"][:200],
    "bound_question_id": b["matched_question"]["id"] if b.get("matched_question") else "",
    "bound_question_stem": b["matched_question"]["stem"][:200] if b.get("matched_question") else "",
    "match_method": b["match_method"],
    "match_score": b["match_score"],
    "flash_approved": b["flash_approved"],
    "inherited_card_ids": b["inherited_card_ids"],
} for b in bindings]

(_DERIVED / "qa_bindings.json").write_text(
    json.dumps({"total": len(output), "bindings": output, "approved": approved}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(f"\nSaved qa_bindings.json → {_DERIVED / 'qa_bindings.json'}")
print(f"Total: {len(output)} bindings, {approved} approved, {total_cards} inherited cards")
