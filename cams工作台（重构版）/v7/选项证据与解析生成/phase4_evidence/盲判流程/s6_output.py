# -*- coding: utf-8 -*-
"""s6 — 输出：写 JSON/MD/JSONL。"""

from __future__ import annotations

import json, time
from collections import Counter
from pathlib import Path
from typing import Any

from s1_indexing import _append_unique


def write_question_json(result: dict[str, Any], output_dir: Path) -> None:
    qid = result["question_id"]
    path = output_dir / "questions" / f"q_{qid}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def write_summary_jsonl(results: list[dict[str, Any]], output_dir: Path) -> None:
    path = output_dir / "blind_judgment_results.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for r in results:
            summary = {
                "question_id": r.get("question_id", ""),
                "predicted_answer": r.get("predicted_answer", []),
                "pipeline_status": r.get("pipeline_status", "?"),
                "candidates": len(r.get("candidate_pool", [])),
                "issues": len(r.get("validation_checks", []) or []),
                "error_traceback": r.get("error_traceback", ""),
            }
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")


def write_markdown_report(results: list[dict[str, Any]], output_dir: Path) -> None:
    """写入可读的 Markdown 报告。"""
    total = len(results)
    ok_count = sum(1 for r in results if r.get("pipeline_status") == "ok")
    pf_count = sum(1 for r in results if r.get("pipeline_status") == "llm_parse_failed")
    issue_counts = Counter()
    for r in results:
        for issue in r.get("validation_checks", []) or []:
            issue_counts[str(issue)[:120]] += 1

    lines = [
        "# 盲判报告\n",
        f"生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n",
        f"## 总结\n\n",
        f"总题数: {total} | ok: {ok_count} | llm_parse_failed: {pf_count}\n\n",
        f"## 校验问题分布\n\n",
    ]
    for issue, count in issue_counts.most_common(30):
        lines.append(f"- [{count}x] {issue}\n")

    lines.append(f"\n## 每题详情\n\n")
    for r in results:
        qid = r.get("question_id", "")
        status = r.get("pipeline_status", "?")
        predicted = "、".join(str(x) for x in r.get("predicted_answer", []) or [])
        issues = r.get("validation_checks", []) or []
        lines.append(f"### {qid} [{status}] predicted={predicted}\n")
        for issue in issues:
            lines.append(f"- {issue}\n")
        lines.append("")

    path = output_dir / "blind_judgment_report.md"
    path.write_text("".join(lines), encoding="utf-8")
