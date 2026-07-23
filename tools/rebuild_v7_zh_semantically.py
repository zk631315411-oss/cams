#!/usr/bin/env python3
"""Rebuild the Chinese body from its semantically positioned backup headings.

The backup and current body have identical non-heading content.  The backup is
therefore used only for heading locations; the current file continues to own
the TOC and all non-heading body text.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
spec_repair = importlib.util.spec_from_file_location("repair", ROOT / "repair_v7_chinese_heading_hierarchy.py")
repair = importlib.util.module_from_spec(spec_repair)
assert spec_repair.loader
spec_repair.loader.exec_module(repair)
spec_align = importlib.util.spec_from_file_location("aligner", ROOT / "align_v7_zh_semantic_headings.py")
aligner = importlib.util.module_from_spec(spec_align)
assert spec_align.loader
spec_align.loader.exec_module(aligner)

AUDIT = repair.V7 / "v7_zh_semantic_rebuild_audit.json"
REPORT = repair.V7 / "v7_zh_semantic_rebuild_audit.md"

MISSING_TITLES = {
    "• Trade-based money laundering (TBML):": "• 基于贸易的洗钱活动（TBML）：",
    "• Commodity-based money laundering:": "• 以商品为基础的洗钱：",
    "Common techniques for money laundering": "洗钱常见技术",
    "• Shell companies and front businesses:": "• 壳公司与前台业务：",
    "Case example: Tamayo's money mules": "案例示例：Tamayo 的资金骡",
    "Case example: Komarov’s tactics": "案例示例：科马罗夫的策略",
    "Financial Crimes Enforcement Network": "金融犯罪执法网络",
    "Individual impact of violations of AFC regulations": "违反 AFC 法规对个人的影响",
    "Case example: A new corporate banking role": "案例示例：新的公司银行岗位",
    "Control and ownership for AML compliance": "反洗钱合规中的控制与所有权",
    "Concentration accounts": "集中账户",
    "Card risks": "卡类产品风险",
    "Cryptoasset risks": "加密资产风险",
    "E-commerce": "电子商务",
    "Asset managers": "资产管理人",
    "Tax avoidance versus tax evasion": "避税与逃税",
    "High-value asset risks": "高价值资产风险",
    "Alternative remittance systems": "替代汇款系统",
    "FATF-style regional bodies": "FATF 风格区域机构",
    "FATF 11 Immediate Outcomes": "FATF 11 项即时成果",
    "Case study: The 1999 Convention and UNSC resolutions for CFT": "案例研究：1999 年公约与联合国安理会 CFT 决议",
    "Organisation for Economic Co-operation and Development AFC guidance": "经济合作与发展组织 AFC 指引",
    "AFC Regulations and Regimes": "AFC 法规与制度",
    "Case example: Drafting policies for an AFC department based in APAC": "案例示例：为亚太地区 AFC 部门起草政策",
    "US AML/CFT regulatory landscape": "美国 AML/CFT 监管框架",
    "Case study: US regulatory enforcement actions": "案例研究：美国监管执法行动",
    "Major ABC regulations": "主要反贿赂和反腐败法规",
    "Case example: Using typology reports to enhance AML controls": "案例示例：利用类型学报告强化 AML 控制",
    "Control effectiveness": "控制有效性",
    "Customer risk assessment versus enterprise-wide risk assessment": "客户风险评估与企业范围风险评估",
    "Case study: Lack of governance at a Canadian bank": "案例研究：加拿大某银行治理缺失",
    "Governance and oversight": "治理与监督",
    "• EDD:": "• 强化尽职调查（EDD）：",
    "• Potential rejection:": "• 可能拒绝：",
    "• Ongoing due diligence, screening, monitoring, and KYC refresh:": "• 持续尽调、筛查、监控及 KYC 更新：",
    "Additional onboarding controls for high-risk scenarios": "高风险场景的附加入职控制",
    "Function of quality control": "质量控制职能",
    "Batch screening": "批量筛查",
    "Politically exposed persons screening": "政治暴露人士筛查",
    "Adverse media checks": "负面媒体核查",
    "Transaction monitoring versus payment screening": "交易监控与支付筛查的比较",
    "Procedures for alerts review": "预警审查程序",
    "Documenting your research": "记录你的研究",
    "Decision to file a SAR": "提交 SAR 的决定",
    "Case example: Implementing technology in AFC compliance": "案例示例：在 AFC 合规中实施技术",
    "Tools and technologies for AFC compliance": "AFC 合规工具与技术",
    "Transitioning from traditional systems to AI-based tools": "从传统系统转向基于 AI 的工具",
    "Digital onboarding technology": "数字化入职技术",
    "Technology for payment and batch screening": "支付与批量筛查技术",
    "Types of ongoing screening": "持续筛查的类型",
    "Technology for payment screening": "支付筛查技术",
    "Case example: Evolution of transaction monitoring": "案例示例：交易监控的演进",
    "Transaction monitoring and sufficient scenarios coverage": "交易监控与充分场景覆盖",
    "Ongoing testing and tuning for AI tools": "AI 工具的持续测试与调优",
    "Network analysis solutions for transaction monitoring": "交易监控的网络分析解决方案",
    "Technology to assist case management": "辅助案件管理的技术",
    "Technology for blockchain tracing": "区块链追踪技术",
    "Data lineage": "数据谱系",
    "AFC data extraction": "AFC 数据提取",
    "Case example: Analyzing customer behaviors": "案例示例：分析客户行为",
}

MISSING_TEXT_ANCHORS = {
    "• Trade-based money laundering (TBML):": "• 基于贸易的洗钱活动（TBML）：",
    "• Commodity-based money laundering:": "• 以商品为基础的洗钱：",
    "• Shell companies and front businesses:": "• 壳公司与前台业务：",
    "Case example: Tamayo's money mules": "美国司法部新闻稿披露",
    "Case example: Komarov’s tactics": "商人阿列克谢·科马罗夫",
    "Case example: A new corporate banking role": "埃琳娜是零售银行业务领域",
}

DEHEADED_OCR_FRAGMENTS = {
    "参与交易行为", "稳定币的类型包括：", "第二道防线 AFC功能", "5. 持续筛查：",
    "异常活动后仍保持账户状态", "导言：客户入会技术", "来源", "组织", "数据准备",
}


def body_start(lines: list[str]) -> int:
    return repair.find_body_start(lines)


def body_lines_equal(current: list[str], current_start: int, backup: list[str], backup_start: int) -> bool:
    current_text = [line.strip() for line in current[current_start:] if line.strip() and not repair.heading(line) and line.strip() not in DEHEADED_OCR_FRAGMENTS]
    backup_text = [line.strip() for line in backup[backup_start:] if line.strip() and not repair.heading(line) and line.strip() not in DEHEADED_OCR_FRAGMENTS]
    return current_text == backup_text


def source_target_pairs(targets: list[dict[str, object]], sources: list[dict[str, object]]) -> list[tuple[int | None, int | None]]:
    return aligner.align(targets, sources)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    current = repair.read(repair.ZH)
    backup = repair.read(Path(str(repair.ZH) + ".bak"))
    current_start = body_start(current)
    backup_start = next(index for index, line in enumerate(backup) if line == "# 浅析金融犯罪的风险与应对方法")
    if not body_lines_equal(current, current_start, backup, backup_start):
        raise RuntimeError("Backup and current non-heading body text differ; refusing to overwrite body")

    en = repair.read(repair.EN)
    en_start = repair.find_exact(en, "# Understanding the Risks and Methods of Financial Crime")
    en_glossary = repair.find_exact(en, "## Glossary", en_start)
    targets = repair.heading_rows(en[en_start:en_glossary])
    backup_glossary = repair.find_exact(backup, "## 术语表", backup_start)
    backup_pre = backup[backup_start:backup_glossary]
    photo_toc = repair.heading_rows(repair.read(repair.ZH_TOC))
    toc_titles = {repair.normalized(repair.without_page_number(str(row["title"]))) for row in photo_toc}
    backup_pre, merged = repair.merge_deterministic_splits(backup_pre, toc_titles)
    sources = repair.heading_rows(backup_pre)
    pairs = source_target_pairs(targets, sources)

    source_to_target: dict[int, int] = {}
    target_to_source: dict[int, int] = {}
    missing: list[int] = []
    extras: list[int] = []
    for target_index, source_index in pairs:
        if target_index is None:
            assert source_index is not None
            extras.append(source_index)
        elif source_index is None:
            missing.append(target_index)
        else:
            source_to_target[source_index] = target_index
            target_to_source[target_index] = source_index
    if any(str(targets[index]["title"]) not in MISSING_TITLES for index in missing):
        unresolved = [targets[index]["title"] for index in missing if str(targets[index]["title"]) not in MISSING_TITLES]
        raise RuntimeError(f"Missing Chinese titles: {unresolved}")

    source_line_to_index = {int(row["line"]) - 1: index for index, row in enumerate(sources)}
    rebuilt_pre: list[str] = []
    emitted_missing: set[int] = set()

    def emit_missing(index: int) -> None:
        rebuilt_pre.extend(["#" * int(targets[index]["level"]) + " " + MISSING_TITLES[str(targets[index]["title"])], ""])
        emitted_missing.add(index)

    for line_index, line in enumerate(backup_pre):
        source_index = source_line_to_index.get(line_index)
        if source_index is None:
            for missing_index in missing:
                anchor = MISSING_TEXT_ANCHORS.get(str(targets[missing_index]["title"]))
                if anchor and missing_index not in emitted_missing and line.strip().startswith(anchor):
                    emit_missing(missing_index)
            rebuilt_pre.append(line)
            continue
        target_index = source_to_target.get(source_index)
        if target_index is None:
            # OCR fragments that are not English structural nodes remain body text.
            parsed = repair.heading(line)
            rebuilt_pre.append(str(parsed[1]) if parsed else line)
            continue
        for missing_index in missing:
            anchor = MISSING_TEXT_ANCHORS.get(str(targets[missing_index]["title"]))
            if missing_index < target_index and missing_index not in emitted_missing and not anchor:
                emit_missing(missing_index)
        parsed = repair.heading(line)
        assert parsed
        rebuilt_pre.append("#" * int(targets[target_index]["level"]) + " " + str(parsed[1]))
    for missing_index in missing:
        if missing_index not in emitted_missing:
            emit_missing(missing_index)

    # Keep glossary definition text in its original semantic order. Existing
    # term headings are normalized to level 3; absent OCR term labels use the
    # English term names so no definition is given a fabricated Chinese label.
    english_glossary = repair.heading_rows(en[en_glossary:])
    backup_glossary_lines = backup[backup_glossary:]
    glossary_sources = repair.heading_rows(backup_glossary_lines)[1:]
    glossary_slots = repair.spread_slots(len(glossary_sources), len(english_glossary) - 1)
    source_to_slot = {source: slot for slot, source in enumerate(glossary_slots) if source is not None}
    source_line_to_index = {int(row["line"]) - 1: index for index, row in enumerate(glossary_sources)}
    glossary_missing = [slot for slot, source in enumerate(glossary_slots) if source is None]
    rebuilt_glossary = ["## 术语表"]
    emitted_glossary: set[int] = set()
    for line_index, line in enumerate(backup_glossary_lines[1:], 1):
        source_index = source_line_to_index.get(line_index)
        if source_index is None:
            rebuilt_glossary.append(line)
            continue
        slot = source_to_slot[source_index]
        for missing_slot in glossary_missing:
            if missing_slot < slot and missing_slot not in emitted_glossary:
                rebuilt_glossary.extend(["### " + str(english_glossary[missing_slot + 1]["title"]), ""])
                emitted_glossary.add(missing_slot)
        parsed = repair.heading(line)
        assert parsed
        rebuilt_glossary.append("### " + str(parsed[1]))
    for missing_slot in glossary_missing:
        if missing_slot not in emitted_glossary:
            rebuilt_glossary.extend(["### " + str(english_glossary[missing_slot + 1]["title"]), ""])

    rebuilt = current[:current_start] + rebuilt_pre + rebuilt_glossary
    rows = repair.heading_rows(rebuilt[current_start:])
    expected = {"1": 4, "2": 17, "3": 417, "4": 333, "5": 54}
    counts = repair.count_levels(rows)
    if counts != expected or repair.jumps(rows):
        raise RuntimeError(f"Invalid heading tree: counts={counts}, jumps={repair.jumps(rows)[:3]}")
    toc_start = repair.find_exact(rebuilt, "# " + str(photo_toc[0]["title"]))
    if repair.heading_rows(rebuilt[toc_start:current_start]) != photo_toc:
        raise RuntimeError("TOC was changed")
    audit = {
        "body_counts": counts,
        "structural_nodes": len(rows),
        "semantic_source": "v7_zh_mineru_merged.md.bak headings",
        "non_heading_body_text_equal_to_backup": True,
        "matched_backup_headings": len(source_to_target),
        "inserted_chinese_headings": [{"english": targets[i]["title"], "chinese": MISSING_TITLES[str(targets[i]["title"])]} for i in missing],
        "deheaded_ocr_fragments": [sources[i]["title"] for i in extras],
        "merged_ocr_heading_fragments": merged,
        "toc_entries": len(photo_toc),
        "toc_matches_photographed_directory": True,
        "toc_level_counts": repair.count_levels(photo_toc),
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(
        "# 中文正文语义重建核验\n\n"
        "- 正文标题：`# 4 / ## 17 / ### 417 / #### 333 / ##### 54`。\n"
        "- 正文非标题文本与备份稿逐行一致；标题位置采用备份稿的正文锚点。\n"
        f"- 已锚定备份标题：`{len(source_to_target)}`；补入中文结构标题：`{len(missing)}`；降为正文的 OCR 碎片：`{len(extras)}`。\n"
        "- TOC：439 条，与拍摄版逐条一致。\n",
        encoding="utf-8",
    )
    if args.write:
        repair.ZH.write_text("\n".join(rebuilt) + "\n", encoding="utf-8")
    print(json.dumps({"written": args.write, **audit}, ensure_ascii=False))


if __name__ == "__main__":
    main()
