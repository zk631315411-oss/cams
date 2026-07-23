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


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
P2_DIR = PHASE_DIR.parent / "phase02_core_points"
DEFAULT_REVIEW_FILE = PHASE_DIR / "outputs" / "p4_formal_all_chapters_top300_batch5x20_v1_p4b_review.jsonl"
DEFAULT_PROMPT = PHASE_DIR / "prompts" / "p4c_relation_evidence_binding_v1.md"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-v4-pro"
API_KEY_ENV_NAMES = (
    "P4_API_KEY",
    "DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY",
)
BASE_URL_ENV_NAMES = ("P4_BASE_URL", "DEEPSEEK_BASE_URL", "DS_BASE_URL")
MODEL_ENV_NAMES = ("P4_MODEL",)
ALLOWED_STRENGTHS = {"strong", "medium", "weak"}
FINAL_DECISIONS = {"accept", "accept_with_direction_fix"}


def load_unit_lookup(path: Path) -> dict[str, dict[str, str]]:
    """从 KG JSON 加载 unit 的 knowledge_zh + en_quote/knowledge_en."""
    data = read_json(path)
    lookup: dict[str, dict[str, str]] = {}
    for u in data.get("units", []) or []:
        uid = u.get("unit_id", "")
        if not uid:
            continue
        en = u.get("en_quote", "") or u.get("knowledge_en", "")
        lookup[uid] = {"zh": u.get("knowledge_zh", ""), "en": en}
    return lookup


def _cp_unit_ids(cp: dict[str, Any]) -> list[str]:
    """收集 CP 所有关联 unit_id（去重）。"""
    seen: set[str] = set()
    uids: list[str] = []
    for key in ("anchor_unit_ids", "support_unit_ids", "key_unit_ids"):
        for uid in cp.get(key, []) or []:
            if uid and uid not in seen:
                seen.add(uid)
                uids.append(uid)
    return uids


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(text + ("\n" if rows else ""), encoding="utf-8")


def get_api_config() -> tuple[str, str, str, str]:
    """Return (api_key, base_url, model, key_source). Reads from env vars."""
    api_key = ""
    key_source = ""
    for env_name in API_KEY_ENV_NAMES:
        api_key = os.environ.get(env_name, "")
        if api_key:
            key_source = env_name
            break
    if not api_key:
        raise RuntimeError("No API key found in env: " + ", ".join(API_KEY_ENV_NAMES))
    base_url = DEFAULT_BASE_URL
    for env_name in BASE_URL_ENV_NAMES:
        url = os.environ.get(env_name, "")
        if url:
            base_url = url
            break
    model = DEFAULT_MODEL
    for env_name in MODEL_ENV_NAMES:
        m = os.environ.get(env_name, "")
        if m:
            model = m
            break
    return api_key, base_url, model, key_source


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


def unit_sort_key(edge: dict[str, Any]) -> int:
    match = re.search(r"(\d+)$", str(edge.get("unit_id") or ""))
    return int(match.group(1)) if match else 10**9


def section_id_from_cp_id(core_point_id: str) -> str:
    match = re.match(r"cp_(CH\d+)_S(\d+)", core_point_id)
    if not match:
        return ""
    return f"{match.group(1)}-S{match.group(2)}"


def load_reviewed_relations(review_file: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    final_relations: list[dict[str, Any]] = []
    p5_candidates: list[dict[str, Any]] = []
    for row in read_jsonl(review_file):
        decision = str(row.get("review_decision") or "")
        if decision == "move_to_p5":
            p5_candidates.append(row)
            continue
        if decision not in FINAL_DECISIONS:
            continue
        model_decision = row.get("model_decision") or {}
        source_id = row.get("review_source_core_point_id") or model_decision.get("source_core_point_id")
        target_id = row.get("review_target_core_point_id") or model_decision.get("target_core_point_id")
        relation_type = row.get("review_relation_type") or model_decision.get("relation_type")
        relation_id = str(row.get("candidate_id") or model_decision.get("candidate_id") or "")
        final_relations.append(
            {
                "relation_id": relation_id,
                "candidate_id": row.get("candidate_id"),
                "global_rank": row.get("global_rank"),
                "similarity": row.get("similarity"),
                "source_core_point_id": source_id,
                "target_core_point_id": target_id,
                "relation_type": relation_type,
                "review_decision": decision,
                "p4b_reason": model_decision.get("reason"),
                "review_reason": row.get("review_reason"),
                "source_title_en": row.get("review_source_title_en"),
                "target_title_en": row.get("review_target_title_en"),
            }
        )
    return final_relations, p5_candidates


def resolve_p2a_run_dir(section_id: str) -> Path | None:
    reviewed_path = P2_DIR / "outputs" / f"p2a_reviewed_core_points.{section_id}.json"
    if reviewed_path.exists():
        reviewed = read_json(reviewed_path)
        source_p2a_run = reviewed.get("source_p2a_run")
        if source_p2a_run:
            parsed_path = (P2_DIR / str(source_p2a_run)).resolve()
            input_dir = parsed_path.parent
            if (input_dir / "input_section.json").exists():
                return input_dir
    matches = sorted(
        [path for path in (P2_DIR / "runs").glob(f"p2a*{section_id}") if (path / "input_section.json").exists()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def resolve_p2b_run_dir(core_point_id: str) -> Path | None:
    matches = sorted(
        [path for path in (P2_DIR / "runs").glob(f"*{core_point_id}") if (path / "parsed_response.json").exists()],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


def load_section_context(section_id: str) -> tuple[dict[str, str], str | None]:
    run_dir = resolve_p2a_run_dir(section_id)
    if run_dir is None:
        return {}, None
    input_path = run_dir / "input_section.json"
    if not input_path.exists():
        return {}, None
    section_input = read_json(input_path)
    return parse_unit_texts(section_input.get("section_text_with_unit_anchors")), section_input.get("section_title")


def load_cp_title(core_point_id: str) -> str | None:
    section_id = section_id_from_cp_id(core_point_id)
    reviewed_path = P2_DIR / "outputs" / f"p2a_reviewed_core_points.{section_id}.json"
    if not reviewed_path.exists():
        return None
    for cp in read_json(reviewed_path).get("core_points") or []:
        if cp.get("draft_core_point_id") == core_point_id or cp.get("core_point_id") == core_point_id:
            return cp.get("title_en") or cp.get("title_zh")
    return None


def load_p2b_edges(core_point_id: str) -> list[dict[str, Any]]:
    section_id = section_id_from_cp_id(core_point_id)
    unit_texts, _section_title = load_section_context(section_id)
    run_dir = resolve_p2b_run_dir(core_point_id)
    if run_dir is None:
        return []
    parsed = read_json(run_dir / "parsed_response.json")
    edges: list[dict[str, Any]] = []
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
    return sorted(edges, key=unit_sort_key)


def _cp_data_for_binding(cp_id: str, unit_lookup: dict[str, dict[str, str]] | None) -> tuple[list[str], list[dict[str, str]]]:
    """获取 CP 的 unit_id 列表和全部 unit 中英文内容。"""
    section_id = section_id_from_cp_id(cp_id)
    reviewed_path = P2_DIR / "outputs" / f"p2a_reviewed_core_points.{section_id}.json"
    if not reviewed_path.exists():
        return [], []
    for cp in read_json(reviewed_path).get("core_points") or []:
        if (cp.get("draft_core_point_id") or cp.get("core_point_id")) == cp_id:
            all_uids = _cp_unit_ids(cp)
            units: list[dict[str, str]] = []
            if unit_lookup:
                for uid in all_uids:
                    u = unit_lookup.get(uid, {})
                    zh = u.get("zh", "")
                    en = u.get("en", "")
                    if zh or en:
                        units.append({"zh": zh, "en": en})
            return all_uids, units
    return [], []


def build_binding_input(relation: dict[str, Any],
                        unit_lookup: dict[str, dict[str, str]] | None = None) -> dict[str, Any]:
    source_id = str(relation.get("source_core_point_id") or "")
    target_id = str(relation.get("target_core_point_id") or "")
    source_section = section_id_from_cp_id(source_id)
    target_section = section_id_from_cp_id(target_id)
    _source_unit_texts, source_section_title = load_section_context(source_section)
    _target_unit_texts, target_section_title = load_section_context(target_section)
    return {
        "binding_batch_id": "p4c_relation_evidence_binding",
        "relations_count": 1,
        "items": [
            {
                "p4_relation": relation,
                "source_core_point": {
                    "core_point_id": source_id,
                    "title": relation.get("source_title_en") or load_cp_title(source_id),
                    "section_id": source_section,
                    "section_title": source_section_title,
                    "unit_ids": (src_uids := _cp_data_for_binding(source_id, unit_lookup))[0],
                    "units": src_uids[1],
                },
                "target_core_point": {
                    "core_point_id": target_id,
                    "title": relation.get("target_title_en") or load_cp_title(target_id),
                    "section_id": target_section,
                    "section_title": target_section_title,
                    "unit_ids": (tgt_uids := _cp_data_for_binding(target_id, unit_lookup))[0],
                    "units": tgt_uids[1],
                },
            }
        ],
    }


def build_messages(prompt_text: str, binding_input: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": prompt_text},
        {
            "role": "user",
            "content": "Bind evidence units to reviewed P4 relations. Return one JSON object only.\n\n"
            + canonical_json(binding_input),
        },
    ]


def validate_output(binding_input: dict[str, Any], output: dict[str, Any] | None) -> list[dict[str, Any]]:
    if output is None:
        return [{"issue": "model_output_malformed"}]
    bindings = output.get("relation_evidence_bindings")
    if not isinstance(bindings, list):
        return [{"issue": "relation_evidence_bindings_not_list"}]
    expected_items = binding_input.get("items") or []
    expected = {item["p4_relation"]["relation_id"]: item for item in expected_items}
    seen: set[str] = set()
    issues: list[dict[str, Any]] = []
    for binding in bindings:
        rel_id = str(binding.get("p4_relation_id") or "")
        if rel_id not in expected:
            issues.append({"issue": "unknown_p4_relation_id", "p4_relation_id": rel_id})
            continue
        if rel_id in seen:
            issues.append({"issue": "duplicate_p4_relation_id", "p4_relation_id": rel_id})
        seen.add(rel_id)
        item = expected[rel_id]
        relation = item["p4_relation"]
        if binding.get("source_core_point_id") != relation.get("source_core_point_id"):
            issues.append({"issue": "source_core_point_id_mismatch", "p4_relation_id": rel_id})
        if binding.get("target_core_point_id") != relation.get("target_core_point_id"):
            issues.append({"issue": "target_core_point_id_mismatch", "p4_relation_id": rel_id})
        if binding.get("relation_type") != relation.get("relation_type"):
            issues.append({"issue": "relation_type_mismatch", "p4_relation_id": rel_id})
        if binding.get("support_strength") not in ALLOWED_STRENGTHS:
            issues.append({"issue": "invalid_support_strength", "p4_relation_id": rel_id, "support_strength": binding.get("support_strength")})
        source_pool = set(item["source_core_point"].get("unit_ids") or [])
        target_pool = set(item["target_core_point"].get("unit_ids") or [])
        for unit_id in binding.get("source_evidence_unit_ids") or []:
            if unit_id not in source_pool:
                issues.append({"issue": "source_unit_not_in_pool", "p4_relation_id": rel_id, "unit_id": unit_id})
        for unit_id in binding.get("target_evidence_unit_ids") or []:
            if unit_id not in target_pool:
                issues.append({"issue": "target_unit_not_in_pool", "p4_relation_id": rel_id, "unit_id": unit_id})
        if len(binding.get("source_evidence_unit_ids") or []) > 5:
            issues.append({"issue": "too_many_source_units", "p4_relation_id": rel_id})
        if len(binding.get("target_evidence_unit_ids") or []) > 5:
            issues.append({"issue": "too_many_target_units", "p4_relation_id": rel_id})
    missing = sorted(set(expected) - seen)
    if missing:
        issues.append({"issue": "missing_bindings", "p4_relation_ids": missing})
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


def run_one(args: argparse.Namespace, client: Any, prompt_text: str, relation: dict[str, Any],
            unit_lookup: dict[str, dict[str, str]] | None = None) -> dict[str, Any]:
    relation_id = str(relation.get("relation_id") or "")
    run_dir = PHASE_DIR / "runs" / args.run_slug / "relations" / relation_id
    binding_input = build_binding_input(relation, unit_lookup)
    messages = build_messages(prompt_text, binding_input)
    write_json(run_dir / "input_p4c_binding.json", binding_input)
    raw, usage = call_model(client, args.model, messages, args.max_tokens, args.disable_thinking)
    (run_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
    parsed = extract_json_object(raw)
    if parsed is not None:
        write_json(run_dir / "parsed_response.json", parsed)
    issues = validate_output(binding_input, parsed)
    manifest = {
        "schema_version": "p4c_relation_evidence_binding_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "relation_id": relation_id,
        "model": args.model,
        "max_tokens": args.max_tokens,
        "disable_thinking": args.disable_thinking,
        "prompt_sha256": sha256_text(prompt_text),
        "input_sha256": sha256_text(canonical_json(binding_input)),
        "usage": usage,
        "status": "passed" if not issues else "validation_failed",
        "issues": issues,
    }
    write_json(run_dir / "run_manifest.json", manifest)
    bindings = (parsed or {}).get("relation_evidence_bindings") or []
    strength = bindings[0].get("support_strength") if bindings else None
    return {
        "relation_id": relation_id,
        "run_dir": str(run_dir),
        "status": manifest["status"],
        "issues": issues,
        "binding_count": len(bindings),
        "support_strength": strength,
    }


def collect_bindings(run_slug: str, relations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = {str(rel.get("relation_id")): index for index, rel in enumerate(relations)}
    bindings: list[dict[str, Any]] = []
    for relation in relations:
        relation_id = str(relation.get("relation_id") or "")
        parsed_path = PHASE_DIR / "runs" / run_slug / "relations" / relation_id / "parsed_response.json"
        if not parsed_path.exists():
            continue
        parsed = read_json(parsed_path)
        for binding in parsed.get("relation_evidence_bindings") or []:
            if isinstance(binding, dict):
                binding["p4_relation"] = relation
                bindings.append(binding)
    bindings.sort(key=lambda row: order.get(str(row.get("p4_relation_id")), 10**9))
    return bindings


def unit_count(binding: dict[str, Any], key: str) -> int:
    value = binding.get(key)
    return len(value) if isinstance(value, list) else 0


def write_report(path: Path, summary: dict[str, Any], bindings: list[dict[str, Any]]) -> None:
    by_type: dict[str, int] = {}
    by_strength: dict[str, int] = {}
    flags: list[str] = []
    for binding in bindings:
        rel_type = str(binding.get("relation_type") or "")
        strength = str(binding.get("support_strength") or "")
        by_type[rel_type] = by_type.get(rel_type, 0) + 1
        by_strength[strength] = by_strength.get(strength, 0) + 1
        source_count = unit_count(binding, "source_evidence_unit_ids")
        target_count = unit_count(binding, "target_evidence_unit_ids")
        if source_count == 0 or target_count == 0 or source_count > 5 or target_count > 5 or strength == "weak":
            flags.append(f"- {binding.get('p4_relation_id')}: strength={strength}, source_units={source_count}, target_units={target_count}")
    lines = [
        "# P4C relation unit evidence report",
        "",
        f"- generated_at: {summary['generated_at']}",
        f"- run_slug: {summary['run_slug']}",
        f"- model: {summary['model']}",
        f"- concurrency: {summary['concurrency']}",
        f"- selected_count: {summary['selected_count']}",
        f"- passed_count: {summary['passed_count']}",
        f"- failed_count: {summary['failed_count']}",
        "",
        "## Relation types",
        "",
    ]
    lines.extend(f"- {key}: {by_type[key]}" for key in sorted(by_type))
    lines.extend(["", "## Support strength", ""])
    lines.extend(f"- {key}: {by_strength[key]}" for key in sorted(by_strength))
    lines.extend(["", "## Review flags", ""])
    lines.extend(flags or ["- none"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_preview(path: Path, bindings: list[dict[str, Any]], limit: int = 20) -> None:
    lines = ["# P4C relation unit evidence preview", ""]
    for binding in bindings[:limit]:
        relation = binding.get("p4_relation") or {}
        lines.extend(
            [
                f"## {binding.get('p4_relation_id')} ({binding.get('relation_type')})",
                "",
                f"- source: {binding.get('source_core_point_id')} | {relation.get('source_title_en')}",
                f"- target: {binding.get('target_core_point_id')} | {relation.get('target_title_en')}",
                f"- source_evidence_unit_ids: {', '.join(binding.get('source_evidence_unit_ids') or [])}",
                f"- target_evidence_unit_ids: {', '.join(binding.get('target_evidence_unit_ids') or [])}",
                f"- support_strength: {binding.get('support_strength')}",
                f"- evidence_summary: {binding.get('evidence_summary')}",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-file", type=Path, default=DEFAULT_REVIEW_FILE)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--run-slug", default="p4c_relation_evidence_binding_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    parser.add_argument("--relation-id", action="append", default=[])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--model", default=None, help="model name (default from env or deepseek-v4-pro)")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--max-tokens", type=int, default=8000)
    parser.add_argument("--disable-thinking", action="store_true", default=True)
    parser.add_argument("--unit-lookup", type=Path, default=None, help="KG JSON for unit zh/en content")
    parser.add_argument("--materialize-only", action="store_true")
    parser.add_argument("--output-jsonl", type=Path, default=None)
    parser.add_argument("--report-md", type=Path, default=None)
    parser.add_argument("--preview-md", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    all_final_relations, p5_candidates = load_reviewed_relations(args.review_file.resolve())

    reviewed_output = PHASE_DIR / "outputs" / "p4_reviewed_cross_chapter_relations.jsonl"
    p5_output = PHASE_DIR / "outputs" / "p4_move_to_p5_candidates.jsonl"
    write_jsonl(reviewed_output, all_final_relations)
    write_jsonl(p5_output, p5_candidates)

    final_relations = list(all_final_relations)
    if args.relation_id:
        selected_ids = set(args.relation_id)
        final_relations = [rel for rel in final_relations if rel.get("relation_id") in selected_ids]
    if args.limit:
        final_relations = final_relations[: args.limit]
    if not final_relations:
        raise SystemExit("No reviewed P4 relations selected.")

    if args.materialize_only:
        print(json.dumps({"reviewed_output": str(reviewed_output), "p5_output": str(p5_output), "selected_count": len(final_relations)}, ensure_ascii=False))
        return

    prompt_text = args.prompt_file.resolve().read_text(encoding="utf-8")
    unit_lookup = load_unit_lookup(args.unit_lookup) if args.unit_lookup else None
    from openai import OpenAI

    api_key, base_url, model, key_source = get_api_config()
    args.model = args.model or model  # ensure model set for downstream use
    client = OpenAI(api_key=api_key, base_url=args.base_url or base_url)
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        future_map = {executor.submit(run_one, args, client, prompt_text, relation, unit_lookup): relation for relation in final_relations}
        for future in as_completed(future_map):
            result = future.result()
            results.append(result)
            print(json.dumps({"status": result["status"], "relation_id": result["relation_id"], "support_strength": result["support_strength"]}, ensure_ascii=False))

    order = {str(rel.get("relation_id")): index for index, rel in enumerate(final_relations)}
    results.sort(key=lambda row: order.get(str(row.get("relation_id")), 10**9))
    summary = {
        "schema_version": "p4c_relation_evidence_binding_summary_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_slug": args.run_slug,
        "review_file": str(args.review_file.resolve()),
        "reviewed_relations_file": str(reviewed_output),
        "move_to_p5_file": str(p5_output),
        "model": args.model,
        "max_tokens": args.max_tokens,
        "disable_thinking": args.disable_thinking,
        "api_key_source": key_source,
        "concurrency": args.concurrency,
        "selected_count": len(final_relations),
        "passed_count": sum(1 for row in results if row["status"] == "passed"),
        "failed_count": sum(1 for row in results if row["status"] != "passed"),
        "results": results,
    }
    summary_path = PHASE_DIR / "runs" / f"{args.run_slug}_summary.json"
    write_json(summary_path, summary)

    bindings = collect_bindings(args.run_slug, final_relations)
    output_jsonl = args.output_jsonl or (PHASE_DIR / "outputs" / f"{args.run_slug}.jsonl")
    report_md = args.report_md or (PHASE_DIR / "reports" / f"{args.run_slug}_report.md")
    preview_md = args.preview_md or (PHASE_DIR / "previews" / f"{args.run_slug}_preview.md")
    write_jsonl(output_jsonl, bindings)
    write_report(report_md, summary, bindings)
    write_preview(preview_md, bindings)
    print(
        json.dumps(
            {
                "summary_path": str(summary_path),
                "output_jsonl": str(output_jsonl),
                "report_md": str(report_md),
                "preview_md": str(preview_md),
                "passed": summary["passed_count"],
                "failed": summary["failed_count"],
            },
            ensure_ascii=False,
        )
    )
    if summary["failed_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
