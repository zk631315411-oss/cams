from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


TEST_DIR = Path(__file__).resolve().parent
PHASE_DIR = next(parent for parent in TEST_DIR.parents if (parent / "scripts" / "run_p7c_batch_ds.py").exists())
DEFAULT_BASELINE_DIR = PHASE_DIR / "phases" / "P7C" / "outputs" / "ds_pro_none_additive_coverage_v23_10sections"
DEFAULT_PACKAGES_DIR = PHASE_DIR / "phases" / "P7B" / "section_packages"
DEFAULT_AUDIT_PROMPT = TEST_DIR / "prompts" / "coverage_audit_v1.md"
DEFAULT_PATCH_PROMPT = TEST_DIR / "prompts" / "coverage_patch_v1.md"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


P7C_RUNNER = load_module("p7c_batch_runner_for_coverage_decomposition", PHASE_DIR / "scripts" / "run_p7c_batch_ds.py")

NODE_TYPES = {
    "entry": {
        "E1_event_signal", "E2_object_entry", "E3_state_threshold", "E4_handoff",
        "E5_time_cycle", "E6_change_exception", "E7_external_command", "E8_decision_finding",
    },
    "process": {
        "P1_assessment", "P2_execution", "P3_branch_routing", "P4_collection", "P5_coordination",
        "P6_feedback", "P7_monitoring", "P8_constrained_action", "P9_planning", "P10_sufficiency",
    },
    "exit": {
        "X1_classification", "X2_product", "X3_state_change", "X4_handoff",
        "X5_config_change", "X6_termination", "X7_continuing_obligation",
    },
    "auxiliary": {"input", "standard"},
}
EDGE_TYPES = {"PRECEDES", "REFERENCES", "PRODUCES", "DECIDES", "FEEDBACK"}
CARD_NATURES = {"execution", "assessment", "risk_indicator", "control"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_sample(path: Path) -> list[str]:
    payload = read_json(path)
    items = payload.get("items") if isinstance(payload, dict) else payload
    if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
        raise ValueError("sample file must contain a string items list")
    return items


def unique_rows(rows: list[Any], key: str, owner: str) -> tuple[dict[str, dict[str, Any]], list[str]]:
    indexed: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict) or not row.get(key):
            errors.append(f"{owner}[{index}] missing {key}")
            continue
        value = str(row[key])
        if value in indexed:
            errors.append(f"{owner} duplicate {key} {value}")
            continue
        indexed[value] = row
    return indexed, errors


def validate_audit(
    original: dict[str, Any], audit: dict[str, Any], allowed_unit_ids: set[str]
) -> list[str]:
    errors: list[str] = []
    if set(audit) != {"section_id", "claims", "scan_summary"}:
        errors.append("audit top-level fields must be section_id, claims, scan_summary")
    if audit.get("section_id") != original.get("section_id"):
        errors.append("audit changed section_id")
    if not isinstance(audit.get("scan_summary"), str) or not audit["scan_summary"].strip():
        errors.append("audit scan_summary is required")
    claims = audit.get("claims")
    if not isinstance(claims, list):
        return errors + ["audit claims must be a list"]
    claims_by_id, row_errors = unique_rows(claims, "claim_id", "claims")
    errors.extend(row_errors)
    known_cards = {
        str(card.get("card_id")) for card in original.get("cards") or []
        if isinstance(card, dict) and card.get("card_id")
    }
    required = {
        "claim_id", "unit_ids", "proposition", "kg_boundary", "coverage_status",
        "matched_card_ids", "missing_part", "condition", "qualifier", "reason",
    }
    for claim_id, claim in claims_by_id.items():
        missing = required - set(claim)
        if missing:
            errors.append(f"claim {claim_id} missing fields {sorted(missing)}")
        unit_ids = claim.get("unit_ids")
        if not isinstance(unit_ids, list) or not unit_ids:
            errors.append(f"claim {claim_id} requires unit_ids")
        elif not set(unit_ids).issubset(allowed_unit_ids):
            errors.append(f"claim {claim_id} uses evidence outside current section")
        if not claim.get("proposition") or not claim.get("reason"):
            errors.append(f"claim {claim_id} requires proposition and reason")
        matched = claim.get("matched_card_ids")
        if not isinstance(matched, list):
            errors.append(f"claim {claim_id} matched_card_ids must be a list")
            matched = []
        elif not set(matched).issubset(known_cards):
            errors.append(f"claim {claim_id} references unknown card IDs")
        boundary = claim.get("kg_boundary")
        status = claim.get("coverage_status")
        if boundary not in {"kg_only", "p7_incremental"}:
            errors.append(f"claim {claim_id} has invalid kg_boundary")
        elif boundary == "kg_only":
            if status != "not_applicable" or matched or claim.get("missing_part") is not None:
                errors.append(f"claim {claim_id} kg_only status contract failed")
        elif status == "covered":
            if not matched or claim.get("missing_part") is not None:
                errors.append(f"claim {claim_id} covered status contract failed")
        elif status == "partially_covered":
            if not matched or not claim.get("missing_part"):
                errors.append(f"claim {claim_id} partially_covered status contract failed")
        elif status == "missing":
            if not claim.get("missing_part"):
                errors.append(f"claim {claim_id} missing status requires missing_part")
        else:
            errors.append(f"claim {claim_id} has invalid coverage_status")
    return errors


def validate_nodes_and_edges(
    owner: str,
    nodes: list[Any],
    edges: list[Any],
    allowed_unit_ids: set[str],
    existing_node_ids: set[str] | None = None,
    existing_edge_ids: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    existing_node_ids = existing_node_ids or set()
    existing_edge_ids = existing_edge_ids or set()
    nodes_by_id, node_errors = unique_rows(nodes, "node_id", f"{owner}.nodes")
    edges_by_id, edge_errors = unique_rows(edges, "edge_id", f"{owner}.edges")
    errors.extend(node_errors + edge_errors)
    if set(nodes_by_id) & existing_node_ids:
        errors.append(f"{owner} reuses existing node IDs")
    if set(edges_by_id) & existing_edge_ids:
        errors.append(f"{owner} reuses existing edge IDs")
    for node_id, node in nodes_by_id.items():
        category = node.get("node_category")
        if category not in NODE_TYPES or node.get("node_type") not in NODE_TYPES[category]:
            errors.append(f"{owner} node {node_id} has invalid category/type")
        if not node.get("label") or node.get("evidence_strength") != "explicit":
            errors.append(f"{owner} node {node_id} has invalid label/evidence_strength")
        evidence = node.get("evidence_unit_ids")
        if not isinstance(evidence, list) or not evidence or not set(evidence).issubset(allowed_unit_ids):
            errors.append(f"{owner} node {node_id} has invalid evidence")
    all_node_ids = existing_node_ids | set(nodes_by_id)
    for edge_id, edge in edges_by_id.items():
        if edge.get("edge_type") not in EDGE_TYPES:
            errors.append(f"{owner} edge {edge_id} has invalid edge_type")
        if edge.get("derivation") not in {"explicit_text", "llm_inference"}:
            errors.append(f"{owner} edge {edge_id} has invalid derivation")
        if edge.get("source") not in all_node_ids or edge.get("target") not in all_node_ids:
            errors.append(f"{owner} edge {edge_id} references unknown node")
        evidence = edge.get("evidence_unit_ids")
        if not isinstance(evidence, list) or not evidence or not set(evidence).issubset(allowed_unit_ids):
            errors.append(f"{owner} edge {edge_id} has invalid evidence")
        source = nodes_by_id.get(str(edge.get("source")))
        target = nodes_by_id.get(str(edge.get("target")))
        if edge.get("edge_type") == "REFERENCES":
            if source and source.get("node_category") != "process":
                errors.append(f"{owner} edge {edge_id} REFERENCES source must be process")
            if target and target.get("node_category") != "auxiliary":
                errors.append(f"{owner} edge {edge_id} REFERENCES target must be auxiliary")
        if edge.get("edge_type") == "PRODUCES" and target and target.get("node_category") != "exit":
            errors.append(f"{owner} edge {edge_id} PRODUCES target must be exit")
    return errors


def validate_patch(
    original: dict[str, Any],
    gap_claims: list[dict[str, Any]],
    patch: dict[str, Any],
    allowed_unit_ids: set[str],
) -> list[str]:
    errors: list[str] = []
    if set(patch) != {"section_id", "claim_resolutions", "new_cards", "card_supplements"}:
        errors.append("patch top-level fields must match contract")
    if patch.get("section_id") != original.get("section_id"):
        errors.append("patch changed section_id")
    target_ids = {str(claim["claim_id"]) for claim in gap_claims}
    resolutions = patch.get("claim_resolutions")
    new_cards = patch.get("new_cards")
    supplements = patch.get("card_supplements")
    if not all(isinstance(value, list) for value in (resolutions, new_cards, supplements)):
        return errors + ["patch list fields are required"]
    resolution_by_id, row_errors = unique_rows(resolutions, "claim_id", "claim_resolutions")
    errors.extend(row_errors)
    if set(resolution_by_id) != target_ids:
        errors.append("claim_resolutions must cover every and only gap claim")
    original_cards, original_card_errors = unique_rows(original.get("cards") or [], "card_id", "original.cards")
    errors.extend(original_card_errors)
    new_cards_by_id, new_card_errors = unique_rows(new_cards, "card_id", "new_cards")
    errors.extend(new_card_errors)
    if set(new_cards_by_id) & set(original_cards):
        errors.append("new_cards reuse original card IDs")
    supplements_by_id, supplement_errors = unique_rows(supplements, "patch_id", "card_supplements")
    errors.extend(supplement_errors)
    supplement_by_card: dict[str, dict[str, Any]] = {}
    for supplement in supplements_by_id.values():
        card_id = str(supplement.get("card_id"))
        if card_id not in original_cards:
            errors.append(f"supplement targets unknown card {card_id}")
        elif card_id in supplement_by_card:
            errors.append(f"multiple supplements target card {card_id}")
        supplement_by_card[card_id] = supplement
    referenced_new: set[str] = set()
    referenced_supplements: set[str] = set()
    for claim_id, resolution in resolution_by_id.items():
        kind = resolution.get("resolution")
        card_id = resolution.get("card_id")
        if not resolution.get("reason"):
            errors.append(f"resolution {claim_id} missing reason")
        if kind == "new_card":
            if card_id not in new_cards_by_id:
                errors.append(f"resolution {claim_id} references unknown new card")
            else:
                referenced_new.add(str(card_id))
        elif kind == "card_supplement":
            if card_id not in supplement_by_card:
                errors.append(f"resolution {claim_id} references missing supplement")
            else:
                referenced_supplements.add(str(card_id))
        elif kind == "unresolved":
            if card_id is not None:
                errors.append(f"resolution {claim_id} unresolved must have null card_id")
        else:
            errors.append(f"resolution {claim_id} has invalid resolution")
    if set(new_cards_by_id) != referenced_new:
        errors.append("new_cards must be referenced by resolutions")
    if set(supplement_by_card) != referenced_supplements:
        errors.append("card_supplements must be referenced by resolutions")
    for card_id, card in new_cards_by_id.items():
        required = {
            "card_id", "section_id", "card_nature", "title", "flow_nodes", "flow_edges",
            "source_unit_ids", "candidate_status", "review_notes", "coverage_claim_ids",
        }
        if not required.issubset(card):
            errors.append(f"new card {card_id} missing required fields")
        if card.get("section_id") != original.get("section_id") or card.get("card_nature") not in CARD_NATURES:
            errors.append(f"new card {card_id} has invalid section/card_nature")
        if card.get("candidate_status") != "candidate":
            errors.append(f"new card {card_id} must remain candidate")
        claim_ids = card.get("coverage_claim_ids")
        if not isinstance(claim_ids, list) or not set(claim_ids).issubset(target_ids):
            errors.append(f"new card {card_id} has invalid coverage_claim_ids")
        source_units = card.get("source_unit_ids")
        if not isinstance(source_units, list) or not set(source_units).issubset(allowed_unit_ids):
            errors.append(f"new card {card_id} has invalid source_unit_ids")
        errors.extend(validate_nodes_and_edges(
            f"new card {card_id}", card.get("flow_nodes") or [], card.get("flow_edges") or [], allowed_unit_ids
        ))
    for patch_id, supplement in supplements_by_id.items():
        card_id = str(supplement.get("card_id"))
        card = original_cards.get(card_id, {})
        required = {
            "patch_id", "card_id", "coverage_claim_ids", "reason", "add_flow_nodes",
            "add_flow_edges", "add_source_unit_ids",
        }
        if not required.issubset(supplement):
            errors.append(f"supplement {patch_id} missing required fields")
        claim_ids = supplement.get("coverage_claim_ids")
        if not isinstance(claim_ids, list) or not set(claim_ids).issubset(target_ids):
            errors.append(f"supplement {patch_id} has invalid coverage_claim_ids")
        added_nodes = supplement.get("add_flow_nodes") or []
        added_edges = supplement.get("add_flow_edges") or []
        if not added_nodes and not added_edges:
            errors.append(f"supplement {patch_id} must add nodes or edges")
        existing_nodes = {
            str(node.get("node_id")) for node in card.get("flow_nodes") or [] if isinstance(node, dict)
        }
        existing_edges = {
            str(edge.get("edge_id")) for edge in card.get("flow_edges") or [] if isinstance(edge, dict)
        }
        errors.extend(validate_nodes_and_edges(
            f"supplement {patch_id}", added_nodes, added_edges, allowed_unit_ids, existing_nodes, existing_edges
        ))
        add_source_units = supplement.get("add_source_unit_ids")
        if not isinstance(add_source_units, list) or not set(add_source_units).issubset(allowed_unit_ids):
            errors.append(f"supplement {patch_id} has invalid add_source_unit_ids")
        final_source = set(card.get("source_unit_ids") or []) | set(add_source_units or [])
        evidence = {
            unit_id
            for row in [*added_nodes, *added_edges]
            if isinstance(row, dict)
            for unit_id in row.get("evidence_unit_ids") or []
        }
        if not evidence.issubset(final_source):
            errors.append(f"supplement {patch_id} evidence missing from final source_unit_ids")
    return errors


def merge_patch(
    original: dict[str, Any], audit: dict[str, Any], patch: dict[str, Any]
) -> dict[str, Any]:
    merged = copy.deepcopy(original)
    cards_by_id = {
        str(card.get("card_id")): card for card in merged.get("cards") or [] if isinstance(card, dict)
    }
    for supplement in patch.get("card_supplements") or []:
        card = cards_by_id[str(supplement["card_id"])]
        card.setdefault("flow_nodes", []).extend(copy.deepcopy(supplement.get("add_flow_nodes") or []))
        card.setdefault("flow_edges", []).extend(copy.deepcopy(supplement.get("add_flow_edges") or []))
        existing_units = list(card.get("source_unit_ids") or [])
        for unit_id in supplement.get("add_source_unit_ids") or []:
            if unit_id not in existing_units:
                existing_units.append(unit_id)
        card["source_unit_ids"] = existing_units
    merged.setdefault("cards", []).extend(copy.deepcopy(patch.get("new_cards") or []))
    merged["coverage_claim_audit"] = copy.deepcopy(audit.get("claims") or [])
    merged["coverage_patch_resolutions"] = copy.deepcopy(patch.get("claim_resolutions") or [])
    P7C_RUNNER.normalize_candidate_payload(merged)
    return merged


def build_audit_prompt(
    template: str, task: dict[str, Any], original: dict[str, Any], allowed: list[str]
) -> str:
    context = {
        "section_id": task.get("section_id"),
        "section_title": task.get("section_title"),
        "base_kg_section_summary": P7C_RUNNER.build_base_kg_section_summary(task),
        "section_text_with_unit_anchors": task.get("section_text_with_unit_anchors", ""),
        "allowed_unit_ids": allowed,
        "original_json": original,
    }
    return template.rstrip() + "\n\n## 调用输入\n\n```json\n" + json.dumps(context, ensure_ascii=False, indent=2) + "\n```\n"


def build_patch_prompt(
    template: str,
    task: dict[str, Any],
    original: dict[str, Any],
    gap_claims: list[dict[str, Any]],
    allowed: list[str],
) -> str:
    context = {
        "section_id": task.get("section_id"),
        "section_title": task.get("section_title"),
        "section_text_with_unit_anchors": task.get("section_text_with_unit_anchors", ""),
        "allowed_unit_ids": allowed,
        "original_json": original,
        "gap_claims": gap_claims,
    }
    return template.rstrip() + "\n\n## 调用输入\n\n```json\n" + json.dumps(context, ensure_ascii=False, indent=2) + "\n```\n"


def call_json(
    prompt: str,
    model: str,
    thinking_effort: str,
    max_tokens: int,
    timeout: float,
    retries: int,
    retry_delay: float,
) -> tuple[dict[str, Any] | None, str, dict[str, Any], list[dict[str, Any]]]:
    raw = ""
    meta: dict[str, Any] = {}
    attempts: list[dict[str, Any]] = []
    for attempt in range(1, max(1, retries + 1) + 1):
        try:
            raw, meta = P7C_RUNNER.call_model(
                prompt, model=model, max_tokens=max_tokens, timeout=timeout, thinking_effort=thinking_effort
            )
            parsed = P7C_RUNNER.parse_json_object(raw)
            if parsed is None:
                attempts.append({"attempt": attempt, "status": "parse_failed", "raw_length": len(raw)})
            else:
                attempts.append({"attempt": attempt, "status": "ok"})
                return parsed, raw, meta, attempts
        except Exception as exc:
            attempts.append({"attempt": attempt, "status": "failed", "error": repr(exc)})
        if attempt <= retries:
            time.sleep(retry_delay * attempt)
    return None, raw, meta, attempts


def load_initial_payload(baseline_dir: Path, section_id: str) -> dict[str, Any]:
    raw_path = baseline_dir / section_id / "raw_response.txt"
    payload = P7C_RUNNER.parse_json_object(raw_path.read_text(encoding="utf-8-sig"))
    if payload is None:
        raise ValueError(f"Cannot parse baseline initial response: {raw_path}")
    P7C_RUNNER.normalize_candidate_payload(payload)
    return payload


def run_variant_section(
    section_id: str,
    artifact_dir: Path,
    baseline_dir: Path,
    packages_dir: Path,
    audit_template: str,
    patch_template: str,
    model: str,
    thinking_effort: str,
    max_tokens: int,
    timeout: float,
    retries: int,
    retry_delay: float,
) -> dict[str, Any]:
    section_dir = artifact_dir / section_id
    section_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "section_id": section_id,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "status": "running",
    }
    try:
        task = read_json(packages_dir / section_id / "task.json")
        original = load_initial_payload(baseline_dir, section_id)
        allowed = P7C_RUNNER.collect_allowed_unit_ids(task)
        audit_prompt = build_audit_prompt(audit_template, task, original, allowed)
        (section_dir / "coverage_audit.prompt.md").write_text(audit_prompt, encoding="utf-8")
        audit, audit_raw, audit_meta, audit_attempts = call_json(
            audit_prompt, model, thinking_effort, max_tokens, timeout, retries, retry_delay
        )
        (section_dir / "coverage_audit.raw.txt").write_text(audit_raw + "\n", encoding="utf-8")
        manifest["audit_call_attempts"] = audit_attempts
        manifest["audit_call_meta"] = audit_meta
        if audit is None:
            raise RuntimeError("coverage audit response could not be parsed")
        write_json(section_dir / "coverage_audit.json", audit)
        audit_errors = validate_audit(original, audit, set(allowed))
        manifest["audit_contract_errors"] = audit_errors
        if audit_errors:
            raise RuntimeError("coverage audit contract failed")
        gap_claims = [
            claim for claim in audit.get("claims") or []
            if claim.get("kg_boundary") == "p7_incremental"
            and claim.get("coverage_status") in {"missing", "partially_covered"}
        ]
        manifest["audit_claim_count"] = len(audit.get("claims") or [])
        manifest["gap_claim_count"] = len(gap_claims)
        if gap_claims:
            patch_prompt = build_patch_prompt(patch_template, task, original, gap_claims, allowed)
            (section_dir / "coverage_patch.prompt.md").write_text(patch_prompt, encoding="utf-8")
            patch, patch_raw, patch_meta, patch_attempts = call_json(
                patch_prompt, model, thinking_effort, max_tokens, timeout, retries, retry_delay
            )
            (section_dir / "coverage_patch.raw.txt").write_text(patch_raw + "\n", encoding="utf-8")
            manifest["patch_call_attempts"] = patch_attempts
            manifest["patch_call_meta"] = patch_meta
            if patch is None:
                raise RuntimeError("coverage patch response could not be parsed")
        else:
            patch = {
                "section_id": section_id,
                "claim_resolutions": [],
                "new_cards": [],
                "card_supplements": [],
            }
            manifest["patch_call_attempts"] = []
            manifest["patch_call_meta"] = {}
        write_json(section_dir / "coverage_patch.json", patch)
        patch_errors = validate_patch(original, gap_claims, patch, set(allowed))
        manifest["patch_contract_errors"] = patch_errors
        if patch_errors:
            raise RuntimeError("coverage patch contract failed")
        merged = merge_patch(original, audit, patch)
        write_json(section_dir / "cards.raw.json", merged)
        unresolved = sum(
            1 for row in patch.get("claim_resolutions") or [] if row.get("resolution") == "unresolved"
        )
        manifest.update({
            "status": "ok_with_unresolved" if unresolved else "ok",
            "initial_card_count": len(original.get("cards") or []),
            "final_card_count": len(merged.get("cards") or []),
            "new_card_count": len(patch.get("new_cards") or []),
            "supplement_count": len(patch.get("card_supplements") or []),
            "unresolved_claim_count": unresolved,
        })
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = repr(exc)
    manifest["finished_at"] = datetime.now().isoformat(timespec="seconds")
    write_json(section_dir / "run_manifest.json", manifest)
    return manifest


def run_baseline(sections: list[str], artifact_dir: Path, baseline_dir: Path) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for section_id in sections:
        source_dir = baseline_dir / section_id
        target_dir = artifact_dir / section_id
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in ("cards.raw.json", "raw_response.txt", "coverage_adjudication.patch.json", "run_manifest.json"):
            source = source_dir / name
            if source.exists():
                shutil.copy2(source, target_dir / name)
        cards = read_json(target_dir / "cards.raw.json")
        manifests.append({
            "section_id": section_id,
            "status": "ok",
            "final_card_count": len(cards.get("cards") or []),
            "source": str(source_dir),
        })
    return manifests


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the isolated two-stage P7C coverage experiment.")
    parser.add_argument("--arm", choices=["baseline", "variant"], required=True)
    parser.add_argument("--sample-file", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--baseline-dir", default=str(DEFAULT_BASELINE_DIR))
    parser.add_argument("--packages-dir", default=str(DEFAULT_PACKAGES_DIR))
    parser.add_argument("--audit-prompt", default=str(DEFAULT_AUDIT_PROMPT))
    parser.add_argument("--patch-prompt", default=str(DEFAULT_PATCH_PROMPT))
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--thinking-effort", choices=["none", "low", "medium", "high"], default="none")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-delay", type=float, default=5.0)
    args = parser.parse_args()

    sections = load_sample(Path(args.sample_file))
    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    baseline_dir = Path(args.baseline_dir)
    if args.arm == "baseline":
        manifests = run_baseline(sections, artifact_dir, baseline_dir)
    else:
        audit_template = Path(args.audit_prompt).read_text(encoding="utf-8-sig")
        patch_template = Path(args.patch_prompt).read_text(encoding="utf-8-sig")
        manifests = []
        with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
            futures = {
                executor.submit(
                    run_variant_section,
                    section_id,
                    artifact_dir,
                    baseline_dir,
                    Path(args.packages_dir),
                    audit_template,
                    patch_template,
                    args.model,
                    args.thinking_effort,
                    args.max_tokens,
                    args.timeout,
                    args.retries,
                    args.retry_delay,
                ): section_id
                for section_id in sections
            }
            for future in as_completed(futures):
                result = future.result()
                manifests.append(result)
                print(
                    f"{result['section_id']}: {result['status']}, "
                    f"gaps={result.get('gap_claim_count')}, cards={result.get('final_card_count')}"
                )
    manifests.sort(key=lambda row: row["section_id"])
    summary = {
        "arm": args.arm,
        "sections": sections,
        "section_count": len(sections),
        "status_counts": {
            status: sum(1 for row in manifests if row.get("status") == status)
            for status in sorted({str(row.get("status")) for row in manifests})
        },
        "manifests": manifests,
    }
    write_json(artifact_dir / "run_summary.json", summary)
    return 0 if all(row.get("status") in {"ok", "ok_with_unresolved"} for row in manifests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
