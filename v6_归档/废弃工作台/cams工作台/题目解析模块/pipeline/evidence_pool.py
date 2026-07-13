"""证据池：薄封装，复用新题解析模块的 AgenticRuntime。

新题解析模块的 ``evidence_pool.load_new_question_runtime`` 已经：
- 加载 cards_v6_sentence.json（v6s 全书句卡，5199 张）
- 构建 BGE 向量索引 + BM25 稀疏索引 + 句卡关系图
- 返回 AgenticRuntime，含 ``retrieve_for_option`` 等检索能力

本模块不重复造轮子。因为两个模块的包都叫 ``pipeline``，直接 ``from pipeline...``
会撞到自身，所以用 importlib 按文件路径加载新题解析模块的 evidence_pool。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_NEW_QUESTION_EVIDENCE_POOL = (
    Path(__file__).resolve().parents[2] / "新题解析模块" / "pipeline" / "evidence_pool.py"
)

if not _NEW_QUESTION_EVIDENCE_POOL.exists():
    raise FileNotFoundError(
        f"找不到新题解析模块的 evidence_pool：{_NEW_QUESTION_EVIDENCE_POOL}"
    )

# 按文件路径加载，避免与本模块的 pipeline 包名冲突
_spec = importlib.util.spec_from_file_location(
    "_nq_evidence_pool", _NEW_QUESTION_EVIDENCE_POOL
)
_nq_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_nq_module)

get_agentic_runtime = _nq_module.get_agentic_runtime
load_new_question_runtime = _nq_module.load_new_question_runtime


def get_match_runtime():
    """返回本模块的 AgenticRuntime 单例（v6-sentence 全书句卡池）。

    首次调用加载 BGE/BM25/关系图（约 30-60 秒），后续调用直接返回缓存。
    """
    return get_agentic_runtime()


def reload_runtime(evidence_scope: str = "v6-sentence"):
    """强制重新加载 runtime（切换 evidence_scope 时用）。"""
    return load_new_question_runtime(evidence_scope=evidence_scope)
