# -*- coding: utf-8 -*-
"""s4 — 解析撰写专用：LLM 输出归一化层。所有 normalize_*、_fallback_*、校验辅助函数。"""

from __future__ import annotations

import json, re, time
from typing import Any

from 解析撰写.s1_explanation_data import (
    INSUFFICIENT_TEXT, INTERNAL_UNIT_ID_RE, SCHEMA_VERSION, PROMPT_VERSION,
    SOURCE_QUOTE_MIN_LENGTH, SOURCE_QUOTE_MAX_LENGTH,
    TEXTBOOK_BASIS_TYPES, STEM_BASIS_TYPES, _DECISION_TO_BASIS,
    _get_unit_page_map,
)
from 解析撰写.s2_explanation_material import (
    candidate_by_unit, enriched_option_material,
)
from 公共函数.llm_utils import strip_json_fence


def parse_json_object(raw_text: str) -> dict[str, Any] | None:
    cleaned = strip_json_fence(raw_text)
    if not cleaned:
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    try:
        import json_repair
        return json.loads(json_repair.repair_json(cleaned))
    except Exception:
        return None


def _valid_citations(values: Any, allowed: set[str]) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for value in values:
        uid = str(value or "").strip()
        if uid in allowed and uid not in out:
            out.append(uid)
    return out


def _grounded_block(value: Any, allowed: set[str]) -> dict[str, Any]:
    value = value if isinstance(value, dict) else {}
    text = _clean_prose(value.get("text", ""))
    cited = _valid_citations(value.get("cited_unit_ids"), allowed)[:3]
    if not text or not cited:
        return {"text": INSUFFICIENT_TEXT, "cited_unit_ids": []}
    return {"text": text, "cited_unit_ids": cited}


def _clean_prose(value: Any) -> str:
    text = INTERNAL_UNIT_ID_RE.sub("", str(value or ""))
    text = re.sub(r"[ \t]+([，。；：、！？])", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _cited_source_text(
    cited_unit_ids: list[str], unit_map: dict[str, dict[str, Any]]
) -> str:
    parts: list[str] = []
    for uid in cited_unit_ids:
        unit = unit_map.get(uid, {})
        parts.extend(
            str(unit.get(field, "") or "")
            for field in ("knowledge_zh", "knowledge_en", "en_quote")
        )
    return " ".join(parts).casefold()


def _source_has_term(source: str, term: str) -> bool:
    folded = term.casefold()
    if folded.isascii():
        return bool(re.search(rf"(?<![a-z]){re.escape(folded)}(?![a-z])", source))
    return folded in source


def _unsupported_relation_issues(
    text: str,
    cited_unit_ids: list[str],
    unit_map: dict[str, dict[str, Any]],
) -> list[str]:
    source = _cited_source_text(cited_unit_ids, unit_map)
    gates = (
        ("必要性", ("必须", "要求", "只能", "仅能", "仅需", "必要条件"),
         ("必须", "要求", "只能", "仅能", "仅需", "必要", "must", "require", "requires", "required", "requiring", "only", "necessary")),
        ("定义性", ("特指",), ("特指", "定义", "是指", "意味着", "refers to", "means", "defined as")),
        ("分类关系", ("属于", "等同于", "相当于", "极端形式"),
         ("属于", "等同", "相当", "形式", "类型", "part of", "form of", "type of", "equivalent")),
        ("典型性", ("典型",), ("典型", "常见", "typical", "typically", "common", "commonly")),
        ("频率", ("通常", "往往", "一般会", "经常"),
         ("通常", "往往", "一般", "经常", "typical", "typically", "usual", "usually", "often", "general", "generally")),
        ("关联关系", ("相关", "关联"), ("相关", "关联", "related", "associated", "connection")),
    )
    issues: list[str] = []
    for label, prose_terms, source_terms in gates:
        if any(_source_has_term(source, term) for term in source_terms):
            continue
        for term in prose_terms:
            start = text.find(term)
            if start < 0:
                continue
            prefix = text[max(0, start - 4): start]
            if term == "要求" and any(marker in prefix for marker in ("题干", "本题", "该项", "选项")):
                continue
            if term in ("属于", "等同于", "相当于") and prefix.endswith(("不", "未", "非")):
                continue
            issues.append(f'无原文支撑的{label}措辞"{term}"')
            break
    return issues


def _normalize_grounded_block(
    value: Any, allowed: set[str], unit_map: dict[str, dict[str, Any]], location: str,
) -> tuple[dict[str, Any], list[str]]:
    block = _grounded_block(value, allowed)
    if not block["cited_unit_ids"]:
        return block, [f"{location}缺少合法教材引用"]
    return block, []


def _core_context_issues(text: str) -> list[str]:
    phrases = ("这种模式符合", "这一模式符合", "整体模式符合")
    return [f'核心解析混合决定性信号与伴随事实"{phrase}"' for phrase in phrases if phrase in text]


def _fallback_core_analysis(option_explanations: list[dict[str, Any]]) -> dict[str, Any] | None:
    rows = [row for row in option_explanations
            if row.get("judgement") == "correct"
            and row.get("basis_type") in {"textbook_direct", "textbook_definition_application"}
            and row.get("analysis") != INSUFFICIENT_TEXT]
    if not rows:
        return None
    text = " ".join(str(row.get("analysis", "")).strip() for row in rows).strip()
    cited: list[str] = []
    for row in rows:
        for uid in row.get("cited_unit_ids", []) or []:
            if uid not in cited:
                cited.append(uid)
    if not text or not cited:
        return None
    return {"text": text, "cited_unit_ids": cited[:3]}


def _fallback_exam_point(
    option_explanations: list[dict[str, Any]], framework: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    framework = framework or {}
    fw_type = str(framework.get("type", "") or "")
    if fw_type in ("is_definition", "is_domain"):
        return {"text": "本题需依据教材规则/定义判断各选项与题干条件的对应关系。"}
    if fw_type == "is_scenario":
        if framework.get("cited_unit_ids"):
            return {"text": "本题需依据教材规则结合题干事实进行场景判断。"}
        return {"text": "本题需依据题干明确事实对各选项进行直接判断。"}
    has_textbook = any(row.get("basis_type") in {"textbook_direct", "textbook_definition_application"}
                       for row in option_explanations)
    if has_textbook:
        return {"text": "本题需依据教材规则/定义判断各选项与题干条件的对应关系。"}
    return {"text": "本题需依据题干明确事实对各选项进行直接判断。"}


def _fallback_easy_mistake(
    option_explanations: list[dict[str, Any]], unit_map: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    correct = next((row for row in option_explanations
                    if row.get("judgement") == "correct"
                    and row.get("basis_type") in {"textbook_direct", "textbook_definition_application"}
                    and row.get("cited_unit_ids")), None)
    distractor = next((row for row in option_explanations
                       if row.get("judgement") == "incorrect"
                       and row.get("basis_type") in {"textbook_direct", "textbook_definition_application"}
                       and row.get("cited_unit_ids")), None)
    if not correct or not distractor:
        return None
    correct_uid = correct["cited_unit_ids"][0]
    distractor_uid = distractor["cited_unit_ids"][0]
    if correct_uid == distractor_uid and len(distractor["cited_unit_ids"]) > 1:
        distractor_uid = distractor["cited_unit_ids"][1]
    elif correct_uid == distractor_uid:
        return None
    correct_fact = _clean_prose(unit_map.get(correct_uid, {}).get("knowledge_zh", ""))
    distractor_fact = _clean_prose(unit_map.get(distractor_uid, {}).get("knowledge_zh", ""))
    correct_fact = correct_fact.rstrip("。！？；; ")
    distractor_fact = distractor_fact.rstrip("。！？；; ")
    if not correct_fact or not distractor_fact:
        return None
    text = (
        f'易将选项{distractor["option"]}与选项{correct["option"]}混淆。'
        f'教材对选项{distractor["option"]}的相关要点是"{distractor_fact}"；'
        f'对选项{correct["option"]}的相关要点是"{correct_fact}"。'
        "判断时应逐项核对题干条件，不要扩大教材中的程度或范围。"
    )
    cited = list(dict.fromkeys([distractor_uid, correct_uid]))
    return {"text": text, "cited_unit_ids": cited}


def _exact_quote(value: Any, source: str) -> str:
    quote = str(value or "").strip()
    return quote if quote and quote in source else ""


def _exact_quotes(values: Any, source: str) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for value in values:
        quote = _exact_quote(value, source)
        if quote and quote not in out:
            out.append(quote)
    return out[:3]


def _legacy_source_claims(
    cited_unit_ids: list[str], unit_map: dict[str, dict[str, Any]]
) -> list[dict[str, str]]:
    claims: list[dict[str, str]] = []
    for uid in cited_unit_ids[:3]:
        unit = unit_map.get(uid, {})
        excerpt = str(unit.get("knowledge_zh", "") or "").strip()
        if not excerpt:
            excerpt = str(unit.get("en_quote") or unit.get("knowledge_en", "") or "").strip()
        if excerpt:
            claims.append({"unit_id": uid, "exact_excerpt": excerpt})
    return claims


def _quoted_text(values: list[str]) -> str:
    return "、".join(f"{value}" for value in values if value)


def _render_structured_option_analysis(
    *, expected_judgement: str, basis_type: str, evidence_status: str,
    source_claims: list[dict[str, str]], stem_quotes: list[str], option_quotes: list[str],
) -> str:
    stem_text = _quoted_text(stem_quotes)
    option_text = _quoted_text(option_quotes)
    if expected_judgement == "correct":
        return "符合上述定义。"
    if basis_type in {"textbook_direct", "textbook_definition_application"}:
        source_text = _quoted_text([claim["exact_excerpt"] for claim in source_claims])
        if evidence_status == "negative":
            return f"教材指出{source_text}，而{option_text or '该选项'}与此不符。"
        return f"教材指出{source_text}。题干中{stem_text or '的条件'}与{option_text or '该选项'}不一致。"
    if basis_type == "stem_contrast":
        return f"{option_text or '该选项'}与题干给出的{stem_text or '事实'}不一致。"
    return INSUFFICIENT_TEXT


def _stem_contrast_text(option_quote: str, stem_quotes: list[str]) -> str:
    stem_text = "".join(stem_quotes)
    return (
        f'选项涉及"{option_quote}"，而题干明确描述的是"{stem_text}"；'
        "两者的关键要素不一致，因此该项不符合题干场景。"
    )


def _candidate_mentions_quote(option_quote: str, unit_map: dict[str, dict[str, Any]]) -> bool:
    needle = re.sub(r"\W+", "", option_quote, flags=re.UNICODE).casefold()
    if len(needle) < 2:
        return False
    for unit in unit_map.values():
        haystack = " ".join(str(unit.get(field, "") or "")
                            for field in ("knowledge_zh", "knowledge_en", "en_quote"))
        normalized = re.sub(r"\W+", "", haystack, flags=re.UNICODE).casefold()
        if needle in normalized:
            return True
    return False


def _build_source_evidence(
    unit_map: dict[str, dict[str, Any]], exam_point: dict[str, Any],
    core_analysis: dict[str, Any], option_explanations: list[dict[str, Any]],
    easy_mistake: dict[str, Any],
) -> list[dict[str, Any]]:
    usage: dict[str, list[str]] = {}

    def add(values: list[str], location: str) -> None:
        for uid in values:
            bucket = usage.setdefault(uid, [])
            if location not in bucket:
                bucket.append(location)

    add(core_analysis["cited_unit_ids"], "核心解析")
    for row in option_explanations:
        add(row["cited_unit_ids"], f"选项{row['option']}")
    add(easy_mistake["cited_unit_ids"], "易错提醒")

    rows: list[dict[str, Any]] = []
    for uid, used_by in usage.items():
        unit = unit_map[uid]
        heading = unit.get("heading_context", []) or []
        if not isinstance(heading, list):
            heading = [str(heading)] if heading else []
        page_info = _get_unit_page_map().get(uid, {})
        rows.append({
            "unit_id": uid,
            "used_by": used_by,
            "knowledge_zh": str(unit.get("knowledge_zh", "") or ""),
            "en_quote": str(unit.get("en_quote") or unit.get("knowledge_en", "") or ""),
            "heading_context": [str(x) for x in heading if str(x).strip()],
            "content_type": str(unit.get("type", "") or ""),
            "pdf_page": page_info.get("pdf_page"),
            "printed_page": page_info.get("printed_page", ""),
        })
    return rows


def _normalize_source_quote(
    raw_core: Any, core_analysis: dict[str, Any], unit_map: dict[str, dict[str, Any]],
) -> tuple[dict[str, str], list[str]]:
    raw_core = raw_core if isinstance(raw_core, dict) else {}
    raw_quote = raw_core.get("source_quote", {})
    raw_quote = raw_quote if isinstance(raw_quote, dict) else {}
    uid = str(raw_quote.get("unit_id", "") or "").strip()
    excerpt = str(raw_quote.get("exact_excerpt", "") or "").strip()
    issues: list[str] = []
    if not uid and not excerpt:
        return {}, []
    if not uid or not excerpt:
        return {}, ["核心解析教材英文短引不完整（缺unit_id或缺excerpt）"]
    if uid not in core_analysis.get("cited_unit_ids", []):
        issues.append("教材英文短引unit未被核心解析引用")
    unit = unit_map.get(uid)
    if not unit:
        issues.append("教材英文短引unit不在本题证据池")
        source = ""
    else:
        source = str(unit.get("en_quote") or unit.get("knowledge_en", "") or "")
    if excerpt and excerpt not in source:
        issues.append("教材英文短引不是对应英文原文的连续子串")
    if not SOURCE_QUOTE_MIN_LENGTH <= len(excerpt) <= SOURCE_QUOTE_MAX_LENGTH:
        issues.append(f"教材英文短引长度不在{SOURCE_QUOTE_MIN_LENGTH}-{SOURCE_QUOTE_MAX_LENGTH}字符范围")
    if issues:
        return {}, issues
    return {"unit_id": uid, "exact_excerpt": excerpt}, []


def _reference_answer_conflicts(predicted: list[str], reference: dict[str, Any]) -> list[str]:
    predicted_set = set(predicted)
    conflicts: list[str] = []
    for field, label in (
        ("final_answer", "题库最终参考答案"),
        ("cn_answer", "中文参考答案"),
        ("en_answer", "英文参考答案"),
    ):
        values = [str(x).strip().upper() for x in reference.get(field, []) or []]
        if values and set(values) != predicted_set:
            conflicts.append(f"AI答案与{label}冲突")
    return conflicts


def _build_software_readiness(
    result: dict[str, Any], predicted: list[str], options: dict[str, Any],
    option_explanations: list[dict[str, Any]], reference: dict[str, Any],
    quote_issues: list[str], grounding_issues: list[str], normalization_warnings: list[str],
) -> dict[str, Any]:
    blockers: list[str] = []

    def add(message: str) -> None:
        if message and message not in blockers:
            blockers.append(message)

    if result.get("pipeline_status") != "ok":
        add(f"盲判状态不是ok: {result.get('pipeline_status', '')}")
    for issue in result.get("validation_checks", []) or []:
        add(f"盲判机械校验失败: {issue}")
    if result.get("citation_filter_drops"):
        add("盲判存在被过滤的非法引用")
    if not predicted:
        add("AI答案为空")
    for row in option_explanations:
        if row.get("basis_type") == "insufficient":
            add(f"选项{row.get('option', '')}证据不足")
    for issue in quote_issues:
        add(issue)
    for issue in grounding_issues:
        add(issue)
    for issue in _reference_answer_conflicts(predicted, reference):
        add(issue)

    risk_flags = [str(flag) for flag in reference.get("risk_flags", []) or [] if str(flag).strip()]
    if normalization_warnings:
        risk_flags.append("normalization_recovered")
    return {
        "ready": not blockers,
        "blocking_reasons": blockers,
        "risk_flags": list(dict.fromkeys(risk_flags)),
    }


def normalize_explanation(
    parsed: dict[str, Any] | None, result: dict[str, Any],
    reference: dict[str, Any], model: str,
) -> dict[str, Any]:
    parsed = parsed if isinstance(parsed, dict) else {}
    deferral = parsed.get("deferral") if isinstance(parsed.get("deferral"), dict) else None
    if deferral and deferral.get("reason"):
        answer = [str(x).strip().upper() for x in parsed.get("answer", []) or []
                  if str(x).strip().upper() in (result.get("options", {}) or {})]
        if not answer:
            answer = [str(x).strip().upper() for x in result.get("predicted_answer", []) or []
                      if str(x).strip().upper() in (result.get("options", {}) or {})]
        return {
            "deferral": deferral, "answer": answer,
            "exam_point": {"text": ""}, "core_analysis": {"text": "", "cited_unit_ids": []},
            "option_explanations": [], "easy_mistake": {"text": ""},
            "primary_unit_id": "",
            "source_evidence": [],
            "software_readiness": {"ready": False, "blocking_reasons": ["LLM 拒答"], "risk_flags": ["llm_deferred"]},
        }
    options = result.get("options", {}) or {}
    predicted = [str(x).strip().upper() for x in result.get("predicted_answer", []) or []
                 if str(x).strip().upper() in options]
    unit_map = candidate_by_unit(result)
    sources = {row["option"]: row for row in enriched_option_material(result)}
    framework = result.get("decision_framework", {}) or {}
    framework_ids = {str(uid) for uid in framework.get("cited_unit_ids", []) or []
                     if str(uid) in unit_map}
    provided_evidence_ids = {card["unit_id"] for source in sources.values()
                             for key in ("evidence_cards", "supplement_cards")
                             for card in source.get(key, []) or []}
    provided_evidence_ids.update(framework_ids)
    raw_rows = parsed.get("option_explanations", [])
    raw_rows = raw_rows if isinstance(raw_rows, list) else []
    raw_by_label = {str(row.get("option", "")).strip().upper(): row
                    for row in raw_rows if isinstance(row, dict)}

    option_explanations: list[dict[str, Any]] = []
    grounding_issues: list[str] = []
    normalization_warnings: list[str] = []
    for label in options:
        label = str(label).strip().upper()
        source = sources.get(label, {})
        raw = raw_by_label.get(label, {})
        expected_judgement = "correct" if label in predicted else "incorrect"
        if expected_judgement == "correct":
            continue
        blind_db = source.get("decision_basis", "")
        evidence_status = source.get("evidence_status", "")
        basis_type = _DECISION_TO_BASIS.get(blind_db)
        if basis_type is None:
            if evidence_status in {"direct", "indirect", "negative"}:
                basis_type = "textbook_direct"
            else:
                basis_type = "insufficient"

        raw_option_quotes = raw.get("option_quotes")
        legacy_stem_schema = not isinstance(raw_option_quotes, list)
        if not isinstance(raw_option_quotes, list):
            legacy_option_quote = str(raw.get("option_quote", "") or "").strip()
            raw_option_quotes = [legacy_option_quote] if legacy_option_quote else []
        option_quotes = _exact_quotes(raw_option_quotes, str(options[label]))
        stem_quotes = _exact_quotes(raw.get("stem_quotes"), str(result.get("stem", "")))

        evidence_status = source.get("evidence_status", "")
        source_claims: list[dict[str, str]] = []
        if basis_type in {"textbook_direct", "textbook_definition_application"}:
            claim_uids: list[str] = []
            for card in source.get("evidence_cards", []) or []:
                uid = str(card.get("unit_id", "") or "").strip()
                if uid and uid in unit_map and uid not in claim_uids:
                    claim_uids.append(uid)
            if basis_type == "textbook_definition_application":
                for uid in framework_ids:
                    if uid and uid in unit_map and uid not in claim_uids:
                        claim_uids.append(uid)
            source_claims = _legacy_source_claims(claim_uids, unit_map)
            if not option_quotes:
                option_quotes = [str(options[label])]

        if not option_quotes:
            option_quotes = [str(options[label])]
        if not stem_quotes and basis_type in (STEM_BASIS_TYPES | {"textbook_definition_application"}):
            stem_quotes = [str(result.get("stem", ""))]

        valid_basis = True
        if basis_type in {"textbook_direct", "textbook_definition_application"}:
            if not source_claims or not option_quotes:
                valid_basis = False
                grounding_issues.append(f"选项{label}教材依据缺少逐字source_claims或option_quotes")
            if basis_type == "textbook_definition_application" and not stem_quotes:
                valid_basis = False
                grounding_issues.append(f"选项{label}定义应用缺少逐字stem_quotes")
        elif basis_type in STEM_BASIS_TYPES:
            if not stem_quotes or not option_quotes:
                valid_basis = False
                grounding_issues.append(f"选项{label}{basis_type}缺少逐字题干或选项片段")
            if basis_type == "stem_contrast" and expected_judgement == "correct":
                valid_basis = False
                grounding_issues.append(f"选项{label}正确项不能使用stem_contrast")
            if (basis_type == "stem_contrast" and legacy_stem_schema and option_quotes
                    and _candidate_mentions_quote(option_quotes[0], unit_map)):
                valid_basis = False
                grounding_issues.append(f"选项{label}旧版stem_contrast被候选教材覆盖")
        else:
            valid_basis = False

        if valid_basis:
            cited = list(dict.fromkeys(claim["unit_id"] for claim in source_claims))[:3]
            raw_analysis = str(raw.get("analysis", "") or "").strip()
            if len(raw_analysis) >= 6:
                analysis = _clean_prose(raw_analysis)
            else:
                analysis = _render_structured_option_analysis(
                    expected_judgement=expected_judgement, basis_type=basis_type,
                    evidence_status=evidence_status, source_claims=source_claims,
                    stem_quotes=stem_quotes, option_quotes=option_quotes)
        else:
            basis_type = "insufficient"
            raw_analysis = str(raw.get("analysis", "") or "").strip()
            if len(raw_analysis) >= 6:
                analysis = _clean_prose(raw_analysis)
            else:
                continue
            cited = []
            source_claims = []
            option_quotes = []
            stem_quotes = []

        if expected_judgement == "correct":
            error_type = "正确"
        elif basis_type == "insufficient":
            error_type = "证据不足"
        else:
            llm_error = str(raw.get("error_type", "") or "").strip()
            valid_errors = {"概念混淆", "主体或阶段错配", "范围或程度偏差", "题干要素不匹配", "证据不足"}
            error_type = llm_error if llm_error in valid_errors else ""
        option_explanations.append({
            "option": label, "judgement": expected_judgement, "error_type": error_type,
            "basis_type": basis_type, "evidence_status": evidence_status, "analysis": analysis,
            "cited_unit_ids": cited, "source_claims": source_claims,
            "option_quotes": option_quotes, "option_quote": option_quotes[0] if option_quotes else "",
            "stem_quotes": stem_quotes,
        })

    correct_rows = [row for row in option_explanations if row.get("judgement") == "correct"]
    correct_sources_list = [sources[row["option"]] for row in option_explanations
                            if row.get("judgement") == "correct" and row["option"] in sources]
    stem_only_answer = bool(correct_sources_list) and all(
        src.get("decision_basis") == "insufficient" for src in correct_sources_list)
    raw_core = parsed.get("core_analysis")

    if stem_only_answer:
        decisive_stem_quotes = list(dict.fromkeys(
            quote for row in correct_rows for quote in row.get("stem_quotes", []) or []))[:3]
        core_text = " ".join(str(row.get("analysis", "")).strip() for row in correct_rows).strip()
        exam_point = {"text": "本题考查依据题干明确事实进行直接判断。"}
        core_analysis = {"text": core_text or INSUFFICIENT_TEXT, "cited_unit_ids": [], "source_quote": {}}
        easy_mistake = {"text": (f"判断时只使用题干明确给出的{_quoted_text(decisive_stem_quotes)}，"
                                 "不要补入题干未提供的外部定义或通常做法。"), "cited_unit_ids": []}
        quote_issues: list[str] = []
    else:
        raw_ep = parsed.get("exam_point") if isinstance(parsed.get("exam_point"), dict) else {}
        raw_ep_text = str(raw_ep.get("text", "") or "").strip()
        if len(raw_ep_text) >= 6:
            exam_point = {"text": _clean_prose(raw_ep_text)}
        else:
            fallback_exam = _fallback_exam_point(option_explanations, framework)
            if fallback_exam and len(fallback_exam.get("text", "")) >= 6:
                exam_point = fallback_exam
            else:
                exam_point = {"text": INSUFFICIENT_TEXT}
        core_analysis, core_issues = _normalize_grounded_block(raw_core, provided_evidence_ids, unit_map, "核心解析")
        if core_issues:
            fallback_core = _fallback_core_analysis(option_explanations)
            if fallback_core:
                core_analysis.update(fallback_core)
                normalization_warnings.extend(core_issues)
            else:
                grounding_issues.extend(core_issues)
        context_issues = _core_context_issues(core_analysis.get("text", ""))
        if context_issues:
            fallback_core = _fallback_core_analysis(option_explanations)
            if fallback_core:
                core_analysis.update(fallback_core)
                normalization_warnings.extend(context_issues)
            else:
                core_analysis = {"text": INSUFFICIENT_TEXT, "cited_unit_ids": []}
                grounding_issues.extend(context_issues)
        source_quote, quote_issues = _normalize_source_quote(raw_core, core_analysis, unit_map)
        core_analysis["source_quote"] = source_quote
        raw_easy = parsed.get("easy_mistake") if isinstance(parsed.get("easy_mistake"), dict) else {}
        raw_easy_text = str(raw_easy.get("text", "") or "").strip()
        if len(raw_easy_text) >= 20:
            easy_mistake = {"text": _clean_prose(raw_easy_text),
                            "cited_unit_ids": _valid_citations(raw_easy.get("cited_unit_ids", []), provided_evidence_ids)[:3]}
        else:
            easy_mistake = {"text": "", "cited_unit_ids": []}

    source_evidence = _build_source_evidence(unit_map, exam_point, core_analysis, option_explanations, easy_mistake)
    software_readiness = _build_software_readiness(result, predicted, options, option_explanations, reference, quote_issues, grounding_issues, normalization_warnings)
    review_flags: list[str] = []
    predicted_set = set(predicted)
    final_set = set(reference.get("final_answer", []) or [])
    if predicted_set and final_set and predicted_set != final_set:
        review_flags.append(f"答案冲突：解析{predicted_set} vs 题库{final_set}")
    if any(row.get("basis_type") == "insufficient" for row in option_explanations):
        insuff_labels = [row["option"] for row in option_explanations if row.get("basis_type") == "insufficient"]
        review_flags.append(f"部分选项证据不足：{', '.join(insuff_labels)}")
    if result.get("validation_checks"):
        review_flags.append("盲判校验未通过")
    if result.get("pipeline_status") != "ok":
        review_flags.append(f"盲判状态异常：{result.get('pipeline_status', '')}")

    return {
        "schema_version": SCHEMA_VERSION, "answer": predicted,
        "primary_unit_id": str(parsed.get("primary_unit_id", "") or "").strip(),
        "exam_point": exam_point, "core_analysis": core_analysis,
        "option_explanations": option_explanations, "easy_mistake": easy_mistake,
        "source_evidence": source_evidence, "software_readiness": software_readiness,
        "normalization_issues": grounding_issues, "normalization_warnings": normalization_warnings,
        "review_flags": review_flags, "chapter_mappings": result.get("chapter_mappings", []),
        "reference_appendix": reference,
        "generation_metadata": {"prompt_version": PROMPT_VERSION, "model": model,
                                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")},
    }