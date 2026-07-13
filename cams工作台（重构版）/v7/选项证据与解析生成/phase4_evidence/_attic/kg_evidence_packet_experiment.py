# -*- coding: utf-8 -*-
"""Experimental KG evidence packet builder.

The production Phase 4 pipeline currently uses KG mostly as candidate expansion.
This script is intentionally isolated under tests/: it reads an existing
blind_adjudication result and the KG retrieval graph, then builds option-level
evidence packets with object-alignment diagnostics.

Example:
    python tests/kg_evidence_packet_experiment.py --question-id v7_q_000009 --question-id v7_q_000012
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PHASE4 = HERE.parent
WORKSPACE = PHASE4.parent
V7_ROOT = WORKSPACE.parent

DEFAULT_RUN_DIR = PHASE4 / "output" / "kg_p5_norm_first50_c30"
KG_GRAPH_PATH = V7_ROOT / "知识图谱提取" / "phases" / "phase06_kg_views" / "outputs" / "kg_retrieval_graph.json"
OUTPUT_DIR = HERE / "output" / "kg_packets"


RELATION_WEIGHT = {
    "defines": 1.12,
    "states_rule": 1.18,
    "prescribes_measure": 1.14,
    "describes_process": 1.02,
    "indicates_risk": 1.02,
    "explains": 0.98,
    "illustrates": 0.90,
    "classifies": 0.82,
    "grounds": 0.78,
    "states_consequence": 0.76,
    "provides_context": 0.48,
    "parallels": 0.42,
    "summarizes": 0.42,
    "contrasts": 0.36,
}

STOPWORDS_EN = {
    "the",
    "and",
    "or",
    "of",
    "to",
    "in",
    "for",
    "a",
    "an",
    "is",
    "are",
    "be",
    "with",
    "by",
    "on",
    "as",
    "it",
    "this",
    "that",
    "which",
    "would",
    "could",
    "should",
    "may",
    "might",
    "can",
    "will",
    "your",
    "their",
    "its",
    "from",
    "into",
    "then",
    "than",
}

TAG_PROFILES: dict[str, dict[str, Any]] = {
    "sanctions_screening": {
        "label": "sanctions screening / 制裁筛查",
        "terms": ["sanctions screening", "sanction screening", "screening system", "screen customers", "制裁筛查", "筛查系统", "筛选系统", "筛查", "筛选"],
        "object": "screening",
    },
    "fuzzy_logic": {
        "label": "fuzzy logic / 模糊逻辑",
        "terms": ["fuzzy logic", "fuzziness", "name variations", "misspellings", "transliterations", "模糊逻辑", "模糊", "名称变体"],
        "object": "screening",
    },
    "transaction_monitoring": {
        "label": "transaction monitoring / 交易监控",
        "terms": ["transaction monitoring", "tm system", "monitoring system", "post-transaction", "transactions monitoring", "交易监控", "交易后监控", "监控系统"],
        "object": "transaction_monitoring",
    },
    "threshold_parameters": {
        "label": "thresholds/parameters / 参数阈值",
        "terms": ["threshold", "thresholds", "parameter", "parameters", "tune", "tuning", "调优", "参数", "阈值", "阀值"],
        "object": "system_settings",
    },
    "ewra": {
        "label": "EWRA / 全企业风险评估",
        "terms": ["enterprise-wide risk assessment", "ewra", "全企业", "全机构", "企业范围", "企业全面风险评估"],
        "object": "risk_assessment",
    },
    "residual_risk": {
        "label": "residual risk / 剩余风险",
        "terms": ["residual risk", "剩余风险", "残余风险"],
        "object": "risk_assessment",
    },
    "inherent_risk": {
        "label": "inherent risk / 固有风险",
        "terms": ["inherent risk", "固有风险"],
        "object": "risk_assessment",
    },
    "control_effectiveness": {
        "label": "control effectiveness / 控制有效性",
        "terms": ["control effectiveness", "effectiveness of controls", "controls are judged to be effective", "effective controls", "控制有效性", "控制措施的有效性", "有效性", "有效"],
        "object": "risk_assessment",
    },
    "implemented_controls": {
        "label": "implemented controls / 已实施控制",
        "terms": ["implemented", "in place", "已实施", "配备", "现有控制", "控制措施"],
        "object": "risk_assessment",
    },
    "cdd_edd": {
        "label": "CDD/EDD / 客户尽调",
        "terms": ["cdd", "edd", "customer due diligence", "enhanced due diligence", "客户尽职调查", "强化尽职调查", "尽职调查"],
        "object": "customer_due_diligence",
    },
    "private_banking": {
        "label": "private banking / 私人银行",
        "terms": ["private banking", "high net worth", "financial structure", "私人银行", "资产净值", "财务结构"],
        "object": "private_banking",
    },
    "action_plan": {
        "label": "action plan / 后续控制计划",
        "terms": ["action plan", "mitigating the highest risks", "additional controls", "further control", "acceptable level", "risk appetite", "行动计划", "进一步", "可接受", "风险偏好"],
        "object": "risk_assessment",
    },
    "eliminate_all_risk": {
        "label": "eliminate all risk / 完全消除风险",
        "terms": ["eliminate", "all potential risks", "completely", "完全消除", "所有潜在风险", "全部风险"],
        "object": "risk_assessment",
    },
}

GENERIC_TAGS = {"ewra", "implemented_controls"}
OBJECT_CONFLICTS = {
    frozenset({"screening", "transaction_monitoring"}),
}


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def tokenize(text: str) -> set[str]:
    text = (text or "").lower()
    tokens = {
        t
        for t in re.findall(r"[a-z0-9][a-z0-9_\-/.]*", text)
        if len(t) > 2 and t not in STOPWORDS_EN
    }
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(run) <= 2:
            tokens.add(run)
        else:
            tokens.update(run[i : i + 2] for i in range(len(run) - 1))
            tokens.update(run[i : i + 3] for i in range(len(run) - 2))
    return tokens


def overlap_score(query: str, text: str) -> float:
    q = tokenize(query)
    t = tokenize(text)
    if not q or not t:
        return 0.0
    precisionish = len(q & t) / len(q)
    recallish = len(q & t) / max(1, min(len(t), 80))
    return (0.75 * precisionish) + (0.25 * recallish)


def contains_term(text: str, term: str) -> bool:
    lowered = (text or "").lower()
    term_l = term.lower()
    if re.fullmatch(r"[a-z0-9][a-z0-9_\-/. ]+", term_l):
        return term_l in lowered
    return term in text


def infer_tags(text: str) -> set[str]:
    tags: set[str] = set()
    for tag, profile in TAG_PROFILES.items():
        if any(contains_term(text, term) for term in profile["terms"]):
            tags.add(tag)
    return tags


def tag_labels(tags: set[str]) -> list[str]:
    return [TAG_PROFILES[t]["label"] for t in sorted(tags) if t in TAG_PROFILES]


def tag_objects(tags: set[str]) -> set[str]:
    return {TAG_PROFILES[t]["object"] for t in tags if t in TAG_PROFILES}


def object_conflict(a: set[str], b: set[str]) -> bool:
    for left in tag_objects(a):
        for right in tag_objects(b):
            if frozenset({left, right}) in OBJECT_CONFLICTS:
                return True
    return False


def tag_alignment(option_tags: set[str], stem_tags: set[str], evidence_tags: set[str]) -> float:
    if not option_tags:
        return 0.0
    direct = len(option_tags & evidence_tags) / len(option_tags)
    specific_option_tags = option_tags - GENERIC_TAGS
    if specific_option_tags:
        specific = len(specific_option_tags & evidence_tags) / len(specific_option_tags)
    else:
        specific = direct
    stem_overlap = len((stem_tags - GENERIC_TAGS) & evidence_tags) / max(1, len(stem_tags - GENERIC_TAGS))
    return (0.55 * direct) + (0.30 * specific) + (0.15 * stem_overlap)


def unit_text(unit: dict[str, Any]) -> str:
    return "\n".join(str(unit.get(k, "")) for k in ("knowledge_zh", "knowledge_en", "en_quote", "type"))


def cp_text(cp: dict[str, Any]) -> str:
    return "\n".join(str(cp.get(k, "")) for k in ("title_en", "title_zh", "reason"))


def build_kg_indexes(kg: dict[str, Any]) -> dict[str, Any]:
    cp_by_id = {cp["core_point_id"]: cp for cp in kg.get("core_points", [])}
    unit_by_id = {unit["unit_id"]: unit for unit in kg.get("units", [])}
    unit_to_cp_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cp_to_unit_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cp_rel_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for edge in kg.get("edges", []):
        scope = edge.get("edge_scope")
        source_id = edge.get("source_id", "")
        target_id = edge.get("target_id", "")
        if scope == "core_point_unit":
            cp_to_unit_edges[source_id].append(edge)
            unit_to_cp_edges[target_id].append(edge)
        elif scope in {"same_section_core_point", "same_chapter_core_point", "cross_chapter_core_point"}:
            cp_rel_edges[source_id].append(edge)
            cp_rel_edges[target_id].append(edge)

    return {
        "cp_by_id": cp_by_id,
        "unit_by_id": unit_by_id,
        "unit_to_cp_edges": unit_to_cp_edges,
        "cp_to_unit_edges": cp_to_unit_edges,
        "cp_rel_edges": cp_rel_edges,
    }


def candidate_rows(result: dict[str, Any], max_seed_units: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for i, row in enumerate(result.get("candidate_pool", [])):
        uid = row.get("unit_id")
        if not uid or uid in seen:
            continue
        if i < max_seed_units:
            rows.append(row)
            seen.add(uid)
    return rows


def row_unit(row: dict[str, Any], unit_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    uid = row.get("unit_id", "")
    kg_unit = dict(unit_by_id.get(uid, {}))
    for key in ("knowledge_zh", "knowledge_en", "en_quote", "type"):
        if row.get(key) and not kg_unit.get(key):
            kg_unit[key] = row[key]
    kg_unit.setdefault("unit_id", uid)
    return kg_unit


def candidate_score(row: dict[str, Any]) -> float:
    try:
        value = float(row.get("score", 0.0))
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, value))


def score_evidence(
    *,
    stem: str,
    option_text: str,
    stem_tags: set[str],
    option_tags: set[str],
    evidence_text: str,
    evidence_tags: set[str],
    base: float,
    relation_type: str = "",
    depth: int = 0,
) -> tuple[float, list[str]]:
    query = f"{stem}\n{option_text}"
    option_overlap = overlap_score(option_text, evidence_text)
    question_overlap = overlap_score(query, evidence_text)
    alignment = tag_alignment(option_tags, stem_tags, evidence_tags)
    relation = RELATION_WEIGHT.get(relation_type, 0.70)
    score = (0.26 * base) + (0.22 * option_overlap) + (0.22 * question_overlap) + (0.30 * alignment)
    score *= relation
    if depth:
        score *= math.pow(0.72, depth)

    diagnostics: list[str] = []
    if option_tags & evidence_tags:
        diagnostics.append("option_tag_match")
    if (stem_tags - GENERIC_TAGS) & evidence_tags:
        diagnostics.append("stem_object_match")
    if object_conflict(option_tags, evidence_tags) or object_conflict(option_tags, stem_tags):
        score *= 0.35
        diagnostics.append("object_mismatch")
    if "eliminate_all_risk" in option_tags:
        score *= 0.35
        diagnostics.append("overclaim_all_risk")
    return round(score, 6), diagnostics


def add_or_update(store: dict[str, dict[str, Any]], item: dict[str, Any]) -> None:
    key = item["unit_id"]
    old = store.get(key)
    if old is None or item["score"] > old["score"]:
        store[key] = item


def build_packet_for_option(
    label: str,
    option_text: str,
    result: dict[str, Any],
    kg_index: dict[str, Any],
    seed_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    stem = result.get("stem", "")
    stem_tags = infer_tags(stem)
    option_tags = infer_tags(option_text)
    unit_by_id = kg_index["unit_by_id"]
    cp_by_id = kg_index["cp_by_id"]
    unit_to_cp_edges = kg_index["unit_to_cp_edges"]
    cp_to_unit_edges = kg_index["cp_to_unit_edges"]
    cp_rel_edges = kg_index["cp_rel_edges"]

    unit_scores: dict[str, dict[str, Any]] = {}
    cp_scores: dict[str, dict[str, Any]] = {}

    for row in seed_rows:
        uid = row.get("unit_id", "")
        unit = row_unit(row, unit_by_id)
        text = unit_text(unit)
        tags = infer_tags(text)
        base = candidate_score(row)
        score, diagnostics = score_evidence(
            stem=stem,
            option_text=option_text,
            stem_tags=stem_tags,
            option_tags=option_tags,
            evidence_text=text,
            evidence_tags=tags,
            base=base,
            depth=0,
        )
        if score > 0.025 or tags & (option_tags | stem_tags):
            add_or_update(
                unit_scores,
                {
                    "unit_id": uid,
                    "score": score,
                    "source": "direct_candidate",
                    "relation_type": "candidate",
                    "diagnostics": diagnostics,
                    "tags": tag_labels(tags),
                    "knowledge_zh": unit.get("knowledge_zh", ""),
                    "en_quote": unit.get("en_quote", ""),
                },
            )

        for edge in unit_to_cp_edges.get(uid, []):
            cp_id = edge.get("source_id", "")
            cp = cp_by_id.get(cp_id, {})
            cp_tags = infer_tags(cp_text(cp)) | tags
            cp_score, cp_diag = score_evidence(
                stem=stem,
                option_text=option_text,
                stem_tags=stem_tags,
                option_tags=option_tags,
                evidence_text=cp_text(cp),
                evidence_tags=cp_tags,
                base=base,
                relation_type=edge.get("relation_type", ""),
                depth=0,
            )
            old = cp_scores.get(cp_id)
            if old is None or cp_score > old["score"]:
                cp_scores[cp_id] = {
                    "core_point_id": cp_id,
                    "title_en": cp.get("title_en", ""),
                    "title_zh": cp.get("title_zh", ""),
                    "score": cp_score,
                    "via_unit_id": uid,
                    "relation_type": edge.get("relation_type", ""),
                    "relation_reason": edge.get("reason", ""),
                    "diagnostics": cp_diag,
                    "tags": tag_labels(cp_tags),
                }

    for cp_id, cp_row in sorted(cp_scores.items(), key=lambda x: x[1]["score"], reverse=True)[:10]:
        for edge in cp_to_unit_edges.get(cp_id, []):
            uid = edge.get("target_id", "")
            unit = unit_by_id.get(uid)
            if not unit:
                continue
            tags = infer_tags(unit_text(unit)) | infer_tags(cp_row.get("title_en", "") + " " + cp_row.get("title_zh", ""))
            score, diagnostics = score_evidence(
                stem=stem,
                option_text=option_text,
                stem_tags=stem_tags,
                option_tags=option_tags,
                evidence_text=unit_text(unit),
                evidence_tags=tags,
                base=cp_row["score"],
                relation_type=edge.get("relation_type", ""),
                depth=1,
            )
            if score > 0.025 or tags & option_tags:
                add_or_update(
                    unit_scores,
                    {
                        "unit_id": uid,
                        "score": score,
                        "source": "kg_same_core_point",
                        "relation_type": edge.get("relation_type", ""),
                        "core_point_id": cp_id,
                        "core_point_title_en": cp_row.get("title_en", ""),
                        "core_point_title_zh": cp_row.get("title_zh", ""),
                        "relation_reason": edge.get("reason", ""),
                        "diagnostics": diagnostics,
                        "tags": tag_labels(tags),
                        "knowledge_zh": unit.get("knowledge_zh", ""),
                        "en_quote": unit.get("en_quote", ""),
                    },
                )

        for rel_edge in cp_rel_edges.get(cp_id, [])[:12]:
            other_id = rel_edge.get("target_id") if rel_edge.get("source_id") == cp_id else rel_edge.get("source_id")
            other_cp = cp_by_id.get(other_id or "")
            if not other_cp:
                continue
            rel_tags = infer_tags(cp_text(other_cp))
            rel_score, rel_diag = score_evidence(
                stem=stem,
                option_text=option_text,
                stem_tags=stem_tags,
                option_tags=option_tags,
                evidence_text=cp_text(other_cp),
                evidence_tags=rel_tags,
                base=cp_row["score"],
                relation_type=rel_edge.get("relation_type", ""),
                depth=2,
            )
            old = cp_scores.get(other_id or "")
            if rel_score > 0.025 and (old is None or rel_score > old["score"]):
                cp_scores[other_id or ""] = {
                    "core_point_id": other_id,
                    "title_en": other_cp.get("title_en", ""),
                    "title_zh": other_cp.get("title_zh", ""),
                    "score": rel_score,
                    "via_core_point_id": cp_id,
                    "relation_type": rel_edge.get("relation_type", ""),
                    "relation_reason": rel_edge.get("reason", ""),
                    "diagnostics": rel_diag,
                    "tags": tag_labels(rel_tags),
                }

    support_units = sorted(unit_scores.values(), key=lambda x: x["score"], reverse=True)[:10]
    matched_core_points = sorted(cp_scores.values(), key=lambda x: x["score"], reverse=True)[:10]
    risk_notes = diagnose_packet(stem, option_text, stem_tags, option_tags, support_units)

    return {
        "option": label,
        "option_text": option_text,
        "stem_tags": tag_labels(stem_tags),
        "option_tags": tag_labels(option_tags),
        "risk_notes": risk_notes,
        "matched_core_points": matched_core_points,
        "support_units": support_units,
    }


def diagnose_packet(
    stem: str,
    option_text: str,
    stem_tags: set[str],
    option_tags: set[str],
    support_units: list[dict[str, Any]],
) -> list[str]:
    notes: list[str] = []
    support_text = "\n".join((u.get("knowledge_zh", "") or "") + "\n" + (u.get("en_quote", "") or "") for u in support_units)
    support_tags = infer_tags(support_text)
    if object_conflict(option_tags, stem_tags) or object_conflict(option_tags, support_tags):
        notes.append("object_mismatch: option object conflicts with question/support object")
    if {"sanctions_screening", "fuzzy_logic"} & option_tags and "sanctions_screening" in stem_tags:
        if {"sanctions_screening", "fuzzy_logic"} & support_tags:
            notes.append("object_aligned: screening-system evidence directly matches the question object")
    if "residual_risk" in (stem_tags | option_tags):
        option_asserts_effectiveness = "control_effectiveness" in option_tags and "action_plan" not in option_tags
        if option_asserts_effectiveness and "controls are judged to be effective" in support_text.lower() and not contains_term(stem, "judged to be effective"):
            notes.append("conditional_gap: support lowers residual risk only if controls are judged effective; stem says controls are implemented")
        if "action_plan" in option_tags and "action_plan" in support_tags:
            notes.append("action_plan_aligned: evidence mentions acceptable residual risk/action plan")
        if "eliminate_all_risk" in option_tags:
            notes.append("overclaim: residual risk is mitigated, not completely eliminated")
    if not support_units:
        notes.append("no_support_units")
    if not notes:
        notes.append("no_major_diagnostic_flag")
    return notes


def build_packets(result: dict[str, Any], kg_index: dict[str, Any], max_seed_units: int) -> dict[str, Any]:
    seed_rows = candidate_rows(result, max_seed_units)
    packets = {}
    for label, text in (result.get("options", {}) or {}).items():
        packets[label] = build_packet_for_option(label, text, result, kg_index, seed_rows)
    return {
        "question_id": result.get("question_id"),
        "stem": result.get("stem"),
        "predicted_answer": result.get("predicted_answer", []),
        "seed_unit_count": len(seed_rows),
        "option_packets": packets,
    }


def render_markdown(packet_doc: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {packet_doc['question_id']} KG Evidence Packet Experiment\n\n")
    lines.append(f"题干：{packet_doc.get('stem', '')}\n\n")
    lines.append(f"裁判答案：{', '.join(packet_doc.get('predicted_answer', []))}\n\n")
    lines.append(f"种子单元数：{packet_doc.get('seed_unit_count')}\n\n")
    for label, packet in packet_doc.get("option_packets", {}).items():
        lines.append(f"## 选项 {label}. {packet.get('option_text', '')}\n\n")
        lines.append("选项标签：" + ("；".join(packet.get("option_tags", [])) or "无") + "\n\n")
        lines.append("诊断：" + "；".join(packet.get("risk_notes", [])) + "\n\n")
        lines.append("### Matched Core Points\n\n")
        for cp in packet.get("matched_core_points", [])[:5]:
            lines.append(
                f"- {cp.get('core_point_id')} | {cp.get('relation_type', '')} | score={cp.get('score')}\n"
                f"  - {cp.get('title_en', '')} / {cp.get('title_zh', '')}\n"
                f"  - tags: {'; '.join(cp.get('tags', [])) or 'none'}\n"
                f"  - via: {cp.get('via_unit_id', cp.get('via_core_point_id', ''))}; {cp.get('relation_reason', '')}\n"
            )
        lines.append("\n### Support Units\n\n")
        for unit in packet.get("support_units", [])[:6]:
            lines.append(
                f"- {unit.get('unit_id')} | {unit.get('source')} | {unit.get('relation_type', '')} | score={unit.get('score')}\n"
                f"  - diagnostics: {'; '.join(unit.get('diagnostics', [])) or 'none'}\n"
                f"  - tags: {'; '.join(unit.get('tags', [])) or 'none'}\n"
                f"  - 中文：{unit.get('knowledge_zh', '')}\n"
                f"  - English: {unit.get('en_quote', '')}\n"
            )
        lines.append("\n")
    return "".join(lines)


def resolve_question_path(run_dir: Path, qid: str) -> Path:
    path = run_dir / "questions" / f"q_{qid}.json"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build experimental option-level KG evidence packets.")
    parser.add_argument("--run-dir", default=str(DEFAULT_RUN_DIR), help="blind_adjudication output directory")
    parser.add_argument("--kg-path", default=str(KG_GRAPH_PATH), help="kg_retrieval_graph.json path")
    parser.add_argument("--question-id", action="append", default=[], help="question id, e.g. v7_q_000009")
    parser.add_argument("--max-seed-units", type=int, default=60, help="candidate_pool units used as KG seeds")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="experiment output directory")
    args = parser.parse_args()

    qids = args.question_id or ["v7_q_000009", "v7_q_000012"]
    run_dir = Path(args.run_dir)
    output_dir = Path(args.output_dir)
    kg = load_json(Path(args.kg_path))
    kg_index = build_kg_indexes(kg)

    index_rows: list[dict[str, str]] = []
    for qid in qids:
        result = load_json(resolve_question_path(run_dir, qid))
        packet_doc = build_packets(result, kg_index, max_seed_units=args.max_seed_units)
        json_path = output_dir / f"{qid}.kg_packets.json"
        md_path = output_dir / f"{qid}.kg_packets.md"
        write_json(json_path, packet_doc)
        write_text(md_path, render_markdown(packet_doc))
        index_rows.append({"question_id": qid, "json": str(json_path), "markdown": str(md_path)})
        print(f"[ok] {qid} -> {json_path}")

    write_json(output_dir / "index.json", index_rows)


if __name__ == "__main__":
    main()
