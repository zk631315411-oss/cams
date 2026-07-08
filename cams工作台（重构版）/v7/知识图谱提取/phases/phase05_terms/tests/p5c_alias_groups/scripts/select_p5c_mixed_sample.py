from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
TEST_DIR = SCRIPT_DIR.parent
DEFAULT_INPUT = TEST_DIR / "outputs" / "p5c_alias_candidate_groups_v3.json"
DEFAULT_OUTPUT = TEST_DIR / "outputs" / "p5c_alias_candidate_groups_mixed50_v1.json"
DEFAULT_PREVIEW = TEST_DIR / "previews" / "p5c_alias_candidate_groups_mixed50_v1.md"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def has_source(group: dict[str, Any], source: str) -> bool:
    return source in set(group.get("source_types") or [])


def has_risk(group: dict[str, Any], risk: str) -> bool:
    return risk in set(group.get("risk_flags") or [])


def term_texts(group: dict[str, Any]) -> str:
    return " ".join(str(term.get("text") or "") for term in group.get("terms") or [])


def take(pool: list[dict[str, Any]], count: int, used: set[str]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for group in pool:
        gid = str(group.get("candidate_group_id") or "")
        if gid in used:
            continue
        selected.append(group)
        used.add(gid)
        if len(selected) >= count:
            break
    return selected


def preview(groups: list[dict[str, Any]], buckets: dict[str, int]) -> str:
    lines = [
        "# P5C mixed sample",
        "",
        f"- candidate_group_count: {len(groups)}",
        "",
        "## Buckets",
        "",
    ]
    for key, count in buckets.items():
        lines.append(f"- {key}: {count}")
    lines.extend([
        "",
        "| id | sources | terms | risks | evidence |",
        "|---|---|---|---|---:|",
    ])
    for group in groups:
        terms = "; ".join(f"{term['text']}({term['lang']}, {term.get('count', 0)})" for term in group.get("terms") or [])
        lines.append(
            f"| {group['candidate_group_id']} | {', '.join(group.get('source_types') or [])} | {terms} | {', '.join(group.get('risk_flags') or [])} | {len(group.get('evidence_examples') or [])} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Select a deterministic mixed P5C review sample.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    groups = read_json(args.input).get("candidate_groups") or []
    used: set[str] = set()
    selected: list[dict[str, Any]] = []
    buckets: dict[str, int] = {}

    normal_p5a = [
        group for group in groups
        if has_source(group, "p5a_accept")
        and has_source(group, "abbreviation_full_form")
        and not has_risk(group, "multiple_full_form_candidates")
    ]
    compound = [group for group in groups if has_source(group, "compound_abbreviation_component")]
    p5b = [group for group in groups if has_source(group, "p5b_en_conflict") or has_source(group, "p5b_zh_conflict")]
    high_risk = [
        group for group in groups
        if has_risk(group, "multiple_full_form_candidates")
        or has_risk(group, "slash_abbreviation")
        or any(token in term_texts(group).upper() for token in ("SAR", "STR", "AML/CFT", "BSA/AML", "KYC/CDD"))
    ]

    for bucket_name, pool, count in [
        ("p5a_normal_abbreviation", normal_p5a, 20),
        ("p5a_compound_abbreviation", compound, 10),
        ("p5b_translation_conflict", p5b, 15),
        ("high_risk_boundary", high_risk, 5),
    ]:
        chunk = take(pool, count, used)
        selected.extend(chunk)
        buckets[bucket_name] = len(chunk)

    if len(selected) < args.limit:
        filler = take(groups, args.limit - len(selected), used)
        selected.extend(filler)
        buckets["filler"] = len(filler)

    selected = selected[: args.limit]
    for index, group in enumerate(selected, start=1):
        group["candidate_group_id"] = f"p5c_mix_{index:06d}"

    payload = {
        "summary": {
            "candidate_group_count": len(selected),
            "source": str(args.input),
            "buckets": buckets,
        },
        "candidate_groups": selected,
    }
    write_json(args.output, payload)
    write_text(args.preview, preview(selected, buckets))
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
