#!/usr/bin/env python3
"""Semantic heading repair, pass 1 (Chinese body, module 1)."""

from pathlib import Path
import importlib.util

ROOT = Path(r"D:\守正公司工作区\cams考试")
FILE = ROOT / "教材、答疑记录、习题与参考文献" / "教材原文" / "v7" / "mineru提取" / "中文" / "v7_zh_mineru_merged.md"
spec = importlib.util.spec_from_file_location("repair", ROOT / "tools" / "repair_v7_chinese_heading_hierarchy.py")
repair = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(repair)


def first(lines: list[str], text: str, start: int) -> int:
    for i in range(start, len(lines)):
        if lines[i].strip().startswith(text):
            return i
    raise ValueError(f"Missing {text!r}")


def pop_heading(lines: list[str], heading: str, body: int) -> str:
    i = first(lines, heading, body)
    result = lines.pop(i)
    if i < len(lines) and not lines[i].strip():
        lines.pop(i)
    return result


def insert_before(lines: list[str], anchor: str, heading: str, body: int) -> None:
    i = first(lines, anchor, body)
    lines[i:i] = [heading, ""]


def main() -> None:
    lines = FILE.read_text(encoding="utf-8-sig").splitlines()
    body = repair.find_body_start(lines)
    toc_before = lines[:body]

    # Each title is moved directly before the first paragraph it introduces.
    fincen = pop_heading(lines, "#### 金融犯罪执法网络", body)
    insert_before(lines, "网络犯罪已被确认为", fincen, body)

    control = pop_heading(lines, "#### 反洗钱合规中的控制与所有权", body)
    insert_before(lines, "控制权与所有权在反洗钱工作中具有关键作用", control, body)
    concentration = pop_heading(lines, "#### 集中账户", body)
    insert_before(lines, "集中账户是金融机构用于将多渠道资金汇总至中央账户", concentration, body)

    # Reuse misplaced/duplicated markers for the directory nodes whose body
    # paragraphs currently have no preceding heading.
    pop_heading(lines, "#### 违反《反兴奋剂条例》的个人影响", body)
    individual = pop_heading(lines, "#### 违反 AFC 法规对个人的影响", body)
    insert_before(lines, "合规专业人士不仅需依据金融犯罪法承担法律责任", individual, body)

    trade_source = pop_heading(lines, "#### 信用卡风险", body)
    insert_before(lines, "贸易金融涵盖多种金融产品与服务", "#### 贸易金融产品与风险", body)
    card = pop_heading(lines, "#### 卡类产品风险", body)
    insert_before(lines, "零售银行与商业银行提供种类繁多的银行卡产品", card, body)

    correspondent_source = trade_source  # Retain the heading node, correcting its OCR title.
    insert_before(lines, "代理银行业务通常指一家银行在海外代理另一家银行开展业务", "#### 代理银行业务风险", body)

    asset = pop_heading(lines, "#### 资产管理人", body)
    insert_before(lines, "资产管理人或资产管理公司代表客户进行投资并管理资产", asset, body)

    if lines[:body] != toc_before:
        raise RuntimeError("TOC was modified")
    body_rows = repair.heading_rows(lines[body:])
    counts = repair.count_levels(body_rows)
    expected = {"1": 4, "2": 17, "3": 417, "4": 333, "5": 54}
    if counts != expected or repair.jumps(body_rows):
        raise RuntimeError(f"Invalid tree after pass 1: {counts}, jumps={repair.jumps(body_rows)[:3]}")
    FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("pass 1 complete", counts)


if __name__ == "__main__":
    main()
