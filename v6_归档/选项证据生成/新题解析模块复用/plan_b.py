"""Plan B: 答案知情证据定位。

盲判裁判给出 AI 答案后，如果与题库答案不一致，Plan B 做两件事：
1. 扩大候选池 — 对不一致的选项做聚焦检索（更宽 window、更低 KG 阈值）
2. 反向精读 — flash+high 已知答案，在扩池中定位最有说服力的证据

结果写入 result["pipeline"]["plan_b"]，不覆盖裁判原判。
"""
from __future__ import annotations

import json
from typing import Any

from pipeline import run_pipeline as nq


def _mismatched_options(
    stem: str,
    options: dict[str, str],
    answer_key: list[str],
    ai_answer: list[str],
    option_analysis: list[dict[str, Any]],
) -> dict[str, str]:
    """Return {option_label: "support"|"refute"} for mismatched options.

    "support": option is in answer key but AI missed or downgraded it
    "refute":  option is in AI answer but not in answer key
    """
    key_set = set(answer_key)
    ai_set = set(ai_answer)
    mismatched: dict[str, str] = {}

    for label in options:
        in_key = label in key_set
        in_ai = label in ai_set
        if in_key and not in_ai:
            mismatched[label] = "support"  # 漏选：找支持证据
        elif in_ai and not in_key:
            mismatched[label] = "refute"   # 误选：找反驳证据
        elif in_key and in_ai:
            # 答案一致但可能证据不足，也扩一下
            row = next((r for r in option_analysis
                        if isinstance(r, dict) and r.get("option") == label), {})
            if row.get("evidence_grade") in ("indirect_context", "needs_manual", None):
                mismatched[label] = "support"

    return mismatched


def expand_pool_for_plan_b(
    rt: Any,
    kg: Any,
    stem: str,
    options: dict[str, str],
    mismatched: dict[str, str],
    *,
    top_k: int = 45,
    kg_node_top_k: int = 8,
    kg_max_cards_per_option: int = 10,
    kg_neighbor_limit: int = 4,
    kg_node_score_threshold: float = 0.43,
) -> dict[str, list[dict[str, Any]]]:
    """Per-option targeted retrieval with wider parameters.

    Returns {option_label: [candidate, ...]}
    """
    import run_agentic_search_experiment as agentic

    expanded: dict[str, list[dict[str, Any]]] = {}
    plan_b_window = 5   # wider than default (3)
    plan_b_kg_threshold = kg_node_score_threshold * 0.8  # lower bar

    for label, direction in mismatched.items():
        option_text = options.get(label, "")
        query_text = f"{stem[:120]} {option_text}"
        must_terms = agentic.extract_phrases(stem, option_text, max_terms=12)

        query_plan: dict[str, Any] = {
            "search_queries": [query_text[:300]],
            "option_claim": option_text[:200],
            "evidence_need": f"{'支持' if direction == 'support' else '反驳'}选项{label}",
            "must_terms": must_terms,
            "related_terms": [],
            "contrast_terms": [],
        }

        candidates, _diag, source_rankings = agentic.retrieve_for_option(
            rt, stem, option_text, query_plan,
            top_k=top_k, return_source_rankings=True,
        )

        # Build union candidates (same logic as retrieve_for_question Phase A)
        merged: dict[str, dict[str, Any]] = {}
        for src_key in ("card_bge", "bm25"):
            for cid, score, _rank in source_rankings.get(src_key, []):
                if cid not in merged or score > merged[cid].get("_best_score", -999):
                    card = rt.card_by_id.get(cid)
                    if card is None:
                        continue
                    merged[cid] = {
                        "card_id": cid,
                        "score": score,
                        "source": src_key,
                        "sources": [{"source": src_key, "score": round(score, 4)}],
                        "type": card.get("type", ""),
                        "knowledge": card.get("knowledge", ""),
                        "citation": card.get("citation", ""),
                        "_best_score": score,
                    }
        for src_key in ("exact_phrase", "adjacent_card"):
            for cid, score, _rank in source_rankings.get(src_key, []):
                if cid in merged:
                    merged[cid]["score"] += score * 0.5
                    merged[cid]["source"] += "+" + src_key
                    merged[cid].setdefault("sources", []).append(
                        {"source": src_key, "score": round(score, 4)})
                else:
                    card = rt.card_by_id.get(cid)
                    if card is None:
                        continue
                    merged[cid] = {
                        "card_id": cid,
                        "score": score,
                        "source": src_key,
                        "sources": [{"source": src_key, "score": round(score, 4)}],
                        "type": card.get("type", ""),
                        "knowledge": card.get("knowledge", ""),
                        "citation": card.get("citation", ""),
                        "_best_score": score,
                    }

        # KG recall
        if kg is not None:
            from run_bindings import kg_recall_for_option
            kg_extra, _ = kg_recall_for_option(
                kg=kg, rt=rt, stem=stem, option_text=option_text,
                option_plan=query_plan,
                top_k_nodes=kg_node_top_k,
                max_cards=kg_max_cards_per_option,
                neighbor_limit=kg_neighbor_limit,
                threshold=plan_b_kg_threshold,
            )
            for kc in kg_extra:
                cid = kc.get("card_id", "")
                if cid in merged:
                    merged[cid]["score"] = float(merged[cid].get("score", 0)) + float(kc.get("score", 0)) * 0.35
                elif cid in rt.card_by_id:
                    merged[cid] = kc

        # Neighbor expansion with wider window
        from run_bindings import _card_adjacency
        if _card_adjacency:
            from retrieval.card_graph import expand_with_neighbors
            candidates_list = sorted(merged.values(), key=lambda c: c.get("score", 0), reverse=True)
            candidates_list = expand_with_neighbors(
                candidates_list, _card_adjacency, rt.card_by_id, window=plan_b_window,
            )
            expanded[label] = candidates_list[:top_k]
        else:
            expanded[label] = sorted(merged.values(), key=lambda c: c.get("score", 0), reverse=True)[:top_k]

    return expanded


def _format_candidate_block(candidates: list[dict[str, Any]], max_cards: int = 40) -> str:
    """Format candidate cards as a compact text block for the prompt."""
    lines: list[str] = []
    for i, c in enumerate(candidates[:max_cards]):
        cid = c.get("card_id", "")
        knowledge = str(c.get("knowledge", "") or "").strip()
        citation = str(c.get("citation", "") or "").strip()
        text = f"[{i}] {cid}"
        if knowledge:
            text += f" | {knowledge}"
        text += f"\n    {citation[:300]}"
        lines.append(text)
    return "\n".join(lines)


def build_plan_b_prompt(
    stem: str,
    options: dict[str, str],
    answer_key: list[str],
    option_analysis: list[dict[str, Any]],
    expanded_pool: dict[str, list[dict[str, Any]]],
    original_pool: list[dict[str, Any]],
) -> str:
    """Build the Plan B reverse close-reading prompt."""
    opt_text = "\n".join(f"{label}. {text}" for label, text in options.items())
    key_str = ",".join(sorted(answer_key))

    # Format original adjudicator analysis
    analysis_lines: list[str] = []
    for row in option_analysis:
        label = row.get("option", "")
        judgement = row.get("judgement", "")
        evidence_cards = row.get("evidence_cards", []) or []
        explanation = str(row.get("explanation", "") or "")[:200]
        card_str = ", ".join(c.get("card_id", "") for c in evidence_cards[:5]) or "无"
        analysis_lines.append(
            f"  选项{label}: 裁判判为 {judgement}\n"
            f"    引用卡: {card_str}\n"
            f"    裁判理由: {explanation}"
        )

    # Merge expanded + original pool, dedup by card_id
    seen: set[str] = set()
    all_cards: list[dict[str, Any]] = []
    for label_pool in expanded_pool.values():
        for c in label_pool:
            cid = c.get("card_id", "")
            if cid not in seen:
                seen.add(cid)
                all_cards.append(c)
    for c in original_pool:
        cid = c.get("card_id", "")
        if cid not in seen:
            seen.add(cid)
            all_cards.append(c)

    candidate_text = _format_candidate_block(all_cards, max_cards=50)

    return f"""你是CAMS证据定位员（答案知情模式）。

题库标准答案是 [{key_str}]。下面列出了盲判裁判的原判断和扩池后的候选教材句卡。

你的任务：
1. 为题库答案中的每个正确选项，在候选池中找到最有说服力的教材原文证据
2. 为裁判误选的选项，找到为什么该选项不成立的教材依据
3. 如果候选池中确实找不到某选项的直接证据，诚实标注 insufficient

严禁：
- 不要因为看到了题库答案就强行编造证据——只能引用候选池中出现的 card_id
- 不要写"标准答案是"或"根据标准答案"

题干：{stem}

选项：
{opt_text}

盲判裁判原判断：
{chr(10).join(analysis_lines)}

候选教材句卡（扩池后，去重）：
{candidate_text}

输出严格JSON，不要Markdown：
{{
  "evidence_found": true,
  "option_analysis": [
    {{
      "option": "A",
      "option_text": "选项全文",
      "plan_b_judgement": "correct/incorrect/insufficient",
      "evidence_status": "direct/indirect/none",
      "evidence_cards": [
        {{
          "card_id": "v6_bXX_NXX",
          "support_type": "direct/indirect/context/negative",
          "quote": "教材原文短摘，不超过120字",
          "reason": "为什么这张卡能支持或反驳该选项（已知正确答案的前提下）",
          "relevance": "high/medium/low"
        }}
      ],
      "new_card_ids": ["v6_bXX_NXX"],
      "explanation": "基于扩池后证据的判断",
      "is_new_evidence": true
    }}
  ],
  "recommend_override": ["A"],
  "overall_notes": "Plan B 证据质量总结",
  "still_insufficient_options": ["B"]
}}

必须逐一分析所有选项，共 {len(options)} 个。new_card_ids 列出本次新发现的卡（不在裁判原引用中的卡）。

recommend_override 只能是题库答案 [{key_str}] 中有充分证据的选项子集。如果即使扩池后某答案选项仍无直接证据，不要将其放入 recommend_override，也不要推荐非答案选项。"""


def run_plan_b(
    rt: Any,
    kg: Any,
    client: Any,
    stem: str,
    options: dict[str, str],
    answer_key: str,
    candidates: list[dict[str, Any]],
    option_analysis: list[dict[str, Any]],
    final_ai_answer: list[str],
    *,
    top_k: int = 45,
) -> dict[str, Any]:
    """Main Plan B entry point. Expand pool + reverse close-read.

    Returns a dict to be stored at result["pipeline"]["plan_b"].
    """
    from stages.llm import call_llm_compat as _call_llm

    _key_labels = nq._normalize_answer_labels(answer_key, options)
    _ai_labels = list(final_ai_answer)

    # 1. Identify mismatched options
    mismatched = _mismatched_options(stem, options, _key_labels, _ai_labels, option_analysis)

    if not mismatched:
        return {
            "applied": False,
            "reason": "no_mismatched_options",
            "mismatched_options": {},
            "expanded_candidates": {},
            "option_analysis": [],
        }

    # 2. Expand candidate pool for mismatched options
    expanded = expand_pool_for_plan_b(
        rt, kg, stem, options, mismatched,
        top_k=top_k,
    )

    # 3. Build prompt & call LLM
    prompt = build_plan_b_prompt(
        stem, options, _key_labels, option_analysis, expanded, candidates,
    )

    raw = ""
    try:
        raw = _call_llm(client, prompt, max_tokens=6000, stage="plan_b")
    except Exception as exc:
        return {
            "applied": True,
            "status": "error",
            "error": str(exc)[:500],
            "mismatched_options": {k: v for k, v in mismatched.items()},
            "expanded_card_ids": {
                k: [c.get("card_id", "") for c in v]
                for k, v in expanded.items()
            },
            "raw_output": "",
            "option_analysis": [],
        }

    # 4. Parse
    import run_agentic_search_experiment as agentic
    parsed = agentic.parse_json_object(raw) or {}

    new_card_ids: set[str] = set()
    original_card_ids: set[str] = set()
    for row in option_analysis:
        for ec in (row.get("evidence_cards") or []):
            if isinstance(ec, dict) and ec.get("card_id"):
                original_card_ids.add(ec["card_id"])

    for row in (parsed.get("option_analysis") or []):
        if isinstance(row, dict):
            for cid in (row.get("new_card_ids") or []):
                new_card_ids.add(cid)

    return {
        "applied": True,
        "status": "done",
        "mismatched_options": {k: v for k, v in mismatched.items()},
        "expanded_card_ids": {
            k: [c.get("card_id", "") for c in v]
            for k, v in expanded.items()
        },
        "expanded_card_count": sum(len(v) for v in expanded.values()),
        "raw_output": raw,
        "option_analysis": parsed.get("option_analysis", []),
        "evidence_found": parsed.get("evidence_found", False),
        "recommend_override": parsed.get("recommend_override", []),
        "overall_notes": parsed.get("overall_notes", ""),
        "still_insufficient_options": parsed.get("still_insufficient_options", []),
        "new_card_ids": sorted(new_card_ids),
        "original_card_count": len(original_card_ids),
        "new_card_count": len(new_card_ids - original_card_ids),
    }
