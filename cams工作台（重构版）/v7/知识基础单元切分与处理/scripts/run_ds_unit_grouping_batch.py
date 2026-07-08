from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DEFAULT_PROMPT = MODULE_DIR / "prompts" / "v7_unit_split_v2.md"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
ALLOWED_UNIT_TYPES = {
    "definition",
    "classification",
    "rule",
    "obligation",
    "process",
    "red_flag",
    "risk_indicator",
    "case_fact",
    "example",
    "fact",
    "needs_review",
}


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def sentence_ids(row: dict[str, Any]) -> list[str]:
    return [
        str(item.get("sentence_id"))
        for item in row.get("payload", {}).get("window", {}).get("sentences", [])
        if item.get("sentence_id")
    ]


def get_deepseek_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_BASE_URL
            return value, base_url, env_name
    raise RuntimeError("DEEPSEEK_API_KEY / DS_API_KEY / DS_KEY is not set.")


def build_messages(prompt_text: str, row: dict[str, Any]) -> list[dict[str, str]]:
    request_payload = {
        "request_id": row.get("request_id"),
        "block_id": row.get("block_id"),
        "pdf_page": row.get("pdf_page"),
        "printed_page": row.get("printed_page"),
        "chapter": row.get("chapter"),
        "payload": row.get("payload"),
    }
    return [
        {"role": "system", "content": prompt_text},
        {
            "role": "user",
            "content": "Group this request. Return one JSON object only.\n\n"
            + canonical_json(request_payload),
        },
    ]


def extract_json_object(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    candidates = [text]
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            try:
                import json_repair

                parsed = json.loads(json_repair.repair_json(candidate))
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                continue
    return None


def fallback_review_decision(row: dict[str, Any], reason: str) -> dict[str, Any]:
    groups = []
    for sid in sentence_ids(row):
        groups.append(
            {
                "sentence_ids": [sid],
                "unit_type": "needs_review",
                "knowledge_hint_en": "API output unavailable or malformed",
                "reason": reason[:240],
                "risk_flags": ["llm_api_output_unusable"],
            }
        )
    return {
        "request_id": row.get("request_id"),
        "sentence_groups": groups,
        "window_risk_flags": ["llm_api_output_unusable"],
    }


def normalize_decision(parsed: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    decision = dict(parsed)
    decision["request_id"] = str(decision.get("request_id") or row.get("request_id"))
    groups = decision.get("sentence_groups")
    if not isinstance(groups, list):
        raise ValueError("missing sentence_groups list")
    normalized_groups = []
    for group in groups:
        if not isinstance(group, dict):
            raise ValueError("sentence_group is not an object")
        sids = [str(sid) for sid in group.get("sentence_ids", []) if sid]
        unit_type = str(group.get("unit_type") or "needs_review")
        if unit_type not in ALLOWED_UNIT_TYPES:
            unit_type = "needs_review"
        normalized_groups.append(
            {
                "sentence_ids": sids,
                "unit_type": unit_type,
                "knowledge_hint_en": str(group.get("knowledge_hint_en") or "").strip(),
                "reason": str(group.get("reason") or "").strip(),
                "risk_flags": [str(flag) for flag in group.get("risk_flags", []) if flag],
            }
        )
    decision["sentence_groups"] = normalized_groups
    decision["window_risk_flags"] = [
        str(flag) for flag in decision.get("window_risk_flags", []) if flag
    ]
    return decision


def call_model(
    client: Any,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> tuple[str, dict[str, Any]]:
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    raw = (resp.choices[0].message.content or "").strip()
    usage = getattr(resp, "usage", None)
    usage_payload = usage.model_dump() if hasattr(usage, "model_dump") else {}
    return raw, usage_payload


def build_request_manifest(
    rows: list[dict[str, Any]],
    prompt_text: str,
    prompt_file: Path,
    provider: str,
    model: str,
    base_url: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
) -> dict[str, Any]:
    prompt_sha = sha256_text(prompt_text)
    request_rows = []
    for row in rows:
        input_sha = sha256_text(canonical_json(row))
        message_sha = sha256_text(canonical_json(build_messages(prompt_text, row)))
        request_rows.append(
            {
                "request_id": row.get("request_id"),
                "block_id": row.get("block_id"),
                "input_sha256": input_sha,
                "message_sha256": message_sha,
                "sentence_ids": sentence_ids(row),
            }
        )
    return {
        "schema_version": "v7_unit_grouping_decision_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "request_manifest",
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "json_mode": json_mode,
        "prompt_file": str(prompt_file),
        "prompt_sha256": prompt_sha,
        "batch_sha256": sha256_text("\n".join(canonical_json(row) for row in rows)),
        "request_count": len(rows),
        "requests": request_rows,
    }


def run(args: argparse.Namespace) -> None:
    batch_file = args.batch_file.resolve()
    prompt_file = args.prompt_file.resolve()
    rows = read_jsonl(batch_file)
    prompt_text = prompt_file.read_text(encoding="utf-8")
    api_key = ""
    base_url = args.base_url or DEFAULT_BASE_URL
    key_source = ""
    if not args.dry_run:
        api_key, base_url, key_source = get_deepseek_config()

    run_dir = args.run_dir.resolve() if args.run_dir else BASE_UNITS_DIR / "llm_runs" / args.run_slug
    raw_dir = run_dir / "raw_responses"
    manifest_path = run_dir / "run_manifest.json"
    decisions_file = args.decisions_file.resolve()

    manifest = build_request_manifest(
        rows,
        prompt_text,
        prompt_file,
        provider="deepseek",
        model=args.model,
        base_url=base_url,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        json_mode=args.json_mode,
    )
    manifest.update(
        {
            "run_slug": args.run_slug,
            "batch_file": str(batch_file),
            "decisions_file": str(decisions_file),
            "raw_response_dir": str(raw_dir),
            "api_key_env": key_source or None,
            "timeout_seconds": args.timeout_seconds,
        }
    )

    if args.dry_run:
        manifest["status"] = "dry_run_no_api_calls"
        write_json(manifest_path, manifest)
        print(f"dry run request manifest: {manifest_path}")
        return

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=args.timeout_seconds)
    decisions: list[dict[str, Any]] = []
    request_results = []
    raw_dir.mkdir(parents=True, exist_ok=True)
    prompt_sha = manifest["prompt_sha256"]

    for index, row in enumerate(rows, start=1):
        request_id = str(row.get("request_id"))
        input_sha = sha256_text(canonical_json(row))
        messages = build_messages(prompt_text, row)
        message_sha = sha256_text(canonical_json(messages))
        raw = ""
        usage: dict[str, Any] = {}
        status = "passed"
        error = ""
        parsed: dict[str, Any] | None = None
        for attempt in range(1, args.retries + 1):
            try:
                raw, usage = call_model(
                    client,
                    args.model,
                    messages,
                    args.temperature,
                    args.max_tokens,
                    args.json_mode,
                )
                parsed = extract_json_object(raw)
                if parsed is None or not isinstance(parsed.get("sentence_groups"), list):
                    error = "model response is not a valid decision JSON object"
                    if attempt < args.retries:
                        time.sleep(args.retry_sleep * attempt)
                        continue
                break
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
                if attempt < args.retries:
                    time.sleep(args.retry_sleep * attempt)
        raw_path = raw_dir / f"{index:04d}_{re.sub(r'[^A-Za-z0-9_.-]+', '_', request_id)}.txt"
        raw_path.write_text(raw, encoding="utf-8")
        if not raw or parsed is None:
            status = "malformed"
            decision = fallback_review_decision(row, error or "model response is not valid JSON object")
        else:
            try:
                decision = normalize_decision(parsed, row)
            except Exception as exc:  # noqa: BLE001
                status = "malformed"
                error = str(exc)
                decision = fallback_review_decision(row, error)
        decision["_meta"] = {
            "schema_version": "v7_unit_grouping_decision_meta_v1",
            "provider": "deepseek",
            "model": args.model,
            "base_url": base_url,
            "temperature": args.temperature,
            "max_tokens": args.max_tokens,
            "json_mode": args.json_mode,
            "timeout_seconds": args.timeout_seconds,
            "prompt_file": str(prompt_file),
            "prompt_sha256": prompt_sha,
            "input_sha256": input_sha,
            "message_sha256": message_sha,
            "raw_response_sha256": sha256_text(raw),
            "raw_response_path": str(raw_path),
            "status": status,
            "usage": usage,
            "error": error[:500] if error else "",
        }
        decisions.append(decision)
        request_results.append(
            {
                "request_id": request_id,
                "input_sha256": input_sha,
                "message_sha256": message_sha,
                "raw_response_sha256": sha256_text(raw),
                "raw_response_path": str(raw_path),
                "status": status,
                "usage": usage,
                "error": error[:500] if error else "",
            }
        )
        print(f"{index}/{len(rows)} {request_id} {status}", flush=True)

    write_jsonl(decisions_file, decisions)
    manifest["status"] = "completed"
    manifest["completed_at"] = datetime.now().isoformat(timespec="seconds")
    manifest["results"] = request_results
    manifest["status_counts"] = {
        status: sum(1 for item in request_results if item["status"] == status)
        for status in sorted({item["status"] for item in request_results})
    }
    write_json(manifest_path, manifest)
    print(f"decisions: {decisions_file}", flush=True)
    print(f"manifest: {manifest_path}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DeepSeek v7 unit grouping for one batch slice.")
    parser.add_argument("--batch-file", required=True, type=Path)
    parser.add_argument("--decisions-file", required=True, type=Path)
    parser.add_argument("--run-slug", required=True)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--model", default=os.environ.get("DS_UNIT_MODEL", "deepseek-chat"))
    parser.add_argument("--base-url", default=os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL"))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--retry-sleep", type=float, default=2.0)
    parser.add_argument("--json-mode", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
