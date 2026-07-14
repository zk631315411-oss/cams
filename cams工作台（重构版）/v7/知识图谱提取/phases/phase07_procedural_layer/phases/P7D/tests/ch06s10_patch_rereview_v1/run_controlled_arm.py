from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


TEST_DIR = Path(__file__).resolve().parent
PHASE_DIR = TEST_DIR.parents[3]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def merged_assessment_variant(source_path: Path) -> dict[str, Any]:
    payload = copy.deepcopy(read_json(source_path))
    card = payload["cards"][0]
    nodes = {node["node_id"]: node for node in card["flow_nodes"]}
    n2 = nodes["N2"]
    n5 = nodes["N5"]
    n2["label"] = "机构基于风险方法，合计直接和间接持股比例并与适用阈值比较，以识别客户的UBO"
    n2["evidence_unit_ids"] = list(
        dict.fromkeys([*(n2.get("evidence_unit_ids") or []), *(n5.get("evidence_unit_ids") or [])])
    )
    card["flow_nodes"] = [node for node in card["flow_nodes"] if node["node_id"] != "N5"]

    kept_edges: list[dict[str, Any]] = []
    for edge in card["flow_edges"]:
        if edge["edge_id"] in {"E4", "E5"}:
            continue
        if edge["edge_id"] == "E6":
            edge["source"] = "N2"
        kept_edges.append(edge)
    card["flow_edges"] = kept_edges
    card["review_notes"] = (
        "测试变体：将原N2的UBO识别与原N5的持股合计/阈值比较合并为一个语义完整的assessment process；"
        "保留入口N1、标准N3、输入N4和结果N6，不新增无原文依据的时序边。"
    )
    payload["cards"] = [card]
    payload["test_variant"] = {
        "name": "merge_N2_N5_assessment_process",
        "source_cards_path": source_path.resolve().as_posix(),
        "source_cards_sha256": sha256(source_path),
        "production_mutated": False,
    }
    return payload


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def baseline(artifact_dir: Path, baseline_ref: Path, cards_path: Path) -> int:
    review_path = baseline_ref / "p7d_edge_reviews.jsonl"
    manifest_path = baseline_ref / "p7d_review_manifest.jsonl"
    reviews = [row for row in read_jsonl(review_path) if row.get("section_id") == "CH06-S10"]
    manifests = [row for row in read_jsonl(manifest_path) if row.get("section_id") == "CH06-S10"]
    write_jsonl(artifact_dir / "archived_ch06_s10_edge_reviews.jsonl", reviews)
    write_jsonl(artifact_dir / "archived_ch06_s10_review_manifest.jsonl", manifests)
    write_json(
        artifact_dir / "archive_manifest.json",
        {
            "archive_mode": "immutable_reference_and_filtered_snapshot",
            "source_p7d_dir": baseline_ref.resolve().as_posix(),
            "source_edge_reviews_sha256": sha256(review_path),
            "source_cards_path": cards_path.resolve().as_posix(),
            "source_cards_sha256": sha256(cards_path),
            "section_id": "CH06-S10",
            "review_count": len(reviews),
            "card_manifest_count": len(manifests),
        },
    )

    structure_dir = artifact_dir / "structure"
    completed = run(
        [
            sys.executable,
            "scripts/validate_and_route_cards.py",
            "--cards",
            str(cards_path),
            "--output-dir",
            str(structure_dir),
        ],
        PHASE_DIR,
    )
    (artifact_dir / "structure.stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (artifact_dir / "structure.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    structures = read_jsonl(structure_dir / "p7d_structure_manifest.jsonl")
    write_json(
        artifact_dir / "result.json",
        {
            "arm": "baseline",
            "command_return_code": completed.returncode,
            "structure_statuses": {row["card_id"]: row["structure_status"] for row in structures},
            "card_001_errors": next(
                (row.get("structure_errors") for row in structures if row.get("card_id") == "p7card_CH06-S10_001"),
                [],
            ),
            "semantic_review_possible_for_card_001": False,
        },
    )
    return completed.returncode


def variant(artifact_dir: Path, cards_path: Path) -> int:
    variant_cards = artifact_dir / "CH06-S10" / "cards.merged_test_variant.json"
    write_json(variant_cards, merged_assessment_variant(cards_path))
    run_id = "p7d_ch06_merge_v3_20260713"
    short_output_root = TEST_DIR / "outputs"
    completed = run(
        [
            sys.executable,
            "scripts/run_p7d_edge_review_ds.py",
            "--cards",
            str(variant_cards),
            "--output-dir",
            str(short_output_root),
            "--run-id",
            run_id,
            "--model",
            "deepseek-v4-pro",
            "--thinking-effort",
            "none",
            "--concurrency",
            "2",
            "--max-tokens",
            "16000",
            "--timeout",
            "300",
            "--retries",
            "2",
        ],
        PHASE_DIR,
    )
    (artifact_dir / "p7d.stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (artifact_dir / "p7d.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    run_dir = short_output_root / run_id
    result: dict[str, Any] = {
        "arm": "variant",
        "command_return_code": completed.returncode,
        "run_id": run_id,
        "run_dir": run_dir.resolve().as_posix(),
    }
    if completed.returncode == 0 and (run_dir / "p7d_edge_reviews.jsonl").exists():
        edge_reviews = read_jsonl(run_dir / "p7d_edge_reviews.jsonl")
        card_manifests = read_jsonl(run_dir / "p7d_review_manifest.jsonl")
        result.update(
            {
                "structure_status": card_manifests[0].get("structure_status") if card_manifests else None,
                "card_result": card_manifests[0].get("card_result") if card_manifests else None,
                "edge_statuses": {row["edge_id"]: row["review_status"] for row in edge_reviews},
                "answer_eligible_edge_ids": [row["edge_id"] for row in edge_reviews if row.get("answer_eligible")],
                "retrieval_only_edge_ids": [
                    row["edge_id"]
                    for row in edge_reviews
                    if row.get("retrieval_eligible") and not row.get("answer_eligible")
                ],
            }
        )
        summary_dir = artifact_dir / "p7d_summary"
        summary_dir.mkdir(parents=True, exist_ok=True)
        for name in (
            "p7d_structure_manifest.jsonl",
            "p7d_edge_reviews.jsonl",
            "p7d_review_manifest.jsonl",
            "p7d_review_history.jsonl",
            "p7d_human_review_queue.jsonl",
            "p7d_rejected_edge_queue.jsonl",
            "p7d_edge_review_report.md",
            "p7d_run_manifest.json",
        ):
            shutil.copy2(run_dir / name, summary_dir / name)
    write_json(artifact_dir / "result.json", result)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=["baseline", "variant"], required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--variant-ref", required=True)
    args = parser.parse_args()
    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    if args.arm == "baseline":
        return baseline(artifact_dir, Path(args.baseline_ref), Path(args.variant_ref))
    return variant(artifact_dir, Path(args.variant_ref))


if __name__ == "__main__":
    raise SystemExit(main())
