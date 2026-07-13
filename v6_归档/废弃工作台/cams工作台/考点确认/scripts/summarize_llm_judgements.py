from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
WORK_DIR = SCRIPT_DIR.parent


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def latest_by_question(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        qid = row.get("question_id")
        if qid:
            by_id[qid] = row
    return [by_id[qid] for qid in sorted(by_id)]


def render(rows: list[dict[str, Any]]) -> str:
    rows = latest_by_question(rows)
    ok = [row for row in rows if row.get("status") == "ok"]
    bad = [row for row in rows if row.get("status") != "ok"]
    validation_bad = [row for row in rows if row.get("validation_errors")]

    point_counts = Counter()
    trap_counts = Counter()
    point_type_counts = Counter()
    confidence_counts = Counter()
    titles = Counter()
    core_card_sets = Counter()

    for row in ok:
        result = row.get("result") or {}
        exam_points = result.get("exam_points") or []
        trap_notes = result.get("trap_notes") or []
        point_counts[len(exam_points)] += 1
        trap_counts[len(trap_notes)] += 1
        for point in exam_points:
            point_type_counts[point.get("point_type") or ""] += 1
            confidence_counts[point.get("confidence") or ""] += 1
            if point.get("title"):
                titles[point["title"]] += 1
            core_key = ",".join(sorted(point.get("core_card_ids") or []))
            if core_key:
                core_card_sets[core_key] += 1

    lines = [
        "# LLM 考点判断全量统计",
        "",
        f"- 题目数：{len(rows)}",
        f"- 成功：{len(ok)}",
        f"- 失败：{len(bad)}",
        f"- 校验异常：{len(validation_bad)}",
        "",
        "## 正式考点数量分布",
        "",
    ]
    for count, total in sorted(point_counts.items()):
        lines.append(f"- {count} 个正式考点：{total} 题")

    lines += ["", "## 易错辨析数量分布", ""]
    for count, total in sorted(trap_counts.items()):
        lines.append(f"- {count} 条易错辨析：{total} 题")

    lines += ["", "## 正式考点类型", ""]
    for name, total in point_type_counts.most_common():
        lines.append(f"- {name}: {total}")

    lines += ["", "## 置信度", ""]
    for name, total in confidence_counts.most_common():
        lines.append(f"- {name}: {total}")

    duplicate_titles = [(title, count) for title, count in titles.items() if count > 1]
    duplicate_core_sets = [(core, count) for core, count in core_card_sets.items() if count > 1]
    lines += ["", "## 重复信号", ""]
    lines.append(f"- 重复标题：{len(duplicate_titles)}")
    for title, count in duplicate_titles[:10]:
        lines.append(f"  - {title}: {count}")
    lines.append(f"- 重复主卡组合：{len(duplicate_core_sets)}")
    for core, count in duplicate_core_sets[:10]:
        lines.append(f"  - {core}: {count}")

    watch_rows = []
    for row in ok:
        result = row.get("result") or {}
        exam_points = result.get("exam_points") or []
        trap_notes = result.get("trap_notes") or []
        reasons = []
        if len(exam_points) != 1:
            reasons.append(f"{len(exam_points)} 个正式考点")
        if len(trap_notes) > 2:
            reasons.append(f"{len(trap_notes)} 条易错辨析")
        for point in exam_points:
            if point.get("point_type") == "textbook_note":
                reasons.append("正式考点类型为 textbook_note")
            if point.get("confidence") != "high":
                reasons.append(f"置信度 {point.get('confidence')}")
            if len(point.get("core_card_ids") or []) > 3:
                reasons.append("主卡超过 3 张")
        if reasons:
            watch_rows.append((row, reasons))

    lines += ["", "## 建议复看题目", ""]
    if not watch_rows:
        lines.append("- 无")
    for row, reasons in watch_rows:
        result = row.get("result") or {}
        titles_text = "；".join(point.get("title") or "" for point in result.get("exam_points") or [])
        lines.append(f"- {row.get('question_id')}: {'；'.join(reasons)} | {titles_text}")

    if validation_bad:
        lines += ["", "## 校验异常详情", ""]
        for row in validation_bad:
            lines.append(f"- {row.get('question_id')}: {'; '.join(row.get('validation_errors') or [])}")

    if bad:
        lines += ["", "## 失败详情", ""]
        for row in bad:
            lines.append(f"- {row.get('question_id')}: {row.get('error')}")

    lines += ["", "## 全量题目概览", ""]
    for row in ok:
        result = row.get("result") or {}
        lines.append(f"### {row.get('question_id')} {result.get('exam_intent') or ''}")
        for point in result.get("exam_points") or []:
            lines.append(
                f"- 正式考点：{point.get('title') or ''} | {point.get('point_type') or ''} | 主卡：{', '.join(point.get('core_card_ids') or [])} | 辅助：{', '.join(point.get('supporting_card_ids') or [])}"
            )
        for note in result.get("trap_notes") or []:
            lines.append(f"- 易错：{note.get('title') or ''} | 卡：{', '.join(note.get('trap_card_ids') or [])}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize LLM role judgement results.")
    parser.add_argument("--work-dir", type=Path, default=WORK_DIR)
    parser.add_argument("--input", type=Path, default=None)
    args = parser.parse_args()

    input_path = args.input or args.work_dir / "outputs" / "llm_role_judgements.sample.jsonl"
    rows = read_jsonl(input_path)
    report = render(rows)
    out_path = args.work_dir / "reports" / "llm_judgement_full_summary.md"
    out_path.write_text(report, encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
