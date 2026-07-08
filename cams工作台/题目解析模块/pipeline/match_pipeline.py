"""单题匹配流水线：题目 → 全书句卡证据召回 → 题目级 matched_card_ids。

借用新题解析模块的 agentic 检索能力（planner + retrieve_for_option + flatten），
但**跳过盲判答案、解析生成、考点提炼**等 LLM 重环节，只产出证据匹配池。

定位：给后续「考点/高频考点生成」提供题目-句卡匹配池，不是给老师看解析草稿。
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

# 把四角色法目录加入 sys.path，复用 agentic / blind 检索模块
_FOUR_ROLE_DIR = (
    Path(__file__).resolve().parents[3] / "题目与kg关系建立流水线（四角色法）"
)
if str(_FOUR_ROLE_DIR) not in sys.path:
    sys.path.insert(0, str(_FOUR_ROLE_DIR))

import run_agentic_search_experiment as agentic  # noqa: E402
import run_blind_q212_experiment as blind  # noqa: E402
import run_step1  # noqa: E402

from pipeline.evidence_pool import get_match_runtime  # noqa: E402
from pipeline.question_loader import Question  # noqa: E402


def _parse_llm_json(raw_text: str) -> dict[str, Any]:
    """容忍 ```json 包裹与尾随噪声的 JSON 解析。"""
    if not raw_text:
        return {}
    import re
    candidates: list[str] = []
    for m in re.finditer(r"```(?:json|JSON)?\s*([\s\S]*?)```", raw_text):
        candidates.append(m.group(1).strip())
    stripped = run_step1.strip_json_fence(raw_text).strip()
    if stripped:
        candidates.append(stripped)
    m = re.search(r"\{[\s\S]*\}", raw_text)
    if m:
        candidates.append(m.group(0))
    for cand in candidates:
        try:
            parsed = json.loads(cand)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            parsed = agentic.parse_json_object(cand)
            if isinstance(parsed, dict):
                return parsed
    return {}


def _build_simple_plan(stem: str, options: dict[str, str]) -> dict[str, Any]:
    """无 LLM 的兜底 plan：用 stem+option 作为检索 query。"""
    option_plans: dict[str, dict[str, Any]] = {}
    for label, option_text in options.items():
        terms = agentic.extract_phrases(stem, option_text)
        option_plans[label] = {
            "search_queries": [f"{stem} {option_text}", option_text],
            "must_terms": terms[:6],
            "evidence_need": f"判断选项{label}是否符合题干",
            "option_claim": option_text,
            "related_terms": [],
            "contrast_terms": [],
            "avoid_confusions": [],
        }
    return {
        "stem": stem,
        "options": options,
        "option_plans": option_plans,
    }


def _call_planner(client: Any, stem: str, options: dict[str, str]) -> tuple[str, dict[str, Any]]:
    """调用 LLM planner 生成检索规划。返回 (raw_output, normalized_plan)。"""
    prompt = blind.build_blind_planner_prompt(stem, options)
    raw = run_step1.call_llm(client, prompt, max_tokens=5000)
    parsed = _parse_llm_json(raw)
    plan = blind.normalize_blind_plan(parsed, stem, options)
    return raw, plan


def build_known_answer_adjudicator_prompt(
    stem: str,
    options: dict[str, str],
    answer: str,
    plan: dict[str, Any],
    candidates_by_option: dict[str, list[dict[str, Any]]],
) -> str:
    """已知答案版 adjudicator prompt：基于标准答案生成选项级解析。

    与 blind 版区别：
    - 已知标准答案，judgement 直接由答案决定，不需盲判
    - 重点产 explanation（选项解析）和 common_trap（易错点）
    - evidence_cards 严格限定在候选句卡内
    """
    opt_text = "\n".join(f"{label}. {text}" for label, text in options.items())
    plan_summary = []
    # 兼容两种 plan 格式：
    # - blind 版：plan["options"] = [{"option":"A", "option_claim":..., ...}, ...]
    # - 简单版：plan["option_plans"] = {"A": {"option_claim":..., ...}, ...}
    raw_options = plan.get("options") or plan.get("option_plans") or []
    if isinstance(raw_options, list):
        # blind 版：list of dicts
        for item in raw_options:
            if isinstance(item, dict):
                plan_summary.append(
                    f"{item.get('option', '?')}: claim={item.get('option_claim')} | need={item.get('evidence_need')} | terms={','.join(item.get('must_terms', [])[:8])}"
                )
    elif isinstance(raw_options, dict):
        # 简单版：dict[label, plan_dict]
        for label, option_plan in raw_options.items():
            if isinstance(option_plan, dict):
                plan_summary.append(
                    f"{label}: claim={option_plan.get('option_claim')} | need={option_plan.get('evidence_need')} | terms={','.join(option_plan.get('must_terms', [])[:8])}"
                )
            else:
                plan_summary.append(f"{label}: claim={option_plan}")
    candidate_text = "\n\n".join(
        agentic.format_candidate_block(label, candidates)
        for label, candidates in candidates_by_option.items()
    )
    candidate_text = candidate_text[: agentic.MAX_CANDIDATE_TEXT_CHARS]
    answer_labels = ",".join(sorted(answer.split(","))) if answer else "未知"

    return f"""你是CAMS选项级解析员。题目已有标准答案，请基于标准答案和教材句卡，为每个选项生成解析。

已知信息：
- 标准答案：{answer_labels}
- 题目：{stem}
- 选项：
{opt_text}

检索规划摘要：
{chr(10).join(plan_summary)}

候选教材句卡：
{candidate_text}

要求：
1. judgement 由标准答案决定：答案中的选项填 correct，其余填 incorrect。
2. evidence_cards 只能引用上方候选教材句卡中出现过的 card_id；找不到直接证据则留空数组。
3. explanation 要写清"该选项为什么对/错"，优先引用教材句卡原文佐证；证据不足时明说。
4. common_trap 写学生容易误解之处，无法推断则填空字符串。
5. evidence_status：direct=句卡直接支撑，indirect=句卡间接相关，none=无证据。

输出严格JSON，不要Markdown，不要代码块：
{{
  "option_analysis": [
    {{
      "option": "A",
      "option_text": "选项全文",
      "judgement": "correct/incorrect",
      "judgement_confidence": "high/medium/low",
      "evidence_status": "direct/indirect/none",
      "evidence_cards": [
        {{
          "card_id": "v6s_NXXXXX",
          "support_type": "direct/indirect/context/negative",
          "source": "card_bge/bm25/exact_phrase/adjacent_card/relation_expand",
          "quote": "教材原文短摘，不超过120字",
          "reason": "为什么这张句卡能支撑或反驳该选项",
          "relevance": "high/medium/low"
        }}
      ],
      "explanation": "该选项为什么对/错，结合教材句卡说明",
      "common_trap": "学生易错点，无法推断则填空"
    }}
  ],
  "overall_notes": "整体证据质量说明",
  "cited_cards": ["v6s_NXXXXX"]
}}

必须逐一分析所有 {len(options)} 个选项。"""


def match_one_question(
    question: Question,
    rt=None,
    top_k: int = 30,
    use_planner: bool = True,
    generate_analysis: bool = False,
    match_only: bool = False,
) -> dict[str, Any]:
    """对单道题跑证据检索，返回题目级 matched_card_ids + 选项级证据。

    Parameters
    ----------
    question : Question
    rt : AgenticRuntime | None
        预加载的 runtime；None 则调用 ``get_match_runtime()``。
    top_k : int
        每个选项最多召回的候选句卡数。
    use_planner : bool
        True=调 LLM planner 生成检索规划（质量高、慢）；
        False=用简单 plan（stem+option 作 query，快、无 LLM）。
    generate_analysis : bool
        True=在检索后追加一次 LLM 调用，基于已知答案生成选项级解析
        （option_analysis：judgement/explanation/common_trap/evidence_cards）。
        需要题目有 answer 字段；无 answer 则跳过。
    match_only : bool
        True=三段式拼装模式，只跑 planner+检索（1次LLM），不调 adjudicator。
        option_analysis 用检索候选 + 教研解析填充，common_trap 留空待后续补。
        与 generate_analysis 互斥；match_only=True 时 generate_analysis 被忽略。

    Returns
    -------
    dict
        {
          "question_id": "3.1_1",
          "section": "3.1",
          "knowledge_point": "...",
          "matched_card_ids": ["v6s_N...", ...],   # 题目级，去重
          "evidence_count": N,
          "option_evidence": {...},                 # 选项级检索候选
          "option_analysis": [...],                 # generate_analysis 或 match_only 时有
          "overall_notes": "...",
          "planner_used": bool,
          "status": "ok" | "parse_failed" | "retrieval_failed" | "analysis_failed",
          "elapsed_ms": ...,
        }
    """
    started = time.perf_counter()
    if rt is None:
        rt = get_match_runtime()

    stem = question.stem
    options = question.options
    result: dict[str, Any] = {
        "question_id": question.id,
        "section": question.section,
        "knowledge_point": question.knowledge_point,
        "matched_card_ids": [],
        "evidence_count": 0,
        "option_evidence": {},
        "option_analysis": [],
        "overall_notes": "",
        "planner_used": use_planner,
        "analysis_generated": False,
        "status": "ok",
    }

    if not stem or len(options) < 2:
        result["status"] = "parse_failed"
        result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
        return result

    client = rt.base.client

    # ---- Step 1: 检索规划 ----
    try:
        if use_planner:
            raw_plan, search_plan = _call_planner(client, stem, options)
        else:
            raw_plan, search_plan = "", _build_simple_plan(stem, options)
    except Exception as exc:
        # planner 失败 → 降级到简单 plan
        raw_plan, search_plan = "", _build_simple_plan(stem, options)
        result["planner_fallback"] = str(exc)

    plans = agentic.option_plan_by_label(search_plan)

    # ---- Step 2: 选项级证据召回 ----
    candidates_by_option: dict[str, list[dict[str, Any]]] = {}
    try:
        for label, option_text in options.items():
            option_plan = plans.get(label, {})
            if not option_plan.get("search_queries"):
                option_plan = {
                    "search_queries": [f"{stem} {option_text}", option_text],
                    "must_terms": agentic.extract_phrases(stem, option_text)[:6],
                    "evidence_need": f"判断选项{label}是否符合题干",
                    "option_claim": option_text,
                    "related_terms": [],
                    "contrast_terms": [],
                    "avoid_confusions": [],
                }
            candidates, _diagnostics = agentic.retrieve_for_option(
                rt, stem, option_text, option_plan, top_k=top_k
            )
            candidates_by_option[label] = candidates
    except Exception as exc:
        result["status"] = "retrieval_failed"
        result["error"] = str(exc)
        result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
        return result

    # ---- Step 2.5: 解析生成 ----
    option_analysis: list[dict[str, Any]] = []
    overall_notes = ""

    if match_only:
        # 三段式拼装模式：检索候选 + 教研解析，不调 adjudicator
        # common_trap 留空，后续单独补
        answer_set = {x.strip() for x in (question.answer or "").split(",") if x.strip()}
        for label, text in options.items():
            cands = candidates_by_option.get(label, [])
            ev_cards = [
                {
                    "card_id": c.get("card_id", ""),
                    "support_type": c.get("support_type", "context"),
                    "source": c.get("source", c.get("retriever", "")),
                    "quote": (c.get("citation") or c.get("text") or "")[:200],
                    "reason": "",
                    "relevance": c.get("relevance", "medium"),
                }
                for c in cands[:5]
            ]
            ev_status = "direct" if ev_cards else "none"
            option_analysis.append({
                "option": label,
                "option_text": text,
                "judgement": "correct" if label in answer_set else "incorrect",
                "judgement_confidence": "high",
                "evidence_status": ev_status,
                "evidence_cards": ev_cards,
                "explanation": question.explanation,  # 教研解析
                "common_trap": "",  # 待后续补
            })
        result["analysis_generated"] = True
    elif generate_analysis and question.answer:
        try:
            adjudicator_prompt = build_known_answer_adjudicator_prompt(
                stem, options, question.answer, search_plan, candidates_by_option
            )
            raw_adj = run_step1.call_llm(client, adjudicator_prompt, max_tokens=9000)
            parsed_adj = _parse_llm_json(raw_adj)
            # 调试：如果解析失败，把 raw 存到 result 方便排查
            if not isinstance(parsed_adj, dict) or not parsed_adj.get("option_analysis"):
                result["_debug_raw_adjudicator"] = raw_adj[:2000]
            if not isinstance(parsed_adj, dict):
                parsed_adj = {}
            option_analysis = parsed_adj.get("option_analysis", []) or []
            if not isinstance(option_analysis, list):
                option_analysis = []
            overall_notes = parsed_adj.get("overall_notes", "") or ""
            # 规整：确保每个选项都有 entry，judgement 与标准答案一致
            answer_set = {x.strip() for x in question.answer.split(",") if x.strip()}
            opt_by_label: dict[str, dict[str, Any]] = {}
            for r in option_analysis:
                if isinstance(r, dict):
                    label = str(r.get("option", "")).strip()
                    if label:
                        opt_by_label[label] = r
            normalized = []
            for label, text in options.items():
                row = dict(opt_by_label.get(label, {"option": label}))
                row["option"] = label
                row["option_text"] = text
                row["judgement"] = "correct" if label in answer_set else "incorrect"
                row.setdefault("evidence_cards", [])
                row.setdefault("explanation", "")
                row.setdefault("common_trap", "")
                row.setdefault("evidence_status", "none")
                normalized.append(row)
            option_analysis = normalized
            result["analysis_generated"] = True
        except Exception as exc:
            # adjudicator 失败不影响匹配池，只标记
            result["status"] = "analysis_failed"
            result["analysis_error"] = str(exc)

    # ---- Step 3: 聚合 ----
    evidence = agentic.flatten_evidence(candidates_by_option)
    # 题目级：所有选项召回的句卡去重
    seen: set[str] = set()
    matched_card_ids: list[str] = []
    for card in evidence:
        cid = card.get("card_id", "")
        if cid and cid not in seen:
            seen.add(cid)
            matched_card_ids.append(cid)

    # 选项级：若已产出 evidence_cards（match_only 或 adjudicator），优先用它的；
    # 否则用检索候选的前 N 张
    option_evidence: dict[str, list[dict[str, Any]]] = {}
    if option_analysis:
        for row in option_analysis:
            label = row.get("option", "")
            cards = row.get("evidence_cards", []) or []
            option_evidence[label] = [
                {
                    "card_id": c.get("card_id", ""),
                    "support_type": c.get("support_type", ""),
                    "source": c.get("source", ""),
                    "quote": (c.get("quote", "") or "")[:200],
                    "reason": c.get("reason", ""),
                    "relevance": c.get("relevance", ""),
                }
                for c in cards[:10]
            ]
    else:
        for label, candidates in candidates_by_option.items():
            option_evidence[label] = [
                {
                    "card_id": c.get("card_id", ""),
                    "score": c.get("score", 0),
                    "quote": (c.get("citation") or c.get("text") or "")[:200],
                }
                for c in candidates[:10]
            ]

    result["matched_card_ids"] = matched_card_ids
    result["evidence_count"] = len(matched_card_ids)
    result["option_evidence"] = option_evidence
    result["option_analysis"] = option_analysis
    result["overall_notes"] = overall_notes
    result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
    return result


def build_refine_prompt(
    question: Question,
    candidate_cards: list[dict[str, Any]],
) -> str:
    """构造 LLM 二次筛选 prompt：从候选句卡中挑出真正相关的 5-15 张。"""
    opt_text = "\n".join(f"{label}. {text}" for label, text in question.options.items())
    answer_labels = question.answer or "未知"
    explanation = (question.explanation or "")[:800]

    card_lines = []
    for i, c in enumerate(candidate_cards, 1):
        cid = c.get("card_id", "")
        text = c.get("text") or c.get("citation") or ""
        card_lines.append(f"[{i}] {cid}: {text}")

    return f"""你是CAMS教材句卡筛选员。题目已匹配到{len(candidate_cards)}张候选句卡，其中含检索噪声。请剔除纯噪声，保留所有可作为证据的句卡。

题目：{question.stem}
选项：
{opt_text}
标准答案：{answer_labels}

教研解析（参考，不要照抄）：
{explanation or '（无）'}

候选句卡（{len(candidate_cards)}张，全部已展示，无截断）：
{chr(10).join(card_lines)}

筛选原则（优先级：召回证据 > 剔除噪声，保留上限35张）：
1. **必留**：直接证据——句卡能直接支撑正确答案、或直接反驳错误选项。判定标准：句卡与选项在主体、行为、场景、判断性质上有实质重合，不只是关键词命中。
2. **可留**：间接相关——句卡提供背景、定义、阶段划分等上下文，帮助理解题目，但本身不足以单独推出选项对错。
3. **必删**：纯噪声——仅因关键词命中但语义无关，或主题完全不同。
4. **必删**：考点偏离——句卡虽主题相关，但题目问的是具体考点（如"社会和经济影响"），句卡讲的是同主题的其他方面（如"洗钱机制/合规要求"），属于偏题，按噪声处理。

关于错误选项的排除依据：
- 句卡能**直接说明或经一步推理说明**该错误选项为何不成立的，算直接证据。
  例1（直接说明）：句卡指出"制裁名单由联合国安理会制定"→ 排除"FATF制定制裁名单"。
  例2（一步推理）：句卡指出"风险为本方法核心是评估客户/地域/产品风险并据此分配资源"→ 一步推出"一刀切停止交易"违反风险为本 → 排除该错误选项。
- 仅提到错误选项中某个关键词（如"欺诈""制裁""PEP"），但**无法推出**该选项为何错的句卡，不算排除依据，按噪声或偏题处理。
  反例：句卡只是PEP定义（"PEP指被赋予重要公共职能的人物"），推不出"FSRB不维护全球PEP数据库"——不算排除依据。

保留数量：所有直接证据 + 间接相关，合计上限35张。超出时优先保留直接证据，间接相关按与考点的接近度排序保留。

严禁误删：
- 不要因为句卡"看起来泛"就删，教材原文的定义、原则、分类往往就是证据。
- 不要因为句卡没出现选项原话就删，反洗钱教材常用同义表述。
- 宁可多留一张间接相关，也不要漏掉一张直接证据。

card_id 必须从上方候选列表中逐字选取，不得臆造。

输出严格JSON，不要Markdown，不要代码块：
{{
  "refined_card_ids": ["v6s_NXXXXX", "v6s_NYYYYY"],
  "direct_evidence_ids": ["v6s_NXXXXX"],
  "indirect_related_ids": ["v6s_NYYYYY"],
  "dropped_noise_count": 0,
  "reason": "简述：保留了多少直接证据、多少间接相关、剔除了多少噪声"
}}"""


def refine_match_with_llm(
    question: Question,
    candidate_card_ids: list[str],
    rt=None,
    max_candidates: int = 0,
) -> dict[str, Any]:
    """LLM 二次筛选：从候选句卡池中挑出真正相关的 5-15 张。

    用 ds pro 关思考，每题 1 次 LLM 调用。失败则保留原候选。

    Parameters
    ----------
    question : Question
    candidate_card_ids : list[str]
        现有 matched_card_ids（约 80 张候选）。
    rt : AgenticRuntime | None
    max_candidates : int
        候选超过此数时只取前 N 张。0 表示不截断，全部送进 prompt。
        默认不截断——之前截断会漏掉排序靠后的直接证据。

    Returns
    -------
    dict
        含 refined_card_ids / reason / raw_candidate_count / refined_count / status / elapsed_ms。
    """
    started = time.perf_counter()
    if rt is None:
        rt = get_match_runtime()

    if not candidate_card_ids:
        return {
            "refined_card_ids": [],
            "reason": "无候选",
            "raw_candidate_count": 0,
            "refined_count": 0,
            "status": "no_candidates",
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        }

    # max_candidates=0 表示不截断，全部候选送进 prompt
    truncated = max_candidates > 0 and len(candidate_card_ids) > max_candidates
    candidate_ids = candidate_card_ids[:max_candidates] if truncated else list(candidate_card_ids)

    # 取候选句卡完整原文（不截断，让LLM看到完整证据）
    candidate_cards: list[dict[str, Any]] = []
    for cid in candidate_ids:
        card = rt.card_by_id.get(cid)
        if card:
            candidate_cards.append({
                "card_id": cid,
                "text": agentic.card_text(card),
            })

    if not candidate_cards:
        return {
            "refined_card_ids": candidate_card_ids,
            "reason": "候选句卡原文全部缺失，保留原候选",
            "raw_candidate_count": len(candidate_card_ids),
            "refined_count": len(candidate_card_ids),
            "status": "failed",
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        }

    prompt = build_refine_prompt(question, candidate_cards)
    client = rt.base.client

    try:
        raw = run_step1.call_llm(client, prompt, max_tokens=2000)
        parsed = _parse_llm_json(raw)
        refined = parsed.get("refined_card_ids", [])
        if not isinstance(refined, list):
            refined = []
        # 过滤掉不在候选里的ID（防LLM幻觉）
        cand_set = set(candidate_ids)
        refined = [cid for cid in refined if isinstance(cid, str) and cid in cand_set]
        # 去重保序
        seen: set[str] = set()
        refined_dedup: list[str] = []
        for cid in refined:
            if cid not in seen:
                seen.add(cid)
                refined_dedup.append(cid)
        reason = parsed.get("reason", "")
        if truncated:
            reason = f"[候选截断: {len(candidate_card_ids)}→{max_candidates}] {reason}"
        return {
            "refined_card_ids": refined_dedup,
            "reason": reason,
            "raw_candidate_count": len(candidate_card_ids),
            "refined_count": len(refined_dedup),
            "status": "ok",
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        }
    except Exception as exc:
        return {
            "refined_card_ids": candidate_card_ids,  # 失败保留原候选
            "reason": f"refine失败: {exc}",
            "raw_candidate_count": len(candidate_card_ids),
            "refined_count": len(candidate_card_ids),
            "status": "failed",
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        }


def to_question_card_map_entry(match_result: dict[str, Any], question: Question) -> dict[str, Any]:
    """把 match_one_question 的结果转成 question_card_map.json 的 entry 格式。

    兼容旧格式：{knowledge_point, num_candidates, matched_card_ids, ...}
    并扩展：保留 option_evidence + match_method，方便后续考点生成。
    """
    entry = {
        "knowledge_point": match_result.get("knowledge_point") or question.knowledge_point,
        "num_candidates": match_result.get("evidence_count", 0),
        "matched_card_ids": match_result.get("matched_card_ids", []),
        "match_method": "agentic_v6s_planner" if match_result.get("planner_used") else "agentic_v6s_simple",
    }
    if match_result.get("option_evidence"):
        entry["option_evidence"] = match_result["option_evidence"]
    return entry
