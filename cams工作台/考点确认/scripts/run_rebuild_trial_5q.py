from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI


SCRIPT_DIR = Path(__file__).resolve().parent
WORK_DIR = SCRIPT_DIR.parent
APP_DIR = WORK_DIR.parent
DATA_DIR = APP_DIR / "data" / "teaching_assets"
PAGE_MAP_PATH = APP_DIR / "data" / "page_maps" / "card_page_map_v6.json"
DEFAULT_OUT_DIR = WORK_DIR / "outputs" / "rebuild_trial_5q"

DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_LIMIT = 5
SIMILARITY_THRESHOLD = 0.72
DEFAULT_FALLBACK_MODELS = ["deepseek-chat", "deepseek-reasoner"]


SYSTEM_PROMPT = """你是 CAMS 考试教研助理，任务是把单道题沉淀为可审计的候选考点。
你只能使用输入中提供的教材句卡 card_id，不得新增、编造或替换教材依据。
正式候选考点只能来自题目考查方向、正确选项和 correct_allowed_card_ids 中的教材句卡。
错误选项证据只用于识别混淆点或易错说明，不得进入 candidate_points 的任何 card_ids 字段。
输出必须是合法 JSON，不要输出 Markdown。"""


USER_PROMPT_TEMPLATE = """请根据下面的题目与教材句卡，输出单题候选考点。

要求：
1. 先给出 exam_intent：这道题换掉表面情境后，仍然在考什么。
2. candidate_points 通常只输出 1 个；只有题目确实考查两个独立知识单元时才输出多个。
3. 每个 candidate_point 必须至少有 1 个 core_card_ids，且 core_card_ids、supporting_card_ids、background_card_ids 都只能来自 correct_allowed_card_ids。
4. title 要像教研整理的知识点，不要照抄选项文本。
5. teaching_focus 用“考查学生能否……”句式，体现教材知识、使用场景和判断逻辑。
6. supporting_card_ids 只放补充场景、边界、例外或相关定义。
7. background_card_ids 只放帮助理解但不直接支撑考点的句卡。
8. trap_notes 只记录错误选项造成的混淆或学生易错点，不是正式考点；related_card_ids 只能来自 trap_allowed_card_ids 或 correct_allowed_card_ids。
9. 如果证据不足，不要硬造考点；在 rejected_evidence 中说明。

输出 JSON 格式：
{
  "question_id": "",
  "exam_intent": "",
  "candidate_points": [
    {
      "title": "",
      "teaching_focus": "",
      "core_card_ids": [],
      "supporting_card_ids": [],
      "background_card_ids": [],
      "reason": "",
      "confidence": "high | medium | low"
    }
  ],
  "trap_notes": [
    {
      "title": "",
      "related_option": "",
      "related_card_ids": [],
      "reason": "",
      "confidence": "high | medium | low"
    }
  ],
  "rejected_evidence": [
    {
      "card_id": "",
      "reason": ""
    }
  ]
}

题目输入：
{pack_json}
"""


MERGE_SYSTEM_PROMPT = """你是 CAMS 考试教研助理，判断两个候选考点是否属于同一个教材知识单元。
只能根据输入的题目考查方向、标题和教材句卡判断。输出合法 JSON。"""


MERGE_USER_PROMPT_TEMPLATE = """请判断下面两个候选考点是否应该合并为同一个正式考点。

合并标准：
1. 两者考查同一个教材知识、使用场景和判断逻辑。
2. 主证据句卡相同、重合或共同指向同一教材原文知识单元。
3. 不能仅因为都属于反洗钱大主题就合并。
4. 宁可少合并，也不要乱合并。

输出 JSON：
{
  "merge": true,
  "reason": "",
  "merged_title": "",
  "merged_teaching_focus": ""
}

候选考点：
{pair_json}
"""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def compact(text: Any, limit: int = 360) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "..."


def normalize_text(text: Any) -> str:
    value = str(text or "").lower()
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[，。！？；：、,.!?;:()\[\]{}<>《》“”\"'`~\-—_/\\|]", "", value)
    return value


def char_bigrams(text: str) -> set[str]:
    value = normalize_text(text)
    if len(value) <= 1:
        return {value} if value else set()
    return {value[i : i + 2] for i in range(len(value) - 1)}


def jaccard(a: Any, b: Any) -> float:
    aa = char_bigrams(str(a or ""))
    bb = char_bigrams(str(b or ""))
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


def client_from_env(model_arg: str | None = None) -> tuple[OpenAI, str]:
    load_env_file(WORK_DIR / ".env")
    api_key = (
        os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("DS_API_KEY")
        or os.getenv("LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    if not api_key:
        raise RuntimeError("Missing API key: set OPENAI_API_KEY, DEEPSEEK_API_KEY, DS_API_KEY, or LLM_API_KEY.")
    base_url = (
        os.getenv("DEEPSEEK_BASE_URL")
        or os.getenv("LLM_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or DEFAULT_BASE_URL
    )
    model = (
        model_arg
        or os.getenv("DEEPSEEK_MODEL")
        or os.getenv("LLM_MODEL_NAME")
        or os.getenv("OPENAI_MODEL")
        or DEFAULT_MODEL
    )
    return OpenAI(api_key=api_key, base_url=base_url), model


def model_chain_from_env(primary_model: str) -> list[str]:
    if "REBUILD_TRIAL_FALLBACK_MODELS" in os.environ:
        fallback_raw = os.environ["REBUILD_TRIAL_FALLBACK_MODELS"]
    elif "LLM_FALLBACK_MODELS" in os.environ:
        fallback_raw = os.environ["LLM_FALLBACK_MODELS"]
    else:
        fallback_raw = None
    if fallback_raw is None:
        fallback_raw = ",".join(DEFAULT_FALLBACK_MODELS)
    if fallback_raw.strip().lower() in {"", "none", "off", "false", "no", "0"}:
        fallback_raw = ""
    models: list[str] = []
    for model in [primary_model, *[item.strip() for item in fallback_raw.split(",")]]:
        if model and model not in models:
            models.append(model)
    return models


def extract_json(text: str) -> dict[str, Any]:
    value = (text or "").strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value)
        value = re.sub(r"\s*```$", "", value)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        start = value.find("{")
        end = value.rfind("}")
        if start >= 0 and end > start:
            return json.loads(value[start : end + 1])
        raise


def call_json(client: OpenAI, model: str, system_prompt: str, user_prompt: str, max_tokens: int = 3000) -> tuple[dict[str, Any], str]:
    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                **kwargs,
                response_format={"type": "json_object"},
            )
            break
        except Exception as exc:
            last_exc = exc
            try:
                response = client.chat.completions.create(**kwargs)
                break
            except Exception as fallback_exc:
                last_exc = fallback_exc
                if attempt < 2:
                    time.sleep(2 + attempt * 3)
                continue
    else:
        assert last_exc is not None
        raise last_exc
    text = response.choices[0].message.content or ""
    return extract_json(text), text


def call_json_with_fallback(
    client: OpenAI,
    models: list[str],
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 3000,
) -> tuple[dict[str, Any], str, str, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    last_exc: Exception | None = None
    for model in models:
        try:
            parsed, raw_text = call_json(client, model, system_prompt, user_prompt, max_tokens=max_tokens)
            return parsed, raw_text, model, errors
        except Exception as exc:
            last_exc = exc
            errors.append({"model": model, "error": f"{type(exc).__name__}: {exc}"})
            continue
    assert last_exc is not None
    raise last_exc


def normalize_cards(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        cards = payload.get("cards", [])
    else:
        cards = payload
    return [card for card in cards if isinstance(card, dict) and card.get("card_id")]


def build_card_indexes(cards: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    by_id = {card["card_id"]: card for card in cards}
    by_norm: dict[str, str] = {}
    for card in cards:
        for field in ["citation", "knowledge"]:
            norm = normalize_text(card.get(field))
            if norm and norm not in by_norm:
                by_norm[norm] = card["card_id"]
    return by_id, by_norm


def map_to_canonical_card(
    evidence_card: dict[str, Any],
    cards: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
    by_norm: dict[str, str],
) -> dict[str, Any]:
    original_id = evidence_card.get("card_id") or ""
    if original_id in by_id:
        card = by_id[original_id]
        return {
            "original_card_id": original_id,
            "canonical_card_id": original_id,
            "match_method": "same_id",
            "confidence": 1.0,
            "quote": card.get("citation", ""),
            "knowledge": card.get("knowledge", ""),
            "chapter_path": card.get("chapter_path", ""),
        }

    texts = [
        evidence_card.get("quote"),
        evidence_card.get("citation"),
        evidence_card.get("knowledge"),
    ]
    for text in texts:
        norm = normalize_text(text)
        if norm and norm in by_norm:
            cid = by_norm[norm]
            card = by_id[cid]
            return {
                "original_card_id": original_id,
                "canonical_card_id": cid,
                "match_method": "exact_quote",
                "confidence": 1.0,
                "quote": card.get("citation", ""),
                "knowledge": card.get("knowledge", ""),
                "chapter_path": card.get("chapter_path", ""),
            }

    best: tuple[float, dict[str, Any] | None] = (0.0, None)
    evidence_text = " ".join(str(text or "") for text in texts)
    for card in cards:
        score = max(
            jaccard(evidence_text, card.get("citation", "")),
            jaccard(evidence_text, card.get("knowledge", "")),
        )
        if score > best[0]:
            best = (score, card)
    score, card = best
    if card and score >= SIMILARITY_THRESHOLD:
        return {
            "original_card_id": original_id,
            "canonical_card_id": card["card_id"],
            "match_method": "text_similarity",
            "confidence": round(score, 4),
            "quote": card.get("citation", ""),
            "knowledge": card.get("knowledge", ""),
            "chapter_path": card.get("chapter_path", ""),
        }

    return {
        "original_card_id": original_id,
        "canonical_card_id": "",
        "match_method": "unmatched",
        "confidence": round(score, 4),
        "quote": evidence_card.get("quote") or evidence_card.get("citation") or "",
        "knowledge": evidence_card.get("knowledge") or "",
        "chapter_path": evidence_card.get("chapter_path") or "",
    }


def option_is_correct(option: dict[str, Any]) -> bool:
    return bool(option.get("is_correct_answer")) or str(option.get("judgement", "")).lower() == "correct"


def evidence_priority(option: dict[str, Any], card: dict[str, Any]) -> int:
    support = str(card.get("support_type") or "").lower()
    status = str(option.get("evidence_status") or "").lower()
    score = 0
    if support == "direct":
        score += 5
    if status == "direct":
        score += 4
    if support in {"support", "positive"}:
        score += 2
    if status == "indirect":
        score += 1
    return score


def build_question_pack(
    item: dict[str, Any],
    questions_by_id: dict[str, dict[str, Any]],
    cards: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
    by_norm: dict[str, str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    qid = item.get("question_id")
    question = questions_by_id.get(qid, {})
    correct_allowed_cards: dict[str, dict[str, Any]] = {}
    trap_allowed_cards: dict[str, dict[str, Any]] = {}
    gaps: list[dict[str, Any]] = []
    correct_options = []
    distractors = []

    for option in item.get("options", []):
        is_correct = option_is_correct(option)
        opt_summary = {
            "option": option.get("option", ""),
            "option_text": option.get("option_text", ""),
            "judgement": option.get("judgement", ""),
            "evidence_status": option.get("evidence_status", ""),
            "common_trap": compact(option.get("common_trap"), 220),
        }
        evidence_rows = []
        for ev in option.get("evidence_cards", []) or []:
            mapped = map_to_canonical_card(ev, cards, by_id, by_norm)
            row = {
                "original_card_id": ev.get("card_id", ""),
                "canonical_card_id": mapped.get("canonical_card_id", ""),
                "match_method": mapped.get("match_method", ""),
                "match_confidence": mapped.get("confidence", 0),
                "support_type": ev.get("support_type", ""),
                "relevance": ev.get("relevance", ""),
                "reason": compact(ev.get("reason"), 260),
                "quote": compact(mapped.get("quote") or ev.get("quote") or ev.get("citation"), 420),
                "knowledge": compact(mapped.get("knowledge") or ev.get("knowledge"), 260),
                "chapter_path": mapped.get("chapter_path") or ev.get("chapter_path", ""),
                "priority": evidence_priority(option, ev),
            }
            if row["canonical_card_id"]:
                if is_correct:
                    correct_allowed_cards[row["canonical_card_id"]] = row
                else:
                    trap_allowed_cards[row["canonical_card_id"]] = row
            elif is_correct:
                gaps.append(
                    {
                        "question_id": qid,
                        "option": option.get("option", ""),
                        "option_text": option.get("option_text", ""),
                        "original_card_id": ev.get("card_id", ""),
                        "reason": "correct option evidence could not be mapped to cards_v6_sentence.json",
                        "best_match_confidence": mapped.get("confidence", 0),
                    }
                )
            evidence_rows.append(row)
        opt_summary["evidence_cards"] = sorted(evidence_rows, key=lambda row: -row.get("priority", 0))[:6]
        if is_correct:
            correct_options.append(opt_summary)
            if not evidence_rows:
                gaps.append(
                    {
                        "question_id": qid,
                        "option": option.get("option", ""),
                        "option_text": option.get("option_text", ""),
                        "reason": "correct option has no evidence_cards",
                    }
                )
        else:
            distractors.append(opt_summary)

    correct_allowed_list = sorted(correct_allowed_cards.values(), key=lambda row: (-row.get("priority", 0), row["canonical_card_id"]))
    trap_allowed_list = sorted(trap_allowed_cards.values(), key=lambda row: (-row.get("priority", 0), row["canonical_card_id"]))
    pack = {
        "question_id": qid,
        "section": question.get("section") or item.get("section", ""),
        "stem": item.get("stem") or question.get("stem", ""),
        "answer": item.get("answer") or question.get("answer", ""),
        "options": question.get("options") or {},
        "teacher_explanation_for_intent_only": compact(question.get("explanation"), 900),
        "correct_options": correct_options,
        "distractors_for_traps_only": distractors,
        "correct_allowed_card_ids": [row["canonical_card_id"] for row in correct_allowed_list],
        "correct_allowed_cards": [
            {
                "card_id": row["canonical_card_id"],
                "quote": row["quote"],
                "knowledge": row["knowledge"],
                "chapter_path": row["chapter_path"],
                "support_type": row["support_type"],
                "reason": row["reason"],
                "from_original_card_id": row["original_card_id"],
                "match_method": row["match_method"],
                "match_confidence": row["match_confidence"],
            }
            for row in correct_allowed_list[:10]
        ],
        "trap_allowed_card_ids": [row["canonical_card_id"] for row in trap_allowed_list],
        "trap_allowed_cards": [
            {
                "card_id": row["canonical_card_id"],
                "quote": row["quote"],
                "knowledge": row["knowledge"],
                "chapter_path": row["chapter_path"],
                "support_type": row["support_type"],
                "reason": row["reason"],
                "from_original_card_id": row["original_card_id"],
                "match_method": row["match_method"],
                "match_confidence": row["match_confidence"],
            }
            for row in trap_allowed_list[:8]
        ],
    }
    return pack, gaps


def select_question_items(option_evidence: dict[str, Any], ids: list[str] | None, limit: int) -> list[dict[str, Any]]:
    items = option_evidence.get("items", [])
    if ids:
        by_id = {item.get("question_id"): item for item in items}
        return [by_id[qid] for qid in ids if qid in by_id]

    scored = []
    for item in items:
        direct_correct = 0
        mapped_like = 0
        indirect_correct = 0
        manual_correct = 0
        for opt in item.get("options", []):
            if not option_is_correct(opt):
                continue
            status = str(opt.get("evidence_status", "")).lower()
            if status == "indirect":
                indirect_correct += 1
            if status == "needs_manual":
                manual_correct += 1
            for ev in opt.get("evidence_cards", []) or []:
                if str(ev.get("support_type", "")).lower() == "direct" or status == "direct":
                    direct_correct += 1
                if ev.get("card_id"):
                    mapped_like += 1
        if mapped_like:
            scored.append((direct_correct, indirect_correct, -manual_correct, mapped_like, item.get("question_id", ""), item))
    scored.sort(key=lambda row: (-row[0], -row[1], row[2], -row[3], row[4]))
    return [row[5] for row in scored[:limit]]


def validate_candidate(result: dict[str, Any], pack: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    correct_allowed = set(pack.get("correct_allowed_card_ids") or [])
    trap_allowed = set(pack.get("trap_allowed_card_ids") or [])
    all_allowed = correct_allowed | trap_allowed
    if result.get("question_id") != pack.get("question_id"):
        issues.append("question_id mismatch")
    candidates = result.get("candidate_points")
    if not isinstance(candidates, list):
        issues.append("candidate_points missing or not a list")
        return issues
    if len(candidates) > 2:
        issues.append("too many candidate_points for one question")
    option_texts = [str(opt.get("option_text") or "") for opt in pack.get("correct_options", [])]
    for idx, point in enumerate(candidates):
        core = point.get("core_card_ids") or []
        if not core:
            issues.append(f"candidate_points[{idx}] has no core_card_ids")
        for field in ["core_card_ids", "supporting_card_ids", "background_card_ids"]:
            for cid in point.get(field) or []:
                if cid not in correct_allowed:
                    if cid in trap_allowed:
                        issues.append(f"candidate_points[{idx}].{field} incorrectly uses trap-only card_id: {cid}")
                    else:
                        issues.append(f"candidate_points[{idx}].{field} has unknown card_id: {cid}")
        title = str(point.get("title") or "").strip()
        if not title:
            issues.append(f"candidate_points[{idx}] has empty title")
        for opt_text in option_texts:
            if title and opt_text and (title == opt_text or title in opt_text or opt_text in title):
                issues.append(f"candidate_points[{idx}] title is too close to correct option text")
    for idx, trap in enumerate(result.get("trap_notes") or []):
        for cid in trap.get("related_card_ids") or []:
            if cid not in all_allowed:
                issues.append(f"trap_notes[{idx}].related_card_ids has unknown card_id: {cid}")
    return issues


def candidate_text(row: dict[str, Any]) -> str:
    point = row.get("candidate_point", {})
    pack = row.get("pack", {})
    cards = pack.get("correct_allowed_cards", [])
    selected = set((point.get("core_card_ids") or []) + (point.get("supporting_card_ids") or []))
    quotes = " ".join(card.get("quote", "") for card in cards if card.get("card_id") in selected)
    return " ".join([point.get("title", ""), point.get("teaching_focus", ""), row.get("exam_intent", ""), quotes])


def build_merge_pairs(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = []
    for i in range(len(candidate_rows)):
        for j in range(i + 1, len(candidate_rows)):
            a = candidate_rows[i]
            b = candidate_rows[j]
            if a.get("question_id") == b.get("question_id"):
                continue
            ap = a.get("candidate_point", {})
            bp = b.get("candidate_point", {})
            a_core = set(ap.get("core_card_ids") or [])
            b_core = set(bp.get("core_card_ids") or [])
            overlap = sorted(a_core & b_core)
            score = jaccard(candidate_text(a), candidate_text(b))
            if len(overlap) >= 2 or score >= 0.42:
                pairs.append(
                    {
                        "a_question_id": a.get("question_id"),
                        "b_question_id": b.get("question_id"),
                        "a_title": ap.get("title", ""),
                        "b_title": bp.get("title", ""),
                        "core_overlap": overlap,
                        "text_similarity": round(score, 4),
                        "needs_llm_judge": True,
                        "merge": None,
                        "reason": "candidate only: shared evidence or text similarity; requires judgement",
                    }
                )
    return pairs


def run_trial(
    ids: list[str] | None,
    limit: int,
    model_arg: str | None,
    skip_llm: bool,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    out_dir = out_dir or DEFAULT_OUT_DIR
    questions = read_json(DATA_DIR / "questions.json").get("questions", [])
    questions_by_id = {q["id"]: q for q in questions if q.get("id")}
    option_evidence = read_json(DATA_DIR / "option_evidence_map.json")
    cards = normalize_cards(read_json(DATA_DIR / "cards_v6_sentence.json"))
    by_id, by_norm = build_card_indexes(cards)
    selected_items = select_question_items(option_evidence, ids, limit)

    packs = []
    evidence_gaps = []
    for item in selected_items:
        pack, gaps = build_question_pack(item, questions_by_id, cards, by_id, by_norm)
        if pack.get("correct_allowed_card_ids"):
            packs.append(pack)
        evidence_gaps.extend(gaps)

    client: OpenAI | None = None
    model = model_arg or os.getenv("DEEPSEEK_MODEL") or os.getenv("LLM_MODEL_NAME") or os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    if not skip_llm:
        client, model = client_from_env(model_arg)

    model_chain = [model]
    if not skip_llm and client is not None:
        model_chain = model_chain_from_env(model)

    raw_rows: list[dict[str, Any]] = []
    candidate_outputs = []
    candidate_rows = []
    for pack in packs:
        prompt = USER_PROMPT_TEMPLATE.replace("{pack_json}", json.dumps(pack, ensure_ascii=False, indent=2))
        if skip_llm:
            parsed = {
                "question_id": pack["question_id"],
                "exam_intent": "",
                "candidate_points": [],
                "trap_notes": [],
                "rejected_evidence": [],
            }
            raw_text = ""
        else:
            assert client is not None
            try:
                parsed, raw_text, used_model, model_attempts = call_json_with_fallback(
                    client,
                    model_chain,
                    SYSTEM_PROMPT,
                    prompt,
                )
            except Exception as exc:
                parsed = {
                    "question_id": pack["question_id"],
                    "exam_intent": "",
                    "candidate_points": [],
                    "trap_notes": [],
                    "rejected_evidence": [],
                }
                raw_text = ""
                output = {
                    "question_id": pack["question_id"],
                    "model": model,
                    "actual_model": "",
                    "model_attempts": [{"model": item, "error": "not reached"} for item in model_chain],
                    "pack": pack,
                    "result": parsed,
                    "validation_issues": [f"llm_call_failed: {type(exc).__name__}: {exc}"],
                }
                candidate_outputs.append(output)
                raw_rows.append(
                    {
                        "question_id": pack["question_id"],
                        "model": model,
                        "model_chain": model_chain,
                        "raw_response": raw_text,
                        "error": str(exc),
                    }
                )
                continue
        if skip_llm:
            used_model = model
            model_attempts = []
        issues = validate_candidate(parsed, pack)
        output = {
            "question_id": pack["question_id"],
            "model": model,
            "actual_model": used_model,
            "model_attempts": model_attempts,
            "pack": pack,
            "result": parsed,
            "validation_issues": issues,
        }
        candidate_outputs.append(output)
        raw_rows.append(
            {
                "question_id": pack["question_id"],
                "model": model,
                "actual_model": used_model,
                "model_attempts": model_attempts,
                "raw_response": raw_text,
            }
        )
        for point in parsed.get("candidate_points") or []:
            candidate_rows.append(
                {
                    "question_id": pack["question_id"],
                    "exam_intent": parsed.get("exam_intent", ""),
                    "candidate_point": point,
                    "pack": pack,
                    "validation_issues": issues,
                }
            )

    merge_pairs = build_merge_pairs(candidate_rows)
    merge_judgements = []
    if not skip_llm and client is not None:
        for pair in merge_pairs[:6]:
            pair_input = {
                "candidate_a": next(
                    row for row in candidate_rows if row["question_id"] == pair["a_question_id"]
                ),
                "candidate_b": next(
                    row for row in candidate_rows if row["question_id"] == pair["b_question_id"]
                ),
            }
            slim = {
                "candidate_a": slim_candidate_for_merge(pair_input["candidate_a"]),
                "candidate_b": slim_candidate_for_merge(pair_input["candidate_b"]),
            }
            prompt = MERGE_USER_PROMPT_TEMPLATE.replace("{pair_json}", json.dumps(slim, ensure_ascii=False, indent=2))
            try:
                parsed, raw_text, used_model, model_attempts = call_json_with_fallback(
                    client,
                    model_chain,
                    MERGE_SYSTEM_PROMPT,
                    prompt,
                    max_tokens=1200,
                )
                pair["llm_judgement"] = parsed
                pair["raw_response"] = raw_text
                pair["actual_model"] = used_model
                pair["model_attempts"] = model_attempts
            except Exception as exc:
                pair["llm_error"] = str(exc)
            merge_judgements.append(pair)

    report = build_report(packs, candidate_outputs, candidate_rows, evidence_gaps, merge_judgements, model, model_chain)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "question_packs.json", {"generated_at": now(), "items": packs})
    write_json(out_dir / "candidate_points.json", {"generated_at": now(), "items": candidate_outputs})
    write_json(out_dir / "merge_preview.json", {"generated_at": now(), "items": merge_judgements})
    write_json(out_dir / "evidence_gaps.json", {"generated_at": now(), "items": evidence_gaps})
    write_jsonl(out_dir / "raw_llm_responses.jsonl", raw_rows)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    return {
        "out_dir": str(out_dir),
        "model": model,
        "model_chain": model_chain,
        "question_count": len(packs),
        "candidate_point_count": len(candidate_rows),
        "evidence_gap_count": len(evidence_gaps),
        "merge_pair_count": len(merge_judgements),
    }


def slim_candidate_for_merge(row: dict[str, Any]) -> dict[str, Any]:
    point = row.get("candidate_point", {})
    pack = row.get("pack", {})
    selected = set((point.get("core_card_ids") or []) + (point.get("supporting_card_ids") or []))
    cards = [
        {
            "card_id": card.get("card_id"),
            "quote": card.get("quote"),
            "knowledge": card.get("knowledge"),
        }
        for card in pack.get("correct_allowed_cards", [])
        if card.get("card_id") in selected
    ]
    return {
        "question_id": row.get("question_id"),
        "exam_intent": row.get("exam_intent"),
        "title": point.get("title"),
        "teaching_focus": point.get("teaching_focus"),
        "core_card_ids": point.get("core_card_ids"),
        "supporting_card_ids": point.get("supporting_card_ids"),
        "cards": cards,
    }


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def build_report(
    packs: list[dict[str, Any]],
    candidate_outputs: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    evidence_gaps: list[dict[str, Any]],
    merge_judgements: list[dict[str, Any]],
    model: str,
    model_chain: list[str] | None = None,
) -> str:
    lines = [
        "# 考点资产重建五题试跑报告",
        "",
        f"- generated_at: {now()}",
        f"- model: {model}",
        f"- model_chain: {', '.join(model_chain or [model])}",
        f"- questions: {len(packs)}",
        f"- candidate_points: {len(candidate_rows)}",
        f"- evidence_gaps: {len(evidence_gaps)}",
        f"- merge_pairs: {len(merge_judgements)}",
        "",
        "## 题目与候选考点",
        "",
    ]
    for item in candidate_outputs:
        result = item.get("result") or {}
        pack = item.get("pack") or {}
        lines.append(f"### {item.get('question_id')} {pack.get('stem', '')}")
        lines.append("")
        lines.append(f"- 答案：{pack.get('answer', '')}")
        lines.append(f"- 题目考查方向：{result.get('exam_intent', '')}")
        if item.get("actual_model") and item.get("actual_model") != item.get("model"):
            lines.append(f"- 实际模型：{item.get('actual_model')}（主模型失败后降级）")
        issues = item.get("validation_issues") or []
        lines.append(f"- 校验问题：{'; '.join(issues) if issues else '无'}")
        for point in result.get("candidate_points") or []:
            lines.append("")
            lines.append(f"#### {point.get('title', '')}")
            lines.append("")
            lines.append(f"- teaching_focus：{point.get('teaching_focus', '')}")
            lines.append(f"- core_card_ids：{', '.join(point.get('core_card_ids') or [])}")
            lines.append(f"- supporting_card_ids：{', '.join(point.get('supporting_card_ids') or [])}")
            lines.append(f"- confidence：{point.get('confidence', '')}")
            lines.append(f"- reason：{point.get('reason', '')}")
        traps = result.get("trap_notes") or []
        if traps:
            lines.append("")
            lines.append("易错/混淆：")
            for trap in traps[:3]:
                lines.append(f"- {trap.get('title', '')}：{trap.get('reason', '')}")
        lines.append("")

    lines += ["## 合并预览", ""]
    if not merge_judgements:
        lines.append("- 暂无需要合并的候选对。")
    for pair in merge_judgements:
        lines.append(
            f"- {pair.get('a_question_id')} / {pair.get('b_question_id')} | "
            f"similarity={pair.get('text_similarity')} | overlap={','.join(pair.get('core_overlap') or [])}"
        )
        if pair.get("reason"):
            lines.append(f"  - {pair.get('reason')}")
        if pair.get("llm_judgement"):
            lines.append(f"  - LLM: {json.dumps(pair.get('llm_judgement'), ensure_ascii=False)}")

    lines += ["", "## 缺依据候选", ""]
    if not evidence_gaps:
        lines.append("- 无。")
    for gap in evidence_gaps[:20]:
        lines.append(
            f"- {gap.get('question_id')} {gap.get('option', '')} "
            f"{gap.get('option_text', '')}：{gap.get('reason', '')}"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run 5-question trial for exam point asset rebuilding.")
    parser.add_argument("--ids", nargs="*", help="Question ids to run, e.g. 2.1_1 2.1_2")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--model", default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--skip-llm", action="store_true")
    args = parser.parse_args()
    summary = run_trial(args.ids, args.limit, args.model, args.skip_llm, args.out_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
