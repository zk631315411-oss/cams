"""
v4.4 Step 4B: extract condition-judgment rule cases.

This step reads current leaf-section text and the admitted node pool, then asks
the LLM to attach RuleCase candidates to existing Theorem/Formula/Method nodes.
It does not create nodes or ordinary edges.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import re
import socket
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
MODULE_DIR = SCRIPT_DIR.parents[1]
DEFAULT_CONFIG = SCRIPT_DIR / "v4_3_config.json"
DEFAULT_PROMPT = SCRIPT_DIR / "prompts" / "rule_case_extraction.md"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "中间产物"
DEFAULT_LEAF_SECTIONS = DEFAULT_OUTPUT_DIR / "leaf_sections.jsonl"
DEFAULT_NODES = DEFAULT_OUTPUT_DIR / "nodes.jsonl"
DEFAULT_RAW_OUTPUT = DEFAULT_OUTPUT_DIR / "raw_rule_case_candidates.jsonl"
DEFAULT_RULE_CASES = DEFAULT_OUTPUT_DIR / "rule_cases.jsonl"
DEFAULT_REVIEW = DEFAULT_OUTPUT_DIR / "rule_case_review_queue.jsonl"
DEFAULT_WARNINGS = DEFAULT_OUTPUT_DIR / "rule_case_extraction_warnings.jsonl"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "rule_case_extraction_report.md"
ENV_PATHS = [REPO_ROOT / ".env", MODULE_DIR / ".env"]

OWNER_TYPES = {"Theorem", "Formula", "Method"}
VALID_LOGIC = {"SUFFICIENT", "NECESSARY", "IFF", "PIECEWISE", "AND", "OR", "UNKNOWN"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract v4.4 rule case candidates.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--leaf-sections", type=Path, default=DEFAULT_LEAF_SECTIONS)
    parser.add_argument("--nodes", type=Path, default=DEFAULT_NODES)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW_OUTPUT)
    parser.add_argument("--rule-cases", type=Path, default=DEFAULT_RULE_CASES)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--warnings", type=Path, default=DEFAULT_WARNINGS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--chunk-id", "--section-node-id", dest="section_node_id", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--model", default="")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("--max-node-pool", type=int, default=48)
    parser.add_argument("--append", action="store_true")
    parser.add_argument(
        "--keep-rejected-candidates",
        action="store_true",
        help="Write locally rejected structured candidates to --rule-cases so Step 4C can audit the full Step 4B output.",
    )
    return parser.parse_args()


def read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"JSONL not found: {path}")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def open_output(path: Path, append: bool):
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("a" if append else "w", encoding="utf-8", newline="\n")


def chunk_order_from_id(section_node_id: str) -> tuple[int, int, int]:
    match = re.search(r":C(\d+):S(\d+):U(\d+)$", str(section_node_id or ""))
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())


def section_sort_key(section: dict[str, Any]) -> tuple[int, int, int, str]:
    return (*chunk_order_from_id(str(section.get("section_node_id") or "")), str(section.get("section_node_id") or ""))


def node_visible_for_section(node: dict[str, Any], section: dict[str, Any]) -> bool:
    return chunk_order_from_id(str(node.get("section_node_id") or "")) <= chunk_order_from_id(str(section.get("section_node_id") or ""))


def node_current_section(node: dict[str, Any], section: dict[str, Any]) -> bool:
    return str(node.get("section_node_id") or "") == str(section.get("section_node_id") or "")


def node_sort_key(node: dict[str, Any]) -> tuple[int, int, int, str]:
    return (*chunk_order_from_id(str(node.get("section_node_id") or "")), str(node.get("name") or ""))


def compact_node(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": node.get("node_id", ""),
        "name": node.get("name", ""),
        "type": node.get("type", ""),
        "review_status": node.get("review_status", ""),
        "source_label": node.get("source_label", ""),
        "aliases": node.get("aliases", [])[:5],
        "section_node_id": node.get("section_node_id", ""),
        "description": str(node.get("description") or node.get("evidence_span") or "")[:180],
    }


def relation_section_text(section: dict[str, Any]) -> str:
    anchors = section.get("anchors")
    if isinstance(anchors, list) and anchors:
        chunks: list[str] = []
        for anchor in anchors:
            if not isinstance(anchor, dict):
                continue
            anchor_type = str(anchor.get("anchor_type") or "").strip().lower()
            if anchor_type in {"example", "exercise"}:
                continue
            text = str(anchor.get("text") or "").strip()
            if text:
                chunks.append(text)
        if chunks:
            return "\n\n".join(chunks)
    return str(section.get("text") or "")


def build_node_pool(section: dict[str, Any], nodes: list[dict[str, Any]], max_nodes: int) -> list[dict[str, Any]]:
    visible = [
        node for node in nodes
        if node_visible_for_section(node, section)
        and node.get("review_status") in {"auto_accept", "review"}
        and node.get("type") in OWNER_TYPES
    ]
    current = [node for node in visible if node_current_section(node, section)]
    previous = [node for node in visible if node not in current]
    ordered = sorted(current, key=node_sort_key) + sorted(previous, key=node_sort_key)
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for node in ordered:
        node_id = str(node.get("node_id") or "")
        if not node_id or node_id in seen:
            continue
        seen.add(node_id)
        deduped.append(node)
        if len(deduped) >= max_nodes:
            break
    return deduped


def select_sections(sections: list[dict[str, Any]], config: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    sections = sorted(sections, key=section_sort_key)
    if args.section_node_id:
        selected = [section for section in sections if section.get("section_node_id") == args.section_node_id]
        if not selected:
            raise ValueError(f"section_node_id not found: {args.section_node_id}")
        return selected
    skip_scopes = set(config.get("tree", {}).get("skip_source_scopes", ["exercise"]))
    eligible = [section for section in sections if section.get("source_scope") not in skip_scopes and section.get("source_scope") == "core_content"]
    if args.dry_run:
        return eligible[:1]
    if args.limit > 0:
        return eligible[: args.limit]
    return eligible


def build_payload(section: dict[str, Any], node_pool: list[dict[str, Any]]) -> dict[str, Any]:
    section_text = relation_section_text(section)
    return {
        "section_metadata": {
            "section_node_id": section.get("section_node_id", ""),
            "textbook_id": section.get("textbook_id", ""),
            "textbook_name": section.get("textbook_name", ""),
            "chapter": section.get("chapter", ""),
            "section": section.get("section", ""),
            "subsection": section.get("subsection", ""),
            "source_scope": section.get("source_scope", ""),
            "line_start": section.get("line_start", 0),
            "line_end": section.get("line_end", 0),
        },
        "section_text": section_text,
        "node_pool": [compact_node(node) for node in node_pool],
    }


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


def call_llm(api_key: str, base_url: str, model: str, prompt: str, payload: dict[str, Any], temperature: float, timeout: float) -> dict[str, Any]:
    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你只输出合法 JSON，不输出 Markdown 或解释。"},
            {"role": "user", "content": prompt + "\n\n## 当前输入\n\n" + json.dumps(payload, ensure_ascii=False)},
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    reasoning_effort = os.environ.get("LLM_REASONING_EFFORT", "").strip()
    if reasoning_effort:
        request_body["reasoning_effort"] = reasoning_effort
    data = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url=base_url.rstrip("/") + "/chat/completions",
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    last_error: RuntimeError | None = None
    for attempt in range(1, 2):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_body = json.loads(response.read().decode("utf-8"))
            content = response_body.get("choices", [{}])[0].get("message", {}).get("content") or "{}"
            return parse_llm_json(content)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM HTTP {exc.code}: {body[:1000]}") from exc
        except http.client.RemoteDisconnected as exc:
            last_error = RuntimeError(f"LLM remote disconnected: {exc}")
        except urllib.error.URLError as exc:
            last_error = RuntimeError(f"LLM request failed: {exc}")
        except (ConnectionError, TimeoutError, socket.timeout, OSError) as exc:
            last_error = RuntimeError(f"LLM transport failed: {exc}")
        except RuntimeError as exc:
            last_error = exc
        if attempt < 1:
            time.sleep(1.5 * attempt)
    assert last_error is not None
    raise last_error


def normalize_for_match(text: str) -> str:
    text = re.sub(r"\s+", "", text)
    text = text.replace("\\pmb", "")
    text = text.replace("{", "").replace("}", "")
    return text


def span_in_section(span: str, section_text: str) -> bool:
    if not span:
        return False
    if span in section_text:
        return True
    normalized_span = normalize_for_match(span)
    normalized_text = normalize_for_match(section_text)
    return bool(normalized_span and normalized_span in normalized_text)


def stable_rule_case_id(row: dict[str, Any], index: int) -> str:
    raw = "|".join([
        str(row.get("owner_node_id") or ""),
        str(row.get("case_name") or ""),
        str(row.get("evidence_span") or ""),
        str(row.get("section_node_id") or ""),
        str(index),
    ])
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:14]
    return f"{row.get('textbook_id', '')}:rulecase:{digest}"


def clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def coerce_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def normalize_rule_case(raw: dict[str, Any], section: dict[str, Any], node_by_id: dict[str, dict[str, Any]], index: int, model: str, mode: str) -> dict[str, Any]:
    owner_id = str(raw.get("owner_node_id") or "")
    owner = node_by_id.get(owner_id, {})
    logic = str(raw.get("condition_logic") or raw.get("logic") or "UNKNOWN").strip().upper()
    if logic not in VALID_LOGIC:
        logic = "UNKNOWN"
    row = {
        "rule_case_id": "",
        "item_kind": "rule_case",
        "owner_node_id": owner_id,
        "owner_name": owner.get("name", str(raw.get("owner_name") or "").strip()),
        "owner_type": owner.get("type", ""),
        "case_name": str(raw.get("case_name") or "").strip(),
        "applies_to": str(raw.get("applies_to") or "").strip(),
        "conditions": clean_list(raw.get("conditions")),
        "condition_logic": logic,
        "outcomes": clean_list(raw.get("outcomes")),
        "formula_refs": clean_list(raw.get("formula_refs")),
        "evidence_span": str(raw.get("evidence_span") or "").strip(),
        "source_label": str(raw.get("source_label") or "").strip(),
        "reason": str(raw.get("reason") or "").strip(),
        "confidence": coerce_confidence(raw.get("confidence", 0)),
        "review_recommended": bool(raw.get("review_recommended", False)),
        "review_reason": str(raw.get("review_reason") or "").strip(),
        "textbook_id": section.get("textbook_id", ""),
        "textbook_name": section.get("textbook_name", ""),
        "chapter": section.get("chapter", ""),
        "section": section.get("section", ""),
        "subsection": section.get("subsection", ""),
        "section_node_id": section.get("section_node_id", ""),
        "source_scope": section.get("source_scope", ""),
        "kg_layer": "rule_case",
        "review_status": "pending",
        "validation_warnings": [],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "mode": mode,
    }
    row["rule_case_id"] = stable_rule_case_id(row, index)
    return row


def validate_rule_case(row: dict[str, Any], section_text: str, node_pool_ids: set[str]) -> list[str]:
    warnings: list[str] = []
    if row.get("owner_node_id") not in node_pool_ids:
        warnings.append(f"owner_not_in_node_pool:{row.get('owner_node_id')}")
    if row.get("owner_type") not in OWNER_TYPES:
        warnings.append(f"owner_invalid_type:{row.get('owner_type')}")
    if not row.get("case_name"):
        warnings.append("missing_case_name")
    if not row.get("conditions"):
        warnings.append("missing_conditions")
    if not row.get("outcomes"):
        warnings.append("missing_outcomes")
    evidence = str(row.get("evidence_span") or "")
    if not evidence:
        warnings.append("missing_evidence_span")
    elif not span_in_section(evidence, section_text):
        warnings.append("evidence_span_not_in_section")
    if "..." in evidence or "……" in evidence or "省略" in evidence:
        warnings.append("evidence_span_contains_ellipsis")
    if row.get("condition_logic") == "IFF" and not any(mark in evidence for mark in ["当且仅当", "充要条件", "充分必要条件"]):
        warnings.append("iff_without_explicit_biconditional")
    if row.get("confidence", 0.0) < 0.72:
        warnings.append("confidence_below_auto_threshold")
    if row.get("review_recommended"):
        warnings.append("review_recommended")
    return warnings


def decide_status(warnings: list[str]) -> str:
    hard_prefixes = ("owner_not_in_node_pool:", "owner_invalid_type:", "evidence_span_not_in_section:")
    hard_exact = {
        "missing_case_name",
        "missing_conditions",
        "missing_outcomes",
        "missing_evidence_span",
        "evidence_span_not_in_section",
        "evidence_span_contains_ellipsis",
    }
    if any(w.startswith(hard_prefixes) for w in warnings) or any(w in hard_exact for w in warnings):
        return "reject"
    if warnings:
        return "review"
    return "auto_accept"


def mock_rule_cases(section: dict[str, Any], node_pool: list[dict[str, Any]]) -> dict[str, Any]:
    return {"rule_cases": []}


def write_report(path: Path, processed_sections: int, total_raw: int, status_counts: dict[str, int], warning_counts: dict[str, int]) -> None:
    lines = [
        "# v4.4 Step 4B Rule Case Extraction Report",
        "",
        f"- processed sections: {processed_sections}",
        f"- raw rule cases: {total_raw}",
        "",
        "## Review Status",
    ]
    for key in sorted(status_counts):
        lines.append(f"- {key}: {status_counts[key]}")
    lines.extend(["", "## Top Warnings"])
    if warning_counts:
        for key, value in sorted(warning_counts.items(), key=lambda item: (-item[1], item[0]))[:30]:
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    sections = select_sections(read_jsonl(args.leaf_sections), config, args)
    nodes = read_jsonl(args.nodes)
    node_by_id = {node.get("node_id"): node for node in nodes if node.get("node_id")}
    llm_config = config.get("llm", {})
    model = args.model or llm_config.get("default_model", "deepseek-chat")
    base_url = args.base_url or load_env_value("LLM_API_BASE") or llm_config.get("base_url", "https://api.openai.com/v1")
    temperature = args.temperature if args.temperature is not None else float(llm_config.get("temperature", 0.0))
    timeout = args.timeout if args.timeout is not None else float(llm_config.get("timeout_seconds", 120))
    prompt = args.prompt.read_text(encoding="utf-8")

    api_key = ""
    if not args.mock:
        api_key = load_env_value("LLM_API_KEY") or load_env_value("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("LLM_API_KEY not found. Use --mock for local validation.")

    print(f"[INFO] sections={len(sections)} nodes={len(nodes)} model={model} mock={args.mock}")
    processed_sections = 0
    total_raw = 0
    status_counts: dict[str, int] = {}
    warning_counts: dict[str, int] = {}
    seen_ids: set[str] = set()
    llm_failed_sections = 0

    with (
        open_output(args.raw_output, args.append) as raw_f,
        open_output(args.rule_cases, args.append) as cases_f,
        open_output(args.review, args.append) as review_f,
        open_output(args.warnings, args.append) as warn_f,
    ):
        for section in sections:
            section_id = section.get("section_node_id", "")
            node_pool = build_node_pool(section, nodes, args.max_node_pool)
            if not node_pool:
                print(f"[SKIP] {section_id} node_pool=0")
                continue
            if args.mock:
                raw = mock_rule_cases(section, node_pool)
                elapsed = 0.0
                mode = "mock"
            else:
                started = time.time()
                raw = None
                mode = "llm"
                errors: list[str] = []
                retry_sizes = [args.max_node_pool, 16, 10, 6, 3]
                retry_sizes = sorted({size for size in retry_sizes if 1 <= size <= args.max_node_pool}, reverse=True)
                for attempt_index, pool_size in enumerate(retry_sizes, start=1):
                    node_pool = build_node_pool(section, nodes, pool_size)
                    payload = build_payload(section, node_pool)
                    try:
                        raw = call_llm(api_key, base_url, model, prompt, payload, temperature, timeout)
                        if attempt_index > 1:
                            warning_counts["llm_call_retried"] = warning_counts.get("llm_call_retried", 0) + 1
                            warn_f.write(json.dumps({
                                "section_node_id": section_id,
                                "warnings": ["llm_call_retried"],
                                "successful_pool_size": len(node_pool),
                                "previous_errors": errors[-2:],
                            }, ensure_ascii=False) + "\n")
                        break
                    except RuntimeError as exc:
                        errors.append(f"pool={len(node_pool)}: {str(exc)[:600]}")
                        continue
                if raw is None:
                    elapsed = time.time() - started
                    warn_f.write(json.dumps({
                        "section_node_id": section_id,
                        "warnings": ["llm_call_failed"],
                        "error": " | ".join(errors)[-1200:],
                    }, ensure_ascii=False) + "\n")
                    warning_counts["llm_call_failed"] = warning_counts.get("llm_call_failed", 0) + 1
                    llm_failed_sections += 1
                    print(f"[ERROR] {section_id} mode=llm elapsed={elapsed:.1f}s {errors[-1] if errors else 'unknown error'}")
                    continue
                elapsed = time.time() - started

            raw_cases = raw.get("rule_cases") if isinstance(raw.get("rule_cases"), list) else []
            raw_f.write(json.dumps({
                "section_node_id": section_id,
                "raw": raw,
                "node_pool_size": len(node_pool),
                "model": model,
                "mode": mode,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }, ensure_ascii=False) + "\n")

            processed_sections += 1
            section_text = relation_section_text(section)
            node_pool_ids = {node.get("node_id") for node in node_pool}
            kept = 0
            warning_rows = 0
            for index, raw_case in enumerate(raw_cases, start=1):
                if not isinstance(raw_case, dict):
                    warn_f.write(json.dumps({
                        "section_node_id": section_id,
                        "candidate_index": index,
                        "warnings": ["raw_rule_case_item_not_object"],
                    }, ensure_ascii=False) + "\n")
                    warning_counts["raw_rule_case_item_not_object"] = warning_counts.get("raw_rule_case_item_not_object", 0) + 1
                    continue
                total_raw += 1
                row = normalize_rule_case(raw_case, section, node_by_id, index, model, mode)
                warnings = validate_rule_case(row, section_text, node_pool_ids)
                if row["rule_case_id"] in seen_ids:
                    warnings.append("duplicate_rule_case_candidate")
                    status = "reject"
                else:
                    status = decide_status(warnings)
                row["review_status"] = status
                row["validation_warnings"] = warnings
                status_counts[status] = status_counts.get(status, 0) + 1
                for warning in warnings:
                    warning_counts[warning] = warning_counts.get(warning, 0) + 1
                if warnings:
                    warning_rows += 1
                    warn_f.write(json.dumps({
                        "section_node_id": section_id,
                        "rule_case_id": row["rule_case_id"],
                        "owner_name": row["owner_name"],
                        "case_name": row["case_name"],
                        "review_status": status,
                        "warnings": warnings,
                    }, ensure_ascii=False) + "\n")
                if status in {"auto_accept", "review"} or args.keep_rejected_candidates:
                    cases_f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    seen_ids.add(row["rule_case_id"])
                    kept += 1
                if status == "review":
                    review_f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"[OK] {section_id} mode={mode} elapsed={elapsed:.1f}s pool={len(node_pool)} raw_cases={len(raw_cases)} kept={kept} warnings={warning_rows}")

    write_report(args.report, processed_sections, total_raw, status_counts, warning_counts)
    if processed_sections == 0 and llm_failed_sections:
        print(f"[WARN] Step 4B produced no rule cases for this chunk: llm_failed_sections={llm_failed_sections}")
    print(f"[OK] raw -> {args.raw_output}")
    print(f"[OK] rule cases -> {args.rule_cases}")
    print(f"[OK] review -> {args.review}")
    print(f"[OK] warnings -> {args.warnings}")
    print(f"[OK] report -> {args.report}")


if __name__ == "__main__":
    main()
