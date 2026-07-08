"""
Option-level agentic search experiment.

This script does not overwrite the formal step1 outputs. It compares the old
"query -> BGE section -> first cards" retrieval shape with a more deliberate
option-level search loop:

1. LLM search planner: turn each option judgement into evidence needs.
2. Multi-route retrieval: card-level BGE, BM25-like sparse search, exact phrase
   hits, adjacent cards, and low-weight relation expansion.
3. LLM evidence adjudicator: write usable option explanations and cite only
   candidate cards.
4. Optional follow-up round: if direct evidence is missing, let the adjudicator
   request more queries and search again.

Final evidence still must be real textbook evidence card_id values. kg_data.json
and card_relations.json remain auxiliary only.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import run_step1


SCHEMA_VERSION = "option_binding_agentic_search_v1"
SAVE_DIR = run_step1.BASE / "output" / "agentic_search_experiment"

CARD_BGE_THRESHOLD = 0.34
MAX_CANDIDATE_TEXT_CHARS = 30000
PLANNER_MAX_TOKENS = 5000
ADJUDICATOR_MAX_TOKENS = 9000
CARD_SCAN_MAX_TOKENS = 7000


@dataclass
class AgenticRuntime:
    base: run_step1.Runtime
    card_ids: list[str]
    card_texts: list[str]
    card_by_id: dict[str, dict[str, Any]]
    card_vecs: Any
    bm25_docs: list[Counter[str]]
    bm25_df: Counter[str]
    bm25_avgdl: float
    relations: dict[str, list[dict[str, Any]]]


def parse_json_object(raw_text: str) -> dict[str, Any] | None:
    if not raw_text:
        return None
    candidates = [run_step1.strip_json_fence(raw_text)]
    match = re.search(r"\{[\s\S]*\}", raw_text)
    if match:
        candidates.append(match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            try:
                import json_repair

                parsed = json.loads(json_repair.repair_json(candidate))
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                continue
    return None


def compact_text(text: str, limit: int = 360) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:limit]


def card_text(card: dict[str, Any]) -> str:
    knowledge = str(card.get("knowledge", "") or "").strip()
    citation = str(card.get("citation", "") or "").strip()
    chapter = str(card.get("chapter_path", "") or "").strip()
    h4 = chapter.split(" > ")[-1].strip() if chapter else ""
    parts = [
        f"KNOWLEDGE:{knowledge}" if knowledge else "",
        f"CITATION:{citation}" if citation else "",
        f"SECTION:{h4}" if h4 and h4 != knowledge else "",
    ]
    return " ".join(p for p in parts if p)


def is_cjk(ch: str) -> bool:
    return "\u4e00" <= ch <= "\u9fff"


def tokenize(text: str) -> list[str]:
    text = (text or "").lower()
    tokens: list[str] = []
    tokens.extend(re.findall(r"[a-z0-9][a-z0-9_\-/.]*", text))

    cjk_runs = re.findall(r"[\u4e00-\u9fff]+", text)
    for run in cjk_runs:
        if len(run) == 1:
            tokens.append(run)
            continue
        for n in (2, 3):
            if len(run) >= n:
                tokens.extend(run[i : i + n] for i in range(len(run) - n + 1))
    return tokens


def extract_phrases(*texts: str, max_terms: int = 24) -> list[str]:
    seen: set[str] = set()
    phrases: list[str] = []
    stop = {"题目", "选项", "正确", "错误", "以下", "哪些", "哪一种", "什么", "为什么"}
    for text in texts:
        for raw in re.split(r"[\s,，。；;：:、/()（）\"'“”‘’\[\]【】]+", text or ""):
            item = raw.strip()
            if len(item) < 2 or item in stop:
                continue
            if len(item) > 24:
                item = item[:24]
            if item not in seen:
                seen.add(item)
                phrases.append(item)
            if len(phrases) >= max_terms:
                return phrases
    return phrases


def load_agentic_runtime(evidence_scope: str = "ch2") -> AgenticRuntime:
    base = run_step1.load_runtime(evidence_scope=evidence_scope)
    card_by_id = {card["card_id"]: card for card in base.cards if card.get("card_id")}
    card_ids = list(card_by_id)
    card_texts = [card_text(card_by_id[cid]) for cid in card_ids]

    print(f"Encoding {len(card_texts)} textbook sentence cards for card-level BGE...")
    card_vecs = base.bge.encode(card_texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)

    bm25_docs = [Counter(tokenize(text)) for text in card_texts]
    bm25_df: Counter[str] = Counter()
    for doc in bm25_docs:
        bm25_df.update(doc.keys())
    bm25_avgdl = sum(sum(doc.values()) for doc in bm25_docs) / max(len(bm25_docs), 1)

    relations_path = run_step1.DATA / "card_relations.json"
    relations = run_step1.read_json(relations_path) if relations_path.exists() else {}

    return AgenticRuntime(
        base=base,
        card_ids=card_ids,
        card_texts=card_texts,
        card_by_id=card_by_id,
        card_vecs=card_vecs,
        bm25_docs=bm25_docs,
        bm25_df=bm25_df,
        bm25_avgdl=bm25_avgdl,
        relations=relations,
    )


def teacher_hint_block(teacher_explanation: str) -> str:
    if not teacher_explanation:
        return ""
    hint = compact_text(teacher_explanation, 1600)
    return f"""
教研解析检索提示（只能用于扩展检索词，不能作为教材证据，最终 evidence_cards 仍必须来自真实教材句卡）：
{hint}
"""


def build_planner_prompt(
    stem: str,
    options: dict[str, str],
    answer: str,
    teacher_explanation: str = "",
) -> str:
    opt_text = "\n".join(f"{label}. {text}" for label, text in options.items())
    return f"""你是CAMS教材证据检索规划员。你的任务不是写解析，而是把每个选项转成可检索的教材证据需求。

输入只有题目、选项和标准答案。若提供“教研解析检索提示”，它只能帮助你补充检索词和同义词，不能被当作证据。不要编造 card_id，不要声称已经找到教材原文。

请输出严格JSON，不要Markdown，不要代码块。

题目：{stem}
选项：
{opt_text}
标准答案：{answer}
{teacher_hint_block(teacher_explanation)}

输出格式：
{{
  "question_focus": "本题考的核心概念或场景",
  "options": [
    {{
      "option": "A",
      "judgement_by_answer": "correct/incorrect",
      "option_claim": "把选项改写成一个需要教材证据判断的命题",
      "evidence_need": "需要找哪类教材原文才能判断此选项",
      "search_queries": ["用教材术语写的查询1", "查询2", "查询3"],
      "must_terms": ["最关键的中文/英文术语"],
      "related_terms": ["同义词、上位词、近义场景"],
      "contrast_terms": ["容易混淆但需要排除或比较的概念"],
      "avoid_confusions": ["检索时容易误抓的噪声"]
    }}
  ]
}}

要求：
1. 每个选项都必须出现，顺序与原题一致。
2. search_queries 要尽量使用教材可能出现的表达，不要只复制选项原话。
3. 对错误选项，也要说明需要找什么教材规则来反驳它。
4. 如果是红旗、义务、处罚、流程、机构、定义、阶段类题，要在 evidence_need 中点明。"""


def fallback_plan(
    stem: str,
    options: dict[str, str],
    answer: str,
    teacher_explanation: str = "",
) -> dict[str, Any]:
    correct = run_step1.normalize_answer(answer, options)
    rows = []
    for label, text in options.items():
        terms = extract_phrases(stem, text, teacher_explanation)
        hint_queries = [compact_text(teacher_explanation, 180)] if teacher_explanation else []
        rows.append(
            {
                "option": label,
                "judgement_by_answer": "correct" if label in correct else "incorrect",
                "option_claim": text,
                "evidence_need": f"判断该选项是否符合题干：{stem}",
                "search_queries": [f"{stem} {text}", text, " ".join(terms[:8]), *hint_queries],
                "must_terms": terms[:6],
                "related_terms": [],
                "contrast_terms": [],
                "avoid_confusions": [],
            }
        )
    return {"question_focus": stem, "options": rows}


def normalize_plan(
    plan: dict[str, Any] | None,
    stem: str,
    options: dict[str, str],
    answer: str,
    teacher_explanation: str = "",
) -> dict[str, Any]:
    if not isinstance(plan, dict) or not isinstance(plan.get("options"), list):
        return fallback_plan(stem, options, answer, teacher_explanation)

    by_label = {str(item.get("option", "")).strip(): item for item in plan.get("options", []) if isinstance(item, dict)}
    fallback = fallback_plan(stem, options, answer, teacher_explanation)
    normalized = {"question_focus": plan.get("question_focus") or fallback["question_focus"], "options": []}
    correct = run_step1.normalize_answer(answer, options)
    for fb in fallback["options"]:
        label = fb["option"]
        item = by_label.get(label, {})
        merged = {**fb, **item}
        merged["option"] = label
        merged["judgement_by_answer"] = "correct" if label in correct else "incorrect"
        for field in ["search_queries", "must_terms", "related_terms", "contrast_terms", "avoid_confusions"]:
            value = merged.get(field)
            if not isinstance(value, list):
                value = []
            merged[field] = [str(x).strip() for x in value if str(x).strip()]
        if not merged["search_queries"]:
            merged["search_queries"] = fb["search_queries"]
        normalized["options"].append(merged)
    return normalized


def call_planner(
    rt: AgenticRuntime,
    stem: str,
    options: dict[str, str],
    answer: str,
    teacher_explanation: str = "",
) -> tuple[dict[str, Any], str]:
    raw = run_step1.call_llm(
        rt.base.client,
        build_planner_prompt(stem, options, answer, teacher_explanation),
        PLANNER_MAX_TOKENS,
    )
    parsed = parse_json_object(raw)
    return normalize_plan(parsed, stem, options, answer, teacher_explanation), raw


def add_candidate(
    bucket: dict[str, dict[str, Any]],
    cid: str,
    score: float,
    source: str,
    query: str,
    rt: AgenticRuntime,
) -> None:
    if cid not in rt.card_by_id:
        return
    card = rt.card_by_id[cid]
    row = bucket.setdefault(
        cid,
        {
            "card_id": cid,
            "score": 0.0,
            "source": source,
            "sources": [],
            "type": card.get("type", ""),
            "knowledge": card.get("knowledge", ""),
            "citation": card.get("citation", ""),
            "context_before": card.get("context_before", ""),
            "context_after": card.get("context_after", ""),
            "text": card_text(card),
        },
    )
    row["score"] += score
    row["sources"].append({"source": source, "score": round(score, 4), "query": compact_text(query, 120)})
    source_parts = row.get("source", "").split("+") if row.get("source") else []
    if source not in source_parts:
        source_parts.append(source)
    row["source"] = "+".join(source_parts)


def card_bge_search(rt: AgenticRuntime, query: str, top_k: int = 18) -> list[tuple[str, float]]:
    q_vec = rt.base.bge.encode([query], normalize_embeddings=True)
    scores = (q_vec @ rt.card_vecs.T).flatten()
    rows: list[tuple[str, float]] = []
    for idx in list(reversed(scores.argsort()))[:top_k]:
        score = float(scores[idx])
        if score < CARD_BGE_THRESHOLD:
            continue
        rows.append((rt.card_ids[idx], score))
    return rows


def bm25_search(rt: AgenticRuntime, query: str, top_k: int = 18) -> list[tuple[str, float]]:
    query_terms = tokenize(query)
    if not query_terms:
        return []
    q_counts = Counter(query_terms)
    total_docs = len(rt.bm25_docs)
    k1 = 1.4
    b = 0.72
    scores: list[tuple[int, float]] = []
    for idx, doc in enumerate(rt.bm25_docs):
        dl = sum(doc.values())
        score = 0.0
        for term, qf in q_counts.items():
            tf = doc.get(term, 0)
            if not tf:
                continue
            df = rt.bm25_df.get(term, 0)
            idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
            denom = tf + k1 * (1 - b + b * dl / max(rt.bm25_avgdl, 1))
            score += idf * (tf * (k1 + 1) / denom) * min(qf, 3)
        if score:
            scores.append((idx, score))
    scores.sort(key=lambda item: item[1], reverse=True)
    return [(rt.card_ids[idx], score) for idx, score in scores[:top_k]]


def exact_phrase_search(rt: AgenticRuntime, phrases: list[str], top_k: int = 18) -> list[tuple[str, float]]:
    if not phrases:
        return []
    scores: dict[str, float] = {}
    for cid, text in zip(rt.card_ids, rt.card_texts):
        total = 0.0
        for phrase in phrases:
            phrase = phrase.strip()
            if len(phrase) < 2:
                continue
            if phrase.lower() in text.lower():
                total += 6.0 + min(len(phrase), 12) * 0.25
        if total:
            scores[cid] = total
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]


def neighbor_ids(cid: str, rt: AgenticRuntime, window: int = 2) -> list[str]:
    match = re.match(r"^(v\d+_b\d+_N|v\d+s_N)(\d+)$", cid)
    if not match:
        return []
    prefix, num_text = match.groups()
    width = len(num_text)
    num = int(num_text)
    rows = []
    for delta in range(-window, window + 1):
        if delta == 0:
            continue
        candidate = f"{prefix}{num + delta:0{width}d}"
        if candidate in rt.card_by_id:
            rows.append(candidate)
    return rows


def retrieve_for_option(
    rt: AgenticRuntime,
    stem: str,
    option_text: str,
    option_plan: dict[str, Any],
    top_k: int = 24,
    *,
    return_source_rankings: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    bucket: dict[str, dict[str, Any]] = {}
    queries = list(option_plan.get("search_queries", []))
    queries.extend([f"{stem} {option_text}", option_text, option_plan.get("evidence_need", "")])
    queries = [compact_text(query, 180) for query in queries if compact_text(query, 180)]

    phrases = extract_phrases(
        option_text,
        option_plan.get("option_claim", ""),
        option_plan.get("evidence_need", ""),
        " ".join(option_plan.get("must_terms", [])),
        " ".join(option_plan.get("related_terms", [])),
        " ".join(option_plan.get("contrast_terms", [])),
    )

    diagnostics = {"queries": queries, "phrases": phrases, "route_counts": Counter()}

    # Per-source ranking capture for RRF (WeKnora CHUNK_SEARCH_PARALLEL)
    source_lists: dict[str, list[tuple[str, float, int]]] = {}
    if return_source_rankings:
        source_lists = {"card_bge": [], "bm25": [], "exact_phrase": [], "adjacent_card": []}

    for query in queries[:8]:
        for rank, (cid, score) in enumerate(card_bge_search(rt, query, top_k=50), start=1):
            add_candidate(bucket, cid, score * 8 + 1 / rank, "card_bge", query, rt)
            diagnostics["route_counts"]["card_bge"] += 1
            if return_source_rankings:
                source_lists["card_bge"].append((cid, score * 8 + 1 / rank, rank))
        for rank, (cid, score) in enumerate(bm25_search(rt, query, top_k=50), start=1):
            add_candidate(bucket, cid, score * 0.35 + 1 / rank, "bm25", query, rt)
            diagnostics["route_counts"]["bm25"] += 1
            if return_source_rankings:
                source_lists["bm25"].append((cid, score * 0.35 + 1 / rank, rank))

    for rank, (cid, score) in enumerate(exact_phrase_search(rt, phrases, top_k=24), start=1):
        add_candidate(bucket, cid, score + 1 / rank, "exact_phrase", " | ".join(phrases[:8]), rt)
        diagnostics["route_counts"]["exact_phrase"] += 1
        if return_source_rankings:
            source_lists["exact_phrase"].append((cid, score + 1 / rank, rank))

    seeds = sorted(bucket.values(), key=lambda item: item["score"], reverse=True)[:10]
    for seed in seeds:
        seed_id = seed["card_id"]
        for rank, cid in enumerate(neighbor_ids(seed_id, rt, window=2), start=1):
            add_candidate(bucket, cid, 1.5, "adjacent_card", seed_id, rt)
            diagnostics["route_counts"]["adjacent_card"] += 1
            if return_source_rankings:
                source_lists["adjacent_card"].append((cid, 1.5, rank))
        for rel in rt.relations.get(seed_id, [])[:6]:
            cid = rel.get("c")
            if cid:
                add_candidate(bucket, cid, 0.8 + min(float(rel.get("s", 0)), 2) * 0.15, "relation_expand", seed_id, rt)
                diagnostics["route_counts"]["relation_expand"] += 1

    candidates = sorted(bucket.values(), key=lambda item: item["score"], reverse=True)[:top_k]
    for item in candidates:
        item["score"] = round(item["score"], 4)
    diagnostics["route_counts"] = dict(diagnostics["route_counts"])
    diagnostics["candidate_count"] = len(candidates)

    if return_source_rankings:
        # Deduplicate per source: keep best rank per card_id
        source_rankings: dict[str, list[tuple[str, float, int]]] = {}
        for src, entries in source_lists.items():
            best: dict[str, tuple[float, int]] = {}
            for cid, score, rank in entries:
                if cid not in best or rank < best[cid][1]:
                    best[cid] = (score, rank)
            source_rankings[src] = [(cid, s, r) for cid, (s, r) in best.items()]
        return candidates, diagnostics, source_rankings

    return candidates, diagnostics


def merge_candidates(existing: list[dict[str, Any]], extra: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {item["card_id"]: dict(item) for item in existing}
    for item in extra:
        cid = item["card_id"]
        if cid in merged:
            merged[cid]["score"] = round(float(merged[cid].get("score", 0)) + float(item.get("score", 0)) * 0.5, 4)
            old_sources = merged[cid].setdefault("sources", [])
            old_sources.extend(item.get("sources", []))
            for source in item.get("source", "").split("+"):
                if source and source not in merged[cid].get("source", "").split("+"):
                    merged[cid]["source"] += f"+{source}"
        else:
            merged[cid] = item
    return sorted(merged.values(), key=lambda row: row.get("score", 0), reverse=True)[:top_k]


def format_candidate_block(label: str, candidates: list[dict[str, Any]], max_cards: int = 18) -> str:
    lines = [f"### 选项 {label} 候选教材句卡"]
    for item in candidates[:max_cards]:
        quote = item.get("citation") or item.get("knowledge") or item.get("text", "")
        context = " ".join(x for x in [item.get("context_before", ""), item.get("context_after", "")] if x)
        lines.append(
            "[{cid}] source={source} score={score} type={typ}\n"
            "knowledge: {knowledge}\n"
            "citation: {citation}\n"
            "context: {context}\n"
            "origin: {origin}".format(
                cid=item["card_id"],
                source=item.get("source", ""),
                score=item.get("score", 0),
                typ=item.get("type", ""),
                knowledge=compact_text(item.get("knowledge", ""), 180),
                citation=compact_text(quote, 240),
                context=compact_text(context, 220),
                origin=compact_text(
                    " ".join(
                        str(x)
                        for x in [
                            item.get("source_asset", ""),
                            item.get("source_line_start", ""),
                            item.get("source_line_end", ""),
                        ]
                        if x not in ("", None)
                    ),
                    220,
                ),
            )
        )
    return "\n".join(lines)


def compact_card_line(card: dict[str, Any]) -> str:
    text = card.get("citation") or card.get("knowledge") or ""
    context = " ".join(x for x in [card.get("context_before", ""), card.get("context_after", "")] if x)
    return "[{cid}] {knowledge} | {citation} | {context}".format(
        cid=card.get("card_id", ""),
        knowledge=compact_text(card.get("knowledge", ""), 120),
        citation=compact_text(text, 160),
        context=compact_text(context, 120),
    )


def build_card_scan_prompt(
    stem: str,
    options: dict[str, str],
    answer: str,
    plan: dict[str, Any],
    target_labels: list[str],
    chunk_lines: list[str],
    chunk_index: int,
    chunk_total: int,
) -> str:
    opt_text = "\n".join(f"{label}. {text}" for label, text in options.items() if label in target_labels)
    plan_rows = []
    by_label = option_plan_by_label(plan)
    for label in target_labels:
        item = by_label.get(label, {})
        plan_rows.append(
            f"{label}: claim={item.get('option_claim', options.get(label, ''))}; need={item.get('evidence_need', '')}; terms={','.join(item.get('must_terms', [])[:8])}"
        )

    return f"""你是CAMS教材句卡检索员。你只能从本片段给出的教材句卡中挑候选证据。

任务：为指定选项寻找能判断其对错的教材句卡。不要写最终解析，不要编造 card_id。

题目：{stem}
标准答案：{answer}
需要检索的选项：
{opt_text}

选项证据需求：
{chr(10).join(plan_rows)}

教材句卡片段 {chunk_index}/{chunk_total}：
{chr(10).join(chunk_lines)}

输出严格JSON，不要Markdown，不要代码块：
{{
  "matches": [
    {{
      "option": "A",
      "card_id": "必须使用本片段中真实出现的card_id",
      "support_type": "direct/indirect/context/negative",
      "relevance": "high/medium/low",
      "reason": "为什么这张卡可能支撑或反驳该选项，若只是相邻场景要说明"
    }}
  ],
  "notes": "本片段是否缺少关键证据"
}}

筛选规则：
1. card_id 必须来自上方片段。
2. 每个选项最多返回 4 张最有价值的卡。
3. direct 要非常严格：必须能直接判断选项关键事实。
4. 仅主题相近但不能判断的，标 indirect 或 context。
5. 完全无用的卡不要返回。"""


def parse_card_scan(raw_text: str, allowed_ids: set[str], target_labels: set[str]) -> list[dict[str, Any]]:
    parsed = parse_json_object(raw_text)
    if not parsed or not isinstance(parsed.get("matches"), list):
        return []
    rows = []
    for item in parsed.get("matches", []):
        if not isinstance(item, dict):
            continue
        cid = str(item.get("card_id", "")).strip()
        label = str(item.get("option", "")).strip()
        if cid not in allowed_ids or label not in target_labels:
            continue
        support_type = item.get("support_type", "context")
        if support_type not in run_step1.SUPPORT_TYPES:
            support_type = "context"
        relevance = item.get("relevance", "low")
        if relevance not in run_step1.RELEVANCE_VALUES:
            relevance = "low"
        rows.append(
            {
                "option": label,
                "card_id": cid,
                "support_type": support_type,
                "relevance": relevance,
                "reason": compact_text(item.get("reason", ""), 220),
            }
        )
    return rows


def scan_card_index_with_llm(
    rt: AgenticRuntime,
    stem: str,
    options: dict[str, str],
    answer: str,
    plan: dict[str, Any],
    mode: str,
    chunk_size: int,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    if mode == "off":
        return {}, []

    correct = run_step1.normalize_answer(answer, options)
    if mode == "correct":
        target_labels = [label for label in options if label in correct]
    else:
        target_labels = list(options)
    if not target_labels:
        return {}, []

    cards = [rt.card_by_id[cid] for cid in rt.card_ids]
    chunks = [cards[i : i + chunk_size] for i in range(0, len(cards), chunk_size)]
    matches_by_option: dict[str, list[dict[str, Any]]] = {label: [] for label in target_labels}
    logs: list[dict[str, Any]] = []

    print(f"  LLM card scan: mode={mode}, options={','.join(target_labels)}, chunks={len(chunks)}")
    for index, chunk in enumerate(chunks, start=1):
        chunk_lines = [compact_card_line(card) for card in chunk]
        allowed = {card.get("card_id", "") for card in chunk}
        prompt = build_card_scan_prompt(stem, options, answer, plan, target_labels, chunk_lines, index, len(chunks))
        try:
            raw = run_step1.call_llm(rt.base.client, prompt, CARD_SCAN_MAX_TOKENS, retries=2)
            matches = parse_card_scan(raw, allowed, set(target_labels))
        except Exception as exc:
            raw = ""
            matches = []
            logs.append({"chunk": index, "error": str(exc)[:300]})
            continue

        for match in matches:
            label = match["option"]
            cid = match["card_id"]
            card = rt.card_by_id.get(cid)
            if not card:
                continue
            support_weight = {"direct": 30.0, "negative": 24.0, "indirect": 16.0, "context": 8.0}.get(
                match["support_type"], 6.0
            )
            relevance_weight = {"high": 6.0, "medium": 3.0, "low": 1.0}.get(match["relevance"], 1.0)
            row = {
                "card_id": cid,
                "score": support_weight + relevance_weight,
                "source": "llm_card_scan",
                "sources": [
                    {
                        "source": "llm_card_scan",
                        "score": support_weight + relevance_weight,
                        "query": f"chunk {index}/{len(chunks)} {match['support_type']} {match['relevance']}",
                    }
                ],
                "type": card.get("type", ""),
                "knowledge": card.get("knowledge", ""),
                "citation": card.get("citation", ""),
                "context_before": card.get("context_before", ""),
                "context_after": card.get("context_after", ""),
                "text": card_text(card),
                "scan_support_type": match["support_type"],
                "scan_relevance": match["relevance"],
                "scan_reason": match["reason"],
            }
            matches_by_option[label].append(row)

        logs.append(
            {
                "chunk": index,
                "match_count": len(matches),
                "matches": matches,
                "raw_excerpt": compact_text(raw, 500),
            }
        )
        time.sleep(0.5)

    for label, rows in matches_by_option.items():
        deduped: dict[str, dict[str, Any]] = {}
        for row in rows:
            cid = row["card_id"]
            if cid not in deduped or row["score"] > deduped[cid]["score"]:
                deduped[cid] = row
        matches_by_option[label] = sorted(deduped.values(), key=lambda item: item.get("score", 0), reverse=True)[:12]

    return matches_by_option, logs


def build_adjudicator_prompt(
    stem: str,
    options: dict[str, str],
    answer: str,
    plan: dict[str, Any],
    candidates_by_option: dict[str, list[dict[str, Any]]],
    round_index: int,
) -> str:
    opt_text = "\n".join(f"{label}. {text}" for label, text in options.items())
    plan_summary = []
    for item in plan.get("options", []):
        plan_summary.append(
            f"{item.get('option')}: claim={item.get('option_claim')} | need={item.get('evidence_need')} | terms={','.join(item.get('must_terms', [])[:8])}"
        )
    candidate_text = "\n\n".join(format_candidate_block(label, candidates) for label, candidates in candidates_by_option.items())
    candidate_text = candidate_text[:MAX_CANDIDATE_TEXT_CHARS]

    return f"""你是CAMS选项级证据裁判和解析员。你只允许依据候选教材句卡和标准答案输出解析。

重要规则：
1. 标准答案控制 judgement：在标准答案中的选项填 correct，不在标准答案中的选项填 incorrect。除非题目或答案明显冲突，否则不要改答案。
2. evidence_cards 只能引用下方候选教材句卡中出现过的 card_id，不准编造。
3. direct 表示该句卡能直接支撑“这个选项为什么对/错”的关键事实；错误选项可用 support_type=negative 表示教材规则直接反驳该选项。
4. indirect 表示只是同类背景、泛化风险、相近案例，不能当直接教材依据。
5. none 表示候选句卡无法支撑判断。证据不足时仍要保留 explanation，但要诚实说明证据不足。
6. common_trap 是教学推断，可以基于题目和学生常见误解写；若无法推断填空。
7. 如果缺直接证据，请给出 followup_queries_by_option，供下一轮继续检索。

题目：{stem}
选项：
{opt_text}
标准答案：{answer}

检索规划摘要：
{chr(10).join(plan_summary)}

候选教材句卡：
{candidate_text}

当前是第 {round_index} 轮证据裁判。

输出严格JSON，不要Markdown，不要代码块：
{{
  "option_analysis": [
    {{
      "option": "A",
      "option_text": "选项全文",
      "judgement": "correct/incorrect/insufficient/needs_manual",
      "evidence_status": "direct/indirect/none/conflict/needs_manual",
      "evidence_cards": [
        {{
          "card_id": "必须使用候选教材句卡中真实出现的card_id",
          "support_type": "direct/indirect/context/negative",
          "source": "card_bge/bm25/exact_phrase/adjacent_card/relation_expand",
          "quote": "教材原文短摘，不超过120字",
          "reason": "为什么这张句卡能支撑或反驳该选项",
          "relevance": "high/medium/low"
        }}
      ],
      "explanation": "给教研审核用的选项级解析。没有直接证据时也要说明基于标准答案的判断逻辑和证据缺口。",
      "common_trap": "学生容易误解之处，无法推断则填空",
      "needs_teacher_review": false,
      "teacher_review_reason": ""
    }}
  ],
  "followup_queries_by_option": {{
    "A": ["如果A缺直接证据，下一轮应搜的教材表达"]
  }},
  "overall_notes": "整体证据质量说明",
  "cited_cards": ["必须使用候选教材句卡中真实出现的card_id"]
}}

必须逐一分析所有选项，共 {len(options)} 个。"""


def flatten_evidence(candidates_by_option: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for label, candidates in candidates_by_option.items():
        for item in candidates:
            cid = item.get("card_id")
            if not cid or cid in seen:
                continue
            seen.add(cid)
            row = dict(item)
            row["option_candidate_for"] = [label]
            rows.append(row)
    rows.sort(key=lambda item: item.get("score", 0), reverse=True)
    return rows


def call_adjudicator(
    rt: AgenticRuntime,
    stem: str,
    options: dict[str, str],
    answer: str,
    plan: dict[str, Any],
    candidates_by_option: dict[str, list[dict[str, Any]]],
    round_index: int,
) -> tuple[dict[str, Any] | None, str]:
    prompt = build_adjudicator_prompt(stem, options, answer, plan, candidates_by_option, round_index)
    raw = run_step1.call_llm(rt.base.client, prompt, ADJUDICATOR_MAX_TOKENS)
    return parse_json_object(raw), raw


def followup_queries(parsed: dict[str, Any] | None, options: dict[str, str], max_queries: int = 2) -> dict[str, list[str]]:
    if not parsed:
        return {}
    raw = parsed.get("followup_queries_by_option", {})
    if not isinstance(raw, dict):
        return {}
    rows: dict[str, list[str]] = {}
    for label in options:
        value = raw.get(label, [])
        if isinstance(value, str):
            value = [value]
        if isinstance(value, list):
            queries = [compact_text(str(item), 180) for item in value if compact_text(str(item), 180)]
            if queries:
                rows[label] = queries[:max_queries]
    return rows


def sanitize_option_analysis(result: dict[str, Any]) -> None:
    """Make model output obey the evidence schema before validation."""
    evidence_set = {item.get("card_id") for item in result.get("evidence", []) if item.get("card_id")}
    for option in result.get("option_analysis", []):
        evidence_cards = option.get("evidence_cards", [])
        if not isinstance(evidence_cards, list):
            evidence_cards = []

        cleaned_cards = []
        for card in evidence_cards:
            if not isinstance(card, dict):
                continue
            cid = card.get("card_id")
            if cid and cid in evidence_set:
                cleaned_cards.append(card)

        status = option.get("evidence_status")
        if status == "negative":
            status = "indirect"
            option["evidence_status"] = status
        elif status not in run_step1.EVIDENCE_STATUSES:
            status = "needs_manual"
            option["evidence_status"] = status
            option["needs_teacher_review"] = True
            option["teacher_review_reason"] = option.get("teacher_review_reason") or "模型输出了无效证据状态"

        if status == "none":
            option["evidence_cards"] = []
        else:
            option["evidence_cards"] = cleaned_cards

        if status == "direct" and not option["evidence_cards"]:
            option["evidence_status"] = "needs_manual"
            option["needs_teacher_review"] = True
            option["teacher_review_reason"] = option.get("teacher_review_reason") or "标为direct但缺少可引用教材句卡"


def extract_external_reference_hints(text: str) -> list[str]:
    if not text:
        return []
    patterns = [
        r"\b\d+\s*CFR\s*§?\s*\d+(?:\.\d+)*\b",
        r"§\s*\d+(?:\.\d+)*",
        r"\bFinCEN\b[^。；;\n]{0,80}",
        r"\bOFAC\b[^。；;\n]{0,80}",
        r"\bFATF\b[^。；;\n]{0,80}",
    ]
    hints: list[str] = []
    seen: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            item = compact_text(match.group(0), 140)
            if item and item not in seen:
                seen.add(item)
                hints.append(item)
            if len(hints) >= 8:
                return hints
    return hints


def mark_external_reference_gaps(result: dict[str, Any], teacher_explanation: str) -> None:
    hints = extract_external_reference_hints(teacher_explanation)
    if not hints:
        return
    rows: list[dict[str, Any]] = []
    for option in result.get("option_analysis", []):
        if option.get("evidence_status") not in {"none", "needs_manual", "conflict"}:
            continue
        option["external_reference_needed"] = True
        option["external_reference_hints"] = hints
        option["needs_teacher_review"] = True
        reason = option.get("teacher_review_reason", "")
        gap_reason = "教材句卡缺少直接证据，但教研解析含外部法规/机构依据线索"
        option["teacher_review_reason"] = f"{reason}; {gap_reason}".strip("; ")
        rows.append(
            {
                "option": option.get("option", ""),
                "evidence_status": option.get("evidence_status", ""),
                "hints": hints,
            }
        )
    if rows:
        result["external_reference_gaps"] = rows


def option_plan_by_label(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item.get("option"): item for item in plan.get("options", []) if isinstance(item, dict)}


def process_question(
    rt: AgenticRuntime,
    question: dict[str, Any],
    max_followups: int,
    top_k: int,
    card_scan_mode: str,
    card_scan_chunk_size: int,
    teacher_hints: bool = False,
) -> dict[str, Any]:
    qid = question["id"]
    stem = question["stem"]
    options = question["options"]
    answer = question["answer"]
    teacher_explanation = question.get("explanation", "") if teacher_hints else ""

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "question_id": qid,
        "stem": stem,
        "options": options,
        "answer": answer,
        "option_count": len(options),
        "status": "started",
        "evidence_scope": rt.base.evidence_scope,
        "evidence_file": rt.base.evidence_file,
        "teacher_hint_mode": "retrieval_only" if teacher_hints else "off",
    }
    if teacher_explanation:
        result["teacher_explanation_hint_excerpt"] = compact_text(teacher_explanation, 500)

    try:
        plan, raw_planner = call_planner(rt, stem, options, answer, teacher_explanation)
    except Exception as exc:
        plan = fallback_plan(stem, options, answer, teacher_explanation)
        raw_planner = ""
        result["planner_error"] = str(exc)[:500]

    result["raw_search_plan"] = raw_planner
    result["search_plan"] = plan

    plans = option_plan_by_label(plan)
    candidates_by_option: dict[str, list[dict[str, Any]]] = {}
    search_rounds: list[dict[str, Any]] = []
    for label, option_text in options.items():
        candidates, diagnostics = retrieve_for_option(rt, stem, option_text, plans[label], top_k=top_k)
        candidates_by_option[label] = candidates
        search_rounds.append({"round": 1, "option": label, "diagnostics": diagnostics, "candidate_ids": [c["card_id"] for c in candidates]})

    scan_matches, scan_logs = scan_card_index_with_llm(
        rt,
        stem,
        options,
        answer,
        plan,
        mode=card_scan_mode,
        chunk_size=card_scan_chunk_size,
    )
    result["llm_card_scan_logs"] = scan_logs
    for label, rows in scan_matches.items():
        if not rows:
            continue
        candidates_by_option[label] = merge_candidates(candidates_by_option.get(label, []), rows, top_k=top_k)
        search_rounds.append(
            {
                "round": "llm_card_scan",
                "option": label,
                "candidate_ids": [row["card_id"] for row in rows],
                "candidate_count": len(rows),
            }
        )

    raw_outputs: list[dict[str, Any]] = []
    parsed: dict[str, Any] | None = None
    for round_index in range(1, max_followups + 2):
        try:
            parsed, raw = call_adjudicator(rt, stem, options, answer, plan, candidates_by_option, round_index)
        except Exception as exc:
            result["adjudicator_error"] = str(exc)[:500]
            parsed, raw = None, ""
        raw_outputs.append({"round": round_index, "raw": raw, "parsed_ok": parsed is not None})

        if round_index > max_followups:
            break
        queries_by_option = followup_queries(parsed, options)
        if not queries_by_option:
            break

        for label, queries in queries_by_option.items():
            option_text = options[label]
            extra_plan = dict(plans[label])
            extra_plan["search_queries"] = queries
            extra_plan["must_terms"] = extract_phrases(option_text, " ".join(queries))
            extra, diagnostics = retrieve_for_option(rt, stem, option_text, extra_plan, top_k=top_k)
            candidates_by_option[label] = merge_candidates(candidates_by_option[label], extra, top_k=top_k)
            search_rounds.append(
                {
                    "round": round_index + 1,
                    "option": label,
                    "followup_queries": queries,
                    "diagnostics": diagnostics,
                    "candidate_ids": [c["card_id"] for c in extra],
                }
            )
        time.sleep(1)

    result["search_rounds"] = search_rounds
    result["candidates_by_option"] = {
        label: [{k: v for k, v in item.items() if k != "text"} for item in candidates]
        for label, candidates in candidates_by_option.items()
    }
    result["evidence"] = flatten_evidence(candidates_by_option)
    result["evidence_count"] = len(result["evidence"])
    result["raw_agentic_outputs"] = raw_outputs

    option_analysis = parsed.get("option_analysis", []) if parsed else None
    if not isinstance(option_analysis, list):
        result["status"] = "parse_failed"
        result["option_analysis"] = run_step1.build_insufficient_options(
            options,
            answer,
            "agentic evidence adjudicator 输出无法解析",
            "parse_failed",
        )
        for option in result["option_analysis"]:
            option["judgement"] = "needs_manual"
            option["evidence_status"] = "needs_manual"
            option["needs_teacher_review"] = True
            option["teacher_review_reason"] = "parse_failed"
    else:
        result["option_analysis"] = option_analysis
        result["overall_notes"] = parsed.get("overall_notes", "")

    run_step1.ensure_option_defaults(result)
    sanitize_option_analysis(result)
    mark_external_reference_gaps(result, teacher_explanation)
    result["cited_cards"] = sorted(
        {
            card.get("card_id", "")
            for option in result.get("option_analysis", [])
            for card in option.get("evidence_cards", [])
            if card.get("card_id")
        }
    )
    result["ai3_output"] = json.dumps(result.get("option_analysis", []), ensure_ascii=False)
    result["validation_issues"] = run_step1.validate_option_analysis(result, rt.base.valid_card_ids)
    result["status"] = run_step1.classify_status(result)
    result["quality"] = run_step1.summarize_quality(result, rt.base.valid_card_ids)
    return result


def baseline_summary(qid: str) -> dict[str, Any] | None:
    path = run_step1.SAVE_DIR / f"q_{qid}.json"
    if not path.exists():
        return None
    try:
        data = run_step1.read_json(path)
    except Exception:
        return None
    quality = data.get("quality", {})
    return {
        "status": data.get("status"),
        "direct": quality.get("direct_evidence_options", 0),
        "indirect": quality.get("indirect_evidence_options", 0),
        "none": quality.get("none_evidence_options", 0),
        "cited_cards": data.get("cited_cards", []),
    }


def output_path(qid: str) -> Path:
    return SAVE_DIR / f"q_{qid}.json"


def select_questions(rt: AgenticRuntime, ids: list[str] | None, limit: int | None) -> list[dict[str, Any]]:
    wanted = set(ids or [])
    selected = []
    for question in rt.base.questions:
        if wanted and question["id"] not in wanted:
            continue
        selected.append(question)
        if limit is not None and len(selected) >= limit:
            break
    return selected


def main(
    ids: list[str] | None = None,
    limit: int | None = None,
    force: bool = False,
    max_followups: int = 1,
    top_k: int = 24,
    card_scan_mode: str = "off",
    card_scan_chunk_size: int = 160,
    evidence_scope: str = "ch2",
    teacher_hints: bool = False,
    output_dir: Path | None = None,
) -> int:
    save_dir = output_dir or SAVE_DIR
    save_dir.mkdir(parents=True, exist_ok=True)
    rt = load_agentic_runtime(evidence_scope=evidence_scope)
    selected = select_questions(rt, ids, limit)
    print(f"Agentic search experiment todo: {len(selected)}")

    for index, question in enumerate(selected, start=1):
        qid = question["id"]
        path = save_dir / f"q_{qid}.json"
        if path.exists() and not force:
            print(f"[{index}/{len(selected)}] {qid}: skip existing {path.name}")
            continue

        print(f"[{index}/{len(selected)}] {qid}: {question['stem'][:50]}...")
        result = process_question(
            rt,
            question,
            max_followups=max_followups,
            top_k=top_k,
            card_scan_mode=card_scan_mode,
            card_scan_chunk_size=card_scan_chunk_size,
            teacher_hints=teacher_hints,
        )
        run_step1.write_json(path, result)

        quality = result.get("quality", {})
        base = baseline_summary(qid)
        base_text = ""
        if base:
            base_text = f" | baseline {base['status']} d/i/n={base['direct']}/{base['indirect']}/{base['none']}"
        print(
            "  -> {status} d/i/n={direct}/{indirect}/{none} cited={cited} issues={issues}{base}".format(
                status=result.get("status"),
                direct=quality.get("direct_evidence_options", 0),
                indirect=quality.get("indirect_evidence_options", 0),
                none=quality.get("none_evidence_options", 0),
                cited=len(result.get("cited_cards", [])),
                issues=len(result.get("validation_issues", [])),
                base=base_text,
            )
        )
    print(f"\nDone. Experiment results in {save_dir}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run option-level agentic search experiment.")
    parser.add_argument("--ids", nargs="*", help="Question ids to run, for example 2.1_1 2.1_2.")
    parser.add_argument("--limit", type=int, help="Maximum question count.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing experiment output.")
    parser.add_argument("--max-followups", type=int, default=1, help="Follow-up search rounds after first adjudication.")
    parser.add_argument("--top-k", type=int, default=24, help="Candidate cards kept per option.")
    parser.add_argument(
        "--card-scan",
        choices=["off", "correct", "all"],
        default="off",
        help="Use LLM chunk scan over the selected textbook sentence-card pool as an extra retrieval route.",
    )
    parser.add_argument("--card-scan-chunk-size", type=int, default=160, help="Cards per LLM card-scan chunk.")
    parser.add_argument(
        "--evidence-scope",
        choices=sorted(run_step1.EVIDENCE_FILES),
        default="ch2",
        help="Textbook evidence pool. ch2 preserves old behavior; v6-sentence uses full V6 sentence-level evidence cards.",
    )
    parser.add_argument(
        "--teacher-hints",
        action="store_true",
        help="Use question.explanation only as retrieval query hints. It is never accepted as textbook evidence.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional output directory for comparison runs. Defaults to output/agentic_search_experiment.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(
        main(
            ids=args.ids,
            limit=args.limit,
            force=args.force,
            max_followups=args.max_followups,
            top_k=args.top_k,
            card_scan_mode=args.card_scan,
            card_scan_chunk_size=args.card_scan_chunk_size,
            evidence_scope=args.evidence_scope,
            teacher_hints=args.teacher_hints,
            output_dir=args.output_dir,
        )
    )
