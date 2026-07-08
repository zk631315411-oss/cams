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
REVIEW_BATCH = "p2a_after_CH24_S17_batch04_review_20260706"
MAIN_PREFIX = "p2a_batch_after_CH24_S17_20260706_"

SECTIONS = [
    "CH24-S18",
    "CH25-S01",
    "CH25-S02",
    "CH25-S03",
    "CH26-S01",
    "CH26-S02",
    "CH26-S03",
    "CH26-S04",
    "CH26-S05",
    "CH26-S06",
    "CH26-S07",
    "CH26-S08",
    "CH27-S01",
    "CH28-S01",
    "CH29-S01",
    "CH30-S01",
    "CH30-S02",
    "CH30-S03",
    "CH30-S04",
    "CH30-S05",
]

MANUAL_DECISIONS = {
    "CH24-S18": "保留 3 个 CP。阿联酋法令、合规义务、国家战略三类复习主题清楚，接受合规义务 CP 的非连续归并。",
    "CH26-S01": "保留 4 个 CP。数据隐私、AML数据使用、隐私增强技术与金融犯罪风险之间边界可用。",
    "CH26-S04": "保留 4 个 CP。GDPR 与 AML 的平衡主题存在回指，但按合规义务、数据主体权利、合法依据、特殊类别数据拆分可用。",
    "CH26-S05": "保留 2 个 CP。消费者保护与普惠金融两个复习主题清楚。",
    "CH26-S06": "保留 3 个 CP。AI 风险、治理原则、模型风险控制三个主题可用。",
    "CH26-S08": "保留 5 个 CP。ESG 基础、联合国倡议、AML/CFT 交叉、融合价值、风险为本方法五个主题可用，接受局部非连续归并。",
    "CH30-S01": "保留 2 个 CP。报告/指引的使用方式与治理落地两个主题可用。",
    "CH30-S02": "保留 1 个 CP。恐怖融资红旗案例是单一案例型小节。",
    "CH30-S04": "保留 3 个 CP。国家、行业/专题、政策行动计划三个层次清楚，接受 NRA CP 的较宽边界。",
    "CH30-S05": "保留 1 个 CP。DeFi 风险评估案例是单一案例型小节。",
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
        "# P2A After CH24-S17 Batch 04 Review Summary",
        "",
        f"- reviewed_at: {REVIEWED_AT}",
        f"- generated_at: {date.today().isoformat()}",
        "- scope: CH24-S18 -> CH30-S05",
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
    (REPORTS_DIR / "p2a_after_CH24_S17_batch04_review_summary_20260706.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    summary_rows: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for section_id in SECTIONS:
        run_dir = RUNS_DIR / f"{MAIN_PREFIX}{section_id}"
        parsed_path = run_dir / "parsed_response.json"
        if not parsed_path.exists():
            raise FileNotFoundError(parsed_path)
        parsed = read_json(parsed_path)
        core_points = [reviewed_keep(item) for item in parsed.get("core_points") or []]
        flagged_count = sum(1 for item in parsed.get("core_points") or [] if item.get("review_flags"))
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
                    "source_core_point_ids": [cp.get("draft_core_point_id") for cp in parsed.get("core_points") or []],
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
