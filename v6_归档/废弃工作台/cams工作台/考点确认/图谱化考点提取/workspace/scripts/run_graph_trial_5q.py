from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI


SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent
GRAPH_DIR = WORKSPACE_DIR.parent
CONFIRM_DIR = GRAPH_DIR.parent
APP_DIR = CONFIRM_DIR.parent
DATA_DIR = APP_DIR / "data" / "teaching_assets"
PAGE_MAP_PATH = APP_DIR / "data" / "page_maps" / "card_page_map_v6.json"

DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_LIMIT = 5


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


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


def compact(text: Any, limit: int = 600) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "..."


def slug(text: Any, prefix: str = "id") -> str:
    value = re.sub(r"[^0-9A-Za-z_\-.]+", "_", str(text or "").strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or prefix


def normalize_text(text: Any) -> str:
    value = str(text or "").lower()
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"[，。！？；：、,.!?;:()\[\]{}<>《》“”\"'`~\-—_/\\|]", "", value)
    return value


def char_bigrams(text: Any) -> set[str]:
    value = normalize_text(text)
    if len(value) <= 1:
        return {value} if value else set()
    return {value[i : i + 2] for i in range(len(value) - 1)}


def jaccard(a: Any, b: Any) -> float:
    aa = char_bigrams(a)
    bb = char_bigrams(b)
    if not aa or not bb:
        return 0.0
    return len(aa & bb) / len(aa | bb)


def normalize_cards(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("cards", "items", "data"):
            if isinstance(payload.get(key), list):
                return payload[key]
    if isinstance(payload, list):
        return payload
    raise ValueError("Unsupported cards payload")


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
    for env_path in [
        GRAPH_DIR / ".env",
        WORKSPACE_DIR / ".env",
        CONFIRM_DIR / ".env",
        APP_DIR / ".env",
    ]:
        load_env_file(env_path)

    api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("DS_API_KEY")
        or os.getenv("DS_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    if not api_key:
        raise RuntimeError("Missing API key: set LLM_API_KEY, DEEPSEEK_API_KEY, DS_API_KEY, DS_KEY, or OPENAI_API_KEY.")

    base_url = (
        os.getenv("LLM_BASE_URL")
        or os.getenv("DEEPSEEK_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or DEFAULT_BASE_URL
    )
    model = model_arg or os.getenv("LLM_MODEL_NAME") or os.getenv("DEEPSEEK_MODEL") or os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    return OpenAI(api_key=api_key, base_url=base_url), model


def extract_json(text: str) -> Any:
    value = (text or "").strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value)
        value = re.sub(r"\s*```$", "", value)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        start_obj = value.find("{")
        end_obj = value.rfind("}")
        start_arr = value.find("[")
        end_arr = value.rfind("]")
        if start_obj >= 0 and end_obj > start_obj:
            return json.loads(value[start_obj : end_obj + 1])
        if start_arr >= 0 and end_arr > start_arr:
            return json.loads(value[start_arr : end_arr + 1])
        raise


def call_json(client: OpenAI, model: str, system_prompt: str, user_payload: dict[str, Any], max_tokens: int = 3000) -> tuple[Any, str]:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, indent=2)},
    ]
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            response = client.chat.completions.create(**kwargs, response_format={"type": "json_object"})
            text = response.choices[0].message.content or ""
            return extract_json(text), text
        except Exception as exc:
            last_exc = exc
            try:
                response = client.chat.completions.create(**kwargs)
                text = response.choices[0].message.content or ""
                return extract_json(text), text
            except Exception as fallback_exc:
                last_exc = fallback_exc
                if attempt < 2:
                    time.sleep(2 + attempt * 2)
    assert last_exc is not None
    raise last_exc


def option_dict(question: dict[str, Any]) -> dict[str, str]:
    options = question.get("options") or {}
    if isinstance(options, dict):
        return {str(k): str(v) for k, v in options.items()}
    result = {}
    if isinstance(options, list):
        for item in options:
            if isinstance(item, dict):
                key = item.get("option") or item.get("label")
                if key:
                    result[str(key)] = str(item.get("text") or item.get("option_text") or "")
    return result


def canonical_card_id(evidence_card: dict[str, Any]) -> str:
    migration = evidence_card.get("card_id_migration") or {}
    to_id = migration.get("to")
    if isinstance(to_id, str) and to_id.startswith("v6s_"):
        return to_id
    card_id = evidence_card.get("card_id") or ""
    return str(card_id)


def fallback_evidence_cards(option: dict[str, Any], cards_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    cards = option.get("evidence_cards") or []
    if cards:
        return [card for card in cards if isinstance(card, dict)]
    result = []
    for cid in option.get("card_ids") or []:
        card = cards_by_id.get(str(cid))
        if card:
            result.append(
                {
                    "card_id": cid,
                    "support_type": option.get("evidence_status") or "",
                    "source": "option.card_ids_fallback",
                    "quote": card.get("citation") or card.get("quote") or "",
                    "reason": "由 option.card_ids 回退生成。",
                    "relevance": "",
                    "knowledge": card.get("knowledge") or "",
                    "citation": card.get("citation") or "",
                    "type": card.get("type") or "",
                    "chapter_path": card.get("chapter_path") or "",
                }
            )
    return result


def select_items(option_evidence: dict[str, Any], ids: list[str] | None, limit: int) -> list[dict[str, Any]]:
    items = option_evidence.get("items") or []
    if ids:
        want = set(ids)
        return [item for item in items if item.get("question_id") in want]
    selected = []
    for item in items:
        edge_count = 0
        correct_edge_count = 0
        incorrect_edge_count = 0
        for option in item.get("options") or []:
            evidence_cards = option.get("evidence_cards") or []
            if evidence_cards:
                edge_count += len(evidence_cards)
                if option.get("is_correct_answer"):
                    correct_edge_count += len(evidence_cards)
                else:
                    incorrect_edge_count += len(evidence_cards)
        if edge_count and correct_edge_count and incorrect_edge_count:
            selected.append(item)
        if len(selected) >= limit:
            break
    if len(selected) < limit:
        for item in items:
            if item not in selected:
                selected.append(item)
            if len(selected) >= limit:
                break
    return selected


def build_edges_for_item(
    item: dict[str, Any],
    question: dict[str, Any],
    cards_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    qid = item.get("question_id") or question.get("id")
    gaps = []
    edges = []
    seen = set()
    for option in item.get("options") or []:
        opt = str(option.get("option") or "")
        is_correct = bool(option.get("is_correct_answer"))
        for evidence_card in fallback_evidence_cards(option, cards_by_id):
            cid = canonical_card_id(evidence_card)
            card = cards_by_id.get(cid)
            if not cid or not card:
                gaps.append(
                    {
                        "question_id": qid,
                        "option": opt,
                        "option_text": option.get("option_text") or "",
                        "original_card_id": evidence_card.get("card_id") or "",
                        "canonical_card_id": cid,
                        "reason": "evidence card cannot be resolved to cards_v6_sentence.json",
                    }
                )
                continue
            edge_key = (qid, opt, cid)
            if edge_key in seen:
                continue
            seen.add(edge_key)
            edge_id = slug(f"{qid}_{opt}_{cid}", "edge")
            edges.append(
                {
                    "edge_id": edge_id,
                    "question_id": qid,
                    "stem": item.get("stem") or question.get("stem") or "",
                    "answer": item.get("answer") or question.get("answer") or "",
                    "option": opt,
                    "option_text": option.get("option_text") or "",
                    "is_correct_answer": is_correct,
                    "judgement": option.get("judgement") or "",
                    "evidence_status": option.get("evidence_status") or "",
                    "support_type": evidence_card.get("support_type") or option.get("evidence_status") or "",
                    "edge_role": "correct_option_evidence" if is_correct else "incorrect_option_evidence",
                    "canonical_card_id": cid,
                    "original_card_id": evidence_card.get("card_id") or cid,
                    "source": evidence_card.get("source") or "",
                    "relevance": evidence_card.get("relevance") or "",
                    "match_confidence": (evidence_card.get("card_id_migration") or {}).get("confidence", ""),
                    "quote": evidence_card.get("quote") or card.get("citation") or "",
                    "knowledge": evidence_card.get("knowledge") or card.get("knowledge") or "",
                    "citation": evidence_card.get("citation") or card.get("citation") or "",
                    "chapter_path": evidence_card.get("chapter_path") or card.get("chapter_path") or "",
                    "evidence_reason": evidence_card.get("reason") or "",
                    "option_explanation": compact(option.get("explanation"), 500),
                    "common_trap": compact(option.get("common_trap"), 320),
                }
            )
    return edges, gaps


def build_question_pack(
    item: dict[str, Any],
    question: dict[str, Any],
    edges: list[dict[str, Any]],
    include_teacher_explanation: bool = False,
) -> dict[str, Any]:
    options = option_dict(question)
    if not options:
        options = {str(opt.get("option")): str(opt.get("option_text") or "") for opt in item.get("options") or []}
    edge_payload = []
    for edge in edges:
        edge_payload.append(
            {
                "edge_id": edge["edge_id"],
                "option": edge["option"],
                "option_text": edge["option_text"],
                "is_correct_answer": edge["is_correct_answer"],
                "edge_role": edge["edge_role"],
                "card_id": edge["canonical_card_id"],
                "support_type": edge["support_type"],
                "evidence_status": edge["evidence_status"],
                "quote": compact(edge["quote"], 260),
                "knowledge": compact(edge["knowledge"], 180),
                "chapter_path": edge["chapter_path"],
                "evidence_reason": compact(edge["evidence_reason"], 240),
            }
        )
    pack = {
        "question_id": item.get("question_id") or question.get("id"),
        "section": question.get("section") or "",
        "stem": item.get("stem") or question.get("stem") or "",
        "answer": item.get("answer") or question.get("answer") or "",
        "options": [{"option": key, "text": value} for key, value in sorted(options.items())],
        "option_evidence_edges": edge_payload,
        "instructions": {
            "goal": "根据所有选项证据生成图谱化考点候选。正确项和错误项都可贡献候选，但必须保留来源角色。",
            "constraints": [
                "只能引用 option_evidence_edges 中出现的 edge_id 和 card_id。",
                "不要把没有教材句卡依据的选项生成候选。",
                "错误项证据不能被描述为正确答案依据，只能作为比较、排除、干扰、辨析或题目涉及知识。",
            ],
        },
    }
    if include_teacher_explanation:
        pack["teacher_explanation_for_reference"] = compact(question.get("explanation"), 1000)
    return pack


def validate_candidate_payload(payload: dict[str, Any], pack: dict[str, Any]) -> list[str]:
    issues = []
    edge_ids = {edge["edge_id"] for edge in pack.get("option_evidence_edges") or []}
    card_ids = {edge["card_id"] for edge in pack.get("option_evidence_edges") or []}
    if payload.get("question_id") != pack.get("question_id"):
        issues.append("question_id mismatch")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        return ["candidates missing or not a list"]
    for idx, candidate in enumerate(candidates):
        if not str(candidate.get("title") or "").strip():
            issues.append(f"candidates[{idx}] empty title")
        src_edges = candidate.get("source_edge_ids") or []
        src_cards = candidate.get("source_card_ids") or []
        if not src_edges:
            issues.append(f"candidates[{idx}] has no source_edge_ids")
        if not src_cards:
            issues.append(f"candidates[{idx}] has no source_card_ids")
        for edge_id in src_edges:
            if edge_id not in edge_ids:
                issues.append(f"candidates[{idx}] unknown edge_id: {edge_id}")
        for card_id in src_cards:
            if card_id not in card_ids:
                issues.append(f"candidates[{idx}] unknown card_id: {card_id}")
    return issues


def candidate_merge_text(candidate: dict[str, Any], edges_by_id: dict[str, dict[str, Any]]) -> str:
    edges = [edges_by_id[eid] for eid in candidate.get("source_edge_ids") or [] if eid in edges_by_id]
    return " ".join(
        [
            candidate.get("title") or "",
            candidate.get("teaching_focus") or "",
            candidate.get("exam_intent") or "",
            " ".join(edge.get("option_text") or "" for edge in edges),
            " ".join(edge.get("knowledge") or "" for edge in edges),
            " ".join(edge.get("quote") or "" for edge in edges),
            " ".join(edge.get("chapter_path") or "" for edge in edges),
        ]
    )


def recall_merge_pairs(candidates: list[dict[str, Any]], edges_by_id: dict[str, dict[str, Any]], limit: int = 40) -> list[dict[str, Any]]:
    pairs = []
    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            a = candidates[i]
            b = candidates[j]
            a_cards = set(a.get("source_card_ids") or [])
            b_cards = set(b.get("source_card_ids") or [])
            shared_cards = sorted(a_cards & b_cards)
            title_sim = jaccard(a.get("title"), b.get("title"))
            text_sim = jaccard(candidate_merge_text(a, edges_by_id), candidate_merge_text(b, edges_by_id))
            same_question = a.get("question_id") == b.get("question_id")
            score = max(title_sim, text_sim) + (0.4 if shared_cards else 0) + (0.12 if same_question else 0)
            if shared_cards or title_sim >= 0.28 or text_sim >= 0.18 or same_question:
                pairs.append(
                    {
                        "pair_id": slug(f"{a['candidate_id']}__{b['candidate_id']}", "pair"),
                        "a_candidate_id": a["candidate_id"],
                        "b_candidate_id": b["candidate_id"],
                        "shared_card_ids": shared_cards,
                        "title_similarity": round(title_sim, 4),
                        "text_similarity": round(text_sim, 4),
                        "same_question": same_question,
                        "recall_score": round(score, 4),
                        "reason": "shared card, same question, or lexical similarity",
                    }
                )
    pairs.sort(key=lambda row: (-row["recall_score"], row["a_candidate_id"], row["b_candidate_id"]))
    return pairs[:limit]


def slim_candidate(candidate: dict[str, Any], edges_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    edges = [edges_by_id[eid] for eid in candidate.get("source_edge_ids") or [] if eid in edges_by_id]
    return {
        "candidate_id": candidate.get("candidate_id"),
        "question_id": candidate.get("question_id"),
        "title": candidate.get("title"),
        "teaching_focus": candidate.get("teaching_focus"),
        "exam_intent": candidate.get("exam_intent"),
        "source_card_ids": candidate.get("source_card_ids"),
        "option_roles": candidate.get("option_roles"),
        "evidence": [
            {
                "option": edge.get("option"),
                "option_text": edge.get("option_text"),
                "is_correct_answer": edge.get("is_correct_answer"),
                "card_id": edge.get("canonical_card_id"),
                "knowledge": compact(edge.get("knowledge"), 180),
                "quote": compact(edge.get("quote"), 220),
                "chapter_path": edge.get("chapter_path"),
            }
            for edge in edges
        ],
    }


class UnionFind:
    def __init__(self, items: list[str]) -> None:
        self.parent = {item: item for item in items}

    def find(self, item: str) -> str:
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]

    def union(self, a: str, b: str) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def groups(self) -> list[list[str]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for item in self.parent:
            grouped[self.find(item)].append(item)
        return list(grouped.values())


def build_exam_points(
    groups: list[list[str]],
    candidates_by_id: dict[str, dict[str, Any]],
    edges_by_id: dict[str, dict[str, Any]],
    title_results: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    points = []
    for index, group in enumerate(groups, start=1):
        members = [candidates_by_id[cid] for cid in group]
        group_key = slug("__".join(sorted(group)), "group")
        title_payload = title_results.get(group_key) or {}
        source_edge_ids = []
        source_card_ids = []
        linked_question_ids = []
        linked_options = []
        for candidate in members:
            source_edge_ids.extend(candidate.get("source_edge_ids") or [])
            source_card_ids.extend(candidate.get("source_card_ids") or [])
        source_edge_ids = sorted(set(source_edge_ids))
        source_card_ids = sorted(set(source_card_ids))
        for edge_id in source_edge_ids:
            edge = edges_by_id.get(edge_id)
            if not edge:
                continue
            linked_question_ids.append(edge.get("question_id"))
            linked_options.append(
                {
                    "question_id": edge.get("question_id"),
                    "option": edge.get("option"),
                    "option_text": edge.get("option_text"),
                    "is_correct_answer": edge.get("is_correct_answer"),
                    "card_id": edge.get("canonical_card_id"),
                    "edge_role": edge.get("edge_role"),
                }
            )
        linked_question_ids = sorted(set(qid for qid in linked_question_ids if qid))
        first = members[0]
        title = title_payload.get("title") or first.get("title") or f"图谱考点 {index}"
        points.append(
            {
                "id": slug(f"gep_{index}_{title}", f"gep_{index}"),
                "title": title,
                "teaching_object_kind": "exam_point",
                "is_exam_point": True,
                "is_high_frequency": len(linked_question_ids) >= 3,
                "linked_question_ids": linked_question_ids,
                "linked_question_count": len(linked_question_ids),
                "source_edge_ids": source_edge_ids,
                "source_card_ids": source_card_ids,
                "option_bindings": linked_options,
                "member_candidate_ids": sorted(group),
                "teaching_focus": title_payload.get("teaching_focus") or first.get("teaching_focus") or "",
                "reason": title_payload.get("reason") or "由图谱化考点候选合并生成。",
                "confidence": title_payload.get("confidence") or first.get("confidence") or "medium",
                "generation_source": "graph_exam_point_trial",
                "updated_at": now(),
            }
        )
    points.sort(key=lambda point: (-point["linked_question_count"], point["title"]))
    return points


def build_report(
    model: str,
    selected_items: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    validation_issues: list[dict[str, Any]],
    merge_pairs: list[dict[str, Any]],
    merge_decisions: list[dict[str, Any]],
    exam_points: list[dict[str, Any]],
) -> str:
    lines = [
        "# 图谱化考点提取五题试跑报告",
        "",
        f"- 生成时间：{now()}",
        f"- 模型：{model}",
        "- 思考模式：未启用 reasoner / reasoning 参数",
        f"- 题目数：{len(selected_items)}",
        f"- 选项证据边：{len(edges)}",
        f"- 缺依据/回表失败：{len(gaps)}",
        f"- 考点候选：{len(candidates)}",
        f"- 候选合并对：{len(merge_pairs)}",
        f"- LLM 合并判断：{len(merge_decisions)}",
        f"- 合并后考点：{len(exam_points)}",
        f"- 高频考点：{sum(1 for point in exam_points if point.get('is_high_frequency'))}",
        f"- 校验问题：{len(validation_issues)}",
        "",
        "## 合并后考点",
        "",
    ]
    for point in exam_points:
        lines += [
            f"### {point['title']}",
            "",
            f"- 题目数：{point.get('linked_question_count')}",
            f"- 题目：{', '.join(point.get('linked_question_ids') or [])}",
            f"- 句卡：{', '.join(point.get('source_card_ids') or [])}",
            f"- 高频：{'是' if point.get('is_high_frequency') else '否'}",
            f"- 教学焦点：{point.get('teaching_focus') or ''}",
            f"- 理由：{point.get('reason') or ''}",
            "",
            "选项连线：",
        ]
        for binding in point.get("option_bindings") or []:
            correct_text = "正确项" if binding.get("is_correct_answer") else "错误项"
            lines.append(
                f"- {binding.get('question_id')} {binding.get('option')}（{correct_text}）："
                f"{binding.get('option_text')} -> {binding.get('card_id')}"
            )
        lines.append("")
    if validation_issues:
        lines += ["## 校验问题", ""]
        for issue in validation_issues:
            lines.append(f"- {issue.get('question_id')}: {', '.join(issue.get('issues') or [])}")
        lines.append("")
    if gaps:
        lines += ["## 缺依据/回表失败", ""]
        for gap in gaps[:50]:
            lines.append(
                f"- {gap.get('question_id')} {gap.get('option')} {gap.get('original_card_id')} -> "
                f"{gap.get('canonical_card_id')}: {gap.get('reason')}"
            )
    return "\n".join(lines) + "\n"


def run(
    limit: int,
    ids: list[str] | None,
    model_arg: str | None,
    out_name: str,
    include_teacher_explanation: bool = False,
) -> dict[str, Any]:
    questions_payload = read_json(DATA_DIR / "questions.json")
    option_evidence = read_json(DATA_DIR / "option_evidence_map.json")
    cards = normalize_cards(read_json(DATA_DIR / "cards_v6_sentence.json"))
    cards_by_id = {card["card_id"]: card for card in cards if card.get("card_id")}
    questions = questions_payload.get("questions") or []
    questions_by_id = {question["id"]: question for question in questions if question.get("id")}
    selected_items = select_items(option_evidence, ids, limit)

    out_root = WORKSPACE_DIR
    intermediate_dir = out_root / "intermediate" / out_name
    outputs_dir = out_root / "outputs" / out_name
    reports_dir = out_root / "reports" / out_name

    input_manifest = {
        "generated_at": now(),
        "source_assets": {
            "questions": str(DATA_DIR / "questions.json"),
            "option_evidence_map": str(DATA_DIR / "option_evidence_map.json"),
            "cards_v6_sentence": str(DATA_DIR / "cards_v6_sentence.json"),
            "card_page_map_v6": str(PAGE_MAP_PATH),
        },
        "selected_question_ids": [item.get("question_id") for item in selected_items],
        "note": "本试跑只读取正式资产，不写回正式前端数据。",
    }
    write_json(out_root / "inputs" / f"{out_name}_input_manifest.json", input_manifest)

    all_edges = []
    gaps = []
    packs = []
    for item in selected_items:
        qid = item.get("question_id")
        question = questions_by_id.get(qid, {})
        edges, item_gaps = build_edges_for_item(item, question, cards_by_id)
        all_edges.extend(edges)
        gaps.extend(item_gaps)
        packs.append(build_question_pack(item, question, edges, include_teacher_explanation=include_teacher_explanation))

    write_json(outputs_dir / "option_evidence_edges.json", {"generated_at": now(), "items": all_edges})
    write_json(intermediate_dir / "question_packs.json", {"generated_at": now(), "items": packs})
    write_json(reports_dir / "evidence_gaps.json", {"generated_at": now(), "items": gaps})

    client, model = client_from_env(model_arg)
    candidate_prompt = (out_root / "prompts" / "candidate_generation.md").read_text(encoding="utf-8")
    merge_prompt = (out_root / "prompts" / "merge_judge.md").read_text(encoding="utf-8")
    title_prompt = (out_root / "prompts" / "group_title.md").read_text(encoding="utf-8")

    raw_candidate_rows = []
    candidate_outputs = []
    validation_issues = []
    candidates = []
    for pack in packs:
        parsed, raw = call_json(client, model, candidate_prompt, pack, max_tokens=3500)
        if not isinstance(parsed, dict):
            parsed = {"question_id": pack["question_id"], "exam_intent": "", "candidates": [], "rejected_edges": []}
        issues = validate_candidate_payload(parsed, pack)
        if issues:
            validation_issues.append({"question_id": pack["question_id"], "issues": issues})
        output = {
            "question_id": pack["question_id"],
            "model": model,
            "pack": pack,
            "result": parsed,
            "validation_issues": issues,
        }
        candidate_outputs.append(output)
        raw_candidate_rows.append({"question_id": pack["question_id"], "raw_response": raw})
        for idx, candidate in enumerate(parsed.get("candidates") or [], start=1):
            source_edge_ids = [eid for eid in candidate.get("source_edge_ids") or []]
            candidate_id = slug(f"cand_{pack['question_id']}_{idx}_{candidate.get('title')}", f"cand_{pack['question_id']}_{idx}")
            candidate["candidate_id"] = candidate_id
            candidate["question_id"] = pack["question_id"]
            candidate["exam_intent"] = parsed.get("exam_intent") or ""
            candidate["source_edge_ids"] = source_edge_ids
            candidates.append(candidate)

    edges_by_id = {edge["edge_id"]: edge for edge in all_edges}
    candidates_by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
    merge_pairs = recall_merge_pairs(candidates, edges_by_id)

    raw_merge_rows = []
    merge_decisions = []
    for pair in merge_pairs:
        payload = {
            "pair": pair,
            "candidate_a": slim_candidate(candidates_by_id[pair["a_candidate_id"]], edges_by_id),
            "candidate_b": slim_candidate(candidates_by_id[pair["b_candidate_id"]], edges_by_id),
        }
        parsed, raw = call_json(client, model, merge_prompt, payload, max_tokens=1600)
        if not isinstance(parsed, dict):
            parsed = {"merge": False, "confidence": "low", "reason": "LLM output invalid", "merged_title": ""}
        decision = {**pair, "model": model, "decision": parsed}
        merge_decisions.append(decision)
        raw_merge_rows.append({"pair_id": pair["pair_id"], "raw_response": raw})

    uf = UnionFind([candidate["candidate_id"] for candidate in candidates])
    for decision in merge_decisions:
        result = decision.get("decision") or {}
        if result.get("merge") is True and result.get("confidence") in {"high", "medium"}:
            uf.union(decision["a_candidate_id"], decision["b_candidate_id"])
    groups = uf.groups()

    title_results = {}
    raw_title_rows = []
    for group in groups:
        group_key = slug("__".join(sorted(group)), "group")
        payload = {
            "group_id": group_key,
            "candidates": [slim_candidate(candidates_by_id[cid], edges_by_id) for cid in group],
        }
        parsed, raw = call_json(client, model, title_prompt, payload, max_tokens=1400)
        if not isinstance(parsed, dict):
            parsed = {}
        title_results[group_key] = parsed
        raw_title_rows.append({"group_id": group_key, "raw_response": raw})

    exam_points = build_exam_points(groups, candidates_by_id, edges_by_id, title_results)

    write_json(outputs_dir / "exam_point_candidates.json", {"generated_at": now(), "items": candidates})
    write_json(intermediate_dir / "candidate_generation_outputs.json", {"generated_at": now(), "items": candidate_outputs})
    write_json(intermediate_dir / "merge_pair_candidates.json", {"generated_at": now(), "items": merge_pairs})
    write_json(intermediate_dir / "merge_decisions.json", {"generated_at": now(), "items": merge_decisions})
    write_json(outputs_dir / "exam_points_graph_preview.json", {"generated_at": now(), "items": exam_points})
    write_json(reports_dir / "evidence_gaps.json", {"generated_at": now(), "items": gaps})
    write_json(reports_dir / "validation_issues.json", {"generated_at": now(), "items": validation_issues})
    write_jsonl(intermediate_dir / "raw_candidate_responses.jsonl", raw_candidate_rows)
    write_jsonl(intermediate_dir / "raw_merge_responses.jsonl", raw_merge_rows)
    write_jsonl(intermediate_dir / "raw_title_responses.jsonl", raw_title_rows)

    report = build_report(
        model,
        selected_items,
        all_edges,
        gaps,
        candidates,
        validation_issues,
        merge_pairs,
        merge_decisions,
        exam_points,
    )
    (reports_dir / "build_report.md").write_text(report, encoding="utf-8")

    manual_lines = [
        "# 人工复核清单",
        "",
        "## 低置信或拒绝合并",
        "",
    ]
    for decision in merge_decisions:
        result = decision.get("decision") or {}
        if result.get("merge") is True and result.get("confidence") == "low":
            manual_lines.append(
                f"- 低置信合并：{decision['a_candidate_id']} <-> {decision['b_candidate_id']}：{result.get('reason', '')}"
            )
        elif result.get("merge") is False and decision.get("recall_score", 0) >= 0.5:
            manual_lines.append(
                f"- 高召回分但拒绝合并：{decision['a_candidate_id']} <-> {decision['b_candidate_id']}：{result.get('reason', '')}"
            )
    if len(manual_lines) == 4:
        manual_lines.append("- 暂无。")
    (reports_dir / "manual_review.md").write_text("\n".join(manual_lines) + "\n", encoding="utf-8")

    summary = {
        "out_name": out_name,
        "model": model,
        "teacher_explanation_included": include_teacher_explanation,
        "questions": len(selected_items),
        "edges": len(all_edges),
        "gaps": len(gaps),
        "candidates": len(candidates),
        "merge_pairs": len(merge_pairs),
        "merge_decisions": len(merge_decisions),
        "exam_points": len(exam_points),
        "high_frequency_points": sum(1 for point in exam_points if point.get("is_high_frequency")),
        "validation_issue_questions": len(validation_issues),
        "report": str(reports_dir / "build_report.md"),
    }
    write_json(reports_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run graph-based exam point extraction trial.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--ids", nargs="*", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--out-name", default="trial_5q")
    parser.add_argument("--include-teacher-explanation", action="store_true")
    args = parser.parse_args()
    summary = run(
        args.limit,
        args.ids,
        args.model,
        args.out_name,
        include_teacher_explanation=args.include_teacher_explanation,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
