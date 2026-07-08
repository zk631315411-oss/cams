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
DEFAULT_RELATIONS = PHASE_DIR / "outputs" / "p3_core_point_relations.jsonl"
SINGLE_RUNNER = SCRIPT_DIR / "run_p3b_relation_evidence_binding_ds.py"


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


def unit_count(binding: dict[str, Any], key: str) -> int:
    value = binding.get(key)
    return len(value) if isinstance(value, list) else 0


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
    parsed_path = PHASE_DIR / "runs" / run_slug / "parsed_response.json"
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


def collect_bindings(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for result in results:
        parsed_path = PHASE_DIR / "runs" / str(result["run_slug"]) / "parsed_response.json"
        if not parsed_path.exists():
            continue
        parsed = read_json(parsed_path)
        for binding in parsed.get("relation_evidence_bindings") or []:
            if isinstance(binding, dict):
                bindings.append(binding)
    order = {str(result["relation_id"]): index for index, result in enumerate(results)}
    bindings.sort(key=lambda row: order.get(str(row.get("p3_relation_id")), 10**9))
    return bindings


def write_report(path: Path, summary: dict[str, Any], bindings: list[dict[str, Any]]) -> None:
    by_type: dict[str, int] = {}
    by_strength: dict[str, int] = {}
    flagged: list[dict[str, Any]] = []
    for binding in bindings:
        relation_type = str(binding.get("relation_type") or "")
        strength = str(binding.get("support_strength") or "")
        by_type[relation_type] = by_type.get(relation_type, 0) + 1
        by_strength[strength] = by_strength.get(strength, 0) + 1
        source_count = unit_count(binding, "source_evidence_unit_ids")
        target_count = unit_count(binding, "target_evidence_unit_ids")
        if source_count == 0 or target_count == 0 or source_count > 5 or target_count > 5:
            flagged.append(binding)

    lines = [
        "# P3B relation unit evidence report",
        "",
        f"- generated_at: {summary['generated_at']}",
        f"- run_prefix: {summary['run_prefix']}",
        f"- model: {summary['model']}",
        f"- concurrency: {summary['concurrency']}",
        f"- selected_count: {summary['selected_count']}",
        f"- passed_count: {summary['passed_count']}",
        f"- failed_count: {summary['failed_count']}",
        "",
        "## Relation types",
        "",
    ]
    lines.extend(f"- {key}: {by_type[key]}" for key in sorted(by_type))
    lines.extend(["", "## Support strength", ""])
    lines.extend(f"- {key}: {by_strength[key]}" for key in sorted(by_strength))
    lines.extend(["", "## Review flags", ""])
    if flagged:
        for binding in flagged:
            lines.append(
                f"- {binding.get('p3_relation_id')}: source_units={unit_count(binding, 'source_evidence_unit_ids')}, "
                f"target_units={unit_count(binding, 'target_evidence_unit_ids')}"
            )
    else:
        lines.append("- none")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_preview(path: Path, bindings: list[dict[str, Any]]) -> None:
    lines = ["# P3B relation unit evidence preview", ""]
    for binding in bindings:
        source_ids = ", ".join(binding.get("source_evidence_unit_ids") or [])
        target_ids = ", ".join(binding.get("target_evidence_unit_ids") or [])
        lines.extend(
            [
                f"## {binding.get('p3_relation_id')} ({binding.get('relation_type')})",
                "",
                f"- source_core_point_id: {binding.get('source_core_point_id')}",
                f"- target_core_point_id: {binding.get('target_core_point_id')}",
                f"- source_evidence_unit_ids: {source_ids}",
                f"- target_evidence_unit_ids: {target_ids}",
                f"- support_strength: {binding.get('support_strength')}",
                f"- evidence_summary: {binding.get('evidence_summary')}",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--relations-file", type=Path, default=DEFAULT_RELATIONS)
    parser.add_argument("--run-prefix", default=None)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--max-tokens", type=int, default=12000)
    parser.add_argument("--disable-thinking", action="store_true", default=True)
    parser.add_argument("--output-jsonl", type=Path, default=None)
    parser.add_argument("--report-md", type=Path, default=None)
    parser.add_argument("--preview-md", type=Path, default=None)
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
    summary_path = PHASE_DIR / "runs" / f"{args.run_prefix.rstrip('_')}_summary.json"
    write_json(summary_path, summary)

    stem = args.run_prefix.rstrip("_")
    output_jsonl = args.output_jsonl or (PHASE_DIR / "outputs" / f"{stem}.jsonl")
    report_md = args.report_md or (PHASE_DIR / "reports" / f"{stem}_report.md")
    preview_md = args.preview_md or (PHASE_DIR / "previews" / f"{stem}_preview.md")
    bindings = collect_bindings(results)
    write_jsonl(output_jsonl, bindings)
    write_report(report_md, summary, bindings)
    write_preview(preview_md, bindings)

    print(
        json.dumps(
            {
                "summary_path": str(summary_path),
                "output_jsonl": str(output_jsonl),
                "report_md": str(report_md),
                "preview_md": str(preview_md),
                "passed": summary["passed_count"],
                "failed": summary["failed_count"],
            },
            ensure_ascii=False,
        )
    )
    if summary["failed_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
