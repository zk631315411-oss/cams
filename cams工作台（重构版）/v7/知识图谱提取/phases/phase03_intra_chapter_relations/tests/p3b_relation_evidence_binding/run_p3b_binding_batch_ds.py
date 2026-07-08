from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


TEST_DIR = Path(__file__).resolve().parent
PHASE_DIR = TEST_DIR.parent.parent
DEFAULT_RELATIONS = PHASE_DIR / "outputs" / "p3a_reviewed_relations_first5.jsonl"
SINGLE_RUNNER = TEST_DIR / "run_p3b_relation_evidence_binding_ds.py"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def run_one(args: argparse.Namespace, relation: dict[str, Any]) -> dict[str, Any]:
    relation_id = str(relation.get("relation_id") or "")
    run_slug = f"{args.run_prefix}{relation_id}"
    cmd = [
        sys.executable,
        str(SINGLE_RUNNER),
        "--relations-file",
        str(args.relations_file),
        "--relation-id",
        relation_id,
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
    parsed_path = TEST_DIR / "runs" / run_slug / "parsed_response.json"
    binding_count = 0
    support_strength = None
    if parsed_path.exists():
        parsed = read_json(parsed_path)
        bindings = parsed.get("relation_evidence_bindings") or []
        binding_count = len(bindings)
        if bindings:
            support_strength = bindings[0].get("support_strength")
    return {
        "relation_id": relation_id,
        "chapter_id": relation.get("chapter_id"),
        "relation_type": relation.get("relation_type"),
        "run_slug": run_slug,
        "status": status,
        "returncode": proc.returncode,
        "binding_count": binding_count,
        "support_strength": support_strength,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--relations-file", type=Path, default=DEFAULT_RELATIONS)
    parser.add_argument("--run-prefix", default=None)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--max-tokens", type=int, default=12000)
    parser.add_argument("--disable-thinking", action="store_true", default=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.relations_file = args.relations_file.resolve()
    if args.run_prefix is None:
        args.run_prefix = "p3b_binding_first5_" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_"
    relations = read_jsonl(args.relations_file)
    if not relations:
        raise SystemExit("No relations found.")

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
        future_map = {executor.submit(run_one, args, relation): relation for relation in relations}
        for future in as_completed(future_map):
            result = future.result()
            results.append(result)
            print(json.dumps({"status": result["status"], "relation_id": result["relation_id"], "support_strength": result["support_strength"]}, ensure_ascii=False))

    order = {str(rel.get("relation_id")): index for index, rel in enumerate(relations)}
    results.sort(key=lambda row: order.get(row["relation_id"], 10**9))
    summary = {
        "schema_version": "p3b_binding_batch_ds_summary_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_prefix": args.run_prefix,
        "relations_file": str(args.relations_file),
        "model": args.model,
        "max_tokens": args.max_tokens,
        "disable_thinking": args.disable_thinking,
        "concurrency": args.concurrency,
        "selected_count": len(relations),
        "passed_count": sum(1 for row in results if row["status"] == "passed"),
        "failed_count": sum(1 for row in results if row["status"] != "passed"),
        "results": results,
    }
    summary_path = TEST_DIR / "runs" / f"{args.run_prefix.rstrip('_')}_summary.json"
    write_json(summary_path, summary)
    print(json.dumps({"summary_path": str(summary_path), "passed": summary["passed_count"], "failed": summary["failed_count"]}, ensure_ascii=False))
    if summary["failed_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
