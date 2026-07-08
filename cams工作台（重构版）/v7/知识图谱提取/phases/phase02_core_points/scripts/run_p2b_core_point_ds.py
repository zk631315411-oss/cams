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
DEFAULT_PROMPT = PHASE_DIR / "prompts" / "p2b_core_point_unit_edges_v1.md"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")

ALLOWED_EDGE_TYPES = {
    "defines",
    "classifies",
    "explains",
    "states_rule",
    "describes_process",
    "indicates_risk",
    "prescribes_measure",
    "illustrates",
    "states_consequence",
    "provides_context",
    "exclude",
}

DEPRECATED_EDGE_FIELDS = {"role", "status", "confidence"}


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
    text = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(text + ("\n" if rows else ""), encoding="utf-8")


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


def expand_spans(units: list[dict[str, Any]], spans: list[list[int]]) -> list[str]:
    by_order = {int(row.get("unit_order")): str(row.get("unit_id")) for row in units}
    ids: list[str] = []
    for span in spans or []:
        if not isinstance(span, list) or len(span) != 2:
            continue
        start, end = int(span[0]), int(span[1])
        for order in range(start, end + 1):
            unit_id = by_order.get(order)
            if unit_id and unit_id not in ids:
                ids.append(unit_id)
    return ids


def find_p2a_run(runs_dir: Path, prefix: str, section_id: str) -> Path:
    run_dir = runs_dir / f"{prefix}{section_id}"
    if not run_dir.exists():
        raise FileNotFoundError(f"P2A run not found: {run_dir}")
    return run_dir


def load_core_points_for_section(p2a_run_dir: Path, section_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    reviewed_path = PHASE_DIR / "outputs" / f"p2a_reviewed_core_points.{section_id}.json"
    if reviewed_path.exists():
        reviewed = read_json(reviewed_path)
        return reviewed.get("core_points") or [], {
            "core_point_source": "p2a_review",
            "core_point_source_path": str(reviewed_path),
            "reviewed_at": reviewed.get("reviewed_at"),
            "retired_core_point_ids": reviewed.get("retired_core_point_ids") or [],
        }
    p2a_output = read_json(p2a_run_dir / "parsed_response.json")
    return p2a_output.get("core_points") or [], {
        "core_point_source": "p2a_raw",
        "core_point_source_path": str(p2a_run_dir / "parsed_response.json"),
        "reviewed_at": None,
        "retired_core_point_ids": [],
    }


def select_core_point(core_points: list[dict[str, Any]], core_point_id: str | None, core_point_index: int | None) -> dict[str, Any]:
    if core_point_id:
        for cp in core_points:
            if str(cp.get("draft_core_point_id")) == core_point_id:
                return cp
        raise ValueError(f"core_point_id not found: {core_point_id}")
    if core_point_index is not None:
        if core_point_index < 0 or core_point_index >= len(core_points):
            raise ValueError(f"core_point_index out of range: {core_point_index}")
        return core_points[core_point_index]
    raise ValueError("Either --core-point-id or --core-point-index is required.")


def build_p2b_input(p2a_run_dir: Path, core_point_id: str | None, core_point_index: int | None) -> dict[str, Any]:
    section_input = read_json(p2a_run_dir / "input_section.json")
    section_id = str(section_input.get("section_id"))
    units = section_input.get("units") or []
    core_points, core_point_source = load_core_points_for_section(p2a_run_dir, section_id)
    target_cp = select_core_point(core_points, core_point_id, core_point_index)

    candidate_ids: list[str] = []
    for unit_id in target_cp.get("anchor_unit_ids") or []:
        if str(unit_id) not in candidate_ids:
            candidate_ids.append(str(unit_id))
    for unit_id in target_cp.get("support_unit_ids") or []:
        if str(unit_id) not in candidate_ids:
            candidate_ids.append(str(unit_id))
    for unit_id in target_cp.get("intervening_support_unit_ids") or []:
        if str(unit_id) not in candidate_ids:
            candidate_ids.append(str(unit_id))
    for unit_id in expand_spans(units, target_cp.get("evidence_unit_spans") or []):
        if unit_id not in candidate_ids:
            candidate_ids.append(unit_id)

    unit_by_id = {str(row.get("unit_id")): row for row in units}
    candidate_units = [unit_by_id[unit_id] for unit_id in candidate_ids if unit_id in unit_by_id]
    sibling_core_points = []
    target_id = str(target_cp.get("draft_core_point_id"))
    for cp in core_points:
        if str(cp.get("draft_core_point_id")) == target_id:
            continue
        sibling_core_points.append(
            {
                "core_point_id": cp.get("draft_core_point_id"),
                "title_zh": cp.get("title_zh"),
                "title_en": cp.get("title_en"),
                "anchor_unit_ids": cp.get("anchor_unit_ids"),
                "evidence_unit_spans": cp.get("evidence_unit_spans"),
            }
        )

    return {
        "request_id": f"p2b::{section_input.get('section_id')}::{target_id}",
        "chapter_id": section_input.get("chapter_id"),
        "section_id": section_input.get("section_id"),
        "section_title": section_input.get("section_title"),
        "section_text_with_unit_anchors": section_input.get("section_text_with_unit_anchors"),
        "all_section_units": units,
        "target_core_point": target_cp,
        "target_core_point_id": target_id,
        **core_point_source,
        "candidate_unit_ids": candidate_ids,
        "candidate_units": candidate_units,
        "sibling_core_points": sibling_core_points,
    }


def build_messages(prompt_text: str, p2b_input: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": prompt_text},
        {
            "role": "user",
            "content": "Build P2B semantic edges for the target core_point. Return one JSON object only.\n\n"
            + canonical_json(p2b_input),
        },
    ]


def validate_output(p2b_input: dict[str, Any], output: dict[str, Any] | None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if output is None:
        return [{"issue": "model_output_malformed"}]
    target_cp_id = str(p2b_input.get("target_core_point_id"))
    section_id = str(p2b_input.get("section_id"))
    candidate_ids = {str(unit_id) for unit_id in p2b_input.get("candidate_unit_ids") or []}
    all_unit_ids = {str(row.get("unit_id")) for row in p2b_input.get("all_section_units") or []}

    if str(output.get("section_id")) != section_id:
        issues.append({"issue": "section_id_mismatch", "expected": section_id, "actual": output.get("section_id")})
    if str(output.get("target_core_point_id")) != target_cp_id:
        issues.append({"issue": "target_core_point_id_mismatch", "expected": target_cp_id, "actual": output.get("target_core_point_id")})

    edges = output.get("core_point_unit_edges", [])
    if not isinstance(edges, list):
        issues.append({"issue": "core_point_unit_edges_not_list"})
        edges = []

    seen_edge_ids: set[str] = set()
    judged_candidate_ids: list[str] = []
    accepted_count = 0
    for edge in edges:
        if not isinstance(edge, dict):
            issues.append({"issue": "edge_not_object"})
            continue
        edge_id = str(edge.get("edge_id") or "")
        cp_id = str(edge.get("core_point_id") or "")
        unit_id = str(edge.get("unit_id") or "")
        edge_type = str(edge.get("edge_type") or "")
        deprecated_fields = sorted(DEPRECATED_EDGE_FIELDS.intersection(edge.keys()))
        if deprecated_fields:
            issues.append({"issue": "deprecated_edge_fields", "edge_id": edge_id, "fields": deprecated_fields})
        if not edge_id:
            issues.append({"issue": "missing_edge_id", "unit_id": unit_id})
        elif edge_id in seen_edge_ids:
            issues.append({"issue": "duplicate_edge_id", "edge_id": edge_id})
        seen_edge_ids.add(edge_id)
        if cp_id != target_cp_id:
            issues.append({"issue": "wrong_core_point_id", "edge_id": edge_id, "core_point_id": cp_id})
        if unit_id not in all_unit_ids:
            issues.append({"issue": "unknown_unit_id", "edge_id": edge_id, "unit_id": unit_id})
        if unit_id in candidate_ids:
            judged_candidate_ids.append(unit_id)
        if edge_type not in ALLOWED_EDGE_TYPES:
            issues.append({"issue": "invalid_edge_type", "edge_id": edge_id, "edge_type": edge_type})
        if edge_type != "exclude":
            accepted_count += 1

    missing_candidates = sorted(candidate_ids - set(judged_candidate_ids))
    if missing_candidates:
        issues.append({"issue": "missing_candidate_unit_judgement", "unit_ids": missing_candidates})
    duplicates = sorted({unit_id for unit_id in judged_candidate_ids if judged_candidate_ids.count(unit_id) > 1})
    if duplicates:
        issues.append({"issue": "duplicate_candidate_unit_judgement", "unit_ids": duplicates})
    if accepted_count == 0 and candidate_ids:
        issues.append({"issue": "no_accepted_edges"})
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


def write_validation_report(path: Path, p2b_input: dict[str, Any], output: dict[str, Any] | None, issues: list[dict[str, Any]]) -> None:
    edges = output.get("core_point_unit_edges", []) if output else []
    lines = [
        "# P2B validation report",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- section_id: {p2b_input.get('section_id')}",
        f"- target_core_point_id: {p2b_input.get('target_core_point_id')}",
        f"- candidate_units: {len(p2b_input.get('candidate_unit_ids') or [])}",
        f"- output_edges: {len(edges) if isinstance(edges, list) else 0}",
        f"- issues: {len(issues)}",
        "",
    ]
    for issue in issues:
        lines.append(json.dumps(issue, ensure_ascii=False))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    p2a_run_dir = find_p2a_run(args.p2a_runs_dir.resolve(), args.p2a_run_prefix, args.section_id)
    p2b_input = build_p2b_input(p2a_run_dir, args.core_point_id, args.core_point_index)
    prompt_text = args.prompt_file.resolve().read_text(encoding="utf-8")
    run_dir = (args.run_dir or (PHASE_DIR / "runs" / args.run_slug)).resolve()
    messages = build_messages(prompt_text, p2b_input)
    manifest = {
        "schema_version": "p2b_core_point_ds_run_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "section_id": args.section_id,
        "target_core_point_id": p2b_input.get("target_core_point_id"),
        "core_point_source": p2b_input.get("core_point_source"),
        "core_point_source_path": p2b_input.get("core_point_source_path"),
        "model": args.model,
        "base_url": args.base_url or DEFAULT_BASE_URL,
        "temperature": 0.0,
        "max_tokens": args.max_tokens,
        "disable_thinking": args.disable_thinking,
        "prompt_file": str(args.prompt_file.resolve()),
        "prompt_sha256": sha256_text(prompt_text),
        "input_sha256": sha256_text(canonical_json(p2b_input)),
        "message_sha256": sha256_text(canonical_json(messages)),
    }

    write_json(run_dir / "input_p2b.json", p2b_input)
    parsed: dict[str, Any] | None = None
    issues: list[dict[str, Any]] = []
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
    issues = validate_output(p2b_input, parsed)
    manifest["status"] = "passed" if not issues else "validation_failed"
    write_json(run_dir / "run_manifest.json", manifest)
    write_validation_report(run_dir / "validation_report.md", p2b_input, parsed, issues)
    if parsed and not args.no_copy_outputs:
        rows = []
        for edge in parsed.get("core_point_unit_edges", []) or []:
            row = dict(edge)
            row["section_id"] = parsed.get("section_id")
            row["run_slug"] = args.run_slug
            rows.append(row)
        write_jsonl(PHASE_DIR / "outputs" / "p2b_core_point_unit_edges.jsonl", rows)

    print(json.dumps({"status": manifest["status"], "run_dir": str(run_dir), "issues": len(issues)}, ensure_ascii=False))
    if issues:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--section-id", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--core-point-id")
    group.add_argument("--core-point-index", type=int)
    parser.add_argument("--p2a-runs-dir", type=Path, default=DEFAULT_P2A_RUNS_DIR)
    parser.add_argument("--p2a-run-prefix", default=DEFAULT_P2A_PREFIX)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--run-slug", default="p2b_core_point_test")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--disable-thinking", action="store_true", default=True)
    parser.add_argument("--no-copy-outputs", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
