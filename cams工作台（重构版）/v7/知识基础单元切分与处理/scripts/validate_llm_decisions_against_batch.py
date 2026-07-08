from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def canonical_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def sentence_ids(row: dict) -> list[str]:
    return [
        str(item.get("sentence_id"))
        for item in row.get("payload", {}).get("window", {}).get("sentences", [])
        if item.get("sentence_id")
    ]


def grouped_sentence_ids(decision: dict) -> list[str]:
    ids = []
    for group in decision.get("sentence_groups", []):
        ids.extend(str(sid) for sid in group.get("sentence_ids", []) if sid)
    return ids


def validate(batch_rows: list[dict], decisions: list[dict]) -> dict:
    issues = []
    batch_by_id = {str(row.get("request_id")): row for row in batch_rows}
    decision_by_id = {str(row.get("request_id")): row for row in decisions}

    duplicate_decisions = [
        request_id
        for request_id, count in Counter(str(row.get("request_id")) for row in decisions).items()
        if count > 1
    ]
    for request_id in duplicate_decisions:
        issues.append({"request_id": request_id, "issue": "duplicate_decision"})

    for request_id, row in batch_by_id.items():
        decision = decision_by_id.get(request_id)
        if not decision:
            issues.append({"request_id": request_id, "issue": "missing_decision"})
            continue
        expected = sentence_ids(row)
        actual = grouped_sentence_ids(decision)
        expected_set = set(expected)
        actual_set = set(actual)
        missing = [sid for sid in expected if sid not in actual_set]
        unknown = [sid for sid in actual if sid not in expected_set]
        duplicated = [sid for sid, count in Counter(actual).items() if count > 1]
        if missing:
            issues.append({"request_id": request_id, "issue": "missing_sentence_ids", "sentence_ids": missing})
        if unknown:
            issues.append({"request_id": request_id, "issue": "unknown_sentence_ids", "sentence_ids": unknown})
        if duplicated:
            issues.append({"request_id": request_id, "issue": "duplicate_sentence_ids", "sentence_ids": duplicated})

    extra = [request_id for request_id in decision_by_id if request_id not in batch_by_id]
    for request_id in extra:
        issues.append({"request_id": request_id, "issue": "extra_decision"})

    return {
        "batch_requests": len(batch_rows),
        "decision_rows": len(decisions),
        "issues": issues,
    }


def validate_provenance(batch_rows: list[dict], decisions: list[dict], prompt_file: Path | None) -> list[dict]:
    issues = []
    batch_by_id = {str(row.get("request_id")): row for row in batch_rows}
    prompt_sha = sha256_text(prompt_file.read_text(encoding="utf-8")) if prompt_file else None
    for decision in decisions:
        request_id = str(decision.get("request_id"))
        meta = decision.get("_meta")
        if not isinstance(meta, dict):
            continue
        row = batch_by_id.get(request_id)
        if not row:
            continue
        expected_input_sha = sha256_text(canonical_json(row))
        actual_input_sha = meta.get("input_sha256")
        if actual_input_sha and actual_input_sha != expected_input_sha:
            issues.append(
                {
                    "request_id": request_id,
                    "issue": "input_sha256_mismatch",
                    "expected": expected_input_sha,
                    "actual": actual_input_sha,
                }
            )
        if prompt_sha:
            actual_prompt_sha = meta.get("prompt_sha256")
            if actual_prompt_sha and actual_prompt_sha != prompt_sha:
                issues.append(
                    {
                        "request_id": request_id,
                        "issue": "prompt_sha256_mismatch",
                        "expected": prompt_sha,
                        "actual": actual_prompt_sha,
                    }
                )
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-file", required=True, type=Path)
    parser.add_argument("--decisions-file", required=True, type=Path)
    parser.add_argument("--out-file", type=Path)
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument(
        "--require-provenance",
        action="store_true",
        help="Require every decision row to contain _meta with input_sha256.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    batch_rows = read_jsonl(args.batch_file)
    decisions = read_jsonl(args.decisions_file)
    result = validate(batch_rows, decisions)
    provenance_issues = validate_provenance(batch_rows, decisions, args.prompt_file)
    if args.require_provenance:
        decision_by_id = {str(row.get("request_id")): row for row in decisions}
        for row in batch_rows:
            decision = decision_by_id.get(str(row.get("request_id")))
            if not isinstance((decision or {}).get("_meta"), dict):
                provenance_issues.append(
                    {"request_id": row.get("request_id"), "issue": "missing_decision_meta"}
                )
    result["provenance_issues"] = provenance_issues
    if args.out_file:
        args.out_file.parent.mkdir(parents=True, exist_ok=True)
        args.out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"batch requests: {result['batch_requests']}")
    print(f"decision rows: {result['decision_rows']}")
    print(f"issues: {len(result['issues'])}")
    for issue in result["issues"][:20]:
        print(json.dumps(issue, ensure_ascii=False))
    print(f"provenance issues: {len(provenance_issues)}")
    for issue in provenance_issues[:20]:
        print(json.dumps(issue, ensure_ascii=False))
    raise SystemExit(1 if result["issues"] or provenance_issues else 0)


if __name__ == "__main__":
    main()
