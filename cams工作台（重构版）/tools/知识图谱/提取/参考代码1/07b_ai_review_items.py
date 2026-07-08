"""
v4.4 Step 7B: AI review recommendations for unified review items.

This step reviews every Step 7A item and writes advisory decisions only. It
does not apply decisions or modify graph candidates.
"""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from review_pipeline_utils import (
    VALID_ACTIONS,
    VALID_TARGET_LAYERS,
    call_llm,
    load_env_value,
    now_iso,
    read_jsonl,
    stable_id,
    write_jsonl,
)


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PROMPT = SCRIPT_DIR / "prompts" / "review_items_audit.md"
DEFAULT_OUT_DIR = SCRIPT_DIR / "中间产物" / "step7_review"
DEFAULT_REVIEW_ITEMS = DEFAULT_OUT_DIR / "review_items.jsonl"
DEFAULT_MODEL = "gpt-5.5"
DEFAULT_BASE_URL = load_env_value("LLM_API_BASE") or "https://api.openai.com/v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate v4.4 Step 7B AI review decisions.")
    parser.add_argument("--review-items", type=Path, default=DEFAULT_REVIEW_ITEMS)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--append", action="store_true")
    parser.add_argument("--max-budget-usd", type=float, default=200.0)
    return parser.parse_args()


def coerce_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def compact_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_item_id": item.get("review_item_id", ""),
        "item_kind": item.get("item_kind", ""),
        "item_id": item.get("item_id", ""),
        "item_name": item.get("item_name", ""),
        "item_type": item.get("item_type", ""),
        "kg_layer": item.get("kg_layer", ""),
        "context": item.get("context", {}),
        "allowed_actions": item.get("allowed_actions", []),
        "default_action": item.get("default_action", "defer"),
        "default_target_layer": item.get("default_target_layer", "review_pending"),
        "risk_flags": item.get("risk_flags", []),
    }


def normalize_action(action: Any, item: dict[str, Any]) -> str:
    text = str(action or "").strip()
    allowed = set(item.get("allowed_actions") or [])
    if text in VALID_ACTIONS and text in allowed:
        return text
    return str(item.get("default_action") or "defer")


def normalize_target_layer(value: Any, action: str, item: dict[str, Any]) -> str:
    text = str(value or "").strip()
    if action in {"reject", "reject_merge"}:
        return "rejected_archive"
    if action in {"defer"}:
        return "review_pending"
    if action == "accept_merge":
        return "review_pending"
    if text in VALID_TARGET_LAYERS:
        return text
    return str(item.get("default_target_layer") or "review_pending")


def default_decision(item: dict[str, Any], action: str, reason: str, confidence: float = 0.0) -> dict[str, Any]:
    target_layer = normalize_target_layer("", action, item)
    return {
        "decision_id": stable_id("step7b", [item.get("review_item_id", ""), action]),
        "review_item_id": item.get("review_item_id", ""),
        "item_kind": item.get("item_kind", ""),
        "item_id": item.get("item_id", ""),
        "item_name": item.get("item_name", ""),
        "item_type": item.get("item_type", ""),
        "action": action,
        "target_layer": target_layer,
        "rewritten_item": None,
        "reason": reason,
        "confidence": confidence,
        "source_review_item": item,
        "generated_at": now_iso(),
    }


def mock_decision(item: dict[str, Any]) -> dict[str, Any]:
    kind = item.get("item_kind")
    flags = item.get("risk_flags") or []
    if kind == "merge_candidate":
        return default_decision(item, "defer", "Mock: semantic merge requires explicit review.", 0.5)
    if kind == "rule_case" and not flags:
        return default_decision(item, "accept", "Mock: complete rule case accepted.", 0.75)
    return default_decision(item, "defer", "Mock: review item deferred for human/AI validation.", 0.5)


def normalize_decisions(raw: dict[str, Any], items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    item_by_id = {str(item.get("review_item_id") or ""): item for item in items}
    warnings: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    seen: set[str] = set()
    raw_decisions = raw.get("decisions") if isinstance(raw.get("decisions"), list) else []
    for index, raw_decision in enumerate(raw_decisions, start=1):
        if not isinstance(raw_decision, dict):
            warnings.append({"warning": "decision_not_object", "index": index})
            continue
        review_item_id = str(raw_decision.get("review_item_id") or "")
        item = item_by_id.get(review_item_id)
        if not item:
            warnings.append({"warning": "decision_item_not_in_batch", "index": index, "review_item_id": review_item_id})
            continue
        if review_item_id in seen:
            warnings.append({"warning": "duplicate_decision", "index": index, "review_item_id": review_item_id})
            continue
        seen.add(review_item_id)
        action = normalize_action(raw_decision.get("action"), item)
        decisions.append(
            {
                "decision_id": stable_id("step7b", [review_item_id, action, str(raw_decision.get("reason") or "")]),
                "review_item_id": review_item_id,
                "item_kind": item.get("item_kind", ""),
                "item_id": item.get("item_id", ""),
                "item_name": item.get("item_name", ""),
                "item_type": item.get("item_type", ""),
                "action": action,
                "target_layer": normalize_target_layer(raw_decision.get("target_layer"), action, item),
                "rewritten_item": raw_decision.get("rewritten_item") if isinstance(raw_decision.get("rewritten_item"), dict) else None,
                "reason": str(raw_decision.get("reason") or "").strip(),
                "confidence": coerce_confidence(raw_decision.get("confidence", 0.0)),
                "source_review_item": item,
                "generated_at": now_iso(),
            }
        )
    for item in items:
        review_item_id = str(item.get("review_item_id") or "")
        if review_item_id not in seen:
            decisions.append(default_decision(item, "defer", "AI 未返回该审核项，保守暂缓。", 0.0))
            warnings.append({"warning": "missing_decision", "review_item_id": review_item_id})
    return decisions, warnings


def batched(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    size = max(1, size)
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids: set[str] = set()
    for row in read_jsonl(path, required=False):
        review_item_id = str(row.get("review_item_id") or "")
        if review_item_id:
            ids.add(review_item_id)
    return ids


def process_batch(batch: list[dict[str, Any]], prompt: str, args: argparse.Namespace, api_key: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if args.mock:
        decisions = [mock_decision(item) for item in batch]
        return decisions, [], {"mode": "mock", "count": len(batch)}
    payload = {
        "model_policy": {
            "model": args.model,
            "max_budget_usd": args.max_budget_usd,
            "note": "Step 7B outputs recommendations only; no graph mutation.",
        },
        "review_items": [compact_item(item) for item in batch],
    }
    raw = call_llm(api_key, args.base_url, args.model, prompt, payload, args.temperature, args.timeout)
    decisions, warnings = normalize_decisions(raw, batch)
    return decisions, warnings, {"mode": "llm", "count": len(batch), "raw": raw}


def fallback_decisions_for_failed_batch(batch: list[dict[str, Any]], error: Exception) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    message = str(error)[:1000]
    decisions = [
        default_decision(
            item,
            "defer",
            f"Step 7B AI审核调用失败，按保守策略暂缓：{message}",
            0.0,
        )
        for item in batch
    ]
    warnings = [
        {
            "warning": "batch_failed_deferred",
            "review_item_id": item.get("review_item_id", ""),
            "error": message,
        }
        for item in batch
    ]
    return decisions, warnings, {"mode": "fallback_defer", "count": len(batch), "error": message}


def write_report(path: Path, decisions: list[dict[str, Any]], warnings: list[dict[str, Any]], args: argparse.Namespace) -> None:
    counts: dict[str, int] = {}
    for decision in decisions:
        key = f"{decision.get('item_kind')}:{decision.get('action')}"
        counts[key] = counts.get(key, 0) + 1
    lines = [
        "# v4.4 Step 7B AI Review Report",
        "",
        f"- model: {args.model}",
        f"- mock: {args.mock}",
        f"- decisions: {len(decisions)}",
        f"- warnings: {len(warnings)}",
        f"- max_budget_usd: {args.max_budget_usd}",
        "",
        "## Decision Counts",
    ]
    for key, value in sorted(counts.items()):
        lines.append(f"- {key}: {value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    decisions_path = out_dir / "ai_review_decisions.jsonl"
    warnings_path = out_dir / "ai_review_warnings.jsonl"
    raw_path = out_dir / "ai_review_raw.jsonl"

    items = read_jsonl(args.review_items, required=False)
    if args.limit > 0:
        items = items[: args.limit]
    if args.resume:
        done = completed_ids(decisions_path)
        items = [item for item in items if str(item.get("review_item_id") or "") not in done]
        append = True
    else:
        append = args.append
    if not append:
        for path in [decisions_path, warnings_path, raw_path]:
            if path.exists():
                path.unlink()

    prompt = args.prompt.read_text(encoding="utf-8")
    api_key = "" if args.mock else load_env_value(args.api_key_env)
    if not args.mock and not api_key:
        raise RuntimeError(f"{args.api_key_env} not found. Use --mock for local validation.")

    batches = batched(items, args.batch_size)
    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        future_to_batch = {executor.submit(process_batch, batch, prompt, args, api_key): batch for batch in batches}
        processed = 0
        failed = 0
        for future in as_completed(future_to_batch):
            batch = future_to_batch[future]
            try:
                decisions, warnings, raw = future.result()
            except Exception as exc:
                failed += len(batch)
                decisions, warnings, raw = fallback_decisions_for_failed_batch(batch, exc)
            processed += len(decisions)
            write_jsonl(decisions_path, decisions, append=True)
            write_jsonl(warnings_path, warnings, append=True)
            write_jsonl(raw_path, [raw], append=True)

    write_report(out_dir / "ai_review_report.md", read_jsonl(decisions_path, required=False), read_jsonl(warnings_path, required=False), args)
    print(f"[OK] decisions -> {decisions_path}")
    print(f"[OK] warnings -> {warnings_path}")
    print(f"[INFO] processed={processed} failed_deferred={failed}")


if __name__ == "__main__":
    main()
