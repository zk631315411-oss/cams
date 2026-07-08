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
KG_DIR = PHASE_DIR.parent.parent
DEFAULT_UNITS = KG_DIR / "phases" / "phase01_chapter_index" / "outputs" / "first_five_chapters_units.jsonl"
DEFAULT_PROMPT = PHASE_DIR / "prompts" / "p2a_section_core_points_v1.md"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")

CANDIDATE_FUNCTION_TYPES = [
    {"function_type": "definition", "description_zh": "定义、概念边界、术语解释"},
    {"function_type": "classification", "description_zh": "类型、类别、形式、构成项"},
    {"function_type": "rule", "description_zh": "规则、要求、控制措施、应做事项"},
    {"function_type": "process", "description_zh": "流程、阶段、步骤"},
    {"function_type": "risk_indicator", "description_zh": "风险、红旗、警示信号、风险暴露"},
    {"function_type": "case", "description_zh": "案例、示例、情景说明"},
    {"function_type": "context", "description_zh": "背景、承接、列表引导、非核心上下文"},
    {"function_type": "fact", "description_zh": "一般事实陈述，无法归入以上类型"},
    {"function_type": "needs_review", "description_zh": "证据或类型不确定，需要人工复核"},
]
FORBIDDEN_UNIT_FIELDS = {"type", "unit_type", "old_type"}


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


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


def build_section_input(units_file: Path, section_id: str) -> dict[str, Any]:
    all_units = read_jsonl(units_file)
    units = [row for row in all_units if str(row.get("section_id")) == section_id]
    units.sort(key=lambda row: int(row.get("unit_order") or 0))
    if not units:
        raise ValueError(f"No units found for section_id={section_id}")

    section_text_parts = []
    clean_units = []
    for row in units:
        unit_id = str(row.get("unit_id"))
        unit_order = int(row.get("unit_order"))
        quote = str(row.get("en_quote") or "").strip()
        section_text_parts.append(f"[{unit_id}|{unit_order}] {quote}")
        clean_units.append(
            {
                "chapter_id": row.get("chapter_id"),
                "section_id": row.get("section_id"),
                "section_title": row.get("section_title"),
                "unit_order": unit_order,
                "unit_id": unit_id,
                "knowledge_zh": row.get("knowledge_zh"),
                "en_quote": row.get("en_quote"),
                "printed_page": row.get("printed_page"),
                "pdf_page": row.get("pdf_page"),
            }
        )

    return {
        "request_id": f"p2a::{section_id}",
        "chapter_id": units[0].get("chapter_id"),
        "section_id": section_id,
        "section_order": units[0].get("section_order"),
        "section_title": units[0].get("section_title"),
        "candidate_function_types": CANDIDATE_FUNCTION_TYPES,
        "section_text_with_unit_anchors": "\n".join(section_text_parts),
        "units": clean_units,
    }


def build_messages(prompt_text: str, section_input: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": prompt_text},
        {
            "role": "user",
            "content": "Analyze this section for P2A. Return one JSON object only.\n\n" + canonical_json(section_input),
        },
    ]


def validate_output(section_input: dict[str, Any], output: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    input_ids = {str(row.get("unit_id")) for row in section_input.get("units", [])}
    input_orders = {int(row.get("unit_order")) for row in section_input.get("units", [])}
    allowed_types = {row["function_type"] for row in section_input.get("candidate_function_types", [])}

    for unit in section_input.get("units", []):
        bad = sorted(FORBIDDEN_UNIT_FIELDS & set(unit))
        if bad:
            issues.append({"issue": "forbidden_input_unit_fields", "unit_id": unit.get("unit_id"), "fields": bad})

    labels = output.get("unit_function_labels", [])
    if not isinstance(labels, list):
        issues.append({"issue": "unit_function_labels_not_list"})
        labels = []
    label_ids = [str(row.get("unit_id")) for row in labels if isinstance(row, dict)]
    missing_labels = sorted(input_ids - set(label_ids))
    unknown_labels = sorted(set(label_ids) - input_ids)
    if missing_labels:
        issues.append({"issue": "missing_unit_function_labels", "unit_ids": missing_labels})
    if unknown_labels:
        issues.append({"issue": "unknown_unit_function_label_ids", "unit_ids": unknown_labels})
    for label in labels:
        if not isinstance(label, dict):
            continue
        function_type = str(label.get("function_type"))
        if function_type not in allowed_types:
            issues.append({"issue": "invalid_function_type", "unit_id": label.get("unit_id"), "function_type": function_type})

    core_points = output.get("core_points", [])
    if not isinstance(core_points, list):
        issues.append({"issue": "core_points_not_list"})
        core_points = []
    for cp in core_points:
        if not isinstance(cp, dict):
            continue
        cp_id = cp.get("draft_core_point_id")
        for field in ("anchor_unit_ids", "support_unit_ids", "intervening_support_unit_ids"):
            for unit_id in cp.get(field, []) or []:
                if str(unit_id) not in input_ids:
                    issues.append({"issue": "unknown_core_point_unit_ref", "core_point_id": cp_id, "field": field, "unit_id": unit_id})
        for field in ("concept_unit_spans", "evidence_unit_spans"):
            spans = cp.get(field)
            if not isinstance(spans, list):
                issues.append({"issue": "missing_or_invalid_spans", "core_point_id": cp_id, "field": field})
                continue
            for span in spans:
                if not isinstance(span, list) or len(span) != 2:
                    issues.append({"issue": "invalid_span_shape", "core_point_id": cp_id, "field": field, "span": span})
                    continue
                start, end = int(span[0]), int(span[1])
                if start > end:
                    issues.append({"issue": "invalid_span_order", "core_point_id": cp_id, "field": field, "span": span})
                if start not in input_orders or end not in input_orders:
                    issues.append({"issue": "span_outside_section", "core_point_id": cp_id, "field": field, "span": span})
        if cp.get("non_contiguous_concept") is True:
            concept_spans = cp.get("concept_unit_spans") or []
            flags = set(cp.get("review_flags") or [])
            if len(concept_spans) < 2:
                issues.append({"issue": "non_contiguous_without_multiple_concept_spans", "core_point_id": cp_id})
            if not flags:
                issues.append({"issue": "non_contiguous_without_review_flags", "core_point_id": cp_id})
    return issues


def write_validation_report(path: Path, section_input: dict[str, Any], output: dict[str, Any] | None, issues: list[dict[str, Any]]) -> None:
    lines = [
        "# P2A validation report",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- section_id: {section_input.get('section_id')}",
        f"- input_units: {len(section_input.get('units', []))}",
        f"- output_labels: {len((output or {}).get('unit_function_labels', [])) if output else 0}",
        f"- output_core_points: {len((output or {}).get('core_points', [])) if output else 0}",
        f"- issues: {len(issues)}",
        "",
    ]
    for issue in issues:
        lines.append(json.dumps(issue, ensure_ascii=False))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def call_model(client: Any, model: str, messages: list[dict[str, str]], temperature: float, max_tokens: int, json_mode: bool) -> tuple[str, dict[str, Any]]:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    raw = (resp.choices[0].message.content or "").strip()
    usage = getattr(resp, "usage", None)
    usage_payload = usage.model_dump() if hasattr(usage, "model_dump") else {}
    return raw, usage_payload


def run(args: argparse.Namespace) -> None:
    phase_dir = PHASE_DIR
    section_input = build_section_input(args.units_file.resolve(), args.section_id)
    prompt_text = args.prompt_file.resolve().read_text(encoding="utf-8")
    run_dir = (args.run_dir or (phase_dir / "runs" / args.run_slug)).resolve()
    input_path = run_dir / "input_section.json"
    raw_path = run_dir / "raw_response.txt"
    parsed_path = run_dir / "parsed_response.json"
    manifest_path = run_dir / "run_manifest.json"
    validation_path = run_dir / "validation_report.md"

    write_json(input_path, section_input)
    messages = build_messages(prompt_text, section_input)
    manifest = {
        "schema_version": "p2a_ds_run_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "section_id": args.section_id,
        "model": args.model,
        "base_url": args.base_url or DEFAULT_BASE_URL,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "json_mode": args.json_mode,
        "prompt_file": str(args.prompt_file.resolve()),
        "prompt_sha256": sha256_text(prompt_text),
        "input_sha256": sha256_text(canonical_json(section_input)),
        "message_sha256": sha256_text(canonical_json(messages)),
        "dry_run": args.dry_run,
    }

    parsed: dict[str, Any] | None = None
    issues: list[dict[str, Any]] = []
    if args.dry_run:
        manifest["status"] = "dry_run_input_only"
        issues.append({"issue": "dry_run_no_model_output"})
    else:
        from openai import OpenAI

        api_key, base_url, key_source = get_deepseek_config()
        manifest["api_key_source"] = key_source
        manifest["base_url"] = args.base_url or base_url
        client = OpenAI(api_key=api_key, base_url=manifest["base_url"])
        raw, usage = call_model(client, args.model, messages, args.temperature, args.max_tokens, args.json_mode)
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(raw, encoding="utf-8")
        manifest["usage"] = usage
        parsed = extract_json_object(raw)
        if parsed is None:
            manifest["status"] = "malformed"
            issues.append({"issue": "model_output_malformed"})
        else:
            write_json(parsed_path, parsed)
            issues.extend(validate_output(section_input, parsed))
            manifest["status"] = "passed" if not issues else "validation_failed"

    write_validation_report(validation_path, section_input, parsed, issues)
    write_json(manifest_path, manifest)
    if parsed and not args.no_copy_outputs:
        core_rows = []
        for cp in parsed.get("core_points", []) or []:
            row = dict(cp)
            row["section_id"] = parsed.get("section_id") or section_input.get("section_id")
            row["chapter_id"] = section_input.get("chapter_id")
            row["section_title"] = section_input.get("section_title")
            row["run_slug"] = args.run_slug
            core_rows.append(row)
        label_rows = []
        for label in parsed.get("unit_function_labels", []) or []:
            row = dict(label)
            row["section_id"] = parsed.get("section_id") or section_input.get("section_id")
            row["chapter_id"] = section_input.get("chapter_id")
            row["run_slug"] = args.run_slug
            label_rows.append(row)
        write_jsonl(phase_dir / "outputs" / "p2a_core_points.jsonl", core_rows)
        write_jsonl(phase_dir / "outputs" / "p2a_unit_function_labels.jsonl", label_rows)
        write_validation_report(phase_dir / "reports" / "p2a_validation_report.md", section_input, parsed, issues)

    print(json.dumps({"status": manifest.get("status"), "run_dir": str(run_dir), "issues": len(issues)}, ensure_ascii=False))
    if issues:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--section-id", required=True)
    parser.add_argument("--units-file", type=Path, default=DEFAULT_UNITS)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--run-slug", default="p2a_ds_flash_test")
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--model", default="deepseek-chat")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--json-mode", action="store_true", default=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-copy-outputs", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())

