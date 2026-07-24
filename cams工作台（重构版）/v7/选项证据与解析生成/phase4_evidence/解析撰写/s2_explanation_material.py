# -*- coding: utf-8 -*-
"""s2 — 解析撰写专用：证据材料层。候选池索引、材料卡构建、上下文增强、格式化输出。"""

from __future__ import annotations

import sys
from pathlib import Path as _Path
_PARENT = str(_Path(__file__).resolve().parent.parent)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from typing import Any

from 解析撰写.s1_explanation_data import (
    KG_GRAPH_PATH, OPTION_SUPPLEMENT_CONTEXT_LIMIT, _get_unit_page_map,
)
from 公共函数.index import _load_kg_units, _compact_text


_TYPE_CN_MAP: dict[str, str] = {
    "definition": "概念定义",
    "rule": "规则/规定",
    "case": "案例",
    "fact": "事实陈述",
    "process": "流程描述",
    "risk_indicator": "风险指标",
    "classification": "分类说明",
    "context": "背景信息",
}


def _type_cn_label(content_type: str) -> str:
    return _TYPE_CN_MAP.get(str(content_type or "").strip(), content_type or "")


def candidate_by_unit(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_unit = {
        str(candidate["unit_id"]): candidate
        for candidate in result.get("candidate_pool", []) or []
        if isinstance(candidate, dict) and candidate.get("unit_id")
    }
    for rows in (result.get("option_supplement_pool", {}) or {}).values():
        for candidate in rows or []:
            if isinstance(candidate, dict) and candidate.get("unit_id"):
                by_unit.setdefault(str(candidate["unit_id"]), candidate)
    return by_unit


def _material_card(unit: dict[str, Any], uid: str, source_kind: str) -> dict[str, Any]:
    return {
        "unit_id": uid,
        "source_kind": source_kind,
        "knowledge_zh": unit.get("knowledge_zh", ""),
        "en_quote": unit.get("en_quote") or unit.get("knowledge_en", ""),
        "heading_context": unit.get("heading_context", []),
        "best_rank": unit.get("best_rank"),
        "routes": unit.get("routes", []),
        "languages": unit.get("languages", []),
        "content_type": unit.get("type", ""),
        "printed_page": unit.get("printed_page", ""),
        "pdf_page": unit.get("pdf_page", ""),
    }


def enriched_option_material(result: dict[str, Any]) -> list[dict[str, Any]]:
    options = result.get("options", {}) or {}
    unit_map = candidate_by_unit(result)
    supplements = result.get("option_supplement_pool", {}) or {}
    by_label = {
        str(row.get("option", "")).strip().upper(): row
        for row in result.get("option_analysis", []) or []
        if isinstance(row, dict)
    }
    rows: list[dict[str, Any]] = []
    for label, option_text in options.items():
        label = str(label).strip().upper()
        analysis = by_label.get(label, {})
        cards: list[dict[str, Any]] = []
        bound_ids: set[str] = set()
        for card in analysis.get("evidence_cards", []) or []:
            if not isinstance(card, dict):
                continue
            uid = str(card.get("unit_id", "")).strip()
            unit = unit_map.get(uid)
            if not unit or uid in bound_ids:
                continue
            bound_ids.add(uid)
            material = _material_card(unit, uid, "adjudicated")
            material["support_type"] = card.get("support_type", "")
            cards.append(material)

        supplement_cards: list[dict[str, Any]] = []
        for unit in supplements.get(label, []) or []:
            uid = str(unit.get("unit_id", "")).strip()
            if not uid or uid in bound_ids:
                continue
            supplement_cards.append(_material_card(unit, uid, "supplement_candidate"))
            if len(supplement_cards) >= OPTION_SUPPLEMENT_CONTEXT_LIMIT:
                break

        rows.append({
            "option": label,
            "option_text": option_text,
            "judgement": analysis.get("judgement", ""),
            "evidence_status": analysis.get("evidence_status", ""),
            "decision_basis": analysis.get("decision_basis", ""),
            "evidence_cards": cards,
            "supplement_cards": supplement_cards,
        })
    return rows


def _format_prompt_card(card: dict[str, Any]) -> str:
    retrieval = ""
    if card.get("source_kind") == "supplement_candidate":
        retrieval = (
            f" | best_rank={card.get('best_rank', '')}"
            f" | routes={','.join(card.get('routes', []) or [])}"
            f" | languages={','.join(card.get('languages', []) or [])}"
        )
    type_label = _type_cn_label(card.get("content_type", ""))
    type_str = f" | 教材类型：{type_label}" if type_label else ""
    page_info = _get_unit_page_map().get(card["unit_id"], {})
    printed_page = page_info.get("printed_page", "")
    page_str = f" | P{printed_page}" if printed_page else ""
    return (
        f"- {card['unit_id']} | {card['source_kind']}"
        f" | {card.get('support_type', '')}{type_str}{page_str}{retrieval}\n"
        f"  中文要点：{_compact_text(card['knowledge_zh'])}\n"
        f"  英文原文：{_compact_text(card['en_quote'])}\n"
        f"  章节：{' > '.join(card['heading_context'])}"
    )


# ── KG 教材原文连续上下文 ──

def _section_context_cards(
    unit_id: str,
    candidate_ids: set[str],
    context_range: int = 4,
) -> list[dict[str, Any]]:
    """返回 unit_id 同 Section 内 unit_order ±context_range 的连续材料卡。"""
    kg_units = _load_kg_units()
    center = kg_units.get(unit_id)
    if not center:
        return []

    section_id = center.get("section_id", "")
    center_order = int(center.get("unit_order") or 0)
    if not section_id or not center_order:
        return []

    siblings: list[dict[str, Any]] = []
    for uid, unit in kg_units.items():
        if unit.get("section_id") == section_id:
            siblings.append(unit)
    siblings.sort(key=lambda u: int(u.get("unit_order") or 0))

    result: list[dict[str, Any]] = []
    for unit in siblings:
        order = int(unit.get("unit_order") or 0)
        if abs(order - center_order) <= context_range:
            uid = str(unit.get("unit_id", ""))
            is_candidate = uid in candidate_ids
            card = {
                "unit_id": uid,
                "knowledge_zh": unit.get("knowledge_zh", ""),
                "en_quote": unit.get("en_quote") or "",
                "heading_context": unit.get("heading_context") or [],
                "type": unit.get("type", ""),
                "printed_page": unit.get("printed_page", ""),
                "real_section": unit.get("real_section") or unit.get("section_id", ""),
                "unit_order": order,
                "is_candidate": is_candidate,
                "is_center": uid == unit_id,
            }
            result.append(card)
    return result


def _format_context_block(cards: list[dict[str, Any]]) -> str:
    """将一组连续材料卡（含上下文）格式化为提示文本块。"""
    if not cards:
        return ""

    section_label = cards[0].get("real_section", "")
    heading = " > ".join(cards[0].get("heading_context", []) or [])

    lines = [f"【教材原文连续段落 — {section_label} ({heading})】", ""]
    for card in cards:
        uid = card["unit_id"]
        zh = _compact_text(card["knowledge_zh"])
        en = _compact_text(card["en_quote"])
        page_str = f" | P{card['printed_page']}" if card.get("printed_page") else ""
        type_label = _type_cn_label(card.get("type", ""))
        type_str = f" | 教材类型：{type_label}" if type_label else ""

        if card["is_center"]:
            marker = "★ 命中"
        elif card["is_candidate"]:
            marker = "  已检索"
        else:
            marker = "  补充上下文"

        lines.append(f"[{uid}] {marker}{type_str}{page_str}")
        lines.append(f"  中文要点：{zh}")
        if en:
            lines.append(f"  英文原文：{en}")
        lines.append("")
    lines.append("-" * 60)
    return "\n".join(lines)


def _build_context_augmented_material(
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    """与 enriched_option_material 同接口，但每张 evidence card 附加 ±2 上下文。"""
    options = result.get("options", {}) or {}
    unit_map = candidate_by_unit(result)
    supplements = result.get("option_supplement_pool", {}) or {}
    by_label = {
        str(row.get("option", "")).strip().upper(): row
        for row in result.get("option_analysis", []) or []
        if isinstance(row, dict)
    }

    rows: list[dict[str, Any]] = []
    for label, option_text in options.items():
        label = str(label).strip().upper()
        analysis = by_label.get(label, {})
        cards: list[dict[str, Any]] = []
        bound_ids: set[str] = set()
        for evidence_card in analysis.get("evidence_cards", []) or []:
            if not isinstance(evidence_card, dict):
                continue
            uid = str(evidence_card.get("unit_id", "")).strip()
            unit = unit_map.get(uid)
            if not unit or uid in bound_ids:
                continue
            bound_ids.add(uid)
            material = _material_card(unit, uid, "adjudicated")
            material["support_type"] = evidence_card.get("support_type", "")
            material["context_block"] = _section_context_cards(uid, bound_ids)
            cards.append(material)

        supplement_cards: list[dict[str, Any]] = []
        for unit in supplements.get(label, []) or []:
            uid = str(unit.get("unit_id", "")).strip()
            if not uid or uid in bound_ids:
                continue
            bound_ids.add(uid)
            sc = _material_card(unit, uid, "supplement_candidate")
            sc["context_block"] = _section_context_cards(uid, bound_ids)
            supplement_cards.append(sc)
            if len(supplement_cards) >= OPTION_SUPPLEMENT_CONTEXT_LIMIT:
                break

        judgement = analysis.get("judgement", "")
        rows.append({
            "option": label,
            "option_text": option_text,
            "judgement": judgement,
            "evidence_status": analysis.get("evidence_status", ""),
            "decision_basis": analysis.get("decision_basis", ""),
            "evidence_cards": cards,
            "supplement_cards": supplement_cards,
        })
    return rows