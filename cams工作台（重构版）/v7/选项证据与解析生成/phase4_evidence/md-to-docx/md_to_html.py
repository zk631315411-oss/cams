# -*- coding: utf-8 -*-
"""将小节 md 转为题库导入 HTML。"""

import argparse
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

# <sup> 和 （书内第XX页） 和 （PXX）
_SUP_RE = re.compile(r"<sup>P(\d+)</sup>|（书内第(\d+)页）|（P(\d+)）")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_TITLE_RE = re.compile(r"p(\d+)-ch(\d+)-h(\d+)")


def section_to_title(filename: str) -> str:
    m = _TITLE_RE.search(filename)
    if not m:
        return "CAMS"
    return f"CAMS CH{m.group(2).zfill(2)}"


def parse_inline(text: str) -> str:
    """行内 <sup> → <sup>P28</sup>, **bold** → <b>bold</b>."""
    result = []
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
            result.append(text[pos:])
            break
        if next_m.start() > pos:
            result.append(text[pos:next_m.start()])
        if tag_type == "sup":
            page = next_m.group(1) or next_m.group(2) or next_m.group(3)
            result.append(f"<sup>P{page}</sup>")
        else:
            result.append(f"<b>{next_m.group(1)}</b>")
        pos = next_m.end()
    return "".join(result)


# 蓝底标签
_BG_LABELS = {
    "考点：": "考点", "核心解析：": "核心解析",
    "易错提醒：": "易错提醒", "教材原句：": "教材原句",
}
_ERROR_RE = re.compile(r"^([A-E])项(\S+)：")


def render_analysis(text: str) -> str:
    """渲染解析文本为 HTML 段落。"""
    lines: list[str] = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        em = _ERROR_RE.match(line)
        if em:
            label = f"{em.group(1)}项{em.group(2)}"
            rest = line[len(f"{em.group(1)}项{em.group(2)}："):]
            lines.append(
                f'<p style="text-indent:2em;margin:4px 0">'
                f'<span style="background:#D6E4F0;font-weight:bold">{label}</span>'
                f'{parse_inline(rest)}</p>'
            )
            continue
        matched = False
        for lbl, title in _BG_LABELS.items():
            if line.startswith(lbl):
                rest = line[len(lbl):]
                tag = f'<span style="background:#D6E4F0;font-weight:bold">{title}</span>'
                if rest:
                    lines.append(
                        f'<p style="text-indent:2em;margin:4px 0">{tag}{parse_inline(rest)}</p>'
                    )
                else:
                    lines.append(
                        f'<p style="text-indent:2em;margin:4px 0">{tag}</p>'
                    )
                matched = True
                break
        if not matched:
            lines.append(
                f'<p style="text-indent:2em;margin:4px 0">{parse_inline(line)}</p>'
            )
    return "\n".join(lines)


def convert_md_to_html(input_path: Path, output_path: Path) -> int:
    content = input_path.read_text(encoding="utf-8")
    content = content.replace("「", "“").replace("」", "”")
    title = section_to_title(input_path.name)

    blocks = content.split("\n\n---\n\n")
    # 第一块 = header + Q1
    first_block = blocks[0].strip()
    header_end = first_block.find("\n教材章节：")
    first_q = first_block[header_end:].strip() if header_end > 0 else ""
    question_blocks = [first_q] if first_q else []
    question_blocks += [b.strip() for b in blocks[1:] if b.strip()]

    html_parts = [
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">",
        "<style>body{font-family:SimSun,serif;font-size:10.5pt;line-height:1.6;margin:2cm 3cm}</style>",
        "</head><body>",
        f"<h2>试卷名称:{title}</h2>",
        "<h3>一、单项选择题</h3>",
    ]

    for qi, block in enumerate(question_blocks, 1):
        lines = block.strip().split("\n")
        stem = ""
        options = []
        answer = ""
        analysis_lines = []
        in_options = False
        in_analysis = False
        opt_buf = None

        for s in lines:
            s = s.strip()
            if s.startswith("教材章节：") or s.startswith("## "):
                continue
            if s.startswith("题型：") or s.startswith("English:"):
                continue
            elif s.startswith("题干：") or s.startswith("题目："):
                stem = s[3:].strip()
            elif s == "选项：":
                in_options = True
            elif in_options and s.startswith("- "):
                if opt_buf:
                    options.append(opt_buf)
                opt_buf = s[2:].strip()
            elif in_options and s.startswith("English:") and opt_buf:
                continue
            elif s.startswith("答案："):
                in_options = False
                if opt_buf:
                    options.append(opt_buf)
                    opt_buf = None
                answer = s[3:].strip()
            elif s == "解析：":
                in_analysis = True
                in_options = False
            elif in_analysis and s:
                if s == "---":
                    break
                analysis_lines.append(s)

        html_parts.append(f"<p><b>{qi}. {parse_inline(stem)} ( )</b></p>")
        for opt in options:
            html_parts.append(f"<p style=\"text-indent:1em\">{parse_inline(opt)}</p>")
        html_parts.append(f"<p><b>答案:{answer}</b></p>")
        html_parts.append("<p><b>解析：</b></p>")
        html_parts.append(render_analysis("\n".join(analysis_lines)))

    html_parts.append("</body></html>")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(html_parts), encoding="utf-8")
    return len(question_blocks)


def main() -> None:
    parser = argparse.ArgumentParser(description="小节 md → 题库导入 HTML")
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()
    total = convert_md_to_html(Path(args.input), Path(args.output))
    print(f"已保存：{args.output}（共{total}题）")


if __name__ == "__main__":
    main()
