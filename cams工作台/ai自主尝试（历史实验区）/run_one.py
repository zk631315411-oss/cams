"""逐题处理：每题BGE+LLM，实时汇报，即时保存"""
import json, time, re, os, sys, numpy as np
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from openai import OpenAI
from sentence_transformers import SentenceTransformer

print("Loading...")
client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
bge = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)

DATA = "data"; OUT = os.path.join(DATA, "agentic_search_eval_v2", "kg"); SAVE = os.path.join(OUT, "question_section_map.json")

with open(os.path.join(OUT, "sections.json"), "r", encoding="utf-8") as f: sections = json.load(f)
with open(os.path.join(OUT, "card_section_map.json"), "r", encoding="utf-8") as f: cs_map = json.load(f)
with open(os.path.join(DATA, "cards_ch2.json"), "r", encoding="utf-8") as f: cards = json.load(f)
with open(os.path.join(DATA, "questions.json"), "r", encoding="utf-8") as f: questions = json.load(f)["questions"]

card_ctx = {}
for c in cards:
    parts = [c.get("context_before",""), c.get("knowledge",""), c.get("context_after","")]
    card_ctx[c["card_id"]] = " ".join(filter(None, parts))
s2c = cs_map["section_to_cards"]
st = [s["subsection_title"] for s in sections]; sd = [s["definition"] for s in sections]
alias = {}
for s in sections:
    for a in s.get("aliases",[]): alias[a.lower()] = s["subsection_title"]
    alias[s["subsection_title"].lower()] = s["subsection_title"]

queries = [t+" "+d+" "+" ".join(s.get("aliases",[])) for s,t,d in zip(sections,st,sd)]
sv = bge.encode(queries, normalize_embeddings=True)

# Resume
done = set()
if os.path.exists(SAVE):
    with open(SAVE, "r", encoding="utf-8") as f: done = {r["question_id"] for r in json.load(f)}
    print(f"Resume: {len(done)} done")
todo = [q for q in questions if q["id"] not in done]
print(f"Todo: {len(todo)} questions")
print()

total_m = total_e = 0
t_start = time.time()
for qi, q in enumerate(todo):
    qid, stem, opts = q["id"], q["stem"], q["options"]

    sm = set()
    for a, sec in alias.items():
        if a.lower() in stem.lower(): sm.add(sec)
    sv_q = bge.encode([stem], normalize_embeddings=True)
    scores = (sv_q @ sv.T).flatten()
    for idx in list(reversed(scores.argsort()))[:3]:
        if float(scores[idx]) > 0.5: sm.add(st[idx])
    ss = sorted(sm, key=lambda t: float(scores[st.index(t)]), reverse=True)

    ev = []
    for sec in ss[:2]:
        cids = s2c.get(sec, [])[:8]
        if cids:
            ev.append("[" + sec + "]")
            for cid in cids[:4]: ev.append("  " + cid + ": " + card_ctx.get(cid, "")[:150])

    mapping = {"question_id": qid, "stem": stem[:80], "options": [], "sections": ss[:2]}
    nm = 0

    if ss and ev:
        ot = " ".join(k + ". " + v for k, v in opts.items())
        prompt = "选项对应哪个小节？从[]选。\n" + stem + "\n" + ot + "\n证据:\n" + "\n".join(ev[:8])
        prompt += "\n\nJSON: {\"options\": [{\"label\": \"A\", \"subsection\": \"小节或NONE\", \"rationale\": \"一句\"}]}"

        for attempt in range(2):
            try:
                t0 = time.time()
                resp = client.chat.completions.create(model="deepseek-v4-pro", messages=[{"role": "user", "content": prompt[:3000]}], max_tokens=8000)
                raw = resp.choices[0].message.content.strip()
                if not raw: time.sleep(3); continue
                raw = re.sub(r"^```(?:json)?\s*", "", raw); raw = re.sub(r"\s*```$", "", raw)
                try: parsed = json.loads(raw)
                except:
                    import json_repair; parsed = json.loads(json_repair.repair_json(raw))
                for opt in parsed.get("options", []):
                    sub = opt.get("subsection", "NONE"); g = "NONE"
                    if sub != "NONE":
                        sv2 = bge.encode([sub], normalize_embeddings=True)
                        s2 = (sv @ sv2.T).flatten(); bi = int(s2.argmax())
                        g = st[bi] if float(s2[bi]) >= 0.5 else "NONE"
                    opt["subsection_graph"] = g; mapping["options"].append(opt)
                    if g != "NONE": nm += 1
                break
            except Exception as e:
                if attempt == 1: print(f"  ERR: {str(e)[:40]}", end="")
                time.sleep(3)

    ne = len(opts) - nm; total_m += nm; total_e += ne
    elapsed = time.time() - t_start
    done_num = len(done) + qi + 1
    eta = elapsed / (qi + 1) * (len(todo) - qi - 1) if qi > 0 else 0
    print(f"[{done_num}/179] {qid}: {nm}m {ne}e | {total_m}m {total_e}e | eta {eta/60:.0f}m")

    all_r = json.load(open(SAVE, "r", encoding="utf-8")) if os.path.exists(SAVE) else []
    all_r.append(mapping)
    with open(SAVE, "w", encoding="utf-8") as f: json.dump(all_r, f, ensure_ascii=False, indent=2)

print(f"\nDONE. {len(done)+len(todo)} questions, {total_m} mapped, {total_e} empty ({100*total_m//max(total_m+total_e,1)}%)")
