#!/usr/bin/env python3
"""TOC-led semantic repair, pass 8: module-1 parent and child hierarchy."""

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
    return found[occurrence - 1]


def take(lines: list[str], index: int) -> str:
    value = lines.pop(index)
    if index < len(lines) and not lines[index].strip():
        lines.pop(index)
    return value


def main() -> None:
    lines = FILE.read_text(encoding="utf-8-sig").splitlines()
    body = repair.find_body_start(lines)
    toc = lines[:body]

    # The photographed TOC makes the comparison a child of Terrorist funding.
    parent = take(lines, find(lines, "### 资助恐怖主义", body))
    child = find(lines, "#### 恐怖主义融资与洗钱的比较", body)
    lines[child:child] = [parent, ""]

    # Blockchain has a complete Chinese definition but lacked its TOC node.
    blockchain = find(lines, "区块链是一种去中心化、分布式公共账本系统", body)
    lines[blockchain:blockchain] = ["#### 区块链", ""]

    # Restore the photographed hierarchy: High-risk industries > High-value
    # asset risks. The later duplicate title has no content of its own.
    high_risk = find(lines, "#### 高风险行业", body)
    lines[high_risk] = "### 高风险行业"
    high_value_parent = find(lines, "### 高价值资产风险", body)
    lines[high_value_parent] = "#### 高价值资产风险"
    duplicate = find(lines, "#### 高价值资产风险", body, occurrence=2)
    take(lines, duplicate)

    if lines[:body] != toc:
        raise RuntimeError("TOC was modified")
    rows = repair.heading_rows(lines[body:])
    if repair.jumps(rows):
        raise RuntimeError(f"Heading jumps: {repair.jumps(rows)[:3]}")
    FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("pass 8 complete", repair.count_levels(rows))


if __name__ == "__main__":
    main()
