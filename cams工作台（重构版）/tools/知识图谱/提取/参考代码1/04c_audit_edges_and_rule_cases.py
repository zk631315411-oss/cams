"""
v4.4 Step 4C: LLM audit for ordinary edges and rule cases.

Step 4A/4B extract candidate edges and rule cases. This step performs a
full-section audit over both kinds of candidates. Accepted candidates are written
to the formal Step 5 inputs; questionable candidates are written to review
queues for Step 7. It does not rewrite, merge, or create candidates.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
MODULE_DIR = SCRIPT_DIR.parents[1]
DEFAULT_CONFIG = SCRIPT_DIR / "v4_3_config.json"
DEFAULT_PROMPT = SCRIPT_DIR / "prompts" / "edge_rule_case_audit.md"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "中间产物"
DEFAULT_LEAF_SECTIONS = DEFAULT_OUTPUT_DIR / "leaf_sections.jsonl"
DEFAULT_EDGES_IN = DEFAULT_OUTPUT_DIR / "edges_pre_audit.jsonl"
DEFAULT_RULE_CASES_IN = DEFAULT_OUTPUT_DIR / "rule_cases_pre_audit.jsonl"
DEFAULT_RAW_OUTPUT = DEFAULT_OUTPUT_DIR / "raw_edge_rule_case_audit.jsonl"
DEFAULT_DECISIONS = DEFAULT_OUTPUT_DIR / "edge_rule_case_audit_decisions.jsonl"
DEFAULT_EDGES_OUT = DEFAULT_OUTPUT_DIR / "edges.jsonl"
DEFAULT_EDGE_REVIEW = DEFAULT_OUTPUT_DIR / "edge_review_queue.jsonl"
DEFAULT_RULE_CASES_OUT = DEFAULT_OUTPUT_DIR / "rule_cases.jsonl"
DEFAULT_RULE_CASE_REVIEW = DEFAULT_OUTPUT_DIR / "rule_case_review_queue.jsonl"
DEFAULT_WARNINGS = DEFAULT_OUTPUT_DIR / "edge_rule_case_audit_warnings.jsonl"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "edge_rule_case_audit_report.md"
ENV_PATHS = [REPO_ROOT / ".env", MODULE_DIR / ".env"]

VALID_DECISIONS = {"accept", "review"}
EDGE_LOCAL_HARD_BLOCK_WARNING_PREFIXES = (
    "source_not_in_node_pool:",
    "target_not_in_node_pool:",
    "invalid_edge_type:",
    "forbidden_edge_type:",
    "example_forbidden_edge_type:",
    "uses_invalid_source_type:",
    "uses_invalid_target_type:",
    "uses_method_target_invalid_source_type:",
    "gets_invalid_source_type:",
    "gets_invalid_target_type:",
    "derives_invalid_source_type:",
    "derives_invalid_target_type:",
    "superior_invalid_type_pair:",
    "equative_invalid_type_pair:",
    "part_of_invalid_type_pair:",
    "has_property_invalid_type_pair:",
    "evidence_span_not_in_section:",
    "empty_evidence_span:",
    "evidence_span_contains_ellipsis:",
    "weak_evidence_span:",
    "derives_naming_statement:",
    "equative_naming_statement:",
)
EDGE_LOCAL_HARD_BLOCK_WARNING_EXACT = {
    "self_loop",
    "missing_evidence_spans",
    "confidence_below_reject_threshold",
}
RULE_CASE_LOCAL_HARD_BLOCK_WARNING_PREFIXES = (
    "owner_not_in_node_pool:",
    "owner_invalid_type:",
)
RULE_CASE_LOCAL_HARD_BLOCK_WARNING_EXACT = {
    "missing_case_name",
    "missing_conditions",
    "missing_outcomes",
    "missing_evidence_span",
    "evidence_span_not_in_section",
    "evidence_span_contains_ellipsis",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit v4.4 edge and rule case candidates.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--leaf-sections", type=Path, default=DEFAULT_LEAF_SECTIONS)
    parser.add_argument("--edges-in", type=Path, default=DEFAULT_EDGES_IN)
    parser.add_argument("--rule-cases-in", type=Path, default=DEFAULT_RULE_CASES_IN)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW_OUTPUT)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--edges-out", type=Path, default=DEFAULT_EDGES_OUT)
    parser.add_argument("--edge-review", type=Path, default=DEFAULT_EDGE_REVIEW)
    parser.add_argument("--rule-cases-out", type=Path, default=DEFAULT_RULE_CASES_OUT)
    parser.add_argument("--rule-case-review", type=Path, default=DEFAULT_RULE_CASE_REVIEW)
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
    parser.add_argument("--append", action="store_true")
    return parser.parse_args()


def read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


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


def read_jsonl(path: Path, required: bool = True) -> list[dict[str, Any]]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"JSONL not found: {path}")
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


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


def compact_edge(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": edge.get("candidate_id", ""),
        "edge_id": edge.get("edge_id", ""),
        "source_node_id": edge.get("source_node_id", ""),
        "source_name": edge.get("source_name", ""),
        "source_type": edge.get("source_type", ""),
        "source_review_status": edge.get("source_review_status", ""),
        "target_node_id": edge.get("target_node_id", ""),
        "target_name": edge.get("target_name", ""),
        "target_type": edge.get("target_type", ""),
        "target_review_status": edge.get("target_review_status", ""),
        "type": edge.get("type", ""),
        "evidence_span": edge.get("evidence_span", ""),
        "evidence_spans": edge.get("evidence_spans", []),
        "description": edge.get("description", ""),
        "confidence": edge.get("confidence", 0),
        "pre_audit_review_status": edge.get("review_status", ""),
        "validation_warnings": edge.get("validation_warnings", []),
        "review_recommended": edge.get("review_recommended", False),
        "review_reason": edge.get("review_reason", ""),
    }


def compact_rule_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "rule_case_id": case.get("rule_case_id", ""),
        "owner_node_id": case.get("owner_node_id", ""),
        "owner_name": case.get("owner_name", ""),
        "owner_type": case.get("owner_type", ""),
        "case_name": case.get("case_name", ""),
        "applies_to": case.get("applies_to", ""),
        "conditions": case.get("conditions", []),
        "condition_logic": case.get("condition_logic", ""),
        "outcomes": case.get("outcomes", []),
        "formula_refs": case.get("formula_refs", []),
        "evidence_span": case.get("evidence_span", ""),
        "source_label": case.get("source_label", ""),
        "reason": case.get("reason", ""),
        "confidence": case.get("confidence", 0),
        "pre_audit_review_status": case.get("review_status", ""),
        "validation_warnings": case.get("validation_warnings", []),
        "review_recommended": case.get("review_recommended", False),
        "review_reason": case.get("review_reason", ""),
    }


def build_payload(section: dict[str, Any], edges: list[dict[str, Any]], rule_cases: list[dict[str, Any]]) -> dict[str, Any]:
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
        "section_text": section.get("text", ""),
        "edge_candidates": [compact_edge(edge) for edge in edges],
        "rule_case_candidates": [compact_rule_case(case) for case in rule_cases],
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
            {"role": "user", "content": prompt + "\n\n## 当前复核输入\n\n" + json.dumps(payload, ensure_ascii=False)},
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
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_body = json.loads(response.read().decode("utf-8"))
            content = response_body.get("choices", [{}])[0].get("message", {}).get("content") or "{}"
            return parse_llm_json(content)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM HTTP {exc.code}: {body[:1000]}") from exc
        except urllib.error.URLError as exc:
            last_error = RuntimeError(f"LLM request failed: {exc}")
        except RuntimeError as exc:
            last_error = exc
        if attempt < 3:
            time.sleep(1.5 * attempt)
    assert last_error is not None
    raise last_error


def mock_audit(edges: list[dict[str, Any]], rule_cases: list[dict[str, Any]]) -> dict[str, Any]:
    edge_decisions = []
    for edge in edges:
        suspicious = bool(edge.get("validation_warnings")) or bool(edge.get("review_recommended")) or edge.get("review_status") != "auto_accept"
        edge_decisions.append(
            {
                "edge_id": edge.get("edge_id", ""),
                "candidate_id": edge.get("candidate_id", ""),
                "decision": "review" if suspicious else "accept",
                "issues": ["mock_suspicious_edge"] if suspicious else [],
                "reason": "Mock audit marks pre-audit warnings for review." if suspicious else "Mock audit accepts clean edge.",
                "confidence": 0.8,
            }
        )
    rule_case_decisions = []
    for case in rule_cases:
        suspicious = bool(case.get("validation_warnings")) or bool(case.get("review_recommended")) or case.get("review_status") != "auto_accept"
        rule_case_decisions.append(
            {
                "rule_case_id": case.get("rule_case_id", ""),
                "decision": "review" if suspicious else "accept",
                "issues": ["mock_suspicious_rule_case"] if suspicious else [],
                "reason": "Mock audit marks pre-audit warnings for review." if suspicious else "Mock audit accepts clean rule case.",
                "confidence": 0.8,
            }
        )
    return {"edge_decisions": edge_decisions, "rule_case_decisions": rule_case_decisions}


def coerce_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def normalize_decision(item: dict[str, Any], id_key: str) -> dict[str, Any]:
    decision = str(item.get("decision") or "").strip()
    if decision not in VALID_DECISIONS:
        decision = "review"
    issues = item.get("issues") if isinstance(item.get("issues"), list) else []
    return {
        id_key: str(item.get(id_key) or ""),
        "candidate_id": str(item.get("candidate_id") or ""),
        "decision": decision,
        "issues": [str(issue).strip() for issue in issues if str(issue).strip()],
        "reason": str(item.get("reason") or "").strip(),
        "confidence": coerce_confidence(item.get("confidence", 0.0)),
    }


def decision_maps(raw: dict[str, Any], edges: list[dict[str, Any]], rule_cases: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    edge_ids = {str(edge.get("edge_id") or "") for edge in edges}
    candidate_ids = {str(edge.get("candidate_id") or "") for edge in edges}
    rule_case_ids = {str(case.get("rule_case_id") or "") for case in rule_cases}
    edge_map: dict[str, dict[str, Any]] = {}
    rule_case_map: dict[str, dict[str, Any]] = {}

    for index, item in enumerate(raw.get("edge_decisions") if isinstance(raw.get("edge_decisions"), list) else [], start=1):
        if not isinstance(item, dict):
            warnings.append({"warning": "edge_decision_item_not_object", "index": index})
            continue
        decision = normalize_decision(item, "edge_id")
        edge_id = decision["edge_id"]
        candidate_id = decision["candidate_id"]
        if edge_id and edge_id not in edge_ids:
            warnings.append({"warning": "edge_decision_id_not_in_input", "index": index, "edge_id": edge_id})
            continue
        if candidate_id and candidate_id not in candidate_ids:
            warnings.append({"warning": "edge_decision_candidate_not_in_input", "index": index, "candidate_id": candidate_id})
        key = edge_id or candidate_id
        if not key:
            warnings.append({"warning": "edge_decision_missing_id", "index": index})
            continue
        edge_map[key] = decision

    for index, item in enumerate(raw.get("rule_case_decisions") if isinstance(raw.get("rule_case_decisions"), list) else [], start=1):
        if not isinstance(item, dict):
            warnings.append({"warning": "rule_case_decision_item_not_object", "index": index})
            continue
        decision = normalize_decision(item, "rule_case_id")
        rule_case_id = decision["rule_case_id"]
        if rule_case_id and rule_case_id not in rule_case_ids:
            warnings.append({"warning": "rule_case_decision_id_not_in_input", "index": index, "rule_case_id": rule_case_id})
            continue
        if not rule_case_id:
            warnings.append({"warning": "rule_case_decision_missing_id", "index": index})
            continue
        rule_case_map[rule_case_id] = decision

    return edge_map, rule_case_map, warnings


def edge_decision_for(edge: dict[str, Any], decisions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    edge_id = str(edge.get("edge_id") or "")
    candidate_id = str(edge.get("candidate_id") or "")
    return decisions.get(edge_id) or decisions.get(candidate_id) or {
        "edge_id": edge_id,
        "candidate_id": candidate_id,
        "decision": "review",
        "issues": ["missing_edge_audit_decision"],
        "reason": "AI 复核未返回该边的决策，按保守策略进入 Step 7 复核。",
        "confidence": 0.0,
    }


def rule_case_decision_for(case: dict[str, Any], decisions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rule_case_id = str(case.get("rule_case_id") or "")
    return decisions.get(rule_case_id) or {
        "rule_case_id": rule_case_id,
        "decision": "review",
        "issues": ["missing_rule_case_audit_decision"],
        "reason": "AI 复核未返回该规则案例的决策，按保守策略进入 Step 7 复核。",
        "confidence": 0.0,
    }


def has_local_hard_block(item: dict[str, Any], prefix: str) -> bool:
    warnings = [str(warning) for warning in (item.get("validation_warnings") or [])]
    if prefix == "edge":
        warning_prefixes = EDGE_LOCAL_HARD_BLOCK_WARNING_PREFIXES
        warning_exact = EDGE_LOCAL_HARD_BLOCK_WARNING_EXACT
    else:
        warning_prefixes = RULE_CASE_LOCAL_HARD_BLOCK_WARNING_PREFIXES
        warning_exact = RULE_CASE_LOCAL_HARD_BLOCK_WARNING_EXACT
    return (
        item.get("review_status") == "reject"
        or any(warning.startswith(warning_prefixes) for warning in warnings)
        or any(warning in warning_exact for warning in warnings)
    )


def apply_audit(item: dict[str, Any], decision: dict[str, Any], model: str, mode: str, prefix: str) -> dict[str, Any]:
    audited = dict(item)
    original_decision = str(decision.get("decision") or "review")
    effective_decision = original_decision
    override_reason = ""
    if original_decision == "accept" and has_local_hard_block(audited, prefix):
        effective_decision = "review"
        override_reason = "local_hard_reject_blocks_accept"

    audited[f"{prefix}_audit_original_decision"] = original_decision
    audited[f"{prefix}_audit_decision"] = effective_decision
    issues = list(decision.get("issues", []) or [])
    if override_reason and override_reason not in issues:
        issues.append(override_reason)
    audited[f"{prefix}_audit_issues"] = issues
    audited[f"{prefix}_audit_reason"] = decision.get("reason", "")
    audited[f"{prefix}_audit_confidence"] = decision.get("confidence", 0.0)
    audited[f"{prefix}_audit_model"] = model
    audited[f"{prefix}_audit_mode"] = mode
    audited[f"{prefix}_audit_at"] = datetime.now().isoformat(timespec="seconds")
    audited[f"pre_{prefix}_audit_review_status"] = audited.get("review_status", "")
    audited[f"{prefix}_audit_decision_overridden"] = bool(override_reason)
    audited[f"{prefix}_audit_override_reason"] = override_reason

    if effective_decision == "accept":
        audited["review_status"] = "auto_accept"
        audited["review_reason"] = ""
    else:
        audited["review_status"] = "review"
        reason = str(decision.get("reason") or "").strip() or "AI 复核认为该候选需要进入 Step 7 复核。"
        if override_reason:
            reason = f"本地硬规则标记为不可自动准入，AI 不能直接升级为 accept；原 AI 判断：{reason}"
        existing = str(audited.get("review_reason") or "").strip()
        audited["review_reason"] = f"{existing}；Step 4C AI复核：{reason}" if existing else f"Step 4C AI复核：{reason}"
        warnings = list(audited.get("validation_warnings") or [])
        warning = f"{prefix}_audit_review"
        if warning not in warnings:
            warnings.append(warning)
        if override_reason and override_reason not in warnings:
            warnings.append(override_reason)
        audited["validation_warnings"] = warnings
    return audited


def write_report(path: Path, processed_sections: int, edge_counts: Counter[str], rule_case_counts: Counter[str], warning_counts: Counter[str], model: str, mock: bool) -> None:
    lines = [
        "# v4.4 Step 4C Edge and Rule Case Audit Report",
        "",
        f"- processed sections: {processed_sections}",
        f"- model: {model}",
        f"- mock: {mock}",
        "",
        "## Edge Decisions",
    ]
    for key, value in sorted(edge_counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Rule Case Decisions"])
    for key, value in sorted(rule_case_counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Warnings"])
    if warning_counts:
        for key, value in sorted(warning_counts.items(), key=lambda item: (-item[1], item[0]))[:30]:
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    sections = select_sections(read_jsonl(args.leaf_sections), config, args)
    edges = read_jsonl(args.edges_in, required=False)
    rule_cases = read_jsonl(args.rule_cases_in, required=False)
    edges_by_section: dict[str, list[dict[str, Any]]] = {}
    rule_cases_by_section: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        edges_by_section.setdefault(str(edge.get("section_node_id") or ""), []).append(edge)
    for case in rule_cases:
        rule_cases_by_section.setdefault(str(case.get("section_node_id") or ""), []).append(case)

    prompt = args.prompt.read_text(encoding="utf-8")
    llm_config = config.get("llm", {})
    model = args.model or llm_config.get("high_risk_model") or llm_config.get("default_model", "deepseek-chat")
    base_url = args.base_url or load_env_value("LLM_API_BASE") or llm_config.get("base_url", "https://api.openai.com/v1")
    temperature = args.temperature if args.temperature is not None else float(llm_config.get("temperature", 0.0))
    timeout = args.timeout if args.timeout is not None else float(llm_config.get("timeout_seconds", 120))

    api_key = ""
    if not args.mock:
        api_key = load_env_value("LLM_API_KEY") or load_env_value("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("LLM_API_KEY not found. Use --mock for local validation.")

    print(f"[INFO] sections={len(sections)} edges_in={len(edges)} rule_cases_in={len(rule_cases)} model={model} mock={args.mock}")
    processed_sections = 0
    edge_counts: Counter[str] = Counter()
    rule_case_counts: Counter[str] = Counter()
    warning_counts: Counter[str] = Counter()

    with (
        open_output(args.raw_output, args.append) as raw_f,
        open_output(args.decisions, args.append) as decisions_f,
        open_output(args.edges_out, args.append) as edges_f,
        open_output(args.edge_review, args.append) as edge_review_f,
        open_output(args.rule_cases_out, args.append) as rule_cases_f,
        open_output(args.rule_case_review, args.append) as rule_case_review_f,
        open_output(args.warnings, args.append) as warn_f,
    ):
        for section in sections:
            section_id = str(section.get("section_node_id") or "")
            section_edges = edges_by_section.get(section_id, [])
            section_rule_cases = rule_cases_by_section.get(section_id, [])
            if not section_edges and not section_rule_cases:
                continue

            started = time.time()
            mode = "mock" if args.mock else "llm"
            if args.mock:
                raw = mock_audit(section_edges, section_rule_cases)
            else:
                payload = build_payload(section, section_edges, section_rule_cases)
                try:
                    raw = call_llm(api_key, base_url, model, prompt, payload, temperature, timeout)
                except Exception as exc:  # noqa: BLE001 - audit failure should become review, not silent acceptance.
                    raw = {
                        "edge_decisions": [
                            {
                                "edge_id": edge.get("edge_id", ""),
                                "candidate_id": edge.get("candidate_id", ""),
                                "decision": "review",
                                "issues": ["edge_audit_call_failed"],
                                "reason": f"AI 复核调用失败，按保守策略进入 Step 7 复核：{str(exc)[:300]}",
                                "confidence": 0.0,
                            }
                            for edge in section_edges
                        ],
                        "rule_case_decisions": [
                            {
                                "rule_case_id": case.get("rule_case_id", ""),
                                "decision": "review",
                                "issues": ["rule_case_audit_call_failed"],
                                "reason": f"AI 复核调用失败，按保守策略进入 Step 7 复核：{str(exc)[:300]}",
                                "confidence": 0.0,
                            }
                            for case in section_rule_cases
                        ],
                    }
                    warning_counts["audit_call_failed"] += 1
                    warn_f.write(json.dumps({"section_node_id": section_id, "warnings": ["audit_call_failed"], "error": str(exc)[:1000]}, ensure_ascii=False) + "\n")

            elapsed = time.time() - started
            raw_f.write(json.dumps({
                "section_node_id": section_id,
                "edge_count": len(section_edges),
                "rule_case_count": len(section_rule_cases),
                "raw": raw,
                "model": model,
                "mode": mode,
                "elapsed_seconds": round(elapsed, 3),
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }, ensure_ascii=False) + "\n")

            edge_map, rule_case_map, decision_warnings = decision_maps(raw, section_edges, section_rule_cases)
            for warning in decision_warnings:
                warning["section_node_id"] = section_id
                warn_f.write(json.dumps(warning, ensure_ascii=False) + "\n")
                warning_counts[str(warning.get("warning") or "unknown_warning")] += 1

            accepted_edges = 0
            review_edges = 0
            for edge in section_edges:
                decision = edge_decision_for(edge, edge_map)
                audited = apply_audit(edge, decision, model, mode, "edge")
                edge_counts[str(audited.get("edge_audit_decision") or "review")] += 1
                decisions_f.write(json.dumps({
                    "item_kind": "edge",
                    "section_node_id": section_id,
                    "edge_id": audited.get("edge_id", ""),
                    "candidate_id": audited.get("candidate_id", ""),
                    "source_name": audited.get("source_name", ""),
                    "target_name": audited.get("target_name", ""),
                    "type": audited.get("type", ""),
                    "decision": audited.get("edge_audit_decision", "review"),
                    "original_decision": audited.get("edge_audit_original_decision", decision.get("decision", "review")),
                    "decision_overridden": audited.get("edge_audit_decision_overridden", False),
                    "override_reason": audited.get("edge_audit_override_reason", ""),
                    "issues": audited.get("edge_audit_issues", []),
                    "reason": decision.get("reason", ""),
                    "confidence": decision.get("confidence", 0.0),
                    "model": model,
                    "mode": mode,
                    "generated_at": audited.get("edge_audit_at", ""),
                }, ensure_ascii=False) + "\n")
                if audited.get("review_status") == "auto_accept":
                    edges_f.write(json.dumps(audited, ensure_ascii=False) + "\n")
                    accepted_edges += 1
                else:
                    edge_review_f.write(json.dumps(audited, ensure_ascii=False) + "\n")
                    review_edges += 1
                    warning_counts["edge_audit_review"] += 1

            accepted_cases = 0
            review_cases = 0
            for case in section_rule_cases:
                decision = rule_case_decision_for(case, rule_case_map)
                audited = apply_audit(case, decision, model, mode, "rule_case")
                rule_case_counts[str(audited.get("rule_case_audit_decision") or "review")] += 1
                decisions_f.write(json.dumps({
                    "item_kind": "rule_case",
                    "section_node_id": section_id,
                    "rule_case_id": audited.get("rule_case_id", ""),
                    "owner_name": audited.get("owner_name", ""),
                    "case_name": audited.get("case_name", ""),
                    "decision": audited.get("rule_case_audit_decision", "review"),
                    "original_decision": audited.get("rule_case_audit_original_decision", decision.get("decision", "review")),
                    "decision_overridden": audited.get("rule_case_audit_decision_overridden", False),
                    "override_reason": audited.get("rule_case_audit_override_reason", ""),
                    "issues": audited.get("rule_case_audit_issues", []),
                    "reason": decision.get("reason", ""),
                    "confidence": decision.get("confidence", 0.0),
                    "model": model,
                    "mode": mode,
                    "generated_at": audited.get("rule_case_audit_at", ""),
                }, ensure_ascii=False) + "\n")
                if audited.get("review_status") == "auto_accept":
                    rule_cases_f.write(json.dumps(audited, ensure_ascii=False) + "\n")
                    accepted_cases += 1
                else:
                    rule_case_review_f.write(json.dumps(audited, ensure_ascii=False) + "\n")
                    review_cases += 1
                    warning_counts["rule_case_audit_review"] += 1

            processed_sections += 1
            print(
                f"[OK] {section_id} mode={mode} elapsed={elapsed:.1f}s "
                f"edges={len(section_edges)} accept/review={accepted_edges}/{review_edges} "
                f"rule_cases={len(section_rule_cases)} accept/review={accepted_cases}/{review_cases}"
            )

    write_report(args.report, processed_sections, edge_counts, rule_case_counts, warning_counts, model, args.mock)
    print(f"[OK] raw -> {args.raw_output}")
    print(f"[OK] decisions -> {args.decisions}")
    print(f"[OK] edges -> {args.edges_out}")
    print(f"[OK] edge review -> {args.edge_review}")
    print(f"[OK] rule cases -> {args.rule_cases_out}")
    print(f"[OK] rule case review -> {args.rule_case_review}")
    print(f"[OK] warnings -> {args.warnings}")
    print(f"[OK] report -> {args.report}")


if __name__ == "__main__":
    main()
