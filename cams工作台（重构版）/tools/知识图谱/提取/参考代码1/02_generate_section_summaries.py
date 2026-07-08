"""
v4.4 Step 2: generate leaf-section overviews and keywords.

Default model comes from the run config. Use --mock for local validation
without calling the DeepSeek API.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
MODULE_DIR = SCRIPT_DIR.parents[1]
DEFAULT_CONFIG = SCRIPT_DIR / "v4_3_config.json"
DEFAULT_PROMPT = SCRIPT_DIR / "prompts" / "section_summary.md"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "中间产物"
DEFAULT_LEAF_SECTIONS = DEFAULT_OUTPUT_DIR / "leaf_sections.jsonl"
DEFAULT_OUTPUT = DEFAULT_OUTPUT_DIR / "section_summaries.jsonl"
DEFAULT_WARNINGS = DEFAULT_OUTPUT_DIR / "section_summary_warnings.jsonl"
ENV_PATHS = [REPO_ROOT / ".env", MODULE_DIR / ".env"]

FORBIDDEN_SUMMARY_FIELDS = (
    "definition_spans",
    "theorem_formula_spans",
    "formula_block_hints",
    "method_problem_spans",
    "state_or_attribute_hints",
    "rule_case_hints",
    "candidate_node_hints",
    "relation_hints",
    "section_role_notes",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate v4.4 section overviews.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--leaf-sections", type=Path, default=DEFAULT_LEAF_SECTIONS)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--warnings", type=Path, default=DEFAULT_WARNINGS)
    parser.add_argument("--chunk-id", "--section-node-id", dest="section_node_id", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true", help="Process one eligible section.")
    parser.add_argument("--mock", action="store_true", help="Generate deterministic local mock summaries.")
    parser.add_argument("--model", default="", help="Override model.")
    parser.add_argument("--base-url", default="", help="Override API base URL.")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("--append", action="store_true")
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
        raise FileNotFoundError(f"JSONL not found: {path}. Run 01_build_textbook_tree.py first.")
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def select_sections(sections: list[dict[str, Any]], config: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.section_node_id:
        selected = [s for s in sections if s.get("section_node_id") == args.section_node_id]
        if not selected:
            raise ValueError(f"section_node_id not found: {args.section_node_id}")
        return selected

    skip_scopes = set(config.get("tree", {}).get("skip_source_scopes", ["exercise"]))
    eligible = [s for s in sections if s.get("source_scope") not in skip_scopes]
    if args.dry_run:
        return eligible[:1]
    if args.limit > 0:
        return eligible[: args.limit]
    return eligible


def build_payload(section: dict[str, Any]) -> dict[str, Any]:
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


def first_sentences(text: str, max_chars: int = 260) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[:max_chars].rstrip() + "..."


def mock_summary(section: dict[str, Any]) -> dict[str, Any]:
    terms: list[str] = []
    for anchor in section.get("anchors", [])[:8]:
        title = str(anchor.get("title", "")).strip()
        if title:
            terms.append(title)
    subsection = str(section.get("subsection") or section.get("section") or "")
    if subsection and subsection not in terms:
        terms.insert(0, subsection)
    return {
        "summary": first_sentences(section.get("text", "")),
        "key_terms": terms[:10],
        "skip_reason": "",
    }


def normalize_key_terms(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    terms: list[str] = []
    seen: set[str] = set()
    for item in value:
        term = str(item).strip()
        if not term or term in seen:
            continue
        seen.add(term)
        terms.append(term)
    return terms


def normalize_summary(raw: dict[str, Any], section: dict[str, Any], model: str, mode: str) -> dict[str, Any]:
    return {
        "summary_id": f"{section.get('section_node_id', '')}:summary",
        "section_node_id": section.get("section_node_id", ""),
        "textbook_id": section.get("textbook_id", ""),
        "textbook_name": section.get("textbook_name", ""),
        "chapter": section.get("chapter", ""),
        "section": section.get("section", ""),
        "subsection": section.get("subsection", ""),
        "source_scope": section.get("source_scope", ""),
        "line_start": section.get("line_start", 0),
        "line_end": section.get("line_end", 0),
        "summary": str(raw.get("summary", "") or "").strip(),
        "key_terms": normalize_key_terms(raw.get("key_terms")),
        "skip_reason": str(raw.get("skip_reason", "") or "").strip(),
        "model": model,
        "mode": mode,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def validate_summary(row: dict[str, Any], section: dict[str, Any], raw: dict[str, Any] | None = None) -> list[str]:
    warnings: list[str] = []
    if row["source_scope"] != "exercise" and not row["summary"]:
        warnings.append("missing_summary")
    if row["source_scope"] == "exercise" and row["summary"]:
        warnings.append("exercise_has_summary")
    if not isinstance(row.get("key_terms"), list):
        warnings.append("key_terms_not_list")
    raw = raw or {}
    for field in FORBIDDEN_SUMMARY_FIELDS:
        warning = f"forbidden_field_present:{field}"
        if (field in raw or field in row) and warning not in warnings:
            warnings.append(warning)
    return warnings

def open_output(path: Path, append: bool):
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("a" if append else "w", encoding="utf-8", newline="\n")


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    sections = select_sections(read_jsonl(args.leaf_sections), config, args)
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

    print(f"[INFO] sections={len(sections)} model={model} mock={args.mock}")
    warning_count = 0
    with open_output(args.output, args.append) as out_f, open_output(args.warnings, args.append) as warn_f:
        for section in sections:
            if args.mock:
                raw = mock_summary(section)
                elapsed = 0.0
                mode = "mock"
            else:
                payload = build_payload(section)
                started = time.time()
                raw = call_llm(api_key, base_url, model, prompt, payload, temperature, timeout)
                elapsed = time.time() - started
                mode = "llm"

            row = normalize_summary(raw, section, model, mode)
            warnings = validate_summary(row, section, raw)
            out_f.write(json.dumps(row, ensure_ascii=False) + "\n")
            if warnings:
                warning_count += 1
                warn_f.write(json.dumps({
                    "section_node_id": section.get("section_node_id", ""),
                    "warnings": warnings,
                    "summary_id": row["summary_id"],
                }, ensure_ascii=False) + "\n")
            print(f"[OK] {section.get('section_node_id')} mode={mode} elapsed={elapsed:.1f}s warnings={len(warnings)}")

    print(f"[OK] summaries -> {args.output}")
    print(f"[OK] warnings -> {args.warnings} count={warning_count}")


if __name__ == "__main__":
    main()

