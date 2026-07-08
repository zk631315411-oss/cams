"""P1.1: Rerank clients — local cross-encoder (GPU) and LLM-based (API)."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


def _parse_flash_scores(raw: str, expected: int) -> list[float] | None:
    """Parse Flash score output to list of floats. Handles broken JSON heuristically."""
    import re
    raw = raw.strip()
    # Try direct JSON parse first
    for candidate in [raw]:
        try:
            arr = json.loads(candidate)
            if isinstance(arr, list):
                if arr and isinstance(arr[0], list):
                    arr = arr[0]
                return [float(x) for x in arr[:expected]]
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    # Extract numbers with regex as fallback
    nums = re.findall(r'\d+(?:\.\d+)?', raw)
    if nums:
        return [float(n) for n in nums[:expected]]
    return None


def llm_rerank(
    query: str,
    passages: list[str],
    *,
    client: Any,
    model: str = "deepseek-v4-flash",
    batch_size: int = 40,
) -> list[float]:
    """Use Flash to score passages (0-10), returning 0-1 scores. Replaces CE.

    Sends passages in batches. Each batch gets a prompt asking for 0-10 relevance
    scores per document. Parse is lenient — falls back to regex if JSON is malformed.
    """
    if not passages or client is None:
        return [0.5] * len(passages)

    all_scores: list[float] = [0.5] * len(passages)

    for start in range(0, len(passages), batch_size):
        batch = passages[start:start + batch_size]
        lines = [f"[{i}] {t[:300]}" for i, t in enumerate(batch)]
        prompt = (
            f"Score each document's relevance to the query (0=irrelevant, 10=exact match). "
            f"Return ONLY a JSON array of {len(batch)} integers, nothing else.\n"
            f"Query: {query[:400]}\n"
            f"Documents:\n" + "\n".join(lines) + "\n"
            f"Scores (JSON array of {len(batch)} ints):"
        )
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=1500,
            )
            raw = (resp.choices[0].message.content or "").strip()
            parsed = _parse_flash_scores(raw, len(batch))
            if parsed:
                for i, s in enumerate(parsed):
                    if i < len(batch):
                        all_scores[start + i] = min(1.0, max(0.0, s / 10.0))
        except Exception as exc:
            print(f"[reuse] llm-rerank batch failed: {exc}")

    return all_scores


def cross_encoder_rerank(
    query: str,
    passages: list[str],
    *,
    url: str = "http://localhost:8000/rerank",
    timeout: int = 30,
) -> list[float]:
    """Return rerank scores in input order.

    The local rerank server follows the WeKnora-style contract:
    ``POST /rerank`` with ``{"query": str, "documents": list[str]}``.
    If the server is unavailable, return neutral scores so the pipeline can
    fall back to retrieval ranking.
    """
    if not passages:
        return []

    body = json.dumps({"query": query, "documents": passages}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        print(f"[reuse] cross-encoder unavailable ({exc}), falling back to retrieval scores")
        return [0.5] * len(passages)

    scores = [0.5] * len(passages)
    for row in data.get("results", []) or []:
        try:
            idx = int(row.get("index", -1))
            score = float(row.get("score", row.get("relevance_score", 0.5)))
        except (TypeError, ValueError):
            continue
        if 0 <= idx < len(scores):
            scores[idx] = score
    return scores
