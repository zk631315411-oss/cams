"""
Run the full Higher Algebra v4.4 pipeline up to Step 8A.

This orchestrator intentionally stops before 08_import_neo4j.py. It keeps the
original v4.4 step scripts as the source of truth and only handles batching,
parallel chunk execution, JSONL merging, and run logging.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_RUN_ROOT = SCRIPT_DIR / "正式_runs"
DEFAULT_UPPER_INPUT = SCRIPT_DIR / "中间产物" / "高等代数上册_full_clean.md"
DEFAULT_LOWER_INPUT = SCRIPT_DIR / "中间产物" / "高等代数下册_full_clean.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run gaodai full extraction to Step 8A.")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--upper-input", type=Path, default=DEFAULT_UPPER_INPUT)
    parser.add_argument("--lower-input", type=Path, default=DEFAULT_LOWER_INPUT)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--audit-workers", type=int, default=12)
    parser.add_argument("--model", default="")
    parser.add_argument("--step2-model", default=os.environ.get("LLM_STEP2_MODEL", "gpt-5.4-mini"))
    parser.add_argument("--step3-model", default=os.environ.get("LLM_STEP3_MODEL", "gpt-5.4"))
    parser.add_argument("--step4-model", default=os.environ.get("LLM_STEP4_MODEL", "gpt-5.5"))
    parser.add_argument("--audit-model", default=os.environ.get("LLM_AUDIT_MODEL", "gpt-5.5"))
    parser.add_argument("--conflict-model", default=os.environ.get("LLM_CONFLICT_MODEL", "gpt-5.5"))
    parser.add_argument("--base-url", default="")
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--audit-timeout", type=float, default=240)
    parser.add_argument("--step2-reasoning", default="medium")
    parser.add_argument("--step3-reasoning", default="medium")
    parser.add_argument("--step4-reasoning", default="high")
    parser.add_argument("--audit-reasoning", default="high")
    parser.add_argument("--conflict-reasoning", default="max")
    parser.add_argument("--step4-max-node-pool", type=int, default=48, help="Maximum node pool passed to Step 4A/4B chunk extractors.")
    parser.add_argument("--only-volume", choices=["shang", "xia"], default="", help="Run only one volume for a chapter test.")
    parser.add_argument("--chapter-prefix", default="", help="Keep only section_node_id values containing this chapter code, e.g. C01.")
    parser.add_argument("--chapter-prefixes", default="", help="Comma-separated chapter codes, e.g. C04,C05. Overrides --chapter-prefix.")
    parser.add_argument("--stop-after-step4c", action="store_true", help="Stop after Step 4C and write the combined pre-Step-5 package.")
    parser.add_argument("--chunk-retries", type=int, default=2, help="Retry failed chunk subprocesses before aborting.")
    parser.add_argument("--chunk-retry-delay", type=float, default=8.0, help="Seconds to wait between chunk retries.")
    parser.add_argument("--step4-hard-timeout", type=float, default=900, help="Parent-process hard timeout for each Step 4 chunk subprocess.")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--no-audit", action="store_true", help="Use Step 7A draft decisions directly.")
    return parser.parse_args()


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_run_dir(args: argparse.Namespace) -> Path:
    run_dir = args.run_dir or DEFAULT_RUN_ROOT / f"gaodai_full_v4_4_{now_stamp()}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def run_env(reasoning_effort: str = "") -> dict[str, str]:
    env = os.environ.copy()
    if env.get("LLM_API_KEY"):
        env["DEEPSEEK_API_KEY"] = env["LLM_API_KEY"]
        env["OPENAI_API_KEY"] = env["LLM_API_KEY"]
    if env.get("LLM_API_BASE"):
        env["DEEPSEEK_API_BASE"] = env["LLM_API_BASE"]
    if reasoning_effort:
        env["LLM_REASONING_EFFORT"] = reasoning_effort
    return env


def run_cmd(
    cmd: list[str],
    cwd: Path,
    log_path: Path,
    env: dict[str, str] | None = None,
    allowed_returncodes: set[int] | None = None,
    timeout_seconds: float | None = None,
) -> int:
    allowed = allowed_returncodes or {0}
    started = time.time()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8", newline="\n") as log:
        log.write("\n" + "=" * 80 + "\n")
        log.write(f"[START] {datetime.now().isoformat(timespec='seconds')}\n")
        log.write(" ".join(cmd) + "\n")
        log.flush()
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(cwd),
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed = time.time() - started
            if exc.stdout:
                log.write(str(exc.stdout))
            if exc.stderr:
                log.write(str(exc.stderr))
            log.write(f"\n[END] returncode=TIMEOUT elapsed={elapsed:.1f}s hard_timeout={timeout_seconds:.1f}s\n")
            raise RuntimeError(f"Command timed out after {timeout_seconds:.1f}s: {' '.join(cmd)}; see {log_path}") from exc
        log.write(proc.stdout)
        elapsed = time.time() - started
        log.write(f"\n[END] returncode={proc.returncode} elapsed={elapsed:.1f}s\n")
    if proc.returncode not in allowed:
        raise RuntimeError(f"Command failed ({proc.returncode}): {' '.join(cmd)}; see {log_path}")
    return proc.returncode


def run_cmd_with_retry(
    cmd: list[str],
    cwd: Path,
    log_path: Path,
    retries: int,
    retry_delay: float,
    env: dict[str, str] | None = None,
    timeout_seconds: float | None = None,
) -> None:
    last_error: Exception | None = None
    for attempt in range(max(0, retries) + 1):
        try:
            run_cmd(cmd, cwd=cwd, log_path=log_path, env=env, timeout_seconds=timeout_seconds)
            return
        except RuntimeError as exc:
            last_error = exc
            if attempt >= max(0, retries):
                break
            with log_path.open("a", encoding="utf-8", newline="\n") as log:
                log.write(f"[RETRY] attempt={attempt + 1} retry_after={retry_delay:.1f}s reason={exc}\n")
            time.sleep(max(0.0, retry_delay))
    if last_error is not None:
        raise last_error


def read_jsonl(path: Path, required: bool = True) -> list[dict]:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def concat_jsonl(output: Path, inputs: Iterable[Path]) -> int:
    count = 0
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as out:
        for path in inputs:
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                if line.strip():
                    out.write(line.rstrip() + "\n")
                    count += 1
    return count


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip())


def script(name: str) -> str:
    return str(SCRIPT_DIR / name)


def py_cmd(name: str, *args: str | Path | int | float) -> list[str]:
    return [sys.executable, script(name), *[str(arg) for arg in args]]


def common_llm_args(args: argparse.Namespace, step_model: str = "") -> list[str]:
    result: list[str] = []
    model = step_model or args.model
    if model:
        result += ["--model", model]
    if args.base_url:
        result += ["--base-url", args.base_url]
    if args.timeout:
        result += ["--timeout", str(args.timeout)]
    if args.mock:
        result.append("--mock")
    return result


def audit_llm_args(args: argparse.Namespace) -> list[str]:
    result: list[str] = []
    model = args.audit_model or os.environ.get("LLM_AUDIT_MODEL", "")
    if model:
        result += ["--model", model]
    if args.base_url:
        result += ["--base-url", args.base_url]
    if args.audit_timeout:
        result += ["--timeout", str(args.audit_timeout)]
    if args.mock:
        result.append("--mock")
    return result


def prepare_volume(
    label: str,
    textbook_id: str,
    textbook_name: str,
    input_path: Path,
    out_dir: Path,
    logs_dir: Path,
) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    config = out_dir / "v4_4_config.json"
    run_cmd(
        py_cmd(
            "00_prepare_config.py",
            "--input", input_path,
            "--output-dir", out_dir,
            "--config", config,
            "--textbook-id", textbook_id,
            "--textbook-name", textbook_name,
            "--course-name", "高等代数",
            "--overwrite",
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / f"{label}_step0_config.log",
        env=run_env(),
    )
    run_cmd(
        py_cmd(
            "01_build_textbook_tree.py",
            "--config", config,
            "--input", input_path,
            "--output-dir", out_dir,
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / f"{label}_step1_tree.log",
    )
    return {
        "dir": out_dir,
        "config": config,
        "leaf": out_dir / "leaf_sections.jsonl",
        "tree_nodes": out_dir / "tree_nodes.jsonl",
        "tree_edges": out_dir / "tree_edges.jsonl",
    }


def selected_ids(
    leaf_path: Path,
    source_scope: str | None = None,
    not_scopes: set[str] | None = None,
    chapter_prefix: str = "",
) -> list[str]:
    rows = read_jsonl(leaf_path)
    ids: list[str] = []
    prefixes = [
        part.strip().upper()
        for part in chapter_prefix.replace(";", ",").split(",")
        if part.strip()
    ]
    for row in rows:
        scope = str(row.get("source_scope") or "")
        if source_scope is not None and scope != source_scope:
            continue
        if not_scopes and scope in not_scopes:
            continue
        section_node_id = str(row.get("section_node_id") or "")
        section_node_id_upper = section_node_id.upper()
        if prefixes and not any(f":{prefix}:" in section_node_id_upper for prefix in prefixes):
            continue
        ids.append(section_node_id)
    return [item for item in ids if item]


def done_marker(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".done")


def run_chunked(
    step_name: str,
    volume_label: str,
    ids: list[str],
    worker_count: int,
    command_builder,
    temp_dir: Path,
    logs_dir: Path,
    skip_existing: bool,
    retries: int = 0,
    retry_delay: float = 0.0,
    env: dict[str, str] | None = None,
    hard_timeout: float | None = None,
) -> None:
    temp_dir.mkdir(parents=True, exist_ok=True)
    if not ids:
        return

    def run_one(index: int, section_id: str) -> str:
        safe = section_id.replace(":", "_").replace("/", "_").replace("\\", "_")
        chunk_dir = temp_dir / f"{index:04d}_{safe}"
        marker = done_marker(chunk_dir / "chunk")
        if skip_existing and marker.exists():
            return f"[SKIP] {step_name} {section_id}"
        if chunk_dir.exists():
            shutil.rmtree(chunk_dir)
        chunk_dir.mkdir(parents=True, exist_ok=True)
        cmd = command_builder(section_id, chunk_dir)
        run_cmd_with_retry(
            cmd,
            cwd=SCRIPT_DIR,
            log_path=logs_dir / f"{volume_label}_{step_name}_{index:04d}.log",
            retries=retries,
            retry_delay=retry_delay,
            env=env,
            timeout_seconds=hard_timeout,
        )
        marker.write_text(datetime.now().isoformat(timespec="seconds") + "\n", encoding="utf-8")
        return f"[OK] {step_name} {section_id}"

    print(f"[INFO] {volume_label} {step_name}: chunks={len(ids)} workers={worker_count}")
    with ThreadPoolExecutor(max_workers=max(1, worker_count)) as executor:
        futures = [executor.submit(run_one, index, section_id) for index, section_id in enumerate(ids, start=1)]
        for future in as_completed(futures):
            print(future.result(), flush=True)


def chunk_dirs(temp_dir: Path) -> list[Path]:
    if not temp_dir.exists():
        return []
    return sorted([p for p in temp_dir.iterdir() if p.is_dir()])


def merge_chunk_outputs(temp_dir: Path, mapping: dict[str, Path]) -> None:
    dirs = chunk_dirs(temp_dir)
    for filename, output in mapping.items():
        concat_jsonl(output, [directory / filename for directory in dirs])


def write_run_summary(run_dir: Path, summary: dict) -> None:
    (run_dir / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = ["# 高等代数全书 v4.4 运行摘要", ""]
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    (run_dir / "run_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    run_dir = ensure_run_dir(args)
    logs_dir = run_dir / "logs"
    combined_dir = run_dir / "combined"
    step5_dir = run_dir / "step5_normalized"
    step6_dir = run_dir / "step6_layers"
    step7_review_dir = run_dir / "step7_review"
    step7_approved_dir = run_dir / "step7_approved_package"
    step8_dir = run_dir / "step8_final_graph"
    logs_dir.mkdir(parents=True, exist_ok=True)

    print(f"[RUN] {run_dir}")
    chapter_filter = args.chapter_prefixes.strip() or args.chapter_prefix.strip()

    requested_volumes = [args.only_volume] if args.only_volume else ["shang", "xia"]
    volume_specs = {
        "shang": ("gaodai_shang", "高等代数上册", args.upper_input, run_dir / "上册"),
        "xia": ("gaodai_xia", "高等代数下册", args.lower_input, run_dir / "下册"),
    }
    volumes = {
        label: prepare_volume(label, textbook_id, textbook_name, input_path, out_dir, logs_dir)
        for label, (textbook_id, textbook_name, input_path, out_dir) in volume_specs.items()
        if label in requested_volumes
    }
    volume_values = list(volumes.values())

    # Step 2 summaries: core content only by config.
    for label, volume in volumes.items():
        ids = selected_ids(volume["leaf"], not_scopes={"exercise", "example"}, chapter_prefix=chapter_filter)
        temp = volume["dir"] / "_chunks_step2"

        def build_summary_cmd(section_id: str, chunk_dir: Path, volume=volume) -> list[str]:
            return py_cmd(
                "02_generate_section_summaries.py",
                "--config", volume["config"],
                "--leaf-sections", volume["leaf"],
                "--output", chunk_dir / "section_summaries.jsonl",
                "--warnings", chunk_dir / "section_summary_warnings.jsonl",
                "--chunk-id", section_id,
                *common_llm_args(args, args.step2_model),
            )

        run_chunked(
            "step2_summary",
            label,
            ids,
            args.workers,
            build_summary_cmd,
            temp,
            logs_dir,
            args.skip_existing,
            args.chunk_retries,
            args.chunk_retry_delay,
            run_env(args.step2_reasoning),
        )
        merge_chunk_outputs(
            temp,
            {
                "section_summaries.jsonl": volume["dir"] / "section_summaries.jsonl",
                "section_summary_warnings.jsonl": volume["dir"] / "section_summary_warnings.jsonl",
            },
        )

    # Step 3 explicit nodes: extraction only. Output is pre-audit.
    for label, volume in volumes.items():
        ids = selected_ids(volume["leaf"], not_scopes={"exercise", "example"}, chapter_prefix=chapter_filter)
        temp = volume["dir"] / "_chunks_step3_nodes"

        def build_node_cmd(section_id: str, chunk_dir: Path, volume=volume) -> list[str]:
            return py_cmd(
                "03_extract_explicit_nodes.py",
                "--config", volume["config"],
                "--leaf-sections", volume["leaf"],
                "--summaries", volume["dir"] / "section_summaries.jsonl",
                "--raw-output", chunk_dir / "raw_explicit_node_candidates.jsonl",
                "--nodes", chunk_dir / "nodes_pre_audit.jsonl",
                "--review", chunk_dir / "node_pre_audit_review_queue.jsonl",
                "--warnings", chunk_dir / "node_extraction_warnings.jsonl",
                "--report", chunk_dir / "node_extraction_report.md",
                "--chunk-id", section_id,
                "--keep-rejected-candidates",
                *common_llm_args(args, args.step3_model),
            )

        run_chunked(
            "step3_nodes",
            label,
            ids,
            args.workers,
            build_node_cmd,
            temp,
            logs_dir,
            args.skip_existing,
            args.chunk_retries,
            args.chunk_retry_delay,
            run_env(args.step3_reasoning),
        )
        merge_chunk_outputs(
            temp,
            {
                "raw_explicit_node_candidates.jsonl": volume["dir"] / "raw_explicit_node_candidates.jsonl",
                "nodes_pre_audit.jsonl": volume["dir"] / "nodes_pre_audit.jsonl",
                "node_pre_audit_review_queue.jsonl": volume["dir"] / "node_pre_audit_review_queue.jsonl",
                "node_extraction_warnings.jsonl": volume["dir"] / "node_extraction_warnings.jsonl",
            },
        )

    # Step 3A full LLM node audit. Accepted nodes enter the main node stream;
    # reviewed nodes still remain visible to Step 4 so relations are not lost.
    for label, volume in volumes.items():
        ids = selected_ids(volume["leaf"], not_scopes={"exercise", "example"}, chapter_prefix=chapter_filter)
        temp = volume["dir"] / "_chunks_step3a_node_audit"

        def build_node_audit_cmd(section_id: str, chunk_dir: Path, volume=volume) -> list[str]:
            return py_cmd(
                "03a_audit_explicit_nodes.py",
                "--config", volume["config"],
                "--leaf-sections", volume["leaf"],
                "--nodes-in", volume["dir"] / "nodes_pre_audit.jsonl",
                "--raw-output", chunk_dir / "raw_node_audit.jsonl",
                "--decisions", chunk_dir / "node_audit_decisions.jsonl",
                "--nodes-out", chunk_dir / "nodes.jsonl",
                "--nodes-for-step4", chunk_dir / "nodes_for_step4.jsonl",
                "--review", chunk_dir / "node_review_queue.jsonl",
                "--warnings", chunk_dir / "node_audit_warnings.jsonl",
                "--report", chunk_dir / "node_audit_report.md",
                "--chunk-id", section_id,
                *audit_llm_args(args),
            )

        run_chunked(
            "step3a_node_audit",
            label,
            ids,
            args.audit_workers,
            build_node_audit_cmd,
            temp,
            logs_dir,
            args.skip_existing,
            args.chunk_retries,
            args.chunk_retry_delay,
            run_env(args.audit_reasoning),
        )
        merge_chunk_outputs(
            temp,
            {
                "raw_node_audit.jsonl": volume["dir"] / "raw_node_audit.jsonl",
                "node_audit_decisions.jsonl": volume["dir"] / "node_audit_decisions.jsonl",
                "nodes.jsonl": volume["dir"] / "nodes.jsonl",
                "nodes_for_step4.jsonl": volume["dir"] / "nodes_for_step4.jsonl",
                "node_review_queue.jsonl": volume["dir"] / "node_review_queue.jsonl",
                "node_audit_warnings.jsonl": volume["dir"] / "node_audit_warnings.jsonl",
            },
        )

    combined_dir.mkdir(parents=True, exist_ok=True)
    concat_jsonl(combined_dir / "leaf_sections.jsonl", [volume["leaf"] for volume in volume_values])
    concat_jsonl(combined_dir / "nodes_pre_audit.jsonl", [volume["dir"] / "nodes_pre_audit.jsonl" for volume in volume_values])
    concat_jsonl(combined_dir / "node_audit_decisions.jsonl", [volume["dir"] / "node_audit_decisions.jsonl" for volume in volume_values])
    concat_jsonl(combined_dir / "nodes.jsonl", [volume["dir"] / "nodes.jsonl" for volume in volume_values])
    concat_jsonl(combined_dir / "nodes_for_step4.jsonl", [volume["dir"] / "nodes_for_step4.jsonl" for volume in volume_values])
    concat_jsonl(combined_dir / "node_review_queue.jsonl", [volume["dir"] / "node_review_queue.jsonl" for volume in volume_values])
    concat_jsonl(combined_dir / "tree_nodes.jsonl", [volume["tree_nodes"] for volume in volume_values])
    concat_jsonl(combined_dir / "tree_edges.jsonl", [volume["tree_edges"] for volume in volume_values])

    # Step 3B example frames.
    for label, volume in volumes.items():
        ids = selected_ids(volume["leaf"], source_scope="example", chapter_prefix=chapter_filter)
        temp = volume["dir"] / "_chunks_step3b_examples"

        def build_example_cmd(section_id: str, chunk_dir: Path, volume=volume) -> list[str]:
            return py_cmd(
                "03b_extract_example_frames.py",
                "--config", volume["config"],
                "--leaf-sections", volume["leaf"],
                "--summaries", volume["dir"] / "section_summaries.jsonl",
                "--raw-output", chunk_dir / "raw_example_frames.jsonl",
                "--frames", chunk_dir / "example_frames.jsonl",
                "--review", chunk_dir / "example_frame_review_queue.jsonl",
                "--warnings", chunk_dir / "example_frame_warnings.jsonl",
                "--report", chunk_dir / "example_frame_report.md",
                "--chunk-id", section_id,
                *common_llm_args(args, args.step3_model),
            )

        run_chunked(
            "step3b_examples",
            label,
            ids,
            args.workers,
            build_example_cmd,
            temp,
            logs_dir,
            args.skip_existing,
            args.chunk_retries,
            args.chunk_retry_delay,
            run_env(args.step3_reasoning),
        )
        merge_chunk_outputs(
            temp,
            {
                "raw_example_frames.jsonl": volume["dir"] / "raw_example_frames.jsonl",
                "example_frames.jsonl": volume["dir"] / "example_frames.jsonl",
                "example_frame_review_queue.jsonl": volume["dir"] / "example_frame_review_queue.jsonl",
                "example_frame_warnings.jsonl": volume["dir"] / "example_frame_warnings.jsonl",
            },
        )

        run_cmd(
            py_cmd(
                "03c_convert_example_frames.py",
                "--frames", volume["dir"] / "example_frames.jsonl",
                "--core-nodes", combined_dir / "nodes.jsonl",
                "--nodes-out", volume["dir"] / "example_app_nodes_raw.jsonl",
                "--edges-out", volume["dir"] / "example_app_edges_raw.jsonl",
                "--review-out", volume["dir"] / "example_app_review_raw.jsonl",
                "--report", volume["dir"] / "example_app_convert_report.md",
            ),
            cwd=SCRIPT_DIR,
            log_path=logs_dir / f"{label}_step3c_convert_examples.log",
        )
        run_cmd(
            py_cmd(
                "03d_normalize_example_applications.py",
                "--app-nodes", volume["dir"] / "example_app_nodes_raw.jsonl",
                "--app-edges", volume["dir"] / "example_app_edges_raw.jsonl",
                "--core-nodes", combined_dir / "nodes.jsonl",
                "--nodes-out", volume["dir"] / "example_app_nodes.jsonl",
                "--edges-out", volume["dir"] / "example_app_edges.jsonl",
                "--report", volume["dir"] / "example_app_normalize_report.md",
                "--clean-flow",
            ),
            cwd=SCRIPT_DIR,
            log_path=logs_dir / f"{label}_step3d_normalize_examples.log",
        )

    concat_jsonl(combined_dir / "example_app_nodes.jsonl", [volume["dir"] / "example_app_nodes.jsonl" for volume in volume_values])
    concat_jsonl(combined_dir / "example_app_edges.jsonl", [volume["dir"] / "example_app_edges.jsonl" for volume in volume_values])

    # Step 4A explicit edges, using the full Step 4 node pool for cross-volume references.
    # This step writes pre-audit candidates only; Step 4C decides which ones become
    # formal edges and which ones enter Step 7 review.
    for label, volume in volumes.items():
        ids = selected_ids(volume["leaf"], source_scope="core_content", chapter_prefix=chapter_filter)
        temp = volume["dir"] / "_chunks_step4_edges"

        def build_edge_cmd(section_id: str, chunk_dir: Path, volume=volume) -> list[str]:
            return py_cmd(
                "04_extract_explicit_edges.py",
                "--config", volume["config"],
                "--leaf-sections", volume["leaf"],
                "--nodes", combined_dir / "nodes_for_step4.jsonl",
                "--raw-output", chunk_dir / "raw_explicit_edge_candidates.jsonl",
                "--edges", chunk_dir / "edges_pre_audit.jsonl",
                "--review", chunk_dir / "edge_pre_audit_review_queue.jsonl",
                "--warnings", chunk_dir / "edge_extraction_warnings.jsonl",
                "--report", chunk_dir / "edge_extraction_report.md",
                "--chunk-id", section_id,
                "--keep-rejected-candidates",
                "--semantic-augment",
                "--max-node-pool", args.step4_max_node_pool,
                *common_llm_args(args, args.step4_model),
            )

        run_chunked(
            "step4_edges",
            label,
            ids,
            args.workers,
            build_edge_cmd,
            temp,
            logs_dir,
            args.skip_existing,
            args.chunk_retries,
            args.chunk_retry_delay,
            run_env(args.step4_reasoning),
            hard_timeout=args.step4_hard_timeout,
        )
        merge_chunk_outputs(
            temp,
            {
                "raw_explicit_edge_candidates.jsonl": volume["dir"] / "raw_explicit_edge_candidates.jsonl",
                "edges_pre_audit.jsonl": volume["dir"] / "edges_pre_audit.jsonl",
                "edge_pre_audit_review_queue.jsonl": volume["dir"] / "edge_pre_audit_review_queue.jsonl",
                "edge_extraction_warnings.jsonl": volume["dir"] / "edge_extraction_warnings.jsonl",
            },
        )

    concat_jsonl(combined_dir / "edges_pre_audit.jsonl", [volume["dir"] / "edges_pre_audit.jsonl" for volume in volume_values])
    concat_jsonl(combined_dir / "edge_pre_audit_review_queue.jsonl", [volume["dir"] / "edge_pre_audit_review_queue.jsonl" for volume in volume_values])

    # Step 4B rule cases, separated from ordinary binary edges.
    # This step also writes pre-audit candidates only; Step 4C audits the full
    # ordinary-edge and rule-case candidate set together.
    for label, volume in volumes.items():
        ids = selected_ids(volume["leaf"], source_scope="core_content", chapter_prefix=chapter_filter)
        temp = volume["dir"] / "_chunks_step4b_rule_cases"

        def build_rule_case_cmd(section_id: str, chunk_dir: Path, volume=volume) -> list[str]:
            return py_cmd(
                "04b_extract_rule_cases.py",
                "--config", volume["config"],
                "--leaf-sections", volume["leaf"],
                "--nodes", combined_dir / "nodes_for_step4.jsonl",
                "--raw-output", chunk_dir / "raw_rule_case_candidates.jsonl",
                "--rule-cases", chunk_dir / "rule_cases_pre_audit.jsonl",
                "--review", chunk_dir / "rule_case_pre_audit_review_queue.jsonl",
                "--warnings", chunk_dir / "rule_case_extraction_warnings.jsonl",
                "--report", chunk_dir / "rule_case_extraction_report.md",
                "--chunk-id", section_id,
                "--keep-rejected-candidates",
                "--max-node-pool", args.step4_max_node_pool,
                *common_llm_args(args, args.step4_model),
            )

        run_chunked(
            "step4b_rule_cases",
            label,
            ids,
            args.workers,
            build_rule_case_cmd,
            temp,
            logs_dir,
            args.skip_existing,
            args.chunk_retries,
            args.chunk_retry_delay,
            run_env(args.step4_reasoning),
            hard_timeout=args.step4_hard_timeout,
        )
        merge_chunk_outputs(
            temp,
            {
                "raw_rule_case_candidates.jsonl": volume["dir"] / "raw_rule_case_candidates.jsonl",
                "rule_cases_pre_audit.jsonl": volume["dir"] / "rule_cases_pre_audit.jsonl",
                "rule_case_pre_audit_review_queue.jsonl": volume["dir"] / "rule_case_pre_audit_review_queue.jsonl",
                "rule_case_extraction_warnings.jsonl": volume["dir"] / "rule_case_extraction_warnings.jsonl",
            },
        )

    concat_jsonl(combined_dir / "rule_cases_pre_audit.jsonl", [volume["dir"] / "rule_cases_pre_audit.jsonl" for volume in volume_values])
    concat_jsonl(combined_dir / "rule_case_pre_audit_review_queue.jsonl", [volume["dir"] / "rule_case_pre_audit_review_queue.jsonl" for volume in volume_values])

    # Step 4C full AI audit for ordinary edges and rule cases.
    # Only candidates reviewed by this gate become formal Step 5 inputs.
    for label, volume in volumes.items():
        ids = selected_ids(volume["leaf"], source_scope="core_content", chapter_prefix=chapter_filter)
        temp = volume["dir"] / "_chunks_step4c_edge_rule_case_audit"

        def build_edge_rule_case_audit_cmd(section_id: str, chunk_dir: Path, volume=volume) -> list[str]:
            return py_cmd(
                "04c_audit_edges_and_rule_cases.py",
                "--config", volume["config"],
                "--leaf-sections", volume["leaf"],
                "--edges-in", volume["dir"] / "edges_pre_audit.jsonl",
                "--rule-cases-in", volume["dir"] / "rule_cases_pre_audit.jsonl",
                "--raw-output", chunk_dir / "raw_edge_rule_case_audit.jsonl",
                "--decisions", chunk_dir / "edge_rule_case_audit_decisions.jsonl",
                "--edges-out", chunk_dir / "edges.jsonl",
                "--edge-review", chunk_dir / "edge_review_queue.jsonl",
                "--rule-cases-out", chunk_dir / "rule_cases.jsonl",
                "--rule-case-review", chunk_dir / "rule_case_review_queue.jsonl",
                "--warnings", chunk_dir / "edge_rule_case_audit_warnings.jsonl",
                "--report", chunk_dir / "edge_rule_case_audit_report.md",
                "--chunk-id", section_id,
                *audit_llm_args(args),
            )

        run_chunked(
            "step4c_edge_rule_case_audit",
            label,
            ids,
            args.audit_workers,
            build_edge_rule_case_audit_cmd,
            temp,
            logs_dir,
            args.skip_existing,
            args.chunk_retries,
            args.chunk_retry_delay,
            run_env(args.audit_reasoning),
            hard_timeout=args.step4_hard_timeout,
        )
        merge_chunk_outputs(
            temp,
            {
                "raw_edge_rule_case_audit.jsonl": volume["dir"] / "raw_edge_rule_case_audit.jsonl",
                "edge_rule_case_audit_decisions.jsonl": volume["dir"] / "edge_rule_case_audit_decisions.jsonl",
                "edges.jsonl": volume["dir"] / "edges.jsonl",
                "edge_review_queue.jsonl": volume["dir"] / "edge_review_queue.jsonl",
                "rule_cases.jsonl": volume["dir"] / "rule_cases.jsonl",
                "rule_case_review_queue.jsonl": volume["dir"] / "rule_case_review_queue.jsonl",
                "edge_rule_case_audit_warnings.jsonl": volume["dir"] / "edge_rule_case_audit_warnings.jsonl",
            },
        )

    concat_jsonl(combined_dir / "edge_rule_case_audit_decisions.jsonl", [volume["dir"] / "edge_rule_case_audit_decisions.jsonl" for volume in volume_values])
    concat_jsonl(combined_dir / "rule_cases.jsonl", [volume["dir"] / "rule_cases.jsonl" for volume in volume_values])
    concat_jsonl(combined_dir / "edges.jsonl", [volume["dir"] / "edges.jsonl" for volume in volume_values])
    concat_jsonl(combined_dir / "edge_review_queue.jsonl", [volume["dir"] / "edge_review_queue.jsonl" for volume in volume_values])
    concat_jsonl(combined_dir / "rule_case_review_queue.jsonl", [volume["dir"] / "rule_case_review_queue.jsonl" for volume in volume_values])

    if args.stop_after_step4c:
        summary = {
            "run_dir": str(run_dir),
            "stopped_before": "05_global_normalize_and_review.py",
            "selected_volumes": ",".join(volumes.keys()),
            "chapter_prefix": chapter_filter,
            "upper_leaf_sections": count_jsonl(volumes["shang"]["leaf"]) if "shang" in volumes else 0,
            "lower_leaf_sections": count_jsonl(volumes["xia"]["leaf"]) if "xia" in volumes else 0,
            "combined_nodes_pre_audit": count_jsonl(combined_dir / "nodes_pre_audit.jsonl"),
            "combined_node_audit_decisions": count_jsonl(combined_dir / "node_audit_decisions.jsonl"),
            "combined_nodes": count_jsonl(combined_dir / "nodes.jsonl"),
            "combined_nodes_for_step4": count_jsonl(combined_dir / "nodes_for_step4.jsonl"),
            "combined_node_review_queue": count_jsonl(combined_dir / "node_review_queue.jsonl"),
            "combined_edges_pre_audit": count_jsonl(combined_dir / "edges_pre_audit.jsonl"),
            "combined_rule_cases_pre_audit": count_jsonl(combined_dir / "rule_cases_pre_audit.jsonl"),
            "combined_edge_rule_case_audit_decisions": count_jsonl(combined_dir / "edge_rule_case_audit_decisions.jsonl"),
            "combined_edges": count_jsonl(combined_dir / "edges.jsonl"),
            "combined_edge_review_queue": count_jsonl(combined_dir / "edge_review_queue.jsonl"),
            "combined_rule_cases": count_jsonl(combined_dir / "rule_cases.jsonl"),
            "combined_rule_case_review_queue": count_jsonl(combined_dir / "rule_case_review_queue.jsonl"),
            "example_app_nodes": count_jsonl(combined_dir / "example_app_nodes.jsonl"),
            "example_app_edges": count_jsonl(combined_dir / "example_app_edges.jsonl"),
        }
        write_run_summary(run_dir, summary)
        print("[DONE] stopped after Step 4C and wrote the combined pre-Step-5 package")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    # Step 5 global normalize and review.
    step5_dir.mkdir(parents=True, exist_ok=True)
    run_cmd(
        py_cmd(
            "05_global_normalize_and_review.py",
            "--nodes", combined_dir / "nodes.jsonl",
            "--edges", combined_dir / "edges.jsonl",
            "--node-review", combined_dir / "node_review_queue.jsonl",
            "--edge-review", combined_dir / "edge_review_queue.jsonl",
            "--app-nodes", combined_dir / "example_app_nodes.jsonl",
            "--app-edges", combined_dir / "example_app_edges.jsonl",
            "--rule-cases-in", combined_dir / "rule_cases.jsonl",
            "--review-rule-cases-in", combined_dir / "rule_case_review_queue.jsonl",
            "--main-nodes-out", step5_dir / "main_nodes.jsonl",
            "--main-edges-out", step5_dir / "main_edges.jsonl",
            "--rule-cases-out", step5_dir / "rule_cases.jsonl",
            "--review-nodes-out", step5_dir / "review_nodes.jsonl",
            "--review-edges-out", step5_dir / "review_edges.jsonl",
            "--review-rule-cases-out", step5_dir / "review_rule_cases.jsonl",
            "--rejected-out", step5_dir / "rejected_archive.jsonl",
            "--report", step5_dir / "global_normalize_report.md",
            "--review-md", step5_dir / "global_review_queue.md",
            "--include-reviewed-app",
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step5_global_normalize.log",
    )

    # Step 5B Aggr semantic aggregation candidates. Review-only; no auto merge.
    run_cmd(
        py_cmd(
            "05b_generate_aggr_candidates.py",
            "--main-nodes", step5_dir / "main_nodes.jsonl",
            "--review-nodes", step5_dir / "review_nodes.jsonl",
            "--main-edges", step5_dir / "main_edges.jsonl",
            "--review-edges", step5_dir / "review_edges.jsonl",
            "--output", step5_dir / "aggr_candidates.jsonl",
            "--report", step5_dir / "aggr_report.md",
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step5b_aggr.log",
    )

    # Step 6 layers.
    run_cmd(
        py_cmd(
            "06_build_layered_candidates.py",
            "--main-nodes", step5_dir / "main_nodes.jsonl",
            "--main-edges", step5_dir / "main_edges.jsonl",
            "--rule-cases", step5_dir / "rule_cases.jsonl",
            "--review-nodes", step5_dir / "review_nodes.jsonl",
            "--review-edges", step5_dir / "review_edges.jsonl",
            "--review-rule-cases", step5_dir / "review_rule_cases.jsonl",
            "--rejected", step5_dir / "rejected_archive.jsonl",
            "--aggr-candidates", step5_dir / "aggr_candidates.jsonl",
            "--out-dir", step6_dir,
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step6_build_layers.log",
    )

    # Step 7A unified review items.
    run_cmd(
        py_cmd(
            "07a_build_review_items.py",
            "--layer-dir", step6_dir,
            "--out-dir", step7_review_dir,
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step7a_build_review_items.log",
    )

    # Step 7B AI review recommendations.
    review_cmd = py_cmd(
        "07b_ai_review_items.py",
        "--review-items", step7_review_dir / "review_items.jsonl",
        "--out-dir", step7_review_dir,
        "--batch-size", "1",
        "--max-workers", str(args.audit_workers),
        "--timeout", str(args.audit_timeout),
        "--api-key-env", "LLM_API_KEY",
        "--resume",
        "--max-budget-usd", "200",
    )
    if args.audit_model:
        review_cmd += ["--model", args.audit_model]
    if args.base_url:
        review_cmd += ["--base-url", args.base_url]
    if args.mock or args.no_audit:
        review_cmd.append("--mock")
    run_cmd(review_cmd, cwd=SCRIPT_DIR, log_path=logs_dir / "step7b_ai_review.log", env=run_env(args.audit_reasoning))

    # Step 7C rule validation and conflict resolution.
    validate_cmd = py_cmd(
        "07c_validate_and_resolve_conflicts.py",
        "--layer-dir", step6_dir,
        "--decisions", step7_review_dir / "ai_review_decisions.jsonl",
        "--out-dir", step7_review_dir,
        "--batch-size", "1",
        "--max-workers", str(args.audit_workers),
        "--timeout", str(args.audit_timeout),
        "--api-key-env", "LLM_API_KEY",
    )
    if args.conflict_model:
        validate_cmd += ["--model", args.conflict_model]
    if args.base_url:
        validate_cmd += ["--base-url", args.base_url]
    if args.mock or args.no_audit:
        validate_cmd.append("--mock")
        validate_cmd.append("--skip-ai-conflict-resolution")
    run_cmd(validate_cmd, cwd=SCRIPT_DIR, log_path=logs_dir / "step7c_validate_conflicts.log", env=run_env(args.conflict_reasoning))

    # Step 7D apply validated decisions.
    run_cmd(
        py_cmd(
            "07d_apply_review_results.py",
            "--layer-dir", step6_dir,
            "--decisions", step7_review_dir / "validated_review_decisions.jsonl",
            "--out-dir", step7_approved_dir,
            "--approval-label", "full-book-run-before-step8-assembly",
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step7d_apply_review_results.log",
    )

    # Step 7E report.
    run_cmd(
        py_cmd(
            "07e_review_report.py",
            "--review-dir", step7_review_dir,
            "--approved-dir", step7_approved_dir,
            "--output", step7_approved_dir / "review_closure_report.md",
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step7e_review_report.log",
    )

    # Step 8A final graph assembly. Exit code 2 means the package was written
    # but hard warnings exist, so import must remain blocked.
    step8a_returncode = run_cmd(
        py_cmd(
            "08a_assemble_final_graph.py",
            "--approved-dir", step7_approved_dir,
            "--out-dir", step8_dir,
        ),
        cwd=SCRIPT_DIR,
        log_path=logs_dir / "step8a_assemble_final_graph.log",
        allowed_returncodes={0, 2},
    )

    summary = {
        "run_dir": str(run_dir),
        "stopped_before": "08_import_neo4j.py",
        "step8a_returncode": step8a_returncode,
        "selected_volumes": ",".join(volumes.keys()),
        "chapter_prefix": chapter_filter,
        "upper_leaf_sections": count_jsonl(volumes["shang"]["leaf"]) if "shang" in volumes else 0,
        "lower_leaf_sections": count_jsonl(volumes["xia"]["leaf"]) if "xia" in volumes else 0,
        "combined_nodes_pre_audit": count_jsonl(combined_dir / "nodes_pre_audit.jsonl"),
        "combined_node_audit_decisions": count_jsonl(combined_dir / "node_audit_decisions.jsonl"),
        "combined_nodes": count_jsonl(combined_dir / "nodes.jsonl"),
        "combined_nodes_for_step4": count_jsonl(combined_dir / "nodes_for_step4.jsonl"),
        "combined_node_review_queue": count_jsonl(combined_dir / "node_review_queue.jsonl"),
        "combined_edges_pre_audit": count_jsonl(combined_dir / "edges_pre_audit.jsonl"),
        "combined_rule_cases_pre_audit": count_jsonl(combined_dir / "rule_cases_pre_audit.jsonl"),
        "combined_edge_rule_case_audit_decisions": count_jsonl(combined_dir / "edge_rule_case_audit_decisions.jsonl"),
        "combined_edges": count_jsonl(combined_dir / "edges.jsonl"),
        "combined_edge_review_queue": count_jsonl(combined_dir / "edge_review_queue.jsonl"),
        "combined_rule_cases": count_jsonl(combined_dir / "rule_cases.jsonl"),
        "combined_rule_case_review_queue": count_jsonl(combined_dir / "rule_case_review_queue.jsonl"),
        "example_app_nodes": count_jsonl(combined_dir / "example_app_nodes.jsonl"),
        "example_app_edges": count_jsonl(combined_dir / "example_app_edges.jsonl"),
        "step5_main_nodes": count_jsonl(step5_dir / "main_nodes.jsonl"),
        "step5_main_edges": count_jsonl(step5_dir / "main_edges.jsonl"),
        "step5_rule_cases": count_jsonl(step5_dir / "rule_cases.jsonl"),
        "step5_review_nodes": count_jsonl(step5_dir / "review_nodes.jsonl"),
        "step5_review_edges": count_jsonl(step5_dir / "review_edges.jsonl"),
        "step5_review_rule_cases": count_jsonl(step5_dir / "review_rule_cases.jsonl"),
        "step7_review_items": count_jsonl(step7_review_dir / "review_items.jsonl"),
        "step7_ai_review_decisions": count_jsonl(step7_review_dir / "ai_review_decisions.jsonl"),
        "step7_validated_decisions": count_jsonl(step7_review_dir / "validated_review_decisions.jsonl"),
        "approved_core_nodes": count_jsonl(step7_approved_dir / "approved_core_nodes.jsonl"),
        "approved_core_edges": count_jsonl(step7_approved_dir / "approved_core_edges.jsonl"),
        "approved_rule_cases": count_jsonl(step7_approved_dir / "approved_rule_cases.jsonl"),
        "merge_plans": count_jsonl(step7_approved_dir / "merge_plans.jsonl"),
        "deferred_items": count_jsonl(step7_approved_dir / "deferred_items.jsonl"),
        "review_archive": count_jsonl(step7_approved_dir / "review_archive.jsonl"),
        "final_core_nodes": count_jsonl(step8_dir / "final_core_nodes.jsonl"),
        "final_core_edges": count_jsonl(step8_dir / "final_core_edges.jsonl"),
        "final_application_nodes": count_jsonl(step8_dir / "final_application_nodes.jsonl"),
        "final_application_edges": count_jsonl(step8_dir / "final_application_edges.jsonl"),
        "final_rule_cases": count_jsonl(step8_dir / "final_rule_cases.jsonl"),
        "final_knowledge_groups": count_jsonl(step8_dir / "final_knowledge_groups.jsonl"),
        "final_knowledge_group_edges": count_jsonl(step8_dir / "final_knowledge_group_edges.jsonl"),
        "merged_nodes": count_jsonl(step8_dir / "merged_nodes.jsonl"),
        "step8_hard_warnings": count_jsonl(step8_dir / "step8_assembly_hard_warnings.jsonl"),
        "step8_soft_warnings": count_jsonl(step8_dir / "step8_assembly_soft_warnings.jsonl"),
    }
    write_run_summary(run_dir, summary)
    print("[DONE] assembled Step 8A final graph package and stopped before Neo4j import")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
