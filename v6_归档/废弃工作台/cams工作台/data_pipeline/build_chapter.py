"""
Step 3: Build chapter JSON with card annotations (v2 — MinerU markdown)
"""
import json, os, re, random

OUT = r"d:\守正公司工作区\cams考试\cams工作台\data"
POOLS = r"d:\守正公司工作区\cams考试\核心数据\pools"
os.makedirs(os.path.join(OUT, "chapters"), exist_ok=True)

# Load
src = r"D:\守正公司工作区\cams考试\CAMS中文版教材-V6.51.md"
with open(src, "r", encoding="utf-8") as f:
    text = f.read()
cards = json.load(open(os.path.join(POOLS, "v6_cards.json"), "r", encoding="utf-8"))
qcm = json.load(open(os.path.join(OUT, "question_card_map.json"), "r", encoding="utf-8"))["mappings"]
qa_bindings = json.load(open(os.path.join(OUT, "qa_bindings.json"), "r", encoding="utf-8"))["bindings"]

# ── 1. Parse TOC to get Ch2 hierarchy ──
# TOC entries with "# " prefix are major sections; those without are subsections.
ch2_heading = "# 洗钱和恐怖融资活动的风险及方法"
toc_ch2_start = text.find(ch2_heading + "..")
toc_ch3_start = text.find("# 国际反洗钱", toc_ch2_start + 10)
toc_text = text[toc_ch2_start:toc_ch3_start]

# Parse TOC lines: extract headings, determine which are major sections
toc_major = []  # list of major section titles
toc_sub_to_major = {}  # subsection_title -> major_section_title
current_major = "概述"  # first major section

for line in toc_text.split("\n"):
    line = line.strip()
    if not line:
        continue
    # Remove trailing page numbers like ".. 2", ". .14", "... .. 30", ".... .80"
    cleaned = re.sub(r"[\.\s]+\d+$", "", line).strip()
    if not cleaned:
        continue
    # Skip chapter heading itself
    if cleaned == ch2_heading:
        continue

    if line.startswith("# "):
        # Major section — strip "# " prefix
        title = cleaned[2:] if cleaned.startswith("# ") else cleaned
        toc_major.append(title)
        current_major = title
    else:
        # Subsection
        toc_sub_to_major[cleaned] = current_major

print(f"TOC major sections: {len(toc_major)}")
for m in toc_major:
    sub_count = sum(1 for s, p in toc_sub_to_major.items() if p == m)
    print(f"  [{m}] -> {sub_count} subs")

# ── 2. Find Ch2 body boundaries ──
body_ch2_start = text.find(ch2_heading + "\n", toc_ch3_start)
if body_ch2_start < 0:
    body_ch2_start = text.find(ch2_heading, len(text) // 3)

next_ch = text.find("\n# 国际反洗钱", body_ch2_start)
if next_ch < 0:
    next_ch = len(text)
ch2_text = text[body_ch2_start:next_ch]
print(f"\nCh2 body: {len(ch2_text)} chars")

# ── 3. Split Ch2 body into sections by # headings ──
sections = []
current_title = ""
current_lines = []

for line in ch2_text.split("\n"):
    m = re.match(r"^# (.+)", line)
    if m:
        if current_lines:
            sections.append({"title": current_title, "text": "\n".join(current_lines)})
        current_title = m.group(1).strip()
        current_lines = []
    else:
        current_lines.append(line)
if current_lines:
    sections.append({"title": current_title, "text": "\n".join(current_lines)})

sections = [s for s in sections if s["text"].strip()]

# ── 4. Group sections by TOC major sections ──
def normalize_title(t):
    """Normalize heading for matching against TOC entries"""
    t = t.strip()
    t = re.sub(r"\s+", "", t)
    return t

# Build normalized lookup for TOC entries
norm_major = {normalize_title(m): m for m in toc_major}
norm_sub_to_major = {}
for sub, major in toc_sub_to_major.items():
    norm_sub_to_major[normalize_title(sub)] = major

grouped = {}  # major_title -> [sections]
current_major_title = toc_major[0] if toc_major else "概述"
unmatched = []

for sec in sections:
    n = normalize_title(sec["title"])
    if n in norm_major:
        current_major_title = norm_major[n]
    else:
        # Check if it maps to a TOC subsection
        if n in norm_sub_to_major:
            current_major_title = norm_sub_to_major[n]

    if current_major_title not in grouped:
        grouped[current_major_title] = []
    grouped[current_major_title].append(sec)

print(f"\nGrouped into {len(grouped)} major sections:")
for major, subs in grouped.items():
    print(f"  {major}: {len(subs)} subsections")

# ── 5. Match cards to paragraphs ──
card_by_id = {c["card_id"]: c for c in cards}

highlight_cards = set()
for qid, v in qcm.items():
    for cid in v.get("matched_card_ids", []):
        highlight_cards.add(cid)
for b in qa_bindings:
    for cid in b.get("inherited_card_ids", []):
        highlight_cards.add(cid)
print(f"\nHighlight cards: {len(highlight_cards)}/{len(cards)}")

def normalize(s):
    s = re.sub(r'\s+', '', s)
    s = re.sub(r'[^一-鿿a-zA-Z0-9]', '', s)
    return s

def fuzzy_match(norm_cit, norm_para):
    """Try to match a citation in paragraph text with tolerance for artifacts.
    Old card citations may have prefix/suffix artifacts or minor character differences
    vs. the clean MinerU text."""
    if len(norm_cit) < 4:
        return False
    # Try trimming 0-5 chars from start, 0-4 from end
    for trim_l in range(0, 6):
        max_trim_r = min(5, len(norm_cit) - trim_l - 4)
        for trim_r in range(0, max_trim_r):
            trimmed = norm_cit[trim_l:len(norm_cit)-trim_r] if trim_r > 0 else norm_cit[trim_l:]
            if len(trimmed) >= 4 and trimmed in norm_para:
                return True
    return False

def match_cards_to_paragraph(para_text):
    norm_para = normalize(para_text)
    matched = []
    highlight = []
    for c in cards:
        norm_cit = normalize(c["citation"])
        if len(norm_cit) < 4:
            continue
        ok = norm_cit in norm_para
        if not ok:
            ok = fuzzy_match(norm_cit, norm_para)
        if ok:
            matched.append(c["card_id"])
            if c["card_id"] in highlight_cards:
                highlight.append(c["card_id"])
    return matched, highlight

output_sections = []
total_paras = 0
paras_with_cards = 0
total_matched = set()
total_highlight = set()

for parent_idx, major_title in enumerate(toc_major):
    if major_title not in grouped:
        continue
    subs = grouped[major_title]
    parent_out = {
        "section_id": f"2.{parent_idx + 1}",
        "section_title": major_title,
        "subsections": [],
    }

    for sub in subs:
        paras = [p.strip() for p in sub["text"].split("\n\n") if p.strip()]
        all_paras = []
        for p in paras:
            if len(p) > 500:
                all_paras.extend([s.strip() for s in p.split("\n") if s.strip()])
            else:
                all_paras.append(p)

        sec_paras = []
        for p in all_paras:
            if len(p) < 20:
                continue
            matched_cids, highlight_cids = match_cards_to_paragraph(p)
            sec_paras.append({
                "text": p,
                "card_ids": matched_cids,
                "highlight_card_ids": highlight_cids,
            })
            total_paras += 1
            if matched_cids:
                paras_with_cards += 1
                total_matched.update(matched_cids)
                total_highlight.update(highlight_cids)

        parent_out["subsections"].append({
            "title": sub["title"],
            "paragraphs": sec_paras,
        })

    output_sections.append(parent_out)

print(f"\nParent sections: {len(output_sections)}")
for p in output_sections:
    print(f"  {p['section_id']} {p['section_title'][:40]} ({len(p['subsections'])} subs, {sum(1 for sub in p['subsections'] for pp in sub['paragraphs'] if pp['highlight_card_ids'])} highlighted paras)")

print(f"\nParagraphs: {total_paras} ({paras_with_cards} with cards)")
print(f"Cards matched: {len(total_matched)}/{len(cards)}")
print(f"Cards highlighted: {len(total_highlight)}")

# Save
output = {
    "chapter": "洗钱和恐怖融资活动的风险及方法",
    "sections": output_sections,
    "stats": {
        "total_paragraphs": total_paras,
        "paragraphs_with_cards": paras_with_cards,
        "cards_matched": len(total_matched),
        "cards_highlighted": len(total_highlight),
    }
}
with open(os.path.join(OUT, "chapters", "ch2.json"), "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print("Saved data/chapters/ch2.json")

# ── Review sample ──
random.seed(301)
highlight_paras = []
for parent in output_sections:
    for sub in parent["subsections"]:
        for p in sub["paragraphs"]:
            if p["highlight_card_ids"]:
                highlight_paras.append((parent["section_title"] + " / " + sub["title"], p))

samples = random.sample(highlight_paras, min(10, len(highlight_paras)))
with open(os.path.join(OUT, "step3_review.txt"), "w", encoding="utf-8") as f:
    for i, (sec_title, p) in enumerate(samples):
        f.write(f"===== [{i+1}] {sec_title} =====\n\n")
        f.write(f"原文:\n{p['text'][:300]}\n\n")
        f.write(f"关联卡片: {len(p['card_ids'])} 张, 高亮: {len(p['highlight_card_ids'])} 张\n")
        for cid in p["highlight_card_ids"][:5]:
            c = card_by_id.get(cid, {})
            f.write(f"  [{cid}] {c.get('knowledge', '')[:100]}\n")
            f.write(f"        citation: {c.get('citation', '')[:100]}\n")
        f.write("\n")
print("Saved step3_review.txt")
