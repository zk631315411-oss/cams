from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


COMPILER_VERSION = "process_ir_compiler_v1"


def _read_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = (
            Path(__file__).resolve().parent.parent
            / "inputs" / "procedural_schema_v2.json"
        )
    return json.loads(schema_path.read_text(encoding="utf-8-sig"))


_SCHEMA = _read_schema()
_SCHEMA_NODE_TYPES = set(_SCHEMA.get("flow_node_types") or [])
_SCHEMA_PROCESS_TYPES = {value for value in _SCHEMA_NODE_TYPES if value.startswith("P")}

VALID_ROLES = {"context", "input", "standard", "action", "decision", "outcome"}

ROLE_TO_NODE_TYPES: dict[str, set[str]] = {
    "context": {value for value in _SCHEMA_NODE_TYPES if value.startswith("E")},
    "input": {"input"} & _SCHEMA_NODE_TYPES,
    "standard": {"standard"} & _SCHEMA_NODE_TYPES,
    "action": _SCHEMA_PROCESS_TYPES - {"P3_branch_routing"},
    "decision": {"P1_assessment", "P3_branch_routing", "P10_sufficiency"} & _SCHEMA_NODE_TYPES,
    "outcome": {value for value in _SCHEMA_NODE_TYPES if value.startswith("X")},
}

VALID_CARD_NATURES = set(_SCHEMA.get("card_natures") or [])
VALID_DISPOSITIONS = {"mapped", "support_only", "excluded_nonprocedural", "ungraphable"}
VALID_RELATION_KINDS = {"trigger", "sequence", "reference", "produce", "branch", "feedback"}
VALID_TRIGGER_MODES = {"event", "condition"}
_EDGE_PROPERTIES = _SCHEMA.get("edge_properties") or {}
_QUALIFIER_CONTRACT = {"aimed_to", "may_lead_to", "helps_achieve"}
_schema_qualifiers = set(_EDGE_PROPERTIES.get("qualifier_allowed") or [])
VALID_QUALIFIERS = _QUALIFIER_CONTRACT & _schema_qualifiers if _schema_qualifiers else _QUALIFIER_CONTRACT

_MODALITY_CONTRACT = {"required", "permitted", "prohibited", "risky", "optional"}
_schema_modalities = set(_EDGE_PROPERTIES.get("modality_allowed") or [])
VALID_MODALITIES = _MODALITY_CONTRACT & _schema_modalities if _schema_modalities else _MODALITY_CONTRACT
VALID_RELATION_TYPES = set(_SCHEMA.get("relation_types") or [])

# (kind, source_role, target_role) -> extra_checks or None (None = invalid)
RELATION_ENDPOINT_MATRIX: dict[tuple[str, str, str], list[str] | None] = {}
for _src_roles, _tgt_roles, _kinds in [
    ({"context", "outcome"}, {"action", "decision"}, ["trigger"]),
    ({"action", "decision", "outcome"}, {"action", "decision", "outcome"}, ["sequence"]),
    ({"action", "decision"}, {"input", "standard"}, ["reference"]),
    ({"action", "decision"}, {"outcome"}, ["produce"]),
    ({"decision"}, {"action", "outcome"}, ["branch"]),
    ({"outcome", "decision"}, {"action", "decision"}, ["feedback"]),
]:
    for _src in _src_roles:
        for _tgt in _tgt_roles:
            for _kind in _kinds:
                RELATION_ENDPOINT_MATRIX[(_kind, _src, _tgt)] = []

# Additional constraints
RELATION_EXTRA_CONSTRAINTS: dict[str, Any] = {
    "trigger": {"require_trigger_mode": True},
    "branch": {"require_p3_source": True, "min_branches": 2, "require_condition_each": True},
    "produce": {"forbid_p3_source": True},
    "reference": {"target_role_must_be": {"input", "standard"}},
}

# Kind to edge_type mapping
KIND_TO_EDGE_TYPE: dict[str, str] = {
    "trigger": "PRECEDES",
    "sequence": "PRECEDES",
    "reference": "REFERENCES",
    "produce": "PRODUCES",
    "branch": "DECIDES",
    "feedback": "FEEDBACK",
}

def validate_process_ir_payload(
    payload: dict[str, Any],
    section_id: str,
    s1_candidates: list[dict[str, Any]],
    allowed_unit_ids: set[str],
    unit_evidence_text: dict[str, str] | None = None,
) -> list[str]:
    """Validate a Process IR payload against the full Process IR contract.

    Returns a list of error strings (empty = valid).
    """
    errors: list[str] = []

    s1_ids = {str(c.get("candidate_id") or "") for c in s1_candidates}
    s1_index = {str(c.get("candidate_id") or ""): c for c in s1_candidates}

    # --- Top-level ---
    if payload.get("section_id") != section_id:
        errors.append(f"section_id mismatch: expected {section_id}, got {payload.get('section_id')}")

    episodes = payload.get("episodes")
    if not isinstance(episodes, list):
        return errors + ["episodes must be a list"]
    candidate_audit = payload.get("candidate_audit")
    if not isinstance(candidate_audit, list):
        return errors + ["candidate_audit must be a list"]

    skip_reason = payload.get("skip_reason")
    if episodes and skip_reason is not None:
        errors.append("skip_reason must be null when episodes is non-empty")
    if not episodes and not isinstance(skip_reason, str):
        errors.append("skip_reason must be a non-empty Chinese string when episodes is empty")
    if not episodes and isinstance(skip_reason, str) and not skip_reason.strip():
        errors.append("skip_reason must be a non-empty Chinese string when episodes is empty")

    # Index episodes
    episode_ids: set[str] = set()
    episodes_by_id: dict[str, dict[str, Any]] = {}
    for idx, ep in enumerate(episodes, 1):
        owner = f"episodes[{idx}]"
        if not isinstance(ep, dict):
            errors.append(f"{owner} must be an object")
            continue
        eid = str(ep.get("episode_id") or "")
        if not eid:
            errors.append(f"{owner} missing episode_id")
        elif not _is_valid_id(eid, "ep_"):
            errors.append(f"{owner} episode_id must match ep_NNN format, got {eid}")
        elif eid in episode_ids:
            errors.append(f"{owner} duplicate episode_id {eid}")
        else:
            episode_ids.add(eid)
            episodes_by_id[eid] = ep

    # --- Validate each episode ---
    for idx, ep in enumerate(episodes, 1):
        owner = f"episodes[{idx}]"
        if not isinstance(ep, dict):
            continue
        eid = ep.get("episode_id", f"<missing-{idx}>")

        # source_candidate_ids
        src_ids = ep.get("source_candidate_ids")
        if not isinstance(src_ids, list) or not src_ids:
            errors.append(f"{owner} source_candidate_ids must be a non-empty list")
            src_ids = []
        else:
            if len(src_ids) != len(set(str(value) for value in src_ids)):
                errors.append(f"{owner} source_candidate_ids contains duplicates")
            unknown_src = set(str(s) for s in src_ids) - s1_ids
            if unknown_src:
                errors.append(f"{owner} references unknown S1 candidates: {sorted(unknown_src)}")

        # focal_question
        fq = ep.get("focal_question")
        if not isinstance(fq, str) or not fq.strip():
            errors.append(f"{owner} focal_question must be a non-empty string")

        # title
        title = ep.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"{owner} title must be a non-empty string")

        # card_nature
        cn = ep.get("card_nature")
        if cn not in VALID_CARD_NATURES:
            errors.append(f"{owner} card_nature must be one of {VALID_CARD_NATURES}, got {cn}")

        # split_reason when candidate reused
        split_reason = ep.get("split_reason")
        if split_reason is not None and not isinstance(split_reason, str):
            errors.append(f"{owner} split_reason must be null or a non-empty string")

        # elements
        elements = ep.get("elements")
        if not isinstance(elements, list) or not elements:
            errors.append(f"{owner} elements must be a non-empty list")
            elements = []
        relations = ep.get("relations")
        if not isinstance(relations, list) or not relations:
            errors.append(f"{owner} relations must be a non-empty list")
            relations = []

        # Collect element IDs per episode
        element_ids: set[str] = set()
        elements_by_id: dict[str, dict[str, Any]] = {}
        has_action_or_decision = False

        for ei, elem in enumerate(elements, 1):
            e_owner = f"{owner}.elements[{ei}]"
            if not isinstance(elem, dict):
                errors.append(f"{e_owner} must be an object")
                continue
            el_id = str(elem.get("element_id") or "")
            if not el_id:
                errors.append(f"{e_owner} missing element_id")
            elif not _is_valid_id(el_id, "e"):
                errors.append(f"{e_owner} element_id must match eNNN format, got {el_id}")
            elif el_id in element_ids:
                errors.append(f"{e_owner} duplicate element_id {el_id}")
            else:
                element_ids.add(el_id)
                elements_by_id[el_id] = elem

            role = elem.get("role")
            if role not in VALID_ROLES:
                errors.append(f"{e_owner} invalid role {role}, must be one of {VALID_ROLES}")
            else:
                if role in {"action", "decision"}:
                    has_action_or_decision = True

            label = elem.get("label")
            if not isinstance(label, str) or not label.strip():
                errors.append(f"{e_owner} label must be a non-empty string")

            ev_ids = elem.get("evidence_unit_ids")
            if not isinstance(ev_ids, list) or not ev_ids:
                errors.append(f"{e_owner} evidence_unit_ids must be a non-empty list")
            else:
                for unit_id in ev_ids:
                    if str(unit_id) not in allowed_unit_ids:
                        errors.append(f"{e_owner} evidence_unit_ids references out-of-section unit {unit_id}")

            modality = elem.get("modality")
            if modality is not None and modality not in VALID_MODALITIES:
                errors.append(f"{e_owner} invalid modality {modality}")

        if not has_action_or_decision:
            errors.append(f"{owner} must have at least one element with role action or decision")

        # Validate relations
        relation_ids: set[str] = set()
        p3_branch_counts: dict[str, int] = {}

        for ri, rel in enumerate(relations, 1):
            r_owner = f"{owner}.relations[{ri}]"
            if not isinstance(rel, dict):
                errors.append(f"{r_owner} must be an object")
                continue
            r_id = str(rel.get("relation_id") or "")
            if not r_id:
                errors.append(f"{r_owner} missing relation_id")
            elif not _is_valid_id(r_id, "r"):
                errors.append(f"{r_owner} relation_id must match rNNN format, got {r_id}")
            elif r_id in relation_ids:
                errors.append(f"{r_owner} duplicate relation_id {r_id}")
            else:
                relation_ids.add(r_id)

            kind = rel.get("kind")
            if kind not in VALID_RELATION_KINDS:
                errors.append(f"{r_owner} invalid kind {kind}, must be one of {VALID_RELATION_KINDS}")
                continue

            # Resolve endpoints based on kind
            src_el_id, tgt_el_id = _resolve_endpoints(rel, kind)
            if not src_el_id or not tgt_el_id:
                errors.append(f"{r_owner} missing endpoint fields for kind={kind}")
                continue
            if src_el_id not in element_ids:
                errors.append(f"{r_owner} source element {src_el_id} not found in episode")
            if tgt_el_id not in element_ids:
                errors.append(f"{r_owner} target element {tgt_el_id} not found in episode")

            # Endpoint role compatibility
            if src_el_id in elements_by_id and tgt_el_id in elements_by_id:
                src_role = elements_by_id[src_el_id].get("role")
                tgt_role = elements_by_id[tgt_el_id].get("role")
                key = (kind, src_role, tgt_role)
                # kind is approximate; S3 determines exact edge_type from source_quote.
                # Off-matrix combinations are non-fatal — S3 can remap.
                if key not in RELATION_ENDPOINT_MATRIX:
                    pass  # non-fatal: S3 corrects based on source_quote

            # Kind-specific checks
            if kind == "trigger":
                tm = rel.get("trigger_mode")
                if tm not in VALID_TRIGGER_MODES:
                    errors.append(f"{r_owner} trigger_mode must be one of {VALID_TRIGGER_MODES}, got {tm}")
                if tm == "condition" and (not isinstance(rel.get("condition"), str) or not rel["condition"].strip()):
                    errors.append(f"{r_owner} condition trigger requires non-empty condition string")
                if tm == "event" and rel.get("condition") is not None and not isinstance(rel.get("condition"), str):
                    errors.append(f"{r_owner} event trigger condition must be null or string")

            if kind == "branch":
                src_elem = elements_by_id.get(src_el_id, {})
                if src_elem.get("role") != "decision":
                    errors.append(f"{r_owner} branch source must have role=decision")
                if not isinstance(rel.get("condition"), str) or not rel["condition"].strip():
                    errors.append(f"{r_owner} branch requires non-empty condition")
                p3_branch_counts[src_el_id] = p3_branch_counts.get(src_el_id, 0) + 1

            if kind == "produce":
                src_elem = elements_by_id.get(src_el_id, {})
                if src_elem.get("role") == "decision" and p3_branch_counts.get(src_el_id, 0) >= 2:
                    errors.append(f"{r_owner} decision element with >=2 branch relations should use branch kind, not produce")

            if kind == "feedback":
                if not isinstance(rel.get("condition"), str) and rel.get("condition") is not None:
                    errors.append(f"{r_owner} feedback condition must be null or string")

            # relation_type validation
            rt = rel.get("relation_type")
            if rt is not None and rt not in VALID_RELATION_TYPES:
                errors.append(f"{r_owner} invalid relation_type {rt}")

            # qualifier validation
            qual = rel.get("qualifier")
            if qual is not None and qual not in VALID_QUALIFIERS:
                errors.append(f"{r_owner} invalid qualifier {qual}")

            # evidence_unit_ids
            ev_ids = rel.get("evidence_unit_ids")
            if not isinstance(ev_ids, list) or not ev_ids:
                errors.append(f"{r_owner} evidence_unit_ids must be a non-empty list")
            else:
                for unit_id in ev_ids:
                    if str(unit_id) not in allowed_unit_ids:
                        errors.append(f"{r_owner} evidence_unit_ids references out-of-section unit {unit_id}")

            source_quote = rel.get("source_quote")
            if not isinstance(source_quote, str) or not source_quote.strip():
                errors.append(f"{r_owner} source_quote is required and must be a non-empty string")
            elif unit_evidence_text is not None:
                    quote_norm = _normalized_text(source_quote)
                    cited_text = " ".join(
                        str(unit_evidence_text.get(str(unit_id), ""))
                        for unit_id in (ev_ids or [])
                    )
                    if quote_norm not in _normalized_text(cited_text):
                        errors.append(
                            f"{r_owner} source_quote is not found in its evidence_unit_ids"
                        )

            # Forbidden fields
            for forbidden in (
                "derivation",
                "evidence_strength",
                "review_status",
                "answer_eligible",
                "modality",
            ):
                if forbidden in rel and rel[forbidden] is not None:
                    errors.append(f"{r_owner} must not declare {forbidden}")

        # Check each decision element with branch relations independently;
        # aggregate episode counts can hide one-branch nodes.
        decision_elements = [eid for eid, el in elements_by_id.items() if el.get("role") == "decision"]
        for d_id in decision_elements:
            branch_count = p3_branch_counts.get(d_id, 0)
            if branch_count == 1:
                errors.append(
                    f"{owner} decision element {d_id} has only "
                    f"{branch_count} branch relation(s), need >=2 (or none)"
                )

        # Check evidence within source_candidate_ids union
        if src_ids:
            src_unit_union = _source_candidate_unit_union(s1_index, src_ids)
            episode_evidence_units: set[str] = set()
            for ei, elem in enumerate(elements, 1):
                if not isinstance(elem, dict):
                    continue
                for unit_id in (elem.get("evidence_unit_ids") or []):
                    episode_evidence_units.add(str(unit_id))
                    if str(unit_id) not in src_unit_union:
                        errors.append(
                            f"{owner}.elements[{ei}] evidence unit {unit_id} "
                            f"outside source_candidate_ids unit union"
                        )
            for ri, rel in enumerate(relations, 1):
                if not isinstance(rel, dict):
                    continue
                for unit_id in (rel.get("evidence_unit_ids") or []):
                    episode_evidence_units.add(str(unit_id))
                    if str(unit_id) not in src_unit_union:
                        errors.append(
                            f"{owner}.relations[{ri}] evidence unit {unit_id} "
                            f"outside source_candidate_ids unit union"
                        )
            for src_id in (str(value) for value in src_ids):
                candidate_units = {
                    str(value)
                    for value in (s1_index.get(src_id, {}).get("unit_ids") or [])
                }
                if candidate_units and not (candidate_units & episode_evidence_units):
                    errors.append(
                        f"{owner} source candidate {src_id} contributes no evidence unit "
                        "to the episode"
                    )

        # Connectivity check (ignoring direction)
        if element_ids:
            connected = _check_connectivity(elements_by_id, relations, element_ids)
            if not connected:
                errors.append(f"{owner} elements do not form a single connected component")

    # --- Validate candidate_audit ---
    audit_ids: set[str] = set()
    for ai, audit in enumerate(candidate_audit, 1):
        a_owner = f"candidate_audit[{ai}]"
        if not isinstance(audit, dict):
            errors.append(f"{a_owner} must be an object")
            continue
        cid = str(audit.get("candidate_id") or "")
        if not cid:
            errors.append(f"{a_owner} missing candidate_id")
        elif cid in audit_ids:
            errors.append(f"{a_owner} duplicate candidate_id {cid}")
        else:
            audit_ids.add(cid)
        if cid and cid not in s1_ids:
            errors.append(f"{a_owner} references unknown S1 candidate {cid}")

        disp = audit.get("disposition")
        if disp not in VALID_DISPOSITIONS:
            errors.append(f"{a_owner} invalid disposition {disp}")

        ep_ids = audit.get("episode_ids") or []
        if not isinstance(ep_ids, list):
            errors.append(f"{a_owner} episode_ids must be a list")
            ep_ids = []

        if disp in {"mapped", "support_only"}:
            if not ep_ids:
                errors.append(f"{a_owner} {disp} must reference at least one episode")
            else:
                for epid in ep_ids:
                    if epid not in episode_ids:
                        errors.append(f"{a_owner} references unknown episode {epid}")
        elif disp in {"excluded_nonprocedural", "ungraphable"}:
            if ep_ids:
                errors.append(f"{a_owner} {disp} must have empty episode_ids")
            reason = audit.get("reason") or ""
            if not reason.strip():
                errors.append(f"{a_owner} {disp} requires a specific reason")

        # KG coverage must not be reason
        reason = str(audit.get("reason") or "")
        if "KG" in reason and ("覆盖" in reason or "已表达" in reason or "已保存" in reason):
            errors.append(f"{a_owner} must not use KG coverage as exclusion reason")

        # No forbidden fields
        if "decision" in audit:
            errors.append(f"{a_owner} must not declare legacy 'decision' field (use disposition)")

    # Check exactly one audit per S1 candidate
    missing = s1_ids - audit_ids
    extra = audit_ids - s1_ids
    if missing:
        errors.append(f"candidate_audit missing S1 candidates: {sorted(missing)}")
    if extra:
        errors.append(f"candidate_audit has unknown candidates: {sorted(extra)}")

    # Check multi-candidate→episode consistency
    candidate_to_episodes: dict[str, set[str]] = {}
    for audit in candidate_audit:
        if not isinstance(audit, dict):
            continue
        cid = audit.get("candidate_id")
        eps = set(audit.get("episode_ids") or [])
        if cid:
            candidate_to_episodes[str(cid)] = eps

    for ep in episodes:
        if not isinstance(ep, dict):
            continue
        eid = ep.get("episode_id", "")
        src_ids_list = [str(s) for s in (ep.get("source_candidate_ids") or [])]
        for src_id in src_ids_list:
            if src_id in candidate_to_episodes:
                if eid not in candidate_to_episodes[src_id]:
                    errors.append(
                        f"episode {eid} lists candidate {src_id} in source_candidate_ids "
                        f"but candidate_audit does not map it to this episode"
                    )

    # Reverse consistency: every audit mapping must also be declared by the episode.
    for cid, eps in candidate_to_episodes.items():
        for eid in eps:
            ep = episodes_by_id.get(eid)
            if not isinstance(ep, dict):
                continue
            ep_sources = {str(value) for value in (ep.get("source_candidate_ids") or [])}
            if cid not in ep_sources:
                errors.append(
                    f"candidate_audit maps candidate {cid} to episode {eid}, "
                    "but the episode does not list it in source_candidate_ids"
                )

    # Check split_reason for candidates mapped to multiple episodes
    for cid, eps in candidate_to_episodes.items():
        if len(eps) > 1:
            for ep in episodes:
                if not isinstance(ep, dict):
                    continue
                eid = ep.get("episode_id", "")
                if eid in eps and not ep.get("split_reason"):
                    errors.append(
                        f"candidate {cid} is mapped to multiple episodes but "
                        f"episode {eid} missing split_reason"
                    )

    return errors


def generate_compile_audit(
    process_ir: dict[str, Any],
    cards_payload: dict[str, Any],
    section_id: str,
) -> dict[str, Any]:
    """Generate compile_audit from Process IR + S3 cards output.

    Maps IR elements to card nodes for traceability. S3 LLM is responsible
    for node_type assignment and ID generation; this function only records
    the mapping for downstream P7D traceability.
    """
    ir_json = json.dumps(process_ir, ensure_ascii=False, sort_keys=True)
    source_hash = hashlib.sha256(ir_json.encode("utf-8")).hexdigest()

    episodes = process_ir.get("episodes") or []
    cards = cards_payload.get("cards") or []

    compile_entries: list[dict[str, Any]] = []

    for ep_idx, ep in enumerate(episodes):
        if not isinstance(ep, dict):
            continue
        episode_id = ep.get("episode_id", "")
        card = cards[ep_idx] if ep_idx < len(cards) else {}

        elements = ep.get("elements") or []
        card_nodes = (card.get("flow_nodes") or []) if isinstance(card, dict) else []
        element_node_map: dict[str, str] = {}
        for ir_elem in elements:
            if not isinstance(ir_elem, dict):
                continue
            eid = ir_elem.get("element_id", "")
            elabel = ir_elem.get("label", "")
            for node in card_nodes:
                if isinstance(node, dict) and node.get("label") == elabel:
                    element_node_map[str(eid)] = str(node.get("node_id", ""))
                    break

        relations = ep.get("relations") or []
        card_edges = (card.get("flow_edges") or []) if isinstance(card, dict) else []
        relation_edge_map: dict[str, str] = {}
        for ir_rel in relations:
            if not isinstance(ir_rel, dict):
                continue
            rid = ir_rel.get("relation_id", "")
            kind = ir_rel.get("kind", "")
            src_el_id, tgt_el_id = _resolve_endpoints(ir_rel, kind)
            src_node = element_node_map.get(src_el_id, "")
            tgt_node = element_node_map.get(tgt_el_id, "")
            for edge in card_edges:
                if (isinstance(edge, dict)
                        and edge.get("source") == src_node
                        and edge.get("target") == tgt_node):
                    relation_edge_map[str(rid)] = str(edge.get("edge_id", ""))
                    break

        compile_entries.append({
            "episode_id": episode_id,
            "card_id": card.get("card_id", "") if isinstance(card, dict) else "",
            "element_node_map": element_node_map,
            "relation_edge_map": relation_edge_map,
            "compile_status": "traced" if card else "unmatched",
            "errors": [] if card else ["no matching card found for episode"],
        })

    return {
        "section_id": section_id,
        "compiler_version": COMPILER_VERSION,
        "source_process_ir_sha256": source_hash,
        "episodes": compile_entries,
    }



def _is_valid_id(value: str, prefix: str) -> bool:
    """Check id format: prefix + digits only."""
    if not value.startswith(prefix):
        return False
    suffix = value[len(prefix):]
    return suffix.isdigit() and len(suffix) == 3


def _normalized_text(value: str) -> str:
    return " ".join(str(value).split()).casefold()


def _resolve_endpoints(rel: dict[str, Any], kind: str) -> tuple[str, str]:
    """Return (source_element_id, target_element_id) based on relation kind."""
    kind_endpoints: dict[str, tuple[str, str]] = {
        "trigger": ("trigger_element_id", "process_element_id"),
        "sequence": ("before_element_id", "after_element_id"),
        "reference": ("process_element_id", "auxiliary_element_id"),
        "produce": ("process_element_id", "outcome_element_id"),
        "branch": ("decision_element_id", "target_element_id"),
        "feedback": ("result_element_id", "process_element_id"),
    }
    src_field, tgt_field = kind_endpoints.get(kind, ("", ""))
    return (str(rel.get(src_field) or ""), str(rel.get(tgt_field) or ""))


def _infer_node_category(node_type: str) -> str:
    if node_type.startswith("E"):
        return "entry"
    elif node_type.startswith("P"):
        return "process"
    elif node_type.startswith("X"):
        return "exit"
    elif node_type in {"input", "standard"}:
        return "auxiliary"
    return "process"


def _source_candidate_unit_union(
    s1_index: dict[str, dict[str, Any]],
    src_ids: list[str],
) -> set[str]:
    """Union of all unit_ids from given S1 candidates."""
    result: set[str] = set()
    for cid in src_ids:
        c = s1_index.get(cid)
        if c:
            for uid in (c.get("unit_ids") or []):
                result.add(str(uid))
    return result


def _check_connectivity(
    elements_by_id: dict[str, dict[str, Any]],
    relations: list[dict[str, Any]],
    element_ids: set[str],
) -> bool:
    """Check if all elements form one connected component (ignoring edge direction)."""
    if not element_ids:
        return True

    # Build adjacency set
    adj: dict[str, set[str]] = {eid: set() for eid in element_ids}
    for rel in relations:
        if not isinstance(rel, dict):
            continue
        kind = rel.get("kind", "")
        src, tgt = _resolve_endpoints(rel, kind)
        if src in adj and tgt in adj:
            adj[src].add(tgt)
            adj[tgt].add(src)

    # BFS from first element
    start = next(iter(element_ids))
    visited: set[str] = set()
    queue = [start]
    while queue:
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        for neighbor in adj.get(node, set()):
            if neighbor not in visited:
                queue.append(neighbor)

    return visited == element_ids
