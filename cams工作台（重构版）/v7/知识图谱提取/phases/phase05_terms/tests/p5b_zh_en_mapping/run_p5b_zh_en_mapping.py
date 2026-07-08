from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TEST_DIR = Path(__file__).resolve().parent
PHASE_DIR = TEST_DIR.parents[1]
KG_ROOT = PHASE_DIR.parents[1]

FIRST_FIVE_UNITS = KG_ROOT / "phases" / "phase01_chapter_index" / "outputs" / "first_five_chapters_units.jsonl"
ELIGIBLE_UNITS = KG_ROOT / "phases" / "phase00_quality_gate" / "outputs" / "eligible_units.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def norm_en(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def norm_zh(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip())


def load_units(scope: str) -> list[dict[str, Any]]:
    all_units = {row["unit_id"]: row for row in read_jsonl(ELIGIBLE_UNITS)}
    if scope == "first5":
        first_five_ids = {row["unit_id"] for row in read_jsonl(FIRST_FIVE_UNITS)}
        return [
            all_units[unit_id]
            for unit_id in sorted(first_five_ids, key=lambda uid: all_units[uid].get("unit_order", 10**12))
            if unit_id in all_units
        ]
    return sorted(all_units.values(), key=lambda row: row.get("unit_order", 10**12))


def main() -> None:
    parser = argparse.ArgumentParser(description="Test P5B zh/en term mapping.")
    parser.add_argument("--scope", choices=["first5", "all"], default="first5")
    args = parser.parse_args()

    units = load_units(args.scope)
    pair_counts: Counter[tuple[str, str]] = Counter()
    en_counts: Counter[str] = Counter()
    zh_counts: Counter[str] = Counter()
    en_display: dict[str, Counter[str]] = defaultdict(Counter)
    evidence: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for unit in units:
        unit_id = str(unit.get("unit_id"))
        seen_in_unit: set[tuple[str, str]] = set()
        for term in unit.get("terms") or []:
            en = norm_en(term.get("en"))
            zh = norm_zh(term.get("zh"))
            if not en or not zh:
                continue
            pair = (en, zh)
            if pair in seen_in_unit:
                continue
            seen_in_unit.add(pair)
            pair_counts[pair] += 1
            en_counts[en] += 1
            zh_counts[zh] += 1
            en_display[en][str(term.get("en") or "").strip()] += 1
            if len(evidence[pair]) < 3:
                evidence[pair].append(
                    {
                        "unit_id": unit_id,
                        "unit_order": unit.get("unit_order"),
                        "en_quote": unit.get("en_quote"),
                        "knowledge_zh": unit.get("knowledge_zh"),
                    }
                )

    zh_by_en: dict[str, set[str]] = defaultdict(set)
    en_by_zh: dict[str, set[str]] = defaultdict(set)
    for en, zh in pair_counts:
        zh_by_en[en].add(zh)
        en_by_zh[zh].add(en)

    mappings: list[dict[str, Any]] = []
    for (en, zh), count in pair_counts.items():
        en_total = en_counts[en]
        zh_total = zh_counts[zh]
        risk_flags: list[str] = []
        if count == 1:
            risk_flags.append("low_frequency")
        if len(zh_by_en[en]) > 1:
            risk_flags.append("multiple_zh_for_en")
        if len(en_by_zh[zh]) > 1:
            risk_flags.append("multiple_en_for_zh")
        has_conflict = "multiple_zh_for_en" in risk_flags or "multiple_en_for_zh" in risk_flags
        decision = "needs_review" if has_conflict else "clean"
        mappings.append(
            {
                "en_key": en,
                "canonical_en": en_display[en].most_common(1)[0][0] if en_display[en] else en,
                "canonical_zh": zh,
                "count": count,
                "en_total_count": en_total,
                "zh_total_count": zh_total,
                "en_share": round(count / en_total, 4) if en_total else 0,
                "zh_share": round(count / zh_total, 4) if zh_total else 0,
                "decision": decision,
                "risk_flags": risk_flags,
                "evidence_examples": evidence[(en, zh)],
            }
        )

    mappings.sort(key=lambda row: (row["decision"] != "needs_review", row["en_key"], -row["count"], row["canonical_zh"]))

    en_conflicts = [
        {
            "en_key": en,
            "canonical_en": en_display[en].most_common(1)[0][0] if en_display[en] else en,
            "zh_options": sorted(zh_values),
            "total_count": en_counts[en],
        }
        for en, zh_values in zh_by_en.items()
        if len(zh_values) > 1
    ]
    zh_conflicts = [
        {
            "canonical_zh": zh,
            "en_options": sorted(en_values),
            "total_count": zh_counts[zh],
        }
        for zh, en_values in en_by_zh.items()
        if len(en_values) > 1
    ]
    en_conflicts.sort(key=lambda row: (-row["total_count"], row["en_key"]))
    zh_conflicts.sort(key=lambda row: (-row["total_count"], row["canonical_zh"]))

    summary = {
        "scope": args.scope,
        "unit_count": len(units),
        "mapping_count": len(mappings),
        "clean_mapping_count": sum(1 for row in mappings if row["decision"] == "clean"),
        "review_mapping_count": sum(1 for row in mappings if row["decision"] == "needs_review"),
        "en_conflict_count": len(en_conflicts),
        "zh_conflict_count": len(zh_conflicts),
        "low_frequency_count": sum(1 for row in mappings if "low_frequency" in row["risk_flags"]),
    }

    payload = {
        "summary": summary,
        "mappings": mappings,
        "en_conflicts": en_conflicts,
        "zh_conflicts": zh_conflicts,
    }
    write_json(TEST_DIR / "outputs" / f"p5b_zh_en_mapping_{args.scope}.json", payload)
    write_text(TEST_DIR / "previews" / f"p5b_zh_en_mapping_{args.scope}.md", preview_markdown(summary, mappings, en_conflicts, zh_conflicts))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def preview_markdown(
    summary: dict[str, Any],
    mappings: list[dict[str, Any]],
    en_conflicts: list[dict[str, Any]],
    zh_conflicts: list[dict[str, Any]],
) -> str:
    lines = ["# P5B zh/en mapping preview", "", "## Summary", ""]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Review mappings", "", "| en | zh | count | en share | zh share | risks |", "|---|---|---:|---:|---:|---|"])
    for row in [item for item in mappings if item["decision"] == "needs_review"][:100]:
        lines.append(
            f"| {row['canonical_en']} | {row['canonical_zh']} | {row['count']} | {row['en_share']} | {row['zh_share']} | {', '.join(row['risk_flags'])} |"
        )

    lines.extend(["", "## Clean mappings sample", "", "| en | zh | count |", "|---|---|---:|"])
    for row in [item for item in mappings if item["decision"] == "clean"][:80]:
        lines.append(f"| {row['canonical_en']} | {row['canonical_zh']} | {row['count']} |")

    lines.extend(["", "## English conflicts", "", "| en | zh options | total |", "|---|---|---:|"])
    for row in en_conflicts[:80]:
        lines.append(f"| {row['canonical_en']} | {', '.join(row['zh_options'])} | {row['total_count']} |")

    lines.extend(["", "## Chinese conflicts", "", "| zh | en options | total |", "|---|---|---:|"])
    for row in zh_conflicts[:80]:
        lines.append(f"| {row['canonical_zh']} | {', '.join(row['en_options'])} | {row['total_count']} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
