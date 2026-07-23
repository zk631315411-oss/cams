#!/usr/bin/env python3
"""Semantic heading repair, pass 4 (data-lineage placement cleanup)."""

from pathlib import Path
import importlib.util

ROOT = Path(r"D:\守正公司工作区\cams考试")
FILE = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v7" / "mineru提取" / "中文" / "v7_zh_mineru_merged.md"
spec = importlib.util.spec_from_file_location("repair", ROOT / "tools" / "repair_v7_chinese_heading_hierarchy.py")
repair = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(repair)


def find(lines: list[str], prefix: str, body: int) -> int:
    for i in range(body, len(lines)):
        if lines[i].strip().startswith(prefix):
            return i
    raise ValueError(prefix)


def main() -> None:
    lines = FILE.read_text(encoding="utf-8-sig").splitlines()
    body = repair.find_body_start(lines)
    toc = lines[:body]
    title = find(lines, "#### 数据谱系", body)
    heading = lines.pop(title)
    if title < len(lines) and not lines[title].strip():
        lines.pop(title)
    target = find(lines, "数据血统是指追踪并映射数据从源系统", body)
    lines[target:target] = [heading, ""]
    plain = next(
        i for i in range(body, len(lines) - 1)
        if lines[i].strip() == "数据准备" and lines[i + 2].startswith("#### 数据准备")
    )
    # The first plain occurrence after the data-quality image is a duplicated
    # OCR title; the markdown title immediately following it is authoritative.
    while plain + 1 < len(lines) and not lines[plain + 1].strip():
        lines.pop(plain + 1)
    if lines[plain].strip() == "数据准备" and lines[plain + 1].startswith("#### 数据准备"):
        lines.pop(plain)
    else:
        raise RuntimeError("Expected duplicate plain Data preparation title")
    if lines[:body] != toc:
        raise RuntimeError("TOC was modified")
    rows = repair.heading_rows(lines[body:])
    counts = repair.count_levels(rows)
    expected = {"1": 4, "2": 17, "3": 417, "4": 333, "5": 54}
    if counts != expected or repair.jumps(rows):
        raise RuntimeError(f"Invalid tree after pass 4: {counts}")
    FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("pass 4 complete", counts)


if __name__ == "__main__":
    main()
