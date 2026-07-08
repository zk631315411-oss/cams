from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np


TEST_DIR = Path(__file__).resolve().parent
PHASE_DIR = TEST_DIR.parent.parent
P2_DIR = PHASE_DIR.parent / "phase02_core_points"
DEFAULT_PROMPT = TEST_DIR / "prompt_p4b_cross_chapter_relation_v1.md"
DEFAULT_P2A_PREFIX = "p2a_batch_first5_chapters_20260706_"
DEFAULT_P2B_PREFIX = "p2b_first5_reviewed_20260706_"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
ALLOWED_RELATION_TYPES = {"summarizes", "illustrates", "grounds", "contrasts", "none"}
ALLOWED_DECISIONS = {"accept", "reject"}

EDGE_PRIORITY = {
    "defines": 0,
    "classifies": 1,
    "states_rule": 2,
    "describes_process": 3,
    "explains": 4,
    "indicates_risk": 5,
    "prescribes_measure": 6,
    "states_consequence": 7,
    "illustrates": 8,
    "provides_context": 9,
    "exclude": 99,
}

CASE_EDGE_PRIORITY = {
    "illustrates": 0,
    "explains": 1,
    "describes_process": 2,
    "provides_context": 3,
    "states_consequence": 4,
}


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


def get_deepseek_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_BASE_URL
            return value, base_url, env_name
    raise RuntimeError("DEEPSEEK_API_KEY / DS_API_KEY / DS_KEY is not set.")


def extract_json_object(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    candidates = [text]
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            try:
                import json_repair

                parsed = json.loads(json_repair.repair_json(candidate))
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                continue
    return None


def parse_unit_texts(section_text: str | None) -> dict[str, str]:
    if not section_text:
        return {}
    unit_texts: dict[str, str] = {}
    pattern = re.compile(r"\[(v7u_N\d+)\|\d+\]\s*(.*)")
    for line in section_text.splitlines():
        match = pattern.match(line.strip())
        if match:
            unit_texts[match.group(1)] = match.group(2).strip()
    return unit_texts


def load_section_input(section_id: str, p2a_prefix: str) -> dict[str, Any]:
    path = P2_DIR / "runs" / f"{p2a_prefix}{section_id}" / "input_section.json"
    return read_json(path) if path.exists() else {}


def load_core_points_for_section(section_id: str, p2a_prefix: str) -> tuple[list[dict[str, Any]], str]:
    reviewed_path = P2_DIR / "outputs" / f"p2a_reviewed_core_points.{section_id}.json"
    if reviewed_path.exists():
        return read_json(reviewed_path).get("core_points") or [], "p2a_review"
    raw_path = P2_DIR / "runs" / f"{p2a_prefix}{section_id}" / "parsed_response.json"
    if raw_path.exists():
        return read_json(raw_path).get("core_points") or [], "p2a_raw"
    return [], "missing"


def load_p2b_edges(cp_id: str, p2b_prefix: str, unit_texts: dict[str, str]) -> list[dict[str, Any]]:
    path = P2_DIR / "runs" / f"{p2b_prefix}{cp_id}" / "parsed_response.json"
    if not path.exists():
        matches = sorted((P2_DIR / "runs").glob(f"*{cp_id}"))
        for match in matches:
            candidate = match / "parsed_response.json"
            if candidate.exists():
                path = candidate
                break
    if not path.exists():
        return []
    parsed = read_json(path)
    edges = []
    for edge in parsed.get("core_point_unit_edges") or []:
        unit_id = str(edge.get("unit_id") or "")
        edges.append(
            {
                "unit_id": unit_id,
                "edge_type": edge.get("edge_type"),
                "unit_text": unit_texts.get(unit_id, ""),
                "reason": edge.get("reason"),
            }
        )
    return edges


def unit_sort_key(edge: dict[str, Any]) -> int:
    match = re.search(r"(\d+)$", str(edge.get("unit_id") or ""))
    return int(match.group(1)) if match else 10**9


def is_case_cp(cp: dict[str, Any]) -> bool:
    title = str(cp.get("title_en") or "").lower()
    if "case" in title or "example" in title:
        return True
    edges = cp.get("p2b_unit_edges") or []
    return bool(edges) and sum(1 for edge in edges if edge.get("edge_type") == "illustrates") >= max(2, len(edges) // 2)


def select_edges(cp: dict[str, Any], max_edges: int, mode: str) -> list[dict[str, Any]]:
    edges = [edge for edge in cp.get("p2b_unit_edges") or [] if edge.get("edge_type") != "exclude"]
    if mode == "all":
        return sorted(edges, key=unit_sort_key)
    priority = CASE_EDGE_PRIORITY if is_case_cp(cp) else EDGE_PRIORITY
    return sorted(edges, key=lambda edge: (priority.get(str(edge.get("edge_type")), 50), unit_sort_key(edge)))[:max_edges]


def collect_core_points(chapters: set[str], p2a_prefix: str, p2b_prefix: str, max_edges: int, unit_context: str) -> list[dict[str, Any]]:
    cps: list[dict[str, Any]] = []
    reviewed_files = sorted((P2_DIR / "outputs").glob("p2a_reviewed_core_points.CH*-S*.json"))
    for reviewed_file in reviewed_files:
        section_id = reviewed_file.stem.replace("p2a_reviewed_core_points.", "", 1)
        chapter_id = section_id.split("-")[0]
        if chapter_id not in chapters:
            continue
        reviewed = read_json(reviewed_file)
        source_run = str(reviewed.get("source_p2a_run") or "").replace("\\", "/")
        section_input: dict[str, Any] = {}
        if source_run:
            source_input_path = P2_DIR / source_run.replace("parsed_response.json", "input_section.json")
            if source_input_path.exists():
                section_input = read_json(source_input_path)
        if not section_input:
            section_input = load_section_input(section_id, p2a_prefix)
        unit_texts = parse_unit_texts(section_input.get("section_text_with_unit_anchors"))
        core_points = reviewed.get("core_points") or []
        source = "p2a_review"
        for cp in core_points:
            cp_id = str(cp.get("draft_core_point_id") or cp.get("core_point_id") or "")
            if not cp_id:
                continue
            all_edges = load_p2b_edges(cp_id, p2b_prefix, unit_texts)
            cp_row = {
                "core_point_id": cp_id,
                "chapter_id": chapter_id,
                "section_id": section_id,
                "section_title": section_input.get("section_title"),
                "source": source,
                "title_en": cp.get("title_en") or "",
                "title_zh": cp.get("title_zh") or "",
                "reason": cp.get("reason") or "",
                "anchor_unit_ids": cp.get("anchor_unit_ids") or [],
                "support_unit_ids": cp.get("support_unit_ids") or [],
                "p2b_unit_edges": all_edges,
            }
            selected_edges = select_edges(cp_row, max_edges, unit_context)
            cp_row["selected_unit_edges"] = selected_edges
            cp_row["omitted_unit_edge_count"] = max(0, len(all_edges) - len(selected_edges))
            cps.append(cp_row)
    return cps


def embedding_text(cp: dict[str, Any]) -> str:
    edge_text = "\n".join(str(edge.get("unit_text") or "") for edge in cp.get("selected_unit_edges") or [])
    return "\n".join(
        part for part in [
            str(cp.get("title_en") or ""),
            str(cp.get("section_title") or ""),
            str(cp.get("reason") or ""),
            edge_text,
        ] if part.strip()
    )[:2500]


def summarize_cp(cp: dict[str, Any]) -> dict[str, Any]:
    return {
        "core_point_id": cp.get("core_point_id"),
        "chapter_id": cp.get("chapter_id"),
        "section_id": cp.get("section_id"),
        "section_title": cp.get("section_title"),
        "title_en": cp.get("title_en"),
        "p2a_reason": cp.get("reason"),
        "selected_unit_edges": cp.get("selected_unit_edges") or [],
        "omitted_unit_edge_count": cp.get("omitted_unit_edge_count", 0),
    }


def load_embedding_model(model_name: str):
    if os.environ.get("P4_ALLOW_MODEL_DOWNLOAD") != "1":
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def generate_vector_candidates(cps: list[dict[str, Any]], embedding_model: str, limit: int, threshold: float) -> list[dict[str, Any]]:
    model = load_embedding_model(embedding_model)
    texts = [embedding_text(cp) for cp in cps]
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    sim_matrix = np.matmul(np.asarray(embeddings), np.asarray(embeddings).T)
    candidates: list[dict[str, Any]] = []
    for i, cp_a in enumerate(cps):
        for j in range(i + 1, len(cps)):
            cp_b = cps[j]
            if cp_a["chapter_id"] == cp_b["chapter_id"]:
                continue
            similarity = float(sim_matrix[i, j])
            if similarity < threshold:
                continue
            candidates.append(
                {
                    "candidate_id": "",
                    "cp_a_id": cp_a["core_point_id"],
                    "cp_b_id": cp_b["core_point_id"],
                    "cp_a_chapter_id": cp_a["chapter_id"],
                    "cp_b_chapter_id": cp_b["chapter_id"],
                    "cp_a_section_id": cp_a["section_id"],
                    "cp_b_section_id": cp_b["section_id"],
                    "cp_a_title_en": cp_a["title_en"],
                    "cp_b_title_en": cp_b["title_en"],
                    "retrieval": {
                        "method": "sentence_transformer_cosine",
                        "embedding_model": embedding_model,
                        "similarity": round(similarity, 6),
                    },
                    "cp_a": summarize_cp(cp_a),
                    "cp_b": summarize_cp(cp_b),
                }
            )
    candidates.sort(key=lambda row: (-row["retrieval"]["similarity"], row["cp_a_id"], row["cp_b_id"]))
    selected = candidates[:limit]
    for index, candidate in enumerate(selected, start=1):
        candidate["candidate_id"] = f"p4vec_{index:04d}"
        candidate["retrieval"]["global_rank"] = index
    return selected


def chunk_rows(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [rows[index:index + size] for index in range(0, len(rows), size)]


def build_messages(prompt_text: str, candidates: list[dict[str, Any]], batch_id: str) -> list[dict[str, str]]:
    payload = {
        "batch_id": batch_id,
        "candidate_count": len(candidates),
        "candidates": candidates,
    }
    return [
        {"role": "system", "content": prompt_text},
        {"role": "user", "content": "Judge these cross-chapter CP candidate pairs. Return one JSON object only.\n\n" + canonical_json(payload)},
    ]


def call_model(args: argparse.Namespace, messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
    from openai import OpenAI

    api_key, base_url, _ = get_deepseek_config()
    client = OpenAI(api_key=api_key, base_url=args.base_url or base_url, timeout=args.request_timeout)
    kwargs: dict[str, Any] = {
        "model": args.model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": args.max_tokens,
        "response_format": {"type": "json_object"},
    }
    if args.disable_thinking:
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    response = client.chat.completions.create(**kwargs)
    raw = (response.choices[0].message.content or "").strip()
    usage = getattr(response, "usage", None)
    return raw, usage.model_dump() if hasattr(usage, "model_dump") else {}


def run_llm_batch(args: argparse.Namespace, prompt_text: str, run_dir: Path, batch_index: int, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    batch_id = f"batch_{batch_index:04d}"
    batch_dir = run_dir / "batches" / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    write_json(batch_dir / "input_candidates.json", {"batch_id": batch_id, "candidate_count": len(candidates), "candidates": candidates})
    messages = build_messages(prompt_text, candidates, batch_id)
    try:
        raw, usage = call_model(args, messages)
    except Exception as exc:
        issue = {"issue": "batch_call_failed", "error": repr(exc)}
        write_json(
            batch_dir / "batch_manifest.json",
            {
                "batch_id": batch_id,
                "batch_index": batch_index,
                "candidate_count": len(candidates),
                "candidate_ids": [candidate["candidate_id"] for candidate in candidates],
                "decision_count": 0,
                "validation_issues": [issue],
                "usage": {},
                "status": "call_failed",
            },
        )
        return {
            "batch_id": batch_id,
            "batch_index": batch_index,
            "candidates": candidates,
            "decisions": [],
            "issues": [issue],
            "usage": {},
            "status": "call_failed",
        }
    (batch_dir / "raw_response.txt").write_text(raw, encoding="utf-8")
    parsed = extract_json_object(raw)
    if parsed is not None:
        write_json(batch_dir / "parsed_response.json", parsed)
    issues = validate_decisions(candidates, parsed)
    decisions = parsed.get("decisions") if isinstance(parsed, dict) and isinstance(parsed.get("decisions"), list) else []
    write_json(
        batch_dir / "batch_manifest.json",
        {
            "batch_id": batch_id,
            "batch_index": batch_index,
            "candidate_count": len(candidates),
            "candidate_ids": [candidate["candidate_id"] for candidate in candidates],
            "decision_count": len(decisions),
            "validation_issues": issues,
            "usage": usage,
            "status": "passed" if not issues else "validation_failed",
        },
    )
    return {
        "batch_id": batch_id,
        "batch_index": batch_index,
        "candidates": candidates,
        "decisions": decisions,
        "issues": issues,
        "usage": usage,
        "status": "passed" if not issues else "validation_failed",
    }


def aggregate_usage(batch_results: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, Any] = {
        "completion_tokens": 0,
        "prompt_tokens": 0,
        "total_tokens": 0,
        "batch_count": len(batch_results),
    }
    for result in batch_results:
        usage = result.get("usage") or {}
        for key in ("completion_tokens", "prompt_tokens", "total_tokens"):
            value = usage.get(key)
            if isinstance(value, int):
                totals[key] += value
        prompt_details = usage.get("prompt_tokens_details") or {}
        for key in ("cached_tokens",):
            value = prompt_details.get(key)
            if isinstance(value, int):
                totals[f"prompt_tokens_details.{key}"] = totals.get(f"prompt_tokens_details.{key}", 0) + value
        for key in ("prompt_cache_hit_tokens", "prompt_cache_miss_tokens"):
            value = usage.get(key)
            if isinstance(value, int):
                totals[key] = totals.get(key, 0) + value
    return totals


def validate_decisions(candidates: list[dict[str, Any]], output: dict[str, Any] | None) -> list[dict[str, Any]]:
    if output is None:
        return [{"issue": "model_output_malformed"}]
    decisions = output.get("decisions")
    if not isinstance(decisions, list):
        return [{"issue": "decisions_not_list"}]
    candidate_map = {candidate["candidate_id"]: candidate for candidate in candidates}
    issues: list[dict[str, Any]] = []
    seen: set[str] = set()
    for decision in decisions:
        candidate_id = str(decision.get("candidate_id") or "")
        candidate = candidate_map.get(candidate_id)
        if not candidate:
            issues.append({"issue": "unknown_candidate_id", "candidate_id": candidate_id})
            continue
        if candidate_id in seen:
            issues.append({"issue": "duplicate_candidate_id", "candidate_id": candidate_id})
        seen.add(candidate_id)
        if decision.get("decision") not in ALLOWED_DECISIONS:
            issues.append({"issue": "invalid_decision", "candidate_id": candidate_id})
        if decision.get("relation_type") not in ALLOWED_RELATION_TYPES:
            issues.append({"issue": "invalid_relation_type", "candidate_id": candidate_id})
        allowed_cp_ids = {candidate["cp_a_id"], candidate["cp_b_id"]}
        if decision.get("decision") == "accept":
            if decision.get("source_core_point_id") not in allowed_cp_ids:
                issues.append({"issue": "source_core_point_id_not_in_pair", "candidate_id": candidate_id})
            if decision.get("target_core_point_id") not in allowed_cp_ids:
                issues.append({"issue": "target_core_point_id_not_in_pair", "candidate_id": candidate_id})
            if decision.get("relation_type") == "none":
                issues.append({"issue": "accepted_none_relation", "candidate_id": candidate_id})
        if decision.get("decision") == "reject" and decision.get("relation_type") != "none":
            issues.append({"issue": "rejected_non_none_relation", "candidate_id": candidate_id})
    missing = sorted(set(candidate_map) - seen)
    if missing:
        issues.append({"issue": "missing_decisions", "candidate_ids": missing})
    return issues


def write_report(path: Path, candidates: list[dict[str, Any]], decisions: list[dict[str, Any]], issues: list[dict[str, Any]], args: argparse.Namespace) -> None:
    accepted = [row for row in decisions if row.get("decision") == "accept"]
    rejected = [row for row in decisions if row.get("decision") == "reject"]
    by_type: dict[str, int] = {}
    for row in accepted:
        rel_type = str(row.get("relation_type") or "")
        by_type[rel_type] = by_type.get(rel_type, 0) + 1
    lines = [
        "# P4 vector cross-chapter probe report",
        "",
        f"- generated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- embedding_model: {args.embedding_model}",
        f"- unit_context: {args.unit_context}",
        f"- max_selected_unit_edges: {args.max_selected_unit_edges}",
        f"- similarity_threshold: {args.similarity_threshold}",
        f"- batch_size: {args.batch_size}",
        f"- concurrency: {args.concurrency}",
        f"- candidates: {len(candidates)}",
        f"- accepted: {len(accepted)}",
        f"- rejected: {len(rejected)}",
        f"- validation_issues: {len(issues)}",
        "",
        "## Accepted by relation type",
        "",
    ]
    if by_type:
        lines.extend(f"- {key}: {by_type[key]}" for key in sorted(by_type))
    else:
        lines.append("- none")
    lines.extend(["", "## Accepted decisions", ""])
    for row in accepted:
        lines.append(
            f"- {row.get('candidate_id')}: `{row.get('relation_type')}` "
            f"{row.get('source_core_point_id')} -> {row.get('target_core_point_id')} | {row.get('reason')}"
        )
    lines.extend(["", "## Top rejected decisions", ""])
    for row in rejected[:20]:
        lines.append(f"- {row.get('candidate_id')}: {row.get('reason')}")
    lines.extend(["", "## Validation issues", ""])
    if issues:
        lines.extend(f"- `{issue.get('issue')}` {issue}" for issue in issues)
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    chapters = set(args.chapter)
    run_slug = args.run_slug or "p4_vector_probe_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = TEST_DIR / "runs" / run_slug
    prompt_text = args.prompt_file.read_text(encoding="utf-8")
    cps = collect_core_points(chapters, args.p2a_prefix, args.p2b_prefix, args.max_selected_unit_edges, args.unit_context)
    candidates = generate_vector_candidates(cps, args.embedding_model, args.limit_candidates, args.similarity_threshold)
    write_json(TEST_DIR / "inputs" / f"{run_slug}_candidates.json", {"core_point_count": len(cps), "candidates": candidates})
    write_json(run_dir / "input_candidates.json", {"core_point_count": len(cps), "candidates": candidates})
    if args.skip_llm:
        print(json.dumps({"status": "candidates_only", "core_points": len(cps), "candidates": len(candidates)}, ensure_ascii=False))
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    candidate_batches = chunk_rows(candidates, args.batch_size)
    batch_results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(run_llm_batch, args, prompt_text, run_dir, batch_index, batch_candidates)
            for batch_index, batch_candidates in enumerate(candidate_batches, start=1)
        ]
        for future in as_completed(futures):
            batch_results.append(future.result())
    batch_results.sort(key=lambda row: row["batch_index"])
    decisions = [decision for result in batch_results for decision in result.get("decisions", [])]
    issues = [
        {"batch_id": result["batch_id"], **issue}
        for result in batch_results
        for issue in result.get("issues", [])
    ]
    candidate_order = {candidate["candidate_id"]: index for index, candidate in enumerate(candidates)}
    decisions.sort(key=lambda row: candidate_order.get(str(row.get("candidate_id") or ""), 10**9))
    parsed = {
        "schema_version": "p4_vector_batch_decisions_v1",
        "run_slug": run_slug,
        "batch_size": args.batch_size,
        "concurrency": args.concurrency,
        "candidate_count": len(candidates),
        "batch_count": len(candidate_batches),
        "decisions": decisions,
    }
    accepted = [row for row in decisions if row.get("decision") == "accept"]
    rejected = [row for row in decisions if row.get("decision") == "reject"]
    write_json(TEST_DIR / "outputs" / f"{run_slug}_decisions.json", parsed or {})
    write_jsonl(TEST_DIR / "outputs" / f"{run_slug}_accepted.jsonl", accepted)
    write_jsonl(TEST_DIR / "outputs" / f"{run_slug}_rejected.jsonl", rejected)
    write_report(TEST_DIR / "reports" / f"{run_slug}_report.md", candidates, decisions, issues, args)
    manifest = {
        "schema_version": "p4_vector_probe_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "chapters": sorted(chapters),
        "model": args.model,
        "max_tokens": args.max_tokens,
        "disable_thinking": args.disable_thinking,
        "embedding_model": args.embedding_model,
        "unit_context": args.unit_context,
        "max_selected_unit_edges": args.max_selected_unit_edges,
        "batch_size": args.batch_size,
        "concurrency": args.concurrency,
        "similarity_threshold": args.similarity_threshold,
        "prompt_sha256": sha256_text(prompt_text),
        "candidate_count": len(candidates),
        "batch_count": len(candidate_batches),
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "validation_issues": issues,
        "usage": aggregate_usage(batch_results),
        "status": "passed" if not issues else "validation_failed",
    }
    write_json(run_dir / "run_manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "run_dir": str(run_dir), "candidates": len(candidates), "accepted": len(accepted), "rejected": len(rejected), "issues": len(issues)}, ensure_ascii=False))
    if issues:
        raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="P4 vector cross-chapter relation probe")
    parser.add_argument("--chapter", action="append", default=["CH01", "CH02", "CH03", "CH04", "CH05"])
    parser.add_argument("--p2a-prefix", default=DEFAULT_P2A_PREFIX)
    parser.add_argument("--p2b-prefix", default=DEFAULT_P2B_PREFIX)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--embedding-model", default="BAAI/bge-small-en-v1.5")
    parser.add_argument("--unit-context", choices=["selected", "all"], default="selected")
    parser.add_argument("--max-selected-unit-edges", type=int, default=5)
    parser.add_argument("--similarity-threshold", type=float, default=0.0)
    parser.add_argument("--limit-candidates", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--run-slug", default=None)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--max-tokens", type=int, default=20000)
    parser.add_argument("--request-timeout", type=float, default=120.0)
    parser.add_argument("--disable-thinking", action="store_true", default=True)
    parser.add_argument("--skip-llm", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
