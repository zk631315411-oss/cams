"""
Single-question blind pipeline for the new-question analysis module.

Flow (blind variant — NO standard answer assumed):
  题目拆解 → 检索规划 → 教材证据召回 → 盲判裁判 → 质量校验

Usage (CLI)::

    cd 新题解析模块
    python -m pipeline.run_pipeline "整段新题文本..."
    python -m pipeline.run_pipeline --file sample.txt
"""

from __future__ import annotations

import datetime
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import run_agentic_search_experiment as agentic
import run_blind_q212_experiment as blind
import run_step1

from evidence_pool import get_agentic_runtime
from question_parser import parse_question

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_DRAFTS_DIR = _HERE / "outputs" / "drafts"
_LOGS_DIR = _HERE / "logs"
_ANSWER_EXPLANATION_HEADING = re.compile(
    r"(?im)^\s*(?:[?？#>*\-•\s]*)"
    r"(答案|标准答案|正确答案|参考答案|解析|题目解析|答案解析|教研解析)\s*[：:]"
)
_OPTION_LINE = re.compile(r"(?m)^\s*[A-K][\.\、\)）]\s+")
_BARE_ANSWER_LINE = re.compile(r"^\s*(?:[?？#>*\-•\s]*)[A-K](?:\s*[,，、/;；]\s*[A-K]|\s+[A-K]){0,10}\s*$")
_INTERNAL_CARD_ID = re.compile(r"\bv\d+[a-z]?[_-]?N\d+\b|\bv6s_N\d+\b|\bv6_b\d+_N\d+\b", re.IGNORECASE)
_EXAM_CORE_BLOOM_LEVELS = {"记忆", "理解", "应用", "分析", "评价", "创造"}
_EXAM_CORE_ACTIONS = {
    "识别",
    "区分",
    "判断",
    "应用",
    "分析",
    "评价",
    "解释",
    "比较",
    "归纳",
    "选择",
}
_EXAM_CORE_GENERIC_PHRASES = (
    "反洗钱知识",
    "合规意识",
    "风险识别能力",
    "选择正确答案",
    "知识点",
    "教材知识",
    "CAMS知识",
    "考试知识",
)


# ---------------------------------------------------------------------------
# Pipeline entry point
# ---------------------------------------------------------------------------
def run_new_question_pipeline(
    text: str,
    rt: agentic.AgenticRuntime | None = None,
    top_k: int = 30,
) -> dict[str, Any]:
    """Run the 5-step blind new-question pipeline and return a draft JSON.

    Parameters
    ----------
    text : str
        Raw pasted question text from the teacher.
    rt : AgenticRuntime or None
        Pre-loaded runtime.  If ``None``, ``get_agentic_runtime()`` is called.
    top_k : int
        Max candidate cards per option (default 30).

    Returns
    -------
    dict
        Complete draft JSON (also saved to ``outputs/drafts/``).
    """
    if rt is None:
        rt = get_agentic_runtime()

    client = rt.base.client
    clean_text, input_sanitization = _sanitize_question_input(text)
    result: dict[str, Any] = {
        "status": "draft",
        "raw_input": text,
        "sanitized_input": clean_text,
        "pipeline": {},
    }
    result["pipeline"]["input_sanitization"] = input_sanitization
    llm_calls: list[dict[str, Any]] = []
    result["pipeline"]["llm_calls"] = llm_calls

    # ==== Step 1: 题目拆解 ================================================
    parse_result = parse_question(client, clean_text)
    result["pipeline"]["parse_question"] = parse_result

    stem = parse_result.get("stem", "")
    options = parse_result.get("options", {})
    detected_answer = parse_result.get("detected_answer", "")
    parse_warnings = parse_result.get("parse_warnings", [])
    question_type = str(parse_result.get("question_type", "unknown")).strip()
    question_subtype = str(parse_result.get("question_subtype", "")).strip()

    if not stem or len(options) < 2:
        result["status"] = "parse_failed"
        result["final"] = _empty_final()
        _save_draft(result)
        return result

    # ==== Step 2: 证据检索 ================================================
    # 2a. Blind search planner (NO standard answer in prompt)
    try:
        planner_prompt = blind.build_blind_planner_prompt(stem, options)
        raw_planner, planner_trace = _call_llm_traced(
            client, "planner", planner_prompt, max_tokens=5000
        )
        llm_calls.append(planner_trace)
        plan_parsed = _parse_llm_json_object(raw_planner)
        search_plan = blind.normalize_blind_plan(plan_parsed, stem, options)
    except Exception as exc:
        result["status"] = "planner_failed"
        result["pipeline"]["retrieve_evidence"] = {"error": str(exc)}
        result["final"] = _empty_final()
        result["final"]["overall_notes"] = f"搜索规划 LLM 调用失败: {exc}"
        _save_draft(result)
        return result

    # 2b. Multi-route retrieval per option
    plans = agentic.option_plan_by_label(search_plan)
    candidates_by_option: dict[str, list[dict[str, Any]]] = {}
    search_rounds: list[dict[str, Any]] = []

    try:
        for label, option_text in options.items():
            option_plan = plans.get(label, {})
            if not option_plan.get("search_queries"):
                terms = agentic.extract_phrases(stem, option_text)
                option_plan = {
                    "search_queries": [f"{stem} {option_text}", option_text],
                    "must_terms": terms[:6],
                    "evidence_need": f"判断选项{label}是否符合题干",
                    "option_claim": option_text,
                    "related_terms": [],
                    "contrast_terms": [],
                    "avoid_confusions": [],
                }
            candidates, diagnostics = agentic.retrieve_for_option(
                rt, stem, option_text, option_plan, top_k=top_k
            )
            candidates_by_option[label] = candidates
            search_rounds.append(
                {
                    "option": label,
                    "diagnostics": diagnostics,
                    "candidate_ids": [c["card_id"] for c in candidates],
                }
            )
    except Exception as exc:
        result["status"] = "retrieval_failed"
        result["pipeline"]["retrieve_evidence"] = {
            "raw_search_plan": raw_planner,
            "search_plan": search_plan,
            "search_rounds": search_rounds,
            "error": str(exc),
        }
        result["final"] = _empty_final()
        result["final"]["overall_notes"] = f"教材证据检索失败: {exc}"
        _save_draft(result)
        return result

    evidence = agentic.flatten_evidence(candidates_by_option)

    result["pipeline"]["retrieve_evidence"] = {
        "raw_search_plan": raw_planner,
        "search_plan": search_plan,
        "search_rounds": search_rounds,
        "candidates_by_option": {
            label: [
                {k: v for k, v in item.items() if k != "text"}
                for item in candidates
            ]
            for label, candidates in candidates_by_option.items()
        },
        "evidence": evidence,
        "evidence_count": len(evidence),
    }

    # ==== Step 3: 答案判断（盲判） ========================================
    try:
        adjudicator_prompt = blind.build_blind_adjudicator_prompt(
            stem, options, search_plan, candidates_by_option
        )
        raw_adjudicator, adjudicator_trace = _call_llm_traced(
            client, "adjudicator", adjudicator_prompt, max_tokens=9000
        )
        llm_calls.append(adjudicator_trace)
        parsed = _parse_llm_json_object(raw_adjudicator) or {}
    except Exception as exc:
        result["status"] = "adjudicator_failed"
        result["pipeline"]["judge_answer"] = {"error": str(exc)}
        result["final"] = _empty_final()
        result["final"]["overall_notes"] = f"盲判裁判 LLM 调用失败: {exc}"
        _save_draft(result)
        return result

    predicted_answer = parsed.get("predicted_answer", [])
    if not isinstance(predicted_answer, list):
        predicted_answer = []
    predicted_confidence = parsed.get("predicted_answer_confidence", "insufficient")
    overall_notes = parsed.get("overall_notes", "")

    result["pipeline"]["judge_answer"] = {
        "raw_adjudicator_output": raw_adjudicator,
        "predicted_answer": predicted_answer,
        "predicted_answer_confidence": predicted_confidence,
        "overall_notes": overall_notes,
    }

    # ==== Step 4-5: 选项解析 + 质量校验 ====================================
    option_analysis = parsed.get("option_analysis", [])
    if not isinstance(option_analysis, list) or not option_analysis:
        option_analysis = _build_insufficient_options(options)
    else:
        normalized_rows: list[dict[str, Any]] = []
        for row in option_analysis:
            if isinstance(row, dict):
                normalized_rows.append(row)
        if len(normalized_rows) != len(option_analysis):
            result["pipeline"]["judge_answer"]["malformed_option_rows"] = (
                len(option_analysis) - len(normalized_rows)
            )
        option_analysis = normalized_rows or _build_insufficient_options(options)

    valid_card_ids = rt.base.valid_card_ids
    evidence_card_ids = {c.get("card_id") for c in evidence}
    checks: list[dict[str, str]] = []

    # ---- Pre-sanitize checks (run on RAW LLM output) -------------------
    # These MUST run before sanitize_blind_result, which drops invalid cards
    # and would mask real problems.

    # A. Hallucination check — raw
    raw_hallucinations: list[str] = []
    for row in option_analysis:
        for card in row.get("evidence_cards", []) or []:
            cid = card.get("card_id") if isinstance(card, dict) else None
            if cid and cid not in valid_card_ids:
                raw_hallucinations.append(cid)
    if raw_hallucinations:
        checks.append({
            "name": "引用句卡存在",
            "status": "fail",
            "detail": f"LLM编造了{len(raw_hallucinations)}个不存在的card_id: {','.join(raw_hallucinations[:5])}",
        })
    else:
        checks.append({"name": "引用句卡存在", "status": "pass"})

    # B. Outside-candidate check — raw
    raw_outside: list[str] = []
    for row in option_analysis:
        for card in row.get("evidence_cards", []) or []:
            cid = card.get("card_id") if isinstance(card, dict) else None
            if cid and cid not in evidence_card_ids:
                raw_outside.append(cid)
    if raw_outside:
        checks.append({
            "name": "引用在候选内",
            "status": "warning",
            "detail": f"LLM引用了{len(raw_outside)}个未检索到的card: {','.join(raw_outside[:3])}",
        })
    else:
        checks.append({"name": "引用在候选内", "status": "pass"})

    # C. Weak-evidence claim check — raw
    for row in option_analysis:
        if row.get("evidence_status") == "direct" and not row.get("evidence_cards"):
            checks.append({
                "name": f"选项{row.get('option', '?')}依据",
                "status": "warning",
                "detail": "LLM标记direct但无引用句卡",
            })

    # D. Leakage check on RAW adjudicator text (most important)
    raw_leakage = blind.leakage_check(
        {"raw": raw_adjudicator, "raw_search_plan": result["pipeline"]["retrieve_evidence"].get("raw_search_plan", "")}
    )
    if raw_leakage:
        checks.append({
            "name": "盲判隔离（原始输出）",
            "status": "fail",
            "detail": f"LLM原始输出包含泄露短语: {'; '.join(raw_leakage)}",
        })

    # ---- Sanitize ------------------------------------------------------
    result_temp: dict[str, Any] = {
        "options": options,
        "answer": "",
        "option_analysis": [dict(row) for row in option_analysis],  # deep copy
        "evidence": evidence,
    }
    blind.sanitize_blind_result(result_temp, options)

    # E. Leakage check on sanitized output (secondary)
    sanitized_leakage = blind.leakage_check(result_temp)
    all_leakage = sorted(set(raw_leakage + sanitized_leakage))

    # ---- Review --------------------------------------------------------
    # A second, narrow LLM pass checks whether the adjudicator stretched
    # merely related evidence into a "correct" option.
    review_result = _review_answer_with_llm(
        client=client,
        stem=stem,
        options=options,
        question_type=question_type,
        question_subtype=question_subtype,
        predicted_answer=predicted_answer,
        option_analysis=result_temp.get("option_analysis", []),
        llm_calls=llm_calls,
    )
    result["pipeline"]["review_answer"] = review_result
    if review_result.get("applied"):
        result_temp["option_analysis"] = review_result.get(
            "option_analysis", result_temp.get("option_analysis", [])
        )
        reviewed_answer = review_result.get("reviewed_answer")
        if reviewed_answer:
            predicted_answer = reviewed_answer
        review_confidence = review_result.get("review_confidence")
        if review_confidence and review_confidence != "unchanged":
            predicted_confidence = review_confidence

    rule_review = _apply_evidence_entailment_guard(
        stem=stem,
        options=options,
        option_analysis=result_temp.get("option_analysis", []),
    )
    result["pipeline"]["rule_review"] = rule_review
    if rule_review.get("applied"):
        result_temp["option_analysis"] = rule_review.get(
            "option_analysis", result_temp.get("option_analysis", [])
        )

    answer_resolution = _finalize_answer_by_type(
        predicted_answer=predicted_answer,
        option_analysis=result_temp.get("option_analysis", []),
        question_type=question_type,
        question_subtype=question_subtype,
        options=options,
    )
    finalized_answer = answer_resolution["answer"]

    cited_cards = sorted(
        {
            card.get("card_id", "")
            for row in result_temp.get("option_analysis", [])
            for card in row.get("evidence_cards", [])
            if card.get("card_id")
        }
    )

    result["pipeline"]["explain_options"] = {
        "option_analysis": result_temp["option_analysis"],
        "cited_cards": cited_cards,
        "leakage_issues": all_leakage,
    }
    result["pipeline"]["answer_resolution"] = answer_resolution
    exam_direction_result = _summarize_exam_direction_with_llm(
        client=client,
        stem=stem,
        options=options,
        finalized_answer=finalized_answer,
        option_analysis=result_temp.get("option_analysis", []),
        llm_calls=llm_calls,
    )
    exam_core_sentence = exam_direction_result.get("sentence", "")
    exam_core_validation = _validate_exam_direction(
        raw_sentence=exam_direction_result.get("raw_output", ""),
        display_sentence=exam_core_sentence,
        stem=stem,
        options=options,
    )
    exam_direction_result["validation"] = exam_core_validation
    result["pipeline"]["exam_direction"] = exam_direction_result
    result["pipeline"]["exam_core"] = {
        "raw_exam_core_sentence": exam_direction_result.get("raw_output", ""),
        "display_exam_core_sentence": exam_core_sentence,
        "exam_core_basis": {},
        "validation": exam_core_validation,
    }

    # ---- Post-sanitize checks (sanitized data, safe to check) ----------

    # 5.1 Stem integrity
    if not stem or len(stem) < 5:
        checks.append({"name": "题干完整性", "status": "fail", "detail": "题干过短或为空"})
    elif parse_warnings:
        checks.append({"name": "题干完整性", "status": "warning", "detail": "; ".join(parse_warnings)})
    else:
        checks.append({"name": "题干完整性", "status": "pass"})

    # 5.2 Options complete
    if len(options) >= 2:
        checks.append({"name": "选项完整性", "status": "pass", "detail": f"共{len(options)}个选项"})
    else:
        checks.append({"name": "选项完整性", "status": "fail", "detail": f"仅{len(options)}个选项"})

    # 5.3 AI answer in option range
    predicted_set = {str(a).strip() for a in finalized_answer}
    if not predicted_set:
        checks.append({"name": "AI答案范围", "status": "warning", "detail": "AI未给出参考答案"})
    elif predicted_set.issubset(set(options)):
        checks.append({"name": "AI答案范围", "status": "pass", "detail": f"预测答案: {','.join(sorted(predicted_set))}"})
    else:
        checks.append({"name": "AI答案范围", "status": "fail", "detail": f"预测答案{','.join(sorted(predicted_set))}不在选项中"})

    if answer_resolution["status"] == "ok":
        checks.append({
            "name": "question_type_answer_resolution",
            "status": "pass",
            "detail": f"{question_type}/{question_subtype}: {','.join(finalized_answer)}",
        })
    else:
        checks.append({
            "name": "question_type_answer_resolution",
            "status": "warning",
            "detail": (
                f"{question_type}/{question_subtype}: {answer_resolution['status']}; "
                f"model={','.join(answer_resolution['model_predicted_answer'])}; "
                f"direct={','.join(answer_resolution['direct_correct_labels'])}"
            ),
        })

    # 5.4 Every option has explanation
    no_explanation = [
        row["option"]
        for row in result_temp.get("option_analysis", [])
        if not (row.get("explanation") or "").strip()
    ]
    if no_explanation:
        checks.append({"name": "选项均有解析", "status": "warning", "detail": f"选项{','.join(no_explanation)}缺少解析"})
    else:
        checks.append({"name": "选项均有解析", "status": "pass"})

    # 5.5 Any evidence at all?
    if not evidence:
        checks.append({"name": "检索结果", "status": "warning", "detail": "未检索到任何教材句卡"})

    # 5.6 Exam core quality
    checks.append({
        "name": "题目考查方向",
        "status": exam_core_validation["status"],
        "detail": exam_core_validation["detail"],
    })

    # 5.6 detected_answer vs AI answer mismatch hint
    if detected_answer and predicted_set:
        detected_set = {a.strip() for a in detected_answer.split(",") if a.strip()}
        if detected_set != predicted_set:
            checks.append({
                "name": "答案对照提示",
                "status": "warning",
                "detail": f"AI参考答案({','.join(sorted(predicted_set))})与原文标注({detected_answer})不一致，请教研复核",
            })

    statuses = [c["status"] for c in checks]
    if "fail" in statuses:
        validation_status = "needs_review"
    elif "warning" in statuses:
        validation_status = "needs_review"
    else:
        validation_status = "passed"

    result["pipeline"]["validate"] = {
        "validation_status": validation_status,
        "checks": checks,
    }

    display_option_analysis = _build_display_option_analysis(
        options=options,
        option_analysis=result["pipeline"]["explain_options"]["option_analysis"],
        finalized_answer=finalized_answer,
    )
    display_overall_notes = _build_display_overall_notes(
        stem=stem,
        options=options,
        finalized_answer=finalized_answer,
        option_analysis=display_option_analysis,
        needs_teacher_review=validation_status != "passed",
    )

    # ==== Build final section =============================================
    result["final"] = {
        "ai_answer": finalized_answer,
        "confidence": predicted_confidence,
        "question_type": question_type,
        "question_subtype": question_subtype,
        "answer_resolution": answer_resolution,
        "option_explanations": [
            {
                "option": row.get("option", ""),
                "option_text": row.get("option_text", ""),
                "judgement": row.get("judgement", "needs_manual"),
                "judgement_confidence": row.get("judgement_confidence", ""),
                "explanation": row.get("explanation", ""),
                "evidence_status": row.get("evidence_status", "none"),
                "evidence_cards": row.get("evidence_cards", []),
                "common_trap": row.get("common_trap", ""),
            }
            for row in result["pipeline"]["explain_options"]["option_analysis"]
        ],
        "display_option_explanations": display_option_analysis,
        "evidence_cards": cited_cards,
        "exam_direction": exam_core_sentence,
        "exam_core_sentence": exam_core_sentence,
        "exam_core_basis": {},
        "exam_core_validation": exam_core_validation,
        "needs_teacher_review": validation_status != "passed",
        "overall_notes": overall_notes,
        "display_overall_notes": display_overall_notes,
    }

    _save_draft(result)
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _summarize_exam_direction_with_llm(
    client: Any,
    stem: str,
    options: dict[str, str],
    finalized_answer: list[str],
    option_analysis: list[dict[str, Any]],
    llm_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    option_lines = "\n".join(f"{label}. {text}" for label, text in options.items())
    analysis_lines: list[str] = []
    for row in option_analysis:
        label = str(row.get("option", "")).strip()
        if not label:
            continue
        judgement = str(row.get("judgement", "")).strip()
        evidence_status = str(row.get("evidence_status", "")).strip()
        explanation = _short_display_text(_strip_review_artifacts(row.get("explanation", "")), 120)
        quotes: list[str] = []
        for card in row.get("evidence_cards", []) or []:
            if not isinstance(card, dict):
                continue
            quote = str(card.get("quote", "") or "").strip()
            if quote:
                quotes.append(_short_display_text(_INTERNAL_CARD_ID.sub("", quote), 80))
            if len(quotes) >= 2:
                break
        analysis_lines.append(
            f"选项{label}: {judgement}/{evidence_status}\n"
            f"解析要点：{explanation or '无'}\n"
            f"教材依据：{'; '.join(quotes) if quotes else '无'}"
        )

    prompt = f"""你是CAMS教研助理。请根据题干、选项、AI参考答案、选项解析和教材依据，提炼本题的“题目考查方向”。

“题目考查方向”不是答案解析，也不是知识点堆砌。
它要回答：这道题换掉表面情境后，仍然在考学生能否掌握哪条教材知识，并完成什么判断。
请先把正确选项的具体表述上升到教材概念层，不要直接改写正确选项。
如果题目主要在区分相近阶段、概念、风险信号或正常商业行为，优先写“区分X与Y”。
如果题目主要在识别某类教材范围、典型手法或风险标志，优先写“识别……的典型范围/典型手法/红旗标志”。

只输出一句中文，不超过45字。
优先使用句式：
- 考查学生能否识别……
- 考查学生能否区分……
- 考查学生能否判断……
- 考查学生能否将……应用于……

好例子：
- 考查学生能否识别CAMS教材中洗钱相关上游犯罪的典型范围。
- 考查学生能否识别洗钱处置阶段的典型手法。
- 考查学生能否区分洗钱三阶段中处置与离析的典型行为。
- 考查学生能否识别第三方尽职调查中的红旗标志。

坏例子：
- 本题考查反洗钱知识。
- 本题考查洗钱、上游犯罪、毒品交易、逃税等知识点。
- 考查学生能否识别将现金直接存入金融系统的行为。
- 根据教材，正确答案是……
- 选项A错误，选项B正确……

严禁：
- 不要出现选项A/B/C/D等字样。
- 不要出现“答案”“正确”“错误”。
- 不要贴着某个选项写具体动作，要抽象到教材知识点或能力标签。
- 不要出现内部句卡ID。
- 不要写解释过程。

题干：
{stem}

选项：
{option_lines}

AI参考答案：
{','.join(finalized_answer) if finalized_answer else '待判断'}

选项解析与教材依据：
{chr(10).join(analysis_lines)}

请只输出一句话。"""

    try:
        raw, trace = _call_llm_traced(client, "exam_direction", prompt, max_tokens=800)
        if llm_calls is not None:
            llm_calls.append(trace)
        sentence = _extract_exam_direction_sentence(raw)
        return {
            "sentence": sentence,
            "raw_output": raw,
            "status": "ok" if sentence else "empty",
        }
    except Exception as exc:
        return {
            "sentence": "",
            "raw_output": "",
            "status": "error",
            "error": str(exc),
        }


def _extract_exam_direction_sentence(raw_text: Any) -> str:
    raw = str(raw_text or "").strip()
    if not raw:
        return ""

    parsed = _parse_llm_json_object(raw)
    if isinstance(parsed, dict):
        for key in [
            "exam_direction",
            "exam_direction_sentence",
            "exam_core_sentence",
            "sentence",
        ]:
            value = str(parsed.get(key, "") or "").strip()
            if value:
                raw = value
                break

    raw = run_step1.strip_json_fence(raw).strip()
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if lines:
        raw = lines[0]
    raw = re.sub(r"^[\-*•\d\.\、\s]+", "", raw).strip()
    raw = re.sub(r"^(题目考查方向|题目考察方向|考查方向|考察方向)\s*[：:]\s*", "", raw)
    raw = raw.strip("“”\"'`")
    raw = _INTERNAL_CARD_ID.sub("", raw)
    return _short_display_text(raw, 80)


def _parse_llm_json_object(raw_text: str) -> dict[str, Any] | None:
    if not raw_text:
        return None

    candidates: list[str] = []
    for match in re.finditer(r"```(?:json|JSON)?\s*([\s\S]*?)```", raw_text):
        content = match.group(1).strip()
        if content:
            candidates.append(content)

    stripped = run_step1.strip_json_fence(raw_text).strip()
    if stripped:
        candidates.append(stripped)

    match = re.search(r"\{[\s\S]*\}", raw_text)
    if match:
        candidates.append(match.group(0))

    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        parsed = _load_json_object(candidate)
        if isinstance(parsed, dict):
            return parsed
    return None


def _load_json_object(candidate: str) -> dict[str, Any] | None:
    for text in (candidate, _escape_inner_json_quotes(candidate)):
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            parsed = agentic.parse_json_object(text)
            if isinstance(parsed, dict):
                return parsed
    return None


def _escape_inner_json_quotes(text: str) -> str:
    """Repair common LLM JSON where string values contain raw double quotes."""
    output: list[str] = []
    in_string = False
    escaped = False
    length = len(text)

    for idx, char in enumerate(text):
        if char != '"' or escaped:
            output.append(char)
            escaped = (char == "\\" and not escaped)
            if char != "\\":
                escaped = False
            continue

        if not in_string:
            in_string = True
            output.append(char)
            escaped = False
            continue

        next_idx = idx + 1
        while next_idx < length and text[next_idx].isspace():
            next_idx += 1
        next_char = text[next_idx] if next_idx < length else ""
        if next_char in {":", ",", "}", "]", ""}:
            in_string = False
            output.append(char)
        else:
            output.append('\\"')
        escaped = False

    return "".join(output)


def _clean_exam_core_sentence(value: Any) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return ""
    text = text.strip("“”\"'`")
    text = _INTERNAL_CARD_ID.sub("教材原文", text)
    return _short_display_text(text, 110)


def _normalize_exam_core_basis(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {
            "bloom_level": "",
            "cognitive_action": "",
            "textbook_knowledge": "",
            "scenario": "",
            "judgement_logic": "",
            "option_trap": "",
            "evidence_card_ids": [],
        }

    basis = dict(value)
    for key in [
        "bloom_level",
        "cognitive_action",
        "textbook_knowledge",
        "scenario",
        "judgement_logic",
        "option_trap",
    ]:
        basis[key] = str(basis.get(key, "") or "").strip()

    raw_ids = basis.get("evidence_card_ids", [])
    if isinstance(raw_ids, str):
        raw_ids = re.split(r"[,，、;\s]+", raw_ids)
    if not isinstance(raw_ids, list):
        raw_ids = []
    seen: set[str] = set()
    evidence_ids: list[str] = []
    for item in raw_ids:
        cid = str(item or "").strip()
        if cid and cid not in seen:
            seen.add(cid)
            evidence_ids.append(cid)
    basis["evidence_card_ids"] = evidence_ids
    return basis


def _validate_exam_direction(
    raw_sentence: str,
    display_sentence: str,
    stem: str,
    options: dict[str, str],
) -> dict[str, Any]:
    issues: list[str] = []
    sentence = str(display_sentence or "").strip()
    raw = str(raw_sentence or "").strip()

    if not sentence:
        issues.append("未输出题目考查方向")
    elif len(sentence) < 12:
        issues.append("表述过短，可能没有说清考查方向")
    elif len(sentence) > 60:
        issues.append("表述偏长，建议压缩成一句教研可读的话")

    if raw and _INTERNAL_CARD_ID.search(raw):
        issues.append("原始输出露出了内部句卡ID")

    compact_sentence = re.sub(r"\s+", "", sentence)
    if any(phrase in sentence for phrase in _EXAM_CORE_GENERIC_PHRASES) and len(compact_sentence) <= 30:
        issues.append("表述偏泛，缺少具体教材知识或判断任务")
    if sentence and not re.search(r"能否|识别|区分|判断|应用|掌握|理解", sentence):
        issues.append("缺少能力或判断动作")
    if re.search(r"选项[A-K]|[A-K]选项|正确答案|答案是|错误|正确", sentence):
        issues.append("像答案解析，不像考查方向")
    if re.search(r"根据教材|因此|所以|故|因为", sentence):
        issues.append("像解释过程，不像一句考查方向")

    option_texts = [str(text or "").strip() for text in options.values()]
    if sentence and (sentence in stem and len(sentence) >= 20):
        issues.append("表述可能只是复述题干，没有抽象出核心")
    elif any(text and text in sentence and len(text) >= 18 for text in option_texts):
        issues.append("表述可能只是复述选项，没有抽象出核心")

    return {
        "core_valid": not issues,
        "status": "pass" if not issues else "warning",
        "issues": issues,
        "detail": "；".join(issues) if issues else "已输出可展示的题目考查方向",
    }


def _normalize_answer_labels(value: Any, options: dict[str, str]) -> list[str]:
    labels = set(options)
    if isinstance(value, str):
        raw_items = [value]
    elif isinstance(value, list):
        raw_items = value
    else:
        raw_items = []

    normalized: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        text = str(item or "").strip().upper()
        if not text:
            continue
        parts = [part for part in re.split(r"[,，、;；\s]+", text) if part]
        if len(parts) == 1 and re.fullmatch(r"[A-K]+", parts[0]):
            parts = list(parts[0])
        for part in parts:
            if part in labels and part not in seen:
                seen.add(part)
                normalized.append(part)
    return normalized


def _sanitize_question_input(text: str) -> tuple[str, dict[str, Any]]:
    raw = str(text or "")
    match = _find_answer_or_explanation_leak(raw)
    if not match:
        return raw.strip(), {
            "stripped_answer_or_explanation": False,
            "strip_heading": "",
            "strip_start": None,
            "clean_chars": len(raw.strip()),
            "raw_chars": len(raw),
        }

    clean = raw[: match.start()].rstrip()
    return clean, {
        "stripped_answer_or_explanation": True,
        "strip_heading": match.heading,
        "strip_start": match.start(),
        "clean_chars": len(clean),
        "raw_chars": len(raw),
    }


class _InputLeakMatch:
    def __init__(self, start: int, heading: str) -> None:
        self._start = start
        self.heading = heading

    def start(self) -> int:
        return self._start


def _find_answer_or_explanation_leak(raw: str) -> _InputLeakMatch | None:
    heading_match = _ANSWER_EXPLANATION_HEADING.search(raw)
    earliest: _InputLeakMatch | None = None
    if heading_match:
        earliest = _InputLeakMatch(heading_match.start(), heading_match.group(1))

    option_count = len(_OPTION_LINE.findall(raw))
    if option_count < 2:
        return earliest

    offset = 0
    for line in raw.splitlines(keepends=True):
        content = line.strip()
        if _BARE_ANSWER_LINE.fullmatch(content):
            line_before = raw[:offset]
            if len(_OPTION_LINE.findall(line_before)) >= 2:
                answer_match = _InputLeakMatch(offset, "疑似答案行")
                if earliest is None or answer_match.start() < earliest.start():
                    earliest = answer_match
                break
        offset += len(line)

    return earliest


def _expected_answer_count(stem: str) -> int | None:
    text = str(stem or "")
    m = re.search(r"(?:请选择|选择|选出|请选)([一二两三四五六七八九十1-9]+)\s*(?:个|项|题|条)?", text)
    if not m:
        return None
    token = m.group(1)
    chinese = {
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    if token.isdigit():
        try:
            return int(token)
        except ValueError:
            return None
    return chinese.get(token)


def _direct_correct_labels(
    option_analysis: list[dict[str, Any]], options: dict[str, str]
) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for row in option_analysis:
        label = str(row.get("option", "")).strip().upper()
        if label not in options or label in seen:
            continue
        if row.get("judgement") != "correct":
            continue
        if row.get("evidence_status") != "direct":
            continue
        if not row.get("evidence_cards"):
            continue
        seen.add(label)
        labels.append(label)
    return labels


def _finalize_answer_by_type(
    predicted_answer: Any,
    option_analysis: list[dict[str, Any]],
    question_type: str,
    question_subtype: str,
    options: dict[str, str],
) -> dict[str, Any]:
    predicted = _normalize_answer_labels(predicted_answer, options)
    direct_correct = _direct_correct_labels(option_analysis, options)

    if question_type in {"multiple_choice", "true_false"}:
        if direct_correct:
            # Include predicted-correct options even when evidence is only indirect.
            # direct_correct requires evidence_status=direct; the adjudicator may
            # conservatively mark strong but indirect evidence as "indirect".
            final = list(dict.fromkeys(direct_correct + predicted))
            status = "ok"
        elif predicted:
            final = predicted
            status = "model_only_needs_review"
        else:
            final = []
            status = "needs_manual"
    elif question_type == "single_choice":
        if len(direct_correct) == 1:
            final = direct_correct
            status = "ok"
        elif len(direct_correct) > 1:
            # Multiple direct-correct options for a single-choice question:
            # trust the adjudicator's first predicted answer as tie-breaker.
            if len(predicted) == 1 and predicted[0] in direct_correct:
                final = predicted
                status = "ok"
            elif predicted and predicted[0] in direct_correct:
                final = [predicted[0]]
                status = "multiple_direct_tiebroken"
            else:
                final = [direct_correct[0]]
                status = "multiple_direct_fallback"
        elif len(predicted) == 1:
            final = predicted
            status = "model_only_needs_review"
        elif len(predicted) > 1:
            final = [predicted[0]]
            status = "multiple_predicted_tiebroken"
        else:
            final = []
            status = "needs_manual"
    else:
        final = direct_correct or predicted
        status = "ok" if direct_correct else "unknown_type_needs_review"

    return {
        "answer": final,
        "status": status,
        "question_type": question_type,
        "question_subtype": question_subtype,
        "model_predicted_answer": predicted,
        "direct_correct_labels": direct_correct,
    }


def _strip_review_artifacts(text: Any) -> str:
    value = str(text or "").strip()
    if not value:
        return ""
    markers = ["\n复核修正：", "\n复核修正:", "复核修正：", "复核修正:"]
    cut = len(value)
    for marker in markers:
        idx = value.find(marker)
        if idx >= 0:
            cut = min(cut, idx)
    value = value[:cut].strip()
    value = re.sub(r"教材句卡\s*(?:v6s_N\d+\s*(?:、|和|,|，)?\s*)+", "教材原文", value)
    value = re.sub(r"v6s_N\d+", "教材原文", value)
    value = value.replace("教材句卡", "教材原文").replace("句卡", "原文")
    return value.strip()


def _short_display_text(text: str, limit: int = 220) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    min_cut = min(80, max(30, int(limit * 0.45)))
    sentence_cuts = [
        match.end()
        for match in re.finditer(r"[。！？!?；;]", value)
        if min_cut <= match.end() <= limit
    ]
    if sentence_cuts:
        return value[: sentence_cuts[-1]].strip()

    soft_cuts = [
        match.end()
        for match in re.finditer(r"[，,、：:]", value)
        if min_cut <= match.end() <= limit
    ]
    cut = soft_cuts[-1] if soft_cuts else limit
    clipped = value[:cut].rstrip("，,、：:；;。 ")
    clipped = re.sub(r"(以及|并且|或者|但是|因此|所以|因为|如果|同时|和|与|及|或|但|并|而|将|把|对|向|从|在|为)$", "", clipped).rstrip()
    return clipped + ("。" if clipped and not re.search(r"[。！？!?]$", clipped) else "")


def _apply_evidence_entailment_guard(
    stem: str,
    options: dict[str, str],
    option_analysis: list[dict[str, Any]],
) -> dict[str, Any]:
    """Deterministic guard for common evidence-entailment mistakes.

    This is intentionally conservative: it does not know the answer key. It
    only adjusts cases where the cited textbook quote already makes the
    evidence direction clear.
    """
    rows = [dict(row) for row in option_analysis]
    changes: list[dict[str, str]] = []
    for row in rows:
        label = str(row.get("option", "")).strip().upper()
        if label not in options:
            continue
        option_text = str(row.get("option_text", options.get(label, ""))).strip()
        evidence_quotes = _row_evidence_quotes(row)
        if not evidence_quotes:
            continue

        requirement_support = _has_requirement_gap_support(option_text, evidence_quotes)
        if requirement_support and (
            row.get("judgement") != "correct" or row.get("evidence_status") != "direct"
        ):
            row["judgement"] = "correct"
            row["evidence_status"] = "direct"
            row["judgement_confidence"] = row.get("judgement_confidence") or "medium"
            row["needs_teacher_review"] = True
            row["teacher_review_reason"] = "规则复核将规范要求与缺失表述识别为直接支持"
            row["explanation"] = _append_review_note(
                row.get("explanation", ""),
                "规则复核：教材原文在同一场景下要求纳入/执行该事项，选项描述其缺乏，可构成直接支持。",
            )
            changes.append({
                "option": label,
                "action": "promote_requirement_gap",
                "detail": "教材要求与选项缺失形成直接对应",
            })
            continue

        if row.get("judgement") == "correct" and row.get("evidence_status") == "direct":
            weak_detail = _weak_direct_support_reason(option_text, evidence_quotes)
            if weak_detail:
                row["judgement"] = "insufficient"
                row["evidence_status"] = "indirect"
                row["judgement_confidence"] = "medium"
                row["needs_teacher_review"] = True
                row["teacher_review_reason"] = "规则复核认为 direct 证据与选项全文重合不足"
                row["explanation"] = _append_review_note(
                    row.get("explanation", ""),
                    "规则复核：引用原文与选项全文的主体、行为或场景重合不足，降级为相关但不足以直接推出。",
                )
                changes.append({
                    "option": label,
                    "action": "downgrade_weak_direct",
                    "detail": weak_detail,
                })

    return {
        "applied": bool(changes),
        "changes": changes,
        "option_analysis": rows,
    }


def _row_evidence_quotes(row: dict[str, Any]) -> list[str]:
    quotes: list[str] = []
    for card in row.get("evidence_cards", []) or []:
        if not isinstance(card, dict):
            continue
        quote = str(card.get("quote", "") or "").strip()
        if quote:
            quotes.append(quote)
    return quotes


def _has_requirement_gap_support(option_text: str, evidence_quotes: list[str]) -> bool:
    option = _compact_for_match(option_text)
    negation_terms = (
        "缺乏",
        "没有",
        "未纳入",
        "未包含",
        "未包括",
        "未建立",
        "未制定",
        "缺少",
        "不具备",
        "不足",
    )
    if not any(term in option for term in negation_terms):
        return False
    requirement_terms = (
        "应",
        "应当",
        "必须",
        "需要",
        "需",
        "纳入",
        "包括",
        "包含",
        "要求",
        "确保",
        "建立",
        "制定",
        "执行",
        "审查",
    )
    for quote in evidence_quotes:
        compact_quote = _compact_for_match(quote)
        if not any(term in compact_quote for term in requirement_terms):
            continue
        if _token_overlap_count(option_text, quote) >= 2:
            return True
    return False


def _weak_direct_support_reason(option_text: str, evidence_quotes: list[str]) -> str:
    max_overlap = max(
        (_token_overlap_count(option_text, quote) for quote in evidence_quotes),
        default=0,
    )
    option = _compact_for_match(option_text)
    third_party_terms = (
        "第三方",
        "供应商",
        "承包商",
        "代理",
        "代理人",
        "中介",
        "业务伙伴",
        "商业伙伴",
        "其他方",
        "关联方",
        "外部方",
        "外包",
    )
    if "第三方" in option:
        has_same_subject = any(
            any(term in _compact_for_match(quote) for term in third_party_terms)
            for quote in evidence_quotes
        )
        if not has_same_subject:
            return "选项主体为第三方，但引用原文未落回第三方/供应商/承包商等同类主体"
    return ""


def _append_review_note(text: Any, note: str) -> str:
    previous = str(text or "").strip()
    return f"{previous}\n{note}".strip()


def _compact_for_match(text: Any) -> str:
    return re.sub(r"\s+", "", str(text or ""))


def _token_overlap_count(left: str, right: str) -> int:
    left_tokens = _significant_tokens(left)
    right_tokens = _significant_tokens(right)
    return len(left_tokens & right_tokens)


def _significant_tokens(text: str) -> set[str]:
    value = str(text or "").strip()
    if not value:
        return set()
    compact = _compact_for_match(value)
    lexicon = {
        "第三方",
        "供应商",
        "承包商",
        "业务伙伴",
        "政府官员",
        "公务人员",
        "政治公众人物",
        "非家庭",
        "商业关系",
        "关系",
        "声明",
        "不寻常",
        "异常",
        "付款",
        "开票",
        "账单",
        "程序",
        "协议",
        "反腐败",
        "合规",
        "合规条款",
        "条款",
        "纳入",
        "缺乏",
        "能力",
        "服务",
        "商品",
        "金额",
        "合理",
        "风险",
        "红旗",
        "可疑",
        "高风险",
        "尽职调查",
        "背景调查",
    }
    stopwords = {
        "选项",
        "教材",
        "原文",
        "句卡",
        "正确",
        "错误",
        "属于",
        "不属",
        "这是",
        "这个",
        "一种",
        "以及",
        "例如",
        "进行",
        "可以",
        "可能",
        "相关",
        "情况",
        "情形",
        "之前",
        "之后",
        "其中",
        "如果",
        "因为",
        "所以",
        "认为",
        "显示",
        "说明",
        "指出",
        "表明",
    }
    tokens: list[str]
    try:
        import logging
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import jieba  # type: ignore

        jieba.setLogLevel(logging.ERROR)
        tokens = [token.strip() for token in jieba.lcut(value)]
    except Exception:
        tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", value)
    result: set[str] = set()
    for term in lexicon:
        if term in compact:
            result.add(term)
    for token in tokens:
        token = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", token)
        if len(token) < 2 or token in stopwords:
            continue
        if token.isdigit():
            continue
        result.add(token)
    return result


def _fallback_option_explanation(
    label: str,
    option_text: str,
    is_answer: bool,
    evidence_status: str,
) -> str:
    if is_answer:
        if evidence_status in {"direct", "indirect"}:
            return f"选项{label}与教材中的可疑资金转移特征最匹配，因此作为本题答案。"
        return f"选项{label}是系统最终保留的答案，但依据不够直接，建议教研复核。"
    if evidence_status == "conflict":
        return f"选项{label}与教材表述不一致，因此排除。"
    if evidence_status in {"none", "indirect", ""}:
        return f"选项{label}本身可能有可疑性，但不是题干中最应聚焦的风险点。"
    return f"选项{label}不是本题最终答案。"


def _build_display_option_analysis(
    options: dict[str, str],
    option_analysis: list[dict[str, Any]],
    finalized_answer: list[str],
) -> list[dict[str, Any]]:
    answer_set = {str(label).strip().upper() for label in finalized_answer}
    rows_by_label = {
        str(row.get("option", "")).strip().upper(): row
        for row in option_analysis
        if str(row.get("option", "")).strip()
    }
    display_rows: list[dict[str, Any]] = []
    for label, option_text in options.items():
        normalized_label = str(label).strip().upper()
        row = rows_by_label.get(normalized_label, {})
        is_answer = normalized_label in answer_set
        evidence_status = str(row.get("evidence_status", "")).strip()
        explanation = _strip_review_artifacts(row.get("explanation", ""))
        if not explanation:
            explanation = _fallback_option_explanation(
                normalized_label, option_text, is_answer, evidence_status
            )
        display_rows.append({
            "option": normalized_label,
            "option_text": row.get("option_text") or option_text,
            "judgement": "correct" if is_answer else "incorrect",
            "judgement_confidence": row.get("judgement_confidence", ""),
            "explanation": _short_display_text(explanation),
            "evidence_status": evidence_status or "none",
            "evidence_cards": row.get("evidence_cards", []),
            "common_trap": _strip_review_artifacts(row.get("common_trap", "")),
        })
    return display_rows


def _build_display_overall_notes(
    stem: str,
    options: dict[str, str],
    finalized_answer: list[str],
    option_analysis: list[dict[str, Any]],
    needs_teacher_review: bool,
) -> str:
    if not finalized_answer:
        return "系统暂未形成可靠答案，建议教研复核题干、选项和教材依据。"
    answer_text = "、".join(finalized_answer)
    chosen = [
        row for row in option_analysis
        if str(row.get("option", "")).strip().upper() in set(finalized_answer)
    ]
    chosen_reason = ""
    if chosen:
        chosen_reason = _strip_review_artifacts(chosen[0].get("explanation", ""))
    if chosen_reason:
        note = f"答案为 {answer_text}。{_short_display_text(chosen_reason, 210)}"
    else:
        note = f"答案为 {answer_text}。该选项与题干中的核心风险点最匹配。"
    if needs_teacher_review:
        note += " 部分依据为相近教材表述，建议教研复核后定稿。"
    return note


def _review_answer_with_llm(
    client: Any,
    stem: str,
    options: dict[str, str],
    question_type: str,
    question_subtype: str,
    predicted_answer: list[str],
    option_analysis: list[dict[str, Any]],
    llm_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    expected_count = _expected_answer_count(stem)
    candidate_lines: list[str] = []
    for row in option_analysis:
        option = str(row.get("option", "")).strip()
        if not option:
            continue
        option_text = str(row.get("option_text", options.get(option, ""))).strip()
        judgment = str(row.get("judgement", "")).strip()
        status = str(row.get("evidence_status", "")).strip()
        explanation = str(row.get("explanation", "")).strip()
        evidence_cards = row.get("evidence_cards", []) or []
        card_lines = []
        for card in evidence_cards:
            if not isinstance(card, dict):
                continue
            cid = str(card.get("card_id", "")).strip()
            support_type = str(card.get("support_type", "")).strip()
            relevance = str(card.get("relevance", "")).strip()
            quote = str(card.get("quote", "")).strip()
            reason = str(card.get("reason", "")).strip()
            if cid:
                card_lines.append(
                    f"- {cid} | {support_type} | {relevance}\n"
                    f"  原文：{quote}\n"
                    f"  上轮理由：{reason}"
                )
        candidate_lines.append(
            f"选项{option}: {option_text}\n"
            f"上轮判断：{judgment} | {status}\n"
            f"上轮解析：{explanation}\n"
            f"引用教材：\n"
            + ("\n".join(card_lines) if card_lines else "- 无直接教材句卡")
        )

    prompt = f"""你是CAMS新题解析的答案复核员。
你的任务是逐项复核所有选项，重新判断上一轮裁判是否正确区分了“教材直接支持、教材反向支持、主题相关但不足以推出、证据不足”。

只允许基于以下内容判断：
1. 题干
2. 题型
3. 题型细分
4. 各选项的既有解析与引用教材句卡

严禁：
- 不要引入题库标准答案
- 不要重新检索
- 不要扩大解释
- 不要因为某项“相关”就保留它
- 不要只复核上一轮预测答案，必须检查所有选项

题干：
{stem}

题型：{question_type}
题型细分：{question_subtype}
题干要求答案数量：{expected_count if expected_count else "未明确"}
上一轮预测答案：{",".join(predicted_answer)}

选项复核材料：
{chr(10).join(candidate_lines)}

请输出严格JSON，不要Markdown：
{{
  "review_status": "modified/unchanged",
  "reviewed_answer": ["A"],
  "review_confidence": "high/medium/low/insufficient/unchanged",
  "dropped_options": ["B"],
  "kept_options": ["C"],
  "option_revisions": [
    {{
      "option": "A",
      "judgement": "correct/incorrect/insufficient/needs_manual",
      "evidence_status": "direct/indirect/none/conflict/needs_manual",
      "review_note": "复核理由"
    }}
  ],
  "review_notes": "说明为什么删掉或保留某些选项"
}}

规则：
- direct 不是“主题相关”，而是“选项全文能被教材原文直接推出”。必须同时匹配主体、行为、场景、判断性质。只共享关键词、概念或风险背景，最多算 indirect/context。
- 正确项必须有正向支持。教材原文需要直接列举、定义、要求、禁止、说明该行为/情形属于题干所问类别。若题干问风险信号/红旗标志，原文中的“风险指标、可疑特征、警示信号、应当防范/纳入/审查”等等价表达也可支持。
- “规范要求”可以支持“缺失风险”，但必须同场景。如果教材说在某场景下“应当/必须/需要做 X”，选项说同场景下“缺乏/没有/未纳入 X”，可以视为 direct；如果只是一般性建议或不同场景要求，不能直接推出。
- 背景风险不能自动推出具体选项。教材说某类人、机构、地区、产品“风险较高”，不等于任何与其有关的关系、声明或行为都是题干所问的正确项；除非原文明确把该具体关系/行为列为风险信号，或同段上下文能直接推出。
- 错误项不能只靠“没找到证据”判错。若教材没有支持也没有反驳，应标为 insufficient。只有教材明确支持相反判断、正常情形、排除条件，才判 incorrect。
- 多选数量是约束，不是证据。题干写“选择两个/三个”，最终答案应尽量符合数量；但不能为了凑数量把 indirect 选项升成 correct。如果 direct correct 数量和题干数量不一致，可以修改为最有证据的答案并在 review_notes 标明需人工关注。
- 复核必须重新检查所有选项。可以降级上一轮误选项，也可以升级上一轮漏掉但证据充分的选项。
- 最终答案只来自 correct 且证据足够的选项。如果某选项是 correct 但 evidence_status 不是 direct，应在 review_notes 中说明风险。
- 如果复核后判断与上一轮不同，review_status 必须是 modified，并填写 option_revisions。"""

    try:
        raw, trace = _call_llm_traced(client, "reviewer", prompt, max_tokens=2500)
        if llm_calls is not None:
            llm_calls.append(trace)
        parsed = _parse_llm_json_object(raw) or {}
    except Exception as exc:
        return {
            "applied": False,
            "review_status": "error",
            "review_confidence": "insufficient",
            "review_error": str(exc),
        }

    reviewed_answer = parsed.get("reviewed_answer", [])
    if not isinstance(reviewed_answer, list):
        reviewed_answer = []
    normalized_answer = _normalize_answer_labels(reviewed_answer, options)
    review_status = str(parsed.get("review_status", "unchanged")).strip() or "unchanged"
    review_confidence = str(parsed.get("review_confidence", "unchanged")).strip() or "unchanged"
    dropped_options = _normalize_answer_labels(parsed.get("dropped_options", []), options)
    kept_options = _normalize_answer_labels(parsed.get("kept_options", []), options)
    review_notes = str(parsed.get("review_notes", "")).strip()
    raw_revisions = parsed.get("option_revisions", [])
    option_revisions: dict[str, dict[str, str]] = {}
    allowed_judgements = {"correct", "incorrect", "insufficient", "needs_manual"}
    allowed_statuses = {"direct", "indirect", "none", "conflict", "needs_manual"}
    if isinstance(raw_revisions, list):
        for item in raw_revisions:
            if not isinstance(item, dict):
                continue
            label = str(item.get("option", "")).strip().upper()
            if label not in options:
                continue
            judgement = str(item.get("judgement", "")).strip()
            evidence_status = str(item.get("evidence_status", "")).strip()
            note = str(item.get("review_note", "")).strip()
            option_revisions[label] = {
                "judgement": judgement if judgement in allowed_judgements else "",
                "evidence_status": evidence_status if evidence_status in allowed_statuses else "",
                "review_note": note,
            }

    applied = review_status == "modified" and (bool(normalized_answer) or bool(option_revisions))
    if applied:
        original = set(_normalize_answer_labels(predicted_answer, options))
        revised = set(normalized_answer)
        inferred_dropped = [label for label in options if label in original and label not in revised]
        inferred_kept = [label for label in options if label in revised]
        if not dropped_options:
            dropped_options = inferred_dropped
        if not kept_options:
            kept_options = inferred_kept
    revised_rows = [dict(row) for row in option_analysis]
    if applied:
        dropped = set(dropped_options)
        added = set(normalized_answer) - set(_normalize_answer_labels(predicted_answer, options))
        for row in revised_rows:
            label = str(row.get("option", "")).strip().upper()
            if label not in options:
                continue
            revision = option_revisions.get(label, {})
            changed = False
            if revision.get("judgement"):
                row["judgement"] = revision["judgement"]
                changed = True
            elif label in dropped and row.get("judgement") == "correct":
                row["judgement"] = "incorrect"
                changed = True
            elif label in added:
                row["judgement"] = "correct"
                changed = True

            if revision.get("evidence_status"):
                row["evidence_status"] = revision["evidence_status"]
                changed = True
            elif label in dropped and row.get("evidence_status") == "direct":
                row["evidence_status"] = "indirect"
                changed = True
            elif label in added and row.get("evidence_cards"):
                row["evidence_status"] = "direct"
                changed = True

            if not changed:
                continue
            row["judgement_confidence"] = review_confidence
            note = revision.get("review_note") or review_notes or "复核重新判断了该选项的证据等级。"
            previous = str(row.get("explanation", "")).strip()
            row["explanation"] = f"{previous}\n复核修正：{note}".strip()
            row["needs_teacher_review"] = True
            row["teacher_review_reason"] = "答案复核调整了该选项的判断"

    return {
        "applied": applied,
        "review_status": review_status,
        "reviewed_answer": normalized_answer if applied else [],
        "review_confidence": review_confidence,
        "dropped_options": dropped_options,
        "kept_options": kept_options,
        "option_revisions": option_revisions,
        "review_notes": review_notes,
        "option_analysis": revised_rows if applied else option_analysis,
        "raw_review_output": raw,
    }


def _call_llm_traced(
    client: Any,
    stage: str,
    prompt: str,
    max_tokens: int,
    retries: int | None = None,
) -> tuple[str, dict[str, Any]]:
    started = time.perf_counter()
    attempt_retries = retries if retries is not None else run_step1.LLM_RETRY
    response_obj: Any = None
    last_error: Exception | None = None
    for attempt in range(attempt_retries):
        try:
            kwargs: dict[str, Any] = {
                "model": run_step1.MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": max_tokens,
                "extra_body": run_step1.V4_NO_THINK,
            }
            response_obj = client.chat.completions.create(**kwargs)
            content = (response_obj.choices[0].message.content or "").strip()
            trace = _record_llm_trace(stage, max_tokens, started, response_obj, prompt, content)
            return content, trace
        except Exception as exc:
            last_error = exc
            if attempt < attempt_retries - 1:
                time.sleep(3 + attempt * 2)
    trace = {
        "stage": stage,
        "max_tokens": max_tokens,
        "status": "error",
        "error": str(last_error) if last_error else "LLM call failed",
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
    }
    raise RuntimeError(trace["error"])


def _record_llm_trace(
    stage: str,
    max_tokens: int,
    started: float,
    response_obj: Any,
    prompt: str,
    content: str,
) -> dict[str, Any]:
    usage = getattr(response_obj, "usage", None)
    prompt_tokens = getattr(usage, "prompt_tokens", None) if usage is not None else None
    completion_tokens = getattr(usage, "completion_tokens", None) if usage is not None else None
    total_tokens = getattr(usage, "total_tokens", None) if usage is not None else None
    return {
        "stage": stage,
        "model": run_step1.MODEL,
        "max_tokens": max_tokens,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "prompt_chars": len(prompt),
        "completion_chars": len(content),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "usage_present": usage is not None,
    }


def _build_insufficient_options(options: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "option": label,
            "option_text": text,
            "judgement": "insufficient",
            "judgement_confidence": "insufficient",
            "evidence_status": "none",
            "evidence_cards": [],
            "explanation": "证据裁判LLM输出无法解析，请教研人工判断。",
            "common_trap": "",
            "needs_teacher_review": True,
            "teacher_review_reason": "LLM输出解析失败",
        }
        for label, text in options.items()
    ]


def _empty_final() -> dict[str, Any]:
    return {
        "ai_answer": [],
        "confidence": "insufficient",
        "option_explanations": [],
        "evidence_cards": [],
        "needs_teacher_review": True,
        "overall_notes": "题目拆解失败，无法进入后续流程。",
    }


def _save_draft(result: dict[str, Any]) -> Path:
    _DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    draft_id = (
        f"nq_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_"
        f"{uuid.uuid4().hex[:4]}"
    )
    result["draft_id"] = draft_id
    result["created_at"] = datetime.datetime.now().isoformat()
    draft_path = _DRAFTS_DIR / f"{draft_id}.json"
    with open(draft_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[run_pipeline] Draft saved → {draft_path}")
    return draft_path


# ---------------------------------------------------------------------------
# CLI entry point (for Phase 1 delivery testing)
# ---------------------------------------------------------------------------
def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the blind new-question pipeline on a single question."
    )
    parser.add_argument(
        "text", nargs="?", default=None,
        help="Raw pasted question text (use quotes for multiline)."
    )
    parser.add_argument(
        "--file", "-f", default=None,
        help="Read question text from a file instead of command line."
    )
    parser.add_argument(
        "--scope", default="v6-sentence",
        choices=["v6-sentence", "ch2", "v6-except-ch2", "ch2-plus-v6-except"],
        help="Evidence pool to use (default: v6-sentence)."
    )
    parser.add_argument(
        "--top-k", type=int, default=30,
        help="Max candidate cards per option (default: 30)."
    )
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8").strip()
    elif args.text:
        text = args.text.strip()
    else:
        # Read from stdin if no argument
        print("Paste question text (Ctrl+Z then Enter on Windows, Ctrl+D on Unix):")
        text = sys.stdin.read().strip()

    if not text:
        print("[run_pipeline] ERROR: No input text provided.", file=sys.stderr)
        return 1

    print(f"[run_pipeline] Loading runtime (scope={args.scope}) ...")
    from evidence_pool import load_new_question_runtime

    rt = load_new_question_runtime(evidence_scope=args.scope)

    print(f"[run_pipeline] Running pipeline on {len(text)} chars of input ...")
    result = run_new_question_pipeline(text, rt=rt, top_k=args.top_k)

    # Print summary
    final = result.get("final", {})
    validate = result.get("pipeline", {}).get("validate", {})
    print()
    print(f"  draft_id:        {result.get('draft_id')}")
    print(f"  status:          {result.get('status')}")
    print(f"  ai_answer:       {final.get('ai_answer')}")
    print(f"  confidence:      {final.get('confidence')}")
    print(f"  cited_cards:     {len(final.get('evidence_cards', []))}")
    print(f"  needs_review:    {final.get('needs_teacher_review')}")
    print(f"  validation:      {validate.get('validation_status')}")
    for c in validate.get("checks", []):
        icon = {"pass": "V", "warning": "!", "fail": "X"}.get(c["status"], "?")
        print(f"    [{icon}] {c['name']}: {c.get('detail', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
