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
DEFAULT_PROMPT_PATH = P7C_DIR / "prompts" / "section_card_extraction_v1.md"
VALIDATOR_PATH = PHASE_DIR / "scripts" / "validate_process_cards.py"
DEFAULT_OUTPUT_DIR = TEST_DIR / "outputs"

API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


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
    names = " / ".join(API_KEY_ENV_NAMES)
    raise RuntimeError(f"{names} are not set; cannot call LLM API.")


def strip_json_fence(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def parse_json_object(raw_text: str) -> dict[str, Any] | None:
    cleaned = strip_json_fence(raw_text)
    if not cleaned:
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    try:
        import json_repair

        return json.loads(json_repair.repair_json(cleaned))
    except Exception:
        return None


def collect_allowed_unit_ids(task: dict[str, Any]) -> list[str]:
    unit_ids: list[str] = []
    seen: set[str] = set()
    for unit in task.get("units") or []:
        unit_id = unit.get("unit_id") if isinstance(unit, dict) else None
        if unit_id and unit_id not in seen:
            seen.add(unit_id)
            unit_ids.append(unit_id)
    if unit_ids:
        return unit_ids
    text = task.get("section_text_with_unit_anchors") or ""
    for unit_id in re.findall(r"\[(v7u_[^|\]]+)\|", text):
        if unit_id not in seen:
            seen.add(unit_id)
            unit_ids.append(unit_id)
    return unit_ids


def parse_validation_error_count(report_path: Path) -> int | None:
    if not report_path.exists():
        return None
    match = re.search(r"^error_count:\s*(\d+)\s*$", report_path.read_text(encoding="utf-8-sig"), re.M)
    if not match:
        return None
    return int(match.group(1))


def build_prompt(prompt_template: str, task: dict[str, Any]) -> str:
    allowed_unit_ids = collect_allowed_unit_ids(task)
    section_block = f"""## Current Section

section_id: `{task.get('section_id')}`

section_title: `{task.get('section_title')}`

section_text_with_unit_anchors:

```text
{task.get('section_text_with_unit_anchors', '')}
```

allowed_unit_ids:

```json
{json.dumps(allowed_unit_ids, ensure_ascii=False, indent=2)}
```
"""
    marker = "## Current Section"
    if marker in prompt_template:
        return prompt_template.split(marker, 1)[0].rstrip() + "\n\n" + section_block
    return prompt_template.rstrip() + "\n\n" + section_block


def call_model(
    prompt: str,
    model: str,
    max_tokens: int,
    timeout: float,
    thinking_effort: str,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    api_key, base_url, env_name = get_llm_config()

    extra_body: dict[str, Any] = {}
    if thinking_effort != "none":
        extra_body = {"thinking": {"type": "enabled", "effort": thinking_effort}}

    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }
    if extra_body:
        payload.update(extra_body)

    endpoint = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {endpoint}: {detail}") from exc
    elapsed = round(time.time() - started, 3)
    usage = response_payload.get("usage") or {}
    meta = {
        "model": model,
        "base_url": base_url,
        "endpoint": endpoint,
        "api_key_env": env_name,
        "thinking_effort": thinking_effort,
        "request_extra": extra_body,
        "elapsed_seconds": elapsed,
        "usage": usage,
    }
    choices = response_payload.get("choices") or []
    if not choices:
        raise RuntimeError(f"No choices returned: {response_payload}")
    message = choices[0].get("message") or {}
    return (message.get("content") or "").strip(), usage, meta


def validate_cards(cards_path: Path, report_path: Path) -> tuple[int, str]:
    cmd = [sys.executable, str(VALIDATOR_PATH), "--cards", str(cards_path), "--report", str(report_path)]
    proc = subprocess.run(cmd, cwd=str(PHASE_DIR), text=True, capture_output=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one P7C section extraction with DS v4 pro.")
    parser.add_argument("--section-id", default="CH47-S01")
    parser.add_argument("--packages-dir", default=str(DEFAULT_PACKAGES_DIR))
    parser.add_argument("--prompt", default=str(DEFAULT_PROMPT_PATH))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--thinking-effort", default="none", choices=["none", "low", "medium", "high"])
    parser.add_argument("--max-tokens", type=int, default=20000)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    package_path = Path(args.packages_dir) / args.section_id / "task.json"
    if not package_path.exists():
        raise SystemExit(f"Missing section package: {package_path}")

    prompt_template = Path(args.prompt).read_text(encoding="utf-8-sig")
    task = read_json(package_path)
    prompt = build_prompt(prompt_template, task)

    section_dir = Path(args.output_dir) / run_id / args.section_id
    section_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = section_dir / "prompt.md"
    raw_path = section_dir / "raw_response.txt"
    cards_path = section_dir / "cards.raw.json"
    manifest_path = section_dir / "run_manifest.json"
    validation_report_path = section_dir / "validation_report.md"

    prompt_path.write_text(prompt, encoding="utf-8")
    manifest: dict[str, Any] = {
        "run_id": run_id,
        "section_id": args.section_id,
        "section_title": task.get("section_title"),
        "package_path": str(package_path),
        "prompt_path": str(prompt_path),
        "prompt_sha256": sha256_text(prompt),
        "model": args.model,
        "thinking_effort": args.thinking_effort,
        "max_tokens": args.max_tokens,
        "timeout": args.timeout,
        "input_policy": "section_text_with_unit_anchors_plus_allowed_unit_ids_only",
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }

    try:
        raw, usage, call_meta = call_model(
            prompt=prompt,
            model=args.model,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
            thinking_effort=args.thinking_effort,
        )
        raw_path.write_text(raw + "\n", encoding="utf-8")
        parsed = parse_json_object(raw)
        manifest.update({"call_meta": call_meta, "raw_response_path": str(raw_path), "raw_sha256": sha256_text(raw)})
        if parsed is None:
            manifest["status"] = "parse_failed"
            write_json(manifest_path, manifest)
            raise SystemExit(f"LLM response could not be parsed as JSON. Raw: {raw_path}")
        write_json(cards_path, parsed)
        manifest["cards_path"] = str(cards_path)
        manifest["card_count"] = len(parsed.get("cards") or []) if isinstance(parsed, dict) else None

        validator_code, validator_output = validate_cards(cards_path, validation_report_path)
        validation_error_count = parse_validation_error_count(validation_report_path)
        manifest["validation_report_path"] = str(validation_report_path)
        manifest["validator_returncode"] = validator_code
        manifest["validation_error_count"] = validation_error_count
        manifest["validator_output"] = validator_output
        if validator_code != 0:
            manifest["status"] = "validation_command_failed"
        elif validation_error_count is None:
            manifest["status"] = "validation_report_unreadable"
        elif validation_error_count > 0:
            manifest["status"] = "validation_failed"
        else:
            manifest["status"] = "ok"
    except Exception as exc:
        manifest["status"] = "failed"
        manifest["error"] = repr(exc)
        write_json(manifest_path, manifest)
        raise

    manifest["finished_at"] = datetime.now().isoformat(timespec="seconds")
    write_json(manifest_path, manifest)
    print(f"P7C section test complete: {args.section_id}")
    print(f"cards: {cards_path}")
    print(f"validation: {validation_report_path}")
    print(f"manifest: {manifest_path}")


if __name__ == "__main__":
    main()
