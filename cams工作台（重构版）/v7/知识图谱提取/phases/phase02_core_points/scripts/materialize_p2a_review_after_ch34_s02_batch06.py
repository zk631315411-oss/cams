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
REVIEW_BATCH = "p2a_after_CH34_S02_batch06_review_20260706"
MAIN_PREFIX = "p2a_batch_after_CH34_S02_20260706_"

SECTIONS = [
    "CH34-S03",
    "CH34-S04",
    "CH34-S05",
    "CH34-S06",
    "CH34-S07",
    "CH34-S08",
    "CH34-S09",
    "CH34-S10",
    "CH34-S11",
    "CH34-S12",
    "CH35-S01",
    "CH35-S02",
    "CH35-S03",
    "CH33-S06",
    "CH33-S07",
    "CH36-S01",
    "CH36-S02",
    "CH36-S03",
    "CH36-S04",
    "CH36-S05",
]

MANUAL_DECISIONS = {
    "CH33-S07": "保留 2 个 CP。SAFS 案例本身作为案例型 CP，另保留企业风险评估重要性总结 CP。",
    "CH34-S05": "保留 2 个 CP。QC 与 QA/合规监控是相邻但不同的复习主题，接受共享背景 unit。",
    "CH34-S08": "保留 2 个 CP。两个公司重组案例分别成点，边界清楚。",
    "CH34-S12": "保留 3 个 CP。董事会、高级管理层/业务领导者、治理结构价值三类职责清楚。",
    "CH35-S01": "保留 4 个 CP。第二道防线协作、互动要素、合规文化、RACI/决策权四个主题可用。",
    "CH35-S02": "保留 8 个 CP。该节按第二道防线与各职能互动逐项展开，枚举项逐个成点合理。",
    "CH35-S03": "保留 1 个 CP。建立合规文化是该节唯一主线，接受非连续归并。",
    "CH36-S01": "保留 7 个 CP。风险评估重要性、三类风险评估、各类评估说明和收益边界清楚。",
    "CH36-S02": "保留 8 个 CP。该节是组织内风险评估类型枚举，各类型独立成点合理。",
    "CH36-S03": "保留 5 个 CP。RBA定义、风险偏好、CRA、有效RBA要求、风险管理流程五个主题可用，接受 CRA 和有效RBA要求的非连续归并。",
    "CH36-S05": "保留 3 个 CP。RAS定义、准备步骤、监管规则/零容忍偏好三个主题可用。",
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
        "# P2A After CH34-S02 Batch 06 Review Summary",
        "",
        f"- reviewed_at: {REVIEWED_AT}",
        f"- generated_at: {date.today().isoformat()}",
        "- scope: CH34-S03 -> CH36-S05",
        "- decision_file: inputs/p2_manual_decisions.jsonl",
        "- decision: no CP split in this batch; high-count sections are mostly enumeration structures",
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
    (REPORTS_DIR / "p2a_after_CH34_S02_batch06_review_summary_20260706.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
