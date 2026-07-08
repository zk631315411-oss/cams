from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
DEFAULT_P2A_RUNS_DIR = PHASE_DIR / "runs"
DEFAULT_P2A_PREFIX = "p2a_batch_first5_chapters_20260706_"
DEFAULT_P2B_RUN_PREFIX = "p2b_first5_reviewed_20260706_"
DEFAULT_PROMPT = PHASE_DIR / "prompts" / "p2c_section_cp_relations_v1.md"
SINGLE_RUNNER = SCRIPT_DIR / "run_p2c_section_ds.py"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def discover_sections(runs_dir: Path, prefix: str) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for run_dir in sorted(runs_dir.glob(f"{prefix}*")):
        if not run_dir.is_dir():
            continue
        input_path = run_dir / "input_section.json"
        output_path = run_dir / "parsed_response.json"
        if not input_path.exists() or not output_path.exists():
            continue
        section_input = read_json(input_path)
        section_id = str(section_input.get("section_id") or "")
        if not section_id:
            section_id = str(read_json(output_path).get("section_id") or "")
        if not section_id:
            continue
        tasks.append(
            {
                "chapter_id": section_input.get("chapter_id"),
                "section_id": section_id,
                "section_order": section_input.get("section_order"),
                "section_title": section_input.get("section_title"),
            }
        )
    return sorted(
        tasks,
        key=lambda row: (
            str(row.get("chapter_id") or ""),
            int(row.get("section_order") or 0),
            str(row.get("section_id") or ""),
        ),
    )


def run_one(args: argparse.Namespace, task: dict[str, Any]) -> dict[str, Any]:
    run_slug = f"{args.run_prefix}{task['section_id']}"
    cmd = [
        sys.executable,
        str(SINGLE_RUNNER),
        "--section-id",
        str(task["section_id"]),
        "--p2a-runs-dir",
        str(args.p2a_runs_dir),
        "--p2a-run-prefix",
        args.p2a_run_prefix,
        "--p2b-run-prefix",
        args.p2b_run_prefix,
        "--prompt-file",
        str(args.prompt_file),
        "--run-slug",
        run_slug,
        "--model",
        args.model,
        "--max-tokens",
        str(args.max_tokens),
    ]
    if args.disable_thinking:
        cmd.append("--disable-thinking")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    status = "passed" if proc.returncode == 0 else "failed"
    return {
        **task,
        "run_slug": run_slug,
        "status": status,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p2a-runs-dir", type=Path, default=DEFAULT_P2A_RUNS_DIR)
    parser.add_argument("--p2a-run-prefix", default=DEFAULT_P2A_PREFIX)
    parser.add_argument("--p2b-run-prefix", default=DEFAULT_P2B_RUN_PREFIX)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--run-prefix", default=None)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--max-tokens", type=int, default=12000)
    parser.add_argument("--disable-thinking", action="store_true", default=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.p2a_runs_dir = args.p2a_runs_dir.resolve()
    args.prompt_file = args.prompt_file.resolve()
    if args.run_prefix is None:
        args.run_prefix = "p2c_first5_sections_" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_"

    all_tasks = discover_sections(args.p2a_runs_dir, args.p2a_run_prefix)
    if args.limit and args.limit > 0:
        selected = all_tasks[args.start_index : args.start_index + args.limit]
    else:
        selected = all_tasks[args.start_index :]
    if not selected:
        raise SystemExit("No P2A sections found for P2C batch.")

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        future_map = {executor.submit(run_one, args, task): task for task in selected}
        for future in as_completed(future_map):
            result = future.result()
            results.append(result)
            print(json.dumps({"status": result["status"], "section_id": result["section_id"]}, ensure_ascii=False))

    order = {task["section_id"]: index for index, task in enumerate(selected)}
    results.sort(key=lambda row: order.get(row["section_id"], 10**9))
    summary = {
        "schema_version": "p2c_batch_ds_summary_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_prefix": args.run_prefix,
        "model": args.model,
        "max_tokens": args.max_tokens,
        "disable_thinking": args.disable_thinking,
        "concurrency": args.concurrency,
        "selected_count": len(selected),
        "passed_count": sum(1 for row in results if row["status"] == "passed"),
        "failed_count": sum(1 for row in results if row["status"] != "passed"),
        "results": results,
    }
    summary_path = PHASE_DIR / "reports" / f"{args.run_prefix.rstrip('_')}_summary.json"
    write_json(summary_path, summary)
    print(json.dumps({"summary_path": str(summary_path), "passed": summary["passed_count"], "failed": summary["failed_count"]}, ensure_ascii=False))
    if summary["failed_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
