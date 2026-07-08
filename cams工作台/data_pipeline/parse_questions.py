"""
Parse Ch2 question bank docx → data/questions.json
Uses python-docx for clean paragraph extraction.
"""
import json, os, re
from docx import Document

DOC_DIR = r"d:\守正公司工作区\cams考试\教材、答疑记录、习题与参考文献\习题"
OUT_DIR = r"d:\守正公司工作区\cams考试\cams工作台\data"

def parse_questions(lines, section):
    questions = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.match(r"^(\d+)\.\s*(.+)", line)
        if not m:
            i += 1
            continue

        qnum = m.group(1)
        stem = m.group(2).strip()
        i += 1

        # Options — up to A-G
        options = {}
        while i < len(lines) and re.match(r"^([A-G])\.", lines[i].strip()):
            om = re.match(r"^([A-G])\.\s*(.+)", lines[i].strip())
            if om:
                options[om.group(1)] = om.group(2).strip()
            i += 1

        # Answer
        answer = ""
        if i < len(lines):
            am = re.match(r"^答案\s*[:：]\s*(.+?)\s*$", lines[i].strip())
            if am:
                raw = am.group(1).strip()
                if re.match(r"^[A-G](\s+[A-G])*$", raw):
                    answer = ",".join(raw.split())
                else:
                    answer = raw
                i += 1

        # Explanation
        expl_lines = []
        while i < len(lines):
            if re.match(r"^\d+\.", lines[i].strip()) and not re.match(r"^[A-G]\.", lines[i].strip()):
                break
            expl_lines.append(lines[i].strip())
            i += 1

        explanation = "\n".join(expl_lines).strip()

        # Fallback: try to extract missing options/answers from explanation
        if (not options or not answer) and explanation:
            # Look for A.xxx B.xxx patterns in first 500 chars
            opt_text = explanation[:500]
            for om in re.finditer(r"([A-G])\.\s*(.+?)(?=\s*[A-G]\.\s|\s*答案|$)", opt_text):
                key = om.group(1)
                if key not in options:
                    options[key] = om.group(2).strip()[:200]
            # Also check for answer in explanation
            am = re.search(r"答案\s*[:：]\s*(.+)", opt_text)
            if am and not answer:
                raw = am.group(1).strip()
                if re.match(r"^[A-G](\s+[A-G])*$", raw):
                    answer = ",".join(raw.split())
                else:
                    answer = raw

        questions.append({
            "id": f"{section}_{qnum}",
            "section": section,
            "number": int(qnum),
            "stem": stem,
            "options": options,
            "answer": answer,
            "explanation": explanation,
        })

    return questions

all_questions = []
os.makedirs(OUT_DIR, exist_ok=True)

for fname in sorted(os.listdir(DOC_DIR)):
    if not fname.endswith(".docx"):
        continue
    section = fname.replace(".docx", "")
    path = os.path.join(DOC_DIR, fname)
    doc = Document(path)
    lines = [p.text for p in doc.paragraphs]
    questions = parse_questions(lines, section)
    all_questions.extend(questions)
    print(f"{fname}: {len(questions)} questions")

# Save
with open(os.path.join(OUT_DIR, "questions.json"), "w", encoding="utf-8") as f:
    json.dump({"total": len(all_questions), "questions": all_questions}, f, ensure_ascii=False, indent=2)

no_ans = sum(1 for q in all_questions if not q["answer"])
no_opt = sum(1 for q in all_questions if not q["options"])
print(f"\nTotal: {len(all_questions)} | No answer: {no_ans} | No options: {no_opt}")
