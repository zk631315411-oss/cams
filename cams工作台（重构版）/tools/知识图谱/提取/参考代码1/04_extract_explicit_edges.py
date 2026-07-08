"""
v4.4 Step 4: extract explicit relation candidates between admitted nodes.

This step only extracts explicit edges supported by the current leaf-section
text. It does not generate PREREQUISITE_OF; navigation prerequisites are
derived later.

v4.4 also adds conservative semantic-attribution candidates after the LLM pass.
These candidates are generated from current-section nodes and section evidence,
not from external knowledge, and are marked with semantic_inferred=true.
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
DEFAULT_PROMPT = SCRIPT_DIR / "prompts" / "explicit_edge_extraction.md"
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "中间产物"
DEFAULT_LEAF_SECTIONS = DEFAULT_OUTPUT_DIR / "leaf_sections.jsonl"
DEFAULT_NODES = DEFAULT_OUTPUT_DIR / "nodes.jsonl"
DEFAULT_RAW_OUTPUT = DEFAULT_OUTPUT_DIR / "raw_explicit_edge_candidates.jsonl"
DEFAULT_EDGES = DEFAULT_OUTPUT_DIR / "edges.jsonl"
DEFAULT_REVIEW = DEFAULT_OUTPUT_DIR / "edge_review_queue.jsonl"
DEFAULT_WARNINGS = DEFAULT_OUTPUT_DIR / "edge_extraction_warnings.jsonl"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "edge_extraction_report.md"
ENV_PATHS = [REPO_ROOT / ".env", MODULE_DIR / ".env"]

VALID_EDGE_TYPES = {"SUPERIOR", "EQUATIVE", "PART_OF", "HAS_PROPERTY", "USES", "GETS", "DERIVES"}
EXAMPLE_EDGE_TYPES = {"USES", "GETS"}
FORBIDDEN_EDGE_TYPES = {
    "PREREQUISITE_OF",
    "APPLIES_TO",
    "RELATED_TO",
    "SAME_AS",
    "DERIVED_FROM",
    "HAS_RULE_CASE",
    "HAS_CONDITION",
    "HAS_OUTCOME",
    "HAS_POSSIBLE_STATE",
}
DERIVES_NAMING_PATTERNS = (
    "称为",
    "叫做",
    "记为",
    "记作",
    "合起来称为",
    "统称为",
)
WEAK_EVIDENCE_EXACT = {
    "证明",
    "解",
}
WEAK_EVIDENCE_PATTERNS = (
    r"^证明[:：。.]?$",
    r"^解[:：。.]?$",
    r"^解法[一二三四五六七八九十\d]+[（(][^）)]{1,12}[）)]。?$",
)
USES_SOURCE_TYPES = {"Concept", "Method", "Formula", "Theorem", "ProblemClass"}
USES_TARGET_TYPES = {"Concept", "Method", "Formula", "Theorem"}
USES_METHOD_TARGET_SOURCE_TYPES = {"Method", "ProblemClass"}
GETS_SOURCE_TYPES = {"Method", "Formula", "Theorem"}
GETS_TARGET_TYPES = {"Concept", "Formula", "Theorem", "ProblemClass"}
DERIVES_SOURCE_TYPES = {"Theorem", "Formula"}
DERIVES_TARGET_TYPES = {"Concept", "Formula", "Theorem"}
SUPERIOR_TYPES = {"Concept", "Formula", "Theorem", "Method", "ProblemClass"}
EQUATIVE_TYPES = {"Concept", "Formula", "Theorem", "Method", "ProblemClass"}
PART_OF_TYPES = {"Concept", "Formula", "Theorem", "Method", "ProblemClass"}
PROPERTY_SOURCE_TYPES = {"Concept", "Formula", "Theorem", "Method", "ProblemClass"}
PROPERTY_TARGET_TYPES = {"Concept", "Theorem", "Formula", "Method"}
PROPERTY_NAME_RE = re.compile(r"(性质|定理|准则|公式|法则|推论)$")
PROPERTY_HINT_RE = re.compile(r"(性质|定理|准则|公式|法则|推论|判定|结论|关系|影响|展开)")
METHOD_HINT_RE = re.compile(r"(方法|算法|法|计算|证明|求解|化为|拆分|展开)")
TOPIC_NAME_HINTS = (
    "行列式",
    "线性方程组",
    "齐次线性方程组",
    "矩阵",
    "向量组",
    "向量空间",
    "矩阵的秩",
    "n元排列",
    "排列",
)
SPECIAL_TOPIC_MODIFIERS = ("上三角形", "范德蒙", "系数", "级矩阵", "分块", "特殊")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract v4.4 explicit edge candidates.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--leaf-sections", type=Path, default=DEFAULT_LEAF_SECTIONS)
    parser.add_argument("--nodes", type=Path, default=DEFAULT_NODES)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--raw-input", type=Path, default=None, help="Existing raw candidate JSONL for replay mode.")
    parser.add_argument("--raw-output", type=Path, default=DEFAULT_RAW_OUTPUT)
    parser.add_argument("--edges", type=Path, default=DEFAULT_EDGES)
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
    parser.add_argument("--include-examples", action="store_true", help="Also run the legacy ordinary edge extractor on example sections.")
    parser.add_argument("--replay-raw", action="store_true", help="Validate existing raw edge candidates without calling the LLM.")
    parser.add_argument(
        "--semantic-augment",
        action="store_true",
        help="Add conservative section-topic/property/method attribution candidates after LLM or replay input.",
    )
    parser.add_argument("--append", action="store_true")
    parser.add_argument(
        "--keep-rejected-candidates",
        action="store_true",
        help="Write locally rejected structured candidates to --edges so Step 4C can audit the full Step 4A output.",
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


def coerce_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def chunk_order_from_id(section_node_id: str) -> tuple[int, int, int]:
    match = re.search(r":C(\d+):S(\d+):U(\d+)$", str(section_node_id or ""))
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())


def section_sort_key(section: dict[str, Any]) -> tuple[int, int, int, str]:
    return (*chunk_order_from_id(str(section.get("section_node_id") or "")), str(section.get("section_node_id") or ""))


def node_sort_key(node: dict[str, Any]) -> tuple[int, int, int, str]:
    return (*chunk_order_from_id(str(node.get("section_node_id") or "")), str(node.get("name") or ""))


def node_visible_for_section(node: dict[str, Any], section: dict[str, Any]) -> bool:
    return chunk_order_from_id(str(node.get("section_node_id") or "")) <= chunk_order_from_id(str(section.get("section_node_id") or ""))


def node_current_section(node: dict[str, Any], section: dict[str, Any]) -> bool:
    return str(node.get("section_node_id") or "") == str(section.get("section_node_id") or "")


def same_parent_section(node: dict[str, Any], section: dict[str, Any]) -> bool:
    node_order = chunk_order_from_id(str(node.get("section_node_id") or ""))
    section_order = chunk_order_from_id(str(section.get("section_node_id") or ""))
    return node_order[:2] == section_order[:2]


def compact_node(node: dict[str, Any]) -> dict[str, Any]:
    evidence = str(node.get("evidence_span") or "")
    return {
        "node_id": node.get("node_id", ""),
        "name": node.get("name", ""),
        "type": node.get("type", ""),
        "review_status": node.get("review_status", ""),
        "source_label": node.get("source_label", ""),
        "aliases": node.get("aliases", [])[:5],
        "section_node_id": node.get("section_node_id", ""),
        "description": str(node.get("description") or evidence[:160]),
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
    visible = [node for node in nodes if node_visible_for_section(node, section) and node.get("review_status") in {"auto_accept", "review"}]
    current = [node for node in visible if node_current_section(node, section)]
    same_section_previous = [node for node in visible if node not in current and same_parent_section(node, section)]
    previous = [node for node in visible if node not in current and node not in same_section_previous]

    # Keep current-section nodes first, then high-utility prior theorem/formula/method/concept nodes.
    same_section_tools = [node for node in same_section_previous if node.get("type") in {"Theorem", "Formula", "Method"}]
    same_section_concepts = [node for node in same_section_previous if node.get("type") == "Concept"]
    same_section_problem = [node for node in same_section_previous if node.get("type") == "ProblemClass"]
    prior_tools = [node for node in previous if node.get("type") in {"Theorem", "Formula", "Method"}]
    prior_concepts = [node for node in previous if node.get("type") == "Concept"]
    prior_problem = [node for node in previous if node.get("type") == "ProblemClass"]
    ordered = sorted(current, key=node_sort_key)
    ordered += sorted(same_section_tools, key=node_sort_key)
    ordered += sorted(same_section_concepts, key=node_sort_key)
    ordered += sorted(same_section_problem, key=node_sort_key)
    ordered += sorted(prior_tools, key=node_sort_key)
    ordered += sorted(prior_concepts, key=node_sort_key)
    ordered += sorted(prior_problem, key=node_sort_key)

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
        "allowed_edge_types": sorted(VALID_EDGE_TYPES),
        "forbidden_edge_types": sorted(FORBIDDEN_EDGE_TYPES),
    }


def select_sections(sections: list[dict[str, Any]], config: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    sections = sorted(sections, key=section_sort_key)
    if args.section_node_id:
        selected = [section for section in sections if section.get("section_node_id") == args.section_node_id]
        if not selected:
            raise ValueError(f"section_node_id not found: {args.section_node_id}")
        return selected
    skip_scopes = set(config.get("tree", {}).get("skip_source_scopes", ["exercise"]))
    if args.include_examples:
        eligible = [section for section in sections if section.get("source_scope") not in skip_scopes]
    else:
        eligible = [section for section in sections if section.get("source_scope") == "core_content"]
    if args.dry_run:
        return eligible[:1]
    if args.limit > 0:
        return eligible[: args.limit]
    return eligible


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


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def is_weak_evidence_span(text: str) -> bool:
    stripped = str(text or "").strip()
    compact = compact_text(stripped)
    if not stripped or compact in WEAK_EVIDENCE_EXACT:
        return True
    return any(re.match(pattern, compact) for pattern in WEAK_EVIDENCE_PATTERNS)


def looks_like_naming_statement(text: str) -> bool:
    compact = compact_text(text)
    return any(pattern in compact for pattern in DERIVES_NAMING_PATTERNS)


def stable_edge_id(edge: dict[str, Any]) -> str:
    raw = "|".join([
        str(edge.get("source_node_id") or ""),
        str(edge.get("target_node_id") or ""),
        str(edge.get("type") or ""),
        str(edge.get("section_node_id") or ""),
    ])
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:14]
    return f"{edge.get('textbook_id', '')}:edge:{digest}"


def edge_key(edge: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(edge.get("source_node_id") or ""),
        str(edge.get("target_node_id") or ""),
        str(edge.get("type") or ""),
        str(edge.get("section_node_id") or ""),
    )


def node_search_text(node: dict[str, Any]) -> str:
    parts = [
        str(node.get("name") or ""),
        str(node.get("source_label") or ""),
        str(node.get("description") or ""),
        str(node.get("definition") or ""),
        str(node.get("evidence_span") or ""),
    ]
    aliases = node.get("aliases") or []
    if isinstance(aliases, list):
        parts.extend(str(alias) for alias in aliases)
    return " ".join(parts)


def node_evidence(node: dict[str, Any], section_text: str, fallback: str = "") -> str:
    candidates = [
        str(node.get("evidence_span") or "").strip(),
        str(node.get("definition") or "").strip(),
        fallback.strip(),
    ]
    for candidate in candidates:
        if candidate and span_in_section(candidate, section_text) and not is_weak_evidence_span(candidate):
            return candidate
    return ""


def short_topic_name(name: str) -> str:
    cleaned = str(name or "").strip()
    cleaned = re.sub(r"^\d+(?:\.\d+)*\s*", "", cleaned)
    cleaned = cleaned.replace("$", "")
    cleaned = re.sub(r"\\pmb\{([^}]*)\}", r"\1", cleaned)
    cleaned = re.sub(r"\s+", "", cleaned)
    return cleaned


def topic_score(node: dict[str, Any], section: dict[str, Any]) -> int:
    name = str(node.get("name") or "")
    text = node_search_text(node)
    section_name = str(section.get("section") or "")
    clean_section = short_topic_name(section_name)
    score = 0
    if node.get("type") == "Concept":
        score += 4
    if name and name in section_name:
        score += 8
    for hint in TOPIC_NAME_HINTS:
        if hint in name and hint in section_name:
            score += 6
        elif hint in name and hint in clean_section:
            score += 5
    if any(hint == name for hint in TOPIC_NAME_HINTS):
        score += 5
    if any(hint in name for hint in TOPIC_NAME_HINTS):
        score += 3
    if "行列式" in section_name and "性质" in section_name and name == "n阶行列式":
        score += 8
    if "行列式" in name and any(modifier in name for modifier in SPECIAL_TOPIC_MODIFIERS):
        score -= 6
    if "定义" in text:
        score += 1
    if PROPERTY_HINT_RE.search(name):
        score -= 5
    if METHOD_HINT_RE.search(name):
        score -= 3
    return score


def infer_topic_node(section: dict[str, Any], node_pool: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidate_concepts = [
        node for node in node_pool
        if node.get("type") == "Concept"
        and node.get("review_status") in {"auto_accept", "review"}
        and not is_property_like_node(node)
        and not is_method_like_node(node)
    ]
    if not candidate_concepts:
        return None
    section_name = str(section.get("section") or "")
    section_topic_terms = [
        term for term in ["行列式", "线性方程组", "矩阵的秩", "矩阵", "向量组", "向量空间", "n元排列", "排列"]
        if term in section_name
    ]
    if not section_topic_terms:
        return None
    if section_topic_terms:
        narrowed = [
            node for node in candidate_concepts
            if any(term in str(node.get("name") or "") for term in section_topic_terms)
        ]
        if narrowed:
            candidate_concepts = narrowed
    if "行列式" in section_name and "性质" in section_name:
        for node in candidate_concepts:
            if str(node.get("name") or "") == "n阶行列式":
                return node
    ranked = sorted(
        candidate_concepts,
        key=lambda node: (-topic_score(node, section), len(str(node.get("name") or "")), str(node.get("name") or "")),
    )
    best = ranked[0]
    if topic_score(best, section) <= 0:
        return None
    return best


def is_property_like_node(node: dict[str, Any]) -> bool:
    node_type = str(node.get("type") or "")
    name = str(node.get("name") or "")
    if node_type in {"Theorem", "Formula"}:
        return True
    if node_type == "Method":
        return False
    # Concept evidence can mention formulas/theorems while defining the concept.
    # For concepts, only the semantic name should make it property-like.
    return bool(PROPERTY_HINT_RE.search(name))


def is_method_like_node(node: dict[str, Any]) -> bool:
    return str(node.get("type") or "") == "Method" or bool(METHOD_HINT_RE.search(str(node.get("name") or "")))


def mentions_node(text: str, node: dict[str, Any]) -> bool:
    compact = compact_text(text)
    names = [str(node.get("name") or "")]
    aliases = node.get("aliases") or []
    if isinstance(aliases, list):
        names.extend(str(alias) for alias in aliases)
    for name in names:
        clean = compact_text(name)
        if clean and len(clean) >= 2 and clean in compact:
            return True
    source_label = compact_text(str(node.get("source_label") or ""))
    return bool(source_label and len(source_label) >= 2 and source_label in compact)


def semantic_raw_edge(
    source: dict[str, Any],
    target: dict[str, Any],
    edge_type: str,
    evidence_text: str,
    description: str,
    confidence: float,
    basis_type: str,
    review: bool,
) -> dict[str, Any]:
    return {
        "source_node_id": source.get("node_id", ""),
        "source_name": source.get("name", ""),
        "target_node_id": target.get("node_id", ""),
        "target_name": target.get("name", ""),
        "type": edge_type,
        "evidence_spans": [{"role": "primary", "text": evidence_text}],
        "description": description,
        "confidence": confidence,
        "review_recommended": review,
        "review_reason": "语义归属增强候选，需确认是否应作为核心语义边。" if review else "",
        "semantic_inferred": True,
        "basis_type": basis_type,
    }


def build_semantic_augmented_raw_edges(section: dict[str, Any], node_pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if section.get("source_scope") != "core_content":
        return []
    section_text = str(section.get("text") or "")
    current = [
        node for node in node_pool
        if node_current_section(node, section)
        and node.get("review_status") in {"auto_accept", "review"}
    ]
    if len(current) < 2:
        return []

    topic = infer_topic_node(section, node_pool)
    raw_edges: list[dict[str, Any]] = []
    existing_keys: set[tuple[str, str, str]] = set()

    def add(raw: dict[str, Any]) -> None:
        key = (
            str(raw.get("source_node_id") or ""),
            str(raw.get("target_node_id") or ""),
            str(raw.get("type") or ""),
        )
        if key[0] and key[1] and key[0] != key[1] and key not in existing_keys:
            existing_keys.add(key)
            raw_edges.append(raw)

    if topic:
        for node in current:
            if node.get("node_id") == topic.get("node_id"):
                continue
            evidence = node_evidence(node, section_text)
            if not evidence:
                continue
            node_type = str(node.get("type") or "")
            name = str(node.get("name") or "")
            if is_property_like_node(node):
                review = node.get("review_status") != "auto_accept" or node_type == "Formula"
                add(semantic_raw_edge(
                    topic,
                    node,
                    "HAS_PROPERTY",
                    evidence,
                    f"{node.get('name')} 是 {topic.get('name')} 所在小节给出的性质、公式、定理或结论。",
                    0.82 if review else 0.88,
                    "section_topic_property",
                    review,
                ))
            elif is_method_like_node(node) and any(token in name for token in ["行列式", "线性方程组", "矩阵", "向量"]):
                add(semantic_raw_edge(
                    node,
                    topic,
                    "USES",
                    evidence,
                    f"{node.get('name')} 是围绕 {topic.get('name')} 的方法，使用该主题对象。",
                    0.78,
                    "section_topic_method",
                    True,
                ))

    property_nodes = [node for node in current if is_property_like_node(node)]
    method_nodes = [node for node in current if is_method_like_node(node)]
    for method in method_nodes:
        method_text = node_search_text(method)
        method_evidence = node_evidence(method, section_text)
        if not method_evidence:
            continue
        for prop in property_nodes:
            if prop.get("node_id") == method.get("node_id"):
                continue
            if mentions_node(method_text, prop):
                add(semantic_raw_edge(
                    method,
                    prop,
                    "USES",
                    method_evidence,
                    f"{method.get('name')} 的教材说明中明确提到使用 {prop.get('name')}。",
                    0.86,
                    "method_mentions_tool",
                    False,
                ))

    return raw_edges


def normalize_edge(
    raw: dict[str, Any],
    section: dict[str, Any],
    node_by_id: dict[str, dict[str, Any]],
    index: int,
    model: str,
    mode: str,
) -> dict[str, Any]:
    evidence_items = raw.get("evidence_spans") if isinstance(raw.get("evidence_spans"), list) else []
    evidence_spans = []
    for item in evidence_items:
        if isinstance(item, dict):
            evidence_spans.append({
                "role": str(item.get("role", "") or "primary"),
                "text": str(item.get("text", "") or "").strip(),
            })
        elif isinstance(item, str):
            evidence_spans.append({"role": "primary", "text": item.strip()})

    edge = {
        "candidate_id": f"{section.get('section_node_id', '')}:edge-cand-{index:03d}",
        "edge_id": "",
        "source_node_id": str(raw.get("source_node_id", "") or ""),
        "source_name": str(raw.get("source_name", "") or "").strip(),
        "target_node_id": str(raw.get("target_node_id", "") or ""),
        "target_name": str(raw.get("target_name", "") or "").strip(),
        "type": str(raw.get("type", "") or "").strip(),
        "evidence_spans": evidence_spans,
        "evidence_span": evidence_spans[0]["text"] if evidence_spans else "",
        "description": str(raw.get("description", "") or "").strip(),
        "confidence": coerce_confidence(raw.get("confidence", 0)),
        "review_recommended": bool(raw.get("review_recommended", False)),
        "review_reason": str(raw.get("review_reason", "") or "").strip(),
        "textbook_id": section.get("textbook_id", ""),
        "textbook_name": section.get("textbook_name", ""),
        "chapter": section.get("chapter", ""),
        "section": section.get("section", ""),
        "subsection": section.get("subsection", ""),
        "section_node_id": section.get("section_node_id", ""),
        "source_scope": section.get("source_scope", ""),
        "line_start": section.get("line_start", 0),
        "line_end": section.get("line_end", 0),
        "layer": "explicit",
        "review_status": "pending",
        "validation_warnings": [],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": model,
        "mode": mode,
    }
    for key in ("semantic_inferred", "basis_type"):
        if key in raw:
            edge[key] = raw[key]
    source_node = node_by_id.get(edge["source_node_id"], {})
    target_node = node_by_id.get(edge["target_node_id"], {})
    if source_node:
        edge["source_name"] = source_node.get("name", edge["source_name"])
        edge["source_type"] = source_node.get("type", "")
        edge["source_review_status"] = source_node.get("review_status", "")
    else:
        edge["source_type"] = ""
        edge["source_review_status"] = ""
    if target_node:
        edge["target_name"] = target_node.get("name", edge["target_name"])
        edge["target_type"] = target_node.get("type", "")
        edge["target_review_status"] = target_node.get("review_status", "")
    else:
        edge["target_type"] = ""
        edge["target_review_status"] = ""
    edge["edge_id"] = stable_edge_id(edge)
    return edge


def validate_edge(edge: dict[str, Any], section_text: str, node_pool_ids: set[str]) -> list[str]:
    warnings: list[str] = []
    edge_type = edge.get("type", "")
    source_id = edge.get("source_node_id", "")
    target_id = edge.get("target_node_id", "")
    source_type = edge.get("source_type", "")
    target_type = edge.get("target_type", "")
    source_scope = edge.get("source_scope", "")

    if source_id not in node_pool_ids:
        warnings.append(f"source_not_in_node_pool:{source_id}")
    if target_id not in node_pool_ids:
        warnings.append(f"target_not_in_node_pool:{target_id}")
    if source_id and source_id == target_id:
        warnings.append("self_loop")
    if edge_type not in VALID_EDGE_TYPES:
        warnings.append(f"invalid_edge_type:{edge_type}")
    if edge_type in FORBIDDEN_EDGE_TYPES:
        warnings.append(f"forbidden_edge_type:{edge_type}")
    if source_scope == "example" and edge_type not in EXAMPLE_EDGE_TYPES:
        warnings.append(f"example_forbidden_edge_type:{edge_type}")

    if edge_type == "USES":
        if source_type not in USES_SOURCE_TYPES:
            warnings.append(f"uses_invalid_source_type:{source_type}")
        if target_type not in USES_TARGET_TYPES:
            warnings.append(f"uses_invalid_target_type:{target_type}")
        if target_type == "Method" and source_type not in USES_METHOD_TARGET_SOURCE_TYPES:
            warnings.append(f"uses_method_target_invalid_source_type:{source_type}")
    elif edge_type == "GETS":
        if source_type not in GETS_SOURCE_TYPES:
            warnings.append(f"gets_invalid_source_type:{source_type}")
        if target_type not in GETS_TARGET_TYPES:
            warnings.append(f"gets_invalid_target_type:{target_type}")
    elif edge_type == "DERIVES":
        if source_type not in DERIVES_SOURCE_TYPES:
            warnings.append(f"derives_invalid_source_type:{source_type}")
        if target_type not in DERIVES_TARGET_TYPES:
            warnings.append(f"derives_invalid_target_type:{target_type}")
    elif edge_type == "SUPERIOR":
        if source_type not in SUPERIOR_TYPES or target_type not in SUPERIOR_TYPES:
            warnings.append(f"superior_invalid_type_pair:{source_type}->{target_type}")
    elif edge_type == "EQUATIVE":
        if source_type not in EQUATIVE_TYPES or target_type not in EQUATIVE_TYPES:
            warnings.append(f"equative_invalid_type_pair:{source_type}->{target_type}")
    elif edge_type == "PART_OF":
        if source_type not in PART_OF_TYPES or target_type not in PART_OF_TYPES:
            warnings.append(f"part_of_invalid_type_pair:{source_type}->{target_type}")
    elif edge_type == "HAS_PROPERTY":
        if source_type not in PROPERTY_SOURCE_TYPES or target_type not in PROPERTY_TARGET_TYPES:
            warnings.append(f"has_property_invalid_type_pair:{source_type}->{target_type}")
        if PROPERTY_NAME_RE.search(str(edge.get("source_name") or "")) or "性质" in str(edge.get("source_name") or ""):
            warnings.append("has_property_direction_suspect")

    evidence_spans = edge.get("evidence_spans", [])
    if not evidence_spans:
        warnings.append("missing_evidence_spans")
    for index, evidence in enumerate(evidence_spans):
        text = str(evidence.get("text") or "") if isinstance(evidence, dict) else ""
        if not text:
            warnings.append(f"empty_evidence_span:{index}")
        elif not span_in_section(text, section_text):
            warnings.append(f"evidence_span_not_in_section:{index}")
        if "..." in text or "……" in text or "省略" in text:
            warnings.append(f"evidence_span_contains_ellipsis:{index}")
        if is_weak_evidence_span(text):
            warnings.append(f"weak_evidence_span:{index}")
        if edge_type == "DERIVES" and looks_like_naming_statement(text):
            warnings.append(f"derives_naming_statement:{index}")
        if edge_type == "EQUATIVE" and looks_like_naming_statement(text):
            warnings.append(f"equative_naming_statement:{index}")

    if edge.get("confidence", 0.0) < 0.72:
        warnings.append("confidence_below_auto_threshold")
    if edge.get("confidence", 0.0) < 0.5:
        warnings.append("confidence_below_reject_threshold")
    if edge.get("review_recommended"):
        warnings.append("review_recommended")
    if source_scope == "example":
        warnings.append("example_edge_requires_review")
        edge["review_recommended"] = True
        if not edge.get("review_reason"):
            edge["review_reason"] = "典型例题中的关系需要人工确认可复用性。"
    return warnings


def decide_review_status(warnings: list[str]) -> str:
    hard_prefixes = (
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
        "part_of_invalid_type_pair:",
        "evidence_span_not_in_section:",
        "empty_evidence_span:",
        "evidence_span_contains_ellipsis:",
        "weak_evidence_span:",
        "derives_naming_statement:",
        "equative_naming_statement:",
    )
    hard_exact = {"self_loop", "missing_evidence_spans"}
    hard_exact.add("confidence_below_reject_threshold")
    if any(w.startswith(hard_prefixes) for w in warnings) or any(w in hard_exact for w in warnings):
        return "reject"
    if warnings:
        return "review"
    return "auto_accept"


def process_raw_edge(
    raw_edge: dict[str, Any],
    section: dict[str, Any],
    node_by_id: dict[str, dict[str, Any]],
    node_pool_ids: set[str],
    section_text: str,
    index: int,
    model: str,
    mode: str,
    seen_edge_ids: set[str],
) -> tuple[dict[str, Any], list[str], str]:
    edge = normalize_edge(raw_edge, section, node_by_id, index, model, mode)
    warnings = validate_edge(edge, section_text, node_pool_ids)
    if edge.get("semantic_inferred"):
        warnings.append(f"semantic_inferred:{edge.get('basis_type', '')}")
        edge["review_recommended"] = bool(edge.get("review_recommended"))
    if edge["edge_id"] in seen_edge_ids:
        warnings.append("duplicate_edge_candidate")
        status = "reject"
    else:
        status = decide_review_status(warnings)
    edge["review_status"] = status
    edge["validation_warnings"] = warnings
    return edge, warnings, status


def write_processed_edge(
    edge: dict[str, Any],
    warnings: list[str],
    status: str,
    section_id: str,
    edges_f: Any,
    review_f: Any,
    warn_f: Any,
    seen_edge_ids: set[str],
    status_counts: dict[str, int],
    type_counts: dict[str, int],
    warning_counts: dict[str, int],
    keep_rejected_candidates: bool = False,
) -> tuple[int, int]:
    status_counts[status] = status_counts.get(status, 0) + 1
    type_counts[edge.get("type", "")] = type_counts.get(edge.get("type", ""), 0) + 1
    for warning in warnings:
        warning_counts[warning] = warning_counts.get(warning, 0) + 1

    warning_rows = 0
    kept = 0
    if warnings:
        warning_rows = 1
        warn_f.write(json.dumps({
            "section_node_id": section_id,
            "candidate_id": edge["candidate_id"],
            "source": edge["source_name"],
            "target": edge["target_name"],
            "type": edge["type"],
            "review_status": status,
            "warnings": warnings,
        }, ensure_ascii=False) + "\n")
    if status in {"auto_accept", "review"} or keep_rejected_candidates:
        edges_f.write(json.dumps(edge, ensure_ascii=False) + "\n")
        seen_edge_ids.add(edge["edge_id"])
        kept = 1
    if status == "review":
        review_f.write(json.dumps(edge, ensure_ascii=False) + "\n")
    return kept, warning_rows


def mock_edges(section: dict[str, Any], node_pool: list[dict[str, Any]]) -> dict[str, Any]:
    current = [node for node in node_pool if node_current_section(node, section)]
    if len(current) < 2:
        return {"edges": []}
    return {
        "edges": [
            {
                "source_node_id": current[0]["node_id"],
                "source_name": current[0]["name"],
                "target_node_id": current[1]["node_id"],
                "target_name": current[1]["name"],
                "type": "EQUATIVE",
                "evidence_spans": [{"role": "primary", "text": str(section.get("text", ""))[:80]}],
                "description": "mock edge",
                "confidence": 0.75,
                "review_recommended": True,
                "review_reason": "mock",
            }
        ]
    }


def write_report(
    path: Path,
    processed_sections: int,
    total_raw: int,
    status_counts: dict[str, int],
    type_counts: dict[str, int],
    warning_counts: dict[str, int],
) -> None:
    lines = [
        "# v4.4 Step 4 Edge Extraction Report",
        "",
        f"- processed sections: {processed_sections}",
        f"- raw edge candidates: {total_raw}",
        "",
        "## Review Status",
    ]
    for key in sorted(status_counts):
        lines.append(f"- {key}: {status_counts[key]}")
    lines.extend(["", "## Edge Types"])
    for key in sorted(type_counts):
        lines.append(f"- {key}: {type_counts[key]}")
    lines.extend(["", "## Top Warnings"])
    if warning_counts:
        for key, value in sorted(warning_counts.items(), key=lambda item: (-item[1], item[0]))[:30]:
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def replay_raw_candidates(
    args: argparse.Namespace,
    sections: list[dict[str, Any]],
    nodes: list[dict[str, Any]],
    node_by_id: dict[str, dict[str, Any]],
    model: str,
) -> None:
    raw_input = args.raw_input or args.raw_output
    raw_records = read_jsonl(raw_input)
    selected_section_ids = {str(section.get("section_node_id") or "") for section in sections}
    section_by_id = {str(section.get("section_node_id") or ""): section for section in sections}

    print(f"[INFO] replay_raw={raw_input} selected_sections={len(selected_section_ids)} nodes={len(nodes)}")
    processed_sections = 0
    total_raw = 0
    status_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    warning_counts: dict[str, int] = {}
    seen_edge_ids: set[str] = set()

    with (
        open_output(args.edges, args.append) as edges_f,
        open_output(args.review, args.append) as review_f,
        open_output(args.warnings, args.append) as warn_f,
    ):
        for raw_record in raw_records:
            section_id = str(raw_record.get("section_node_id") or "")
            if section_id not in selected_section_ids:
                continue
            section = section_by_id[section_id]
            raw = raw_record.get("raw") if isinstance(raw_record.get("raw"), dict) else {}
            raw_edges = raw.get("edges") if isinstance(raw.get("edges"), list) else []
            pool_size = max(int(raw_record.get("node_pool_size") or args.max_node_pool), args.max_node_pool)
            node_pool = build_node_pool(section, nodes, pool_size)
            node_pool_ids = {node.get("node_id") for node in node_pool}
            section_text = relation_section_text(section)
            kept = 0
            warning_rows = 0
            processed_sections += 1

            if args.semantic_augment:
                raw_edges = [*raw_edges, *build_semantic_augmented_raw_edges(section, node_pool)]

            for index, raw_edge in enumerate(raw_edges, start=1):
                if not isinstance(raw_edge, dict):
                    warn_f.write(json.dumps({
                        "section_node_id": section_id,
                        "candidate_index": index,
                        "warnings": ["raw_edge_item_not_object"],
                    }, ensure_ascii=False) + "\n")
                    warning_counts["raw_edge_item_not_object"] = warning_counts.get("raw_edge_item_not_object", 0) + 1
                    continue

                total_raw += 1
                edge, warnings, status = process_raw_edge(
                    raw_edge,
                    section,
                    node_by_id,
                    node_pool_ids,
                    section_text,
                    index,
                    model,
                    "replay",
                    seen_edge_ids,
                )
                kept_delta, warning_delta = write_processed_edge(
                    edge,
                    warnings,
                    status,
                    section_id,
                    edges_f,
                    review_f,
                    warn_f,
                    seen_edge_ids,
                    status_counts,
                    type_counts,
                    warning_counts,
                    args.keep_rejected_candidates,
                )
                kept += kept_delta
                warning_rows += warning_delta

            print(
                f"[OK] replay {section_id} pool={len(node_pool)} "
                f"raw_edges={len(raw_edges)} kept={kept} warnings={warning_rows}"
            )

    write_report(args.report, processed_sections, total_raw, status_counts, type_counts, warning_counts)
    print(f"[OK] replay source -> {raw_input}")
    print(f"[OK] edges -> {args.edges}")
    print(f"[OK] review -> {args.review}")
    print(f"[OK] warnings -> {args.warnings}")
    print(f"[OK] report -> {args.report}")


def main() -> None:
    args = parse_args()
    config = read_config(args.config)
    sections = select_sections(read_jsonl(args.leaf_sections), config, args)
    nodes = read_jsonl(args.nodes)
    node_by_id = {node.get("node_id"): node for node in nodes if node.get("node_id")}
    llm_config = config.get("llm", {})
    model = args.model or llm_config.get("default_model", "deepseek-chat")

    if args.replay_raw:
        replay_raw_candidates(args, sections, nodes, node_by_id, model)
        return

    prompt = args.prompt.read_text(encoding="utf-8")
    base_url = args.base_url or load_env_value("LLM_API_BASE") or llm_config.get("base_url", "https://api.openai.com/v1")
    temperature = args.temperature if args.temperature is not None else float(llm_config.get("temperature", 0.0))
    timeout = args.timeout if args.timeout is not None else float(llm_config.get("timeout_seconds", 120))

    api_key = ""
    if not args.mock:
        api_key = load_env_value("LLM_API_KEY") or load_env_value("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError("LLM_API_KEY not found. Use --mock for local validation.")

    print(f"[INFO] sections={len(sections)} nodes={len(nodes)} model={model} mock={args.mock}")
    processed_sections = 0
    total_raw = 0
    status_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    warning_counts: dict[str, int] = {}
    seen_edge_ids: set[str] = set()
    llm_failed_sections = 0

    with (
        open_output(args.raw_output, args.append) as raw_f,
        open_output(args.edges, args.append) as edges_f,
        open_output(args.review, args.append) as review_f,
        open_output(args.warnings, args.append) as warn_f,
    ):
        for section in sections:
            node_pool = build_node_pool(section, nodes, args.max_node_pool)
            section_id = section.get("section_node_id", "")
            if len(node_pool) < 2:
                print(f"[SKIP] {section_id} node_pool={len(node_pool)}")
                continue

            if args.mock:
                raw = mock_edges(section, node_pool)
                elapsed = 0.0
                mode = "mock"
            else:
                started = time.time()
                raw = None
                mode = "llm"
                errors: list[str] = []
                retry_sizes = [args.max_node_pool, 12, 8, 5]
                retry_sizes = sorted({size for size in retry_sizes if 2 <= size <= args.max_node_pool}, reverse=True)
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
                    if args.semantic_augment:
                        raw = {"edges": build_semantic_augmented_raw_edges(section, node_pool)}
                        mode = "semantic_fallback"
                    else:
                        continue
                elapsed = time.time() - started

            raw_edges = raw.get("edges") if isinstance(raw.get("edges"), list) else []
            raw_f.write(json.dumps({
                "section_node_id": section_id,
                "raw": raw,
                "node_pool_size": len(node_pool),
                "model": model,
                "mode": mode,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }, ensure_ascii=False) + "\n")

            processed_sections += 1
            node_pool_ids = {node.get("node_id") for node in node_pool}
            section_text = relation_section_text(section)
            kept = 0
            warning_rows = 0

            if args.semantic_augment and mode != "semantic_fallback":
                raw_edges = [*raw_edges, *build_semantic_augmented_raw_edges(section, node_pool)]

            for index, raw_edge in enumerate(raw_edges, start=1):
                if not isinstance(raw_edge, dict):
                    warn_f.write(json.dumps({
                        "section_node_id": section_id,
                        "candidate_index": index,
                        "warnings": ["raw_edge_item_not_object"],
                    }, ensure_ascii=False) + "\n")
                    warning_counts["raw_edge_item_not_object"] = warning_counts.get("raw_edge_item_not_object", 0) + 1
                    continue
                total_raw += 1
                edge, warnings, status = process_raw_edge(
                    raw_edge,
                    section,
                    node_by_id,
                    node_pool_ids,
                    section_text,
                    index,
                    model,
                    mode,
                    seen_edge_ids,
                )
                kept_delta, warning_delta = write_processed_edge(
                    edge,
                    warnings,
                    status,
                    section_id,
                    edges_f,
                    review_f,
                    warn_f,
                    seen_edge_ids,
                    status_counts,
                    type_counts,
                    warning_counts,
                    args.keep_rejected_candidates,
                )
                kept += kept_delta
                warning_rows += warning_delta

            print(
                f"[OK] {section_id} mode={mode} elapsed={elapsed:.1f}s "
                f"pool={len(node_pool)} raw_edges={len(raw_edges)} kept={kept} warnings={warning_rows}"
            )

    write_report(args.report, processed_sections, total_raw, status_counts, type_counts, warning_counts)
    if processed_sections == 0 and llm_failed_sections:
        raise RuntimeError(f"Step 4A failed for all processed chunks: llm_failed_sections={llm_failed_sections}")
    print(f"[OK] raw -> {args.raw_output}")
    print(f"[OK] edges -> {args.edges}")
    print(f"[OK] review -> {args.review}")
    print(f"[OK] warnings -> {args.warnings}")
    print(f"[OK] report -> {args.report}")


if __name__ == "__main__":
    main()
