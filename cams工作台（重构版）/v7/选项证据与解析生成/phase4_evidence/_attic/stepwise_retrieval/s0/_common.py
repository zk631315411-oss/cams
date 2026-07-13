# -*- coding: utf-8 -*-
"""s0 三步脚本共享的路径常量、I/O 工具、文本工具和题目筛选函数。

三个脚本（s0a、s0b、s0c）共用的代码集中在此，避免重复定义。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# ── 路径常量 ──────────────────────────────────────────────
# _common.py 位于 s0/ 目录下，以此推算各层级目录

S0_DIR = Path(__file__).resolve().parent           # s0/
STEPWISE_DIR = S0_DIR.parent                        # stepwise_retrieval/
TESTS_DIR = STEPWISE_DIR.parent                     # tests/
PHASE4_DIR = TESTS_DIR.parent                       # phase4_evidence/
WORKSPACE_DIR = PHASE4_DIR.parent                   # 选项证据与解析生成/
V7_ROOT = WORKSPACE_DIR.parent                      # v7/

QUESTIONS_PATH = (
    WORKSPACE_DIR / "phase3.5_questions" / "output" / "v7_questions.json"
)
P5_ALIAS_INDEX_PATH = (
    V7_ROOT
    / "知识图谱提取"
    / "phases"
    / "phase05_terms"
    / "outputs"
    / "p5c_alias_index.json"
)


# ── I/O 工具 ──────────────────────────────────────────────

def load_json(path: Path) -> Any:
    """读取 JSON 文件并返回 Python 对象。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    """将数据写入 JSON 文件，自动创建父目录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_text(path: Path, text: str) -> None:
    """将字符串写入文本文件，自动创建父目录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


# ── 文本工具 ──────────────────────────────────────────────

def normalize_space(text: str) -> str:
    """将连续空白压缩为单个空格，并去除首尾空白。"""
    return re.sub(r"\s+", " ", str(text or "").strip())


def normalize_cjk_term(text: str) -> str:
    """对 CJK 术语做规范化：去空格、去标点、去"的"。"""
    text = normalize_space(text).lower()
    text = re.sub(r"[\s，。、“”‘’：:；;,.!?！？（）()《》<>\[\]{}\-_/]", "", text)
    text = text.replace("的", "")
    return text


def term_in_text(term: str, text: str) -> bool:
    """判断 term 是否出现在 text 中（支持中英文模糊匹配）。"""
    term = normalize_space(term).lower()
    text = normalize_space(text).lower()
    if not term or not text:
        return False
    if re.fullmatch(r"[a-z0-9][a-z0-9_\-/. ]*", term):
        escaped = re.escape(term).replace(r"\ ", r"\s+")
        return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text) is not None
    if term in text:
        return True
    return normalize_cjk_term(term) in normalize_cjk_term(text)


# ── 共享工具函数 ──────────────────────────────────────────

def append_unique(values: list[str], value: str) -> None:
    """向列表追加不重复的值（大小写不敏感）。"""
    value = normalize_space(value)
    if value and value.lower() not in {v.lower() for v in values}:
        values.append(value)


# ── 题目加载和筛选 ────────────────────────────────────────

def load_questions(path: Path) -> list[dict[str, Any]]:
    """从 v7_questions.json 中提取题目列表。"""
    data = load_json(path)
    return data["items"]


def select_questions(
    questions: list[dict[str, Any]],
    question_ids: list[str],
    run_all: bool,
    limit: int | None,
    offset: int,
) -> list[dict[str, Any]]:
    """按参数筛选题目列表。

    优先级：
    1. question_ids 指定题号
    2. run_all 或 limit 指定范围
    3. 默认只返回 v7_q_000009
    """
    questions = sorted(questions, key=lambda q: q.get("question_id", ""))
    if question_ids:
        wanted = set(question_ids)
        selected = [q for q in questions if q.get("question_id") in wanted]
        missing = wanted - {q.get("question_id") for q in selected}
        if missing:
            raise RuntimeError(f"指定题号不存在: {', '.join(sorted(missing))}")
        return selected

    if run_all or limit is not None:
        start = max(offset, 0)
        end = None if limit is None else start + max(limit, 0)
        return questions[start:end]

    return [q for q in questions if q.get("question_id") == "v7_q_000009"]