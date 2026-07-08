"""
Step 1: run the four-role pipeline and save option-level textbook evidence.

Flow:
AI #1 association -> AI #2 claim/query extraction -> BGE retrieval -> AI #3
isolated JSON adjudication.

The final evidence field must point to real textbook evidence card_id values.
KG and card relations are retrieval/navigation aids only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.modules.setdefault("run_step1", sys.modules[__name__])

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


MODEL = os.environ.get("DS_MODEL") or "deepseek-v4-pro"
SCHEMA_VERSION = "option_binding_v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
BGE_SCORE_THRESHOLD = 0.45
EVIDENCE_MAX_CHARS = 20000
AI3_MAX_TOKENS = 8000
AI3_RETRY = 2
LLM_RETRY = 3
# 仅 deepseek 系列需要 thinking 参数；其他模型（如 gpt5.4）传空 dict
V4_NO_THINK = {"thinking": {"type": "disabled"}} if MODEL.lower().startswith("deepseek") else {}

_HERE = Path(__file__).resolve().parent
BASE = _HERE
_WORKSPACE = _HERE.parents[1]  # cams工作台（重构版）/
DATA = _WORKSPACE / "data"
KG_DIR = _WORKSPACE / "data" / "derived"
SAVE_DIR = _HERE / "output" / "step1_ai_responses"
EVIDENCE_FILES = {
    "ch2": _WORKSPACE / "data" / "cards" / "cards_v6_sentence.json",
    "v6-sentence": _WORKSPACE / "data" / "cards" / "cards_v6_sentence.json",
    "v6-except-ch2": _WORKSPACE / "data" / "cards" / "cards_v6_sentence.json",
    "ch2-plus-v6-except": _WORKSPACE / "data" / "cards" / "cards_v6_sentence.json",
}

JUDGEMENTS = {"correct", "incorrect", "insufficient", "needs_manual"}
EVIDENCE_STATUSES = {"direct", "indirect", "none", "conflict", "needs_manual"}
SUPPORT_TYPES = {"direct", "indirect", "context", "negative"}
RELEVANCE_VALUES = {"high", "medium", "low"}


@dataclass
class Runtime:
    sections: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    section_to_cards: dict[str, list[str]]
    cards: list[dict[str, Any]]
    questions: list[dict[str, Any]]
    card_ctx: dict[str, str]
    valid_card_ids: set[str]
    section_titles: list[str]
    edge_index: dict[str, list[dict[str, Any]]]
    bge: Any
    section_vecs: Any
    client: Any
    evidence_scope: str
    evidence_file: str


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_answer(answer: str, options: dict[str, str] | None = None) -> set[str]:
    answer_text = str(answer or "").strip()
    compact = re.sub(r"\s+", "", answer_text)
    if not compact:
        return set()

    tokens = [token for token in re.split(r"[,，、/;；]+", compact) if token]
    if len(tokens) == 1 and re.fullmatch(r"[A-Z]+", tokens[0]):
        raw = set(tokens[0])
    else:
        raw = set(tokens)

    if not options:
        return raw

    labels = set(options)
    if raw & labels:
        return raw & labels

    normalized_text = {label: re.sub(r"\s+", "", str(text or "")) for label, text in options.items()}
    mapped: set[str] = set()
    for token in raw:
        for label, text in normalized_text.items():
            if token == text:
                mapped.add(label)
    if mapped:
        return mapped

    truth_aliases = {
        "正确": {"正确", "对", "是", "true", "True", "TRUE"},
        "错误": {"错误", "错", "否", "false", "False", "FALSE"},
    }
    for token in raw:
        for label, text in normalized_text.items():
            for canonical, aliases in truth_aliases.items():
                if token in aliases and text in aliases:
                    mapped.add(label)
    return mapped or raw


def explicit_answer_labels(answer: str) -> set[str]:
    """Return option letters explicitly written in the answer text."""
    answer_text = str(answer or "").strip()
    compact = re.sub(r"\s+", "", answer_text).upper()
    if not compact or compact in {"TRUE", "FALSE"}:
        return set()

    tokens = [token for token in re.split(r"[,，、/;；]+", compact) if token]
    labels: set[str] = set()
    for token in tokens:
        if token in {"TRUE", "FALSE"}:
            continue
        if re.fullmatch(r"[A-K]", token):
            labels.add(token)
        elif re.fullmatch(r"[A-K]{2,}", token):
            labels.update(token)
    return labels


def get_deepseek_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_DEEPSEEK_BASE_URL
            return value, base_url, env_name
    names = " / ".join(API_KEY_ENV_NAMES)
    raise RuntimeError(f"{names} 环境变量均未设置，不能调用 DeepSeek API。")


def load_runtime(evidence_scope: str = "ch2") -> Runtime:
    api_key, base_url, env_name = get_deepseek_config()

    from openai import OpenAI
    from sentence_transformers import SentenceTransformer

    if evidence_scope not in EVIDENCE_FILES:
        raise ValueError(f"unknown evidence_scope={evidence_scope}; choose one of {sorted(EVIDENCE_FILES)}")
    evidence_file = EVIDENCE_FILES[evidence_scope]
    if not evidence_file.exists():
        raise FileNotFoundError(evidence_file)

    print(
        "Loading KG and textbook cards... DeepSeek key source: {env}, base_url: {base}, evidence_scope={scope}".format(
            env=env_name,
            base=base_url,
            scope=evidence_scope,
        )
    )
    sections = read_json(KG_DIR / "sections.json")
    edges = read_json(KG_DIR / "edges.json")
    cs_map = read_json(KG_DIR / "card_section_map.json")

    raw_cards = read_json(evidence_file)
    cards = raw_cards.get("cards", raw_cards) if isinstance(raw_cards, dict) else raw_cards
    if not isinstance(cards, list):
        raise ValueError(f"{evidence_file.name} 既不是数组，也不是包含 cards 数组的对象。")

    questions = read_json(DATA / "questions.json")["questions"]

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

    client = OpenAI(api_key=api_key, base_url=base_url)

    return Runtime(
        sections=sections,
        edges=edges,
        section_to_cards=cs_map["section_to_cards"],
        cards=cards,
        questions=questions,
        card_ctx=card_ctx,
        valid_card_ids=valid_card_ids,
        section_titles=section_titles,
        edge_index=edge_index,
        bge=bge,
        section_vecs=section_vecs,
        client=client,
        evidence_scope=evidence_scope,
        evidence_file=str(evidence_file),
    )


def bge_search(rt: Runtime, query_text: str, top_k_sections: int = 5, top_k_cards: int = 3) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    q_vec = rt.bge.encode([query_text], normalize_embeddings=True)
    scores = (q_vec @ rt.section_vecs.T).flatten()

    evidence: list[dict[str, Any]] = []
    seen_cids: set[str] = set()
    matched_sections: list[str] = []

    for idx in list(reversed(scores.argsort()))[:top_k_sections]:
        score = float(scores[idx])
        if score < BGE_SCORE_THRESHOLD:
            continue
        section = rt.section_titles[idx]
        matched_sections.append(section)
        for cid in rt.section_to_cards.get(section, [])[:top_k_cards]:
            if cid in seen_cids:
                continue
            seen_cids.add(cid)
            evidence.append(
                {
                    "card_id": cid,
                    "section": section,
                    "bge_score": score,
                    "source": "bge_direct",
                    "text": rt.card_ctx.get(cid, ""),
                }
            )

    expanded_sections: set[str] = set()
    for section in matched_sections[:3]:
        for edge in rt.edge_index.get(section, [])[:3]:
            target = edge.get("to_subsection", "")
            if target and target not in matched_sections:
                expanded_sections.add(target)

    for section in expanded_sections:
        if section in rt.section_titles:
            sec_idx = rt.section_titles.index(section)
            expanded_score = float(scores[sec_idx])
            if expanded_score < 0.3:
                continue
        else:
            expanded_score = 0.0

        for cid in rt.section_to_cards.get(section, [])[:2]:
            if cid in seen_cids:
                continue
            seen_cids.add(cid)
            evidence.append(
                {
                    "card_id": cid,
                    "section": section,
                    "bge_score": expanded_score,
                    "source": "edge_expand",
                    "text": rt.card_ctx.get(cid, ""),
                }
            )

    return evidence, matched_sections, sorted(expanded_sections)


def strip_json_fence(raw_text: str) -> str:
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def parse_ai3_json(raw_text: str) -> tuple[list[dict[str, Any]] | None, list[str], str]:
    if not raw_text:
        return None, [], ""

    candidates = [strip_json_fence(raw_text)]
    match = re.search(r'\{[\s\S]*"option_analysis"[\s\S]*\}', raw_text)
    if match:
        candidates.append(match.group(0))

    parsed: dict[str, Any] | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            break
        except json.JSONDecodeError:
            try:
                import json_repair

                parsed = json.loads(json_repair.repair_json(candidate))
                break
            except Exception:
                continue

    if parsed is None:
        return None, [], ""

    option_analysis = parsed.get("option_analysis", [])
    if not isinstance(option_analysis, list):
        return None, [], parsed.get("overall_notes", "")

    cited = sorted(
        {
            card.get("card_id", "")
            for option in option_analysis
            for card in option.get("evidence_cards", [])
            if card.get("card_id")
        }
    )
    return option_analysis, cited, parsed.get("overall_notes", "")


def ensure_option_defaults(result: dict[str, Any]) -> None:
    option_texts = result.get("options", {})
    correct_set = normalize_answer(result.get("answer", ""), option_texts)
    for option in result.get("option_analysis", []):
        label = option.get("option", "")
        option.setdefault("option_text", option_texts.get(label, ""))
        option["is_correct_answer"] = label in correct_set
        option.setdefault("judgement_confidence", "")
        option.setdefault("evidence_cards", [])
        option.setdefault("kg_concepts", [])
        option.setdefault("common_trap", "")
        option.setdefault("needs_teacher_review", False)
        option.setdefault("teacher_review_reason", "")


def validate_option_analysis(result: dict[str, Any], valid_card_ids: set[str]) -> list[str]:
    issues: list[str] = []
    options = result.get("options", {})
    option_analysis = result.get("option_analysis", [])
    correct_set = normalize_answer(result.get("answer", ""), options)
    explicit_labels = explicit_answer_labels(result.get("answer", ""))
    expected_labels = list(options.keys())
    actual_labels = [option.get("option", "") for option in option_analysis]
    evidence_set = {item.get("card_id") for item in result.get("evidence", []) if item.get("card_id")}

    missing_answer_labels = sorted(explicit_labels - set(expected_labels))
    if missing_answer_labels:
        issues.append(f"标准答案包含不存在的选项: {missing_answer_labels}; options={expected_labels}")
    if len(option_analysis) != len(options):
        issues.append(f"选项数量不匹配: analysis={len(option_analysis)} vs options={len(options)}")
    if actual_labels != expected_labels:
        issues.append(f"选项标签不一致: expected={expected_labels} actual={actual_labels}")
    if len(set(actual_labels)) != len(actual_labels):
        issues.append(f"选项标签重复: {actual_labels}")

    for option in option_analysis:
        label = option.get("option", "?")
        for field in ["option", "option_text", "judgement", "evidence_status", "explanation", "common_trap"]:
            if field not in option:
                issues.append(f"选项{label}: 缺少字段 {field}")

        if option.get("option_text") and options.get(label) and option.get("option_text") != options.get(label):
            issues.append(f"选项{label}: option_text 与原题不一致")

        judgement = option.get("judgement")
        evidence_status = option.get("evidence_status")
        if judgement not in JUDGEMENTS:
            issues.append(f"选项{label}: 无效 judgement={judgement}")
        if evidence_status not in EVIDENCE_STATUSES:
            issues.append(f"选项{label}: 无效 evidence_status={evidence_status}")

        evidence_cards = option.get("evidence_cards", [])
        if not isinstance(evidence_cards, list):
            issues.append(f"选项{label}: evidence_cards 不是数组")
            evidence_cards = []

        if evidence_status == "direct" and not any(card.get("card_id") for card in evidence_cards):
            issues.append(f"选项{label}: evidence_status=direct 但 evidence_cards 为空")
        if evidence_status == "none" and any(card.get("card_id") for card in evidence_cards):
            issues.append(f"选项{label}: evidence_status=none 但 evidence_cards 不为空")

        for card in evidence_cards:
            cid = card.get("card_id", "")
            if not cid:
                issues.append(f"选项{label}: evidence_card 缺少 card_id")
                continue
            if cid not in valid_card_ids:
                issues.append(f"选项{label}: 幻觉 card_id={cid}")
            if evidence_set and cid not in evidence_set:
                issues.append(f"选项{label}: card_id={cid} 不在本次给 AI #3 的 evidence 中")
            if card.get("support_type") and card.get("support_type") not in SUPPORT_TYPES:
                issues.append(f"选项{label}: 无效 support_type={card.get('support_type')}")
            if card.get("relevance") and card.get("relevance") not in RELEVANCE_VALUES:
                issues.append(f"选项{label}: 无效 relevance={card.get('relevance')}")

        is_correct = label in correct_set
        if is_correct and evidence_status != "direct":
            option["needs_teacher_review"] = True
            if not option.get("teacher_review_reason"):
                option["teacher_review_reason"] = "正确选项缺少直接教材句卡依据"

        if judgement == "correct" and not is_correct:
            issues.append(f"选项{label}: 判为正确但与标准答案冲突")
        if judgement == "incorrect" and is_correct:
            issues.append(f"选项{label}: 判为错误但与标准答案冲突")

    return issues


def classify_status(result: dict[str, Any]) -> str:
    option_analysis = result.get("option_analysis", [])
    if not option_analysis:
        return result.get("status", "parse_failed")

    issues = result.get("validation_issues", [])
    correct_set = normalize_answer(result.get("answer", ""), result.get("options", {}))
    all_judged = all(option.get("judgement") in {"correct", "incorrect"} for option in option_analysis)
    correct_labels_with_direct = {
        option.get("option")
        for option in option_analysis
        if option.get("option") in correct_set and option.get("evidence_status") == "direct"
    }
    all_correct_have_direct = bool(correct_set) and correct_set.issubset(correct_labels_with_direct)
    any_direct = any(option.get("evidence_status") == "direct" for option in option_analysis)
    all_none_or_manual = all(option.get("evidence_status") in {"none", "needs_manual"} for option in option_analysis)

    if issues:
        return "evidence_insufficient" if all_none_or_manual else "partial"
    if all_judged and all_correct_have_direct:
        return "answered"
    if all_none_or_manual:
        return "evidence_insufficient"
    if any_direct or any(option.get("judgement") in {"correct", "incorrect"} for option in option_analysis):
        return "partial"
    return "evidence_insufficient"


def summarize_quality(result: dict[str, Any], valid_card_ids: set[str]) -> dict[str, Any]:
    option_analysis = result.get("option_analysis", [])
    cited = result.get("cited_cards", [])
    evidence = result.get("evidence", [])
    explicit_labels = explicit_answer_labels(result.get("answer", ""))
    expected_labels = set(result.get("options", {}))
    missing_answer_labels = sorted(explicit_labels - expected_labels)
    hallucinations = sorted(
        {
            card.get("card_id", "")
            for option in option_analysis
            for card in option.get("evidence_cards", [])
            if card.get("card_id") and card.get("card_id") not in valid_card_ids
        }
    )
    return {
        "hallucinations": hallucinations,
        "hallucination_rate": len(hallucinations) / max(len(cited), 1),
        "option_coverage_ok": len(option_analysis) == len(result.get("options", {})),
        "answer_option_coverage_ok": not missing_answer_labels,
        "missing_answer_options": missing_answer_labels,
        "analyzed_options": len(option_analysis),
        "expected_options": len(result.get("options", {})),
        "direct_evidence_options": sum(1 for item in option_analysis if item.get("evidence_status") == "direct"),
        "indirect_evidence_options": sum(1 for item in option_analysis if item.get("evidence_status") == "indirect"),
        "none_evidence_options": sum(1 for item in option_analysis if item.get("evidence_status") == "none"),
        "validation_issues": result.get("validation_issues", []),
        "cards_from_edge_expand": len(
            [
                cid
                for cid in cited
                if any(item.get("card_id") == cid and item.get("source") == "edge_expand" for item in evidence)
            ]
        ),
    }


def build_insufficient_options(options: dict[str, str], answer: str, explanation: str, reason: str) -> list[dict[str, Any]]:
    correct_set = normalize_answer(answer, options)
    rows = []
    for label, text in options.items():
        is_correct = label in correct_set
        rows.append(
            {
                "option": label,
                "option_text": text,
                "is_correct_answer": is_correct,
                "judgement": "insufficient",
                "judgement_confidence": "",
                "evidence_status": "none",
                "evidence_cards": [],
                "kg_concepts": [],
                "explanation": explanation,
                "common_trap": "",
                "needs_teacher_review": is_correct,
                "teacher_review_reason": reason if is_correct else "",
            }
        )
    return rows


def call_llm(client: Any, prompt: str, max_tokens: int, retries: int = LLM_RETRY,
             model: str = "", extra_body: dict[str, Any] | None = None) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            kwargs: dict[str, Any] = {
                "model": model or MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": max_tokens,
                "extra_body": extra_body if extra_body is not None else V4_NO_THINK,
            }
            response = client.chat.completions.create(**kwargs)
            return (response.choices[0].message.content or "").strip()
        except Exception as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(3 + attempt * 2)
    raise RuntimeError(str(last_error) if last_error else "LLM call failed")


def build_ai1_prompt(stem: str, opt_text: str, answer: str) -> str:
    return f"""你是CAMS反洗钱考试专家。请自由回答以下问题。

题目：{stem}
选项：{opt_text}
正确答案：{answer}

请做两件事：
1. 分析每个选项为什么对或错。调动你所有知识，可以跨章节联想。涉及法条编号、教材章节名、概念定义、案例细节时请明确写出。
2. 在分析末尾，列出"需要查教材原文验证的具体事实主张"，每条以"需要验证："开头。"""


def build_ai2_prompt(ai1_output: str) -> str:
    return f"""从以下分析中提取所有"需要查教材原文验证的具体事实主张"。

每条主张：可在教材原文中查到的具体断言，非结论性判断。
输出格式：
需要验证：[主张1]
需要验证：[主张2]
...

搜索query：
[query1 - 用教材术语描述]
[query2 - 用教材术语描述]
[query3 - 用教材术语描述]

AI分析：
{ai1_output}"""


def build_ai3_prompt(stem: str, opt_text: str, answer: str, evidence_text: str, option_count: int) -> str:
    return f"""你是CAMS反洗钱考试专家。基于以下教材句卡证据，推理判断每个选项的对错。

你必须输出严格JSON，不要输出Markdown。不要用代码块包裹。

引用规则：
- evidence_cards 只能包含本次提供的证据中真实存在的 card_id
- 如果某个选项没有直接证据支撑，evidence_status 填 "none" 或 "indirect"，evidence_cards 填空数组 []
- 不要因为知道正确答案就编造 card_id
- common_trap 是教学推断字段，措辞用"可能误以为""容易混淆为"，若无法推断填 ""
- kg_concepts 第一阶段统一填 []

题目：{stem}
选项：{opt_text}
正确答案：{answer}

教材句卡证据：
{evidence_text[:EVIDENCE_MAX_CHARS]}

输出JSON格式：
{{
  "option_analysis": [
    {{
      "option": "A",
      "option_text": "选项全文",
      "judgement": "correct/incorrect/insufficient/needs_manual",
      "evidence_status": "direct/indirect/none/conflict/needs_manual",
      "evidence_cards": [
        {{"card_id": "必须使用上方证据中真实出现的card_id", "support_type": "direct/indirect/context/negative", "source": "bge_direct/edge_expand", "quote": "教材原文短摘，不超过120字", "reason": "为什么支撑该选项", "relevance": "high/medium/low"}}
      ],
      "explanation": "为什么该选项正确或错误",
      "common_trap": "学生容易误选/误排除的原因，无法推断则填空",
      "needs_teacher_review": false,
      "teacher_review_reason": ""
    }}
  ],
  "overall_notes": "整体说明",
  "cited_cards": ["必须使用上方证据中真实出现的card_id"]
}}

你必须逐一分析每个选项，共 {option_count} 个。"""


def extract_search_queries(ai2_output: str, stem: str, options: dict[str, str]) -> list[str]:
    query_block = re.search(r"搜索query[：:]\s*\n(.+)", ai2_output, re.DOTALL)
    ai2_queries: list[str] = []
    if query_block:
        ai2_queries = [line.strip(" []") for line in query_block.group(1).splitlines() if line.strip()]

    claims = re.findall(r"需要验证：(.+)", ai2_output)
    if ai2_queries:
        queries = ai2_queries[:5]
    elif claims:
        queries = [claim.split("||")[0].strip()[:150] for claim in claims[:5]]
    else:
        queries = []

    queries.extend([stem])
    queries.extend([f"{label}. {text}" for label, text in options.items()])
    return queries[:12]


def retrieve_evidence(rt: Runtime, queries: list[str]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    all_evidence: list[dict[str, Any]] = []
    seen: set[str] = set()
    all_matched: list[str] = []
    all_expanded: list[str] = []

    for query in queries:
        evidence, matched, expanded = bge_search(rt, query, top_k_sections=3, top_k_cards=3)
        all_matched.extend(matched)
        all_expanded.extend(expanded)
        for item in evidence:
            cid = item.get("card_id")
            if cid and cid not in seen:
                seen.add(cid)
                all_evidence.append(item)

    return all_evidence, sorted(set(all_matched)), sorted(set(all_expanded))


def process_question(rt: Runtime, question: dict[str, Any]) -> dict[str, Any]:
    qid = question["id"]
    stem = question["stem"]
    options = question["options"]
    answer = question["answer"]
    opt_text = " ".join(f"{label}. {text}" for label, text in options.items())
    option_count = len(options)

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "question_id": qid,
        "stem": stem,
        "options": options,
        "answer": answer,
        "status": "started",
        "option_count": option_count,
        "retrieval_mode": "baseline",
        "evidence_scope": rt.evidence_scope,
        "evidence_file": rt.evidence_file,
    }

    try:
        result["ai1_output"] = call_llm(rt.client, build_ai1_prompt(stem, opt_text, answer), 8000)
    except Exception as exc:
        result["status"] = "ai1_failed"
        result["error"] = str(exc)[:500]
        return result

    try:
        result["ai2_output"] = call_llm(rt.client, build_ai2_prompt(result["ai1_output"]), 8000)
    except Exception as exc:
        result["status"] = "ai2_failed"
        result["error"] = str(exc)[:500]
        return result

    queries = extract_search_queries(result["ai2_output"], stem, options)
    evidence, matched, expanded = retrieve_evidence(rt, queries)
    result["evidence_count"] = len(evidence)
    result["evidence"] = evidence
    result["sections_matched"] = matched
    result["sections_expanded"] = expanded

    if not evidence:
        result["status"] = "evidence_insufficient"
        result["option_analysis"] = build_insufficient_options(
            options,
            answer,
            "教材中未检索到相关内容",
            "0条证据",
        )
        result["cited_cards"] = []
        result["raw_ai3_output"] = ""
        result["validation_issues"] = validate_option_analysis(result, rt.valid_card_ids)
        result["quality"] = summarize_quality(result, rt.valid_card_ids)
        return result

    evidence_text = "\n---\n".join(
        f'[{item["card_id"]}] [{item["section"]}] (来源:{item["source"]})\n{item["text"]}'
        for item in evidence[:30]
    )

    raw_ai3 = ""
    for attempt in range(AI3_RETRY):
        try:
            raw_ai3 = call_llm(rt.client, build_ai3_prompt(stem, opt_text, answer, evidence_text, option_count), AI3_MAX_TOKENS)
            if raw_ai3:
                break
        except Exception as exc:
            print(f"  AI #3 error attempt {attempt + 1}: {str(exc)[:80]}")
        time.sleep(5)

    result["raw_ai3_output"] = raw_ai3
    option_analysis, cited_cards, overall_notes = parse_ai3_json(raw_ai3)

    if option_analysis is None:
        result["status"] = "parse_failed"
        result["option_analysis"] = build_insufficient_options(
            options,
            answer,
            "AI输出无法解析为JSON",
            "parse_failed",
        )
        for option in result["option_analysis"]:
            option["judgement"] = "needs_manual"
            option["evidence_status"] = "needs_manual"
            option["needs_teacher_review"] = True
            option["teacher_review_reason"] = "parse_failed"
        result["cited_cards"] = []
        result["validation_issues"] = validate_option_analysis(result, rt.valid_card_ids)
        result["quality"] = summarize_quality(result, rt.valid_card_ids)
        return result

    result["option_analysis"] = option_analysis
    result["overall_notes"] = overall_notes
    ensure_option_defaults(result)
    result["cited_cards"] = sorted(
        {
            card.get("card_id", "")
            for option in result["option_analysis"]
            for card in option.get("evidence_cards", [])
            if card.get("card_id")
        }
    )
    result["ai3_output"] = json.dumps(result["option_analysis"], ensure_ascii=False)
    result["validation_issues"] = validate_option_analysis(result, rt.valid_card_ids)
    result["status"] = classify_status(result)
    result["quality"] = summarize_quality(result, rt.valid_card_ids)
    return result


def output_path(qid: str) -> Path:
    return SAVE_DIR / f"q_{qid}.json"


def is_valid_done_file(
    path: Path,
    question: dict[str, Any],
    valid_card_ids: set[str],
    retrieval_mode: str,
    evidence_scope: str,
) -> bool:
    if not path.exists():
        return False
    try:
        data = read_json(path)
    except Exception:
        return False
    if data.get("schema_version") != SCHEMA_VERSION:
        return False
    if data.get("question_id") != question.get("id"):
        return False
    if data.get("retrieval_mode", "baseline") != retrieval_mode:
        return False
    if data.get("evidence_scope", "ch2") != evidence_scope:
        return False
    if "quality" not in data or "validation_issues" not in data:
        return False

    check_data = {
        **data,
        "options": question.get("options", {}),
        "answer": question.get("answer", ""),
    }
    issues = validate_option_analysis(check_data, valid_card_ids)
    return not issues and len(data.get("option_analysis", [])) == len(question.get("options", {}))


def select_questions(
    rt: Runtime,
    ids: list[str] | None = None,
    limit: int | None = None,
    force: bool = False,
    retrieval_mode: str = "baseline",
) -> tuple[list[dict[str, Any]], int]:
    wanted = set(ids or [])
    selected: list[dict[str, Any]] = []
    done_count = 0

    for question in rt.questions:
        qid = question["id"]
        if wanted and qid not in wanted:
            continue
        if not force and is_valid_done_file(
            output_path(qid),
            question,
            rt.valid_card_ids,
            retrieval_mode,
            rt.evidence_scope,
        ):
            done_count += 1
            continue
        selected.append(question)
        if limit is not None and len(selected) >= limit:
            break

    return selected, done_count


def process_question_agentic(
    agentic_rt: Any,
    question: dict[str, Any],
    max_followups: int,
    top_k: int,
    card_scan_mode: str,
    card_scan_chunk_size: int,
    teacher_hints: bool,
) -> dict[str, Any]:
    import run_agentic_search_experiment as agentic_search

    result = agentic_search.process_question(
        agentic_rt,
        question,
        max_followups=max_followups,
        top_k=top_k,
        card_scan_mode=card_scan_mode,
        card_scan_chunk_size=card_scan_chunk_size,
        teacher_hints=teacher_hints,
    )
    result["schema_version"] = SCHEMA_VERSION
    result["retrieval_mode"] = "agentic"
    result["evidence_scope"] = agentic_rt.base.evidence_scope
    result["evidence_file"] = agentic_rt.base.evidence_file
    result["quality"] = summarize_quality(result, agentic_rt.base.valid_card_ids)
    return result


def main(
    ids: list[str] | None = None,
    limit: int | None = None,
    force: bool = False,
    retrieval_mode: str = "baseline",
    max_followups: int = 1,
    top_k: int = 30,
    card_scan_mode: str = "correct",
    card_scan_chunk_size: int = 180,
    evidence_scope: str = "ch2",
    teacher_hints: bool = False,
) -> int:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    if retrieval_mode == "agentic":
        import run_agentic_search_experiment as agentic_search

        agentic_rt = agentic_search.load_agentic_runtime(evidence_scope=evidence_scope)
        rt = agentic_rt.base
    else:
        agentic_rt = None
        rt = load_runtime(evidence_scope=evidence_scope)

    selected, done_count = select_questions(rt, ids=ids, limit=limit, force=force, retrieval_mode=retrieval_mode)

    print(
        f"Total: {len(rt.questions)}, Done(valid {retrieval_mode} schema): {done_count}, Todo(this run): {len(selected)}"
    )
    if ids:
        missing = sorted(set(ids) - {q["id"] for q in rt.questions})
        if missing:
            print(f"Warning: unknown question ids: {', '.join(missing)}")

    for index, question in enumerate(selected, start=1):
        qid = question["id"]
        print(f"[{index}/{len(selected)}] {qid}: {question['stem'][:50]}...")
        if retrieval_mode == "agentic":
            result = process_question_agentic(
                agentic_rt,
                question,
                max_followups=max_followups,
                top_k=top_k,
                card_scan_mode=card_scan_mode,
                card_scan_chunk_size=card_scan_chunk_size,
                teacher_hints=teacher_hints,
            )
        else:
            result = process_question(rt, question)
        write_json(output_path(qid), result)

        quality = result.get("quality", {})
        print(
            "  -> {status} direct={direct} indirect={indirect} none={none} cited={cited} issues={issues}".format(
                status=result.get("status"),
                direct=quality.get("direct_evidence_options", 0),
                indirect=quality.get("indirect_evidence_options", 0),
                none=quality.get("none_evidence_options", 0),
                cited=len(result.get("cited_cards", [])),
                issues=len(result.get("validation_issues", [])),
            )
        )

    print(f"\nDone. Results in {SAVE_DIR}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run option-level question-card binding pipeline.")
    parser.add_argument("--ids", nargs="*", help="Question ids to run, for example 2.1_1 2.1_2.")
    parser.add_argument("--limit", type=int, help="Maximum number of pending questions to run.")
    parser.add_argument("--force", action="store_true", help="Re-run even if a valid schema output exists.")
    parser.add_argument(
        "--retrieval",
        choices=["baseline", "agentic"],
        default="baseline",
        help="Evidence retrieval mode. baseline keeps the old AI#1/AI#2/BGE flow; agentic uses option-level search.",
    )
    parser.add_argument("--max-followups", type=int, default=1, help="Agentic mode follow-up search rounds.")
    parser.add_argument("--top-k", type=int, default=30, help="Agentic mode candidate cards kept per option.")
    parser.add_argument(
        "--card-scan",
        choices=["off", "correct", "all"],
        default="correct",
        help="Agentic mode LLM scan over the selected textbook sentence-card pool.",
    )
    parser.add_argument("--card-scan-chunk-size", type=int, default=180, help="Cards per LLM scan chunk.")
    parser.add_argument(
        "--teacher-hints",
        action="store_true",
        help="Agentic mode only: use question.explanation as retrieval hints, never as textbook evidence.",
    )
    parser.add_argument(
        "--evidence-scope",
        choices=sorted(EVIDENCE_FILES),
        default="ch2",
        help=(
            "Textbook evidence pool. ch2 preserves MVP chapter-2 behavior; "
            "v6-sentence uses full V6 sentence-level evidence cards; "
            "v6-except-ch2 uses the cross-chapter fallback pool excluding chapter 2; "
            "ch2-plus-v6-except combines chapter-2 cards with the cross-chapter fallback pool."
        ),
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(
        main(
            ids=args.ids,
            limit=args.limit,
            force=args.force,
            retrieval_mode=args.retrieval,
            max_followups=args.max_followups,
            top_k=args.top_k,
            card_scan_mode=args.card_scan,
            card_scan_chunk_size=args.card_scan_chunk_size,
            evidence_scope=args.evidence_scope,
            teacher_hints=args.teacher_hints,
        )
    )
