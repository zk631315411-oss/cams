from __future__ import annotations

import argparse
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
TEST_DIR = SCRIPT_DIR.parent
DEFAULT_CANDIDATES = TEST_DIR / "outputs" / "p5c_alias_candidate_groups.json"
DEFAULT_PROMPT = TEST_DIR / "prompts" / "p5c_alias_group_review_v1.md"
DEFAULT_OUTPUT = TEST_DIR / "outputs" / "p5c_alias_group_reviews.jsonl"
DEFAULT_PREVIEW = TEST_DIR / "previews" / "p5c_alias_group_reviews.md"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + ("\n" if rows else ""), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def get_deepseek_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_BASE_URL
            return value, base_url, env_name
    raise RuntimeError("DEEPSEEK_API_KEY / DS_API_KEY / DS_KEY is not set.")


def extract_json_object(raw: str) -> dict[str, Any] | None:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{[\s\S]*\}", text)
    candidates = [text]
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


def chunks(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def call_model(client: Any, model: str, prompt: str, batch: list[dict[str, Any]], temperature: float, max_tokens: int) -> dict[str, Any]:
    user_payload = json.dumps({"candidate_groups": batch}, ensure_ascii=False, indent=2)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_payload},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    raw = response.choices[0].message.content or ""
    parsed = extract_json_object(raw)
    return {"raw_response": raw, "parsed_response": parsed}


def preview(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# P5C alias group review preview",
        "",
        f"- rows: {len(rows)}",
        "",
        "| group | decision | type | canonical_en | canonical_zh | confidence |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows[:120]:
        review = row.get("review") or {}
        lines.append(
            f"| {row.get('candidate_group_id')} | {review.get('decision', '')} | {review.get('merge_type', '')} | {review.get('canonical_en', '')} | {review.get('canonical_zh', '')} | {review.get('confidence', '')} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run P5C alias group sub-agent review with DeepSeek.")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    payload = read_json(args.candidates)
    groups = payload.get("candidate_groups") or []
    if args.limit > 0:
        groups = groups[: args.limit]
    prompt = args.prompt.read_text(encoding="utf-8")

    if args.dry_run:
        print(json.dumps({"candidate_group_count": len(groups), "batch_size": args.batch_size, "batches": len(chunks(groups, args.batch_size))}, ensure_ascii=False, indent=2))
        return

    from openai import OpenAI

    api_key, base_url, key_source = get_deepseek_config()
    client = OpenAI(api_key=api_key, base_url=base_url)
    started_at = datetime.now().isoformat(timespec="seconds")
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_batch = {
            executor.submit(call_model, client, args.model, prompt, batch, args.temperature, args.max_tokens): batch
            for batch in chunks(groups, args.batch_size)
        }
        for future in as_completed(future_to_batch):
            batch = future_to_batch[future]
            result = future.result()
            parsed = result.get("parsed_response") or {}
            reviews = parsed.get("reviews") if isinstance(parsed, dict) else None
            review_by_id = {review.get("candidate_group_id"): review for review in reviews or [] if isinstance(review, dict)}
            for group in batch:
                rows.append(
                    {
                        "candidate_group_id": group.get("candidate_group_id"),
                        "source_types": group.get("source_types"),
                        "review": review_by_id.get(group.get("candidate_group_id")),
                        "raw_response": result.get("raw_response"),
                        "run_meta": {
                            "model": args.model,
                            "key_source": key_source,
                            "started_at": started_at,
                        },
                    }
                )
    rows.sort(key=lambda row: row.get("candidate_group_id") or "")
    write_jsonl(args.output, rows)
    write_text(args.preview, preview(rows))
    print(json.dumps({"review_count": len(rows), "output": str(args.output)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

