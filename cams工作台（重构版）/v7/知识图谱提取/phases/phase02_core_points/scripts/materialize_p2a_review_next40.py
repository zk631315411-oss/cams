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
REVIEW_BATCH = "p2a_next40_review_20260706"

SECTIONS = [
    "CH06-S01",
    "CH06-S02",
    "CH06-S03",
    "CH06-S04",
    "CH06-S05",
    "CH06-S06",
    "CH06-S07",
    "CH06-S08",
    "CH06-S09",
    "CH06-S10",
    "CH06-S11",
    "CH07-S01",
    "CH07-S02",
    "CH07-S03",
    "CH07-S04",
    "CH07-S05",
    "CH08-S01",
    "CH08-S02",
    "CH08-S03",
    "CH08-S04",
    "CH08-S05",
    "CH09-S01",
    "CH09-S02",
    "CH09-S03",
    "CH09-S04",
    "CH09-S05",
    "CH09-S06",
    "CH10-S01",
    "CH10-S02",
    "CH11-S01",
    "CH11-S02",
    "CH11-S03",
    "CH11-S04",
    "CH11-S05",
    "CH12-S01",
    "CH12-S02",
    "CH12-S03",
    "CH12-S04",
    "CH12-S05",
    "CH13-S01",
]

RETRY_SECTIONS = {"CH06-S11", "CH09-S02", "CH11-S05"}

TITLE_OVERRIDES = {
    "cp_CH06_S09_001": {
        "title_zh": "政治敏感人物的定义、范围和关联人",
        "title_en": "PEP definition, scope, and related persons",
        "reason": "Human review kept the non-contiguous definition/scope grouping and clarified that the CP covers immediate family, close associates, and owned businesses.",
        "review_flags": ["human_reviewed_title_adjusted", "human_reviewed_accept_non_contiguous"],
    }
}

ACCEPT_NON_CONTIGUOUS = {
    "cp_CH06_S07_001",
    "cp_CH06_S07_002",
    "cp_CH06_S09_005",
    "cp_CH07_S02_001",
    "cp_CH07_S02_002",
    "cp_CH09_S02_003",
    "cp_CH13_S01_001",
    "cp_CH13_S01_005",
    "cp_CH13_S01_006",
    "cp_CH06_S11_001",
}

SECTION_DECISIONS = {
    "CH06-S07": "保留 3 个 CP：定义、风险和类型、丹麦银行案例。shell/shelf/front company 连续讲解，合并合理；风险与所有权结构作为一个复习点保留。",
    "CH06-S09": "保留 5 个 CP；将 CP1 标题调整为“政治敏感人物的定义、范围和关联人”。PEP 定义范围虽非连续，但属于同一复习主题。",
    "CH07-S02": "保留 4 个 CP：零售银行风险、商业银行风险、贸易型洗钱风险、易受影响的贸易融资产品。接受前两个 CP 的非连续点状聚合。",
    "CH09-S02": "补跑后保留 4 个 CP。CP3 将非法活动和红旗信号合并为“识别电汇滥用”的复习主题，接受非连续合并。",
    "CH13-S01": "保留 7 个 CP。该 section 同时覆盖生态、数字资产类别、区块链基础、优势、交易流程、风险和红旗；接受第 1、5、6 个 CP 的非连续合并。",
    "CH06-S11": "补跑后保留 1 个 CP：集中账户的定义、用途和洗钱风险。section 只有 3 个 unit，不拆分。",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def p2a_run_dir(section_id: str) -> Path:
    prefix = "p2a_retry_20260706_" if section_id in RETRY_SECTIONS else "p2a_next40_20260706_"
    return RUNS_DIR / f"{prefix}{section_id}"


def reviewed_core_points(section_id: str, parsed: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    status = "reviewed_keep"
    reviewed: list[dict[str, Any]] = []
    for cp in parsed.get("core_points") or []:
        row = dict(cp)
        cp_id = str(row.get("draft_core_point_id"))
        row.setdefault("source_core_point_ids", [cp_id])
        if cp_id in TITLE_OVERRIDES:
            override = TITLE_OVERRIDES[cp_id]
            row["title_zh"] = override["title_zh"]
            row["title_en"] = override["title_en"]
            row["review_flags"] = override["review_flags"]
            row["reason"] = override["reason"]
            status = "reviewed_title_adjusted"
        elif cp_id in ACCEPT_NON_CONTIGUOUS:
            row["review_flags"] = ["human_reviewed_accept_non_contiguous"]
            row["reason"] = "Human review accepted this non-contiguous grouping because it forms one useful review topic in the section."
        else:
            row["review_flags"] = ["human_reviewed_keep"]
            row.setdefault("reason", "Human review kept the P2A core_point boundary unchanged.")
        reviewed.append(row)
    if section_id in SECTION_DECISIONS and status == "reviewed_keep":
        status = "reviewed_manual_keep"
    return reviewed, status


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
        run_dir = p2a_run_dir(section_id)
        parsed_path = run_dir / "parsed_response.json"
        if not parsed_path.exists():
            raise FileNotFoundError(parsed_path)
        parsed = read_json(parsed_path)
        core_points, review_status = reviewed_core_points(section_id, parsed)
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

        summary_rows.append(
            {
                "section_id": section_id,
                "review_status": review_status,
                "core_point_count": len(core_points),
                "source_run": run_dir.name,
                "decision": SECTION_DECISIONS.get(section_id, "人工审核后确认 P2A CP 边界可用，保持不改。"),
            }
        )

        if section_id in SECTION_DECISIONS:
            decisions.append(
                {
                    "section_id": section_id,
                    "review_type": review_status,
                    "source_core_point_ids": [cp.get("draft_core_point_id") for cp in parsed.get("core_points") or []],
                    "result_core_point_id": None,
                    "decision": SECTION_DECISIONS[section_id],
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
        "# P2A Next 40 Review Summary",
        "",
        f"- reviewed_at: {REVIEWED_AT}",
        f"- generated_at: {date.today().isoformat()}",
        "- scope: CH06-S01 -> CH13-S01",
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
    (REPORTS_DIR / "p2a_next40_review_summary_20260706.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
