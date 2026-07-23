#!/usr/bin/env python3
"""Dry-run semantic alignment of English body headings to Chinese backup headings."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path


spec = importlib.util.spec_from_file_location("repair", Path(__file__).with_name("repair_v7_chinese_heading_hierarchy.py"))
repair = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(repair)

OUT = repair.V7 / "v7_zh_semantic_alignment_dry_run.json"

FORCED_TRANSLATIONS = {
    "Card risks": "信用卡风险",
    "E-commerce": "电子商务",
    "Asset managers": "资产管理人",
    "Tax avoidance versus tax evasion": "避税与逃税",
    "High-value asset risks": "高价值资产风险",
    "Alternative remittance systems": "替代汇款系统",
    "FATF 11 Immediate Outcomes": "FATF 11",
    "Organisation for Economic Co-operation and Development AFC guidance": "经济合作与发展组织",
    "AFC Regulations and Regimes": "AFC法规与制度",
    "Major ABC regulations": "主要ABC法规",
    "Control effectiveness": "控制有效性",
    "Customer risk assessment versus enterprise-wide risk assessment": "客户风险评估与企业范围风险评估",
    "Governance and oversight": "治理和监督",
    "Batch screening": "批量筛查",
    "Adverse media checks": "负面媒体核查",
    "Transaction monitoring versus payment screening": "交易监控与支付筛查",
    "Procedures for alerts review": "警报审查程序",
    "Documenting your research": "记录你的研究",
    "Decision to file a SAR": "提交SAR的决定",
    "Tools and technologies for AFC compliance": "AFC合规性工具与技术",
    "Transitioning from traditional systems to AI-based tools": "传统系统",
    "Digital onboarding technology": "数字化入职技术",
    "Technology for payment and batch screening": "支付与批量筛查技术",
    "Types of ongoing screening": "持续筛查",
    "Technology for payment screening": "支付筛查技术",
    "Case example: Evolution of transaction monitoring": "交易监控的演变",
    "Transaction monitoring and sufficient scenarios coverage": "交易监控与充分场景覆盖",
    "Ongoing testing and tuning for AI tools": "人工智能工具",
    "Network analysis solutions for transaction monitoring": "网络分析解决方案",
    "Technology to assist case management": "病例管理",
    "Technology for blockchain tracing": "区块链溯源",
    "Data lineage": "数据谱系",
    "AFC data extraction": "AFC数据提取",
    "Case example: Analyzing customer behaviors": "客户行为分析",
}


def semantic_score(en: str, zh: str, ti: int, si: int, tn: int, sn: int) -> float:
    en_low = en.lower()
    score = -abs(ti / max(tn - 1, 1) - si / max(sn - 1, 1)) * 35
    if en == "Key takeaways":
        return score + (60 if "关键要点" in zh else -20)
    if en == "Introduction":
        return score + (55 if "引言" in zh else -20)
    if en_low.startswith("introduction:"):
        return score + (50 if "引言" in zh or "导言" in zh else -18)
    if "case example" in en_low:
        score += 30 if "案例" in zh or "病例" in zh else -8
    if "student note" in en_low:
        score += 30 if "学生" in zh else -8
    forced_pairs = {
        ("Common techniques for money laundering", "洗钱常见技术"),
        ("AFC Regulations and Regimes", "AFC 法规与制度"),
    }
    if (en, zh) in forced_pairs:
        score += 100
    # General translated-title hints are intentionally not used as hard
    # matches: common terms such as "数据" and "技术" can otherwise pull a
    # heading away from its neighbouring body block.
    hints = {
        "money laundering": "洗钱", "financial crime": "金融犯罪", "sanction": "制裁",
        "common techniques": "常见技术", "trade-based": "贸易", "commodity": "商品",
        "shell companies": "壳", "tamayo": "Tamayo", "komarov": "科马罗夫",
        "predicate": "从犯", "types of financial": "金融犯罪的类型",
        "bribery": "贿赂", "corruption": "腐败", "cyber": "网络", "environment": "环境",
        "drug": "贩毒", "terror": "恐怖", "bank": "银行", "retail": "零售",
        "commercial": "商业", "private": "私人", "wealth": "财富", "trust": "信托",
        "offshore": "离岸", "insurance": "保险", "securities": "证券", "brokerage": "经纪",
        "crypto": "加密", "fintech": "金融科技", "real estate": "房地产", "gaming": "游戏",
        "guidance": "指南", "standard": "标准", "risk assessment": "风险评估",
        "governance": "治理", "investigation": "调查", "screening": "筛查",
        "technology": "技术", "data": "数据", "transaction": "交易", "report": "报告",
        "capital markets": "资本市场", "correspondent": "代理银行", "e-commerce": "电子商务",
        "asset managers": "资产管理人", "credit unions": "信用合作社", "concentration": "集中账户",
    }
    for needle, translation in hints.items():
        if needle in en_low and translation in zh:
            score += 8
    if "risk" in en_low and "风险" in zh:
        score += 4
    en_codes = set(re.findall(r"\b[A-Z][A-Z0-9/\-]{1,}\b", en))
    zh_codes = set(re.findall(r"\b[A-Z][A-Z0-9/\-]{1,}\b", zh))
    score += 10 * len(en_codes & zh_codes)
    return score


def align(targets: list[dict[str, object]], sources: list[dict[str, object]]) -> list[tuple[int | None, int | None]]:
    n, m = len(targets), len(sources)
    skip = -5.0
    dp = [[float("-inf")] * (m + 1) for _ in range(n + 1)]
    step: list[list[str]] = [[""] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + skip
        step[i][0] = "t"
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + skip
        step[0][j] = "s"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            match = dp[i - 1][j - 1] + semantic_score(
                str(targets[i - 1]["title"]), str(sources[j - 1]["title"]), i - 1, j - 1, n, m
            )
            skip_target = dp[i - 1][j] + skip
            skip_source = dp[i][j - 1] + skip
            best, kind = max((match, "m"), (skip_target, "t"), (skip_source, "s"), key=lambda item: item[0])
            dp[i][j], step[i][j] = best, kind
    result: list[tuple[int | None, int | None]] = []
    i, j = n, m
    while i or j:
        kind = step[i][j]
        if kind == "m":
            result.append((i - 1, j - 1)); i -= 1; j -= 1
        elif kind == "t":
            result.append((i - 1, None)); i -= 1
        else:
            result.append((None, j - 1)); j -= 1
    return list(reversed(result))


def main() -> None:
    en = repair.read(repair.EN)
    backup = repair.read(Path(str(repair.ZH) + ".bak"))
    en_start = repair.find_exact(en, "# Understanding the Risks and Methods of Financial Crime")
    en_glossary = repair.find_exact(en, "## Glossary", en_start)
    targets = repair.heading_rows(en[en_start:en_glossary])
    backup_start = next(index for index, line in enumerate(backup) if line == "# 浅析金融犯罪的风险与应对方法")
    backup_glossary = repair.find_exact(backup, "## 术语表", backup_start)
    sources = repair.heading_rows(backup[backup_start:backup_glossary])
    pairs = align(targets, sources)
    rows = []
    for target_index, source_index in pairs:
        item: dict[str, object] = {"target_index": target_index, "source_index": source_index}
        if target_index is not None:
            item["english"] = targets[target_index]["title"]
            item["english_level"] = targets[target_index]["level"]
        if source_index is not None:
            item["chinese"] = sources[source_index]["title"]
            item["backup_line"] = int(sources[source_index]["line"]) + backup_start - 1
        if target_index is not None and source_index is not None:
            item["score"] = round(semantic_score(str(item["english"]), str(item["chinese"]), target_index, source_index, len(targets), len(sources)), 2)
        rows.append(item)
    OUT.write_text(json.dumps({"targets": len(targets), "sources": len(sources), "alignment": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"targets": len(targets), "sources": len(sources), "matched": sum(x[0] is not None and x[1] is not None for x in pairs), "missing_targets": sum(x[0] is not None and x[1] is None for x in pairs), "extra_sources": sum(x[0] is None and x[1] is not None for x in pairs), "output": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
