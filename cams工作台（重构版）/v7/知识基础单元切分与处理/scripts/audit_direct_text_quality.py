from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DEFAULT_INPUT = BASE_UNITS_DIR / "draft" / "v2_fullbook" / "v7_units_draft.v2_fullbook_all.combined.json"
DEFAULT_OUT_DIR = BASE_UNITS_DIR / "audit" / "direct_text_quality"


TEXT_ISSUE_RULES = [
    {
        "issue": "missing_hyphen_timeconsuming",
        "pattern": re.compile(r"\btimeconsuming\b", re.IGNORECASE),
        "recommended_action": "auto_surface_fix_candidate",
        "suggestion": "time-consuming",
        "rationale": "likely missing hyphen/space in extracted text",
    },
    {
        "issue": "missing_hyphen_enduser",
        "pattern": re.compile(r"\benduser\b", re.IGNORECASE),
        "recommended_action": "auto_surface_fix_candidate",
        "suggestion": "end-user",
        "rationale": "likely missing hyphen/space in extracted text",
    },
    {
        "issue": "broken_financia_account",
        "pattern": re.compile(r"\bfinancia account\b", re.IGNORECASE),
        "recommended_action": "manual_source_review",
        "suggestion": "financial account",
        "rationale": "probable OCR deletion; verify against source before changing",
    },
    {
        "issue": "duplicated_phrase_accommodate",
        "pattern": re.compile(r"\bof varying to accommodate\b", re.IGNORECASE),
        "recommended_action": "manual_source_review_or_review_gate",
        "suggestion": None,
        "rationale": "sentence appears to contain repeated or garbled extraction",
    },
    {
        "issue": "damaged_publication_reference",
        "pattern": re.compile(r"\bIn its\s*,", re.IGNORECASE),
        "recommended_action": "manual_source_review",
        "suggestion": None,
        "rationale": "publication title appears missing from extraction",
    },
    {
        "issue": "mojibake_or_replacement_char",
        "pattern": re.compile(r"�|鈥|濃|锟|Íatest|\borigina\b", re.IGNORECASE),
        "recommended_action": "manual_source_review_or_review_gate",
        "suggestion": None,
        "rationale": "possible OCR/mojibake/extraction damage",
    },
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: str, limit: int = 700) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def find_issues(unit: dict[str, Any]) -> list[dict[str, Any]]:
    quote = str(unit.get("en_quote") or "")
    issues = []
    for rule in TEXT_ISSUE_RULES:
        matches = [match.group(0) for match in rule["pattern"].finditer(quote)]
        if not matches:
            continue
        issues.append(
            {
                "issue": rule["issue"],
                "matches": sorted(set(matches)),
                "recommended_action": rule["recommended_action"],
                "suggestion": rule["suggestion"],
                "rationale": rule["rationale"],
            }
        )
    return issues


def unit_brief(unit: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, Any]:
    actions = sorted(set(issue["recommended_action"] for issue in issues))
    return {
        "unit_id": unit.get("unit_id"),
        "chapter": unit.get("chapter"),
        "unit_type": unit.get("unit_type"),
        "type": unit.get("type"),
        "printed_page": unit.get("printed_page"),
        "pdf_page": unit.get("pdf_page"),
        "heading_context": unit.get("heading_context", []),
        "knowledge_en": unit.get("knowledge_en"),
        "en_quote": compact(str(unit.get("en_quote") or "")),
        "en_sentence_ids": unit.get("en_sentence_ids", []),
        "risk_flags": unit.get("risk_flags", []),
        "source": unit.get("source", {}),
        "issues": issues,
        "recommended_actions": actions,
    }


def build_report(audit: dict[str, Any]) -> str:
    lines = [
        "# v7 Direct Text Quality Audit",
        "",
        f"Generated at: {audit['generated_at']}",
        "",
        "## Summary",
        "",
        f"- direct items scanned: {audit['direct_items_scanned']}",
        f"- issue units: {audit['issue_units']}",
        "",
        "## Issue Counts",
        "",
    ]
    for issue, count in audit["issue_counts"].items():
        lines.append(f"- {issue}: {count}")
    lines.extend(["", "## Recommended Actions", ""])
    for action, count in audit["recommended_action_counts"].items():
        lines.append(f"- {action}: {count}")
    for action, samples in audit["samples_by_action"].items():
        lines.extend(["", f"## Samples: {action}", ""])
        for sample in samples[:12]:
            lines.extend(
                [
                    f"### {sample['unit_id']}",
                    "",
                    f"- chapter: {sample.get('chapter')}",
                    f"- page: {sample.get('printed_page')} / pdf {sample.get('pdf_page')}",
                    f"- heading: {' / '.join(sample.get('heading_context', []))}",
                    f"- knowledge_en: {sample.get('knowledge_en')}",
                    f"- en_quote: {sample.get('en_quote')}",
                    f"- issues: {json.dumps(sample.get('issues', []), ensure_ascii=False)}",
                    "",
                ]
            )
    return "\n".join(lines)


def audit_direct_text(input_file: Path) -> dict[str, Any]:
    payload = read_json(input_file)
    units = payload.get("items", [])
    issue_units = []
    issue_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    by_action: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for unit in units:
        issues = find_issues(unit)
        if not issues:
            continue
        brief = unit_brief(unit, issues)
        issue_units.append(brief)
        issue_counts.update(issue["issue"] for issue in issues)
        for issue in issues:
            action_counts[issue["recommended_action"]] += 1
            by_action[issue["recommended_action"]].append(brief)

    return {
        "schema_version": "v7_direct_text_quality_audit_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input_file": str(input_file),
        "direct_items_scanned": len(units),
        "issue_units": len(issue_units),
        "issue_counts": dict(issue_counts.most_common()),
        "recommended_action_counts": dict(action_counts.most_common()),
        "issue_items": issue_units,
        "samples_by_action": {action: samples[:20] for action, samples in sorted(by_action.items())},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit direct v7 base unit text for small extraction defects.")
    parser.add_argument("--input-file", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audit = audit_direct_text(args.input_file.resolve())
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_json = args.out_dir / "direct_text_quality_audit.json"
    out_report = args.out_dir / "direct_text_quality_audit_report.md"
    write_json(out_json, audit)
    out_report.write_text(build_report(audit), encoding="utf-8")
    print(f"direct items scanned: {audit['direct_items_scanned']}")
    print(f"issue units: {audit['issue_units']}")
    print(f"issues: {json.dumps(audit['issue_counts'], ensure_ascii=False)}")
    print(f"actions: {json.dumps(audit['recommended_action_counts'], ensure_ascii=False)}")
    print(f"wrote: {out_json}")
    print(f"wrote: {out_report}")


if __name__ == "__main__":
    main()
