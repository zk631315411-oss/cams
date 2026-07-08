"""
Parse structured QA Markdown files -> data/source/qa.json
Reads 答疑记录结构化/*.md, outputs clean structured JSON.
"""
import json
import os
import re
from pathlib import Path

MD_DIR = Path(r"D:\守正公司工作区\cams考试\教材、答疑记录、习题与参考文献\答疑记录\答疑记录结构化")
OUT_DIR = Path(r"D:\守正公司工作区\cams考试\cams工作台（重构版）\data\source")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _extract_section(heading: str, filename: str) -> str:
    """Extract section like '2.1' from H1 heading or filename."""
    m = re.search(r"(\d+)\.(\d+)", heading)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    m = re.search(r"(\d+)\.(\d+)", filename)
    if m:
        return f"{m.group(1)}.{m.group(2)}"
    # fallback: extract chapter number only (e.g. "第二章" -> "2", "第4章" -> "4")
    ch = re.search(r"第\s*([一二三四五六七八九十\d]+)\s*章", heading)
    if ch:
        num = ch.group(1)
        digits = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6"}
        d = digits.get(num, num)
        return f"{d}.0"
    return "unknown"


def _split_sections(text: str) -> dict[str, str]:
    """Split markdown body into named sections by ## headers."""
    sections: dict[str, str] = {}
    parts = re.split(r"\n(?=## )", text)
    for part in parts:
        m = re.match(r"##\s+(.+)", part)
        if m:
            key = m.group(1).strip()
            # Remove the header line itself, keep the body
            body = re.sub(r"^##\s+.+\n", "", part).strip()
            sections[key] = body
    return sections


def parse_md(filepath: Path) -> dict:
    """Parse a single structured QA markdown file."""
    text = filepath.read_text(encoding="utf-8")

    # Extract H1 heading (chapter + title)
    h1 = ""
    m = re.match(r"#\s+(.+)", text)
    if m:
        h1 = m.group(1).strip()

    # Remove H1, keep body
    body = re.sub(r"^#\s+.+\n", "", text, count=1).strip()

    secs = _split_sections(body)

    question = secs.get("题目", "")
    answer = secs.get("答案", "").strip()
    options = secs.get("选项", "")
    student_q = secs.get("学生提出的问题", "")
    teacher_a = secs.get("教研的回答", "")

    # Normalize answer: extract uppercase letters
    answer_letters = re.findall(r"[A-G]", answer.upper()) if answer else []
    answer = ",".join(answer_letters) if answer_letters else answer

    section = _extract_section(h1, filepath.name)
    qid = re.sub(r"[^\w一-鿿]+", "_", filepath.stem)[:40]

    return {
        "id": qid,
        "section": section,
        "question": question,
        "options": _parse_options(options),
        "answer": answer,
        "student_question": student_q,
        "teacher_answer": teacher_a,
        "source_file": filepath.name,
    }


def _parse_options(text: str) -> dict[str, str]:
    """Parse option lines like '- A. xxx' or '- A xxx' into {A: xxx}."""
    opts: dict[str, str] = {}
    for line in text.split("\n"):
        line = line.strip()
        m = re.match(r"-?\s*([A-E])[\.\、\)）\s]+(.+)", line)
        if m:
            opts[m.group(1)] = m.group(2).strip()
    return opts


def main() -> None:
    all_qa: list[dict] = []
    problems: list[str] = []

    for fname in sorted(os.listdir(MD_DIR)):
        if not fname.endswith(".md"):
            continue
        filepath = MD_DIR / fname
        qa = parse_md(filepath)

        if not qa["answer"]:
            problems.append(fname)

        all_qa.append(qa)

    output_path = OUT_DIR / "qa.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "total": len(all_qa),
                "records": all_qa,
                "problems": len(problems),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"Parsed {len(all_qa)} QA records | Problems: {len(problems)}")
    if problems:
        for p in problems[:10]:
            print(f"  {p[:60]}")


if __name__ == "__main__":
    main()
