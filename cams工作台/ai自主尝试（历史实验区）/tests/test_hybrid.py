"""
混合策略：图谱优先，失败时四角色法兜底
"""
import os, sys, json, numpy as np, re, time

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

with open(os.path.join(OUT_DIR, "sections.json"), "r", encoding="utf-8") as f:
    sections = json.load(f)
with open(os.path.join(OUT_DIR, "card_section_map.json"), "r", encoding="utf-8") as f:
    cs_map = json.load(f)
with open(os.path.join(DATA_DIR, "cards_ch2.json"), "r", encoding="utf-8") as f:
    cards = json.load(f)
with open(os.path.join(DATA_DIR, "questions.json"), "r", encoding="utf-8") as f:
    all_questions = json.load(f)["questions"]

card_knowledge = {c["card_id"]: c.get("knowledge", "") for c in cards}
card_context = {}
for c in cards:
    parts = [c.get("context_before", ""), c.get("knowledge", ""), c.get("context_after", "")]
    card_context[c["card_id"]] = " ".join(filter(None, parts))

section_to_cards = cs_map["section_to_cards"]
section_titles = [s.get("subsection_title", "") for s in sections]
section_defs = [s.get("definition", "") for s in sections]

alias_to_section = {}
for s in sections:
    for alias in s.get("aliases", []):
        alias_to_section[alias.lower()] = s["subsection_title"]
    alias_to_section[s["subsection_title"].lower()] = s["subsection_title"]

from sentence_transformers import SentenceTransformer
bge = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)
queries_bge = []
for s, t, d in zip(sections, section_titles, section_defs):
    aliases_str = " ".join(s.get("aliases", []))
    queries_bge.append(t + " " + d + " " + aliases_str)
section_vecs = bge.encode(queries_bge, normalize_embeddings=True)

with open(os.path.join(DATA_DIR, "agentic_search_eval_v2", "ch2_full_text.txt"), "r", encoding="utf-8") as f:
    textbook = f.read()

test_ids = ["2.1_4", "2.1_19", "2.1_30", "2.2_1", "2.2_6", "2.2_9"]
results = []

for qid in test_ids:
    q = [x for x in all_questions if x["id"] == qid][0]
    stem = q["stem"]
    options = q["options"]
    answer = q["answer"]

    print("\n" + "=" * 60)
    print("Testing: " + qid)

    # Phase 1: Graph
    stem_matched = set()
    for alias, sec_title in alias_to_section.items():
        if alias.lower() in stem.lower():
            stem_matched.add(sec_title)

    stem_vec = bge.encode([stem], normalize_embeddings=True)
    stem_scores = (stem_vec @ section_vecs.T).flatten()
    for idx in list(reversed(stem_scores.argsort()))[:5]:
        if float(stem_scores[idx]) > 0.5:
            stem_matched.add(section_titles[idx])

    stem_sorted = sorted(stem_matched, key=lambda t: float(stem_scores[section_titles.index(t)]), reverse=True)
    graph_evidence = []
    for sec_title in stem_sorted[:3]:
        cids = section_to_cards.get(sec_title, [])[:15]
        if cids:
            graph_evidence.append("[" + sec_title + "]")
            for cid in cids[:5]:
                ctx = card_context.get(cid, card_knowledge.get(cid, ""))[:300]
                graph_evidence.append("  " + cid + ": " + ctx)

    graph_chain = ""
    if stem_sorted:
        graph_prompt = "基于以下教材证据回答问题。\n\n题目：" + stem
        graph_prompt += "\n选项：" + json.dumps(options, ensure_ascii=False)
        graph_prompt += "\n正确答案：" + str(answer)
        graph_prompt += "\n\n教材证据：\n" + "\n".join(graph_evidence[:20])
        graph_prompt += "\n\n写一句推理链，引用card_id。不超过80字。"

        resp = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": graph_prompt}], temperature=0.2, max_tokens=200)
        graph_chain = resp.choices[0].message.content.strip()
        graph_ok = bool(graph_chain) and any(cid in graph_chain for cid in ["v6_b", "N0"])
        print("  [Graph] " + ("PASS" if graph_ok else "WEAK") + ": " + graph_chain[:100])
    else:
        graph_ok = False
        print("  [Graph] No sections matched")

    if graph_ok:
        save_text = "Method: graph\nAnswer: " + str(answer) + "\n\n" + graph_chain
        with open(os.path.join(OUT_DIR, "hybrid_" + qid + "_chain.txt"), "w", encoding="utf-8") as sf:
            sf.write(save_text)
        results.append({"qid": qid, "method": "graph", "chain": graph_chain, "pass": True})
        continue

    # Phase 2: Four-role fallback
    print("  [Fallback] Running four-role...")
    q_text = "题干：" + stem + "\n"
    for k, v in options.items():
        q_text += "  " + k + ". " + v + "\n"
    q_text += "正确答案：" + str(answer) + "\n"

    fb_prompt = "你是CAMS反洗钱考试专家。以下是教材第2章全文。\n\n【教材全文】\n" + textbook
    fb_prompt += "\n\n请分析下面这道题，逐一说明每个选项为什么对或错，引用教材中的具体小节名称和原文。直接输出分析文本。\n\n" + q_text

    fb_chain = ""
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": fb_prompt}], temperature=0.3, max_tokens=600)
            fb_chain = resp.choices[0].message.content.strip()
            if fb_chain:
                break
            print("    Empty, retry " + str(attempt+1) + "...")
            time.sleep(10)
        except Exception as e:
            print("    Error: " + str(e)[:80] + ", retry " + str(attempt+1) + "...")
            time.sleep(10)

    fb_ok = bool(fb_chain) and len(fb_chain) > 50
    print("  [Fallback] " + ("PASS" if fb_ok else "FAIL") + " (" + str(len(fb_chain)) + " chars)")

    save_text = "Method: fallback\nAnswer: " + str(answer) + "\n\n" + fb_chain
    with open(os.path.join(OUT_DIR, "hybrid_" + qid + "_chain.txt"), "w", encoding="utf-8") as sf:
        sf.write(save_text)
    results.append({"qid": qid, "method": "fallback" if fb_ok else "failed", "chain": fb_chain, "pass": fb_ok})

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
for r in results:
    status = "PASS" if r["pass"] else "FAIL"
    print("  " + r["qid"] + ": " + r["method"] + " - " + status)
passed = sum(1 for r in results if r["pass"])
print("\n  Total: " + str(passed) + "/" + str(len(results)) + " passed")
