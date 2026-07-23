#!/usr/bin/env python3
"""TOC-led semantic repair, pass 5: photographed-directory nodes in module 1."""

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


def insert(lines: list[str], prefix: str, heading: str, body: int) -> None:
    i = find(lines, prefix, body)
    lines[i:i] = [heading, ""]


def move(lines: list[str], source: str, target: str, heading: str, body: int, occurrence: int = 1) -> None:
    found = [i for i in range(body, len(lines)) if lines[i].strip().startswith(source)]
    if len(found) < occurrence:
        raise ValueError(source)
    i = found[occurrence - 1]
    lines.pop(i)
    if i < len(lines) and not lines[i].strip():
        lines.pop(i)
    insert(lines, target, heading, body)


def main() -> None:
    lines = FILE.read_text(encoding="utf-8-sig").splitlines()
    body = repair.find_body_start(lines)
    toc = lines[:body]

    # The following are all photographed-directory entries whose Chinese
    # definition paragraphs were present but had no title marker.
    plain_money = next(i for i in range(body, len(lines)) if lines[i].strip() == "洗钱")
    lines[plain_money] = "#### 洗钱"
    insert(lines, "避税或税务筹划并不违法", "#### 避税与逃税", body)
    insert(lines, "欺诈行为是指为获取不正当", "#### 欺诈", body)
    insert(lines, "金融犯罪具有深远的社会经济影响", "#### 金融犯罪的社会后果", body)
    insert(lines, "金融犯罪会破坏经济稳定", "#### 防止金融犯罪的制度问责", body)

    # FinCEN is a US-regulatory section, not a child of cybercrime.
    move(lines, "#### 金融犯罪执法网络", "美国国会指定金融犯罪执法网络（FinCEN）", "#### 金融犯罪执法网络", body)

    # Reassign two misplaced duplicate markers to their photographed-TOC
    # sections, preserving the surrounding Chinese prose unchanged.
    move(lines, "#### 避税与逃税", "洗钱问题在法律界备受关注", "#### 法律服务部门风险", body, occurrence=2)
    move(lines, "#### 替代汇款系统", "以贸易为幌子的洗钱活动是指", "#### 进出口业务风险", body, occurrence=2)

    if lines[:body] != toc:
        raise RuntimeError("TOC was modified")
    rows = repair.heading_rows(lines[body:])
    if repair.jumps(rows):
        raise RuntimeError(f"Heading jumps: {repair.jumps(rows)[:3]}")
    FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("pass 5 complete", repair.count_levels(rows))


if __name__ == "__main__":
    main()
