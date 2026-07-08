from __future__ import annotations

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
ENV_PATHS = [REPO_ROOT / ".env", MODULE_DIR / ".env"]

VALID_NODE_TYPES = {"Concept", "Method", "Formula", "Theorem", "ProblemClass"}
VALID_EDGE_TYPES = {"SUPERIOR", "EQUATIVE", "PART_OF", "HAS_PROPERTY", "USES", "GETS", "DERIVES"}
VALID_ACTIONS = {"accept", "reject", "rewrite", "defer", "accept_merge", "reject_merge"}
VALID_TARGET_LAYERS = {"core", "example_application", "rule_case", "review_pending", "rejected_archive"}
VALID_RULE_LOGIC = {"SUFFICIENT", "NECESSARY", "AND", "OR", "IFF", "PIECEWISE", "UNKNOWN"}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def stable_id(prefix: str, parts: list[str]) -> str:
    digest = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:14]
    return f"{prefix}:{digest}"


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


def read_json(path: Path, required: bool = True) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"JSON not found: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")


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
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_body = json.loads(response.read().decode("utf-8"))
            content = response_body.get("choices", [{}])[0].get("message", {}).get("content") or "{}"
            return parse_llm_json(content)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            error = RuntimeError(f"LLM HTTP {exc.code}: {body[:1200]}")
            if exc.code in {429, 500, 502, 503, 504}:
                last_error = error
            else:
                raise error from exc
        except urllib.error.URLError as exc:
            last_error = RuntimeError(f"LLM request failed: {exc}")
        except RuntimeError as exc:
            last_error = exc
        if attempt < 3:
            time.sleep(2.0 * attempt)
    assert last_error is not None
    raise last_error


def compact_text(value: Any, limit: int = 1000) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def source_code(row: dict[str, Any]) -> str:
    section_node_id = str(row.get("section_node_id") or "").strip()
    textbook_id = str(row.get("textbook_id") or "").strip()
    base = section_node_id or textbook_id or "unknown-source"
    line_start = row.get("line_start")
    line_end = row.get("line_end")
    if line_start not in (None, "", 0) or line_end not in (None, "", 0):
        return f"{base}:L{line_start or ''}-L{line_end or ''}"
    return base


def ensure_source_code(item: dict[str, Any]) -> dict[str, Any]:
    item.setdefault("source_code", source_code(item))
    return item


def node_identity(node: dict[str, Any]) -> str:
    node_id = str(node.get("node_id") or "")
    if node_id:
        return node_id
    return stable_id("node-key", [str(node.get("name") or ""), str(node.get("type") or "")])


def edge_identity(edge: dict[str, Any]) -> str:
    return stable_id(
        "edge-key",
        [
            str(edge.get("source_node_id") or edge.get("source_name") or ""),
            str(edge.get("target_node_id") or edge.get("target_name") or ""),
            str(edge.get("type") or ""),
            str(edge.get("kg_layer") or ""),
        ],
    )


def rule_case_identity(rule_case: dict[str, Any]) -> str:
    rule_case_id = str(rule_case.get("rule_case_id") or "")
    if rule_case_id:
        return rule_case_id
    return stable_id(
        "rule-case-key",
        [
            str(rule_case.get("owner_node_id") or rule_case.get("owner_name") or ""),
            str(rule_case.get("case_name") or ""),
            str(rule_case.get("evidence_span") or ""),
        ],
    )


def review_item_identity(item: dict[str, Any]) -> str:
    return str(item.get("review_item_id") or item.get("decision_id") or item.get("candidate_id") or item.get("item_id") or "")
