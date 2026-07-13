"""
第二步：卡片→节点挂载
路A: citation 字符串匹配（确定性）
路B: BGE 搜索（兜底）
+ 2.1_19 选项预验证
"""
import os, sys, json, re

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_DIR = os.path.join(DATA_DIR, "agentic_search_eval_v2", "kg")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load inputs ────────────────────────────────────────────────────
with open(os.path.join(OUT_DIR, "sections.json"), "r", encoding="utf-8") as f:
    sections = json.load(f)
with open(os.path.join(DATA_DIR, "cards_ch2.json"), "r", encoding="utf-8") as f:
    cards = json.load(f)
# Load ch2.json for section text matching
with open(os.path.join(DATA_DIR, "chapters", "ch2.json"), "r", encoding="utf-8") as f:
    ch2 = json.load(f)

print(f"Sections: {len(sections)}")
print(f"Cards: {len(cards)}")

# Build section text lookup: subsection_title -> full text of that subsection
section_texts = {}
for sec in ch2.get("sections", []):
    sid = sec.get("section_id", "")
    for sub in sec.get("subsections", []):
        title = sub.get("title", "")
        text = " ".join(p.get("text", "") for p in sub.get("paragraphs", []))
        section_texts[title] = text

# ── Path A: citation direct matching ───────────────────────────────
print("\n--- Path A: Citation matching ---")
card_section_map = {}  # card_id -> {section_title, method, score}
section_cards = {}     # section_title -> [card_ids]

import re as _re
def _clean(t):
    return _re.sub(r'[•‣◦○●■□▪▫]', '', t)

for card in cards:
    cid = card.get("card_id", "")
    citation = card.get("citation", "")
    knowledge = card.get("knowledge", "")
    if not cid or not citation:
        continue

    citation_clean = _clean(citation)
    knowledge_clean = _clean(knowledge)

    best_match = None
    best_len = 0
    for stitle, stext in section_texts.items():
        stext_clean = _clean(stext)
        if (citation_clean[:30] in stext_clean or citation_clean[-30:] in stext_clean or knowledge_clean[:30] in stext_clean):
            if len(stitle) > best_len:
                best_match = stitle
                best_len = len(stitle)

    if best_match:
        card_section_map[cid] = {
            "section_title": best_match,
            "method": "citation",
            "score": 1.0
        }
        if best_match not in section_cards:
            section_cards[best_match] = []
        section_cards[best_match].append(cid)

print(f"  Citation matched: {len(card_section_map)} cards")

# Check key cards
for key_cid in ["v6_b04_N09", "v6_b03_N18"]:
    if key_cid in card_section_map:
        st = card_section_map[key_cid]["section_title"]
        print(f"  {key_cid} -> {st} (citation)")
    else:
        print(f"  {key_cid} -> NOT FOUND by citation, will use BGE")

# ── Path B: BGE for unmatched cards ─────────────────────────────────
print("\n--- Path B: BGE search ---")
unmatched = [c for c in cards if c.get("card_id") and c["card_id"] not in card_section_map]
print(f"  Unmatched cards: {len(unmatched)}")

from sentence_transformers import SentenceTransformer
bge = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)

if unmatched:
    model = bge  # reuse

    # Pre-compute card embeddings
    card_knowledges = []
    card_ids_b = []
    for c in unmatched:
        know = c.get("knowledge", "")[:200]
        card_knowledges.append(know)
        card_ids_b.append(c["card_id"])
    card_vecs = model.encode(card_knowledges, normalize_embeddings=True)

    # For each section, compute embedding and search
    section_titles = []
    section_defs = []
    for s in sections:
        section_titles.append(s.get("subsection_title", ""))
        section_defs.append(s.get("definition", ""))

    # Build query = title + definition for each section
    queries = [f"{t} {d}" for t, d in zip(section_titles, section_defs)]
    query_vecs = model.encode(queries, normalize_embeddings=True)

    # Cosine similarity: query_vecs @ card_vecs.T
    import numpy as np
    scores_matrix = query_vecs @ card_vecs.T  # (n_sections, n_cards)

    # Collect all (card, section, score) triples, then assign global-best
    candidates = []
    for i, stitle in enumerate(section_titles):
        row = scores_matrix[i]
        top_indices = np.argsort(row)[::-1][:5]
        for j in top_indices:
            score = float(row[j])
            if score >= 0.5:
                cid = card_ids_b[j]
                candidates.append((score, cid, stitle))

    # Sort by score descending, assign each card to highest-scoring section
    candidates.sort(reverse=True)
    assigned_cards = set()
    for score, cid, stitle in candidates:
        if cid not in assigned_cards:
            card_section_map[cid] = {
                "section_title": stitle,
                "method": "bge",
                "score": score
            }
            if stitle not in section_cards:
                section_cards[stitle] = []
            section_cards[stitle].append(cid)
            assigned_cards.add(cid)

    # Post-BGE: prefer child subsection over parent section using ch2.json hierarchy
    # Build parent-child map from ch2.json subsection structure
    ch2_parent_of = {}
    for sec in ch2.get("sections", []):
        for sub in sec.get("subsections", []):
            title = sub.get("title", "")
            # Parent = the section_id (e.g., 2.1) - child subsections have more specific titles
            # Group subsections that share a broader concept name
            # For now: use the fact that subsections under same section are siblings
            ch2_parent_of[title] = {"section_id": sec.get("section_id", ""), "section_title": sec.get("section_title", "")}

    reassigned = 0
    for cid in list(card_section_map.keys()):
        entry = card_section_map[cid]
        if entry["method"] != "bge":
            continue
        current = entry["section_title"]
        current_score = entry["score"]
        current_info = ch2_parent_of.get(current, {})

        # Check all other sections: if a section has a higher score AND is more specific (longer title, narrower scope)
        # prefer it over broad sections
        if current in section_titles:
            current_idx = section_titles.index(current)
            for child_idx, child_title in enumerate(section_titles):
                if child_idx == current_idx:
                    continue
                child_score = float(scores_matrix[child_idx][card_ids_b.index(cid)])
                # Reassign if child score is close and child seems more specific
                if child_score >= 0.5 and child_score >= current_score * 0.85:
                    child_info = ch2_parent_of.get(child_title, {})
                    # Only reassign if target is more specific (narrower scope than current)
                    if child_info.get("section_id") == current_info.get("section_id", ""):
                        # Same section - prefer more specific subsection
                        old_section = current
                        card_section_map[cid] = {"section_title": child_title, "method": "bge_child", "score": child_score}
                        if old_section in section_cards and cid in section_cards[old_section]:
                            section_cards[old_section].remove(cid)
                        if child_title not in section_cards:
                            section_cards[child_title] = []
                        section_cards[child_title].append(cid)
                        reassigned += 1
                        break
    print(f"  BGE child-preference reassigned: {reassigned} cards")

    # Check key cards again
    for key_cid in ["v6_b04_N09", "v6_b03_N18"]:
        if key_cid in card_section_map:
            entry = card_section_map[key_cid]
            print(f"  {key_cid} -> {entry['section_title']} ({entry['method']}, score={entry['score']:.3f})")
        else:
            print(f"  {key_cid} -> STILL NOT FOUND")

# ── Save ────────────────────────────────────────────────────────────
output = {
    "card_to_section": card_section_map,
    "section_to_cards": section_cards
}
with open(os.path.join(OUT_DIR, "card_section_map.json"), "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# ── Acceptance checks ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("ACCEPTANCE CHECKS")
print("=" * 60)

# 2.1: v6_b04_N09 -> 削弱金融组织
v04 = card_section_map.get("v6_b04_N09", {})
check_2_1 = "削弱" in v04.get("section_title", "") or "金融" in v04.get("section_title", "")
print(f"2.1 v6_b04_N09 -> FI consequences: {check_2_1} ({v04.get('section_title', 'NOT FOUND')})")

# 2.2: v6_b03_N18 -> 税收损失
v03 = card_section_map.get("v6_b03_N18", {})
check_2_2 = "税收" in v03.get("section_title", "")
print(f"2.2 v6_b03_N18 -> tax loss: {check_2_2} ({v03.get('section_title', 'NOT FOUND')})")

# 2.3: Mount rate
total_sections = len(sections)
mounted = len([s for s in section_titles if section_cards.get(s)])
check_2_3 = mounted / max(total_sections, 1) >= 0.8
print(f"2.3 Mount rate: {mounted}/{total_sections} = {mounted/total_sections:.1%} (>=80%: {check_2_3})")

# 2.6: Option pre-validation for 2.1_19
print(f"\n2.6 Option pre-validation:")
options = {
    "A": "盈利业务的减少或损失",
    "B": "代理银行设施的增加",
    "C": "雇员人数减少",
    "D": "公司税的增加",
    "E": "调查费用和罚金的增加"
}

# BGE encode option texts vs section query texts
opt_texts = list(options.values())
opt_vecs = model.encode(opt_texts, normalize_embeddings=True)
opt_scores = opt_vecs @ query_vecs.T  # (5, n_sections)

for idx, (opt_label, opt_text) in enumerate(options.items()):
    row = opt_scores[idx]
    top3_idx = np.argsort(row)[::-1][:3]
    top3 = [(section_titles[i], float(row[i])) for i in top3_idx]
    print(f"  {opt_label} '{opt_text}':")
    for rank, (stitle, score) in enumerate(top3):
        marker = ""
        if opt_label in ["A", "E"] and ("削弱" in stitle or "金融" in stitle):
            marker = " <- EXPECTED"
        elif opt_label == "D" and "税收" in stitle:
            marker = " <- EXPECTED"
        elif opt_label == "C" and score < 0.5:
            marker = " <- EXPECTED LOW (no textbook support)"
        print(f"    {rank+1}. {stitle} ({score:.3f}){marker}")

# Check D -> 税收损失
d_scores = opt_scores[3]  # D is index 3
d_top = np.argsort(d_scores)[::-1][:3]
d_in_tax = any("税收" in section_titles[i] for i in d_top)
print(f"\n  D -> tax section in top-3: {d_in_tax}")

all_pass = check_2_1 and check_2_2 and check_2_3 and d_in_tax
print(f"\n  STEP 2 PASS: {all_pass}")
