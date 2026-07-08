from __future__ import annotations

import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
SOURCE = PHASE_DIR / "runs" / "p2c_after_CH13_S01_batch01_reviewed_20260706_CH13-S02" / "parsed_response.json"
OUTPUT = PHASE_DIR / "outputs" / "p2c_reviewed_relations.CH13-S02.json"
REPORT = PHASE_DIR / "reports" / "p2c_review_summary_20260706.md"

DELETED_RELATION_IDS = {"p2c_rel_CH13_S02_001_003"}


def main() -> None:
    payload = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    original_relations = payload.get("core_point_relations") or []
    reviewed_relations = [rel for rel in original_relations if rel.get("relation_id") not in DELETED_RELATION_IDS]
    reviewed = {
        "section_id": "CH13-S02",
        "review_source": "inputs/p2c_manual_decisions.jsonl",
        "source_p2c_run": str(SOURCE.relative_to(PHASE_DIR)),
        "reviewed_at": "2026-07-06",
        "review_batch": "p2c_after_CH13_S01_batch01_review_20260706",
        "review_status": "reviewed_delete_relation",
        "core_point_relations": reviewed_relations,
        "deleted_relation_ids": sorted(DELETED_RELATION_IDS),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(reviewed, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# P2C Review Summary",
        "",
        "- reviewed_at: 2026-07-06",
        "- decision_file: inputs/p2c_manual_decisions.jsonl",
        "",
        "## CH13-S02",
        "",
        "- status: reviewed_delete_relation",
        "- deleted: p2c_rel_CH13_S02_001_003",
        "- reason: CBDC 风险与 cryptoasset 风险概览是相关并列主题，不应使用 contains 表示从属。",
        f"- original_relations: {len(original_relations)}",
        f"- reviewed_relations: {len(reviewed_relations)}",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"section_id": "CH13-S02", "original_relations": len(original_relations), "reviewed_relations": len(reviewed_relations)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
