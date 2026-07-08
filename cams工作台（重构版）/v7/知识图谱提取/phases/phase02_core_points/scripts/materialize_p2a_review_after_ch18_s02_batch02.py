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
REVIEW_BATCH = "p2a_after_CH18_S02_batch02_review_20260706"
MAIN_PREFIX = "p2a_batch_after_CH18_S02_20260706_"

SECTIONS = [
    "CH18-S03",
    "CH19-S01",
    "CH19-S02",
    "CH19-S03",
    "CH19-S04",
    "CH19-S05",
    "CH19-S06",
    "CH19-S07",
    "CH20-S01",
    "CH20-S02",
    "CH20-S03",
    "CH20-S04",
    "CH20-S05",
    "CH20-S06",
    "CH20-S07",
    "CH20-S08",
    "CH21-S01",
    "CH21-S02",
    "CH21-S03",
    "CH21-S04",
]

MANUAL_DECISIONS = {
    "CH19-S05": "保留 3 个 CP。FATF 互评估的重点/组成/演变、11 项直接目标、七阶段流程构成清楚的复习结构。",
    "CH20-S01": "保留 5 个 CP。UNOCT 内容跨段出现，但均服务联合国反恐怖融资角色，接受非连续合并。",
    "CH21-S02": "保留 2 个 CP。透明国际使命/重点与腐败指数/风险评估工具分层清楚；接受指数工具 CP 的非连续合并。",
    "CH21-S03": "保留 3 个 CP。巴塞尔治理研究所、ICAR、巴塞尔 AML 指数分别作为复习主题；接受 CP1 非连续合并。",
    "CH21-S04": "保留 2 个 CP。TJN 指数体系与客户风险评估应用分开，接受两个 CP 的非连续合并。",
}

ACCEPT_NON_CONTIGUOUS = {
    "cp_CH19_S05_001",
    "cp_CH20_S01_002",
    "cp_CH21_S02_002",
    "cp_CH21_S03_001",
    "cp_CH21_S04_001",
    "cp_CH21_S04_002",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def reviewed_core_points(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cp in parsed.get("core_points") or []:
        row = dict(cp)
        cp_id = str(row.get("draft_core_point_id"))
        row.setdefault("source_core_point_ids", [cp_id])
        if cp_id in ACCEPT_NON_CONTIGUOUS:
            row["review_flags"] = ["human_reviewed_accept_non_contiguous"]
            row["reason"] = "Human review accepted this non-contiguous grouping because it forms one useful review topic in the section."
        else:
            row["review_flags"] = ["human_reviewed_keep"]
            row.setdefault("reason", "Human review kept the P2A core_point boundary unchanged.")
        rows.append(row)
    return rows


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


def main() -> None:
    summary_rows: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for section_id in SECTIONS:
        run_dir = RUNS_DIR / f"{MAIN_PREFIX}{section_id}"
        parsed_path = run_dir / "parsed_response.json"
        if not parsed_path.exists():
            raise FileNotFoundError(parsed_path)
        parsed = read_json(parsed_path)
        core_points = reviewed_core_points(parsed)
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
        summary_rows.append({"section_id": section_id, "review_status": review_status, "core_point_count": len(core_points), "source_run": run_dir.name, "decision": decision})
        if section_id in MANUAL_DECISIONS:
            decisions.append({"section_id": section_id, "review_type": review_status, "source_core_point_ids": [cp.get("draft_core_point_id") for cp in parsed.get("core_points") or []], "result_core_point_id": None, "decision": decision, "reviewer": "human", "reviewed_at": REVIEWED_AT, "review_batch": REVIEW_BATCH})
    append_manual_decisions(decisions)
    write_review_summary(summary_rows)
    print(json.dumps({"reviewed_sections": len(summary_rows), "manual_decisions": len(decisions)}, ensure_ascii=False))


def write_review_summary(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# P2A After CH18-S02 Batch 02 Review Summary",
        "",
        f"- reviewed_at: {REVIEWED_AT}",
        f"- generated_at: {date.today().isoformat()}",
        "- scope: CH18-S03 -> CH21-S04",
        "- decision_file: inputs/p2_manual_decisions.jsonl",
        "",
        "| section_id | status | CPs | source_run | decision |",
        "|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['section_id']} | {row['review_status']} | {row['core_point_count']} | {row['source_run']} | {row['decision']} |")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "p2a_after_CH18_S02_batch02_review_summary_20260706.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
