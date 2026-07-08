"""
Step 0+1 合并：配置 + 教材树 → leaf_sections.jsonl

对标 00_prepare_config.py + 01_build_textbook_tree.py。
CAMS 单教材，配置硬编码，不生成独立 config 文件。

输入：v6_clean.md
输出：work/leaf_sections.jsonl + work/ch{}/leaf_sections.jsonl + work/config.json
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

CONFIG = {
    "version": "cams_v1",
    "source": {
        "textbook_id": "cams_v6",
        "textbook_name": "CAMS v6.51 教材（中文版）",
    },
    "schema": {
        "node_types": ["KnowledgePoint", "Regulation", "RiskIndicator", "CaseStudy", "Institution"],
        "edge_types": ["包含", "并列", "导致", "缓解", "前提", "依据"],
        "source_scopes": ["content", "case"],
    },
    "llm": {
        "provider": "openai_compatible",
        "default_base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "temperature": 0.0,
    },
}

_WORKSPACE = Path(__file__).resolve().parents[3]
_MD_PATH = Path(r"d:\守正公司工作区\cams考试\核心数据\源文\source\v6_clean.md")
_WORK = Path(__file__).resolve().parent / "work"

_TOC_END_LINE = 28
_HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
_CASE_RE = re.compile(r"（案例[^）]*）")

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


def classify_source_scope(title: str) -> str:
    return "case" if _CASE_RE.search(title) else "content"


def strip_case_marker(title: str) -> str:
    return _CASE_RE.sub("", title).strip().rstrip(">")


def build_textbook_tree(md_path: Path) -> list[dict]:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    leaves: list[dict] = []
    tid = CONFIG["source"]["textbook_id"]
    tname = CONFIG["source"]["textbook_name"]

    current_chapter = 0
    current_section: str | None = None
    section_order = 0
    subsection_order = 0

    for i, line in enumerate(lines):
        if i < _TOC_END_LINE:
            continue
        m = _HEADING_RE.match(line)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()

        if level == 1:
            continue
        if level == 2:
            current_section = title
            new_ch = _H2_TO_CHAPTER.get(title, 0)
            if new_ch != current_chapter:
                current_chapter = new_ch
                section_order = 0
            section_order += 1
            subsection_order = 0
            continue
        if level == 3 and current_section:
            subsection_order += 1
            scope = classify_source_scope(title)
            clean_title = strip_case_marker(title) if scope == "case" else title
            text_lines: list[str] = []
            j = i + 1
            while j < len(lines):
                if _HEADING_RE.match(lines[j]):
                    break
                stripped = lines[j].strip()
                if stripped:
                    text_lines.append(stripped)
                j += 1

            sid = f"{tid}:C{current_chapter:02d}:S{section_order:02d}:U{subsection_order:02d}"
            leaves.append({
                "section_node_id": sid,
                "textbook_id": tid,
                "textbook_name": tname,
                "chapter_node_id": f"{tid}:C{current_chapter:02d}",
                "section_parent_id": f"{tid}:C{current_chapter:02d}:S{section_order:02d}",
                "chapter_order": current_chapter,
                "section_order": section_order,
                "subsection_order": subsection_order,
                "chapter": f"第{current_chapter}章",
                "section": current_section,
                "subsection": clean_title,
                "subsection_raw": title,
                "source_scope": scope,
                "line_start": i + 1,
                "line_end": j,
                "text": "\n".join(text_lines),
            })
    return leaves


def main() -> int:
    leaves = build_textbook_tree(_MD_PATH)
    print(f"leaf_sections: {len(leaves)}")

    ch_counts = Counter(l["chapter_order"] for l in leaves)
    for ch, cnt in sorted(ch_counts.items()):
        content_n = sum(1 for l in leaves if l["chapter_order"] == ch and l["source_scope"] == "content")
        case_n = sum(1 for l in leaves if l["chapter_order"] == ch and l["source_scope"] == "case")
        print(f"  第{ch}章: {cnt} 节 (content={content_n}, case={case_n})")

    _WORK.mkdir(parents=True, exist_ok=True)
    by_ch: dict[int, list[dict]] = {}
    for l in leaves:
        by_ch.setdefault(l["chapter_order"], []).append(l)

    for ch, ch_leaves in sorted(by_ch.items()):
        out_dir = _WORK / f"ch{ch}"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "leaf_sections.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for leaf in ch_leaves:
                f.write(json.dumps(leaf, ensure_ascii=False) + "\n")
        print(f"  -> {out_path} ({len(ch_leaves)})")

    all_path = _WORK / "leaf_sections.jsonl"
    with all_path.open("w", encoding="utf-8") as f:
        for leaf in leaves:
            f.write(json.dumps(leaf, ensure_ascii=False) + "\n")
    print(f"  -> {all_path} ({len(leaves)})")

    config_path = _WORK / "config.json"
    config_path.write_text(json.dumps(CONFIG, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
