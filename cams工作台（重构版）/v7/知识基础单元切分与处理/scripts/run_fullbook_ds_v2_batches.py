from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
BATCH_DIR = BASE_UNITS_DIR / "llm_batches"
SLICE_DIR = BATCH_DIR / "v2_fullbook_slices"
DECISION_DIR = BATCH_DIR / "v2_fullbook_decisions"
DRAFT_DIR = BASE_UNITS_DIR / "draft" / "v2_fullbook"
RUN_LOG_DIR = BASE_UNITS_DIR / "fullbook_ds_v2_run"
PROMPT_FILE = MODULE_DIR / "prompts" / "v7_unit_split_v2.md"
PLAN_FILE = BATCH_DIR / "v7_fullbook_llm_batch_plan.json"


@dataclass(frozen=True)
class BatchTask:
    chapter: str
    chapter_slug: str
    offset: int
    limit: int
    row_count: int
    source_file: Path
    batch_file: Path
    decisions_file: Path
    validation_file: Path
    run_slug: str
    llm_file: Path
    combined_file: Path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def slice_suffix(offset: int, limit: int) -> str:
    return f"offset{offset:03d}_limit{limit:03d}"


def task_slug(chapter_slug: str, offset: int, limit: int) -> str:
    return f"v2fb_{chapter_slug}_o{offset:03d}_l{limit:03d}"


def build_report(task: BatchTask, rows: list[dict[str, Any]]) -> str:
    lines = [
        "# v7 DS v2 Fullbook Batch Slice",
        "",
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"- chapter: {task.chapter}",
        f"- source: {task.source_file.relative_to(BASE_UNITS_DIR)}",
        f"- offset: {task.offset}",
        f"- limit: {task.limit}",
        f"- rows: {len(rows)}",
        f"- output: {task.batch_file.relative_to(BASE_UNITS_DIR)}",
        f"- run_slug: {task.run_slug}",
        "",
        "## Requests",
        "",
    ]
    for index, row in enumerate(rows, start=task.offset + 1):
        payload = row.get("payload", {})
        heading = " / ".join(payload.get("heading_stack", []))
        sentence_count = len(payload.get("window", {}).get("sentences", []))
        lines.append(f"- {index}: `{row.get('request_id')}` P{row.get('printed_page')} {heading} sentences={sentence_count}")
    return "\n".join(lines)


def load_tasks(limit: int) -> list[BatchTask]:
    plan = read_json(PLAN_FILE)
    tasks: list[BatchTask] = []
    for chapter in plan.get("chapter_summaries", []):
        chapter_name = str(chapter["chapter"])
        chapter_slug = str(chapter["slug"])
        source_file = BASE_UNITS_DIR / str(chapter["batch_file"])
        rows = read_jsonl(source_file)
        for offset in range(0, len(rows), limit):
            current_rows = rows[offset : offset + limit]
            if not current_rows:
                continue
            suffix = slice_suffix(offset, limit)
            run_slug = task_slug(chapter_slug, offset, limit)
            batch_file = SLICE_DIR / f"{chapter_slug}.{suffix}.jsonl"
            decisions_file = DECISION_DIR / f"pilot_{run_slug}_decisions.jsonl"
            validation_file = DECISION_DIR / f"pilot_{run_slug}_validation.json"
            llm_file = DRAFT_DIR / f"v7_units_draft.pilot_{run_slug}.llm.json"
            combined_file = DRAFT_DIR / f"v7_units_draft.pilot_{run_slug}.combined.json"
            tasks.append(
                BatchTask(
                    chapter=chapter_name,
                    chapter_slug=chapter_slug,
                    offset=offset,
                    limit=limit,
                    row_count=len(current_rows),
                    source_file=source_file,
                    batch_file=batch_file,
                    decisions_file=decisions_file,
                    validation_file=validation_file,
                    run_slug=run_slug,
                    llm_file=llm_file,
                    combined_file=combined_file,
                )
            )
    return tasks


def prepare_slices(tasks: list[BatchTask]) -> None:
    for task in tasks:
        rows = read_jsonl(task.source_file)
        sliced = rows[task.offset : task.offset + task.limit]
        write_jsonl(task.batch_file, sliced)
        manifest = {
            "schema_version": "v7_ds_v2_fullbook_batch_slice_v1",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "chapter": task.chapter,
            "source": str(task.source_file.relative_to(BASE_UNITS_DIR)),
            "chapter_slug": task.chapter_slug,
            "offset": task.offset,
            "limit": task.limit,
            "row_count": len(sliced),
            "request_ids": [row.get("request_id") for row in sliced],
            "output_jsonl": str(task.batch_file.relative_to(BASE_UNITS_DIR)),
            "run_slug": task.run_slug,
            "prompt_file": str(PROMPT_FILE),
        }
        write_json(task.batch_file.with_suffix(".manifest.json"), manifest)
        task.batch_file.with_suffix(".report.md").write_text(build_report(task, sliced), encoding="utf-8")


def manifest_passed(task: BatchTask) -> bool:
    manifest_path = BASE_UNITS_DIR / "llm_runs" / task.run_slug / "run_manifest.json"
    if not task.decisions_file.exists() or not manifest_path.exists():
        return False
    try:
        manifest = read_json(manifest_path)
    except Exception:
        return False
    counts = manifest.get("status_counts") or {}
    return manifest.get("status") == "completed" and counts.get("passed") == task.row_count


def validation_passed(task: BatchTask) -> bool:
    if not task.validation_file.exists():
        return False
    try:
        payload = read_json(task.validation_file)
    except Exception:
        return False
    return not payload.get("issues") and not payload.get("provenance_issues")


def combined_passed(task: BatchTask) -> bool:
    audit_file = DRAFT_DIR / f"v7_units_draft.pilot_{task.run_slug}.combined_audit.json"
    if not task.combined_file.exists() or not audit_file.exists():
        return False
    try:
        audit = read_json(audit_file)
    except Exception:
        return False
    return not audit.get("issues")


def run_subprocess(cmd: list[str], log_path: Path) -> dict[str, Any]:
    started_at = datetime.now().isoformat(timespec="seconds")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write("$ " + " ".join(cmd) + "\n\n")
        log.flush()
        proc = subprocess.run(cmd, cwd=MODULE_DIR, text=True, stdout=log, stderr=subprocess.STDOUT)
    return {
        "cmd": cmd,
        "log_path": str(log_path),
        "returncode": proc.returncode,
        "started_at": started_at,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
    }


def run_decision(task: BatchTask, args: argparse.Namespace) -> dict[str, Any]:
    if args.resume and manifest_passed(task):
        return {"stage": "decision", "run_slug": task.run_slug, "status": "skipped_passed"}
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "run_ds_unit_grouping_batch.py"),
        "--batch-file",
        str(task.batch_file),
        "--decisions-file",
        str(task.decisions_file),
        "--run-slug",
        task.run_slug,
        "--model",
        args.model,
        "--max-tokens",
        str(args.max_tokens),
        "--timeout-seconds",
        str(args.timeout_seconds),
        "--retries",
        str(args.retries),
        "--prompt-file",
        str(PROMPT_FILE),
    ]
    result = run_subprocess(cmd, RUN_LOG_DIR / "logs" / f"{task.run_slug}.decision.log")
    result.update({"stage": "decision", "run_slug": task.run_slug})
    return result


def run_validation(task: BatchTask) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "validate_llm_decisions_against_batch.py"),
        "--batch-file",
        str(task.batch_file),
        "--decisions-file",
        str(task.decisions_file),
        "--prompt-file",
        str(PROMPT_FILE),
        "--require-provenance",
        "--out-file",
        str(task.validation_file),
    ]
    result = run_subprocess(cmd, RUN_LOG_DIR / "logs" / f"{task.run_slug}.validation.log")
    result.update({"stage": "validation", "run_slug": task.run_slug})
    return result


def run_materialize(task: BatchTask) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "materialize_fullbook_llm_pilot_units.py"),
        "--batch-file",
        str(task.batch_file),
        "--decisions-file",
        str(task.decisions_file),
        "--slug",
        task.run_slug,
        "--out-dir",
        str(DRAFT_DIR),
    ]
    result = run_subprocess(cmd, RUN_LOG_DIR / "logs" / f"{task.run_slug}.materialize.log")
    result.update({"stage": "materialize", "run_slug": task.run_slug})
    return result


def run_combined(task: BatchTask) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "build_chapter_combined_pilot_units.py"),
        "--chapter",
        task.chapter,
        "--slug",
        task.run_slug,
        "--llm-pilot-file",
        str(task.llm_file),
        "--out-dir",
        str(DRAFT_DIR),
        "--scope-from-llm-pages",
        "--scope-from-llm-block-span",
    ]
    result = run_subprocess(cmd, RUN_LOG_DIR / "logs" / f"{task.run_slug}.combined.log")
    result.update({"stage": "combined", "run_slug": task.run_slug})
    return result


def write_status(tasks: list[BatchTask], results: list[dict[str, Any]]) -> None:
    summary = []
    for task in tasks:
        summary.append(
            {
                "chapter": task.chapter,
                "chapter_slug": task.chapter_slug,
                "offset": task.offset,
                "limit": task.limit,
                "row_count": task.row_count,
                "run_slug": task.run_slug,
                "batch_file": str(task.batch_file.relative_to(BASE_UNITS_DIR)),
                "decisions_file": str(task.decisions_file.relative_to(BASE_UNITS_DIR)),
                "decision_passed": manifest_passed(task),
                "validation_passed": validation_passed(task),
                "combined_passed": combined_passed(task),
            }
        )
    payload = {
        "schema_version": "v7_ds_v2_fullbook_run_status_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "task_count": len(tasks),
        "request_count": sum(task.row_count for task in tasks),
        "decision_passed": sum(1 for task in tasks if manifest_passed(task)),
        "validation_passed": sum(1 for task in tasks if validation_passed(task)),
        "combined_passed": sum(1 for task in tasks if combined_passed(task)),
        "results_tail": results[-200:],
        "tasks": summary,
    }
    write_json(RUN_LOG_DIR / "run_status.json", payload)


def run_decisions_concurrent(tasks: list[BatchTask], args: argparse.Namespace) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    failures = 0
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        future_to_task = {}
        task_iter = iter(tasks)

        def submit_next() -> None:
            try:
                task = next(task_iter)
            except StopIteration:
                return
            future_to_task[executor.submit(run_decision, task, args)] = task

        for _ in range(min(args.max_workers, len(tasks))):
            submit_next()

        while future_to_task:
            for future in as_completed(list(future_to_task)):
                task = future_to_task.pop(future)
                try:
                    result = future.result()
                except Exception as exc:  # noqa: BLE001
                    result = {
                        "stage": "decision",
                        "run_slug": task.run_slug,
                        "status": "exception",
                        "error": str(exc),
                        "finished_at": datetime.now().isoformat(timespec="seconds"),
                    }
                results.append(result)
                ok = result.get("status") == "skipped_passed" or result.get("returncode") == 0
                if not ok:
                    failures += 1
                    print(f"[decision failed] {task.run_slug} failures={failures}", flush=True)
                else:
                    print(f"[decision ok] {task.run_slug}", flush=True)
                write_status(tasks, results)
                if failures >= args.max_failures:
                    print(f"max failures reached: {failures}", flush=True)
                    return results
                submit_next()
                break
    return results


def run_postprocess(tasks: list[BatchTask], args: argparse.Namespace) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, task in enumerate(tasks, start=1):
        if not manifest_passed(task):
            results.append({"stage": "postprocess", "run_slug": task.run_slug, "status": "skipped_decision_not_passed"})
            continue
        if args.resume and combined_passed(task):
            results.append({"stage": "postprocess", "run_slug": task.run_slug, "status": "skipped_combined_passed"})
            continue
        print(f"[post {index}/{len(tasks)}] {task.run_slug}", flush=True)
        validation = run_validation(task)
        results.append(validation)
        if validation.get("returncode") != 0 or not validation_passed(task):
            results.append({"stage": "postprocess", "run_slug": task.run_slug, "status": "skipped_validation_failed"})
            write_status(tasks, results)
            continue
        materialize = run_materialize(task)
        results.append(materialize)
        if materialize.get("returncode") != 0:
            results.append({"stage": "postprocess", "run_slug": task.run_slug, "status": "skipped_materialize_failed"})
            write_status(tasks, results)
            continue
        combined = run_combined(task)
        results.append(combined)
        write_status(tasks, results)
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run official v7 DS v2 fullbook batch decisions and draft materialization.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--max-workers", type=int, default=20)
    parser.add_argument("--max-failures", type=int, default=20)
    parser.add_argument("--model", default="deepseek-chat")
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--stage", choices=["prepare", "decisions", "postprocess", "all"], default="all")
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--only-first", type=int, default=0, help="For smoke tests; 0 means all tasks.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    tasks = load_tasks(args.limit)
    if args.only_first:
        tasks = tasks[: args.only_first]
    prepare_slices(tasks)
    write_status(tasks, [])
    print(f"tasks: {len(tasks)} requests: {sum(task.row_count for task in tasks)}", flush=True)
    print(f"max_workers: {args.max_workers} stage: {args.stage}", flush=True)
    print(f"status: {RUN_LOG_DIR / 'run_status.json'}", flush=True)

    results: list[dict[str, Any]] = []
    if args.stage in {"decisions", "all"}:
        results.extend(run_decisions_concurrent(tasks, args))
    if args.stage in {"postprocess", "all"}:
        results.extend(run_postprocess(tasks, args))
    write_status(tasks, results)
    print(f"done. status: {RUN_LOG_DIR / 'run_status.json'}", flush=True)


if __name__ == "__main__":
    main()
