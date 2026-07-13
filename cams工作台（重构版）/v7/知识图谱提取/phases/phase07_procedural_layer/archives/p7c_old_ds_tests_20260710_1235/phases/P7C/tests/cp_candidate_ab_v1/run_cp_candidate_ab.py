from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


TEST_DIR = Path(__file__).resolve().parent
P7C_DIR = TEST_DIR.parents[1]
PHASES_DIR = P7C_DIR.parent
PHASE_DIR = PHASES_DIR.parent

DEFAULT_PACKAGES_DIR = PHASES_DIR / "P7B" / "section_packages"
DEFAULT_DIRECT_PROMPT = TEST_DIR.parent / "card_scope_definition_v1" / "prompts" / "section_card_extraction_scope_v1.md"
DEFAULT_CANDIDATE_PROMPT = TEST_DIR / "prompts" / "cp_to_flow_node_candidates_v1.md"
DEFAULT_B_OVERLAY = TEST_DIR / "prompts" / "cp_candidate_card_extraction_overlay_v1.md"
DEFAULT_OUTPUT_DIR = TEST_DIR / "outputs"
VALIDATOR_PATH = PHASE_DIR / "scripts" / "validate_process_cards.py"

FOCUS6 = ["CH47-S06", "CH49-S13", "CH49-S16", "CH47-S03", "CH47-S04", "CH49-S10"]
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
ALLOWED_CANDIDATE_KINDS = {
    "scenario",
    "trigger",
    "action",
    "decision",
    "input",
    "criterion",
    "condition",
    "safeguard",
    "limitation",
    "exception",
    "outcome",
    "implication",
    "output",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_llm_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_DEEPSEEK_BASE_URL
            return value, base_url, env_name
    raise RuntimeError(f"None of {' / '.join(API_KEY_ENV_NAMES)} is set; cannot call DS API.")


def strip_json_fence(text: str) -> str:
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    return cleaned.strip()


def parse_json_object(raw_text: str) -> dict[str, Any] | None:
    cleaned = strip_json_fence(raw_text)
    if not cleaned:
        return None
    try:
        payload = json.loads(cleaned)
        return payload if isinstance(payload, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            payload = json.loads(match.group(0))
            return payload if isinstance(payload, dict) else None
        except json.JSONDecodeError:
            pass
    try:
        import json_repair

        payload = json.loads(json_repair.repair_json(cleaned))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def collect_allowed_unit_ids(task: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for unit in task.get("units") or []:
        unit_id = unit.get("unit_id") if isinstance(unit, dict) else None
        if unit_id and unit_id not in seen:
            seen.add(unit_id)
            ids.append(unit_id)
    return ids


def collect_cp_unit_ids(core_points: list[dict[str, Any]]) -> set[str]:
    unit_ids: set[str] = set()
    for cp in core_points:
        for field in ("anchor_unit_ids", "key_unit_ids", "support_unit_ids"):
            unit_ids.update(uid for uid in cp.get(field) or [] if isinstance(uid, str))
    return unit_ids


def build_cp_unit_excerpt_map(task: dict[str, Any], core_points: list[dict[str, Any]]) -> dict[str, Any]:
    cp_unit_ids = collect_cp_unit_ids(core_points)
    excerpts: dict[str, Any] = {}
    for unit in task.get("units") or []:
        unit_id = unit.get("unit_id") if isinstance(unit, dict) else None
        if unit_id in cp_unit_ids:
            excerpts[unit_id] = {
                "type": unit.get("type"),
                "en_quote": unit.get("en_quote"),
                "knowledge_zh": unit.get("knowledge_zh"),
            }
    return excerpts


def replace_template_values(template: str, values: dict[str, str]) -> str:
    result = template
    for marker, value in values.items():
        result = result.replace(f"<{marker}>", value)
    return result


def build_candidate_prompt(
    template: str,
    task: dict[str, Any],
    core_points: list[dict[str, Any]],
    cp_edges: list[dict[str, Any]],
) -> str:
    return replace_template_values(
        template,
        {
            "section_id": str(task.get("section_id") or ""),
            "section_title": str(task.get("section_title") or ""),
            "core_points": json.dumps(core_points, ensure_ascii=False, indent=2),
            "same_section_cp_edges": json.dumps(cp_edges, ensure_ascii=False, indent=2),
            "cp_unit_excerpt_map": json.dumps(build_cp_unit_excerpt_map(task, core_points), ensure_ascii=False, indent=2),
        },
    )


def section_input_block(task: dict[str, Any]) -> str:
    return f"""## Current Section

section_id: `{task.get('section_id')}`

section_title: `{task.get('section_title')}`

section_text_with_unit_anchors:

```text
{task.get('section_text_with_unit_anchors', '')}
```

allowed_unit_ids:

```json
{json.dumps(collect_allowed_unit_ids(task), ensure_ascii=False, indent=2)}
```
"""


def prompt_without_current_section(template: str) -> str:
    marker = "## Current Section"
    return template.split(marker, 1)[0].rstrip() if marker in template else template.rstrip()


def build_direct_prompt(template: str, task: dict[str, Any]) -> str:
    return prompt_without_current_section(template) + "\n\n" + section_input_block(task)


def build_b_prompt(base_template: str, overlay_template: str, task: dict[str, Any], candidates: dict[str, Any]) -> str:
    overlay = overlay_template.replace(
        "<flow_node_candidates_payload>",
        json.dumps(candidates, ensure_ascii=False, indent=2),
    )
    return prompt_without_current_section(base_template) + "\n\n" + overlay.rstrip() + "\n\n" + section_input_block(task)


def call_model(
    prompt: str,
    model: str,
    max_tokens: int,
    timeout: float,
    thinking_effort: str,
) -> tuple[str, dict[str, Any]]:
    api_key, base_url, env_name = get_llm_config()
    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    if thinking_effort != "none":
        payload["thinking"] = {"type": "enabled", "effort": thinking_effort}

    endpoint = base_url.rstrip("/") + "/chat/completions"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {endpoint}: {detail}") from exc

    choices = response_payload.get("choices") or []
    if not choices:
        raise RuntimeError(f"No choices returned: {response_payload}")
    raw = ((choices[0].get("message") or {}).get("content") or "").strip()
    meta = {
        "model": model,
        "base_url": base_url,
        "endpoint": endpoint,
        "api_key_env": env_name,
        "thinking_effort": thinking_effort,
        "max_tokens": max_tokens,
        "elapsed_seconds": round(time.time() - started, 3),
        "usage": response_payload.get("usage") or {},
    }
    return raw, meta


def parse_validation_error_count(report_path: Path) -> int | None:
    if not report_path.exists():
        return None
    match = re.search(r"^error_count:\s*(\d+)\s*$", report_path.read_text(encoding="utf-8-sig"), re.M)
    return int(match.group(1)) if match else None


def validate_cards(cards_path: Path, report_path: Path) -> dict[str, Any]:
    command = [sys.executable, str(VALIDATOR_PATH), "--cards", str(cards_path), "--report", str(report_path)]
    proc = subprocess.run(command, cwd=str(PHASE_DIR), text=True, capture_output=True)
    return {
        "returncode": proc.returncode,
        "error_count": parse_validation_error_count(report_path),
        "output": ((proc.stdout or "") + (proc.stderr or "")).strip(),
    }


def validate_candidates(
    payload: dict[str, Any],
    section_id: str,
    core_points: list[dict[str, Any]],
    allowed_unit_ids: list[str],
) -> list[str]:
    errors: list[str] = []
    if payload.get("section_id") != section_id:
        errors.append(f"section_id mismatch: {payload.get('section_id')!r}")
    for forbidden in ("cards", "flow_nodes", "flow_edges"):
        if forbidden in payload:
            errors.append(f"first-stage payload must not contain {forbidden}")
    candidates = payload.get("flow_node_candidates")
    if not isinstance(candidates, list):
        return errors + ["flow_node_candidates must be a list"]

    cp_ids = {cp.get("core_point_id") for cp in core_points}
    unit_ids = set(allowed_unit_ids)
    candidate_ids: set[str] = set()
    for index, candidate in enumerate(candidates, 1):
        if not isinstance(candidate, dict):
            errors.append(f"candidate #{index} is not an object")
            continue
        candidate_id = candidate.get("candidate_id")
        if not candidate_id:
            errors.append(f"candidate #{index} missing candidate_id")
        elif candidate_id in candidate_ids:
            errors.append(f"duplicate candidate_id {candidate_id}")
        else:
            candidate_ids.add(candidate_id)
        if candidate.get("candidate_kind") not in ALLOWED_CANDIDATE_KINDS:
            errors.append(f"candidate {candidate_id or index} invalid candidate_kind {candidate.get('candidate_kind')!r}")
        if not candidate.get("candidate_label"):
            errors.append(f"candidate {candidate_id or index} missing candidate_label")
        source_cp_ids = candidate.get("source_core_point_ids") or []
        if not source_cp_ids:
            errors.append(f"candidate {candidate_id or index} missing source_core_point_ids")
        for cp_id in source_cp_ids:
            if cp_id not in cp_ids:
                errors.append(f"candidate {candidate_id or index} unknown core_point_id {cp_id}")
        evidence_ids = candidate.get("evidence_unit_ids") or []
        if not evidence_ids:
            errors.append(f"candidate {candidate_id or index} missing evidence_unit_ids")
        for unit_id in evidence_ids:
            if unit_id not in unit_ids:
                errors.append(f"candidate {candidate_id or index} unknown unit_id {unit_id}")
    return errors


def card_metrics(payload: dict[str, Any] | None) -> dict[str, Any]:
    cards = payload.get("cards") or [] if isinstance(payload, dict) else []
    nodes = [node for card in cards for node in (card.get("flow_nodes") or []) if isinstance(card, dict)]
    edges = [edge for card in cards for edge in (card.get("flow_edges") or []) if isinstance(card, dict)]
    source_units = {unit_id for card in cards for unit_id in (card.get("source_unit_ids") or []) if isinstance(card, dict)}
    return {
        "card_count": len(cards),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "source_unit_count": len(source_units),
        "titles": [str(card.get("title") or "") for card in cards if isinstance(card, dict)],
        "card_types": [str(card.get("card_type") or "") for card in cards if isinstance(card, dict)],
    }


def run_json_call(
    *,
    prompt: str,
    output_dir: Path,
    output_filename: str,
    model: str,
    thinking_effort: str,
    max_tokens: int,
    timeout: float,
    dry_run: bool,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = output_dir / "prompt.md"
    raw_path = output_dir / "raw_response.txt"
    parsed_path = output_dir / output_filename
    manifest_path = output_dir / "run_manifest.json"
    prompt_path.write_text(prompt, encoding="utf-8")
    manifest: dict[str, Any] = {
        "prompt_path": str(prompt_path),
        "prompt_sha256": sha256_text(prompt),
        "model": model,
        "thinking_effort": thinking_effort,
        "max_tokens": max_tokens,
        "timeout": timeout,
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }
    if dry_run:
        manifest.update({"status": "dry_run", "finished_at": datetime.now().isoformat(timespec="seconds")})
        write_json(manifest_path, manifest)
        return None, manifest

    try:
        raw, call_meta = call_model(prompt, model, max_tokens, timeout, thinking_effort)
        raw_path.write_text(raw + "\n", encoding="utf-8")
        parsed = parse_json_object(raw)
        manifest.update({"call_meta": call_meta, "raw_response_path": str(raw_path), "raw_sha256": sha256_text(raw)})
        if parsed is None:
            manifest["status"] = "parse_failed"
            raise RuntimeError(f"DS response is not a JSON object: {raw_path}")
        write_json(parsed_path, parsed)
        manifest.update({"status": "ok", "parsed_path": str(parsed_path)})
    except Exception as exc:
        manifest.update({"status": "failed", "error": repr(exc)})
        write_json(manifest_path, manifest)
        raise
    manifest["finished_at"] = datetime.now().isoformat(timespec="seconds")
    write_json(manifest_path, manifest)
    return parsed, manifest


def run_cards_arm(
    *,
    prompt: str,
    output_dir: Path,
    args: argparse.Namespace,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    payload, manifest = run_json_call(
        prompt=prompt,
        output_dir=output_dir,
        output_filename="cards.raw.json",
        model=args.model,
        thinking_effort=args.thinking_effort,
        max_tokens=args.max_tokens_cards,
        timeout=args.timeout,
        dry_run=args.dry_run,
    )
    if payload is None:
        return None, manifest
    validation = validate_cards(output_dir / "cards.raw.json", output_dir / "validation_report.md")
    manifest["validation"] = validation
    manifest["metrics"] = card_metrics(payload)
    if validation["returncode"] != 0 or validation["error_count"] not in (0, None):
        manifest["status"] = "validation_failed"
    write_json(output_dir / "run_manifest.json", manifest)
    return payload, manifest


def write_section_comparison(
    path: Path,
    section_id: str,
    candidate_count: int | None,
    direct_manifest: dict[str, Any],
    b_manifest: dict[str, Any],
) -> None:
    a_metrics = direct_manifest.get("metrics") or {}
    b_metrics = b_manifest.get("metrics") or {}
    lines = [
        f"# AB Comparison: {section_id}",
        "",
        f"- candidate_count: {candidate_count if candidate_count is not None else 'n/a'}",
        f"- A status: `{direct_manifest.get('status')}`",
        f"- B status: `{b_manifest.get('status')}`",
        "",
        "| metric | A direct | B CP candidates |",
        "|---|---:|---:|",
    ]
    for key in ("card_count", "node_count", "edge_count", "source_unit_count"):
        lines.append(f"| {key} | {a_metrics.get(key, 'n/a')} | {b_metrics.get(key, 'n/a')} |")
    a_errors = (direct_manifest.get("validation") or {}).get("error_count", "n/a")
    b_errors = (b_manifest.get("validation") or {}).get("error_count", "n/a")
    lines.append(f"| validation_error_count | {a_errors} | {b_errors} |")
    lines.extend(["", "## A Titles", ""])
    lines.extend([f"- {title}" for title in a_metrics.get("titles") or []] or ["- none"])
    lines.extend(["", "## B Titles", ""])
    lines.extend([f"- {title}" for title in b_metrics.get("titles") or []] or ["- none"])
    lines.extend([
        "",
        "## Manual Review",
        "",
        "- [ ] B improves recall or graph completeness.",
        "- [ ] B does not promote ordinary KG material into P7.",
        "- [ ] B edges are supported by section units rather than CP order or CP-CP edges.",
        "- [ ] Parallel criteria are not serialized with unsupported PRECEDES edges.",
        "- [ ] Candidate deletion, merge, split, and supplementation are reasonable.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_run_summary(output_dir: Path, run_id: str, rows: list[dict[str, Any]], dry_run: bool) -> None:
    summary = {"run_id": run_id, "dry_run": dry_run, "sections": rows}
    write_json(output_dir / "run_summary.json", summary)
    lines = [
        f"# CP Candidate AB Summary: {run_id}",
        "",
        f"dry_run: `{str(dry_run).lower()}`",
        "",
        "| section | candidates | A cards | B cards | A errors | B errors | status |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['section_id']} | {row.get('candidate_count', 'n/a')} | {row.get('a_card_count', 'n/a')} | "
            f"{row.get('b_card_count', 'n/a')} | {row.get('a_validation_errors', 'n/a')} | "
            f"{row.get('b_validation_errors', 'n/a')} | {row.get('status')} |"
        )
    (output_dir / "run_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run P7C direct-vs-CP-candidate AB tests.")
    parser.add_argument("--sections", nargs="+", default=FOCUS6)
    parser.add_argument("--packages-dir", default=str(DEFAULT_PACKAGES_DIR))
    parser.add_argument("--direct-prompt", default=str(DEFAULT_DIRECT_PROMPT))
    parser.add_argument("--candidate-prompt", default=str(DEFAULT_CANDIDATE_PROMPT))
    parser.add_argument("--b-overlay", default=str(DEFAULT_B_OVERLAY))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--thinking-effort", choices=["none", "low", "medium", "high"], default="none")
    parser.add_argument("--max-tokens-candidates", type=int, default=8000)
    parser.add_argument("--max-tokens-cards", type=int, default=20000)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(args.output_dir) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    packages_dir = Path(args.packages_dir)
    direct_template = Path(args.direct_prompt).read_text(encoding="utf-8-sig")
    candidate_template = Path(args.candidate_prompt).read_text(encoding="utf-8-sig")
    b_overlay = Path(args.b_overlay).read_text(encoding="utf-8-sig")
    write_json(
        output_dir / "run_plan.json",
        {
            "run_id": run_id,
            "sections": args.sections,
            "arms": {
                "A_direct": "section units -> final cards",
                "B_cp_candidates": "CP + CP edges -> candidates; candidates + section units -> final cards",
            },
            "model": args.model,
            "thinking_effort": args.thinking_effort,
            "dry_run": args.dry_run,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
    )

    rows: list[dict[str, Any]] = []
    for section_id in args.sections:
        print(f"[{section_id}] loading package")
        section_dir = output_dir / section_id
        package_dir = packages_dir / section_id
        row: dict[str, Any] = {"section_id": section_id, "status": "started"}
        try:
            task = read_json(package_dir / "task.json")
            core_points = read_json(package_dir / "core_points.json")
            cp_edges = read_json(package_dir / "same_section_cp_edges.json")

            print(f"[{section_id}] A direct extraction")
            direct_payload, direct_manifest = run_cards_arm(
                prompt=build_direct_prompt(direct_template, task),
                output_dir=section_dir / "A_direct",
                args=args,
            )

            print(f"[{section_id}] B round 1 candidate generation")
            candidate_dir = section_dir / "B_cp_candidates" / "01_candidates"
            candidate_payload, candidate_manifest = run_json_call(
                prompt=build_candidate_prompt(candidate_template, task, core_points, cp_edges),
                output_dir=candidate_dir,
                output_filename="flow_node_candidates.raw.json",
                model=args.model,
                thinking_effort=args.thinking_effort,
                max_tokens=args.max_tokens_candidates,
                timeout=args.timeout,
                dry_run=args.dry_run,
            )
            if candidate_payload is None:
                candidate_payload = {"section_id": section_id, "flow_node_candidates": [], "dry_run_placeholder": True}
                candidate_errors: list[str] = []
            else:
                candidate_errors = validate_candidates(
                    candidate_payload,
                    section_id,
                    core_points,
                    collect_allowed_unit_ids(task),
                )
                write_json(candidate_dir / "candidate_validation.json", {"error_count": len(candidate_errors), "errors": candidate_errors})
                candidate_manifest["candidate_validation_error_count"] = len(candidate_errors)
                candidate_manifest["candidate_count"] = len(candidate_payload.get("flow_node_candidates") or [])
                if candidate_errors:
                    candidate_manifest["status"] = "candidate_validation_failed"
                write_json(candidate_dir / "run_manifest.json", candidate_manifest)

            print(f"[{section_id}] B round 2 final extraction")
            b_payload, b_manifest = run_cards_arm(
                prompt=build_b_prompt(direct_template, b_overlay, task, candidate_payload),
                output_dir=section_dir / "B_cp_candidates" / "02_cards",
                args=args,
            )

            candidate_count = None if args.dry_run else len(candidate_payload.get("flow_node_candidates") or [])
            write_section_comparison(
                section_dir / "ab_comparison.md",
                section_id,
                candidate_count,
                direct_manifest,
                b_manifest,
            )
            a_metrics = card_metrics(direct_payload)
            b_metrics = card_metrics(b_payload)
            row.update(
                {
                    "candidate_count": candidate_count if candidate_count is not None else "n/a",
                    "candidate_validation_errors": len(candidate_errors),
                    "a_card_count": a_metrics["card_count"] if direct_payload is not None else "n/a",
                    "b_card_count": b_metrics["card_count"] if b_payload is not None else "n/a",
                    "a_validation_errors": (direct_manifest.get("validation") or {}).get("error_count", "n/a"),
                    "b_validation_errors": (b_manifest.get("validation") or {}).get("error_count", "n/a"),
                    "status": "dry_run" if args.dry_run else "ok",
                }
            )
        except Exception as exc:
            row.update({"status": "failed", "error": repr(exc)})
            print(f"[{section_id}] FAILED: {exc}", file=sys.stderr)
        rows.append(row)
        write_run_summary(output_dir, run_id, rows, args.dry_run)

    failed = [row for row in rows if row.get("status") == "failed"]
    print(f"AB run complete: {output_dir}")
    if failed:
        raise SystemExit(f"{len(failed)} section(s) failed; see run_summary.json")


if __name__ == "__main__":
    main()
