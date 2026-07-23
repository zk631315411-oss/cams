from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
PHASE_DIR = SCRIPT_DIR.parent
P7E_DIR = PHASE_DIR / "phases" / "P7E"
DEFAULT_PROMPT_PATH = P7E_DIR / "prompts" / "bridge_review_v2.md"
DEFAULT_OUTPUT_DIR = P7E_DIR / "outputs"

API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def get_llm_config() -> tuple[str, str, str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = os.environ.get("DEEPSEEK_BASE_URL", "") or os.environ.get("DS_BASE_URL", "") or DEFAULT_BASE_URL
            return value, base_url, env_name
    raise RuntimeError(f"{' / '.join(API_KEY_ENV_NAMES)} not set.")


def call_model(prompt: str, model: str, max_tokens: int, timeout: float, thinking_effort: str) -> tuple[str, dict[str, Any]]:
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
    payload.update(extra_body)
    endpoint = base_url.rstrip("/") + "/chat/completions"
    started = time.time()
    try:
        import requests
        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=timeout,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
        response_payload = response.json()
    except ImportError:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=body,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                response_payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    elapsed = round(time.time() - started, 3)
    choices = response_payload.get("choices") or []
    if not choices:
        raise RuntimeError(f"No choices: {response_payload}")
    message = choices[0].get("message") or {}
    meta = {
        "model": model, "base_url": base_url, "api_key_env": env_name,
        "thinking_effort": thinking_effort, "elapsed_seconds": elapsed,
        "usage": response_payload.get("usage") or {},
    }
    return (message.get("content") or "").strip(), meta


def build_batch_prompt(template: str, source_card: dict[str, Any], target_card: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    """Build review prompt for all bridge candidates between one card pair."""
    cand_list: list[dict[str, Any]] = []
    for c in candidates:
        cand_list.append({
            "source_node_id": c.get("source_node_id"),
            "target_node_id": c.get("target_node_id"),
            "bridge_semantics": c.get("bridge_semantics"),
            "signals": c.get("bridge_basis", {}).get("signals", []),
            "score": c.get("score"),
        })
    payload = {
        "source_card": {
            "card_id": source_card.get("card_id"),
            "section_id": source_card.get("section_id"),
            "card_nature": source_card.get("card_nature"),
            "title": source_card.get("title"),
            "flow_nodes": source_card.get("flow_nodes"),
            "flow_edges": source_card.get("flow_edges"),
        },
        "target_card": {
            "card_id": target_card.get("card_id"),
            "section_id": target_card.get("section_id"),
            "card_nature": target_card.get("card_nature"),
            "title": target_card.get("title"),
            "flow_nodes": target_card.get("flow_nodes"),
            "flow_edges": target_card.get("flow_edges"),
        },
        "candidates": cand_list,
    }
    candidate_json = json.dumps(payload, ensure_ascii=False, indent=2)
    return template.replace("<CANDIDATE_JSON>", candidate_json)


def review_card_pair(
    pair_candidates: list[dict[str, Any]],
    source_card: dict[str, Any],
    target_card: dict[str, Any],
    prompt_template: str,
    model: str,
    max_tokens: int,
    timeout: float,
    thinking_effort: str,
    retries: int,
    retry_delay: float,
) -> list[dict[str, Any]]:
    """Review all bridge candidates between one card pair in a single LLM call."""
    results: list[dict[str, Any]] = []
    # Build placeholder results for error cases
    for c in pair_candidates:
        results.append({
            "bridge_id": c.get("bridge_id"),
            "source_card_id": c.get("source_card_id"),
            "target_card_id": c.get("target_card_id"),
            "source_node_id": c.get("source_node_id"),
            "target_node_id": c.get("target_node_id"),
            "bridge_semantics": c.get("bridge_semantics"),
            "review_status": "pending",
            "reason": "",
            "llm_error": None,
        })

    prompt = build_batch_prompt(prompt_template, source_card, target_card, pair_candidates)

    for attempt in range(1, retries + 1):
        try:
            raw, meta = call_model(prompt, model, max_tokens, timeout, thinking_effort)
            parsed = parse_json_object(raw)
            if isinstance(parsed, dict) and isinstance(parsed.get("results"), list):
                batch_results = parsed["results"]
                if len(batch_results) != len(results):
                    for r in results:
                        r["llm_error"] = f"Result count mismatch: got {len(batch_results)}, expected {len(results)}"
                    return results
                for i, br in enumerate(batch_results):
                    if isinstance(br, dict):
                        status = br.get("review_status", "")
                        if status in {"accepted", "rejected"}:
                            results[i]["review_status"] = status
                            results[i]["reason"] = br.get("reason", "")
                            results[i]["call_meta"] = meta
                        else:
                            results[i]["llm_error"] = f"Invalid review_status: {status}"
                    else:
                        results[i]["llm_error"] = "Non-dict result"
                return results
            else:
                for r in results:
                    r["llm_error"] = "Batch parse failed (no results array)"
                return results
        except Exception as exc:
            if attempt < retries:
                time.sleep(retry_delay)
    for r in results:
        r["llm_error"] = r["llm_error"] or "All retries exhausted"
    return results


def review_candidates(
    candidates: list[dict[str, Any]],
    cards_index: dict[str, dict[str, Any]],
    prompt_template: str,
    model: str,
    max_tokens: int,
    timeout: float,
    thinking_effort: str,
    retries: int,
    retry_delay: float,
    concurrency: int,
) -> list[dict[str, Any]]:
    """Group candidates by card pair, then review each pair in one LLM call."""
    # Group by (source_card_id, target_card_id)
    pairs: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for c in candidates:
        key = (c.get("source_card_id") or "", c.get("target_card_id") or "")
        pairs.setdefault(key, []).append(c)

    print(f"Grouped {len(candidates)} candidates into {len(pairs)} card pairs ({len(candidates)/len(pairs):.1f} avg)")

    all_results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
        futures = {}
        for (src_cid, tgt_cid), pair_cands in pairs.items():
            src_card = cards_index.get(src_cid, {})
            tgt_card = cards_index.get(tgt_cid, {})
            future = executor.submit(
                review_card_pair,
                pair_cands, src_card, tgt_card, prompt_template,
                model, max_tokens, timeout, thinking_effort,
                retries, retry_delay,
            )
            futures[future] = (src_cid, tgt_cid)
        for future in as_completed(futures):
            all_results.extend(future.result())

    all_results.sort(key=lambda r: (r.get("source_card_id") or "", r.get("target_card_id") or ""))
    return all_results


def load_cards_index(cards_dir: str) -> dict[str, dict[str, Any]]:
    """Load all cards from a directory tree into a flat card_id -> card dict."""
    cards_root = Path(cards_dir)
    index: dict[str, dict[str, Any]] = {}
    for cf in sorted(cards_root.rglob("cards.raw.json")):
        try:
            payload = read_json(cf)
        except Exception:
            continue
        for card in payload.get("cards") or []:
            cid = card.get("card_id")
            if cid:
                index[cid] = card
    return index


def main() -> None:
    parser = argparse.ArgumentParser(description="P7E LLM bridge candidate review.")
    parser.add_argument("--candidates", required=True, help="Path to p7e_bridge_candidates.jsonl")
    parser.add_argument("--cards-dir", required=True, help="Directory containing P7C cards.raw.json files (recursive)")
    parser.add_argument("--prompt", default=str(DEFAULT_PROMPT_PATH), help="Prompt template path")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--model", default="deepseek-v4-pro")
    parser.add_argument("--thinking-effort", default="none", choices=["none", "low", "medium", "high"])
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--max-tokens", type=int, default=8000)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--retry-delay", type=float, default=3.0)
    parser.add_argument("--limit", type=int, default=0, help="Limit candidates for testing (0=all)")
    parser.add_argument("--skip", type=int, default=0, help="Skip first N candidates (after filtering)")
    parser.add_argument("--min-score", type=int, default=0, help="Only review candidates with score >= N (0=all)")
    args = parser.parse_args()

    run_id = args.run_id or f"p7e_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = Path(args.output_dir) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    candidates = read_jsonl(Path(args.candidates))
    # Filter to pass candidates only
    candidates = [c for c in candidates if c.get("review_result") == "pass"]
    if args.min_score > 0:
        candidates = [c for c in candidates if c.get("score", 0) >= args.min_score]
    if args.skip > 0:
        candidates = candidates[args.skip:]
    if args.limit > 0:
        candidates = candidates[:args.limit]
    print(f"Loaded {len(candidates)} candidates for review")

    cards_index = load_cards_index(args.cards_dir)
    print(f"Loaded {len(cards_index)} cards")

    prompt_template = Path(args.prompt).read_text(encoding="utf-8-sig")

    results = review_candidates(
        candidates, cards_index, prompt_template,
        args.model, args.max_tokens, args.timeout, args.thinking_effort,
        args.retries, args.retry_delay, args.concurrency,
    )

    counts = Counter(r["review_status"] for r in results)
    print(f"Review complete: accepted={counts.get('accepted',0)}, rejected={counts.get('rejected',0)}, pending={counts.get('pending',0)}")

    write_jsonl(output_dir / "p7e_bridge_reviews.jsonl", results)
    # Also write accepted-only for downstream use
    accepted = [r for r in results if r["review_status"] == "accepted"]
    if accepted:
        write_jsonl(output_dir / "p7e_accepted_bridges.jsonl", accepted)
    print(f"Output: {output_dir}")


if __name__ == "__main__":
    main()
