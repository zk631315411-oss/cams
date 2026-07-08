"""
v4.3 Step 3B: extract ExampleFrame records from example sections.

ExampleFrame is an intermediate structure, not a formal KG node. It keeps
problem classes, methods, tool uses, and get-results from examples before
they are normalized into application-layer nodes and edges.
"""

from __future__ import annotations

import argparse
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
DEFAULT_PROMPT = SCRIPT_DIR / "prompts" / "example_frame_extraction.md"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "中间产物"
DEFAULT_LEAF_SECTIONS = DEFAULT_OUTPUT_DIR / "leaf_sections.jsonl"
DEFAULT_SUMMARIES = DEFAULT_OUTPUT_DIR / "section_summaries.jsonl"
DEFAULT_RAW_OUTPUT = DEFAULT_OUTPUT_DIR / "raw_example_frames.jsonl"
DEFAULT_FRAMES = DEFAULT_OUTPUT_DIR / "example_frames.jsonl"
DEFAULT_REVIEW = DEFAULT_OUTPUT_DIR / "example_frame_review_queue.jsonl"
DEFAULT_WARNINGS = DEFAULT_OUTPUT_DIR / "example_frame_warnings.jsonl"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "example_frame_report.md"
ENV_PATHS = [REPO_ROOT / ".env", MODULE_DIR / ".env"]

FORBIDDEN_TEXT = ("...", "……", "省略")
TOOL_TYPE_HINTS = {"Formula", "Theorem", "Method", "Concept", "Unknown"}
RESULT_TYPE_HINTS = {"Formula", "Concept", "ProblemClass", "Unknown"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract v4.3 ExampleFrame records.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--leaf-sections", type=Path, default=DEFAULT_LEAF_SECTIONS)
    parser.add_argument("--summaries", type=Path, default=DEFAULT_SUMMARIES)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW_OUTPUT)
    parser.add_argument("--frames", type=Path, default=DEFAULT_FRAMES)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--warnings", type=Path, default=DEFAULT_WARNINGS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--chunk-id", "--section-node-id", dest="section_node_id", default="")
    parser.add_argument("--limit", type=int, default=0)
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


def coerce_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def normalize_for_match(text: str) -> str:
    text = re.sub(r"\s+", "", str(text or ""))
    text = text.replace("\\pmb", "")
    text = text.replace("{", "").replace("}", "")
    return text


def span_in_section(span: str, section_text: str) -> bool:
    if not span:
        return True
    if span in section_text:
        return True
    normalized_span = normalize_for_match(span)
    normalized_text = normalize_for_match(section_text)
    return bool(normalized_span and normalized_span in normalized_text)


def has_forbidden_text(span: str) -> bool:
    return any(token in str(span or "") for token in FORBIDDEN_TEXT)


def valid_span(span: str, section_text: str) -> bool:
    return bool(span) and not has_forbidden_text(span) and span_in_section(span, section_text)


def sanitize_frame(frame: dict[str, Any], section_text: str) -> list[str]:
    """Drop optional invalid evidence without losing the whole example frame."""
    warnings: list[str] = []

    problem_class = frame.get("problem_class", {})
    problem_evidence = clean_text(problem_class.get("evidence_span"))
    problem_text = clean_text(frame.get("problem_text_span"))
    if problem_evidence and not valid_span(problem_evidence, section_text):
        warnings.append("problem_class_evidence_filtered")
        problem_class["evidence_span"] = problem_text if valid_span(problem_text, section_text) else ""

    kept_methods: list[dict[str, Any]] = []
    for index, method in enumerate(frame.get("methods", [])):
        marker = clean_text(method.get("method_marker_span"))
        operation = clean_text(method.get("operation_span"))
        marker_ok = valid_span(marker, section_text)
        operation_ok = valid_span(operation, section_text)
        if marker and not marker_ok:
            method["method_marker_span"] = ""
            warnings.append(f"method_marker_span_filtered:{index}")
        if operation and not operation_ok:
            method["operation_span"] = ""
            warnings.append(f"method_operation_span_filtered:{index}")
        if not method.get("name") or not (marker_ok or operation_ok):
            warnings.append(f"method_filtered:{index}")
            continue
        kept_methods.append(method)
    frame["methods"] = kept_methods

    kept_tool_uses: list[dict[str, Any]] = []
    for index, tool_use in enumerate(frame.get("tool_uses", [])):
        evidence = clean_text(tool_use.get("evidence_span"))
        if not valid_span(evidence, section_text):
            warnings.append(f"tool_use_filtered:{index}")
            continue
        kept_tool_uses.append(tool_use)
    frame["tool_uses"] = kept_tool_uses

    kept_gets: list[dict[str, Any]] = []
    for index, get_item in enumerate(frame.get("gets", [])):
        evidence = clean_text(get_item.get("evidence_span"))
        if not valid_span(evidence, section_text):
            warnings.append(f"get_filtered:{index}")
            continue
        kept_gets.append(get_item)
    frame["gets"] = kept_gets
    frame["normalization_warnings"] = warnings
    return warnings


def build_payload(section: dict[str, Any], summary: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "section_metadata": {
            "section_node_id": section.get("section_node_id", ""),
            "parent_section_node_id": section.get("parent_section_node_id", section.get("section_node_id", "")),
            "example_label_hint": section.get("example_label_hint", ""),
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
        "step2_summary": summary or {},
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
        raise RuntimeError(
            f"LLM returned invalid JSON: {first_exc}; content_prefix={content[:1000]}"
        ) from first_exc


def split_example_section(section: dict[str, Any]) -> list[dict[str, Any]]:
    text = str(section.get("text") or "")
    matches = list(re.finditer(r"(?m)^#####\s*(例\s*[0-9一二三四五六七八九十]+)\s*$", text))
    if not matches:
        return [section]
    chunks: list[dict[str, Any]] = []
    prefix = text[: matches[0].start()].strip()
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        chunk = dict(section)
        label = re.sub(r"\s+", "", match.group(1))
        chunk["section_node_id"] = f"{section.get('section_node_id', '')}:{label}"
        chunk["parent_section_node_id"] = section.get("section_node_id", "")
        chunk["example_label_hint"] = label
        chunk["text"] = (prefix + "\n\n" + text[start:end]).strip() if prefix else text[start:end].strip()
        chunks.append(chunk)
    return chunks


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
        except (ConnectionError, TimeoutError, socket.timeout, OSError) as exc:
            last_error = RuntimeError(f"LLM transport failed: {exc}")
        except RuntimeError as exc:
            last_error = exc
        if attempt < 3:
            time.sleep(1.5 * attempt)
    assert last_error is not None
    raise last_error


def select_sections(sections: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    selected = [section for section in sections if section.get("source_scope") == "example"]
    if args.section_node_id:
        selected = [section for section in selected if section.get("section_node_id") == args.section_node_id]
        if not selected:
            raise ValueError(f"example section_node_id not found: {args.section_node_id}")
    split_sections: list[dict[str, Any]] = []
    for section in selected:
        split_sections.extend(split_example_section(section))
    selected = split_sections
    if args.limit > 0:
        selected = selected[: args.limit]
    return selected


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_frame(raw: dict[str, Any], section: dict[str, Any], index: int, model: str, mode: str) -> dict[str, Any]:
    problem_class = raw.get("problem_class") if isinstance(raw.get("problem_class"), dict) else {}
    methods = raw.get("methods") if isinstance(raw.get("methods"), list) else []
    tool_uses = raw.get("tool_uses") if isinstance(raw.get("tool_uses"), list) else []
    gets = raw.get("gets") if isinstance(raw.get("gets"), list) else []

    normalized_methods: list[dict[str, Any]] = []
    for item in methods:
        if not isinstance(item, dict):
            continue
        normalized_methods.append({
            "name": clean_text(item.get("name")),
            "method_marker_span": clean_text(item.get("method_marker_span")),
            "operation_span": clean_text(item.get("operation_span")),
            "reusable": bool(item.get("reusable", True)),
            "confidence": coerce_confidence(item.get("confidence", 0)),
        })

    normalized_tool_uses: list[dict[str, Any]] = []
    for item in tool_uses:
        if not isinstance(item, dict):
            continue
        hint = clean_text(item.get("tool_type_hint")) or "Unknown"
        normalized_tool_uses.append({
            "user_name": clean_text(item.get("user_name")),
            "tool_name": clean_text(item.get("tool_name")),
            "tool_type_hint": hint if hint in TOOL_TYPE_HINTS else "Unknown",
            "evidence_span": clean_text(item.get("evidence_span")),
            "confidence": coerce_confidence(item.get("confidence", 0)),
        })

    normalized_gets: list[dict[str, Any]] = []
    for item in gets:
        if not isinstance(item, dict):
            continue
        hint = clean_text(item.get("result_type_hint")) or "Unknown"
        normalized_gets.append({
            "source_name": clean_text(item.get("source_name")),
            "result_name": clean_text(item.get("result_name")),
            "result_type_hint": hint if hint in RESULT_TYPE_HINTS else "Unknown",
            "evidence_span": clean_text(item.get("evidence_span")),
            "confidence": coerce_confidence(item.get("confidence", 0)),
        })

    return {
        "frame_id": f"{section.get('section_node_id', '')}:example-frame-{index:03d}",
        "example_label": clean_text(raw.get("example_label")) or clean_text(section.get("example_label_hint")),
        "problem_text_span": clean_text(raw.get("problem_text_span")),
        "problem_class": {
            "name": clean_text(problem_class.get("name")),
            "evidence_span": clean_text(problem_class.get("evidence_span")),
            "confidence": coerce_confidence(problem_class.get("confidence", 0)),
        },
        "methods": normalized_methods,
        "tool_uses": normalized_tool_uses,
        "gets": normalized_gets,
        "review_recommended": True,
        "review_reason": clean_text(raw.get("review_reason")) or "典型例题框架需要人工确认可复用性。",
        "textbook_id": section.get("textbook_id", ""),
        "textbook_name": section.get("textbook_name", ""),
        "chapter": section.get("chapter", ""),
        "section": section.get("section", ""),
        "subsection": section.get("subsection", ""),
        "section_node_id": section.get("parent_section_node_id", section.get("section_node_id", "")),
        "example_chunk_id": section.get("section_node_id", ""),
        "parent_section_node_id": section.get("parent_section_node_id", section.get("section_node_id", "")),
        "example_label_hint": section.get("example_label_hint", ""),
        "source_scope": section.get("source_scope", ""),
        "line_start": section.get("line_start", 0),
        "line_end": section.get("line_end", 0),
        "layer": "example_frame",
        "review_status": "pending",
        "validation_warnings": [],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "mode": mode,
    }


def validate_frame(frame: dict[str, Any], section_text: str) -> list[str]:
    warnings: list[str] = ["example_frame_requires_review", *frame.get("normalization_warnings", [])]
    if not frame.get("example_label"):
        warnings.append("missing_example_label")

    problem_class = frame.get("problem_class", {})
    problem_name = clean_text(problem_class.get("name"))
    if problem_name and not problem_name.endswith("问题"):
        warnings.append("problem_class_name_not_ending_with_problem")
    if problem_name and not clean_text(problem_class.get("evidence_span")):
        warnings.append("problem_class_missing_evidence")

    spans = [("problem_text_span", frame.get("problem_text_span", ""))]
    spans.append(("problem_class.evidence_span", problem_class.get("evidence_span", "")))
    for index, method in enumerate(frame.get("methods", [])):
        if not method.get("name"):
            warnings.append(f"method_missing_name:{index}")
        if method.get("name", "").endswith("问题"):
            warnings.append(f"method_name_looks_like_problem_class:{index}")
        spans.append((f"methods.{index}.method_marker_span", method.get("method_marker_span", "")))
        spans.append((f"methods.{index}.operation_span", method.get("operation_span", "")))
    for index, tool_use in enumerate(frame.get("tool_uses", [])):
        if not tool_use.get("user_name") or not tool_use.get("tool_name"):
            warnings.append(f"tool_use_missing_name:{index}")
        if not tool_use.get("evidence_span"):
            warnings.append(f"tool_use_missing_evidence:{index}")
        spans.append((f"tool_uses.{index}.evidence_span", tool_use.get("evidence_span", "")))
    for index, get_item in enumerate(frame.get("gets", [])):
        if not get_item.get("source_name") or not get_item.get("result_name"):
            warnings.append(f"get_missing_name:{index}")
        if not get_item.get("evidence_span"):
            warnings.append(f"get_missing_evidence:{index}")
        spans.append((f"gets.{index}.evidence_span", get_item.get("evidence_span", "")))

    for field, span in spans:
        if not span:
            continue
        if has_forbidden_text(span):
            warnings.append(f"span_contains_ellipsis:{field}")
        if not span_in_section(span, section_text):
            warnings.append(f"span_not_in_section:{field}")

    if not frame.get("methods") and not frame.get("problem_class", {}).get("name"):
        warnings.append("empty_frame")
    return warnings


def decide_review_status(warnings: list[str]) -> str:
    hard_prefixes = (
        "span_not_in_section:",
        "span_contains_ellipsis:",
        "method_missing_name:",
        "tool_use_missing_name:",
        "get_missing_name:",
    )
    hard_exact = {
        "problem_class_name_not_ending_with_problem",
        "empty_frame",
    }
    if any(w.startswith(hard_prefixes) for w in warnings) or any(w in hard_exact for w in warnings):
        return "reject"
    return "review"


def write_report(
    path: Path,
    processed_sections: int,
    total_raw: int,
    status_counts: dict[str, int],
    warning_counts: dict[str, int],
) -> None:
    lines = [
        "# v4.3 Step 3B ExampleFrame Report",
        "",
        f"- processed sections: {processed_sections}",
        f"- raw example frames: {total_raw}",
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
    sections = select_sections(read_jsonl(args.leaf_sections), args)
    summaries = {row.get("section_node_id"): row for row in read_jsonl(args.summaries)}
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

    print(f"[INFO] example_sections={len(sections)} model={model} mock={args.mock}")
    processed_sections = 0
    total_raw = 0
    status_counts: dict[str, int] = {}
    warning_counts: dict[str, int] = {}

    with (
        open_output(args.raw_output, args.append) as raw_f,
        open_output(args.frames, args.append) as frames_f,
        open_output(args.review, args.append) as review_f,
        open_output(args.warnings, args.append) as warn_f,
    ):
        for section in sections:
            section_id = section.get("section_node_id", "")
            summary = summaries.get(section.get("parent_section_node_id", section_id))
            started = time.time()
            mode = "mock" if args.mock else "llm"
            if args.mock:
                raw = {"example_frames": []}
            else:
                payload = build_payload(section, summary)
                try:
                    raw = call_llm(api_key, base_url, model, prompt, payload, temperature, timeout)
                except Exception as exc:
                    warning_counts["llm_call_failed"] = warning_counts.get("llm_call_failed", 0) + 1
                    warn_f.write(json.dumps({
                        "section_node_id": section_id,
                        "warnings": ["llm_call_failed"],
                        "error": str(exc)[:1200],
                    }, ensure_ascii=False) + "\n")
                    warn_f.flush()
                    print(f"[ERROR] {section_id} {exc}")
                    continue
            elapsed = time.time() - started
            raw_frames = raw.get("example_frames") if isinstance(raw.get("example_frames"), list) else []
            raw_f.write(json.dumps({
                "section_node_id": section_id,
                "raw": raw,
                "model": model,
                "mode": mode,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }, ensure_ascii=False) + "\n")
            raw_f.flush()

            processed_sections += 1
            kept = 0
            warning_rows = 0
            section_text = str(section.get("text") or "")
            for index, raw_frame in enumerate(raw_frames, start=1):
                if not isinstance(raw_frame, dict):
                    warning_counts["raw_frame_item_not_object"] = warning_counts.get("raw_frame_item_not_object", 0) + 1
                    continue
                total_raw += 1
                frame = normalize_frame(raw_frame, section, index, model, mode)
                sanitize_frame(frame, section_text)
                warnings = validate_frame(frame, section_text)
                status = decide_review_status(warnings)
                frame["review_status"] = status
                frame["validation_warnings"] = warnings
                status_counts[status] = status_counts.get(status, 0) + 1
                for warning in warnings:
                    warning_counts[warning] = warning_counts.get(warning, 0) + 1
                if warnings:
                    warning_rows += 1
                    warn_f.write(json.dumps({
                        "section_node_id": section_id,
                        "frame_id": frame["frame_id"],
                        "example_label": frame["example_label"],
                        "review_status": status,
                        "warnings": warnings,
                    }, ensure_ascii=False) + "\n")
                    warn_f.flush()
                if status == "review":
                    frames_f.write(json.dumps(frame, ensure_ascii=False) + "\n")
                    review_f.write(json.dumps(frame, ensure_ascii=False) + "\n")
                    frames_f.flush()
                    review_f.flush()
                    kept += 1

            print(f"[OK] {section_id} elapsed={elapsed:.1f}s raw_frames={len(raw_frames)} kept={kept} warnings={warning_rows}")

    write_report(args.report, processed_sections, total_raw, status_counts, warning_counts)
    print(f"[OK] raw -> {args.raw_output}")
    print(f"[OK] frames -> {args.frames}")
    print(f"[OK] review -> {args.review}")
    print(f"[OK] warnings -> {args.warnings}")
    print(f"[OK] report -> {args.report}")


if __name__ == "__main__":
    main()
