from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


TEST_DIR = Path(__file__).resolve().parent
PHASE_DIR = TEST_DIR.parents[1]
KG_ROOT = PHASE_DIR.parents[1]

FIRST_FIVE_UNITS = KG_ROOT / "phases" / "phase01_chapter_index" / "outputs" / "first_five_chapters_units.jsonl"
ELIGIBLE_UNITS = KG_ROOT / "phases" / "phase00_quality_gate" / "outputs" / "eligible_units.jsonl"

ABBREVIATION_RE = re.compile(r"\b[A-Z][A-Z0-9]{2,}(?:/[A-Z0-9]{2,})?s?\b")
FULL_BEFORE_ABBR_RE = re.compile(
    r"\b(?P<full>[A-Za-z][A-Za-z0-9&'’/\-]*(?:[\s\-]+[A-Za-z0-9&'’/\-]+){1,8})\s*\(\s*(?P<abbr>[A-Z][A-Z0-9]{2,}(?:/[A-Z0-9]{2,})?)s?\s*\)"
)
ABBR_BEFORE_FULL_RE = re.compile(
    r"\b(?P<abbr>[A-Z][A-Z0-9]{2,}(?:/[A-Z0-9]{2,})?)s?\s*\(\s*(?P<full>[A-Za-z][A-Za-z0-9&'’/\-]*(?:[\s\-]+[A-Za-z0-9&'’/\-]+){1,12})\s*\)"
)
MIN_AUTO_ABBR_UNIT_COUNT = 3
MIN_AUTO_OVERLAP_RATIO = 0.5
MIN_AUTO_FULL_FORM_OVERLAP_RATIO = 0.5
ACRONYM_STOPWORDS = {"a", "an", "and", "for", "in", "of", "the", "to"}


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


def norm_abbr(value: str) -> str:
    value = value.strip()
    if value.endswith("s") and len(value) > 3 and value[-2].isupper():
        value = value[:-1]
    return value.lower()


def clean_parenthetical_full_form(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip(" ,.;:-"))
    text = re.sub(r"^(?:the|a|an|and|or)\s+", "", text, flags=re.IGNORECASE)
    return text


def display_abbr(value: str) -> str:
    return value.upper()


def term_initials(full_form: str) -> str:
    initials = []
    for token in re.findall(r"[A-Za-z0-9]+", full_form.lower()):
        if token in ACRONYM_STOPWORDS:
            continue
        initials.append(token[0])
    return "".join(initials)


def term_initial_variants(full_form: str) -> set[str]:
    variants = {term_initials(full_form)}
    tokens = re.findall(r"[A-Za-z0-9]+", full_form.lower())
    has_counter = any(token.startswith(("counter", "combat")) for token in tokens)
    has_terror = "terrorism" in tokens or "terrorist" in tokens
    ctf_component_only = not ({"anti", "money", "laundering", "act", "law", "laws", "regulation", "regulations", "directive", "amendment"} & set(tokens))
    if "financing" in tokens and has_terror and has_counter and ctf_component_only:
        variants.update({"cft", "ctf"})
    return {variant for variant in variants if variant}


def is_abbreviation_like(value: str) -> bool:
    text = str(value or "").strip()
    return bool(text) and text.upper() == text and bool(re.search(r"[A-Z]", text))


def is_self_abbreviation_pair(candidate: dict[str, Any]) -> bool:
    full_form = re.sub(r"[^a-z0-9]+", "", str(candidate["full_form"] or "").lower())
    abbreviation = re.sub(r"[^a-z0-9]+", "", str(candidate["abbreviation"] or "").lower())
    return bool(full_form) and full_form == abbreviation


def phrase_pattern(phrase: str) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", phrase)
    if not tokens:
        return re.escape(phrase)
    escaped = [re.escape(token) for token in tokens]
    escaped[-1] = escaped[-1] + "s?"
    return r"\b" + r"[\s\-]+".join(escaped) + r"\b"


def has_parenthetical_evidence(en_quote: str, full_form: str, abbr_key: str) -> bool:
    if not en_quote or not full_form or not abbr_key:
        return False
    abbr = re.escape(display_abbr(abbr_key))
    abbr_in_parens = abbr + ("s?" if "/" not in abbr_key else "")
    full = phrase_pattern(full_form)
    patterns = [
        full + r"\s*\(\s*" + abbr_in_parens + r"\s*\)",
        r"\b" + abbr_in_parens + r"\b\s*\(\s*" + full + r"\s*\)",
    ]
    return any(re.search(pattern, en_quote, flags=re.IGNORECASE) for pattern in patterns)


def has_precise_parenthetical_evidence(en_quote: str, full_form: str, abbr_key: str) -> bool:
    if not has_parenthetical_evidence(en_quote, full_form, abbr_key):
        return False
    return abbr_key in term_initial_variants(full_form) or compound_component_match(abbr_key, full_form)


def compound_component_match(abbr_key: str, full_form: str) -> bool:
    if "/" not in abbr_key:
        return False
    components = {component.strip().lower() for component in abbr_key.split("/") if component.strip()}
    return bool(components & term_initial_variants(full_form))


def extract_abbreviations(en_quote: str) -> set[str]:
    abbrs: set[str] = set()
    for match in ABBREVIATION_RE.finditer(en_quote or ""):
        raw = match.group(0)
        if raw.isdigit():
            continue
        abbrs.add(norm_abbr(raw))
    return abbrs


def extract_parenthetical_pairs(en_quote: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for pattern in (FULL_BEFORE_ABBR_RE, ABBR_BEFORE_FULL_RE):
        for match in pattern.finditer(en_quote or ""):
            full_form = clean_parenthetical_full_form(match.group("full"))
            abbr = norm_abbr(match.group("abbr"))
            if not full_form or is_abbreviation_like(full_form):
                continue
            pairs.append((abbr, full_form))
    return pairs


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


def risk_flags_for_pair(candidate: dict[str, Any], passing_full_forms_by_abbr: dict[str, list[str]]) -> list[str]:
    flags: list[str] = []
    if is_self_abbreviation_pair(candidate):
        flags.append("self_abbreviation_term")
    if candidate["abbr_unit_count"] < MIN_AUTO_ABBR_UNIT_COUNT:
        flags.append("low_frequency_abbreviation")
    if candidate["overlap_ratio"] < MIN_AUTO_OVERLAP_RATIO:
        flags.append("low_overlap")
    if candidate["full_form_overlap_ratio"] < MIN_AUTO_FULL_FORM_OVERLAP_RATIO:
        flags.append("low_full_form_overlap")
    if "/" not in candidate["abbreviation"] and len(passing_full_forms_by_abbr.get(candidate["abbreviation_key"], [])) > 1:
        flags.append("multiple_full_form_candidates")
    if "/" in candidate["abbreviation"]:
        flags.append("slash_abbreviation")
    if any(ch.isdigit() for ch in candidate["abbreviation"]):
        flags.append("numbered_abbreviation")
    return flags


def main() -> None:
    parser = argparse.ArgumentParser(description="Test P5A abbreviation/full-form discovery.")
    parser.add_argument("--scope", choices=["first5", "all"], default="first5")
    args = parser.parse_args()
    units = load_units(args.scope)

    abbr_units: dict[str, set[str]] = defaultdict(set)
    full_form_units: dict[str, set[str]] = defaultdict(set)
    full_form_display: dict[str, str] = {}
    full_form_zh: dict[str, set[str]] = defaultdict(set)
    cooccur_units: dict[tuple[str, str], set[str]] = defaultdict(set)
    parenthetical_units: dict[tuple[str, str], set[str]] = defaultdict(set)
    evidence: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for unit in units:
        unit_id = str(unit["unit_id"])
        abbrs = extract_abbreviations(unit.get("en_quote") or "")
        terms_by_key: dict[str, str] = {}
        for term in unit.get("terms") or []:
            en = norm_en(term.get("en"))
            if not en:
                continue
            terms_by_key.setdefault(en, str(term.get("en") or "").strip())
            if term.get("zh"):
                full_form_zh[en].add(str(term.get("zh")).strip())
        for abbr, full_form in extract_parenthetical_pairs(unit.get("en_quote") or ""):
            abbrs.add(abbr)
            terms_by_key.setdefault(norm_en(full_form), full_form)
        terms = list(terms_by_key.keys())
        for en, display in terms_by_key.items():
            full_form_display.setdefault(en, display)
        for abbr in abbrs:
            abbr_units[abbr].add(unit_id)
        for full_form in terms:
            full_form_units[full_form].add(unit_id)
        for abbr in abbrs:
            for full_form in terms:
                cooccur_units[(abbr, full_form)].add(unit_id)
                if has_precise_parenthetical_evidence(unit.get("en_quote") or "", full_form_display.get(full_form, full_form), abbr):
                    parenthetical_units[(abbr, full_form)].add(unit_id)
                evidence[(abbr, full_form)].append(
                    {
                        "unit_id": unit_id,
                        "unit_order": unit.get("unit_order"),
                        "chapter": unit.get("chapter"),
                        "full_form": full_form_display.get(full_form, full_form),
                        "zh": sorted(full_form_zh.get(full_form) or []),
                        "en_quote": unit.get("en_quote"),
                    }
                )

    raw_candidates: list[dict[str, Any]] = []
    for (abbr, full_form), unit_ids in cooccur_units.items():
        abbr_count = len(abbr_units[abbr])
        full_count = len(full_form_units[full_form])
        co_count = len(unit_ids)
        overlap_ratio = co_count / abbr_count if abbr_count else 0.0
        full_form_overlap_ratio = co_count / full_count if full_count else 0.0
        raw_candidates.append(
            {
                "abbreviation_key": abbr,
                "abbreviation": display_abbr(abbr),
                "full_form_key": full_form,
                "full_form": full_form_display.get(full_form, full_form),
                "zh": sorted(full_form_zh.get(full_form) or []),
                "decision": "pending",
                "cooccur_count": co_count,
                "abbr_unit_count": abbr_count,
                "full_form_unit_count": full_count,
                "overlap_ratio": round(overlap_ratio, 4),
                "full_form_overlap_ratio": round(full_form_overlap_ratio, 4),
                "parenthetical_count": len(parenthetical_units.get((abbr, full_form), set())),
                "parenthetical_unit_ids": sorted(parenthetical_units.get((abbr, full_form), set())),
                "initials_match": abbr in term_initial_variants(full_form),
                "compound_component_match": compound_component_match(abbr, full_form),
                "evidence_unit_ids": sorted(unit_ids),
                "evidence_examples": evidence[(abbr, full_form)][:3],
            }
        )

    passing_full_forms_by_abbr: dict[str, list[str]] = defaultdict(list)
    for candidate in raw_candidates:
        statistical_pass = (
            candidate["cooccur_count"] >= 1
            and candidate["abbr_unit_count"] >= MIN_AUTO_ABBR_UNIT_COUNT
            and candidate["overlap_ratio"] >= MIN_AUTO_OVERLAP_RATIO
            and candidate["full_form_overlap_ratio"] >= MIN_AUTO_FULL_FORM_OVERLAP_RATIO
        )
        strong_pattern_pass = candidate["parenthetical_count"] > 0 or candidate["compound_component_match"]
        low_frequency_initials_pass = (
            candidate["initials_match"]
            and not is_abbreviation_like(candidate["full_form"])
            and candidate["abbr_unit_count"] <= 3
            and candidate["full_form_overlap_ratio"] >= MIN_AUTO_FULL_FORM_OVERLAP_RATIO
        )
        if (statistical_pass or strong_pattern_pass or low_frequency_initials_pass) and not is_self_abbreviation_pair(candidate):
            passing_full_forms_by_abbr[candidate["abbreviation_key"]].append(candidate["full_form_key"])

    candidates: list[dict[str, Any]] = []
    for candidate in raw_candidates:
        flags = risk_flags_for_pair(candidate, passing_full_forms_by_abbr)
        statistical_pass = (
            candidate["cooccur_count"] >= 1
            and candidate["abbr_unit_count"] >= MIN_AUTO_ABBR_UNIT_COUNT
            and candidate["overlap_ratio"] >= MIN_AUTO_OVERLAP_RATIO
            and candidate["full_form_overlap_ratio"] >= MIN_AUTO_FULL_FORM_OVERLAP_RATIO
        )
        strong_pattern_pass = candidate["parenthetical_count"] > 0 or candidate["compound_component_match"]
        low_frequency_initials_pass = (
            candidate["initials_match"]
            and not is_abbreviation_like(candidate["full_form"])
            and candidate["abbr_unit_count"] <= 3
            and candidate["full_form_overlap_ratio"] >= MIN_AUTO_FULL_FORM_OVERLAP_RATIO
        )
        multiple_strong_candidates = "/" not in candidate["abbreviation"] and len(passing_full_forms_by_abbr.get(candidate["abbreviation_key"], [])) > 1
        if (statistical_pass or strong_pattern_pass or low_frequency_initials_pass) and not multiple_strong_candidates and not is_self_abbreviation_pair(candidate):
            candidate["decision"] = "auto_merge"
        else:
            candidate["decision"] = "candidate_only"
        candidate["risk_flags"] = flags
        candidate["match_types"] = []
        if candidate["parenthetical_count"] > 0:
            candidate["match_types"].append("parenthetical")
        if candidate["compound_component_match"]:
            candidate["match_types"].append("compound_component_initials")
        if candidate["initials_match"]:
            candidate["match_types"].append("initials")
        if statistical_pass:
            candidate["match_types"].append("statistical_overlap")
        if low_frequency_initials_pass:
            candidate["match_types"].append("low_frequency_initials")
        candidates.append(candidate)

    candidates.sort(key=lambda row: (row["decision"] != "auto_merge", row["abbreviation_key"], -row["cooccur_count"], row["full_form_key"]))
    independent_abbreviations = []
    cooccur_abbrs = {candidate["abbreviation_key"] for candidate in candidates}
    for abbr, unit_ids in sorted(abbr_units.items()):
        if abbr not in cooccur_abbrs:
            independent_abbreviations.append(
                {
                    "abbreviation_key": abbr,
                    "abbreviation": display_abbr(abbr),
                    "decision": "independent_abbreviation",
                    "abbr_unit_count": len(unit_ids),
                    "unit_ids": sorted(unit_ids),
                    "risk_flags": ["abbreviation_no_full_form"],
                }
            )

    summary = {
        "scope": args.scope,
        "unit_count": len(units),
        "abbreviation_count": len(abbr_units),
        "full_form_count": len(full_form_units),
        "candidate_pair_count": len(candidates),
        "auto_merge_count": sum(1 for row in candidates if row["decision"] == "auto_merge"),
        "candidate_only_count": sum(1 for row in candidates if row["decision"] == "candidate_only"),
        "independent_abbreviation_count": len(independent_abbreviations),
        "rules": {
            "min_auto_abbr_unit_count": MIN_AUTO_ABBR_UNIT_COUNT,
            "min_auto_overlap_ratio": MIN_AUTO_OVERLAP_RATIO,
            "min_auto_full_form_overlap_ratio": MIN_AUTO_FULL_FORM_OVERLAP_RATIO,
        },
    }

    output_payload = {
        "summary": summary,
        "candidates": candidates,
        "independent_abbreviations": independent_abbreviations,
    }
    suffix = args.scope
    write_json(TEST_DIR / "outputs" / f"p5a_abbreviation_candidates_{suffix}.json", output_payload)
    write_json(TEST_DIR / "outputs" / f"p5a_abbreviation_summary_{suffix}.json", summary)
    write_text(TEST_DIR / "previews" / f"p5a_abbreviation_candidates_{suffix}.md", preview_markdown(summary, candidates, independent_abbreviations))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def preview_markdown(summary: dict[str, Any], candidates: list[dict[str, Any]], independent: list[dict[str, Any]]) -> str:
    lines = [
        "# P5A abbreviation/full-form first-five preview",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        if key != "rules":
            lines.append(f"- {key}: {value}")
    lines.extend(["", "## Auto merge candidates", "", "| abbr | full form | zh | cooccur | abbr units | full units | abbr overlap | full overlap | match | risks |", "|---|---|---|---:|---:|---:|---:|---:|---|---|"])
    for row in [candidate for candidate in candidates if candidate["decision"] == "auto_merge"][:80]:
        lines.append(
            f"| {row['abbreviation']} | {row['full_form']} | {', '.join(row['zh'])} | {row['cooccur_count']} | "
            f"{row['abbr_unit_count']} | {row['full_form_unit_count']} | {row['overlap_ratio']} | {row['full_form_overlap_ratio']} | "
            f"{', '.join(row['match_types'])} | {', '.join(row['risk_flags'])} |"
        )
    lines.extend(["", "## Candidate only", "", "| abbr | full form | zh | cooccur | abbr units | full units | abbr overlap | full overlap | match | risks |", "|---|---|---|---:|---:|---:|---:|---:|---|---|"])
    for row in [candidate for candidate in candidates if candidate["decision"] == "candidate_only"][:120]:
        lines.append(
            f"| {row['abbreviation']} | {row['full_form']} | {', '.join(row['zh'])} | {row['cooccur_count']} | "
            f"{row['abbr_unit_count']} | {row['full_form_unit_count']} | {row['overlap_ratio']} | {row['full_form_overlap_ratio']} | "
            f"{', '.join(row['match_types'])} | {', '.join(row['risk_flags'])} |"
        )
    lines.extend(["", "## Independent abbreviations", "", "| abbr | unit_count | risks |", "|---|---:|---|"])
    for row in independent[:80]:
        lines.append(f"| {row['abbreviation']} | {row['abbr_unit_count']} | {', '.join(row['risk_flags'])} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
