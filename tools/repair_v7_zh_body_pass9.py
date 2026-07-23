#!/usr/bin/env python3
"""TOC-led semantic repair, pass 9: verified module-2 nodes."""

from pathlib import Path
import importlib.util

ROOT = Path(r"D:\守正公司工作区\cams考试")
FILE = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v7" / "mineru提取" / "中文" / "v7_zh_mineru_merged.md"
spec = importlib.util.spec_from_file_location("repair", ROOT / "tools" / "repair_v7_chinese_heading_hierarchy.py")
repair = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(repair)


def find(lines: list[str], prefix: str, body: int, occurrence: int = 1) -> int:
    found = [i for i in range(body, len(lines)) if lines[i].strip().startswith(prefix)]
    if len(found) < occurrence:
        raise ValueError(prefix)
    return found[occurrence - 1]


def insert(lines: list[str], prefix: str, heading: str, body: int) -> None:
    i = find(lines, prefix, body)
    lines[i:i] = [heading, ""]


def remove(lines: list[str], prefix: str, body: int, occurrence: int = 1) -> None:
    i = find(lines, prefix, body, occurrence)
    lines.pop(i)
    if i < len(lines) and not lines[i].strip():
        lines.pop(i)


def main() -> None:
    lines = FILE.read_text(encoding="utf-8-sig").splitlines()
    body = repair.find_body_start(lines)
    toc = lines[:body]

    insert(lines, "阿米娜是美国金融机构FinTrust的经理", "#### 案例分析：FinTrust银行实施AFC标准实践", body)
    insert(lines, "《 FATF 建议》是 FATF 用于指导", "#### FATF 40条建议", body)
    insert(lines, "FATF 互评机制是由 FATF 成员国", "#### FATF 互惠评价", body)
    insert(lines, "FATF 标准建议1要求各司法管辖区识别", "#### FATF 风险评估指南", body)
    insert(lines, "世界银行是一家为发展中国家提供资金支持", "#### 世界银行和国际货币基金组织AFC指南", body)
    insert(lines, "巴塞尔治理研究所的核心使命是", "#### 巴塞尔治理研究所AFC指引", body)

    # Restore the photographed parent-child levels for the international-guidance section.
    lines[find(lines, "#### 国际主要组织的AFC指南", body)] = "### 国际主要组织的AFC指南"
    lines[find(lines, "### 联合国亚洲及太平洋合作框架指导文件", body)] = "#### 联合国亚洲及太平洋合作框架指导文件"

    remove(lines, "#### 案例研究：1999 年公约", body)
    remove(lines, "#### 经济合作与发展组织", body, occurrence=2)
    remove(lines, "#### AFC规则与制度", body)
    container = find(lines, "## AFC 法规与制度", body)
    lines[container] = "## AFC规则与制度"

    if lines[:body] != toc:
        raise RuntimeError("TOC was modified")
    rows = repair.heading_rows(lines[body:])
    if repair.jumps(rows):
        raise RuntimeError(f"Heading jumps: {repair.jumps(rows)[:3]}")
    FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("pass 9 complete", repair.count_levels(rows))


if __name__ == "__main__":
    main()
