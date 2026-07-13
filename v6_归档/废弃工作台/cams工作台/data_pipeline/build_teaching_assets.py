#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build teaching-oriented exam point assets for the CAMS workbench.

This script creates a unified teaching exam-point layer from:
- option-level evidence derived exam points
- textbook sentence cards that look like basic definitions, processes, risks, laws, or categories

It also creates a sentence/card to exam-point map used by the reader.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "data" / "teaching_assets"

CHAPTER_PATH = ASSET_DIR / "chapters" / "ch2_extracted.json"
CARDS_PATH = ASSET_DIR / "cards_v6_sentence.json"
OPTION_EP_PATH = ASSET_DIR / "exam_points_from_option_evidence_mvp.json"
OPTION_EVIDENCE_PATH = ASSET_DIR / "option_evidence_map.json"
OUT_EP_PATH = ASSET_DIR / "exam_points_teaching_mvp.json"
OUT_MAP_PATH = ASSET_DIR / "sentence_exam_point_map.json"


BASIC_TYPES = {"定义", "流程", "风险指标", "法规", "分类"}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_cards(payload) -> list[dict]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("cards"), list):
        return payload["cards"]
    return []


def iter_chapter_paragraphs(chapter: dict):
    for section in chapter.get("sections", []):
        for subsection in section.get("subsections", []):
            for paragraph in subsection.get("paragraphs", []):
                yield section, subsection, paragraph


def collect_chapter_card_ids(chapter: dict) -> set[str]:
    ids: set[str] = set()
    for _, _, paragraph in iter_chapter_paragraphs(chapter):
        for cid in (paragraph.get("card_ids") or []) + (paragraph.get("highlight_card_ids") or []):
            if cid:
                ids.add(cid)
    return ids


def collect_option_traps(option_evidence: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for item in option_evidence.get("items", []):
        qid = item.get("question_id")
        for option in item.get("options", []):
            trap = (option.get("common_trap") or "").strip()
            if not trap:
                continue
            for cid in option.get("card_ids") or []:
                out[cid].append(
                    {
                        "question_id": qid,
                        "option": option.get("option", ""),
                        "option_text": option.get("option_text", ""),
                        "common_trap": trap,
                        "evidence_status": option.get("evidence_status", ""),
                        "judgement": option.get("judgement", ""),
                    }
                )
    return out


def teaching_type_from_card(card: dict) -> str:
    type_name = card.get("type") or ""
    if type_name == "定义":
        return "基础定义"
    if type_name == "流程":
        return "流程/步骤"
    if type_name == "风险指标":
        return "风险/红旗"
    if type_name == "法规":
        return "法规义务/监管"
    if type_name == "分类":
        return "分类/范围"
    return "基础教材句"


def option_ep_to_teaching(ep: dict) -> dict:
    item = dict(ep)
    item["source"] = "teaching_assets"
    item["source_types"] = sorted(set((item.get("source_types") or []) + ["question_derived_point"]))
    item["teaching_point_type"] = item.get("teaching_point_type") or "题目反推考点"
    item["display_layer"] = "question_derived"
    item["asset_note"] = "由题目、选项、解析和教材证据反推，供教研审核。"
    item["review_status"] = item.get("status") or "ai_candidate"
    return item


def build_basic_ep(card: dict, traps: list[dict]) -> dict:
    cid = card["card_id"]
    status = "ai_candidate"
    if traps:
        status = "needs_teacher_attention"
    return {
        "id": "ep_basic_" + cid.lower(),
        "title": card.get("knowledge") or card.get("citation") or cid,
        "status": status,
        "review_status": status,
        "type": teaching_type_from_card(card),
        "teaching_point_type": teaching_type_from_card(card),
        "source_types": ["basic_textbook_point"] + (["trap_supported_point"] if traps else []),
        "display_layer": "basic_textbook" if not traps else "trap_warning",
        "source_card_ids": [cid],
        "question_ids": sorted({row["question_id"] for row in traps if row.get("question_id")}),
        "qa_ids": [],
        "student_confusion": "；".join(dict.fromkeys(row["common_trap"] for row in traps if row.get("common_trap"))),
        "reason": "该句卡属于第二章教材中的%s句，作为基础教材考点纳入。%s" % (
            card.get("type") or "关键",
            "同时已有选项易错点指向该句卡。" if traps else "当前尚未确认其是否为高频出题点，需教研审核。",
        ),
        "teacher_note": "",
        "created_from": "textbook_sentence_card",
        "confidence": "medium",
        "needs": ["teacher_review"],
        "updated_at": date.today().isoformat(),
        "evidence_scope": "ch2-reader-sentence-card",
        "source": "exam_points_teaching_mvp",
        "option_bindings": [
            {
                "question_id": row["question_id"],
                "option": row["option"],
                "option_text": row["option_text"],
                "judgement": row["judgement"],
                "evidence_status": row["evidence_status"],
                "common_trap": row["common_trap"],
            }
            for row in traps
        ],
        "source_card_details": [
            {
                "card_id": cid,
                "support_type": "direct",
                "relevance": "textbook_basic",
                "quote": card.get("citation", ""),
                "knowledge": card.get("knowledge", ""),
                "reason": "教材句卡类型为%s，适合作为基础考点候选。" % (card.get("type") or "未知"),
                "chapter_path": card.get("chapter_path", ""),
                "source_line_start": card.get("source_line_start", ""),
                "source_line_end": card.get("source_line_end", ""),
            }
        ],
        "source_data_issues": [],
        "validation_issues": [],
    }


def build_sentence_map(chapter: dict, exam_points: list[dict]) -> dict:
    by_card: dict[str, list[dict]] = defaultdict(list)
    by_quote: list[tuple[str, dict, str]] = []

    for ep in exam_points:
        source_types = ep.get("source_types") or []
        display_layer = ep.get("display_layer") or "question_derived"
        for cid in ep.get("source_card_ids") or []:
            by_card[cid].append(
                {
                    "exam_point_id": ep["id"],
                    "title": ep.get("title", ""),
                    "status": ep.get("status", ""),
                    "display_layer": display_layer,
                    "source_types": source_types,
                    "question_ids": ep.get("question_ids") or [],
                }
            )
        for detail in ep.get("source_card_details") or []:
            quote = (detail.get("quote") or detail.get("citation") or "").strip()
            if len(quote) >= 8:
                by_quote.append((quote, {
                    "exam_point_id": ep["id"],
                    "title": ep.get("title", ""),
                    "status": ep.get("status", ""),
                    "display_layer": display_layer,
                    "source_types": source_types,
                    "question_ids": ep.get("question_ids") or [],
                    "card_id": detail.get("card_id", ""),
                }, detail.get("card_id", "")))

    paragraphs = []
    sentence_rows = []
    for section, subsection, paragraph in iter_chapter_paragraphs(chapter):
      paragraph_text = paragraph.get("text") or ""
      card_ids = (paragraph.get("card_ids") or []) + (paragraph.get("highlight_card_ids") or [])
      point_ids: set[str] = set()
      annotations = []

      for cid in dict.fromkeys(card_ids):
          for ep_ref in by_card.get(cid, []):
              point_ids.add(ep_ref["exam_point_id"])
              annotations.append({**ep_ref, "match_type": "card_id", "card_id": cid})

      for quote, ep_ref, cid in by_quote:
          if quote in paragraph_text:
              point_ids.add(ep_ref["exam_point_id"])
              annotations.append({**ep_ref, "match_type": "quote", "quote": quote, "card_id": cid})

      if annotations:
          paragraphs.append(
              {
                  "section_id": section.get("section_id", ""),
                  "section_title": section.get("section_title", ""),
                  "subsection_title": subsection.get("title", ""),
                  "text": paragraph_text,
                  "card_ids": list(dict.fromkeys(card_ids)),
                  "exam_point_ids": sorted(point_ids),
                  "annotations": annotations,
              }
          )
          for annotation in annotations:
              sentence_rows.append(
                  {
                      "card_id": annotation.get("card_id", ""),
                      "quote": annotation.get("quote", ""),
                      "exam_point_id": annotation["exam_point_id"],
                      "display_layer": annotation["display_layer"],
                      "match_type": annotation["match_type"],
                      "section_id": section.get("section_id", ""),
                      "subsection_title": subsection.get("title", ""),
                  }
              )

    return {
        "version": "0.1",
        "asset_note": "原文句子/句卡到教研考点的映射，供阅读区显示考点和易错预警。",
        "generated_at": date.today().isoformat(),
        "stats": {
            "paragraphs_with_exam_points": len(paragraphs),
            "sentence_rows": len(sentence_rows),
            "mapped_exam_points": len({row["exam_point_id"] for row in sentence_rows}),
        },
        "paragraphs": paragraphs,
        "sentences": sentence_rows,
    }


def main() -> None:
    chapter = read_json(CHAPTER_PATH)
    cards = normalize_cards(read_json(CARDS_PATH))
    option_ep = read_json(OPTION_EP_PATH)
    option_evidence = read_json(OPTION_EVIDENCE_PATH)

    chapter_card_ids = collect_chapter_card_ids(chapter)
    card_by_id = {card.get("card_id"): card for card in cards if card.get("card_id")}
    traps_by_card = collect_option_traps(option_evidence)

    exam_points = [option_ep_to_teaching(ep) for ep in option_ep.get("exam_points", [])]
    existing_cards = {
        cid
        for ep in exam_points
        for cid in (ep.get("source_card_ids") or [])
    }

    basic_points = []
    for cid in sorted(chapter_card_ids):
        if cid in existing_cards:
            continue
        card = card_by_id.get(cid)
        if not card or card.get("type") not in BASIC_TYPES:
            continue
        basic_points.append(build_basic_ep(card, traps_by_card.get(cid, [])))

    exam_points.extend(basic_points)
    exam_points.sort(key=lambda ep: (ep.get("display_layer") != "basic_textbook", ep.get("id", "")))

    output = {
        "version": "0.1",
        "asset_note": "教研视角统一考点层：整合基础教材句、题目选项证据和易错提示。所有非 confirmed 项均需教研审核。",
        "source_assets": [
            "cards_v6_sentence.json",
            "chapters/ch2_extracted.json",
            "option_evidence_map.json",
            "exam_points_from_option_evidence_mvp.json",
        ],
        "generated_at": date.today().isoformat(),
        "stats": {
            "total_exam_points": len(exam_points),
            "question_derived_points": len(option_ep.get("exam_points", [])),
            "basic_textbook_points": len(basic_points),
            "basic_types": dict(sorted(
                defaultdict(int, {
                    type_name: sum(1 for ep in basic_points if ep.get("type") == type_name)
                    for type_name in {ep.get("type") for ep in basic_points}
                }).items()
            )),
        },
        "exam_points": exam_points,
    }
    write_json(OUT_EP_PATH, output)
    write_json(OUT_MAP_PATH, build_sentence_map(chapter, exam_points))
    print(json.dumps({
        "wrote": [str(OUT_EP_PATH), str(OUT_MAP_PATH)],
        "stats": output["stats"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
