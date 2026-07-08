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
P2_DIR = PHASE_DIR.parent / "phase02_core_points"
DEFAULT_RELATIONS = PHASE_DIR / "outputs" / "p3a_reviewed_relations_first5.jsonl"
DEFAULT_PROMPT = TEST_DIR / "p3b_relation_evidence_binding_v1.md"
DEFAULT_P2A_RUN_PREFIX = "p2a_batch_first5_chapters_20260706_"
DEFAULT_P2B_RUN_PREFIX = "p2b_first5_reviewed_20260706_"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
ALLOWED_STRENGTHS = {"strong", "medium", "weak"}


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


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
    unit_texts: dict[str, str] = {}
    if not section_text:
        return unit_texts
    pattern = re.compile(r"\[(v7u_N\d+)\|\d+\]\s*(.*)")
    for line in section_text.splitlines():
        match = pattern.match(line.strip())
        if match:
            unit_texts[match.group(1)] = match.group(2).strip()
    return unit_texts


def section_id_from_cp_id(core_point_id: str) -> str:
    match = re.match(r"cp_(CH\d+)_S(\d+)", core_point_id)
    if not match:
        return ""
    return f"{match.group(1)}-S{match.group(2)}"


def load_unit_texts(section_id: str, p2a_run_prefix: str) -> dict[str, str]:
    run_dir = P2_DIR / "runs" / f"{p2a_run_prefix}{section_id}"
    input_path = run_dir / "input_section.json"
    if not input_path.exists():
        return {}
    section_input = read_json(input_path)
    return parse_unit_texts(section_input.get("section_text_with_unit_anchors"))


def load_p2b_edges(core_point_id: str, p2b_run_prefix: str, p2a_run_prefix: str) -> list[dict[str, Any]]:
    parsed_path = P2_DIR / "runs" / f"{p2b_run_prefix}{core_point_id}" / "parsed_response.json"
    if not parsed_path.exists():
        return []
    section_id = section_id_from_cp_id(core_point_id)
    unit_texts = load_unit_texts(section_id, p2a_run_prefix)
    parsed = read_json(parsed_path)
    return [
        {
            "unit_id": edge.get("unit_id"),
            "edge_type": edge.get("edge_type"),
            "unit_text": unit_texts.get(str(edge.get("unit_id")) or ""),
            "reason": edge.get("reason"),
        }
        for edge in parsed.get("core_point_unit_edges") or []
    ]


def load_cp_title(core_point_id: str, p2a_run_prefix: str) -> str | None:
    section_id = section_id_from_cp_id(core_point_id)
    reviewed_path = P2_DIR / "outputs" / f"p2a_reviewed_core_points.{section_id}.json"
    candidates: list[dict[str, Any]] = []
    if reviewed_path.exists():
        candidates.extend(read_json(reviewed_path).get("core_points") or [])
    raw_path = P2_DIR / "runs" / f"{p2a_run_prefix}{section_id}" / "parsed_response.json"
    if raw_path.exists():
        candidates.extend(read_json(raw_path).get("core_points") or [])
    for cp in candidates:
        if cp.get("draft_core_point_id") == core_point_id:
            return cp.get("title_zh") or cp.get("title_en")
    return None


def build_input(relations_path: Path, p2a_run_prefix: str, p2b_run_prefix: str, relation_ids: set[str] | None, limit: int | None) -> dict[str, Any]:
    relations = read_jsonl(relations_path)
    if relation_ids:
        relations = [rel for rel in relations if rel.get("relation_id") in relation_ids]
    if limit:
        relations = relations[:limit]
    items = []
    for rel in relations:
        source_id = str(rel.get("source_core_point_id"))
        target_id = str(rel.get("target_core_point_id"))
        items.append(
            {
                "p3_relation": rel,
                "source_core_point": {
                    "core_point_id": source_id,
                    "title": load_cp_title(source_id, p2a_run_prefix),
                    "section_id": section_id_from_cp_id(source_id),
                    "p2b_unit_edges": load_p2b_edges(source_id, p2b_run_prefix, p2a_run_prefix),
                },
                "target_core_point": {
                    "core_point_id": target_id,
                    "title": load_cp_title(target_id, p2a_run_prefix),
                    "section_id": section_id_from_cp_id(target_id),
                    "p2b_unit_edges": load_p2b_edges(target_id, p2b_run_prefix, p2a_run_prefix),
                },
            }
        )
    return {
        "binding_batch_id": "p3b_relation_evidence_binding_test",
        "relations_count": len(items),
        "items": items,
    }


def build_messages(prompt_text: str, binding_input: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": prompt_text},
        {
            "role": "user",
            "content": "Bind evidence units to reviewed P3A relations. Return one JSON object only.\n\n"
            + canonical_json(binding_input),
        },
    ]


def validate_output(binding_input: dict[str, Any], output: dict[str, Any] | None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if output is None:
        return [{"issue": "model_output_malformed"}]
    expected = {item["p3_relation"]["relation_id"]: item for item in binding_input.get("items") or []}
    bindings = output.get("relation_evidence_bindings")
    if not isinstance(bindings, list):
        return [{"issue": "relation_evidence_bindings_not_list"}]
    seen: set[str] = set()
    for binding in bindings:
        rel_id = str(binding.get("p3_relation_id") or "")
        if rel_id not in expected:
            issues.append({"issue": "unknown_p3_relation_id", "p3_relation_id": rel_id})
            continue
        if rel_id in seen:
            issues.append({"issue": "duplicate_p3_relation_id", "p3_relation_id": rel_id})
        seen.add(rel_id)
        item = expected[rel_id]
        expected_source = str(item["p3_relation"].get("source_core_point_id"))
        expected_target = str(item["p3_relation"].get("target_core_point_id"))
        if binding.get("source_core_point_id") != expected_source:
            issues.append({"issue": "source_core_point_id_mismatch", "p3_relation_id": rel_id})
        if binding.get("target_core_point_id") != expected_target:
            issues.append({"issue": "target_core_point_id_mismatch", "p3_relation_id": rel_id})
        if binding.get("support_strength") not in ALLOWED_STRENGTHS:
            issues.append({"issue": "invalid_support_strength", "p3_relation_id": rel_id, "support_strength": binding.get("support_strength")})
        source_pool = {edge.get("unit_id") for edge in item["source_core_point"].get("p2b_unit_edges") or []}
        target_pool = {edge.get("unit_id") for edge in item["target_core_point"].get("p2b_unit_edges") or []}
        for unit_id in binding.get("source_evidence_unit_ids") or []:
            if unit_id not in source_pool:
                issues.append({"issue": "source_unit_not_in_pool", "p3_relation_id": rel_id, "unit_id": unit_id})
        for unit_id in binding.get("target_evidence_unit_ids") or []:
            if unit_id not in target_pool:
                issues.append({"issue": "target_unit_not_in_pool", "p3_relation_id": rel_id, "unit_id": unit_id})
    missing = sorted(set(expected) - seen)
    if missing:
        issues.append({"issue": "missing_bindings", "p3_relation_ids": missing})
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


def get_deepseek_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_BASE_URL
            return value, base_url, env_name
    raise RuntimeError("DEEPSEEK_API_KEY / DS_API_KEY / DS_KEY is not set.")


def run(args: argparse.Namespace) -> None:
    relation_ids = set(args.relation_id or []) or None
    prompt_text = args.prompt_file.resolve().read_text(encoding="utf-8")
    binding_input = build_input(args.relations_file.resolve(), args.p2a_run_prefix, args.p2b_run_prefix, relation_ids, args.limit)
    run_dir = (args.run_dir or (TEST_DIR / "runs" / args.run_slug)).resolve()
    messages = build_messages(prompt_text, binding_input)
    write_json(run_dir / "input_p3b_binding.json", binding_input)

    from openai import OpenAI

    api_key, base_url, key_source = get_deepseek_config()
    client = OpenAI(api_key=api_key, base_url=args.base_url or base_url)
    raw, usage = call_model(client, args.model, messages, args.max_tokens, args.disable_thinking)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
    parsed = extract_json_object(raw)
    if parsed is not None:
        write_json(run_dir / "parsed_response.json", parsed)
    issues = validate_output(binding_input, parsed)
    manifest = {
        "schema_version": "p3b_relation_evidence_binding_test_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": args.model,
        "max_tokens": args.max_tokens,
        "disable_thinking": args.disable_thinking,
        "api_key_source": key_source,
        "prompt_sha256": sha256_text(prompt_text),
        "input_sha256": sha256_text(canonical_json(binding_input)),
        "usage": usage,
        "status": "passed" if not issues else "validation_failed",
        "issues": issues,
    }
    write_json(run_dir / "run_manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "run_dir": str(run_dir), "issues": len(issues)}, ensure_ascii=False))
    if issues:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--relations-file", type=Path, default=DEFAULT_RELATIONS)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--p2a-run-prefix", default=DEFAULT_P2A_RUN_PREFIX)
    parser.add_argument("--p2b-run-prefix", default=DEFAULT_P2B_RUN_PREFIX)
    parser.add_argument("--relation-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--run-slug", default="p3b_relation_evidence_binding_test")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--max-tokens", type=int, default=20000)
    parser.add_argument("--disable-thinking", action="store_true", default=True)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
