from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
V7_DIR = MODULE_DIR.parent
BASE_UNITS_DIR = V7_DIR / "work" / "base_units"
DEFAULT_PROMPT = MODULE_DIR / "prompts" / "v7_unit_zh_enrichment_v1.md"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
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
        "payload": row.get("payload"),
    }
    return [
        {"role": "system", "content": prompt_text},
        {
            "role": "user",
            "content": "Generate zh enrichment. Return one JSON object only.\n\n"
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


def normalize_decision(parsed: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    expected_ids = [str(unit_id) for unit_id in row.get("unit_ids", [])]
    expected_set = set(expected_ids)
    units = parsed.get("units")
    if not isinstance(units, list):
        raise ValueError("missing units list")
    normalized_units = []
    seen: set[str] = set()
    for unit in units:
        if not isinstance(unit, dict):
            raise ValueError("unit item is not an object")
        tmp_unit_id = str(unit.get("tmp_unit_id") or "")
        if tmp_unit_id not in expected_set:
            raise ValueError(f"unexpected tmp_unit_id: {tmp_unit_id}")
        if tmp_unit_id in seen:
            raise ValueError(f"duplicate tmp_unit_id: {tmp_unit_id}")
        seen.add(tmp_unit_id)
        terms = []
        raw_terms = unit.get("terms") or []
        if not isinstance(raw_terms, list):
            raw_terms = []
        for term in raw_terms[:5]:
            if not isinstance(term, dict):
                continue
            en = str(term.get("en") or "").strip()
            zh = str(term.get("zh") or "").strip()
            if en and zh:
                terms.append({"en": en, "zh": zh, "source": "llm"})
        normalized_units.append(
            {
                "tmp_unit_id": tmp_unit_id,
                "knowledge_zh": str(unit.get("knowledge_zh") or "").strip(),
                "terms": terms,
                "notes": str(unit.get("notes") or "").strip(),
            }
        )
    missing = [unit_id for unit_id in expected_ids if unit_id not in seen]
    if missing:
        raise ValueError(f"missing unit ids: {', '.join(missing[:5])}")
    by_id = {unit["tmp_unit_id"]: unit for unit in normalized_units}
    return {
        "request_id": str(parsed.get("request_id") or row.get("request_id")),
        "units": [by_id[unit_id] for unit_id in expected_ids],
    }


def fallback_decision(row: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "request_id": row.get("request_id"),
        "units": [
            {
                "tmp_unit_id": unit_id,
                "knowledge_zh": "",
                "terms": [],
                "notes": f"zh enrichment failed: {reason[:180]}",
            }
            for unit_id in row.get("unit_ids", [])
        ],
    }


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


def build_manifest(
    rows: list[dict[str, Any]],
    prompt_text: str,
    prompt_file: Path,
    model: str,
    base_url: str,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
    concurrency: int,
) -> dict[str, Any]:
    prompt_sha = sha256_text(prompt_text)
    requests = []
    for row in rows:
        messages = build_messages(prompt_text, row)
        requests.append(
            {
                "request_id": row.get("request_id"),
                "unit_count": row.get("unit_count"),
                "unit_ids": row.get("unit_ids", []),
                "input_sha256": sha256_text(canonical_json(row)),
                "message_sha256": sha256_text(canonical_json(messages)),
            }
        )
    return {
        "schema_version": "v7_zh_enrichment_decision_manifest_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "request_manifest",
        "provider": "deepseek",
        "model": model,
        "base_url": base_url,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "json_mode": json_mode,
        "concurrency": concurrency,
        "prompt_file": str(prompt_file),
        "prompt_sha256": prompt_sha,
        "batch_sha256": sha256_text("\n".join(canonical_json(row) for row in rows)),
        "request_count": len(rows),
        "requests": requests,
    }


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)[:140]


def run_one(
    *,
    index: int,
    total: int,
    row: dict[str, Any],
    client: Any,
    args: argparse.Namespace,
    prompt_text: str,
    prompt_file: Path,
    prompt_sha: str,
    base_url: str,
    raw_dir: Path,
) -> tuple[int, dict[str, Any], dict[str, Any]]:
    request_id = str(row.get("request_id"))
    messages = build_messages(prompt_text, row)
    input_sha = sha256_text(canonical_json(row))
    message_sha = sha256_text(canonical_json(messages))
    raw = ""
    usage: dict[str, Any] = {}
    parsed: dict[str, Any] | None = None
    decision: dict[str, Any] | None = None
    status = "passed"
    error = ""
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
            if parsed is None:
                error = "model response is not valid JSON"
                if attempt < args.retries:
                    time.sleep(args.retry_sleep * attempt)
                    continue
            try:
                decision = normalize_decision(parsed, row)
                break
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
                decision = None
                if attempt < args.retries:
                    time.sleep(args.retry_sleep * attempt)
                    continue
                break
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
            if attempt < args.retries:
                time.sleep(args.retry_sleep * attempt)
    raw_path = raw_dir / f"{index:04d}_{safe_name(request_id)}.txt"
    raw_path.write_text(raw, encoding="utf-8")
    if not raw or parsed is None or decision is None:
        status = "malformed"
        decision = fallback_decision(row, error or "empty model response")

    meta = {
        "schema_version": "v7_zh_enrichment_decision_meta_v1",
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
    decision["_meta"] = meta
    result = {
        "request_id": request_id,
        "index": index,
        "total": total,
        "unit_count": row.get("unit_count"),
        "input_sha256": input_sha,
        "message_sha256": message_sha,
        "raw_response_sha256": sha256_text(raw),
        "raw_response_path": str(raw_path),
        "status": status,
        "usage": usage,
        "error": error[:500] if error else "",
    }
    return index, decision, result


def run(args: argparse.Namespace) -> None:
    batch_file = args.batch_file.resolve()
    prompt_file = args.prompt_file.resolve()
    rows = read_jsonl(batch_file)
    if args.limit:
        rows = rows[: args.limit]
    prompt_text = prompt_file.read_text(encoding="utf-8")
    base_url = args.base_url or DEFAULT_BASE_URL
    key_source = ""
    api_key = ""
    if not args.dry_run:
        api_key, base_url, key_source = get_deepseek_config()

    run_dir = args.run_dir.resolve() if args.run_dir else BASE_UNITS_DIR / "llm_runs" / args.run_slug
    raw_dir = run_dir / "raw_responses"
    manifest_path = run_dir / "run_manifest.json"
    decisions_file = args.decisions_file.resolve()
    manifest = build_manifest(
        rows,
        prompt_text,
        prompt_file,
        args.model,
        base_url,
        args.temperature,
        args.max_tokens,
        args.json_mode,
        args.concurrency,
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
    raw_dir.mkdir(parents=True, exist_ok=True)
    prompt_sha = manifest["prompt_sha256"]
    decisions_by_index: dict[int, dict[str, Any]] = {}
    results_by_index: dict[int, dict[str, Any]] = {}

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [
            executor.submit(
                run_one,
                index=index,
                total=len(rows),
                row=row,
                client=client,
                args=args,
                prompt_text=prompt_text,
                prompt_file=prompt_file,
                prompt_sha=prompt_sha,
                base_url=base_url,
                raw_dir=raw_dir,
            )
            for index, row in enumerate(rows, start=1)
        ]
        for future in as_completed(futures):
            index, decision, result = future.result()
            decisions_by_index[index] = decision
            results_by_index[index] = result
            print(f"{index}/{len(rows)} {result['request_id']} {result['status']}", flush=True)

    decisions = [decisions_by_index[index] for index in sorted(decisions_by_index)]
    results = [results_by_index[index] for index in sorted(results_by_index)]
    write_jsonl(decisions_file, decisions)
    manifest["status"] = "completed"
    manifest["completed_at"] = datetime.now().isoformat(timespec="seconds")
    manifest["results"] = results
    manifest["status_counts"] = {
        status: sum(1 for item in results if item["status"] == status)
        for status in sorted({item["status"] for item in results})
    }
    write_json(manifest_path, manifest)
    print(f"decisions: {decisions_file}", flush=True)
    print(f"manifest: {manifest_path}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DeepSeek Chinese enrichment for v7 units.")
    parser.add_argument("--batch-file", required=True, type=Path)
    parser.add_argument("--decisions-file", required=True, type=Path)
    parser.add_argument("--run-slug", required=True)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--prompt-file", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--model", default=os.environ.get("DS_ZH_MODEL", "deepseek-chat"))
    parser.add_argument("--base-url", default=os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL"))
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=16384)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--retry-sleep", type=float, default=2.0)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--json-mode", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
