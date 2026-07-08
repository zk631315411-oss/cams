from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "work" / "preview_v8_naming_sample"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-v4-pro"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else HERE / path


def batch_name() -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "", os.getenv("PREVIEW_V8_BATCH_NAME", "").strip())


def out_name(stem: str, suffix: str, name: str | None = None) -> str:
    value = batch_name() if name is None else re.sub(r"[^A-Za-z0-9_-]+", "", name.strip())
    return f"{stem}_{value}.{suffix}" if value else f"{stem}.{suffix}"


def get_deepseek_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_BASE_URL
            return value, base_url, env_name
    names = " / ".join(API_KEY_ENV_NAMES)
    raise RuntimeError(f"{names} environment variables are not set.")


def extract_json_object(text: str) -> dict[str, Any]:
    content = text.strip()
    if "```" in content:
        blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)```", content, flags=re.IGNORECASE)
        if blocks:
            content = blocks[0].strip()
    if not content.startswith("{"):
        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            content = match.group(0)
    return json.loads(content)


def task_payload(input_payload: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": input_payload.get("schema_version"),
        "source_exam_point_system": input_payload.get("source_exam_point_system"),
        "source_edges": input_payload.get("source_edges"),
        "source_relation_records": input_payload.get("source_relation_records"),
        "selection_policy": {"single_task": True},
        "tasks": [task],
    }


def build_user_content(prompt: str, input_payload: dict[str, Any], task: dict[str, Any], retry_note: str = "") -> str:
    single = task_payload(input_payload, task)
    retry_block = f"\n\n# 上次输出问题\n{retry_note}\n请修正后重新输出完整 JSON。\n" if retry_note else ""
    return (
        prompt
        + "\n\n# 本次只处理下面 1 个 task\n"
        + "请输出同一 schema 的 JSON 对象，records 数组里只能有这一条考点记录。"
        + "不要输出 Markdown，不要解释过程。\n"
        + "为避免 JSON 截断，请保持极简：title 6-16字；teaching_focus 35字以内；"
        + "relation_summary 一句话；card_roles 最多 5 条；question_roles 最多 5 条；"
        + "每个 reason 20字以内。\n"
        + retry_block
        + "\n"
        + json.dumps(single, ensure_ascii=False, indent=2)
    )


def validate_record(record: dict[str, Any], expected_id: str) -> list[str]:
    required = {
        "exam_point_id",
        "title",
        "teaching_focus",
        "relation_summary",
        "card_roles",
        "question_roles",
        "split_recommendation",
        "risk_flags",
        "confidence",
    }
    errors = []
    missing = required - set(record)
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")
    if record.get("exam_point_id") != expected_id:
        errors.append(f"exam_point_id mismatch: expected {expected_id}, got {record.get('exam_point_id')}")
    if record.get("confidence") not in {"high", "medium", "low"}:
        errors.append(f"invalid confidence: {record.get('confidence')}")
    if not str(record.get("teaching_focus") or "").startswith("考查学生能否"):
        errors.append("teaching_focus must start with 考查学生能否")
    flags = record.get("risk_flags")
    if not isinstance(flags, list) or not flags:
        errors.append("risk_flags must be a non-empty list")
    return errors


def call_deepseek(client: Any, model: str, user_content: str, max_tokens: int, retries: int) -> tuple[str, Any]:
    messages = [{"role": "user", "content": user_content}]
    extra_body = {"thinking": {"type": "disabled"}} if model.lower().startswith("deepseek") else None
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": 0.0,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }
            if extra_body:
                kwargs["extra_body"] = extra_body
            try:
                resp = client.chat.completions.create(**kwargs)
            except TypeError:
                kwargs.pop("response_format", None)
                resp = client.chat.completions.create(**kwargs)
            except Exception as exc:
                message = str(exc).lower()
                if "response_format" in message:
                    kwargs.pop("response_format", None)
                    resp = client.chat.completions.create(**kwargs)
                elif "thinking" in message or "extra_body" in message:
                    kwargs.pop("extra_body", None)
                    resp = client.chat.completions.create(**kwargs)
                else:
                    raise
            content = (resp.choices[0].message.content or "").strip()
            if not content:
                raise RuntimeError("empty response")
            return content, getattr(resp, "usage", None)
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(8, 1.5 * attempt))
    raise RuntimeError(str(last_error))


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_path = resolve_path(args.input_file) if args.input_file else OUT_DIR / out_name("agent_naming_input", "json", args.batch_name)
    prompt_path = resolve_path(args.prompt_file) if args.prompt_file else OUT_DIR / "agent_prompt.md"
    output_path = resolve_path(args.output_file) if args.output_file else OUT_DIR / out_name("agent_naming_output", "json", args.batch_name)
    raw_dir = resolve_path(args.raw_dir) if args.raw_dir else OUT_DIR / f"ds_raw_{args.batch_name or batch_name() or 'default'}"

    input_payload = read_json(input_path)
    prompt = prompt_path.read_text(encoding="utf-8")
    tasks = input_payload.get("tasks", [])
    if args.limit:
        tasks = tasks[: args.limit]

    api_key, base_url, key_source = get_deepseek_config()
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    raw_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    run_records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    total_usage = CounterDict()

    for idx, task in enumerate(tasks, start=1):
        ep_id = task["exam_point_id"]
        started = time.time()
        raw_content = ""
        try:
            retry_note = ""
            usage_dict: dict[str, Any] = {}
            record: dict[str, Any] | None = None
            user_content = ""
            for parse_attempt in range(1, args.parse_retries + 1):
                user_content = build_user_content(prompt, input_payload, task, retry_note=retry_note)
                raw_content, usage = call_deepseek(client, args.model, user_content, args.max_tokens, args.retries)
                try:
                    parsed = extract_json_object(raw_content)
                    task_records = parsed.get("records", [])
                    if len(task_records) != 1:
                        raise RuntimeError(f"expected 1 record, got {len(task_records)}")
                    candidate = task_records[0]
                    errors = validate_record(candidate, ep_id)
                    if errors:
                        raise RuntimeError("; ".join(errors))
                    record = candidate
                    usage_dict = usage.model_dump() if hasattr(usage, "model_dump") else dict(usage or {})
                    break
                except Exception as parse_exc:
                    retry_note = f"{type(parse_exc).__name__}: {str(parse_exc)[:220]}"
                    if parse_attempt >= args.parse_retries:
                        raise
            if record is None:
                raise RuntimeError("no valid record generated")
            records.append(record)
            elapsed = round(time.time() - started, 2)
            total_usage.add_usage(usage_dict)
            run_records.append(
                {
                    "exam_point_id": ep_id,
                    "status": "ok",
                    "elapsed_seconds": elapsed,
                    "usage": usage_dict,
                    "input_chars": len(user_content),
                    "output_chars": len(raw_content),
                }
            )
            print(f"[{idx}/{len(tasks)}] OK {ep_id} {elapsed}s")
        except Exception as exc:
            elapsed = round(time.time() - started, 2)
            failures.append(
                {
                    "exam_point_id": ep_id,
                    "status": "failed",
                    "elapsed_seconds": elapsed,
                    "error": str(exc),
                    "input_chars": len(user_content),
                    "raw_output_chars": len(raw_content),
                }
            )
            print(f"[{idx}/{len(tasks)}] FAIL {ep_id}: {exc}")
        finally:
            if raw_content:
                (raw_dir / f"{idx:03d}_{ep_id}.txt").write_text(raw_content, encoding="utf-8")
            checkpoint = {
                "schema_version": "preview_v8_agent_naming_output_v1",
                "agent": "deepseek",
                "model": args.model,
                "source_input": str(input_path),
                "records": records,
            }
            write_json(output_path, checkpoint)

    output = {
        "schema_version": "preview_v8_agent_naming_output_v1",
        "agent": "deepseek",
        "model": args.model,
        "base_url": base_url,
        "key_source": key_source,
        "source_input": str(input_path),
        "prompt_file": str(prompt_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "records": records,
    }
    write_json(output_path, output)

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "ok" if not failures else "partial",
        "model": args.model,
        "input_file": str(input_path),
        "output_file": str(output_path),
        "raw_dir": str(raw_dir),
        "task_count": len(tasks),
        "success_count": len(records),
        "failure_count": len(failures),
        "failures": failures,
        "run_records": run_records,
        "total_usage": total_usage.data,
    }
    write_json(OUT_DIR / out_name("ds_executor_summary", "json", args.batch_name), summary)
    return summary


class CounterDict:
    def __init__(self) -> None:
        self.data: dict[str, int] = {}

    def add_usage(self, usage: dict[str, Any]) -> None:
        for key, value in usage.items():
            if isinstance(value, int):
                self.data[key] = self.data.get(key, 0) + value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DeepSeek naming for preview_v8 agent input.")
    parser.add_argument("--batch-name", default=batch_name(), help="Batch suffix, e.g. v10_probe20.")
    parser.add_argument("--input-file", default="", help="Input JSON path. Defaults to v8 batch input.")
    parser.add_argument("--prompt-file", default="", help="Prompt markdown path. Defaults to agent_prompt.md.")
    parser.add_argument("--output-file", default="", help="Output JSON path. Defaults to v8 batch output.")
    parser.add_argument("--raw-dir", default="", help="Directory for raw model outputs.")
    parser.add_argument("--model", default=os.getenv("DS_MODEL") or DEFAULT_MODEL)
    parser.add_argument("--max-tokens", type=int, default=int(os.getenv("PREVIEW_V11_MAX_TOKENS", "5000")))
    parser.add_argument("--retries", type=int, default=int(os.getenv("PREVIEW_V11_RETRIES", "3")))
    parser.add_argument("--parse-retries", type=int, default=int(os.getenv("PREVIEW_V11_PARSE_RETRIES", "2")))
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    summary = run(parse_args())
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
