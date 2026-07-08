"""
Audit option-level textbook evidence mappings.

This script audits the mechanical step2 outputs. It does not call an LLM and it
does not change evidence labels. Any issue reported here should be fixed in the
pipeline or sent to teacher review, not hidden in the front end.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parent
OUTPUT_DIR = BASE / "output" / "step2_option_mapping"
QUESTION_MAP = OUTPUT_DIR / "question_option_card_map.json"
STATS_PATH = OUTPUT_DIR / "stats.json"
REPORT_PATH = OUTPUT_DIR / "audit_report.md"

REQUIRED_OPTION_FIELDS = [
    "option",
    "option_text",
    "is_correct_answer",
    "judgement",
    "evidence_status",
    "card_ids",
    "evidence_cards",
    "explanation",
    "common_trap",
    "needs_teacher_review",
]


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def label_order(label: str) -> tuple[int, str]:
    order = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    idx = order.find(str(label or "").strip())
    return (idx if idx >= 0 else 999, str(label or ""))


def audit(question_map: dict[str, Any], stats: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    issues: list[dict[str, Any]] = []
    lines: list[str] = []
    items = question_map.get("items", [])

    total_options = 0
    structured_options = 0
    correct_total = 0
    correct_direct = 0
    direct_options = 0
    indirect_options = 0
    none_options = 0
    needs_manual_options = 0

    for item in items:
        qid = item.get("question_id", "")
        options = item.get("options", [])
        if not isinstance(options, list):
            issues.append({"question_id": qid, "type": "options_not_list"})
            options = []

        labels = [opt.get("option", "") for opt in options if isinstance(opt, dict)]
        sorted_labels = sorted(labels, key=label_order)
        if labels != sorted_labels:
            issues.append({"question_id": qid, "type": "option_order_changed", "actual": labels, "expected": sorted_labels})

        total_options += len(options)
        for opt in options:
            if not isinstance(opt, dict):
                issues.append({"question_id": qid, "type": "option_not_object"})
                continue
            structured_options += 1
            label = opt.get("option", "")
            missing = [field for field in REQUIRED_OPTION_FIELDS if field not in opt]
            if missing:
                issues.append({"question_id": qid, "option": label, "type": "missing_fields", "fields": missing})

            evidence_status = opt.get("evidence_status", "")
            evidence_cards = opt.get("evidence_cards", [])
            card_ids = opt.get("card_ids", [])
            if not isinstance(evidence_cards, list):
                issues.append({"question_id": qid, "option": label, "type": "evidence_cards_not_list"})
                evidence_cards = []
            if not isinstance(card_ids, list):
                issues.append({"question_id": qid, "option": label, "type": "card_ids_not_list"})
                card_ids = []

            direct_options += 1 if evidence_status == "direct" else 0
            indirect_options += 1 if evidence_status == "indirect" else 0
            none_options += 1 if evidence_status == "none" else 0
            needs_manual_options += 1 if evidence_status == "needs_manual" else 0

            if evidence_status == "direct" and not evidence_cards:
                issues.append({"question_id": qid, "option": label, "type": "direct_without_evidence_cards"})
            if evidence_status == "none" and evidence_cards:
                issues.append({"question_id": qid, "option": label, "type": "none_with_evidence_cards"})
            if sorted(card_ids) != sorted([card.get("card_id") for card in evidence_cards if isinstance(card, dict)]):
                issues.append({"question_id": qid, "option": label, "type": "card_ids_mismatch_evidence_cards"})

            if opt.get("is_correct_answer"):
                correct_total += 1
                if evidence_status == "direct":
                    correct_direct += 1
                elif not opt.get("needs_teacher_review"):
                    issues.append(
                        {
                            "question_id": qid,
                            "option": label,
                            "type": "correct_option_without_direct_not_reviewed",
                            "evidence_status": evidence_status,
                        }
                    )

    hallucinated = stats.get("hallucinated_card_ids", [])
    if hallucinated:
        issues.append({"type": "hallucinated_card_ids", "count": len(hallucinated), "items": hallucinated[:20]})

    for row in stats.get("issues", []):
        issues.append({"type": "step2_issue", "detail": row})

    lines.append("# 选项级教材依据绑定审计报告")
    lines.append("")
    lines.append("## 汇总")
    lines.append("")
    lines.append(f"- 题目数：{len(items)}")
    lines.append(f"- 选项数：{total_options}")
    lines.append(f"- 结构化选项数：{structured_options}")
    lines.append(f"- direct 选项：{direct_options}")
    lines.append(f"- indirect 选项：{indirect_options}")
    lines.append(f"- none 选项：{none_options}")
    lines.append(f"- needs_manual 选项：{needs_manual_options}")
    lines.append(f"- 正确选项 direct 覆盖：{correct_direct}/{correct_total}")
    lines.append(f"- 幻觉 card_id：{len(hallucinated)}")
    lines.append(f"- 审计问题数：{len(issues)}")
    lines.append("")
    lines.append("## 判断")
    lines.append("")
    if not issues:
        lines.append("通过当前机器审计。仍需教研抽查 direct 证据是否语义充分。")
    else:
        lines.append("未完全通过。以下问题需要处理或进入教研复核。")

    lines.append("")
    lines.append("## 问题明细")
    lines.append("")
    if not issues:
        lines.append("无。")
    else:
        for idx, issue in enumerate(issues, start=1):
            qid = issue.get("question_id", "-")
            option = issue.get("option", "-")
            typ = issue.get("type", "unknown")
            lines.append(f"{idx}. `{typ}` · 题 `{qid}` · 选项 `{option}`")
            detail = {k: v for k, v in issue.items() if k not in {"type", "question_id", "option"}}
            if detail:
                lines.append(f"   - {json.dumps(detail, ensure_ascii=False)}")

    lines.append("")
    lines.append("## 备注")
    lines.append("")
    lines.append("- 本审计只检查结构和引用合法性，不替代教研对解析质量的判断。")
    lines.append("- `kg_data.json`、`card_relations.json` 只允许作为召回辅助，不是最终教材证据。")
    lines.append("- `cards_ch2.json`、`cards_v6_sentence.json` 均为教材句卡，不是考点卡。")

    return issues, "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit option-level question/card mappings.")
    parser.parse_args(argv)

    question_map = read_json(QUESTION_MAP)
    stats = read_json(STATS_PATH)
    issues, report = audit(question_map, stats)
    write_text(REPORT_PATH, report)
    print(report)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
