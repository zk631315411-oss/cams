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
REVIEW_BATCH = "p2a_after_CH21_S04_batch03_review_20260706"
MAIN_PREFIX = "p2a_batch_after_CH21_S04_20260706_"

SECTIONS = [
    "CH22-S01",
    "CH22-S02",
    "CH23-S01",
    "CH24-S01",
    "CH24-S02",
    "CH24-S03",
    "CH24-S04",
    "CH24-S05",
    "CH24-S06",
    "CH24-S07",
    "CH24-S08",
    "CH24-S09",
    "CH24-S10",
    "CH24-S11",
    "CH24-S12",
    "CH24-S13",
    "CH24-S14",
    "CH24-S15",
    "CH24-S16",
    "CH24-S17",
]

MANUAL_DECISIONS = {
    "CH24-S01": "保留 4 个 CP。BSA 范围 CP 跨反恐融资与域外适用，属于同一范围扩展主题，接受非连续合并。",
    "CH24-S03": "人工拆分原 CP1。将 2020 年反洗钱法案过粗的关键条款拆为：总体与受益所有权、监管范围与调查权、SAR 与国家战略优先事项；FinCEN 和美国主要监管机构保留。",
    "CH24-S04": "保留 1 个 CP。富国银行监管执法行动是一个案例型小节，接受非连续案例要素合并。",
    "CH24-S07": "保留 4 个 CP。欧盟监管范围和指令历史中存在非连续回指，但复习主题清楚，接受。",
    "CH24-S08": "保留 4 个 CP。EU AML package 先列法规名称再分别解释，四个 CP 的非连续合并合理。",
    "CH24-S10": "保留 5 个 CP。MiCA 概述与适用范围跨概述和范围说明，接受非连续合并。",
    "CH24-S11": "保留 3 个 CP。信息共享与 FATF 建议 18 属于同一合规治理主题，接受非连续合并。",
    "CH24-S13": "保留 9 个 CP。澳大利亚与新加坡监管内容较长，但按法案、监管机构、战略和资源拆分，粒度可用。",
    "CH24-S14": "保留 1 个 CP。香港监管框架小节较短，整体作为一个复习主题。",
}

ACCEPT_NON_CONTIGUOUS = {
    "cp_CH24_S01_004",
    "cp_CH24_S04_001",
    "cp_CH24_S07_001",
    "cp_CH24_S07_003",
    "cp_CH24_S08_001",
    "cp_CH24_S08_002",
    "cp_CH24_S08_003",
    "cp_CH24_S08_004",
    "cp_CH24_S10_001",
    "cp_CH24_S11_002",
    "cp_CH24_S13_001",
    "cp_CH24_S14_001",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def cp(
    cp_id: str,
    title_en: str,
    title_zh: str,
    anchors: list[str],
    supports: list[str],
    concept_spans: list[list[int]],
    evidence_spans: list[list[int]],
    reason: str,
    source_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "draft_core_point_id": cp_id,
        "title_en": title_en,
        "title_zh": title_zh,
        "source_core_point_ids": source_ids or ["cp_CH24_S03_001"],
        "anchor_unit_ids": anchors,
        "support_unit_ids": supports,
        "concept_unit_spans": concept_spans,
        "evidence_unit_spans": evidence_spans,
        "non_contiguous_concept": len(concept_spans) > 1,
        "intervening_support_unit_ids": [],
        "review_flags": ["human_reviewed_split"],
        "reason": reason,
    }


def reviewed_ch24_s03(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    raw = {item["draft_core_point_id"]: item for item in parsed.get("core_points") or []}
    return [
        cp(
            "cp_CH24_S03_001A",
            "AML Act 2020 modernization and beneficial ownership transparency",
            "2020年反洗钱法案：现代化与受益所有权透明度",
            ["v7u_N001710", "v7u_N001711", "v7u_N001712", "v7u_N001717"],
            ["v7u_N001713", "v7u_N001716"],
            [[1710, 1712], [1717, 1717]],
            [[1710, 1717]],
            "Human review split the broad AML Act CP. This CP covers modernization, transparency, and beneficial ownership database/disclosure requirements.",
        ),
        cp(
            "cp_CH24_S03_001B",
            "AML Act 2020 expanded regulatory scope and investigative powers",
            "2020年反洗钱法案：监管范围扩展与调查权",
            ["v7u_N001714", "v7u_N001715", "v7u_N001718", "v7u_N001720"],
            ["v7u_N001719"],
            [[1714, 1715], [1718, 1720]],
            [[1714, 1720]],
            "Human review split the broad AML Act CP. This CP covers crypto/art/antique scope expansion, foreign financial institution subpoenas, whistleblower protection, and crypto exchanges as MSBs.",
        ),
        cp(
            "cp_CH24_S03_001C",
            "AML Act 2020 SAR intelligence and national AML/CFT priorities",
            "2020年反洗钱法案：SAR情报化与国家战略优先事项",
            ["v7u_N001721", "v7u_N001722", "v7u_N001723", "v7u_N001732", "v7u_N001733"],
            ["v7u_N001724", "v7u_N001725", "v7u_N001726", "v7u_N001727", "v7u_N001728", "v7u_N001729", "v7u_N001730", "v7u_N001731", "v7u_N001734"],
            [[1721, 1723], [1732, 1733]],
            [[1721, 1734]],
            "Human review split the broad AML Act CP. This CP covers SAR intelligence value, cross-border SAR sharing, national AML/CFT priorities, and mandatory risk assessment/program updates.",
        ),
        reviewed_keep(raw["cp_CH24_S03_002"], "human_reviewed_accept_non_contiguous"),
        reviewed_keep(raw["cp_CH24_S03_003"], "human_reviewed_accept_non_contiguous"),
    ]


def reviewed_keep(row: dict[str, Any], flag: str = "human_reviewed_keep") -> dict[str, Any]:
    item = dict(row)
    cp_id = str(item.get("draft_core_point_id"))
    item.setdefault("source_core_point_ids", [cp_id])
    item["review_flags"] = [flag]
    if flag == "human_reviewed_accept_non_contiguous":
        item["reason"] = "Human review accepted this non-contiguous grouping because it forms one useful review topic in the section."
    else:
        item.setdefault("reason", "Human review kept the P2A core_point boundary unchanged.")
    return item


def reviewed_core_points(section_id: str, parsed: dict[str, Any]) -> list[dict[str, Any]]:
    if section_id == "CH24-S03":
        return reviewed_ch24_s03(parsed)
    rows: list[dict[str, Any]] = []
    for item in parsed.get("core_points") or []:
        cp_id = str(item.get("draft_core_point_id"))
        if cp_id in ACCEPT_NON_CONTIGUOUS:
            rows.append(reviewed_keep(item, "human_reviewed_accept_non_contiguous"))
        else:
            rows.append(reviewed_keep(item))
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
        core_points = reviewed_core_points(section_id, parsed)
        review_status = "reviewed_split" if section_id == "CH24-S03" else ("reviewed_manual_keep" if section_id in MANUAL_DECISIONS else "reviewed_keep")
        reviewed = {
            "section_id": section_id,
            "review_source": "inputs/p2_manual_decisions.jsonl",
            "source_p2a_run": str(parsed_path.relative_to(PHASE_DIR)),
            "reviewed_at": REVIEWED_AT,
            "review_batch": REVIEW_BATCH,
            "review_status": review_status,
            "core_points": core_points,
            "retired_core_point_ids": ["cp_CH24_S03_001"] if section_id == "CH24-S03" else [],
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
        "# P2A After CH21-S04 Batch 03 Review Summary",
        "",
        f"- reviewed_at: {REVIEWED_AT}",
        f"- generated_at: {date.today().isoformat()}",
        "- scope: CH22-S01 -> CH24-S17",
        "- decision_file: inputs/p2_manual_decisions.jsonl",
        "",
        "| section_id | status | CPs | source_run | decision |",
        "|---|---|---:|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['section_id']} | {row['review_status']} | {row['core_point_count']} | {row['source_run']} | {row['decision']} |")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "p2a_after_CH21_S04_batch03_review_summary_20260706.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
