from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
DEFAULT_OUTPUT_DIR = PHASE_DIR / "outputs" / "p7e_bridge_candidates"
DEFAULT_REPORT_DIR = PHASE_DIR / "reports" / "p7e_bridge_candidates"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "for", "from", "if", "in", "is",
    "it", "its", "of", "on", "or", "such", "that", "the", "their", "this", "to", "with", "within",
    "customer", "customers", "process", "risk", "risks", "review", "assessment", "assess", "screen",
    "screening", "determine", "determined", "required", "requires", "relationship", "business",
}

NATURE_DIRECTIONS: dict[tuple[str, str], str] = {
    ("risk_indicator", "assessment"): "provides_basis",
    ("risk_indicator", "execution"): "provides_basis",
    ("assessment", "execution"): "proceeds_to",
    ("control", "assessment"): "supports_control",
    ("control", "execution"): "supports_control",
    ("execution", "execution"): "proceeds_to",
    ("assessment", "assessment"): "provides_basis",
}

STRONG_TERMS = {
    "pep", "peps", "high-net-worth", "jurisdiction", "jurisdictions",
    "private", "banking", "wealth", "kyc", "cdd", "edd", "onboarding", "committee", "suitability",
    "beneficial", "owner", "owners", "ubo", "ubos", "sanctions", "adverse", "media", "screening",
    "enhanced", "diligence", "standard", "full",
}

SOURCE_NODE_PRIORITY = {
    "X1_classification": 30, "X2_product": 30, "X3_state_change": 20,
    "X4_handoff": 40, "X5_config_change": 20, "X7_continuing_obligation": 30,
    "P3_branch_routing": 20, "P1_assessment": 10,
}
TARGET_NODE_PRIORITY = {
    "E1_event_signal": 40, "E3_state_threshold": 30, "E8_decision_finding": 30,
    "P1_assessment": 20, "P2_execution": 20, "standard": 10, "input": 10,
}
CONFIDENCE_PRIORITY = {"strong_candidate": 30, "candidate": 20, "needs_review": 10}

# Outlet node types (nodes that can serve as bridge source)
OUTLET_NODE_TYPES = {
    "X1_classification", "X2_product", "X3_state_change",
    "X4_handoff", "X5_config_change", "X7_continuing_obligation",
}
# Inlet node types (nodes that can serve as bridge target)
INLET_NODE_TYPES = {
    "E1_event_signal", "E3_state_threshold", "E8_decision_finding",
    "P1_assessment", "P2_execution", "standard", "input",
}

# KG relation_type → preferred outlet→inlet pairs
KG_RELATION_OUTLET_INLET: dict[str, list[tuple[str, str]]] = {
    "summarizes": [("X1_classification", "E8_decision_finding"), ("P1_assessment", "P1_assessment")],
    "grounds": [("X1_classification", "P1_assessment"), ("standard", "P1_assessment")],
    "prepares": [("X4_handoff", "E1_event_signal"), ("X3_state_change", "E1_event_signal")],
    "illustrates": [("X1_classification", "standard"), ("P3_branch_routing", "P1_assessment")],
    "elaborates": [("X1_classification", "E1_event_signal"), ("P2_execution", "P2_execution")],
}

# Outlet→Inlet node_type compatibility: which combinations have semantic meaning.
# Combinations NOT in this set get a score penalty (-2) but are not rejected.
# This filters noise while allowing edge cases through if other signals are strong.
OUTLET_INLET_COMPAT: dict[str, set[str]] = {
    "X1_classification": {"E8_decision_finding", "P1_assessment", "E1_event_signal", "E3_state_threshold", "P2_execution"},
    "X2_product": {"input", "P2_execution", "E1_event_signal"},
    "X3_state_change": {"E1_event_signal", "E3_state_threshold", "P2_execution"},
    "X4_handoff": {"E4_handoff", "P2_execution", "E1_event_signal"},
    "X5_config_change": {"standard", "E3_state_threshold"},
    "X7_continuing_obligation": {"P7_monitoring", "E5_time_cycle"},
    "P3_branch_routing": {"E1_event_signal", "P2_execution", "P1_assessment"},
    "P1_assessment": {"E8_decision_finding", "P1_assessment", "E1_event_signal"},
}
OUTLET_INLET_PENALTY = -4  # Score penalty for incompatible node_type pairs

BLOCKING_OUTPUT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bunsuitable\b",
        r"\bfilter(?:ed)?\s+out\b",
        r"\breject(?:ed)?\b",
        r"\bdeclin(?:e|ed)\b",
    ]
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def collect_cards(payload: Any) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    if isinstance(payload, list):
        for item in payload:
            cards.extend(collect_cards(item))
    elif isinstance(payload, dict):
        if isinstance(payload.get("cards"), list):
            cards.extend(collect_cards(payload["cards"]))
        elif payload.get("card_id"):
            cards.append(payload)
    return cards


def collect_card_files(card_paths: list[str], card_dirs: list[str]) -> list[Path]:
    files = [Path(path) for path in card_paths]
    for card_dir in card_dirs:
        root = Path(card_dir)
        if root.is_file():
            files.append(root)
        else:
            files.extend(sorted(root.rglob("cards.raw.json")))
    unique: list[Path] = []
    seen: set[Path] = set()
    for file in files:
        resolved = file.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(file)
    return unique


def load_cards(card_files: list[Path], allowed_card_ids: set[str] | None) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for file in card_files:
        for card in collect_cards(read_json(file)):
            if allowed_card_ids is None or card.get("card_id") in allowed_card_ids:
                cards.append(card)
    return cards


def allowed_cards_from_manifest(path: Path | None) -> set[str] | None:
    if path is None:
        return None
    allowed: set[str] = set()
    for row in read_jsonl(path):
        if (row.get("card_result") == "pass" or row.get("review_result") == "pass") and row.get("card_id"):
            allowed.add(row["card_id"])
    return allowed


def tokenize(text: str) -> set[str]:
    normalized = text.lower().replace("/", " ").replace("-", "-")
    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", normalized)
    kept = {token for token in tokens if len(token) >= 3 and token not in STOPWORDS}
    if "high" in tokens and "net" in tokens and "worth" in tokens:
        kept.add("high-net-worth")
    return kept


def card_standard_text(card: dict[str, Any]) -> str:
    parts: list[str] = []
    for node in card.get("flow_nodes") or []:
        if node.get("node_type") in {"standard", "input"}:
            parts.extend([node.get("label"), node.get("description"), node.get("source_quote")])
    return " ".join(str(part) for part in parts if part)


def node_text(card: dict[str, Any], node: dict[str, Any]) -> str:
    parts = [
        card.get("title"),
        card.get("summary"),
        card.get("scenario"),
        card.get("trigger"),
        card.get("objective"),
        node.get("label"),
        node.get("description"),
        node.get("source_quote"),
    ]
    if card.get("card_nature") == "risk_indicator" and node.get("node_type") in {"output", "end", "decision"}:
        parts.append(card_standard_text(card))
    return " ".join(str(part) for part in parts if part)


def outlet_nodes(card: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract outlet nodes from a card for bridge generation."""
    rows: list[dict[str, Any]] = []
    for node in card.get("flow_nodes") or []:
        nt = node.get("node_type", "")
        if nt in OUTLET_NODE_TYPES:
            rows.append(_node_info(card, node))
            continue
        # P3_branch_routing only qualifies if it has >=2 DECIDES edges
        if nt == "P3_branch_routing":
            decide_count = sum(1 for e in card.get("flow_edges") or []
                              if e.get("edge_type") == "DECIDES" and e.get("source") == node.get("node_id"))
            if decide_count >= 2:
                rows.append(_node_info(card, node))
            continue
        # P1_assessment only qualifies if it has PRODUCES to an exit
        if nt == "P1_assessment":
            produces_to_exit = any(
                e.get("edge_type") == "PRODUCES" and e.get("source") == node.get("node_id")
                and any(n.get("node_id") == e.get("target") and (n.get("node_type") or "").startswith("X")
                        for n in (card.get("flow_nodes") or []))
                for e in (card.get("flow_edges") or [])
            )
            if produces_to_exit:
                rows.append(_node_info(card, node))
            continue
    return rows


def inlet_nodes(card: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract inlet nodes from a card for bridge generation."""
    rows: list[dict[str, Any]] = []
    for node in card.get("flow_nodes") or []:
        if node.get("node_type", "") in INLET_NODE_TYPES:
            rows.append(_node_info(card, node))
    return rows


def _node_info(card: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    return {
        "card_id": card.get("card_id"),
        "section_id": card.get("section_id"),
        "card_nature": card.get("card_nature"),
        "node_id": node.get("node_id"),
        "node_type": node.get("node_type"),
        "label": node.get("label"),
        "evidence_strength": node.get("evidence_strength"),
        "evidence_unit_ids": node.get("evidence_unit_ids") or [],
        "text": node_text(card, node),
        "terms": tokenize(node_text(card, node)),
    }


def deprecated_interfaces(card: dict[str, Any], kinds: set[str]) -> list[dict[str, Any]]:
    """Legacy interface extraction — kept for backward compat with old card format."""
    rows: list[dict[str, Any]] = []
    for node in card.get("flow_nodes") or []:
        if node.get("node_type") not in kinds:
            continue
        rows.append(_node_info(card, node))
    return rows


# Real textbook chapter structure: section_id → (part, chapter, heading_group)
_REAL_STRUCT: dict[str, tuple[int, int, int]] = {}


def load_real_structure(mapping_path: Path) -> None:
    """Load section→real-chapter mapping from a p-ch-h JSON file."""
    global _REAL_STRUCT
    raw = json.loads(mapping_path.read_text(encoding="utf-8-sig"))
    for section_id, pch_str in raw.items():
        if not pch_str or not isinstance(pch_str, str):
            continue
        m = re.match(r"p(\d+)-ch(\d+)-h(\d+)", pch_str)
        if m:
            _REAL_STRUCT[section_id] = (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def section_relation(source_section: str | None, target_section: str | None) -> tuple[int, str | None]:
    if not _REAL_STRUCT:
        return _section_relation_legacy(source_section, target_section)
    src = _REAL_STRUCT.get(source_section or "")
    tgt = _REAL_STRUCT.get(target_section or "")
    if not src or not tgt:
        return 0, None
    src_part, src_ch, src_hd = src
    tgt_part, tgt_ch, tgt_hd = tgt
    if src == tgt:
        return 2, "section_order"  # Strong: same heading group
    if src_part == tgt_part and src_ch == tgt_ch:
        return 1, "chapter_proximity"  # Weak: same chapter, different heading
    if src_part == tgt_part and abs(tgt_ch - src_ch) == 1:
        return 1, "chapter_proximity"  # Weak: adjacent chapters
    return 0, None


def _section_relation_legacy(source_section: str | None, target_section: str | None) -> tuple[int, str | None]:
    """Fallback using old CH numbering when real structure not loaded."""
    match_s = re.search(r"CH(\d+)-S(\d+)", source_section or "")
    match_t = re.search(r"CH(\d+)-S(\d+)", target_section or "")
    if not match_s or not match_t:
        return 0, None
    source_ch, source_s = int(match_s.group(1)), int(match_s.group(2))
    target_ch, target_s = int(match_t.group(1)), int(match_t.group(2))
    if source_ch == target_ch and source_s == target_s:
        return 2, "section_order"
    if source_ch == target_ch and 0 <= target_s - source_s <= 2:
        return 1, "chapter_proximity"
    if 0 <= target_ch - source_ch <= 1:
        return 1, "chapter_proximity"
    return 0, None


def shared_units(source: dict[str, Any], target: dict[str, Any]) -> list[str]:
    return sorted(set(source.get("evidence_unit_ids") or []) & set(target.get("evidence_unit_ids") or []))


def label_similarity(source: dict[str, Any], target: dict[str, Any]) -> float:
    """Jaccard similarity on tokenized label + description text of two nodes."""
    s_terms = source.get("terms", set())
    t_terms = target.get("terms", set())
    if not s_terms or not t_terms:
        return 0.0
    intersection = s_terms & t_terms
    union = s_terms | t_terms
    return len(intersection) / len(union) if union else 0.0


def cp_shared_units(
    source_card_id: str,
    target_card_id: str,
    card_cps: dict[str, set[str]],
    cp_unit_map: dict[str, set[str]],
) -> list[str]:
    """Check if any CP covered by source card shares units with any CP covered by target card."""
    src_cps = card_cps.get(source_card_id, set())
    tgt_cps = card_cps.get(target_card_id, set())
    shared: set[str] = set()
    for scp in src_cps:
        for tcp in tgt_cps:
            if scp == tcp:
                continue
            su = cp_unit_map.get(scp, set())
            tu = cp_unit_map.get(tcp, set())
            shared |= su & tu
    return sorted(shared)


def is_blocking_output(source: dict[str, Any]) -> bool:
    # Blocking branch detection must look only at the interface node itself.
    # Card-level text may mention every branch and would wrongly block valid outputs.
    text = str(source.get("label") or "")
    return any(pattern.search(text) for pattern in BLOCKING_OUTPUT_PATTERNS)


def bridge_semantics(source_card: dict[str, Any], target_card: dict[str, Any]) -> str | None:
    return NATURE_DIRECTIONS.get((source_card.get("card_nature"), target_card.get("card_nature")))


def confidence(score: int, basis: list[str], source: dict[str, Any], target: dict[str, Any]) -> str:
    if source.get("evidence_strength") == "functional_dependency" or target.get("evidence_strength") == "functional_dependency":
        return "needs_review"
    if score >= 7 and "lexical_signal" in basis and "card_nature_logic" in basis and len(basis) >= 3:
        return "strong_candidate"
    if score >= 4:
        return "candidate"
    return "needs_review"


def review_result(conf: str, basis: list[str], matched_terms: list[str]) -> str:
    if basis == ["lexical_signal"]:
        return "fail"
    if "card_nature_logic" not in basis:
        return "fail"
    # Require at least one strong signal: content evidence or same-heading proximity.
    # chapter_proximity alone (same chapter / adjacent chapters) is too weak.
    _strong = {"lexical_signal", "label_similarity", "shared_node_unit", "shared_unit", "cp_shared_unit", "section_order"}
    if not (_strong & set(basis)):
        return "fail"
    if conf == "needs_review" and len(matched_terms) < 2:
        return "fail"
    return "pass"


def make_candidate(
    source_card: dict[str, Any],
    target_card: dict[str, Any],
    source: dict[str, Any],
    target: dict[str, Any],
    index: int,
    card_cps: dict[str, set[str]] | None = None,
    cp_unit_map: dict[str, set[str]] | None = None,
) -> dict[str, Any] | None:
    semantics = bridge_semantics(source_card, target_card)
    if semantics == "proceeds_to" and target_card.get("card_nature") == "execution" and is_blocking_output(source):
        return None

    basis: list[str] = []
    score = 0
    if semantics:
        basis.append("card_nature_logic")
        score += 2

    # ── Signal 1: STRONG_TERMS exact match (existing) ──
    matched_terms = sorted((source["terms"] & target["terms"]) & STRONG_TERMS)
    if matched_terms:
        basis.append("lexical_signal")
        score += min(4, len(matched_terms))

    # ── Signal 2: Node-level shared evidence units ──
    shared_node_units = shared_units(source, target)
    if shared_node_units:
        basis.append("shared_node_unit")
        score += 3

    # ── Signal 3: Label text similarity (Jaccard) ──
    jaccard = label_similarity(source, target)
    if jaccard >= 0.15:
        basis.append("label_similarity")
        score += max(1, int(jaccard * 8))  # 0.15→1, 0.25→2, 0.38→3

    # ── Signal 4: CP co-membership via shared units ──
    if card_cps and cp_unit_map:
        cp_shared = cp_shared_units(
            source_card.get("card_id", ""),
            target_card.get("card_id", ""),
            card_cps,
            cp_unit_map,
        )
        if cp_shared:
            basis.append("cp_shared_unit")
            score += 2

    # ── Signal 5: Card-level shared units (existing) ──
    shared_card_units = shared_units(source_card, target_card)
    if shared_card_units:
        basis.append("shared_unit")
        score += 3

    section_score, section_basis = section_relation(source.get("section_id"), target.get("section_id"))
    if section_basis:
        basis.append(section_basis)
        score += section_score

    role_ok = source.get("node_type") in SOURCE_NODE_PRIORITY and target.get("node_type") in TARGET_NODE_PRIORITY
    if role_ok:
        score += 1

    score += SOURCE_NODE_PRIORITY.get(source.get("node_type"), 0) // 10
    score += TARGET_NODE_PRIORITY.get(target.get("node_type"), 0) // 10

    # Node_type compatibility: penalize semantically unlikely outlet→inlet pairs
    src_nt = source.get("node_type", "")
    tgt_nt = target.get("node_type", "")
    if src_nt in OUTLET_INLET_COMPAT and tgt_nt not in OUTLET_INLET_COMPAT.get(src_nt, set()):
        basis.append("weak_nt_match")
        score += OUTLET_INLET_PENALTY

    if score < 3 or not basis:
        return None

    conf = confidence(score, basis, source, target)
    review = review_result(conf, basis, matched_terms)
    if not semantics:
        semantics = "may_trigger"
        if review == "pass":
            review = "fail"

    bridge_id = f"p7bridge_{source_card['card_id'].replace('p7card_', '')}__{target_card['card_id'].replace('p7card_', '')}_{index:03d}"
    notes = (
        f"{source_card.get('card_nature')} card output '{source.get('label')}' may connect to "
        f"{target_card.get('card_nature')} card inlet '{target.get('label')}'. "
        f"Semantics: {semantics}. Basis: {', '.join(basis)}."
    )
    if matched_terms:
        notes += f" Matched terms: {', '.join(matched_terms)}."
    if source.get("evidence_strength") == "functional_dependency" or target.get("evidence_strength") == "functional_dependency":
        notes += " Candidate downgraded because at least one interface is functional_dependency."

    return {
        "bridge_id": bridge_id,
        "edge_type": "BRIDGES_TO",
        "source_card_id": source_card.get("card_id"),
        "target_card_id": target_card.get("card_id"),
        "source_node_id": source.get("node_id"),
        "target_node_id": target.get("node_id"),
        "bridge_semantics": semantics,
        "bridge_basis": basis,
        "matched_terms": matched_terms,
        "evidence_unit_ids": sorted(set(source.get("evidence_unit_ids") or []) | set(target.get("evidence_unit_ids") or [])),
        "source_node_strength": source.get("evidence_strength"),
        "target_node_strength": target.get("evidence_strength"),
        "condition": None,
        "confidence": conf,
        "review_status": "needs_review",
        "review_result": review,
        "score": score,
        "interface_score": SOURCE_NODE_PRIORITY.get(source.get("node_type"), 0) + TARGET_NODE_PRIORITY.get(target.get("node_type"), 0),
        "notes": notes,
    }


def candidate_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("review_result") != "pass",
        -CONFIDENCE_PRIORITY.get(row.get("confidence"), 0),
        -int(row.get("score") or 0),
        -int(row.get("interface_score") or 0),
        row.get("source_card_id") or "",
        row.get("target_card_id") or "",
        row.get("source_node_id") or "",
        row.get("target_node_id") or "",
    )


def compact_candidates(candidates: list[dict[str, Any]], max_per_pair_semantics: int = 2) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for candidate in candidates:
        key = (
            candidate.get("source_card_id") or "",
            candidate.get("target_card_id") or "",
            candidate.get("bridge_semantics") or "",
        )
        grouped.setdefault(key, []).append(candidate)

    compacted: list[dict[str, Any]] = []
    for rows in grouped.values():
        rows.sort(key=candidate_sort_key)
        pass_rows = [row for row in rows if row.get("review_result") == "pass"]
        kept = pass_rows[:max_per_pair_semantics] if pass_rows else rows[:1]
        for rank, row in enumerate(kept, 1):
            row["candidate_rank"] = rank
            row["candidate_group_size"] = len(rows)
            compacted.append(row)
    compacted.sort(key=candidate_sort_key)
    return compacted


def generate_candidates(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Legacy topology-only bridge candidate generation."""
    by_id = {card.get("card_id"): card for card in cards}
    outlets = {card["card_id"]: deprecated_interfaces(card, {"output", "end", "decision"}) for card in cards}
    inlets = {card["card_id"]: deprecated_interfaces(card, {"trigger", "start", "action", "standard"}) for card in cards}
    return _pair_and_compact(by_id, outlets, inlets)


def generate_candidates_dual_layer(
    cards: list[dict[str, Any]],
    packages_dir: Path | None = None,
    kg_graph_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Dual-layer bridge generation: KG-backed (Layer 1) + topology fallback (Layer 2).

    Uses the new 27-type node_type schema for outlet/inlet extraction.
    """
    by_id = {card.get("card_id"): card for card in cards}
    outlets = {card["card_id"]: outlet_nodes(card) for card in cards}
    inlets = {card["card_id"]: inlet_nodes(card) for card in cards}
    idx = 1
    kg_pairs: set[tuple[str, str]] = set()
    raw: list[dict[str, Any]] = []

    # ── Layer 1: KG-backed ──
    card_cps: dict[str, set[str]] = {}
    cp_unit_map: dict[str, set[str]] = {}
    if packages_dir:
        card_cps, cp_unit_map = build_card_cp_index(cards, packages_dir)
    if packages_dir and kg_graph_path:
        kg_edges = load_kg_cross_section_edges(kg_graph_path)
        for src_cid, tgt_cid, kg_rel in pair_cards_by_kg(cards, card_cps, kg_edges, by_id):
            kg_pairs.add((src_cid, tgt_cid))
            src_card = by_id.get(src_cid)
            tgt_card = by_id.get(tgt_cid)
            if not src_card or not tgt_card:
                continue
            for source in outlets.get(src_cid, []):
                for target in inlets.get(tgt_cid, []):
                    cand = make_candidate(src_card, tgt_card, source, target, idx, card_cps, cp_unit_map)
                    if cand:
                        cand["bridge_basis"] = {
                            "source": "kg_cp_relation",
                            "signals": cand.get("bridge_basis", []),
                            "kg_relation": kg_rel,
                            "topology_match": {
                                "outlet_type": source.get("node_type"),
                                "inlet_type": target.get("node_type"),
                                "outlet_label": source.get("label"),
                                "inlet_label": target.get("label"),
                            },
                        }
                        cand["review_status"] = "candidate"
                        raw.append(cand)
                        idx += 1

    # ── Layer 2: Topology fallback ──
    for source_id, source_card in by_id.items():
        for target_id, target_card in by_id.items():
            if source_id == target_id:
                continue
            if (source_id, target_id) in kg_pairs:
                continue  # Already covered by Layer 1
            for source in outlets.get(source_id, []):
                for target in inlets.get(target_id, []):
                    cand = make_candidate(source_card, target_card, source, target, idx, card_cps, cp_unit_map)
                    if cand:
                        cand["bridge_basis"] = {
                            "source": "topology_match",
                            "signals": cand.get("bridge_basis", []),
                            "topology_match": {
                                "outlet_type": source.get("node_type"),
                                "inlet_type": target.get("node_type"),
                                "outlet_label": source.get("label"),
                                "inlet_label": target.get("label"),
                            },
                        }
                        cand["review_status"] = "needs_review"
                        raw.append(cand)
                        idx += 1

    return compact_candidates(raw)


def _pair_and_compact(
    by_id: dict[str, dict[str, Any]],
    outlets: dict[str, list[dict[str, Any]]],
    inlets: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    raw: list[dict[str, Any]] = []
    idx = 1
    for source_id, source_card in by_id.items():
        for target_id, target_card in by_id.items():
            if source_id == target_id:
                continue
            for source in outlets.get(source_id, []):
                for target in inlets.get(target_id, []):
                    candidate = make_candidate(source_card, target_card, source, target, idx)
                    if candidate:
                        raw.append(candidate)
                        idx += 1
    return compact_candidates(raw)


# ── KG cross-section CP utilities ──


def build_card_cp_index(
    cards: list[dict[str, Any]], packages_dir: Path
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Map each card to CPs it covers, and each CP to its units (across all sections)."""
    card_cps: dict[str, set[str]] = {}
    cp_unit_map: dict[str, set[str]] = {}
    for card in cards:
        cid = card.get("card_id", "")
        section_id = card.get("section_id", "")
        if not section_id:
            card_cps[cid] = set()
            continue
        task_path = packages_dir / section_id / "task.json"
        if not task_path.exists():
            card_cps[cid] = set()
            continue
        task = read_json(task_path)
        card_units = set(card.get("source_unit_ids") or [])

        cp_units: dict[str, set[str]] = {}
        for edge in task.get("core_point_unit_edges") or []:
            cp_id = edge.get("source_id", "")
            unit_id = edge.get("target_id", "")
            if cp_id and unit_id:
                cp_units.setdefault(cp_id, set()).add(unit_id)
                cp_unit_map.setdefault(cp_id, set()).add(unit_id)

        covered = set()
        for cp_id, units in cp_units.items():
            if units & card_units:
                covered.add(cp_id)
        card_cps[cid] = covered
    return card_cps, cp_unit_map


def load_kg_cross_section_edges(kg_graph_path: Path) -> list[dict[str, Any]]:
    """Load cross-section CP edges from P6 kg_retrieval_graph.json."""
    graph = read_json(kg_graph_path)
    edges = []
    for e in graph.get("edges") or []:
        scope = e.get("edge_scope", "")
        if scope in {"same_chapter_core_point", "cross_chapter_core_point"}:
            edges.append({
                "source_cp": e.get("source_id", ""),
                "target_cp": e.get("target_id", ""),
                "relation_type": e.get("relation_type", ""),
                "support_strength": e.get("support_strength", ""),
                "evidence_unit_ids": e.get("source_evidence_unit_ids", []) + e.get("target_evidence_unit_ids", []),
            })
    return edges


def pair_cards_by_kg(
    cards: list[dict[str, Any]],
    card_cps: dict[str, set[str]],
    kg_edges: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
) -> list[tuple[str, str, dict[str, Any]]]:
    """Generate (source_card_id, target_card_id, kg_relation) triples from KG edges."""
    # Build reverse index: CP → cards
    cp_cards: dict[str, list[str]] = {}
    for cid, cps in card_cps.items():
        for cp in cps:
            cp_cards.setdefault(cp, []).append(cid)

    pairs: list[tuple[str, str, dict[str, Any]]] = []
    for kg_edge in kg_edges:
        src_cp = kg_edge["source_cp"]
        tgt_cp = kg_edge["target_cp"]
        src_cards = cp_cards.get(src_cp, [])
        tgt_cards = cp_cards.get(tgt_cp, [])
        for sc in src_cards:
            for tc in tgt_cards:
                if sc == tc:
                    continue
                src_sec = (by_id.get(sc) or {}).get("section_id", "")
                tgt_sec = (by_id.get(tc) or {}).get("section_id", "")
                if src_sec == tgt_sec:
                    continue  # Skip same-section pairs (not a bridge)
                pairs.append((sc, tc, kg_edge))
    return pairs


def write_report(path: Path, candidates: list[dict[str, Any]], card_count: int) -> None:
    confidence_counts = Counter(row["confidence"] for row in candidates)
    review_counts = Counter(row["review_result"] for row in candidates)
    semantic_counts = Counter(row["bridge_semantics"] for row in candidates)
    lines = [
        "# P7E Bridge Candidate Report",
        "",
        "P7E generates conservative bridge candidates only. It does not create confirmed bridges or modify p7_card.flow_edges.",
        "",
        "## Summary",
        "",
        f"card_count: {card_count}",
        f"candidate_count: {len(candidates)}",
        f"review_result_pass: {review_counts.get('pass', 0)}",
        f"review_result_fail: {review_counts.get('fail', 0)}",
        "",
        "## Confidence",
        "",
    ]
    for name in ["strong_candidate", "candidate", "needs_review"]:
        lines.append(f"- {name}: {confidence_counts.get(name, 0)}")
    lines.extend(["", "## Bridge Semantics", ""])
    for name, count in semantic_counts.most_common():
        lines.append(f"- {name}: {count}")
    lines.extend(["", "## Candidates", ""])
    for row in candidates[:200]:
        lines.append(
            f"- {row['review_result']} | {row['confidence']} | {row['bridge_semantics']} | "
            f"{row['source_card_id']}:{row['source_node_id']} -> {row['target_card_id']}:{row['target_node_id']}"
        )
        lines.append(f"  - basis: {', '.join(row['bridge_basis'])}")
        if row.get("matched_terms"):
            lines.append(f"  - matched_terms: {', '.join(row['matched_terms'])}")
        lines.append(f"  - notes: {row['notes']}")
    if len(candidates) > 200:
        lines.append(f"- ... truncated {len(candidates) - 200} additional candidates")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate P7E bridge candidates from P7C cards.")
    parser.add_argument("--cards", action="append", default=[], help="Path to one cards.raw.json file. Can be repeated.")
    parser.add_argument("--cards-dir", action="append", default=[], help="Directory containing cards.raw.json files. Can be repeated.")
    parser.add_argument(
        "--p7d-manifest",
        help="P7D review manifest. Only card_result=pass cards are used.",
    )
    parser.add_argument(
        "--dual-layer",
        action="store_true",
        help="Enable dual-layer mode: KG-backed (Layer 1) + topology fallback (Layer 2). Uses 27-type node_type schema.",
    )
    parser.add_argument(
        "--packages-dir",
        default=None,
        help="P7B section packages directory (required for --dual-layer KG index).",
    )
    parser.add_argument(
        "--kg-graph",
        default=None,
        help="Path to P6 kg_retrieval_graph.json (for --dual-layer KG-backed pairing).",
    )
    parser.add_argument(
        "--section-mapping",
        default=str(PHASE_DIR.parents[4] / "section_mapping_p-ch-h.json"),
        help="Path to section_mapping_p-ch-h.json for real chapter structure.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    args = parser.parse_args()

    section_mapping_path = Path(args.section_mapping)
    if section_mapping_path.exists():
        load_real_structure(section_mapping_path)
        print(f"Loaded real chapter structure: {len(_REAL_STRUCT)} sections")
    else:
        print(f"Section mapping not found at {section_mapping_path}, using legacy CH numbering")

    card_files = collect_card_files(args.cards, args.cards_dir)
    if not card_files:
        raise SystemExit("No cards.raw.json inputs found.")
    allowed = allowed_cards_from_manifest(Path(args.p7d_manifest)) if args.p7d_manifest else None
    cards = load_cards(card_files, allowed)

    if args.dual_layer:
        packages_dir = Path(args.packages_dir) if args.packages_dir else None
        kg_graph_path = Path(args.kg_graph) if args.kg_graph else None
        candidates = generate_candidates_dual_layer(cards, packages_dir, kg_graph_path)
    else:
        candidates = generate_candidates(cards)

    output_path = Path(args.output_dir) / "p7e_bridge_candidates.jsonl"
    report_path = Path(args.report_dir) / "p7e_bridge_candidate_report.md"
    write_jsonl(output_path, candidates)
    write_report(report_path, candidates, len(cards))
    review_counts = Counter(row["review_result"] for row in candidates)
    conf_counts = Counter(row.get("confidence", "?") for row in candidates)
    print(
        f"Generated {len(candidates)} candidates from {len(cards)} cards. "
        f"pass={review_counts.get('pass', 0)}, fail={review_counts.get('fail', 0)}. "
        f"confidence={dict(conf_counts)}. "
        f"Report: {report_path}"
    )


if __name__ == "__main__":
    main()
