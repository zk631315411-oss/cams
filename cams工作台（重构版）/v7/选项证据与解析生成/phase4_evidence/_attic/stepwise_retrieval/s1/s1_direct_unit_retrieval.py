# -*- coding: utf-8 -*-
"""s1: direct unit retrieval for independent s0 A/B tests.

s0a, s0b, and s0c are separate experiments:
- s0a compares original field heads with P5-normalized heads.
- s0b compares original heads with P5 alias-expanded heads.
- s0c compares original heads with P5 canonical-inline heads.

s1 only runs direct BGE/BM25 retrieval. It does not run KG expansion, call an
LLM, or judge answers.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
STEPWISE = HERE.parent
TESTS = STEPWISE.parent
PHASE4 = TESTS.parent
SCRIPTS = PHASE4 / "scripts"
sys.path.insert(0, str(SCRIPTS))

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import blind_adjudication as ba  # noqa: E402


S0A_INPUT_DIR = STEPWISE / "s0" / "output" / "s0a_p5_heads"
S0B_INPUT_DIR = STEPWISE / "s0" / "output" / "s0b_alias_expanded_heads"
S0C_INPUT_DIR = STEPWISE / "s0" / "output" / "s0c_canonical_inline_heads"
OUTPUT_DIR = HERE / "output" / "s1_direct_unit_retrieval"

EXPERIMENTS = ("s0a", "s0b", "s0c")
VARIANTS = ("query_baseline", "query_test")
ROUTES = ("bge", "bm25_zh", "bm25_en")


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


def normalize_route_scores(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    scores = [float(row.get("score") or 0.0) for row in rows]
    min_score = min(scores)
    max_score = max(scores)
    out: list[dict[str, Any]] = []
    for row in rows:
        raw = float(row.get("score") or 0.0)
        if max_score > min_score:
            norm = (raw - min_score) / (max_score - min_score)
        else:
            norm = 1.0 if raw > 0 else 0.0
        item = dict(row)
        item["raw_score"] = round(raw, 6)
        item["score_norm"] = round(norm, 6)
        item.pop("score", None)
        out.append(item)
    return out


def compact_unit(row: dict[str, Any], head: dict[str, Any], query_variant: str, route: str) -> dict[str, Any]:
    return {
        "head_id": head.get("head_id"),
        "head_kind": head.get("head_kind"),
        "option": head.get("option"),
        "query_variant": query_variant,
        "route": route,
        "rank": row.get("rank"),
        "unit_id": row.get("unit_id"),
        "raw_score": row.get("raw_score"),
        "score_norm": row.get("score_norm"),
        "knowledge_zh": row.get("knowledge_zh", ""),
        "knowledge_en": row.get("knowledge_en", ""),
        "en_quote": row.get("en_quote", ""),
        "heading_context": row.get("heading_context", []),
        "type": row.get("type", ""),
    }


def search_one_query(
    query: str,
    head: dict[str, Any],
    query_variant: str,
    index: dict[str, Any],
    bm25_zh: ba.BM25,
    bm25_en: ba.BM25,
    top_k: int,
    bm25_min_score: float,
) -> dict[str, list[dict[str, Any]]]:
    card_ids = index["card_ids"]
    unit_lookup = index["unit_lookup"]

    by_route: dict[str, list[dict[str, Any]]] = {}
    bge_rows = normalize_route_scores(
        ba.bge_search(query, index["bge_vecs"], card_ids, unit_lookup, top_k=top_k)
    )
    by_route["bge"] = [compact_unit(row, head, query_variant, "bge") for row in bge_rows]

    bm25_zh_rows = [
        row
        for row in ba.bm25_search(query, bm25_zh, card_ids, unit_lookup, top_k=top_k)
        if float(row.get("score") or 0.0) > bm25_min_score
    ]
    by_route["bm25_zh"] = [
        compact_unit(row, head, query_variant, "bm25_zh")
        for row in normalize_route_scores(bm25_zh_rows)
    ]

    bm25_en_rows = [
        row
        for row in ba.bm25_search(query, bm25_en, card_ids, unit_lookup, top_k=top_k)
        if float(row.get("score") or 0.0) > bm25_min_score
    ]
    by_route["bm25_en"] = [
        compact_unit(row, head, query_variant, "bm25_en")
        for row in normalize_route_scores(bm25_en_rows)
    ]
    return by_route


def merge_units(route_results: dict[str, list[dict[str, Any]]], merged_top_k: int) -> list[dict[str, Any]]:
    by_uid: dict[str, dict[str, Any]] = {}
    for route, rows in route_results.items():
        for row in rows:
            uid = row.get("unit_id")
            if not uid:
                continue
            hit = {
                "route": route,
                "rank": row.get("rank"),
                "raw_score": row.get("raw_score"),
                "score_norm": row.get("score_norm"),
            }
            if uid not in by_uid:
                by_uid[uid] = {
                    "unit_id": uid,
                    "best_score_norm": row.get("score_norm", 0.0),
                    "best_route": route,
                    "knowledge_zh": row.get("knowledge_zh", ""),
                    "knowledge_en": row.get("knowledge_en", ""),
                    "en_quote": row.get("en_quote", ""),
                    "heading_context": row.get("heading_context", []),
                    "type": row.get("type", ""),
                    "route_hits": [hit],
                }
                continue
            by_uid[uid]["route_hits"].append(hit)
            if float(row.get("score_norm") or 0.0) > float(by_uid[uid].get("best_score_norm") or 0.0):
                by_uid[uid]["best_score_norm"] = row.get("score_norm", 0.0)
                by_uid[uid]["best_route"] = route

    merged = list(by_uid.values())
    merged.sort(
        key=lambda item: (
            float(item.get("best_score_norm") or 0.0),
            len(item.get("route_hits", [])),
        ),
        reverse=True,
    )
    return merged[:merged_top_k]


def diff_variants(variant_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    baseline = variant_results.get("query_baseline", {}).get("merged_units", [])
    test = variant_results.get("query_test", {}).get("merged_units", [])
    baseline_ids = [row["unit_id"] for row in baseline]
    test_ids = [row["unit_id"] for row in test]
    baseline_set = set(baseline_ids)
    test_set = set(test_ids)
    by_uid = {row["unit_id"]: row for row in baseline + test}
    return {
        "added_by_test": [by_uid[uid] for uid in test_ids if uid not in baseline_set],
        "dropped_by_test": [by_uid[uid] for uid in baseline_ids if uid not in test_set],
        "common_unit_ids": [uid for uid in test_ids if uid in baseline_set],
    }


def should_keep_head(head: dict[str, Any], include_all_options: bool) -> bool:
    head_kind = head.get("head_kind")
    if head_kind in {"stem", "option"}:
        return True
    if head.get("head_id") == "all_options":
        return include_all_options
    return False


def original_query_from_parts(source_doc: dict[str, Any], head: dict[str, Any]) -> str:
    fields = source_doc.get("fields", {}) or {}
    parts = head.get("parts", []) or []
    texts = []
    for part in parts:
        field = fields.get(part, {}) or {}
        text = field.get("text") or field.get("original_text") or ""
        if text:
            texts.append(str(text))
    if texts:
        return " ".join(texts).strip()
    return str(head.get("query_original") or head.get("query_zh") or "").strip()


def make_ab_head(source_doc: dict[str, Any], head: dict[str, Any], experiment: str) -> dict[str, Any]:
    if experiment == "s0a":
        return {
            "head_id": head.get("head_id"),
            "head_kind": head.get("head_kind"),
            "option": head.get("option"),
            "parts": head.get("parts", []),
            "query_baseline": original_query_from_parts(source_doc, head),
            "query_test": str(head.get("query_zh") or "").strip(),
            "baseline_label": "original_field_head",
            "test_label": "s0a_p5_normalized_head",
            "p5_terms": head.get("p5_terms", []),
            "query_alias_hints": [],
            "alias_hits": [],
        }
    if experiment == "s0b":
        return {
            "head_id": head.get("head_id"),
            "head_kind": head.get("head_kind"),
            "option": head.get("option"),
            "parts": head.get("parts", []),
            "query_baseline": str(head.get("query_original") or "").strip(),
            "query_test": str(head.get("query_expanded") or "").strip(),
            "baseline_label": "query_original",
            "test_label": "s0b_query_expanded",
            "p5_terms": [],
            "query_alias_hints": head.get("query_alias_hints", []),
            "alias_hits": head.get("alias_hits", []),
        }
    if experiment == "s0c":
        return {
            "head_id": head.get("head_id"),
            "head_kind": head.get("head_kind"),
            "option": head.get("option"),
            "parts": head.get("parts", []),
            "query_baseline": str(head.get("query_original") or "").strip(),
            "query_test": str(head.get("query_canonical") or "").strip(),
            "baseline_label": "query_original",
            "test_label": "s0c_query_canonical",
            "p5_terms": [],
            "query_alias_hints": [],
            "alias_hits": head.get("canonical_inline_hits", []),
        }
    raise ValueError(f"unknown experiment: {experiment}")


def build_s1_doc(
    source_doc: dict[str, Any],
    experiment: str,
    input_path: Path,
    index: dict[str, Any],
    bm25_zh: ba.BM25,
    bm25_en: ba.BM25,
    top_k: int,
    merged_top_k: int,
    bm25_min_score: float,
    include_all_options: bool,
) -> dict[str, Any]:
    head_docs: list[dict[str, Any]] = []
    for raw_head in source_doc.get("retrieval_heads", []) or []:
        if not should_keep_head(raw_head, include_all_options=include_all_options):
            continue
        head = make_ab_head(source_doc, raw_head, experiment)
        variant_results: dict[str, dict[str, Any]] = {}
        for variant in VARIANTS:
            query = str(head.get(variant, "") or "").strip()
            route_results = search_one_query(
                query=query,
                head=head,
                query_variant=variant,
                index=index,
                bm25_zh=bm25_zh,
                bm25_en=bm25_en,
                top_k=top_k,
                bm25_min_score=bm25_min_score,
            )
            variant_results[variant] = {
                "label": head["baseline_label"] if variant == "query_baseline" else head["test_label"],
                "query": query,
                "route_results": route_results,
                "merged_units": merge_units(route_results, merged_top_k=merged_top_k),
            }
        head_docs.append(
            {
                "head_id": head.get("head_id"),
                "head_kind": head.get("head_kind"),
                "option": head.get("option"),
                "parts": head.get("parts", []),
                "baseline_label": head["baseline_label"],
                "test_label": head["test_label"],
                "p5_terms": head.get("p5_terms", []),
                "query_alias_hints": head.get("query_alias_hints", []),
                "alias_hits": head.get("alias_hits", []),
                "variants": variant_results,
                "variant_diff": diff_variants(variant_results),
            }
        )

    contrast = {
        "s0a": "original field head vs P5-normalized head",
        "s0b": "query_original vs P5 alias-expanded query",
        "s0c": "query_original vs P5 canonical-inline query",
    }[experiment]
    return {
        "step": "s1_direct_unit_retrieval",
        "source_experiment": experiment,
        "source_step": source_doc.get("step"),
        "source_file": str(input_path),
        "question_id": source_doc.get("question_id"),
        "stem": source_doc.get("stem", ""),
        "options": source_doc.get("options", {}),
        "policy": {
            "purpose": f"run direct BGE/BM25 retrieval for {experiment} A/B test",
            "contrast": contrast,
            "no_kg_expansion": True,
            "no_llm": True,
            "p5_role": "query transformation only; not direct evidence",
            "default_heads": "stem plus stem+single-option heads",
        },
        "params": {
            "top_k_per_route": top_k,
            "merged_top_k_per_variant": merged_top_k,
            "bm25_min_score": bm25_min_score,
            "include_all_options": include_all_options,
            "routes": list(ROUTES),
            "query_variants": list(VARIANTS),
        },
        "heads": head_docs,
    }


def one_line(text: str, max_len: int = 120) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def render_units_table(rows: list[dict[str, Any]], limit: int) -> str:
    lines = ["| rank | unit_id | best_route | score_norm | 摘要 |\n"]
    lines.append("|---:|---|---|---:|---|\n")
    for rank, row in enumerate(rows[:limit], start=1):
        lines.append(
            f"| {rank} | `{row.get('unit_id', '')}` | {row.get('best_route', '')} "
            f"| {row.get('best_score_norm', '')} | {one_line(row.get('knowledge_zh') or row.get('en_quote'), 90)} |\n"
        )
    if not rows:
        lines.append("| - | - | - | - | 无 |\n")
    return "".join(lines)


def render_md(doc: dict[str, Any], table_limit: int = 8) -> str:
    lines: list[str] = []
    experiment = doc.get("source_experiment", "")
    lines.append(f"# {doc['question_id']} s1 {experiment} 分层直接检索\n\n")
    lines.append("## s1定位\n\n")
    lines.append(f"- 来源实验：{experiment}。\n")
    lines.append(f"- A/B 对照：{doc.get('policy', {}).get('contrast', '')}。\n")
    lines.append("- 默认检索 stem 与 stem+单个选项。\n")
    lines.append("- 只跑 BGE/BM25 直接 unit 召回；不做 KG 扩展，不调用 LLM。\n\n")
    lines.append(f"题干：{doc.get('stem', '')}\n\n")

    options = doc.get("options", {}) or {}
    if options:
        lines.append("## 选项\n\n")
        for label, text in options.items():
            lines.append(f"- {label}. {text}\n")
        lines.append("\n")

    for head in doc.get("heads", []) or []:
        lines.append(f"## {head.get('head_id')}\n\n")
        hints = head.get("query_alias_hints", []) or []
        p5_terms = head.get("p5_terms", []) or []
        inline_hits = head.get("alias_hits", []) or []
        if hints:
            lines.append(f"P5 alias hints: {', '.join(hints)}\n\n")
        elif p5_terms:
            desc = [f"{t.get('matched_term')} -> {t.get('canonical_en')} / {t.get('canonical_zh')}" for t in p5_terms]
            lines.append(f"P5 normalized terms: {'; '.join(desc)}\n\n")
        elif inline_hits:
            desc = [f"{t.get('matched_term')} -> {t.get('inline_text')}" for t in inline_hits]
            lines.append(f"P5 canonical inline hits: {'; '.join(desc)}\n\n")
        else:
            lines.append("P5变化：无\n\n")

        for variant in VARIANTS:
            result = head.get("variants", {}).get(variant, {})
            lines.append(f"### {variant}: {result.get('label', '')}\n\n")
            lines.append(f"query: {result.get('query', '')}\n\n")
            lines.append(render_units_table(result.get("merged_units", []) or [], table_limit))
            lines.append("\n")

        diff = head.get("variant_diff", {}) or {}
        added = diff.get("added_by_test", []) or []
        dropped = diff.get("dropped_by_test", []) or []
        lines.append("### test 对 baseline 的变化\n\n")
        lines.append(f"新增 unit 数：{len(added)}；丢失 unit 数：{len(dropped)}；共同 unit 数：{len(diff.get('common_unit_ids', []) or [])}\n\n")
        if added:
            lines.append("新增 unit：\n")
            for row in added[:table_limit]:
                lines.append(f"- `{row.get('unit_id')}` | {row.get('best_route')} | {one_line(row.get('knowledge_zh') or row.get('en_quote'), 100)}\n")
            lines.append("\n")
        if dropped:
            lines.append("丢失 unit：\n")
            for row in dropped[:table_limit]:
                lines.append(f"- `{row.get('unit_id')}` | {row.get('best_route')} | {one_line(row.get('knowledge_zh') or row.get('en_quote'), 100)}\n")
            lines.append("\n")
    return "".join(lines)


def experiment_input_dir(experiment: str) -> Path:
    return {"s0a": S0A_INPUT_DIR, "s0b": S0B_INPUT_DIR, "s0c": S0C_INPUT_DIR}[experiment]


def experiment_suffix(experiment: str) -> str:
    return experiment


def question_id_from_path(path: Path, suffix: str) -> str:
    name = path.name
    ending = f".{suffix}.json"
    return name[: -len(ending)] if name.endswith(ending) else path.stem


def available_question_ids(experiment: str) -> list[str]:
    input_dir = experiment_input_dir(experiment)
    suffix = experiment_suffix(experiment)
    return sorted(question_id_from_path(path, suffix) for path in input_dir.glob(f"*.{suffix}.json"))


def limited_question_ids(experiments: list[str], limit: int | None, offset: int) -> list[str] | None:
    if limit is None and offset <= 0:
        return None
    id_sets = [set(available_question_ids(experiment)) for experiment in experiments]
    if not id_sets:
        return []
    common_ids = sorted(set.intersection(*id_sets))
    start = max(offset, 0)
    end = None if limit is None else start + max(limit, 0)
    return common_ids[start:end]


def resolve_input_files(
    experiments: list[str],
    question_ids: list[str],
    input_file: str | None,
    limit: int | None,
    offset: int,
) -> list[tuple[str, Path]]:
    if input_file:
        path = Path(input_file)
        data = load_json(path)
        step = str(data.get("step", ""))
        if step.startswith("s0a"):
            return [("s0a", path)]
        if step.startswith("s0b"):
            return [("s0b", path)]
        if step.startswith("s0c"):
            return [("s0c", path)]
        raise ValueError(f"cannot detect s0 experiment from {path}")

    selected_ids = question_ids or limited_question_ids(experiments, limit=limit, offset=offset)
    pairs: list[tuple[str, Path]] = []
    for experiment in experiments:
        input_dir = experiment_input_dir(experiment)
        suffix = experiment_suffix(experiment)
        if selected_ids is not None:
            pairs.extend((experiment, input_dir / f"{qid}.{suffix}.json") for qid in selected_ids)
        else:
            pairs.extend((experiment, path) for path in sorted(input_dir.glob(f"*.{suffix}.json")))
    return pairs


def main() -> None:
    parser = argparse.ArgumentParser(description="s1: direct BGE/BM25 retrieval for s0a/s0b/s0c A/B tests")
    parser.add_argument("--question-id", action="append", default=[], help="question id, e.g. v7_q_000009")
    parser.add_argument("--experiment", choices=["s0a", "s0b", "s0c", "all"], default="all")
    parser.add_argument("--input-file", default=None, help="specific s0a/s0b/s0c json file")
    parser.add_argument("--limit", type=int, default=None, help="process first N common question ids after sorting")
    parser.add_argument("--offset", type=int, default=0, help="offset used with --limit")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--index-pkl", default=str(ba.INDEX_PKL))
    parser.add_argument("--top-k", type=int, default=12, help="top k per route")
    parser.add_argument("--merged-top-k", type=int, default=20, help="merged top k per query variant")
    parser.add_argument("--bm25-min-score", type=float, default=0.0)
    parser.add_argument("--include-all-options", action="store_true", help="also retrieve all_options fallback head")
    args = parser.parse_args()

    experiments = list(EXPERIMENTS) if args.experiment == "all" else [args.experiment]
    input_pairs = resolve_input_files(experiments, args.question_id, args.input_file, args.limit, args.offset)
    missing = [str(path) for _, path in input_pairs if not path.exists()]
    if missing:
        raise FileNotFoundError("s0 input missing: " + "; ".join(missing))
    if not input_pairs:
        raise FileNotFoundError("no s0 input files found")

    index = ba.load_index(args.index_pkl)
    bm25_zh = ba.BM25(index["zh_bm25_docs"], index["zh_bm25_df"], index["zh_bm25_avgdl"])
    bm25_en = ba.BM25(index["en_bm25_docs"], index["en_bm25_df"], index["en_bm25_avgdl"])
    ba.get_bge_model()

    output_dir = Path(args.output_dir)
    index_rows: list[dict[str, str]] = []
    for experiment, input_path in input_pairs:
        source_doc = load_json(input_path)
        doc = build_s1_doc(
            source_doc=source_doc,
            experiment=experiment,
            input_path=input_path,
            index=index,
            bm25_zh=bm25_zh,
            bm25_en=bm25_en,
            top_k=args.top_k,
            merged_top_k=args.merged_top_k,
            bm25_min_score=args.bm25_min_score,
            include_all_options=args.include_all_options,
        )
        qid = doc["question_id"]
        exp_dir = output_dir / experiment
        json_path = exp_dir / f"{qid}.s1.{experiment}.json"
        md_path = exp_dir / f"{qid}.s1.{experiment}.md"
        write_json(json_path, doc)
        write_text(md_path, render_md(doc))
        index_rows.append({"experiment": experiment, "question_id": qid, "json": str(json_path), "markdown": str(md_path)})
        print(f"[ok] {experiment} {qid} -> {json_path}")

    write_json(output_dir / "index.json", index_rows)


if __name__ == "__main__":
    main()
