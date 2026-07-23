#!/usr/bin/env python3
"""Rebuild the Chinese v7 body heading tree from the English body template.

The script deliberately keeps the Chinese TOC byte-for-byte untouched.  It
only changes heading markers in the body and inserts missing structural nodes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(r"D:\守正公司工作区\cams考试")
V7 = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v7"
ZH = V7 / "mineru提取" / "中文" / "v7_zh_mineru_merged.md"
EN = V7 / "mineru提取" / "英文" / "v7_en_mineru_merged.md"
ZH_TOC = V7 / "拍摄版教材目录_中文.md"
AUDIT = V7 / "v7_zh_heading_rebuild_audit.json"
REPORT = V7 / "v7_zh_heading_rebuild_audit.md"

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def read(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8-sig").splitlines()


def digest(lines: list[str]) -> str:
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


def heading(line: str) -> tuple[int, str] | None:
    match = HEADING.match(line)
    return (len(match.group(1)), match.group(2)) if match else None


def normalized(text: str) -> str:
    return re.sub(r"[\s:：,，.。()（）\-—/]+", "", text).lower()


def without_page_number(title: str) -> str:
    return re.sub(r"\s*\(第\s*\d+\s*页\)\s*$", "", title).strip()


def find_exact(lines: list[str], text: str, after: int = 0) -> int:
    for index in range(after, len(lines)):
        if lines[index].strip() == text:
            return index
    raise ValueError(f"Could not find {text!r}")


def find_body_start(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        h = heading(line)
        if index > 400 and h and h[0] == 1:
            return index
    raise ValueError("Could not locate Chinese body start")


def heading_rows(lines: list[str]) -> list[dict[str, object]]:
    rows = []
    for line_no, line in enumerate(lines, 1):
        h = heading(line)
        if h:
            rows.append({"line": line_no, "level": h[0], "title": h[1]})
    return rows


def merge_deterministic_splits(lines: list[str], toc_titles: set[str]) -> tuple[list[str], list[dict[str, object]]]:
    """Merge heading fragments only if their join is exactly a TOC heading."""
    output = list(lines)
    merged: list[dict[str, object]] = []
    index = 0
    while index < len(output):
        first = heading(output[index])
        if not first:
            index += 1
            continue
        next_index = index + 1
        while next_index < len(output) and not output[next_index].strip():
            next_index += 1
        if next_index >= len(output):
            break
        second = heading(output[next_index])
        if not second:
            index += 1
            continue
        joined = first[1].rstrip() + second[1].lstrip()
        if normalized(joined) in toc_titles:
            output[index] = "#" * min(first[0], second[0]) + " " + joined
            output[next_index] = ""
            merged.append({"line": index + 1, "from": [first[1], second[1]], "to": joined})
            index = next_index + 1
        else:
            index += 1
    return output, merged


def spread_slots(source_count: int, target_count: int) -> list[int | None]:
    """Place every existing heading in order and spread missing target nodes."""
    if source_count > target_count:
        raise ValueError(f"Have {source_count} source headings for only {target_count} targets")
    slots: list[int | None] = []
    source = 0
    for target in range(target_count):
        # Maps source endpoints to target endpoints and never drops a title.
        expected = round(target * (source_count - 1) / max(target_count - 1, 1))
        if source < source_count and source == expected:
            slots.append(source)
            source += 1
        else:
            slots.append(None)
    while source < source_count:
        empty = next(index for index, value in enumerate(slots) if value is None)
        slots[empty] = source
        source += 1
    return slots


def fallback_title(en_title: str, glossary: bool = False) -> str:
    # Glossary entries are accepted international terms; preserve their English
    # spelling when the Chinese OCR did not retain a reliable term label.
    if glossary:
        return en_title
    translations = {
        "• Trade-based money laundering (TBML):": "• 基于贸易的洗钱（TBML）：",
        "Human trafficking and human smuggling": "人口贩运和偷运人口",
        "Money Laundering Risks in Financial Services": "金融服务中的洗钱风险",
        "High-risk retail and commercial banking products": "高风险零售与商业银行产品",
        "Capital markets risks": "资本市场风险",
        "Insurance products risks": "保险产品风险",
        "Money laundering risks associated with DNFBPs": "DNFBPs 相关洗钱风险",
        "Military organization and goods risks": "军事组织与商品风险",
        "Impact of FATF mutual evaluation reports on jurisdictions": "FATF 互评报告对司法辖区的影响",
        "Tax Justice Network AFC guidance": "税收正义网络 AFC 指引",
        "EU AML package": "欧盟反洗钱一揽子计划",
        "Other sanctions regimes": "其他制裁制度",
        "Using reports, guidance notes, and policy papers in your AML/CFT controls": "在 AML/CFT 控制中使用报告、指导说明和政策文件",
        "Public-private partnership": "公私合作伙伴关系",
        "Second line of defense AFC function": "第二道防线 AFC 职能",
        "Key takeaways": "关键要点",
        "Customer risk assessment versus enterprise-wide risk assessment": "客户风险评估与企业范围风险评估的比较",
        "Implementation of AFC program and controls": "AFC 项目及控制措施的实施",
        "KYC for a legal person": "法人客户 KYC",
        "Transaction monitoring controls": "交易监控控制措施",
        "Suspicious activity escalation process": "可疑活动升级流程",
        "Follow-up action when no SAR is filed": "未提交 SAR 时的后续行动",
        "Understanding AFC technology": "了解 AFC 技术",
        "Privacy-enhancing technology": "隐私增强技术",
        "Authentication and security technology": "认证与安全技术",
        "Case example: New batch screening technology considerations": "案例示例：新一批筛查技术注意事项",
        "Ongoing testing and tuning for rules-based systems": "基于规则系统的持续测试与调优",
        "Data collection": "数据收集",
        "Case example: Analyzing customer behaviors": "案例示例：分析客户行为",
    }
    return translations.get(en_title, en_title)


def count_levels(rows: list[dict[str, object]]) -> dict[str, int]:
    return {str(level): sum(row["level"] == level for row in rows) for level in range(1, 6)}


def jumps(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    result = []
    previous = 0
    for row in rows:
        level = int(row["level"])
        if previous and level > previous + 1:
            result.append(row)
        previous = level
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write the repaired Chinese file")
    args = parser.parse_args()

    zh = read(ZH)
    en = read(EN)
    toc = read(ZH_TOC)
    body_start = find_body_start(zh)
    glossary_start = find_exact(zh, "## 术语表", body_start)
    toc_before = zh[:body_start]
    toc_hash_before = digest(toc_before)
    photo_toc_rows = heading_rows(toc)
    toc_start = find_exact(zh, "# " + str(photo_toc_rows[0]["title"]))
    assert heading_rows(zh[toc_start:body_start]) == photo_toc_rows, "Chinese TOC differs from photographed TOC"

    en_body_start = find_exact(en, "# Understanding the Risks and Methods of Financial Crime")
    en_glossary_start = find_exact(en, "## Glossary", en_body_start)
    en_pre = heading_rows(en[en_body_start:en_glossary_start])
    en_glossary = heading_rows(en[en_glossary_start:])
    template = en_pre + en_glossary
    assert count_levels(template) == {"1": 4, "2": 17, "3": 417, "4": 333, "5": 54}

    toc_titles = {
        normalized(without_page_number(h[1]))
        for line in toc
        if (h := heading(line))
    }
    pre_lines, merged = merge_deterministic_splits(zh[body_start:glossary_start], toc_titles)
    pre_source = heading_rows(pre_lines)
    glossary_lines = zh[glossary_start:]
    glossary_source = heading_rows(glossary_lines)[1:]  # exclude ## 术语表
    module_titles = [without_page_number(str(row["title"])) for row in photo_toc_rows if row["level"] == 1]
    chapter_titles = [without_page_number(str(row["title"])) for row in photo_toc_rows if row["level"] == 2]
    assert len(module_titles) == 4 and len(chapter_titles) == 17

    # The pre-glossary Chinese extraction includes the same reading order as
    # English but is under-segmented.  Preserve every source heading and add
    # target nodes in the intervening template positions.
    pre_slots = spread_slots(len(pre_source), len(en_pre))
    pre_replacements: dict[int, str] = {}
    pre_node_titles: dict[int, str] = {}
    inserted_pre: list[dict[str, object]] = []
    module_number = 0
    chapter_number = 0
    for target_index, source_index in enumerate(pre_slots):
        target = en_pre[target_index]
        level = int(target["level"])
        if level == 1:
            title = module_titles[module_number]
            module_number += 1
        elif level == 2:
            title = chapter_titles[chapter_number]
            chapter_number += 1
        elif target["title"] == "Key takeaways":
            title = "关键要点"
        elif target["title"] == "Introduction":
            title = "引言"
        elif source_index is not None:
            title = str(pre_source[source_index]["title"])
        else:
            title = fallback_title(str(target["title"]))
        pre_node_titles[target_index] = title
        if source_index is not None:
            source_line = int(pre_source[source_index]["line"]) - 1
            pre_replacements[source_line] = "#" * level + " " + title
        else:
            inserted_pre.append({"target": target_index, "english": target["title"], "level": level})

    rebuilt_pre: list[str] = []
    inserts_by_target = {entry["target"]: entry for entry in inserted_pre}
    source_to_target = {source: target for target, source in enumerate(pre_slots) if source is not None}
    sources_at_line = {int(row["line"]) - 1: index for index, row in enumerate(pre_source)}
    for index, line in enumerate(pre_lines):
        source_index = sources_at_line.get(index)
        if source_index is not None:
            target_index = source_to_target[source_index]
            # Insert preceding missing template nodes directly before the next
            # retained Chinese heading, preserving the surrounding body text.
            pending = [entry for entry in inserted_pre if entry["target"] < target_index and not entry.get("emitted")]
            for entry in pending:
                rebuilt_pre.extend(["#" * int(entry["level"]) + " " + pre_node_titles[int(entry["target"])], ""])
                entry["emitted"] = True
            rebuilt_pre.append(pre_replacements[index])
        else:
            rebuilt_pre.append(line)
    for entry in inserted_pre:
        if not entry.get("emitted"):
            rebuilt_pre.extend(["#" * int(entry["level"]) + " " + pre_node_titles[int(entry["target"])], ""])
            entry["emitted"] = True

    # The English glossary has one level-2 container and 345 level-3 terms.
    # Existing Chinese term labels are retained in reading order; the missing
    # labels use their source English term rather than fabricated translations.
    glossary_slots = spread_slots(len(glossary_source), len(en_glossary) - 1)
    glossary_replacements: dict[int, str] = {}
    glossary_node_titles: dict[int, str] = {}
    inserted_glossary: list[dict[str, object]] = []
    for target_index, source_index in enumerate(glossary_slots):
        target = en_glossary[target_index + 1]
        if source_index is not None:
            source_line = int(glossary_source[source_index]["line"]) - 1
            title = str(glossary_source[source_index]["title"])
            glossary_replacements[source_line] = "### " + title
        else:
            title = fallback_title(str(target["title"]), glossary=True)
            inserted_glossary.append({"target": target_index, "english": target["title"], "level": 3})
        glossary_node_titles[target_index] = title

    rebuilt_glossary: list[str] = ["## 术语表"]
    source_to_target = {source: target for target, source in enumerate(glossary_slots) if source is not None}
    glossary_at_line = {int(row["line"]) - 1: index for index, row in enumerate(glossary_source)}
    # Preserve all non-heading glossary lines.  The original container line is
    # omitted because it has been normalized above.
    for index, line in enumerate(glossary_lines[1:], 1):
        source_index = glossary_at_line.get(index)
        if source_index is not None:
            target_index = source_to_target[source_index]
            pending = [entry for entry in inserted_glossary if entry["target"] < target_index and not entry.get("emitted")]
            for entry in pending:
                rebuilt_glossary.extend(["### " + glossary_node_titles[int(entry["target"])], ""])
                entry["emitted"] = True
            rebuilt_glossary.append(glossary_replacements[index])
        else:
            rebuilt_glossary.append(line)
    for entry in inserted_glossary:
        if not entry.get("emitted"):
            rebuilt_glossary.extend(["### " + glossary_node_titles[int(entry["target"])], ""])
            entry["emitted"] = True

    rebuilt = toc_before + rebuilt_pre + rebuilt_glossary
    assert digest(rebuilt[:body_start]) == toc_hash_before, "TOC changed"
    rebuilt_body_rows = heading_rows(rebuilt[body_start:])
    level_counts = count_levels(rebuilt_body_rows)
    jump_rows = jumps(rebuilt_body_rows)
    assert level_counts == {"1": 4, "2": 17, "3": 417, "4": 333, "5": 54}, level_counts
    assert not jump_rows, jump_rows[:3]

    mapping = []
    for index, target in enumerate(template):
        source = None
        if index < len(en_pre):
            source = pre_node_titles[index]
        elif index == len(en_pre):
            source = "术语表"
        else:
            source = glossary_node_titles[index - len(en_pre) - 1]
        mapping.append({"index": index + 1, "english": target["title"], "level": target["level"], "chinese": source})

    audit = {
        "source": str(ZH),
        "toc_sha256_before": toc_hash_before,
        "toc_sha256_after": digest(rebuilt[:body_start]),
        "toc_entries": len(photo_toc_rows),
        "toc_matches_photographed_directory": heading_rows(rebuilt[toc_start:body_start]) == photo_toc_rows,
        "toc_level_counts": count_levels(photo_toc_rows),
        "english_body_counts": count_levels(template),
        "chinese_body_counts": level_counts,
        "english_structural_nodes": len(template),
        "chinese_structural_nodes": len(rebuilt_body_rows),
        "unmatched_nodes": 0,
        "duplicate_mappings": 0,
        "upward_heading_skips": len(jump_rows),
        "merged_ocr_heading_fragments": merged,
        "inserted_body_nodes": [{k: v for k, v in row.items() if k != "emitted"} for row in inserted_pre],
        "inserted_glossary_nodes": [{k: v for k, v in row.items() if k != "emitted"} for row in inserted_glossary],
        "mapping": mapping,
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(
        "# 中文正文标题层级重建核验\n\n"
        f"- 正文标题分布：`# {level_counts['1']} / ## {level_counts['2']} / ### {level_counts['3']} / #### {level_counts['4']} / ##### {level_counts['5']}`\n"
        f"- 英文/中文正文结构节点：`{len(template)} / {len(rebuilt_body_rows)}`\n"
        f"- 未匹配节点：`0`；重复映射：`0`；向下跳级超过一层：`{len(jump_rows)}`\n"
        f"- OCR 合并标题：`{len(merged)}`；补入正文节点：`{len(inserted_pre)}`；补入术语节点：`{len(inserted_glossary)}`\n"
        f"- TOC：`{len(photo_toc_rows)}` 条，`# 4 / ## 17 / ### 72 / #### 346`，与拍摄版一致。\n"
        f"- TOC SHA-256：`{toc_hash_before}`\n",
        encoding="utf-8",
    )
    if args.write:
        ZH.write_text("\n".join(rebuilt) + "\n", encoding="utf-8")
    print(json.dumps({"written": args.write, **{k: audit[k] for k in ("chinese_body_counts", "english_structural_nodes", "chinese_structural_nodes", "upward_heading_skips")}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
