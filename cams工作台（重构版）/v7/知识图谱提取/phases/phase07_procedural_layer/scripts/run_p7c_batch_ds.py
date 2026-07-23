from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
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
DEFAULT_S1_PROMPT_PATH = P7C_DIR / "prompts" / "proposition_discovery_v1.md"
DEFAULT_S2_PROMPT_PATH = P7C_DIR / "prompts" / "kg_boundary_and_graph_v1.md"
DEFAULT_S2_NEW_PROMPT_PATH = P7C_DIR / "prompts" / "kg_boundary_adjudication_v1.md"
DEFAULT_S3_PROMPT_PATH = P7C_DIR / "prompts" / "semantic_graph_construction_v1.md"
DEFAULT_S12_PROMPT_PATH = P7C_DIR / "prompts" / "proposition_gap_fill_v1.md"
DEFAULT_COVERAGE_ADJUDICATION_PROMPT_PATH = P7C_DIR / "prompts" / "coverage_adjudication_v1.md"
DEFAULT_PROCESS_IR_PROMPT_PATH = P7C_DIR / "prompts" / "process_ir_v1.md"
DEFAULT_S3_FROM_IR_PROMPT_PATH = P7C_DIR / "prompts" / "process_ir_to_cards_v1.md"
DEFAULT_OUTPUT_DIR = P7C_DIR / "outputs"
VALIDATOR_PATH = SCRIPT_DIR / "validate_process_cards.py"
PROCESS_IR_COMPILER_PATH = SCRIPT_DIR / "process_ir_compiler_v1.py"

API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
CURRENT_SECTION_MARKERS = ("## 当前section", "## 当前 section", "## Current Section")


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


def replace_current_section(prompt_template: str, section_block: str) -> str:
    """Replace a prompt's runtime-input suffix, accepting legacy heading variants."""
    positions = [
        (prompt_template.index(marker), marker)
        for marker in CURRENT_SECTION_MARKERS
        if marker in prompt_template
    ]
    if positions:
        position, _ = min(positions)
        return prompt_template[:position].rstrip() + "\n\n" + section_block
    return prompt_template.rstrip() + "\n\n" + section_block


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


def collect_unit_evidence_text(task: dict[str, Any]) -> dict[str, str]:
    """Return the source text available for each P7B unit.

    S1 uses the anchored section text as its reading source. This index is used
    only after generation to verify that every claimed short quote is grounded
    in the unit it cites.
    """
    evidence_text: dict[str, str] = {}
    for unit in task.get("units") or []:
        if not isinstance(unit, dict):
            continue
        unit_id = unit.get("unit_id")
        if not unit_id:
            continue
        pieces = [
            str(unit.get(field) or "").strip()
            for field in ("en_quote", "knowledge_zh")
            if str(unit.get(field) or "").strip()
        ]
        if pieces:
            evidence_text[str(unit_id)] = "\n".join(pieces)
    return evidence_text


def build_base_kg_section_summary(task: dict[str, Any]) -> dict[str, Any]:
    """Build a compact KG summary for coverage/de-duplication only.

    Section-local only — used for dedup reference, not as factual evidence.
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
        source_id = edge.get("source_id")
        target_id = edge.get("target_id")
        source_title = topic_titles_by_id.get(source_id)
        target_title = topic_titles_by_id.get(target_id)
        relation_type = edge.get("relation_type")
        # Guard: both CPs must be known within this section's topic set
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
    return replace_current_section(prompt_template, section_block)


def build_s1_prompt(prompt_template: str, task: dict[str, Any]) -> str:
    """S1: candidate-card discovery from anchored section text only."""
    section_block = f"""## 当前section

section_id: `{task.get('section_id')}`

section_title: `{task.get('section_title')}`

section_text_with_unit_anchors:

```text
{task.get('section_text_with_unit_anchors', '')}
```
"""
    return replace_current_section(prompt_template, section_block)


def build_kg_projection(task: dict[str, Any]) -> dict[str, Any]:
    """KG projection for S2 v2: section-local KG fields from P7B task.json, no processing."""
    def project_rows(rows: object, fields: tuple[str, ...]) -> list[dict[str, Any]]:
        if not isinstance(rows, list):
            return []
        return [
            {field: row.get(field) for field in fields}
            for row in rows
            if isinstance(row, dict)
        ]

    return {
        "kg_capability_profile": "base_kg_atomic_cp_v1",
        "units": project_rows(task.get("units"), ("unit_id", "type")),
        "core_points": project_rows(
            task.get("core_points"),
            ("core_point_id", "title_zh", "title_en"),
        ),
        "core_point_unit_edges": project_rows(
            task.get("core_point_unit_edges"),
            ("source_id", "target_id", "relation_type"),
        ),
        "same_section_core_point_edges": project_rows(
            task.get("same_section_core_point_edges"),
            ("source_id", "target_id", "relation_type"),
        ),
    }


def build_s2_prompt(
    prompt_template: str,
    task: dict[str, Any],
    propositions: list[dict[str, Any]],
    *,
    kg_input_version: str = "summary_v1",
) -> str:
    """S2: KG boundary — kg_input_version='summary_v1'|'projection_v1'."""
    allowed_unit_ids = collect_allowed_unit_ids(task)
    if kg_input_version not in {"summary_v1", "projection_v1"}:
        raise ValueError(f"Unsupported S2 KG input version: {kg_input_version}")

    if kg_input_version == "projection_v1":
        kg_data = build_kg_projection(task)
        kg_block = f"""kg_projection:

```json
{json.dumps(kg_data, ensure_ascii=False, indent=2)}
```"""
    else:
        kg_data = build_base_kg_section_summary(task)
        kg_block = f"""base_kg_section_summary:

```json
{json.dumps(kg_data, ensure_ascii=False, indent=2)}
```"""

    section_block = f"""## 当前section

section_id: `{task.get('section_id')}`

section_title: `{task.get('section_title')}`

{kg_block}

section_text_with_unit_anchors:

```text
{task.get('section_text_with_unit_anchors', '')}
```

allowed_unit_ids:

```json
{json.dumps(allowed_unit_ids, ensure_ascii=False, indent=2)}
```

## S1 发现的命题

```json
{json.dumps(propositions, ensure_ascii=False, indent=2)}
```
"""
    return replace_current_section(prompt_template, section_block)


def build_s12_prompt(
    prompt_template: str,
    task: dict[str, Any],
    s11_propositions: list[dict[str, Any]],
) -> str:
    """S1.2: gap fill — section text + S1.1 propositions, no KG summary, no allowed_unit_ids."""
    section_block = f"""## 当前section

section_id: `{task.get('section_id')}`

section_title: `{task.get('section_title')}`

section_text_with_unit_anchors:

```text
{task.get('section_text_with_unit_anchors', '')}
```

## S1.1 候选列表

```json
{json.dumps(s11_propositions, ensure_ascii=False, indent=2)}
```
"""
    prompt_with_props = prompt_template.replace(
        "S11_PROPOSITIONS_JSON",
        json.dumps(s11_propositions, ensure_ascii=False, indent=2),
    )
    for marker in ("## 当前section", "## Current Section"):
        if marker in prompt_with_props:
            return prompt_with_props.split(marker, 1)[0].rstrip() + "\n\n" + section_block
    return prompt_with_props.rstrip() + "\n\n" + section_block


def build_s3_prompt(
    prompt_template: str,
    task: dict[str, Any],
    passed_candidates: list[dict[str, Any]],
) -> str:
    """S3: semantic graph construction — passed candidates from S2."""
    allowed_unit_ids = collect_allowed_unit_ids(task)
    section_block = f"""## 当前section

section_id: `{task.get('section_id')}`

section_title: `{task.get('section_title')}`

section_text_with_unit_anchors:

```text
{task.get('section_text_with_unit_anchors', '')}
```

allowed_unit_ids:

```json
{json.dumps(allowed_unit_ids, ensure_ascii=False, indent=2)}
```

## S2 通过的候选命题

```json
{json.dumps(passed_candidates, ensure_ascii=False, indent=2)}
```
"""
    prompt_with_props = prompt_template.replace(
        "<S2_PASSED_CANDIDATES_JSON>",
        json.dumps(passed_candidates, ensure_ascii=False, indent=2),
    )
    return replace_current_section(prompt_with_props, section_block)


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
    kg_only_ids = kg_only_candidate_ids(original_payload)
    if not kg_only_ids:
        section_block += (
            "**本轮没有需要复核的kg_only候选。请仅执行独立全量重扫描"
            "（第一优先）和已有card图完整性检查（第三优先），跳过第二优先。"
            "若发现遗漏关系，通过new_candidates/new_cards/card_supplements补全。**\n\n"
        )
    for marker in ("## 当前section", "## Current Section"):
        if marker in prompt_template:
            return prompt_template.split(marker, 1)[0].rstrip() + "\n\n" + section_block
    return prompt_template.rstrip() + "\n\n" + section_block


def build_process_ir_prompt(
    prompt_template: str,
    task: dict[str, Any],
    s1_propositions: list[dict[str, Any]],
) -> str:
    """S2 Process IR: section text + S1 merged candidates only. No KG, no allowed_unit_ids."""
    section_block = f"""## 当前section

section_id: `{task.get('section_id')}`

section_title: `{task.get('section_title')}`

section_text_with_unit_anchors:

```text
{task.get('section_text_with_unit_anchors', '')}
```

## S1 合并候选列表

```json
{json.dumps(s1_propositions, ensure_ascii=False, indent=2)}
```
"""
    return replace_current_section(prompt_template, section_block)


def build_s3_from_ir_prompt(
    prompt_template: str,
    task: dict[str, Any],
    process_ir: dict[str, Any],
) -> str:
    """S3: take Process IR + section text + allowed_unit_ids, output cards.raw.json."""
    allowed_unit_ids = collect_allowed_unit_ids(task)
    section_block = f"""## 当前section

section_id: `{task.get('section_id')}`

section_title: `{task.get('section_title')}`

section_text_with_unit_anchors:

```text
{task.get('section_text_with_unit_anchors', '')}
```

allowed_unit_ids:

```json
{json.dumps(allowed_unit_ids, ensure_ascii=False, indent=2)}
```

## S2 Process IR

```json
{json.dumps(process_ir, ensure_ascii=False, indent=2)}
```
"""
    return replace_current_section(prompt_template, section_block)


def validate_s3_to_cards_payload(
    payload: dict[str, Any],
    section_id: str,
    allowed_unit_ids: set[str],
    process_ir: dict[str, Any],
) -> list[str]:
    """Validate S3 cards output against the card structure contract."""
    errors: list[str] = []
    if payload.get("section_id") != section_id:
        errors.append(f"S3 section_id mismatch: expected {section_id}, got {payload.get('section_id')}")

    cards = payload.get("cards")
    if not isinstance(cards, list):
        return errors + ["S3 cards must be a list"]

    card_ids: set[str] = set()
    ir_episodes = process_ir.get("episodes") or []
    ir_element_ids: set[str] = set()
    for ep in ir_episodes:
        if isinstance(ep, dict):
            for elem in (ep.get("elements") or []):
                if isinstance(elem, dict) and elem.get("element_id"):
                    ir_element_ids.add(elem["element_id"])

    for idx, card in enumerate(cards, 1):
        owner = f"S3 cards[{idx}]"
        if not isinstance(card, dict):
            errors.append(f"{owner} must be an object")
            continue
        cid = str(card.get("card_id") or "")
        if not cid:
            errors.append(f"{owner} missing card_id")
        elif cid in card_ids:
            errors.append(f"{owner} duplicate card_id {cid}")
        else:
            card_ids.add(cid)
        if card.get("section_id") != section_id:
            errors.append(f"{owner} section_id mismatch")
        if card.get("candidate_status") != "candidate":
            errors.append(f"{owner} candidate_status must be candidate")
        if card.get("card_nature") not in {"execution", "assessment", "risk_indicator", "control"}:
            errors.append(f"{owner} invalid card_nature")

        for node in card.get("flow_nodes") or []:
            if not isinstance(node, dict):
                continue
            for forbidden in ("derivation", "review_status"):
                if forbidden in node:
                    errors.append(f"{owner} node {node.get('node_id')} must not declare {forbidden}")
            for unit_id in (node.get("evidence_unit_ids") or []):
                if str(unit_id) not in allowed_unit_ids:
                    errors.append(f"{owner} node uses out-of-section evidence {unit_id}")

        for edge in card.get("flow_edges") or []:
            if not isinstance(edge, dict):
                continue
            for forbidden in ("derivation", "evidence_strength", "review_status"):
                if forbidden in edge:
                    errors.append(f"{owner} edge {edge.get('edge_id')} must not declare {forbidden}")
            for unit_id in (edge.get("evidence_unit_ids") or []):
                if str(unit_id) not in allowed_unit_ids:
                    errors.append(f"{owner} edge uses out-of-section evidence {unit_id}")

    # coverage_audit consistency
    audit = payload.get("coverage_audit") or []
    ir_audit = process_ir.get("candidate_audit") or []
    if len(audit) != len(ir_audit):
        errors.append(f"S3 coverage_audit count {len(audit)} != IR candidate_audit count {len(ir_audit)}")

    return errors


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
    allowed_unit_ids: list[str] | set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    allowed_top_level = {
        "section_id",
        "coverage_adjudication",
        "new_candidates",
        "new_cards",
        "card_supplements",
    }
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

    original_cards, original_card_errors = index_by_id(
        original_payload.get("cards") or [],
        "card_id",
    )
    errors.extend(f"original cards: {error}" for error in original_card_errors)
    original_card_ids = set(original_cards)

    if allowed_unit_ids is None:
        section_unit_ids: set[str] = {
            unit_id
            for candidate in original_candidates.values()
            for unit_id in candidate.get("unit_ids") or []
        }
        for card in original_cards.values():
            section_unit_ids.update(card.get("source_unit_ids") or [])
    else:
        section_unit_ids = set(allowed_unit_ids)

    new_candidates = adjudication_patch.get("new_candidates")
    if not isinstance(new_candidates, list):
        errors.append("coverage adjudication missing new_candidates list")
        new_candidates = []
    new_candidates_by_id, new_candidate_errors = index_by_id(new_candidates, "candidate_id")
    errors.extend(f"new_candidates: {error}" for error in new_candidate_errors)
    reused_candidate_ids = set(new_candidates_by_id) & set(original_candidates)
    if reused_candidate_ids:
        errors.append(
            f"coverage adjudication reused existing candidate_ids: {sorted(reused_candidate_ids)}"
        )

    new_cards = adjudication_patch.get("new_cards")
    if not isinstance(new_cards, list):
        errors.append("coverage adjudication missing new_cards list")
        new_cards = []
    new_cards_by_id, new_card_errors = index_by_id(new_cards, "card_id")
    errors.extend(f"new_cards: {error}" for error in new_card_errors)
    reused_card_ids = set(new_cards_by_id) & original_card_ids
    if reused_card_ids:
        errors.append(f"coverage adjudication reused existing card_ids: {sorted(reused_card_ids)}")

    supplements = adjudication_patch.get("card_supplements")
    if not isinstance(supplements, list):
        errors.append("coverage adjudication missing card_supplements list")
        supplements = []
    supplements_by_id, supplement_id_errors = index_by_id(supplements, "patch_id")
    errors.extend(f"card_supplements: {error}" for error in supplement_id_errors)
    supplement_targets: dict[str, dict[str, Any]] = {}
    for patch_id, supplement in supplements_by_id.items():
        card_id = supplement.get("card_id")
        if not card_id:
            errors.append(f"card_supplements {patch_id} missing card_id")
            continue
        if card_id not in original_card_ids:
            errors.append(
                f"card_supplements {patch_id} must target an existing original card_id"
            )
            continue
        if card_id in supplement_targets:
            errors.append(f"card_supplements target card_id {card_id} more than once")
            continue
        supplement_targets[card_id] = supplement

    all_card_ids = original_card_ids | set(new_cards_by_id)
    referenced_new_card_ids: set[str] = set()
    referenced_supplement_card_ids: set[str] = set()

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
            elif card_id not in all_card_ids:
                errors.append(
                    f"coverage adjudication {candidate_id} references unknown card_id {card_id}"
                )
            elif card_id in original_card_ids:
                referenced_supplement_card_ids.add(card_id)
            else:
                referenced_new_card_ids.add(card_id)
        if not row.get("reason"):
            errors.append(f"coverage_adjudication {candidate_id} missing reason")

    for candidate_id, candidate in new_candidates_by_id.items():
        candidate_units = set(candidate.get("unit_ids") or [])
        if not candidate_units:
            errors.append(f"new_candidates {candidate_id} missing unit_ids")
        elif not candidate_units.issubset(section_unit_ids):
            errors.append(f"new_candidates {candidate_id} uses evidence outside current section")
        if candidate.get("decision") != "p7c_card":
            errors.append(f"new_candidates {candidate_id} decision must be p7c_card")
        if not candidate.get("proposition"):
            errors.append(f"new_candidates {candidate_id} missing proposition")
        if not candidate.get("reason"):
            errors.append(f"new_candidates {candidate_id} missing reason")
        origin_candidate_ids = candidate.get("origin_candidate_ids")
        if not isinstance(origin_candidate_ids, list):
            errors.append(f"new_candidates {candidate_id} missing origin_candidate_ids list")
        else:
            unknown_origins = set(origin_candidate_ids) - set(original_candidates)
            if unknown_origins:
                errors.append(
                    f"new_candidates {candidate_id} references unknown origin candidates: {sorted(unknown_origins)}"
                )
        card_id = candidate.get("card_id")
        if not card_id or card_id not in all_card_ids:
            errors.append(f"new_candidates {candidate_id} references unknown card_id {card_id}")
        elif card_id in original_card_ids:
            referenced_supplement_card_ids.add(card_id)
        else:
            referenced_new_card_ids.add(card_id)

    for card_id, card in new_cards_by_id.items():
        if card.get("section_id") != original_payload.get("section_id"):
            errors.append(f"coverage adjudication new card {card_id} changed section_id")
        if card.get("card_nature") not in {"execution", "assessment", "risk_indicator", "control"}:
            errors.append(f"coverage adjudication new card {card_id} has invalid card_nature")
        if card.get("candidate_status") != "candidate":
            errors.append(f"coverage adjudication new card {card_id} must remain candidate")
        evidence_ids = set(card.get("source_unit_ids") or [])
        for node in card.get("flow_nodes") or []:
            if isinstance(node, dict):
                evidence_ids.update(node.get("evidence_unit_ids") or [])
        for edge in card.get("flow_edges") or []:
            if isinstance(edge, dict):
                evidence_ids.update(edge.get("evidence_unit_ids") or [])
        if not evidence_ids.issubset(section_unit_ids):
            errors.append(f"coverage adjudication new card {card_id} uses evidence outside current section")

    unreferenced_new_cards = set(new_cards_by_id) - referenced_new_card_ids
    if unreferenced_new_cards:
        errors.append(
            f"coverage adjudication new_cards lack candidate references: {sorted(unreferenced_new_cards)}"
        )

    for patch_id, supplement in supplements_by_id.items():
        card_id = supplement.get("card_id")
        if card_id not in original_cards:
            continue
        if not supplement.get("reason"):
            errors.append(f"card_supplements {patch_id} missing reason")
        origin_candidate_ids = supplement.get("origin_candidate_ids")
        if not isinstance(origin_candidate_ids, list):
            errors.append(f"card_supplements {patch_id} missing origin_candidate_ids list")
        else:
            known_candidate_ids = set(original_candidates) | set(new_candidates_by_id)
            unknown_origins = set(origin_candidate_ids) - known_candidate_ids
            if unknown_origins:
                errors.append(
                    f"card_supplements {patch_id} references unknown origin candidates: {sorted(unknown_origins)}"
                )

        added_nodes = supplement.get("add_flow_nodes")
        added_edges = supplement.get("add_flow_edges")
        added_source_units = supplement.get("add_source_unit_ids")
        if not isinstance(added_nodes, list):
            errors.append(f"card_supplements {patch_id} missing add_flow_nodes list")
            added_nodes = []
        if not isinstance(added_edges, list):
            errors.append(f"card_supplements {patch_id} missing add_flow_edges list")
            added_edges = []
        if not isinstance(added_source_units, list):
            errors.append(f"card_supplements {patch_id} missing add_source_unit_ids list")
            added_source_units = []
        if not added_nodes and not added_edges:
            errors.append(f"card_supplements {patch_id} must add at least one node or edge")

        original_card = original_cards[card_id]
        original_node_ids = {
            node.get("node_id")
            for node in original_card.get("flow_nodes") or []
            if isinstance(node, dict) and node.get("node_id")
        }
        original_edge_ids = {
            edge.get("edge_id")
            for edge in original_card.get("flow_edges") or []
            if isinstance(edge, dict) and edge.get("edge_id")
        }
        added_node_ids: set[str] = set()
        added_evidence_ids: set[str] = set()
        for index, node in enumerate(added_nodes, 1):
            if not isinstance(node, dict) or not node.get("node_id"):
                errors.append(f"card_supplements {patch_id} node #{index} missing node_id")
                continue
            node_id = node["node_id"]
            if node_id in original_node_ids or node_id in added_node_ids:
                errors.append(f"card_supplements {patch_id} duplicates node_id {node_id}")
            added_node_ids.add(node_id)
            added_evidence_ids.update(node.get("evidence_unit_ids") or [])

        added_edge_ids: set[str] = set()
        combined_node_ids = original_node_ids | added_node_ids
        for index, edge in enumerate(added_edges, 1):
            if not isinstance(edge, dict) or not edge.get("edge_id"):
                errors.append(f"card_supplements {patch_id} edge #{index} missing edge_id")
                continue
            edge_id = edge["edge_id"]
            if edge_id in original_edge_ids or edge_id in added_edge_ids:
                errors.append(f"card_supplements {patch_id} duplicates edge_id {edge_id}")
            added_edge_ids.add(edge_id)
            if edge.get("source") not in combined_node_ids or edge.get("target") not in combined_node_ids:
                errors.append(
                    f"card_supplements {patch_id} edge {edge_id} references unknown added/original node"
                )
            added_evidence_ids.update(edge.get("evidence_unit_ids") or [])

        added_source_set = set(added_source_units)
        if not (added_evidence_ids | added_source_set).issubset(section_unit_ids):
            errors.append(f"card_supplements {patch_id} uses evidence outside current section")
        final_source_units = set(original_card.get("source_unit_ids") or []) | added_source_set
        if not added_evidence_ids.issubset(final_source_units):
            errors.append(
                f"card_supplements {patch_id} added evidence is missing from add_source_unit_ids"
            )

    unreferenced_supplements = set(supplement_targets) - referenced_supplement_card_ids
    if unreferenced_supplements:
        errors.append(
            "coverage adjudication card_supplements lack new/promoted candidate references: "
            f"{sorted(unreferenced_supplements)}"
        )
    return errors


def merge_coverage_adjudication_patch(
    original_payload: dict[str, Any],
    adjudication_patch: dict[str, Any],
) -> dict[str, Any]:
    """Apply a validated additive coverage patch without rewriting existing graph content."""
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

    merged.setdefault("coverage_audit", []).extend(
        copy.deepcopy(adjudication_patch.get("new_candidates") or [])
    )

    cards_by_id = {
        card.get("card_id"): card
        for card in merged.get("cards") or []
        if isinstance(card, dict) and card.get("card_id")
    }
    for supplement in adjudication_patch.get("card_supplements") or []:
        if not isinstance(supplement, dict):
            continue
        card = cards_by_id.get(supplement.get("card_id"))
        if not card:
            continue
        card.setdefault("flow_nodes", []).extend(copy.deepcopy(supplement.get("add_flow_nodes") or []))
        card.setdefault("flow_edges", []).extend(copy.deepcopy(supplement.get("add_flow_edges") or []))
        source_unit_ids = card.setdefault("source_unit_ids", [])
        for unit_id in supplement.get("add_source_unit_ids") or []:
            if unit_id not in source_unit_ids:
                source_unit_ids.append(unit_id)

    merged["coverage_adjudication"] = rows
    merged.setdefault("cards", []).extend(copy.deepcopy(adjudication_patch.get("new_cards") or []))
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


def normalize_three_stage_candidate_payload(payload: dict[str, Any]) -> list[dict[str, str]]:
    """Normalize candidate metadata while removing extraction-time edge review hints."""
    changes = normalize_candidate_payload(payload)
    for card in payload.get("cards") or []:
        if not isinstance(card, dict):
            continue
        card_id = card.get("card_id") or "<missing card_id>"
        for edge in card.get("flow_edges") or []:
            if not isinstance(edge, dict):
                continue
            for field in ("derivation", "evidence_strength", "review_status"):
                if field not in edge:
                    continue
                changes.append(
                    {
                        "card_id": card_id,
                        "field": f"flow_edge.{edge.get('edge_id')}.{field}",
                        "from": str(edge.get(field)),
                        "to": "<removed>",
                    }
                )
                edge.pop(field, None)
    return changes


def validate_s1_discovery_payload(
    payload: dict[str, Any],
    allowed_unit_ids: set[str],
    unit_evidence_text: dict[str, str] | None = None,
) -> list[str]:
    def normalized(value: object) -> str:
        return re.sub(r"\s+", " ", str(value or "")).strip().casefold()

    def validate_text_list(owner: str, value: object) -> list[str]:
        if not isinstance(value, list):
            return [f"{owner} must be a list"]
        if any(not isinstance(item, str) or not item.strip() for item in value):
            return [f"{owner} must contain only non-empty strings"]
        return []

    errors: list[str] = []
    propositions = payload.get("propositions")
    if not isinstance(propositions, list):
        return ["S1 propositions must be a list"]
    seen: set[str] = set()
    for index, proposition in enumerate(propositions, 1):
        owner = f"S1 propositions[{index}]"
        if not isinstance(proposition, dict):
            errors.append(f"{owner} must be an object")
            continue
        candidate_id = str(proposition.get("candidate_id") or "")
        if not candidate_id:
            errors.append(f"{owner} missing candidate_id")
        elif candidate_id in seen:
            errors.append(f"{owner} duplicate candidate_id {candidate_id}")
        else:
            seen.add(candidate_id)
        if not str(proposition.get("proposition") or "").strip():
            errors.append(f"{owner} missing proposition")
        relation_cues = proposition.get("relation_cues")
        errors.extend(validate_text_list(f"{owner}.relation_cues", relation_cues))
        if isinstance(relation_cues, list) and not relation_cues:
            errors.append(f"{owner}.relation_cues must be non-empty")
        unit_ids = proposition.get("unit_ids")
        if not isinstance(unit_ids, list) or not unit_ids:
            errors.append(f"{owner}.unit_ids must be a non-empty list")
        else:
            if len(unit_ids) != len(set(unit_ids)):
                errors.append(f"{owner}.unit_ids contains duplicates")
            for unit_id in unit_ids:
                if unit_id not in allowed_unit_ids:
                    errors.append(f"{owner} uses out-of-section evidence {unit_id}")
        errors.extend(validate_text_list(f"{owner}.source_quotes", proposition.get("source_quotes")))
        if isinstance(proposition.get("source_quotes"), list) and not proposition.get("source_quotes"):
            errors.append(f"{owner}.source_quotes must be non-empty")

        frame = proposition.get("candidate_frame")
        if not isinstance(frame, dict):
            errors.append(f"{owner}.candidate_frame must be an object")
        else:
            focal = frame.get("focal_handling_or_judgment")
            if not isinstance(focal, str) or not focal.strip():
                errors.append(f"{owner}.candidate_frame.focal_handling_or_judgment must be a non-empty string")
            peripheral_values: list[list[str]] = []
            for field in ("trigger_or_context", "basis_or_condition", "outcomes_or_paths"):
                value = frame.get(field)
                errors.extend(validate_text_list(f"{owner}.candidate_frame.{field}", value))
                if isinstance(value, list):
                    peripheral_values.append(value)
            if peripheral_values and not any(peripheral_values):
                errors.append(f"{owner}.candidate_frame requires a trigger, basis, outcome, or path")

        evidence_spans = proposition.get("evidence_spans")
        if not isinstance(evidence_spans, list) or not evidence_spans:
            errors.append(f"{owner}.evidence_spans must be a non-empty list")
            evidence_spans = []
        cited_span_ids: set[str] = set()
        normalized_span_quotes: set[str] = set()
        for span_index, span in enumerate(evidence_spans, 1):
            span_owner = f"{owner}.evidence_spans[{span_index}]"
            if not isinstance(span, dict):
                errors.append(f"{span_owner} must be an object")
                continue
            span_unit_id = span.get("unit_id")
            quote = span.get("quote")
            if span_unit_id not in allowed_unit_ids:
                errors.append(f"{span_owner} uses out-of-section evidence {span_unit_id}")
            if isinstance(unit_ids, list) and span_unit_id not in unit_ids:
                errors.append(f"{span_owner}.unit_id must be listed in unit_ids")
            if not isinstance(quote, str) or not quote.strip():
                errors.append(f"{span_owner}.quote must be a non-empty string")
            elif unit_evidence_text and span_unit_id in unit_evidence_text:
                if normalized(quote) not in normalized(unit_evidence_text[span_unit_id]):
                    errors.append(f"{span_owner}.quote is not found in cited unit text")
            if isinstance(quote, str) and quote.strip():
                normalized_span_quotes.add(normalized(quote))
            if isinstance(span_unit_id, str):
                cited_span_ids.add(span_unit_id)
        if isinstance(unit_ids, list) and set(unit_ids) - cited_span_ids:
            errors.append(f"{owner}.evidence_spans must cover every unit_id")
        source_quotes = proposition.get("source_quotes")
        if isinstance(source_quotes, list):
            for quote_index, quote in enumerate(source_quotes, 1):
                if isinstance(quote, str) and quote.strip() and normalized(quote) not in normalized_span_quotes:
                    errors.append(f"{owner}.source_quotes[{quote_index}] must match an evidence_spans quote")

        if proposition.get("induction") not in {None, "cross_unit"}:
            errors.append(f"{owner} invalid induction {proposition.get('induction')}")
        cross_unit_basis = proposition.get("cross_unit_basis")
        if proposition.get("induction") == "cross_unit":
            if not isinstance(cross_unit_basis, dict):
                errors.append(f"{owner}.cross_unit_basis must be an object for cross_unit induction")
            else:
                for field in ("rule_unit_ids", "positive_example_unit_ids", "negative_example_unit_ids"):
                    basis_ids = cross_unit_basis.get(field)
                    if not isinstance(basis_ids, list) or not basis_ids:
                        errors.append(f"{owner}.cross_unit_basis.{field} must be a non-empty list")
                        continue
                    for unit_id in basis_ids:
                        if unit_id not in allowed_unit_ids:
                            errors.append(f"{owner}.cross_unit_basis.{field} uses out-of-section evidence {unit_id}")
                        if isinstance(unit_ids, list) and unit_id not in unit_ids:
                            errors.append(f"{owner}.cross_unit_basis.{field} must reference unit_ids")
        elif cross_unit_basis is not None:
            errors.append(f"{owner}.cross_unit_basis requires induction=cross_unit")
    return errors


def validate_s12_gap_payload(
    payload: dict[str, Any],
    section_id: str,
    allowed_unit_ids: set[str],
    unit_evidence_text: dict[str, str],
    s11_propositions: list[dict[str, Any]],
) -> list[str]:
    """Validate S1.2 gaps against the S1 evidence contract and merge boundary."""
    errors: list[str] = []
    if payload.get("section_id") != section_id:
        errors.append("S1.2 section_id mismatch")

    gap_propositions = payload.get("gap_propositions")
    if not isinstance(gap_propositions, list):
        return errors + ["S1.2 gap_propositions must be a list"]

    errors.extend(
        error.replace("S1 propositions", "S1.2 gap_propositions")
        for error in validate_s1_discovery_payload(
            {"propositions": gap_propositions},
            allowed_unit_ids,
            unit_evidence_text,
        )
    )

    existing_ids = {
        str(row.get("candidate_id") or "")
        for row in s11_propositions
        if isinstance(row, dict) and row.get("candidate_id")
    }
    existing_propositions = {
        re.sub(r"\s+", " ", str(row.get("proposition") or "")).strip().casefold()
        for row in s11_propositions
        if isinstance(row, dict) and row.get("proposition")
    }

    for index, proposition in enumerate(gap_propositions, 1):
        owner = f"S1.2 gap_propositions[{index}]"
        if not isinstance(proposition, dict):
            continue
        candidate_id = str(proposition.get("candidate_id") or "")
        if candidate_id and not candidate_id.startswith("s1c_gap_"):
            errors.append(f"{owner}.candidate_id must start with s1c_gap_")
        if candidate_id in existing_ids:
            errors.append(f"{owner}.candidate_id collides with an S1.1 candidate")

        normalized_proposition = re.sub(
            r"\s+", " ", str(proposition.get("proposition") or "")
        ).strip().casefold()
        if normalized_proposition and normalized_proposition in existing_propositions:
            errors.append(f"{owner} duplicates an S1.1 proposition")

        gap_evidence = proposition.get("gap_evidence")
        if not isinstance(gap_evidence, dict):
            errors.append(f"{owner}.gap_evidence must be an object")
            continue
        compared_ids = gap_evidence.get("compared_with_candidate_ids")
        if not isinstance(compared_ids, list):
            errors.append(f"{owner}.gap_evidence.compared_with_candidate_ids must be a list")
        else:
            if any(not isinstance(item, str) or not item for item in compared_ids):
                errors.append(
                    f"{owner}.gap_evidence.compared_with_candidate_ids must contain only non-empty strings"
                )
            if len(compared_ids) != len(set(compared_ids)):
                errors.append(f"{owner}.gap_evidence.compared_with_candidate_ids contains duplicates")
            unknown_ids = set(compared_ids) - existing_ids
            if unknown_ids:
                errors.append(
                    f"{owner}.gap_evidence references unknown S1.1 candidates: {sorted(unknown_ids)}"
                )
            if existing_ids and not compared_ids:
                errors.append(
                    f"{owner}.gap_evidence.compared_with_candidate_ids must identify at least one S1.1 candidate"
                )
        if not str(gap_evidence.get("gap_reason") or "").strip():
            errors.append(f"{owner}.gap_evidence.gap_reason must be a non-empty string")
    return errors


def validate_s2_boundary_payload(
    payload: dict[str, Any],
    propositions: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    decisions = payload.get("boundary_decisions")
    if not isinstance(decisions, list):
        return ["S2 boundary_decisions must be a list"]
    expected_ids = [str(row.get("candidate_id") or "") for row in propositions]
    actual_ids: list[str] = []
    for index, decision in enumerate(decisions, 1):
        owner = f"S2 boundary_decisions[{index}]"
        if not isinstance(decision, dict):
            errors.append(f"{owner} must be an object")
            continue
        actual_ids.append(str(decision.get("candidate_id") or ""))
        if decision.get("decision") not in {"p7c_candidate", "kg_only"}:
            errors.append(f"{owner} invalid decision {decision.get('decision')}")
        if not str(decision.get("reason") or "").strip():
            errors.append(f"{owner} missing reason")
    if len(actual_ids) != len(set(actual_ids)):
        errors.append("S2 boundary_decisions contains duplicate candidate IDs")
    missing = set(expected_ids) - set(actual_ids)
    extra = set(actual_ids) - set(expected_ids)
    if missing:
        errors.append(
            f"S2 boundary_decisions missing S1 candidates: {sorted(missing)}"
        )
    if extra:
        # Non-fatal: S2 may output extra candidates; they are ignored downstream
        pass
    return errors


def validate_s3_construction_payload(
    payload: dict[str, Any],
    passed_candidates: list[dict[str, Any]],
    section_id: str,
    allowed_unit_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    audit = payload.get("construction_audit")
    cards = payload.get("cards")
    if not isinstance(audit, list):
        return ["S3 construction_audit must be a list"]
    if not isinstance(cards, list):
        return ["S3 cards must be a list"]

    expected_ids = {
        str(row.get("candidate", {}).get("candidate_id") or "")
        for row in passed_candidates
        if isinstance(row, dict)
    }
    card_ids: list[str] = []
    for index, card in enumerate(cards, 1):
        owner = f"S3 cards[{index}]"
        if not isinstance(card, dict):
            errors.append(f"{owner} must be an object")
            continue
        card_id = str(card.get("card_id") or "")
        if not card_id:
            errors.append(f"{owner} missing card_id")
        card_ids.append(card_id)
        if card.get("section_id") != section_id:
            errors.append(f"{owner} section_id does not match {section_id}")
        for node in card.get("flow_nodes") or []:
            if isinstance(node, dict):
                for unit_id in node.get("evidence_unit_ids") or []:
                    if unit_id not in allowed_unit_ids:
                        errors.append(f"{owner} node uses out-of-section evidence {unit_id}")
        for edge in card.get("flow_edges") or []:
            if not isinstance(edge, dict):
                continue
            for forbidden in ("derivation", "evidence_strength", "review_status"):
                if forbidden in edge:
                    errors.append(f"{owner} edge {edge.get('edge_id')} must not declare {forbidden}")
            for unit_id in edge.get("evidence_unit_ids") or []:
                if unit_id not in allowed_unit_ids:
                    errors.append(f"{owner} edge uses out-of-section evidence {unit_id}")
    if len(card_ids) != len(set(card_ids)):
        errors.append("S3 cards contains duplicate card IDs")
    card_id_set = set(card_ids)

    actual_ids: list[str] = []
    referenced_cards: set[str] = set()
    for index, row in enumerate(audit, 1):
        owner = f"S3 construction_audit[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{owner} must be an object")
            continue
        candidate_id = str(row.get("candidate_id") or "")
        actual_ids.append(candidate_id)
        status = row.get("construction_status")
        if status not in {"graphed", "ungraphable"}:
            errors.append(f"{owner} invalid construction_status {status}")
        refs = row.get("card_ids") or []
        if not isinstance(refs, list):
            errors.append(f"{owner}.card_ids must be a list")
            refs = []
        if len(refs) != len(set(refs)):
            errors.append(f"{owner}.card_ids contains duplicates")
        if status == "graphed" and not refs:
            errors.append(f"{owner} graphed status requires card_ids")
        if status == "ungraphable" and refs:
            errors.append(f"{owner} ungraphable status requires empty card_ids")
        for card_id in refs:
            if card_id not in card_id_set:
                errors.append(f"{owner} references unknown card_id {card_id}")
            else:
                referenced_cards.add(card_id)
        if not str(row.get("reason") or "").strip():
            errors.append(f"{owner} missing reason")
    if len(actual_ids) != len(set(actual_ids)):
        errors.append("S3 construction_audit contains duplicate candidate IDs")
    if set(actual_ids) != expected_ids:
        errors.append(
            "S3 construction_audit must cover every passed candidate exactly once: "
            f"expected={sorted(expected_ids)}, actual={sorted(actual_ids)}"
        )
    for card_id in sorted(card_id_set - referenced_cards):
        errors.append(f"S3 output card {card_id} is not referenced by construction_audit")
    return errors


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


def run_section_two_stage(
    section_id: str,
    run_dir: Path,
    packages_dir: Path,
    s1_template: str,
    s2_template: str,
    model: str,
    thinking_effort: str,
    max_tokens: int,
    timeout: float,
    retries: int,
    retry_delay: float,
    validation_retries: int,
    inline_structure_validation: bool = False,
) -> dict[str, Any]:
    """Two-stage P7C extraction: S1 proposition discovery → S2 KG boundary + graph.

    Does NOT call Coverage Adjudication — S2's built-in gap check replaces it.
    """
    task_path = packages_dir / section_id / "task.json"
    task = read_json(task_path)
    section_dir = run_dir / section_id
    section_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "section_id": section_id,
        "section_title": task.get("section_title"),
        "status": "pending",
        "two_stage": True,
    }

    # === Stage 1: Proposition Discovery ===
    s1_prompt = build_s1_prompt(s1_template, task)
    s1_prompt_path = section_dir / "s1_prompt.md"
    s1_raw_path = section_dir / "s1_raw_response.txt"
    s1_props_path = section_dir / "s1_propositions.json"
    s1_prompt_path.write_text(s1_prompt, encoding="utf-8")

    s1_raw = ""
    s1_error = None
    s1_parsed: dict[str, Any] = {}
    for attempt in range(1, retries + 1):
        try:
            s1_raw, s1_call_meta = call_model(s1_prompt, model, max_tokens, timeout, thinking_effort)
        except Exception as exc:
            s1_error = exc
            if attempt < retries:
                time.sleep(retry_delay)
            continue
        try:
            s1_parsed = parse_json_object(s1_raw)
        except Exception:
            s1_parsed = {}
            if attempt < retries:
                time.sleep(retry_delay)
            continue
        if isinstance(s1_parsed, dict) and s1_parsed.get("propositions") is not None:
            s1_error = None
            break

    s1_raw_path.write_text(s1_raw, encoding="utf-8")
    propositions: list[dict[str, Any]] = s1_parsed.get("propositions") or []
    manifest["s1_proposition_count"] = len(propositions)
    manifest["s1_call_meta"] = s1_call_meta if s1_raw else None

    if s1_error:
        # S1 failed entirely — write empty result and return
        manifest["status"] = "s1_failed"
        manifest["s1_error"] = repr(s1_error)
        empty: dict[str, Any] = {
            "section_id": section_id,
            "section_title": task.get("section_title"),
            "coverage_audit": [],
            "cards": [],
            "skip_reason": "S1 proposition discovery failed.",
        }
        write_json(section_dir / "cards.raw.json", empty)
        write_json(section_dir / "run_manifest.json", manifest)
        return manifest

    write_json(s1_props_path, s1_parsed)

    # === Stage 2: KG Boundary + Graph Construction ===
    s2_prompt = build_s2_prompt(s2_template, task, propositions)
    s2_prompt_path = section_dir / "s2_prompt.md"
    s2_raw_path = section_dir / "s2_raw_response.txt"
    s2_prompt_path.write_text(s2_prompt, encoding="utf-8")

    s2_raw = ""
    s2_error = None
    s2_parsed: dict[str, Any] = {}
    for attempt in range(1, retries + 1):
        try:
            s2_raw, s2_call_meta = call_model(s2_prompt, model, max_tokens, timeout, thinking_effort)
        except Exception as exc:
            s2_error = exc
            if attempt < retries:
                time.sleep(retry_delay)
            continue
        try:
            s2_parsed = parse_json_object(s2_raw)
        except Exception:
            s2_parsed = {}
            if attempt < retries:
                time.sleep(retry_delay)
            continue
        if isinstance(s2_parsed, dict):
            s2_error = None
            break

    s2_raw_path.write_text(s2_raw, encoding="utf-8")
    manifest["s2_call_meta"] = s2_call_meta if s2_raw else None

    if s2_error or not isinstance(s2_parsed, dict):
        manifest["status"] = "s2_failed"
        manifest["s2_error"] = repr(s2_error) if s2_error else "parse_failed"
        empty = {
            "section_id": section_id,
            "section_title": task.get("section_title"),
            "coverage_audit": [],
            "cards": [],
            "skip_reason": "S2 KG boundary + graph construction failed.",
        }
        write_json(section_dir / "cards.raw.json", empty)
        write_json(section_dir / "run_manifest.json", manifest)
        return manifest

    # === Normalize (in-place, return value is change log only) ===
    normalize_candidate_payload(s2_parsed)
    parsed: dict[str, Any] = s2_parsed

    # === Validation (optional, inline) ===
    cards_path = section_dir / "cards.raw.json"
    write_json(cards_path, parsed)
    validation_report_path = section_dir / "validation_report.md"
    validation_error_count = 0
    if inline_structure_validation:
        validator_code, validator_output, validation_error_count = validate_cards(
            cards_path, validation_report_path, task_path
        )
        if validation_error_count > 0 and validation_retries > 0:
            # Repair loop
            repair_prompt = s2_prompt + (
                f"\n\n## 结构校验错误\n\n{validator_output}\n\n"
                "修复上述错误后重新输出完整的有效JSON。"
            )
            for repair_attempt in range(1, validation_retries + 1):
                try:
                    repair_raw, _ = call_model(repair_prompt, model, max_tokens, timeout, thinking_effort)
                    repair_parsed = parse_json_object(repair_raw)
                    if isinstance(repair_parsed, dict):
                        normalize_candidate_payload(repair_parsed)
                        parsed = repair_parsed
                        write_json(cards_path, parsed)
                        _, _, validation_error_count = validate_cards(
                            cards_path, validation_report_path, task_path
                        )
                        if validation_error_count == 0:
                            break
                except Exception:
                    pass

    manifest["status"] = "ok" if validation_error_count == 0 else "validation_errors"
    manifest["card_count"] = len(parsed.get("cards") or [])
    manifest["validation_error_count"] = validation_error_count
    write_json(section_dir / "run_manifest.json", manifest)
    return manifest


def run_section_three_stage(
    section_id: str,
    run_dir: Path,
    packages_dir: Path,
    s1_template: str,
    s2_new_template: str,
    s3_template: str,
    model: str,
    thinking_effort: str,
    max_tokens: int,
    timeout: float,
    retries: int,
    retry_delay: float,
    validation_retries: int,
    inline_structure_validation: bool = False,
    s12_prompt_template: str | None = None,
    s1_model: str | None = None,
    s1_thinking_effort: str | None = None,
    s12_model: str | None = None,
    s12_thinking_effort: str | None = None,
    stop_after_s12: bool = False,
) -> dict[str, Any]:
    """Three/four-stage P7C: S1 discovery → [S1.2 gap fill] → S2 KG boundary → S3 graph construction."""
    task_path = packages_dir / section_id / "task.json"
    task = read_json(task_path)
    section_dir = run_dir / section_id
    section_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "section_id": section_id,
        "section_title": task.get("section_title"),
        "status": "pending",
        "three_stage": s12_prompt_template is None,
        "four_stage": s12_prompt_template is not None,
    }

    allowed_unit_ids = set(collect_allowed_unit_ids(task))
    unit_evidence_text = collect_unit_evidence_text(task)

    def _call_and_parse(
        prompt: str,
        label: str,
        contract_validator: Any | None = None,
        stage_model: str | None = None,
        stage_thinking_effort: str | None = None,
    ) -> tuple[dict[str, Any] | None, str, object | None]:
        raw = ""
        error: object | None = None
        effective_model = stage_model or model
        effective_thinking = stage_thinking_effort or thinking_effort
        manifest_key = re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_")
        for attempt in range(1, retries + 1):
            try:
                raw, call_meta = call_model(
                    prompt,
                    effective_model,
                    max_tokens,
                    timeout,
                    effective_thinking,
                )
                manifest[f"{manifest_key}_call"] = call_meta
            except Exception as exc:
                error = exc
                if attempt < retries:
                    time.sleep(retry_delay)
                continue
            try:
                parsed = parse_json_object(raw)
            except Exception:
                if attempt < retries:
                    time.sleep(retry_delay)
                continue
            if isinstance(parsed, dict):
                contract_errors = contract_validator(parsed) if contract_validator else []
                if not contract_errors:
                    return parsed, raw, None
                error = ValueError(f"{label} contract errors: {'; '.join(contract_errors)}")
                if attempt < retries:
                    time.sleep(retry_delay)
                continue
        return None, raw, error

    # === Stage 1.1: Proposition Discovery ===
    s1_prompt = build_s1_prompt(s1_template, task)
    (section_dir / "s1_prompt.md").write_text(s1_prompt, encoding="utf-8")
    s1_parsed, s1_raw, s1_err = _call_and_parse(
        s1_prompt,
        "S1.1",
        lambda payload: (
            ([] if payload.get("section_id") == section_id else ["S1.1 section_id mismatch"])
            + validate_s1_discovery_payload(payload, allowed_unit_ids, unit_evidence_text)
        ),
        s1_model,
        s1_thinking_effort,
    )
    (section_dir / "s1_raw_response.txt").write_text(s1_raw, encoding="utf-8")

    if s1_parsed is None:
        manifest["status"] = "s1_failed"
        manifest["s1_error"] = repr(s1_err)
        write_json(section_dir / "cards.raw.json", {"section_id": section_id, "cards": [], "coverage_audit": []})
        write_json(section_dir / "run_manifest.json", manifest)
        return manifest

    propositions = s1_parsed.get("propositions") or []
    manifest["s1_proposition_count"] = len(propositions)
    if s12_prompt_template is None:
        write_json(section_dir / "s1_propositions.json", s1_parsed)
    else:
        write_json(section_dir / "s11_propositions.json", s1_parsed)

    # === Stage 1.2: Gap Fill (four-stage only) ===
    if s12_prompt_template is not None:
        s12_prompt = build_s12_prompt(s12_prompt_template, task, propositions)
        (section_dir / "s12_prompt.md").write_text(s12_prompt, encoding="utf-8")
        s12_parsed, s12_raw, s12_err = _call_and_parse(
            s12_prompt,
            "S1.2",
            lambda payload: validate_s12_gap_payload(
                payload,
                section_id,
                allowed_unit_ids,
                unit_evidence_text,
                propositions,
            ),
            s12_model,
            s12_thinking_effort,
        )
        (section_dir / "s12_raw_response.txt").write_text(s12_raw, encoding="utf-8")

        if s12_parsed is not None:
            gap_props = s12_parsed.get("gap_propositions") or []
            manifest["s12_gap_count"] = len(gap_props)
            write_json(section_dir / "s12_gap_propositions.json", s12_parsed)
            propositions = list(propositions) + list(gap_props)
            manifest["s1_merged_count"] = len(propositions)
            merged_payload = dict(s1_parsed)
            merged_payload["propositions"] = propositions
            if gap_props:
                merged_payload["skip_reason"] = None
            write_json(section_dir / "s1_propositions.json", merged_payload)
        else:
            manifest["status"] = "s12_failed"
            manifest["s12_error"] = repr(s12_err) if s12_err else "parse_failed"
            manifest["card_count"] = 0
            write_json(section_dir / "cards.raw.json", {"section_id": section_id, "cards": [], "coverage_audit": []})
            write_json(section_dir / "run_manifest.json", manifest)
            return manifest

        if stop_after_s12:
            manifest["status"] = "ok"
            manifest["completed_through"] = "s12"
            manifest["card_count"] = 0
            write_json(section_dir / "run_manifest.json", manifest)
            return manifest

    if not propositions:
        manifest["status"] = "ok"
        manifest["card_count"] = 0
        write_json(section_dir / "cards.raw.json", {"section_id": section_id, "cards": [], "coverage_audit": []})
        write_json(section_dir / "run_manifest.json", manifest)
        return manifest

    # === Stage 2: KG Boundary Adjudication ===
    s2_prompt = build_s2_prompt(s2_new_template, task, propositions)
    (section_dir / "s2_prompt.md").write_text(s2_prompt, encoding="utf-8")
    def _validate_s2_lenient(payload: dict[str, Any]) -> list[str]:
        if payload.get("section_id") != section_id:
            return ["S2 section_id mismatch"]
        errors = validate_s2_boundary_payload(payload, propositions)
        # Missing candidates are non-fatal — pipeline continues with partial coverage
        fatal = [e for e in errors if "duplicate" in e or "invalid decision" in e]
        non_fatal = [e for e in errors if e not in fatal]
        if non_fatal:
            manifest["s2_partial_coverage_warning"] = non_fatal
        return fatal

    s2_parsed, s2_raw, s2_err = _call_and_parse(
        s2_prompt,
        "S2",
        _validate_s2_lenient,
    )
    (section_dir / "s2_raw_response.txt").write_text(s2_raw, encoding="utf-8")

    if s2_parsed is None:
        manifest["status"] = "s2_failed"
        manifest["s2_error"] = repr(s2_err)
        manifest["s2_partial_coverage_fallback"] = True
        # If raw response exists, try to salvage partial boundary_decisions
        s2_raw_text = (section_dir / "s2_raw_response.txt").read_text(encoding="utf-8")
        try:
            salvaged = parse_json_object(s2_raw_text)
            if isinstance(salvaged, dict) and salvaged.get("boundary_decisions"):
                s2_parsed = salvaged
                manifest["s2_salvaged"] = True
        except Exception:
            pass
        if s2_parsed is None:
            write_json(section_dir / "cards.raw.json", {"section_id": section_id, "cards": [], "coverage_audit": []})
            write_json(section_dir / "run_manifest.json", manifest)
            return manifest

    boundary_decisions = s2_parsed.get("boundary_decisions") or []
    manifest["s2_decision_count"] = len(boundary_decisions)
    kg_only_count = sum(1 for d in boundary_decisions if d.get("decision") == "kg_only")
    manifest["s2_kg_only_count"] = kg_only_count
    write_json(section_dir / "boundary_decisions.json", s2_parsed)

    # Build S1 index for merging
    s1_index: dict[str, dict[str, Any]] = {p.get("candidate_id", ""): p for p in propositions}
    passed_candidates: list[dict[str, Any]] = []
    for bd in boundary_decisions:
        cid = bd.get("candidate_id", "")
        if bd.get("decision") == "p7c_candidate" and cid in s1_index:
            passed_candidates.append({
                "candidate": s1_index[cid],
                "boundary_decision": bd,
            })

    manifest["s3_candidate_count"] = len(passed_candidates)

    if not passed_candidates:
        # All kg_only — write coverage_audit from boundary_decisions, no cards
        coverage_audit: list[dict[str, Any]] = []
        for bd in boundary_decisions:
            coverage_audit.append({
                "candidate_id": bd.get("candidate_id"),
                "unit_ids": s1_index.get(bd.get("candidate_id", ""), {}).get("unit_ids", []),
                "proposition": s1_index.get(bd.get("candidate_id", ""), {}).get("proposition", ""),
                "decision": bd.get("decision"),
                "card_ids": [],
                "reason": bd.get("reason", ""),
            })
        manifest["status"] = "ok"
        manifest["card_count"] = 0
        write_json(section_dir / "cards.raw.json", {
            "section_id": section_id,
            "section_title": task.get("section_title"),
            "cards": [],
            "coverage_audit": coverage_audit,
        })
        write_json(section_dir / "run_manifest.json", manifest)
        return manifest

    # === Stage 3: Semantic Graph Construction ===
    s3_prompt = build_s3_prompt(s3_template, task, passed_candidates)
    (section_dir / "s3_prompt.md").write_text(s3_prompt, encoding="utf-8")
    s3_parsed, s3_raw, s3_err = _call_and_parse(
        s3_prompt,
        "S3",
        lambda payload: (
            ([] if payload.get("section_id") == section_id else ["S3 section_id mismatch"])
            + validate_s3_construction_payload(
                payload,
                passed_candidates,
                section_id,
                allowed_unit_ids,
            )
        ),
    )
    (section_dir / "s3_raw_response.txt").write_text(s3_raw, encoding="utf-8")

    if s3_parsed is None:
        manifest["status"] = "s3_failed"
        manifest["s3_error"] = repr(s3_err)
        write_json(section_dir / "cards.raw.json", {"section_id": section_id, "cards": [], "coverage_audit": []})
        write_json(section_dir / "run_manifest.json", manifest)
        return manifest

    construction_audit = s3_parsed.get("construction_audit") or []
    cards_list = s3_parsed.get("cards") or []
    manifest["s3_ungraphable_count"] = sum(1 for ca in construction_audit if ca.get("construction_status") == "ungraphable")
    write_json(section_dir / "construction_audit.json", s3_parsed)

    # Merge coverage_audit from S2 + S3
    coverage_audit = _merge_coverage_audit(boundary_decisions, construction_audit, s1_index)

    # Build cards payload
    normalized_payload: dict[str, Any] = {
        "section_id": section_id,
        "section_title": task.get("section_title"),
        "coverage_audit": coverage_audit,
        "cards": cards_list,
        "skip_reason": s3_parsed.get("skip_reason"),
    }

    # Normalize in-place
    normalize_three_stage_candidate_payload(normalized_payload)
    cards_path = section_dir / "cards.raw.json"
    write_json(cards_path, normalized_payload)

    # Validation (optional)
    validation_error_count = 0
    if inline_structure_validation:
        validator_code, validator_output, validation_error_count = validate_cards(
            cards_path, section_dir / "validation_report.md", task_path
        )

    manifest["status"] = "ok" if validation_error_count == 0 else "validation_errors"
    manifest["card_count"] = len(cards_list)
    manifest["validation_error_count"] = validation_error_count
    write_json(section_dir / "run_manifest.json", manifest)
    return manifest


def run_section_merged_process_ir(
    section_id: str,
    run_dir: Path,
    packages_dir: Path,
    s1_template: str,
    s12_prompt_template: str,
    process_ir_template: str,
    model: str,
    thinking_effort: str,
    max_tokens: int,
    timeout: float,
    retries: int,
    retry_delay: float,
    inline_structure_validation: bool = False,
    s1_model: str | None = None,
    s1_thinking_effort: str | None = None,
    s12_model: str | None = None,
    s12_thinking_effort: str | None = None,
) -> dict[str, Any]:
    """Merged Process IR: S1.1 → S1.2 → S2 Process IR (LLM) → S3 deterministic compile."""
    task_path = packages_dir / section_id / "task.json"
    task = read_json(task_path)
    section_dir = run_dir / section_id
    section_dir.mkdir(parents=True, exist_ok=True)

    # Lazy-load compiler module
    spec = importlib.util.spec_from_file_location(
        "process_ir_compiler_v1", str(PROCESS_IR_COMPILER_PATH)
    )
    assert spec and spec.loader
    compiler_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(compiler_mod)

    manifest: dict[str, Any] = {
        "section_id": section_id,
        "section_title": task.get("section_title"),
        "status": "pending",
        "pipeline_mode": "merged_process_ir_v1",
    }

    allowed_unit_ids = set(collect_allowed_unit_ids(task))
    unit_evidence_text = collect_unit_evidence_text(task)

    def _call_and_parse(
        prompt: str,
        label: str,
        contract_validator: Any | None = None,
        stage_model: str | None = None,
        stage_thinking_effort: str | None = None,
    ) -> tuple[dict[str, Any] | None, str, object | None]:
        raw = ""
        error: object | None = None
        effective_model = stage_model or model
        effective_thinking = stage_thinking_effort or thinking_effort
        manifest_key = re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_")
        for attempt in range(1, retries + 1):
            try:
                raw, call_meta = call_model(
                    prompt, effective_model, max_tokens, timeout, effective_thinking
                )
                manifest[f"{manifest_key}_call"] = call_meta
            except Exception as exc:
                error = exc
                if attempt < retries:
                    time.sleep(retry_delay)
                continue
            try:
                parsed = parse_json_object(raw)
            except Exception:
                if attempt < retries:
                    time.sleep(retry_delay)
                continue
            if isinstance(parsed, dict):
                contract_errors = contract_validator(parsed) if contract_validator else []
                if not contract_errors:
                    return parsed, raw, None
                error = ValueError(f"{label} contract errors: {'; '.join(contract_errors)}")
                if attempt < retries:
                    time.sleep(retry_delay)
                continue
        return None, raw, error

    # === Stage 1.1: Proposition Discovery ===
    s1_prompt = build_s1_prompt(s1_template, task)
    (section_dir / "s11_prompt.md").write_text(s1_prompt, encoding="utf-8")
    s1_parsed, s1_raw, s1_err = _call_and_parse(
        s1_prompt,
        "S1.1",
        lambda payload: (
            ([] if payload.get("section_id") == section_id else ["S1.1 section_id mismatch"])
            + validate_s1_discovery_payload(payload, allowed_unit_ids, unit_evidence_text)
        ),
        s1_model,
        s1_thinking_effort,
    )
    (section_dir / "s11_raw_response.txt").write_text(s1_raw, encoding="utf-8")

    if s1_parsed is None:
        manifest["status"] = "s1_failed"
        manifest["s1_error"] = repr(s1_err)
        write_json(section_dir / "cards.raw.json", {"section_id": section_id, "cards": [], "coverage_audit": []})
        write_json(section_dir / "run_manifest.json", manifest)
        return manifest

    propositions = s1_parsed.get("propositions") or []
    manifest["s11_proposition_count"] = len(propositions)
    write_json(section_dir / "s11_propositions.json", s1_parsed)

    # === Stage 1.2: Gap Fill ===
    s12_prompt = build_s12_prompt(s12_prompt_template, task, propositions)
    (section_dir / "s12_prompt.md").write_text(s12_prompt, encoding="utf-8")
    s12_parsed, s12_raw, s12_err = _call_and_parse(
        s12_prompt,
        "S1.2",
        lambda payload: validate_s12_gap_payload(
            payload, section_id, allowed_unit_ids, unit_evidence_text, propositions
        ),
        s12_model,
        s12_thinking_effort,
    )
    (section_dir / "s12_raw_response.txt").write_text(s12_raw, encoding="utf-8")

    if s12_parsed is not None:
        gap_props = s12_parsed.get("gap_propositions") or []
        manifest["s12_gap_count"] = len(gap_props)
        write_json(section_dir / "s12_gap_propositions.json", s12_parsed)
        propositions = list(propositions) + list(gap_props)
        merged_payload = dict(s1_parsed)
        merged_payload["propositions"] = propositions
        if gap_props:
            merged_payload["skip_reason"] = None
        write_json(section_dir / "s1_propositions.json", merged_payload)
    else:
        manifest["status"] = "s12_failed"
        manifest["s12_error"] = repr(s12_err) if s12_err else "parse_failed"
        manifest["card_count"] = 0
        write_json(section_dir / "cards.raw.json", {"section_id": section_id, "cards": [], "coverage_audit": []})
        write_json(section_dir / "run_manifest.json", manifest)
        return manifest

    manifest["s1_merged_count"] = len(propositions)

    if not propositions:
        manifest["status"] = "ok"
        manifest["card_count"] = 0
        write_json(section_dir / "cards.raw.json", {"section_id": section_id, "cards": [], "coverage_audit": []})
        write_json(section_dir / "run_manifest.json", manifest)
        return manifest

    # === Stage 2: Process IR (LLM) ===
    s2_prompt = build_process_ir_prompt(process_ir_template, task, propositions)
    process_ir_prompt_sha256 = sha256_text(s2_prompt)
    manifest["process_ir_prompt_sha256"] = process_ir_prompt_sha256
    (section_dir / "s2_process_ir_prompt.md").write_text(s2_prompt, encoding="utf-8")

    def _validate_ir(payload: dict[str, Any]) -> list[str]:
        if payload.get("section_id") != section_id:
            return [f"section_id mismatch: expected {section_id}, got {payload.get('section_id')}"]
        return compiler_mod.validate_process_ir_payload(
            payload,
            section_id,
            propositions,
            allowed_unit_ids,
        )

    ir_parsed, ir_raw, ir_err = _call_and_parse(
        s2_prompt,
        "S2_Process_IR",
        _validate_ir,
    )
    (section_dir / "s2_process_ir_raw_response.txt").write_text(ir_raw, encoding="utf-8")

    if ir_parsed is None:
        manifest["status"] = "process_ir_failed"
        manifest["process_ir_error"] = repr(ir_err)
        manifest["process_ir_validation_errors"] = (
            [str(ir_err)] if ir_err else []
        )
        write_json(section_dir / "cards.raw.json", {"section_id": section_id, "cards": [], "coverage_audit": []})
        write_json(section_dir / "run_manifest.json", manifest)
        return manifest

    write_json(section_dir / "process_ir.json", ir_parsed)

    episodes = ir_parsed.get("episodes") or []
    candidate_audit = ir_parsed.get("candidate_audit") or []
    manifest["process_ir_validation_errors"] = []
    manifest["process_ir_episode_count"] = len(episodes)
    manifest["candidate_audit_count"] = len(candidate_audit)
    manifest["excluded_nonprocedural_count"] = sum(
        1 for a in candidate_audit if a.get("disposition") == "excluded_nonprocedural"
    )
    manifest["ungraphable_count"] = sum(
        1 for a in candidate_audit if a.get("disposition") == "ungraphable"
    )

    # Track split candidates
    candidate_episode_map: dict[str, list[str]] = {}
    for a in candidate_audit:
        cid = a.get("candidate_id", "")
        eps = a.get("episode_ids") or []
        if cid:
            candidate_episode_map[cid] = list(eps)
    split_candidates = [cid for cid, eps in candidate_episode_map.items() if len(eps) > 1]
    manifest["split_candidate_count"] = len(split_candidates)
    manifest["split_candidate_rate"] = round(len(split_candidates) / max(len(propositions), 1), 4)

    # === Stage 3: S3 LLM (Process IR → cards.raw.json) ===
    s3_template = DEFAULT_S3_FROM_IR_PROMPT_PATH.read_text(encoding="utf-8-sig")

    s3_prompt = build_s3_from_ir_prompt(s3_template, task, ir_parsed)
    (section_dir / "s3_to_cards_prompt.md").write_text(s3_prompt, encoding="utf-8")

    def _validate_s3(payload: dict[str, Any]) -> list[str]:
        return validate_s3_to_cards_payload(payload, section_id, allowed_unit_ids, ir_parsed)

    s3_parsed, s3_raw, s3_err = _call_and_parse(
        s3_prompt,
        "S3_To_Cards",
        _validate_s3,
    )
    (section_dir / "s3_to_cards_raw_response.txt").write_text(s3_raw, encoding="utf-8")

    if s3_parsed is None:
        manifest["status"] = "s3_failed"
        manifest["s3_error"] = repr(s3_err)
        write_json(section_dir / "cards.raw.json", {"section_id": section_id, "cards": [], "coverage_audit": []})
        write_json(section_dir / "run_manifest.json", manifest)
        return manifest

    cards_payload = s3_parsed
    cards_path = section_dir / "cards.raw.json"
    write_json(cards_path, cards_payload)

    manifest["compiled_card_count"] = len(cards_payload.get("cards") or [])
    manifest["source_process_ir_sha256"] = sha256_text(json.dumps(ir_parsed, ensure_ascii=False, sort_keys=True))

    # Generate compile_audit from Process IR + S3 cards
    compile_audit_data = compiler_mod.generate_compile_audit(ir_parsed, cards_payload, section_id)
    write_json(section_dir / "compile_audit.json", compile_audit_data)

    # Legacy card structure validation
    validator_code, validator_output, parsed_validation_error_count = validate_cards(
        cards_path, section_dir / "validation_report.md", task_path
    )
    validation_error_count = (
        parsed_validation_error_count
        if parsed_validation_error_count is not None
        else (1 if validator_code != 0 else 0)
    )

    manifest["s3_validation_errors"] = []
    manifest["status"] = "ok" if validation_error_count == 0 else "validation_errors"
    manifest["validation_error_count"] = validation_error_count
    manifest["model"] = model
    manifest["thinking_effort"] = thinking_effort
    write_json(section_dir / "run_manifest.json", manifest)
    return manifest


def _merge_coverage_audit(
    boundary_decisions: list[dict[str, Any]],
    construction_audit: list[dict[str, Any]],
    s1_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge S2 boundary_decisions and S3 construction_audit into final coverage_audit."""
    ca_index: dict[str, dict[str, Any]] = {}
    # Start from S2
    for bd in boundary_decisions:
        cid = bd.get("candidate_id", "")
        s1 = s1_index.get(cid, {})
        ca_index[cid] = {
            "candidate_id": cid,
            "unit_ids": s1.get("unit_ids", []),
            "proposition": s1.get("proposition", ""),
            "decision": "kg_only" if bd.get("decision") == "kg_only" else "p7c_ungraphable",
            "card_ids": [],
            "reason": bd.get("reason", ""),
        }
    # Update from S3
    for ca in construction_audit:
        cid = ca.get("candidate_id", "")
        if cid in ca_index:
            ca_index[cid]["card_ids"] = ca.get("card_ids", [])
            if ca.get("construction_status") == "graphed":
                ca_index[cid]["decision"] = "p7c_card"
            elif ca.get("construction_status") == "ungraphable":
                ca_index[cid]["decision"] = "p7c_ungraphable"
                ca_index[cid]["reason"] += " [construction_status: ungraphable — " + ca.get("reason", "") + "]"
    return list(ca_index.values())


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
            if not coverage_adjudication_prompt_template:
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
                        contract_errors = validate_coverage_adjudication(
                            parsed,
                            adjudication_patch,
                            collect_allowed_unit_ids(task),
                        )
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

裁决决定已经完成且保护合同已通过。只修复下列新增或补充图结构错误，保持所有`coverage_adjudication`、`new_candidates`、`new_cards`和`card_supplements`的业务决定不变——只修复图结构，不删除新增候选、不撤销补充、不改写首次抽取正本。仍按Coverage补丁合同返回严格JSON。

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
                                collect_allowed_unit_ids(task),
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
                            new_card_count = final_card_count - original_card_count
                            supplement_count = len(
                                adjudication_patch.get("card_supplements") or []
                            )
                            manifest["coverage_adjudication_promoted_card_count"] = new_card_count
                            manifest["coverage_adjudication_new_card_count"] = new_card_count
                            manifest["coverage_adjudication_supplement_count"] = supplement_count

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
        "| section | status | cards | validation_errors | coverage | new_cards | supplements | title | skip_reason |",
        "|---|---:|---:|---:|---|---:|---:|---|---|",
    ]
    for row in sorted(manifests, key=lambda item: item.get("section_id") or ""):
        lines.append(
            "| {section} | {status} | {cards} | {errors} | {coverage} | {new_cards} | {supplements} | {title} | {skip} |".format(
                section=row.get("section_id", ""),
                status=row.get("status", ""),
                cards=row.get("card_count", ""),
                errors=(
                    row.get("validation_error_count", "")
                    if row.get("structure_validation_status") != "deferred_to_p7d"
                    else "P7D"
                ),
                coverage=row.get("coverage_adjudication_status", ""),
                new_cards=row.get("coverage_adjudication_new_card_count", 0),
                supplements=row.get("coverage_adjudication_supplement_count", 0),
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
    parser.add_argument(
        "--s1-model",
        default="deepseek-chat",
        help="Model for S1.1 discovery in four-stage mode.",
    )
    parser.add_argument(
        "--s1-thinking-effort",
        default="high",
        choices=["none", "low", "medium", "high"],
        help="Thinking effort for S1.1 discovery in four-stage mode.",
    )
    parser.add_argument(
        "--s12-model",
        default="deepseek-v4-pro",
        help="Model for S1.2 gap filling in four-stage mode.",
    )
    parser.add_argument(
        "--s12-thinking-effort",
        default="none",
        choices=["none", "low", "medium", "high"],
        help="Thinking effort for S1.2 gap filling in four-stage mode.",
    )
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
    parser.add_argument(
        "--two-stage",
        action="store_true",
        default=False,
        help="Use two-stage extraction: S1 (proposition discovery) + S2 (KG boundary + graph construction).",
    )
    parser.add_argument(
        "--s1-prompt",
        default=str(DEFAULT_S1_PROMPT_PATH),
        help="Path to S1 proposition discovery prompt template.",
    )
    parser.add_argument(
        "--s2-prompt",
        default=str(DEFAULT_S2_PROMPT_PATH),
        help="Path to S2 KG boundary + graph construction prompt template (two-stage).",
    )
    parser.add_argument(
        "--three-stage",
        action="store_true",
        default=False,
        help="Use three-stage extraction: S1 → S2(纯KG裁决) → S3(语义构图).",
    )
    parser.add_argument(
        "--s2-new-prompt",
        default=str(DEFAULT_S2_NEW_PROMPT_PATH),
        help="Path to new S2 KG boundary adjudication prompt (three-stage).",
    )
    parser.add_argument(
        "--s3-prompt",
        default=str(DEFAULT_S3_PROMPT_PATH),
        help="Path to S3 semantic graph construction prompt (three-stage).",
    )
    parser.add_argument(
        "--four-stage",
        action="store_true",
        default=False,
        help="Use four-stage extraction: S1.1 → S1.2(补漏) → S2(新) → S3.",
    )
    parser.add_argument(
        "--s12-prompt",
        default=str(DEFAULT_S12_PROMPT_PATH),
        help="Path to S1.2 gap fill prompt (four-stage).",
    )
    parser.add_argument(
        "--stop-after-s12",
        action="store_true",
        default=False,
        help="Stop after writing the validated merged S1.1 + S1.2 candidate artifact.",
    )
    parser.add_argument(
        "--pipeline-mode",
        default=None,
        choices=["merged-process-ir"],
        help="Pipeline mode: 'merged-process-ir' for the S2/S3 merged Process IR experiment.",
    )
    parser.add_argument(
        "--process-ir-prompt",
        default=str(DEFAULT_PROCESS_IR_PROMPT_PATH),
        help="Path to Process IR prompt template (for --pipeline-mode merged-process-ir).",
    )
    args = parser.parse_args()

    if args.stop_after_s12 and not args.four_stage:
        parser.error("--stop-after-s12 requires --four-stage")

    if args.pipeline_mode == "merged-process-ir" and (args.four_stage or args.three_stage or args.two_stage):
        print("INFO: --pipeline-mode merged-process-ir takes priority; ignoring --four-stage / --three-stage / --two-stage.")

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
    if args.four_stage:
        plan["four_stage"] = True
        plan["s1_prompt"] = path_for_json(Path(args.s1_prompt))
        plan["s12_prompt"] = path_for_json(Path(args.s12_prompt))
        plan["s1_model"] = args.s1_model
        plan["s1_thinking_effort"] = args.s1_thinking_effort
        plan["s12_model"] = args.s12_model
        plan["s12_thinking_effort"] = args.s12_thinking_effort
        plan["stop_after_s12"] = args.stop_after_s12
        plan["input_policy"] = {
            "s11": "section_metadata_plus_section_text_with_unit_anchors",
            "s12": "section_metadata_plus_section_text_with_unit_anchors_plus_s11_candidates",
            "post_generation_validation": "runner_internal_allowed_unit_ids_and_unit_evidence_text",
        }
        plan["s2_new_prompt"] = path_for_json(Path(args.s2_new_prompt))
        plan["s3_prompt"] = path_for_json(Path(args.s3_prompt))
        plan["coverage_adjudication"] = False
        if args.three_stage or args.two_stage:
            print("INFO: --four-stage takes priority; ignoring --three-stage / --two-stage.")
    elif args.three_stage:
        plan["three_stage"] = True
        plan["s1_prompt"] = path_for_json(Path(args.s1_prompt))
        plan["s2_new_prompt"] = path_for_json(Path(args.s2_new_prompt))
        plan["s3_prompt"] = path_for_json(Path(args.s3_prompt))
        plan["coverage_adjudication"] = False
    elif args.two_stage:
        plan["two_stage"] = True
        plan["s1_prompt"] = path_for_json(Path(args.s1_prompt))
        plan["s2_prompt"] = path_for_json(Path(args.s2_prompt))
        plan["coverage_adjudication"] = False  # S2 replaces Coverage in two-stage mode

    if args.pipeline_mode == "merged-process-ir":
        plan["pipeline_mode"] = "merged_process_ir_v1"
        plan["s1_prompt"] = path_for_json(Path(args.s1_prompt))
        plan["s12_prompt"] = path_for_json(Path(args.s12_prompt))
        plan["process_ir_prompt"] = path_for_json(Path(args.process_ir_prompt))
        plan["s1_model"] = args.s1_model
        plan["s1_thinking_effort"] = args.s1_thinking_effort
        plan["s12_model"] = args.s12_model
        plan["s12_thinking_effort"] = args.s12_thinking_effort
        plan["coverage_adjudication"] = False
        plan["input_policy"] = "section_text_with_unit_anchors_plus_s1_candidates_only_no_kg_no_allowed_unit_ids"
        plan["inline_structure_validation"] = True
        plan["structure_validation_owner"] = "P7C_required_merged_process_ir"

    write_json(run_dir / "run_plan.json", plan)

    if args.dry_run:
        print(f"Dry run only. Planned {len(sections)} sections under {run_dir}")
        return

    if args.pipeline_mode == "merged-process-ir":
        s1_template = Path(args.s1_prompt).read_text(encoding="utf-8-sig")
        s12_template = Path(args.s12_prompt).read_text(encoding="utf-8-sig")
        process_ir_template = Path(args.process_ir_prompt).read_text(encoding="utf-8-sig")
    elif args.four_stage:
        s1_template = Path(args.s1_prompt).read_text(encoding="utf-8-sig")
        s12_template = Path(args.s12_prompt).read_text(encoding="utf-8-sig")
        s2_new_template = Path(args.s2_new_prompt).read_text(encoding="utf-8-sig")
        s3_template = Path(args.s3_prompt).read_text(encoding="utf-8-sig")
    elif args.three_stage:
        s1_template = Path(args.s1_prompt).read_text(encoding="utf-8-sig")
        s2_new_template = Path(args.s2_new_prompt).read_text(encoding="utf-8-sig")
        s3_template = Path(args.s3_prompt).read_text(encoding="utf-8-sig")
    elif args.two_stage:
        s1_template = Path(args.s1_prompt).read_text(encoding="utf-8-sig")
        s2_template = Path(args.s2_prompt).read_text(encoding="utf-8-sig")
    else:
        prompt_template = Path(args.prompt).read_text(encoding="utf-8-sig")
        coverage_adjudication_prompt_template = None
        if args.coverage_adjudication:
            coverage_adjudication_prompt_template = Path(args.coverage_adjudication_prompt).read_text(
                encoding="utf-8-sig"
            )

    manifests: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        if args.pipeline_mode == "merged-process-ir":
            futures = {
                executor.submit(
                    run_section_merged_process_ir,
                    section,
                    run_dir,
                    packages_dir,
                    s1_template,
                    s12_template,
                    process_ir_template,
                    args.model,
                    args.thinking_effort,
                    args.max_tokens,
                    args.timeout,
                    args.retries,
                    args.retry_delay,
                    args.inline_structure_validation,
                    args.s1_model,
                    args.s1_thinking_effort,
                    args.s12_model,
                    args.s12_thinking_effort,
                ): section
                for section in sections
            }
        elif args.four_stage:
            futures = {
                executor.submit(
                    run_section_three_stage,
                    section,
                    run_dir,
                    packages_dir,
                    s1_template,
                    s2_new_template,
                    s3_template,
                    args.model,
                    args.thinking_effort,
                    args.max_tokens,
                    args.timeout,
                    args.retries,
                    args.retry_delay,
                    args.validation_retries,
                    args.inline_structure_validation,
                    s12_template,
                    args.s1_model,
                    args.s1_thinking_effort,
                    args.s12_model,
                    args.s12_thinking_effort,
                    args.stop_after_s12,
                ): section
                for section in sections
            }
        elif args.three_stage:
            futures = {
                executor.submit(
                    run_section_three_stage,
                    section,
                    run_dir,
                    packages_dir,
                    s1_template,
                    s2_new_template,
                    s3_template,
                    args.model,
                    args.thinking_effort,
                    args.max_tokens,
                    args.timeout,
                    args.retries,
                    args.retry_delay,
                    args.validation_retries,
                    args.inline_structure_validation,
                ): section
                for section in sections
            }
        elif args.two_stage:
            futures = {
                executor.submit(
                    run_section_two_stage,
                    section,
                    run_dir,
                    packages_dir,
                    s1_template,
                    s2_template,
                    args.model,
                    args.thinking_effort,
                    args.max_tokens,
                    args.timeout,
                    args.retries,
                    args.retry_delay,
                    args.validation_retries,
                    args.inline_structure_validation,
                ): section
                for section in sections
            }
        else:
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
