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
REVIEW_BATCH = "p2a_after_CH13_S01_batch01_review_20260706"
MAIN_PREFIX = "p2a_batch_after_CH13_S01_20260706_"
RETRY_RUNS = {"CH16-S01": "p2a_retry_after_CH13_S01_20260706_CH16-S01"}

SECTIONS = [
    "CH13-S02",
    "CH13-S03",
    "CH13-S04",
    "CH14-S01",
    "CH14-S02",
    "CH15-S01",
    "CH15-S02",
    "CH15-S03",
    "CH15-S04",
    "CH16-S01",
    "CH16-S02",
    "CH16-S03",
    "CH16-S04",
    "CH16-S05",
    "CH16-S06",
    "CH16-S07",
    "CH17-S01",
    "CH17-S02",
    "CH18-S01",
    "CH18-S02",
]

MANUAL_DECISIONS = {
    "CH13-S03": "保留 1 个 CP。CBDC 的定义、发行理由和国家示例共同构成一个小节复习主题，接受非连续合并。",
    "CH13-S04": "保留 3 个 CP。CP3 将混合器洗钱风险与 VASP 尽职调查合并，属于同一风险控制主题。",
    "CH15-S02": "保留 6 个 CP。博彩业风险按行业概况、固有风险、在线博彩、实体赌场、赌团和常见威胁拆分，粒度可用。",
    "CH15-S03": "保留 3 个 CP。房地产风险、会计审计风险、法律行业风险分别对应 DNFBP 三类主题；接受房地产 CP 中风险与缓解措施的非连续合并。",
    "CH16-S01": "采用补跑结果，保留 2 个 CP：高价值资产洗钱风险与尽职调查措施、高价值资产洗钱红旗信号。",
    "CH16-S04": "保留 1 个 CP。自由贸易区的定义、便利条件和犯罪利用风险在本节服务同一复习主题。",
    "CH16-S07": "保留 3 个 CP。军事组织、军事/两用商品、军事交易金融犯罪风险三层结构清楚；接受 CP2 的非连续合并。",
    "CH18-S01": "保留 1 个 CP。该节是全球 AFC 框架和国际机构的导入性小节，不强行拆细。",
}

ACCEPT_NON_CONTIGUOUS = {
    "cp_CH13_S03_001",
    "cp_CH13_S04_003",
    "cp_CH15_S02_001",
    "cp_CH15_S02_004",
    "cp_CH15_S03_001",
    "cp_CH16_S01_001",
    "cp_CH16_S04_001",
    "cp_CH16_S07_002",
    "cp_CH18_S01_001",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def source_run(section_id: str) -> Path:
    run_name = RETRY_RUNS.get(section_id, f"{MAIN_PREFIX}{section_id}")
    return RUNS_DIR / run_name


def reviewed_core_points(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    reviewed: list[dict[str, Any]] = []
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
        reviewed.append(row)
    return reviewed


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
        run_dir = source_run(section_id)
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
        summary_rows.append(
            {
                "section_id": section_id,
                "review_status": review_status,
                "core_point_count": len(core_points),
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


def write_review_summary(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# P2A After CH13-S01 Batch 01 Review Summary",
        "",
        f"- reviewed_at: {REVIEWED_AT}",
        f"- generated_at: {date.today().isoformat()}",
        "- scope: CH13-S02 -> CH18-S02",
        "- decision_file: inputs/p2_manual_decisions.jsonl",
        "",
        "| section_id | status | CPs | source_run | decision |",
        "|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['section_id']} | {row['review_status']} | {row['core_point_count']} | "
            f"{row['source_run']} | {row['decision']} |"
        )
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "p2a_after_CH13_S01_batch01_review_summary_20260706.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
