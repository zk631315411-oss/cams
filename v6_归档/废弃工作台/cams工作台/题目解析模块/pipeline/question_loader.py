"""题库加载器：解析习题结构化提取 md → 统一题目格式。

输入：教材、答疑记录、习题与参考文献/习题/习题结构化提取/{section}_习题集.md
输出：[{id, section, number, stem, options, answer, explanation, knowledge_point}, ...]

md 格式（以 3.1_习题集.md 为例）::

    # 第三章 3.1 习题集

    共 44 题

    ## 第1题 题干文本
    ### 选项
    - A.选项A
    - B.选项B
    ### 答案
    答案:A
    ### 解析
    解析:具体知识点:
    知识点名称
    教材原文引用...
    选项分析:
    B选项错误...
    ---
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_RE_HEADING_SECTION = re.compile(
    r"^#\s*(?:第[一二三四五六七八九十]+章\s*)?([\d.]+)\s*习题(?:集)?", re.MULTILINE
)
_RE_QUESTION = re.compile(r"^##\s*第(\d+)题\s*(.*)", re.MULTILINE)
_RE_OPTION = re.compile(r"^-\s*([A-K])[\.、\)）]\s*(.+)", re.MULTILINE)
_RE_ANSWER = re.compile(r"答案\s*[:：]\s*([A-K,，、/;；\s]+)")
_RE_KNOWLEDGE_POINT = re.compile(r"具体知识点\s*[:：]\s*\n?(.+?)(?:\n|选项|解析|$)", re.DOTALL)


@dataclass
class Question:
    id: str
    section: str
    number: int
    stem: str
    options: dict[str, str] = field(default_factory=dict)
    answer: str = ""
    explanation: str = ""
    knowledge_point: str = ""
    source_file: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "section": self.section,
            "number": self.number,
            "stem": self.stem,
            "options": self.options,
            "answer": self.answer,
            "explanation": self.explanation,
            "knowledge_point": self.knowledge_point,
            "source_file": self.source_file,
        }


def _extract_knowledge_point(explanation: str) -> str:
    """从解析文本里提取「具体知识点:」后的标签。"""
    if not explanation:
        return ""
    m = _RE_KNOWLEDGE_POINT.search(explanation)
    if not m:
        return ""
    kp = m.group(1).strip()
    kp = re.sub(r"[。，；;]$", "", kp)
    if len(kp) > 80:
        kp = kp.split("\n")[0].strip()
    return kp[:100]


def _normalize_answer(raw: str) -> str:
    """答案归一化为 'A' 或 'A,B' 形式。"""
    if not raw:
        return ""
    labels = sorted(set(re.findall(r"[A-K]", raw.upper())))
    return ",".join(labels)


def parse_md_file(md_path: Path) -> list[Question]:
    """解析单个 {section}_习题集.md 文件。

    Returns
    -------
    list[Question]
    """
    text = md_path.read_text(encoding="utf-8")
    section_match = _RE_HEADING_SECTION.search(text)
    section = ""
    if section_match:
        section = section_match.group(1).strip()
    # 第6章主题文件标题（如"# 第六章 6.了解您的客户(KYC) 习题集"）会被正则提取成 "6."，
    # 不够区分各主题；此时用文件名兜底（6.了解您的客户(KYC)_习题集 → 6.了解您的客户(KYC)）
    if not section or section == "6.":
        section = _section_from_filename(md_path.stem)

    # 按 ## 第N题 切块
    blocks = re.split(r"(?=^##\s*第\d+题)", text, flags=re.MULTILINE)
    questions: list[Question] = []
    for block in blocks:
        qm = _RE_QUESTION.search(block)
        if not qm:
            continue
        number = int(qm.group(1))
        stem = qm.group(2).strip()
        if not stem:
            # 题干可能跨行，取首段
            stem_lines = [ln.strip() for ln in block.splitlines() if ln.strip() and not ln.startswith("#") and not ln.startswith("-")]
            stem = stem_lines[0] if stem_lines else ""

        options: dict[str, str] = {}
        for om in _RE_OPTION.finditer(block):
            label = om.group(1).strip()
            body = om.group(2).strip()
            if label not in options:
                options[label] = body

        answer = ""
        am = _RE_ANSWER.search(block)
        if am:
            answer = _normalize_answer(am.group(1))

        explanation = ""
        expl_m = re.search(r"###\s*解析\s*\n(.+?)(?:\n---|\Z)", block, re.DOTALL)
        if expl_m:
            explanation = expl_m.group(1).strip()

        knowledge_point = _extract_knowledge_point(explanation)
        if not knowledge_point:
            knowledge_point = stem[:60]

        questions.append(Question(
            id=f"{section}_{number}",
            section=section,
            number=number,
            stem=stem,
            options=options,
            answer=answer,
            explanation=explanation,
            knowledge_point=knowledge_point,
            source_file=md_path.name,
        ))
    return questions


def _section_from_filename(stem: str) -> str:
    """从文件名提取 section 前缀：3.1_习题集 → 3.1；2_1_习题 → 2.1；6.了解您的客户(KYC)_习题集 → 6.了解您的客户(KYC)。"""
    # 先尝试 数字_数字 格式（2_1_习题 → 2.1）
    m2 = re.match(r"(\d+)_(\d+)", stem)
    if m2:
        return f"{m2.group(1)}.{m2.group(2)}"
    # 第6章主题文件名：6.了解您的客户(KYC)_习题集 → 6.了解您的客户(KYC)
    # 保留点号后的主题名，去掉 _习题集 后缀
    if stem.startswith("6."):
        # 取 _习题集 之前的部分
        return stem.split("_习题")[0].strip()
    # 再尝试 点号分隔（3.1_习题集 → 3.1）
    m = re.match(r"([\d.]+)", stem)
    if m:
        return m.group(1).strip()
    return stem


def load_questions(
    md_dir: Path | list[Path],
    sections: list[str] | None = None,
) -> list[Question]:
    """批量加载习题结构化提取 md。

    Parameters
    ----------
    md_dir : Path | list[Path]
        习题目录，可传单个或多个（同时扫描"习题结构化"和"习题结构化提取"）。
    sections : list[str] | None
        指定小节前缀，如 ["2.1", "3.1"]。None 表示加载全部。

    Returns
    -------
    list[Question]
    """
    md_dirs = [Path(d) for d in (md_dir if isinstance(md_dir, list) else [md_dir])]
    for d in md_dirs:
        if not d.exists():
            raise FileNotFoundError(d)

    all_questions: list[Question] = []
    seen_files: set[Path] = set()
    for md_dir in md_dirs:
        for md_path in sorted(md_dir.glob("*_习题*.md")):
            # 跳过早期 regex 实验版（2.1_习题_regex.md），用正式版 2_1_习题.md
            if "_regex" in md_path.stem:
                continue
            if md_path in seen_files:
                continue
            seen_files.add(md_path)
            section_from_name = _section_from_filename(md_path.stem)
            if sections and not any(section_from_name.startswith(s) for s in sections):
                continue
            questions = parse_md_file(md_path)
            all_questions.extend(questions)
            print(f"[question_loader] {md_path.name}: {len(questions)} 题")
    return all_questions


def questions_to_questions_json(questions: list[Question]) -> dict[str, Any]:
    """转成与旧 questions.json 兼容的格式，方便复用旧脚本。"""
    return {
        "total": len(questions),
        "questions": [q.to_dict() for q in questions],
    }
