"""检索层的唯一业务入口，明确区分题目检索和一般检索。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .assets import load_assets, load_retrieval_defaults
from .pipeline import make_config, retrieve_general, retrieve_question


def search_evidence(root: str | Path | None, query: str, top_k: int = 20,
                    *, language: str = "auto", config: dict[str, Any] | None = None) -> dict[str, Any]:
    """一般检索：单查询 RAG 与 KG 图谱扩展，不建立题目检索头或 P5 归一。"""
    overrides = load_retrieval_defaults(root)
    overrides.update(config or {})
    overrides["top_k"] = int(top_k)
    retrieval_config = make_config(overrides, question_mode=False)
    assets = load_assets(root, enable_kg=retrieval_config.enable_kg, enable_p5=False)
    return retrieve_general(query, assets, retrieval_config, language)


def retrieve_question_evidence(root: str | Path | None, question: dict[str, Any],
                               *, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """题目检索：完整 V7 检索头、P5、RAG、选项补充池和 KG 图谱扩展。"""
    overrides = load_retrieval_defaults(root)
    overrides.update(config or {})
    retrieval_config = make_config(overrides, question_mode=True)
    assets = load_assets(root, enable_kg=retrieval_config.enable_kg, enable_p5=retrieval_config.enable_p5)
    return retrieve_question(question, assets, retrieval_config)
