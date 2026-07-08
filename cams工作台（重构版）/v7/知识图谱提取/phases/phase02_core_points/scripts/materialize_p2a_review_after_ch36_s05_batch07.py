from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
RUNS_DIR = PHASE_DIR / "runs"
OUTPUTS_DIR = PHASE_DIR / "outputs"
INPUTS_DIR = PHASE_DIR / "inputs"
REPORTS_DIR = PHASE_DIR / "reports"

REVIEWED_AT = "2026-07-06"
REVIEW_BATCH = "p2a_after_CH36_S05_batch07_review_20260706"
MAIN_PREFIX = "p2a_batch_after_CH36_S05_20260706_"

SECTIONS = [
    "CH37-S01",
    "CH37-S02",
    "CH37-S03",
    "CH37-S04",
    "CH37-S05",
    "CH37-S06",
    "CH38-S01",
    "CH39-S01",
    "CH40-S01",
    "CH40-S02",
    "CH41-S01",
    "CH41-S02",
    "CH41-S03",
    "CH41-S04",
    "CH41-S05",
    "CH41-S06",
    "CH41-S07",
    "CH41-S08",
    "CH41-S09",
    "CH41-S10",
    "CH41-S11",
    "CH41-S12",
    "CH42-S01",
    "CH42-S02",
    "CH42-S03",
    "CH42-S04",
    "CH42-S05",
    "CH42-S06",
    "CH42-S07",
    "CH42-S08",
]

MANUAL_DECISIONS = {
    "CH37-S02": "保留补跑后的 5 个 CP。固有风险、风险确定流程、控制策略、控制类型、控制有效性五个主题清楚。",
    "CH37-S03": "保留 4 个 CP。剩余风险、控制有效性重要性、设计有效性、运营有效性四个主题可用。",
    "CH37-S05": "保留 1 个 CP。风险评估工具的评分、输入和定制化服务同一复习主题。",
    "CH37-S06": "保留 3 个 CP。报告对象/责任、报告职责、报告价值三类主题可用。",
    "CH38-S01": "保留 3 个 CP。持续评估、CRA要求、产品和渠道风险评估三类主题清楚。",
    "CH39-S01": "保留补跑后的 3 个 CP。CRA/EWRA、产品风险因素评分、产品风险评估流程三类主题可用。",
    "CH40-S01": "保留 1 个 CP。金融犯罪防控计划基础是短节单一主线。",
    "CH41-S02": "保留 9 个 CP。该节按政策/程序定义、治理、实施、风险为本、例外、过渡期和益处展开，细项粒度合理。",
    "CH41-S08": "保留 2 个 CP。英国监管报告和监管机构互动两个主题可用，接受局部非连续归并。",
    "CH41-S09": "保留 1 个 CP。开户时 KYC/CDD 控制是单一生命周期控制主题。",
    "CH42-S02": "保留 1 个 CP。客户风险评估与尽职调查在该短节内为同一主线。",
    "CH42-S07": "保留 5 个 CP。自然人KYC、CIP、CDD、EDD、风险为本方法五个主题边界清楚。",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def reviewed_keep(row: dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    cp_id = str(item.get("draft_core_point_id"))
    original_flags = list(item.get("review_flags") or [])
    item.setdefault("source_core_point_ids", [cp_id])
    if original_flags:
        item["review_flags"] = ["human_reviewed_accept_flagged_boundary", *original_flags]
        item["reason"] = "Human review accepted the P2A boundary after checking the section-level review topic."
    else:
        item["review_flags"] = ["human_reviewed_keep"]
        item.setdefault("reason", "Human review kept the P2A core_point boundary unchanged.")
    return item


def append_manual_decisions(decisions: list[dict[str, Any]]) -> None:
    path = INPUTS_DIR / "p2_manual_decisions.jsonl"
    existing_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    existing_keys = set()
    for line in existing_lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        existing_keys.add((row.get("review_batch"), row.get("section_id"), row.get("review_type")))
    new_lines = list(existing_lines)
    for row in decisions:
        key = (row.get("review_batch"), row.get("section_id"), row.get("review_type"))
        if key in existing_keys:
            continue
        new_lines.append(json.dumps(row, ensure_ascii=False))
        existing_keys.add(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def write_review_summary(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# P2A After CH36-S05 Batch 07 Review Summary",
        "",
        f"- reviewed_at: {REVIEWED_AT}",
        f"- generated_at: {date.today().isoformat()}",
        "- scope: CH37-S01 -> CH42-S08",
        "- decision_file: inputs/p2_manual_decisions.jsonl",
        "- decision: no CP split in this batch; CH37-S02 and CH39-S01 were rerun and accepted",
        "",
        "| section_id | status | CPs | flagged CPs | source_run | decision |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['section_id']} | {row['review_status']} | {row['core_point_count']} | "
            f"{row['flagged_core_point_count']} | {row['source_run']} | {row['decision']} |"
        )
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "p2a_after_CH36_S05_batch07_review_summary_20260706.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    summary_rows: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for section_id in SECTIONS:
        run_dir = RUNS_DIR / f"{MAIN_PREFIX}{section_id}"
        parsed_path = run_dir / "parsed_response.json"
        if not parsed_path.exists():
            raise FileNotFoundError(parsed_path)
        parsed = read_json(parsed_path)
        raw_core_points = parsed.get("core_points") or []
        core_points = [reviewed_keep(item) for item in raw_core_points]
        flagged_count = sum(1 for item in raw_core_points if item.get("review_flags"))
        review_status = "reviewed_manual_keep" if section_id in MANUAL_DECISIONS else "reviewed_keep"
        reviewed = {
            "section_id": section_id,
            "review_source": "inputs/p2_manual_decisions.jsonl",
            "source_p2a_run": str(parsed_path.relative_to(PHASE_DIR)),
            "reviewed_at": REVIEWED_AT,
            "review_batch": REVIEW_BATCH,
            "review_status": review_status,
            "core_points": core_points,
            "retired_core_point_ids": [],
        }
        write_json(OUTPUTS_DIR / f"p2a_reviewed_core_points.{section_id}.json", reviewed)
        decision = MANUAL_DECISIONS.get(section_id, "人工审核后确认 P2A CP 边界可用，保持不改。")
        summary_rows.append(
            {
                "section_id": section_id,
                "review_status": review_status,
                "core_point_count": len(core_points),
                "flagged_core_point_count": flagged_count,
                "source_run": run_dir.name,
                "decision": decision,
            }
        )
        if section_id in MANUAL_DECISIONS:
            decisions.append(
                {
                    "section_id": section_id,
                    "review_type": review_status,
                    "source_core_point_ids": [cp.get("draft_core_point_id") for cp in raw_core_points],
                    "result_core_point_id": None,
                    "decision": decision,
                    "reviewer": "human",
                    "reviewed_at": REVIEWED_AT,
                    "review_batch": REVIEW_BATCH,
                }
            )
    append_manual_decisions(decisions)
    write_review_summary(summary_rows)
    print(json.dumps({"reviewed_sections": len(summary_rows), "manual_decisions": len(decisions)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
