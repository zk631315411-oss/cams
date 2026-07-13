# -*- coding: utf-8 -*-
"""Experimental multi-head retrieval for Phase 4.

This script is isolated under tests/. It does not call the LLM and does not
change production outputs. The goal is to compare the current single query
shape (stem + all options) with separate retrieval heads:

  - stem
  - stem + option A/B/C/D
  - optional stem + all options fallback

Each returned unit keeps the retrieval head(s) that found it, so later KG or
option evidence packet experiments can tell whether evidence came from the
stem, a specific option, or the all-options fallback.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PHASE4 = HERE.parent
SCRIPTS = PHASE4 / "scripts"
sys.path.insert(0, str(SCRIPTS))

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import blind_adjudication as ba  # noqa: E402


OUTPUT_DIR = HERE / "output" / "multi_head_retrieval"

HEAD_WEIGHTS = {
    "stem": 1.08,
    "option": 1.00,
    "all_options": 0.62,
}

RELATION_WEIGHTS = {
    "states_rule": 1.00,
    "prescribes_measure": 0.98,
    "defines": 0.92,
    "explains": 0.88,
    "describes_process": 0.82,
    "illustrates": 0.72,
    "indicates_risk": 0.70,
    "states_consequence": 0.68,
    "provides_context": 0.48,
    "summarizes": 0.45,
    "parallels": 0.42,
    "contrasts": 0.35,
}

EDGE_SCOPE_WEIGHTS = {
    "same_section_core_point": 0.88,
    "same_chapter_core_point": 0.72,
    "cross_chapter_core_point": 0.60,
}

RELATION_LABELS = {
    "contains": "包含",
    "defines": "定义",
    "states_rule": "规则依据",
    "prescribes_measure": "措施要求",
    "explains": "解释说明",
    "describes_process": "流程说明",
    "illustrates": "例证",
    "indicates_risk": "指出风险",
    "states_consequence": "说明后果",
    "grounds": "提供根据",
    "prepares": "铺垫/引出",
    "provides_context": "背景",
    "summarizes": "总结",
    "parallels": "并列相关",
    "contrasts": "对比/区分",
    "same_core_point": "同知识点包含",
}

EDGE_SCOPE_LABELS = {
    "same_core_point": "同一核心知识点",
    "same_section_core_point": "同小节知识点",
    "same_chapter_core_point": "同章节知识点",
    "cross_chapter_core_point": "跨章节知识点",
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def build_retrieval_heads(question: dict[str, Any], include_all_options: bool) -> list[dict[str, Any]]:
    stem = question.get("stem", "")
    stem_en = question.get("stem_en", "")
    options = question.get("options", {}) or {}
    options_en = question.get("options_en", {}) or {}

    heads: list[dict[str, Any]] = [
        {
            "head_id": "stem",
            "head_kind": "stem",
            "option": None,
            "query_zh": stem.strip(),
            "query_en": stem_en.strip() or None,
        }
    ]

    for label, option_text in options.items():
        option_en = options_en.get(label, "")
        heads.append(
            {
                "head_id": f"option_{label}",
                "head_kind": "option",
                "option": label,
                "query_zh": f"{stem} {option_text}".strip(),
                "query_en": f"{stem_en} {option_en}".strip() if stem_en else None,
            }
        )

    if include_all_options:
        opt_text = " ".join(str(v) for v in options.values())
        opt_en_text = " ".join(str(v) for v in options_en.values())
        heads.append(
            {
                "head_id": "all_options",
                "head_kind": "all_options",
                "option": None,
                "query_zh": f"{stem} {opt_text}".strip(),
                "query_en": f"{stem_en} {opt_en_text}".strip() if stem_en else None,
            }
        )
    return heads


def search_head(
    head: dict[str, Any],
    bge_vecs: Any,
    card_ids: list[str],
    unit_lookup: dict[str, dict[str, Any]],
    bm25_zh_index: ba.BM25,
    bm25_en_index: ba.BM25,
    p5_index: dict[str, Any] | None,
    top_k: int,
    p5_top_k: int,
) -> list[dict[str, Any]]:
    query_zh = head.get("query_zh", "") or ""
    query_en = head.get("query_en")
    head_id = head["head_id"]
    head_kind = head["head_kind"]
    head_weight = HEAD_WEIGHTS.get(head_kind, 1.0)

    rows: list[dict[str, Any]] = []

    query_bge = query_zh if not query_en else f"{query_zh} {query_en}"
    bge_rows = ba._normalize_route_scores(
        ba.bge_search(query_bge, bge_vecs, card_ids, unit_lookup, top_k=top_k)
    )
    for row in bge_rows:
        row = dict(row)
        row["route"] = "bge"
        rows.append(row)

    bm25_zh_rows = ba._normalize_route_scores(
        ba.bm25_search(query_zh, bm25_zh_index, card_ids, unit_lookup, top_k=top_k)
    )
    for row in bm25_zh_rows:
        row = dict(row)
        row["route"] = "bm25_zh"
        rows.append(row)

    if query_en:
        bm25_en_rows = ba._normalize_route_scores(
            ba.bm25_search(query_en, bm25_en_index, card_ids, unit_lookup, top_k=top_k)
        )
        for row in bm25_en_rows:
            row = dict(row)
            row["route"] = "bm25_en"
            rows.append(row)

    p5_rows = ba.p5_alias_search(query_zh, query_en, p5_index, unit_lookup, top_k=p5_top_k)
    for row in p5_rows:
        rows.append(dict(row))

    out: list[dict[str, Any]] = []
    for row in rows:
        weighted_score = round(float(row.get("score") or 0.0) * head_weight, 6)
        out.append(
            {
                "unit_id": row["unit_id"],
                "knowledge_zh": row.get("knowledge_zh", ""),
                "knowledge_en": row.get("knowledge_en", ""),
                "en_quote": row.get("en_quote", ""),
                "heading_context": row.get("heading_context", []),
                "type": row.get("type", ""),
                "head_id": head_id,
                "head_kind": head_kind,
                "option": head.get("option"),
                "route": row.get("route", ""),
                "score": row.get("score", 0.0),
                "weighted_score": weighted_score,
                "raw_score": row.get("raw_score", row.get("score", 0.0)),
                "p5": row.get("p5"),
            }
        )
    out.sort(key=lambda x: x["weighted_score"], reverse=True)
    return out


def merge_head_results(head_results: dict[str, list[dict[str, Any]]], merge_top_k: int) -> list[dict[str, Any]]:
    by_uid: dict[str, dict[str, Any]] = {}
    for head_id, rows in head_results.items():
        for row in rows:
            uid = row["unit_id"]
            hit = {
                "head_id": row["head_id"],
                "head_kind": row["head_kind"],
                "option": row.get("option"),
                "route": row.get("route"),
                "score": row.get("score"),
                "weighted_score": row.get("weighted_score"),
                "raw_score": row.get("raw_score"),
            }
            if row.get("p5"):
                hit["p5"] = row["p5"]

            if uid not in by_uid:
                by_uid[uid] = {
                    "unit_id": uid,
                    "knowledge_zh": row.get("knowledge_zh", ""),
                    "knowledge_en": row.get("knowledge_en", ""),
                    "en_quote": row.get("en_quote", ""),
                    "heading_context": row.get("heading_context", []),
                    "type": row.get("type", ""),
                    "score": row.get("weighted_score", 0.0),
                    "best_head_id": head_id,
                    "best_route": row.get("route", ""),
                    "head_hits": [hit],
                }
                continue

            by_uid[uid]["head_hits"].append(hit)
            if row.get("weighted_score", 0.0) > by_uid[uid]["score"]:
                by_uid[uid]["score"] = row.get("weighted_score", 0.0)
                by_uid[uid]["best_head_id"] = head_id
                by_uid[uid]["best_route"] = row.get("route", "")

    merged = list(by_uid.values())
    for row in merged:
        row["head_hits"].sort(key=lambda x: x.get("weighted_score", 0.0), reverse=True)
        row["hit_count"] = len(row["head_hits"])
        row["hit_heads"] = sorted({h["head_id"] for h in row["head_hits"]})
        row["hit_options"] = sorted({h["option"] for h in row["head_hits"] if h.get("option")})
    merged.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return merged[:merge_top_k]


def joined_unit_text(unit: dict[str, Any]) -> str:
    return " ".join(
        str(unit.get(k, ""))
        for k in ("knowledge_zh", "knowledge_en", "en_quote")
    )


def text_relevance(query: str, text: str) -> float:
    query_tokens = set(ba.tokenize(query))
    text_tokens = set(ba.tokenize(text))
    if not query_tokens or not text_tokens:
        return 0.0
    return round(len(query_tokens & text_tokens) / max(len(query_tokens), 1), 6)


def unit_payload(uid: str, unit_lookup: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    unit = unit_lookup.get(uid)
    if not unit:
        return None
    return {
        "unit_id": uid,
        "knowledge_zh": unit.get("knowledge_zh", ""),
        "knowledge_en": unit.get("knowledge_en", ""),
        "en_quote": unit.get("en_quote", ""),
        "heading_context": unit.get("heading_context", []),
        "type": unit.get("type", ""),
    }


def cp_payload(cp_id: str, kg_index: dict[str, Any]) -> dict[str, Any]:
    cp = kg_index["cp_meta"].get(cp_id, {})
    return {
        "core_point_id": cp_id,
        "title_zh": cp.get("title_zh", ""),
        "title_en": cp.get("title_en", ""),
        "section_id": cp.get("section_id", ""),
        "reason": cp.get("reason", ""),
    }


def relation_strength(edge: dict[str, Any]) -> float:
    rel = edge.get("relation_type", "")
    scope = edge.get("edge_scope", "")
    return RELATION_WEIGHTS.get(rel, 0.50) * EDGE_SCOPE_WEIGHTS.get(scope, 0.55)


def rank_units_for_query(
    unit_ids: list[str],
    query: str,
    unit_lookup: dict[str, dict[str, Any]],
    limit: int,
    exclude: set[str] | None = None,
) -> list[dict[str, Any]]:
    exclude = exclude or set()
    rows: list[dict[str, Any]] = []
    for uid in unit_ids:
        if uid in exclude:
            continue
        payload = unit_payload(uid, unit_lookup)
        if not payload:
            continue
        relevance = text_relevance(query, joined_unit_text(payload))
        payload["text_relevance"] = relevance
        rows.append(payload)
    rows.sort(key=lambda x: (x.get("text_relevance", 0.0), x.get("unit_id", "")), reverse=True)
    return rows[:limit]


def build_kg_packets_for_head(
    head: dict[str, Any],
    head_rows: list[dict[str, Any]],
    kg_index: dict[str, Any] | None,
    unit_lookup: dict[str, dict[str, Any]],
    seed_limit: int,
    source_cp_limit: int,
    same_cp_unit_limit: int,
    related_cp_limit: int,
    related_cp_unit_limit: int,
) -> list[dict[str, Any]]:
    if not kg_index:
        return []

    query = " ".join([head.get("query_zh", "") or "", head.get("query_en", "") or ""]).strip()
    unit_to_cps = kg_index["unit_to_cps"]
    cp_to_units = kg_index["cp_to_units"]
    relation_edges_by_cp = kg_index["relation_edges_by_cp"]
    cp_meta = kg_index["cp_meta"]

    seed_rows = [r for r in head_rows if r.get("route") in {"bge", "bm25_zh", "bm25_en", "p5_alias"}]
    packets: list[dict[str, Any]] = []
    for seed in seed_rows[:seed_limit]:
        seed_uid = seed["unit_id"]
        seed_unit = unit_payload(seed_uid, unit_lookup)
        if not seed_unit:
            continue
        seed_packet = {
            "head_id": head["head_id"],
            "head_kind": head["head_kind"],
            "option": head.get("option"),
            "seed_unit_id": seed_uid,
            "seed_route": seed.get("route", ""),
            "seed_score": seed.get("weighted_score", seed.get("score", 0.0)),
            "seed_unit": seed_unit,
            "source_core_points": [],
        }

        source_cp_ids = unit_to_cps.get(seed_uid, [])[:source_cp_limit]
        for cp_id in source_cp_ids:
            cp = cp_payload(cp_id, kg_index)
            same_units = rank_units_for_query(
                cp_to_units.get(cp_id, []),
                query,
                unit_lookup,
                limit=same_cp_unit_limit,
                exclude={seed_uid},
            )
            for unit in same_units:
                unit["evidence_role"] = "same_cp_context"
                unit["source_core_point_id"] = cp_id

            related_edges = list(relation_edges_by_cp.get(cp_id, []))
            related_edges.sort(
                key=lambda edge: (
                    relation_strength(edge),
                    text_relevance(
                        query,
                        " ".join(
                            str(cp_meta.get(edge.get("target_id") if edge.get("source_id") == cp_id else edge.get("source_id"), {}).get(k, ""))
                            for k in ("title_zh", "title_en", "reason")
                        ),
                    ),
                ),
                reverse=True,
            )

            related_packets: list[dict[str, Any]] = []
            seen_related: set[str] = set()
            for edge in related_edges:
                other_cp_id = edge.get("target_id") if edge.get("source_id") == cp_id else edge.get("source_id")
                if not other_cp_id or other_cp_id in seen_related:
                    continue
                seen_related.add(other_cp_id)
                other_cp = cp_payload(other_cp_id, kg_index)
                relation = {
                    "edge_id": edge.get("edge_id", ""),
                    "edge_scope": edge.get("edge_scope", ""),
                    "relation_type": edge.get("relation_type", ""),
                    "reason": edge.get("reason", ""),
                    "relation_strength": round(relation_strength(edge), 6),
                }
                related_units = rank_units_for_query(
                    cp_to_units.get(other_cp_id, []),
                    query,
                    unit_lookup,
                    limit=related_cp_unit_limit,
                    exclude={seed_uid},
                )
                for unit in related_units:
                    unit["evidence_role"] = "related_cp_context"
                    unit["source_core_point_id"] = cp_id
                    unit["target_core_point_id"] = other_cp_id
                    unit["relation_type"] = edge.get("relation_type", "")
                    unit["edge_scope"] = edge.get("edge_scope", "")

                related_packets.append(
                    {
                        **other_cp,
                        "relation": relation,
                        "related_cp_units": related_units,
                    }
                )
                if len(related_packets) >= related_cp_limit:
                    break

            seed_packet["source_core_points"].append(
                {
                    **cp,
                    "same_cp_units": same_units,
                    "related_core_points": related_packets,
                }
            )
        packets.append(seed_packet)
    return packets


def flatten_kg_packets(
    packets_by_head: dict[str, list[dict[str, Any]]],
    existing_unit_ids: set[str],
    kg_top_k: int,
) -> list[dict[str, Any]]:
    by_uid: dict[str, dict[str, Any]] = {}
    for head_id, packets in packets_by_head.items():
        for packet in packets:
            for cp in packet.get("source_core_points", []):
                unit_groups = [("same_cp_context", cp.get("same_cp_units", []))]
                for related_cp in cp.get("related_core_points", []):
                    unit_groups.append(("related_cp_context", related_cp.get("related_cp_units", [])))
                for role, units in unit_groups:
                    for unit in units:
                        uid = unit["unit_id"]
                        if uid in existing_unit_ids or uid == packet.get("seed_unit_id"):
                            continue
                        score = round(
                            float(packet.get("seed_score") or 0.0) * 0.40
                            + float(unit.get("text_relevance") or 0.0) * 0.35
                            + (0.25 if role == "same_cp_context" else 0.16),
                            6,
                        )
                        row = {
                            "unit_id": uid,
                            "knowledge_zh": unit.get("knowledge_zh", ""),
                            "knowledge_en": unit.get("knowledge_en", ""),
                            "en_quote": unit.get("en_quote", ""),
                            "route": f"kg_{role}",
                            "score": score,
                            "head_id": head_id,
                            "option": packet.get("option"),
                            "evidence_role": role,
                            "source_seed_unit_id": packet.get("seed_unit_id"),
                            "source_core_point_id": unit.get("source_core_point_id") or cp.get("core_point_id"),
                            "target_core_point_id": unit.get("target_core_point_id") or cp.get("core_point_id"),
                            "relation_type": unit.get("relation_type", "same_core_point"),
                            "edge_scope": unit.get("edge_scope", "same_core_point"),
                            "text_relevance": unit.get("text_relevance", 0.0),
                        }
                        current = by_uid.get(uid)
                        if current is None or row["score"] > current["score"]:
                            by_uid[uid] = row
    rows = list(by_uid.values())
    rows.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return rows[:kg_top_k]


def compact_text(text: str, limit: int = 130) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def relation_text(edge_scope: str, relation_type: str, reason: str = "") -> str:
    scope_label = EDGE_SCOPE_LABELS.get(edge_scope, edge_scope or "关系")
    rel_label = RELATION_LABELS.get(relation_type, relation_type or "相关")
    raw = "/".join(x for x in (edge_scope, relation_type) if x)
    if raw:
        label = f"{scope_label} / {rel_label}（{raw}）"
    else:
        label = f"{scope_label} / {rel_label}"
    if reason:
        label += f"：{compact_text(reason, 100)}"
    return label


def unit_line(unit: dict[str, Any]) -> str:
    quote = unit.get("knowledge_zh") or unit.get("en_quote") or unit.get("knowledge_en") or ""
    return f"[Unit {unit.get('unit_id')}] {compact_text(quote)}"


def cp_line(cp: dict[str, Any]) -> str:
    title = cp.get("title_zh") or cp.get("title_en") or ""
    if cp.get("title_en") and cp.get("title_zh"):
        title = f"{cp.get('title_zh')} / {cp.get('title_en')}"
    return f"[CP {cp.get('core_point_id')}] {compact_text(title)}"


def path_hint(head_id: str, relation_type: str, role: str) -> str:
    if role == "same_cp_context":
        return "同一核心知识点下的补充单元，适合补足教材上下文；是否支持选项仍需看对象是否一致。"
    if relation_type in {"states_rule", "prescribes_measure", "defines", "explains", "describes_process"}:
        return "关系类型较强，可作为候选依据；需结合题干对象和选项对象判断是否直接支持。"
    if relation_type == "prepares":
        return "该边表示铺垫或引出，适合扩展相邻知识点；不能仅凭该边视为直接证明。"
    if relation_type in {"provides_context", "parallels", "summarizes"}:
        return "该边偏背景或并列相关，主要用于补充语境，不宜单独作为强证据。"
    if relation_type == "contrasts":
        return "该边表示对比或区分，可能用于反证或边界判断。"
    return "图谱相关路径，需回到 Unit 原文判断证据作用。"


def render_kg_micro_textbook(
    doc: dict[str, Any],
    max_paths_per_head: int = 8,
    max_paths_per_seed: int = 3,
) -> str:
    lines: list[str] = []
    lines.append(f"# {doc['question_id']} KG 微缩教材\n\n")
    lines.append("本文件把 KG 扩展结果压缩成 LLM 可读的路径式教材。格式为：`Unit --关系--> CP --关系--> Unit`。\n\n")
    lines.append(f"题干：{doc.get('stem', '')}\n\n")
    lines.append("## 选项\n\n")
    for label, text in (doc.get("options", {}) or {}).items():
        lines.append(f"- {label}. {text}\n")
    lines.append("\n")

    packets_by_head = doc.get("kg_expansion_packets", {}) or {}
    if not packets_by_head:
        lines.append("未生成 KG 扩展包。\n")
        return "".join(lines)

    head_order = ["stem"] + [f"option_{label}" for label in (doc.get("options", {}) or {}).keys()] + ["all_options"]
    for head_id in head_order:
        packets = packets_by_head.get(head_id) or []
        if not packets:
            continue
        if head_id.startswith("option_"):
            label = head_id.split("_", 1)[1]
            title = f"选项 {label}：{doc.get('options', {}).get(label, '')}"
        elif head_id == "stem":
            title = "题干背景"
        else:
            title = "全选项兜底"
        lines.append(f"## {title}\n\n")

        path_count = 0
        seen_paths: set[tuple[str, str, str, str]] = set()
        for packet in packets:
            seed_path_count = 0
            seed_unit = packet.get("seed_unit", {})
            for cp in packet.get("source_core_points", []):
                # Related-CP paths show the actual KG edge semantics, so render them before same-CP context.
                for related_cp in cp.get("related_core_points", []):
                    if path_count >= max_paths_per_head or seed_path_count >= max_paths_per_seed:
                        break
                    rel = related_cp.get("relation", {})
                    related_units = related_cp.get("related_cp_units", [])
                    for unit in related_units[:1]:
                        if path_count >= max_paths_per_head or seed_path_count >= max_paths_per_seed:
                            break
                        path_key = (
                            packet.get("seed_unit_id", ""),
                            cp.get("core_point_id", ""),
                            related_cp.get("core_point_id", ""),
                            unit.get("unit_id", ""),
                        )
                        if path_key in seen_paths:
                            continue
                        seen_paths.add(path_key)
                        path_count += 1
                        seed_path_count += 1
                        relation_type = rel.get("relation_type", "")
                        lines.append(f"### 路径 {head_id}-{path_count}｜相关知识点扩展\n\n")
                        lines.append(f"{unit_line(seed_unit)}\n")
                        lines.append("  -- 属于知识点 -->\n")
                        lines.append(f"{cp_line(cp)}\n")
                        lines.append(
                            f"  -- {relation_text(rel.get('edge_scope', ''), relation_type, rel.get('reason', ''))} -->\n"
                        )
                        lines.append(f"{cp_line(related_cp)}\n")
                        lines.append("  -- 包含知识单元 -->\n")
                        lines.append(f"{unit_line(unit)}\n\n")
                        lines.append(f"判读提示：{path_hint(head_id, relation_type, 'related_cp_context')}\n\n")

                if path_count >= max_paths_per_head or seed_path_count >= max_paths_per_seed:
                    break

                for unit in cp.get("same_cp_units", [])[:2]:
                    if path_count >= max_paths_per_head or seed_path_count >= max_paths_per_seed:
                        break
                    path_key = (
                        packet.get("seed_unit_id", ""),
                        cp.get("core_point_id", ""),
                        cp.get("core_point_id", ""),
                        unit.get("unit_id", ""),
                    )
                    if path_key in seen_paths:
                        continue
                    seen_paths.add(path_key)
                    path_count += 1
                    seed_path_count += 1
                    lines.append(f"### 路径 {head_id}-{path_count}｜同知识点补充\n\n")
                    lines.append(f"{unit_line(seed_unit)}\n")
                    lines.append("  -- 属于知识点 -->\n")
                    lines.append(f"{cp_line(cp)}\n")
                    lines.append(f"  -- {relation_text('same_core_point', 'same_core_point')} -->\n")
                    lines.append(f"{unit_line(unit)}\n\n")
                    lines.append(f"判读提示：{path_hint(head_id, 'same_core_point', 'same_cp_context')}\n\n")
                if path_count >= max_paths_per_head or seed_path_count >= max_paths_per_seed:
                    break
            if path_count >= max_paths_per_head:
                break
        if path_count == 0:
            lines.append("未形成可展示路径。\n\n")
    return "".join(lines)


def render_markdown(doc: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {doc['question_id']} Multi-Head Retrieval Experiment\n\n")
    lines.append(f"题干：{doc.get('stem', '')}\n\n")
    for label, text in (doc.get("options", {}) or {}).items():
        lines.append(f"- {label}. {text}\n")
    lines.append("\n")

    lines.append("## Heads\n\n")
    for head in doc.get("heads", []):
        lines.append(f"- {head['head_id']} | kind={head['head_kind']} | option={head.get('option') or '-'}\n")

    lines.append("\n## Merged Top Units\n\n")
    for i, row in enumerate(doc.get("merged_candidates", [])[:20], start=1):
        hit_desc = "; ".join(
            f"{h['head_id']}/{h['route']}={h['weighted_score']}"
            for h in row.get("head_hits", [])[:5]
        )
        lines.append(
            f"{i}. {row['unit_id']} | score={row.get('score')} | best={row.get('best_head_id')}/{row.get('best_route')}\n"
            f"   - heads: {hit_desc}\n"
            f"   - 中文：{row.get('knowledge_zh', '')}\n"
            f"   - English: {row.get('en_quote', '') or row.get('knowledge_en', '')}\n"
        )

    lines.append("\n## Per-Head Top Units\n\n")
    for head_id, rows in doc.get("head_results", {}).items():
        lines.append(f"### {head_id}\n\n")
        for i, row in enumerate(rows[:10], start=1):
            lines.append(
                f"{i}. {row['unit_id']} | {row.get('route')} | score={row.get('weighted_score')}\n"
                f"   - 中文：{row.get('knowledge_zh', '')}\n"
            )
        lines.append("\n")

    if doc.get("kg_candidates"):
        lines.append("## KG Flattened Candidates\n\n")
        for i, row in enumerate(doc.get("kg_candidates", [])[:20], start=1):
            lines.append(
                f"{i}. {row['unit_id']} | {row.get('route')} | score={row.get('score')} | head={row.get('head_id')} | option={row.get('option') or '-'}\n"
                f"   - seed: {row.get('source_seed_unit_id')} -> cp {row.get('source_core_point_id')} -> {row.get('target_core_point_id')}\n"
                f"   - relation: {row.get('edge_scope')}/{row.get('relation_type')} | relevance={row.get('text_relevance')}\n"
                f"   - 中文：{row.get('knowledge_zh', '')}\n"
            )
        lines.append("\n")

    if doc.get("kg_expansion_packets"):
        lines.append("## KG Expansion Packets\n\n")
        for head_id, packets in doc.get("kg_expansion_packets", {}).items():
            lines.append(f"### {head_id}\n\n")
            for packet in packets[:3]:
                lines.append(
                    f"- seed {packet.get('seed_unit_id')} | route={packet.get('seed_route')} | score={packet.get('seed_score')}\n"
                    f"  - seed text: {packet.get('seed_unit', {}).get('knowledge_zh', '')}\n"
                )
                for cp in packet.get("source_core_points", [])[:2]:
                    lines.append(
                        f"  - source CP {cp.get('core_point_id')}: {cp.get('title_en')} / {cp.get('title_zh')}\n"
                    )
                    for unit in cp.get("same_cp_units", [])[:3]:
                        lines.append(
                            f"    - same unit {unit.get('unit_id')} | rel={unit.get('text_relevance')}: {unit.get('knowledge_zh')}\n"
                        )
                    for related in cp.get("related_core_points", [])[:2]:
                        rel = related.get("relation", {})
                        lines.append(
                            f"    - related CP {related.get('core_point_id')} | {rel.get('edge_scope')}/{rel.get('relation_type')} | strength={rel.get('relation_strength')}: {related.get('title_en')} / {related.get('title_zh')}\n"
                        )
                        for unit in related.get("related_cp_units", [])[:2]:
                            lines.append(
                                f"      - related unit {unit.get('unit_id')} | rel={unit.get('text_relevance')}: {unit.get('knowledge_zh')}\n"
                            )
            lines.append("\n")
    return "".join(lines)


def process_question(
    question: dict[str, Any],
    bge_vecs: Any,
    card_ids: list[str],
    unit_lookup: dict[str, dict[str, Any]],
    bm25_zh_index: ba.BM25,
    bm25_en_index: ba.BM25,
    p5_index: dict[str, Any] | None,
    top_k: int,
    merge_top_k: int,
    include_all_options: bool,
    p5_top_k: int,
    kg_index: dict[str, Any] | None,
    kg_seed_limit: int,
    kg_top_k: int,
) -> dict[str, Any]:
    heads = build_retrieval_heads(question, include_all_options=include_all_options)
    head_results: dict[str, list[dict[str, Any]]] = {}
    for head in heads:
        head_results[head["head_id"]] = search_head(
            head,
            bge_vecs=bge_vecs,
            card_ids=card_ids,
            unit_lookup=unit_lookup,
            bm25_zh_index=bm25_zh_index,
            bm25_en_index=bm25_en_index,
            p5_index=p5_index,
            top_k=top_k,
            p5_top_k=p5_top_k,
        )

    merged = merge_head_results(head_results, merge_top_k=merge_top_k)
    kg_packets: dict[str, list[dict[str, Any]]] = {}
    if kg_index:
        head_map = {head["head_id"]: head for head in heads}
        for head_id, rows in head_results.items():
            kg_packets[head_id] = build_kg_packets_for_head(
                head_map[head_id],
                rows,
                kg_index=kg_index,
                unit_lookup=unit_lookup,
                seed_limit=kg_seed_limit,
                source_cp_limit=3,
                same_cp_unit_limit=5,
                related_cp_limit=4,
                related_cp_unit_limit=3,
            )
    kg_candidates = flatten_kg_packets(
        kg_packets,
        existing_unit_ids={row["unit_id"] for row in merged},
        kg_top_k=kg_top_k,
    ) if kg_packets else []
    return {
        "question_id": question.get("question_id"),
        "stem": question.get("stem", ""),
        "options": question.get("options", {}) or {},
        "heads": heads,
        "head_route_counts": {
            head_id: dict(Counter(row.get("route", "unknown") for row in rows))
            for head_id, rows in head_results.items()
        },
        "head_results": head_results,
        "merged_candidates": merged,
        "kg_expansion_packets": kg_packets,
        "kg_candidates": kg_candidates,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-head retrieval experiment without LLM.")
    parser.add_argument("--question-id", action="append", default=[], help="question id, e.g. v7_q_000009")
    parser.add_argument("--top-k", type=int, default=12, help="per route top-k for each head")
    parser.add_argument("--merge-top-k", type=int, default=80, help="merged candidate size")
    parser.add_argument("--include-all-options", action="store_true", help="include low-weight all-options fallback head")
    parser.add_argument("--enable-p5", action="store_true", help="include P5 alias recall")
    parser.add_argument("--p5-top-k", type=int, default=8, help="P5 top-k per head")
    parser.add_argument("--enable-kg", action="store_true", help="build per-head KG expansion packets")
    parser.add_argument("--kg-seed-limit", type=int, default=4, help="top direct seeds per head for KG packets")
    parser.add_argument("--kg-top-k", type=int, default=40, help="flattened KG candidate top-k")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR), help="experiment output directory")
    args = parser.parse_args()

    questions = ba.load_questions(ba.QUESTIONS_PATH)
    wanted = set(args.question_id or ["v7_q_000009", "v7_q_000012"])
    selected = [q for q in questions if q.get("question_id") in wanted]
    selected.sort(key=lambda x: x.get("question_id", ""))
    missing = wanted - {q.get("question_id") for q in selected}
    if missing:
        raise RuntimeError(f"指定题号不存在: {', '.join(sorted(missing))}")

    index = ba.load_index(ba.INDEX_PKL)
    card_ids: list[str] = index["card_ids"]
    bge_vecs = index["bge_vecs"]
    unit_lookup: dict[str, dict[str, Any]] = index["unit_lookup"]
    bm25_zh = ba.BM25(index["zh_bm25_docs"], index["zh_bm25_df"], index["zh_bm25_avgdl"])
    bm25_en = ba.BM25(index["en_bm25_docs"], index["en_bm25_df"], index["en_bm25_avgdl"])
    ba.get_bge_model()
    p5_index = ba.load_p5_alias_index(ba.P5_ALIAS_INDEX_PATH) if args.enable_p5 else None
    kg_index = ba.load_kg_graph(ba.KG_GRAPH_PATH) if args.enable_kg else None

    output_dir = Path(args.output_dir)
    index_rows: list[dict[str, str]] = []
    for question in selected:
        doc = process_question(
            question,
            bge_vecs=bge_vecs,
            card_ids=card_ids,
            unit_lookup=unit_lookup,
            bm25_zh_index=bm25_zh,
            bm25_en_index=bm25_en,
            p5_index=p5_index,
            top_k=args.top_k,
            merge_top_k=args.merge_top_k,
            include_all_options=args.include_all_options,
            p5_top_k=args.p5_top_k,
            kg_index=kg_index,
            kg_seed_limit=args.kg_seed_limit,
            kg_top_k=args.kg_top_k,
        )
        qid = doc["question_id"]
        json_path = output_dir / f"{qid}.multi_head_retrieval.json"
        md_path = output_dir / f"{qid}.multi_head_retrieval.md"
        kg_micro_path = output_dir / f"{qid}.kg_micro_textbook.md"
        write_json(json_path, doc)
        write_text(md_path, render_markdown(doc))
        if doc.get("kg_expansion_packets"):
            write_text(kg_micro_path, render_kg_micro_textbook(doc))
        index_rows.append(
            {
                "question_id": qid,
                "json": str(json_path),
                "markdown": str(md_path),
                "kg_micro_textbook": str(kg_micro_path) if doc.get("kg_expansion_packets") else "",
            }
        )
        print(f"[ok] {qid} -> {json_path}")

    write_json(output_dir / "index.json", index_rows)


if __name__ == "__main__":
    main()
