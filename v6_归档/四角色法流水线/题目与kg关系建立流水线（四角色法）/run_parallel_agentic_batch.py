"""
Conservative parallel runner for option-level agentic evidence binding.

Each worker launches run_agentic_search_experiment.py for one small group of
questions. This avoids output-file collisions while reducing repeated BGE load
and evidence-pool encoding cost.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import FIRST_COMPLETED, Future, wait
from datetime import datetime
from pathlib import Path
from typing import Any


BASE = Path(__file__).resolve().parent
FORMAL_OUTPUT_DIR = BASE / "output" / "step1_ai_responses"
RUN_AGENTIC = BASE / "run_agentic_search_experiment.py"
QUESTIONS_FILE = BASE / "数据" / "data" / "questions.json"
DESIRED_EVIDENCE_SCOPE = "ch2-plus-v6-except"


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_key_from_bashrc(env: dict[str, str]) -> None:
    """Mirror the manual PowerShell setup used in earlier runs, without printing secrets."""
    if any(env.get(name) for name in ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")):
        return
    bashrc = Path.home() / ".bashrc"
    if not bashrc.exists():
        return
    pattern = re.compile(r"^\s*(?:export\s+)?(DEEPSEEK_API_KEY|DS_API_KEY|DS_KEY)\s*=\s*['\"]?([^'\"]+)['\"]?\s*$")
    for line in bashrc.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = pattern.match(line)
        if match:
            env[match.group(1)] = match.group(2)
            return


def existing_result(qid: str, output_dir: Path) -> dict[str, Any] | None:
    path = output_dir / f"q_{qid}.json"
    if not path.exists():
        return None
    try:
        return read_json(path)
    except Exception:
        return None


def all_question_ids() -> list[str]:
    data = read_json(QUESTIONS_FILE)
    return [item["id"] for item in data.get("questions", []) if item.get("id")]


def existing_question_ids(output_dir: Path) -> list[str]:
    ids: list[str] = []
    for path in sorted(output_dir.glob("q_*.json")):
        data = existing_result(path.stem.removeprefix("q_"), output_dir)
        ids.append(data.get("question_id") if data else path.stem.removeprefix("q_"))
    return [qid for qid in ids if qid]


def is_weak(data: dict[str, Any]) -> bool:
    return bool(data.get("validation_issues")) or data.get("status") != "answered"


def select_ids(args: argparse.Namespace) -> list[str]:
    source_dir = Path(args.source_dir) if args.source_dir else FORMAL_OUTPUT_DIR
    if args.ids:
        selected = list(dict.fromkeys(args.ids))
    elif args.target == "all-existing":
        selected = existing_question_ids(source_dir)
    elif args.target == "all-questions":
        selected = all_question_ids()
    elif args.target == "missing-formal":
        formal_existing = set(existing_question_ids(Path(args.formal_dir)))
        selected = [qid for qid in all_question_ids() if qid not in formal_existing]
    elif args.target == "weak":
        selected = [
            qid
            for qid in existing_question_ids(source_dir)
            if (data := existing_result(qid, source_dir)) and is_weak(data)
        ]
    elif args.target == "not-fullbook":
        selected = [
            qid
            for qid in existing_question_ids(source_dir)
            if (data := existing_result(qid, source_dir)) and data.get("evidence_scope") != args.evidence_scope
        ]
    elif args.target == "no-teacher-hints":
        selected = [
            qid
            for qid in existing_question_ids(source_dir)
            if (data := existing_result(qid, source_dir)) and data.get("teacher_hint_mode") != "retrieval_only"
        ]
    else:
        raise ValueError(f"unknown target={args.target}")

    if args.skip_existing:
        output_dir = Path(args.output_dir)
        selected = [qid for qid in selected if not (output_dir / f"q_{qid}.json").exists()]
    if args.limit is not None:
        selected = selected[: args.limit]
    return selected


def chunked(items: list[str], size: int) -> list[list[str]]:
    if size <= 0:
        raise ValueError("group size must be > 0")
    return [items[i : i + size] for i in range(0, len(items), size)]


def command_for(qids: list[str], args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        str(RUN_AGENTIC),
        "--ids",
        *qids,
        "--force",
        "--max-followups",
        str(args.max_followups),
        "--top-k",
        str(args.top_k),
        "--card-scan",
        args.card_scan,
        "--evidence-scope",
        args.evidence_scope,
        "--output-dir",
        str(Path(args.output_dir)),
    ]
    if args.teacher_hints:
        command.append("--teacher-hints")
    return command


def summarize_output(qid: str, args: argparse.Namespace, log_path: Path, seconds: float, returncode: int) -> dict[str, Any]:
    output_file = Path(args.output_dir) / f"q_{qid}.json"
    data = existing_result(qid, Path(args.output_dir))
    quality = data.get("quality", {}) if data else {}
    return {
        "question_id": qid,
        "returncode": returncode,
        "seconds": round(seconds, 1),
        "output_file": str(output_file),
        "log_file": str(log_path),
        "status": data.get("status") if data else None,
        "teacher_hint_mode": data.get("teacher_hint_mode") if data else None,
        "evidence_scope": data.get("evidence_scope") if data else None,
        "external_reference_gaps": len(data.get("external_reference_gaps", [])) if data else 0,
        "validation_issues": data.get("validation_issues", []) if data else ["missing output json"],
        "direct": quality.get("direct_evidence_options"),
        "indirect": quality.get("indirect_evidence_options"),
        "none": quality.get("none_evidence_options"),
        "cited_cards": len(data.get("cited_cards", [])) if data else 0,
    }


def run_group(group: list[str], args: argparse.Namespace, env: dict[str, str], log_dir: Path) -> list[dict[str, Any]]:
    start = time.time()
    group_name = "__".join(group)
    if len(group_name) > 120:
        group_name = f"{group[0]}__to__{group[-1]}__{len(group)}"
    log_path = log_dir / f"{group_name}.log"
    cmd = command_for(group, args)
    with log_path.open("w", encoding="utf-8") as log:
        log.write("$ " + " ".join(cmd) + "\n\n")
        proc = subprocess.run(
            cmd,
            cwd=str(BASE),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=args.timeout_seconds * max(1, len(group)),
        )

    seconds = time.time() - start
    return [summarize_output(qid, args, log_path, seconds, proc.returncode) for qid in group]


def run_parallel(qids: list[str], args: argparse.Namespace) -> list[dict[str, Any]]:
    output_dir = Path(args.output_dir)
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = output_dir / "logs" / run_stamp
    log_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    load_key_from_bashrc(env)

    results: list[dict[str, Any]] = []
    pending = chunked(list(qids), args.group_size)
    running: dict[Future[list[dict[str, Any]]], list[str]] = {}

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        while pending or running:
            while pending and len(running) < args.max_workers:
                group = pending.pop(0)
                future = executor.submit(run_group, group, args, env, log_dir)
                running[future] = group
                done_count = len(results)
                print(f"START {' '.join(group)} ({done_count + len(group)}/{len(qids)} questions queued/running)")

            done, _ = wait(running, return_when=FIRST_COMPLETED)
            for future in done:
                group = running.pop(future)
                try:
                    group_results = future.result()
                except Exception as exc:
                    group_results = [
                        {
                            "question_id": qid,
                            "returncode": -1,
                            "seconds": None,
                            "status": None,
                            "validation_issues": [str(exc)[:500]],
                        }
                        for qid in group
                    ]
                results.extend(group_results)
                for result in group_results:
                    print(
                        "DONE {qid}: rc={rc} status={status} d/i/n={d}/{i}/{n} issues={issues} seconds={sec}".format(
                            qid=result.get("question_id"),
                            rc=result.get("returncode"),
                            status=result.get("status"),
                            d=result.get("direct"),
                            i=result.get("indirect"),
                            n=result.get("none"),
                            issues=len(result.get("validation_issues") or []),
                            sec=result.get("seconds"),
                        )
                    )
    return results


def write_reports(results: list[dict[str, Any]], args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    report_dir = output_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = report_dir / f"parallel_summary_{stamp}.json"
    md_path = report_dir / f"parallel_summary_{stamp}.md"

    write_json(
        json_path,
        {
            "args": vars(args),
            "count": len(results),
            "results": results,
        },
    )

    status_counts: dict[str, int] = {}
    issue_count = 0
    external_count = 0
    for item in results:
        status_counts[item.get("status") or "missing"] = status_counts.get(item.get("status") or "missing", 0) + 1
        issue_count += 1 if item.get("validation_issues") else 0
        external_count += 1 if item.get("external_reference_gaps") else 0

    lines = [
        "# Parallel Agentic Batch Summary",
        "",
        f"- target: `{args.target}`",
        f"- output_dir: `{output_dir}`",
        f"- evidence_scope: `{args.evidence_scope}`",
        f"- teacher_hints: `{args.teacher_hints}`",
        f"- max_workers: `{args.max_workers}`",
        f"- count: `{len(results)}`",
        f"- status_counts: `{status_counts}`",
        f"- questions_with_validation_issues: `{issue_count}`",
        f"- questions_with_external_reference_gaps: `{external_count}`",
        "",
        "| question_id | status | d/i/n | issues | external_gaps | seconds |",
        "|---|---|---|---:|---:|---:|",
    ]
    for item in sorted(results, key=lambda row: row.get("question_id") or ""):
        lines.append(
            "| {qid} | {status} | {d}/{i}/{n} | {issues} | {external} | {sec} |".format(
                qid=item.get("question_id"),
                status=item.get("status"),
                d=item.get("direct"),
                i=item.get("indirect"),
                n=item.get("none"),
                issues=len(item.get("validation_issues") or []),
                external=item.get("external_reference_gaps"),
                sec=item.get("seconds"),
            )
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"SUMMARY_JSON {json_path}")
    print(f"SUMMARY_MD {md_path}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run agentic evidence binding with small safe parallelism.")
    parser.add_argument("--ids", nargs="*", help="Explicit question IDs. Overrides --target.")
    parser.add_argument(
        "--target",
        choices=[
            "weak",
            "not-fullbook",
            "no-teacher-hints",
            "missing-formal",
            "all-existing",
            "all-questions",
        ],
        default="weak",
        help="Question selector when --ids is not provided.",
    )
    parser.add_argument("--source-dir", help="Directory used to select existing-result targets.")
    parser.add_argument(
        "--formal-dir",
        default=str(FORMAL_OUTPUT_DIR),
        help="Formal output directory used by --target missing-formal.",
    )
    parser.add_argument("--output-dir", default=str(BASE / "output" / "agentic_parallel_teacher_hints"))
    parser.add_argument("--limit", type=int, help="Limit selected question count.")
    parser.add_argument("--skip-existing", action="store_true", help="Do not run IDs already present in output-dir.")
    parser.add_argument("--max-workers", type=int, default=2, help="Use 2 by default; 3 is usually the upper safe limit.")
    parser.add_argument(
        "--group-size",
        type=int,
        default=1,
        help="Questions per worker process. Use 4-6 to reuse one BGE load across several questions.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--max-followups", type=int, default=1)
    parser.add_argument("--top-k", type=int, default=30)
    parser.add_argument("--card-scan", choices=["off", "correct", "all"], default="off")
    parser.add_argument("--evidence-scope", choices=["ch2", "v6-sentence", "v6-except-ch2", "ch2-plus-v6-except"], default=DESIRED_EVIDENCE_SCOPE)
    parser.add_argument("--teacher-hints", action="store_true", help="Pass --teacher-hints to each one-question run.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.max_workers < 1:
        raise SystemExit("--max-workers must be >= 1")
    if args.max_workers > 3:
        print("Warning: max-workers > 3 can be slow or hit API limits because each worker loads BGE.")

    qids = select_ids(args)
    print(f"Selected {len(qids)} questions: {' '.join(qids)}")
    if args.dry_run or not qids:
        return 0

    results = run_parallel(qids, args)
    write_reports(results, args)
    failures = [item for item in results if item.get("returncode") != 0 or not item.get("status")]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
