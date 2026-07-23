#!/usr/bin/env python3
"""TOC-led semantic repair, pass 10: AFC-control section hierarchy."""

from pathlib import Path
import importlib.util

ROOT = Path(r"D:\守正公司工作区\cams考试")
FILE = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v7" / "mineru提取" / "中文" / "v7_zh_mineru_merged.md"
spec = importlib.util.spec_from_file_location("repair", ROOT / "tools" / "repair_v7_chinese_heading_hierarchy.py")
repair = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(repair)


def find(lines: list[str], text: str, body: int) -> int:
    return next(i for i in range(body, len(lines)) if lines[i].strip() == text)


def main() -> None:
    lines = FILE.read_text(encoding="utf-8-sig").splitlines()
    body = repair.find_body_start(lines)
    toc = lines[:body]
    lines[find(lines, "### 质量控制功能", body)] = "#### 质量控制功能"
    duplicate = find(lines, "#### 质量控制职能", body)
    lines.pop(duplicate)
    if duplicate < len(lines) and not lines[duplicate].strip():
        lines.pop(duplicate)
    lines[find(lines, "#### 持续性AFC控制", body)] = "### 持续性AFC控制"
    if lines[:body] != toc:
        raise RuntimeError("TOC was modified")
    rows = repair.heading_rows(lines[body:])
    if repair.jumps(rows):
        raise RuntimeError(f"Heading jumps: {repair.jumps(rows)[:3]}")
    FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("pass 10 complete", repair.count_levels(rows))


if __name__ == "__main__":
    main()
