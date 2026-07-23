#!/usr/bin/env python3
"""Semantic heading repair, pass 3 (risk assessment, QC, and data sections)."""

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


def take_heading(lines: list[str], prefix: str, body: int) -> str:
    i = find(lines, prefix, body)
    heading = lines.pop(i)
    if i < len(lines) and not lines[i].strip():
        lines.pop(i)
    return heading


def put_before(lines: list[str], prefix: str, heading: str, body: int) -> None:
    i = find(lines, prefix, body)
    lines[i:i] = [heading, ""]


def main() -> None:
    lines = FILE.read_text(encoding="utf-8-sig").splitlines()
    body = repair.find_body_start(lines)
    toc = lines[:body]

    # An OCR bullet was promoted to a title. Reuse that structural marker at
    # the product-risk-assessment definition which it actually describes.
    take_heading(lines, "#### • 客户所属行业的变化", body)
    put_before(lines, "产品风险评估有助于企业识别", "#### 产品风险评估", body)

    # The directory makes 'Quality control function' the parent topic.
    qc = take_heading(lines, "#### 质量控制职能", body)
    parent = find(lines, "### 质量控制功能", body)
    lines[parent + 1:parent + 1] = [""]
    put_before(lines, "质量控制（QC）是AFC合规框架", qc, body)

    # Re-establish the TOC's data-preparation tree and use the duplicated
    # lineage marker for the previously plain-text Data preparation subtopic.
    i = find(lines, "#### 数据准备", body)
    lines[i] = "### 数据准备"
    i = find(lines, "### 数据质量", body)
    lines[i] = "#### 数据质量"
    take_heading(lines, "#### 数据谱系", body)  # first occurrence is correct; restore it below.
    # The first data-lineage title belongs at its definition; the second was a duplicate.
    put_before(lines, "数据溯源可分为逆向追溯", "#### 数据谱系", body)
    duplicate_lineage = take_heading(lines, "#### 数据谱系", body)
    put_before(lines, "数据准备是一个包含数据收集", "#### 数据准备", body)
    extraction = take_heading(lines, "#### AFC 数据提取", body)
    put_before(lines, "数据提取前，验证规则会自动检测", extraction, body)

    if lines[:body] != toc:
        raise RuntimeError("TOC was modified")
    rows = repair.heading_rows(lines[body:])
    counts = repair.count_levels(rows)
    expected = {"1": 4, "2": 17, "3": 417, "4": 333, "5": 54}
    if counts != expected or repair.jumps(rows):
        raise RuntimeError(f"Invalid tree after pass 3: {counts}, {repair.jumps(rows)[:3]}")
    FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("pass 3 complete", counts)


if __name__ == "__main__":
    main()
