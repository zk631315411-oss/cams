from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DEFAULT_SOURCE_DIR = HERE / "work" / "preview_v10_full828"
DEFAULT_OUT_DIR = HERE / "work" / "preview_v13_relation_review"
QUESTIONS_FILE = ROOT / "data" / "source" / "questions.json"

TRACE_ACTIONS = {
    "parent_child_review_trace",
    "sibling_under_parent_review_trace",
}

DEFAULT_PRIORITY_PAIR_IDS = [
    "v6s_N02777__v6s_N02778",
    "v6s_N04712__v6s_N04713",
    "v6s_N04713__v6s_N04714",
    "v6s_N00477__v6s_N00476",
    "v6s_N00755__v6s_N00754",
]

ALLOWED_DECISIONS = {
    "confirmed_parent_child",
    "confirmed_sibling",
    "merge_same_point",
    "keep_separate",
    "needs_review",
    "direction_reversed",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else HERE / path


def source_dir() -> Path:
    raw = os.getenv("PREVIEW_V13_SOURCE_DIR", "").strip().strip('"')
    return resolve_path(raw) if raw else DEFAULT_SOURCE_DIR


def out_dir() -> Path:
    raw = os.getenv("PREVIEW_V13_OUT_DIR", "").strip().strip('"')
    return resolve_path(raw) if raw else DEFAULT_OUT_DIR


def batch_name() -> str:
    raw = os.getenv("PREVIEW_V13_BATCH_NAME", "").strip()
    value = re.sub(r"[^A-Za-z0-9_-]+", "", raw)
    if value:
        return value
    return f"start{env_int('PREVIEW_V13_START', 0)}_limit{env_int('PREVIEW_V13_LIMIT', 20)}"


def compact(text: Any, limit: int = 260) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)] + "..."


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(v for v in values if v))


def load_questions() -> dict[str, dict[str, Any]]:
    payload = read_json(QUESTIONS_FILE)
    items = payload.get("questions", payload) if isinstance(payload, dict) else payload
    return {str(item["id"]): item for item in items}


def build_card_index(points: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    edge_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for edge in edges:
        card_id = str(edge.get("card_id") or "")
        if not card_id:
            continue
        if edge.get("role"):
            edge_counts[card_id][str(edge["role"])] += 1
        if edge.get("key_is_correct") is True:
            edge_counts[card_id]["correct_option"] += 1
        elif edge.get("key_is_correct") is False:
            edge_counts[card_id]["wrong_option"] += 1

    for point in points:
        quotes = {
            str(item.get("card_id")): item.get("quote")
            for item in point.get("evidence_quotes", [])
            if item.get("card_id")
        }
        for card_id in point.get("card_ids", []):
            card_id = str(card_id)
            current = index.setdefault(
                card_id,
                {
                    "card_id": card_id,
                    "exam_point_ids": [],
                    "titles": [],
                    "quotes": [],
                    "question_ids": [],
                    "core_question_ids": [],
                    "contrast_question_ids": [],
                    "sections": Counter(),
                    "point_types": Counter(),
                    "tags": Counter(),
                },
            )
            current["exam_point_ids"].append(str(point.get("id") or ""))
            if point.get("title"):
                current["titles"].append(str(point["title"]))
            quote = quotes.get(card_id)
            if quote:
                current["quotes"].append(str(quote))
            current["question_ids"].extend(str(qid) for qid in point.get("question_ids", []))
            current["core_question_ids"].extend(str(qid) for qid in point.get("core_question_ids", []))
            current["contrast_question_ids"].extend(str(qid) for qid in point.get("contrast_question_ids", []))
            for section, count in (point.get("sections") or {}).items():
                current["sections"][str(section)] += int(count or 0)
            if point.get("point_type"):
                current["point_types"][str(point["point_type"])] += 1
            for tag in point.get("tags", []):
                current["tags"][str(tag)] += 1

    for card_id, item in index.items():
        item["exam_point_ids"] = unique(item["exam_point_ids"])
        item["question_ids"] = unique(item["question_ids"])
        item["core_question_ids"] = unique(item["core_question_ids"])
        item["contrast_question_ids"] = unique(item["contrast_question_ids"])
        item["title"] = compact(item["titles"][0] if item["titles"] else "", 180)
        item["quote"] = compact(item["quotes"][0] if item["quotes"] else "", 500)
        item["question_count"] = len(item["question_ids"])
        item["core_question_count"] = len(item["core_question_ids"])
        item["contrast_question_count"] = len(item["contrast_question_ids"])
        item["sections"] = dict(item["sections"].most_common())
        item["point_types"] = dict(item["point_types"])
        item["tags"] = list(item["tags"].keys())
        item["edge_role_counts"] = dict(edge_counts.get(card_id, Counter()))
        del item["titles"]
        del item["quotes"]
    return index


def build_edges_by_card(edges: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_card: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        card_id = str(edge.get("card_id") or "")
        if card_id:
            by_card[card_id].append(edge)
    return by_card


def edge_view(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "option": edge.get("option"),
        "option_text": compact(edge.get("option_text"), 160),
        "role": edge.get("role"),
        "key_is_correct": edge.get("key_is_correct"),
        "judgement": edge.get("judgement"),
        "evidence_grade": edge.get("evidence_grade"),
        "evidence_status": edge.get("evidence_status"),
        "support_type": edge.get("support_type"),
        "focus_type": edge.get("focus_type"),
        "quote": compact(edge.get("quote"), 220),
    }


def question_contexts_for_pair(
    record: dict[str, Any],
    edges_by_card: dict[str, list[dict[str, Any]]],
    questions: dict[str, dict[str, Any]],
    max_contexts: int = 4,
) -> list[dict[str, Any]]:
    card_a = str(record.get("card_a_id") or "")
    card_b = str(record.get("card_b_id") or "")
    a_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    b_by_question: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in edges_by_card.get(card_a, []):
        if edge.get("question_id"):
            a_by_question[str(edge["question_id"])].append(edge)
    for edge in edges_by_card.get(card_b, []):
        if edge.get("question_id"):
            b_by_question[str(edge["question_id"])].append(edge)

    shared_ids = sorted(set(a_by_question) & set(b_by_question))
    if not shared_ids:
        union_ids = unique(list(a_by_question)[:2] + list(b_by_question)[:2])
    else:
        union_ids = shared_ids

    contexts: list[dict[str, Any]] = []
    for question_id in union_ids[:max_contexts]:
        question = questions.get(question_id, {})
        a_edges = sorted(a_by_question.get(question_id, []), key=lambda e: str(e.get("option") or ""))
        b_edges = sorted(b_by_question.get(question_id, []), key=lambda e: str(e.get("option") or ""))
        contexts.append(
            {
                "question_id": question_id,
                "section": question.get("section"),
                "stem": compact(question.get("stem"), 320),
                "options": {key: compact(value, 120) for key, value in (question.get("options") or {}).items()},
                "answer": question.get("answer"),
                "same_question_for_both_cards": bool(a_edges and b_edges),
                "same_option_for_both_cards": bool(
                    {str(edge.get("option")) for edge in a_edges}
                    & {str(edge.get("option")) for edge in b_edges}
                ),
                "card_a_edges": [edge_view(edge) for edge in a_edges[:3]],
                "card_b_edges": [edge_view(edge) for edge in b_edges[:3]],
            }
        )
    return contexts


def ordered_relation_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    trace_records = [row for row in records if row.get("applied_action") in TRACE_ACTIONS]
    pair_filter_raw = os.getenv("PREVIEW_V13_PAIR_IDS", "").strip()
    if pair_filter_raw:
        wanted = {
            part.strip()
            for chunk in pair_filter_raw.split(";")
            for part in chunk.split(",")
            if part.strip()
        }
        trace_records = [row for row in trace_records if row.get("pair_id") in wanted]

    by_pair = {row.get("pair_id"): row for row in trace_records}
    priority = [
        by_pair[pair_id]
        for pair_id in DEFAULT_PRIORITY_PAIR_IDS
        if pair_id in by_pair
    ]
    used = {row.get("pair_id") for row in priority}
    buckets: dict[str, list[dict[str, Any]]] = {
        action: []
        for action in sorted(TRACE_ACTIONS)
    }
    for row in trace_records:
        if row.get("pair_id") in used:
            continue
        action = str(row.get("applied_action") or "")
        if action in buckets:
            buckets[action].append(row)
    for rows in buckets.values():
        rows.sort(key=lambda row: (-int(row.get("score") or 0), str(row.get("pair_id") or "")))

    # Interleave buckets so small probes exercise both parent-child and sibling traces.
    interleaved: list[dict[str, Any]] = []
    while any(buckets.values()):
        for action in ("parent_child_review_trace", "sibling_under_parent_review_trace"):
            rows = buckets.get(action) or []
            if rows:
                interleaved.append(rows.pop(0))

    ordered = priority + interleaved
    return ordered


def selected_relation_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = ordered_relation_records(records)
    start = max(0, env_int("PREVIEW_V13_START", 0))
    limit = max(1, env_int("PREVIEW_V13_LIMIT", 20))
    return ordered[start : start + limit]


def build_review_items(
    records: list[dict[str, Any]],
    card_index: dict[str, dict[str, Any]],
    edges_by_card: dict[str, list[dict[str, Any]]],
    questions: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        card_a_id = str(record.get("card_a_id") or "")
        card_b_id = str(record.get("card_b_id") or "")
        source_direction = None
        if record.get("source_draft_label") == "parent_child":
            source_direction = {
                "parent_card_id": record.get("parent_card_id"),
                "child_card_id": record.get("child_card_id"),
                "direction_confidence": record.get("direction_confidence"),
                "direction_method": record.get("direction_method"),
            }
        items.append(
            {
                "review_id": f"V13RR-{index:04d}",
                "pair_id": record.get("pair_id"),
                "source_record": {
                    "decision_id": record.get("decision_id"),
                    "candidate_type": record.get("candidate_type"),
                    "score": record.get("score"),
                    "source_draft_label": record.get("source_draft_label"),
                    "source_draft_confidence": record.get("source_draft_confidence"),
                    "source_draft_rationale": record.get("source_draft_rationale"),
                    "source_draft_risk_flags": record.get("source_draft_risk_flags", []),
                    "applied_action": record.get("applied_action"),
                    "skip_reason": record.get("skip_reason"),
                    "context_scope": record.get("context_scope"),
                    "reasons": record.get("reasons", []),
                    "source_direction": source_direction,
                },
                "card_a": card_index.get(card_a_id, {"card_id": card_a_id, "missing": True}),
                "card_b": card_index.get(card_b_id, {"card_id": card_b_id, "missing": True}),
                "question_contexts": question_contexts_for_pair(record, edges_by_card, questions),
                "allowed_decisions": sorted(ALLOWED_DECISIONS),
                "review_instruction": (
                    "Judge the relation between the two textbook sentence cards. "
                    "Do not create a parent-child relation from semantic similarity, same question, or high frequency alone. "
                    "Parent-child requires explicit textbook structure in the quoted text."
                ),
            }
        )
    return items


def expected_schema_payload(batch: str) -> dict[str, Any]:
    return {
        "schema_version": "preview_v13_relation_review_decisions",
        "batch_name": batch,
        "llm_or_reviewer": "subagent_or_llm_name",
        "decisions": [
            {
                "review_id": "V13RR-0001",
                "pair_id": "v6s_N00000__v6s_N00001",
                "decision_label": "confirmed_parent_child | confirmed_sibling | merge_same_point | keep_separate | needs_review | direction_reversed",
                "confidence": "high | medium | low",
                "parent_card_id": "required for confirmed_parent_child or direction_reversed; otherwise null",
                "child_card_id": "required for confirmed_parent_child or direction_reversed; otherwise null",
                "proposed_parent_title": "optional short title for confirmed_sibling; otherwise null",
                "rationale": "one or two sentences, cite concrete quote evidence",
                "evidence_card_ids": ["card ids actually used"],
                "question_signal_used": "none | shared_question | same_option | contrast_pair",
                "risk_flags": ["optional concise flags"],
                "needs_human_reason": "required when decision_label is needs_review; otherwise null",
            }
        ],
    }


def prompt_text(batch: str, input_file_name: str) -> str:
    return f"""# Preview v13 关系复核任务

你是 CAMS 考点体系的关系复核员。请读取 `{input_file_name}`，只判断每条记录中两张教材句卡之间的关系。

## 目标

把 v10 strict 模式保留下来的 `parent_child_review_trace` 和 `sibling_under_parent_review_trace` 做二次判断。判断结果只用于关系确认，不允许新增不存在于输入中的句卡，不允许自由发明新考点。

## 可选 decision_label

- `merge_same_point`：两张句卡表达同一原子知识点，属于重复、同义改写或同一事实的完整/缩写版本。
- `confirmed_parent_child`：一张句卡是教材中的上位标题、定义、规则、清单或总述，另一张是其明确展开、条款、步骤、例子或适用细节。必须给出 `parent_card_id` 和 `child_card_id`。
- `direction_reversed`：可以确认父子关系，但输入里推断的父子方向反了。必须给出修正后的 `parent_card_id` 和 `child_card_id`。
- `confirmed_sibling`：两张句卡是同一上位教材主题下的并列子点，不应合并，也不能互为父子。可以给一个很短的 `proposed_parent_title`。
- `keep_separate`：相关性不足，或只是同题/同选项/语义相近导致的召回，不能进入结构关系。
- `needs_review`：材料不足、方向不清、跨制度/跨场景容易误合并，需要人工判断。

## 硬约束

1. 不要因为“同一题召回”“同一选项召回”“高频考点吸收”就判父子。
2. 不要因为向量语义相近就判同一考点；必须回到两张句卡 quote。
3. 父子关系必须能从教材原文 quote 看到结构信号，例如标题-细则、定义-机制、总述-列项、规则-适用条款。
4. 如果两张卡属于不同国家/机构/法规/案例/名单，即使词很像，也优先 `keep_separate` 或 `needs_review`。
5. 错误项/辨析题共同召回的卡，通常更可能是 `confirmed_sibling` 或 `keep_separate`，除非 quote 明确给出父子结构。
6. 输出必须是严格 JSON，符合 `{batch}` 的 expected schema，不要写 Markdown 解释。

## 输出

请按 `expected_output_schema_{batch}.json` 输出完整 JSON。每条输入必须有且只有一条 decision。
"""


def build_input_payload(
    items: list[dict[str, Any]],
    source: Path,
    batch: str,
    start: int | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    action_counts = Counter(item["source_record"].get("applied_action") for item in items)
    label_counts = Counter(item["source_record"].get("source_draft_label") for item in items)
    return {
        "schema_version": "preview_v13_relation_review_input",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "llm_used_to_create_this_file": False,
        "batch_name": batch,
        "source_dir": str(source),
        "selection_policy": {
            "include_applied_actions": sorted(TRACE_ACTIONS),
            "priority_pair_ids_first_if_present": DEFAULT_PRIORITY_PAIR_IDS,
            "start": env_int("PREVIEW_V13_START", 0) if start is None else start,
            "limit": env_int("PREVIEW_V13_LIMIT", 20) if limit is None else limit,
        },
        "summary": {
            "item_count": len(items),
            "applied_action_counts": dict(action_counts),
            "source_draft_label_counts": dict(label_counts),
        },
        "items": items,
    }


def validate_decisions(
    input_payload: dict[str, Any],
    decisions_payload: dict[str, Any],
    allow_partial: bool = False,
) -> dict[str, Any]:
    input_by_pair = {item["pair_id"]: item for item in input_payload.get("items", [])}
    decisions = decisions_payload.get("decisions", [])
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    seen_pairs: set[str] = set()
    label_counts = Counter()
    confidence_counts = Counter()

    for idx, decision in enumerate(decisions, start=1):
        pair_id = str(decision.get("pair_id") or "")
        label = str(decision.get("decision_label") or "")
        confidence = str(decision.get("confidence") or "")
        label_counts[label] += 1
        confidence_counts[confidence] += 1
        if pair_id not in input_by_pair:
            errors.append({"index": idx, "pair_id": pair_id, "error": "pair_id_not_in_input"})
            continue
        if pair_id in seen_pairs:
            errors.append({"index": idx, "pair_id": pair_id, "error": "duplicate_pair_decision"})
        seen_pairs.add(pair_id)
        if label not in ALLOWED_DECISIONS:
            errors.append({"index": idx, "pair_id": pair_id, "error": "invalid_decision_label", "label": label})
        if confidence not in {"high", "medium", "low"}:
            errors.append({"index": idx, "pair_id": pair_id, "error": "invalid_confidence", "confidence": confidence})
        if label in {"confirmed_parent_child", "direction_reversed"}:
            parent = decision.get("parent_card_id")
            child = decision.get("child_card_id")
            item = input_by_pair[pair_id]
            valid_cards = {item["card_a"].get("card_id"), item["card_b"].get("card_id")}
            if parent not in valid_cards or child not in valid_cards or parent == child:
                errors.append({"index": idx, "pair_id": pair_id, "error": "invalid_parent_child_ids"})
        if label == "needs_review" and not decision.get("needs_human_reason"):
            warnings.append({"index": idx, "pair_id": pair_id, "warning": "needs_review_without_reason"})
        if label == "confirmed_sibling" and not decision.get("proposed_parent_title"):
            warnings.append({"index": idx, "pair_id": pair_id, "warning": "confirmed_sibling_without_parent_title"})

    missing = sorted(set(input_by_pair) - seen_pairs)
    for pair_id in missing:
        target = warnings if allow_partial else errors
        target.append({"pair_id": pair_id, "error": "missing_decision", "allow_partial": allow_partial})

    return {
        "input_count": len(input_by_pair),
        "decision_count": len(decisions),
        "allow_partial": allow_partial,
        "missing_count": len(missing),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "decision_label_counts": dict(label_counts),
        "confidence_counts": dict(confidence_counts),
    }


def question_signal_used(item: dict[str, Any]) -> str:
    contexts = item.get("question_contexts") or []
    if any(ctx.get("same_option_for_both_cards") for ctx in contexts):
        return "same_option"
    if any(ctx.get("same_question_for_both_cards") for ctx in contexts):
        return "shared_question"
    return "none"


def baseline_decision(item: dict[str, Any]) -> dict[str, Any]:
    source = item.get("source_record") or {}
    risk_flags = set(source.get("source_draft_risk_flags") or [])
    source_label = source.get("source_draft_label")
    source_direction = source.get("source_direction") or {}
    pair_id = item.get("pair_id")
    card_a_id = item.get("card_a", {}).get("card_id")
    card_b_id = item.get("card_b", {}).get("card_id")
    evidence_ids = [card_a_id, card_b_id]
    signal = question_signal_used(item)

    parent_like_flags = {
        "explicit_structure",
        "heading_detail",
        "definition_mechanism",
        "priority_includes_detail",
        "general_specific",
    }

    if source_label == "parent_child" and risk_flags & parent_like_flags:
        parent = source_direction.get("parent_card_id")
        child = source_direction.get("child_card_id")
        if parent in evidence_ids and child in evidence_ids and parent != child:
            return {
                "review_id": item.get("review_id"),
                "pair_id": pair_id,
                "decision_label": "confirmed_parent_child",
                "confidence": "medium",
                "parent_card_id": parent,
                "child_card_id": child,
                "proposed_parent_title": None,
                "rationale": "Baseline rule: the source trace carries explicit textbook-structure flags, so this pair is provisionally treated as parent-child pending LLM/human review.",
                "evidence_card_ids": evidence_ids,
                "question_signal_used": signal,
                "risk_flags": ["baseline_not_final", *sorted(risk_flags)],
                "needs_human_reason": None,
            }

    if source_label == "sibling_under_parent" and "parallel_enumeration" in risk_flags:
        return {
            "review_id": item.get("review_id"),
            "pair_id": pair_id,
            "decision_label": "confirmed_sibling",
            "confidence": "medium",
            "parent_card_id": None,
            "child_card_id": None,
            "proposed_parent_title": "同一教材主题下的并列子点",
            "rationale": "Baseline rule: the source trace marks parallel enumeration, so the pair is provisionally treated as sibling sub-points, not merge or parent-child.",
            "evidence_card_ids": evidence_ids,
            "question_signal_used": signal,
            "risk_flags": ["baseline_not_final", *sorted(risk_flags)],
            "needs_human_reason": None,
        }

    return {
        "review_id": item.get("review_id"),
        "pair_id": pair_id,
        "decision_label": "needs_review",
        "confidence": "low",
        "parent_card_id": None,
        "child_card_id": None,
        "proposed_parent_title": None,
        "rationale": "Baseline rule: the deterministic signal is not strong enough to confirm merge, parent-child, or sibling relation.",
        "evidence_card_ids": evidence_ids,
        "question_signal_used": signal,
        "risk_flags": ["baseline_not_final", *sorted(risk_flags)],
        "needs_human_reason": "Needs subagent/LLM or human review before materialization.",
    }


def write_baseline_decisions() -> tuple[Path, dict[str, Any]]:
    out = out_dir()
    batch = batch_name()
    input_path = out / f"relation_review_input_{batch}.json"
    if not input_path.exists():
        _, _ = build_batch()
    input_payload = read_json(input_path)
    decisions_payload = {
        "schema_version": "preview_v13_relation_review_decisions",
        "batch_name": batch,
        "llm_or_reviewer": "deterministic_baseline_not_final",
        "decisions": [baseline_decision(item) for item in input_payload.get("items", [])],
    }
    decisions_path = out / f"relation_review_decisions_{batch}_baseline.json"
    write_json(decisions_path, decisions_payload)
    return decisions_path, decisions_payload


def merge_decision_payloads(decision_files: list[Path], batch: str) -> tuple[Path, dict[str, Any]]:
    out = out_dir()
    merged_decisions: list[dict[str, Any]] = []
    seen_pairs: set[str] = set()
    source_files: list[str] = []
    reviewers: list[str] = []
    duplicates: list[str] = []
    for path in decision_files:
        payload = read_json(path)
        source_files.append(str(path))
        if payload.get("llm_or_reviewer"):
            reviewers.append(str(payload["llm_or_reviewer"]))
        for decision in payload.get("decisions", []):
            pair_id = str(decision.get("pair_id") or "")
            if pair_id in seen_pairs:
                duplicates.append(pair_id)
                continue
            seen_pairs.add(pair_id)
            merged_decisions.append(decision)
    merged_payload = {
        "schema_version": "preview_v13_relation_review_decisions",
        "batch_name": batch,
        "llm_or_reviewer": "merged:" + ",".join(unique(reviewers)),
        "source_files": source_files,
        "duplicate_pair_ids_skipped": duplicates,
        "decisions": merged_decisions,
    }
    path = out / f"relation_review_decisions_{batch}_merged.json"
    write_json(path, merged_payload)
    return path, merged_payload


def report_text(batch: str, input_payload: dict[str, Any], validation: dict[str, Any] | None = None) -> str:
    lines = [
        f"# Preview v13 relation review - {batch}",
        "",
        f"- created_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- input items: {input_payload['summary']['item_count']}",
        f"- source actions: {input_payload['summary']['applied_action_counts']}",
        f"- source labels: {input_payload['summary']['source_draft_label_counts']}",
        "",
        "## Sample pairs",
    ]
    for item in input_payload.get("items", [])[:8]:
        lines.extend(
            [
                "",
                f"### {item['pair_id']}",
                f"- source: {item['source_record'].get('source_draft_label')} / {item['source_record'].get('applied_action')} / confidence={item['source_record'].get('source_draft_confidence')}",
                f"- card_a: {item['card_a'].get('card_id')} | {compact(item['card_a'].get('quote'), 120)}",
                f"- card_b: {item['card_b'].get('card_id')} | {compact(item['card_b'].get('quote'), 120)}",
                f"- shared contexts: {len([ctx for ctx in item.get('question_contexts', []) if ctx.get('same_question_for_both_cards')])}",
            ]
        )
    if validation is not None:
        lines.extend(
            [
                "",
                "## Decision validation",
                "",
                f"- valid: {validation['valid']}",
                f"- input_count: {validation['input_count']}",
                f"- decision_count: {validation['decision_count']}",
                f"- decision_label_counts: {validation['decision_label_counts']}",
                f"- confidence_counts: {validation['confidence_counts']}",
                f"- errors: {len(validation['errors'])}",
                f"- warnings: {len(validation['warnings'])}",
            ]
        )
        for error in validation["errors"][:10]:
            lines.append(f"  - error: {error}")
        for warning in validation["warnings"][:10]:
            lines.append(f"  - warning: {warning}")
    return "\n".join(lines) + "\n"


def build_batch() -> tuple[Path, dict[str, Any]]:
    src = source_dir()
    out = out_dir()
    batch = batch_name()
    records = read_jsonl(src / "relation_judgement_records.jsonl")
    points_payload = read_json(src / "exam_point_system_full828.json")
    edges_payload = read_json(src / "exam_point_question_card_edges.json")
    points = points_payload.get("items", [])
    edges = edges_payload.get("items", [])
    questions = load_questions()
    card_index = build_card_index(points, edges)
    edges_by_card = build_edges_by_card(edges)
    selected = selected_relation_records(records)
    items = build_review_items(selected, card_index, edges_by_card, questions)
    input_payload = build_input_payload(items, src, batch)

    input_path = out / f"relation_review_input_{batch}.json"
    schema_path = out / f"expected_output_schema_{batch}.json"
    prompt_path = out / f"relation_review_prompt_{batch}.md"
    report_path = out / f"relation_review_report_{batch}.md"
    write_json(input_path, input_payload)
    write_json(schema_path, expected_schema_payload(batch))
    write_text(prompt_path, prompt_text(batch, input_path.name))
    write_text(report_path, report_text(batch, input_payload))
    return out, input_payload


def build_batches() -> tuple[Path, dict[str, Any]]:
    src = source_dir()
    out = out_dir()
    batch_prefix = batch_name()
    records = read_jsonl(src / "relation_judgement_records.jsonl")
    points_payload = read_json(src / "exam_point_system_full828.json")
    edges_payload = read_json(src / "exam_point_question_card_edges.json")
    points = points_payload.get("items", [])
    edges = edges_payload.get("items", [])
    questions = load_questions()
    card_index = build_card_index(points, edges)
    edges_by_card = build_edges_by_card(edges)
    ordered = ordered_relation_records(records)
    size = max(1, env_int("PREVIEW_V13_BATCH_SIZE", 20))
    max_items = env_int("PREVIEW_V13_TOTAL_LIMIT", len(ordered))
    max_items = min(max_items, len(ordered))
    manifest_items: list[dict[str, Any]] = []
    for start in range(0, max_items, size):
        selected = ordered[start : min(start + size, max_items)]
        batch = f"{batch_prefix}_b{len(manifest_items) + 1:02d}"
        items = build_review_items(selected, card_index, edges_by_card, questions)
        input_payload = build_input_payload(items, src, batch, start=start, limit=size)
        input_path = out / f"relation_review_input_{batch}.json"
        schema_path = out / f"expected_output_schema_{batch}.json"
        prompt_path = out / f"relation_review_prompt_{batch}.md"
        report_path = out / f"relation_review_report_{batch}.md"
        write_json(input_path, input_payload)
        write_json(schema_path, expected_schema_payload(batch))
        write_text(prompt_path, prompt_text(batch, input_path.name))
        write_text(report_path, report_text(batch, input_payload))
        manifest_items.append(
            {
                "batch_name": batch,
                "start": start,
                "limit": size,
                "item_count": len(items),
                "input_file": str(input_path),
                "prompt_file": str(prompt_path),
                "schema_file": str(schema_path),
                "report_file": str(report_path),
                "pair_ids": [item["pair_id"] for item in items],
                "summary": input_payload["summary"],
            }
        )
    manifest = {
        "schema_version": "preview_v13_relation_review_batch_manifest",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "batch_prefix": batch_prefix,
        "batch_size": size,
        "total_available_trace_count": len(ordered),
        "total_selected_count": sum(item["item_count"] for item in manifest_items),
        "batch_count": len(manifest_items),
        "items": manifest_items,
    }
    manifest_path = out / f"relation_review_batch_manifest_{batch_prefix}.json"
    write_json(manifest_path, manifest)
    return manifest_path, manifest


def validate_batch(decisions_file: Path, allow_partial: bool = False) -> tuple[Path, dict[str, Any]]:
    out = out_dir()
    batch = batch_name()
    input_path = out / f"relation_review_input_{batch}.json"
    input_payload = read_json(input_path)
    decisions_payload = read_json(decisions_file)
    validation = validate_decisions(input_payload, decisions_payload, allow_partial=allow_partial)
    validation_path = out / f"relation_review_validation_{batch}.json"
    report_path = out / f"relation_review_report_{batch}.md"
    write_json(validation_path, validation)
    write_text(report_path, report_text(batch, input_payload, validation))
    return validation_path, validation


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and validate v13 relation review batches.")
    parser.add_argument("--decisions", help="Path to relation review decisions JSON to validate.")
    parser.add_argument(
        "--build-batches",
        action="store_true",
        help="Build multiple relation review input batches using PREVIEW_V13_BATCH_SIZE.",
    )
    parser.add_argument(
        "--merge-decisions",
        nargs="+",
        help="Merge multiple relation review decision JSON files into one merged decisions JSON.",
    )
    parser.add_argument(
        "--merged-batch-name",
        help="Batch name for --merge-decisions output. Defaults to PREVIEW_V13_BATCH_NAME or merged_decisions.",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="Allow decisions JSON to cover only part of the input batch.",
    )
    parser.add_argument(
        "--baseline-decisions",
        action="store_true",
        help="Write deterministic non-final baseline decisions for schema/pipeline testing.",
    )
    args = parser.parse_args()
    if args.build_batches:
        path, manifest = build_batches()
        print(f"batch manifest: {path}")
        print(json.dumps(
            {
                "batch_prefix": manifest["batch_prefix"],
                "batch_count": manifest["batch_count"],
                "total_selected_count": manifest["total_selected_count"],
                "batch_size": manifest["batch_size"],
            },
            ensure_ascii=False,
            indent=2,
        ))
        return
    if args.merge_decisions:
        batch = args.merged_batch_name or os.getenv("PREVIEW_V13_BATCH_NAME", "").strip() or "merged_decisions"
        path, payload = merge_decision_payloads([resolve_path(item) for item in args.merge_decisions], batch)
        print(f"merged decisions: {path}")
        print(json.dumps(
            {
                "decision_count": len(payload["decisions"]),
                "duplicate_pair_ids_skipped": payload["duplicate_pair_ids_skipped"],
                "source_files": payload["source_files"],
            },
            ensure_ascii=False,
            indent=2,
        ))
        return
    if args.baseline_decisions:
        path, payload = write_baseline_decisions()
        print(f"baseline decisions: {path}")
        print(json.dumps(Counter(row["decision_label"] for row in payload["decisions"]), ensure_ascii=False, indent=2))
        return
    if args.decisions:
        path, validation = validate_batch(resolve_path(args.decisions), allow_partial=args.allow_partial)
        print(f"validated: {path}")
        print(json.dumps(validation, ensure_ascii=False, indent=2))
        return
    out, input_payload = build_batch()
    batch = input_payload["batch_name"]
    print(f"built: {out}")
    print(f"batch: {batch}")
    print(json.dumps(input_payload["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
