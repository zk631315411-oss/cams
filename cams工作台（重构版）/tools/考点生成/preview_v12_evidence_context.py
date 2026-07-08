from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DATA_DIR = HERE.parents[1] / "data"
OUT_DIR = HERE / "work" / "preview_v12_evidence_context"

DEFAULT_NAMED_FILE = HERE / "work" / "preview_v8_naming_sample" / "named_exam_points_sample_v10_full831_all_prompt_v2.json"
DEFAULT_DECISION_FILE = (
    HERE
    / "work"
    / "preview_v9_admission_gate"
    / "admission_decisions_v10_full831_all_prompt_v2_rules_v3.json"
)
DEFAULT_EDGES_FILE = HERE / "work" / "preview_v10_full828" / "exam_point_question_card_edges.json"
DEFAULT_CARDS_FILE = DATA_DIR / "cards" / "cards_v6_sentence.json"
DEFAULT_PAGE_MAP_FILE = DATA_DIR / "page_maps" / "card_page_map_v6.json"
DEFAULT_QUESTIONS_FILE = DATA_DIR / "source" / "questions.json"

DEFAULT_SAMPLE_IDS = [
    "EP10-0524",
    "EP10-0338",
    "EP10-0068",
    "EP10-0810",
    "EP10-0811",
    "EP10-0813",
    "EP10-0010",
    "EP10-0020",
]


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else HERE / path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def batch_name() -> str:
    raw = os.getenv("PREVIEW_V12_BATCH_NAME", "").strip()
    return "".join(ch for ch in raw if ch.isalnum() or ch in {"_", "-"}) or "sample"


def out_name(stem: str, suffix: str) -> str:
    return f"{stem}_{batch_name()}.{suffix}"


def load_cards(path: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("cards", payload if isinstance(payload, list) else [])
    return {str(row.get("card_id") or row.get("id")): row for row in rows if row.get("card_id") or row.get("id")}


def load_page_map(path: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(path)
    cards = payload.get("cards", {})
    if isinstance(cards, dict):
        return cards
    if isinstance(cards, list):
        return {str(row.get("card_id") or row.get("id")): row for row in cards if row.get("card_id") or row.get("id")}
    return {}


def load_questions(path: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("questions") or payload.get("items") if isinstance(payload, dict) else payload
    return {str(row.get("id")): row for row in rows if row.get("id")}


def compact(text: Any, limit: int = 360) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)] + "..."


def join_context(before: str, citation: str, after: str) -> str:
    parts = [part.strip() for part in [before, citation, after] if str(part or "").strip()]
    return " ".join(parts)


def context_quality(original_quote: str, display_context: str, card: dict[str, Any], page: dict[str, Any] | None) -> str:
    if not display_context:
        return "missing_card"
    before = str(card.get("context_before") or "").strip()
    after = str(card.get("context_after") or "").strip()
    if len(display_context) >= 60 and (before or after):
        return "expanded"
    if len(display_context) >= max(30, len(original_quote or "")):
        return "usable"
    if page is None:
        return "thin_no_page"
    return "thin"


def build_card_context(
    card_id: str,
    source_quote: str,
    cards_by_id: dict[str, dict[str, Any]],
    page_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    card = cards_by_id.get(card_id, {})
    page = page_by_id.get(card_id)
    citation = str(card.get("citation") or source_quote or "").strip()
    context_before = str(card.get("context_before") or "").strip()
    context_after = str(card.get("context_after") or "").strip()
    display_context = join_context(context_before, citation, context_after)
    if not display_context:
        display_context = source_quote

    page_label = ""
    page_confidence = ""
    physical_pages: list[Any] = []
    textbook_pages: list[Any] = []
    if page:
        page_label = str(page.get("page_label") or "")
        page_confidence = str(page.get("confidence") or "")
        physical_pages = page.get("physical_pages") or []
        textbook_pages = page.get("textbook_pages") or []

    return {
        "card_id": card_id,
        "original_quote": source_quote,
        "citation": citation,
        "display_context": compact(display_context, 520),
        "context_before": compact(context_before, 220),
        "context_after": compact(context_after, 260),
        "chapter_path": card.get("chapter_path") or (page or {}).get("chapter_path") or "",
        "page_label": page_label,
        "physical_pages": physical_pages,
        "textbook_pages": textbook_pages,
        "page_confidence": page_confidence,
        "source_line_start": card.get("source_line_start") or (page or {}).get("source_line_start"),
        "source_line_end": card.get("source_line_end") or (page or {}).get("source_line_end"),
        "quality": context_quality(source_quote, display_context, card, page),
        "card_type": card.get("type") or "",
        "evidence_scope": card.get("evidence_scope") or "",
    }


def group_edges(edges: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_ep: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        by_ep.setdefault(str(edge.get("exam_point_id")), []).append(edge)
    for rows in by_ep.values():
        rows.sort(key=lambda row: (str(row.get("question_id")), str(row.get("option")), str(row.get("card_id"))))
    return by_ep


def build_question_links(
    item: dict[str, Any],
    edges: list[dict[str, Any]],
    questions_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for edge in edges:
        key = (
            str(edge.get("question_id") or ""),
            str(edge.get("option") or ""),
            str(edge.get("card_id") or ""),
            str(edge.get("role") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        question = questions_by_id.get(str(edge.get("question_id") or ""), {})
        rows.append(
            {
                "question_id": edge.get("question_id"),
                "section": edge.get("section"),
                "stem": compact(question.get("stem"), 260),
                "answer": question.get("answer"),
                "option": edge.get("option"),
                "option_text": edge.get("option_text"),
                "role": edge.get("role"),
                "key_is_correct": edge.get("key_is_correct"),
                "judgement": edge.get("judgement"),
                "evidence_grade": edge.get("evidence_grade"),
                "evidence_status": edge.get("evidence_status"),
                "support_type": edge.get("support_type"),
                "relevance": edge.get("relevance"),
                "card_id": edge.get("card_id"),
            }
        )
    return rows


def select_items(
    named_items: list[dict[str, Any]],
    decisions_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    include_raw = os.getenv("PREVIEW_V12_INCLUDE_IDS", "").strip()
    if include_raw:
        include_ids = [item.strip() for item in include_raw.split(",") if item.strip()]
    else:
        include_ids = DEFAULT_SAMPLE_IDS

    by_id = {item["id"]: item for item in named_items}
    selected = [by_id[ep_id] for ep_id in include_ids if ep_id in by_id]
    if selected:
        return selected

    limit = int(os.getenv("PREVIEW_V12_LIMIT", "8"))
    candidates = [
        item
        for item in named_items
        if decisions_by_id.get(item["id"], {}).get("admission_status") == "evidence_supplement_candidate"
    ]
    candidates.sort(key=lambda item: (-int(item.get("question_count") or 0), item["id"]))
    return candidates[:limit]


def build_sample() -> dict[str, Any]:
    named_file = resolve_path(os.getenv("PREVIEW_V12_NAMED_FILE", str(DEFAULT_NAMED_FILE)))
    decision_file = resolve_path(os.getenv("PREVIEW_V12_DECISION_FILE", str(DEFAULT_DECISION_FILE)))
    edges_file = resolve_path(os.getenv("PREVIEW_V12_EDGES_FILE", str(DEFAULT_EDGES_FILE)))
    cards_file = resolve_path(os.getenv("PREVIEW_V12_CARDS_FILE", str(DEFAULT_CARDS_FILE)))
    page_map_file = resolve_path(os.getenv("PREVIEW_V12_PAGE_MAP_FILE", str(DEFAULT_PAGE_MAP_FILE)))
    questions_file = resolve_path(os.getenv("PREVIEW_V12_QUESTIONS_FILE", str(DEFAULT_QUESTIONS_FILE)))

    named_items = read_json(named_file)["items"]
    decisions = read_json(decision_file)["items"]
    decisions_by_id = {row["exam_point_id"]: row for row in decisions}
    edges_by_ep = group_edges(read_json(edges_file)["items"])
    cards_by_id = load_cards(cards_file)
    page_by_id = load_page_map(page_map_file)
    questions_by_id = load_questions(questions_file)

    selected = select_items(named_items, decisions_by_id)
    output_items: list[dict[str, Any]] = []
    for item in selected:
        decision = decisions_by_id.get(item["id"], {})
        contexts = [
            build_card_context(
                str(row.get("card_id")),
                str(row.get("quote") or ""),
                cards_by_id,
                page_by_id,
            )
            for row in item.get("evidence_quotes", [])
            if row.get("card_id")
        ]
        question_links = build_question_links(item, edges_by_ep.get(item["id"], []), questions_by_id)
        output_items.append(
            {
                "id": item["id"],
                "title": item.get("title"),
                "point_type": item.get("point_type"),
                "admission_status": decision.get("admission_status"),
                "recommended_actions": decision.get("recommended_actions", []),
                "decision_reasons": decision.get("decision_reasons", []),
                "question_count": item.get("question_count"),
                "core_question_count": item.get("core_question_count"),
                "contrast_question_count": item.get("contrast_question_count"),
                "card_ids": item.get("card_ids", []),
                "teaching_focus": item.get("teaching_focus"),
                "relation_summary": item.get("relation_summary"),
                "naming_risk_flags": item.get("naming_risk_flags", []),
                "naming_confidence": item.get("naming_confidence"),
                "evidence_contexts": contexts,
                "question_links": question_links,
                "context_quality_distribution": dict(Counter(row.get("quality") for row in contexts)),
            }
        )

    return {
        "schema_version": "preview_v12_evidence_context_sample_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_files": {
            "named": str(named_file),
            "decisions": str(decision_file),
            "edges": str(edges_file),
            "cards": str(cards_file),
            "page_map": str(page_map_file),
            "questions": str(questions_file),
        },
        "note": "Deterministic context supplement for evidence_supplement_candidate. It does not rename or re-admit exam points.",
        "items": output_items,
        "summary": {
            "item_count": len(output_items),
            "card_context_count": sum(len(item["evidence_contexts"]) for item in output_items),
            "question_link_count": sum(len(item["question_links"]) for item in output_items),
            "context_quality_distribution": dict(
                Counter(
                    context.get("quality")
                    for item in output_items
                    for context in item.get("evidence_contexts", [])
                )
            ),
            "page_label_count": sum(
                1
                for item in output_items
                for context in item.get("evidence_contexts", [])
                if context.get("page_label")
            ),
        },
    }


def write_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Preview v12 证据上下文补写小样本",
        "",
        "本轮只做确定性回表补写：不改考点名，不改题目链接，不改 v9 门禁结论。",
        "",
        "## 汇总",
        "",
        f"- 考点数：{payload['summary']['item_count']}",
        f"- 句卡上下文数：{payload['summary']['card_context_count']}",
        f"- 题目证据边数：{payload['summary']['question_link_count']}",
        f"- 带页码句卡数：{payload['summary']['page_label_count']}",
        f"- 上下文质量：{payload['summary']['context_quality_distribution']}",
        "",
        "## 样例",
        "",
    ]
    for item in payload["items"]:
        lines.extend(
            [
                f"### {item['id']} {item['title']}",
                f"- 状态：{item.get('admission_status')}；题目数：{item.get('question_count')}；句卡：{', '.join(item.get('card_ids') or [])}",
                f"- 考查方向：{item.get('teaching_focus')}",
                f"- 关系说明：{item.get('relation_summary')}",
                "- 教材依据：",
            ]
        )
        for context in item.get("evidence_contexts", []):
            page = f"（{context.get('page_label')}）" if context.get("page_label") else "（页码待补）"
            lines.append(
                f"  - {context.get('card_id')} {page} [{context.get('quality')}]: {context.get('display_context')}"
            )
        lines.append("- 题目链接：")
        for link in item.get("question_links", [])[:8]:
            lines.append(
                f"  - {link.get('question_id')} {link.get('option')} {link.get('role')}：{link.get('option_text')}"
            )
        lines.append("")
    (OUT_DIR / out_name("evidence_context_report", "md")).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    payload = build_sample()
    write_json(OUT_DIR / out_name("evidence_context_sample", "json"), payload)
    write_report(payload)
    print(json.dumps({"status": "ok", **payload["summary"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
