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
PHASE_DIR = SCRIPT_DIR.parents[1]
DEFAULT_PROMPT = SCRIPT_DIR / "p2b_role_edges_prompt.md"
DEFAULT_RUNS_DIR = PHASE_DIR / "runs"
DEFAULT_P2A_PREFIX = "p2a_batch_first5_chapters_20260706_"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")

ALLOWED_ROLES = {"anchor", "support", "example", "risk", "measure", "context", "exclude"}
ALLOWED_STATUSES = {"accepted", "excluded", "needs_review"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}

VARIANTS = {
    "flash_thinking": {
        "model": "deepseek-v4-flash",
        "reasoning_effort": "high",
        "extra_body": {"thinking": {"type": "enabled"}, "reasoning_effort": "high"},
    },
    "pro_no_thinking": {
        "model": "deepseek-v4-pro",
        "reasoning_effort": "off",
        "extra_body": {"thinking": {"type": "disabled"}},
    },
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


def build_p2b_input(p2a_run_dir: Path) -> dict[str, Any]:
    section_input = read_json(p2a_run_dir / "input_section.json")
    p2a_output = read_json(p2a_run_dir / "parsed_response.json")
    return {
        "request_id": f"p2b::{section_input.get('section_id')}",
        "chapter_id": section_input.get("chapter_id"),
        "section_id": section_input.get("section_id"),
        "section_title": section_input.get("section_title"),
        "section_text_with_unit_anchors": section_input.get("section_text_with_unit_anchors"),
        "units": section_input.get("units") or [],
        "p2a_core_points": p2a_output.get("core_points") or [],
    }


def build_messages(prompt_text: str, p2b_input: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": prompt_text},
        {
            "role": "user",
            "content": "Build P2B core_point to unit role edges. Return one JSON object only.\n\n"
            + canonical_json(p2b_input),
        },
    ]


def validate_output(p2b_input: dict[str, Any], output: dict[str, Any] | None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if output is None:
        return [{"issue": "model_output_malformed"}]

    unit_ids = {str(row.get("unit_id")) for row in p2b_input.get("units", [])}
    cp_ids = {str(row.get("draft_core_point_id")) for row in p2b_input.get("p2a_core_points", [])}
    edges = output.get("core_point_unit_edges", [])
    if not isinstance(edges, list):
        issues.append({"issue": "core_point_unit_edges_not_list"})
        edges = []

    accepted_by_cp: dict[str, int] = {cp_id: 0 for cp_id in cp_ids}
    seen_edge_ids: set[str] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            issues.append({"issue": "edge_not_object"})
            continue
        edge_id = str(edge.get("edge_id") or "")
        cp_id = str(edge.get("core_point_id") or "")
        unit_id = str(edge.get("unit_id") or "")
        role = str(edge.get("role") or "")
        status = str(edge.get("status") or "")
        confidence = str(edge.get("confidence") or "")
        if not edge_id:
            issues.append({"issue": "missing_edge_id", "core_point_id": cp_id, "unit_id": unit_id})
        elif edge_id in seen_edge_ids:
            issues.append({"issue": "duplicate_edge_id", "edge_id": edge_id})
        seen_edge_ids.add(edge_id)
        if cp_id not in cp_ids:
            issues.append({"issue": "unknown_core_point_id", "edge_id": edge_id, "core_point_id": cp_id})
        if unit_id not in unit_ids:
            issues.append({"issue": "unknown_unit_id", "edge_id": edge_id, "unit_id": unit_id})
        if role not in ALLOWED_ROLES:
            issues.append({"issue": "invalid_role", "edge_id": edge_id, "role": role})
        if status not in ALLOWED_STATUSES:
            issues.append({"issue": "invalid_status", "edge_id": edge_id, "status": status})
        if confidence not in ALLOWED_CONFIDENCE:
            issues.append({"issue": "invalid_confidence", "edge_id": edge_id, "confidence": confidence})
        if role == "exclude" and status != "excluded":
            issues.append({"issue": "exclude_role_without_excluded_status", "edge_id": edge_id})
        if role != "exclude" and status == "accepted" and cp_id in accepted_by_cp:
            accepted_by_cp[cp_id] += 1

    for cp_id, count in accepted_by_cp.items():
        if count == 0:
            issues.append({"issue": "core_point_without_accepted_edges", "core_point_id": cp_id})

    return issues


def call_model(client: Any, variant: dict[str, Any], messages: list[dict[str, str]], max_tokens: int) -> tuple[str, dict[str, Any]]:
    kwargs: dict[str, Any] = {
        "model": variant["model"],
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    if variant.get("extra_body"):
        kwargs["extra_body"] = variant["extra_body"]
    resp = client.chat.completions.create(**kwargs)
    raw = (resp.choices[0].message.content or "").strip()
    usage = getattr(resp, "usage", None)
    return raw, usage.model_dump() if hasattr(usage, "model_dump") else {}


def write_validation_report(path: Path, p2b_input: dict[str, Any], output: dict[str, Any] | None, issues: list[dict[str, Any]]) -> None:
    edges = output.get("core_point_unit_edges", []) if output else []
    lines = [
        "# P2B AB validation report",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- section_id: {p2b_input.get('section_id')}",
        f"- core_points: {len(p2b_input.get('p2a_core_points', []))}",
        f"- units: {len(p2b_input.get('units', []))}",
        f"- output_edges: {len(edges) if isinstance(edges, list) else 0}",
        f"- issues: {len(issues)}",
        "",
    ]
    for issue in issues:
        lines.append(json.dumps(issue, ensure_ascii=False))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize_variant(parsed: dict[str, Any] | None, issues: list[dict[str, Any]]) -> dict[str, Any]:
    edges = parsed.get("core_point_unit_edges", []) if parsed else []
    role_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    for edge in edges if isinstance(edges, list) else []:
        if not isinstance(edge, dict):
            continue
        role_counts[str(edge.get("role"))] = role_counts.get(str(edge.get("role")), 0) + 1
        status_counts[str(edge.get("status"))] = status_counts.get(str(edge.get("status")), 0) + 1
    return {
        "edges": len(edges) if isinstance(edges, list) else 0,
        "issues": len(issues),
        "role_counts": role_counts,
        "status_counts": status_counts,
        "review_items": len(parsed.get("review_items", [])) if parsed else 0,
    }


def run_variant(client: Any, variant_name: str, variant: dict[str, Any], prompt_text: str, p2b_input: dict[str, Any], out_dir: Path, max_tokens: int) -> dict[str, Any]:
    messages = build_messages(prompt_text, p2b_input)
    manifest = {
        "schema_version": "p2b_ab_run_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "variant": variant_name,
        "model": variant["model"],
        "reasoning_effort": variant.get("reasoning_effort"),
        "extra_body": variant.get("extra_body"),
        "max_tokens": max_tokens,
        "prompt_sha256": sha256_text(prompt_text),
        "input_sha256": sha256_text(canonical_json(p2b_input)),
        "message_sha256": sha256_text(canonical_json(messages)),
    }
    write_json(out_dir / "input_p2b.json", p2b_input)
    raw, usage = call_model(client, variant, messages, max_tokens)
    (out_dir / "raw_response.txt").parent.mkdir(parents=True, exist_ok=True)
    (out_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
    parsed = extract_json_object(raw)
    if parsed is not None:
        write_json(out_dir / "parsed_response.json", parsed)
    issues = validate_output(p2b_input, parsed)
    manifest["usage"] = usage
    manifest["status"] = "passed" if not issues else "validation_failed"
    write_json(out_dir / "run_manifest.json", manifest)
    write_validation_report(out_dir / "validation_report.md", p2b_input, parsed, issues)
    summary = summarize_variant(parsed, issues)
    summary.update({"status": manifest["status"], "run_dir": str(out_dir)})
    return summary


def write_comparison(path: Path, run_slug: str, summaries: list[dict[str, Any]]) -> None:
    lines = [
        "# P2B AB comparison",
        "",
        f"- run_slug: {run_slug}",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "| section | variant | status | edges | issues | review_items | roles | statuses |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in summaries:
        roles = ", ".join(f"{k}:{v}" for k, v in sorted(row.get("role_counts", {}).items()))
        statuses = ", ".join(f"{k}:{v}" for k, v in sorted(row.get("status_counts", {}).items()))
        lines.append(
            f"| {row['section_id']} | {row['variant']} | {row['status']} | {row['edges']} | {row['issues']} | {row['review_items']} | {roles} | {statuses} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--section-id", action="append", default=[])
    parser.add_argument("--p2a-runs-dir", type=Path, default=DEFAULT_RUNS_DIR)
    parser.add_argument("--p2a-run-prefix", default=DEFAULT_P2A_PREFIX)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--run-slug", default="p2b_ab_20260706")
    parser.add_argument("--out-dir", type=Path, default=SCRIPT_DIR / "runs")
    parser.add_argument("--max-tokens", type=int, default=24000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    section_ids = args.section_id or ["CH02-S06", "CH05-S04"]
    prompt_text = args.prompt_file.resolve().read_text(encoding="utf-8")
    api_key, base_url, _key_source = get_deepseek_config()

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    summaries: list[dict[str, Any]] = []
    for section_id in section_ids:
        p2a_run = find_p2a_run(args.p2a_runs_dir.resolve(), args.p2a_run_prefix, section_id)
        p2b_input = build_p2b_input(p2a_run)
        for variant_name, variant in VARIANTS.items():
            out_dir = args.out_dir.resolve() / args.run_slug / section_id / variant_name
            summary = run_variant(client, variant_name, variant, prompt_text, p2b_input, out_dir, args.max_tokens)
            summary.update({"section_id": section_id, "variant": variant_name})
            summaries.append(summary)

    comparison_path = args.out_dir.resolve() / args.run_slug / "comparison_summary.md"
    write_comparison(comparison_path, args.run_slug, summaries)
    print(json.dumps({"status": "completed", "comparison": str(comparison_path), "runs": summaries}, ensure_ascii=False))


if __name__ == "__main__":
    main()

