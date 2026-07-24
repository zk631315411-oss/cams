# -*- coding: utf-8 -*-
"""候选记录工厂。所有检索路径通过此函数构建候选记录，字段只定义一次。"""

from __future__ import annotations
from typing import Any


def make_candidate(unit: dict[str, Any], route: str, score: float, **overrides: Any) -> dict[str, Any]:
    """从 unit 构建统一的候选记录。BGE/BM25/补充池/KG扩展统一入口。"""
    c: dict[str, Any] = {
        "unit_id": unit["unit_id"],
        "knowledge_zh": unit.get("knowledge_zh", ""),
        "knowledge_en": unit.get("knowledge_en", ""),
        "en_quote": unit.get("en_quote", ""),
        "heading_context": unit.get("heading_context", []),
        "type": unit.get("type", ""),
        "route": route,
        "score": round(score, 6),
        "printed_page": unit.get("printed_page", ""),
        "pdf_page": unit.get("pdf_page", ""),
    }
    c.update(overrides)
    return c
