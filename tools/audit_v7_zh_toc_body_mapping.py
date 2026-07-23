#!/usr/bin/env python3
"""Map photographed Chinese TOC nodes to Chinese body headings without editing text."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(r"D:\守正公司工作区\cams考试")
V7 = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v7"
BOOK = V7 / "mineru提取" / "中文" / "v7_zh_mineru_merged.md"
TOC = V7 / "拍摄版教材目录_中文.md"
REPORT = V7 / "v7_zh_toc_body_mapping.md"
HEADING = re.compile(r"^(#{1,5})\s+(.+?)\s*$")
PAGE = re.compile(r"\s*\(第\s*\d+\s*页\)\s*$")


def parse(lines: list[str], offset: int = 0) -> list[dict[str, object]]:
    rows = []
    for index, line in enumerate(lines, offset + 1):
        match = HEADING.match(line)
        if match:
            rows.append({"line": index, "level": len(match.group(1)), "title": match.group(2)})
    return rows


def bare(title: str) -> str:
    return PAGE.sub("", title).strip()


def normalized(title: str) -> str:
    return re.sub(r"[\s,，.。:：;；()（）/\\-—]+", "", bare(title)).lower()


def body_start(lines: list[str]) -> int:
    for index, line in enumerate(lines):
        if index > 400 and line.startswith("# "):
            return index
    raise ValueError("Body start not found")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    book = BOOK.read_text(encoding="utf-8-sig").splitlines()
    photo = parse(TOC.read_text(encoding="utf-8-sig").splitlines())
    start = body_start(book)
    body = parse(book[start:], start)
    next_after = 0
    mapped = []
    for node in photo:
        candidates = [
            row for row in body[next_after:]
            if row["level"] == node["level"] and normalized(str(row["title"])) == normalized(str(node["title"]))
        ]
        if candidates:
            match = candidates[0]
            next_after = body.index(match) + 1
            mapped.append((node, match, "exact"))
        else:
            mapped.append((node, None, "missing"))
    counts = {level: sum(1 for node, _, _ in mapped if int(node["level"]) == level) for level in range(1, 5)}
    unmatched = [(node, status) for node, _, status in mapped if status != "exact"]
    print(f"TOC nodes: {len(photo)}; levels: {counts}; sequential exact mappings: {len(photo) - len(unmatched)}; unmatched titles: {len(unmatched)}")
    for node, _ in unmatched:
        print(f"UNMATCHED L{node['level']} TOC line {node['line']}: {node['title']}")
    if args.write:
        lines = ["# 中文 TOC 与正文映射核验", "", f"- 拍摄版 TOC 节点：`{len(photo)}`。", f"- 顺序精确映射：`{len(photo) - len(unmatched)}`。", f"- 未精确匹配：`{len(unmatched)}`。", "- 注：未精确匹配仅表示题名或顺序存在 OCR 异文，不能单独证明正文节点缺失；需结合段首语义抽查判断。", "", "| TOC 行 | 级别 | TOC 标题 | 正文行 | 状态 |", "|---:|---:|---|---:|---|"]
        for node, match, status in mapped:
            body_line = str(match["line"]) if match else ""
            lines.append(f"| {node['line']} | {node['level']} | {bare(str(node['title']))} | {body_line} | {status} |")
        REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
