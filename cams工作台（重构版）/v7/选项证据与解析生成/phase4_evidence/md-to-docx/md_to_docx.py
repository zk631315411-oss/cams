# -*- coding: utf-8 -*-
"""
将润色后的小节 md 转为标准试卷 DOCX 格式。

单文件：
    python md_to_docx.py -i sections/p1-ch1-h2.md -o sections/p1-ch1-h2.docx

批量：
    python md_to_docx.py --batch sections/
"""

import argparse
import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_LINE_SPACING
except ImportError:
    print("错误：缺少 python-docx，请先安装：pip install python-docx")
    sys.exit(1)

# <sup>PXXX</sup> 和 **bold** 正则
_SUP_RE = re.compile(r"<sup>P(\d+)</sup>|（书内第(\d+)页）|（P(\d+)）")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")

# 试卷名称映射：p1-ch1-h2 → CAMS CH01
_TITLE_RE = re.compile(r"p(\d+)-ch(\d+)-h(\d+)")


def section_to_title(filename: str) -> str:
    """从文件名提取试卷标题，如 p1-ch1-h2.md → CAMS CH01。"""
    m = _TITLE_RE.search(filename)
    if not m:
        return "CAMS"
    return f"CAMS CH{m.group(2).zfill(2)}"


def _set_run_bg(run, color: str):
    """给 run 设置文字底色。"""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn as _qn
    shd = OxmlElement("w:shd")
    shd.set(_qn("w:fill"), color)
    shd.set(_qn("w:val"), "clear")
    run._element.get_or_add_rPr().append(shd)


def add_styled_paragraph(doc, segments, indent_cm=0, space_after=2):
    """添加段落，segments 为 [(text, bold, superscript), ...]。"""
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_after = Pt(space_after)
    if indent_cm:
        p.paragraph_format.first_line_indent = Cm(indent_cm)
    for text, bold, is_sup in segments:
        run = p.add_run(text)
        if bold:
            run.font.bold = True
        if is_sup:
            run.font.superscript = True
            run.font.size = Pt(7.5)
    return p


def add_section_header(doc, label: str):
    """添加蓝色文字底色的解析小节标题，如「考点」「核心解析」。"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(label)
    run.font.bold = True
    run.font.size = Pt(10.5)
    _set_run_bg(run, "D6E4F0")
    return p


def parse_inline(text: str) -> list[tuple[str, bool, bool]]:
    """解析行内 <sup> 和 **bold**，返回 [(text, bold, sup), ...] 列表。"""
    # 合并两个正则，按出现顺序解析
    tokens = []
    pos = 0
    while pos < len(text):
        sup_m = _SUP_RE.search(text, pos)
        bold_m = _BOLD_RE.search(text, pos)

        next_m = None
        tag_type = None
        if sup_m and (not bold_m or sup_m.start() <= bold_m.start()):
            next_m = sup_m
            tag_type = "sup"
        elif bold_m:
            next_m = bold_m
            tag_type = "bold"

        if not next_m:
            tokens.append((text[pos:], False, False))
            break

        if next_m.start() > pos:
            tokens.append((text[pos:next_m.start()], False, False))

        if tag_type == "sup":
            page = next_m.group(1) or next_m.group(2) or next_m.group(3)
            tokens.append((f"P{page}", False, True))
        else:
            tokens.append((next_m.group(1), True, False))

        pos = next_m.end()

    return tokens


def render_section_label(doc, label: str):
    """渲染加粗的段落标签，如「考点：」「核心解析：」等。"""
    add_styled_paragraph(doc, [(label, True, False)], space_after=0)


def render_body_text(doc, text: str):
    """渲染正文段落，支持行内上标和加粗。"""
    text = text.strip()
    if not text:
        return
    segments = parse_inline(text)
    add_styled_paragraph(doc, segments, indent_cm=0.74)


def convert_md_to_docx(input_path: Path, output_path: Path) -> tuple[int, int]:
    content = input_path.read_text(encoding="utf-8")
    # 中文弯引号替换为直引号
    content = content.replace("「", "“").replace("」", "”")
    title = section_to_title(input_path.name)

    doc = Document()
    # 页面设置：参考样式
    for sec in doc.sections:
        sec.top_margin = Cm(2.54)
        sec.bottom_margin = Cm(2.54)
        sec.left_margin = Cm(3.17)
        sec.right_margin = Cm(3.17)

    # 试卷名称
    add_styled_paragraph(doc, [(f"试卷名称:{title}", False, False)], space_after=12)

    # 一、单项选择题
    add_styled_paragraph(doc, [("一、单项选择题", False, False)], space_after=8)

    # 切分题目：以 --- 为分隔符
    blocks = content.split("\n\n---\n\n")
    # 第一块是 section header + 第一题，去掉 section header 得到第一题
    first_block = blocks[0].strip()
    header_end = first_block.find("\n教材章节：")
    if header_end > 0:
        first_q = first_block[header_end:].strip()
    else:
        first_q = ""
    # 后续各题
    question_blocks = [first_q] if first_q else []
    question_blocks += [b.strip() for b in blocks[1:] if b.strip()]

    total = 0
    for qi, block in enumerate(question_blocks, 1):
        q = _parse_question(block)
        if not q:
            continue
        total += 1

        # 题目
        add_styled_paragraph(doc, [(f"{qi}. {q['stem']} ( )", False, False)], space_after=2)

        # 选项 A-D
        for opt in q["options"]:
            add_styled_paragraph(doc, [(opt, False, False)], indent_cm=0.5, space_after=1)

        # 答案
        add_styled_paragraph(doc, [(f"答案:{q['answer']}", False, False)], space_after=2)

        # 解析
        add_styled_paragraph(doc, [("解析：", False, False)], space_after=2)
        # 解析段落标签 → 蓝底标题 + 内容分行
        _LABEL_MAP = {
            "考点：": "考点", "核心解析：": "核心解析",
            "易错提醒：": "易错提醒", "教材原句：": "教材原句",
        }
        _ERROR_LABEL_RE = re.compile(r"^([A-E])项(\S+)：")
        for line in q.get("analysis_text", "").split("\n"):
            line = line.strip()
            if not line:
                continue
            em = _ERROR_LABEL_RE.match(line)
            if em:
                add_section_header(doc, f"{em.group(1)}项{em.group(2)}")
                rest = line[len(f"{em.group(1)}项{em.group(2)}："):]
                render_body_text(doc, rest)
                continue
            matched = False
            for lbl, title in _LABEL_MAP.items():
                if line.startswith(lbl):
                    add_section_header(doc, title)
                    rest = line[len(lbl):]
                    if rest:
                        render_body_text(doc, rest)
                    matched = True
                    break
            if not matched:
                render_body_text(doc, line)

        if qi < len(question_blocks):
            add_styled_paragraph(doc, [("", False, False)], space_after=6)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    return total, 0


def _parse_question(block: str) -> dict | None:
    """解析单个题块，提取题干、选项、答案、解析。"""
    lines = block.strip().split("\n")
    result = {"stem": "", "options": [], "answer": "", "analysis": {}}
    in_options = False
    opt_buf = None
    in_analysis = False
    current_sec = None
    sec_lines: list[str] = []

    for line in lines:
        s = line.strip()

        if s.startswith("教材章节："):
            continue
        if s.startswith("## "):
            result["id"] = s[3:].strip()
            continue
        if s.startswith("题型：") or s.startswith("English:"):
            continue
        elif s.startswith("题干：") or s.startswith("题目："):
            result["stem"] = s[3:].strip()
        elif s == "选项：":
            in_options = True
        elif in_options and s.startswith("- "):
            if opt_buf:
                result["options"].append(opt_buf)
            opt_buf = s[2:].strip()
        elif in_options and s.startswith("English:") and opt_buf:
            continue
        elif s.startswith("答案："):
            in_options = False
            if opt_buf:
                result["options"].append(opt_buf)
                opt_buf = None
            result["answer"] = s[3:].strip()
        elif s == "解析：":
            in_analysis = True
            in_options = False
        elif in_analysis and s:
            if s == "---":
                break
            sec_lines.append(s)

    result["analysis_text"] = "\n".join(sec_lines)
    return result if result["stem"] else None


def main():
    parser = argparse.ArgumentParser(description="将润色后的小节 md 转为标准试卷 DOCX")
    parser.add_argument("-i", "--input", default="")
    parser.add_argument("-o", "--output", default="")
    parser.add_argument("--batch", default="", help="批量模式：指定目录，转换所有 p*-ch*-h*.md")
    args = parser.parse_args()

    if args.batch:
        batch_dir = Path(args.batch)
        if not batch_dir.is_dir():
            print(f"错误：目录不存在：{batch_dir}")
            sys.exit(1)
        md_files = sorted(batch_dir.glob("p*-ch*-h*.md"))
        if not md_files:
            print(f"错误：目录下无 p*-ch*-h*.md 文件：{batch_dir}")
            sys.exit(1)
        total_files = len(md_files)
        docx_dir = batch_dir / "docx"
        docx_dir.mkdir(parents=True, exist_ok=True)
        grand_total = 0
        for i, md_path in enumerate(md_files, 1):
            docx_path = docx_dir / md_path.with_suffix(".docx").name
            total, _ = convert_md_to_docx(md_path, docx_path)
            grand_total += total
            print(f"  [{i}/{total_files}] {md_path.name} → docx/{docx_path.name} ({total}题)")
        print(f"批量完成：{total_files}文件, {grand_total}题, 输出到 {docx_dir}")
        return

    if not args.input or not args.output:
        print("错误：单文件模式需要 -i 和 -o，或使用 --batch 批量模式")
        sys.exit(1)

    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.exists():
        print(f"错误：输入文件不存在：{input_path}")
        sys.exit(1)

    total, skipped = convert_md_to_docx(input_path, output_path)
    print(f"已保存：{output_path}（共{total}题）")


if __name__ == "__main__":
    main()
