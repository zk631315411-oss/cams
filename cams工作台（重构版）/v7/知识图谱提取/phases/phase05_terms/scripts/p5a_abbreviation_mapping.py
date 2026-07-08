from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
KG_ROOT = PHASE_DIR.parents[1]

DEFAULT_ELIGIBLE_UNITS = KG_ROOT / "phases" / "phase00_quality_gate" / "outputs" / "eligible_units.jsonl"
DEFAULT_FIRST_FIVE_UNITS = KG_ROOT / "phases" / "phase01_chapter_index" / "outputs" / "first_five_chapters_units.jsonl"
DEFAULT_OUTPUT = PHASE_DIR / "outputs" / "p5a_abbreviation_mapping.json"
DEFAULT_PREVIEW = PHASE_DIR / "previews" / "p5a_abbreviation_mapping_preview.md"
DEFAULT_REPORT = PHASE_DIR / "reports" / "p5a_abbreviation_mapping_report.md"

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
LEGAL_TITLE_WORDS = {"act", "acts", "law", "laws", "regulation", "regulations", "directive", "directives", "amendment", "amendments"}


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


def term_tokens(full_form: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+", full_form.lower())


def term_initials(full_form: str) -> str:
    initials = []
    for token in term_tokens(full_form):
        if token in ACRONYM_STOPWORDS:
            continue
        initials.append(token[0])
    return "".join(initials)


def term_initial_variants(full_form: str) -> set[str]:
    variants = {term_initials(full_form)}
    tokens = term_tokens(full_form)
    token_set = set(tokens)
    has_counter = any(token.startswith(("counter", "combat")) for token in tokens)
    has_terror = "terrorism" in token_set or "terrorist" in token_set
    ctf_component_only = not ({"anti", "money", "laundering"} | LEGAL_TITLE_WORDS) & token_set
    if "financing" in token_set and has_terror and has_counter and ctf_component_only:
        variants.update({"cft", "ctf"})
    return {variant for variant in variants if variant}


def is_abbreviation_like(value: str) -> bool:
    text = str(value or "").strip()
    return bool(text) and text.upper() == text and bool(re.search(r"[A-Z]", text))


def normalized_pair_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def is_self_abbreviation_pair(edge: dict[str, Any]) -> bool:
    return bool(edge.get("full_form")) and normalized_pair_text(edge["full_form"]) == normalized_pair_text(edge["abbreviation"])


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


def joined_slash_components(abbr: str) -> str:
    return "".join(component.strip().lower() for component in str(abbr or "").split("/") if component.strip())


def is_legal_short_title(edge: dict[str, Any]) -> bool:
    tokens = set(term_tokens(edge.get("full_form") or ""))
    if "/" not in str(edge.get("abbreviation") or "") or not (tokens & LEGAL_TITLE_WORDS):
        return False
    abbr_joined = joined_slash_components(edge.get("abbreviation") or "")
    full_norm = normalized_pair_text(edge.get("full_form") or "")
    initials = term_initials(edge.get("full_form") or "")
    return bool(abbr_joined) and (abbr_joined in full_norm or initials.startswith(abbr_joined))


def edge_type_for(edge: dict[str, Any]) -> str:
    if is_self_abbreviation_pair(edge):
        return "self_abbreviation_term"
    if edge.get("compound_component_match"):
        return "compound_abbreviation_component"
    if is_legal_short_title(edge):
        return "legal_short_title"
    if edge.get("initials_match") or edge.get("parenthetical_count", 0) > 0:
        return "abbreviation_full_form"
    return "possible_abbreviation"


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


def load_units(scope: str, eligible_units: Path, first_five_units: Path) -> list[dict[str, Any]]:
    all_units = {row["unit_id"]: row for row in read_jsonl(eligible_units)}
    if scope == "first5":
        first_five_ids = {row["unit_id"] for row in read_jsonl(first_five_units)}
        return [
            all_units[unit_id]
            for unit_id in sorted(first_five_ids, key=lambda uid: all_units[uid].get("unit_order", 10**12))
            if unit_id in all_units
        ]
    return sorted(all_units.values(), key=lambda row: row.get("unit_order", 10**12))


def risk_flags_for_edge(edge: dict[str, Any], passing_full_forms_by_abbr: dict[str, list[str]]) -> list[str]:
    flags: list[str] = []
    if edge["edge_type"] == "self_abbreviation_term":
        flags.append("self_abbreviation_term")
    if edge["edge_type"] == "legal_short_title":
        flags.append("legal_short_title_needs_review")
    if edge["abbr_unit_count"] < MIN_AUTO_ABBR_UNIT_COUNT:
        flags.append("low_frequency_abbreviation")
    if edge["overlap_ratio"] < MIN_AUTO_OVERLAP_RATIO:
        flags.append("low_overlap")
    if edge["full_form_overlap_ratio"] < MIN_AUTO_FULL_FORM_OVERLAP_RATIO:
        flags.append("low_full_form_overlap")
    if "/" not in edge["abbreviation"] and len(passing_full_forms_by_abbr.get(edge["abbreviation_key"], [])) > 1:
        flags.append("multiple_full_form_candidates")
    if "/" in edge["abbreviation"]:
        flags.append("slash_abbreviation")
    if any(ch.isdigit() for ch in edge["abbreviation"]):
        flags.append("numbered_abbreviation")
    return flags


def pass_signals(edge: dict[str, Any]) -> tuple[bool, bool, bool]:
    statistical_pass = (
        edge["cooccur_count"] >= 1
        and edge["abbr_unit_count"] >= MIN_AUTO_ABBR_UNIT_COUNT
        and edge["overlap_ratio"] >= MIN_AUTO_OVERLAP_RATIO
        and edge["full_form_overlap_ratio"] >= MIN_AUTO_FULL_FORM_OVERLAP_RATIO
    )
    strong_pattern_pass = edge["parenthetical_count"] > 0 or edge["compound_component_match"]
    low_frequency_initials_pass = (
        edge["initials_match"]
        and not is_abbreviation_like(edge["full_form"])
        and edge["abbr_unit_count"] <= 3
        and edge["full_form_overlap_ratio"] >= MIN_AUTO_FULL_FORM_OVERLAP_RATIO
    )
    return statistical_pass, strong_pattern_pass, low_frequency_initials_pass


def build_mapping(units: list[dict[str, Any]]) -> dict[str, Any]:
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
                        "full_form": full_form_display.get(full_form, full_form),
                        "zh": sorted(full_form_zh.get(full_form) or []),
                        "en_quote": unit.get("en_quote"),
                    }
                )

    raw_edges: list[dict[str, Any]] = []
    for (abbr, full_form), unit_ids in cooccur_units.items():
        abbr_count = len(abbr_units[abbr])
        full_count = len(full_form_units[full_form])
        co_count = len(unit_ids)
        edge = {
            "abbreviation_key": abbr,
            "abbreviation": display_abbr(abbr),
            "full_form_key": full_form,
            "full_form": full_form_display.get(full_form, full_form),
            "zh_hints": sorted(full_form_zh.get(full_form) or []),
            "cooccur_count": co_count,
            "abbr_unit_count": abbr_count,
            "full_form_unit_count": full_count,
            "overlap_ratio": round(co_count / abbr_count, 4) if abbr_count else 0.0,
            "full_form_overlap_ratio": round(co_count / full_count, 4) if full_count else 0.0,
            "parenthetical_count": len(parenthetical_units.get((abbr, full_form), set())),
            "parenthetical_unit_ids": sorted(parenthetical_units.get((abbr, full_form), set())),
            "initials_match": abbr in term_initial_variants(full_form),
            "compound_component_match": compound_component_match(abbr, full_form),
            "evidence_unit_ids": sorted(unit_ids),
            "evidence_examples": evidence[(abbr, full_form)][:3],
        }
        edge["edge_type"] = edge_type_for(edge)
        raw_edges.append(edge)

    passing_full_forms_by_abbr: dict[str, list[str]] = defaultdict(list)
    for edge in raw_edges:
        statistical_pass, strong_pattern_pass, low_frequency_initials_pass = pass_signals(edge)
        if (statistical_pass or strong_pattern_pass or low_frequency_initials_pass) and edge["edge_type"] not in {"self_abbreviation_term", "legal_short_title"}:
            passing_full_forms_by_abbr[edge["abbreviation_key"]].append(edge["full_form_key"])

    edges: list[dict[str, Any]] = []
    for index, edge in enumerate(raw_edges, start=1):
        statistical_pass, strong_pattern_pass, low_frequency_initials_pass = pass_signals(edge)
        edge["risk_flags"] = risk_flags_for_edge(edge, passing_full_forms_by_abbr)
        edge["match_types"] = []
        if edge["parenthetical_count"] > 0:
            edge["match_types"].append("parenthetical")
        if edge["compound_component_match"]:
            edge["match_types"].append("compound_component_initials")
        if edge["initials_match"]:
            edge["match_types"].append("initials")
        if statistical_pass:
            edge["match_types"].append("statistical_overlap")
        if low_frequency_initials_pass:
            edge["match_types"].append("low_frequency_initials")
        if edge["edge_type"] == "self_abbreviation_term":
            edge["decision"] = "reject"
        elif edge["edge_type"] == "legal_short_title":
            edge["decision"] = "needs_review"
        elif statistical_pass or strong_pattern_pass or low_frequency_initials_pass:
            edge["decision"] = "accept"
        else:
            edge["decision"] = "candidate_only"
        edge["edge_id"] = f"p5a_abbr_{index:06d}"
        edges.append(edge)

    edges.sort(key=lambda row: (row["decision"] != "accept", row["edge_type"], row["abbreviation_key"], -row["cooccur_count"], row["full_form_key"]))
    for index, edge in enumerate(edges, start=1):
        edge["edge_id"] = f"p5a_abbr_{index:06d}"

    cooccur_abbrs = {edge["abbreviation_key"] for edge in edges}
    independent_abbreviations = [
        {
            "abbreviation_key": abbr,
            "abbreviation": display_abbr(abbr),
            "decision": "independent_abbreviation",
            "abbr_unit_count": len(unit_ids),
            "unit_ids": sorted(unit_ids),
            "risk_flags": ["abbreviation_no_full_form"],
        }
        for abbr, unit_ids in sorted(abbr_units.items())
        if abbr not in cooccur_abbrs
    ]
    summary = {
        "unit_count": len(units),
        "abbreviation_count": len(abbr_units),
        "full_form_count": len(full_form_units),
        "edge_count": len(edges),
        "accept_count": sum(1 for row in edges if row["decision"] == "accept"),
        "candidate_only_count": sum(1 for row in edges if row["decision"] == "candidate_only"),
        "needs_review_count": sum(1 for row in edges if row["decision"] == "needs_review"),
        "reject_count": sum(1 for row in edges if row["decision"] == "reject"),
        "independent_abbreviation_count": len(independent_abbreviations),
        "edge_type_counts": {edge_type: sum(1 for row in edges if row["edge_type"] == edge_type) for edge_type in sorted({row["edge_type"] for row in edges})},
    }
    return {"summary": summary, "edges": edges, "independent_abbreviations": independent_abbreviations}


def preview_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    edges = payload["edges"]
    lines = ["# P5A abbreviation mapping preview", "", "## Summary", ""]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Accepted Edges", "", "| abbr | full form | type | zh hints | cooccur | abbr units | full units | match | risks |", "|---|---|---|---|---:|---:|---:|---|---|"])
    for row in [edge for edge in edges if edge["decision"] == "accept"][:100]:
        lines.append(
            f"| {row['abbreviation']} | {row['full_form']} | {row['edge_type']} | {', '.join(row['zh_hints'])} | {row['cooccur_count']} | {row['abbr_unit_count']} | {row['full_form_unit_count']} | {', '.join(row['match_types'])} | {', '.join(row['risk_flags'])} |"
        )
    lines.extend(["", "## Needs Review", "", "| abbr | full form | type | zh hints | cooccur | risks |", "|---|---|---|---|---:|---|"])
    for row in [edge for edge in edges if edge["decision"] == "needs_review"][:100]:
        lines.append(f"| {row['abbreviation']} | {row['full_form']} | {row['edge_type']} | {', '.join(row['zh_hints'])} | {row['cooccur_count']} | {', '.join(row['risk_flags'])} |")
    lines.extend(["", "## Rejected Self Mappings", "", "| abbr | full form | cooccur |", "|---|---|---:|"])
    for row in [edge for edge in edges if edge["decision"] == "reject"][:80]:
        lines.append(f"| {row['abbreviation']} | {row['full_form']} | {row['cooccur_count']} |")
    return "\n".join(lines) + "\n"


def report_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# P5A abbreviation mapping report",
        "",
        "P5A builds pair-level abbreviation edges. It does not build final term groups; P5C consumes accepted/reviewed edges and merges them with P5B translations.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Edge Types",
            "",
            "- `abbreviation_full_form`: ordinary abbreviation/full-form pair.",
            "- `compound_abbreviation_component`: slash abbreviation mapped to one component, such as AML/CFT -> anti-money laundering.",
            "- `legal_short_title`: legal or regulatory title abbreviation that needs review before merging.",
            "- `self_abbreviation_term`: self mapping such as API -> API; rejected from P5A accept output.",
            "- `possible_abbreviation`: weak candidate retained for audit/search but not accepted.",
            "",
            "## Boundary",
            "",
            "P5A treats Chinese labels as `zh_hints` only. P5B remains the source of Chinese-English mapping truth.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 5A abbreviation/full-form mapping.")
    parser.add_argument("--scope", choices=["first5", "all"], default="all")
    parser.add_argument("--eligible-units", type=Path, default=DEFAULT_ELIGIBLE_UNITS)
    parser.add_argument("--first-five-units", type=Path, default=DEFAULT_FIRST_FIVE_UNITS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    units = load_units(args.scope, args.eligible_units, args.first_five_units)
    payload = build_mapping(units)
    payload["summary"]["scope"] = args.scope
    write_json(args.output, payload)
    write_text(args.preview, preview_markdown(payload))
    write_text(args.report, report_markdown(payload))
    print(json.dumps({**payload["summary"], "output": str(args.output)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
