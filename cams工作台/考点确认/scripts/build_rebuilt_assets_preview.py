from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
WORK_DIR = SCRIPT_DIR.parent
APP_DIR = WORK_DIR.parent
DATA_DIR = APP_DIR / "data" / "teaching_assets"
PAGE_MAP_PATH = APP_DIR / "data" / "page_maps" / "card_page_map_v6.json"
DEFAULT_TRIAL_DIR = WORK_DIR / "outputs" / "rebuild_trial_20q_chat_v3"
DEFAULT_OUT_DIR = WORK_DIR / "outputs" / "rebuilt_assets_preview"
DEFAULT_READER_PATH = DATA_DIR / "chapters" / "v6_full.json"
DEFAULT_MERGE_DECISIONS = WORK_DIR / "merge_decisions_rebuilt_preview.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def compact(text: Any, limit: int = 240) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def unique(items: list[Any]) -> list[Any]:
    result = []
    seen = set()
    for item in items:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True) if isinstance(item, dict) else item
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def slug(text: str, fallback: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"{fallback}_{digest}"


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def normalize_cards(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        return [card for card in payload.get("cards", []) if isinstance(card, dict) and card.get("card_id")]
    return [card for card in payload if isinstance(card, dict) and card.get("card_id")]


def card_detail(card_id: str, cards_by_id: dict[str, dict[str, Any]], page_map: dict[str, Any]) -> dict[str, Any]:
    card = cards_by_id.get(card_id, {})
    page = page_map.get(card_id, {})
    return {
        "card_id": card_id,
        "quote": card.get("citation", ""),
        "knowledge": card.get("knowledge", ""),
        "chapter_path": card.get("chapter_path", ""),
        "source_line_start": card.get("source_line_start", ""),
        "source_line_end": card.get("source_line_end", ""),
        "page_label": page.get("page_label", ""),
        "page_confidence": page.get("confidence", ""),
    }


def collect_reader_card_locations(chapter: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    locations: dict[str, list[dict[str, Any]]] = defaultdict(list)
    chapter_title = chapter.get("chapter", "")
    for section in chapter.get("sections", []):
        section_title = section.get("display_title") or section.get("section_title") or ""
        for subsection in section.get("subsections", []):
            subsection_title = subsection.get("display_title") or subsection.get("title") or ""
            path = " > ".join(part for part in [chapter_title, section_title, subsection_title] if part)
            for paragraph_index, paragraph in enumerate(subsection.get("paragraphs", [])):
                card_ids = unique((paragraph.get("card_ids") or []) + (paragraph.get("highlight_card_ids") or []))
                row = {
                    "section_id": section.get("section_id") or section.get("number", ""),
                    "section_title": section_title,
                    "subsection_title": subsection_title,
                    "chapter_path": path,
                    "paragraph_index": paragraph_index,
                    "source_line_start": paragraph.get("source_line_start", ""),
                    "source_line_end": paragraph.get("source_line_end", ""),
                    "text": paragraph.get("text", ""),
                }
                for card_id in card_ids:
                    locations[card_id].append(row)
    return locations


def build_exam_points(
    candidate_items: list[dict[str, Any]],
    cards_by_id: dict[str, dict[str, Any]],
    page_map: dict[str, Any],
) -> list[dict[str, Any]]:
    points = []
    for item in candidate_items:
        if item.get("validation_issues"):
            # Keep auditable but mark it; do not drop it silently.
            validation_issues = item.get("validation_issues") or []
        else:
            validation_issues = []
        result = item.get("result") or {}
        pack = item.get("pack") or {}
        question_id = item.get("question_id") or pack.get("question_id")
        for index, point in enumerate(result.get("candidate_points") or [], start=1):
            core_ids = unique([cid for cid in point.get("core_card_ids") or [] if cid in cards_by_id])
            supporting_ids = unique([cid for cid in point.get("supporting_card_ids") or [] if cid in cards_by_id and cid not in core_ids])
            background_ids = unique(
                [
                    cid
                    for cid in point.get("background_card_ids") or []
                    if cid in cards_by_id and cid not in core_ids and cid not in supporting_ids
                ]
            )
            source_ids = unique(core_ids + supporting_ids + background_ids)
            if not question_id or not source_ids:
                continue
            title = compact(point.get("title"), 90) or f"未命名考点 {question_id}-{index}"
            linked_question_ids = [question_id]
            item_id = slug(f"{question_id}|{index}|{title}", "ep_rebuilt")
            points.append(
                {
                    "id": item_id,
                    "title": title,
                    "teaching_object_kind": "exam_point",
                    "is_exam_point": True,
                    "is_high_frequency": len(linked_question_ids) >= 3,
                    "is_misconception": False,
                    "linked_question_ids": linked_question_ids,
                    "linked_question_count": len(linked_question_ids),
                    "linked_qa_ids": [],
                    "linked_qa_count": 0,
                    "question_ids": linked_question_ids,
                    "qa_ids": [],
                    "exam_intents": [result.get("exam_intent", "")] if result.get("exam_intent") else [],
                    "teaching_focus": compact(point.get("teaching_focus"), 280),
                    "reason": compact(point.get("reason"), 520),
                    "confidence": point.get("confidence") or "medium",
                    "core_card_ids": core_ids,
                    "supporting_card_ids": supporting_ids,
                    "background_card_ids": background_ids,
                    "source_card_ids": source_ids,
                    "source_card_details": [card_detail(cid, cards_by_id, page_map) for cid in source_ids],
                    "option_bindings": [
                        {
                            "question_id": question_id,
                            "answer": pack.get("answer", ""),
                            "correct_options": [
                                {
                                    "option": opt.get("option", ""),
                                    "option_text": opt.get("option_text", ""),
                                }
                                for opt in pack.get("correct_options", [])
                            ],
                        }
                    ],
                    "trap_notes": result.get("trap_notes") or [],
                    "validation_issues": validation_issues,
                    "generation_source": "rebuild_trial_candidate_points",
                    "actual_model": item.get("actual_model") or item.get("model", ""),
                    "updated_at": now(),
                }
            )
    return points


def load_merge_decisions(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = read_json(path)
    if isinstance(payload, list):
        return payload
    return payload.get("merge_decisions", [])


def point_matches_decision(point: dict[str, Any], decision_side: dict[str, Any]) -> bool:
    qid = decision_side.get("question_id")
    title = decision_side.get("title")
    if qid and qid not in (point.get("linked_question_ids") or []):
        return False
    if title:
        point_title = point.get("title") or ""
        if title == point_title:
            return True
        title_key = "".join(str(title).split())
        point_key = "".join(str(point_title).split())
        if title_key and point_key and (title_key in point_key or point_key in title_key):
            return True
        if qid and decision_side.get("allow_question_only_match", True):
            return True
    return True


def apply_merge_decisions(points: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_id = {point["id"]: point for point in points}
    consumed: set[str] = set()
    applied = []
    result = []

    for decision in decisions:
        if not decision.get("merge"):
            continue
        sides = decision.get("points") or []
        matched = []
        for side in sides:
            for point in points:
                if point["id"] in consumed:
                    continue
                if point_matches_decision(point, side):
                    matched.append(point)
                    break
        if len(matched) < 2:
            continue
        for point in matched:
            consumed.add(point["id"])
        title = decision.get("merged_title") or matched[0].get("title") or "合并考点"
        merged_id = slug("merge|" + "|".join(point["id"] for point in matched) + "|" + title, "ep_rebuilt")
        linked_question_ids = unique([qid for point in matched for qid in point.get("linked_question_ids") or []])
        linked_qa_ids = unique([qa_id for point in matched for qa_id in point.get("linked_qa_ids") or []])
        core_ids = unique([cid for point in matched for cid in point.get("core_card_ids") or []])
        supporting_ids = unique([cid for point in matched for cid in point.get("supporting_card_ids") or [] if cid not in core_ids])
        background_ids = unique(
            [
                cid
                for point in matched
                for cid in point.get("background_card_ids") or []
                if cid not in core_ids and cid not in supporting_ids
            ]
        )
        source_ids = unique(core_ids + supporting_ids + background_ids)
        details_by_id = {}
        for point in matched:
            for detail in point.get("source_card_details") or []:
                if detail.get("card_id") and detail["card_id"] not in details_by_id:
                    details_by_id[detail["card_id"]] = detail
        merged = {
            **matched[0],
            "id": merged_id,
            "title": title,
            "linked_question_ids": linked_question_ids,
            "linked_question_count": len(linked_question_ids),
            "question_ids": linked_question_ids,
            "linked_qa_ids": linked_qa_ids,
            "linked_qa_count": len(linked_qa_ids),
            "qa_ids": linked_qa_ids,
            "is_misconception": bool(linked_qa_ids),
            "is_high_frequency": len(linked_question_ids) >= 3,
            "exam_intents": unique([intent for point in matched for intent in point.get("exam_intents") or []]),
            "teaching_focus": compact(decision.get("merged_teaching_focus") or matched[0].get("teaching_focus"), 280),
            "reason": compact(decision.get("reason") or "按人工确认合并同一教材知识单元。", 520),
            "core_card_ids": core_ids,
            "supporting_card_ids": supporting_ids,
            "background_card_ids": background_ids,
            "source_card_ids": source_ids,
            "source_card_details": [details_by_id[cid] for cid in source_ids if cid in details_by_id],
            "option_bindings": unique([binding for point in matched for binding in point.get("option_bindings") or []]),
            "trap_notes": unique([note for point in matched for note in point.get("trap_notes") or []]),
            "validation_issues": unique([issue for point in matched for issue in point.get("validation_issues") or []]),
            "member_point_ids": [point["id"] for point in matched],
            "generation_source": "rebuild_trial_candidate_points_with_manual_merge",
        }
        result.append(merged)
        applied.append(
            {
                "merged_id": merged_id,
                "merged_title": title,
                "member_point_ids": [point["id"] for point in matched],
                "linked_question_ids": linked_question_ids,
            }
        )

    for point in points:
        if point["id"] not in consumed:
            result.append(point)
    result.sort(key=lambda point: (-len(point.get("linked_question_ids") or []), point.get("title") or ""))
    return result, applied


def attach_qa_signals(points: list[dict[str, Any]], qa_bindings: list[dict[str, Any]]) -> dict[str, Any]:
    by_question: dict[str, list[str]] = defaultdict(list)
    for binding in qa_bindings:
        qa_id = binding.get("qa_id")
        qid = binding.get("bound_question_id")
        if qa_id and qid:
            by_question[qid].append(qa_id)

    links = []
    for point in points:
        qa_ids = []
        for qid in point.get("linked_question_ids") or []:
            qa_ids.extend(by_question.get(qid, []))
        qa_ids = unique(qa_ids)
        point["linked_qa_ids"] = qa_ids
        point["linked_qa_count"] = len(qa_ids)
        point["qa_ids"] = qa_ids
        point["is_misconception"] = bool(qa_ids)
        if not qa_ids:
            continue
        for qa_id in qa_ids:
            links.append(
                {
                    "target_kind": "exam_point",
                    "target_id": point["id"],
                    "qa_id": qa_id,
                    "linked_question_ids": point.get("linked_question_ids") or [],
                    "match_method": "bound_question_id",
                }
            )
    return {
        "version": "0.1",
        "asset_note": "正式学生答疑挂接到新定义考点的易错信号预览。网页临时答疑不进入本资产。",
        "generated_at": now(),
        "stats": {
            "links": len(links),
            "exam_points_with_qa": len({link["target_id"] for link in links}),
            "unique_qa": len({link["qa_id"] for link in links}),
        },
        "links": links,
    }


def build_textbook_knowledge_points(
    cards: list[dict[str, Any]],
    exam_points: list[dict[str, Any]],
    reader_locations: dict[str, list[dict[str, Any]]],
    page_map: dict[str, Any],
    limit: int = 300,
) -> list[dict[str, Any]]:
    used_cards = {cid for point in exam_points for cid in point.get("source_card_ids") or []}
    points = []
    for card in cards:
        cid = card.get("card_id")
        if not cid or cid in used_cards or cid not in reader_locations:
            continue
        title = compact(card.get("knowledge") or card.get("citation"), 90)
        if not title:
            continue
        points.append(
            {
                "id": f"tkp_{cid.lower()}",
                "title": title,
                "teaching_object_kind": "textbook_knowledge_point",
                "is_exam_point": False,
                "is_high_frequency": False,
                "is_misconception": False,
                "linked_question_ids": [],
                "linked_question_count": 0,
                "linked_qa_ids": [],
                "linked_qa_count": 0,
                "source_card_ids": [cid],
                "source_card_details": [card_detail(cid, {cid: card}, page_map)],
                "generation_source": "reader_sentence_card_not_exam_point",
            }
        )
        if len(points) >= limit:
            break
    return points


def build_sentence_map(
    exam_points: list[dict[str, Any]],
    knowledge_points: list[dict[str, Any]],
    reader_locations: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    rows = []
    paragraphs: dict[str, dict[str, Any]] = {}

    def add_object(obj: dict[str, Any]) -> None:
        for card_id in obj.get("source_card_ids") or []:
            for location in reader_locations.get(card_id, []):
                paragraph_key = "|".join(
                    [
                        str(location.get("section_id", "")),
                        str(location.get("source_line_start", "")),
                        str(location.get("source_line_end", "")),
                        str(location.get("paragraph_index", "")),
                    ]
                )
                rows.append(
                    {
                        "card_id": card_id,
                        "teaching_object_id": obj["id"],
                        "teaching_object_kind": obj.get("teaching_object_kind"),
                        "title": obj.get("title"),
                        "paragraph_key": paragraph_key,
                        "section_id": location.get("section_id", ""),
                        "chapter_path": location.get("chapter_path", ""),
                        "source_line_start": location.get("source_line_start", ""),
                        "source_line_end": location.get("source_line_end", ""),
                    }
                )
                paragraphs.setdefault(
                    paragraph_key,
                    {
                        "paragraph_key": paragraph_key,
                        "section_id": location.get("section_id", ""),
                        "chapter_path": location.get("chapter_path", ""),
                        "source_line_start": location.get("source_line_start", ""),
                        "source_line_end": location.get("source_line_end", ""),
                        "text": location.get("text", ""),
                        "teaching_object_ids": [],
                    },
                )
                paragraphs[paragraph_key]["teaching_object_ids"].append(obj["id"])

    for point in exam_points:
        add_object(point)
    for point in knowledge_points:
        add_object(point)

    paragraph_rows = list(paragraphs.values())
    for row in paragraph_rows:
        row["teaching_object_ids"] = unique(row["teaching_object_ids"])
    return {
        "version": "0.1",
        "asset_note": "新定义阅读页定位预览：考点和教材知识点分开标识。",
        "generated_at": now(),
        "stats": {
            "sentence_rows": len(rows),
            "paragraphs_with_objects": len(paragraph_rows),
            "mapped_exam_points": len({row["teaching_object_id"] for row in rows if row["teaching_object_kind"] == "exam_point"}),
            "mapped_textbook_knowledge_points": len(
                {row["teaching_object_id"] for row in rows if row["teaching_object_kind"] == "textbook_knowledge_point"}
            ),
        },
        "sentences": rows,
        "paragraphs": paragraph_rows,
    }


def render_report(exam_points: list[dict[str, Any]], knowledge_points: list[dict[str, Any]], misconception_links: dict[str, Any], sentence_map: dict[str, Any]) -> str:
    issue_points = [point for point in exam_points if point.get("validation_issues")]
    lines = [
        "# 新定义考点资产 preview 报告",
        "",
        f"- generated_at: {now()}",
        f"- 正式考点：{len(exam_points)}",
        f"- 高频考点：{sum(1 for point in exam_points if point.get('is_high_frequency'))}",
        f"- 易错信号链接：{misconception_links.get('stats', {}).get('links', 0)}",
        f"- 教材知识点 preview：{len(knowledge_points)}",
        f"- 阅读页映射考点：{sentence_map.get('stats', {}).get('mapped_exam_points', 0)}",
        f"- 阅读页映射教材知识点：{sentence_map.get('stats', {}).get('mapped_textbook_knowledge_points', 0)}",
        f"- 有校验问题的考点：{len(issue_points)}",
        "",
        "## 正式考点样例",
        "",
    ]
    for point in exam_points[:30]:
        tags = []
        if point.get("is_high_frequency"):
            tags.append("高频")
        if point.get("is_misconception"):
            tags.append("易错")
        tag_text = f" ({', '.join(tags)})" if tags else ""
        lines += [
            f"### {point['title']}{tag_text}",
            "",
            f"- ID：{point['id']}",
            f"- 题目：{', '.join(point.get('linked_question_ids') or [])}",
            f"- 答疑：{', '.join(point.get('linked_qa_ids') or []) or '无'}",
            f"- 主证据：{', '.join(point.get('core_card_ids') or [])}",
            f"- 补充证据：{', '.join(point.get('supporting_card_ids') or []) or '无'}",
            f"- 考查方向：{'; '.join(point.get('exam_intents') or [])}",
            "",
        ]
    if issue_points:
        lines += ["## 校验问题", ""]
        for point in issue_points:
            lines.append(f"- {point['id']} {point['title']}：{'; '.join(point.get('validation_issues') or [])}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Build new-definition preview assets from rebuild trial outputs.")
    parser.add_argument("--trial-dir", type=Path, default=DEFAULT_TRIAL_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--reader-path", type=Path, default=DEFAULT_READER_PATH)
    parser.add_argument("--merge-decisions", type=Path, default=DEFAULT_MERGE_DECISIONS)
    parser.add_argument("--knowledge-limit", type=int, default=300)
    args = parser.parse_args()

    candidate_payload = read_json(args.trial_dir / "candidate_points.json")
    cards = normalize_cards(read_json(DATA_DIR / "cards_v6_sentence.json"))
    cards_by_id = {card["card_id"]: card for card in cards}
    page_map = read_json(PAGE_MAP_PATH).get("cards", {})
    chapter = read_json(args.reader_path)
    qa_bindings = read_json(DATA_DIR / "qa_bindings.json").get("bindings", [])
    reader_locations = collect_reader_card_locations(chapter)

    exam_points = build_exam_points(candidate_payload.get("items", []), cards_by_id, page_map)
    merge_decisions = load_merge_decisions(args.merge_decisions)
    exam_points, applied_merges = apply_merge_decisions(exam_points, merge_decisions)
    misconception_links = attach_qa_signals(exam_points, qa_bindings)
    knowledge_points = build_textbook_knowledge_points(cards, exam_points, reader_locations, page_map, limit=args.knowledge_limit)
    sentence_map = build_sentence_map(exam_points, knowledge_points, reader_locations)

    exam_payload = {
        "version": "0.1",
        "asset_note": "新定义正式考点 preview。只包含至少关联 1 道正式题目、且能回到教材句卡的候选考点。",
        "generated_at": now(),
        "source_assets": [str(args.trial_dir / "candidate_points.json"), "cards_v6_sentence.json", "card_page_map_v6.json"],
        "stats": {
            "exam_points": len(exam_points),
            "high_frequency_points": sum(1 for point in exam_points if point.get("is_high_frequency")),
            "misconception_points": sum(1 for point in exam_points if point.get("is_misconception")),
            "applied_merges": len(applied_merges),
            "unique_questions": len({qid for point in exam_points for qid in point.get("linked_question_ids") or []}),
            "unique_cards": len({cid for point in exam_points for cid in point.get("source_card_ids") or []}),
            "points_with_validation_issues": sum(1 for point in exam_points if point.get("validation_issues")),
        },
        "applied_merges": applied_merges,
        "exam_points": exam_points,
    }
    knowledge_payload = {
        "version": "0.1",
        "asset_note": "教材知识点 preview：有教材句卡但无正式题目关联，不叫考点。",
        "generated_at": now(),
        "stats": {"textbook_knowledge_points": len(knowledge_points)},
        "textbook_knowledge_points": knowledge_points,
    }

    write_json(args.out_dir / "exam_points_rebuilt_preview.json", exam_payload)
    write_json(args.out_dir / "textbook_knowledge_points_preview.json", knowledge_payload)
    write_json(args.out_dir / "misconception_links_preview.json", misconception_links)
    write_json(args.out_dir / "sentence_teaching_point_map_preview.json", sentence_map)
    (args.out_dir / "report.md").write_text(render_report(exam_points, knowledge_points, misconception_links, sentence_map), encoding="utf-8")

    print(
        json.dumps(
            {
                "out_dir": str(args.out_dir),
                "exam_points": len(exam_points),
                "textbook_knowledge_points": len(knowledge_points),
                "misconception_links": misconception_links.get("stats", {}).get("links", 0),
                "mapped_exam_points": sentence_map.get("stats", {}).get("mapped_exam_points", 0),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
