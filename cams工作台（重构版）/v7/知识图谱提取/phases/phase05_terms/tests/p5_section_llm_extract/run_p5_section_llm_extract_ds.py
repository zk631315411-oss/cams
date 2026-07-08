from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


TEST_DIR = Path(__file__).resolve().parent
PHASE_DIR = TEST_DIR.parents[1]
KG_ROOT = PHASE_DIR.parents[1]
UNITS_FILE = KG_ROOT / "phases" / "phase01_chapter_index" / "outputs" / "all_chapters_units.jsonl"
ELIGIBLE_UNITS_FILE = KG_ROOT / "phases" / "phase00_quality_gate" / "outputs" / "eligible_units.jsonl"
DEFAULT_PROMPT = TEST_DIR / "prompt_p5_section_terms_v1.md"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_deepseek_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_BASE_URL
            return value, base_url, env_name
    raise RuntimeError("DEEPSEEK_API_KEY / DS_API_KEY / DS_KEY is not set.")


def extract_json_object(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    candidates = [text]
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            try:
                import json_repair

                parsed = json.loads(json_repair.repair_json(candidate))
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                continue
    return None


def section_sort_key(section_id: str) -> tuple[int, int]:
    match = re.match(r"CH(\d+)-S(\d+)", section_id)
    if not match:
        return (10**9, 10**9)
    return (int(match.group(1)), int(match.group(2)))


def load_sections(scope: str) -> list[dict[str, Any]]:
    eligible_by_id = {row["unit_id"]: row for row in read_jsonl(ELIGIBLE_UNITS_FILE)}
    grouped: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(UNITS_FILE):
        chapter_id = str(row.get("chapter_id") or "")
        if scope == "first5" and not chapter_id.startswith(("CH01", "CH02", "CH03", "CH04", "CH05")):
            continue
        section_id = str(row.get("section_id") or "")
        if not section_id:
            continue
        section = grouped.setdefault(
            section_id,
            {
                "section_id": section_id,
                "chapter_id": chapter_id,
                "section_order": row.get("section_order"),
                "section_title": row.get("section_title"),
                "units": [],
            },
        )
        full_unit = dict(row)
        extra = eligible_by_id.get(row.get("unit_id"), {})
        if extra.get("terms"):
            full_unit["terms"] = extra.get("terms")
        section["units"].append(full_unit)
    sections = list(grouped.values())
    for section in sections:
        section["units"].sort(key=lambda unit: unit.get("unit_order", 10**12))
    sections.sort(key=lambda section: section_sort_key(section["section_id"]))
    return sections


def build_section_input(section: dict[str, Any]) -> dict[str, Any]:
    units = []
    for unit in section.get("units") or []:
        units.append(
            {
                "unit_id": unit.get("unit_id"),
                "unit_order": unit.get("unit_order"),
                "type": unit.get("type"),
                "en_quote": unit.get("en_quote"),
                "knowledge_zh": unit.get("knowledge_zh"),
                "terms_hint": unit.get("terms") or [],
            }
        )
    return {
        "task": "P5 section-level term dictionary extraction",
        "section_id": section.get("section_id"),
        "chapter_id": section.get("chapter_id"),
        "section_title": section.get("section_title"),
        "unit_count": len(units),
        "units": units,
        "section_text_with_unit_anchors": "\n".join(
            f"[{unit.get('unit_id')}|{unit.get('unit_order')}] {unit.get('en_quote') or ''}" for unit in units
        ),
    }


def build_messages(prompt_text: str, section_input: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": "Extract P5 dictionary candidates from this section. Return one JSON object only.\n\n" + canonical_json(section_input)},
    ]


def contains_term_text(source_text: str, value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    pattern = re.escape(text)
    if re.fullmatch(r"[A-Z][A-Z0-9/&.-]{1,}", text):
        pattern += r"s?"
    if text[0].isalnum():
        pattern = r"(?<![A-Za-z0-9])" + pattern
    if text[-1].isalnum():
        pattern += r"(?![A-Za-z0-9])"
    return re.search(pattern, source_text, flags=re.IGNORECASE) is not None


def has_parenthetical_evidence_structure(evidence_quote: Any) -> bool:
    quote = str(evidence_quote or "")
    for match in re.finditer(r"\(([^()]+)\)", quote):
        inside = match.group(1).strip()
        outside = (quote[: match.start()] + quote[match.end() :]).strip()
        if inside and outside:
            return True
    return False


def append_repair_flag(output: dict[str, Any], repair: dict[str, Any]) -> None:
    flags = output.get("review_flags")
    if not isinstance(flags, list):
        flags = []
        output["review_flags"] = flags
    flags.append({"type": "repair", **repair})


def repair_output(section_input: dict[str, Any], output: dict[str, Any] | None) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    if output is None:
        return None, []
    repairs: list[dict[str, Any]] = []
    terms = output.get("terms")
    if not isinstance(terms, list):
        return output, repairs

    section_text = str(section_input.get("section_text_with_unit_anchors") or "")
    term_hint_text = canonical_json([unit.get("terms_hint") or [] for unit in section_input.get("units") or []])
    abbreviation_source_text = f"{section_input.get('section_title') or ''}\n{section_text}\n{term_hint_text}"

    for index, term in enumerate(terms):
        if not isinstance(term, dict):
            continue
        kept_abbreviations = []
        for abbreviation in term.get("abbreviations") or []:
            abbr_text = str(abbreviation or "").strip()
            if abbr_text and not contains_term_text(abbreviation_source_text, abbr_text):
                repair = {
                    "repair_type": "removed_abbreviation_not_in_section_or_hint",
                    "term_index": index,
                    "term": term.get("canonical_en") or term.get("canonical_zh") or abbr_text,
                    "abbreviation": abbr_text,
                }
                repairs.append(repair)
                append_repair_flag(output, repair)
            else:
                kept_abbreviations.append(abbreviation)
        if isinstance(term.get("abbreviations"), list):
            term["abbreviations"] = kept_abbreviations

        occurrences = term.get("occurrences")
        if not isinstance(occurrences, list):
            continue
        for occurrence_index, occurrence in enumerate(occurrences):
            if not isinstance(occurrence, dict):
                continue
            if occurrence.get("evidence_type") == "abbreviation_full_form" and not has_parenthetical_evidence_structure(occurrence.get("evidence_quote")):
                original_type = occurrence.get("evidence_type")
                occurrence["evidence_type"] = "mention"
                repair = {
                    "repair_type": "downgraded_abbreviation_full_form_without_parenthetical_evidence",
                    "term_index": index,
                    "occurrence_index": occurrence_index,
                    "term": term.get("canonical_en") or term.get("canonical_zh") or "",
                    "unit_id": occurrence.get("unit_id"),
                    "original_evidence_type": original_type,
                    "new_evidence_type": "mention",
                    "evidence_quote": occurrence.get("evidence_quote"),
                }
                repairs.append(repair)
                append_repair_flag(output, repair)
    return output, repairs


def validate_output(section_input: dict[str, Any], output: dict[str, Any] | None) -> list[dict[str, Any]]:
    if output is None:
        return [{"issue": "model_output_malformed"}]
    issues: list[dict[str, Any]] = []
    if output.get("section_id") != section_input.get("section_id"):
        issues.append({"issue": "section_id_mismatch", "actual": output.get("section_id")})
    terms = output.get("terms")
    if not isinstance(terms, list):
        return issues + [{"issue": "terms_not_list"}]
    allowed_units = {unit.get("unit_id") for unit in section_input.get("units") or []}
    section_text = str(section_input.get("section_text_with_unit_anchors") or "")
    term_hint_text = canonical_json([unit.get("terms_hint") or [] for unit in section_input.get("units") or []])
    abbreviation_source_text = f"{section_input.get('section_title') or ''}\n{section_text}\n{term_hint_text}"
    for index, term in enumerate(terms):
        if not isinstance(term, dict):
            issues.append({"issue": "term_not_object", "index": index})
            continue
        if not term.get("canonical_en") and not term.get("canonical_zh") and not term.get("abbreviations"):
            issues.append({"issue": "empty_term_identity", "index": index})
        if len(str(term.get("notes") or "")) > 160:
            issues.append({"issue": "notes_too_long", "index": index, "term": term.get("canonical_en")})
        for abbreviation in term.get("abbreviations") or []:
            abbr_text = str(abbreviation or "").strip()
            if abbr_text and not contains_term_text(abbreviation_source_text, abbr_text):
                issues.append({"issue": "abbreviation_not_in_section_or_hint", "index": index, "abbreviation": abbr_text, "term": term.get("canonical_en")})
        occurrences = term.get("occurrences")
        if not isinstance(occurrences, list) or not occurrences:
            issues.append({"issue": "missing_occurrences", "index": index, "term": term.get("canonical_en")})
            continue
        seen_occurrences: set[tuple[str, str, str]] = set()
        for occurrence in occurrences:
            unit_id = occurrence.get("unit_id") if isinstance(occurrence, dict) else None
            if unit_id not in allowed_units:
                issues.append({"issue": "occurrence_unit_not_in_section", "index": index, "unit_id": unit_id})
            if isinstance(occurrence, dict):
                key = (str(unit_id), str(occurrence.get("evidence_type") or ""), str(occurrence.get("evidence_quote") or ""))
                if key in seen_occurrences:
                    issues.append({"issue": "duplicate_occurrence", "index": index, "unit_id": unit_id})
                seen_occurrences.add(key)
                if occurrence.get("evidence_type") == "abbreviation_full_form" and not has_parenthetical_evidence_structure(occurrence.get("evidence_quote")):
                    issues.append(
                        {
                            "issue": "abbreviation_full_form_without_parenthetical_evidence",
                            "index": index,
                            "unit_id": unit_id,
                            "evidence_quote": occurrence.get("evidence_quote"),
                        }
                    )
    return issues


def call_model(client: Any, model: str, messages: list[dict[str, str]], max_tokens: int, disable_thinking: bool) -> tuple[str, dict[str, Any]]:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    if disable_thinking:
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    resp = client.chat.completions.create(**kwargs)
    raw = (resp.choices[0].message.content or "").strip()
    usage = getattr(resp, "usage", None)
    return raw, usage.model_dump() if hasattr(usage, "model_dump") else {}


def run_one(args: argparse.Namespace, client: Any, prompt_text: str, section: dict[str, Any]) -> dict[str, Any]:
    section_id = str(section.get("section_id") or "")
    run_dir = TEST_DIR / "runs" / args.run_slug / "sections" / section_id
    section_input = build_section_input(section)
    messages = build_messages(prompt_text, section_input)
    write_json(run_dir / "input_section_terms.json", section_input)
    raw, usage = call_model(client, args.model, messages, args.max_tokens, args.disable_thinking)
    (run_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
    parsed = extract_json_object(raw)
    repaired, repairs = repair_output(section_input, parsed)
    if repaired is not None:
        write_json(run_dir / "parsed_response.json", repaired)
        if repairs:
            write_json(run_dir / "repair_log.json", repairs)
    issues = validate_output(section_input, repaired)
    repair_counts: dict[str, int] = {}
    for repair in repairs:
        repair_type = str(repair.get("repair_type") or "unknown_repair")
        repair_counts[repair_type] = repair_counts.get(repair_type, 0) + 1
    manifest = {
        "schema_version": "p5_section_llm_extract_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "section_id": section_id,
        "section_title": section.get("section_title"),
        "model": args.model,
        "prompt_sha256": sha256_text(prompt_text),
        "input_sha256": sha256_text(canonical_json(section_input)),
        "usage": usage,
        "repair_count": len(repairs),
        "repair_counts": repair_counts,
        "repairs": repairs,
        "status": "passed" if not issues else "validation_failed",
        "issues": issues,
    }
    write_json(run_dir / "run_manifest.json", manifest)
    return {
        "section_id": section_id,
        "section_title": section.get("section_title"),
        "run_dir": str(run_dir),
        "status": manifest["status"],
        "issues": issues,
        "repair_count": len(repairs),
        "repair_counts": repair_counts,
        "term_count": len((repaired or {}).get("terms") or []),
    }


def collect_outputs(run_slug: str, sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section in sections:
        section_id = str(section.get("section_id") or "")
        parsed_path = TEST_DIR / "runs" / run_slug / "sections" / section_id / "parsed_response.json"
        if not parsed_path.exists():
            continue
        rows.append(json.loads(parsed_path.read_text(encoding="utf-8-sig")))
    return rows


def write_preview(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = ["# P5 section LLM extraction preview", ""]
    for row in rows:
        lines.extend([f"## {row.get('section_id')} {row.get('section_title')}", ""])
        for term in (row.get("terms") or [])[:20]:
            abbrs = ", ".join(term.get("abbreviations") or [])
            fulls = ", ".join(term.get("full_forms") or [])
            zh = term.get("canonical_zh") or ""
            occurrences = term.get("occurrences") or []
            unit_ids = ", ".join(dict.fromkeys(str(item.get("unit_id")) for item in occurrences if isinstance(item, dict)))
            lines.append(f"- {term.get('canonical_en') or ''} | {zh} | abbr: {abbrs} | full: {fulls} | units: {unit_ids}")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["first5", "all"], default="first5")
    parser.add_argument("--section-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--max-tokens", type=int, default=6000)
    parser.add_argument("--disable-thinking", action="store_true", default=True)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--run-slug", default="p5_section_llm_extract_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sections = load_sections(args.scope)
    if args.section_id:
        wanted = set(args.section_id)
        sections = [section for section in sections if section.get("section_id") in wanted]
    else:
        sections = sections[args.offset : args.offset + args.limit]
    if not sections:
        raise SystemExit("No sections selected.")

    prompt_text = args.prompt_file.resolve().read_text(encoding="utf-8")
    from openai import OpenAI

    api_key, base_url, key_source = get_deepseek_config()
    client = OpenAI(api_key=api_key, base_url=args.base_url or base_url)

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        future_map = {executor.submit(run_one, args, client, prompt_text, section): section for section in sections}
        for future in as_completed(future_map):
            result = future.result()
            results.append(result)
            print(json.dumps({"section_id": result["section_id"], "status": result["status"], "term_count": result["term_count"]}, ensure_ascii=False))

    order = {section["section_id"]: index for index, section in enumerate(sections)}
    results.sort(key=lambda row: order.get(row["section_id"], 10**9))
    rows = collect_outputs(args.run_slug, sections)
    output_jsonl = TEST_DIR / "outputs" / f"{args.run_slug}.jsonl"
    preview_md = TEST_DIR / "previews" / f"{args.run_slug}_preview.md"
    write_jsonl(output_jsonl, rows)
    write_preview(preview_md, rows)
    summary = {
        "schema_version": "p5_section_llm_extract_summary_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_slug": args.run_slug,
        "scope": args.scope,
        "model": args.model,
        "api_key_source": key_source,
        "selected_count": len(sections),
        "passed_count": sum(1 for row in results if row["status"] == "passed"),
        "failed_count": sum(1 for row in results if row["status"] != "passed"),
        "repair_count": sum(int(row.get("repair_count") or 0) for row in results),
        "output_jsonl": str(output_jsonl),
        "preview_md": str(preview_md),
        "results": results,
    }
    summary_path = TEST_DIR / "runs" / f"{args.run_slug}_summary.json"
    write_json(summary_path, summary)
    print(json.dumps({"summary_path": str(summary_path), "output_jsonl": str(output_jsonl), "preview_md": str(preview_md), "passed": summary["passed_count"], "failed": summary["failed_count"], "repairs": summary["repair_count"]}, ensure_ascii=False))
    if summary["failed_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
