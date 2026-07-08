from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


TEST_DIR = Path(__file__).resolve().parent
PHASE_DIR = TEST_DIR.parent.parent
KG_DIR = PHASE_DIR.parent.parent
P2_DIR = PHASE_DIR.parent / "phase02_core_points"
DEFAULT_PROMPT = TEST_DIR / "prompt_p4b_cross_chapter_relation_v1.md"
DEFAULT_P2A_PREFIX = "p2a_batch_first5_chapters_20260706_"
DEFAULT_P2B_PREFIX = "p2b_first5_reviewed_20260706_"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
ALLOWED_RELATION_TYPES = {"summarizes", "illustrates", "grounds", "contrasts", "none"}
ALLOWED_DECISIONS = {"accept", "reject"}


DOMAIN_TERMS = {
    "aml", "money", "laundering", "placement", "layering", "integration",
    "predicate", "crime", "financial", "risk", "sanctions", "evasion",
    "bribery", "corruption", "fraud", "terrorism", "terrorist", "financing",
    "human", "trafficking", "smuggling", "drug", "environmental", "cyber",
    "virtual", "asset", "crypto", "hawala", "ars", "tbml", "shell",
    "company", "compliance", "monitoring", "kyc", "beneficial", "ownership",
    "red", "flag", "typology", "case", "risk", "control", "obliged",
    "entity", "operational", "legal", "reputational", "concentration",
}

SIGNAL_GROUPS = {
    "money_laundering": ({"money", "laundering"}, 3.0),
    "predicate_crime": ({"predicate", "crime"}, 3.0),
    "predicate_crimes": ({"predicate", "crimes"}, 3.0),
    "sanctions_evasion": ({"sanctions", "evasion"}, 3.0),
    "terrorist_financing": ({"terrorist", "financing"}, 3.0),
    "terrorism_financing": ({"terrorism", "financing"}, 3.0),
    "bribery_corruption": ({"bribery", "corruption"}, 2.5),
    "human_trafficking": ({"human", "trafficking"}, 2.5),
    "human_smuggling": ({"human", "smuggling"}, 2.5),
    "drug_trafficking": ({"drug", "trafficking"}, 2.5),
    "money_laundering_stages": ({"placement", "layering", "integration"}, 3.5),
    "hawala_ars": ({"hawala", "ars"}, 2.5),
    "beneficial_ownership": ({"beneficial", "ownership"}, 2.5),
    "tbml": ({"tbml"}, 2.0),
    "crypto": ({"crypto"}, 2.0),
    "fraud": ({"fraud"}, 2.0),
    "cyber": ({"cyber"}, 2.0),
}


STOP_TERMS = {
    "and", "or", "the", "of", "to", "in", "for", "with", "from", "as", "a",
    "an", "by", "on", "into", "through", "about", "between", "types", "type",
    "overview", "key", "takeaways", "definition", "definitions", "examples",
}


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


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


def parse_unit_texts(section_text: str | None) -> dict[str, str]:
    if not section_text:
        return {}
    unit_texts: dict[str, str] = {}
    pattern = re.compile(r"\[(v7u_N\d+)\|\d+\]\s*(.*)")
    for line in section_text.splitlines():
        match = pattern.match(line.strip())
        if match:
            unit_texts[match.group(1)] = match.group(2).strip()
    return unit_texts


def section_id_from_cp_id(cp_id: str) -> str:
    match = re.match(r"cp_(CH\d+)_S(\d+)", cp_id)
    return f"{match.group(1)}-S{match.group(2)}" if match else ""


def load_section_input(section_id: str, p2a_prefix: str) -> dict[str, Any]:
    path = P2_DIR / "runs" / f"{p2a_prefix}{section_id}" / "input_section.json"
    return read_json(path) if path.exists() else {}


def load_core_points_for_section(section_id: str, p2a_prefix: str) -> tuple[list[dict[str, Any]], str]:
    reviewed_path = P2_DIR / "outputs" / f"p2a_reviewed_core_points.{section_id}.json"
    if reviewed_path.exists():
        return read_json(reviewed_path).get("core_points") or [], "p2a_review"
    raw_path = P2_DIR / "runs" / f"{p2a_prefix}{section_id}" / "parsed_response.json"
    if raw_path.exists():
        return read_json(raw_path).get("core_points") or [], "p2a_raw"
    return [], "missing"


def load_p2b_edges(cp_id: str, p2b_prefix: str, unit_texts: dict[str, str]) -> list[dict[str, Any]]:
    path = P2_DIR / "runs" / f"{p2b_prefix}{cp_id}" / "parsed_response.json"
    if not path.exists():
        return []
    parsed = read_json(path)
    edges = []
    for edge in parsed.get("core_point_unit_edges") or []:
        unit_id = str(edge.get("unit_id") or "")
        edges.append(
            {
                "unit_id": unit_id,
                "edge_type": edge.get("edge_type"),
                "unit_text": unit_texts.get(unit_id, ""),
                "reason": edge.get("reason"),
            }
        )
    return edges


def collect_core_points(chapters: set[str], p2a_prefix: str, p2b_prefix: str) -> list[dict[str, Any]]:
    cps: list[dict[str, Any]] = []
    run_dirs = sorted((P2_DIR / "runs").glob(f"{p2a_prefix}CH*-S*"))
    for run_dir in run_dirs:
        section_id = run_dir.name.replace(p2a_prefix, "", 1)
        chapter_id = section_id.split("-")[0]
        if chapter_id not in chapters:
            continue
        section_input = load_section_input(section_id, p2a_prefix)
        unit_texts = parse_unit_texts(section_input.get("section_text_with_unit_anchors"))
        core_points, source = load_core_points_for_section(section_id, p2a_prefix)
        for cp in core_points:
            cp_id = str(cp.get("draft_core_point_id") or cp.get("core_point_id") or "")
            if not cp_id:
                continue
            p2b_edges = load_p2b_edges(cp_id, p2b_prefix, unit_texts)
            cps.append(
                {
                    "core_point_id": cp_id,
                    "chapter_id": chapter_id,
                    "section_id": section_id,
                    "section_title": section_input.get("section_title"),
                    "source": source,
                    "title_en": cp.get("title_en") or "",
                    "title_zh": cp.get("title_zh") or "",
                    "reason": cp.get("reason") or "",
                    "anchor_unit_ids": cp.get("anchor_unit_ids") or [],
                    "support_unit_ids": cp.get("support_unit_ids") or [],
                    "p2b_unit_edges": p2b_edges,
                }
            )
    return cps


def tokenize(text: str) -> set[str]:
    tokens = {token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]+", text or "")}
    return {token for token in tokens if token not in STOP_TERMS and len(token) > 2}


def cp_text(cp: dict[str, Any]) -> str:
    edge_text = " ".join(str(edge.get("unit_text") or "") for edge in cp.get("p2b_unit_edges") or [])
    return " ".join([str(cp.get("title_en") or ""), str(cp.get("reason") or ""), edge_text])


def matched_signal_groups(tokens: set[str]) -> dict[str, float]:
    matches: dict[str, float] = {}
    for name, (required_terms, weight) in SIGNAL_GROUPS.items():
        if required_terms.issubset(tokens):
            matches[name] = weight
    return matches


def summarize_cp(cp: dict[str, Any]) -> dict[str, Any]:
    edges = cp.get("p2b_unit_edges") or []
    return {
        "core_point_id": cp.get("core_point_id"),
        "chapter_id": cp.get("chapter_id"),
        "section_id": cp.get("section_id"),
        "section_title": cp.get("section_title"),
        "title_en": cp.get("title_en"),
        "reason": cp.get("reason"),
        "unit_edges": edges[:4],
    }


def score_pair(a: dict[str, Any], b: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    text_a = cp_text(a)
    text_b = cp_text(b)
    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)
    shared = sorted((tokens_a & tokens_b) & DOMAIN_TERMS)
    all_shared = sorted(tokens_a & tokens_b)
    groups_a = matched_signal_groups(tokens_a)
    groups_b = matched_signal_groups(tokens_b)
    shared_groups = sorted(set(groups_a) & set(groups_b))
    source_tags: list[str] = []
    score = 0.0
    if shared_groups:
        score += sum(min(groups_a[group], groups_b[group]) for group in shared_groups)
        source_tags.extend(f"shared_{group}" for group in shared_groups)
    if "case" in tokenize(str(a.get("title_en"))) or "case" in tokenize(str(b.get("title_en"))):
        if shared_groups:
            score += 2.0
            source_tags.append("case_with_shared_signal_group")
    foundation_terms = {"definition", "framework", "stages", "process", "classification", "comparison"}
    if (tokenize(str(a.get("title_en"))) & foundation_terms) or (tokenize(str(b.get("title_en"))) & foundation_terms):
        if shared_groups:
            score += 1.5
            source_tags.append("foundation_title")
    if len(shared_groups) >= 2:
        score += 1.0
        source_tags.append("multiple_signal_groups")
    return score, source_tags, all_shared[:12]


def generate_candidates(cps: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for i, cp_a in enumerate(cps):
        for cp_b in cps[i + 1:]:
            if cp_a["chapter_id"] == cp_b["chapter_id"]:
                continue
            score, source_tags, shared_terms = score_pair(cp_a, cp_b)
            if score < 4.5:
                continue
            candidates.append(
                {
                    "candidate_id": f"p4cand_{len(candidates) + 1:04d}",
                    "cp_a_id": cp_a["core_point_id"],
                    "cp_b_id": cp_b["core_point_id"],
                    "cp_a_chapter_id": cp_a["chapter_id"],
                    "cp_b_chapter_id": cp_b["chapter_id"],
                    "cp_a_section_id": cp_a["section_id"],
                    "cp_b_section_id": cp_b["section_id"],
                    "cp_a_title_en": cp_a["title_en"],
                    "cp_b_title_en": cp_b["title_en"],
                    "candidate_score": round(score, 3),
                    "candidate_source": sorted(set(source_tags)),
                    "shared_terms": shared_terms,
                    "cp_a": summarize_cp(cp_a),
                    "cp_b": summarize_cp(cp_b),
                }
            )
    candidates.sort(key=lambda row: (-row["candidate_score"], row["cp_a_id"], row["cp_b_id"]))
    selected = candidates[:limit]
    for index, candidate in enumerate(selected, start=1):
        candidate["candidate_id"] = f"p4cand_{index:04d}"
    return selected


def build_messages(prompt_text: str, candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
    payload = {
        "batch_id": "p4_cross_chapter_probe_20260706",
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    return [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": "Judge these cross-chapter CP candidate pairs. Return one JSON object only.\n\n" + canonical_json(payload)},
    ]


def call_model(args: argparse.Namespace, messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
    from openai import OpenAI

    api_key, base_url, _ = get_deepseek_config()
    client = OpenAI(api_key=api_key, base_url=args.base_url or base_url)
    kwargs: dict[str, Any] = {
        "model": args.model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": args.max_tokens,
        "response_format": {"type": "json_object"},
    }
    if args.disable_thinking:
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    response = client.chat.completions.create(**kwargs)
    raw = (response.choices[0].message.content or "").strip()
    usage = getattr(response, "usage", None)
    return raw, usage.model_dump() if hasattr(usage, "model_dump") else {}


def validate_decisions(candidates: list[dict[str, Any]], output: dict[str, Any] | None) -> list[dict[str, Any]]:
    if output is None:
        return [{"issue": "model_output_malformed"}]
    decisions = output.get("decisions")
    if not isinstance(decisions, list):
        return [{"issue": "decisions_not_list"}]
    candidate_map = {candidate["candidate_id"]: candidate for candidate in candidates}
    issues: list[dict[str, Any]] = []
    seen: set[str] = set()
    for decision in decisions:
        candidate_id = str(decision.get("candidate_id") or "")
        candidate = candidate_map.get(candidate_id)
        if not candidate:
            issues.append({"issue": "unknown_candidate_id", "candidate_id": candidate_id})
            continue
        if candidate_id in seen:
            issues.append({"issue": "duplicate_candidate_id", "candidate_id": candidate_id})
        seen.add(candidate_id)
        if decision.get("decision") not in ALLOWED_DECISIONS:
            issues.append({"issue": "invalid_decision", "candidate_id": candidate_id, "decision": decision.get("decision")})
        if decision.get("relation_type") not in ALLOWED_RELATION_TYPES:
            issues.append({"issue": "invalid_relation_type", "candidate_id": candidate_id, "relation_type": decision.get("relation_type")})
        allowed_cp_ids = {candidate["cp_a_id"], candidate["cp_b_id"]}
        if decision.get("decision") == "accept":
            if decision.get("source_core_point_id") not in allowed_cp_ids:
                issues.append({"issue": "source_core_point_id_not_in_pair", "candidate_id": candidate_id})
            if decision.get("target_core_point_id") not in allowed_cp_ids:
                issues.append({"issue": "target_core_point_id_not_in_pair", "candidate_id": candidate_id})
            if decision.get("relation_type") == "none":
                issues.append({"issue": "accepted_none_relation", "candidate_id": candidate_id})
        if decision.get("decision") == "reject" and decision.get("relation_type") != "none":
            issues.append({"issue": "rejected_non_none_relation", "candidate_id": candidate_id})
    missing = sorted(set(candidate_map) - seen)
    if missing:
        issues.append({"issue": "missing_decisions", "candidate_ids": missing})
    return issues


def write_report(path: Path, candidates: list[dict[str, Any]], decisions: list[dict[str, Any]], issues: list[dict[str, Any]]) -> None:
    accepted = [row for row in decisions if row.get("decision") == "accept"]
    rejected = [row for row in decisions if row.get("decision") == "reject"]
    by_type: dict[str, int] = {}
    for row in accepted:
        rel_type = str(row.get("relation_type") or "")
        by_type[rel_type] = by_type.get(rel_type, 0) + 1
    lines = [
        "# P4 cross-chapter probe report",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- candidates: {len(candidates)}",
        f"- accepted: {len(accepted)}",
        f"- rejected: {len(rejected)}",
        f"- validation_issues: {len(issues)}",
        "",
        "## Accepted by relation type",
        "",
    ]
    if by_type:
        lines.extend(f"- {key}: {by_type[key]}" for key in sorted(by_type))
    else:
        lines.append("- none")
    lines.extend(["", "## Accepted decisions", ""])
    for row in accepted:
        lines.append(
            f"- {row.get('candidate_id')}: `{row.get('relation_type')}` "
            f"{row.get('source_core_point_id')} -> {row.get('target_core_point_id')} | {row.get('reason')}"
        )
    lines.extend(["", "## Validation issues", ""])
    if issues:
        lines.extend(f"- `{issue.get('issue')}` {issue}" for issue in issues)
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    chapters = set(args.chapter)
    run_slug = args.run_slug or "p4_probe_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = TEST_DIR / "runs" / run_slug
    prompt_text = args.prompt_file.read_text(encoding="utf-8")
    cps = collect_core_points(chapters, args.p2a_prefix, args.p2b_prefix)
    candidates = generate_candidates(cps, args.limit_candidates)
    write_json(TEST_DIR / "inputs" / f"{run_slug}_candidates.json", {"core_point_count": len(cps), "candidates": candidates})
    write_json(run_dir / "input_candidates.json", {"core_point_count": len(cps), "candidates": candidates})
    if args.skip_llm:
        print(json.dumps({"status": "candidates_only", "core_points": len(cps), "candidates": len(candidates)}, ensure_ascii=False))
        return
    messages = build_messages(prompt_text, candidates)
    raw, usage = call_model(args, messages)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
    parsed = extract_json_object(raw)
    if parsed is not None:
        write_json(run_dir / "parsed_response.json", parsed)
    issues = validate_decisions(candidates, parsed)
    decisions = parsed.get("decisions") if isinstance(parsed, dict) and isinstance(parsed.get("decisions"), list) else []
    accepted = [row for row in decisions if row.get("decision") == "accept"]
    rejected = [row for row in decisions if row.get("decision") == "reject"]
    write_json(TEST_DIR / "outputs" / f"{run_slug}_decisions.json", parsed or {})
    write_jsonl(TEST_DIR / "outputs" / f"{run_slug}_accepted.jsonl", accepted)
    write_jsonl(TEST_DIR / "outputs" / f"{run_slug}_rejected.jsonl", rejected)
    write_report(TEST_DIR / "reports" / f"{run_slug}_report.md", candidates, decisions, issues)
    manifest = {
        "schema_version": "p4_cross_chapter_probe_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "chapters": sorted(chapters),
        "model": args.model,
        "max_tokens": args.max_tokens,
        "disable_thinking": args.disable_thinking,
        "prompt_sha256": sha256_text(prompt_text),
        "candidate_count": len(candidates),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "validation_issues": issues,
        "usage": usage,
        "status": "passed" if not issues else "validation_failed",
    }
    write_json(run_dir / "run_manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "run_dir": str(run_dir), "candidates": len(candidates), "accepted": len(accepted), "rejected": len(rejected), "issues": len(issues)}, ensure_ascii=False))
    if issues:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P4 cross-chapter relation probe")
    parser.add_argument("--chapter", action="append", default=["CH01", "CH02", "CH03", "CH04", "CH05"])
    parser.add_argument("--p2a-prefix", default=DEFAULT_P2A_PREFIX)
    parser.add_argument("--p2b-prefix", default=DEFAULT_P2B_PREFIX)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--limit-candidates", type=int, default=50)
    parser.add_argument("--run-slug", default=None)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--max-tokens", type=int, default=20000)
    parser.add_argument("--disable-thinking", action="store_true", default=True)
    parser.add_argument("--skip-llm", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
