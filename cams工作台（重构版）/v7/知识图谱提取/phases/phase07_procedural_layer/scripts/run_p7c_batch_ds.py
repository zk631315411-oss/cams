from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
PHASES_DIR = PHASE_DIR.parent
P7C_DIR = PHASE_DIR / "phases" / "P7C"

DEFAULT_PACKAGES_DIR = PHASE_DIR / "phases" / "P7B" / "section_packages"
DEFAULT_PROMPT_PATH = P7C_DIR / "prompts" / "section_card_extraction_v1.md"
DEFAULT_COVERAGE_ADJUDICATION_PROMPT_PATH = P7C_DIR / "prompts" / "coverage_adjudication_v1.md"
DEFAULT_OUTPUT_DIR = P7C_DIR / "outputs"
VALIDATOR_PATH = SCRIPT_DIR / "validate_process_cards.py"

API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


def path_for_json(path: Path) -> str:
    """Store paths with forward slashes so JSON readers never see bad backslash escapes."""
    return path.resolve().as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_llm_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_DEEPSEEK_BASE_URL
            return value, base_url, env_name
    names = " / ".join(API_KEY_ENV_NAMES)
    raise RuntimeError(f"{names} are not set; cannot call LLM API.")


def strip_json_fence(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def parse_json_object(raw_text: str) -> dict[str, Any] | None:
    cleaned = strip_json_fence(raw_text)
    if not cleaned:
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    try:
        import json_repair

        return json.loads(json_repair.repair_json(cleaned))
    except Exception:
        return None


def collect_allowed_unit_ids(task: dict[str, Any]) -> list[str]:
    unit_ids: list[str] = []
    seen: set[str] = set()
    for unit in task.get("units") or []:
        unit_id = unit.get("unit_id") if isinstance(unit, dict) else None
        if unit_id and unit_id not in seen:
            seen.add(unit_id)
            unit_ids.append(unit_id)
    if unit_ids:
        return unit_ids
    text = task.get("section_text_with_unit_anchors") or ""
    for unit_id in re.findall(r"\[(v7u_[^|\]]+)\|", text):
        if unit_id not in seen:
            seen.add(unit_id)
            unit_ids.append(unit_id)
    return unit_ids


def build_base_kg_section_summary(task: dict[str, Any]) -> dict[str, Any]:
    """Build a compact KG summary for coverage/de-duplication only.

    The prompt explicitly forbids using this summary as factual evidence. Keep it
    small and section-local so it helps detect missed CP-level topics without
    importing aliases or package-level retrieval material.
    """
    units_by_id: dict[str, dict[str, Any]] = {
        unit.get("unit_id"): unit
        for unit in task.get("units") or []
        if isinstance(unit, dict) and unit.get("unit_id")
    }

    p2b_role_by_pair: dict[tuple[str, str], str] = {}
    for edge in task.get("core_point_unit_edges") or []:
        if not isinstance(edge, dict):
            continue
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        relation_type = edge.get("relation_type")
        if source_id and target_id and relation_type:
            p2b_role_by_pair[(source_id, target_id)] = relation_type

    covered_topics: list[dict[str, Any]] = []
    topic_titles_by_id: dict[str, str] = {}
    for cp in task.get("core_points") or []:
        if not isinstance(cp, dict):
            continue
        cp_id = cp.get("core_point_id")
        ordered_unit_ids: list[str] = []
        seen: set[str] = set()
        for field in ("anchor_unit_ids", "key_unit_ids", "support_unit_ids"):
            for unit_id in cp.get(field) or []:
                if unit_id and unit_id not in seen:
                    seen.add(unit_id)
                    ordered_unit_ids.append(unit_id)

        title_zh = cp.get("title_zh")
        title_en = cp.get("title_en")
        if cp_id:
            topic_titles_by_id[cp_id] = title_zh or title_en or ""

        covered_units: list[dict[str, Any]] = []
        for unit_id in ordered_unit_ids:
            unit = units_by_id.get(unit_id) or {}
            role = p2b_role_by_pair.get((cp_id, unit_id)) if cp_id else None
            covered_units.append(
                {
                    "unit_id": unit_id,
                    "unit_type": unit.get("type"),
                    "kg_role": role,
                }
            )

        covered_topics.append(
            {
                "title_zh": title_zh,
                "title_en": title_en,
                "covered_units": covered_units,
            }
        )

    covered_relations: list[dict[str, Any]] = []
    for edge in task.get("same_section_core_point_edges") or []:
        if not isinstance(edge, dict):
            continue
        source_title = topic_titles_by_id.get(edge.get("source_id"))
        target_title = topic_titles_by_id.get(edge.get("target_id"))
        relation_type = edge.get("relation_type")
        if not source_title or not target_title or not relation_type:
            continue
        covered_relations.append(
            {
                "source_title": source_title,
                "target_title": target_title,
                "relation_type": relation_type,
            }
        )

    return {
        "summary_policy": "coverage_and_dedup_only_not_fact_evidence",
        "covered_topics": covered_topics,
        "covered_relations": covered_relations,
    }


def build_prompt(prompt_template: str, task: dict[str, Any]) -> str:
    allowed_unit_ids = collect_allowed_unit_ids(task)
    base_kg_section_summary = build_base_kg_section_summary(task)
    section_block = f"""## 当前section

section_id: `{task.get('section_id')}`

section_title: `{task.get('section_title')}`

base_kg_section_summary:

```json
{json.dumps(base_kg_section_summary, ensure_ascii=False, indent=2)}
```

section_text_with_unit_anchors:

```text
{task.get('section_text_with_unit_anchors', '')}
```

allowed_unit_ids:

```json
{json.dumps(allowed_unit_ids, ensure_ascii=False, indent=2)}
```
"""
    for marker in ("## 当前section", "## Current Section"):
        if marker in prompt_template:
            return prompt_template.split(marker, 1)[0].rstrip() + "\n\n" + section_block
    return prompt_template.rstrip() + "\n\n" + section_block


def build_coverage_adjudication_prompt(
    prompt_template: str,
    task: dict[str, Any],
    original_payload: dict[str, Any],
) -> str:
    allowed_unit_ids = collect_allowed_unit_ids(task)
    base_kg_section_summary = build_base_kg_section_summary(task)
    section_block = f"""## 当前section

section_id: `{task.get('section_id')}`

section_title: `{task.get('section_title')}`

base_kg_section_summary:

```json
{json.dumps(base_kg_section_summary, ensure_ascii=False, indent=2)}
```

section_text_with_unit_anchors:

```text
{task.get('section_text_with_unit_anchors', '')}
```

allowed_unit_ids:

```json
{json.dumps(allowed_unit_ids, ensure_ascii=False, indent=2)}
```

original_json:

```json
{json.dumps(original_payload, ensure_ascii=False, indent=2)}
```

review_target_candidate_ids:

```json
{json.dumps(kg_only_candidate_ids(original_payload), ensure_ascii=False, indent=2)}
```
"""
    for marker in ("## 当前section", "## Current Section"):
        if marker in prompt_template:
            return prompt_template.split(marker, 1)[0].rstrip() + "\n\n" + section_block
    return prompt_template.rstrip() + "\n\n" + section_block


def kg_only_candidate_ids(payload: dict[str, Any]) -> list[str]:
    return [
        candidate.get("candidate_id")
        for candidate in payload.get("coverage_audit") or []
        if isinstance(candidate, dict)
        and candidate.get("decision") == "kg_only"
        and candidate.get("candidate_id")
    ]


def validate_coverage_adjudication(
    original_payload: dict[str, Any],
    adjudication_patch: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    allowed_top_level = {"section_id", "coverage_adjudication", "promoted_cards"}
    unexpected_fields = set(adjudication_patch) - allowed_top_level
    if unexpected_fields:
        errors.append(f"coverage adjudication patch has unsupported fields: {sorted(unexpected_fields)}")
    if adjudication_patch.get("section_id") != original_payload.get("section_id"):
        errors.append("coverage adjudication changed section_id")

    original_audit = original_payload.get("coverage_audit") or []
    if not isinstance(original_audit, list):
        return errors + ["original payload requires coverage_audit list"]

    def index_by_id(rows: list[Any], field: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
        indexed: dict[str, dict[str, Any]] = {}
        index_errors: list[str] = []
        for idx, row in enumerate(rows, 1):
            if not isinstance(row, dict) or not row.get(field):
                index_errors.append(f"row #{idx} missing {field}")
                continue
            row_id = row[field]
            if row_id in indexed:
                index_errors.append(f"duplicate {field} '{row_id}'")
                continue
            indexed[row_id] = row
        return indexed, index_errors

    original_candidates, candidate_errors = index_by_id(original_audit, "candidate_id")
    errors.extend(f"original coverage_audit: {error}" for error in candidate_errors)
    original_kg_candidates = {
        candidate_id: candidate
        for candidate_id, candidate in original_candidates.items()
        if candidate.get("decision") == "kg_only"
    }

    adjudication_rows = adjudication_patch.get("coverage_adjudication")
    if not isinstance(adjudication_rows, list):
        errors.append("coverage adjudication missing coverage_adjudication list")
        adjudication_rows = []
    adjudication_by_id, adjudication_errors = index_by_id(adjudication_rows, "candidate_id")
    errors.extend(f"coverage_adjudication: {error}" for error in adjudication_errors)
    if set(adjudication_by_id) != set(original_kg_candidates):
        errors.append("coverage_adjudication must review every and only original kg_only candidate")

    promoted_card_ids: set[str] = set()
    promoted_units_by_card: dict[str, set[str]] = {}
    for candidate_id, row in adjudication_by_id.items():
        if row.get("original_decision") != "kg_only":
            errors.append(f"coverage_adjudication {candidate_id} original_decision must be kg_only")
        final_decision = row.get("final_decision")
        if final_decision not in {"kg_only", "p7c_card"}:
            errors.append(f"coverage adjudication invalid final decision for {candidate_id}")
        elif final_decision == "kg_only":
            if row.get("card_id") is not None:
                errors.append(f"coverage adjudication kept {candidate_id} as kg_only but assigned card_id")
        else:
            card_id = row.get("card_id")
            if not card_id:
                errors.append(f"coverage adjudication promoted {candidate_id} without card_id")
            else:
                if card_id in promoted_card_ids:
                    errors.append(f"coverage adjudication assigned card_id {card_id} to multiple candidates")
                promoted_card_ids.add(card_id)
                promoted_units_by_card[card_id] = set(
                    (original_kg_candidates.get(candidate_id) or {}).get("unit_ids") or []
                )
        if not row.get("reason"):
            errors.append(f"coverage_adjudication {candidate_id} missing reason")

    promoted_cards = adjudication_patch.get("promoted_cards")
    if not isinstance(promoted_cards, list):
        errors.append("coverage adjudication missing promoted_cards list")
        promoted_cards = []
    promoted_cards_by_id, card_errors = index_by_id(promoted_cards, "card_id")
    errors.extend(f"promoted_cards: {error}" for error in card_errors)
    original_card_ids = {
        card.get("card_id")
        for card in original_payload.get("cards") or []
        if isinstance(card, dict) and card.get("card_id")
    }
    reused_ids = set(promoted_cards_by_id) & original_card_ids
    if reused_ids:
        errors.append(f"coverage adjudication reused existing card_ids: {sorted(reused_ids)}")
    if set(promoted_cards_by_id) != promoted_card_ids:
        errors.append("promoted_cards do not exactly match promoted candidate card_ids")

    for card_id, card in promoted_cards_by_id.items():
        if card.get("section_id") != original_payload.get("section_id"):
            errors.append(f"coverage adjudication new card {card_id} changed section_id")
        evidence_ids = set(card.get("source_unit_ids") or [])
        for node in card.get("flow_nodes") or []:
            if isinstance(node, dict):
                evidence_ids.update(node.get("evidence_unit_ids") or [])
        for edge in card.get("flow_edges") or []:
            if isinstance(edge, dict):
                evidence_ids.update(edge.get("evidence_unit_ids") or [])
        if not evidence_ids.issubset(promoted_units_by_card.get(card_id, set())):
            errors.append(f"coverage adjudication new card {card_id} uses evidence outside promoted candidate")
    return errors


def merge_coverage_adjudication_patch(
    original_payload: dict[str, Any],
    adjudication_patch: dict[str, Any],
) -> dict[str, Any]:
    """Apply a validated coverage patch without letting the LLM rewrite existing cards."""
    merged = copy.deepcopy(original_payload)
    rows = copy.deepcopy(adjudication_patch.get("coverage_adjudication") or [])
    rows_by_id = {
        row.get("candidate_id"): row
        for row in rows
        if isinstance(row, dict) and row.get("candidate_id")
    }
    for candidate in merged.get("coverage_audit") or []:
        if not isinstance(candidate, dict):
            continue
        row = rows_by_id.get(candidate.get("candidate_id"))
        if not row:
            continue
        candidate["decision"] = row.get("final_decision")
        candidate["card_id"] = row.get("card_id") if row.get("final_decision") == "p7c_card" else None
        candidate["reason"] = row.get("reason")

    merged["coverage_adjudication"] = rows
    merged.setdefault("cards", []).extend(copy.deepcopy(adjudication_patch.get("promoted_cards") or []))
    if merged.get("cards"):
        merged["skip_reason"] = None
    return merged


def normalize_new_adjudicated_cards(
    original_payload: dict[str, Any],
    adjudicated_payload: dict[str, Any],
) -> list[dict[str, str]]:
    original_card_ids = {
        card.get("card_id")
        for card in original_payload.get("cards") or []
        if isinstance(card, dict) and card.get("card_id")
    }
    changes: list[dict[str, str]] = []
    for card in adjudicated_payload.get("cards") or []:
        if not isinstance(card, dict) or card.get("card_id") in original_card_ids:
            continue
        card_id = card.get("card_id") or "<missing card_id>"
        for node in card.get("flow_nodes") or []:
            if not isinstance(node, dict) or node.get("node_category"):
                continue
            node_type = node.get("node_type") or ""
            if node_type.startswith("E"):
                expected_category = "entry"
            elif node_type.startswith("P"):
                expected_category = "process"
            elif node_type.startswith("X"):
                expected_category = "exit"
            elif node_type in {"input", "standard"}:
                expected_category = "auxiliary"
            else:
                continue
            node["node_category"] = expected_category
            changes.append(
                {
                    "card_id": card_id,
                    "field": f"flow_node.{node.get('node_id')}.node_category",
                    "from": "<missing>",
                    "to": expected_category,
                }
            )

        if card.get("candidate_status") != "candidate":
            previous_status = card.get("candidate_status")
            card["candidate_status"] = "candidate"
            changes.append(
                {
                    "card_id": card_id,
                    "field": "candidate_status",
                    "from": str(previous_status) if previous_status is not None else "<missing>",
                    "to": "candidate",
                }
            )
        if "review_status" in card:
            changes.append(
                {
                    "card_id": card_id,
                    "field": "review_status",
                    "from": str(card.get("review_status")),
                    "to": "<removed>",
                }
            )
            card.pop("review_status", None)
        for edge in card.get("flow_edges") or []:
            if not isinstance(edge, dict) or edge.get("derivation"):
                continue
            legacy_strength = edge.get("evidence_strength")
            if legacy_strength == "explicit":
                edge["derivation"] = "explicit_text"
            elif legacy_strength == "functional_dependency":
                edge["derivation"] = "llm_inference"
            if edge.get("derivation"):
                changes.append(
                    {
                        "card_id": card_id,
                        "field": f"flow_edge.{edge.get('edge_id')}.derivation",
                        "from": str(legacy_strength) if legacy_strength is not None else "<missing>",
                        "to": edge["derivation"],
                    }
                )
            edge.pop("evidence_strength", None)
    return changes


def normalize_candidate_payload(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Normalize current P7C candidate fields without assigning P7D review results."""
    changes: list[dict[str, str]] = []
    for card in payload.get("cards") or []:
        if not isinstance(card, dict):
            continue
        card_id = card.get("card_id") or "<missing card_id>"
        if card.get("candidate_status") != "candidate":
            previous = card.get("candidate_status")
            card["candidate_status"] = "candidate"
            changes.append(
                {
                    "card_id": card_id,
                    "field": "candidate_status",
                    "from": str(previous) if previous is not None else "<missing>",
                    "to": "candidate",
                }
            )
        if "review_status" in card:
            changes.append(
                {
                    "card_id": card_id,
                    "field": "review_status",
                    "from": str(card.get("review_status")),
                    "to": "<removed>",
                }
            )
            card.pop("review_status", None)
        for edge in card.get("flow_edges") or []:
            if not isinstance(edge, dict):
                continue
            if not edge.get("derivation"):
                legacy_strength = edge.get("evidence_strength")
                if legacy_strength == "explicit":
                    edge["derivation"] = "explicit_text"
                elif legacy_strength == "functional_dependency":
                    edge["derivation"] = "llm_inference"
                if edge.get("derivation"):
                    changes.append(
                        {
                            "card_id": card_id,
                            "field": f"flow_edge.{edge.get('edge_id')}.derivation",
                            "from": str(legacy_strength) if legacy_strength is not None else "<missing>",
                            "to": edge["derivation"],
                        }
                    )
            edge.pop("evidence_strength", None)
    return changes


def call_model(prompt: str, model: str, max_tokens: int, timeout: float, thinking_effort: str) -> tuple[str, dict[str, Any]]:
    api_key, base_url, env_name = get_llm_config()

    extra_body: dict[str, Any] = {}
    if thinking_effort != "none":
        extra_body = {"thinking": {"type": "enabled", "effort": thinking_effort}}

    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    payload.update(extra_body)

    endpoint = base_url.rstrip("/") + "/chat/completions"
    started = time.time()
    try:
        try:
            import requests

            response = requests.post(
                endpoint,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=timeout,
            )
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code} from {endpoint}: {response.text}")
            response_payload = response.json()
            client = "requests"
        except ImportError:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            request = urllib.request.Request(
                endpoint,
                data=body,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    response_payload = json.loads(response.read().decode("utf-8"))
                client = "urllib"
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"HTTP {exc.code} from {endpoint}: {detail}") from exc
    except Exception:
        raise

    elapsed = round(time.time() - started, 3)
    choices = response_payload.get("choices") or []
    if not choices:
        raise RuntimeError(f"No choices returned: {response_payload}")
    message = choices[0].get("message") or {}
    meta = {
        "model": model,
        "base_url": base_url,
        "endpoint": endpoint,
        "api_key_env": env_name,
        "thinking_effort": thinking_effort,
        "request_extra": extra_body,
        "http_client": client,
        "elapsed_seconds": elapsed,
        "usage": response_payload.get("usage") or {},
    }
    return (message.get("content") or "").strip(), meta


def parse_validation_error_count(report_path: Path) -> int | None:
    if not report_path.exists():
        return None
    match = re.search(r"^error_count:\s*(\d+)\s*$", report_path.read_text(encoding="utf-8-sig"), re.M)
    if not match:
        return None
    return int(match.group(1))


def validate_cards(cards_path: Path, report_path: Path, section_package_path: Path) -> tuple[int, str, int | None]:
    cmd = [
        sys.executable,
        str(VALIDATOR_PATH),
        "--cards",
        str(cards_path),
        "--section-package",
        str(section_package_path),
        "--require-coverage-audit",
        "--report",
        str(report_path),
    ]
    proc = subprocess.run(cmd, cwd=str(PHASE_DIR), text=True, capture_output=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip(), parse_validation_error_count(report_path)


def maybe_validate_cards(
    enabled: bool,
    cards_path: Path,
    report_path: Path,
    section_package_path: Path,
) -> tuple[int, str, int | None]:
    if not enabled:
        return 0, "deferred_to_p7d", 0
    return validate_cards(cards_path, report_path, section_package_path)


def discover_sections(packages_dir: Path) -> list[str]:
    return sorted(path.name for path in packages_dir.iterdir() if path.is_dir() and (path / "task.json").exists())


def parse_sections(raw: str, packages_dir: Path) -> list[str]:
    if raw == "all":
        return discover_sections(packages_dir)
    sections: list[str] = []
    for part in raw.split(","):
        section = part.strip()
        if section:
            sections.append(section)
    return sections


def run_section(
    section_id: str,
    run_dir: Path,
    packages_dir: Path,
    prompt_template: str,
    model: str,
    thinking_effort: str,
    max_tokens: int,
    timeout: float,
    retries: int,
    retry_delay: float,
    validation_retries: int = 1,
    coverage_adjudication: bool = False,
    coverage_adjudication_prompt_template: str | None = None,
    inline_structure_validation: bool = True,
) -> dict[str, Any]:
    package_path = packages_dir / section_id / "task.json"
    section_dir = run_dir / section_id
    section_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = section_dir / "prompt.md"
    raw_path = section_dir / "raw_response.txt"
    cards_path = section_dir / "cards.raw.json"
    manifest_path = section_dir / "run_manifest.json"
    validation_report_path = section_dir / "validation_report.md"

    manifest: dict[str, Any] = {
        "run_id": run_dir.name,
        "section_id": section_id,
        "package_path": path_for_json(package_path),
        "prompt_path": path_for_json(prompt_path),
        "raw_response_path": path_for_json(raw_path),
        "cards_path": path_for_json(cards_path),
        "validation_report_path": path_for_json(validation_report_path),
        "model": model,
        "thinking_effort": thinking_effort,
        "max_tokens": max_tokens,
        "timeout": timeout,
        "retries": retries,
        "retry_delay": retry_delay,
        "validation_retries": validation_retries,
        "inline_structure_validation": inline_structure_validation,
        "structure_validation_owner": "P7C_legacy_diagnostic" if inline_structure_validation else "P7D",
        "coverage_adjudication": coverage_adjudication,
        "input_policy": "section_text_with_unit_anchors_plus_base_kg_summary_for_coverage_plus_allowed_unit_ids",
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }

    try:
        if not package_path.exists():
            raise FileNotFoundError(f"Missing section package: {package_path}")
        task = read_json(package_path)
        manifest["section_title"] = task.get("section_title")
        prompt = build_prompt(prompt_template, task)
        prompt_path.write_text(prompt, encoding="utf-8")
        manifest["prompt_sha256"] = sha256_text(prompt)

        call_attempts: list[dict[str, Any]] = []
        raw = ""
        parsed: dict[str, Any] | None = None
        call_meta: dict[str, Any] = {}
        last_error: Exception | None = None
        for attempt in range(1, max(1, retries + 1) + 1):
            try:
                raw, call_meta = call_model(prompt, model=model, max_tokens=max_tokens, timeout=timeout, thinking_effort=thinking_effort)
                last_error = None
                parsed = parse_json_object(raw)
                if parsed is None:
                    call_attempts.append(
                        {
                            "attempt": attempt,
                            "status": "parse_failed",
                            "raw_length": len(raw),
                        }
                    )
                    if attempt <= retries:
                        time.sleep(retry_delay * attempt)
                    continue
                call_attempts.append({"attempt": attempt, "status": "ok"})
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                call_attempts.append({"attempt": attempt, "status": "failed", "error": repr(exc)})
                if attempt <= retries:
                    time.sleep(retry_delay * attempt)
        manifest["call_attempts"] = call_attempts
        if parsed is None and last_error is not None:
            raise last_error
        raw_path.write_text(raw + "\n", encoding="utf-8")
        manifest["call_meta"] = call_meta
        manifest["raw_sha256"] = sha256_text(raw)

        if parsed is None:
            manifest["status"] = "parse_failed"
            manifest["finished_at"] = datetime.now().isoformat(timespec="seconds")
            write_json(manifest_path, manifest)
            return manifest

        normalize_candidate_payload(parsed)
        write_json(cards_path, parsed)
        manifest["card_count"] = len(parsed.get("cards") or []) if isinstance(parsed, dict) else None
        manifest["skip_reason"] = parsed.get("skip_reason") if isinstance(parsed, dict) else None

        validator_code, validator_output, validation_error_count = maybe_validate_cards(
            inline_structure_validation,
            cards_path,
            validation_report_path,
            package_path,
        )
        validation_attempts: list[dict[str, Any]] = [
            {
                "attempt": 0,
                "kind": "initial",
                "validator_returncode": validator_code,
                "validation_error_count": validation_error_count,
            }
        ]

        for repair_attempt in range(1, max(0, validation_retries) + 1):
            if validator_code != 0 or validation_error_count is None or validation_error_count == 0:
                break

            previous_json = cards_path.read_text(encoding="utf-8-sig")
            validation_report = validation_report_path.read_text(encoding="utf-8-sig")
            repair_prompt = f"""{prompt}

## JSON校验修复

上一次输出已经完成语义抽取，但未通过结构校验。只修复下列校验错误，不得引入当前section之外的事实，不得删除`coverage_audit`中已经识别的合格候选，也不得为了通过校验而把合格card改成`kg_only`。返回完整的严格JSON对象。

validation_report:

```text
{validation_report}
```

previous_json:

```json
{previous_json}
```
"""
            repair_prompt_path = section_dir / f"validation_repair_{repair_attempt}.prompt.md"
            repair_raw_path = section_dir / f"validation_repair_{repair_attempt}.raw.txt"
            repair_prompt_path.write_text(repair_prompt, encoding="utf-8")

            repair_raw = ""
            repair_meta: dict[str, Any] = {}
            repair_error: Exception | None = None
            repair_calls: list[dict[str, Any]] = []
            for call_attempt in range(1, max(1, retries + 1) + 1):
                try:
                    repair_raw, repair_meta = call_model(
                        repair_prompt,
                        model=model,
                        max_tokens=max_tokens,
                        timeout=timeout,
                        thinking_effort=thinking_effort,
                    )
                    repair_calls.append({"attempt": call_attempt, "status": "ok"})
                    repair_error = None
                    break
                except Exception as exc:
                    repair_error = exc
                    repair_calls.append({"attempt": call_attempt, "status": "failed", "error": repr(exc)})
                    if call_attempt <= retries:
                        time.sleep(retry_delay * call_attempt)

            repair_record: dict[str, Any] = {
                "attempt": repair_attempt,
                "kind": "validation_repair",
                "prompt_path": path_for_json(repair_prompt_path),
                "raw_response_path": path_for_json(repair_raw_path),
                "call_attempts": repair_calls,
            }
            if repair_error is not None:
                repair_record["status"] = "call_failed"
                repair_record["error"] = repr(repair_error)
                validation_attempts.append(repair_record)
                break

            repair_raw_path.write_text(repair_raw + "\n", encoding="utf-8")
            repaired = parse_json_object(repair_raw)
            if repaired is None:
                repair_record["status"] = "parse_failed"
                validation_attempts.append(repair_record)
                continue

            initial_raw_path = section_dir / "raw_response.initial.txt"
            if not initial_raw_path.exists():
                initial_raw_path.write_text(raw + "\n", encoding="utf-8")
                manifest["initial_raw_response_path"] = path_for_json(initial_raw_path)
            raw = repair_raw
            parsed = repaired
            raw_path.write_text(raw + "\n", encoding="utf-8")
            write_json(cards_path, parsed)
            validator_code, validator_output, validation_error_count = maybe_validate_cards(
                inline_structure_validation,
                cards_path,
                validation_report_path,
                package_path,
            )
            repair_record.update(
                {
                    "status": "ok" if validation_error_count == 0 else "validation_failed",
                    "call_meta": repair_meta,
                    "validator_returncode": validator_code,
                    "validation_error_count": validation_error_count,
                }
            )
            validation_attempts.append(repair_record)

        manifest["validation_attempts"] = validation_attempts

        coverage_adjudication_failed = False
        if (
            coverage_adjudication
            and validator_code == 0
            and validation_error_count == 0
            and isinstance(parsed, dict)
        ):
            kg_candidate_ids = kg_only_candidate_ids(parsed)
            manifest["coverage_adjudication_candidate_count"] = len(kg_candidate_ids)
            if not kg_candidate_ids:
                manifest["coverage_adjudication_status"] = "skipped_no_kg_only_candidates"
            elif not coverage_adjudication_prompt_template:
                coverage_adjudication_failed = True
                manifest["coverage_adjudication_status"] = "missing_prompt_template"
            else:
                adjudication_prompt = build_coverage_adjudication_prompt(
                    coverage_adjudication_prompt_template,
                    task,
                    parsed,
                )
                adjudication_prompt_path = section_dir / "coverage_adjudication.prompt.md"
                adjudication_raw_path = section_dir / "coverage_adjudication.raw.txt"
                adjudication_patch_path = section_dir / "coverage_adjudication.patch.json"
                adjudication_cards_path = section_dir / "coverage_adjudication.cards.json"
                adjudication_contract_report_path = section_dir / "coverage_adjudication.contract.md"
                adjudication_validation_report_path = section_dir / "coverage_adjudication.validation.md"
                adjudication_prompt_path.write_text(adjudication_prompt, encoding="utf-8")

                adjudication_raw = ""
                adjudication_meta: dict[str, Any] = {}
                adjudication_error: Exception | None = None
                adjudication_calls: list[dict[str, Any]] = []
                for call_attempt in range(1, max(1, retries + 1) + 1):
                    try:
                        adjudication_raw, adjudication_meta = call_model(
                            adjudication_prompt,
                            model=model,
                            max_tokens=max_tokens,
                            timeout=timeout,
                            thinking_effort=thinking_effort,
                        )
                        adjudication_calls.append({"attempt": call_attempt, "status": "ok"})
                        adjudication_error = None
                        break
                    except Exception as exc:
                        adjudication_error = exc
                        adjudication_calls.append(
                            {"attempt": call_attempt, "status": "failed", "error": repr(exc)}
                        )
                        if call_attempt <= retries:
                            time.sleep(retry_delay * call_attempt)

                manifest["coverage_adjudication_prompt_path"] = path_for_json(adjudication_prompt_path)
                manifest["coverage_adjudication_raw_path"] = path_for_json(adjudication_raw_path)
                manifest["coverage_adjudication_patch_path"] = path_for_json(adjudication_patch_path)
                manifest["coverage_adjudication_call_attempts"] = adjudication_calls
                if adjudication_error is not None:
                    coverage_adjudication_failed = True
                    manifest["coverage_adjudication_status"] = "call_failed"
                    manifest["coverage_adjudication_error"] = repr(adjudication_error)
                else:
                    adjudication_raw_path.write_text(adjudication_raw + "\n", encoding="utf-8")
                    adjudication_patch = parse_json_object(adjudication_raw)
                    if adjudication_patch is None:
                        coverage_adjudication_failed = True
                        manifest["coverage_adjudication_status"] = "parse_failed"
                    else:
                        write_json(adjudication_patch_path, adjudication_patch)
                        contract_errors = validate_coverage_adjudication(parsed, adjudication_patch)
                        adjudication_normalizations: list[dict[str, str]] = []
                        adjudicated: dict[str, Any] | None = None
                        if not contract_errors:
                            adjudicated = merge_coverage_adjudication_patch(parsed, adjudication_patch)
                            adjudication_normalizations = normalize_new_adjudicated_cards(
                                parsed,
                                adjudicated,
                            )
                        contract_lines = [
                            "# P7C Coverage Adjudication Contract Report",
                            "",
                            f"error_count: {len(contract_errors)}",
                            "",
                        ]
                        if contract_errors:
                            contract_lines.extend(["## Errors", ""])
                            contract_lines.extend(f"- {error}" for error in contract_errors)
                        else:
                            contract_lines.append("No contract errors.")
                        adjudication_contract_report_path.write_text(
                            "\n".join(contract_lines) + "\n",
                            encoding="utf-8",
                        )
                        if adjudicated is not None:
                            write_json(adjudication_cards_path, adjudicated)
                            (
                                adjudication_validator_code,
                                adjudication_validator_output,
                                adjudication_validation_error_count,
                            ) = maybe_validate_cards(
                                inline_structure_validation,
                                adjudication_cards_path,
                                adjudication_validation_report_path,
                                package_path,
                            )
                        else:
                            adjudication_validator_code = 0
                            adjudication_validator_output = "skipped_contract_failure"
                            adjudication_validation_error_count = 0
                        adjudication_validation_attempts: list[dict[str, Any]] = [
                            {
                                "attempt": 0,
                                "kind": "initial",
                                "contract_error_count": len(contract_errors),
                                "validator_returncode": adjudication_validator_code,
                                "validation_error_count": adjudication_validation_error_count,
                            }
                        ]
                        for repair_attempt in range(1, max(0, validation_retries) + 1):
                            if (
                                contract_errors
                                or adjudication_validator_code != 0
                                or adjudication_validation_error_count is None
                                or adjudication_validation_error_count == 0
                            ):
                                break

                            adjudication_validation_report = adjudication_validation_report_path.read_text(
                                encoding="utf-8-sig"
                            )
                            previous_adjudication_patch = adjudication_patch_path.read_text(
                                encoding="utf-8-sig"
                            )
                            adjudication_repair_prompt = f"""{adjudication_prompt}

## 裁决JSON结构修复

裁决决定已经完成且保护合同已通过。只修复下列新增card结构错误，必须保持所有`coverage_adjudication`决定和所有`promoted_cards`的业务内容不变。不得删除提升候选或把它改回`kg_only`。仍按Coverage补丁合同返回严格JSON，不得回显或修改首次抽取正本。

validation_report:

```text
{adjudication_validation_report}
```

previous_adjudication_patch:

```json
{previous_adjudication_patch}
```
"""
                            adjudication_repair_prompt_path = (
                                section_dir / f"coverage_adjudication.validation_repair_{repair_attempt}.prompt.md"
                            )
                            adjudication_repair_raw_path = (
                                section_dir / f"coverage_adjudication.validation_repair_{repair_attempt}.raw.txt"
                            )
                            adjudication_repair_prompt_path.write_text(
                                adjudication_repair_prompt,
                                encoding="utf-8",
                            )

                            adjudication_repair_raw = ""
                            adjudication_repair_meta: dict[str, Any] = {}
                            adjudication_repair_error: Exception | None = None
                            adjudication_repair_calls: list[dict[str, Any]] = []
                            for call_attempt in range(1, max(1, retries + 1) + 1):
                                try:
                                    adjudication_repair_raw, adjudication_repair_meta = call_model(
                                        adjudication_repair_prompt,
                                        model=model,
                                        max_tokens=max_tokens,
                                        timeout=timeout,
                                        thinking_effort=thinking_effort,
                                    )
                                    adjudication_repair_calls.append(
                                        {"attempt": call_attempt, "status": "ok"}
                                    )
                                    adjudication_repair_error = None
                                    break
                                except Exception as exc:
                                    adjudication_repair_error = exc
                                    adjudication_repair_calls.append(
                                        {
                                            "attempt": call_attempt,
                                            "status": "failed",
                                            "error": repr(exc),
                                        }
                                    )
                                    if call_attempt <= retries:
                                        time.sleep(retry_delay * call_attempt)

                            adjudication_repair_record: dict[str, Any] = {
                                "attempt": repair_attempt,
                                "kind": "validation_repair",
                                "prompt_path": path_for_json(adjudication_repair_prompt_path),
                                "raw_response_path": path_for_json(adjudication_repair_raw_path),
                                "call_attempts": adjudication_repair_calls,
                            }
                            if adjudication_repair_error is not None:
                                adjudication_repair_record["status"] = "call_failed"
                                adjudication_repair_record["error"] = repr(adjudication_repair_error)
                                adjudication_validation_attempts.append(adjudication_repair_record)
                                break

                            adjudication_repair_raw_path.write_text(
                                adjudication_repair_raw + "\n",
                                encoding="utf-8",
                            )
                            repaired_patch = parse_json_object(adjudication_repair_raw)
                            if repaired_patch is None:
                                adjudication_repair_record["status"] = "parse_failed"
                                adjudication_validation_attempts.append(adjudication_repair_record)
                                continue

                            repaired_contract_errors = validate_coverage_adjudication(
                                parsed,
                                repaired_patch,
                            )
                            if repaired_contract_errors:
                                adjudication_repair_record.update(
                                    {
                                        "status": "contract_failed",
                                        "contract_errors": repaired_contract_errors,
                                    }
                                )
                                adjudication_validation_attempts.append(adjudication_repair_record)
                                break

                            adjudication_patch = repaired_patch
                            adjudicated = merge_coverage_adjudication_patch(parsed, repaired_patch)
                            adjudication_normalizations.extend(
                                normalize_new_adjudicated_cards(parsed, adjudicated)
                            )
                            contract_errors = repaired_contract_errors
                            write_json(adjudication_patch_path, repaired_patch)
                            write_json(adjudication_cards_path, adjudicated)
                            (
                                adjudication_validator_code,
                                adjudication_validator_output,
                                adjudication_validation_error_count,
                            ) = maybe_validate_cards(
                                inline_structure_validation,
                                adjudication_cards_path,
                                adjudication_validation_report_path,
                                package_path,
                            )
                            adjudication_repair_record.update(
                                {
                                    "status": (
                                        "ok"
                                        if adjudication_validation_error_count == 0
                                        else "validation_failed"
                                    ),
                                    "call_meta": adjudication_repair_meta,
                                    "contract_error_count": 0,
                                    "validator_returncode": adjudication_validator_code,
                                    "validation_error_count": adjudication_validation_error_count,
                                }
                            )
                            adjudication_validation_attempts.append(adjudication_repair_record)

                        contract_lines = [
                            "# P7C Coverage Adjudication Contract Report",
                            "",
                            f"error_count: {len(contract_errors)}",
                            "",
                        ]
                        if contract_errors:
                            contract_lines.extend(["## Errors", ""])
                            contract_lines.extend(f"- {error}" for error in contract_errors)
                        else:
                            contract_lines.append("No contract errors.")
                        adjudication_contract_report_path.write_text(
                            "\n".join(contract_lines) + "\n",
                            encoding="utf-8",
                        )
                        manifest["coverage_adjudication_call_meta"] = adjudication_meta
                        manifest["coverage_adjudication_normalizations"] = adjudication_normalizations
                        manifest["coverage_adjudication_validation_attempts"] = (
                            adjudication_validation_attempts
                        )
                        manifest["coverage_adjudication_contract_errors"] = contract_errors
                        manifest["coverage_adjudication_validation_error_count"] = (
                            adjudication_validation_error_count
                        )
                        manifest["coverage_adjudication_validator_output"] = adjudication_validator_output
                        manifest["coverage_adjudication_contract_report_path"] = path_for_json(
                            adjudication_contract_report_path
                        )
                        manifest["coverage_adjudication_validation_report_path"] = path_for_json(
                            adjudication_validation_report_path
                        )
                        if (
                            contract_errors
                            or adjudication_validator_code != 0
                            or adjudication_validation_error_count is None
                            or adjudication_validation_error_count > 0
                        ):
                            coverage_adjudication_failed = True
                            manifest["coverage_adjudication_status"] = "rejected"
                        else:
                            original_card_count = len(parsed.get("cards") or [])
                            if adjudicated is None:
                                raise RuntimeError("coverage adjudication merge missing after successful contract validation")
                            parsed = adjudicated
                            write_json(cards_path, parsed)
                            validator_code, validator_output, validation_error_count = maybe_validate_cards(
                                inline_structure_validation,
                                cards_path,
                                validation_report_path,
                                package_path,
                            )
                            final_card_count = len(parsed.get("cards") or [])
                            manifest["coverage_adjudication_status"] = "accepted"
                            manifest["coverage_adjudication_promoted_card_count"] = (
                                final_card_count - original_card_count
                            )

        manifest["raw_sha256"] = sha256_text(raw)
        manifest["card_count"] = len(parsed.get("cards") or []) if isinstance(parsed, dict) else None
        manifest["skip_reason"] = parsed.get("skip_reason") if isinstance(parsed, dict) else None
        manifest["validator_returncode"] = validator_code if inline_structure_validation else None
        manifest["validation_error_count"] = validation_error_count if inline_structure_validation else None
        manifest["validator_output"] = validator_output
        manifest["structure_validation_status"] = "completed" if inline_structure_validation else "deferred_to_p7d"
        if not inline_structure_validation:
            manifest["status"] = "coverage_adjudication_failed" if coverage_adjudication_failed else "ok"
        elif validator_code != 0:
            manifest["status"] = "validation_command_failed"
        elif validation_error_count is None:
            manifest["status"] = "validation_report_unreadable"
        elif validation_error_count > 0:
            manifest["status"] = "validation_failed"
        elif coverage_adjudication_failed:
            manifest["status"] = "coverage_adjudication_failed"
        else:
            manifest["status"] = "ok"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = repr(exc)

    manifest["finished_at"] = datetime.now().isoformat(timespec="seconds")
    write_json(manifest_path, manifest)
    return manifest


def write_summary(run_dir: Path, manifests: list[dict[str, Any]]) -> None:
    summary_json = run_dir / "run_summary.json"
    summary_md = run_dir / "run_summary.md"
    write_json(summary_json, manifests)

    lines = [
        "# P7C Batch Run Summary",
        "",
        "| section | status | cards | validation_errors | coverage | promoted | title | skip_reason |",
        "|---|---:|---:|---:|---|---:|---|---|",
    ]
    for row in sorted(manifests, key=lambda item: item.get("section_id") or ""):
        lines.append(
            "| {section} | {status} | {cards} | {errors} | {coverage} | {promoted} | {title} | {skip} |".format(
                section=row.get("section_id", ""),
                status=row.get("status", ""),
                cards=row.get("card_count", ""),
                errors=(
                    row.get("validation_error_count", "")
                    if row.get("structure_validation_status") != "deferred_to_p7d"
                    else "P7D"
                ),
                coverage=row.get("coverage_adjudication_status", ""),
                promoted=row.get("coverage_adjudication_promoted_card_count", 0),
                title=(row.get("section_title") or "").replace("|", "\\|"),
                skip=(row.get("skip_reason") or "").replace("|", "\\|"),
            )
        )
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch-run P7C DS extraction over section packages.")
    parser.add_argument("--sections", default="all", help="Comma-separated section IDs or 'all'.")
    parser.add_argument("--packages-dir", default=str(DEFAULT_PACKAGES_DIR))
    parser.add_argument("--prompt", default=str(DEFAULT_PROMPT_PATH))
    parser.add_argument(
        "--coverage-adjudication-prompt",
        default=str(DEFAULT_COVERAGE_ADJUDICATION_PROMPT_PATH),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--thinking-effort", default="none", choices=["none", "low", "medium", "high"])
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--max-tokens", type=int, default=20000)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-delay", type=float, default=5.0)
    parser.add_argument("--validation-retries", type=int, default=1)
    parser.add_argument(
        "--inline-structure-validation",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Legacy P7C diagnostic only. Formal structure validation belongs to P7D.",
    )
    parser.add_argument(
        "--coverage-adjudication",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    packages_dir = Path(args.packages_dir)
    sections = parse_sections(args.sections, packages_dir)
    run_id = args.run_id or f"p7c_ds_{args.thinking_effort}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir = Path(args.output_dir) / run_id

    if not sections:
        raise SystemExit("No sections selected.")

    run_dir.mkdir(parents=True, exist_ok=True)
    plan = {
        "run_id": run_id,
        "run_dir": path_for_json(run_dir),
        "sections": sections,
        "section_count": len(sections),
        "packages_dir": path_for_json(packages_dir),
        "prompt": path_for_json(Path(args.prompt)),
        "coverage_adjudication_prompt": path_for_json(Path(args.coverage_adjudication_prompt)),
        "model": args.model,
        "thinking_effort": args.thinking_effort,
        "concurrency": args.concurrency,
        "max_tokens": args.max_tokens,
        "timeout": args.timeout,
        "retries": args.retries,
        "retry_delay": args.retry_delay,
        "validation_retries": args.validation_retries,
        "inline_structure_validation": args.inline_structure_validation,
        "structure_validation_owner": "P7C_legacy_diagnostic" if args.inline_structure_validation else "P7D",
        "coverage_adjudication": args.coverage_adjudication,
        "input_policy": "section_text_with_unit_anchors_plus_base_kg_summary_for_coverage_plus_allowed_unit_ids",
        "planned_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_json(run_dir / "run_plan.json", plan)

    if args.dry_run:
        print(f"Dry run only. Planned {len(sections)} sections under {run_dir}")
        return

    prompt_template = Path(args.prompt).read_text(encoding="utf-8-sig")
    coverage_adjudication_prompt_template = None
    if args.coverage_adjudication:
        coverage_adjudication_prompt_template = Path(args.coverage_adjudication_prompt).read_text(
            encoding="utf-8-sig"
        )
    manifests: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        futures = {
            executor.submit(
                run_section,
                section,
                run_dir,
                packages_dir,
                prompt_template,
                args.model,
                args.thinking_effort,
                args.max_tokens,
                args.timeout,
                args.retries,
                args.retry_delay,
                args.validation_retries,
                args.coverage_adjudication,
                coverage_adjudication_prompt_template,
                args.inline_structure_validation,
            ): section
            for section in sections
        }
        for future in as_completed(futures):
            manifest = future.result()
            manifests.append(manifest)
            print(
                "{section}: {status}, cards={cards}, errors={errors}".format(
                    section=manifest.get("section_id"),
                    status=manifest.get("status"),
                    cards=manifest.get("card_count"),
                    errors=manifest.get("validation_error_count"),
                )
            )

    write_summary(run_dir, manifests)
    print(f"Batch complete: {run_dir}")


if __name__ == "__main__":
    main()
