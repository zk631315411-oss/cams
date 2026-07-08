from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
WORK_DIR = SCRIPT_DIR.parent
APP_DIR = WORK_DIR.parent
DATA_DIR = APP_DIR / "data" / "teaching_assets"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize(text: Any) -> str:
    return re.sub(
        r"[，。；：、“”‘’（）()\[\]【】,.?:;\"'\-\s]",
        "",
        str(text or ""),
    )


def bigram_similarity(a: Any, b: Any) -> float:
    a = normalize(a)
    b = normalize(b)
    if not a or not b:
        return 0.0
    if a in b or b in a:
        return min(len(a), len(b)) / max(len(a), len(b))
    if len(a) < 2 or len(b) < 2:
        return 1.0 if a == b else 0.0
    aa = {a[i : i + 2] for i in range(len(a) - 1)}
    bb = {b[i : i + 2] for i in range(len(b) - 1)}
    return len(aa & bb) / (len(aa | bb) or 1)


def collect_reader_card_ids(chapter: Any) -> set[str]:
    ids: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if not isinstance(node, dict):
            return
        for key in ["cardIds", "card_ids", "highlightCardIds", "highlight_card_ids"]:
            value = node.get(key)
            if isinstance(value, list):
                ids.update(str(item) for item in value if item)
        for value in node.values():
            walk(value)

    walk(chapter)
    return ids


def collect_reader_card_locations(chapter: Any) -> dict[str, dict[str, Any]]:
    locations: dict[str, dict[str, Any]] = {}
    chapter_title = chapter.get("chapter", "")
    for section in chapter.get("sections", []):
        section_title = section.get("section_title", "")
        for subsection in section.get("subsections", []):
            subsection_title = subsection.get("title", "")
            path = " > ".join(
                part
                for part in [chapter_title, section_title, subsection_title]
                if part
            )
            for paragraph in subsection.get("paragraphs", []):
                ids = (paragraph.get("card_ids") or []) + (paragraph.get("highlight_card_ids") or [])
                for cid in ids:
                    if cid and cid not in locations:
                        locations[cid] = {
                            "chapter_path": path,
                            "source_line_start": paragraph.get("source_line_start", ""),
                            "source_line_end": paragraph.get("source_line_end", ""),
                        }
    return locations


def collect_reader_paragraph_locations(chapter: Any) -> list[dict[str, Any]]:
    rows = []
    chapter_title = chapter.get("chapter", "")
    for section in chapter.get("sections", []):
        section_title = section.get("section_title", "")
        for subsection in section.get("subsections", []):
            subsection_title = subsection.get("title", "")
            path = " > ".join(
                part
                for part in [chapter_title, section_title, subsection_title]
                if part
            )
            for paragraph in subsection.get("paragraphs", []):
                rows.append(
                    {
                        "chapter_path": path,
                        "source_line_start": paragraph.get("source_line_start", ""),
                        "source_line_end": paragraph.get("source_line_end", ""),
                        "text": paragraph.get("text", ""),
                    }
                )
    return rows


def best_reader_matches(
    source_id: str,
    source_cards_by_id: dict[str, dict[str, Any]],
    reader_cards: list[dict[str, Any]],
    reader_card_ids: set[str],
    threshold: float,
) -> list[dict[str, Any]]:
    if source_id in reader_card_ids:
        return [{"card_id": source_id, "score": 1.0, "match_type": "same_id"}]

    source = source_cards_by_id.get(source_id)
    if not source:
        return []
    source_texts = [
        source.get("card_knowledge"),
        source.get("card_quote"),
        source.get("title"),
    ]
    source_texts = [text for text in source_texts if text]
    if not source_texts:
        return []

    matches = []
    for card in reader_cards:
        cid = card.get("card_id")
        if cid not in reader_card_ids:
            continue
        target_texts = [card.get("knowledge"), card.get("citation")]
        score = max(
            bigram_similarity(src, tgt)
            for src in source_texts
            for tgt in target_texts
            if tgt
        )
        if score >= threshold:
            matches.append(
                {
                    "card_id": cid,
                    "score": round(score, 4),
                    "match_type": "text_similarity",
                    "source_card_id": source_id,
                }
            )
    matches.sort(key=lambda item: (-item["score"], item["card_id"]))
    return matches[:2]


def build_source_card_index(work_dir: Path) -> dict[str, dict[str, Any]]:
    cards = read_json(work_dir / "outputs" / "evidence_card_scores.json").get("cards", [])
    return {card["card_id"]: card for card in cards if card.get("card_id")}


def corrected_location_from_line(
    line_no: Any,
    reader_locations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    try:
        line = int(line_no)
    except (TypeError, ValueError):
        return {}
    best = {}
    best_distance = None
    for location in reader_locations.values():
        try:
            start = int(location.get("source_line_start") or 0)
            end = int(location.get("source_line_end") or start)
        except (TypeError, ValueError):
            continue
        if not start:
            continue
        if start <= line <= end:
            return location
        distance = min(abs(line - start), abs(line - end))
        if best_distance is None or distance < best_distance:
            best = location
            best_distance = distance
    if best_distance is not None and best_distance <= 3:
        return best
    return {}


def corrected_location_from_text(
    card: dict[str, Any],
    reader_paragraphs: list[dict[str, Any]],
) -> dict[str, Any]:
    source_texts = [
        card.get("card_quote", ""),
        card.get("card_knowledge", ""),
        card.get("quote", ""),
        card.get("knowledge", ""),
    ]
    source_texts = [text for text in source_texts if len(normalize(text)) >= 4]
    if not source_texts:
        return {}
    best = {}
    best_score = 0.0
    for paragraph in reader_paragraphs:
        text = paragraph.get("text", "")
        text_norm = normalize(text)
        for source in source_texts:
            source_norm = normalize(source)
            if source_norm and (source_norm in text_norm or text_norm in source_norm):
                return {
                    "chapter_path": paragraph.get("chapter_path", ""),
                    "source_line_start": paragraph.get("source_line_start", ""),
                    "source_line_end": paragraph.get("source_line_end", ""),
                }
        score = max((bigram_similarity(source, text) for source in source_texts), default=0.0)
        if score > best_score:
            best = paragraph
            best_score = score
    if best_score >= 0.62:
        return {
            "chapter_path": best.get("chapter_path", ""),
            "source_line_start": best.get("source_line_start", ""),
            "source_line_end": best.get("source_line_end", ""),
        }
    return {}


def source_card_detail(
    card_id: str,
    source_cards_by_id: dict[str, dict[str, Any]],
    reader_locations: dict[str, dict[str, Any]] | None = None,
    reader_paragraphs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    card = source_cards_by_id.get(card_id, {})
    corrected = corrected_location_from_text(card, reader_paragraphs or {})
    if not corrected:
        corrected = corrected_location_from_line(card.get("source_line_start"), reader_locations or {})
    return {
        "card_id": card_id,
        "support_type": card.get("support_type", ""),
        "relevance": card.get("relevance", ""),
        "knowledge": card.get("card_knowledge", ""),
        "quote": card.get("card_quote", ""),
        "chapter_path": corrected.get("chapter_path") or card.get("chapter_path", ""),
        "source_line_start": corrected.get("source_line_start") or card.get("source_line_start", ""),
        "source_line_end": corrected.get("source_line_end") or card.get("source_line_end", ""),
        "question_ids": card.get("question_ids", []),
        "qa_ids": card.get("qa_ids_for_question", []) or card.get("qa_ids_for_card", []),
    }


def build_reader_source_details(
    ep: dict[str, Any],
    reader_ids: list[str],
    source_to_reader: dict[str, list[dict[str, Any]]],
    source_cards_by_id: dict[str, dict[str, Any]],
    reader_cards_by_id: dict[str, dict[str, Any]],
    reader_locations: dict[str, dict[str, Any]],
    reader_paragraphs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    original_details = {
        (detail.get("card_id") or detail.get("id")): detail
        for detail in ep.get("source_card_details", [])
        if detail.get("card_id") or detail.get("id")
    }
    reader_to_source: dict[str, str] = {}
    for source_id, matches in source_to_reader.items():
        for match in matches:
            reader_to_source.setdefault(match["card_id"], source_id)

    details = []
    for reader_id in reader_ids:
        source_id = reader_to_source.get(reader_id, reader_id)
        detail = dict(original_details.get(source_id) or source_card_detail(source_id, source_cards_by_id, reader_locations, reader_paragraphs))
        reader_card = reader_cards_by_id.get(reader_id, {})
        location = reader_locations.get(reader_id, {})
        detail["card_id"] = reader_id
        if source_id != reader_id:
            detail["original_source_card_id"] = source_id
        detail["knowledge"] = detail.get("knowledge") or reader_card.get("knowledge", "")
        detail["quote"] = detail.get("quote") or detail.get("citation") or reader_card.get("citation", "")
        if location:
            detail["chapter_path"] = location.get("chapter_path", "")
            detail["source_line_start"] = location.get("source_line_start", "")
            detail["source_line_end"] = location.get("source_line_end", "")
        details.append(detail)
    return details


def convert(work_dir: Path, data_dir: Path, threshold: float) -> tuple[dict[str, Any], dict[str, Any]]:
    curated = read_json(work_dir / "outputs" / "exam_points_curated_mvp.json")
    source_cards_by_id = build_source_card_index(work_dir)
    reader_cards = read_json(data_dir / "cards_v6_sentence.json").get("cards", [])
    chapter = read_json(data_dir / "chapters" / "ch2_extracted.json")
    reader_card_ids = collect_reader_card_ids(chapter)
    reader_locations = collect_reader_card_locations(chapter)
    reader_paragraphs = collect_reader_paragraph_locations(chapter)
    reader_cards_by_id = {card["card_id"]: card for card in reader_cards if card.get("card_id")}

    converted_points = []
    mapping_rows = []
    no_reader_hit = []

    for ep in curated.get("exam_points", []):
        original_ids = ep.get("source_card_ids") or []
        reader_ids = []
        external_ids = []
        source_to_reader: dict[str, list[dict[str, Any]]] = {}
        for source_id in original_ids:
            matches = best_reader_matches(source_id, source_cards_by_id, reader_cards, reader_card_ids, threshold)
            if matches:
                source_to_reader[source_id] = matches
                for match in matches:
                    if match["card_id"] not in reader_ids:
                        reader_ids.append(match["card_id"])
                mapping_rows.extend(matches)
            elif source_id not in external_ids:
                external_ids.append(source_id)
        if not reader_ids:
            no_reader_hit.append(ep["id"])

        item = dict(ep)
        item["original_source_card_ids"] = original_ids
        item["reader_source_card_ids"] = reader_ids
        item["external_source_card_ids"] = external_ids
        item["external_source_card_details"] = [
            source_card_detail(source_id, source_cards_by_id, reader_locations, reader_paragraphs) for source_id in external_ids
        ]
        item["source_card_details"] = build_reader_source_details(
            ep,
            reader_ids,
            source_to_reader,
            source_cards_by_id,
            reader_cards_by_id,
            reader_locations,
            reader_paragraphs,
        )
        item["source_to_reader_card_map"] = source_to_reader
        item["source_card_ids"] = reader_ids
        item["evidence_scope"] = "ch2-reader-sentence-card"
        item["external_evidence_scope"] = "cross-chapter-source-card" if external_ids else ""
        item["source"] = "exam_points_curated_mvp_frontend"
        converted_points.append(item)

    payload = {
        "version": curated.get("version", "0.1"),
        "asset_note": "前端阅读区可定位版 curated 考点。source_card_ids 已映射为阅读页 v6s 句卡，original_source_card_ids 保留原候选证据卡。",
        "source_assets": [
            "考点确认/outputs/exam_points_curated_mvp.json",
            "考点确认/outputs/evidence_card_scores.json",
            "data/teaching_assets/cards_v6_sentence.json",
            "data/teaching_assets/chapters/ch2_extracted.json",
        ],
        "stats": {
            "curated_points": len(converted_points),
            "points_with_reader_source": sum(1 for ep in converted_points if ep.get("reader_source_card_ids")),
            "points_without_reader_source": len(no_reader_hit),
            "points_with_external_source": sum(1 for ep in converted_points if ep.get("external_source_card_ids")),
            "external_source_cards": len({cid for ep in converted_points for cid in ep.get("external_source_card_ids", [])}),
            "unique_reader_cards": len({cid for ep in converted_points for cid in ep.get("reader_source_card_ids", [])}),
            "mapping_rows": len(mapping_rows),
            "threshold": threshold,
        },
        "exam_points": converted_points,
    }
    report = {
        "stats": payload["stats"],
        "no_reader_hit_ids": no_reader_hit,
        "mapping_rows": mapping_rows,
    }
    return payload, report


def render_report(payload: dict[str, Any], report: dict[str, Any]) -> str:
    stats = payload["stats"]
    lines = [
        "# 前端可定位 Curated 考点报告",
        "",
        f"- 考点数：{stats['curated_points']}",
        f"- 可定位考点：{stats['points_with_reader_source']}",
        f"- 不可定位考点：{stats['points_without_reader_source']}",
        f"- 唯一阅读页句卡：{stats['unique_reader_cards']}",
        f"- 映射行数：{stats['mapping_rows']}",
        f"- 相似度阈值：{stats['threshold']}",
        "",
        "## 不可定位考点",
        "",
    ]
    id_to_title = {ep["id"]: ep["title"] for ep in payload.get("exam_points", [])}
    if not report["no_reader_hit_ids"]:
        lines.append("- 无")
    else:
        for eid in report["no_reader_hit_ids"]:
            lines.append(f"- {eid}: {id_to_title.get(eid, '')}")

    lines += ["", "## 考点映射概览", ""]
    for ep in payload.get("exam_points", []):
        lines += [
            f"### {ep['title']}",
            "",
            f"- 原始证据卡：{', '.join(ep.get('original_source_card_ids') or [])}",
            f"- 阅读页句卡：{', '.join(ep.get('reader_source_card_ids') or [])}",
            "",
        ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build frontend-readable curated exam points.")
    parser.add_argument("--work-dir", type=Path, default=WORK_DIR)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--threshold", type=float, default=0.62)
    args = parser.parse_args()

    payload, report = convert(args.work_dir, args.data_dir, args.threshold)
    local_out = args.work_dir / "outputs" / "exam_points_curated_frontend.json"
    target = args.data_dir / "exam_points_curated_mvp.json"
    write_json(local_out, payload)
    write_json(args.work_dir / "outputs" / "reader_card_mapping_report.json", report)
    (args.work_dir / "reports" / "frontend_curated_mapping_report.md").write_text(
        render_report(payload, report),
        encoding="utf-8",
    )
    shutil.copyfile(local_out, target)
    print(local_out)
    print(target)
    print(json.dumps(payload["stats"], ensure_ascii=False))


if __name__ == "__main__":
    main()
