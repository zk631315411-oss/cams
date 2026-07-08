from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
P2_DIR = PHASE_DIR.parent / "phase02_core_points"
DEFAULT_P2A_RUNS_DIR = P2_DIR / "runs"
DEFAULT_P2A_PREFIX = ""
DEFAULT_PROMPT = PHASE_DIR / "prompts" / "p3a_chapter_section_relations_v1.md"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")

ALLOWED_RELATION_TYPES = {"summarizes", "illustrates", "grounds"}


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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


def load_core_points(p2a_run_dir: Path, section_id: str) -> tuple[list[dict[str, Any]], str]:
    reviewed_path = P2_DIR / "outputs" / f"p2a_reviewed_core_points.{section_id}.json"
    if reviewed_path.exists():
        reviewed = read_json(reviewed_path)
        return reviewed.get("core_points") or [], "p2a_review"
    p2a_output = read_json(p2a_run_dir / "parsed_response.json")
    return p2a_output.get("core_points") or [], "p2a_raw"


def section_sort_key(section_id: str) -> tuple[int, int, str]:
    match = re.match(r"CH(\d+)-S(\d+)$", section_id)
    if not match:
        return (10**9, 10**9, section_id)
    return (int(match.group(1)), int(match.group(2)), section_id)


def resolve_p2a_run_dir(reviewed: dict[str, Any], section_id: str, p2a_runs_dir: Path, p2a_run_prefix: str) -> Path | None:
    if p2a_run_prefix:
        candidate = p2a_runs_dir / f"{p2a_run_prefix}{section_id}"
        if (candidate / "input_section.json").exists():
            return candidate

    source_p2a_run = reviewed.get("source_p2a_run")
    if source_p2a_run:
        parsed_path = (P2_DIR / str(source_p2a_run)).resolve()
        if parsed_path.exists() and (parsed_path.parent / "input_section.json").exists():
            return parsed_path.parent

    matches = sorted(
        [path for path in p2a_runs_dir.glob(f"p2a*{section_id}") if (path / "input_section.json").exists()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def discover_reviewed_sections(chapter_id: str) -> list[tuple[str, Path, dict[str, Any]]]:
    rows: list[tuple[str, Path, dict[str, Any]]] = []
    for path in (P2_DIR / "outputs").glob(f"p2a_reviewed_core_points.{chapter_id}-S*.json"):
        reviewed = read_json(path)
        section_id = str(reviewed.get("section_id") or path.name.removeprefix("p2a_reviewed_core_points.").removesuffix(".json"))
        rows.append((section_id, path, reviewed))
    rows.sort(key=lambda row: section_sort_key(row[0]))
    return rows


def summarize_core_point(cp: dict[str, Any], section_id: str, section_order: int, section_title: str) -> dict[str, Any]:
    return {
        "core_point_id": cp.get("draft_core_point_id"),
        "section_id": section_id,
        "section_order": section_order,
        "section_title": section_title,
        "title_zh": cp.get("title_zh"),
        "title_en": cp.get("title_en"),
        "anchor_unit_ids": cp.get("anchor_unit_ids") or [],
        "support_unit_ids": cp.get("support_unit_ids") or [],
        "evidence_unit_spans": cp.get("evidence_unit_spans") or [],
        "reason": cp.get("reason"),
    }


def build_p3a_input(chapter_id: str, p2a_runs_dir: Path, p2a_run_prefix: str) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    reviewed_sections = discover_reviewed_sections(chapter_id)
    if not reviewed_sections and p2a_run_prefix:
        reviewed_sections = [(path.name.removeprefix(p2a_run_prefix), path, {}) for path in sorted(p2a_runs_dir.glob(f"{p2a_run_prefix}{chapter_id}-S*"))]
    for section_id, _reviewed_path, reviewed in reviewed_sections:
        run_dir = resolve_p2a_run_dir(reviewed, section_id, p2a_runs_dir, p2a_run_prefix)
        if run_dir is None:
            continue
        input_path = run_dir / "input_section.json"
        output_path = run_dir / "parsed_response.json"
        if not input_path.exists() or not output_path.exists():
            continue
        section_input = read_json(input_path)
        section_id = str(section_input.get("section_id") or section_id)
        if not section_id:
            continue
        section_order = int(section_input.get("section_order") or 0)
        section_title = str(section_input.get("section_title") or "")
        core_points, source = load_core_points(run_dir, section_id)
        sections.append(
            {
                "section_id": section_id,
                "section_order": section_order,
                "section_title": section_title,
                "section_text_with_unit_anchors": section_input.get("section_text_with_unit_anchors"),
                "core_point_source": source,
                "core_points": [
                    summarize_core_point(cp, section_id, section_order, section_title)
                    for cp in core_points
                    if cp.get("draft_core_point_id")
                ],
            }
        )
    sections.sort(key=lambda row: int(row.get("section_order") or 0))
    core_points = [cp for section in sections for cp in section.get("core_points", [])]
    return {
        "request_id": f"p3a::{chapter_id}",
        "chapter_id": chapter_id,
        "sections": sections,
        "core_points": core_points,
    }


def build_messages(prompt_text: str, p3a_input: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": prompt_text},
        {
            "role": "user",
            "content": "Build P3A same-chapter cross-section core_point relations. Return one JSON object only.\n\n"
            + canonical_json(p3a_input),
        },
    ]


def validate_output(p3a_input: dict[str, Any], output: dict[str, Any] | None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if output is None:
        return [{"issue": "model_output_malformed"}]
    chapter_id = str(p3a_input.get("chapter_id"))
    cp_to_section = {
        str(cp.get("core_point_id")): str(cp.get("section_id"))
        for cp in p3a_input.get("core_points") or []
    }
    if str(output.get("chapter_id")) != chapter_id:
        issues.append({"issue": "chapter_id_mismatch", "expected": chapter_id, "actual": output.get("chapter_id")})
    relations = output.get("core_point_relations", [])
    if not isinstance(relations, list):
        issues.append({"issue": "core_point_relations_not_list"})
        relations = []
    seen_ids: set[str] = set()
    seen_pairs: set[tuple[str, str, str]] = set()
    for rel in relations:
        if not isinstance(rel, dict):
            issues.append({"issue": "relation_not_object"})
            continue
        rel_id = str(rel.get("relation_id") or "")
        source = str(rel.get("source_core_point_id") or "")
        target = str(rel.get("target_core_point_id") or "")
        relation_type = str(rel.get("relation_type") or "")
        if not rel_id:
            issues.append({"issue": "missing_relation_id", "source": source, "target": target})
        elif rel_id in seen_ids:
            issues.append({"issue": "duplicate_relation_id", "relation_id": rel_id})
        seen_ids.add(rel_id)
        if source not in cp_to_section:
            issues.append({"issue": "unknown_source_core_point_id", "relation_id": rel_id, "source": source})
        if target not in cp_to_section:
            issues.append({"issue": "unknown_target_core_point_id", "relation_id": rel_id, "target": target})
        if source == target:
            issues.append({"issue": "self_relation", "relation_id": rel_id})
        if source in cp_to_section and target in cp_to_section and cp_to_section[source] == cp_to_section[target]:
            issues.append({"issue": "same_section_relation", "relation_id": rel_id, "section_id": cp_to_section[source]})
        if relation_type not in ALLOWED_RELATION_TYPES:
            issues.append({"issue": "invalid_relation_type", "relation_id": rel_id, "relation_type": relation_type})
        key = (source, target, relation_type)
        if key in seen_pairs:
            issues.append({"issue": "duplicate_relation_pair", "relation_id": rel_id})
        seen_pairs.add(key)
    return issues


def filter_invalid_relations(p3a_input: dict[str, Any], output: dict[str, Any] | None) -> dict[str, Any] | None:
    if output is None:
        return None
    cp_to_section = {
        str(cp.get("core_point_id")): str(cp.get("section_id"))
        for cp in p3a_input.get("core_points") or []
    }
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str, str]] = set()
    for rel in output.get("core_point_relations") or []:
        if not isinstance(rel, dict):
            removed.append({"removed_relation": rel, "reason": "relation_not_object"})
            continue
        source = str(rel.get("source_core_point_id") or "")
        target = str(rel.get("target_core_point_id") or "")
        relation_type = str(rel.get("relation_type") or "")
        key = (source, target, relation_type)
        reason = None
        if source not in cp_to_section:
            reason = "unknown_source_core_point_id"
        elif target not in cp_to_section:
            reason = "unknown_target_core_point_id"
        elif source == target:
            reason = "self_relation"
        elif cp_to_section[source] == cp_to_section[target]:
            reason = "same_section_relation"
        elif relation_type not in ALLOWED_RELATION_TYPES:
            reason = "invalid_relation_type"
        elif key in seen_pairs:
            reason = "duplicate_relation_pair"
        if reason:
            removed.append({"removed_relation": rel, "reason": reason})
            continue
        seen_pairs.add(key)
        kept.append(rel)
    filtered = dict(output)
    filtered["core_point_relations"] = kept
    review_items = list(filtered.get("review_items") or [])
    review_items.extend(removed)
    filtered["review_items"] = review_items
    return filtered


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


def write_validation_report(path: Path, p3a_input: dict[str, Any], output: dict[str, Any] | None, issues: list[dict[str, Any]]) -> None:
    relations = output.get("core_point_relations", []) if output else []
    lines = [
        "# P3A validation report",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- chapter_id: {p3a_input.get('chapter_id')}",
        f"- sections: {len(p3a_input.get('sections') or [])}",
        f"- core_points: {len(p3a_input.get('core_points') or [])}",
        f"- output_relations: {len(relations) if isinstance(relations, list) else 0}",
        f"- issues: {len(issues)}",
        "",
    ]
    for issue in issues:
        lines.append(json.dumps(issue, ensure_ascii=False))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    p3a_input = build_p3a_input(args.chapter_id, args.p2a_runs_dir.resolve(), args.p2a_run_prefix)
    prompt_text = args.prompt_file.resolve().read_text(encoding="utf-8")
    run_dir = (args.run_dir or (PHASE_DIR / "runs" / args.run_slug)).resolve()
    messages = build_messages(prompt_text, p3a_input)
    manifest = {
        "schema_version": "p3a_chapter_ds_run_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "chapter_id": args.chapter_id,
        "model": args.model,
        "base_url": args.base_url or DEFAULT_BASE_URL,
        "temperature": 0.0,
        "max_tokens": args.max_tokens,
        "disable_thinking": args.disable_thinking,
        "prompt_file": str(args.prompt_file.resolve()),
        "prompt_sha256": sha256_text(prompt_text),
        "input_sha256": sha256_text(canonical_json(p3a_input)),
        "message_sha256": sha256_text(canonical_json(messages)),
    }
    write_json(run_dir / "input_p3a.json", p3a_input)

    from openai import OpenAI

    api_key, base_url, key_source = get_deepseek_config()
    manifest["api_key_source"] = key_source
    manifest["base_url"] = args.base_url or base_url
    client = OpenAI(api_key=api_key, base_url=manifest["base_url"])
    raw, usage = call_model(client, args.model, messages, args.max_tokens, args.disable_thinking)
    (run_dir / "raw_response.txt").parent.mkdir(parents=True, exist_ok=True)
    (run_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
    manifest["usage"] = usage
    parsed = extract_json_object(raw)
    if args.filter_invalid:
        parsed = filter_invalid_relations(p3a_input, parsed)
    if parsed is not None:
        write_json(run_dir / "parsed_response.json", parsed)
    issues = validate_output(p3a_input, parsed)
    manifest["status"] = "passed" if not issues else "validation_failed"
    write_json(run_dir / "run_manifest.json", manifest)
    write_validation_report(run_dir / "validation_report.md", p3a_input, parsed, issues)
    print(json.dumps({"status": manifest["status"], "run_dir": str(run_dir), "issues": len(issues)}, ensure_ascii=False))
    if issues:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter-id", required=True)
    parser.add_argument("--p2a-runs-dir", type=Path, default=DEFAULT_P2A_RUNS_DIR)
    parser.add_argument("--p2a-run-prefix", default=DEFAULT_P2A_PREFIX, help="Optional legacy P2A run prefix. Empty default uses reviewed P2A outputs and source_p2a_run.")
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--run-slug", default="p3a_chapter_test")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--disable-thinking", action="store_true", default=True)
    parser.add_argument("--filter-invalid", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())

