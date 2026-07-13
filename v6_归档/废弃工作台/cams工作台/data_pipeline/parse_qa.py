"""
Parse Ch2 QA record PDFs → data/qa.json
No truncation, complete fields.
"""
import json, os, re
import fitz

QA_DIR = r"d:\守正公司工作区\cams考试\教材、答疑记录、习题与参考文献\答疑记录"
OUT_DIR = r"d:\守正公司工作区\cams考试\cams工作台\data"
os.makedirs(OUT_DIR, exist_ok=True)

ANSWER_PREFIXES = [
    "答案", "正确答案", "正确答案是", "正确答案为", "正确答案应为",
    "答案是", "正确选项", "答", "最终答案", "最终答案是", "最终答案为",
]

def parse_pdf(path):
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()

def extract_question(lines):
    """Collect lines from start until first option/answer line."""
    q_lines = []
    for line in lines:
        ls = line.strip()
        if not ls:
            if q_lines:  # empty line after content → stop
                break
            continue
        # Stop at options: A.xxx / A xxx
        if re.match(r"^[A-E][\.\s]", ls):
            break
        # Stop at answer line
        for pf in ANSWER_PREFIXES:
            if ls.startswith(pf):
                break
        else:
            q_lines.append(ls)
            continue
        break
    return " ".join(q_lines).strip()

def extract_answer(lines):
    """Extract answer letter(s) from any known format."""
    for i, line in enumerate(lines):
        ls = line.strip()
        for pf in ANSWER_PREFIXES:
            # "答案是：A" or "答案是 C。" or "正确答案应为 B"
            m = re.match(rf"^{pf}\s*[：:]\s*(.+)(?:\s*$)", ls)
            if m:
                letters = re.findall(r"[A-G]", m.group(1))
                if letters:
                    return ",".join(letters)
                return m.group(1).strip()
            # "最终答案A." or "答案是 C。" (no colon)
            m2 = re.match(rf"^{pf}\s*([A-G])", ls)
            if m2:
                return m2.group(1)
            # "最终答案：" on its own → check next lines
            if re.match(rf"^{pf}\s*[：:]\s*$", ls):
                ans = []
                for j in range(i+1, min(i+10, len(lines))):
                    om = re.match(r"^([A-G])[\.\s、]", lines[j].strip())
                    if om:
                        ans.append(om.group(1))
                    elif ans:
                        break
                if ans:
                    return ",".join(ans)
    return ""

def extract_core_point(lines):
    """Extract text between core analysis marker and option analysis."""
    in_core = False
    core = []
    for line in lines:
        if "核心分析思路" in line or "核心思路" in line:
            in_core = True
            continue
        if in_core and ("选项分析" in line or "最终答案" in line):
            break
        if in_core and line.strip():
            core.append(line.strip())
    return "\n".join(core)

def parse_qa(text):
    lines = text.split("\n")
    return {
        "question": extract_question(lines),
        "answer": extract_answer(lines),
        "core_point": extract_core_point(lines),
        "full_text": text,
    }

all_qa = []
problems = []

for fname in sorted(os.listdir(QA_DIR)):
    if not fname.endswith(".pdf"):
        continue
    path = os.path.join(QA_DIR, fname)
    text = parse_pdf(path)
    qa = parse_qa(text)

    sec_match = re.search(r"(\d+)\.(\d+)", fname)
    section = f"{sec_match.group(1)}.{sec_match.group(2)}" if sec_match else "unknown"

    # Clean formatting noise from AI-generated PDFs
    for field in ["question", "core_point", "full_text"]:
        txt = qa[field]
        # Remove "Plain Text" labels
        txt = re.sub(r'\bPlain Text\b', '', txt)
        # Remove standalone numbers (table row markers)
        txt = re.sub(r'\n\d+\n', '\n', txt)
        # Collapse 3+ consecutive newlines
        txt = re.sub(r'\n{3,}', '\n\n', txt)
        qa[field] = txt.strip()

    qa["id"] = f"QA_{fname[:30].replace(' ','_')}"
    qa["source_file"] = fname
    qa["section"] = section

    if not qa["answer"]:
        problems.append(fname)

    # Normalize answer letters to uppercase (single or comma-separated)
    ans = qa["answer"]
    if re.match(r"^[a-g,\s]+$", ans):
        qa["answer"] = ans.upper()

    all_qa.append(qa)

with open(os.path.join(OUT_DIR, "qa.json"), "w", encoding="utf-8") as f:
    json.dump({"total": len(all_qa), "records": all_qa, "problems": len(problems)},
              f, ensure_ascii=False, indent=2)

print(f"Parsed {len(all_qa)} QA records | Problems: {len(problems)}")
for p in problems[:5]:
    print(f"  {p[:60]}")
