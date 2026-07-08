from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DRAFT_DIR = BASE_UNITS_DIR / "draft" / "v2_fullbook"
RUN_STATUS = BASE_UNITS_DIR / "fullbook_ds_v2_run" / "run_status.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def duplicate_values(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def dedupe_direct_items(raw_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    seen_sentence_owner: dict[str, str] = {}
    skipped: list[dict[str, Any]] = []
    for unit in raw_items:
        sentence_ids = [str(sid) for sid in unit.get("en_sentence_ids", []) if sid]
        duplicate_sentence_ids = [sid for sid in sentence_ids if sid in seen_sentence_owner]
        if duplicate_sentence_ids and set(duplicate_sentence_ids) == set(sentence_ids):
            skipped.append(
                {
                    "unit_id": unit.get("unit_id"),
                    "duplicate_sentence_ids": duplicate_sentence_ids,
                    "kept_unit_ids": sorted({seen_sentence_owner[sid] for sid in duplicate_sentence_ids}),
                    "chapter": unit.get("chapter"),
                    "knowledge_en": unit.get("knowledge_en"),
                    "en_quote": str(unit.get("en_quote") or "")[:500],
                    "source": unit.get("source"),
                }
            )
            continue
        kept.append(unit)
        for sid in sentence_ids:
            seen_sentence_owner.setdefault(sid, str(unit.get("unit_id")))
    return kept, skipped


def build_report(payload: dict[str, Any]) -> str:
    audit = payload["audit"]
    lines = [
        "# v7 Fullbook DS v2 Combined Draft",
        "",
        f"Generated at: {payload['generated_at']}",
        "",
        "## Summary",
        "",
        f"- slices: {audit['slice_count']}",
        f"- requests: {audit['request_count']}",
        f"- direct items: {audit['direct_items']}",
        f"- raw direct items before dedupe: {audit['raw_direct_items']}",
        f"- review items: {audit['review_items']}",
        f"- parent/context items: {audit['parent_items']}",
        f"- skipped duplicate direct items: {len(audit['skipped_duplicate_direct_items'])}",
        f"- duplicate unit_ids: {len(audit['duplicate_unit_ids'])}",
        f"- duplicate direct sentence_ids: {len(audit['duplicate_direct_sentence_ids'])}",
        f"- combined audit issues: {audit['combined_audit_issue_count']}",
        "",
        "## Top Chapters By Direct Items",
        "",
    ]
    for chapter, stats in sorted(payload["chapter_stats"].items(), key=lambda item: -item[1]["direct_items"])[:30]:
        lines.append(
            f"- {chapter}: direct {stats['direct_items']}, review {stats['review_items']}, parent {stats['parent_items']}"
        )
    lines.extend(["", "## Top Review Flags", ""])
    for flag, count in audit["review_flag_counts"][:30]:
        lines.append(f"- {flag}: {count}")
    if audit["review_examples"]:
        lines.extend(["", "## Review Examples", ""])
        for item in audit["review_examples"]:
            lines.extend(
                [
                    f"### {item['chapter']}",
                    "",
                    f"- knowledge_en: {item.get('knowledge_en')}",
                    f"- en_quote: {item.get('en_quote')}",
                    f"- risk_flags: {json.dumps(item.get('risk_flags', []), ensure_ascii=False)}",
                    "",
                ]
            )
    if audit["skipped_duplicate_direct_items"]:
        lines.extend(["", "## Skipped Duplicate Direct Items", ""])
        for item in audit["skipped_duplicate_direct_items"]:
            lines.extend(
                [
                    f"### {item.get('unit_id')}",
                    "",
                    f"- chapter: {item.get('chapter')}",
                    f"- duplicate_sentence_ids: {', '.join(item.get('duplicate_sentence_ids', []))}",
                    f"- kept_unit_ids: {', '.join(item.get('kept_unit_ids', []))}",
                    f"- knowledge_en: {item.get('knowledge_en')}",
                    f"- en_quote: {item.get('en_quote')}",
                    "",
                ]
            )
    return "\n".join(lines)


def main() -> None:
    status = read_json(RUN_STATUS)
    raw_items: list[dict[str, Any]] = []
    review_items: list[dict[str, Any]] = []
    parent_items: list[dict[str, Any]] = []
    chapter_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"direct_items": 0, "review_items": 0, "parent_items": 0})
    combined_audit_issues: list[dict[str, Any]] = []
    review_flags = Counter()
    review_examples: list[dict[str, Any]] = []

    for task in status["tasks"]:
        slug = task["run_slug"]
        combined_path = DRAFT_DIR / f"v7_units_draft.pilot_{slug}.combined.json"
        audit_path = DRAFT_DIR / f"v7_units_draft.pilot_{slug}.combined_audit.json"
        combined = read_json(combined_path)
        audit = read_json(audit_path)
        chapter = task["chapter"]
        direct = combined.get("items", [])
        review = combined.get("review_items", [])
        parent = combined.get("parent_items", [])
        raw_items.extend(direct)
        review_items.extend(review)
        parent_items.extend(parent)
        chapter_stats[chapter]["direct_items"] += len(direct)
        chapter_stats[chapter]["review_items"] += len(review)
        chapter_stats[chapter]["parent_items"] += len(parent)
        for issue in audit.get("issues") or []:
            combined_audit_issues.append({"run_slug": slug, **issue})
        for unit in review:
            for flag in unit.get("risk_flags", []):
                review_flags[str(flag)] += 1
            if len(review_examples) < 20:
                review_examples.append(
                    {
                        "chapter": chapter,
                        "unit_id": unit.get("unit_id"),
                        "knowledge_en": unit.get("knowledge_en"),
                        "en_quote": str(unit.get("en_quote") or "")[:500],
                        "risk_flags": unit.get("risk_flags", []),
                    }
                )

    items, skipped_duplicate_direct_items = dedupe_direct_items(raw_items)
    unit_ids = [str(unit.get("unit_id")) for unit in [*items, *review_items, *parent_items] if unit.get("unit_id")]
    direct_sentence_ids = [
        str(sentence_id)
        for unit in items
        for sentence_id in unit.get("en_sentence_ids", [])
        if sentence_id
    ]
    payload = {
        "schema_version": "v7_units_draft_fullbook_ds_v2_combined_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "draft_fullbook_combined_not_for_downstream_binding",
        "sources": {
            "run_status": str(RUN_STATUS.relative_to(BASE_UNITS_DIR)),
            "draft_dir": str(DRAFT_DIR.relative_to(BASE_UNITS_DIR)),
        },
        "notes": [
            "This file aggregates all v2 fullbook slice combined outputs.",
            "IDs remain temporary v7u_tmp_* IDs and must not be used as final downstream binding IDs.",
            "zh_search_text / knowledge_zh are still pending unless explicitly filled by later stages.",
        ],
        "items": items,
        "review_items": review_items,
        "parent_items": parent_items,
        "chapter_stats": dict(chapter_stats),
        "audit": {
            "slice_count": status["task_count"],
            "request_count": status["request_count"],
            "raw_direct_items": len(raw_items),
            "direct_items": len(items),
            "review_items": len(review_items),
            "parent_items": len(parent_items),
            "skipped_duplicate_direct_items": skipped_duplicate_direct_items,
            "duplicate_unit_ids": duplicate_values(unit_ids),
            "duplicate_direct_sentence_ids": duplicate_values(direct_sentence_ids),
            "combined_audit_issue_count": len(combined_audit_issues),
            "combined_audit_issues": combined_audit_issues,
            "review_flag_counts": review_flags.most_common(),
            "review_examples": review_examples,
        },
    }
    out_json = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.combined.json"
    out_audit = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.combined_audit.json"
    out_report = DRAFT_DIR / "v7_units_draft.v2_fullbook_all.combined_report.md"
    write_json(out_json, payload)
    write_json(out_audit, payload["audit"])
    out_report.write_text(build_report(payload), encoding="utf-8")
    print(f"direct items: {len(items)}")
    print(f"review items: {len(review_items)}")
    print(f"parent/context items: {len(parent_items)}")
    print(f"duplicate unit_ids: {len(payload['audit']['duplicate_unit_ids'])}")
    print(f"duplicate direct sentence_ids: {len(payload['audit']['duplicate_direct_sentence_ids'])}")
    print(f"combined audit issues: {len(combined_audit_issues)}")
    print(f"wrote: {out_json}")
    print(f"wrote: {out_audit}")
    print(f"wrote: {out_report}")


if __name__ == "__main__":
    main()
