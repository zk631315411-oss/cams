# -*- coding: utf-8 -*-
"""s1 — 盲判专用：检索头构建 + 上下文卡片。公共基础设施从 公共函数.index 导入。"""

from __future__ import annotations

import sys
from pathlib import Path as _Path
_PARENT = str(_Path(__file__).resolve().parent.parent)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from typing import Any

from 公共函数.index import *

# ── 盲判专用常量 ──

_SECTION_RANGE = 4

# ── 盲判专用：上下文卡片 ──

def _section_context_cards(unit_id: str, candidate_ids: set[str], context_range: int=_SECTION_RANGE) -> list[dict[str,Any]]:
    kg_units = _load_kg_units()
    center = kg_units.get(unit_id)
    if not center: return []
    section_id, center_order = center.get("section_id",""), int(center.get("unit_order") or 0)
    if not section_id or not center_order: return []
    siblings = sorted([u for u in kg_units.values() if u.get("section_id")==section_id], key=lambda u: int(u.get("unit_order") or 0))
    result: list[dict[str,Any]] = []
    for unit in siblings:
        order = int(unit.get("unit_order") or 0)
        if abs(order - center_order) <= context_range:
            uid = str(unit.get("unit_id",""))
            result.append({"unit_id":uid,"knowledge_zh":unit.get("knowledge_zh",""),"en_quote":unit.get("en_quote") or "","heading_context":unit.get("heading_context") or [],"type":unit.get("type",""),"printed_page":unit.get("printed_page",""),"real_section":unit.get("real_section") or unit.get("section_id",""),"unit_order":order,"is_candidate":uid in candidate_ids,"is_center":uid==unit_id})
    return result

def _format_context_block(cards: list[dict[str,Any]]) -> str:
    if not cards: return ""
    section_label, heading = cards[0].get("real_section",""), " > ".join(cards[0].get("heading_context",[]) or [])
    lines = [f"【教材原文连续段落 — {section_label} ({heading})】", ""]
    for card in cards:
        zh, en = _compact_text(card["knowledge_zh"]), _compact_text(card["en_quote"])
        page_str = f" | P{card['printed_page']}" if card.get("printed_page") else ""
        marker = "★ 命中" if card["is_center"] else ("  已检索" if card["is_candidate"] else "  补充上下文")
        lines.append(f"[{card['unit_id']}] {marker}{page_str}")
        if zh: lines.append(f"  中文要点：{zh}")
        if en: lines.append(f"  英文原文：{en}")
        lines.append("")
    lines.append("-"*60)
    return "\n".join(lines)

# ── 盲判专用：检索头 ──

def build_retrieval_heads(question: dict[str, Any]) -> list[dict[str, Any]]:
    heads: list[dict[str, Any]] = []
    stem = str(question.get("stem","") or "").strip()
    stem_en = str(question.get("stem_en","") or "").strip()
    options = question.get("options",{}) or {}
    options_en = question.get("options_en",{}) or {}
    if stem: heads.append({"head_id":"stem_zh","head_kind":"stem","option":None,"language":"zh","query":stem})
    for label, text in options.items():
        query = f"{stem} {text}".strip()
        if query: heads.append({"head_id":f"option_{label}_zh","head_kind":"option","option":str(label),"language":"zh","query":query})
    if stem_en: heads.append({"head_id":"stem_en","head_kind":"stem","option":None,"language":"en","query":stem_en})
    for label, text in options_en.items():
        query = f"{stem_en} {text}".strip()
        if query: heads.append({"head_id":f"option_{label}_en","head_kind":"option","option":str(label),"language":"en","query":query})
    return heads

def build_option_only_heads(question: dict[str, Any]) -> list[dict[str, Any]]:
    heads: list[dict[str, Any]] = []
    for language, field in (("zh","options"),("en","options_en")):
        for label, text in (question.get(field,{}) or {}).items():
            query = str(text or "").strip()
            if not query: continue
            heads.append({"head_id":f"option_only_{label}_{language}","head_kind":"option_only_supplement","option":str(label),"language":language,"query":query})
    return heads
