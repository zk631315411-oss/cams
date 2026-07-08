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
REVIEW_BATCH = "p2a_after_CH30_S05_batch05_review_20260706"
MAIN_PREFIX = "p2a_batch_after_CH30_S05_20260706_"

SECTIONS = [
    "CH31-S01",
    "CH31-S02",
    "CH31-S03",
    "CH31-S04",
    "CH31-S05",
    "CH31-S06",
    "CH31-S07",
    "CH31-S08",
    "CH32-S01",
    "CH32-S02",
    "CH32-S03",
    "CH32-S04",
    "CH32-S05",
    "CH33-S01",
    "CH33-S02",
    "CH33-S03",
    "CH33-S04",
    "CH33-S05",
    "CH34-S01",
    "CH34-S02",
]

MANUAL_DECISIONS = {
    "CH31-S01": "保留 5 个 CP。监管、执法、执法权限、FIU、机构合作五个复习主题边界清楚。",
    "CH31-S05": "保留 5 个 CP。FIU职责、操作分析、分析深度、信息来源/国际共享、情报可采性五个主题可用。",
    "CH31-S06": "保留 1 个 CP。该小节是 FIU 与执法合作案例，整体作为案例型 CP。",
    "CH31-S08": "保留 4 个 CP。司法协助工具、局限、EIO、私营调查员保密问题四个主题可用。",
    "CH32-S02": "保留 1 个 CP。AUSTRAC Fintel Alliance 是单一案例型小节。",
    "CH32-S04": "保留 1 个 CP。私营部门合作形式与合规要求在该节内服务同一复习主题。",
    "CH33-S05": "保留 6 个 CP。五大支柱概述和五个支柱分别成点，符合教材复习结构。",
    "CH34-S02": "保留 3 个 CP。第一道防线、风险管理结构变化、前台/中台角色三个主题可用，接受结构变化 CP 的较宽边界。",
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
        "# P2A After CH30-S05 Batch 05 Review Summary",
        "",
        f"- reviewed_at: {REVIEWED_AT}",
        f"- generated_at: {date.today().isoformat()}",
        "- scope: CH31-S01 -> CH34-S02",
        "- decision_file: inputs/p2_manual_decisions.jsonl",
        "- decision: no CP split in this batch; flagged boundaries accepted after sampling",
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
    (REPORTS_DIR / "p2a_after_CH30_S05_batch05_review_summary_20260706.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
