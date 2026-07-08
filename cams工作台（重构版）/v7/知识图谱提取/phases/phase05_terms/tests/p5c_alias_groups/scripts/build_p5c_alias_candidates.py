from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
TEST_DIR = SCRIPT_DIR.parent
PHASE_DIR = TEST_DIR.parents[1]

DEFAULT_P5B = PHASE_DIR / "outputs" / "p5b_zh_en_mapping.json"
DEFAULT_P5A = PHASE_DIR / "outputs" / "p5a_abbreviation_mapping.json"
DEFAULT_OUTPUT = TEST_DIR / "outputs" / "p5c_alias_candidate_groups.json"
DEFAULT_PREVIEW = TEST_DIR / "previews" / "p5c_alias_candidate_groups.md"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def norm_text(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip()).lower()
    return re.sub(r"[\"'《》“”()（）]", "", text)


def term_key(term: dict[str, Any]) -> str:
    return f"{term.get('lang') or lang_of(term.get('text') or '')}:{norm_text(term.get('text') or '')}"


def is_compound_component_group(group: dict[str, Any]) -> bool:
    return "compound_abbreviation_component" in set(group.get("source_types") or [])


def bridge_term_keys(group: dict[str, Any]) -> list[str]:
    if not is_compound_component_group(group):
        return [term_key(term) for term in group.get("terms") or []]
    return [
        term_key(term)
        for term in group.get("terms") or []
        if "abbreviation" in set(term.get("roles") or [])
    ]


def lang_of(text: str) -> str:
    return "zh" if re.search(r"[\u4e00-\u9fff]", text or "") else "en"


def add_term(terms: dict[str, dict[str, Any]], text: str, source: str, count: int | None = None, role: str | None = None) -> None:
    text = str(text or "").strip()
    if not text:
        return
    key = f"{lang_of(text)}:{norm_text(text)}"
    item = terms.setdefault(
        key,
        {
            "text": text,
            "lang": lang_of(text),
            "count": 0,
            "source": [],
            "roles": [],
        },
    )
    if count:
        item["count"] += int(count)
    if source not in item["source"]:
        item["source"].append(source)
    if role and role not in item["roles"]:
        item["roles"].append(role)


def mapping_lookup(p5b: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for row in p5b.get("mappings") or []:
        rows[(row.get("en_key") or "", row.get("canonical_zh") or "")] = row
    return rows


def evidence_from_rows(rows: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        for item in row.get("evidence_examples") or []:
            uid = str(item.get("unit_id") or "")
            if uid and uid not in seen:
                evidence.append(item)
                seen.add(uid)
            if len(evidence) >= limit:
                return evidence
    return evidence


def build_from_p5b(p5b: dict[str, Any]) -> list[dict[str, Any]]:
    lookup = mapping_lookup(p5b)
    groups: list[dict[str, Any]] = []

    for row in p5b.get("en_conflicts") or []:
        terms: dict[str, dict[str, Any]] = {}
        en_key = row.get("en_key") or ""
        canonical_en = row.get("canonical_en") or en_key
        add_term(terms, canonical_en, "p5b", row.get("total_count"), "english_term")
        source_rows = []
        for zh in row.get("zh_options") or []:
            match = lookup.get((en_key, zh))
            add_term(terms, zh, "p5b", (match or {}).get("count"), "zh_option")
            if match:
                source_rows.append(match)
        groups.append(
            {
                "source_types": ["p5b_en_conflict"],
                "source_key": en_key,
                "terms": sorted(terms.values(), key=lambda item: (item["lang"], item["text"])),
                "evidence_examples": evidence_from_rows(source_rows),
                "risk_flags": ["multiple_zh_for_en"],
            }
        )

    for row in p5b.get("zh_conflicts") or []:
        terms = {}
        zh = row.get("canonical_zh") or ""
        add_term(terms, zh, "p5b", row.get("total_count"), "zh_term")
        source_rows = []
        for en_key in row.get("en_options") or []:
            match = next((m for m in p5b.get("mappings") or [] if m.get("en_key") == en_key and m.get("canonical_zh") == zh), None)
            add_term(terms, (match or {}).get("canonical_en") or en_key, "p5b", (match or {}).get("count"), "english_option")
            if match:
                source_rows.append(match)
        groups.append(
            {
                "source_types": ["p5b_zh_conflict"],
                "source_key": zh,
                "terms": sorted(terms.values(), key=lambda item: (item["lang"], item["text"])),
                "evidence_examples": evidence_from_rows(source_rows),
                "risk_flags": ["multiple_en_for_zh"],
            }
        )
    return groups


def build_from_p5a(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    p5a = read_json(path)
    groups: list[dict[str, Any]] = []
    for row in p5a.get("edges") or []:
        if row.get("decision") != "accept":
            continue
        terms: dict[str, dict[str, Any]] = {}
        add_term(terms, row.get("abbreviation"), "p5a", row.get("abbr_unit_count"), "abbreviation")
        add_term(terms, row.get("full_form"), "p5a", row.get("full_form_unit_count"), "full_form")
        for zh in row.get("zh_hints") or []:
            add_term(terms, zh, "p5a", row.get("cooccur_count"), "zh_hint")
        groups.append(
            {
                "source_types": ["p5a_accept", row.get("edge_type") or "p5a_edge"],
                "source_key": row.get("edge_id") or row.get("abbreviation_key"),
                "terms": sorted(terms.values(), key=lambda item: (item["lang"], item["text"])),
                "evidence_examples": row.get("evidence_examples") or [],
                "risk_flags": row.get("risk_flags") or [],
            }
        )
    return groups


def merge_duplicate_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parent = list(range(len(groups)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    seen_terms: dict[str, int] = {}
    for index, group in enumerate(groups):
        for key in bridge_term_keys(group):
            if key in seen_terms:
                union(index, seen_terms[key])
            else:
                seen_terms[key] = index

    components: dict[int, list[dict[str, Any]]] = {}
    for index, group in enumerate(groups):
        components.setdefault(find(index), []).append(group)

    output: list[dict[str, Any]] = []
    for component_groups in components.values():
        source_types: list[str] = []
        source_keys: list[str] = []
        risk_flags: set[str] = set()
        evidence_rows: list[dict[str, Any]] = []
        terms_by_key: dict[str, dict[str, Any]] = {}
        for group in component_groups:
            for source_type in group.get("source_types") or []:
                if source_type not in source_types:
                    source_types.append(source_type)
            if group.get("source_key"):
                source_keys.append(str(group.get("source_key")))
            risk_flags.update(group.get("risk_flags") or [])
            evidence_rows.append({"evidence_examples": group.get("evidence_examples") or []})
            for term in group.get("terms") or []:
                key = term_key(term)
                item = terms_by_key.setdefault(key, {**term, "source": [], "roles": [], "count": 0})
                item["count"] = max(int(item.get("count") or 0), int(term.get("count") or 0))
                for source in term.get("source") or []:
                    if source not in item["source"]:
                        item["source"].append(source)
                for role in term.get("roles") or []:
                    if role not in item["roles"]:
                        item["roles"].append(role)
        output.append(
            {
                "source_types": source_types,
                "source_keys": sorted(set(source_keys)),
                "source_key": sorted(set(source_keys))[0] if source_keys else "",
                "terms": sorted(terms_by_key.values(), key=lambda item: (item["lang"], item["text"])),
                "evidence_examples": evidence_from_rows(evidence_rows),
                "risk_flags": sorted(risk_flags),
            }
        )
    for index, group in enumerate(output, start=1):
        group["candidate_group_id"] = f"p5c_cand_{index:06d}"
    return output


def preview(groups: list[dict[str, Any]], limit: int = 120) -> str:
    lines = [
        "# P5C alias candidate groups",
        "",
        f"- candidate_group_count: {len(groups)}",
        "",
        "| id | sources | terms | risks | evidence |",
        "|---|---|---|---|---:|",
    ]
    for group in groups[:limit]:
        terms = "; ".join(f"{term['text']}({term['lang']}, {term.get('count', 0)})" for term in group.get("terms") or [])
        lines.append(
            f"| {group['candidate_group_id']} | {', '.join(group.get('source_types') or [])} | {terms} | {', '.join(group.get('risk_flags') or [])} | {len(group.get('evidence_examples') or [])} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build P5C alias candidate groups for sub-agent review.")
    parser.add_argument("--p5b", type=Path, default=DEFAULT_P5B)
    parser.add_argument("--p5a", type=Path, default=DEFAULT_P5A)
    parser.add_argument("--include-p5a", action="store_true")
    parser.add_argument("--include-p5a-test", action="store_true", help="Deprecated alias for --include-p5a.")
    parser.add_argument("--p5a-limit", type=int, default=0)
    parser.add_argument("--p5b-limit", type=int, default=0)
    parser.add_argument("--must-contain", action="append", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    args = parser.parse_args()

    p5b_groups = build_from_p5b(read_json(args.p5b))
    if args.p5b_limit > 0:
        p5b_groups = p5b_groups[: args.p5b_limit]
    groups = p5b_groups
    include_p5a = bool(args.include_p5a or args.include_p5a_test)
    if include_p5a:
        p5a_groups = build_from_p5a(args.p5a)
        if args.p5a_limit > 0:
            p5a_groups = p5a_groups[: args.p5a_limit]
        groups.extend(p5a_groups)
    groups = merge_duplicate_groups(groups)
    groups.sort(key=lambda group: (group["source_types"], group["source_key"] or ""))
    if args.must_contain:
        filters = {norm_text(item) for item in args.must_contain}
        groups = [
            group
            for group in groups
            if any(norm_text(term.get("text") or "") in filters for term in group.get("terms") or [])
        ]
    if args.limit > 0:
        groups = groups[: args.limit]
        for index, group in enumerate(groups, start=1):
            group["candidate_group_id"] = f"p5c_cand_{index:06d}"

    payload = {
        "summary": {
            "candidate_group_count": len(groups),
            "include_p5a": include_p5a,
            "p5a_limit": args.p5a_limit,
            "p5b_limit": args.p5b_limit,
        },
        "candidate_groups": groups,
    }
    write_json(args.output, payload)
    write_text(args.preview, preview(groups))
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
