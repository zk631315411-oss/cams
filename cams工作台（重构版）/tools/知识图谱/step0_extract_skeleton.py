"""
Step 0：从 v6_clean.md 机械提取叶子节，不调 LLM。
对标高代提取 01_build_textbook_tree.py 的 leaf_sections.jsonl 格式。

输入：v6_clean.md（全书教材 Markdown）
输出：work/leaf_sections.jsonl（全量） + work/ch{}/leaf_sections.jsonl（按章）
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_WORKSPACE = Path(__file__).resolve().parents[2]
_MD_PATH = Path(r"d:\守正公司工作区\cams考试\核心数据\源文\source\v6_clean.md")
_WORK = _WORKSPACE / "tools" / "知识图谱" / "work"

_TOC_END_LINE = 28
_TEXTBOOK_ID = "cams_v6"
_TEXTBOOK_NAME = "CAMS v6.51 教材（中文版）"
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
_CASE_RE = re.compile(r"（案例[^）]*）")

# H2 标题 → 章节号（按习题集组织）
_H2_TO_CHAPTER: dict[str, int] = {
    "概述": 2, "银行和其他储蓄机构": 2, "非银行金融机构": 2,
    "非金融行业": 2, "国际贸易活动": 2, "新型支付产品及服务的风险": 2,
    "用于非法融资的公司组织形式": 2, "恐怖融资": 2,
    "金融行动特别工作组": 3, "巴塞尔银行监管委员会": 3,
    "欧洲联盟反洗钱指令": 3, "与金融行动特别工作组类似的区域性组织": 3,
    "其他有影响力的机构": 3, "重要的美国立法和监管举措": 3,
    "评估反洗钱 / 反恐融资风险": 4, "反洗钱 / 反恐融资制度": 4,
    "\"了解您的客户\"": 4, "监控及筛查": 4, "洗钱和恐怖融资活动的危险信号": 4,
    "金融组织发起的调查": 5, "执法机构发起的调查": 5,
    "国家或地区间的反洗钱/反恐融资合作": 5,
}


def _classify_source_scope(h3_title: str) -> str:
    """数学 KG 用 content/example/exercise；CAMS 用 content/case"""
    return "case" if _CASE_RE.search(h3_title) else "content"


def _strip_case_marker(title: str) -> str:
    return _CASE_RE.sub("", title).strip().rstrip(">")


def extract_leaf_sections(md_path: Path) -> list[dict]:
    """遍历 Markdown，按 H2 → H3 层级提取所有叶子节，对齐数学 KG leaf_sections 格式"""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    leaves: list[dict] = []

    current_chapter = 0
    current_section: str | None = None  # H2
    subsection_order = 0  # H3 在当前 H2 内的序号
    section_order = 0      # H2 在当前章内的序号

    current_seen_sections: set[str] = set()  # 去重

    for i, line in enumerate(lines):
        if i < _TOC_END_LINE:
            continue

        m = _HEADING_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()

        if level == 1:  # H1：忽略
            continue

        if level == 2:  # H2
            current_section = title
            new_chapter = _H2_TO_CHAPTER.get(title, 0)
            if new_chapter != current_chapter:
                current_chapter = new_chapter
                section_order = 0
            section_order += 1
            subsection_order = 0
            continue

        if level == 3 and current_section:  # H3
            subsection_order += 1
            scope = _classify_source_scope(title)
            subsection_clean = _strip_case_marker(title) if scope == "case" else title

            # 收集该 H3 的段落原文
            text_lines: list[str] = []
            j = i + 1
            while j < len(lines):
                if _HEADING_RE.match(lines[j]):
                    break
                stripped = lines[j].strip()
                if stripped:
                    text_lines.append(stripped)
                j += 1

            section_node_id = f"{_TEXTBOOK_ID}:C{current_chapter:02d}:S{section_order:02d}:U{subsection_order:02d}"

            leaves.append({
                "section_node_id": section_node_id,
                "textbook_id": _TEXTBOOK_ID,
                "textbook_name": _TEXTBOOK_NAME,
                "chapter_node_id": f"{_TEXTBOOK_ID}:C{current_chapter:02d}",
                "section_parent_id": f"{_TEXTBOOK_ID}:C{current_chapter:02d}:S{section_order:02d}",
                "chapter_order": current_chapter,
                "section_order": section_order,
                "subsection_order": subsection_order,
                "chapter": f"第{current_chapter}章",
                "section": current_section,
                "subsection": subsection_clean,
                "subsection_raw": title,
                "source_scope": scope,
                "line_start": i + 1,
                "line_end": j,
                "text": "\n".join(text_lines),
            })
    return leaves


def main() -> int:
    leaves = extract_leaf_sections(_MD_PATH)
    print(f"提取叶子节: {len(leaves)} 个")

    # 统计
    from collections import Counter
    scope_counts = Counter(l["source_scope"] for l in leaves)
    chapter_counts = Counter(l["chapter_order"] for l in leaves)
    for ch, count in sorted(chapter_counts.items()):
        ch_leaves = [l for l in leaves if l["chapter_order"] == ch]
        content_n = sum(1 for l in ch_leaves if l["source_scope"] == "content")
        case_n = sum(1 for l in ch_leaves if l["source_scope"] == "case")
        print(f"  第{ch}章: {count} 节 (content={content_n}, case={case_n})")

    # 按章节写入 leaf_sections.jsonl
    by_chapter: dict[int, list[dict]] = {}
    for l in leaves:
        by_chapter.setdefault(l["chapter_order"], []).append(l)

    for ch, ch_leaves in sorted(by_chapter.items()):
        out_dir = _WORK / f"ch{ch}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "leaf_sections.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for leaf in ch_leaves:
                f.write(json.dumps(leaf, ensure_ascii=False) + "\n")
        print(f"写入: {out_path} ({len(ch_leaves)} 条)")

    # 全量汇总
    all_path = _WORK / "leaf_sections.jsonl"
    with all_path.open("w", encoding="utf-8") as f:
        for leaf in leaves:
            f.write(json.dumps(leaf, ensure_ascii=False) + "\n")
    print(f"写入: {all_path} ({len(leaves)} 条)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
