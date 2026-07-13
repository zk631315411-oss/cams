"""
179题映射：BGE预计算 + 5并发LLM，每题实时输出
"""
import os, sys, json, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
SAVE_PATH = os.path.join(OUT_DIR, "question_section_map.json")

print("Loading...")
with open(os.path.join(OUT_DIR, "sections.json"), "r", encoding="utf-8") as f:
    sections = json.load(f)
with open(os.path.join(OUT_DIR, "card_section_map.json"), "r", encoding="utf-8") as f:
    cs_map = json.load(f)
with open(os.path.join(DATA_DIR, "cards_ch2.json"), "r", encoding="utf-8") as f:
    cards = json.load(f)
with open(os.path.join(DATA_DIR, "questions.json"), "r", encoding="utf-8") as f:
    questions = json.load(f)["questions"]

card_context = {}
for c in cards:
    parts = [c.get("context_before",""), c.get("knowledge",""), c.get("context_after","")]
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
queries_bge = [t + " " + d + " " + " ".join(s.get("aliases", [])) for s, t, d in zip(sections, section_titles, section_defs)]
section_vecs = bge.encode(queries_bge, normalize_embeddings=True)

# Resume
done_ids = set()
if os.path.exists(SAVE_PATH):
    with open(SAVE_PATH, "r", encoding="utf-8") as f:
        done_ids = {r["question_id"] for r in json.load(f)}
    print(f"Resume: {len(done_ids)} done, {len(questions)-len(done_ids)} todo")

todo = [q for q in questions if q["id"] not in done_ids]

# Precompute: BGE stem matching + evidence for ALL questions
print(f"Precomputing BGE for {len(todo)} questions...")
precompute = {}
for q in todo:
    stem = q["stem"]
    stem_matched = set()
    for alias, sec_title in alias_to_section.items():
        if alias.lower() in stem.lower():
            stem_matched.add(sec_title)
    stem_vec = bge.encode([stem], normalize_embeddings=True)
    stem_scores = (stem_vec @ section_vecs.T).flatten()
    for idx in list(reversed(stem_scores.argsort()))[:3]:
        if float(stem_scores[idx]) > 0.5:
            stem_matched.add(section_titles[idx])
    stem_sorted = sorted(stem_matched, key=lambda t: float(stem_scores[section_titles.index(t)]), reverse=True)

    ev_lines = []
    for sec in stem_sorted[:2]:
        cids = section_to_cards.get(sec, [])[:8]
        if cids:
            ev_lines.append("[" + sec + "]")
            for cid in cids[:4]:
                ev_lines.append(card_context.get(cid, "")[:200])
    precompute[q["id"]] = {"stem_sorted": stem_sorted, "ev": "\n".join(ev_lines[:10])}
print(f"  Done. Starting LLM calls with 5 workers...")
print()

# Worker function
def process_one(q):
    qid = q["id"]
    pre = precompute[qid]
    stem_sorted = pre["stem_sorted"]
    ev = pre["ev"]
    options = q["options"]
    mapping = {"question_id": qid, "stem": q["stem"][:80], "options": [], "sections": stem_sorted[:2]}

    if stem_sorted and ev:
        opt_text = " ".join(k + ". " + v for k, v in options.items())
        prompt = "选项对应教材哪个小节？从[]选。\n" + q["stem"] + "\n" + opt_text + "\n证据:\n" + ev[:800] + "\n\nJSON:{\"options\":[{\"label\":\"A\",\"subsection\":\"小节或NONE\",\"rationale\":\"一句\"}]}"

        for attempt in range(2):
            try:
                resp = client.chat.completions.create(model=MODEL, messages=[{"role": "user", "content": prompt[:3000]}], max_tokens=8000)
                raw = resp.choices[0].message.content.strip()
                if not raw:
                    time.sleep(3)
                    continue
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
                try:
                    parsed = json.loads(raw)
                except:
                    import json_repair
                    parsed = json.loads(json_repair.repair_json(raw))
                for opt in parsed.get("options", []):
                    sub = opt.get("subsection", "")
                    opt["subsection_graph"] = "NONE"
                    if sub and sub != "NONE":
                        sub_vec = bge.encode([sub], normalize_embeddings=True)
                        scores = (section_vecs @ sub_vec.T).flatten()
                        best_idx = int(scores.argmax())
                        if float(scores[best_idx]) >= 0.5:
                            opt["subsection_graph"] = section_titles[best_idx]
                mapping["options"] = parsed.get("options", [])
                break
            except Exception as e:
                time.sleep(3)
    return mapping

# Process with 5 workers
results_dict = {}
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(process_one, q): q["id"] for q in todo}
    completed = len(done_ids)
    for future in as_completed(futures):
        qid = futures[future]
        try:
            mapping = future.result()
            results_dict[qid] = mapping
            completed += 1
            n_m = sum(1 for o in mapping.get("options",[]) if o.get("subsection_graph","NONE") != "NONE")
            n_e = len(mapping.get("options",[])) - n_m
            print(f"  [{completed}/179] {qid}: {n_m}m {n_e}e")
            # Save incrementally
            all_r = [r for r in json.load(open(SAVE_PATH, "r", encoding="utf-8"))] if os.path.exists(SAVE_PATH) else []
            all_r.append(mapping)
            with open(SAVE_PATH, "w", encoding="utf-8") as f:
                json.dump(all_r, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  {qid}: FAIL - {str(e)[:60]}")

# Final stats
all_r = json.load(open(SAVE_PATH, "r", encoding="utf-8"))
total_opts = sum(len(r.get("options",[])) for r in all_r)
total_mapped = sum(1 for r in all_r for o in r.get("options",[]) if o.get("subsection_graph","NONE") != "NONE")
print(f"\nDONE. {len(all_r)}q, {total_opts}opts, {total_mapped}m ({100*total_mapped//max(total_opts,1)}%)")
