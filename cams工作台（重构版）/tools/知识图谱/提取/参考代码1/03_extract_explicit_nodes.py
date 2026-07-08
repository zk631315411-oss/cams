"""
v4.4 Step 3: extract explicit KG node candidates from section text.

Step 2 only provides a section overview and keywords for orientation. This
step must extract explicit nodes from the current leaf-section source text and
validate every candidate against that text. It does not extract relations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
DEFAULT_PROMPT = SCRIPT_DIR / "prompts" / "explicit_node_extraction.md"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "中间产物"
DEFAULT_LEAF_SECTIONS = DEFAULT_OUTPUT_DIR / "leaf_sections.jsonl"
DEFAULT_SUMMARIES = DEFAULT_OUTPUT_DIR / "section_summaries.jsonl"
DEFAULT_RAW_OUTPUT = DEFAULT_OUTPUT_DIR / "raw_explicit_node_candidates.jsonl"
DEFAULT_NODES = DEFAULT_OUTPUT_DIR / "nodes.jsonl"
DEFAULT_REVIEW = DEFAULT_OUTPUT_DIR / "node_review_queue.jsonl"
DEFAULT_WARNINGS = DEFAULT_OUTPUT_DIR / "node_extraction_warnings.jsonl"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "node_extraction_report.md"
ENV_PATHS = [REPO_ROOT / ".env", MODULE_DIR / ".env"]

VALID_NODE_TYPES = {"Concept", "Method", "Formula", "Theorem", "ProblemClass"}
FORBIDDEN_NODE_TYPES = {"Definition", "AttributeValue", "EvidenceOnly"}
EXAMPLE_ALLOWED_TYPES = {"Method", "ProblemClass"}
SUMMARY_LIST_FIELDS: tuple[str, ...] = ()
NUMBERED_NAME_RE = re.compile(
    r"^(定义|定理|命题|推论|引理|性质|公式|例|题)\s*[\(（]?[0-9一二三四五六七八九十]+[\)）]?$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract v4.3 explicit node candidates.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--leaf-sections", type=Path, default=DEFAULT_LEAF_SECTIONS)
    parser.add_argument("--summaries", type=Path, default=DEFAULT_SUMMARIES)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW_OUTPUT)
    parser.add_argument("--nodes", type=Path, default=DEFAULT_NODES)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--warnings", type=Path, default=DEFAULT_WARNINGS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--chunk-id", "--section-node-id", dest="section_node_id", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true", help="Process one eligible summary.")
    parser.add_argument("--mock", action="store_true", help="Generate deterministic local mock candidates.")
    parser.add_argument("--model", default="", help="Override model.")
    parser.add_argument("--base-url", default="", help="Override API base URL.")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("--append", action="store_true")
    parser.add_argument(
        "--keep-rejected-candidates",
        action="store_true",
        help="Write locally rejected structured candidates to --nodes so Step 3A can audit the full Step 3 output.",
    )
    return parser.parse_args()


def read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}. Run 00_prepare_config.py first.")
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


def select_summaries(
    summaries: list[dict[str, Any]],
    config: dict[str, Any],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    if args.section_node_id:
        selected = [s for s in summaries if s.get("section_node_id") == args.section_node_id]
        if not selected:
            raise ValueError(f"section_node_id not found in summaries: {args.section_node_id}")
        return selected

    skip_scopes = set(config.get("tree", {}).get("skip_source_scopes", ["exercise"]))
    eligible = [s for s in summaries if s.get("source_scope") not in skip_scopes]
    if args.dry_run:
        return eligible[:1]
    if args.limit > 0:
        return eligible[: args.limit]
    return eligible


def build_payload(section: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
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
            "anchors": [
                {
                    "anchor_id": a.get("anchor_id", ""),
                    "title": a.get("title", ""),
                    "anchor_type": a.get("anchor_type", ""),
                    "source_label": a.get("source_label", ""),
                }
                for a in section.get("anchors", [])
            ],
        },
        "section_text": section.get("text", ""),
        "section_summary": {
            "summary": summary.get("summary", ""),
            "key_terms": summary.get("key_terms", []),
        },
        "allowed_node_types": sorted(VALID_NODE_TYPES),
        "forbidden_node_types": sorted(FORBIDDEN_NODE_TYPES),
    }


def call_llm_with_json_fallback(
    api_key: str,
    base_url: str,
    model: str,
    prompt: str,
    payload: dict[str, Any],
    section: dict[str, Any],
    summary: dict[str, Any],
    temperature: float,
    timeout: float,
) -> dict[str, Any]:
    try:
        return call_llm(api_key, base_url, model, prompt, payload, temperature, timeout)
    except RuntimeError as first_error:
        if "invalid JSON" not in str(first_error):
            raise
        fallback_prompt = (
            prompt
            + "\n\n## JSON 修复重试约束\n\n"
            + "- 上一次输出不是合法 JSON。本次必须输出严格 JSON 对象。\n"
            + "- 直接依据当前 section_text 抽取，不依赖 Step 2 提供定义、定理、公式或条件判断线索。\n"
            + "- 最多输出 8 个 nodes；宁可少输出，也必须保证 JSON 完整合法。\n"
        )
        raw_retry = call_llm(api_key, base_url, model, fallback_prompt, payload, temperature, timeout)
        raw_retry["_fallback"] = {
            "reason": "initial_invalid_json",
            "initial_error": str(first_error)[:1000],
            "mode": "strict_json_retry",
        }
        return raw_retry


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
        raise RuntimeError(
            f"LLM returned invalid JSON: {first_exc}; content_prefix={content[:1000]}"
        ) from first_exc


def call_llm(
    api_key: str,
    base_url: str,
    model: str,
    prompt: str,
    payload: dict[str, Any],
    temperature: float,
    timeout: float,
) -> dict[str, Any]:
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
            raise RuntimeError(f"LLM HTTP {exc.code}: {body[:1000]}") from exc
        except urllib.error.URLError as exc:
            last_error = RuntimeError(f"LLM request failed: {exc}")
        except RuntimeError as exc:
            last_error = exc
        if attempt < 3:
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


def coerce_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def list_field(raw: dict[str, Any], name: str) -> list[Any]:
    value = raw.get(name)
    return value if isinstance(value, list) else []


def stable_node_id(textbook_id: str, name: str, node_type: str) -> str:
    digest = hashlib.sha1(f"{textbook_id}|{node_type}|{name}".encode("utf-8")).hexdigest()[:12]
    return f"{textbook_id}:node:{digest}"


def clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def anchor_statement_text(anchor: dict[str, Any]) -> str:
    text = str(anchor.get("text") or "").strip()
    anchor_type = str(anchor.get("anchor_type") or "")
    if not text:
        return ""
    if anchor_type in {"theorem", "proposition", "corollary", "lemma", "property"}:
        text = re.split(r"\n\s*证明", text, maxsplit=1)[0].strip()
    return text


def source_label_title(source_label: str) -> str:
    match = re.match(r"^(定义|定理|命题|推论|引理|性质|公式|例)\s*[0-9一二三四五六七八九十]+", source_label)
    return match.group(0) if match else ""


def find_anchor_by_label(section: dict[str, Any], source_label: str, aliases: list[str]) -> dict[str, Any] | None:
    labels = [source_label, *aliases]
    titles = [source_label_title(label) for label in labels if label]
    titles = [title for title in titles if title]
    for anchor in section.get("anchors", []):
        source = str(anchor.get("source_label") or "")
        title = str(anchor.get("title") or "")
        if source_label and (source_label == source or source_label in source or source in source_label):
            return anchor
        if any(title == candidate or source.startswith(candidate) for candidate in titles):
            return anchor
    return None


def find_formula_block_by_tag(section_text: str, tags: list[str]) -> str:
    tag_numbers: list[str] = []
    for tag in tags:
        for number in re.findall(r"(?:公式)?[\(（]\s*([0-9]+)\s*[\)）]", tag):
            tag_numbers.append(number)
    for number in tag_numbers:
        pattern = re.compile(
            rf"\$\$.*?\\tag\s*\{{\s*{re.escape(number)}\s*\}}.*?\$\$",
            re.DOTALL,
        )
        match = pattern.search(section_text)
        if match:
            return match.group(0).strip()
    return ""


def normalize_term_text(text: str) -> str:
    text = re.sub(r"[（(][^()（）]*[）)]", "", text)
    text = re.sub(r"\s+", "", text)
    return text


def find_paragraph_containing(section_text: str, terms: list[str]) -> str:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section_text) if p.strip()]
    clean_terms = [term for term in terms if term]
    definition_markers = ("称为", "叫做", "定义", "记作")
    normalized_terms = [normalize_term_text(term) for term in clean_terms]

    for term in normalized_terms:
        if not term:
            continue
        for paragraph in paragraphs:
            normalized_paragraph = normalize_term_text(paragraph)
            if term in normalized_paragraph and any(marker in paragraph for marker in definition_markers):
                return paragraph

    for term in clean_terms:
        for paragraph in paragraphs:
            if term in paragraph:
                return paragraph
    for term in normalized_terms:
        if not term:
            continue
        for paragraph in paragraphs:
            if term in normalize_term_text(paragraph):
                return paragraph
    return ""


def repair_spans(node: dict[str, Any], section: dict[str, Any]) -> list[str]:
    repairs: list[str] = []
    section_text = str(section.get("text") or "")
    aliases = clean_list(node.get("aliases"))
    source_label = str(node.get("source_label") or "")
    anchor = find_anchor_by_label(section, source_label, aliases)

    if not span_in_section(str(node.get("evidence_span") or ""), section_text):
        repaired = ""
        if anchor:
            repaired = anchor_statement_text(anchor)
        if not repaired and node.get("type") == "Formula":
            repaired = find_formula_block_by_tag(section_text, [source_label, *aliases])
        if not repaired:
            repaired = find_paragraph_containing(section_text, [str(node.get("name") or ""), *aliases])
        if repaired and span_in_section(repaired, section_text):
            node["evidence_span"] = repaired
            repairs.append("evidence_span_repaired")

    definition = str(node.get("definition") or "")
    if definition and not span_in_section(definition, section_text):
        repaired_definition = ""
        if anchor and str(anchor.get("anchor_type") or "") == "definition":
            repaired_definition = anchor_statement_text(anchor)
        if not repaired_definition:
            repaired_definition = find_paragraph_containing(section_text, [str(node.get("name") or ""), *aliases])
        if repaired_definition and span_in_section(repaired_definition, section_text):
            node["definition"] = repaired_definition
            repairs.append("definition_span_repaired")
        else:
            node["definition"] = ""
            node.setdefault("state_notes", [])
            if isinstance(node["state_notes"], list):
                node["state_notes"].append("definition 原始片段未命中原文，已清空。")
            repairs.append("definition_span_cleared")
    return repairs


def normalize_candidate(
    raw: dict[str, Any],
    section: dict[str, Any],
    summary: dict[str, Any],
    index: int,
    model: str,
    mode: str,
) -> dict[str, Any]:
    name = str(raw.get("name", "") or "").strip()
    node_type = str(raw.get("type", "") or "").strip()
    textbook_id = section.get("textbook_id", "")
    source_scope = section.get("source_scope", "")
    candidate_id = f"{section.get('section_node_id', '')}:node-cand-{index:03d}"
    aliases = clean_list(raw.get("aliases"))
    source_label = str(raw.get("source_label", "") or "").strip()
    if source_label and source_label not in aliases:
        aliases.append(source_label)

    node = {
        "candidate_id": candidate_id,
        "node_id": stable_node_id(textbook_id, name, node_type) if name and node_type else "",
        "name": name,
        "type": node_type,
        "aliases": aliases,
        "source_label": source_label,
        "definition": str(raw.get("definition", "") or "").strip(),
        "description": str(raw.get("description", "") or "").strip(),
        "attributes": raw.get("attributes") if isinstance(raw.get("attributes"), list) else [],
        "state_notes": clean_list(raw.get("state_notes")),
        "rule_cases": [],
        "evidence_span": str(raw.get("evidence_span", "") or "").strip(),
        "confidence": coerce_confidence(raw.get("confidence", 0)),
        "reason": str(raw.get("reason", "") or "").strip(),
        "review_recommended": bool(raw.get("review_recommended", False)),
        "review_reason": str(raw.get("review_reason", "") or "").strip(),
        "textbook_id": textbook_id,
        "textbook_name": section.get("textbook_name", ""),
        "chapter": section.get("chapter", ""),
        "section": section.get("section", ""),
        "subsection": section.get("subsection", ""),
        "section_node_id": section.get("section_node_id", ""),
        "source_scope": source_scope,
        "line_start": section.get("line_start", 0),
        "line_end": section.get("line_end", 0),
        "layer": "explicit",
        "review_status": "pending",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "mode": mode,
        "validation_warnings": [],
        "summary_id": summary.get("summary_id", ""),
    }
    return node


def validate_candidate(node: dict[str, Any], section_text: str) -> list[str]:
    warnings: list[str] = []
    name = node.get("name", "")
    node_type = node.get("type", "")
    source_scope = node.get("source_scope", "")
    evidence = node.get("evidence_span", "")
    if not name:
        warnings.append("missing_name")
    if NUMBERED_NAME_RE.match(name):
        warnings.append("numbered_name")
    if node_type not in VALID_NODE_TYPES:
        warnings.append(f"invalid_node_type:{node_type}")
    if node_type in FORBIDDEN_NODE_TYPES:
        warnings.append(f"forbidden_node_type:{node_type}")
    if source_scope == "example" and node_type not in EXAMPLE_ALLOWED_TYPES:
        warnings.append(f"example_forbidden_node_type:{node_type}")
    if source_scope == "example":
        node["review_recommended"] = True
        if not node.get("review_reason"):
            node["review_reason"] = "典型例题中抽出的 Method/ProblemClass 需要人工确认可复用性。"
    if not evidence:
        warnings.append("missing_evidence_span")
    elif not span_in_section(evidence, section_text):
        warnings.append("evidence_span_not_in_section")

    for index, attr in enumerate(node.get("attributes", [])):
        if not isinstance(attr, dict):
            warnings.append(f"attribute_item_not_object:{index}")
            continue
        attr_evidence = str(attr.get("evidence_span") or "")
        if attr_evidence and not span_in_section(attr_evidence, section_text):
            warnings.append(f"attribute_evidence_span_not_in_section:{index}")

    if node.get("confidence", 0.0) < 0.72:
        warnings.append("confidence_below_auto_threshold")
    if node.get("review_recommended"):
        warnings.append("review_recommended")
    return warnings


def decide_review_status(warnings: list[str]) -> str:
    hard_reject_prefixes = (
        "invalid_node_type:",
        "forbidden_node_type:",
        "example_forbidden_node_type:",
    )
    hard_reject_exact = {
        "missing_name",
        "numbered_name",
        "missing_evidence_span",
        "evidence_span_not_in_section",
    }
    if (
        any(w.startswith(hard_reject_prefixes) for w in warnings)
        or any(w in hard_reject_exact for w in warnings)
    ):
        return "reject"
    if warnings:
        return "review"
    return "auto_accept"


def mock_nodes(section: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    return {"nodes": []}


def write_report(
    path: Path,
    total_raw: int,
    status_counts: dict[str, int],
    type_counts: dict[str, int],
    warning_counts: dict[str, int],
    processed_sections: int,
) -> None:
    lines = [
        "# v4.3 Step 3 Node Extraction Report",
        "",
        f"- processed sections: {processed_sections}",
        f"- raw node candidates: {total_raw}",
        "",
        "## Review Status",
    ]
    for key in sorted(status_counts):
        lines.append(f"- {key}: {status_counts[key]}")
    lines.extend(["", "## Node Types"])
    for key in sorted(type_counts):
        lines.append(f"- {key}: {type_counts[key]}")
    lines.extend(["", "## Top Warnings"])
    if warning_counts:
        for key, value in sorted(warning_counts.items(), key=lambda item: (-item[1], item[0]))[:20]:
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    sections = {row.get("section_node_id"): row for row in read_jsonl(args.leaf_sections)}
    summaries = select_summaries(read_jsonl(args.summaries), config, args)
    prompt = args.prompt.read_text(encoding="utf-8")
    llm_config = config.get("llm", {})
    model = args.model or llm_config.get("default_model", "deepseek-chat")
    base_url = args.base_url or load_env_value("LLM_API_BASE") or llm_config.get("base_url", "https://api.openai.com/v1")
    temperature = args.temperature if args.temperature is not None else float(llm_config.get("temperature", 0.0))
    timeout = args.timeout if args.timeout is not None else float(llm_config.get("timeout_seconds", 120))

    api_key = ""
    if not args.mock:
        api_key = load_env_value("LLM_API_KEY") or load_env_value("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("LLM_API_KEY not found. Use --mock for local validation.")

    print(f"[INFO] summaries={len(summaries)} model={model} mock={args.mock}")
    total_raw = 0
    processed_sections = 0
    status_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    warning_counts: dict[str, int] = {}

    with (
        open_output(args.raw_output, args.append) as raw_f,
        open_output(args.nodes, args.append) as nodes_f,
        open_output(args.review, args.append) as review_f,
        open_output(args.warnings, args.append) as warn_f,
    ):
        for summary in summaries:
            section_id = summary.get("section_node_id", "")
            section = sections.get(section_id)
            if not section:
                warn_f.write(json.dumps({
                    "section_node_id": section_id,
                    "warnings": ["section_not_found_for_summary"],
                }, ensure_ascii=False) + "\n")
                continue

            if args.mock:
                raw = mock_nodes(section, summary)
                elapsed = 0.0
                mode = "mock"
            else:
                payload = build_payload(section, summary)
                started = time.time()
                raw = call_llm_with_json_fallback(
                    api_key,
                    base_url,
                    model,
                    prompt,
                    payload,
                    section,
                    summary,
                    temperature,
                    timeout,
                )
                elapsed = time.time() - started
                mode = "llm"

            raw_nodes = raw.get("nodes") if isinstance(raw.get("nodes"), list) else []
            raw_f.write(json.dumps({
                "section_node_id": section_id,
                "raw": raw,
                "model": model,
                "mode": mode,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }, ensure_ascii=False) + "\n")

            section_text = str(section.get("text") or "")
            processed_sections += 1
            section_warning_count = 0
            accepted_or_reviewed = 0
            for index, raw_node in enumerate(raw_nodes, start=1):
                if not isinstance(raw_node, dict):
                    warning = {
                        "section_node_id": section_id,
                        "candidate_index": index,
                        "warnings": ["raw_node_item_not_object"],
                    }
                    warn_f.write(json.dumps(warning, ensure_ascii=False) + "\n")
                    warning_counts["raw_node_item_not_object"] = warning_counts.get("raw_node_item_not_object", 0) + 1
                    continue
                total_raw += 1
                node = normalize_candidate(raw_node, section, summary, index, model, mode)
                repair_notes = repair_spans(node, section)
                warnings = validate_candidate(node, section_text)
                if repair_notes:
                    node["span_repairs"] = repair_notes
                status = decide_review_status(warnings)
                node["review_status"] = status
                node["validation_warnings"] = warnings
                status_counts[status] = status_counts.get(status, 0) + 1
                type_counts[node.get("type", "")] = type_counts.get(node.get("type", ""), 0) + 1
                for warning in warnings:
                    warning_counts[warning] = warning_counts.get(warning, 0) + 1

                if warnings:
                    section_warning_count += 1
                    warn_f.write(json.dumps({
                        "section_node_id": section_id,
                        "candidate_id": node["candidate_id"],
                        "name": node["name"],
                        "type": node["type"],
                        "review_status": status,
                        "warnings": warnings,
                    }, ensure_ascii=False) + "\n")

                if status in {"auto_accept", "review"} or args.keep_rejected_candidates:
                    nodes_f.write(json.dumps(node, ensure_ascii=False) + "\n")
                    accepted_or_reviewed += 1
                if status == "review":
                    review_f.write(json.dumps(node, ensure_ascii=False) + "\n")

            print(
                f"[OK] {section_id} mode={mode} elapsed={elapsed:.1f}s "
                f"raw_nodes={len(raw_nodes)} kept={accepted_or_reviewed} warnings={section_warning_count}"
            )

    write_report(args.report, total_raw, status_counts, type_counts, warning_counts, processed_sections)
    print(f"[OK] raw -> {args.raw_output}")
    print(f"[OK] nodes -> {args.nodes}")
    print(f"[OK] review -> {args.review}")
    print(f"[OK] warnings -> {args.warnings}")
    print(f"[OK] report -> {args.report}")


if __name__ == "__main__":
    main()

