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
DEFAULT_P2A_RUNS_DIR = PHASE_DIR / "runs"
DEFAULT_P2A_PREFIX = "p2a_batch_first5_chapters_20260706_"
DEFAULT_P2B_RUN_PREFIX = "p2b_first5_reviewed_20260706_"
DEFAULT_PROMPT = PHASE_DIR / "prompts" / "p2c_section_cp_relations_v1.md"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")

ALLOWED_RELATION_TYPES = {"contains", "illustrates", "prepares", "parallels", "contrasts"}


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


def find_p2a_run(runs_dir: Path, prefix: str, section_id: str) -> Path:
    run_dir = runs_dir / f"{prefix}{section_id}"
    if not run_dir.exists():
        raise FileNotFoundError(f"P2A run not found: {run_dir}")
    return run_dir


def load_core_points(p2a_run_dir: Path, section_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    reviewed_path = PHASE_DIR / "outputs" / f"p2a_reviewed_core_points.{section_id}.json"
    if reviewed_path.exists():
        reviewed = read_json(reviewed_path)
        return reviewed.get("core_points") or [], {
            "core_point_source": "p2a_review",
            "core_point_source_path": str(reviewed_path),
        }
    p2a_output = read_json(p2a_run_dir / "parsed_response.json")
    return p2a_output.get("core_points") or [], {
        "core_point_source": "p2a_raw",
        "core_point_source_path": str(p2a_run_dir / "parsed_response.json"),
    }


def load_p2b_edges_for_cp(core_point_id: str, p2b_run_prefix: str) -> list[dict[str, Any]]:
    run_dir = PHASE_DIR / "runs" / f"{p2b_run_prefix}{core_point_id}"
    if not run_dir.exists():
        return []
    parsed_path = run_dir / "parsed_response.json"
    if not parsed_path.exists():
        return []
    parsed = read_json(parsed_path)
    edges = parsed.get("core_point_unit_edges") or []
    return [
        {
            "unit_id": edge.get("unit_id"),
            "edge_type": edge.get("edge_type"),
            "reason": edge.get("reason"),
        }
        for edge in edges
    ]


def summarize_core_point(cp: dict[str, Any], p2b_run_prefix: str) -> dict[str, Any]:
    cp_id = str(cp.get("draft_core_point_id"))
    return {
        "core_point_id": cp_id,
        "title_zh": cp.get("title_zh"),
        "title_en": cp.get("title_en"),
        "anchor_unit_ids": cp.get("anchor_unit_ids") or [],
        "support_unit_ids": cp.get("support_unit_ids") or [],
        "evidence_unit_spans": cp.get("evidence_unit_spans") or [],
        "unit_edges_summary": load_p2b_edges_for_cp(cp_id, p2b_run_prefix),
    }


def build_p2c_input(section_id: str, p2a_runs_dir: Path, p2a_run_prefix: str, p2b_run_prefix: str) -> dict[str, Any]:
    p2a_run_dir = find_p2a_run(p2a_runs_dir, p2a_run_prefix, section_id)
    section_input = read_json(p2a_run_dir / "input_section.json")
    core_points, source_info = load_core_points(p2a_run_dir, section_id)
    return {
        "request_id": f"p2c::{section_id}",
        "chapter_id": section_input.get("chapter_id"),
        "section_id": section_id,
        "section_order": section_input.get("section_order"),
        "section_title": section_input.get("section_title"),
        "section_text_with_unit_anchors": section_input.get("section_text_with_unit_anchors"),
        "core_points": [summarize_core_point(cp, p2b_run_prefix) for cp in core_points],
        **source_info,
    }


def build_messages(prompt_text: str, p2c_input: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": prompt_text},
        {
            "role": "user",
            "content": "Build P2C same-section core_point relations. Return one JSON object only.\n\n"
            + canonical_json(p2c_input),
        },
    ]


def validate_output(p2c_input: dict[str, Any], output: dict[str, Any] | None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if output is None:
        return [{"issue": "model_output_malformed"}]
    section_id = str(p2c_input.get("section_id"))
    cp_ids = {str(cp.get("core_point_id")) for cp in p2c_input.get("core_points") or []}
    if str(output.get("section_id")) != section_id:
        issues.append({"issue": "section_id_mismatch", "expected": section_id, "actual": output.get("section_id")})
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
        if source not in cp_ids:
            issues.append({"issue": "unknown_source_core_point_id", "relation_id": rel_id, "source": source})
        if target not in cp_ids:
            issues.append({"issue": "unknown_target_core_point_id", "relation_id": rel_id, "target": target})
        if source == target:
            issues.append({"issue": "self_relation", "relation_id": rel_id})
        if relation_type not in ALLOWED_RELATION_TYPES:
            issues.append({"issue": "invalid_relation_type", "relation_id": rel_id, "relation_type": relation_type})
        key = (source, target, relation_type)
        if key in seen_pairs:
            issues.append({"issue": "duplicate_relation_pair", "relation_id": rel_id, "source": source, "target": target, "relation_type": relation_type})
        seen_pairs.add(key)
    cp_count = len(cp_ids)
    if cp_count and len(relations) > cp_count * 2:
        issues.append({"issue": "too_many_relations_for_section", "relations": len(relations), "core_points": cp_count})
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


def write_validation_report(path: Path, p2c_input: dict[str, Any], output: dict[str, Any] | None, issues: list[dict[str, Any]]) -> None:
    relations = output.get("core_point_relations", []) if output else []
    lines = [
        "# P2C validation report",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- section_id: {p2c_input.get('section_id')}",
        f"- core_points: {len(p2c_input.get('core_points') or [])}",
        f"- output_relations: {len(relations) if isinstance(relations, list) else 0}",
        f"- issues: {len(issues)}",
        "",
    ]
    for issue in issues:
        lines.append(json.dumps(issue, ensure_ascii=False))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    p2c_input = build_p2c_input(args.section_id, args.p2a_runs_dir.resolve(), args.p2a_run_prefix, args.p2b_run_prefix)
    prompt_text = args.prompt_file.resolve().read_text(encoding="utf-8")
    run_dir = (args.run_dir or (PHASE_DIR / "runs" / args.run_slug)).resolve()
    messages = build_messages(prompt_text, p2c_input)
    manifest = {
        "schema_version": "p2c_section_ds_run_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "section_id": args.section_id,
        "model": args.model,
        "base_url": args.base_url or DEFAULT_BASE_URL,
        "temperature": 0.0,
        "max_tokens": args.max_tokens,
        "disable_thinking": args.disable_thinking,
        "prompt_file": str(args.prompt_file.resolve()),
        "prompt_sha256": sha256_text(prompt_text),
        "input_sha256": sha256_text(canonical_json(p2c_input)),
        "message_sha256": sha256_text(canonical_json(messages)),
        "core_point_source": p2c_input.get("core_point_source"),
        "core_point_source_path": p2c_input.get("core_point_source_path"),
    }
    write_json(run_dir / "input_p2c.json", p2c_input)

    if len(p2c_input.get("core_points") or []) < 2:
        parsed = {
            "section_id": args.section_id,
            "core_point_relations": [],
            "review_items": [],
        }
        raw = canonical_json(parsed)
        (run_dir / "raw_response.txt").parent.mkdir(parents=True, exist_ok=True)
        (run_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
        write_json(run_dir / "parsed_response.json", parsed)
        issues = validate_output(p2c_input, parsed)
        manifest["status"] = "passed" if not issues else "validation_failed"
        manifest["skipped_model"] = True
        manifest["skip_reason"] = "fewer_than_two_core_points"
        manifest["usage"] = {}
        write_json(run_dir / "run_manifest.json", manifest)
        write_validation_report(run_dir / "validation_report.md", p2c_input, parsed, issues)
        print(json.dumps({"status": manifest["status"], "run_dir": str(run_dir), "issues": len(issues)}, ensure_ascii=False))
        if issues:
            raise SystemExit(1)
        return

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
    if parsed is not None:
        write_json(run_dir / "parsed_response.json", parsed)
    issues = validate_output(p2c_input, parsed)
    manifest["status"] = "passed" if not issues else "validation_failed"
    write_json(run_dir / "run_manifest.json", manifest)
    write_validation_report(run_dir / "validation_report.md", p2c_input, parsed, issues)
    print(json.dumps({"status": manifest["status"], "run_dir": str(run_dir), "issues": len(issues)}, ensure_ascii=False))
    if issues:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--section-id", required=True)
    parser.add_argument("--p2a-runs-dir", type=Path, default=DEFAULT_P2A_RUNS_DIR)
    parser.add_argument("--p2a-run-prefix", default=DEFAULT_P2A_PREFIX)
    parser.add_argument("--p2b-run-prefix", default=DEFAULT_P2B_RUN_PREFIX)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--run-slug", default="p2c_section_test")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--max-tokens", type=int, default=12000)
    parser.add_argument("--disable-thinking", action="store_true", default=True)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
