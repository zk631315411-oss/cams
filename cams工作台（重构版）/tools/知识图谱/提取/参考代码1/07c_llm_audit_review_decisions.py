"""
v4.3 Step 7C: LLM-assisted review decision audit.

This step asks a stronger LLM to review Step 7A pending decisions and produce
Step 7B-compatible decisions. It is still advisory: every output is validated
and must be applied by 07b_apply_review_decisions.py.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
MODULE_DIR = SCRIPT_DIR.parents[1]
DEFAULT_CONFIG = SCRIPT_DIR / "v4_3_config.json"
DEFAULT_PROMPT = SCRIPT_DIR / "prompts" / "review_decision_audit.md"
DEFAULT_MIDDLE_DIR = SCRIPT_DIR / "中间产物"
DEFAULT_LAYER_DIR = DEFAULT_MIDDLE_DIR / "step6_layers"
DEFAULT_PREAPPROVAL = DEFAULT_MIDDLE_DIR / "step7_preapproval" / "preapproval_decisions.jsonl"
DEFAULT_OUT_DIR = DEFAULT_MIDDLE_DIR / "step7_llm_audit"
ENV_PATHS = [REPO_ROOT / ".env", MODULE_DIR / ".env"]

VALID_RECOMMENDATIONS = {"accept", "rewrite", "reject", "defer"}
VALID_TARGET_LAYERS = {"core", "explicit_core", "rule_case", "example_application", "rejected_archive", "review_pending"}
VALID_EDGE_TYPES = {"SUPERIOR", "EQUATIVE", "PART_OF", "HAS_PROPERTY", "USES", "GETS", "DERIVES"}
VALID_RULE_LOGIC = {"AND", "OR", "IFF", "PIECEWISE", "UNKNOWN"}
SAFE_DEFAULT_MODEL = "deepseek-chat"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Step 7C LLM audit decisions.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--layer-dir", type=Path, default=DEFAULT_LAYER_DIR)
    parser.add_argument("--preapproval", type=Path, default=DEFAULT_PREAPPROVAL)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--model", default="", help="Override model. Default: config high_risk_model or deepseek-chat.")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-workers", type=int, default=1, help="Parallel LLM requests. Keep low for paid API calls.")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--item-kind", choices=["all", "node", "edge", "rule_case"], default="all")
    parser.add_argument("--mock", action="store_true", help="Use deterministic heuristic decisions without calling the API.")
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Skip decisions already present in llm_audit_decisions.jsonl.")
    parser.add_argument("--allow-pro", action="store_true", help="Allow expensive Pro models. Pro is blocked unless this flag or config llm.allow_pro=true is set.")
    parser.add_argument("--thinking", action="store_true", help="Send DeepSeek thinking controls. Disabled by default to control cost.")
    parser.add_argument("--reasoning-effort", default="low", choices=["low", "medium", "high", "max"])
    return parser.parse_args()


def read_json(path: Path, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"JSON not found: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path, required: bool = True) -> list[dict[str, Any]]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"JSONL not found: {path}")
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]], append: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_completed_decision_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        decision_id = str(row.get("decision_id") or "")
        if decision_id:
            completed.add(decision_id)
    return completed


def load_env_value(key: str) -> str:
    value = os.environ.get(key, "")
    if value:
        return value
    for env_path in ENV_PATHS:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            name, value = stripped.split("=", 1)
            if name.strip() == key:
                return value.strip().strip('"').strip("'")
    return ""


def is_pro_model(model: str) -> bool:
    return "pro" in model.lower()


def parse_llm_json(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError as first_exc:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise RuntimeError(f"LLM returned invalid JSON: {first_exc}; content_prefix={content[:1000]}") from first_exc


def call_llm(
    api_key: str,
    base_url: str,
    model: str,
    prompt: str,
    payload: dict[str, Any],
    temperature: float,
    timeout: float,
    thinking: bool,
    reasoning_effort: str,
) -> dict[str, Any]:
    request_body: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你只输出合法 JSON，不输出 Markdown 或解释。"},
            {"role": "user", "content": prompt + "\n\n## 当前审核输入\n\n" + json.dumps(payload, ensure_ascii=False)},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    if thinking:
        request_body["thinking"] = {"type": "enabled"}
        request_body["reasoning_effort"] = reasoning_effort

    data = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url=base_url.rstrip("/") + "/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last_error: RuntimeError | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_body = json.loads(response.read().decode("utf-8"))
            content = response_body.get("choices", [{}])[0].get("message", {}).get("content") or "{}"
            return parse_llm_json(content)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM HTTP {exc.code}: {body[:1200]}") from exc
        except urllib.error.URLError as exc:
            last_error = RuntimeError(f"LLM request failed: {exc}")
        except RuntimeError as exc:
            last_error = exc
        if attempt < 3:
            time.sleep(1.5 * attempt)
    assert last_error is not None
    raise last_error


def compact_text(value: Any, limit: int = 1600) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def load_layer_context(layer_dir: Path) -> dict[str, Any]:
    nodes = read_jsonl(layer_dir / "explicit_core_nodes.jsonl", required=False)
    review_nodes = read_jsonl(layer_dir / "review_pending_nodes.jsonl", required=False)
    all_nodes = nodes + review_nodes
    return {
        "schema": {
            "node_types": ["Concept", "Method", "Formula", "Theorem", "ProblemClass"],
            "edge_types": sorted(VALID_EDGE_TYPES),
            "recommendations": sorted(VALID_RECOMMENDATIONS),
            "target_layers": sorted(VALID_TARGET_LAYERS),
        },
        "available_nodes": [
            {
                "node_id": row.get("node_id", ""),
                "name": row.get("name", ""),
                "type": row.get("type", ""),
                "section_node_id": row.get("section_node_id", ""),
                "review_status": row.get("review_status", ""),
            }
            for row in all_nodes
        ],
    }


def strip_source_item(item: dict[str, Any], item_kind: str) -> dict[str, Any]:
    source = item.get("source_item") or {}
    common = {
        "decision_id": item.get("decision_id", ""),
        "item_kind": item_kind,
        "item_id": item.get("item_id", ""),
        "item_name": item.get("item_name", ""),
        "item_type": item.get("item_type", ""),
        "kg_layer": item.get("kg_layer", ""),
        "basis": item.get("basis", ""),
        "evidence_excerpt": item.get("evidence_excerpt", ""),
            "source_item": {
                "name": source.get("name", ""),
                "type": source.get("type", ""),
                "source_name": source.get("source_name", ""),
                "target_name": source.get("target_name", ""),
                "edge_type": source.get("type", "") if item_kind == "edge" else "",
                "semantic_inferred": bool(source.get("semantic_inferred")) if item_kind == "edge" else False,
                "basis_type": source.get("basis_type", "") if item_kind == "edge" else "",
                "source_type": source.get("source_type", "") if item_kind == "edge" else "",
                "target_type": source.get("target_type", "") if item_kind == "edge" else "",
                "owner_name": source.get("owner_name", ""),
                "case_name": source.get("case_name", ""),
                "applies_to": source.get("applies_to", ""),
                "conditions": source.get("conditions", []),
            "condition_logic": source.get("condition_logic", ""),
            "outcomes": source.get("outcomes", []),
            "formula_refs": source.get("formula_refs", []),
            "description": source.get("description", ""),
            "evidence_span": compact_text(source.get("evidence_span", ""), 2400),
            "definition": compact_text(source.get("definition", ""), 1200),
            "source_label": source.get("source_label", ""),
            "validation_warnings": source.get("validation_warnings", []),
            "review_reason": source.get("review_reason", ""),
            "section_node_id": source.get("section_node_id", ""),
            "chapter": source.get("chapter", ""),
            "section": source.get("section", ""),
            "subsection": source.get("subsection", ""),
        },
    }
    if item_kind == "node":
        common["source_item"]["rule_cases"] = source.get("rule_cases", [])
        common["source_item"]["dropped_rule_cases"] = source.get("dropped_rule_cases", [])
    return common


def select_decisions(decisions: list[dict[str, Any]], item_kind: str, limit: int) -> list[dict[str, Any]]:
    selected = decisions if item_kind == "all" else [row for row in decisions if row.get("item_kind") == item_kind]
    if limit > 0:
        selected = selected[:limit]
    return selected


def batched(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    size = max(1, size)
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def default_decision(source_decision: dict[str, Any], recommendation: str, detail: str, basis: str) -> dict[str, Any]:
    target_layer = {
        "accept": "rule_case" if source_decision.get("item_kind") == "rule_case" else "core",
        "reject": "rejected_archive",
        "defer": "review_pending",
        "rewrite": source_decision.get("target_layer") or "core",
    }[recommendation]
    row = copy.deepcopy(source_decision)
    row["recommendation"] = recommendation
    row["action_detail"] = detail
    row["target_layer"] = target_layer
    row["basis"] = f"{source_decision.get('basis', '')} | {basis}"
    row["rewritten_item"] = None
    row["generated_at"] = datetime.now().isoformat(timespec="seconds")
    return row


def mock_audit(decision: dict[str, Any]) -> dict[str, Any]:
    kind = decision.get("item_kind")
    source = decision.get("source_item") or {}
    if kind == "node":
        return default_decision(decision, "accept", "mock_accept_node", "Mock audit: review node kept as explicit knowledge point.")
    if kind == "rule_case":
        evidence = str(source.get("evidence_span") or "")
        if len(evidence.strip()) < 12:
            return default_decision(decision, "reject", "mock_reject_rule_case_short_evidence", "Mock audit: evidence too short.")
        return default_decision(decision, "accept", "mock_accept_rule_case", "Mock audit: rule case has condition, outcome and evidence.")
    if kind == "edge":
        warnings = source.get("validation_warnings") or []
        edge_type = str(source.get("type") or "")
        if "equative_weak_relation_requires_review" in warnings:
            return default_decision(decision, "reject", "mock_reject_weak_equative", "Mock audit: weak EQUATIVE relation.")
        if edge_type == "DERIVES":
            return default_decision(decision, "defer", "mock_defer_derives", "Mock audit: DERIVES requires direction review.")
        return default_decision(decision, "accept", "mock_accept_edge", "Mock audit: edge accepted by heuristic.")
    return default_decision(decision, "defer", "mock_defer_unknown", "Mock audit: unknown item kind.")


def normalize_recommendation(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text if text in VALID_RECOMMENDATIONS else "defer"


def normalize_target_layer(recommendation: str, value: Any, item_kind: str) -> str:
    text = str(value or "").strip()
    if text not in VALID_TARGET_LAYERS:
        text = ""
    if recommendation == "reject":
        return "rejected_archive"
    if recommendation == "defer":
        return "review_pending"
    if recommendation == "accept" and item_kind == "rule_case":
        return "rule_case"
    if recommendation == "accept" and not text:
        return "core"
    if recommendation == "rewrite" and not text:
        return "core"
    return text


def validate_rewrite(rewrite: Any, source_decision: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    warnings: list[str] = []
    if not isinstance(rewrite, dict):
        return None, ["missing_rewritten_item"]
    operation = str(rewrite.get("operation") or "")
    item_kind = str(source_decision.get("item_kind") or "")
    fixed = dict(rewrite)
    if item_kind == "edge":
        if operation != "replace_edge":
            warnings.append("edge_rewrite_requires_replace_edge")
        if str(fixed.get("type") or "") not in VALID_EDGE_TYPES:
            warnings.append("invalid_rewrite_edge_type")
        if not fixed.get("source_name") or not fixed.get("target_name"):
            warnings.append("missing_rewrite_edge_endpoint")
        fixed.setdefault("kg_layer", "core")
    elif item_kind == "rule_case":
        if operation != "replace_rule_case":
            warnings.append("rule_case_rewrite_requires_replace_rule_case")
        if not fixed.get("conditions") or not fixed.get("outcomes"):
            warnings.append("rewrite_rule_case_missing_condition_or_outcome")
        if str(fixed.get("condition_logic") or "") not in VALID_RULE_LOGIC:
            fixed["condition_logic"] = "UNKNOWN"
    elif item_kind == "node":
        if operation != "merge_node":
            warnings.append("node_rewrite_only_supports_merge_node")
        if not fixed.get("target_name") and not fixed.get("target_node_id"):
            warnings.append("missing_merge_target")
    else:
        warnings.append("unknown_rewrite_item_kind")
    return (fixed if not warnings else None), warnings


def hard_guard_decision(decision: dict[str, Any], source_decision: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    item_kind = str(source_decision.get("item_kind") or "")
    rec = normalize_recommendation(decision.get("recommendation"))
    target_layer = normalize_target_layer(rec, decision.get("target_layer"), item_kind)

    if rec == "rewrite":
        rewrite, rewrite_warnings = validate_rewrite(decision.get("rewritten_item"), source_decision)
        if rewrite_warnings:
            warnings.extend(rewrite_warnings)
            rec = "defer"
            target_layer = "review_pending"
            rewrite = None
        decision["rewritten_item"] = rewrite
    else:
        decision["rewritten_item"] = None

    if rec == "accept" and item_kind == "edge":
        source = source_decision.get("source_item") or {}
        if source.get("type") == "DERIVES" and "derives_direction_requires_review" in (source.get("validation_warnings") or []):
            warnings.append("guard_deferred_derives_direction_warning")
            rec = "defer"
            target_layer = "review_pending"

    if rec == "accept" and item_kind == "rule_case":
        source = source_decision.get("source_item") or {}
        evidence = str(source.get("evidence_span") or "")
        if len(evidence.strip()) < 8:
            warnings.append("guard_rejected_rule_case_evidence_too_short")
            rec = "reject"
            target_layer = "rejected_archive"

    fixed = copy.deepcopy(source_decision)
    fixed["recommendation"] = rec
    fixed["target_layer"] = target_layer
    fixed["action_detail"] = str(decision.get("action_detail") or f"llm_audit_{rec}")[:200]
    llm_basis = str(decision.get("basis") or "").strip()
    original_basis = str(source_decision.get("basis") or "").strip()
    fixed["basis"] = f"{original_basis} | LLM audit: {llm_basis}" if original_basis else f"LLM audit: {llm_basis}"
    fixed["rewritten_item"] = decision.get("rewritten_item") if rec == "rewrite" else None
    fixed["generated_at"] = datetime.now().isoformat(timespec="seconds")
    if warnings:
        fixed["llm_audit_guard_warnings"] = warnings
        if rec == "defer":
            fixed["action_detail"] = "guard_deferred_invalid_llm_decision"
    return fixed, warnings


def index_source_decisions(decisions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("decision_id") or ""): row for row in decisions}


def process_llm_response(raw: dict[str, Any], batch: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_by_id = index_source_decisions(batch)
    raw_decisions = raw.get("decisions") if isinstance(raw.get("decisions"), list) else []
    output: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw_decision in raw_decisions:
        if not isinstance(raw_decision, dict):
            warnings.append({"warning": "raw_decision_not_object", "raw": raw_decision})
            continue
        decision_id = str(raw_decision.get("decision_id") or "")
        source = source_by_id.get(decision_id)
        if not source:
            warnings.append({"warning": "unknown_decision_id", "decision_id": decision_id})
            continue
        fixed, guard_warnings = hard_guard_decision(raw_decision, source)
        if guard_warnings:
            warnings.append({"warning": "guard_warnings", "decision_id": decision_id, "details": guard_warnings})
        output.append(fixed)
        seen.add(decision_id)
    for source in batch:
        decision_id = str(source.get("decision_id") or "")
        if decision_id not in seen:
            fixed = default_decision(source, "defer", "llm_audit_missing_decision", "LLM audit did not return this item; deferred by guard.")
            output.append(fixed)
            warnings.append({"warning": "missing_decision_from_llm", "decision_id": decision_id})
    return output, warnings


def write_summary(path: Path, decisions: list[dict[str, Any]], warnings: list[dict[str, Any]], model: str, mock: bool) -> None:
    by_kind = Counter((row.get("item_kind", ""), row.get("recommendation", "")) for row in decisions)
    lines = [
        "# v4.3 Step 7C LLM Audit Summary",
        "",
        f"- model: {model}",
        f"- mock: {mock}",
        f"- decisions: {len(decisions)}",
        f"- guard_warnings: {len(warnings)}",
        "",
        "## Decision Counts",
    ]
    for (kind, rec), count in sorted(by_kind.items()):
        lines.append(f"- {kind} / {rec}: {count}")
    if warnings:
        lines.extend(["", "## Guard Warnings"])
        for warning in warnings[:80]:
            lines.append(f"- {json.dumps(warning, ensure_ascii=False)}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def failed_batch_result(batch_index: int, batch: list[dict[str, Any]], model: str, mock: bool, error: Exception) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    warning = {
        "warning": "batch_failed_deferred",
        "batch_index": batch_index,
        "error": str(error)[:1200],
        "decision_ids": [row.get("decision_id", "") for row in batch],
    }
    output = [
        default_decision(
            row,
            "defer",
            "llm_audit_batch_failed_deferred",
            f"LLM audit batch failed; deferred by guard. error={str(error)[:500]}",
        )
        for row in batch
    ]
    raw_record = {
        "batch_index": batch_index,
        "model": model,
        "mock": mock,
        "elapsed_seconds": 0.0,
        "input_decision_ids": [row.get("decision_id", "") for row in batch],
        "error": str(error)[:2000],
        "raw": {},
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    return raw_record, output, [warning]


def run_batch(
    batch_index: int,
    batch: list[dict[str, Any]],
    context: dict[str, Any],
    prompt: str,
    api_key: str,
    base_url: str,
    model: str,
    temperature: float,
    timeout: float,
    mock: bool,
    thinking: bool,
    reasoning_effort: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    payload = {
        "batch_index": batch_index,
        "schema": context["schema"],
        "available_nodes": context["available_nodes"],
        "items": [strip_source_item(row, str(row.get("item_kind") or "")) for row in batch],
    }
    started = time.time()
    if mock:
        raw = {"decisions": [mock_audit(row) for row in batch]}
        elapsed = 0.0
    else:
        raw = call_llm(
            api_key,
            base_url,
            model,
            prompt,
            payload,
            temperature,
            timeout,
            thinking=thinking,
            reasoning_effort=reasoning_effort,
        )
        elapsed = time.time() - started
    output, warnings = process_llm_response(raw, batch)
    raw_record = {
        "batch_index": batch_index,
        "model": model,
        "mock": mock,
        "elapsed_seconds": round(elapsed, 2),
        "input_decision_ids": [row.get("decision_id", "") for row in batch],
        "raw": raw,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    return raw_record, output, warnings


def main() -> None:
    args = parse_args()
    config = read_json(args.config, required=False)
    llm_config = config.get("llm", {})
    model = args.model or llm_config.get("high_risk_model") or SAFE_DEFAULT_MODEL
    allow_pro = bool(args.allow_pro or llm_config.get("allow_pro", False))
    if is_pro_model(model) and not allow_pro:
        raise RuntimeError(
            f"Pro model requested ({model}) but Pro is disabled. "
            "Pass --allow-pro or set llm.allow_pro=true only for intentional small-sample audits."
        )
    base_url = args.base_url or llm_config.get("base_url", "https://api.deepseek.com/v1")
    temperature = args.temperature if args.temperature is not None else 0.0
    timeout = args.timeout if args.timeout is not None else float(llm_config.get("timeout_seconds", 180))
    prompt = args.prompt.read_text(encoding="utf-8")

    all_decisions = select_decisions(read_jsonl(args.preapproval), args.item_kind, args.limit)
    context = load_layer_context(args.layer_dir)
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    decisions_path = out_dir / "llm_audit_decisions.jsonl"
    raw_path = out_dir / "llm_audit_raw.jsonl"
    warnings_path = out_dir / "llm_audit_warnings.jsonl"
    if not args.append and not args.resume:
        for path in [decisions_path, raw_path, warnings_path]:
            if path.exists():
                path.unlink()
    if args.resume:
        completed_ids = read_completed_decision_ids(decisions_path)
        before = len(all_decisions)
        all_decisions = [row for row in all_decisions if str(row.get("decision_id") or "") not in completed_ids]
        print(f"[INFO] resume=True completed={before - len(all_decisions)} remaining={len(all_decisions)}")

    api_key = ""
    if not args.mock:
        api_key = load_env_value("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("DEEPSEEK_API_KEY not found. Use --mock for local validation.")

    batches = list(enumerate(batched(all_decisions, args.batch_size), start=1))
    print(
        f"[INFO] decisions={len(all_decisions)} batches={len(batches)} "
        f"batch_size={args.batch_size} max_workers={args.max_workers} model={model} mock={args.mock}"
    )
    all_output: list[dict[str, Any]] = []
    all_warnings: list[dict[str, Any]] = []

    def handle_result(raw_record: dict[str, Any], output: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> None:
        write_jsonl(raw_path, [raw_record], append=True)
        write_jsonl(decisions_path, output, append=True)
        if warnings:
            write_jsonl(warnings_path, warnings, append=True)
        all_output.extend(output)
        all_warnings.extend(warnings)
        counts = Counter(row.get("recommendation", "") for row in output)
        print(
            f"[OK] batch={raw_record.get('batch_index')} elapsed={raw_record.get('elapsed_seconds', 0.0):.1f}s "
            f"decisions={len(output)} counts={dict(counts)} warnings={len(warnings)}"
        )

    if args.max_workers <= 1:
        for batch_index, batch in batches:
            try:
                raw_record, output, warnings = run_batch(
                    batch_index,
                    batch,
                    context,
                    prompt,
                    api_key,
                    base_url,
                    model,
                    temperature,
                    timeout,
                    args.mock,
                    thinking=args.thinking,
                    reasoning_effort=args.reasoning_effort,
                )
            except Exception as exc:  # noqa: BLE001 - keep pipeline moving and record the failed batch.
                raw_record, output, warnings = failed_batch_result(batch_index, batch, model, args.mock, exc)
            handle_result(raw_record, output, warnings)
    else:
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            future_to_batch = {
                executor.submit(
                    run_batch,
                    batch_index,
                    batch,
                    context,
                    prompt,
                    api_key,
                    base_url,
                    model,
                    temperature,
                    timeout,
                    args.mock,
                    args.thinking,
                    args.reasoning_effort,
                ): (batch_index, batch)
                for batch_index, batch in batches
            }
            for future in as_completed(future_to_batch):
                batch_index, batch = future_to_batch[future]
                try:
                    raw_record, output, warnings = future.result()
                except Exception as exc:  # noqa: BLE001 - keep pipeline moving and record the failed batch.
                    raw_record, output, warnings = failed_batch_result(batch_index, batch, model, args.mock, exc)
                handle_result(raw_record, output, warnings)

    write_summary(out_dir / "llm_audit_summary.md", all_output, all_warnings, model, args.mock)
    print(f"[OK] decisions -> {decisions_path}")
    print(f"[OK] raw -> {raw_path}")
    print(f"[OK] warnings -> {warnings_path}")
    print(f"[OK] summary -> {out_dir / 'llm_audit_summary.md'}")


if __name__ == "__main__":
    main()
