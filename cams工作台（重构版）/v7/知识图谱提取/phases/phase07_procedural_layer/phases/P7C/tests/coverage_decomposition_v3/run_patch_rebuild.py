from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


TEST_DIR = Path(__file__).resolve().parent
PHASE_DIR = next(parent for parent in TEST_DIR.parents if (parent / "scripts" / "run_p7c_batch_ds.py").exists())
V1_RUNNER_PATH = PHASE_DIR / "phases" / "P7C" / "tests" / "coverage_decomposition_v1" / "run_coverage_decomposition.py"
DEFAULT_INITIAL_DIR = PHASE_DIR / "phases" / "P7C" / "outputs" / "ds_pro_none_additive_coverage_v23_10sections"
DEFAULT_PACKAGES_DIR = PHASE_DIR / "phases" / "P7B" / "section_packages"
DEFAULT_PATCH_PROMPT = TEST_DIR / "prompts" / "coverage_patch_v2.md"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


V1 = load_module("coverage_decomposition_v1_for_patch_rebuild", V1_RUNNER_PATH)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_sample(path: Path) -> list[str]:
    payload = read_json(path)
    items = payload.get("items") if isinstance(payload, dict) else payload
    if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
        raise ValueError("sample file must contain a string items list")
    return items


def run_baseline(sections: list[str], artifact_dir: Path, audit_source_dir: Path) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    for section_id in sections:
        source_dir = audit_source_dir / section_id
        target_dir = artifact_dir / section_id
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in ("cards.raw.json", "coverage_audit.json", "coverage_patch.json", "run_manifest.json"):
            source = source_dir / name
            if source.exists():
                shutil.copy2(source, target_dir / name)
        cards = read_json(target_dir / "cards.raw.json")
        manifests.append({
            "section_id": section_id,
            "status": "ok",
            "final_card_count": len(cards.get("cards") or []),
            "source": str(source_dir),
        })
    return manifests


def run_variant_section(
    section_id: str,
    artifact_dir: Path,
    audit_source_dir: Path,
    initial_dir: Path,
    packages_dir: Path,
    patch_template: str,
    model: str,
    thinking_effort: str,
    max_tokens: int,
    timeout: float,
    retries: int,
    retry_delay: float,
) -> dict[str, Any]:
    section_dir = artifact_dir / section_id
    section_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "section_id": section_id,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "status": "running",
        "audit_source": str(audit_source_dir / section_id / "coverage_audit.json"),
    }
    try:
        task = read_json(packages_dir / section_id / "task.json")
        original = V1.load_initial_payload(initial_dir, section_id)
        audit = read_json(audit_source_dir / section_id / "coverage_audit.json")
        allowed = V1.P7C_RUNNER.collect_allowed_unit_ids(task)
        audit_errors = V1.validate_audit(original, audit, set(allowed))
        if audit_errors:
            raise RuntimeError(f"source audit contract failed: {audit_errors}")
        gap_claims = [
            claim for claim in audit.get("claims") or []
            if claim.get("kg_boundary") == "p7_incremental"
            and claim.get("coverage_status") in {"missing", "partially_covered"}
        ]
        write_json(section_dir / "coverage_audit.json", audit)
        manifest["gap_claim_count"] = len(gap_claims)
        if gap_claims:
            patch_prompt = V1.build_patch_prompt(patch_template, task, original, gap_claims, allowed)
            (section_dir / "coverage_patch.prompt.md").write_text(patch_prompt, encoding="utf-8")
            patch, patch_raw, patch_meta, patch_attempts = V1.call_json(
                patch_prompt, model, thinking_effort, max_tokens, timeout, retries, retry_delay
            )
            (section_dir / "coverage_patch.raw.txt").write_text(patch_raw + "\n", encoding="utf-8")
            manifest["patch_call_attempts"] = patch_attempts
            manifest["patch_call_meta"] = patch_meta
            if patch is None:
                raise RuntimeError("coverage patch response could not be parsed")
        else:
            patch = {
                "section_id": section_id,
                "claim_resolutions": [],
                "new_cards": [],
                "card_supplements": [],
            }
            manifest["patch_call_attempts"] = []
            manifest["patch_call_meta"] = {}
        write_json(section_dir / "coverage_patch.json", patch)
        patch_errors = V1.validate_patch(original, gap_claims, patch, set(allowed))
        manifest["patch_contract_errors"] = patch_errors
        if patch_errors:
            raise RuntimeError("coverage patch contract failed")
        merged = V1.merge_patch(original, audit, patch)
        write_json(section_dir / "cards.raw.json", merged)
        unresolved = sum(
            1 for row in patch.get("claim_resolutions") or [] if row.get("resolution") == "unresolved"
        )
        manifest.update({
            "status": "ok_with_unresolved" if unresolved else "ok",
            "initial_card_count": len(original.get("cards") or []),
            "final_card_count": len(merged.get("cards") or []),
            "new_card_count": len(patch.get("new_cards") or []),
            "supplement_count": len(patch.get("card_supplements") or []),
            "unresolved_claim_count": unresolved,
        })
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = repr(exc)
    manifest["finished_at"] = datetime.now().isoformat(timespec="seconds")
    write_json(section_dir / "run_manifest.json", manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild P7C Coverage patches from a fixed Audit ledger.")
    parser.add_argument("--arm", choices=["baseline", "variant"], required=True)
    parser.add_argument("--sample-file", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--audit-source-dir", required=True)
    parser.add_argument("--initial-dir", default=str(DEFAULT_INITIAL_DIR))
    parser.add_argument("--packages-dir", default=str(DEFAULT_PACKAGES_DIR))
    parser.add_argument("--patch-prompt", default=str(DEFAULT_PATCH_PROMPT))
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--thinking-effort", choices=["none", "low", "medium", "high"], default="none")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-delay", type=float, default=5.0)
    args = parser.parse_args()

    sections = load_sample(Path(args.sample_file))
    artifact_dir = Path(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    audit_source_dir = Path(args.audit_source_dir)
    if args.arm == "baseline":
        manifests = run_baseline(sections, artifact_dir, audit_source_dir)
    else:
        patch_template = Path(args.patch_prompt).read_text(encoding="utf-8-sig")
        manifests: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as executor:
            futures = {
                executor.submit(
                    run_variant_section,
                    section_id,
                    artifact_dir,
                    audit_source_dir,
                    Path(args.initial_dir),
                    Path(args.packages_dir),
                    patch_template,
                    args.model,
                    args.thinking_effort,
                    args.max_tokens,
                    args.timeout,
                    args.retries,
                    args.retry_delay,
                ): section_id
                for section_id in sections
            }
            for future in as_completed(futures):
                result = future.result()
                manifests.append(result)
                print(
                    f"{result['section_id']}: {result['status']}, "
                    f"gaps={result.get('gap_claim_count')}, cards={result.get('final_card_count')}"
                )
    manifests.sort(key=lambda row: row["section_id"])
    write_json(artifact_dir / "run_summary.json", {
        "arm": args.arm,
        "sections": sections,
        "section_count": len(sections),
        "status_counts": {
            status: sum(1 for row in manifests if row.get("status") == status)
            for status in sorted({str(row.get("status")) for row in manifests})
        },
        "manifests": manifests,
    })
    return 0 if all(row.get("status") in {"ok", "ok_with_unresolved"} for row in manifests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
