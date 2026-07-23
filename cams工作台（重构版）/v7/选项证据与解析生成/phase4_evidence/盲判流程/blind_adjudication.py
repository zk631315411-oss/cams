# -*- coding: utf-8 -*-
"""
Phase 4.1 — 小批量盲判脚本（Blind Adjudication）
================================================

从 manual_reviewed 标记的题目中抽样（默认前 10 题），对每道题执行：

  1. 按题干/单选项分头执行 BGE + 对应语言 BM25，合并取 top-30 候选池
  2. 构建裁判 prompt（不含参考答案），调用 LLM 裁判
  3. 解析 LLM 响应并做机械校验
  4. 输出每题详情 JSON + 汇总 JSONL + Markdown 报告

用法:
    python blind_adjudication.py --limit 10 --concurrency 10 --model deepseek-v4-pro

依赖:
    pip install openai rank_bm25 scikit-learn numpy
"""

from __future__ import annotations

import argparse
import json
import math
import os
import pickle
import re
import sys
import time
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# ── 路径 ───────────────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent  # phase4_evidence/盲判流程/
PHASE4 = HERE.parent
V7_ROOT = PHASE4.parent  # 选项证据与解析生成/
PROJECT_ROOT = PHASE4.parents[1]  # v7/

QUESTIONS_PATH = (
    V7_ROOT / "phase3.5_questions" / "output" / "v7_questions.json"
)
INDEX_PKL = (
    V7_ROOT
    / "phase3_index"
    / "output"
    / "index"
    / "v7_index_5614abb1c4bf.pkl"
)
KG_GRAPH_PATH = (
    PROJECT_ROOT
    / "知识图谱提取"
    / "phases"
    / "phase06_kg_views"
    / "outputs"
    / "kg_retrieval_graph.json"
)
P5_ALIAS_INDEX_PATH = (
    PROJECT_ROOT
    / "知识图谱提取"
    / "phases"
    / "phase05_terms"
    / "outputs"
    / "p5c_alias_index.json"
)
OUTPUT_DIR = PHASE4 / "output"
QUESTION_TEXT_OVERRIDES_PATH = HERE / "question_text_overrides.jsonl"

API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

# ── ±4 上下文扩展（从解析脚本移植） ─────────────────────────────────

_KG_UNIT_CACHE: dict[str, dict[str, Any]] | None = None
_SECTION_RANGE = 4


def _load_kg_units() -> dict[str, dict[str, Any]]:
    global _KG_UNIT_CACHE
    if _KG_UNIT_CACHE is not None:
        return _KG_UNIT_CACHE
    if not KG_GRAPH_PATH.exists():
        _KG_UNIT_CACHE = {}
        return _KG_UNIT_CACHE
    with open(KG_GRAPH_PATH, "r", encoding="utf-8") as f:
        kg = json.load(f)
    _KG_UNIT_CACHE = {}
    for unit in kg.get("units", []) or []:
        uid = str(unit.get("unit_id", "")).strip()
        if uid:
            _KG_UNIT_CACHE[uid] = unit
    return _KG_UNIT_CACHE


def _compact_text(value: Any, max_len: int = 520) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _section_context_cards(
    unit_id: str, candidate_ids: set[str], context_range: int = _SECTION_RANGE,
) -> list[dict[str, Any]]:
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
            result.append({
                "unit_id": uid,
                "knowledge_zh": unit.get("knowledge_zh", ""),
                "en_quote": unit.get("en_quote") or "",
                "heading_context": unit.get("heading_context") or [],
                "type": unit.get("type", ""),
                "printed_page": unit.get("printed_page", ""),
                "real_section": unit.get("real_section") or unit.get("section_id", ""),
                "unit_order": order,
                "is_candidate": uid in candidate_ids,
                "is_center": uid == unit_id,
            })
    return result


def _format_context_block(cards: list[dict[str, Any]]) -> str:
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
        if card["is_center"]:
            marker = "★ 命中"
        elif card["is_candidate"]:
            marker = "  已检索"
        else:
            marker = "  补充上下文"
        lines.append(f"[{uid}] {marker}{page_str}")
        if zh:
            lines.append(f"  中文要点：{zh}")
        if en:
            lines.append(f"  英文原文：{en}")
        lines.append("")
    lines.append("-" * 60)
    return "\n".join(lines)


# ── 分词器（复用 P4.0 / phase3 实现） ──────────────────────────────


def tokenize(text: str) -> list[str]:
    """与 v6 / phase3 一致的 tokenizer：英文按单词，中文按 2/3-gram 子串。"""
    text = (text or "").lower()
    tokens: list[str] = []
    # 英文/数字 token：连续字母数字，允许 _ - / .
    tokens.extend(re.findall(r"[a-z0-9][a-z0-9_\-/.]*", text))
    # 中文 token：CJK 字符的 2-gram 和 3-gram 子串
    cjk_runs = re.findall(r"[一-鿿]+", text)
    for run in cjk_runs:
        if len(run) == 1:
            tokens.append(run)
            continue
        for n in (2, 3):
            if len(run) >= n:
                tokens.extend(run[i: i + n] for i in range(len(run) - n + 1))
    return tokens


# ── BM25（复用 P4.0 实现） ────────────────────────────────────────────


class BM25:
    """Okapi BM25 实现，适配 phase3 已预分词的 Counter 文档。"""

    def __init__(
        self,
        docs: list[Counter],
        df: dict[str, int],
        avgdl: float,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        self.docs = docs
        self.df = df
        self.avgdl = avgdl
        self.k1 = k1
        self.b = b
        self.N = len(docs)
        self.doc_lens = [sum(doc.values()) for doc in docs]
        self.idf_cache: dict[str, float] = {}

    def idf(self, term: str) -> float:
        if term not in self.idf_cache:
            n = self.df.get(term, 0)
            self.idf_cache[term] = math.log(
                (self.N - n + 0.5) / (n + 0.5) + 1.0
            )
        return self.idf_cache[term]

    def score(self, query_tokens: list[str], doc_idx: int) -> float:
        doc = self.docs[doc_idx]
        doc_len = self.doc_lens[doc_idx]
        score = 0.0
        qtf = Counter(query_tokens)
        for term, qf in qtf.items():
            tf = doc.get(term, 0)
            if tf == 0:
                continue
            idf_val = self.idf(term)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * doc_len / self.avgdl
            )
            score += idf_val * (numerator / denominator) * qf
        return score

    def search(self, query: str, top_k: int = 20) -> list[tuple[int, float]]:
        q_tokens = tokenize(query)
        if not q_tokens:
            return []
        scores = [(i, self.score(q_tokens, i)) for i in range(self.N)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ── 数据加载 ──────────────────────────────────────────────────────────


def load_index(pkl_path: str | Path) -> dict[str, Any]:
    """加载 phase3 索引 PKL 文件。"""
    print(f"[load] 读取索引: {pkl_path}")
    with open(pkl_path, "rb") as f:
        idx = pickle.load(f)
    print(
        f"[load] 索引加载完成 | card_ids={len(idx['card_ids'])}"
        f" | bge_vecs={idx['bge_vecs'].shape}"
        f" | unit_lookup={len(idx['unit_lookup'])}"
    )
    return idx


def load_question_text_overrides(
    jsonl_path: str | Path,
) -> dict[str, dict[str, Any]]:
    """加载可审计的题目显示文本修订，不接触原始题库。"""
    path = Path(jsonl_path)
    if not path.exists():
        raise RuntimeError(f"题目文本 override 文件不存在: {path}")

    overrides: dict[str, dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"{path}:{line_no}: JSON 解析失败: {exc}"
                ) from exc
            qid = str(row.get("question_id", "")).strip()
            if not qid:
                raise RuntimeError(f"{path}:{line_no}: 缺少 question_id")
            if qid in overrides:
                raise RuntimeError(f"题目文本 override question_id 重复: {qid}")
            overrides[qid] = row
    return overrides


def apply_question_text_overrides(
    items: list[dict[str, Any]],
    overrides: dict[str, dict[str, Any]],
    override_source: str | Path,
) -> list[dict[str, Any]]:
    """校验上游原文后应用显示值，并把原值与来源写入审计元数据。"""
    item_ids = {str(item.get("question_id", "")) for item in items}
    unknown_ids = sorted(set(overrides) - item_ids)
    if unknown_ids:
        raise RuntimeError(
            "题目文本 override 指向不存在的题号: " + ", ".join(unknown_ids)
        )

    applied: list[dict[str, Any]] = []
    for item in items:
        qid = str(item.get("question_id", ""))
        override = overrides.get(qid)
        if not override:
            applied.append(item)
            continue

        normalized = dict(item)
        normalized["options"] = dict(item.get("options", {}) or {})
        normalized["options_en"] = dict(item.get("options_en", {}) or {})
        audit_options: dict[str, dict[str, Any]] = {}

        option_overrides = override.get("option_overrides", {}) or {}
        if not isinstance(option_overrides, dict) or not option_overrides:
            raise RuntimeError(f"{qid}: override 缺少 option_overrides")

        for raw_label, option_override in option_overrides.items():
            label = str(raw_label).upper()
            if not isinstance(option_override, dict):
                raise RuntimeError(f"{qid} {label}: option override 必须是对象")
            actual_zh = normalized["options"].get(label)
            actual_en = normalized["options_en"].get(label)
            expected_zh = option_override.get("expected_source_zh")
            expected_en = option_override.get("expected_source_en")
            if actual_zh != expected_zh or actual_en != expected_en:
                raise RuntimeError(
                    f"{qid} {label}: 上游题源文本已变化，拒绝应用 override; "
                    f"中文 actual={actual_zh!r} expected={expected_zh!r}; "
                    f"英文 actual={actual_en!r} expected={expected_en!r}"
                )
            display_zh = str(option_override.get("display_zh", "")).strip()
            if not display_zh:
                raise RuntimeError(f"{qid} {label}: 缺少 display_zh")
            normalized["options"][label] = display_zh
            audit_options[label] = {
                "source_zh": actual_zh,
                "source_en": actual_en,
                "display_zh": display_zh,
                "flags": list(option_override.get("flags", []) or []),
                "source_screenshots": dict(
                    option_override.get("source_screenshots", {}) or {}
                ),
                "reason": str(option_override.get("reason", "")),
            }

        normalized["_question_text_override"] = {
            "override_source": str(Path(override_source).resolve()),
            "options": audit_options,
        }
        applied.append(normalized)
    return applied


def load_questions(
    json_path: str | Path,
    overrides_path: str | Path | None = QUESTION_TEXT_OVERRIDES_PATH,
) -> list[dict[str, Any]]:
    """加载 v7 题库，并在副本上应用可审计的显示文本修订。"""
    print(f"[load] 读取题库: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data["items"]
    if overrides_path is not None:
        overrides = load_question_text_overrides(overrides_path)
        items = apply_question_text_overrides(items, overrides, overrides_path)
        print(f"[load] 题目文本 override 已应用 | 共 {len(overrides)} 题")
    print(f"[load] 题库加载完成 | 共 {len(items)} 题")
    return items


def load_chapter_mapping_index(
    jsonl_path: str | Path,
) -> dict[str, dict[str, Any]]:
    """加载按 question_id 索引的已审核章节决定。"""
    path = Path(jsonl_path)
    if not path.exists():
        raise RuntimeError(f"章节映射文件不存在: {path}")
    index: dict[str, dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: JSON 解析失败: {exc}") from exc
            qid = str(row.get("question_id", ""))
            if not qid:
                raise RuntimeError(f"{path}:{line_no}: 缺少 question_id")
            if qid in index:
                raise RuntimeError(f"章节映射 question_id 重复: {qid}")
            index[qid] = row
    return index


def _append_unique(bucket: list[str], value: str) -> None:
    """保持插入顺序的无重复追加。"""
    if value and value not in bucket:
        bucket.append(value)


def load_kg_graph(json_path: str | Path) -> dict[str, Any]:
    """加载 P6 KG 母版并构建轻量级导航索引。

    KG 仅用于从检索种子单元扩展候选单元。它不替代证据判断，
    且绝不可引入 phase3 单元索引之外的 unit_id。
    """
    json_path = Path(json_path)
    print(f"[kg] 读取 KG 母版: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        kg = json.load(f)

    cp_meta: dict[str, dict[str, Any]] = {}
    unit_meta: dict[str, dict[str, Any]] = {}
    cp_to_units: dict[str, list[str]] = defaultdict(list)
    unit_to_cps: dict[str, list[str]] = defaultdict(list)
    relation_edges_by_cp: dict[str, list[dict[str, Any]]] = defaultdict(list)
    section_to_cps: dict[str, list[str]] = defaultdict(list)

    for unit in kg.get("units", []):
        uid = unit.get("unit_id", "")
        if uid:
            unit_meta[uid] = unit

    for cp in kg.get("core_points", []):
        cp_id = cp.get("core_point_id", "")
        if not cp_id:
            continue
        cp_meta[cp_id] = cp
        section_id = cp.get("section_id", "")
        if section_id:
            _append_unique(section_to_cps[section_id], cp_id)
        for key in ("key_unit_ids", "anchor_unit_ids", "support_unit_ids"):
            for uid in cp.get(key, []) or []:
                _append_unique(cp_to_units[cp_id], uid)
                _append_unique(unit_to_cps[uid], cp_id)

    relation_scopes = {
        "same_section_core_point",
        "same_chapter_core_point",
        "cross_chapter_core_point",
    }
    for edge in kg.get("edges", []):
        scope = edge.get("edge_scope", "")
        source_id = edge.get("source_id", "")
        target_id = edge.get("target_id", "")
        if scope == "core_point_unit":
            _append_unique(cp_to_units[source_id], target_id)
            _append_unique(unit_to_cps[target_id], source_id)
        elif scope == "section_core_point":
            _append_unique(section_to_cps[source_id], target_id)
        elif scope in relation_scopes:
            relation_edges_by_cp[source_id].append(edge)
            relation_edges_by_cp[target_id].append(edge)

    # 按章节/unit_order 对 core_point 下单元排序
    def unit_sort_key(uid: str) -> tuple[str, int, str]:
        meta = unit_meta.get(uid, {})
        return (
            meta.get("real_chapter") or meta.get("chapter_id", ""),
            int(meta.get("unit_order") or 0),
            uid,
        )

    for cp_id, unit_ids in list(cp_to_units.items()):
        cp_to_units[cp_id] = sorted(unit_ids, key=unit_sort_key)

    print(
        "[kg] KG 导航索引就绪"
        f" | chapters={len(kg.get('chapters', []))}"
        f" | core_points={len(cp_meta)}"
        f" | units={len(unit_meta)}"
        f" | edges={len(kg.get('edges', []))}"
    )
    return {
        "raw": kg,
        "cp_meta": cp_meta,
        "unit_meta": unit_meta,
        "cp_to_units": dict(cp_to_units),
        "unit_to_cps": dict(unit_to_cps),
        "relation_edges_by_cp": dict(relation_edges_by_cp),
        "section_to_cps": dict(section_to_cps),
    }


def _normalize_term(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _term_in_query(term: str, query: str) -> bool:
    """保守匹配 P5 术语；短拉丁文别名需词边界检查。"""
    term = _normalize_term(term)
    query = _normalize_term(query)
    if not term or not query:
        return False
    if re.fullmatch(r"[a-z0-9][a-z0-9_\-/. ]*", term):
        escaped = re.escape(term).replace(r"\ ", r"\s+")
        return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", query) is not None
    return term in query


def load_p5_alias_index(json_path: str | Path) -> dict[str, Any]:
    """加载 P5C 别名组作为外部检索辅助。"""
    json_path = Path(json_path)
    print(f"[p5] 读取 P5 术语索引: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    aliases: list[dict[str, Any]] = []
    for group in data.get("alias_groups", []) or []:
        terms: list[str] = []
        for key in ("canonical_en", "canonical_zh"):
            value = group.get(key, "")
            if value:
                terms.append(value)
        for key in ("aliases_en", "aliases_zh", "all_terms"):
            terms.extend(group.get(key, []) or [])
        normalized_terms = sorted(
            {_normalize_term(t) for t in terms if len(_normalize_term(t)) >= 2},
            key=len,
            reverse=True,
        )
        unit_ids = [uid for uid in group.get("evidence_unit_ids", []) or [] if uid]
        if normalized_terms and unit_ids:
            aliases.append(
                {
                    "alias_group_id": group.get("alias_group_id", ""),
                    "canonical_en": group.get("canonical_en", ""),
                    "canonical_zh": group.get("canonical_zh", ""),
                    "terms": normalized_terms,
                    "unit_ids": unit_ids,
                    "alias_scope": group.get("alias_scope", ""),
                }
            )

    print(f"[p5] P5 术语索引就绪 | alias_groups={len(aliases)}")
    return {"aliases": aliases, "raw": data}


# ── API 配置 ──────────────────────────────────────────────────────────


def get_llm_config() -> tuple[str, str, str]:
    """获取 LLM API 配置：api_key, base_url, env_name。"""
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = (
                os.environ.get("DEEPSEEK_BASE_URL")
                or os.environ.get("DS_BASE_URL")
                or DEFAULT_DEEPSEEK_BASE_URL
            )
            return value, base_url, env_name
    names = " / ".join(API_KEY_ENV_NAMES)
    raise RuntimeError(f"{names} 环境变量均未设置，不能调用 LLM API。")


# ── 查询构建 ──────────────────────────────────────────────────────────


def build_queries(
    question: dict[str, Any],
) -> tuple[str, str | None]:
    """构建供 P5 和 KG 相关度计算使用的整题查询。

    返回:
        query_zh: 中文查询 (stem + options)
        query_en: 英文查询 (stem_en + options_en)，若无 stem_en 则返回 None
    """
    stem = question.get("stem", "")
    options = question.get("options", {})
    opt_text = " ".join(options.values())
    query_zh = f"{stem} {opt_text}".strip()

    stem_en = question.get("stem_en", "")
    if not stem_en:
        return query_zh, None

    options_en = question.get("options_en", {})
    opt_en_text = " ".join(options_en.values())
    query_en = f"{stem_en} {opt_en_text}".strip()
    return query_zh, query_en


def build_retrieval_heads(question: dict[str, Any]) -> list[dict[str, Any]]:
    """构建正式直接召回使用的题干和题干加单选项检索头。"""
    heads: list[dict[str, Any]] = []
    stem = str(question.get("stem", "") or "").strip()
    stem_en = str(question.get("stem_en", "") or "").strip()
    options = question.get("options", {}) or {}
    options_en = question.get("options_en", {}) or {}

    if stem:
        heads.append(
            {
                "head_id": "stem_zh",
                "head_kind": "stem",
                "option": None,
                "language": "zh",
                "query": stem,
            }
        )
    for label, text in options.items():
        query = f"{stem} {text}".strip()
        if query:
            heads.append(
                {
                    "head_id": f"option_{label}_zh",
                    "head_kind": "option",
                    "option": str(label),
                    "language": "zh",
                    "query": query,
                }
            )

    if stem_en:
        heads.append(
            {
                "head_id": "stem_en",
                "head_kind": "stem",
                "option": None,
                "language": "en",
                "query": stem_en,
            }
        )
    for label, text in options_en.items():
        query = f"{stem_en} {text}".strip()
        if query:
            heads.append(
                {
                    "head_id": f"option_{label}_en",
                    "head_kind": "option",
                    "option": str(label),
                    "language": "en",
                    "query": query,
                }
            )
    return heads


def build_option_only_heads(question: dict[str, Any]) -> list[dict[str, Any]]:
    """构建不含题干的中英文单选项补充检索头。"""
    heads: list[dict[str, Any]] = []
    for language, field in (("zh", "options"), ("en", "options_en")):
        for label, text in (question.get(field, {}) or {}).items():
            query = str(text or "").strip()
            if not query:
                continue
            heads.append(
                {
                    "head_id": f"option_only_{label}_{language}",
                    "head_kind": "option_only_supplement",
                    "option": str(label),
                    "language": language,
                    "query": query,
                }
            )
    return heads


def aggregate_option_supplements(
    retrieval_rows: list[dict[str, Any]],
    unit_lookup: dict[str, dict[str, Any]],
    excluded_unit_ids: set[str],
    per_option_limit: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    """按选项对 option-only 命中做确定性 RRF 汇总。"""
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in retrieval_rows:
        option = str(row.get("option", "") or "").strip().upper()
        uid = str(row.get("unit_id", "") or "").strip()
        if option and uid and uid not in excluded_unit_ids and uid in unit_lookup:
            grouped[option][uid].append(row)

    result: dict[str, list[dict[str, Any]]] = {}
    for option, by_uid in sorted(grouped.items()):
        ranked: list[dict[str, Any]] = []
        for uid, rows in by_uid.items():
            hits = [
                {
                    "head_id": row["head_id"],
                    "language": row["language"],
                    "route": row["route"],
                    "rank": int(row.get("rank") or 0),
                    "raw_score": row.get("raw_score", row.get("score", 0.0)),
                    "query": row.get("query", ""),
                }
                for row in rows
            ]
            hits.sort(key=lambda hit: (hit["rank"], hit["head_id"], hit["route"]))
            routes = sorted({hit["route"] for hit in hits})
            languages = sorted({hit["language"] for hit in hits})
            fusion_score = sum(
                1.0 / (60 + int(hit.get("rank") or 1)) for hit in hits
            )
            best_rank = min(int(hit.get("rank") or 999999) for hit in hits)
            unit = unit_lookup[uid]
            ranked.append(
                {
                    "unit_id": uid,
                    "knowledge_zh": unit.get("knowledge_zh", ""),
                    "knowledge_en": unit.get("knowledge_en", ""),
                    "en_quote": unit.get("en_quote", ""),
                    "heading_context": unit.get("heading_context", []),
                    "type": unit.get("type", ""),
                    "supplement_only": True,
                    "fusion_score": round(fusion_score, 8),
                    "routes": routes,
                    "languages": languages,
                    "best_rank": best_rank,
                    "retrieval_hits": hits,
                }
            )
        ranked.sort(
            key=lambda row: (
                -float(row["fusion_score"]),
                -len(row["routes"]),
                -len(row["languages"]),
                int(row["best_rank"]),
                row["unit_id"],
            )
        )
        result[option] = ranked[: max(0, per_option_limit)]
    return result


def retrieve_option_supplements(
    question: dict[str, Any],
    bge_vecs: np.ndarray,
    card_ids: list[str],
    unit_lookup: dict[str, dict[str, Any]],
    bm25_zh_index: BM25,
    bm25_en_index: BM25,
    excluded_unit_ids: set[str],
    top_k: int = 20,
    per_option_limit: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    """执行 option-only BGE/BM25 补召回，不参与主池或 KG 扩展。"""
    heads = build_option_only_heads(question)
    retrieval_rows: list[dict[str, Any]] = []

    if heads:
        model = get_bge_model()
        vectors = model.encode(
            [head["query"] for head in heads], normalize_embeddings=True
        )
        similarities = cosine_similarity(vectors, bge_vecs)
        for head, scores in zip(heads, similarities):
            for rank, idx in enumerate(np.argsort(scores)[::-1][:top_k], start=1):
                retrieval_rows.append(
                    {
                        **head,
                        "route": "bge",
                        "rank": rank,
                        "raw_score": round(float(scores[idx]), 6),
                        "unit_id": card_ids[idx],
                    }
                )

    for head in heads:
        if head["language"] == "en":
            bm25_index = bm25_en_index
            route = "bm25_en"
        else:
            bm25_index = bm25_zh_index
            route = "bm25_zh"
        for row in bm25_search(
            head["query"], bm25_index, card_ids, unit_lookup, top_k
        ):
            retrieval_rows.append(
                {
                    **head,
                    "route": route,
                    "rank": int(row["rank"]),
                    "raw_score": float(row["score"]),
                    "unit_id": row["unit_id"],
                }
            )

    return aggregate_option_supplements(
        retrieval_rows,
        unit_lookup,
        excluded_unit_ids,
        per_option_limit=per_option_limit,
    )


def select_head_balanced_candidates(
    merged: list[dict[str, Any]],
    heads: list[dict[str, Any]],
    limit: int,
    per_head_minimum: int = 2,
) -> list[dict[str, Any]]:
    """先保证各检索头的候选覆盖，再按全局融合排名补足候选池。"""
    if limit <= 0:
        return []

    selected_ids: set[str] = set()
    for _ in range(per_head_minimum):
        for head in heads:
            if len(selected_ids) >= limit:
                break
            head_id = head["head_id"]
            ranked: list[tuple[float, float, str, dict[str, Any]]] = []
            for candidate in merged:
                hits = [
                    hit
                    for hit in candidate.get("retrieval_hits", [])
                    if hit.get("head_id") == head_id
                ]
                if not hits:
                    continue
                head_score = sum(
                    1.0 / (60 + int(hit.get("rank") or 1)) for hit in hits
                )
                best_raw = max(float(hit.get("raw_score") or 0.0) for hit in hits)
                ranked.append(
                    (head_score, best_raw, candidate["unit_id"], candidate)
                )
            ranked.sort(key=lambda row: (-row[0], -row[1], row[2]))
            for _, _, uid, _candidate in ranked:
                if uid not in selected_ids:
                    selected_ids.add(uid)
                    break

    # 从全局剩余候选补足达到 limit
    for candidate in merged:
        if len(selected_ids) >= limit:
            break
        selected_ids.add(candidate["unit_id"])

    return [
        candidate for candidate in merged if candidate["unit_id"] in selected_ids
    ][:limit]


# ── BGE 模型（全局单例） ─────────────────────────────────────────────

_BGE_MODEL: Any = None


def get_bge_model() -> Any:
    """延迟加载 BGE-M3 模型，全局复用。"""
    global _BGE_MODEL
    if _BGE_MODEL is not None:
        return _BGE_MODEL
    print("[bge] 加载 BGE-M3 编码模型 ...")
    from sentence_transformers import SentenceTransformer

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    _BGE_MODEL = SentenceTransformer(
        "BAAI/bge-m3", local_files_only=True
    )
    dim = _BGE_MODEL.get_embedding_dimension()
    print(f"[bge] BGE-M3 就绪 | dim={dim}")
    return _BGE_MODEL


# ── 检索函数 ──────────────────────────────────────────────────────────


def bge_search(
    query: str,
    bge_vecs: np.ndarray,
    card_ids: list[str],
    unit_lookup: dict[str, dict],
    top_k: int = 20,
) -> list[dict[str, Any]]:
    """BGE-M3 余弦相似度检索。"""
    if not query.strip():
        return []

    model = get_bge_model()
    q_vec = model.encode([query], normalize_embeddings=True)
    sims = cosine_similarity(q_vec, bge_vecs)[0]

    top_indices = np.argsort(sims)[::-1][:top_k]
    results = []
    for rank, idx in enumerate(top_indices, start=1):
        cid = card_ids[idx]
        unit = unit_lookup.get(cid, {})
        results.append(
            {
                "rank": rank,
                "score": round(float(sims[idx]), 6),
                "unit_id": cid,
                "knowledge_zh": unit.get("knowledge_zh", ""),
                "knowledge_en": unit.get("knowledge_en", ""),
                "en_quote": unit.get("en_quote", ""),
                "heading_context": unit.get("heading_context", []),
                "type": unit.get("type", ""),
            }
        )
    return results


def bm25_search(
    query: str,
    bm25_index: BM25,
    card_ids: list[str],
    unit_lookup: dict[str, dict],
    top_k: int = 20,
) -> list[dict[str, Any]]:
    """BM25 检索。"""
    if not query.strip():
        return []
    results = bm25_index.search(query, top_k=top_k)
    rows = []
    for rank, (doc_idx, score) in enumerate(results, start=1):
        cid = card_ids[doc_idx]
        unit = unit_lookup.get(cid, {})
        rows.append(
            {
                "rank": rank,
                "score": round(score, 6),
                "unit_id": cid,
                "knowledge_zh": unit.get("knowledge_zh", ""),
                "knowledge_en": unit.get("knowledge_en", ""),
                "en_quote": unit.get("en_quote", ""),
                "heading_context": unit.get("heading_context", []),
                "type": unit.get("type", ""),
            }
        )
    return rows


def _candidate_from_unit(
    unit_id: str,
    unit_lookup: dict[str, dict],
    route: str,
    score: float,
    kg_info: dict[str, Any],
) -> dict[str, Any] | None:
    """从 unit_lookup 构建统一的候选记录。"""
    unit = unit_lookup.get(unit_id)
    if not unit:
        return None
    return {
        "unit_id": unit_id,
        "knowledge_zh": unit.get("knowledge_zh", ""),
        "en_quote": unit.get("en_quote", ""),
        "knowledge_en": unit.get("knowledge_en", ""),
        "heading_context": unit.get("heading_context", []),
        "type": unit.get("type", ""),
        "route": route,
        "score": round(score, 6),
        "kg": kg_info,
    }


def _relation_route(edge_scope: str) -> str:
    """将 KG 边作用域映射为候选路由标签。"""
    if edge_scope == "same_section_core_point":
        return "kg_same_section_cp"
    if edge_scope == "same_chapter_core_point":
        return "kg_same_chapter_cp"
    if edge_scope == "cross_chapter_core_point":
        return "kg_cross_chapter_cp"
    return "kg_related_cp"


def _normalize_route_scores(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """路由内分数归一化，使异构检索器可以合并。"""
    if not records:
        return []
    scores = [float(r.get("score") or 0.0) for r in records]
    min_score = min(scores)
    max_score = max(scores)
    out: list[dict[str, Any]] = []
    for r in records:
        rank = int(r.get("rank") or 0)
        if max_score > min_score:
            norm = (float(r.get("score") or 0.0) - min_score) / (max_score - min_score)
        else:
            norm = 1.0 if float(r.get("score") or 0.0) > 0 else 0.0
        rank_boost = 1.0 / (rank + 1.0) if rank else 0.0
        row = dict(r)
        row["raw_score"] = round(float(r.get("score") or 0.0), 6)
        row["score"] = round((0.85 * norm) + (0.15 * rank_boost), 6)
        out.append(row)
    return out


def p5_canonical_inline(
    query: str,
    p5_index: dict[str, Any] | None,
    lang: str = "zh",
) -> str:
    """s0c 规范内联：在 query 中为匹配到的术语插入规范名括号注释。

    例如 "FATF的40项建议" -> "FATF（金融行动特别工作组）的40项建议"
    不直接拉 unit，不改变后续 BGE/BM25 检索流程。
    """
    if not p5_index or not query.strip():
        return query
    haystack = _normalize_term(query)
    hits: list[tuple[int, int, str, str]] = []  # (start, end, canonical, scope)
    for group in p5_index.get("aliases", []) or []:
        for term in group.get("terms", []):
            term_norm = _normalize_term(term)
            if not term_norm or len(term_norm) < 2:
                continue
            # 找 term 在 query 中的位置（忽略 "()" 内已有的注释，避免重复内联）
            start = haystack.find(term_norm)
            while start >= 0:
                canonical = group.get("canonical_zh", "") or group.get("canonical_en", "")
                if not canonical:
                    break
                # 不要把已有括号注释再包一层
                prefix = haystack[max(0, start - 1):start]
                suffix = haystack[start + len(term_norm):start + len(term_norm) + 1]
                if prefix != "（" and suffix != "）":
                    hits.append((start, start + len(term_norm), canonical, group.get("alias_scope", "")))
                start = haystack.find(term_norm, start + 1)
    if not hits:
        return query
    # 唯一去重：同位置只留一个最长规范名
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    selected: list[tuple[int, int, str]] = []
    for h in hits:
        if not selected or h[0] > selected[-1][1]:
            selected.append((h[0], h[1], h[2]))
    # 从后往前插入，保持位置偏移正确
    result = query
    for start, end, canonical in reversed(selected):
        result = result[:end] + f"（{canonical}）" + result[end:]
    return result


# 语义强边：KG 图边 reason 为空时，回填中文含义供 LLM 理解
SEMANTIC_FORCE_REASONS = {
    "grounds": "奠基关系——定义/框架是判断前置条件，不拉即残缺",
    "illustrates": "案例与定义互补——种子在案例则拉定义，种子在定义则拉案例",
    "contrasts": "易混淆对照——池子里只有一边就补另一边，供 LLM 区分",
}


def expand_with_kg(
    direct_candidates: list[dict[str, Any]],
    kg_index: dict[str, Any] | None,
    unit_lookup: dict[str, dict],
    query_zh: str = "",
    query_en: str | None = None,
    max_extra: int = 30,
    seed_limit: int = 20,
    per_seed_limit: int = 3,
) -> list[dict[str, Any]]:
    """通过 KG core-point 邻域扩展检索种子单元。"""
    if not kg_index or max_extra <= 0:
        return []

    cp_to_units: dict[str, list[str]] = kg_index["cp_to_units"]
    unit_to_cps: dict[str, list[str]] = kg_index["unit_to_cps"]
    cp_meta: dict[str, dict[str, Any]] = kg_index["cp_meta"]
    relation_edges_by_cp: dict[str, list[dict[str, Any]]] = kg_index[
        "relation_edges_by_cp"
    ]

    query_tokens = set(tokenize(f"{query_zh} {query_en or ''}"))
    existing = {c["unit_id"] for c in direct_candidates}
    proposed: dict[str, dict[str, Any]] = {}

    # 路由权重：同核心点 > 同节 > 同章 > 跨章 > 其他
    route_weight = {
        "kg_same_core_point": 1.0,
        "kg_same_section_cp": 0.86,
        "kg_same_chapter_cp": 0.72,
        "kg_cross_chapter_cp": 0.62,
        "kg_related_cp": 0.55,
    }

    def text_relevance(unit: dict[str, Any]) -> float:
        """计算查询与单元文本的 token 重叠度。"""
        tokens = set(
            tokenize(
                " ".join(
                    [
                        unit.get("knowledge_zh", ""),
                        unit.get("knowledge_en", ""),
                        unit.get("en_quote", ""),
                        " ".join(unit.get("heading_context", []) or []),
                    ]
                )
            )
        )
        if not query_tokens or not tokens:
            return 0.0
        overlap = len(query_tokens & tokens)
        return min(overlap / max(len(query_tokens), 1), 1.0)

    def add_unit(
        uid: str,
        route: str,
        seed: dict[str, Any],
        source_cp_id: str,
        target_cp_id: str,
        edge: dict[str, Any] | None = None,
    ) -> None:
        """将单元加入候选并记录 KG 导航元数据。"""
        if uid in existing or uid == seed["unit_id"]:
            return
        unit = unit_lookup.get(uid)
        if not unit:
            return
        target_cp = cp_meta.get(target_cp_id, {})
        source_cp = cp_meta.get(source_cp_id, {})
        seed_score = float(seed.get("score") or 0.0)
        relevance = text_relevance(unit)
        kg_info = {
            "source_seed_unit_id": seed["unit_id"],
            "source_core_point_id": source_cp_id,
            "source_core_point_title_zh": source_cp.get("title_zh", ""),
            "target_core_point_id": target_cp_id,
            "target_core_point_title_zh": target_cp.get("title_zh", ""),
            "text_relevance": round(relevance, 6),
        }
        if edge:
            kg_info.update(
                {
                    "edge_id": edge.get("edge_id", ""),
                    "edge_scope": edge.get("edge_scope", ""),
                    "relation_type": edge.get("relation_type", ""),
                    "reason": edge.get("reason", "") or SEMANTIC_FORCE_REASONS.get(
                        edge.get("relation_type", ""), ""
                    ),
                }
            )
        # 候选得分 = 种子得分 × 0.48 + 路由权重 × 0.32 + 文本相关度 × 0.20
        score = (
            seed_score * 0.48
            + route_weight.get(route, 0.55) * 0.32
            + relevance * 0.20
        )
        candidate = _candidate_from_unit(uid, unit_lookup, route, score, kg_info)
        if candidate:
            candidate["kg"]["seed_score"] = round(seed_score, 6)
            existing_candidate = proposed.get(uid)
            if not existing_candidate or candidate["score"] > existing_candidate["score"]:
                proposed[uid] = candidate

    # 优先以 bge/bm25 直接命中为种子，不足时补充其他路由
    seed_candidates = [
        c for c in direct_candidates
        if c.get("route") in {"bge", "bm25_zh", "bm25_en"}
    ]
    if len(seed_candidates) < seed_limit:
        seed_candidates.extend(
            c for c in direct_candidates
            if c.get("route") not in {"bge", "bm25_zh", "bm25_en"}
        )

    for seed in seed_candidates[:seed_limit]:
        seed_added_before = len(proposed)
        seed_uid = seed["unit_id"]
        for cp_id in unit_to_cps.get(seed_uid, [])[:3]:
            # 第一步：同 core_point 内的兄弟单元
            for uid in cp_to_units.get(cp_id, [])[:10]:
                add_unit(uid, "kg_same_core_point", seed, cp_id, cp_id)
                if len(proposed) - seed_added_before >= per_seed_limit:
                    break
            if len(proposed) - seed_added_before >= per_seed_limit:
                break

            # 第二步：关联 core_point 下的单元
            for edge in relation_edges_by_cp.get(cp_id, [])[:6]:
                other_cp_id = (
                    edge.get("target_id")
                    if edge.get("source_id") == cp_id
                    else edge.get("source_id")
                )
                route = _relation_route(edge.get("edge_scope", ""))
                for uid in cp_to_units.get(other_cp_id, [])[:4]:
                    add_unit(uid, route, seed, cp_id, other_cp_id, edge=edge)
                    if len(proposed) - seed_added_before >= per_seed_limit:
                        break
                if len(proposed) - seed_added_before >= per_seed_limit:
                    break

            # 第三步：同 section 内其他 core_point 下的单元（不受 KG 边限制）
            section_id = cp_meta.get(cp_id, {}).get("section_id", "")
            for other_cp_id in kg_index["section_to_cps"].get(section_id, [])[:5]:
                if other_cp_id == cp_id:
                    continue
                for uid in cp_to_units.get(other_cp_id, [])[:3]:
                    add_unit(uid, "kg_same_section_cp", seed, cp_id, other_cp_id)
                    if len(proposed) - seed_added_before >= per_seed_limit:
                        break
                if len(proposed) - seed_added_before >= per_seed_limit:
                    break

    extras = list(proposed.values())
    extras.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return extras[:max_extra]


# ── 对一道题执行三路检索并合并去重 ────────────────────────────────────


def search_and_merge(
    question: dict[str, Any],
    bge_vecs: np.ndarray,
    card_ids: list[str],
    unit_lookup: dict[str, dict],
    bm25_zh_index: BM25,
    bm25_en_index: BM25,
    top_k: int = 20,
    merge_top_k: int = 30,
    kg_index: dict[str, Any] | None = None,
    kg_max_extra: int = 30,
    p5_index: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """按题干/单选项分头直接召回，合并去重后执行可选 KG 扩展。

    返回的每条记录包含: unit_id, knowledge_zh, en_quote, knowledge_en,
    heading_context, type, route, score；直接命中还保留 retrieval_hits。
    """
    heads = build_retrieval_heads(question)
    query_zh, query_en = build_queries(question)
    route_map: dict[str, list[dict]] = {}

    # 0. s0c P5 规范内联：改写 query，插入规范名括号注释
    if p5_index is not None:
        for head in heads:
            head["query"] = p5_canonical_inline(head["query"], p5_index, lang=head["language"])

    # 1. 所有中文/英文检索头批量执行 BGE，避免逐头重复编码
    if heads:
        model = get_bge_model()
        query_vectors = model.encode(
            [head["query"] for head in heads], normalize_embeddings=True
        )
        similarities = cosine_similarity(query_vectors, bge_vecs)
        for head, scores in zip(heads, similarities):
            top_indices = np.argsort(scores)[::-1][:top_k]
            rows: list[dict[str, Any]] = []
            for rank, idx in enumerate(top_indices, start=1):
                uid = card_ids[idx]
                unit = unit_lookup.get(uid, {})
                rows.append(
                    {
                        "rank": rank,
                        "score": round(float(scores[idx]), 6),
                        "unit_id": uid,
                        "knowledge_zh": unit.get("knowledge_zh", ""),
                        "knowledge_en": unit.get("knowledge_en", ""),
                        "en_quote": unit.get("en_quote", ""),
                        "heading_context": unit.get("heading_context", []),
                        "type": unit.get("type", ""),
                    }
                )
            for row in _normalize_route_scores(rows):
                row.update(
                    {
                        "route": "bge",
                        "head_id": head["head_id"],
                        "head_kind": head["head_kind"],
                        "option": head["option"],
                        "language": head["language"],
                    }
                )
                route_map.setdefault(row["unit_id"], []).append(row)

    # 2. 中文头只跑中文 BM25，英文头只跑英文 BM25
    for head in heads:
        if head["language"] == "en":
            bm25_index = bm25_en_index
            route = "bm25_en"
        else:
            bm25_index = bm25_zh_index
            route = "bm25_zh"
        rows = _normalize_route_scores(
            bm25_search(head["query"], bm25_index, card_ids, unit_lookup, top_k)
        )
        for row in rows:
            row.update(
                {
                    "route": route,
                    "head_id": head["head_id"],
                    "head_kind": head["head_kind"],
                    "option": head["option"],
                    "language": head["language"],
                }
            )
            route_map.setdefault(row["unit_id"], []).append(row)

    # 合并去重：用确定性 RRF 汇总各检索头，同时保留原始分数和排名
    merged: list[dict[str, Any]] = []
    for uid, records in route_map.items():
        best = max(records, key=lambda x: x["score"])
        retrieval_hits = [
            {
                "head_id": row["head_id"],
                "head_kind": row["head_kind"],
                "option": row["option"],
                "language": row["language"],
                "route": row["route"],
                "rank": int(row.get("rank") or 0),
                "raw_score": row.get("raw_score", row.get("score", 0.0)),
            }
            for row in records
            if row.get("head_id")
        ]
        retrieval_hits.sort(
            key=lambda hit: (hit["rank"], hit["head_id"], hit["route"])
        )
        fusion_score = sum(
            1.0 / (60 + int(row.get("rank") or 1)) for row in records
        )
        merged.append(
            {
                "unit_id": uid,
                "knowledge_zh": best.get("knowledge_zh", ""),
                "en_quote": best.get("en_quote", ""),
                "knowledge_en": best.get("knowledge_en", ""),
                "heading_context": best.get("heading_context", []),
                "type": best.get("type", ""),
                "route": best["route"],
                "score": best["score"],
                "raw_score": best.get("raw_score", best.get("score", 0.0)),
                "fusion_score": round(fusion_score, 8),
                "retrieval_hits": retrieval_hits,
            }
        )
        if best.get("p5"):
            merged[-1]["p5"] = best["p5"]

    # 按跨检索头融合分数排序，稳定保留被多个头共同支持的单元
    merged.sort(
        key=lambda x: (
            -float(x["fusion_score"]),
            -float(x["score"]),
            x["unit_id"],
        )
    )
    direct_candidates = select_head_balanced_candidates(
        merged, heads, merge_top_k
    )

    kg_candidates = expand_with_kg(
        direct_candidates,
        kg_index=kg_index,
        unit_lookup=unit_lookup,
        query_zh=query_zh,
        query_en=query_en,
        max_extra=kg_max_extra,
    )
    return direct_candidates + kg_candidates


# ── 构建裁判 prompt ───────────────────────────────────────────────────


_TYPE_LABELS: dict[str, str] = {
    "definition": "概念定义",
    "rule": "规则/规定",
    "case": "案例",
    "fact": "事实陈述",
    "process": "流程描述",
    "risk_indicator": "风险指标",
    "classification": "分类说明",
    "context": "背景信息",
}


def format_candidates(candidates: list[dict[str, Any]]) -> str:
    """将候选池格式化为 ±4 上下文连续块，同 section 内按教材顺序展示。"""
    lines: list[str] = []
    candidate_ids = {c["unit_id"] for c in candidates}

    # CP 关系去重摘要
    cp_rels: dict[tuple[str, str, str], str] = {}
    for c in candidates:
        kg_info = c.get("kg") or {}
        rel = kg_info.get("relation_type", "")
        if not rel:
            continue
        src = kg_info.get("source_core_point_id", "")
        tgt = kg_info.get("target_core_point_id", "")
        if src and tgt:
            key = (src, tgt, rel)
            if key not in cp_rels:
                cp_rels[key] = kg_info.get("reason", "")

    if cp_rels:
        lines.append("[CP 边关系 — 以下 unit 按 KG 语义边召回]")
        for (src, tgt, rel), reason in cp_rels.items():
            reason_str = f"（{reason}）" if reason else ""
            lines.append(f"  {src} --{rel}--> {tgt} {reason_str}")
        lines.append("")

    # 按 ±4 上下文块展示，去重
    shown_ctx: set[tuple[str, int]] = set()
    candidate_units = {c["unit_id"]: c for c in candidates}

    for c in candidates:
        uid = c["unit_id"]
        ctx_cards = _section_context_cards(uid, candidate_ids)
        if not ctx_cards:
            lines.append(f"[知识单元] {uid}")
            lines.append(f"  中文: {c.get('knowledge_zh', '')}")
            en = c.get("en_quote", "") or c.get("knowledge_en", "")
            if en:
                lines.append(f"  英文: {en}")
            lines.append("  " + "-" * 60)
            continue

        section_key = ctx_cards[0].get("real_section", "")
        center_order = next(
            (card["unit_order"] for card in ctx_cards if card["is_center"]), 0
        )
        ctx_key = (section_key, center_order)

        if ctx_key in shown_ctx:
            continue
        shown_ctx.add(ctx_key)
        lines.append(_format_context_block(ctx_cards))

    return "\n".join(lines)


def format_option_supplements(
    question: dict[str, Any],
    supplement_pool: dict[str, list[dict[str, Any]]],
) -> str:
    """按选项渲染仅供语义核验的补召回候选。"""
    lines: list[str] = []
    options = question.get("options", {}) or {}
    options_en = question.get("options_en", {}) or {}
    for label in options:
        rows = supplement_pool.get(str(label).upper(), []) or []
        lines.append(
            f"[选项 {label} 补充候选] 中文={options.get(label, '')}"
            f" | 英文={options_en.get(label, '')}"
        )
        if not rows:
            lines.append("  无")
            continue
        for row in rows:
            type_label = _TYPE_LABELS.get(str(row.get("type", "") or "").strip(), "")
            lines.append(f"  - unit_id: {row['unit_id']}")
            if type_label:
                lines.append(f"    教材类型: {type_label}")
            if row.get("knowledge_zh"):
                lines.append(f"    中文: {row['knowledge_zh']}")
            en = row.get("en_quote") or row.get("knowledge_en", "")
            if en:
                lines.append(f"    英文: {en}")
            hit_text = ", ".join(
                f"{hit['head_id']}/{hit['route']}/rank={hit['rank']}"
                for hit in row.get("retrieval_hits", [])
            )
            lines.append(f"    补召回路径: {hit_text}")
    return "\n".join(lines)


def build_prompt(
    question: dict[str, Any],
    candidates: list[dict[str, Any]],
    supplement_pool: dict[str, list[dict[str, Any]]] | None = None,
) -> str:
    """构建裁判 prompt，不包含参考答案。"""
    stem = question.get("stem", "")
    options = question.get("options", {})
    stem_en = question.get("stem_en", "")
    options_en = question.get("options_en", {})
    qtype = question.get("question_type", "single")
    qtype_label = "单选题" if qtype == "single" else "多选题"

    opt_lines = "\n".join(f"  {k}: {v}" for k, v in options.items())
    opt_en_lines = "\n".join(
        f"  {k}: {options_en.get(k, '')}" for k in options if options_en.get(k)
    )
    stem_en_str = f"\n英文题干: {stem_en}" if stem_en else ""
    opt_en_str = f"\n英文选项:\n{opt_en_lines}" if opt_en_lines else ""
    candidates_text = format_candidates(candidates)
    supplements_text = format_option_supplements(
        question, supplement_pool or {}
    )

    prompt = f"""你是一个 CAMS 反洗钱考试题目裁判。你需要判断每道题的每个选项是否正确。

### 题目信息
题干: {stem}{stem_en_str}
选项:
{opt_lines}{opt_en_str}
题型: {qtype_label}

**注意**：本题来自英文考试，中文为翻译版本。当中文翻译与英文原意的强弱、边界不一致时（如英文为模糊边缘行为而中文译为明确违法），以英文为准进行判断。

### 教材证据
以下是教材中与本题相关的知识单元（候选池），请基于这些单元判断每个选项：
其中 `KG导航` 只表示该单元与检索命中的单元在教材知识图谱中同属或相邻；它不是答案依据。最终判断必须回到知识单元的中英文原文。

{candidates_text}

### 单选项独立补充候选
以下内容由单个选项独立召回，只表示"可能与该选项概念相关"，不是已经成立的证据：
- 只有当某个 unit 同时解释选项含义及其与本题题干的关系时，才能引用。
- 不得因为某个选项没有补充候选就判定该选项错误。
- 不得引用仅因同词异义、翻译偏差或宽泛词命中的 unit。
- 补充候选不会自动改变答案；必须回到教材中英文原文做判断。

{supplements_text}

### 材料类型与推理权重
每个知识单元标注了"教材类型"，请在引用时按以下权重推理：

**概念定义/规则规定（最高权重）**
- 从中提取必要条件和边界，做演绎推理。
- 只有定义/规则中的条件才能用于"不满足条件即排除选项"。
- 推理链条必须是：定义条件 → 选项文本是否满足 → 结论。

**核心区分/分类说明**
- 用于判断选项属于哪个类别、区分相近概念。
- 两个概念的核心区别必须直接从分类说明中提取，不得用案例中的伴随特征来区分。

**事实陈述/常见表现（辅助，不可独立排除）**
- 描述的是"通常怎样"，不是"必须怎样"。
- 可与定义互相印证，但不能单独作为排除选项的唯一依据。

**案例（最低权重，仅作辅助）**
- 案例中的具体数字、地点、行为方式属于该案例的特殊情节。
- 不得将案例中的具体特征上升为普遍定义或判断标准。
- 案例只能用于帮助理解概念在具体场景中的表现，不能参与"不满足X条件"的演绎推理。

**教材特点说明**
本教材常将概念区分放在案例对比中，而非给出字典式定义。相近概念的划分标准可能只在案例中体现。当教材没有为某个概念提供独立的普遍定义时：
- 可以从案例对比中提取区分信息进行辨析，但需说明"教材案例表现为……教材未给出严格、普遍的划分标准"。
- 不得因教材未给出普遍标准就直接否定概念存在或判定 insufficient。
- 教材的"定义"声明（如 Microstructuring resembles traditional structuring but is typically used with digital asset laundering）即使简短，也应被视为该概念最权威的直接依据。

**风险指标/流程描述**
- 用于匹配题干行为是否符合指标或流程。
- 指出题干行为是否符合该指标即可，不要求建立因果链条。

**条件性概念的表述**
教材中某些概念本身具有条件性或场景差异（如 placement 可表现为存款、购买资产等多种形式；房地产快速转售可能兼具 layering 和 integration 特征）。对于这类概念：
- 不得为了凸显正确答案而将某一种表现描述为唯一对应关系。
- 应说明"该行为在什么条件下可能属于X阶段"，再结合题干指出"本题没有提供哪些条件，因此更符合Y"。
- 严禁机械断言"购买资产一定是 placement""信托一定隐藏所有权"等绝对化判断。

**语境有效性（强制检查 —— 违反将导致证据失效）**
引用 unit 前，必须完成以下三项检查，缺一不可：

1. **主语一致性**：证据的主语/对象必须与结论的主语一致。
   - 证据讲的是"银行"的规则，不能直接套用到"赌场"。
   - 证据讲的是"PSP（支付服务提供商）"的业务特征，不能当作"MSB 客户"的风险信号。
   - 证据讲的是"私营部门间（银行对银行）"的信息共享，不能当作"公私合作（PPP）"的益处。
   - 判定方法：把证据原文的主语写出来，把结论的主语写出来，两者必须一致或存在教材明确声明的等价关系。

2. **时间节点/业务阶段匹配**：证据所处的业务阶段必须与题干场景的阶段一致。
   - 证据来自"S​​AR 提交后维持账户"章节，不能用来证明"客户开户时"应实施的控制。
   - 证据来自"持续尽调（ongoing due diligence）"章节，不能用来证明"首次准入（onboarding）"的流程。
   - 证据来自"调查结束后"的处置，不能用来证明"发现可疑信号时"的第一步操作。
   - 判定方法：读出证据的章节路径，确认章节描述的业务阶段（准入/持续监控/调查/报告后/退出），与题干问的时间节点对比。

3. **场景限定**：若证据来自特定场景（如大使馆、外交使团、某具体案例、某类机构），该 unit 的陈述只在该场景下有效，不能当作跨场景的普遍原则使用。来自 CH01 等通用章节的定义除外。案例中的具体数字、地点、行为方式属于该案例的特殊情节，不得将其上升为普遍定义或判断标准。

### 输出要求
以 JSON 格式输出，不要包含其他内容。文本值中引用原文词汇时使用中文引号「」或单引号''，不得使用 ASCII 双引号""（会破坏 JSON 结构）：
- 先选择整题的 `decision_framework.type`：
  - `is_definition`：定义、类别或"哪些属于"题。必须先引用定义或明确分类规则，提取 `required_conditions`，再把规则逐项应用到选项。
  - `is_domain`：询问某一特定领域、计划或产品的警示信号。必须先建立领域边界，再区分"通用风险/通用渠道"和"该领域特有信号"。
  - `is_scenario`：其余场景匹配题。必须从题干事实与教材规则之间建立对应关系。
- 定义/类别题不得用"教材没有列举该选项"直接证明选项错误；只有引用材料明确给出穷尽分类时，未列入才可作为分类依据。
- 必须按选项和题干原文判断，不得补充题干或选项没有提供的特殊事实、动机、后果或运作机制。严禁"语义贪污"——题干写"低于"不得写成"略低于"，写"一个账户"不得写成"跨账户"，写"支付发票"不得写成"虚假发票"。题干没用程度副词你也不能用，题干没写的结构特征你不能补。
- 定义应用必须区分"选项明确违反必要条件"和"题目没有提供该条件"。只有前者可以据定义判错并使用 `definition_application`；仅仅没有写出某个条件，不能证明选项错误，应标为 `insufficient`，除非教材给出了明确穷尽分类或题干事实可直接排除。
  排除选项时必须使用演绎逻辑：列出必要条件 → 指出选项文本缺少哪个条件 → 结论"不满足条件"。不得使用"通常""一般""往往"等概率措辞。
  示例——"上游犯罪的必要条件是产生非法收益（v7u_N000017）。选项X是暴力人身犯罪，题干未提供其产生非法收益的信息，不满足必要条件，因此不构成上游犯罪。"
- `required_conditions` 只是逐项核对规则，不允许据此推测选项通常具有或不具有题目未说明的动机、收益、伤害程度或附加情境。
- 特定领域题中，"某工具一般存在洗钱风险"不等于"该工具是题目所问领域的特有警示信号"。
- `domain_contrast` 必须用所引 unit 正面说明"通用概念"和"特定领域规则"的边界，不得以"教材清单未列举该选项"为理由。
- 如果某个选项按其普通字面就不包含题干所要求的领域要素，可用 `stem_contrast` 和 `evidence_status=none` 判错；理由应直接对照题干领域边界，不得写成"没有召回/教材没有单元提及"。
- 每个选项的 `decision_basis` 必须是以下五种之一（注意与 `decision_framework.type` 是两套独立的分类，不要混淆）：
  - `direct_taxonomy`：教材原文直接支持或反驳该选项。
  - `definition_application`：基于整题定义框架提取的必要条件，逐项核对该选项。
  - `domain_contrast`：基于教材原文建立的领域边界，判断选项属于领域内还是领域外。
  - `stem_contrast`：仅基于题干和选项的可见文字直接对照得出结论，不需教材单元。当你能从题干文字推理出选项正误但无教材 unit 引用时，使用此值而非 `insufficient`。
  - `insufficient`：现有材料无法做出任何可靠判断时才使用。如果你的 `judgement` 是 `correct` 或 `incorrect` 且写出了实质 `decision_reason`，说明你已做出判断，不应标 `insufficient`。
- `definition_application` 必须在 evidence_cards 中绑定整题所引定义 unit；`direct_taxonomy` 必须绑定明确分类 unit；`domain_contrast` 必须绑定领域规则或选项概念 unit。
- `decision_reason` 只写实体判断，不得出现"候选池、召回、提示词、约束、模型输出"等内部过程词。
- 在输出 JSON 前逐项自检：
  1. `definition_application` 的每个选项都必须从 `decision_framework.cited_unit_ids` 复制至少一个定义 unit 到本选项 `evidence_cards`。
  2. `direct_taxonomy` 和 `domain_contrast` 的 `evidence_cards` 不得为空；若理由同时比较通用概念和领域规则，应分别绑定相应 unit。
  3. `decision_reason` 中写出的每个 unit_id 都必须同时出现在本选项 `evidence_cards` 或整题 `decision_framework.cited_unit_ids`，不得只在 prose 中提 ID。
  4. 有 `indirect` 卡片时 `evidence_status` 不得写 `none`；只有确实没有卡片的 `stem_contrast` 才可使用 `none`。
  5. `decision_reason` 中复述题干事实时，与题干原文逐字核对：不得添加题干没有的程度副词（略、远、刚好）、数量词（多个、跨）、性质词（虚假、伪造）。
  6. 每个 `evidence_cards` 中引用的 unit，必须通过语境有效性三项检查：主语是否与结论一致？章节的业务阶段是否与题干时间节点匹配？是否将特定场景/案例的陈述当作普遍原则使用？任何一项不通过，该 unit 不得作为 `direct` 证据，最多降级为 `indirect` 或放弃引用。
- `evidence_status=direct` 表示教材直接支持该选项；`indirect` 表示只能间接支持；`negative` 表示教材证据反驳该选项；`none` 表示没有可引用证据，且 evidence_cards 必须为空。
{{
  "predicted_answer": ["A"],
  "decision_framework": {{
    "type": "is_definition|is_domain|is_scenario",
    "rule_summary": "题目采用的判断规则",
    "cited_unit_ids": ["v7u_N000001"],
    "required_conditions": ["规则成立所需条件"]
  }},
  "option_analysis": [
    {{
      "option": "A",
      "judgement": "correct|incorrect|insufficient",
      "decision_basis": "direct_taxonomy|definition_application|domain_contrast|stem_contrast|insufficient",
      "decision_reason": "从整题规则到该选项结论的完整判断理由",
      "evidence_status": "direct|indirect|negative|none",
      "evidence_cards": [
        {{"unit_id": "v7u_N000001", "support_type": "direct|indirect|negative", "reason": "为什么这个单元支持或反驳该选项"}}
      ]
    }}
  ]
}}"""
    return prompt



# ── LLM 调用 ──────────────────────────────────────────────────────────


def call_llm(
    client: Any,
    prompt: str,
    model: str = "deepseek-v4-pro",
    max_tokens: int = 20000,
    timeout: float = 120.0,
    reasoning_effort: str = "high",
    enable_thinking: bool = True,
) -> str:
    """调用 LLM，返回响应文本。"""
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "timeout": timeout,
    }
    if enable_thinking:
        kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
        kwargs["reasoning_effort"] = reasoning_effort
    else:
        kwargs["temperature"] = 0
    response = client.chat.completions.create(**kwargs)
    return (response.choices[0].message.content or "").strip()


# ── 解析 LLM 响应 ─────────────────────────────────────────────────────


def strip_json_fence(text: str) -> str:
    """去除 markdown 代码块标记。"""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def parse_llm_output(raw_text: str) -> dict[str, Any] | None:
    """从 LLM 返回中提取 JSON。"""
    if not raw_text:
        return None

    cleaned = strip_json_fence(raw_text)

    # 尝试直接解析
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 尝试用正则提取 JSON 对象
    match = re.search(r"\{[\s\S]*\"option_analysis\"[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # 尝试 json_repair
    try:
        import json_repair
        return json.loads(json_repair.repair_json(cleaned))
    except Exception:
        pass

    return None


def normalize_llm_result(parsed: dict[str, Any]) -> dict[str, Any]:
    """对 LLM JSON 做最小 schema 归一化，不改判断和引用内容。"""
    option_analysis = parsed.get("option_analysis", [])
    if not isinstance(option_analysis, list):
        return parsed

    for opt in option_analysis:
        if not isinstance(opt, dict):
            continue
        evidence_cards = opt.get("evidence_cards", [])
        if not isinstance(evidence_cards, list):
            continue

        # 当 evidence_status 与 evidence_cards 矛盾时自动修正
        support_types = {
            card.get("support_type")
            for card in evidence_cards
            if isinstance(card, dict)
        }
        if opt.get("evidence_status") == "none" and evidence_cards:
            if "negative" in support_types:
                opt["evidence_status"] = "negative"
            elif "direct" in support_types:
                opt["evidence_status"] = "direct"
            else:
                opt["evidence_status"] = "indirect"

    return parsed


def filter_llm_citations(
    parsed: dict[str, Any],
    allowed_unit_ids: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """删除池外引用并保留审计记录，不猜测或修复相邻 unit_id。"""
    dropped: list[dict[str, Any]] = []
    framework = parsed.get("decision_framework")
    if isinstance(framework, dict):
        raw_framework_ids = framework.get("cited_unit_ids", [])
        if not isinstance(raw_framework_ids, list):
            raw_framework_ids = []
        legal_framework_ids: list[str] = []
        for raw_uid in raw_framework_ids:
            uid = str(raw_uid or "").strip()
            if uid in allowed_unit_ids and uid not in legal_framework_ids:
                legal_framework_ids.append(uid)
            elif uid not in allowed_unit_ids:
                dropped.append(
                    {
                        "location": "decision_framework",
                        "unit_id": uid,
                        "reason": "unit_id 不在本题主候选池或选项补充池",
                    }
                )
        framework["cited_unit_ids"] = legal_framework_ids

    option_analysis = parsed.get("option_analysis", [])
    if not isinstance(option_analysis, list):
        return parsed, dropped

    for option in option_analysis:
        if not isinstance(option, dict):
            continue
        cards = option.get("evidence_cards", [])
        if not isinstance(cards, list):
            continue
        legal_cards: list[dict[str, Any]] = []
        for card in cards:
            if not isinstance(card, dict):
                continue
            uid = str(card.get("unit_id", "") or "").strip()
            if uid in allowed_unit_ids:
                legal_cards.append(card)
            else:
                dropped.append(
                    {
                        "location": "option_analysis",
                        "option": option.get("option", ""),
                        "unit_id": uid,
                        "support_type": card.get("support_type", ""),
                        "reason": card.get("reason", ""),
                    }
                )
        option["evidence_cards"] = legal_cards
        # 证据卡被清空后降级处理
        if not legal_cards and option.get("evidence_status") != "none":
            option["evidence_status"] = "none"
        if (
            not legal_cards
            and option.get("decision_basis")
            in {"direct_taxonomy", "definition_application", "domain_contrast"}
        ):
            option["decision_basis"] = "insufficient"
            option["judgement"] = "insufficient"
            original_reason = str(option.get("decision_reason", "")).strip()
            option["decision_reason"] = (
                "引用单元不在本题可用教材证据范围内，缺少合法依据。"
                + (f" 原始判定理由：{original_reason}" if original_reason else "")
            )
    return parsed, dropped


# ── 机械校验 ──────────────────────────────────────────────────────────


def validate_result(
    result: dict[str, Any],
    candidates: list[dict[str, Any]],
    unit_lookup: dict[str, dict],
    supplement_pool: dict[str, list[dict[str, Any]]] | None = None,
) -> list[str]:
    """执行机械校验，返回问题列表。"""
    issues: list[str] = []

    # 候选池 unit_id 集合
    candidate_unit_ids = {c["unit_id"] for c in candidates}
    candidate_unit_ids.update(
        row["unit_id"]
        for rows in (supplement_pool or {}).values()
        for row in rows
        if row.get("unit_id")
    )
    # ±4 上下文扩展的 unit 也视为合法引用来源
    kg_units = _load_kg_units()
    if kg_units:
        for c in candidates:
            for card in _section_context_cards(c["unit_id"], candidate_unit_ids):
                candidate_unit_ids.add(card["unit_id"])
    # 真实 unit_id 集合（索引中存在）
    valid_unit_ids = set(unit_lookup.keys())

    option_analysis = result.get("option_analysis", [])
    options = result.get("options", {})
    predicted_answer = result.get("predicted_answer", [])

    # 答案合法性检查
    if not isinstance(predicted_answer, list):
        issues.append("predicted_answer 必须是数组")
    else:
        option_labels = {str(label) for label in options}
        invalid_answers = [
            str(answer) for answer in predicted_answer
            if str(answer) not in option_labels
        ]
        if invalid_answers:
            issues.append(
                "predicted_answer 包含不存在的选项: "
                + ",".join(invalid_answers)
            )
        if (
            result.get("question_type") == "single"
            and len(predicted_answer) != 1
        ):
            issues.append(
                "单选题 predicted_answer 必须且只能包含一个答案"
            )

    # decision_framework 校验
    framework = result.get("decision_framework")
    framework_ids: set[str] = set()
    if not isinstance(framework, dict):
        issues.append("缺少 decision_framework")
    else:
        framework_type = framework.get("type", "")
        if framework_type not in {
            "is_definition",
            "is_domain",
            "is_scenario",
        }:
            issues.append(f"非法 decision_framework.type={framework_type}")
        if not str(framework.get("rule_summary", "")).strip():
            issues.append("decision_framework 缺少 rule_summary")
        required_conditions = framework.get("required_conditions", [])
        if not isinstance(required_conditions, list):
            issues.append("decision_framework.required_conditions 必须是数组")
        elif framework_type == "is_definition" and not required_conditions:
            issues.append("is_definition 类型必须给出 required_conditions")
        cited_ids = framework.get("cited_unit_ids", [])
        if not isinstance(cited_ids, list):
            issues.append("decision_framework.cited_unit_ids 必须是数组")
            cited_ids = []
        for uid in cited_ids:
            uid = str(uid or "").strip()
            if not uid:
                issues.append("decision_framework 含空 unit_id")
                continue
            if uid in framework_ids:
                issues.append(f"decision_framework: unit_id={uid} 重复引用")
            framework_ids.add(uid)
            if uid not in valid_unit_ids:
                issues.append(f"decision_framework: 幻觉 unit_id={uid}（不在索引中）")
            if uid not in candidate_unit_ids:
                issues.append(
                    f"decision_framework: unit_id={uid} 不在本题候选池中"
                )

    # 选项数量一致性
    if len(option_analysis) != len(options):
        issues.append(
            f"选项数量不匹配: analysis={len(option_analysis)} vs options={len(options)}"
        )

    # 逐选项校验
    for opt in option_analysis:
        label = opt.get("option", "?")
        judgement = opt.get("judgement", "")
        decision_basis = opt.get("decision_basis", "")
        decision_reason = str(opt.get("decision_reason", "")).strip()
        evidence_status = opt.get("evidence_status", "")
        evidence_cards = opt.get("evidence_cards", [])

        # 选项完整性：每个选项都有 judgement 和 evidence_status
        if not judgement:
            issues.append(f"选项{label}: 缺少 judgement")
        if decision_basis not in {
            "direct_taxonomy",
            "definition_application",
            "domain_contrast",
            "stem_contrast",
            "insufficient",
        }:
            issues.append(f"选项{label}: 非法 decision_basis={decision_basis}")
        if not decision_reason:
            issues.append(f"选项{label}: 缺少 decision_reason")
        else:
            # 检查是否泄露内部过程词
            if re.search(
                r"候选池|补充池|召回|提示词|按约束|模型输出|原模型|白名单过滤|本次修复",
                decision_reason,
            ):
                issues.append(f"选项{label}: decision_reason 泄露内部检索或生成过程")
            # 检查是否用了"教材未列举"来证明错误（穷尽分类除外）
            # 只拦截"未列 → 因此错"的因果论证，不拦纯粹的事实描述
            absence_claim = re.search(
                r"教材.{0,20}(?:未|没有).{0,20}(?:列|提及|单元|认定|提供)"
                r".{0,30}(?:因此|所以|故|说明|应?排除|不属于|不正确|不是|并非)",
                decision_reason,
            )
            exhaustive_taxonomy = (
                decision_basis == "direct_taxonomy"
                and isinstance(framework, dict)
                and framework.get("type") == "is_definition"
                and re.search(
                    r"穷尽|完整|全部|21\s*类|21\s*categories",
                    str(framework.get("rule_summary", "")),
                    flags=re.IGNORECASE,
                )
            )
            if absence_claim and not exhaustive_taxonomy:
                issues.append(
                    f"选项{label}: 不得用教材未列举或未召回直接证明选项错误"
                )
            # 检查 definition_application 是否有推测性措辞
            if (
                decision_basis == "definition_application"
                and re.search(r"通常不|一般不|不必然", decision_reason)
            ):
                issues.append(
                    f"选项{label}: definition_application 不得推测选项通常具有或不具有的事实"
                )
        if not evidence_status:
            issues.append(f"选项{label}: 缺少 evidence_status")
        elif evidence_status not in {"direct", "indirect", "negative", "none"}:
            issues.append(f"选项{label}: 非法 evidence_status={evidence_status}")

        # direct 有据：evidence_status=direct 时必须至少有一条 evidence_cards
        if evidence_status == "direct" and not evidence_cards:
            issues.append(f"选项{label}: evidence_status=direct 但 evidence_cards 为空")

        # negative 有据：evidence_status=negative 时必须至少有一条反证 evidence_card
        if evidence_status == "negative":
            if not evidence_cards:
                issues.append(f"选项{label}: evidence_status=negative 但 evidence_cards 为空")
            elif not any(card.get("support_type") == "negative" for card in evidence_cards):
                issues.append(f"选项{label}: evidence_status=negative 但没有 negative evidence_card")

        # none 无据：evidence_status=none 时 evidence_cards 必须为空
        if evidence_status == "none" and evidence_cards:
            issues.append(f"选项{label}: evidence_status=none 但 evidence_cards 不为空")

        # evidence_cards 无重复、来源合法
        seen_uids: set[str] = set()
        for card in evidence_cards:
            uid = card.get("unit_id", "")
            support_type = card.get("support_type", "")
            if support_type and support_type not in {"direct", "indirect", "negative"}:
                issues.append(f"选项{label}: 非法 support_type={support_type}")

            if not uid:
                issues.append(f"选项{label}: evidence_card 缺少 unit_id")
                continue

            # unit_id 真实性
            if uid not in valid_unit_ids:
                issues.append(f"选项{label}: 幻觉 unit_id={uid}（不在索引中）")

            # 候选集来源
            if uid not in candidate_unit_ids:
                issues.append(f"选项{label}: unit_id={uid} 不在本题候选池中")

            # 重复
            if uid in seen_uids:
                issues.append(f"选项{label}: unit_id={uid} 重复引用")
            seen_uids.add(uid)

        # decision_reason 中引用的 unit_id 必须在 evidence_cards 或 framework 中有结构化绑定
        mentioned_unit_ids = set(
            re.findall(r"v7u_N\d+", decision_reason)
        )
        unbound_mentions = sorted(
            mentioned_unit_ids - seen_uids - framework_ids
        )
        if unbound_mentions:
            issues.append(
                f"选项{label}: decision_reason 提到未结构化绑定的 unit_id="
                + ",".join(unbound_mentions)
            )

        # decision_basis 为教材型时必须有合法 evidence_cards
        if decision_basis in {
            "direct_taxonomy",
            "definition_application",
            "domain_contrast",
        } and not evidence_cards:
            issues.append(
                f"选项{label}: decision_basis={decision_basis} 但没有合法 evidence_cards"
            )
        if decision_basis == "definition_application":
            if not framework_ids:
                issues.append(
                    f"选项{label}: definition_application 但整题未引用定义 unit"
                )
            elif not (seen_uids & framework_ids):
                issues.append(
                    f"选项{label}: definition_application 未在 evidence_cards "
                    "绑定整题定义 unit"
                )
        if decision_basis == "insufficient" and judgement != "insufficient":
            issues.append(
                f"选项{label}: decision_basis=insufficient 时 judgement 必须为 insufficient"
            )

    return issues


# ── 单题处理流程 ──────────────────────────────────────────────────────


def process_question(
    question: dict[str, Any],
    bge_vecs: np.ndarray,
    card_ids: list[str],
    unit_lookup: dict[str, dict],
    bm25_zh_index: BM25,
    bm25_en_index: BM25,
    api_key: str,
    base_url: str,
    model: str,
    top_k: int = 20,
    merge_top_k: int = 30,
    kg_index: dict[str, Any] | None = None,
    kg_max_extra: int = 30,
    p5_index: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """对一道题执行完整盲判流程。"""
    qid = question["question_id"]
    qtype = question.get("question_type", "single")
    tier = question.get("tier", "")

    result: dict[str, Any] = {
        "question_id": qid,
        "stem": question.get("stem", ""),
        "options": question.get("options", {}),
        "question_type": qtype,
        "tier": tier,
        "pipeline_status": "ok",
    }
    if question.get("_chapter_mappings") is not None:
        result["chapter_mappings"] = question.get("_chapter_mappings", [])
    if question.get("_question_text_override") is not None:
        result["question_text_override"] = question.get(
            "_question_text_override", {}
        )

    try:
        # 步骤 1: 检索 → 候选池
        candidates = search_and_merge(
            question,
            bge_vecs=bge_vecs,
            card_ids=card_ids,
            unit_lookup=unit_lookup,
            bm25_zh_index=bm25_zh_index,
            bm25_en_index=bm25_en_index,
            top_k=top_k,
            merge_top_k=merge_top_k,
            kg_index=kg_index,
            kg_max_extra=kg_max_extra,
            p5_index=p5_index,
        )
        result["candidate_pool"] = candidates
        result["candidate_route_counts"] = dict(
            Counter(c.get("route", "unknown") for c in candidates)
        )
        result["kg_enabled"] = kg_index is not None
        result["p5_enabled"] = p5_index is not None

        # 选项独立补充召回
        supplement_pool = retrieve_option_supplements(
            question,
            bge_vecs=bge_vecs,
            card_ids=card_ids,
            unit_lookup=unit_lookup,
            bm25_zh_index=bm25_zh_index,
            bm25_en_index=bm25_en_index,
            excluded_unit_ids={row["unit_id"] for row in candidates},
            top_k=top_k,
            per_option_limit=3,
        )
        result["option_supplement_pool"] = supplement_pool
        result["option_supplement_counts"] = {
            label: len(rows) for label, rows in supplement_pool.items()
        }

        # 步骤 2: 构建 prompt
        prompt = build_prompt(question, candidates, supplement_pool)

        # 步骤 3: LLM 调用（每个线程独立的 client）
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        llm_output = call_llm(client, prompt, model=model, reasoning_effort="high")
        result["llm_output"] = llm_output

        # 步骤 4: 解析 LLM 响应
        parsed = parse_llm_output(llm_output)
        if parsed is None:
            result["pipeline_status"] = "llm_parse_failed"
            result["option_analysis"] = []
            result["validation_checks"] = ["LLM 输出无法解析为 JSON"]
            result["predicted_answer"] = []
            return result
        parsed = normalize_llm_result(parsed)

        # 过滤池外引用
        allowed_unit_ids = {row["unit_id"] for row in candidates}
        allowed_unit_ids.update(
            row["unit_id"]
            for rows in supplement_pool.values()
            for row in rows
        )
        parsed, citation_drops = filter_llm_citations(
            parsed, allowed_unit_ids
        )
        result["citation_filter_drops"] = citation_drops

        # 确定性修复 LLM 的机械一致性错误
        framework_ids = {
            str(uid) for uid in
            (parsed.get("decision_framework") or {}).get("cited_unit_ids", []) or []
        }
        for opt in parsed.get("option_analysis", []) or []:
            cards = opt.get("evidence_cards", [])
            if not isinstance(cards, list):
                cards = []
                opt["evidence_cards"] = cards
            # (a) evidence_status=negative 但没有 negative card → 对齐
            if (opt.get("evidence_status") == "negative"
                    and not any(c.get("support_type") == "negative" for c in cards if isinstance(c, dict))):
                if cards:
                    for c in cards:
                        if isinstance(c, dict):
                            c["support_type"] = "negative"
                            break
                else:
                    opt["evidence_status"] = "none"
            # (b) decision_reason 提到但未绑定的 unit_id → 自动补到 evidence_cards
            reason = str(opt.get("decision_reason", "") or "")
            mentioned = set(re.findall(r"v7u_N\d+", reason))
            bound = {str(c.get("unit_id", "")) for c in cards if isinstance(c, dict)}
            bound.update(framework_ids)
            unbound = mentioned - bound
            for uid in sorted(unbound):
                if uid in allowed_unit_ids:
                    cards.append({
                        "unit_id": uid,
                        "support_type": "indirect",
                        "reason": "从 decision_reason 自动绑定",
                    })
            # (c) 有 evidence_cards 但 evidence_status=none → 对齐
            if cards and opt.get("evidence_status") == "none":
                opt["evidence_status"] = "indirect"

        result["option_analysis"] = parsed.get("option_analysis", [])
        result["predicted_answer"] = parsed.get("predicted_answer", [])
        result["decision_framework"] = parsed.get("decision_framework")

        # 步骤 5: 机械校验（仅检查，不修复）
        validation_issues = validate_result(
            result, candidates, unit_lookup, supplement_pool
        )
        result["validation_checks"] = validation_issues
        if validation_issues:
            result["pipeline_status"] = "validation_failed"

    except Exception as exc:
        result["pipeline_status"] = "llm_parse_failed"
        result["option_analysis"] = []
        result["validation_checks"] = [f"处理异常: {str(exc)[:200]}"]
        result["predicted_answer"] = []
        result["error_traceback"] = traceback.format_exc()

    return result


# ── 输出 ──────────────────────────────────────────────────────────────


def write_question_json(
    result: dict[str, Any],
    output_dir: Path,
) -> None:
    """将每题详情写入 output/questions/q_{question_id}.json。"""
    qid = result["question_id"]
    path = output_dir / "questions" / f"q_{qid}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def write_summary_jsonl(
    results: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """写入汇总 JSONL。"""
    path = output_dir / "blind_judgment_results.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for r in results:
            summary = {
                "question_id": r["question_id"],
                "tier": r.get("tier", ""),
                "question_type": r.get("question_type", ""),
                "predicted_answer": r.get("predicted_answer", []),
                "option_analysis": r.get("option_analysis", []),
                "decision_framework": r.get("decision_framework"),
                "validation_passed": r.get("pipeline_status") == "ok",
                "pipeline_status": r.get("pipeline_status", "error"),
                "chapter_mappings": r.get("chapter_mappings", []),
                "option_supplement_counts": r.get(
                    "option_supplement_counts", {}
                ),
            }
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")
    print(f"[output] JSONL 已写入: {path} ({len(results)} 行)")


def write_markdown_report(
    results: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """写入人读 Markdown 报告。"""
    path = output_dir / "blind_judgment_report.md"
    lines: list[str] = []
    lines.append("# Phase 4.1 — 盲判结果报告\n")
    lines.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    total = len(results)
    ok_count = sum(1 for r in results if r.get("pipeline_status") == "ok")
    vf_count = sum(1 for r in results if r.get("pipeline_status") == "validation_failed")
    pf_count = sum(1 for r in results if r.get("pipeline_status") == "llm_parse_failed")
    lines.append(f"总题数: {total} | ok: {ok_count} | validation_failed: {vf_count} | llm_parse_failed: {pf_count}\n")
    lines.append("---\n")

    for r in results:
        qid = r["question_id"]
        status = r.get("pipeline_status", "?")
        stem = r.get("stem", "")[:80]
        qtype = r.get("question_type", "?")
        predicted = r.get("predicted_answer", [])
        checks = r.get("validation_checks", [])

        lines.append(f"\n## {qid} | {qtype} | status={status}\n")
        lines.append(f"**题干**: {stem}...\n")
        lines.append(f"**预测答案**: {', '.join(predicted) if predicted else '(无)'}\n")

        # 候选池统计
        candidates = r.get("candidate_pool", [])
        lines.append(f"**候选池**: {len(candidates)} 个知识单元\n")
        supplement_counts = r.get("option_supplement_counts", {})
        if supplement_counts:
            text = ", ".join(
                f"{label}={count}" for label, count in supplement_counts.items()
            )
            lines.append(f"**选项独立补充池**: {text}\n")
        route_counts = r.get("candidate_route_counts", {})
        if route_counts:
            route_text = ", ".join(f"{k}={v}" for k, v in route_counts.items())
            lines.append(f"**候选来源**: {route_text}\n")

        # 选项分析
        option_analysis = r.get("option_analysis", [])
        if option_analysis:
            lines.append("### 选项分析\n")
            lines.append("| 选项 | 判断 | 证据状态 | 证据数 |\n")
            lines.append("|------|------|----------|--------|\n")
            for opt in option_analysis:
                label = opt.get("option", "?")
                judgement = opt.get("judgement", "?")
                ev_status = opt.get("evidence_status", "?")
                n_cards = len(opt.get("evidence_cards", []))
                lines.append(f"| {label} | {judgement} | {ev_status} | {n_cards} |\n")

        # 校验结果
        if checks:
            lines.append("\n### 校验问题\n")
            for issue in checks:
                lines.append(f"- {issue}\n")

        lines.append("\n---\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"[output] Markdown 已写入: {path}")


# ── 主流程 ────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Phase 4.1 — 小批量盲判脚本"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="处理题数（默认 10）",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="并发数（默认 10）",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-v4-pro",
        help="模型名称（默认 deepseek-v4-pro）",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="每路检索 top-k（默认 20）",
    )
    parser.add_argument(
        "--merge-top-k",
        type=int,
        default=30,
        help="合并后候选池大小（默认 30）",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="处理全部题目（覆盖 manual_reviewed 默认筛选）",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="跳过 output/questions/ 下已有 JSON 的题目",
    )
    parser.add_argument(
        "--question-id",
        action="append",
        default=[],
        help="指定题号，可重复传入；例如 --question-id v7_q_000009",
    )
    parser.add_argument(
        "--chapter-map",
        type=str,
        default="",
        help="人工确认的 question_chapter_mappings.jsonl",
    )
    parser.add_argument(
        "--chapter-id",
        type=str,
        default="",
        help="按真实教材章节选择全部题目，例如 Ch1",
    )
    parser.add_argument(
        "--enable-kg",
        action="store_true",
        help="启用 KG 候选扩展（默认关闭）",
    )
    parser.add_argument(
        "--kg-graph-path",
        type=str,
        default=str(KG_GRAPH_PATH),
        help="P6 KG 母版路径",
    )
    parser.add_argument(
        "--kg-max-extra",
        type=int,
        default=30,
        help="每题最多追加的 KG 候选数（默认 30）",
    )
    parser.add_argument(
        "--enable-p5",
        action="store_true",
        help="启用 P5 术语/别名检索辅助（默认关闭）",
    )
    parser.add_argument(
        "--p5-alias-path",
        type=str,
        default=str(P5_ALIAS_INDEX_PATH),
        help="P5C alias index 路径",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUTPUT_DIR),
        help="输出目录（默认 phase4_evidence/output）",
    )
    args = parser.parse_args()

    if args.question_id and args.chapter_id:
        parser.error("--question-id 与 --chapter-id 不能同时使用")
    if args.chapter_id and not args.chapter_map:
        parser.error("使用 --chapter-id 时必须同时提供 --chapter-map")

    print("=" * 60)
    print("Phase 4.1 — 小批量盲判脚本")
    print("=" * 60)
    print(f"limit={args.limit}, concurrency={args.concurrency}, model={args.model}")
    print(f"top_k={args.top_k}, merge_top_k={args.merge_top_k}\n")
    print(
        f"kg_enabled={args.enable_kg}, kg_max_extra={args.kg_max_extra}, "
        f"kg_graph_path={args.kg_graph_path}\n"
    )
    print(
        f"p5_enabled={args.enable_p5}, p5_alias_path={args.p5_alias_path}\n"
    )

    # 1. 加载数据
    questions = load_questions(QUESTIONS_PATH)
    index = load_index(INDEX_PKL)
    chapter_mapping_index = (
        load_chapter_mapping_index(args.chapter_map) if args.chapter_map else {}
    )
    if chapter_mapping_index:
        enriched_questions: list[dict[str, Any]] = []
        for question in questions:
            row = chapter_mapping_index.get(question["question_id"])
            enriched = dict(question)
            enriched["_chapter_mappings"] = (
                row.get("chapter_mappings", []) if row else []
            )
            enriched_questions.append(enriched)
        questions = enriched_questions

    card_ids: list[str] = index["card_ids"]
    bge_vecs: np.ndarray = index["bge_vecs"]
    unit_lookup: dict[str, dict] = index["unit_lookup"]
    zh_bm25_docs: list[Counter] = index["zh_bm25_docs"]
    zh_bm25_df: dict[str, int] = index["zh_bm25_df"]
    zh_bm25_avgdl: float = index["zh_bm25_avgdl"]
    en_bm25_docs: list[Counter] = index["en_bm25_docs"]
    en_bm25_df: dict[str, int] = index["en_bm25_df"]
    en_bm25_avgdl: float = index["en_bm25_avgdl"]

    # 2. 构建 BM25 检索器
    print("\n[bm25] 构建中文 BM25 检索器 ...")
    bm25_zh = BM25(zh_bm25_docs, zh_bm25_df, zh_bm25_avgdl)
    print(f"[bm25] 中文 BM25 就绪 | N={bm25_zh.N}, avgdl={bm25_zh.avgdl:.2f}")

    print("[bm25] 构建英文 BM25 检索器 ...")
    bm25_en = BM25(en_bm25_docs, en_bm25_df, en_bm25_avgdl)
    print(f"[bm25] 英文 BM25 就绪 | N={bm25_en.N}, avgdl={bm25_en.avgdl:.2f}")

    # 3. 预加载 BGE 模型
    print()
    get_bge_model()

    # 3.5 可选加载 KG 导航索引与 P5 术语索引
    kg_index = load_kg_graph(args.kg_graph_path) if args.enable_kg else None
    p5_index = load_p5_alias_index(args.p5_alias_path) if args.enable_p5 else None

    # 4. 获取 API 配置
    api_key, base_url, env_name = get_llm_config()
    print(f"\n[api] 使用 {env_name} | base_url={base_url}")

    # 5. 筛选题目
    if args.question_id:
        wanted = set(args.question_id)
        sampled = [q for q in questions if q.get("question_id") in wanted]
        sampled.sort(key=lambda x: x["question_id"])
        found = {q["question_id"] for q in sampled}
        missing = sorted(wanted - found)
        if missing:
            raise RuntimeError(f"指定题号不存在: {', '.join(missing)}")
        print(f"\n[sample] 指定题号 {len(sampled)} 题")
    elif args.chapter_id:
        chapter_id = args.chapter_id.strip()
        # 兼容旧格式 CH01 和新格式 Ch1
        sampled = [
            q for q in questions
            if any(
                mapping.get("chapter_id") == chapter_id.upper()
                or mapping.get("real_chapter") == chapter_id
                or (isinstance(mapping.get("real_chapter"), list)
                    and chapter_id in mapping.get("real_chapter", []))
                for mapping in q.get("_chapter_mappings", []) or []
            )
        ]
        sampled.sort(key=lambda x: x["question_id"])
        if not sampled:
            raise RuntimeError(f"章节 {chapter_id} 没有已确认题目")
        print(f"\n[sample] 教材章节 {chapter_id} 共 {len(sampled)} 题（不应用 --limit）")
    else:
        if args.all:
            sampled = sorted(questions, key=lambda x: x["question_id"])[:args.limit]
            print(f"\n[sample] 全部 {len(questions)} 题，取前 {len(sampled)} 题")
        else:
            manual_questions = [
                q for q in questions
                if "manual_reviewed" in q.get("risk_flags", [])
            ]
            manual_questions.sort(key=lambda x: x["question_id"])
            sampled = manual_questions[:args.limit]
            print(
                f"\n[sample] manual_reviewed 共 {len(manual_questions)} 题，"
                f"取前 {len(sampled)} 题"
            )
    for q in sampled:
        mapped = ",".join(
            row.get("real_chapter") or row.get("chapter_id", "")
            for row in q.get("_chapter_mappings", []) or []
        ) or "unmapped"
        print(f"  {q['question_id']} | {mapped} | {q.get('question_type','?')}")

    # 6. 跳过已有
    output_dir = Path(args.output_dir)
    if args.skip_existing:
        questions_dir = output_dir / "questions"
        before = len(sampled)
        sampled = [
            q for q in sampled
            if not (questions_dir / f"q_{q['question_id']}.json").exists()
        ]
        skipped = before - len(sampled)
        if skipped:
            print(f"\n[skip] 跳过已存在 {skipped} 题，剩余 {len(sampled)} 题")
    if not sampled:
        print("全部题目已处理完毕，无需运行。")
        return

    # 7. 并发处理
    print(f"\n[run] 开始并发处理（{args.concurrency} 线程）...")
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        future_map = {
            executor.submit(
                process_question,
                q,
                bge_vecs,
                card_ids,
                unit_lookup,
                bm25_zh,
                bm25_en,
                api_key,
                base_url,
                args.model,
                args.top_k,
                args.merge_top_k,
                kg_index,
                args.kg_max_extra,
                p5_index,
            ): q
            for q in sampled
        }

        for i, future in enumerate(as_completed(future_map), start=1):
            q = future_map[future]
            qid = q["question_id"]
            try:
                result = future.result()
                results.append(result)

                # 进度打印
                status = result.get("pipeline_status", "?")
                n_issues = len(result.get("validation_checks", []))
                n_candidates = len(result.get("candidate_pool", []))
                predicted = result.get("predicted_answer", [])
                print(
                    f"[{i}/{len(sampled)}] {qid}"
                    f" | status={status}"
                    f" | candidates={n_candidates}"
                    f" | predicted={' '.join(predicted) if predicted else '?'}"
                    f" | issues={n_issues}"
                )

                # 写入每题 JSON
                write_question_json(result, output_dir)

            except Exception as exc:
                print(f"[{i}/{len(sampled)}] {qid} | ERROR: {str(exc)[:100]}")
                error_result = {
                    "question_id": qid,
                    "stem": q.get("stem", ""),
                    "options": q.get("options", {}),
                    "question_type": q.get("question_type", ""),
                    "tier": q.get("tier", ""),
                    "pipeline_status": "llm_parse_failed",
                    "candidate_pool": [],
                    "option_supplement_pool": {},
                    "option_supplement_counts": {},
                    "option_analysis": [],
                    "validation_checks": [f"线程异常: {str(exc)[:200]}"],
                    "predicted_answer": [],
                    "chapter_mappings": q.get("_chapter_mappings", []),
                    "question_text_override": q.get(
                        "_question_text_override", {}
                    ),
                    "decision_framework": None,
                }
                results.append(error_result)
                write_question_json(error_result, output_dir)

    # 按 question_id 排序结果
    results.sort(key=lambda x: x["question_id"])

    # 7. 输出汇总
    print("\n" + "=" * 60)
    print("输出汇总结果")
    print("=" * 60)

    write_summary_jsonl(results, output_dir)
    write_markdown_report(results, output_dir)

    # 统计
    status_counts = Counter(r.get("pipeline_status", "?") for r in results)
    print(f"\n[stats] 状态分布: {dict(status_counts)}")
    print(f"[stats] 共处理 {len(results)} 题")

    ok_count = status_counts.get("ok", 0)
    vf_count = status_counts.get("validation_failed", 0)
    pf_count = status_counts.get("llm_parse_failed", 0)
    print(f"  [OK] ok: {ok_count}")
    print(f"  [WARN] validation_failed: {vf_count}")
    print(f"  [ERR] llm_parse_failed: {pf_count}")
    print("\nDone.")


if __name__ == "__main__":
    # 确保 sentence_transformers 的离线环境
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    main()
