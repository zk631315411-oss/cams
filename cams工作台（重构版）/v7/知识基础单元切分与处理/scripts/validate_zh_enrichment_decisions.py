from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DEFAULT_BATCH = BASE_UNITS_DIR / "llm_batches" / "zh_enrichment" / "v7_zh_enrichment_batch.v1.jsonl"
DEFAULT_DECISIONS = BASE_UNITS_DIR / "llm_batches" / "zh_enrichment" / "v7_zh_enrichment_decisions.v1.ds.jsonl"
DEFAULT_OUT = BASE_UNITS_DIR / "llm_batches" / "zh_enrichment" / "v7_zh_enrichment_validation.v1.json"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def validate(batch_file: Path, decisions_file: Path) -> dict[str, Any]:
    batch_rows = read_jsonl(batch_file)
    decision_rows = read_jsonl(decisions_file)
    expected_request_ids = [str(row.get("request_id")) for row in batch_rows]
    expected_units_by_request = {
        str(row.get("request_id")): [str(unit_id) for unit_id in row.get("unit_ids", [])]
        for row in batch_rows
    }
    decisions_by_request = {str(row.get("request_id")): row for row in decision_rows}
    issues = []
    status_counts: Counter[str] = Counter()
    unit_count = 0
    term_count = 0

    for request_id in expected_request_ids:
        decision = decisions_by_request.get(request_id)
        if not decision:
            issues.append({"request_id": request_id, "issue": "missing_decision"})
            continue
        meta = decision.get("_meta") or {}
        status_counts[str(meta.get("status") or "unknown")] += 1
        expected_units = expected_units_by_request[request_id]
        units = decision.get("units")
        if not isinstance(units, list):
            issues.append({"request_id": request_id, "issue": "decision_units_not_list"})
            continue
        seen = []
        for unit in units:
            tmp_unit_id = str((unit or {}).get("tmp_unit_id") or "")
            seen.append(tmp_unit_id)
            unit_count += 1
            knowledge_zh = str((unit or {}).get("knowledge_zh") or "").strip()
            if tmp_unit_id not in expected_units:
                issues.append({"request_id": request_id, "tmp_unit_id": tmp_unit_id, "issue": "unexpected_unit_id"})
            if not knowledge_zh:
                issues.append({"request_id": request_id, "tmp_unit_id": tmp_unit_id, "issue": "empty_knowledge_zh"})
            elif not has_cjk(knowledge_zh):
                issues.append({"request_id": request_id, "tmp_unit_id": tmp_unit_id, "issue": "knowledge_zh_has_no_cjk"})
            if len(knowledge_zh) > 120:
                issues.append({"request_id": request_id, "tmp_unit_id": tmp_unit_id, "issue": "knowledge_zh_too_long"})
            terms = (unit or {}).get("terms") or []
            if not isinstance(terms, list):
                issues.append({"request_id": request_id, "tmp_unit_id": tmp_unit_id, "issue": "terms_not_list"})
                terms = []
            term_count += len(terms)
            for term in terms:
                if not isinstance(term, dict) or not term.get("en") or not term.get("zh"):
                    issues.append({"request_id": request_id, "tmp_unit_id": tmp_unit_id, "issue": "bad_term_item"})
        missing_units = [unit_id for unit_id in expected_units if unit_id not in set(seen)]
        for unit_id in missing_units:
            issues.append({"request_id": request_id, "tmp_unit_id": unit_id, "issue": "missing_unit"})
        duplicates = [unit_id for unit_id, count in Counter(seen).items() if count > 1]
        for unit_id in duplicates:
            issues.append({"request_id": request_id, "tmp_unit_id": unit_id, "issue": "duplicate_unit"})

    return {
        "schema_version": "v7_zh_enrichment_validation_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "batch_file": str(batch_file),
        "decisions_file": str(decisions_file),
        "request_count": len(batch_rows),
        "decision_count": len(decision_rows),
        "unit_count": unit_count,
        "term_count": term_count,
        "status_counts": dict(status_counts.most_common()),
        "issue_count": len(issues),
        "issue_counts": dict(Counter(item["issue"] for item in issues).most_common()),
        "issues": issues,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate v7 zh enrichment decisions.")
    parser.add_argument("--batch-file", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--decisions-file", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--out-file", type=Path, default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = validate(args.batch_file.resolve(), args.decisions_file.resolve())
    write_json(args.out_file, report)
    print(f"requests: {report['request_count']}")
    print(f"decisions: {report['decision_count']}")
    print(f"units: {report['unit_count']}")
    print(f"terms: {report['term_count']}")
    print(f"status_counts: {json.dumps(report['status_counts'], ensure_ascii=False)}")
    print(f"issue_count: {report['issue_count']}")
    print(f"issue_counts: {json.dumps(report['issue_counts'], ensure_ascii=False)}")
    print(f"wrote: {args.out_file}")


if __name__ == "__main__":
    main()
