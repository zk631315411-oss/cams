"""
v4.4 Step 3A: LLM audit for explicit node candidates.

Step 3 extracts explicit node candidates. This step performs a full-section
audit over those candidates and decides which nodes are admitted for Step 4.
It does not rewrite nodes, merge synonyms, create edges, or create rule cases.
Nodes accepted here are written to nodes.jsonl; nodes judged questionable are
written to node_review_queue.jsonl for Step 7 review. Both accepted and review
nodes are also written to nodes_for_step4.jsonl so relation extraction can see
the full local context and avoid losing edges around review nodes.
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
DEFAULT_PROMPT = SCRIPT_DIR / "prompts" / "explicit_node_audit.md"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "中间产物"
DEFAULT_LEAF_SECTIONS = DEFAULT_OUTPUT_DIR / "leaf_sections.jsonl"
DEFAULT_NODES_IN = DEFAULT_OUTPUT_DIR / "nodes_pre_audit.jsonl"
DEFAULT_RAW_OUTPUT = DEFAULT_OUTPUT_DIR / "raw_node_audit.jsonl"
DEFAULT_DECISIONS = DEFAULT_OUTPUT_DIR / "node_audit_decisions.jsonl"
DEFAULT_NODES_OUT = DEFAULT_OUTPUT_DIR / "nodes.jsonl"
DEFAULT_NODES_FOR_STEP4 = DEFAULT_OUTPUT_DIR / "nodes_for_step4.jsonl"
DEFAULT_REVIEW = DEFAULT_OUTPUT_DIR / "node_review_queue.jsonl"
DEFAULT_WARNINGS = DEFAULT_OUTPUT_DIR / "node_audit_warnings.jsonl"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "node_audit_report.md"
ENV_PATHS = [REPO_ROOT / ".env", MODULE_DIR / ".env"]

VALID_DECISIONS = {"accept", "review"}
LOCAL_HARD_BLOCK_WARNING_PREFIXES = (
    "invalid_node_type:",
    "forbidden_node_type:",
    "example_forbidden_node_type:",
)
LOCAL_HARD_BLOCK_WARNING_EXACT = {
    "missing_name",
    "numbered_name",
    "missing_evidence_span",
    "evidence_span_not_in_section",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit v4.4 explicit node candidates.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--leaf-sections", type=Path, default=DEFAULT_LEAF_SECTIONS)
    parser.add_argument("--nodes-in", type=Path, default=DEFAULT_NODES_IN)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW_OUTPUT)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--nodes-out", type=Path, default=DEFAULT_NODES_OUT)
    parser.add_argument("--nodes-for-step4", type=Path, default=DEFAULT_NODES_FOR_STEP4)
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
    parser.add_argument("--append", action="store_true")
    return parser.parse_args()


def read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}. Run 00_prepare_config.py first.")
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
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
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


def compact_node(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": node.get("candidate_id", ""),
        "node_id": node.get("node_id", ""),
        "name": node.get("name", ""),
        "type": node.get("type", ""),
        "aliases": node.get("aliases", [])[:8],
        "source_label": node.get("source_label", ""),
        "definition": node.get("definition", ""),
        "description": node.get("description", ""),
        "attributes": node.get("attributes", []),
        "state_notes": node.get("state_notes", []),
        "evidence_span": node.get("evidence_span", ""),
        "confidence": node.get("confidence", 0),
        "reason": node.get("reason", ""),
        "review_recommended": node.get("review_recommended", False),
        "review_reason": node.get("review_reason", ""),
        "pre_audit_review_status": node.get("review_status", ""),
        "validation_warnings": node.get("validation_warnings", []),
    }


def build_payload(section: dict[str, Any], nodes: list[dict[str, Any]]) -> dict[str, Any]:
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
        "extracted_nodes": [compact_node(node) for node in nodes],
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


def mock_audit(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    for node in nodes:
        warnings = node.get("validation_warnings") or []
        name = str(node.get("name") or "")
        suspicious = bool(warnings) or bool(node.get("review_recommended")) or re.match(r"^(定理|定义|公式|命题|推论)\s*\d+$", name)
        decisions.append(
            {
                "candidate_id": node.get("candidate_id", ""),
                "node_id": node.get("node_id", ""),
                "decision": "review" if suspicious else "accept",
                "issues": ["mock_suspicious_node"] if suspicious else [],
                "reason": "Mock audit marks pre-audit warnings for review." if suspicious else "Mock audit accepts clean node.",
                "confidence": 0.8,
            }
        )
    return {"decisions": decisions}


def coerce_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def normalize_decisions(raw: dict[str, Any], nodes: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    raw_decisions = raw.get("decisions") if isinstance(raw.get("decisions"), list) else []
    by_candidate: dict[str, dict[str, Any]] = {}
    node_ids = {str(node.get("node_id") or "") for node in nodes}
    candidate_ids = {str(node.get("candidate_id") or "") for node in nodes}

    for index, item in enumerate(raw_decisions, start=1):
        if not isinstance(item, dict):
            warnings.append({"warning": "decision_item_not_object", "index": index})
            continue
        candidate_id = str(item.get("candidate_id") or "")
        node_id = str(item.get("node_id") or "")
        decision = str(item.get("decision") or "").strip()
        if decision not in VALID_DECISIONS:
            warnings.append({"warning": "invalid_decision", "index": index, "candidate_id": candidate_id, "decision": decision})
            decision = "review"
        if candidate_id and candidate_id not in candidate_ids:
            warnings.append({"warning": "decision_candidate_not_in_input", "index": index, "candidate_id": candidate_id})
            continue
        if node_id and node_id not in node_ids:
            warnings.append({"warning": "decision_node_not_in_input", "index": index, "node_id": node_id})
        key = candidate_id or node_id
        if not key:
            warnings.append({"warning": "decision_missing_ids", "index": index})
            continue
        if key in by_candidate:
            warnings.append({"warning": "duplicate_decision", "index": index, "candidate_id": candidate_id, "node_id": node_id})
            continue
        issues = item.get("issues") if isinstance(item.get("issues"), list) else []
        by_candidate[key] = {
            "candidate_id": candidate_id,
            "node_id": node_id,
            "decision": decision,
            "issues": [str(issue).strip() for issue in issues if str(issue).strip()],
            "reason": str(item.get("reason") or "").strip(),
            "confidence": coerce_confidence(item.get("confidence", 0.0)),
        }

    return by_candidate, warnings


def decision_for_node(node: dict[str, Any], decisions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    candidate_id = str(node.get("candidate_id") or "")
    node_id = str(node.get("node_id") or "")
    decision = decisions.get(candidate_id) or decisions.get(node_id)
    if decision:
        return decision
    return {
        "candidate_id": candidate_id,
        "node_id": node_id,
        "decision": "review",
        "issues": ["missing_audit_decision"],
        "reason": "AI 复核未返回该节点的决策，按保守策略进入 Step 7 复核。",
        "confidence": 0.0,
    }


def has_local_hard_block(node: dict[str, Any]) -> bool:
    warnings = [str(warning) for warning in (node.get("validation_warnings") or [])]
    return (
        node.get("review_status") == "reject"
        or any(warning.startswith(LOCAL_HARD_BLOCK_WARNING_PREFIXES) for warning in warnings)
        or any(warning in LOCAL_HARD_BLOCK_WARNING_EXACT for warning in warnings)
    )


def apply_decision(node: dict[str, Any], decision: dict[str, Any], model: str, mode: str) -> dict[str, Any]:
    audited = dict(node)
    pre_status = audited.get("review_status", "")
    pre_warnings = list(audited.get("validation_warnings") or [])
    original_decision = str(decision.get("decision") or "review")
    effective_decision = original_decision
    override_reason = ""
    if original_decision == "accept" and has_local_hard_block(audited):
        effective_decision = "review"
        override_reason = "local_hard_reject_blocks_accept"

    audited["pre_audit_review_status"] = pre_status
    audited["pre_audit_validation_warnings"] = pre_warnings
    audited["node_audit_original_decision"] = original_decision
    audited["node_audit_decision"] = effective_decision
    issues = list(decision.get("issues", []) or [])
    if override_reason and override_reason not in issues:
        issues.append(override_reason)
    audited["node_audit_issues"] = issues
    audited["node_audit_reason"] = decision.get("reason", "")
    audited["node_audit_confidence"] = decision.get("confidence", 0.0)
    audited["node_audit_model"] = model
    audited["node_audit_mode"] = mode
    audited["node_audit_at"] = datetime.now().isoformat(timespec="seconds")
    audited["node_audit_decision_overridden"] = bool(override_reason)
    audited["node_audit_override_reason"] = override_reason

    if effective_decision == "accept":
        audited["review_status"] = "auto_accept"
        audited["review_reason"] = ""
    else:
        audited["review_status"] = "review"
        reason = str(decision.get("reason") or "").strip() or "AI 复核认为该节点需要进入 Step 7 复核。"
        if override_reason:
            reason = f"本地硬规则标记为不可自动准入，AI 不能直接升级为 accept；原 AI 判断：{reason}"
        existing = str(audited.get("review_reason") or "").strip()
        audited["review_reason"] = f"{existing}；Step 3A AI复核：{reason}" if existing else f"Step 3A AI复核：{reason}"
        warnings = list(audited.get("validation_warnings") or [])
        if "node_audit_review" not in warnings:
            warnings.append("node_audit_review")
        if override_reason and override_reason not in warnings:
            warnings.append(override_reason)
        audited["validation_warnings"] = warnings
    return audited


def write_report(
    path: Path,
    processed_sections: int,
    audited_nodes: int,
    status_counts: Counter[str],
    type_counts: Counter[str],
    warning_counts: Counter[str],
    model: str,
    mock: bool,
) -> None:
    lines = [
        "# v4.4 Step 3A Node Audit Report",
        "",
        f"- processed sections: {processed_sections}",
        f"- audited nodes: {audited_nodes}",
        f"- model: {model}",
        f"- mock: {mock}",
        "",
        "## Audit Decisions",
    ]
    for key, value in sorted(status_counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Accepted Node Types"])
    for key, value in sorted(type_counts.items()):
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
    nodes = read_jsonl(args.nodes_in)
    nodes_by_section: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        section_id = str(node.get("section_node_id") or "")
        nodes_by_section.setdefault(section_id, []).append(node)

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

    print(f"[INFO] sections={len(sections)} nodes_in={len(nodes)} model={model} mock={args.mock}")
    processed_sections = 0
    audited_nodes = 0
    status_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    warning_counts: Counter[str] = Counter()

    with (
        open_output(args.raw_output, args.append) as raw_f,
        open_output(args.decisions, args.append) as decisions_f,
        open_output(args.nodes_out, args.append) as nodes_f,
        open_output(args.nodes_for_step4, args.append) as step4_nodes_f,
        open_output(args.review, args.append) as review_f,
        open_output(args.warnings, args.append) as warn_f,
    ):
        for section in sections:
            section_id = str(section.get("section_node_id") or "")
            section_nodes = nodes_by_section.get(section_id, [])
            if not section_nodes:
                continue

            started = time.time()
            mode = "mock" if args.mock else "llm"
            if args.mock:
                raw = mock_audit(section_nodes)
            else:
                payload = build_payload(section, section_nodes)
                try:
                    raw = call_llm(api_key, base_url, model, prompt, payload, temperature, timeout)
                except Exception as exc:  # noqa: BLE001 - audit failure should become review, not silent acceptance.
                    raw = {
                        "decisions": [
                            {
                                "candidate_id": node.get("candidate_id", ""),
                                "node_id": node.get("node_id", ""),
                                "decision": "review",
                                "issues": ["node_audit_call_failed"],
                                "reason": f"AI 复核调用失败，按保守策略进入 Step 7 复核：{str(exc)[:300]}",
                                "confidence": 0.0,
                            }
                            for node in section_nodes
                        ]
                    }
                    warning_counts["node_audit_call_failed"] += 1
                    warn_f.write(json.dumps({
                        "section_node_id": section_id,
                        "warnings": ["node_audit_call_failed"],
                        "error": str(exc)[:1000],
                    }, ensure_ascii=False) + "\n")

            elapsed = time.time() - started
            raw_f.write(json.dumps({
                "section_node_id": section_id,
                "node_count": len(section_nodes),
                "raw": raw,
                "model": model,
                "mode": mode,
                "elapsed_seconds": round(elapsed, 3),
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }, ensure_ascii=False) + "\n")

            decisions_by_id, decision_warnings = normalize_decisions(raw, section_nodes)
            for warning in decision_warnings:
                warning["section_node_id"] = section_id
                warn_f.write(json.dumps(warning, ensure_ascii=False) + "\n")
                warning_counts[str(warning.get("warning") or "unknown_warning")] += 1

            section_accept = 0
            section_review = 0
            processed_sections += 1
            for node in section_nodes:
                decision = decision_for_node(node, decisions_by_id)
                audited = apply_decision(node, decision, model, mode)
                step4_nodes_f.write(json.dumps(audited, ensure_ascii=False) + "\n")
                audited_nodes += 1
                status_counts[str(audited.get("node_audit_decision") or "review")] += 1
                if audited.get("review_status") == "auto_accept":
                    type_counts[str(audited.get("type") or "")] += 1
                    nodes_f.write(json.dumps(audited, ensure_ascii=False) + "\n")
                    section_accept += 1
                else:
                    review_f.write(json.dumps(audited, ensure_ascii=False) + "\n")
                    section_review += 1

                decision_row = {
                    "section_node_id": section_id,
                    "candidate_id": audited.get("candidate_id", ""),
                    "node_id": audited.get("node_id", ""),
                    "name": audited.get("name", ""),
                    "type": audited.get("type", ""),
                    "decision": audited.get("node_audit_decision", "review"),
                    "original_decision": audited.get("node_audit_original_decision", decision.get("decision", "review")),
                    "decision_overridden": audited.get("node_audit_decision_overridden", False),
                    "override_reason": audited.get("node_audit_override_reason", ""),
                    "issues": audited.get("node_audit_issues", []),
                    "reason": decision.get("reason", ""),
                    "confidence": decision.get("confidence", 0.0),
                    "pre_audit_review_status": audited.get("pre_audit_review_status", ""),
                    "model": model,
                    "mode": mode,
                    "generated_at": audited.get("node_audit_at", ""),
                }
                decisions_f.write(json.dumps(decision_row, ensure_ascii=False) + "\n")

                if audited.get("node_audit_decision") != "accept":
                    warn_f.write(json.dumps({
                        "section_node_id": section_id,
                        "candidate_id": audited.get("candidate_id", ""),
                        "node_id": audited.get("node_id", ""),
                        "name": audited.get("name", ""),
                        "warnings": ["node_audit_review", *list(audited.get("node_audit_issues") or [])],
                        "reason": decision.get("reason", ""),
                        "original_decision": audited.get("node_audit_original_decision", ""),
                        "decision_overridden": audited.get("node_audit_decision_overridden", False),
                        "override_reason": audited.get("node_audit_override_reason", ""),
                    }, ensure_ascii=False) + "\n")
                    warning_counts["node_audit_review"] += 1

            print(
                f"[OK] {section_id} mode={mode} elapsed={elapsed:.1f}s "
                f"nodes={len(section_nodes)} accept={section_accept} review={section_review}"
            )

    write_report(args.report, processed_sections, audited_nodes, status_counts, type_counts, warning_counts, model, args.mock)
    print(f"[OK] raw -> {args.raw_output}")
    print(f"[OK] decisions -> {args.decisions}")
    print(f"[OK] nodes -> {args.nodes_out}")
    print(f"[OK] nodes_for_step4 -> {args.nodes_for_step4}")
    print(f"[OK] review -> {args.review}")
    print(f"[OK] warnings -> {args.warnings}")
    print(f"[OK] report -> {args.report}")


if __name__ == "__main__":
    main()
