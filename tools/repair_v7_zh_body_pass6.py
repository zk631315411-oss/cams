#!/usr/bin/env python3
"""TOC-led semantic repair, pass 6: correct two module-1 title anchors."""

from pathlib import Path
import importlib.util

ROOT = Path(r"D:\守正公司工作区\cams考试")
FILE = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v7" / "mineru提取" / "中文" / "v7_zh_mineru_merged.md"
spec = importlib.util.spec_from_file_location("repair", ROOT / "tools" / "repair_v7_chinese_heading_hierarchy.py")
repair = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(repair)


def find(lines: list[str], prefix: str, body: int) -> int:
    return next(i for i in range(body, len(lines)) if lines[i].strip().startswith(prefix))


def move(lines: list[str], title: str, anchor: str, body: int) -> None:
    i = find(lines, title, body)
    heading = lines.pop(i)
    if i < len(lines) and not lines[i].strip():
        lines.pop(i)
    target = find(lines, anchor, body)
    lines[target:target] = [heading, ""]


def main() -> None:
    lines = FILE.read_text(encoding="utf-8-sig").splitlines()
    body = repair.find_body_start(lines)
    toc = lines[:body]
    move(lines, "#### 金融犯罪的社会后果", "金融犯罪以多种方式损害各类组织", body)
    move(lines, "#### 防止金融犯罪的制度问责", "金融犯罪会破坏经济稳定", body)
    if lines[:body] != toc:
        raise RuntimeError("TOC was modified")
    rows = repair.heading_rows(lines[body:])
    if repair.jumps(rows):
        raise RuntimeError("Heading jump introduced")
    FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("pass 6 complete", repair.count_levels(rows))


if __name__ == "__main__":
    main()
