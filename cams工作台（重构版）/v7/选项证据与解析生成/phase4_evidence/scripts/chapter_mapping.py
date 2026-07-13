# -*- coding: utf-8 -*-
"""构建确定性章节候选并校验人工审核的章节映射。

候选生成仅使用直接 BGE/BM25 相似度，不调用任何 LLM，也绝不读取旧题库中的
``chapter_code`` 字段。候选数据包与人工审核决定是两个独立产物。
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from blind_adjudication import (
    BM25,
    INDEX_PKL,
    KG_GRAPH_PATH,
    QUESTIONS_PATH,
    bm25_search,
    get_bge_model,
    load_index,
    load_questions,
)


HERE = Path(__file__).resolve().parent
PHASE4 = HERE.parent
DEFAULT_OUTPUT_DIR = PHASE4 / "chapter_mapping"
DEFAULT_CANDIDATES_PATH = DEFAULT_OUTPUT_DIR / "chapter_similarity_candidates.jsonl"
DEFAULT_MAPPINGS_PATH = DEFAULT_OUTPUT_DIR / "question_chapter_mappings.jsonl"

RRF_K = 60


def load_kg_catalog(path: str | Path) -> dict[str, Any]:
    """加载 KG 母版并构建章节/节/单元索引。"""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    chapters = {row["chapter_id"]: row for row in raw.get("chapters", [])}
    sections = {row["section_id"]: row for row in raw.get("sections", [])}
    units = {row["unit_id"]: row for row in raw.get("units", [])}
    if len(chapters) != 59:
        raise RuntimeError(f"KG 章节数应为 59，实际为 {len(chapters)}")
    return {"raw": raw, "chapters": chapters, "sections": sections, "units": units}


def build_query_heads(question: dict[str, Any]) -> list[dict[str, str]]:
    """构建题目中英文查询头（题干 + 题干拼接各选项）。"""
    heads: list[dict[str, str]] = []
    stem = str(question.get("stem", "") or "").strip()
    stem_en = str(question.get("stem_en", "") or "").strip()
    if stem:
        heads.append({"head_id": "stem_zh", "language": "zh", "query": stem})
    if stem_en:
        heads.append({"head_id": "stem_en", "language": "en", "query": stem_en})

    options = question.get("options", {}) or {}
    options_en = question.get("options_en", {}) or {}
    for label, text in options.items():
        query = f"{stem} {text}".strip()
        if query:
            heads.append(
                {"head_id": f"option_{label}_zh", "language": "zh", "query": query}
            )
    for label, text in options_en.items():
        query = f"{stem_en} {text}".strip()
        if query:
            heads.append(
                {"head_id": f"option_{label}_en", "language": "en", "query": query}
            )
    return heads


def _result_record(
    row: dict[str, Any], head: dict[str, str], route: str
) -> dict[str, Any]:
    """从检索行与查询头构建标准化命中记录。"""
    return {
        "head_id": head["head_id"],
        "language": head["language"],
        "route": route,
        "rank": int(row["rank"]),
        "raw_score": float(row["score"]),
        "unit_id": row["unit_id"],
    }


def retrieve_heads(
    heads: list[dict[str, str]],
    index: dict[str, Any],
    bm25_zh: BM25,
    bm25_en: BM25,
    top_k: int,
) -> list[dict[str, Any]]:
    """对一组查询头执行批量 BGE 编码 + 中英文 BM25，返回所有命中行。"""
    rows: list[dict[str, Any]] = []
    if heads:
        model = get_bge_model()
        vectors = model.encode(
            [head["query"] for head in heads], normalize_embeddings=True
        )
        similarities = cosine_similarity(vectors, index["bge_vecs"])
        for head, scores in zip(heads, similarities):
            top_indices = np.argsort(scores)[::-1][:top_k]
            for rank, idx in enumerate(top_indices, start=1):
                uid = index["card_ids"][idx]
                rows.append(
                    {
                        "head_id": head["head_id"],
                        "language": head["language"],
                        "route": "bge",
                        "rank": rank,
                        "raw_score": round(float(scores[idx]), 6),
                        "unit_id": uid,
                    }
                )

    for head in heads:
        query = head["query"]
        bm25 = bm25_en if head["language"] == "en" else bm25_zh
        route = "bm25_en" if head["language"] == "en" else "bm25_zh"
        for row in bm25_search(
            query, bm25, index["card_ids"], index["unit_lookup"], top_k
        ):
            rows.append(_result_record(row, head, route))
    return rows


def aggregate_candidates(
    retrieval_rows: list[dict[str, Any]],
    catalog: dict[str, Any],
    unit_lookup: dict[str, dict[str, Any]],
    max_chapters: int = 8,
    representative_units: int = 5,
) -> list[dict[str, Any]]:
    """将检索命中行汇总为按章节 RRF 分数排序的候选列表。"""
    unit_hits: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in retrieval_rows:
        unit_hits[row["unit_id"]].append(row)

    unit_scores: dict[str, float] = {}
    for uid, hits in unit_hits.items():
        unit_scores[uid] = sum(1.0 / (RRF_K + int(hit["rank"])) for hit in hits)

    chapter_units: dict[str, list[str]] = defaultdict(list)
    for uid in unit_scores:
        kg_unit = catalog["units"].get(uid)
        if kg_unit and kg_unit.get("chapter_id"):
            chapter_units[kg_unit["chapter_id"]].append(uid)

    chapter_rows: list[dict[str, Any]] = []
    for chapter_id, unit_ids in chapter_units.items():
        unit_ids.sort(key=lambda uid: (-unit_scores[uid], uid))
        all_hits = [hit for uid in unit_ids for hit in unit_hits[uid]]
        head_ids = sorted({hit["head_id"] for hit in all_hits})
        languages = sorted({hit["language"] for hit in all_hits})
        routes = sorted({hit["route"] for hit in all_hits})
        option_heads = sorted({h for h in head_ids if h.startswith("option_")})
        representative: list[dict[str, Any]] = []
        section_ids: list[str] = []
        for uid in unit_ids[:representative_units]:
            kg_unit = catalog["units"][uid]
            section_id = kg_unit.get("section_id", "")
            if section_id and section_id not in section_ids:
                section_ids.append(section_id)
            unit = unit_lookup.get(uid, {})
            hits = sorted(
                unit_hits[uid], key=lambda h: (h["rank"], h["head_id"], h["route"])
            )
            representative.append(
                {
                    "unit_id": uid,
                    "section_id": section_id,
                    "rrf_score": round(unit_scores[uid], 8),
                    "knowledge_zh": unit.get("knowledge_zh", ""),
                    "en_quote": unit.get("en_quote", ""),
                    "heading_context": unit.get("heading_context", []),
                    "hits": hits,
                }
            )
        chapter = catalog["chapters"][chapter_id]
        chapter_rows.append(
            {
                "chapter_id": chapter_id,
                "chapter_title": chapter.get("chapter_title", ""),
                "rrf_score": round(sum(unit_scores[uid] for uid in unit_ids), 8),
                "matched_head_count": len(head_ids),
                "matched_option_head_count": len(option_heads),
                "languages": languages,
                "routes": routes,
                "section_ids": section_ids,
                "representative_units": representative,
            }
        )
    chapter_rows.sort(
        key=lambda row: (
            -float(row["rrf_score"]),
            -int(row["matched_head_count"]),
            row["chapter_id"],
        )
    )
    return chapter_rows[:max_chapters]


def build_candidate_packet(
    question: dict[str, Any],
    index: dict[str, Any],
    catalog: dict[str, Any],
    bm25_zh: BM25,
    bm25_en: BM25,
    top_k: int,
) -> dict[str, Any]:
    """对一道题构建完整的章节相似度候选数据包。"""
    heads = build_query_heads(question)
    retrieval_rows = retrieve_heads(heads, index, bm25_zh, bm25_en, top_k)
    return {
        "schema_version": "v7_chapter_similarity_candidates_v1",
        "question_id": question["question_id"],
        "question_type": question.get("question_type", ""),
        "stem": question.get("stem", ""),
        "stem_en": question.get("stem_en", ""),
        "options": question.get("options", {}),
        "options_en": question.get("options_en", {}),
        "risk_flags": question.get("risk_flags", []),
        "query_heads": heads,
        "chapter_candidates": aggregate_candidates(
            retrieval_rows, catalog, index["unit_lookup"]
        ),
        "retrieval_rows": retrieval_rows,
    }


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """加载 JSONL 文件为字典列表。"""
    rows: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"{path}:{line_no}: JSON 解析失败: {exc}") from exc
    return rows


def write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    """将字典列表写入 JSONL 文件。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def mapping_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """按 question_id 索引章节映射行。"""
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        qid = str(row.get("question_id", ""))
        if not qid:
            raise RuntimeError("章节映射存在空 question_id")
        if qid in index:
            raise RuntimeError(f"章节映射存在重复 question_id: {qid}")
        index[qid] = row
    return index


def validate_mappings(
    mapping_rows: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    catalog: dict[str, Any],
) -> list[str]:
    """校验章节映射的完整性、章节存在性及支撑单元归属。"""
    errors: list[str] = []
    question_ids = {q["question_id"] for q in questions}
    try:
        by_qid = mapping_index(mapping_rows)
    except RuntimeError as exc:
        return [str(exc)]

    missing = sorted(question_ids - set(by_qid))
    extra = sorted(set(by_qid) - question_ids)
    if missing:
        errors.append(f"缺少 {len(missing)} 个题号: {', '.join(missing[:10])}")
    if extra:
        errors.append(f"存在 {len(extra)} 个未知题号: {', '.join(extra[:10])}")

    for qid, row in by_qid.items():
        mappings = row.get("chapter_mappings", []) or []
        status = row.get("mapping_status", "")
        if not mappings and status not in {"needs_source_repair", "unmapped"}:
            errors.append(f"{qid}: 无章节但 mapping_status={status!r}")
        seen_chapters: set[str] = set()
        for mapping in mappings:
            chapter_id = mapping.get("chapter_id", "")
            if chapter_id in seen_chapters:
                errors.append(f"{qid}: 章节重复 {chapter_id}")
            seen_chapters.add(chapter_id)
            if chapter_id not in catalog["chapters"]:
                errors.append(f"{qid}: 未知 chapter_id={chapter_id}")
                continue
            for section_id in mapping.get("section_ids", []) or []:
                section = catalog["sections"].get(section_id)
                if not section:
                    errors.append(f"{qid}: 未知 section_id={section_id}")
                elif section.get("chapter_id") != chapter_id:
                    errors.append(
                        f"{qid}: {section_id} 不属于 {chapter_id}"
                    )
            support = mapping.get("supporting_unit_ids", []) or []
            if not support:
                errors.append(f"{qid}: {chapter_id} 缺少 supporting_unit_ids")
            for uid in support:
                unit = catalog["units"].get(uid)
                if not unit:
                    errors.append(f"{qid}: 未知 supporting unit={uid}")
                elif unit.get("chapter_id") != chapter_id:
                    errors.append(f"{qid}: {uid} 不属于 {chapter_id}")
    return errors


def build_batches(
    mapping_rows: list[dict[str, Any]], catalog: dict[str, Any], output_dir: str | Path
) -> None:
    """按章节生成题目批次 JSON 文件。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    batches: dict[str, list[str]] = {cid: [] for cid in catalog["chapters"]}
    for row in mapping_rows:
        qid = row["question_id"]
        for mapping in row.get("chapter_mappings", []) or []:
            cid = mapping["chapter_id"]
            if qid not in batches[cid]:
                batches[cid].append(qid)
    for cid, qids in batches.items():
        qids.sort()
        chapter = catalog["chapters"][cid]
        payload = {
            "schema_version": "v7_chapter_batch_v1",
            "chapter_id": cid,
            "chapter_title": chapter.get("chapter_title", ""),
            "question_count": len(qids),
            "question_ids": qids,
        }
        with open(output_dir / f"{cid}.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)


def materialize_reviewed_mappings(
    candidate_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """将人工/Agent 的显式决定展开为最终映射 schema。"""
    candidates = {row["question_id"]: row for row in candidate_rows}
    decisions = mapping_index(decision_rows)
    missing = sorted(set(candidates) - set(decisions))
    extra = sorted(set(decisions) - set(candidates))
    if missing or extra:
        raise RuntimeError(
            f"人工决定与候选题号不一致: missing={missing[:10]}, extra={extra[:10]}"
        )

    output: list[dict[str, Any]] = []
    for qid in sorted(candidates):
        packet = candidates[qid]
        decision = decisions[qid]
        selected_ids = decision.get("chapter_ids", []) or []
        candidate_by_chapter = {
            row["chapter_id"]: row for row in packet.get("chapter_candidates", [])
        }
        mappings: list[dict[str, Any]] = []
        for chapter_id in selected_ids:
            candidate = candidate_by_chapter.get(chapter_id)
            if not candidate:
                raise RuntimeError(f"{qid}: 人工选择 {chapter_id} 不在相似度候选中")
            units = candidate.get("representative_units", []) or []
            support_ids = [row["unit_id"] for row in units[:3]]
            section_ids: list[str] = []
            for row in units[:3]:
                section_id = row.get("section_id", "")
                if section_id and section_id not in section_ids:
                    section_ids.append(section_id)
            custom_reasons = decision.get("reasons", {}) or {}
            mappings.append(
                {
                    "chapter_id": chapter_id,
                    "chapter_title": candidate.get("chapter_title", ""),
                    "section_ids": section_ids,
                    "supporting_unit_ids": support_ids,
                    "confidence": decision.get("confidence", "medium"),
                    "decision_method": "agent_review",
                    "reason": custom_reasons.get(
                        chapter_id,
                        f"题干与选项直接命中该章教材内容，代表证据为{','.join(support_ids)}。",
                    ),
                }
            )
        needs_repair = bool(decision.get("needs_source_repair", False))
        output.append(
            {
                "question_id": qid,
                "chapter_mappings": mappings,
                "mapping_status": (
                    "needs_source_repair" if needs_repair and not mappings else "mapped"
                ),
                "needs_source_repair": needs_repair,
                "review_note": str(decision.get("review_note", "") or ""),
            }
        )
    return output


def decisions_from_review_policy(
    candidate_rows: list[dict[str, Any]], policy: dict[str, Any]
) -> list[dict[str, Any]]:
    """从 Agent 审核策略中为每道题生成显式决定。

    策略记录了已审核的默认规则及题级修正项。展开后的最终产物不含隐式/默认决定。
    """
    if policy.get("default_decision") != "accept_top_similarity_candidate":
        raise RuntimeError("review policy 缺少受支持的 default_decision")
    overrides = policy.get("overrides", {}) or {}
    known = {row["question_id"] for row in candidate_rows}
    unknown_overrides = sorted(set(overrides) - known)
    if unknown_overrides:
        raise RuntimeError(f"review policy 包含未知题号: {unknown_overrides[:10]}")
    rows: list[dict[str, Any]] = []
    for packet in candidate_rows:
        qid = packet["question_id"]
        candidates = packet.get("chapter_candidates", []) or []
        if not candidates:
            rows.append(
                {
                    "question_id": qid,
                    "chapter_ids": [],
                    "confidence": "low",
                    "needs_source_repair": True,
                    "review_note": "直接相似检索未形成章节候选。",
                }
            )
            continue
        override = overrides.get(qid, {}) or {}
        rows.append(
            {
                "question_id": qid,
                "chapter_ids": override.get(
                    "chapter_ids", [candidates[0]["chapter_id"]]
                ),
                "confidence": override.get(
                    "confidence", policy.get("default_confidence", "medium")
                ),
                "needs_source_repair": override.get("needs_source_repair", False),
                "review_note": override.get("review_note", ""),
                "reasons": override.get("reasons", {}),
            }
        )
    return rows


def write_review(path: str | Path, rows: list[dict[str, Any]]) -> None:
    """将候选数据包写入人读审查 Markdown。"""
    lines = ["# 题目章节映射审查\n\n"]
    for row in rows:
        lines.append(f"## {row['question_id']}\n\n")
        lines.append(f"题干：{row.get('stem', '')}\n\n")
        for candidate in row.get("chapter_candidates", []) or []:
            lines.append(
                f"### {candidate['chapter_id']} {candidate['chapter_title']}"
                f" | RRF={candidate['rrf_score']}\n\n"
            )
            for unit in candidate.get("representative_units", []) or []:
                lines.append(
                    f"- `{unit['unit_id']}` / `{unit.get('section_id', '')}`："
                    f"{unit.get('knowledge_zh', '')}\n"
                )
        lines.append("\n")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def write_mapping_review(
    path: str | Path,
    mapping_rows: list[dict[str, Any]],
    questions: list[dict[str, Any]],
) -> None:
    """将最终映射写入人读审查 Markdown。"""
    question_by_id = {row["question_id"]: row for row in questions}
    lines = ["# 最终题目章节映射审查\n\n"]
    lines.append(f"题目总数：{len(mapping_rows)}\n\n")
    for row in mapping_rows:
        qid = row["question_id"]
        question = question_by_id.get(qid, {})
        lines.append(f"## {qid}\n\n")
        lines.append(f"题干：{question.get('stem', '')}\n\n")
        if row.get("needs_source_repair"):
            lines.append(f"状态：需修复题源。{row.get('review_note', '')}\n\n")
        for mapping in row.get("chapter_mappings", []) or []:
            lines.append(
                f"- `{mapping['chapter_id']}` {mapping.get('chapter_title', '')}"
                f"（{mapping.get('confidence', '')}）：{mapping.get('reason', '')}"
                f" 支撑：{', '.join(mapping.get('supporting_unit_ids', []) or [])}\n"
            )
        lines.append("\n")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def make_bm25(index: dict[str, Any]) -> tuple[BM25, BM25]:
    """从索引字典构建中英文 BM25 检索器。"""
    return (
        BM25(index["zh_bm25_docs"], index["zh_bm25_df"], index["zh_bm25_avgdl"]),
        BM25(index["en_bm25_docs"], index["en_bm25_df"], index["en_bm25_avgdl"]),
    )


def command_candidates(args: argparse.Namespace) -> None:
    """子命令 candidates：生成确定性章节相似度候选。"""
    questions = load_questions(args.questions_path)
    if args.question_id:
        wanted = set(args.question_id)
        questions = [q for q in questions if q["question_id"] in wanted]
        missing = wanted - {q["question_id"] for q in questions}
        if missing:
            raise RuntimeError(f"指定题号不存在: {', '.join(sorted(missing))}")
    elif args.limit:
        questions = questions[: args.limit]

    index = load_index(args.index_path)
    catalog = load_kg_catalog(args.kg_graph_path)
    bm25_zh, bm25_en = make_bm25(index)
    get_bge_model()
    rows: list[dict[str, Any]] = []
    for i, question in enumerate(questions, start=1):
        row = build_candidate_packet(
            question, index, catalog, bm25_zh, bm25_en, args.top_k
        )
        rows.append(row)
        top = row["chapter_candidates"][0]["chapter_id"] if row["chapter_candidates"] else "?"
        print(f"[{i}/{len(questions)}] {question['question_id']} | top={top}")
    write_jsonl(args.output, rows)
    write_review(Path(args.output).with_suffix(".md"), rows)
    print(f"[output] {args.output}")


def command_validate(args: argparse.Namespace) -> None:
    """子命令 validate：校验人工决定并生成章节批次。"""
    questions = load_questions(args.questions_path)
    catalog = load_kg_catalog(args.kg_graph_path)
    mappings = load_jsonl(args.mapping_path)
    errors = validate_mappings(mappings, questions, catalog)
    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        raise SystemExit(1)
    build_batches(mappings, catalog, args.batch_dir)
    write_mapping_review(args.review_path, mappings, questions)
    print(f"[OK] {len(mappings)} 题映射通过校验")
    print(f"[output] chapter_batches={args.batch_dir}")
    print(f"[output] review={args.review_path}")


def command_finalize(args: argparse.Namespace) -> None:
    """子命令 finalize：物化人工确认的章节决定。"""
    candidates = load_jsonl(args.candidates_path)
    decisions_path = Path(args.decisions_path)
    if decisions_path.suffix.lower() == ".json":
        with open(decisions_path, "r", encoding="utf-8") as f:
            policy = json.load(f)
        decisions = decisions_from_review_policy(candidates, policy)
    else:
        decisions = load_jsonl(decisions_path)
    mappings = materialize_reviewed_mappings(candidates, decisions)
    write_jsonl(args.output, mappings)
    print(f"[OK] 已物化 {len(mappings)} 题人工章节决定")
    print(f"[output] {args.output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="V7 题目教材章节相似度映射")
    sub = parser.add_subparsers(dest="command", required=True)

    candidates = sub.add_parser("candidates", help="生成确定性相似度候选")
    candidates.add_argument("--questions-path", default=str(QUESTIONS_PATH))
    candidates.add_argument("--index-path", default=str(INDEX_PKL))
    candidates.add_argument("--kg-graph-path", default=str(KG_GRAPH_PATH))
    candidates.add_argument("--question-id", action="append", default=[])
    candidates.add_argument("--limit", type=int, default=0)
    candidates.add_argument("--top-k", type=int, default=20)
    candidates.add_argument("--output", default=str(DEFAULT_CANDIDATES_PATH))
    candidates.set_defaults(func=command_candidates)

    finalize = sub.add_parser("finalize", help="物化人工确认的章节决定")
    finalize.add_argument("--candidates-path", default=str(DEFAULT_CANDIDATES_PATH))
    finalize.add_argument(
        "--decisions-path", default=str(DEFAULT_OUTPUT_DIR / "reviewed_decisions.jsonl")
    )
    finalize.add_argument("--output", default=str(DEFAULT_MAPPINGS_PATH))
    finalize.set_defaults(func=command_finalize)

    validate = sub.add_parser("validate", help="校验人工决定并生成章节批次")
    validate.add_argument("--questions-path", default=str(QUESTIONS_PATH))
    validate.add_argument("--kg-graph-path", default=str(KG_GRAPH_PATH))
    validate.add_argument("--mapping-path", default=str(DEFAULT_MAPPINGS_PATH))
    validate.add_argument(
        "--batch-dir", default=str(DEFAULT_OUTPUT_DIR / "chapter_batches")
    )
    validate.add_argument(
        "--review-path",
        default=str(DEFAULT_OUTPUT_DIR / "question_chapter_mapping_review.md"),
    )
    validate.set_defaults(func=command_validate)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    main()
