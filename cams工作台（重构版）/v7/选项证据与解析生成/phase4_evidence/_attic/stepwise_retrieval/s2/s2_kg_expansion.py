# -*- coding: utf-8 -*-
"""s2: KG expansion from s1 direct unit seeds.

This script keeps s0a/s0b and baseline/test variants independent. It does not
run retrieval or LLM calls. KG output is candidate context with readable paths.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
STEPWISE = HERE.parent
TESTS = STEPWISE.parent
PHASE4 = TESTS.parent
WORKSPACE = PHASE4.parent
V7_ROOT = WORKSPACE.parent

S1_INPUT_ROOT = STEPWISE / "s1" / "output" / "s1_direct_unit_retrieval"
KG_GRAPH_PATH = (
    V7_ROOT
    / "知识图谱提取"
    / "phases"
    / "phase06_kg_views"
    / "outputs"
    / "kg_retrieval_graph.json"
)
OUTPUT_DIR = HERE / "output"

EXPERIMENTS = ("s0a", "s0b")
VARIANTS = ("query_baseline", "query_test")

EDGE_SCOPE_WEIGHTS = {
    "same_section_core_point": 0.90,
    "same_chapter_core_point": 0.70,
    "cross_chapter_core_point": 0.45,
}
RELATION_WEIGHTS = {
    "grounds": 1.00,
    "contains": 0.92,
    "prepares": 0.82,
    "summarizes": 0.78,
    "illustrates": 0.70,
    "parallels": 0.58,
    "contrasts": 0.45,
}
ORIGIN_WEIGHTS = {
    "direct_seed": 1.00,
    "same_core_point": 0.82,
    "related_core_point_edge": 0.66,
    "section_context": 0.42,
}


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def append_unique(bucket: list[str], value: str) -> None:
    if value and value not in bucket:
        bucket.append(value)


def load_kg_graph(path: Path) -> dict[str, Any]:
    kg = load_json(path)
    unit_meta: dict[str, dict[str, Any]] = {}
    cp_meta: dict[str, dict[str, Any]] = {}
    cp_to_units: dict[str, list[str]] = defaultdict(list)
    unit_to_cps: dict[str, list[str]] = defaultdict(list)
    cp_edges: dict[str, list[dict[str, Any]]] = defaultdict(list)
    section_to_cps: dict[str, list[str]] = defaultdict(list)

    for unit in kg.get("units", []) or []:
        uid = unit.get("unit_id")
        if uid:
            unit_meta[uid] = unit

    for cp in kg.get("core_points", []) or []:
        cp_id = cp.get("core_point_id")
        if not cp_id:
            continue
        cp_meta[cp_id] = cp
        section_id = cp.get("section_id", "")
        append_unique(section_to_cps[section_id], cp_id)
        for key in ("key_unit_ids", "anchor_unit_ids", "support_unit_ids"):
            for uid in cp.get(key, []) or []:
                append_unique(cp_to_units[cp_id], uid)
                append_unique(unit_to_cps[uid], cp_id)

    relation_scopes = set(EDGE_SCOPE_WEIGHTS)
    for edge in kg.get("edges", []) or []:
        scope = edge.get("edge_scope", "")
        source_id = edge.get("source_id", "")
        target_id = edge.get("target_id", "")
        if scope == "core_point_unit":
            append_unique(cp_to_units[source_id], target_id)
            append_unique(unit_to_cps[target_id], source_id)
        elif scope == "section_core_point":
            append_unique(section_to_cps[source_id], target_id)
        elif scope in relation_scopes:
            cp_edges[source_id].append(edge)
            cp_edges[target_id].append(edge)

    def unit_sort_key(uid: str) -> tuple[str, int, str]:
        unit = unit_meta.get(uid, {})
        return (unit.get("chapter_id", ""), int(unit.get("unit_order") or 0), uid)

    for cp_id in list(cp_to_units):
        cp_to_units[cp_id] = sorted(cp_to_units[cp_id], key=unit_sort_key)

    return {
        "raw": kg,
        "unit_meta": unit_meta,
        "cp_meta": cp_meta,
        "cp_to_units": dict(cp_to_units),
        "unit_to_cps": dict(unit_to_cps),
        "cp_edges": dict(cp_edges),
        "section_to_cps": dict(section_to_cps),
    }


def unit_summary(unit: dict[str, Any]) -> dict[str, Any]:
    return {
        "knowledge_zh": unit.get("knowledge_zh", ""),
        "knowledge_en": unit.get("knowledge_en", ""),
        "en_quote": unit.get("en_quote", ""),
        "chapter_id": unit.get("chapter_id", ""),
        "section_id": unit.get("section_id", ""),
        "unit_order": unit.get("unit_order"),
        "type": unit.get("type", ""),
        "printed_page": unit.get("printed_page", ""),
        "pdf_page": unit.get("pdf_page", ""),
    }


def cp_label(cp: dict[str, Any]) -> str:
    return cp.get("title_zh") or cp.get("title_en") or cp.get("core_point_id", "")


def seed_score(seed: dict[str, Any], seed_rank: int, seed_count: int) -> float:
    score = float(seed.get("best_score_norm") or 0.0)
    if score > 0:
        return score
    if seed_count <= 1:
        return 1.0
    return 1.0 - ((seed_rank - 1) / seed_count)


def make_path(*parts: str) -> str:
    return " -> ".join(part for part in parts if part)


def make_direct_record(seed: dict[str, Any], seed_rank: int, seed_count: int, kg: dict[str, Any]) -> dict[str, Any]:
    uid = seed.get("unit_id", "")
    unit = kg["unit_meta"].get(uid, {})
    score = seed_score(seed, seed_rank, seed_count)
    return {
        "unit_id": uid,
        "origin": "direct_seed",
        "seed_unit_id": uid,
        "seed_rank": seed_rank,
        "seed_score": round(score, 6),
        "kg_score": round(score * ORIGIN_WEIGHTS["direct_seed"], 6),
        "path_readable": uid,
        "source": "s1_direct_retrieval",
        "unit": unit_summary(unit),
    }


def make_same_cp_record(
    target_uid: str,
    seed_uid: str,
    seed_rank: int,
    seed_count: int,
    seed: dict[str, Any],
    cp_id: str,
    kg: dict[str, Any],
) -> dict[str, Any]:
    unit = kg["unit_meta"].get(target_uid, {})
    cp = kg["cp_meta"].get(cp_id, {})
    score = seed_score(seed, seed_rank, seed_count)
    kg_score = score * ORIGIN_WEIGHTS["same_core_point"]
    return {
        "unit_id": target_uid,
        "origin": "same_core_point",
        "seed_unit_id": seed_uid,
        "seed_rank": seed_rank,
        "seed_core_point_id": cp_id,
        "target_core_point_id": cp_id,
        "core_point": {"core_point_id": cp_id, "title": cp_label(cp), "section_id": cp.get("section_id", "")},
        "score_components": {"seed_score": round(score, 6), "origin_weight": ORIGIN_WEIGHTS["same_core_point"]},
        "kg_score": round(kg_score, 6),
        "path_readable": make_path(seed_uid, cp_id, target_uid),
        "unit": unit_summary(unit),
    }


def edge_other_cp(edge: dict[str, Any], cp_id: str) -> str:
    source = edge.get("source_id", "")
    target = edge.get("target_id", "")
    return target if source == cp_id else source


def edge_direction(edge: dict[str, Any], cp_id: str) -> str:
    if edge.get("source_id") == cp_id:
        return "outgoing"
    if edge.get("target_id") == cp_id:
        return "incoming"
    return "undirected_view"


def make_edge_record(
    target_uid: str,
    seed_uid: str,
    seed_rank: int,
    seed_count: int,
    seed: dict[str, Any],
    seed_cp_id: str,
    target_cp_id: str,
    edge: dict[str, Any],
    kg: dict[str, Any],
) -> dict[str, Any]:
    unit = kg["unit_meta"].get(target_uid, {})
    target_cp = kg["cp_meta"].get(target_cp_id, {})
    relation = edge.get("relation_type", "")
    scope = edge.get("edge_scope", "")
    direction = edge_direction(edge, seed_cp_id)
    score = seed_score(seed, seed_rank, seed_count)
    relation_weight = RELATION_WEIGHTS.get(relation, 0.50)
    scope_weight = EDGE_SCOPE_WEIGHTS.get(scope, 0.50)
    kg_score = score * ORIGIN_WEIGHTS["related_core_point_edge"] * relation_weight * scope_weight
    return {
        "unit_id": target_uid,
        "origin": "related_core_point_edge",
        "seed_unit_id": seed_uid,
        "seed_rank": seed_rank,
        "seed_core_point_id": seed_cp_id,
        "target_core_point_id": target_cp_id,
        "target_core_point": {
            "core_point_id": target_cp_id,
            "title": cp_label(target_cp),
            "section_id": target_cp.get("section_id", ""),
        },
        "edge": {
            "edge_id": edge.get("edge_id", ""),
            "edge_scope": scope,
            "relation_type": relation,
            "direction_from_seed_cp": direction,
            "reason": edge.get("reason", ""),
        },
        "score_components": {
            "seed_score": round(score, 6),
            "origin_weight": ORIGIN_WEIGHTS["related_core_point_edge"],
            "relation_weight": relation_weight,
            "edge_scope_weight": scope_weight,
        },
        "kg_score": round(kg_score, 6),
        "path_readable": f"{seed_uid} -> {seed_cp_id} --{relation}/{scope}/{direction}--> {target_cp_id} -> {target_uid}",
        "unit": unit_summary(unit),
    }


def make_section_record(
    target_uid: str,
    seed_uid: str,
    seed_rank: int,
    seed_count: int,
    seed: dict[str, Any],
    seed_cp_id: str,
    target_cp_id: str,
    kg: dict[str, Any],
) -> dict[str, Any]:
    unit = kg["unit_meta"].get(target_uid, {})
    cp = kg["cp_meta"].get(target_cp_id, {})
    score = seed_score(seed, seed_rank, seed_count)
    kg_score = score * ORIGIN_WEIGHTS["section_context"]
    return {
        "unit_id": target_uid,
        "origin": "section_context",
        "seed_unit_id": seed_uid,
        "seed_rank": seed_rank,
        "seed_core_point_id": seed_cp_id,
        "target_core_point_id": target_cp_id,
        "target_core_point": {"core_point_id": target_cp_id, "title": cp_label(cp), "section_id": cp.get("section_id", "")},
        "score_components": {"seed_score": round(score, 6), "origin_weight": ORIGIN_WEIGHTS["section_context"]},
        "kg_score": round(kg_score, 6),
        "path_readable": f"{seed_uid} -> {seed_cp_id} -> section:{cp.get('section_id', '')} -> {target_cp_id} -> {target_uid}",
        "unit": unit_summary(unit),
    }


def add_best(records_by_uid: dict[str, dict[str, Any]], record: dict[str, Any]) -> None:
    uid = record.get("unit_id")
    if not uid:
        return
    if uid not in records_by_uid or float(record.get("kg_score") or 0.0) > float(records_by_uid[uid].get("kg_score") or 0.0):
        records_by_uid[uid] = record


def expand_variant(
    variant_doc: dict[str, Any],
    kg: dict[str, Any],
    seed_top_k: int,
    same_cp_unit_limit: int,
    related_cp_limit: int,
    related_cp_unit_limit: int,
    section_cp_limit: int,
    section_unit_limit: int,
    allow_cross_chapter: bool,
) -> dict[str, Any]:
    seeds = (variant_doc.get("merged_units", []) or [])[:seed_top_k]
    seed_count = max(len(seeds), 1)
    records_by_uid: dict[str, dict[str, Any]] = {}
    seed_records: list[dict[str, Any]] = []
    no_cp_seed_ids: list[str] = []

    for seed_rank, seed in enumerate(seeds, start=1):
        seed_uid = seed.get("unit_id", "")
        direct = make_direct_record(seed, seed_rank, seed_count, kg)
        seed_records.append(direct)
        add_best(records_by_uid, direct)

        cp_ids = kg["unit_to_cps"].get(seed_uid, [])
        if not cp_ids:
            no_cp_seed_ids.append(seed_uid)
            continue

        for cp_id in cp_ids:
            siblings = [uid for uid in kg["cp_to_units"].get(cp_id, []) if uid != seed_uid]
            for target_uid in siblings[:same_cp_unit_limit]:
                add_best(records_by_uid, make_same_cp_record(target_uid, seed_uid, seed_rank, seed_count, seed, cp_id, kg))

            related_seen = 0
            for edge in kg["cp_edges"].get(cp_id, []):
                scope = edge.get("edge_scope", "")
                if scope == "cross_chapter_core_point" and not allow_cross_chapter:
                    continue
                target_cp_id = edge_other_cp(edge, cp_id)
                if not target_cp_id or target_cp_id == cp_id:
                    continue
                related_seen += 1
                if related_seen > related_cp_limit:
                    break
                target_units = kg["cp_to_units"].get(target_cp_id, [])
                for target_uid in target_units[:related_cp_unit_limit]:
                    if target_uid == seed_uid:
                        continue
                    add_best(records_by_uid, make_edge_record(target_uid, seed_uid, seed_rank, seed_count, seed, cp_id, target_cp_id, edge, kg))

            if section_cp_limit > 0 and section_unit_limit > 0:
                cp = kg["cp_meta"].get(cp_id, {})
                section_id = cp.get("section_id", "")
                section_cps = [sid for sid in kg["section_to_cps"].get(section_id, []) if sid != cp_id]
                for target_cp_id in section_cps[:section_cp_limit]:
                    for target_uid in kg["cp_to_units"].get(target_cp_id, [])[:section_unit_limit]:
                        if target_uid == seed_uid:
                            continue
                        add_best(records_by_uid, make_section_record(target_uid, seed_uid, seed_rank, seed_count, seed, cp_id, target_cp_id, kg))

    expanded = list(records_by_uid.values())
    expanded.sort(key=lambda row: float(row.get("kg_score") or 0.0), reverse=True)
    return {
        "query": variant_doc.get("query", ""),
        "label": variant_doc.get("label", ""),
        "direct_seed_units": seed_records,
        "expanded_units": expanded,
        "metrics": compute_metrics(seed_records, expanded, no_cp_seed_ids),
    }


def compute_metrics(seed_records: list[dict[str, Any]], expanded: list[dict[str, Any]], no_cp_seed_ids: list[str]) -> dict[str, Any]:
    seed_ids = {row.get("unit_id") for row in seed_records}
    added = [row for row in expanded if row.get("unit_id") not in seed_ids]
    origins = Counter(row.get("origin", "") for row in expanded)
    scopes = Counter((row.get("edge") or {}).get("edge_scope", "") for row in expanded if row.get("origin") == "related_core_point_edge")
    relations = Counter((row.get("edge") or {}).get("relation_type", "") for row in expanded if row.get("origin") == "related_core_point_edge")
    core_points = {row.get("target_core_point_id") for row in expanded if row.get("target_core_point_id")}
    sections = {row.get("unit", {}).get("section_id") for row in expanded if row.get("unit", {}).get("section_id")}
    cross = scopes.get("cross_chapter_core_point", 0)
    edge_total = sum(scopes.values())
    return {
        "direct_seed_unit_count": len(seed_records),
        "kg_added_unit_count": len(added),
        "total_unit_count": len(expanded),
        "covered_core_point_count": len(core_points),
        "covered_section_count": len(sections),
        "origin_distribution": dict(origins),
        "edge_scope_distribution": dict(scopes),
        "relation_distribution": dict(relations),
        "cross_chapter_expansion_ratio": round(cross / edge_total, 4) if edge_total else 0.0,
        "average_added_units_per_seed": round(len(added) / max(len(seed_records), 1), 4),
        "seed_without_core_point_count": len(no_cp_seed_ids),
        "seed_without_core_point_ids": no_cp_seed_ids,
    }


def build_s2_doc(s1_doc: dict[str, Any], input_path: Path, kg: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    head_docs: list[dict[str, Any]] = []
    for head in s1_doc.get("heads", []) or []:
        variant_docs: dict[str, Any] = {}
        for variant in VARIANTS:
            source_variant = (head.get("variants", {}) or {}).get(variant, {})
            variant_docs[variant] = expand_variant(
                source_variant,
                kg=kg,
                seed_top_k=args.seed_top_k,
                same_cp_unit_limit=args.same_cp_unit_limit,
                related_cp_limit=args.related_cp_limit,
                related_cp_unit_limit=args.related_cp_unit_limit,
                section_cp_limit=args.section_cp_limit,
                section_unit_limit=args.section_unit_limit,
                allow_cross_chapter=args.allow_cross_chapter,
            )
        head_docs.append(
            {
                "head_id": head.get("head_id"),
                "head_kind": head.get("head_kind"),
                "option": head.get("option"),
                "parts": head.get("parts", []),
                "baseline_label": head.get("baseline_label", ""),
                "test_label": head.get("test_label", ""),
                "variants": variant_docs,
            }
        )

    return {
        "step": "s2_kg_expansion",
        "source_experiment": s1_doc.get("source_experiment"),
        "source_step": s1_doc.get("step"),
        "source_file": str(input_path),
        "question_id": s1_doc.get("question_id"),
        "stem": s1_doc.get("stem", ""),
        "options": s1_doc.get("options", {}),
        "policy": {
            "purpose": "expand s1 direct unit seeds through KG while preserving paths",
            "no_bge_bm25": True,
            "no_llm": True,
            "no_answer_judgement": True,
            "kg_units_are_candidate_context": True,
            "output_target": "s3 KG micro-textbook rendering",
        },
        "params": {
            "seed_top_k": args.seed_top_k,
            "same_cp_unit_limit": args.same_cp_unit_limit,
            "related_cp_limit": args.related_cp_limit,
            "related_cp_unit_limit": args.related_cp_unit_limit,
            "section_cp_limit": args.section_cp_limit,
            "section_unit_limit": args.section_unit_limit,
            "allow_cross_chapter": args.allow_cross_chapter,
        },
        "heads": head_docs,
    }


def one_line(text: str, max_len: int = 100) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def render_units(rows: list[dict[str, Any]], limit: int) -> str:
    lines = ["| rank | origin | unit_id | kg_score | path | 摘要 |\n"]
    lines.append("|---:|---|---|---:|---|---|\n")
    for rank, row in enumerate(rows[:limit], start=1):
        unit = row.get("unit", {}) or {}
        summary = unit.get("knowledge_zh") or unit.get("en_quote") or ""
        lines.append(
            f"| {rank} | {row.get('origin', '')} | `{row.get('unit_id', '')}` | {row.get('kg_score', '')} "
            f"| {one_line(row.get('path_readable'), 80)} | {one_line(summary, 80)} |\n"
        )
    if not rows:
        lines.append("| - | - | - | - | - | 无 |\n")
    return "".join(lines)


def render_md(doc: dict[str, Any], table_limit: int = 12) -> str:
    lines: list[str] = []
    exp = doc.get("source_experiment", "")
    lines.append(f"# {doc['question_id']} s2 KG扩展 {exp}\n\n")
    lines.append("## s2定位\n\n")
    lines.append("- KG 从 s1 的 direct unit_id 接入。\n")
    lines.append("- 每个扩展 unit 保留路径。\n")
    lines.append("- KG 边关系先可观察再筛选。\n")
    lines.append("- 输出面向后续 s3 微缩教材渲染。\n\n")
    lines.append(f"题干：{doc.get('stem', '')}\n\n")
    for head in doc.get("heads", []) or []:
        lines.append(f"## {head.get('head_id')}\n\n")
        for variant in VARIANTS:
            vdoc = (head.get("variants", {}) or {}).get(variant, {})
            lines.append(f"### {variant}: {vdoc.get('label', '')}\n\n")
            metrics = vdoc.get("metrics", {}) or {}
            lines.append(
                f"seed={metrics.get('direct_seed_unit_count', 0)} | "
                f"kg_added={metrics.get('kg_added_unit_count', 0)} | "
                f"total={metrics.get('total_unit_count', 0)} | "
                f"core_points={metrics.get('covered_core_point_count', 0)} | "
                f"sections={metrics.get('covered_section_count', 0)} | "
                f"cross_ratio={metrics.get('cross_chapter_expansion_ratio', 0)}\n\n"
            )
            lines.append(f"origin_distribution: `{json.dumps(metrics.get('origin_distribution', {}), ensure_ascii=False)}`\n\n")
            lines.append(render_units(vdoc.get("expanded_units", []) or [], table_limit))
            lines.append("\n")
    return "".join(lines)


def resolve_input_files(experiments: list[str], question_ids: list[str], input_file: str | None) -> list[tuple[str, Path]]:
    if input_file:
        path = Path(input_file)
        data = load_json(path)
        exp = str(data.get("source_experiment", ""))
        if exp not in EXPERIMENTS:
            raise ValueError(f"cannot detect s1 experiment from {path}")
        return [(exp, path)]
    pairs: list[tuple[str, Path]] = []
    for exp in experiments:
        input_dir = S1_INPUT_ROOT / exp
        if question_ids:
            pairs.extend((exp, input_dir / f"{qid}.s1.{exp}.json") for qid in question_ids)
        else:
            pairs.extend((exp, path) for path in sorted(input_dir.glob(f"*.s1.{exp}.json")))
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(description="s2: KG expansion from s1 direct unit seeds")
    parser.add_argument("--question-id", action="append", default=[])
    parser.add_argument("--experiment", choices=["s0a", "s0b", "all"], default="all")
    parser.add_argument("--input-file", default=None)
    parser.add_argument("--kg-path", default=str(KG_GRAPH_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--seed-top-k", type=int, default=8)
    parser.add_argument("--same-cp-unit-limit", type=int, default=6)
    parser.add_argument("--related-cp-limit", type=int, default=4)
    parser.add_argument("--related-cp-unit-limit", type=int, default=4)
    parser.add_argument("--section-cp-limit", type=int, default=0)
    parser.add_argument("--section-unit-limit", type=int, default=0)
    parser.add_argument("--allow-cross-chapter", action="store_true")
    args = parser.parse_args()

    experiments = list(EXPERIMENTS) if args.experiment == "all" else [args.experiment]
    input_pairs = resolve_input_files(experiments, args.question_id, args.input_file)
    missing = [str(path) for _, path in input_pairs if not path.exists()]
    if missing:
        raise FileNotFoundError("s1 input missing: " + "; ".join(missing))
    if not input_pairs:
        raise FileNotFoundError("no s1 input files found")

    print(f"[kg] load {args.kg_path}")
    kg = load_kg_graph(Path(args.kg_path))
    print(
        f"[kg] ready units={len(kg['unit_meta'])} cps={len(kg['cp_meta'])} "
        f"unit_to_cps={len(kg['unit_to_cps'])} cp_edges={sum(len(v) for v in kg['cp_edges'].values())}"
    )

    output_dir = Path(args.output_dir)
    index_rows: list[dict[str, str]] = []
    for exp, input_path in input_pairs:
        s1_doc = load_json(input_path)
        doc = build_s2_doc(s1_doc, input_path, kg, args)
        qid = doc["question_id"]
        exp_dir = output_dir / exp
        json_path = exp_dir / f"{qid}.s2.{exp}.json"
        md_path = exp_dir / f"{qid}.s2.{exp}.md"
        write_json(json_path, doc)
        write_text(md_path, render_md(doc))
        index_rows.append({"experiment": exp, "question_id": qid, "json": str(json_path), "markdown": str(md_path)})
        print(f"[ok] {exp} {qid} -> {json_path}")
    write_json(output_dir / "index.json", index_rows)


if __name__ == "__main__":
    main()
