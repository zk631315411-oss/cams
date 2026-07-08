from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
P2_DIR = PHASE_DIR.parent / "phase02_core_points"
SINGLE_RUNNER = SCRIPT_DIR / "run_p3a_chapter_relations_ds.py"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


def chapter_sort_key(chapter_id: str) -> tuple[int, str]:
    match = re.match(r"CH(\d+)$", chapter_id)
    if not match:
        return (10**9, chapter_id)
    return (int(match.group(1)), chapter_id)


def discover_chapters() -> list[str]:
    chapters: set[str] = set()
    for path in (P2_DIR / "outputs").glob("p2a_reviewed_core_points.CH*-S*.json"):
        match = re.match(r"p2a_reviewed_core_points\.(CH\d+)-S\d+\.json$", path.name)
        if match:
            chapters.add(match.group(1))
    return sorted(chapters, key=chapter_sort_key)


def run_one(args: argparse.Namespace, chapter_id: str) -> dict[str, Any]:
    run_slug = f"{args.run_prefix}{chapter_id}"
    cmd = [
        sys.executable,
        str(SINGLE_RUNNER),
        "--chapter-id",
        chapter_id,
        "--run-slug",
        run_slug,
        "--model",
        args.model,
        "--max-tokens",
        str(args.max_tokens),
    ]
    if args.prompt_file:
        cmd.extend(["--prompt-file", str(args.prompt_file)])
    if args.p2a_run_prefix:
        cmd.extend(["--p2a-run-prefix", args.p2a_run_prefix])
    if args.disable_thinking:
        cmd.append("--disable-thinking")
    if args.no_filter_invalid:
        cmd.append("--no-filter-invalid")

    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    status = "passed" if proc.returncode == 0 else "failed"
    run_dir = PHASE_DIR / "runs" / run_slug
    parsed_path = run_dir / "parsed_response.json"
    relation_count = 0
    if parsed_path.exists():
        parsed = read_json(parsed_path)
        relations = parsed.get("core_point_relations") or []
        relation_count = len(relations) if isinstance(relations, list) else 0
    return {
        "chapter_id": chapter_id,
        "run_slug": run_slug,
        "status": status,
        "returncode": proc.returncode,
        "relation_count": relation_count,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def collect_relations(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        parsed_path = PHASE_DIR / "runs" / str(result["run_slug"]) / "parsed_response.json"
        if not parsed_path.exists():
            continue
        parsed = read_json(parsed_path)
        for rel in parsed.get("core_point_relations") or []:
            if not isinstance(rel, dict):
                continue
            row = dict(rel)
            row.setdefault("chapter_id", result["chapter_id"])
            row.setdefault("review_status", "pending_review")
            rows.append(row)
    order = {result["chapter_id"]: index for index, result in enumerate(results)}
    rows.sort(key=lambda row: (order.get(str(row.get("chapter_id")), 10**9), str(row.get("relation_id") or "")))
    return rows


def write_report(path: Path, summary: dict[str, Any], relations: list[dict[str, Any]]) -> None:
    by_chapter: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for rel in relations:
        chapter_id = str(rel.get("chapter_id") or "")
        relation_type = str(rel.get("relation_type") or "")
        by_chapter[chapter_id] = by_chapter.get(chapter_id, 0) + 1
        by_type[relation_type] = by_type.get(relation_type, 0) + 1

    lines = [
        "# P3A chapter relation candidates report",
        "",
        f"- generated_at: {summary['generated_at']}",
        f"- run_prefix: {summary['run_prefix']}",
        f"- model: {summary['model']}",
        f"- concurrency: {summary['concurrency']}",
        f"- selected_chapters: {summary['selected_count']}",
        f"- passed_count: {summary['passed_count']}",
        f"- failed_count: {summary['failed_count']}",
        f"- candidate_relations: {len(relations)}",
        "",
        "## By relation type",
        "",
    ]
    lines.extend(f"- {key}: {by_type[key]}" for key in sorted(by_type))
    lines.extend(["", "## By chapter", ""])
    lines.extend(f"- {key}: {by_chapter[key]}" for key in sorted(by_chapter, key=chapter_sort_key))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_preview(path: Path, relations: list[dict[str, Any]]) -> None:
    lines = ["# P3A chapter relation candidates preview", ""]
    for rel in relations:
        lines.extend(
            [
                f"## {rel.get('relation_id')} ({rel.get('relation_type')})",
                "",
                f"- chapter_id: {rel.get('chapter_id')}",
                f"- source_core_point_id: {rel.get('source_core_point_id')}",
                f"- target_core_point_id: {rel.get('target_core_point_id')}",
                f"- review_status: {rel.get('review_status')}",
                f"- reason: {rel.get('reason')}",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter-id", action="append", default=[])
    parser.add_argument("--start-chapter", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--run-prefix", default=None)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--prompt-file", type=Path, default=None)
    parser.add_argument("--p2a-run-prefix", default="")
    parser.add_argument("--disable-thinking", action="store_true", default=True)
    parser.add_argument("--no-filter-invalid", action="store_true", default=False)
    parser.add_argument("--output-jsonl", type=Path, default=None)
    parser.add_argument("--report-md", type=Path, default=None)
    parser.add_argument("--preview-md", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chapters = args.chapter_id or discover_chapters()
    chapters = sorted(dict.fromkeys(chapters), key=chapter_sort_key)
    if args.start_chapter:
        chapters = [chapter for chapter in chapters if chapter_sort_key(chapter) >= chapter_sort_key(args.start_chapter)]
    if args.limit:
        chapters = chapters[: args.limit]
    if not chapters:
        raise SystemExit("No chapters selected.")
    if args.run_prefix is None:
        args.run_prefix = "p3a_chapter_batch_" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_"

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        future_map = {executor.submit(run_one, args, chapter_id): chapter_id for chapter_id in chapters}
        for future in as_completed(future_map):
            result = future.result()
            results.append(result)
            print(json.dumps({"status": result["status"], "chapter_id": result["chapter_id"], "relations": result["relation_count"]}, ensure_ascii=False))

    order = {chapter: index for index, chapter in enumerate(chapters)}
    results.sort(key=lambda row: order.get(str(row["chapter_id"]), 10**9))
    relations = collect_relations(results)
    summary = {
        "schema_version": "p3a_chapter_batch_ds_summary_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_prefix": args.run_prefix,
        "model": args.model,
        "max_tokens": args.max_tokens,
        "disable_thinking": args.disable_thinking,
        "concurrency": args.concurrency,
        "selected_count": len(chapters),
        "passed_count": sum(1 for row in results if row["status"] == "passed"),
        "failed_count": sum(1 for row in results if row["status"] != "passed"),
        "results": results,
    }
    stem = args.run_prefix.rstrip("_")
    summary_path = PHASE_DIR / "runs" / f"{stem}_summary.json"
    output_jsonl = args.output_jsonl or (PHASE_DIR / "outputs" / "p3_core_point_relation_candidates.jsonl")
    report_md = args.report_md or (PHASE_DIR / "reports" / "p3a_candidate_report.md")
    preview_md = args.preview_md or (PHASE_DIR / "previews" / "p3a_candidate_preview.md")
    write_json(summary_path, summary)
    write_jsonl(output_jsonl, relations)
    write_report(report_md, summary, relations)
    write_preview(preview_md, relations)
    print(json.dumps({"summary_path": str(summary_path), "output_jsonl": str(output_jsonl), "report_md": str(report_md), "preview_md": str(preview_md), "passed": summary["passed_count"], "failed": summary["failed_count"]}, ensure_ascii=False))
    if summary["failed_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
