"""
Runtime initialisation for the new-question analysis module.

Loads BGE model, encodes all textbook sentence cards, builds BM25 index, and
wires up the AgenticRuntime *once* at service / CLI startup.  The runtime is
cached in a module-level singleton so every subsequent request reuses it.

Evidence pool: cards_v6_sentence.json (full-book V6 sentence cards, ~5174).
KG assets (sections / edges / card_section_map) are loaded for search-planner
context but are NOT the primary retrieval entry point — retrieval relies on
card-level BGE, BM25, exact-phrase, adjacent-card, and relation expansion.
"""

from __future__ import annotations

import hashlib
import os
import pickle
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# sys.path – make the existing four-role pipeline importable
# ---------------------------------------------------------------------------
_FOUR_ROLE_DIR = (
    Path(__file__).resolve().parents[3] / "题目与kg关系建立流水线（四角色法）"
)
if str(_FOUR_ROLE_DIR) not in sys.path:
    sys.path.insert(0, str(_FOUR_ROLE_DIR))

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# Re-use the production run_step1 / run_agentic_search_experiment modules.
# The blind-experiment module is imported for its helper functions but we do
# NOT call load_agentic_runtime_without_questions() — we build our own variant
# that supports evidence-scope switching and richer logging.
import run_agentic_search_experiment as agentic  # noqa: E402
import run_step1  # noqa: E402

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_AGENTIC_RUNTIME: agentic.AgenticRuntime | None = None
_MODULE_DIR = Path(__file__).resolve().parents[1]
_CACHE_DIR = _MODULE_DIR / "outputs" / "cache"
_BGE_MODEL_NAME = "BAAI/bge-small-zh-v1.5"


def load_new_question_runtime(
    evidence_scope: str = "v6-sentence",
) -> agentic.AgenticRuntime:
    """Load KG sections / edges / card_section_map, encode every textbook
    sentence card with BGE, build a BM25 sparse index, and return a ready-to-use
    ``AgenticRuntime``.

    Parameters
    ----------
    evidence_scope:
        One of ``"v6-sentence"`` (default, full-book), ``"ch2"``,
        ``"v6-except-ch2"``, or ``"ch2-plus-v6-except"``.

    Returns
    -------
    agentic.AgenticRuntime
        Fully initialised runtime.  **questions.json is NOT loaded** — this is
        intentional for the blind new-question workflow.
    """
    api_key, base_url, env_name = run_step1.get_deepseek_config()

    from openai import OpenAI
    from sentence_transformers import SentenceTransformer

    # --- evidence file ---
    if evidence_scope not in run_step1.EVIDENCE_FILES:
        raise ValueError(
            f"Unknown evidence_scope={evidence_scope}; "
            f"choose one of {sorted(run_step1.EVIDENCE_FILES)}"
        )
    evidence_file = run_step1.EVIDENCE_FILES[evidence_scope]
    if not evidence_file.exists():
        raise FileNotFoundError(evidence_file)

    print(
        f"[evidence_pool] Loading runtime | scope={evidence_scope} | "
        f"DeepSeek key={env_name} | base_url={base_url}"
    )

    # --- KG assets (auxiliary nav only) ---
    sections = run_step1.read_json(run_step1.KG_DIR / "sections.json")
    edges = run_step1.read_json(run_step1.KG_DIR / "edges.json")
    cs_map = run_step1.read_json(run_step1.KG_DIR / "card_section_map.json")

    # --- textbook sentence cards ---
    raw_cards = run_step1.read_json(evidence_file)
    cards = (
        raw_cards.get("cards", raw_cards) if isinstance(raw_cards, dict) else raw_cards
    )
    if not isinstance(cards, list):
        raise ValueError(
            f"{evidence_file.name} is neither a list nor an object with a 'cards' key."
        )
    print(f"[evidence_pool] Loaded {len(cards)} textbook sentence cards")

    # card context dict (used by agentic retrieval)
    card_ctx: dict[str, str] = {}
    for card in cards:
        cid = card.get("card_id")
        if not cid:
            continue
        parts = [
            card.get("context_before", ""),
            card.get("knowledge", ""),
            card.get("citation", ""),
            card.get("context_after", ""),
        ]
        card_ctx[cid] = " ".join(x for x in parts if x)
    valid_card_ids: set[str] = set(card_ctx)

    # section metadata
    section_titles = [s.get("subsection_title", "") for s in sections]
    edge_index: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        src = edge.get("from_subsection", "")
        tgt = edge.get("to_subsection", "")
        edge_index.setdefault(src, []).append(edge)
        if tgt:
            edge_index.setdefault(
                tgt, []).append({**edge, "from_subsection": tgt, "to_subsection": src})

    # --- BGE model ---
    print(f"[evidence_pool] Loading {_BGE_MODEL_NAME} (local_files_only=True) ...")
    bge = SentenceTransformer(_BGE_MODEL_NAME, local_files_only=True)

    section_queries = [
        title + " " + s.get("definition", "") + " " + " ".join(s.get("aliases", []))
        for s, title in zip(sections, section_titles)
    ]
    # --- Runtime (questions=[] — blind workflow) ---
    base = run_step1.Runtime(
        sections=sections,
        edges=edges,
        section_to_cards=cs_map.get("section_to_cards", {}),
        cards=cards,
        questions=[],  # <-- intentionally empty for blind new-question mode
        card_ctx=card_ctx,
        valid_card_ids=valid_card_ids,
        section_titles=section_titles,
        edge_index=edge_index,
        bge=bge,
        section_vecs=[],
        client=OpenAI(api_key=api_key, base_url=base_url),
        evidence_scope=evidence_scope,
        evidence_file=str(evidence_file),
    )

    # --- card-level BGE vectors ---
    card_by_id = {c["card_id"]: c for c in base.cards if c.get("card_id")}
    card_ids = list(card_by_id)
    card_texts = [agentic.card_text(card_by_id[cid]) for cid in card_ids]

    cache_path = _cache_path(evidence_scope, evidence_file)
    cached = _load_retrieval_cache(cache_path, evidence_file, card_ids, card_texts)
    if cached:
        print(f"[evidence_pool] Loaded retrieval cache: {cache_path}")
        section_vecs = cached["section_vecs"]
        card_vecs = cached["card_vecs"]
        bm25_docs = cached["bm25_docs"]
        bm25_df = cached["bm25_df"]
        bm25_avgdl = cached["bm25_avgdl"]
    else:
        print("[evidence_pool] Encoding KG section vectors ...")
        section_vecs = bge.encode(section_queries, normalize_embeddings=True)

        print(f"[evidence_pool] Encoding {len(card_texts)} cards for card-level BGE ...")
        card_vecs = base.bge.encode(
            card_texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True
        )

        # --- BM25 sparse index ---
        print("[evidence_pool] Building BM25 index ...")
        bm25_docs = [Counter(agentic.tokenize(t)) for t in card_texts]
        bm25_df: Counter[str] = Counter()
        for doc in bm25_docs:
            bm25_df.update(doc.keys())
        bm25_avgdl = sum(sum(doc.values()) for doc in bm25_docs) / max(len(bm25_docs), 1)
        _save_retrieval_cache(
            cache_path,
            evidence_file,
            card_ids,
            card_texts,
            section_vecs,
            card_vecs,
            bm25_docs,
            bm25_df,
            bm25_avgdl,
        )
        print(f"[evidence_pool] Saved retrieval cache: {cache_path}")
    base.section_vecs = section_vecs

    # --- card relations (low-weight expansion) ---
    relations_path = run_step1.DATA / "card_relations.json"
    relations = run_step1.read_json(relations_path) if relations_path.exists() else {}

    rt = agentic.AgenticRuntime(
        base=base,
        card_ids=card_ids,
        card_texts=card_texts,
        card_by_id=card_by_id,
        card_vecs=card_vecs,
        bm25_docs=bm25_docs,
        bm25_df=bm25_df,
        bm25_avgdl=bm25_avgdl,
        relations=relations,
    )

    print(
        f"[evidence_pool] Runtime ready: {len(rt.card_ids)} cards, "
        f"{len(rt.base.sections)} KG sections, "
        f"BM25 avgdl={bm25_avgdl:.1f}"
    )
    return rt


def _cache_path(evidence_scope: str, evidence_file: Path) -> Path:
    stamp = _evidence_cache_stamp(evidence_file)
    digest = hashlib.sha256(
        f"{evidence_scope}|{evidence_file}|{stamp}|{_BGE_MODEL_NAME}".encode("utf-8")
    ).hexdigest()[:16]
    return _CACHE_DIR / f"retrieval_{evidence_scope}_{digest}.pkl"


def _evidence_cache_stamp(evidence_file: Path) -> str:
    stat = evidence_file.stat()
    return f"{stat.st_size}:{int(stat.st_mtime)}"


def _card_texts_digest(card_ids: list[str], card_texts: list[str]) -> str:
    h = hashlib.sha256()
    for cid, text in zip(card_ids, card_texts):
        h.update(cid.encode("utf-8", errors="ignore"))
        h.update(b"\0")
        h.update(text.encode("utf-8", errors="ignore"))
        h.update(b"\0")
    return h.hexdigest()


def _load_retrieval_cache(
    cache_path: Path,
    evidence_file: Path,
    card_ids: list[str],
    card_texts: list[str],
) -> dict[str, Any] | None:
    if not cache_path.exists():
        return None
    try:
        with cache_path.open("rb") as f:
            cached = pickle.load(f)
    except Exception as exc:
        print(f"[evidence_pool] Ignoring unreadable cache: {exc}")
        return None

    expected = {
        "schema_version": 1,
        "evidence_file": str(evidence_file),
        "evidence_stamp": _evidence_cache_stamp(evidence_file),
        "bge_model": _BGE_MODEL_NAME,
        "card_count": len(card_ids),
        "card_texts_digest": _card_texts_digest(card_ids, card_texts),
    }
    meta = cached.get("meta", {}) if isinstance(cached, dict) else {}
    for key, value in expected.items():
        if meta.get(key) != value:
            print(f"[evidence_pool] Cache miss: {key} changed")
            return None

    payload = cached.get("payload", {})
    required = {"section_vecs", "card_vecs", "bm25_docs", "bm25_df", "bm25_avgdl"}
    if not required.issubset(payload):
        print("[evidence_pool] Cache miss: payload incomplete")
        return None
    return payload


def _save_retrieval_cache(
    cache_path: Path,
    evidence_file: Path,
    card_ids: list[str],
    card_texts: list[str],
    section_vecs: Any,
    card_vecs: Any,
    bm25_docs: list[Counter[str]],
    bm25_df: Counter[str],
    bm25_avgdl: float,
) -> None:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "schema_version": 1,
            "evidence_file": str(evidence_file),
            "evidence_stamp": _evidence_cache_stamp(evidence_file),
            "bge_model": _BGE_MODEL_NAME,
            "card_count": len(card_ids),
            "card_texts_digest": _card_texts_digest(card_ids, card_texts),
        },
        "payload": {
            "section_vecs": section_vecs,
            "card_vecs": card_vecs,
            "bm25_docs": bm25_docs,
            "bm25_df": bm25_df,
            "bm25_avgdl": bm25_avgdl,
        },
    }
    tmp_path = cache_path.with_suffix(".tmp")
    with tmp_path.open("wb") as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
    tmp_path.replace(cache_path)


def get_agentic_runtime() -> agentic.AgenticRuntime:
    """Return the cached global AgenticRuntime singleton.

    Calls ``load_new_question_runtime()`` on first access; subsequent calls
    return the same object.
    """
    global _AGENTIC_RUNTIME
    if _AGENTIC_RUNTIME is None:
        _AGENTIC_RUNTIME = load_new_question_runtime()
    return _AGENTIC_RUNTIME


# ---------------------------------------------------------------------------
# Convenience: allow ``python -m pipeline.evidence_pool`` as a quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    rt = get_agentic_runtime()
    print(f"Smoke test OK — {len(rt.card_ids)} cards loaded.")
