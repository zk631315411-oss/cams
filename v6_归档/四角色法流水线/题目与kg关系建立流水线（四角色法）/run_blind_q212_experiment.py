"""
Blind 2.1_2 experiment.

Purpose:
Test whether an LLM can find option-level textbook evidence and write a usable
explanation when it sees only the question stem and options, with no standard
answer and no existing explanation.

This script intentionally writes to a separate output directory and does not
modify the formal step1 outputs.
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import run_agentic_search_experiment as agentic
import run_step1


SAVE_DIR = run_step1.BASE / "output" / "blind_no_answer_experiment"
TARGET_QID = "2.1_2"
PLANNER_MAX_TOKENS = 5000
ADJUDICATOR_MAX_TOKENS = 9000

BLIND_QUESTION = {
    "id": TARGET_QID,
    "stem": "资金转移的危险信号是什么?",
    "options": {
        "A": "从相关行业的实体收到大量小额的资金转移",
        "B": "资金转账重复发送给同一受益人，与业务目的不符",
        "C": "资金转移是重复性的，符合预期模式",
        "D": "资金转移到已知同行业内位于风险地区的供应商发起人",
    },
}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_agentic_runtime_without_questions() -> agentic.AgenticRuntime:
    """Load KG/cards/retrievers without loading questions.json."""
    api_key, base_url, env_name = run_step1.get_deepseek_config()

    from openai import OpenAI
    from sentence_transformers import SentenceTransformer

    print(f"Loading KG and textbook cards only... DeepSeek key source: {env_name}, base_url: {base_url}")
    sections = run_step1.read_json(run_step1.KG_DIR / "sections.json")
    edges = run_step1.read_json(run_step1.KG_DIR / "edges.json")
    cs_map = run_step1.read_json(run_step1.KG_DIR / "card_section_map.json")

    raw_cards = run_step1.read_json(run_step1.DATA / "cards_ch2.json")
    cards = raw_cards.get("cards", raw_cards) if isinstance(raw_cards, dict) else raw_cards
    if not isinstance(cards, list):
        raise ValueError("cards_ch2.json 既不是数组，也不是包含 cards 数组的对象。")

    card_ctx: dict[str, str] = {}
    for card in cards:
        cid = card.get("card_id")
        if not cid:
            continue
        parts = [
            card.get("context_before", ""),
            card.get("knowledge", ""),
            card.get("citation", ""),
            card.get("context_after", ""),
        ]
        card_ctx[cid] = " ".join(x for x in parts if x)
    valid_card_ids = set(card_ctx)

    section_titles = [s.get("subsection_title", "") for s in sections]
    edge_index: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        src = edge.get("from_subsection", "")
        tgt = edge.get("to_subsection", "")
        edge_index.setdefault(src, []).append(edge)
        if tgt:
            edge_index.setdefault(tgt, []).append({**edge, "from_subsection": tgt, "to_subsection": src})

    bge = SentenceTransformer("BAAI/bge-small-zh-v1.5", local_files_only=True)
    section_queries = [
        title + " " + section.get("definition", "") + " " + " ".join(section.get("aliases", []))
        for section, title in zip(sections, section_titles)
    ]
    section_vecs = bge.encode(section_queries, normalize_embeddings=True)

    base = run_step1.Runtime(
        sections=sections,
        edges=edges,
        section_to_cards=cs_map["section_to_cards"],
        cards=cards,
        questions=[],
        card_ctx=card_ctx,
        valid_card_ids=valid_card_ids,
        section_titles=section_titles,
        edge_index=edge_index,
        bge=bge,
        section_vecs=section_vecs,
        client=OpenAI(api_key=api_key, base_url=base_url),
        evidence_scope="blind-v6-cards",
        evidence_file=str(run_step1.DATA / "cards_ch2.json"),
    )

    card_by_id = {card["card_id"]: card for card in base.cards if card.get("card_id")}
    card_ids = list(card_by_id)
    card_texts = [agentic.card_text(card_by_id[cid]) for cid in card_ids]

    print(f"Encoding {len(card_texts)} textbook sentence cards for card-level BGE...")
    card_vecs = base.bge.encode(card_texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)

    bm25_docs = [Counter(agentic.tokenize(text)) for text in card_texts]
    bm25_df: Counter[str] = Counter()
    for doc in bm25_docs:
        bm25_df.update(doc.keys())
    bm25_avgdl = sum(sum(doc.values()) for doc in bm25_docs) / max(len(bm25_docs), 1)

    relations_path = run_step1.DATA / "card_relations.json"
    relations = run_step1.read_json(relations_path) if relations_path.exists() else {}

    return agentic.AgenticRuntime(
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


def build_blind_planner_prompt(stem: str, options: dict[str, str]) -> str:
    opt_text = "\n".join(f"{label}. {text}" for label, text in options.items())
    return f"""你是CAMS教材证据检索规划员。

你只能看到题目和选项；你看不到标准答案，也看不到题库解析。
你的任务不是先猜答案，而是为每个选项设计教材证据搜索计划。

严禁：
- 不要引用或猜测题库标准答案。
- 不要说“根据标准答案”。
- 不要编造 card_id。
- 不要使用既有解析、题库文件、历史输出作为依据。

请输出严格JSON，不要Markdown，不要代码块。

题目：{stem}
选项：
{opt_text}

输出格式：
{{
  "question_focus": "本题考的核心概念、风险场景或判断标准",
  "options": [
    {{
      "option": "A",
      "option_claim": "把选项改写成一个需要教材证据判断的命题",
      "evidence_need": "需要找哪类教材原文才能判断此选项",
      "search_queries": ["用教材术语写的查询1", "查询2", "查询3"],
      "must_terms": ["关键术语"],
      "related_terms": ["同义词、上位词、近义场景"],
      "contrast_terms": ["容易混淆但需要比较或排除的概念"],
      "avoid_confusions": ["检索时容易误抓的噪声"]
    }}
  ]
}}

要求：
1. 每个选项都必须出现，顺序与原题一致。
2. 查询词要尽量贴近教材可能出现的表达，不要只复制选项原话。
3. 如果选项含有“符合预期模式”“与业务目的不符”“风险地区”等限定词，要作为判断关键。"""


def fallback_blind_plan(stem: str, options: dict[str, str]) -> dict[str, Any]:
    rows = []
    for label, text in options.items():
        terms = agentic.extract_phrases(stem, text)
        rows.append(
            {
                "option": label,
                "option_claim": text,
                "evidence_need": f"判断该选项是否符合题干：{stem}",
                "search_queries": [f"{stem} {text}", text, " ".join(terms[:8])],
                "must_terms": terms[:6],
                "related_terms": [],
                "contrast_terms": [],
                "avoid_confusions": [],
            }
        )
    return {"question_focus": stem, "options": rows}


def normalize_blind_plan(plan: dict[str, Any] | None, stem: str, options: dict[str, str]) -> dict[str, Any]:
    if not isinstance(plan, dict) or not isinstance(plan.get("options"), list):
        return fallback_blind_plan(stem, options)

    fallback = fallback_blind_plan(stem, options)
    by_label = {str(item.get("option", "")).strip(): item for item in plan.get("options", []) if isinstance(item, dict)}
    normalized = {"question_focus": plan.get("question_focus") or fallback["question_focus"], "options": []}
    for fb in fallback["options"]:
        label = fb["option"]
        item = by_label.get(label, {})
        merged = {**fb, **item}
        merged["option"] = label
        for field in ["search_queries", "must_terms", "related_terms", "contrast_terms", "avoid_confusions"]:
            value = merged.get(field)
            if not isinstance(value, list):
                value = []
            merged[field] = [str(x).strip() for x in value if str(x).strip()]
        if not merged["search_queries"]:
            merged["search_queries"] = fb["search_queries"]
        normalized["options"].append(merged)
    return normalized


def call_blind_planner(rt: agentic.AgenticRuntime, stem: str, options: dict[str, str]) -> tuple[dict[str, Any], str]:
    raw = run_step1.call_llm(rt.base.client, build_blind_planner_prompt(stem, options), PLANNER_MAX_TOKENS)
    parsed = agentic.parse_json_object(raw)
    return normalize_blind_plan(parsed, stem, options), raw


def build_blind_adjudicator_prompt(
    stem: str,
    options: dict[str, str],
    plan: dict[str, Any],
    candidates_by_option: dict[str, list[dict[str, Any]]],
) -> str:
    opt_text = "\n".join(f"{label}. {text}" for label, text in options.items())
    plan_summary = []
    for item in plan.get("options", []):
        plan_summary.append(
            f"{item.get('option')}: claim={item.get('option_claim')} | need={item.get('evidence_need')} | terms={','.join(item.get('must_terms', [])[:8])}"
        )
    candidate_text = "\n\n".join(
        agentic.format_candidate_block(label, candidates)
        for label, candidates in candidates_by_option.items()
    )
    candidate_text = candidate_text[: agentic.MAX_CANDIDATE_TEXT_CHARS]

    return f"""你是CAMS选项级证据裁判和解析员。

你只能看到题目、选项、检索计划和候选教材句卡；你看不到标准答案，也看不到题库解析。

严禁：
1. 不要写“标准答案是”或“根据标准答案”。
2. 不要使用任何未提供的题库解析。
3. evidence_cards 只能引用下方候选教材句卡中出现过的 card_id。
4. direct 必须非常严格：句卡能直接判断选项关键事实。
5. 如果无法仅凭教材句卡判断，judgement 填 insufficient 或 needs_manual。

题目：{stem}
选项：
{opt_text}

检索规划摘要：
{chr(10).join(plan_summary)}

候选教材句卡：
{candidate_text}

输出严格JSON，不要Markdown，不要代码块：
{{
  "predicted_answer": ["A"],
  "predicted_answer_confidence": "high/medium/low/insufficient",
  "option_analysis": [
    {{
      "option": "A",
      "option_text": "选项全文",
      "judgement": "correct/incorrect/insufficient/needs_manual",
      "judgement_confidence": "high/medium/low/insufficient",
      "evidence_status": "direct/indirect/none/conflict/needs_manual",
      "evidence_cards": [
        {{
          "card_id": "v6_bXX_NXX",
          "support_type": "direct/indirect/context/negative",
          "source": "card_bge/bm25/exact_phrase/adjacent_card/relation_expand",
          "quote": "教材原文短摘，不超过120字",
          "reason": "为什么这张句卡能支撑或反驳该选项",
          "relevance": "high/medium/low"
        }}
      ],
      "explanation": "只基于题目、选项和教材句卡写为什么该选项更可能正确/错误；证据不足时明说不足。",
      "common_trap": "学生容易误解之处，无法推断则填空",
      "needs_teacher_review": false,
      "teacher_review_reason": ""
    }}
  ],
  "overall_notes": "整体证据质量说明",
  "cited_cards": ["v6_bXX_NXX"]
}}

必须逐一分析所有选项，共 {len(options)} 个。"""


def sanitize_blind_result(result: dict[str, Any], options: dict[str, str]) -> None:
    evidence_set = {item.get("card_id") for item in result.get("evidence", []) if item.get("card_id")}
    allowed_judgements = {"correct", "incorrect", "insufficient", "needs_manual"}
    allowed_statuses = run_step1.EVIDENCE_STATUSES
    allowed_supports = run_step1.SUPPORT_TYPES

    rows = result.get("option_analysis", [])
    if not isinstance(rows, list):
        rows = []
    by_label = {str(row.get("option", "")).strip(): row for row in rows if isinstance(row, dict)}

    normalized = []
    for label, text in options.items():
        row = by_label.get(label, {"option": label})
        row["option"] = label
        row["option_text"] = text
        if row.get("judgement") not in allowed_judgements:
            row["judgement"] = "needs_manual"
        if row.get("evidence_status") not in allowed_statuses:
            row["evidence_status"] = "needs_manual"

        cards = row.get("evidence_cards", [])
        if not isinstance(cards, list):
            cards = []
        cleaned = []
        for card in cards:
            if not isinstance(card, dict):
                continue
            cid = card.get("card_id")
            if cid not in evidence_set:
                continue
            if card.get("support_type") not in allowed_supports:
                card["support_type"] = "context"
            if card.get("relevance") not in run_step1.RELEVANCE_VALUES:
                card["relevance"] = "low"
            cleaned.append(card)
        if row["evidence_status"] == "none":
            cleaned = []
        row["evidence_cards"] = cleaned
        row.setdefault("judgement_confidence", "")
        row.setdefault("common_trap", "")
        row.setdefault("needs_teacher_review", False)
        row.setdefault("teacher_review_reason", "")
        normalized.append(row)

    result["option_analysis"] = normalized
    result["cited_cards"] = sorted(
        {
            card.get("card_id", "")
            for row in normalized
            for card in row.get("evidence_cards", [])
            if card.get("card_id")
        }
    )
    if not isinstance(result.get("predicted_answer"), list):
        result["predicted_answer"] = [
            row["option"]
            for row in normalized
            if row.get("judgement") == "correct"
        ]


def leakage_check(data: dict[str, Any]) -> list[str]:
    text = json.dumps(data, ensure_ascii=False)
    issues = []
    leaked_patterns = [
        "标准答案",
        "根据答案",
        "根据标准答案",
        "题库解析",
        "现有解析",
        "答案:B",
        "答案：B",
    ]
    for pattern in leaked_patterns:
        if pattern in text:
            issues.append(f"contains leaked phrase: {pattern}")
    return issues


def wording_check(data: dict[str, Any]) -> list[str]:
    text = json.dumps(
        {
            "raw_search_plan": data.get("raw_search_plan", ""),
            "raw_blind_adjudicator_output": data.get("raw_blind_adjudicator_output", ""),
            "option_analysis": data.get("option_analysis", []),
            "overall_notes": data.get("overall_notes", ""),
        },
        ensure_ascii=False,
    )
    return ["model used phrase: 正确答案"] if "正确答案" in text else []


def main() -> int:
    rt = load_agentic_runtime_without_questions()
    question = BLIND_QUESTION
    stem = question["stem"]
    options = question["options"]

    result: dict[str, Any] = {
        "schema_version": "blind_no_answer_v1",
        "question_id": TARGET_QID,
        "stem": stem,
        "options": options,
        "blind_input_contract": {
            "standard_answer_visible_to_llm": False,
            "existing_explanation_visible_to_llm": False,
            "questions_json_loaded": False,
            "question_fields_used": ["hardcoded_blind_id", "stem", "options"],
            "forbidden_fields": ["answer", "explanation", "questions.json"],
        },
    }

    plan, raw_plan = call_blind_planner(rt, stem, options)
    result["raw_search_plan"] = raw_plan
    result["search_plan"] = plan

    plans = agentic.option_plan_by_label(plan)
    candidates_by_option: dict[str, list[dict[str, Any]]] = {}
    search_rounds: list[dict[str, Any]] = []
    for label, option_text in options.items():
        candidates, diagnostics = agentic.retrieve_for_option(rt, stem, option_text, plans[label], top_k=30)
        candidates_by_option[label] = candidates
        search_rounds.append(
            {
                "option": label,
                "diagnostics": diagnostics,
                "candidate_ids": [c["card_id"] for c in candidates],
            }
        )

    result["search_rounds"] = search_rounds
    result["candidates_by_option"] = {
        label: [{k: v for k, v in item.items() if k != "text"} for item in candidates]
        for label, candidates in candidates_by_option.items()
    }
    result["evidence"] = agentic.flatten_evidence(candidates_by_option)
    result["evidence_count"] = len(result["evidence"])

    raw_adjudicator = run_step1.call_llm(
        rt.base.client,
        build_blind_adjudicator_prompt(stem, options, plan, candidates_by_option),
        ADJUDICATOR_MAX_TOKENS,
    )
    result["raw_blind_adjudicator_output"] = raw_adjudicator
    parsed = agentic.parse_json_object(raw_adjudicator) or {}
    result.update(parsed)
    sanitize_blind_result(result, options)
    result["leakage_issues"] = leakage_check(result)
    result["wording_issues"] = wording_check(result)

    out_path = SAVE_DIR / f"q_{TARGET_QID}.json"
    write_json(out_path, result)
    print(f"Wrote {out_path}")
    print(json.dumps(
        {
            "question_id": result["question_id"],
            "predicted_answer": result.get("predicted_answer"),
            "predicted_answer_confidence": result.get("predicted_answer_confidence"),
            "evidence_count": result.get("evidence_count"),
            "cited_cards": result.get("cited_cards"),
            "leakage_issues": result.get("leakage_issues"),
            "wording_issues": result.get("wording_issues"),
            "option_judgements": [
                {
                    "option": row.get("option"),
                    "judgement": row.get("judgement"),
                    "confidence": row.get("judgement_confidence"),
                    "evidence_status": row.get("evidence_status"),
                    "cards": [card.get("card_id") for card in row.get("evidence_cards", [])],
                }
                for row in result.get("option_analysis", [])
            ],
        },
        ensure_ascii=False,
        indent=2,
    ))
    time.sleep(0.1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
