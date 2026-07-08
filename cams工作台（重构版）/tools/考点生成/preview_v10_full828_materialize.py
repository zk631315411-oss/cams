from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
WORK_DIR = HERE / "work"
V1_DIR = WORK_DIR / "preview_v1"
V5_DIR = WORK_DIR / "preview_v5"
V6_DIR = WORK_DIR / "preview_v6"
OUT_DIR = WORK_DIR / "preview_v10_full828"


DEFAULT_MIN_CONFIDENCE = {
    "merge_same_point": "medium",
    "parent_child": "medium",
    "sibling_under_parent": "high",
}

DEFAULT_RELATION_APPLY_MODE = "strict"
RELATION_APPLY_MODES = {"strict", "merge_only", "legacy"}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")


def env_confidence(name: str, default: str) -> str:
    value = (os.getenv(name) or default).strip().lower()
    return value if value in {"low", "medium", "high", "off"} else default


def confidence_rank(value: str | None) -> int:
    return {"high": 3, "medium": 2, "low": 1, "off": 99}.get(str(value or "").lower(), 0)


def min_confidence(label: str) -> str:
    env_name = f"PREVIEW_V10_{label.upper()}_MIN_CONFIDENCE"
    return env_confidence(env_name, DEFAULT_MIN_CONFIDENCE[label])


def relation_apply_mode() -> str:
    value = (os.getenv("PREVIEW_V10_RELATION_APPLY_MODE") or DEFAULT_RELATION_APPLY_MODE).strip().lower()
    return value if value in RELATION_APPLY_MODES else DEFAULT_RELATION_APPLY_MODE


def passes_confidence(value: str | None, minimum: str) -> bool:
    if minimum == "off":
        return False
    return confidence_rank(value) >= confidence_rank(minimum)


def compact(text: Any, limit: int = 90) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)] + "..."


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(v for v in values if v))


def question_count_type(question_count: int) -> str:
    return "高频考点" if question_count >= 3 else "普通考点"


def normalize_for_heading(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def heading_score(card_summary: dict[str, Any]) -> int:
    text = normalize_for_heading(
        str(card_summary.get("title_placeholder") or "") + str(card_summary.get("quote") or "")
    )
    title = normalize_for_heading(str(card_summary.get("title_placeholder") or ""))
    score = 0
    if len(title) <= 55:
        score += 1
    if any(word in text for word in ("第", "条", "定义", "原则", "要求", "制度", "风险", "阶段", "清单")):
        score += 1
    if any(word in text for word in ("包括", "如下", "以下", "例如", "特别是", "分为", "本法条", "该法条")):
        score += 1
    if title.endswith(("：", ":", "。")):
        score += 1
    return score


def infer_parent_child_direction(item: dict[str, Any]) -> dict[str, Any]:
    a = item["card_a"]
    b = item["card_b"]
    title_a = str(a.get("title_placeholder") or "")
    title_b = str(b.get("title_placeholder") or "")
    quote_a = str(a.get("quote") or "")
    quote_b = str(b.get("quote") or "")

    def looks_like_short_heading(title: str, quote: str) -> bool:
        text = title + quote
        if len(title) > 90:
            return False
        if re.search(r"第\s*\d+.*条", title) or re.search(r"第\s*\d+.*项", title):
            return True
        return any(word in text for word in ("定义", "四大关键元素", "关键优先事项", "主要职责", "基本原则"))

    def looks_like_detail(title: str, quote: str) -> bool:
        text = title + quote
        return any(word in text for word in ("本法条", "该法条", "该条款", "此外", "另外", "包括", "例如", "必须", "应当", "要求"))

    a_heading = looks_like_short_heading(title_a, quote_a)
    b_heading = looks_like_short_heading(title_b, quote_b)
    a_detail = looks_like_detail(title_a, quote_a)
    b_detail = looks_like_detail(title_b, quote_b)
    if a_heading and b_detail and not b_heading:
        return {
            "parent_card_id": a["card_id"],
            "child_card_id": b["card_id"],
            "direction_confidence": "medium",
            "direction_method": "short_heading_over_detail",
            "heading_score_a": None,
            "heading_score_b": None,
        }
    if b_heading and a_detail and not a_heading:
        return {
            "parent_card_id": b["card_id"],
            "child_card_id": a["card_id"],
            "direction_confidence": "medium",
            "direction_method": "short_heading_over_detail",
            "heading_score_a": None,
            "heading_score_b": None,
        }

    score_a = heading_score(a)
    score_b = heading_score(b)
    qa = int(a.get("question_count") or 0)
    qb = int(b.get("question_count") or 0)

    if score_a != score_b:
        parent_key = "card_a" if score_a > score_b else "card_b"
        confidence = "medium" if abs(score_a - score_b) >= 2 else "low"
        method = "heading_score"
    elif qa != qb:
        parent_key = "card_a" if qa > qb else "card_b"
        confidence = "low"
        method = "question_count_tiebreaker"
    else:
        parent_key = "card_a"
        confidence = "low"
        method = "stable_pair_order_fallback"

    child_key = "card_b" if parent_key == "card_a" else "card_a"
    return {
        "parent_card_id": item[parent_key]["card_id"],
        "child_card_id": item[child_key]["card_id"],
        "direction_confidence": confidence,
        "direction_method": method,
        "heading_score_a": score_a,
        "heading_score_b": score_b,
    }


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, value: str) -> str:
        self.parent.setdefault(value, value)
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, a: str, b: str) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def merge_point_fields(cards: list[str], points_by_card: dict[str, dict[str, Any]]) -> dict[str, Any]:
    points = [points_by_card[card] for card in cards if card in points_by_card]
    raw_question_ids = unique([qid for point in points for qid in point.get("raw_question_ids", [])])
    question_ids = unique([qid for point in points for qid in point.get("question_ids", [])])
    core_question_ids = unique([qid for point in points for qid in point.get("core_question_ids", [])])
    contrast_question_ids = unique(
        [qid for point in points for qid in point.get("confusing_contrast_question_ids", [])]
    )
    needs_review_contrast_question_ids = unique(
        [qid for point in points for qid in point.get("needs_review_contrast_question_ids", [])]
    )
    tags = unique([tag for point in points for tag in point.get("tags", [])])
    if contrast_question_ids and "易错/辨析" not in tags:
        tags.append("易错/辨析")

    sections: Counter[str] = Counter()
    for point in points:
        for section, count in (point.get("sections") or {}).items():
            sections[section] += int(count or 0)

    evidence_quotes = [
        {
            "card_id": point["card_id"],
            "quote": point.get("quote") or "",
            "source_point_id": point.get("id"),
        }
        for point in points
    ]
    title_source = max(points, key=lambda point: (point.get("question_count") or 0, -len(point.get("quote") or "")))
    return {
        "title": title_source.get("title_placeholder") or title_source.get("quote") or cards[0],
        "title_status": "placeholder_from_card_quote",
        "card_ids": cards,
        "source_point_ids": [point.get("id") for point in points],
        "raw_question_ids": raw_question_ids,
        "question_ids": question_ids,
        "question_count": len(question_ids),
        "core_question_ids": core_question_ids,
        "core_question_count": len(core_question_ids),
        "contrast_question_ids": contrast_question_ids,
        "contrast_question_count": len(contrast_question_ids),
        "needs_review_contrast_question_ids": needs_review_contrast_question_ids,
        "needs_review_contrast_question_count": len(needs_review_contrast_question_ids),
        "tags": tags,
        "evidence_quotes": evidence_quotes,
        "sections": dict(sorted(sections.items())),
        "cross_chapter": any(point.get("cross_chapter") for point in points),
    }


def build_strong_edge_index(strong_edges: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for edge in strong_edges:
        card_id = edge.get("card_id")
        question_id = edge.get("question_id")
        if card_id and question_id:
            index[(card_id, question_id)].append(edge)
    return index


def build_direct_edges(
    point: dict[str, Any],
    points_by_card: dict[str, dict[str, Any]],
    strong_edges_by_card_question: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = []
    for card_id in point.get("card_ids", []):
        source = points_by_card.get(card_id)
        if not source:
            continue
        source_core_questions = set(source.get("core_question_ids", []))
        source_contrast_questions = set(source.get("confusing_contrast_question_ids", []))
        for qid in source.get("question_ids", []):
            matched_edges = strong_edges_by_card_question.get((card_id, qid), [])
            if matched_edges:
                for edge in matched_edges:
                    rows.append(
                        {
                            "exam_point_id": point["id"],
                            "edge_scope": "direct",
                            "question_id": edge.get("question_id"),
                            "section": edge.get("section"),
                            "option": edge.get("option"),
                            "option_text": edge.get("option_text"),
                            "role": edge.get("role"),
                            "key_is_correct": edge.get("key_is_correct"),
                            "judgement": edge.get("judgement"),
                            "evidence_grade": edge.get("evidence_grade"),
                            "evidence_status": edge.get("evidence_status"),
                            "focus_type": edge.get("focus_type"),
                            "card_id": card_id,
                            "quote": edge.get("quote"),
                            "support_type": edge.get("support_type"),
                            "relevance": edge.get("relevance"),
                            "question_flagged": edge.get("question_flagged"),
                            "source_point_id": source.get("id"),
                            "source_edge_key": "::".join(
                                [
                                    str(edge.get("question_id") or ""),
                                    str(edge.get("option") or ""),
                                    card_id,
                                    str(edge.get("role") or ""),
                                ]
                            ),
                        }
                    )
                continue

            roles = []
            if qid in source_core_questions:
                roles.append("core")
            if qid in source_contrast_questions:
                roles.append("contrast")
            rows.append(
                {
                    "exam_point_id": point["id"],
                    "edge_scope": "direct",
                    "question_id": qid,
                    "section": None,
                    "option": None,
                    "option_text": None,
                    "role": "+".join(roles) if roles else "unknown",
                    "key_is_correct": None,
                    "judgement": None,
                    "evidence_grade": None,
                    "evidence_status": None,
                    "focus_type": source.get("top_focus_type"),
                    "card_id": card_id,
                    "quote": source.get("quote"),
                    "support_type": source.get("card", {}).get("support_type"),
                    "relevance": source.get("card", {}).get("relevance"),
                    "question_flagged": None,
                    "source_point_id": source.get("id"),
                    "source_edge_key": None,
                }
            )
    return rows


def make_relation_record(
    idx: int,
    item: dict[str, Any],
    formal_card_ids: set[str],
    apply_mode: str,
) -> tuple[dict[str, Any], bool, str]:
    label = item.get("draft_label")
    confidence = item.get("draft_confidence")
    a = item["card_a"]["card_id"]
    b = item["card_b"]["card_id"]
    both_formal = a in formal_card_ids and b in formal_card_ids
    applied = False
    applied_action = "trace_only"
    skip_reason = ""
    extra: dict[str, Any] = {}

    if not both_formal:
        skip_reason = "one_or_both_cards_not_in_formal_828"
    elif label in {"merge_same_point", "parent_child", "sibling_under_parent"}:
        minimum = min_confidence(str(label))
        if not passes_confidence(confidence, minimum):
            skip_reason = f"below_{label}_min_confidence_{minimum}"
        elif label == "merge_same_point":
            applied = True
            applied_action = "merge_cards_into_one_exam_point"
        elif label == "parent_child":
            extra = infer_parent_child_direction(item)
            if apply_mode == "legacy":
                applied = True
                applied_action = "create_parent_child_relation"
            else:
                skip_reason = f"{apply_mode}_parent_child_requires_review"
                applied_action = "parent_child_review_trace"
        elif label == "sibling_under_parent":
            if apply_mode == "legacy":
                applied = True
                applied_action = "create_sibling_virtual_parent_candidate"
            else:
                skip_reason = f"{apply_mode}_sibling_under_parent_requires_review"
                applied_action = "sibling_under_parent_review_trace"
    elif label == "keep_separate":
        skip_reason = "keep_separate_trace"
        applied_action = "keep_separate_trace"
    else:
        skip_reason = "unknown_label_trace"

    record = {
        "decision_id": f"V10RJ-{idx:04d}",
        "record_type": "relation",
        "judgement_source": "preview_v6_structure_draft.rule",
        "pair_id": item.get("pair_id"),
        "candidate_type": item.get("candidate_type"),
        "score": item.get("score"),
        "source_draft_label": label,
        "source_draft_confidence": confidence,
        "source_draft_rationale": item.get("draft_rationale"),
        "source_draft_risk_flags": item.get("draft_risk_flags") or [],
        "context_scope": item.get("context_scope"),
        "reasons": item.get("reasons") or [],
        "card_a_id": a,
        "card_b_id": b,
        "card_a_question_count": item.get("card_a", {}).get("question_count"),
        "card_b_question_count": item.get("card_b", {}).get("question_count"),
        "applied": applied,
        "applied_action": applied_action,
        "skip_reason": skip_reason,
        "relation_apply_mode": apply_mode,
        **extra,
    }
    return record, applied, str(label or "")


def collect_descendants(item_id: str, items_by_id: dict[str, dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []

    def walk(current_id: str) -> None:
        item = items_by_id.get(current_id)
        if not item:
            return
        for child_id in item.get("children", []):
            if child_id in seen:
                continue
            seen.add(child_id)
            ordered.append(child_id)
            walk(child_id)

    walk(item_id)
    return ordered


def refresh_subtree_counts(items: list[dict[str, Any]], items_by_id: dict[str, dict[str, Any]]) -> None:
    for item in items:
        question_ids = set(item.get("question_ids", []))
        for child_id in collect_descendants(item["id"], items_by_id):
            child = items_by_id.get(child_id)
            if child:
                question_ids.update(child.get("question_ids", []))
        item["subtree_question_count"] = len(question_ids)


def materialize() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    candidate_points = read_json(V5_DIR / "all_candidate_points.json")["items"]
    relation_items = read_json(V6_DIR / "relation_draft.json")["items"]
    contrast_items = read_json(V6_DIR / "contrast_draft.json")["items"]
    strong_edges = read_json(V1_DIR / "strong_edges.json")["items"]

    formal_points = [point for point in candidate_points if int(point.get("question_count") or 0) > 0]
    review_only_points = [point for point in candidate_points if int(point.get("question_count") or 0) <= 0]
    points_by_card = {point["card_id"]: point for point in formal_points}
    formal_card_ids = set(points_by_card)
    strong_edges_by_card_question = build_strong_edge_index(strong_edges)
    apply_mode = relation_apply_mode()

    uf = UnionFind()
    for card_id in sorted(formal_card_ids):
        uf.find(card_id)

    judgement_records: list[dict[str, Any]] = []
    for idx, item in enumerate(relation_items, start=1):
        record, applied, label = make_relation_record(idx, item, formal_card_ids, apply_mode)
        if applied and label == "merge_same_point":
            uf.union(record["card_a_id"], record["card_b_id"])
        judgement_records.append(record)

    groups: dict[str, list[str]] = defaultdict(list)
    for card_id in sorted(formal_card_ids):
        groups[uf.find(card_id)].append(card_id)

    items: list[dict[str, Any]] = []
    card_to_exam_point: dict[str, str] = {}
    for idx, (_, cards) in enumerate(sorted(groups.items(), key=lambda row: row[1][0]), start=1):
        fields = merge_point_fields(cards, points_by_card)
        ep_id = f"EP10-{idx:04d}"
        item = {
            "id": ep_id,
            "title": fields["title"],
            "title_status": fields["title_status"],
            "point_type": question_count_type(fields["question_count"]),
            "is_high_frequency": fields["question_count"] >= 3,
            "tags": fields["tags"],
            "parent_id": None,
            "children": [],
            "sibling_relation_pair_ids": [],
            "card_ids": fields["card_ids"],
            "source_point_ids": fields["source_point_ids"],
            "raw_question_ids": fields["raw_question_ids"],
            "question_ids": fields["question_ids"],
            "question_count": fields["question_count"],
            "core_question_ids": fields["core_question_ids"],
            "core_question_count": fields["core_question_count"],
            "contrast_question_ids": fields["contrast_question_ids"],
            "contrast_question_count": fields["contrast_question_count"],
            "needs_review_contrast_question_ids": fields["needs_review_contrast_question_ids"],
            "needs_review_contrast_question_count": fields["needs_review_contrast_question_count"],
            "subtree_question_count": fields["question_count"],
            "evidence_quotes": fields["evidence_quotes"],
            "sections": fields["sections"],
            "cross_chapter": fields["cross_chapter"],
            "materialize_relation_pair_ids": [],
            "relation_trace_pair_ids": [],
            "build_method": "v10_full828_from_v5_points_and_v6_relation_draft",
            "review_status": "full828_draft_not_final",
        }
        for card_id in cards:
            card_to_exam_point[card_id] = ep_id
        items.append(item)

    items_by_id = {item["id"]: item for item in items}
    conflict_records: list[dict[str, Any]] = []

    def attach_relation_pair(ep_id: str | None, pair_id: str | None) -> None:
        if not ep_id or not pair_id or ep_id not in items_by_id:
            return
        if pair_id not in items_by_id[ep_id]["materialize_relation_pair_ids"]:
            items_by_id[ep_id]["materialize_relation_pair_ids"].append(pair_id)

    def attach_relation_trace(ep_id: str | None, pair_id: str | None) -> None:
        if not ep_id or not pair_id or ep_id not in items_by_id:
            return
        if pair_id not in items_by_id[ep_id]["relation_trace_pair_ids"]:
            items_by_id[ep_id]["relation_trace_pair_ids"].append(pair_id)

    for record in judgement_records:
        pair_id = record.get("pair_id")
        label = record.get("source_draft_label")
        a_ep = card_to_exam_point.get(record["card_a_id"])
        b_ep = card_to_exam_point.get(record["card_b_id"])
        if label in {"merge_same_point", "parent_child", "sibling_under_parent"}:
            attach_relation_trace(a_ep, pair_id)
            attach_relation_trace(b_ep, pair_id)
        if not record.get("applied"):
            continue
        attach_relation_pair(a_ep, pair_id)
        attach_relation_pair(b_ep, pair_id)
        if label != "parent_child":
            continue
        parent_ep = card_to_exam_point.get(record.get("parent_card_id"))
        child_ep = card_to_exam_point.get(record.get("child_card_id"))
        if not parent_ep or not child_ep:
            conflict_records.append(
                {
                    "type": "parent_child_missing_endpoint_after_merge",
                    "pair_id": pair_id,
                    "parent_card_id": record.get("parent_card_id"),
                    "child_card_id": record.get("child_card_id"),
                }
            )
            continue
        if parent_ep == child_ep:
            continue
        child = items_by_id[child_ep]
        parent = items_by_id[parent_ep]
        if child["parent_id"] and child["parent_id"] != parent_ep:
            conflict_records.append(
                {
                    "type": "multiple_parent_conflict",
                    "pair_id": pair_id,
                    "child_exam_point_id": child_ep,
                    "existing_parent_id": child["parent_id"],
                    "new_parent_id": parent_ep,
                }
            )
            continue
        child["parent_id"] = parent_ep
        if child_ep not in parent["children"]:
            parent["children"].append(child_ep)

    sibling_components = UnionFind()
    sibling_ep_ids: set[str] = set()
    for record in judgement_records:
        if record.get("source_draft_label") != "sibling_under_parent" or not record.get("applied"):
            continue
        a_ep = card_to_exam_point.get(record["card_a_id"])
        b_ep = card_to_exam_point.get(record["card_b_id"])
        if not a_ep or not b_ep or a_ep == b_ep:
            continue
        sibling_components.union(a_ep, b_ep)
        sibling_ep_ids.update([a_ep, b_ep])
        items_by_id[a_ep]["sibling_relation_pair_ids"].append(record["pair_id"])
        items_by_id[b_ep]["sibling_relation_pair_ids"].append(record["pair_id"])

    sibling_groups: dict[str, list[str]] = defaultdict(list)
    for ep_id in sibling_ep_ids:
        sibling_groups[sibling_components.find(ep_id)].append(ep_id)

    virtual_parent_count = 0
    for _, group_ids in sorted(sibling_groups.items(), key=lambda row: sorted(row[1])[0]):
        child_ids = sorted(set(group_ids))
        free_child_ids = [ep_id for ep_id in child_ids if not items_by_id[ep_id].get("parent_id")]
        if len(free_child_ids) < 2:
            conflict_records.append(
                {
                    "type": "sibling_group_not_materialized",
                    "reason": "less_than_two_free_children",
                    "child_ids": child_ids,
                    "free_child_ids": free_child_ids,
                }
            )
            continue
        virtual_parent_count += 1
        vp_id = f"EP10-VP-{virtual_parent_count:04d}"
        child_titles = [compact(items_by_id[ep_id]["title"], 28) for ep_id in free_child_ids[:3]]
        question_ids = unique([qid for ep_id in free_child_ids for qid in items_by_id[ep_id].get("question_ids", [])])
        raw_question_ids = unique(
            [qid for ep_id in free_child_ids for qid in items_by_id[ep_id].get("raw_question_ids", [])]
        )
        tags = unique([tag for ep_id in free_child_ids for tag in items_by_id[ep_id].get("tags", [])])
        relation_pair_ids = unique(
            [
                pair_id
                for ep_id in free_child_ids
                for pair_id in items_by_id[ep_id].get("sibling_relation_pair_ids", [])
            ]
        )
        vp = {
            "id": vp_id,
            "title": "并列教材知识点组：" + " / ".join(child_titles),
            "title_status": "virtual_parent_needs_naming",
            "point_type": "结构父点",
            "is_high_frequency": False,
            "tags": tags,
            "parent_id": None,
            "children": free_child_ids,
            "sibling_relation_pair_ids": relation_pair_ids,
            "card_ids": [],
            "source_point_ids": [],
            "raw_question_ids": raw_question_ids,
            "question_ids": question_ids,
            "question_count": 0,
            "core_question_ids": [],
            "core_question_count": 0,
            "contrast_question_ids": [],
            "contrast_question_count": 0,
            "needs_review_contrast_question_ids": [],
            "needs_review_contrast_question_count": 0,
            "subtree_question_count": len(question_ids),
            "evidence_quotes": [],
            "sections": {},
            "cross_chapter": any(items_by_id[ep_id].get("cross_chapter") for ep_id in free_child_ids),
            "materialize_relation_pair_ids": relation_pair_ids,
            "relation_trace_pair_ids": relation_pair_ids,
            "build_method": "v10_virtual_parent_from_sibling_under_parent_relations",
            "review_status": "full828_virtual_parent_draft_not_final",
        }
        for ep_id in free_child_ids:
            items_by_id[ep_id]["parent_id"] = vp_id
        items.append(vp)
        items_by_id[vp_id] = vp

    refresh_subtree_counts(items, items_by_id)

    edge_rows: list[dict[str, Any]] = []
    for item in sorted(items, key=lambda row: row["id"]):
        if item.get("card_ids"):
            edge_rows.extend(build_direct_edges(item, points_by_card, strong_edges_by_card_question))
        for child_id in collect_descendants(item["id"], items_by_id):
            child = items_by_id.get(child_id)
            if not child or not child.get("card_ids"):
                continue
            for child_edge in build_direct_edges(child, points_by_card, strong_edges_by_card_question):
                edge_rows.append(
                    {
                        **child_edge,
                        "exam_point_id": item["id"],
                        "edge_scope": "subtree",
                        "child_exam_point_id": child_id,
                    }
                )

    contrast_records = []
    for idx, item in enumerate(contrast_items, start=1):
        ep_id = card_to_exam_point.get(item.get("card_id"))
        contrast_records.append(
            {
                "decision_id": f"V10CJ-{idx:04d}",
                "record_type": "contrast",
                "judgement_source": "preview_v6_contrast_draft.rule",
                "edge_key": item.get("edge_key"),
                "question_id": item.get("question_id"),
                "section": item.get("section"),
                "option": item.get("option"),
                "option_text": item.get("option_text"),
                "card_id": item.get("card_id"),
                "exam_point_id": ep_id,
                "source_classification": item.get("classification"),
                "draft_action": item.get("draft_action"),
                "included_in_exam_point": item.get("draft_action") == "count_in_exam_point" and bool(ep_id),
                "reason": item.get("reason"),
                "quote": item.get("quote"),
                "focus_type": item.get("focus_type"),
                "evidence_grade": item.get("evidence_grade"),
                "evidence_status": item.get("evidence_status"),
            }
        )

    sorted_items = sorted(items, key=lambda item: (item["id"].startswith("EP10-VP"), -item["question_count"], item["id"]))
    payload = {
        "schema_version": "preview_v10_full828_materialized_draft",
        "note": (
            "Full draft materialization from v5 formal candidate points. "
            "This stage is deterministic and does not call LLM/DeepSeek."
        ),
        "items": sorted_items,
    }

    applied_relations = [record for record in judgement_records if record.get("applied")]
    direct_items = [item for item in items if item.get("card_ids")]
    actual_parent_child_link_count = len(
        [
            item
            for item in items
            if item.get("parent_id") and not str(item.get("parent_id")).startswith("EP10-VP-")
        ]
    )
    virtual_parent_child_link_count = sum(
        len(item.get("children", [])) for item in items if str(item.get("id", "")).startswith("EP10-VP-")
    )

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_candidate_points": str(V5_DIR / "all_candidate_points.json"),
        "source_relation_draft": str(V6_DIR / "relation_draft.json"),
        "source_contrast_draft": str(V6_DIR / "contrast_draft.json"),
        "source_strong_edges": str(V1_DIR / "strong_edges.json"),
        "candidate_point_count": len(candidate_points),
        "formal_candidate_point_count": len(formal_points),
        "review_only_point_count": len(review_only_points),
        "strong_edge_count": len(strong_edges),
        "relation_draft_count": len(relation_items),
        "relation_draft_distribution": dict(Counter(item.get("draft_label") for item in relation_items).most_common()),
        "relation_apply_mode": apply_mode,
        "applied_relation_count": len(applied_relations),
        "applied_relation_distribution": dict(
            Counter(record.get("source_draft_label") for record in applied_relations).most_common()
        ),
        "skipped_relation_distribution": dict(
            Counter(record.get("skip_reason") for record in judgement_records if not record.get("applied")).most_common()
        ),
        "min_confidence": {
            "merge_same_point": min_confidence("merge_same_point"),
            "parent_child": min_confidence("parent_child"),
            "sibling_under_parent": min_confidence("sibling_under_parent"),
        },
        "materialized_item_count": len(items),
        "direct_exam_point_count": len(direct_items),
        "virtual_parent_count": virtual_parent_count,
        "multi_card_exam_point_count": len([item for item in direct_items if len(item.get("card_ids", [])) > 1]),
        "parent_link_count": len([item for item in items if item.get("parent_id")]),
        "actual_parent_child_link_count": actual_parent_child_link_count,
        "virtual_parent_child_link_count": virtual_parent_child_link_count,
        "high_frequency_direct_exam_point_count": len([item for item in direct_items if item.get("is_high_frequency")]),
        "normal_direct_exam_point_count": len(
            [item for item in direct_items if not item.get("is_high_frequency")]
        ),
        "direct_question_count_distribution": dict(
            sorted(Counter(item.get("question_count") for item in direct_items).items(), key=lambda row: row[0])
        ),
        "edge_row_count": len(edge_rows),
        "contrast_draft_count": len(contrast_items),
        "contrast_draft_distribution": dict(Counter(item.get("draft_action") for item in contrast_items).most_common()),
        "included_contrast_count": len([row for row in contrast_records if row.get("included_in_exam_point")]),
        "conflict_count": len(conflict_records),
    }

    write_json(OUT_DIR / "summary.json", summary)
    write_json(OUT_DIR / "exam_point_system_full828.json", payload)
    write_json(OUT_DIR / "exam_point_question_card_edges.json", {"items": edge_rows})
    write_json(OUT_DIR / "materialize_conflicts.json", {"items": conflict_records})
    write_json(OUT_DIR / "review_only_points.json", {"items": review_only_points})
    write_jsonl(OUT_DIR / "relation_judgement_records.jsonl", judgement_records)
    write_jsonl(OUT_DIR / "contrast_judgement_records.jsonl", contrast_records)
    write_report(summary, payload, judgement_records, contrast_records)
    return summary


def write_report(
    summary: dict[str, Any],
    payload: dict[str, Any],
    relation_records: list[dict[str, Any]],
    contrast_records: list[dict[str, Any]],
) -> None:
    items = payload["items"]
    multi_card = [item for item in items if len(item.get("card_ids", [])) > 1]
    parents = [item for item in items if item.get("children") and item.get("card_ids")]
    virtual_parents = [item for item in items if item.get("children") and not item.get("card_ids")]
    high_frequency = [item for item in items if item.get("card_ids") and item.get("is_high_frequency")]
    sample_items = multi_card[:4] + parents[:4] + virtual_parents[:4] + high_frequency[:4]
    seen: set[str] = set()
    lines = [
        "# Preview v10 full828 物化报告",
        "",
        "本报告验证 v5 的 828 个有题目支撑候选点能否全量物化为可追溯的“考点-题目-选项-句卡”结构。",
        "",
        "## 统计",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## 典型物化样例", ""])
    for item in sample_items:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        lines.extend(
            [
                f"### {item['id']} {compact(item['title'], 80)}",
                f"- 类型：{item['point_type']}；题目数：{item['question_count']}；子树题目数：{item['subtree_question_count']}",
                f"- 句卡：{', '.join(item.get('card_ids') or ['（虚拟父点，无直接句卡）'])}",
                f"- 题目：{', '.join(item.get('question_ids', [])[:12])}",
                f"- 子点：{', '.join(item.get('children', [])[:12]) if item.get('children') else '无'}",
                f"- 来源关系：{', '.join(item.get('materialize_relation_pair_ids', [])[:12]) or '无'}",
                "",
            ]
        )

    applied_relation_distribution = Counter(
        record.get("source_draft_label") for record in relation_records if record.get("applied")
    )
    contrast_distribution = Counter(record.get("draft_action") for record in contrast_records)
    lines.extend(
        [
            "## 可复现边界",
            "",
            "- v10 物化阶段不调用 LLM/DeepSeek，只应用可复现规则。",
            "- 828 个有题目支撑的 v5 候选点全部入场；77 个无题目支撑点写入 `review_only_points.json`，不进入正式候选。",
            f"- 当前关系应用模式：`{summary.get('relation_apply_mode')}`。",
            "- `merge_same_point` 默认中/高置信才合并。",
            "- strict/merge_only 模式下，`parent_child` 和 `sibling_under_parent` 只保留为 relation trace，不直接建立父子或虚拟父点。",
            "- 如需复现实验性旧结构，可显式设置 `PREVIEW_V10_RELATION_APPLY_MODE=legacy`。",
            "- 所有 v6 relation 都写入 `relation_judgement_records.jsonl`；未应用的边保留 `skip_reason`。",
            "- 所有 v6 contrast 都写入 `contrast_judgement_records.jsonl`，其中 `count_in_exam_point` 可作为易错/辨析信号。",
            "",
            "## 当前应用分布",
            "",
            f"- applied_relation_distribution: {dict(applied_relation_distribution)}",
            f"- contrast_distribution: {dict(contrast_distribution)}",
            "",
            "## 下一步",
            "",
            "1. 抽查 full828 多句卡、父子、虚拟父点质量。",
            "2. 用 v8 命名链路对 full828 分批命名；第一批建议用 DeepSeek pro 校准。",
            "3. 命名后接 v9 门禁，把低置信、薄证据、父子方向不稳的点分流到复核队列。",
            "",
        ]
    )
    (OUT_DIR / "materialize_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    summary = materialize()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
