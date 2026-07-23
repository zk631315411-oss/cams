#!/usr/bin/env python3
"""Semantic heading repair, pass 2 (Chinese body, modules 1-2)."""

from pathlib import Path
import importlib.util

ROOT = Path(r"D:\守正公司工作区\cams考试")
FILE = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v7" / "mineru提取" / "中文" / "v7_zh_mineru_merged.md"
spec = importlib.util.spec_from_file_location("repair", ROOT / "tools" / "repair_v7_chinese_heading_hierarchy.py")
repair = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(repair)


def find(lines: list[str], text: str, start: int) -> int:
    for i in range(start, len(lines)):
        if lines[i].strip().startswith(text):
            return i
    raise ValueError(text)


def move(lines: list[str], heading: str, anchor: str, body: int, replacement: str | None = None) -> None:
    source = find(lines, heading, body)
    lines.pop(source)
    if source < len(lines) and not lines[source].strip():
        lines.pop(source)
    target = find(lines, anchor, body)
    lines[target:target] = [replacement or heading, ""]


def main() -> None:
    lines = FILE.read_text(encoding="utf-8-sig").splitlines()
    body = repair.find_body_start(lines)
    toc = lines[:body]
    move(lines, "#### FATF 风格区域机构", "FATF 级区域机构（FSRB）是独立运作", body)
    move(lines, "#### FATF 11 项即时成果", "丹斯克", body, "#### 案例示例：爱沙尼亚银行分行")
    if lines[:body] != toc:
        raise RuntimeError("TOC was modified")
    rows = repair.heading_rows(lines[body:])
    counts = repair.count_levels(rows)
    if counts != {"1": 4, "2": 17, "3": 417, "4": 333, "5": 54} or repair.jumps(rows):
        raise RuntimeError(f"Invalid tree after pass 2: {counts}")
    FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("pass 2 complete", counts)


if __name__ == "__main__":
    main()
