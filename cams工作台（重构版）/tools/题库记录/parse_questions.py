"""
从习题结构化 MD 文件生成 data/source/questions.json（全教材 720 题）。

输入：教材、答疑记录、习题与参考文献/习题/习题结构化/*_习题*.md
输出：data/source/questions.json
"""
import json
import re
from pathlib import Path

# --- 路径配置 ---
_WORKSPACE = Path(__file__).resolve().parents[2]
_MD_DIR = Path(r"d:\守正公司工作区\cams考试\教材、答疑记录、习题与参考文献\习题\习题结构化")
_OUT = _WORKSPACE / "data" / "source" / "questions.json"

_RE_HEADING_SECTION = re.compile(
    r"^#\s*(?:第[一二三四五六七八九十]+章\s*)?([\d.]+)\s*习题(?:集)?", re.MULTILINE
)
_RE_QUESTION = re.compile(r"^##\s*第(\d+)题\s*(.*)", re.MULTILINE)
_RE_OPTION = re.compile(r"^-\s*([A-K])[\.、\)）]\s*(.+)", re.MULTILINE)
_RE_ANSWER = re.compile(r"答案\s*[:：]\s*(.+?)(?:\n|---|$)", re.MULTILINE)


def _section_from_filename(stem: str) -> str:
    """从文件名提取 section：3.1_习题集 → 3.1；2_1_习题 → 2.1；6.了解您的客户(KYC)_习题集 → 6.了解您的客户(KYC)"""
    m2 = re.match(r"(\d+)_(\d+)", stem)
    if m2:
        return f"{m2.group(1)}.{m2.group(2)}"
    if stem.startswith("6."):
        return stem.split("_习题")[0].strip()
    m = re.match(r"([\d.]+)", stem)
    if m:
        return m.group(1).strip()
    return stem


def _normalize_answer(raw: str) -> str:
    """答案归一化为 'A' 或 'A,B' 形式。判断题（正确/错误）保留中文"""
    if not raw:
        return ""
    raw = raw.strip()
    # 判断题
    if raw in ("正确", "错误"):
        return raw
    labels = sorted(set(re.findall(r"[A-K]", raw.upper())))
    return ",".join(labels)


def parse_md_file(md_path: Path) -> list[dict]:
    """解析单个习题 MD，返回题目列表"""
    text = md_path.read_text(encoding="utf-8")

    # 从一级标题提取 section
    section_match = _RE_HEADING_SECTION.search(text)
    section = ""
    if section_match:
        section = section_match.group(1).strip()
    if not section or section == "6.":
        section = _section_from_filename(md_path.stem)

    # 按 ## 第N题 切块
    blocks = re.split(r"(?=^##\s*第\d+题)", text, flags=re.MULTILINE)
    questions: list[dict] = []

    for block in blocks:
        qm = _RE_QUESTION.search(block)
        if not qm:
            continue
        number = int(qm.group(1))
        stem = qm.group(2).strip()
        if not stem:
            stem_lines = [
                ln.strip() for ln in block.splitlines()
                if ln.strip() and not ln.startswith("#") and not ln.startswith("-")
            ]
            stem = stem_lines[0] if stem_lines else ""

        # 选项
        options: dict[str, str] = {}
        for om in _RE_OPTION.finditer(block):
            label = om.group(1).strip()
            body = om.group(2).strip()
            if label not in options:
                options[label] = body

        # 答案
        answer = ""
        am = _RE_ANSWER.search(block)
        if am:
            answer = _normalize_answer(am.group(1))

        # 解析
        explanation = ""
        expl_m = re.search(r"###\s*解析\s*\n(.+?)(?:\n---|\Z)", block, re.DOTALL)
        if expl_m:
            explanation = expl_m.group(1).strip()

        questions.append({
            "id": f"{section}_{number}",
            "section": section,
            "number": number,
            "stem": stem,
            "options": options,
            "answer": answer,
            "explanation": explanation,
        })

    # 过滤伪题目：没有真实选项、没有真实答案的非题块
    questions = [q for q in questions if len(q["options"]) >= 2 or q["answer"]]
    return questions


# ---- 主流程 ----
all_questions: list[dict] = []

for md_path in sorted(_MD_DIR.glob("*_习题*.md")):
    if "_regex" in md_path.stem:       # 跳过 regex 实验版
        continue
    questions = parse_md_file(md_path)
    all_questions.extend(questions)
    print(f"{md_path.name}: {len(questions)} 题")

# 输出
_OUT.parent.mkdir(parents=True, exist_ok=True)
_OUT.write_text(
    json.dumps({"total": len(all_questions), "questions": all_questions}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

no_ans = sum(1 for q in all_questions if not q["answer"])
no_opt = sum(1 for q in all_questions if not q["options"])
no_exp = sum(1 for q in all_questions if not q["explanation"])
print(f"\n总计: {len(all_questions)} 题 | 无答案: {no_ans} | 无选项: {no_opt} | 无解析: {no_exp}")
print(f"输出: {_OUT}")
