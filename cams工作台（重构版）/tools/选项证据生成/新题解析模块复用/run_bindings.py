"""
Lightweight reuse of the usable 新题解析模块 for formal question-card bindings.

This wrapper keeps the useful multi-role core:
  search planner -> sentence-card retrieval -> blind adjudicator -> LLM reviewer
  -> deterministic rule review -> validation/export

It intentionally drops API/frontend draft concerns and display-only generation
such as exam_direction. The output is a compact per-question JSON plus JSONL
binding rows for downstream audit and frontend ingestion.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import pickle
import re
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
WORKBENCH = HERE.parents[2]  # cams工作台（重构版）
ROOT = HERE.parents[3]  # cams考试
SOURCE_MODULE = ROOT / "cams工作台" / "新题解析模块"
FOUR_ROLE_DIR = ROOT / "题目与kg关系建立流水线（四角色法）"

for path in (str(SOURCE_MODULE), str(FOUR_ROLE_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import run_agentic_search_experiment as agentic  # noqa: E402
import run_blind_q212_experiment as blind  # noqa: E402
import run_step1  # noqa: E402
from pipeline.question_parser import parse_question  # noqa: E402
from pipeline import run_pipeline as nq  # noqa: E402

# === WeKnora 式检索增强模块 ===
from retrieval.terminology_map import expand_terms
from retrieval.card_graph import (
    build_card_adjacency,
    build_parent_blocks,
    build_card_to_parent,
    expand_short_cards,
    resolve_parent_block,
    expand_with_neighbors,
)
from retrieval.enrich import enrich_candidates
from retrieval.rrf import rrf_fuse, merge_rrf_with_append
from retrieval.cross_encoder import cross_encoder_rerank, llm_rerank
import plan_b as plan_b_module

from retrieval.passage_score_mmr import (
    clean_card_text,
    build_passage,
    build_ce_passage,
    compute_composite_score,
    jaccard_mmr,
)

SCHEMA_VERSION = "new_question_reuse_binding_v1"
OUTPUT_DIR = HERE / "output"
BINDINGS_JSONL = OUTPUT_DIR / "question_option_card_bindings.jsonl"
SUMMARY_JSON = OUTPUT_DIR / "summary.json"
CACHE_DIR = OUTPUT_DIR / "cache"
CANDIDATE_CACHE_DIR = OUTPUT_DIR / "candidate_cache"
DEFAULT_KG_WORK_DIR = WORKBENCH / "tools" / "知识图谱" / "提取" / "work"
LEGACY_KG_WORK_DIR = WORKBENCH / "tools" / "知识图谱" / "模拟高代提取" / "work"
BGE_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
# LLM constants and functions moved to pipeline.llm
from stages.llm import (
    DEFAULT_BASE_URL, DEFAULT_MODEL, DEFAULT_REASONING_EFFORT,
    DEFAULT_STAGE_MODELS, DEFAULT_STAGE_REASONING, JSON_SYSTEM_PROMPT,
    LLMStageConfig, llm_stage_config, llm_stage_summary,
    parse_stage_model_requirements, assert_stage_model_requirements,
    print_model_plan, configure_llm_from_env,
    call_llm_compat, _patched_nq_call_llm_traced,
    _THREAD_LOCAL,
)
DEFAULT_WORKERS = 1
DEFAULT_STAGE_RETRIES = 1
DEFAULT_STAGE_RETRY_CONCURRENCY = 1
DEFAULT_STAGE_RETRY_DELAY_SECONDS = 20.0
DEFAULT_REPAIR_DISAGREEMENTS = True
DEFAULT_REPAIR_MAX_ROUNDS = 1
DEFAULT_REPAIR_TOP_K = 45
DEFAULT_REPAIR_MAX_FOLLOWUPS = 1
DEFAULT_REPAIR_KG_NODE_TOP_K = 12
DEFAULT_REPAIR_KG_MAX_CARDS_PER_OPTION = 16
DEFAULT_REPAIR_KG_NEIGHBOR_LIMIT = 6
DEFAULT_REPAIR_KG_NODE_SCORE_THRESHOLD = 0.36
REPAIR_DISAGREEMENT_TYPES = {"retrieval_gap", "focus_misdirected", "weak_convergence"}
REVIEW_ADJUSTMENT_REASON = "答案复核调整了该选项的判断"
MAX_BINDING_CARDS_PER_OPTION = 12
DISAGREEMENT_REVIEW_MAX_TOKENS = 2800
DEFAULT_KG_NODE_TOP_K = 8
DEFAULT_KG_MAX_CARDS_PER_OPTION = 10
DEFAULT_KG_NEIGHBOR_LIMIT = 4
DEFAULT_KG_NODE_SCORE_THRESHOLD = 0.43
FIELD_NOTES = {
    "evidence_card_ids": "强证据关系：裁判/复核明确采信并引用的句卡，适合作为题目-选项-句卡的高置信绑定。",
    "candidate_card_ids": "候选关系：当前选项最终候选池中的高排位句卡，用于教研复核、召回扩展和弱关系沉淀，不等同于已采信证据。",
    "card_ids": "混合绑定关系：先放 evidence_card_ids，再补 candidate_card_ids 至上限；默认用于宽关系资产沉淀。消费时应优先读取 evidence_card_ids。",
    "evidence_cards": "强证据详情：包含 quote/reason/support_type/relevance，是解释为什么判对、判错或证据不足的主要依据。",
    "relation_strengths": "card_ids 的逐卡强弱标记：strong_evidence 表示已采信证据；weak_candidate 表示补充候选。",
}
# JSON_SYSTEM_PROMPT moved to pipeline.llm
configure_llm_from_env()  # patches run_step1 + nq at import time
BLIND_LLM_STAGES = {"adjudicator", "reviewer"}
BLIND_PROMPT_LEAK_RE = re.compile(
    r"(?:题库答案|标准答案|正确答案|参考答案|推荐答案|recommended_answer|key_answer)"
    r"['\"]?\s*[：:=]\s*(?:['\"]?[A-K](?:\s*[,，、/;；]\s*['\"]?[A-K])*|[\[\(]\s*['\"]?[A-K])",
    re.IGNORECASE,
)
_card_adjacency: dict[str, dict[str, str | None]] = {}
_parent_blocks: dict[str, dict[str, Any]] = {}
_card_to_parent: dict[str, str] = {}
# Pipeline feature flags
_use_card_expansion = True
_use_enrichment = True
_use_cross_encoder = True
_use_llm_rerank = True
_cross_encoder_url = "http://localhost:8000/rerank"
_use_parent_replace = True
_use_mmr = True
_mmr_lambda = 0.7
_use_plan_b = False


@dataclass
class KGRecallRuntime:
    work_dir: Path
    nodes: dict[str, dict[str, Any]]
    node_ids: list[str]
    node_texts: list[str]
    node_vecs: Any
    node_cards: dict[str, list[dict[str, Any]]]
    neighbors: dict[str, list[dict[str, Any]]]
    source_stats: dict[str, int]
    card_to_nodes: dict[str, list[str]]  # card_id → node_ids 反向索引


# LLMStageConfig moved to pipeline.llm


# LLM functions moved to pipeline.llm
# Patches applied at pipeline.llm import time


MD_DIR = ROOT / "教材、答疑记录、习题与参考文献" / "习题" / "习题结构化"
RE_Q = re.compile(r"^##\s*第(\d+)题\s*(.+)")
RE_O = re.compile(r"^-\s*([A-K])[\.\、\)）]\s*(.+)", re.MULTILINE)
RE_A = re.compile(r"答案\s*[:：]\s*([A-K,，、/;；\s]+)")
RE_SECTION = re.compile(r"^#\s*(?:第[一二三四五六七八九十]+章\s*)?([\d.]+)\s*习题(?:集)?")


def load_reuse_runtime(evidence_scope: str = "v6-sentence") -> agentic.AgenticRuntime:
    """Load only the sentence-card evidence pool and retrieval indexes.

    This intentionally does not load legacy KG sections / card_section_map or
    card_relations.json. The optional KG recall layer is loaded separately from
    the v6s-native audited graph outputs.
    """
    api_key, base_url, env_name = run_step1.get_deepseek_config()

    from openai import OpenAI
    from sentence_transformers import SentenceTransformer

    if evidence_scope not in run_step1.EVIDENCE_FILES:
        raise ValueError(f"unknown evidence_scope={evidence_scope}; choose one of {sorted(run_step1.EVIDENCE_FILES)}")
    evidence_file = run_step1.EVIDENCE_FILES[evidence_scope]
    if not evidence_file.exists():
        raise FileNotFoundError(evidence_file)

    print(f"[reuse] loading sentence-card runtime | scope={evidence_scope} | key={env_name} | base_url={base_url}")
    raw_cards = read_json(evidence_file)
    cards = raw_cards.get("cards", raw_cards) if isinstance(raw_cards, dict) else raw_cards
    if not isinstance(cards, list):
        raise ValueError(f"{evidence_file.name} is neither a list nor an object with a cards key.")

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

    print(f"[reuse] loading {BGE_MODEL_NAME} ...")
    bge = SentenceTransformer(BGE_MODEL_NAME, local_files_only=True)
    client = OpenAI(api_key=api_key, base_url=base_url)

    base = run_step1.Runtime(
        sections=[],
        edges=[],
        section_to_cards={},
        cards=cards,
        questions=[],
        card_ctx=card_ctx,
        valid_card_ids=set(card_ctx),
        section_titles=[],
        edge_index={},
        bge=bge,
        section_vecs=[],
        client=client,
        evidence_scope=evidence_scope,
        evidence_file=str(evidence_file),
    )

    card_by_id = {card["card_id"]: card for card in cards if card.get("card_id")}
    card_ids = list(card_by_id)
    card_texts = [agentic.card_text(card_by_id[cid]) for cid in card_ids]
    cache_path = retrieval_cache_path(evidence_scope, evidence_file, card_ids)
    cached = load_retrieval_cache(cache_path, evidence_file, card_ids)
    if cached:
        print(f"[reuse] loaded retrieval cache: {cache_path}")
        card_vecs = cached["card_vecs"]
        bm25_docs = cached["bm25_docs"]
        bm25_df = cached["bm25_df"]
        bm25_avgdl = cached["bm25_avgdl"]
    else:
        print(f"[reuse] encoding {len(card_texts)} sentence cards ...")
        card_vecs = bge.encode(card_texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True)
        print("[reuse] building BM25 index ...")
        bm25_docs = [Counter(agentic.tokenize(text)) for text in card_texts]
        bm25_df: Counter[str] = Counter()
        for doc in bm25_docs:
            bm25_df.update(doc.keys())
        bm25_avgdl = sum(sum(doc.values()) for doc in bm25_docs) / max(len(bm25_docs), 1)
        save_retrieval_cache(cache_path, evidence_file, card_ids, card_vecs, bm25_docs, bm25_df, bm25_avgdl)
        print(f"[reuse] saved retrieval cache: {cache_path}")

    return agentic.AgenticRuntime(
        base=base,
        card_ids=card_ids,
        card_texts=card_texts,
        card_by_id=card_by_id,
        card_vecs=card_vecs,
        bm25_docs=bm25_docs,
        bm25_df=bm25_df,
        bm25_avgdl=bm25_avgdl,
        relations={},
    )


# === P0.1: sibling chain ===
# build_card_adjacency imported from retrieval.card_graph



# build_parent_blocks imported from retrieval.card_graph

# === P1.1: cross-encoder re-rank client ===
CROSS_ENCODER_URL = "http://localhost:8000/rerank"
CROSS_ENCODER_TIMEOUT = 300  # seconds


def make_openai_client() -> Any:
    api_key, base_url, _env_name = run_step1.get_deepseek_config()
    from openai import OpenAI
    return OpenAI(api_key=api_key, base_url=base_url)


def runtime_for_current_thread(rt: agentic.AgenticRuntime) -> agentic.AgenticRuntime:
    client = getattr(_THREAD_LOCAL, "client", None)
    if client is None:
        client = make_openai_client()
        _THREAD_LOCAL.client = client
    return agentic.AgenticRuntime(
        base=replace(rt.base, client=client),
        card_ids=rt.card_ids,
        card_texts=rt.card_texts,
        card_by_id=rt.card_by_id,
        card_vecs=rt.card_vecs,
        bm25_docs=rt.bm25_docs,
        bm25_df=rt.bm25_df,
        bm25_avgdl=rt.bm25_avgdl,
        relations=rt.relations,
    )


def kg_node_text(node: dict[str, Any]) -> str:
    parts = [
        node.get("title", ""),
        node.get("node_type", ""),
        node.get("definition", ""),
        node.get("chapter", ""),
        node.get("section", ""),
        node.get("subsection", ""),
        node.get("evidence_span", ""),
    ]
    return " ".join(str(part).strip() for part in parts if str(part or "").strip())


def add_kg_neighbor(neighbors: dict[str, list[dict[str, Any]]], src: str, dst: str, edge: dict[str, Any], direction: str) -> None:
    if not src or not dst:
        return
    neighbors.setdefault(src, []).append(
        {
            "node_id": dst,
            "edge_id": edge.get("edge_id", ""),
            "type": edge.get("type", ""),
            "detail": edge.get("detail", ""),
            "direction": direction,
            "source": edge.get("source", "explicit"),
            "strength": edge.get("strength", ""),
        }
    )


def resolve_kg_work_dir(work_dir: Path) -> Path:
    if work_dir.exists() and work_dir.is_dir() and any(work_dir.glob("ch*/nodes_accepted.jsonl")):
        return work_dir
    nested_work = work_dir / "work"
    if nested_work.exists() and any(nested_work.glob("ch*/nodes_accepted.jsonl")):
        return nested_work
    if work_dir == LEGACY_KG_WORK_DIR and DEFAULT_KG_WORK_DIR.exists():
        return DEFAULT_KG_WORK_DIR
    return work_dir


def kg_hidden_edge_paths(work_dir: Path) -> list[Path]:
    direct = work_dir / "edges_hidden.jsonl"
    if direct.exists():
        return [direct]
    archive_paths = sorted(
        work_dir.glob("archive_*/edges_hidden.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return archive_paths[:1]


def load_kg_recall_runtime(
    *,
    work_dir: Path = DEFAULT_KG_WORK_DIR,
    bge: Any,
    valid_card_ids: set[str],
) -> KGRecallRuntime | None:
    work_dir = resolve_kg_work_dir(work_dir)
    if not work_dir.exists():
        print(f"[reuse] KG recall disabled: work_dir not found: {work_dir}")
        return None

    nodes: dict[str, dict[str, Any]] = {}
    node_cards: dict[str, list[dict[str, Any]]] = {}
    neighbors: dict[str, list[dict[str, Any]]] = {}
    source_stats: Counter[str] = Counter()

    chapter_dirs = sorted(path for path in work_dir.iterdir() if path.is_dir() and path.name.startswith("ch"))
    for chapter_dir in chapter_dirs:
        for node in read_jsonl(chapter_dir / "nodes_accepted.jsonl"):
            node_id = str(node.get("node_id", "")).strip()
            if node_id:
                nodes[node_id] = node

        for edge_path in (chapter_dir / "edges_accepted.jsonl", chapter_dir / "edges_for_merge.jsonl"):
            for edge in read_jsonl(edge_path):
                src = str(edge.get("source_node_id", "")).strip()
                dst = str(edge.get("target_node_id", "")).strip()
                if not src or not dst:
                    continue
                add_kg_neighbor(neighbors, src, dst, edge, "out")
                add_kg_neighbor(neighbors, dst, src, edge, "in")

        mount_path = chapter_dir / "card_mounts_audited.jsonl"
        raw_mount = False
        if not mount_path.exists() or mount_path.stat().st_size == 0:
            mount_path = chapter_dir / "card_mounts.jsonl"
            raw_mount = True
        for mount in read_jsonl(mount_path):
            node_id = str(mount.get("node_id", "")).strip()
            if not node_id:
                continue
            rows: list[dict[str, Any]] = []
            for card in mount.get("cards", []) or []:
                if not isinstance(card, dict):
                    continue
                cid = str(card.get("card_id", "")).strip()
                if not cid or cid not in valid_card_ids:
                    continue
                decision = str(card.get("decision", "accept" if raw_mount else "") or "").strip()
                if not raw_mount and decision != "accept":
                    continue
                method = str(card.get("method", "") or "").strip()
                source = "kg_mount_raw" if raw_mount else "kg_mount"
                rows.append(
                    {
                        "card_id": cid,
                        "node_id": node_id,
                        "method": method,
                        "score": float(card.get("score", 0) or 0),
                        "decision": decision or ("raw" if raw_mount else ""),
                        "source": source,
                    }
                )
                source_stats[source] += 1
            if rows:
                node_cards.setdefault(node_id, [])
                node_cards[node_id].extend(rows)

    for hidden_path in kg_hidden_edge_paths(work_dir):
        for edge in read_jsonl(hidden_path):
            src = str(edge.get("source_node_id", "")).strip()
            dst = str(edge.get("target_node_id", "")).strip()
            if not src or not dst:
                continue
            edge = {**edge, "source": "hidden"}
            add_kg_neighbor(neighbors, src, dst, edge, "out")
            add_kg_neighbor(neighbors, dst, src, edge, "in")
            source_stats["hidden_edges"] += 1
        source_stats["hidden_edge_files"] += 1

    node_ids = [node_id for node_id, node in nodes.items() if kg_node_text(node)]
    node_texts = [kg_node_text(nodes[node_id]) for node_id in node_ids]
    if not node_ids:
        print(f"[reuse] KG recall disabled: no accepted nodes in {work_dir}")
        return None

    # Build card_id → node_id reverse index for enrichment
    card_to_nodes: dict[str, list[str]] = {}
    for node_id, cards in node_cards.items():
        for card in cards:
            cid = card.get("card_id", "")
            if cid:
                card_to_nodes.setdefault(cid, [])
                if node_id not in card_to_nodes[cid]:
                    card_to_nodes[cid].append(node_id)

    print(f"[reuse] loading KG recall | nodes={len(node_ids)} mounted_nodes={len(node_cards)} "
          f"card_to_nodes={len(card_to_nodes)} work_dir={work_dir}")
    node_vecs = bge.encode(node_texts, normalize_embeddings=True, batch_size=64, show_progress_bar=False)
    return KGRecallRuntime(
        work_dir=work_dir,
        nodes=nodes,
        node_ids=node_ids,
        node_texts=node_texts,
        node_vecs=node_vecs,
        node_cards=node_cards,
        neighbors=neighbors,
        source_stats=dict(source_stats),
        card_to_nodes=card_to_nodes,
    )


def retrieval_cache_path(evidence_scope: str, evidence_file: Path, card_ids: list[str]) -> Path:
    stat = evidence_file.stat()
    digest = hashlib.sha1(
        f"{evidence_scope}|{evidence_file}|{stat.st_size}|{stat.st_mtime_ns}|{BGE_MODEL_NAME}|{len(card_ids)}".encode("utf-8")
    ).hexdigest()[:12]
    return CACHE_DIR / f"retrieval_{evidence_scope}_{digest}.pkl"


def load_retrieval_cache(path: Path, evidence_file: Path, card_ids: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        with path.open("rb") as f:
            data = pickle.load(f)
    except Exception:
        return None
    stat = evidence_file.stat()
    meta = data.get("meta", {})
    if meta.get("evidence_file") != str(evidence_file):
        return None
    if meta.get("size") != stat.st_size or meta.get("mtime_ns") != stat.st_mtime_ns:
        return None
    if meta.get("card_ids") != card_ids:
        return None
    return data


def save_retrieval_cache(
    path: Path,
    evidence_file: Path,
    card_ids: list[str],
    card_vecs: Any,
    bm25_docs: list[Counter[str]],
    bm25_df: Counter[str],
    bm25_avgdl: float,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stat = evidence_file.stat()
    data = {
        "meta": {
            "evidence_file": str(evidence_file),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "model": BGE_MODEL_NAME,
            "card_ids": card_ids,
        },
        "card_vecs": card_vecs,
        "bm25_docs": bm25_docs,
        "bm25_df": bm25_df,
        "bm25_avgdl": bm25_avgdl,
    }
    with path.open("wb") as f:
        pickle.dump(data, f)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows



def blind_leakage_audit(stage: str, prompt: str, raw: str = "") -> dict[str, Any]:
    """Audit blind-stage text for answer-key leakage indicators."""
    payload: dict[str, Any] = {"stage": stage, "status": "not_applicable", "issues": []}
    if stage not in BLIND_LLM_STAGES:
        return payload
    prompt_issues = [
        f"prompt contains answer-like field: {match.group(0)[:80]}"
        for match in BLIND_PROMPT_LEAK_RE.finditer(prompt)
    ]
    raw_issues = blind.leakage_check({"raw": raw}) if raw else []
    issues = prompt_issues + [f"raw:{item}" for item in raw_issues]
    payload["status"] = "fail" if issues else "pass"
    payload["issues"] = issues
    payload["prompt_chars"] = len(prompt)
    payload["completion_chars"] = len(raw)
    return payload


def strip_answer_lines(text: str) -> str:
    """Remove explicit answer/explanation blocks before blind parsing fallback."""
    text = re.sub(
        r"(?im)^\s*(?:答案|标准答案|正确答案|参考答案)\s*[：:].*$",
        "",
        str(text or ""),
    )
    text = re.sub(
        r"(?ims)^\s*(?:解析|题目解析|答案解析)\s*[：:].*$",
        "",
        text,
    )
    return text.strip()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def question_output_path(qid: str, output_dir: Path = OUTPUT_DIR) -> Path:
    safe = re.sub(r"[^0-9A-Za-z_.-]+", "_", str(qid))
    return output_dir / "questions" / f"q_{safe}.json"


def normalize_answer(answer: Any, options: dict[str, str]) -> list[str]:
    labels = set(options)
    if isinstance(answer, list):
        raw = " ".join(str(x) for x in answer)
    else:
        raw = str(answer or "")
    raw = raw.strip().upper()
    if not raw:
        return []
    parts = [p for p in re.split(r"[,，、/;；\s]+", raw) if p]
    if len(parts) == 1 and re.fullmatch(r"[A-K]+", parts[0]):
        parts = list(parts[0])
    seen: set[str] = set()
    rows: list[str] = []
    for part in parts:
        if part in labels and part not in seen:
            seen.add(part)
            rows.append(part)
    return rows


def load_questions_from_md(md_dir: Path = MD_DIR) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for path in sorted(md_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        sm = RE_SECTION.search(text)
        section = sm.group(1).strip() if sm else path.stem.split("_")[0]
        blocks = re.split(r"(?=^##\s*第\d+题)", text, flags=re.MULTILINE)
        for block in blocks:
            qm = RE_Q.search(block)
            if not qm:
                continue
            number = int(qm.group(1))
            stem = qm.group(2).strip()
            # setdefault keeps first match only — answer explanations that
            # share the same `- B. …` prefix are ignored.
            options: dict[str, str] = {}
            for m in RE_O.finditer(block):
                options.setdefault(m.group(1), m.group(2).strip())
            am = RE_A.search(block)
            answer = ",".join(sorted(set(re.findall(r"[A-K]", am.group(1).upper())))) if am else ""
            qid = f"{section}_{number}"
            questions.append(
                {
                    "id": qid,
                    "section": section,
                    "number": number,
                    "stem": stem,
                    "options": options,
                    "answer": answer,
                    "source": str(path),
                }
            )
    return questions


def load_questions_from_jsonl(path: Path) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if "raw_text" in data and ("stem" not in data or "options" not in data):
                questions.append({"id": data.get("id") or f"line_{line_no}", "raw_text": data["raw_text"]})
            else:
                questions.append(data)
    return questions


def structured_question_text(question: dict[str, Any]) -> str:
    if question.get("raw_text"):
        return str(question["raw_text"]).strip()
    stem = str(question.get("stem", "")).strip()
    options = question.get("options", {}) or {}
    lines = [stem]
    for label, text in options.items():
        lines.append(f"{label}. {text}")
    answer = str(question.get("answer", "")).strip()
    if answer:
        lines.append(f"答案：{answer}")
    return "\n".join(lines).strip()


def blind_structured_question_text(question: dict[str, Any]) -> str:
    stem = str(question.get("stem", "")).strip()
    options = question.get("options", {}) if isinstance(question.get("options"), dict) else {}
    if stem and options:
        lines = [stem]
        for label, text in options.items():
            lines.append(f"{label}. {text}")
        return "\n".join(lines).strip()
    return strip_answer_lines(str(question.get("raw_text", "")))


def normalize_question(question: dict[str, Any], client: Any) -> dict[str, Any]:
    qid = str(question.get("id") or question.get("question_id") or "").strip()
    stem = str(question.get("stem", "")).strip()
    options = question.get("options", {}) if isinstance(question.get("options"), dict) else {}
    answer = str(question.get("answer", question.get("detected_answer", "")) or "").strip()
    if not answer and question.get("raw_text"):
        # Keep the answer for post-hoc QA when rules can extract it locally,
        # while the blind parser below receives answer-stripped text only.
        original_rules = parse_question(None, structured_question_text(question))
        answer = str(original_rules.get("detected_answer", "") or "").strip()

    if stem and len(options) >= 2:
        normalized_options = {str(k).strip().upper(): str(v).strip() for k, v in options.items() if str(k).strip()}
        qtype = str(question.get("question_type", "") or "").strip()
        qsub = str(question.get("question_subtype", "") or "").strip()
        if not qtype:
            parsed = parse_question(None, blind_structured_question_text({**question, "options": normalized_options}))
            qtype = parsed.get("question_type", "unknown")
            qsub = parsed.get("question_subtype", "unknown")
        return {
            **question,
            "id": qid,
            "stem": stem,
            "options": normalized_options,
            "answer": answer,
            "detected_answer": answer,
            "question_type": qtype or "unknown",
            "question_subtype": qsub or "unknown",
            "parse_method": question.get("parse_method", "structured"),
            "parse_warnings": question.get("parse_warnings", []),
        }

    raw_text = blind_structured_question_text(question)
    parsed = parse_question(client, raw_text)
    return {
        **question,
        "id": qid or str(question.get("id") or ""),
        "stem": parsed.get("stem", ""),
        "options": parsed.get("options", {}),
        "answer": str(answer or parsed.get("detected_answer", "") or ""),
        "detected_answer": str(answer or parsed.get("detected_answer", "") or ""),
        "question_type": parsed.get("question_type", "unknown"),
        "question_subtype": parsed.get("question_subtype", "unknown"),
        "parse_method": parsed.get("parse_method", "unknown"),
        "parse_warnings": parsed.get("parse_warnings", []),
        "parse_question": parsed,
    }


def call_llm_traced(client: Any, stage: str, prompt: str, max_tokens: int) -> tuple[str, dict[str, Any]]:
    started = time.perf_counter()
    cfg = llm_stage_config(stage)
    raw = run_step1.call_llm(client, prompt, max_tokens, stage=stage)
    return raw, {
        "stage": stage,
        "model": cfg.model,
        "reasoning_effort": cfg.reasoning_effort,
        "extra_body": cfg.extra_body,
        "max_tokens": max_tokens,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
        "prompt_chars": len(prompt),
        "completion_chars": len(raw),
        "blind_leakage_check": blind_leakage_audit(stage, prompt, raw),
    }


def infer_focus_type(stem: str, options: dict[str, str]) -> str:
    text = f"{stem} " + " ".join(options.values())
    if any(term in text for term in ["可疑交易报告", "STR", "SAR", "报告的焦点", "应成为可疑交易报告的焦点"]):
        return "str_focus"
    if any(term in text for term in ["社会/经济后果", "社会经济后果", "经济后果", "社会后果", "后果是什么"]):
        return "social_economic_consequence"
    if any(term in text for term in ["OFAC", "SDN", "制裁", "冻结", "海外资产控制办公室"]):
        return "sanctions_ofac_action"
    if any(term in text for term in ["声誉风险", "合规风险", "升级关注", "高风险司法管辖区公司"]):
        return "reputation_compliance_risk"
    if any(term in text for term in ["危险信号", "红旗", "可疑", "异常", "风险信号"]):
        return "transaction_red_flag"
    if any(term in text for term in ["阶段", "处置", "离析", "融合", "放置"]):
        return "process_stage"
    if any(term in text for term in ["定义", "是什么", "指的是", "概念"]):
        return "definition"
    return "other"



def normalize_evidence_grade(row: dict[str, Any], focus_type: str) -> str:
    existing = str(row.get("evidence_grade", "")).strip()
    if existing:
        return existing
    judgement = str(row.get("judgement", "")).strip()
    status = str(row.get("evidence_status", "")).strip()
    cards = row.get("evidence_cards", []) or []
    directish = [
        card for card in cards
        if isinstance(card, dict) and str(card.get("support_type", "")).strip() in {"direct", "negative"}
    ]
    quotes = " ".join(str(card.get("quote", "")) for card in cards if isinstance(card, dict))
    option_text = str(row.get("option_text", ""))

    if status in {"conflict"}:
        return "negative_direct"
    if status in {"none", "needs_manual", ""}:
        return status or "none"
    if judgement == "correct" and status == "direct":
        if len(directish) >= 2:
            return "direct_multi"
        return "direct_single"
    if judgement == "correct" and status == "indirect":
        if len(directish) >= 2:
            return "direct_multi"
        if focus_type == "transaction_red_flag" and len(cards) >= 2 and all(
            isinstance(card, dict) and str(card.get("relevance", "")).strip() in {"high", "medium"}
            for card in cards
        ):
            return "direct_multi"
        if is_semantic_direct(option_text, quotes, focus_type):
            return "semantic_direct"
        return "indirect_context"
    if status == "direct":
        return "direct_single" if len(directish) <= 1 else "direct_multi"
    if is_semantic_direct(option_text, quotes, focus_type):
        return "semantic_direct"
    return "indirect_context"


def is_semantic_direct(option_text: str, evidence_text: str, focus_type: str) -> bool:
    option = option_text.replace(" ", "")
    evidence = evidence_text.replace(" ", "")
    if not option or not evidence:
        return False
    if focus_type == "social_economic_consequence":
        if "增加" in option and any(term in evidence for term in ["风险增大", "滋生", "猖獗", "更多"]):
            return True
        if "削弱" in option and any(term in evidence for term in ["削弱", "损害", "危害", "负面影响"]):
            return True
    if focus_type == "reputation_compliance_risk":
        if "声誉风险" in option and "声誉风险" in evidence:
            return True
    if focus_type == "str_focus":
        if any(term in option for term in ["外国管辖区", "境外", "多个"]) and any(
            term in evidence for term in ["多个司法管辖区", "从一个国家或地区转移到另外一个国家或地区", "高风险司法管辖区"]
        ):
            return True
    return False


def enrich_option_grades(result: dict[str, Any]) -> dict[str, Any]:
    focus_type = infer_focus_type(result.get("stem", ""), result.get("options", {}))
    result.setdefault("pipeline", {}).setdefault("question_focus", {})["question_focus_type"] = focus_type
    for row in result.get("pipeline", {}).get("explain_options", {}).get("option_analysis", []):
        if not isinstance(row, dict):
            continue
        row["evidence_grade"] = normalize_evidence_grade(row, focus_type)
        row["focus_type"] = focus_type
    result.setdefault("final", {})["focus_type"] = focus_type
    return result


def diagnose_answer_disagreement(result: dict[str, Any]) -> dict[str, Any]:
    options = result.get("options", {})
    key = set(normalize_answer(result.get("answer", ""), options))
    ai = set(result.get("final", {}).get("ai_answer", []) or [])
    answer_resolution = result.get("pipeline", {}).get("answer_resolution", {})
    if not key and not ai:
        return {"status": "not_applicable", "disagreement_type": "", "reason": ""}
    if key == ai:
        status = str(answer_resolution.get("status", ""))
        if status and status != "ok":
            return {
                "status": "needs_review",
                "disagreement_type": "weak_convergence",
                "reason": f"答案一致但收敛依赖非直接证据: {status}",
            }
        return {"status": "passed", "disagreement_type": "", "reason": ""}

    option_rows = {
        str(row.get("option", "")).strip().upper(): row
        for row in result.get("pipeline", {}).get("explain_options", {}).get("option_analysis", [])
        if isinstance(row, dict)
    }
    missed = sorted(key - ai)
    extra = sorted(ai - key)
    missed_grades = [option_rows.get(label, {}).get("evidence_grade", "") for label in missed]
    extra_grades = [option_rows.get(label, {}).get("evidence_grade", "") for label in extra]
    if any(grade == "semantic_direct" for grade in missed_grades):
        dtype = "semantic_too_strict"
    elif any(grade == "direct_multi" for grade in missed_grades):
        dtype = "multi_card_underused"
    elif missed and extra:
        dtype = "focus_misdirected"
    elif missed:
        dtype = "missing_key_option"
    else:
        dtype = "extra_ai_option"
    reason_parts = []
    if missed:
        reason_parts.append(f"漏选题库项 {','.join(missed)}，对应证据等级 {','.join(missed_grades) or 'unknown'}")
    if extra:
        reason_parts.append(f"多选AI项 {','.join(extra)}，对应证据等级 {','.join(extra_grades) or 'unknown'}")
    return {
        "status": "needs_review",
        "disagreement_type": dtype,
        "reason": "；".join(reason_parts),
        "key_answer": sorted(key),
        "ai_answer": sorted(ai),
        "missed_key_options": missed,
        "extra_ai_options": extra,
    }


def needs_llm_disagreement_review(result: dict[str, Any]) -> bool:
    review = result.get("pipeline", {}).get("answer_disagreement_review", {})
    return review.get("status") == "needs_review" and bool(review.get("disagreement_type"))


def build_disagreement_review_prompt(result: dict[str, Any]) -> str:
    options = result.get("options", {})
    option_lines = "\n".join(f"{label}. {text}" for label, text in options.items())
    focus = result.get("pipeline", {}).get("question_focus", {})
    answer_resolution = result.get("pipeline", {}).get("answer_resolution", {})
    diagnostic = result.get("pipeline", {}).get("answer_disagreement_review", {})
    rows = []
    for row in result.get("pipeline", {}).get("explain_options", {}).get("option_analysis", []):
        card_lines = []
        for card in row.get("evidence_cards", []) or []:
            if not isinstance(card, dict):
                continue
            card_lines.append(
                f"- {card.get('card_id')} | {card.get('support_type')} | {card.get('relevance')}\n"
                f"  原文：{card.get('quote', '')}\n"
                f"  理由：{card.get('reason', '')}"
            )
        rows.append(
            f"选项{row.get('option')}: {row.get('option_text')}\n"
            f"判断：{row.get('judgement')} | evidence_status={row.get('evidence_status')} | "
            f"evidence_grade={row.get('evidence_grade')} | confidence={row.get('judgement_confidence')}\n"
            f"解析：{row.get('explanation', '')}\n"
            f"引用：\n" + ("\n".join(card_lines) if card_lines else "- 无")
        )
    return f"""你是CAMS题目-句卡绑定的后验质检二审员。

前面的盲判裁判和复核员没有看到题库答案。现在你可以看到题库答案，但你的任务不是无条件迎合题库答案，
而是判断分歧来自哪里，并给出是否应升级证据等级或保留人工复核的建议。

题干：
{result.get('stem', '')}

选项：
{option_lines}

题型：{result.get('question_type')} / {result.get('question_subtype')}
考点路由：{focus.get('question_focus_type')} | {focus.get('question_focus', '')}

题库答案：{','.join(normalize_answer(result.get('answer', ''), options))}
AI答案：{','.join(result.get('final', {}).get('ai_answer', []) or [])}
答案收敛：{json.dumps(answer_resolution, ensure_ascii=False)}
规则诊断：{json.dumps(diagnostic, ensure_ascii=False)}

选项证据：
{chr(10).join(rows)}

请输出严格JSON，不要Markdown：
{{
  "review_status": "confirm_ai/confirm_key/partial_key/needs_teacher_review",
  "disagreement_type": "semantic_too_strict/multi_card_underused/focus_misdirected/retrieval_gap/key_suspect/weak_convergence/other",
  "recommended_answer": ["A"],
  "confidence": "high/medium/low",
  "option_updates": [
    {{
      "option": "A",
      "suggested_judgement": "correct/incorrect/insufficient/needs_manual/unchanged",
      "suggested_evidence_grade": "direct_single/direct_multi/semantic_direct/indirect_context/negative_direct/none/needs_manual/unchanged",
      "reason": "为什么建议这样处理"
    }}
  ],
  "repair_action": {{
    "rerun_blind_pipeline": true,
    "repair_reason": "retrieval_gap/focus_misdirected/weak_convergence/none",
    "repair_mode": "broaden_recall/refocus_all_options/enable_followup/none",
    "reason": "如果需要回到盲判流程补跑，只说明检索/证据层面的原因，不要写标准答案应选哪项"
  }},
  "reason": "总体判断，说明题库答案为什么成立/不成立，或为什么需要人工复核",
  "teacher_review_required": true
}}

判断规则：
- 不要因为看到了题库答案就强行改成题库答案。
- 如果题库答案能由多张句卡组合直接推出，可建议 direct_multi。
- 如果教材表达与选项是考试语义等价，比如“风险增大/滋生”支持“增加”，可建议 semantic_direct。
- 如果 AI 被更具体但非题干考点的证据吸走，应标 focus_misdirected。
- 如果题库答案缺少候选句卡支持，应标 retrieval_gap 或 needs_teacher_review。
- 如果题库答案本身疑似不如 AI 答案合理，可标 key_suspect，但要谨慎。
- 如果需要重新检索，不要在 repair_action 里透露标准答案或推荐答案，只输出是否需要扩大召回/重新聚焦。"""


def apply_disagreement_review(result: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(review, dict) or not review:
        return result
    result.setdefault("pipeline", {})["answer_disagreement_llm_review"] = review
    updates = review.get("option_updates", [])
    if isinstance(updates, list):
        by_label = {
            str(item.get("option", "")).strip().upper(): item
            for item in updates
            if isinstance(item, dict)
        }
        for row in result.get("pipeline", {}).get("explain_options", {}).get("option_analysis", []):
            label = str(row.get("option", "")).strip().upper()
            update = by_label.get(label)
            if not update:
                continue
            grade = str(update.get("suggested_evidence_grade", "")).strip()
            judgement = str(update.get("suggested_judgement", "")).strip()
            if grade and grade != "unchanged":
                row["evidence_grade"] = grade
            if judgement and judgement != "unchanged":
                row["post_review_suggested_judgement"] = judgement
                row["judgement"] = judgement
                row["post_review_revised"] = True
                # Sync evidence_status for _direct_correct_labels to pick up
                if judgement == "correct":
                    row["evidence_status"] = "direct"
                elif judgement == "incorrect":
                    row["evidence_status"] = row.get("evidence_status") or "none"
            row["post_review_reason"] = str(update.get("reason", "")).strip()
    result["pipeline"]["answer_disagreement_review"] = {
        **result.get("pipeline", {}).get("answer_disagreement_review", {}),
        "llm_review_status": review.get("review_status", ""),
        "llm_disagreement_type": review.get("disagreement_type", ""),
        "llm_recommended_answer": review.get("recommended_answer", []),
        "llm_confidence": review.get("confidence", ""),
        "llm_reason": review.get("reason", ""),
        "llm_teacher_review_required": bool(review.get("teacher_review_required", True)),
    }
    return result


def run_disagreement_llm_review(
    client: Any,
    result: dict[str, Any],
    llm_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not needs_llm_disagreement_review(result):
        result.setdefault("pipeline", {})["answer_disagreement_llm_review"] = {"review_status": "skipped"}
        return result
    try:
        prompt = build_disagreement_review_prompt(result)
        raw, trace = call_llm_traced(client, "disagreement_reviewer", prompt, DISAGREEMENT_REVIEW_MAX_TOKENS)
        if llm_calls is not None:
            llm_calls.append(trace)
        parsed = agentic.parse_json_object(raw)
        parsed["raw_review_output"] = raw
        return apply_disagreement_review(result, parsed)
    except Exception as exc:
        result.setdefault("pipeline", {})["answer_disagreement_llm_review"] = {
            "review_status": "error",
            "error": str(exc)[:800],
        }
        return result


def collect_validation_checks(
    *,
    question: dict[str, Any],
    result: dict[str, Any],
    raw_adjudicator: str,
    evidence: list[dict[str, Any]],
    valid_card_ids: set[str],
) -> dict[str, Any]:
    options = question["options"]
    detected_answer = str(question.get("detected_answer") or question.get("answer") or "")
    finalized_answer = result.get("final", {}).get("ai_answer", [])
    option_analysis = result.get("pipeline", {}).get("explain_options", {}).get("option_analysis", [])
    checks: list[dict[str, str]] = []

    evidence_card_ids = {c.get("card_id") for c in evidence}
    raw_hallucinations: list[str] = []
    raw_outside: list[str] = []
    for row in option_analysis:
        for card in row.get("evidence_cards", []) or []:
            if not isinstance(card, dict):
                continue
            cid = card.get("card_id")
            if cid and cid not in valid_card_ids:
                raw_hallucinations.append(cid)
            if cid and cid not in evidence_card_ids:
                raw_outside.append(cid)

    if raw_hallucinations:
        checks.append(
            {
                "name": "引用句卡存在",
                "status": "fail",
                "detail": f"LLM编造了{len(raw_hallucinations)}个不存在的card_id: {','.join(raw_hallucinations[:5])}",
            }
        )
    else:
        checks.append({"name": "引用句卡存在", "status": "pass"})

    if raw_outside:
        checks.append(
            {
                "name": "引用在候选内",
                "status": "warning",
                "detail": f"LLM引用了{len(raw_outside)}个未检索到的card: {','.join(raw_outside[:3])}",
            }
        )
    else:
        checks.append({"name": "引用在候选内", "status": "pass"})

    leakage = blind.leakage_check({"raw": raw_adjudicator, "raw_search_plan": result["pipeline"]["retrieve_evidence"].get("raw_search_plan", "")})
    trace_leakage = [
        f"{call.get('stage')}:{','.join((call.get('blind_leakage_check') or {}).get('issues', []))}"
        for call in result.get("pipeline", {}).get("llm_calls", [])
        if (call.get("blind_leakage_check") or {}).get("status") == "fail"
    ]
    if leakage or trace_leakage:
        details = leakage + trace_leakage
        checks.append({"name": "盲判隔离", "status": "fail", "detail": "; ".join(details)})
    else:
        checks.append({"name": "盲判隔离", "status": "pass"})

    stem = question.get("stem", "")
    parse_warnings = question.get("parse_warnings", [])
    if not stem or len(stem) < 5:
        checks.append({"name": "题干完整性", "status": "fail", "detail": "题干过短或为空"})
    elif parse_warnings:
        checks.append({"name": "题干完整性", "status": "warning", "detail": "; ".join(map(str, parse_warnings))})
    else:
        checks.append({"name": "题干完整性", "status": "pass"})

    checks.append(
        {
            "name": "选项完整性",
            "status": "pass" if len(options) >= 2 else "fail",
            "detail": f"共{len(options)}个选项",
        }
    )

    final_set = set(finalized_answer)
    if not final_set:
        checks.append({"name": "AI答案范围", "status": "warning", "detail": "AI未给出参考答案"})
    elif final_set.issubset(set(options)):
        checks.append({"name": "AI答案范围", "status": "pass", "detail": f"预测答案: {','.join(sorted(final_set))}"})
    else:
        checks.append({"name": "AI答案范围", "status": "fail", "detail": f"预测答案{','.join(sorted(final_set))}不在选项中"})

    missing_explanations = [
        row.get("option", "?")
        for row in option_analysis
        if not str(row.get("explanation", "")).strip()
    ]
    if missing_explanations:
        checks.append({"name": "选项均有解析", "status": "warning", "detail": f"选项{','.join(missing_explanations)}缺少解析"})
    else:
        checks.append({"name": "选项均有解析", "status": "pass"})

    if not evidence:
        checks.append({"name": "检索结果", "status": "warning", "detail": "未检索到任何教材句卡"})

    answer_resolution = result.get("pipeline", {}).get("answer_resolution", {})
    resolution_status = str(answer_resolution.get("status", "")).strip()
    if resolution_status and resolution_status != "ok":
        checks.append(
            {
                "name": "答案收敛",
                "status": "warning",
                "detail": f"答案依赖非直接证据或需人工关注: {resolution_status}",
            }
        )

    disagreement = result.get("pipeline", {}).get("answer_disagreement_review", {})
    if disagreement.get("status") == "needs_review" and disagreement.get("disagreement_type"):
        checks.append(
            {
                "name": "答案分歧诊断",
                "status": "warning",
                "detail": f"{disagreement.get('disagreement_type')}: {disagreement.get('reason', '')}",
            }
        )
    llm_review = result.get("pipeline", {}).get("answer_disagreement_llm_review", {})
    if llm_review.get("review_status") and llm_review.get("review_status") not in {"skipped"}:
        status = "warning" if llm_review.get("review_status") in {"needs_teacher_review", "error"} else "pass"
        checks.append(
            {
                "name": "答案分歧二审",
                "status": status,
                "detail": f"{llm_review.get('review_status')}: {llm_review.get('reason', llm_review.get('error', ''))}",
            }
        )

    if detected_answer and final_set:
        detected = set(normalize_answer(detected_answer, options))
        if detected and detected != final_set:
            checks.append(
                {
                    "name": "答案对照提示",
                    "status": "warning",
                    "detail": f"AI参考答案({','.join(sorted(final_set))})与题库答案({','.join(sorted(detected))})不一致，请教研复核",
                }
            )

    statuses = [c["status"] for c in checks]
    validation_status = "needs_review" if ("fail" in statuses or "warning" in statuses) else "passed"
    return {"validation_status": validation_status, "checks": checks}


def refresh_result_validation(result: dict[str, Any]) -> dict[str, Any]:
    """Recompute lightweight validation for cached outputs."""
    result = enrich_option_grades(result)
    options = result.get("options", {})
    valid_card_ids = {
        item.get("card_id")
        for candidates in result.get("pipeline", {}).get("retrieve_evidence", {}).get("candidates_by_option", {}).values()
        for item in candidates
        if item.get("card_id")
    }
    valid_card_ids.update(
        card.get("card_id")
        for row in result.get("pipeline", {}).get("explain_options", {}).get("option_analysis", [])
        for card in row.get("evidence_cards", [])
        if isinstance(card, dict) and card.get("card_id")
    )
    evidence = result.get("pipeline", {}).get("retrieve_evidence", {}).get("evidence", [])
    if not isinstance(evidence, list):
        evidence = []
    question = {
        "stem": result.get("stem", ""),
        "options": options,
        "answer": result.get("answer", ""),
        "detected_answer": result.get("detected_answer", result.get("answer", "")),
        "parse_warnings": result.get("parse_warnings", []),
    }
    raw_outputs = result.get("pipeline", {}).get("judge_answer", {}).get("raw_adjudicator_outputs", [])
    raw_adjudicator = ""
    if raw_outputs and isinstance(raw_outputs[-1], dict):
        raw_adjudicator = str(raw_outputs[-1].get("raw", ""))
    result["pipeline"]["answer_disagreement_review"] = diagnose_answer_disagreement(result)
    result["pipeline"]["validate"] = collect_validation_checks(
        question=question,
        result=result,
        raw_adjudicator=raw_adjudicator,
        evidence=evidence,
        valid_card_ids=valid_card_ids,
    )
    result.setdefault("final", {})["needs_teacher_review"] = (
        result["pipeline"]["validate"]["validation_status"] != "passed"
    )
    return result


def refresh_cached_result(
    result: dict[str, Any],
    *,
    client: Any | None = None,
    run_llm_disagreement_review: bool = False,
) -> dict[str, Any]:
    result = refresh_result_validation(result)
    if run_llm_disagreement_review and client is not None:
        llm_calls = result.setdefault("pipeline", {}).setdefault("llm_calls", [])
        result = run_disagreement_llm_review(client, result, llm_calls)
        result = refresh_result_validation(result)
    return result


def should_repair_from_disagreement(result: dict[str, Any]) -> tuple[bool, str]:
    llm_review = result.get("pipeline", {}).get("answer_disagreement_llm_review", {})
    if not isinstance(llm_review, dict):
        return False, ""
    repair_action = llm_review.get("repair_action", {})
    if isinstance(repair_action, dict) and bool(repair_action.get("rerun_blind_pipeline")):
        reason = str(repair_action.get("repair_reason") or llm_review.get("disagreement_type") or "").strip()
        return True, reason or "repair_action"
    dtype = str(llm_review.get("disagreement_type", "") or "").strip()
    status = str(llm_review.get("review_status", "") or "").strip()
    if dtype in REPAIR_DISAGREEMENT_TYPES:
        return True, dtype
    if status == "needs_teacher_review" and dtype in {"retrieval_gap", "focus_misdirected"}:
        return True, dtype
    return False, ""



def run_question_with_optional_blind_repair(
    rt: agentic.AgenticRuntime,
    question: dict[str, Any],
    *,
    top_k: int,
    max_followups: int,
    reviewer: bool,
    disagreement_reviewer: bool,
    kg: KGRecallRuntime | None,
    kg_node_top_k: int,
    kg_max_cards_per_option: int,
    kg_neighbor_limit: int,
    kg_node_score_threshold: float,
    repair_disagreements: bool,
    repair_max_rounds: int,
    repair_top_k: int,
    repair_max_followups: int,
    repair_kg_node_top_k: int,
    repair_kg_max_cards_per_option: int,
    repair_kg_neighbor_limit: int,
    repair_kg_node_score_threshold: float,
    use_card_expansion: bool = True,
    use_enrichment: bool = True,
    use_cross_encoder: bool = True,
    use_llm_rerank: bool = True,
    cross_encoder_url: str = CROSS_ENCODER_URL,
    use_parent_replace: bool = True,
    use_mmr: bool = True,
    mmr_lambda: float = 0.7,
) -> dict[str, Any]:
    result = run_question_core(
        rt,
        question,
        top_k=top_k,
        max_followups=max_followups,
        reviewer=reviewer,
        disagreement_reviewer=disagreement_reviewer,
        kg=kg,
        kg_node_top_k=kg_node_top_k,
        kg_max_cards_per_option=kg_max_cards_per_option,
        kg_neighbor_limit=kg_neighbor_limit,
        kg_node_score_threshold=kg_node_score_threshold,
        use_card_expansion=use_card_expansion,
        use_enrichment=use_enrichment,
        use_cross_encoder=use_cross_encoder,
        use_llm_rerank=use_llm_rerank,
        cross_encoder_url=cross_encoder_url,
        use_parent_replace=use_parent_replace,
        use_mmr=use_mmr,
        mmr_lambda=mmr_lambda,
    )
    if not repair_disagreements or not disagreement_reviewer or repair_max_rounds <= 0:
        return result

    repair_history: list[dict[str, Any]] = []
    current = result
    for repair_round in range(1, repair_max_rounds + 1):
        should_repair, repair_reason = should_repair_from_disagreement(current)
        if not should_repair:
            break
        first_pipeline = current.get("pipeline", {})
        repair_history.append(
            {
                "round": repair_round,
                "trigger_reason": repair_reason,
                "previous_ai_answer": current.get("final", {}).get("ai_answer", []),
                "previous_validation_status": first_pipeline.get("validate", {}).get("validation_status", ""),
                "previous_llm_disagreement_type": first_pipeline.get("answer_disagreement_llm_review", {}).get("disagreement_type", ""),
                "mode": "blind_rerun_broaden_recall",
                "leakage_guard": "standard answer is not passed to planner/adjudicator/reviewer during repair",
            }
        )
        repaired = run_question_core(
            rt,
            question,
            top_k=max(top_k, repair_top_k),
            max_followups=max(max_followups, repair_max_followups),
            reviewer=reviewer,
            disagreement_reviewer=disagreement_reviewer,
            kg=kg,
            kg_node_top_k=max(kg_node_top_k, repair_kg_node_top_k),
            kg_max_cards_per_option=max(kg_max_cards_per_option, repair_kg_max_cards_per_option),
            kg_neighbor_limit=max(kg_neighbor_limit, repair_kg_neighbor_limit),
            kg_node_score_threshold=min(kg_node_score_threshold, repair_kg_node_score_threshold),
            use_card_expansion=use_card_expansion,
            use_enrichment=use_enrichment,
            use_cross_encoder=use_cross_encoder,
            use_llm_rerank=use_llm_rerank,
            cross_encoder_url=cross_encoder_url,
            use_parent_replace=use_parent_replace,
            use_mmr=use_mmr,
            mmr_lambda=mmr_lambda,
        )
        repaired.setdefault("pipeline", {})["blind_repair"] = {
            "enabled": True,
            "rounds_used": repair_round,
            "history": repair_history,
            "final_status": repaired.get("status", ""),
        }
        current = repaired
    if repair_history:
        current.setdefault("pipeline", {}).setdefault("blind_repair", {})["history"] = repair_history
    return current


def run_question_core(
    rt: agentic.AgenticRuntime,
    question: dict[str, Any],
    *,
    top_k: int,
    max_followups: int,
    reviewer: bool,
    disagreement_reviewer: bool,
    kg: KGRecallRuntime | None,
    kg_node_top_k: int,
    kg_max_cards_per_option: int,
    kg_neighbor_limit: int,
    kg_node_score_threshold: float,
    # P0/P1/P2 feature flags
    use_card_expansion: bool = True,
    use_enrichment: bool = True,
    use_cross_encoder: bool = True,
    use_llm_rerank: bool = True,
    cross_encoder_url: str = CROSS_ENCODER_URL,
    use_parent_replace: bool = True,
    use_mmr: bool = True,
    mmr_lambda: float = 0.7,
) -> dict[str, Any]:
    client = rt.base.client
    question = normalize_question(question, client)
    qid = str(question.get("id") or "").strip()
    stem = question["stem"]
    options = question["options"]
    question_type = str(question.get("question_type", "unknown"))
    question_subtype = str(question.get("question_subtype", "unknown"))
    llm_calls: list[dict[str, Any]] = []
    model_plan = llm_stage_summary()

    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "question_id": qid,
        "section": question.get("section", ""),
        "number": question.get("number"),
        "stem": stem,
        "options": options,
        "answer": question.get("answer", ""),
        "detected_answer": question.get("detected_answer", ""),
        "question_type": question_type,
        "question_subtype": question_subtype,
        "status": "started",
        "model": model_plan["adjudicator"]["model"],
        "model_field_note": "legacy compatibility field; use effective_model_plan/llm_stage_models for actual per-stage calls",
        "effective_model_plan": model_plan,
        "evidence_scope": rt.base.evidence_scope,
        "evidence_file": rt.base.evidence_file,
        "source_module": str(SOURCE_MODULE),
        "created_at": _dt.datetime.now().isoformat(),
        "pipeline": {"llm_calls": llm_calls},
    }

    if not stem or len(options) < 2:
        result["status"] = "parse_failed"
        result["pipeline"]["parse_question"] = question.get("parse_question", {})
        result["final"] = {"ai_answer": [], "confidence": "insufficient", "evidence_cards": [], "needs_teacher_review": True}
        return result

    # Candidate cache: load precomputed retrieval+CE results if available.
    _cache_path = CANDIDATE_CACHE_DIR / f"{qid}.pkl" if qid else None
    _from_cache = False
    if _cache_path and _cache_path.exists():
        try:
            with _cache_path.open("rb") as _f:
                _cached = pickle.load(_f)
            if isinstance(_cached, dict) and _cached.get("scope") == rt.base.evidence_scope:
                candidates = _cached["candidates"]
                diagnostics = _cached.get("diagnostics", {})
                _from_cache = True
        except Exception:
            pass

    if not _from_cache:
        # Retrieval: single query, union-based, shared candidates (WeKnora CHUNK_SEARCH_PARALLEL).
        candidates, diagnostics = retrieve_for_question(
        rt,
        stem,
        options,
        top_k=top_k,
        kg=kg,
        kg_node_top_k=kg_node_top_k,
        kg_max_cards_per_option=kg_max_cards_per_option,
        kg_neighbor_limit=kg_neighbor_limit,
        kg_node_score_threshold=kg_node_score_threshold,
        use_card_expansion=use_card_expansion,
        use_enrichment=use_enrichment,
        use_cross_encoder=use_cross_encoder,
        use_llm_rerank=use_llm_rerank,
        cross_encoder_url=cross_encoder_url,
        use_parent_replace=use_parent_replace,
        use_mmr=use_mmr,
        mmr_lambda=mmr_lambda,
    )

    # Save candidate cache for later adjudicate-only runs
    if qid and not _from_cache:
        CANDIDATE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_data = {
            "scope": rt.base.evidence_scope,
            "qid": qid,
            "candidates": candidates,
            "diagnostics": diagnostics,
        }
        try:
            with open(CANDIDATE_CACHE_DIR / f"{qid}.pkl", "wb") as _f:
                pickle.dump(_cache_data, _f)
        except Exception:
            pass

    # All options share the same candidate pool (WeKnora: no per-option retrieval).
    candidates_by_option: dict[str, list[dict[str, Any]]] = {
        label: list(candidates) for label in options
    }
    evidence = agentic.flatten_evidence(candidates_by_option)

    result["pipeline"]["retrieve_evidence"] = {
        "search_method": "cached" if _from_cache else "union_search",
        "candidates_by_option": {
            label: [{k: v for k, v in item.items() if k != "text"} for item in candidates]
            for label, candidates in candidates_by_option.items()
        },
        "evidence": evidence,
        "evidence_count": len(evidence),
        "diagnostics": diagnostics,
        "kg_recall": {
            "enabled": kg is not None,
            "work_dir": str(kg.work_dir) if kg is not None else "",
            "source_stats": kg.source_stats if kg is not None else {},
            "node_count": len(kg.node_ids) if kg is not None else 0,
            "mounted_node_count": len(kg.node_cards) if kg is not None else 0,
        },
    }
    result["pipeline"]["question_focus"] = {
        "question_focus": stem,
        "question_focus_type": infer_focus_type(stem, options),
    }

    # AI #2: blind evidence adjudicator (simplified — no plan dependency).
    raw_adjudicator = ""
    parsed: dict[str, Any] | None = None
    raw_outputs: list[dict[str, Any]] = []
    for round_index in range(1, max_followups + 2):
        try:
            adjudicator_prompt = build_adjudicator_prompt(
                stem, options, candidates_for_adjudicator_prompt(candidates_by_option, rt),
            )
            raw_adjudicator, trace = call_llm_traced(client, "adjudicator", adjudicator_prompt, max_tokens=9000)
            llm_calls.append(trace)
            parsed = agentic.parse_json_object(raw_adjudicator)
        except Exception as exc:
            result["adjudicator_error"] = str(exc)[:500]
            parsed = None
        raw_outputs.append({"round": round_index, "raw": raw_adjudicator, "parsed_ok": parsed is not None})
        if round_index > max_followups:
            break
        queries_by_option = agentic.followup_queries(parsed, options)
        if not queries_by_option:
            break
        for label, queries in queries_by_option.items():
            query_plan = {"search_queries": queries, "must_terms": agentic.extract_phrases(options[label], " ".join(queries))}
            extra, _, extra_rankings = agentic.retrieve_for_option(
                rt, stem, options[label], query_plan,
                top_k=top_k, return_source_rankings=True,
            )
            rrf_extra = rrf_fuse(extra_rankings)
            extra_candidates = merge_rrf_with_append(rrf_extra, extra_rankings, rt.card_by_id)
            candidates_by_option[label] = merge_candidate_lists(
                candidates_by_option[label], extra_candidates, top_k=top_k,
            )
            if "search_rounds" not in result["pipeline"]["retrieve_evidence"]:
                result["pipeline"]["retrieve_evidence"]["search_rounds"] = []
            result["pipeline"]["retrieve_evidence"]["search_rounds"].append(
                {"round": round_index + 1, "option": label, "followup_queries": queries,
                 "candidate_ids": [c["card_id"] for c in extra_candidates]})
        evidence = agentic.flatten_evidence(candidates_by_option)
        result["pipeline"]["retrieve_evidence"]["evidence"] = evidence
        result["pipeline"]["retrieve_evidence"]["evidence_count"] = len(evidence)

    option_analysis = parsed.get("option_analysis", []) if parsed else []
    if not isinstance(option_analysis, list) or not option_analysis:
        option_analysis = nq._build_insufficient_options(options)

    predicted_answer = parsed.get("predicted_answer", []) if parsed else []
    if not isinstance(predicted_answer, list):
        predicted_answer = []
    predicted_confidence = parsed.get("predicted_answer_confidence", "insufficient") if parsed else "insufficient"
    overall_notes = parsed.get("overall_notes", "") if parsed else ""

    result["pipeline"]["judge_answer"] = {
        "raw_adjudicator_outputs": raw_outputs,
        "predicted_answer": predicted_answer,
        "predicted_answer_confidence": predicted_confidence,
        "overall_notes": overall_notes,
    }

    temp = {"options": options, "answer": "", "option_analysis": option_analysis, "evidence": evidence}
    blind.sanitize_blind_result(temp, options)
    temp["option_analysis"] = restore_original_evidence_quotes(
        temp.get("option_analysis", []),
        candidates_by_option,
    )
    sanitized_leakage = blind.leakage_check(temp)

    # AI #3: narrow answer/evidence reviewer.
    review_result = {"applied": False, "review_status": "skipped"}
    if reviewer:
        review_result = nq._review_answer_with_llm(
            client=client,
            stem=stem,
            options=options,
            question_type=question_type,
            question_subtype=question_subtype,
            predicted_answer=predicted_answer,
            option_analysis=temp.get("option_analysis", []),
            llm_calls=llm_calls,
        )
        if review_result.get("applied"):
            temp["option_analysis"] = review_result.get("option_analysis", temp.get("option_analysis", []))
            temp["option_analysis"] = restore_original_evidence_quotes(
                temp.get("option_analysis", []),
                candidates_by_option,
            )
            reviewed = review_result.get("reviewed_answer")
            if reviewed:
                predicted_answer = reviewed
            review_confidence = review_result.get("review_confidence")
            if review_confidence and review_confidence != "unchanged":
                predicted_confidence = review_confidence

    result["pipeline"]["review_answer"] = review_result

    # rule_review disabled: the entailment guard uses string-match heuristics
    # that frequently downgrade correct LLM judgements (e.g. "前台公司" vs "空壳公司").
    rule_review = {"applied": False}
    result["pipeline"]["rule_review"] = rule_review

    focus_type = result["pipeline"].get("question_focus", {}).get("question_focus_type", infer_focus_type(stem, options))
    for row in temp.get("option_analysis", []):
        if isinstance(row, dict):
            row["evidence_grade"] = normalize_evidence_grade(row, focus_type)
            row["focus_type"] = focus_type

    answer_resolution = nq._finalize_answer_by_type(
        predicted_answer=predicted_answer,
        option_analysis=temp.get("option_analysis", []),
        question_type=question_type,
        question_subtype=question_subtype,
        options=options,
    )
    finalized_answer = answer_resolution["answer"]
    # Flag questions for manual review when evidence is structurally absent.
    _all_judgements = {row.get("judgement", "") for row in temp.get("option_analysis", []) if isinstance(row, dict)}
    _has_key = bool(str(question.get("answer", "") or "").strip())
    _is_tf = len(options) == 2
    _review_reason = ""
    if _is_tf and not _has_key:
        _review_reason = "判断题题库未标注答案，需人工判定"
    elif not _all_judgements or _all_judgements.issubset({"insufficient", "needs_manual", "conflict"}):
        _review_reason = "所有选项均无充分教材证据，需人工查证教材原文"
    if _review_reason:
        for row in temp.get("option_analysis", []):
            if isinstance(row, dict):
                row["needs_teacher_review"] = True
                if not row.get("teacher_review_reason"):
                    row["teacher_review_reason"] = _review_reason
    cited_cards = sorted(
        {
            card.get("card_id", "")
            for row in temp.get("option_analysis", [])
            for card in row.get("evidence_cards", [])
            if card.get("card_id")
        }
    )

    result["pipeline"]["explain_options"] = {
        "option_analysis": temp.get("option_analysis", []),
        "cited_cards": cited_cards,
        "leakage_issues": sanitized_leakage,
    }
    result["pipeline"]["answer_resolution"] = answer_resolution
    result["final"] = {
        "ai_answer": finalized_answer,
        "confidence": predicted_confidence,
        "answer_resolution": answer_resolution,
        "option_explanations": temp.get("option_analysis", []),
        "evidence_cards": cited_cards,
        "needs_teacher_review": True,
        "overall_notes": overall_notes,
    }
    result["pipeline"]["answer_disagreement_review"] = diagnose_answer_disagreement(result)
    if disagreement_reviewer:
        result = run_disagreement_llm_review(client, result, llm_calls)
        # Re-finalize answer when LLM review revised option judgements
        if any(
            row.get("post_review_revised")
            for row in result.get("pipeline", {}).get("explain_options", {}).get("option_analysis", [])
            if isinstance(row, dict)
        ):
            revised_analysis = result["pipeline"]["explain_options"]["option_analysis"]
            answer_resolution = nq._finalize_answer_by_type(
                predicted_answer=predicted_answer,
                option_analysis=revised_analysis,
                question_type=question_type,
                question_subtype=question_subtype,
                options=options,
            )
            result["pipeline"]["answer_resolution"] = answer_resolution
            result["final"]["ai_answer"] = answer_resolution["answer"]
    else:
        result["pipeline"]["answer_disagreement_llm_review"] = {"review_status": "skipped"}

    # Plan B: answer-informed evidence location when AI ≠ key
    answer_key = str(question.get("answer", "") or "").strip()
    ai_answer = result["final"].get("ai_answer", []) or []
    if _use_plan_b and answer_key and ai_answer:
        key_labels = nq._normalize_answer_labels(answer_key, options)
        ai_labels = list(ai_answer)
        if sorted(key_labels) != sorted(ai_labels):
            try:
                plan_b_result = plan_b_module.run_plan_b(
                    rt=rt, kg=kg, client=client,
                    stem=stem, options=options,
                    answer_key=answer_key,
                    candidates=candidates,
                    option_analysis=result.get("pipeline", {}).get("explain_options", {}).get("option_analysis", []),
                    final_ai_answer=ai_labels,
                    top_k=top_k,
                )
                result["pipeline"]["plan_b"] = plan_b_result
            except Exception as exc:
                result["pipeline"]["plan_b"] = {
                    "applied": False, "status": "error",
                    "error": str(exc)[:500],
                }

    result["pipeline"]["validate"] = collect_validation_checks(
        question=question,
        result=result,
        raw_adjudicator=raw_adjudicator,
        evidence=evidence,
        valid_card_ids=rt.base.valid_card_ids,
    )
    result["final"]["needs_teacher_review"] = result["pipeline"]["validate"]["validation_status"] != "passed"
    result["status"] = "done"
    return result


def binding_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    final_answer = set(result.get("final", {}).get("ai_answer", []) or [])
    key_answer = set(normalize_answer(result.get("answer", ""), result.get("options", {})))
    candidates_by_option = result.get("pipeline", {}).get("retrieve_evidence", {}).get("candidates_by_option", {})
    final_needs_review = result.get("final", {}).get("needs_teacher_review", True)
    validation_status = result.get("pipeline", {}).get("validate", {}).get("validation_status", "")
    focus_type = result.get("pipeline", {}).get("question_focus", {}).get("question_focus_type", "")
    disagreement = result.get("pipeline", {}).get("answer_disagreement_review", {})
    disagreement_llm = result.get("pipeline", {}).get("answer_disagreement_llm_review", {})
    plan_b = result.get("pipeline", {}).get("plan_b", {})
    plan_b_by_option: dict[str, dict[str, Any]] = {}
    if isinstance(plan_b, dict) and plan_b.get("applied"):
        for pb_row in (plan_b.get("option_analysis") or []):
            if isinstance(pb_row, dict) and pb_row.get("option"):
                plan_b_by_option[str(pb_row["option"]).strip().upper()] = pb_row
    for option in result.get("pipeline", {}).get("explain_options", {}).get("option_analysis", []):
        label = str(option.get("option", "")).strip()
        candidate_ids = [
            item.get("card_id")
            for item in candidates_by_option.get(label, [])
            if item.get("card_id")
        ]
        evidence_card_ids = [
            card.get("card_id")
            for card in option.get("evidence_cards", [])
            if card.get("card_id")
        ]
        binding_card_ids = merge_binding_card_ids(evidence_card_ids, candidate_ids)
        evidence_set = set(evidence_card_ids)
        relation_strengths = [
            {
                "card_id": cid,
                "strength": "strong_evidence" if cid in evidence_set else "weak_candidate",
                "source_field": "evidence_card_ids" if cid in evidence_set else "candidate_card_ids",
            }
            for cid in binding_card_ids
        ]
        teacher_review_reason = str(option.get("teacher_review_reason", "")).strip()
        option_needs_review = bool(option.get("needs_teacher_review")) or bool(final_needs_review)
        if validation_status == "passed" and teacher_review_reason == REVIEW_ADJUSTMENT_REASON:
            option_needs_review = False
            teacher_review_reason = ""
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "question_id": result.get("question_id", ""),
                "section": result.get("section", ""),
                "option": label,
                "option_text": option.get("option_text", ""),
                "key_is_correct": label in key_answer if key_answer else None,
                "ai_is_correct": label in final_answer,
                "judgement": option.get("judgement", ""),
                "judgement_confidence": option.get("judgement_confidence", ""),
                "evidence_status": option.get("evidence_status", ""),
                "evidence_grade": option.get("evidence_grade", ""),
                "focus_type": option.get("focus_type", focus_type),
                "card_ids": binding_card_ids,
                "card_id_semantics": {
                    "evidence_card_ids": FIELD_NOTES["evidence_card_ids"],
                    "candidate_card_ids": FIELD_NOTES["candidate_card_ids"],
                    "card_ids": FIELD_NOTES["card_ids"],
                },
                "relation_strengths": relation_strengths,
                "evidence_card_ids": evidence_card_ids,
                "evidence_cards": option.get("evidence_cards", []),
                "candidate_card_ids": candidate_ids,
                "needs_teacher_review": option_needs_review,
                "teacher_review_reason": teacher_review_reason,
                "validation_status": validation_status,
                "disagreement_type": disagreement.get("disagreement_type", ""),
                "disagreement_reason": disagreement.get("reason", ""),
                "disagreement_llm_status": disagreement_llm.get("review_status", ""),
                "disagreement_llm_type": disagreement_llm.get("disagreement_type", ""),
                "disagreement_llm_recommended_answer": disagreement_llm.get("recommended_answer", []),
                "disagreement_llm_reason": disagreement_llm.get("reason", ""),
                "post_review_suggested_judgement": option.get("post_review_suggested_judgement", ""),
                "post_review_reason": option.get("post_review_reason", ""),
                "plan_b_applied": bool(plan_b.get("applied")),
                "plan_b_evidence_found": plan_b.get("evidence_found"),
                "plan_b_recommend_override": plan_b.get("recommend_override", []),
                "plan_b_judgement": plan_b_by_option.get(label, {}).get("plan_b_judgement", ""),
                "plan_b_evidence_status": plan_b_by_option.get(label, {}).get("evidence_status", ""),
                "plan_b_evidence_cards": plan_b_by_option.get(label, {}).get("evidence_cards", []),
                "plan_b_new_card_ids": plan_b_by_option.get(label, {}).get("new_card_ids", []),
                "plan_b_still_insufficient": plan_b.get("still_insufficient_options", []),
                "plan_b_overall_notes": plan_b.get("overall_notes", ""),
                "model": (result.get("effective_model_plan") or llm_stage_summary()).get("adjudicator", {}).get("model", ""),
                "effective_model_plan": result.get("effective_model_plan") or llm_stage_summary(),
                "evidence_scope": result.get("evidence_scope", ""),
                "evidence_file": result.get("evidence_file", ""),
            }
        )
    return rows


def merge_binding_card_ids(evidence_card_ids: list[str], candidate_card_ids: list[str]) -> list[str]:
    """Keep final relation bindings broader than strict evidence citations.

    evidence_card_ids are the cards the adjudicator/reviewer explicitly cited.
    candidate_card_ids are high-ranking retrieval candidates for this option.
    The formal relation layer should preserve both: cited evidence first, then
    enough nearby/high-score candidates for teacher review and downstream use.
    """
    merged: list[str] = []
    seen: set[str] = set()
    for cid in evidence_card_ids + candidate_card_ids:
        if not cid or cid in seen:
            continue
        seen.add(cid)
        merged.append(cid)
        if len(merged) >= MAX_BINDING_CARDS_PER_OPTION:
            break
    return merged


def kg_card_candidate(
    *,
    card: dict[str, Any],
    node: dict[str, Any],
    card_by_id: dict[str, dict[str, Any]],
    score: float,
    source: str,
    query: str,
    edge: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    cid = str(card.get("card_id", "")).strip()
    base_card = card_by_id.get(cid)
    if not base_card:
        return None
    row = {
        "card_id": cid,
        "score": round(score, 4),
        "source": source,
        "sources": [
            {
                "source": source,
                "score": round(score, 4),
                "query": agentic.compact_text(query, 120),
                "kg_node_id": node.get("node_id", ""),
                "kg_node_title": node.get("title", ""),
                "kg_mount_method": card.get("method", ""),
                "kg_mount_score": card.get("score", 0),
                "kg_mount_decision": card.get("decision", ""),
            }
        ],
        "type": base_card.get("type", ""),
        "knowledge": base_card.get("knowledge", ""),
        "citation": base_card.get("citation", ""),
        "context_before": base_card.get("context_before", ""),
        "context_after": base_card.get("context_after", ""),
        "text": agentic.card_text(base_card),
    }
    if edge:
        row["sources"][0]["kg_edge_id"] = edge.get("edge_id", "")
        row["sources"][0]["kg_edge_type"] = edge.get("type", "")
        row["sources"][0]["kg_edge_source"] = edge.get("source", "")
    return row



def kg_recall_for_option(
    *,
    kg: KGRecallRuntime,
    rt: agentic.AgenticRuntime,
    stem: str,
    option_text: str,
    option_plan: dict[str, Any],
    top_k_nodes: int,
    max_cards: int,
    neighbor_limit: int,
    threshold: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    query_parts = [
        stem,
        option_text,
        option_plan.get("option_claim", ""),
        option_plan.get("evidence_need", ""),
        " ".join(option_plan.get("must_terms", []) or []),
        " ".join(option_plan.get("related_terms", []) or []),
        " ".join((option_plan.get("search_queries", []) or [])[:3]),
    ]
    query = agentic.compact_text(" ".join(str(part) for part in query_parts if str(part or "").strip()), 600)
    if not query:
        return [], {"enabled": True, "candidate_count": 0, "node_hits": []}

    q_vec = rt.base.bge.encode([query], normalize_embeddings=True)
    scores = (q_vec @ kg.node_vecs.T).flatten()
    node_hits: list[tuple[str, float]] = []
    for idx in list(reversed(scores.argsort()))[: max(top_k_nodes * 3, top_k_nodes)]:
        score = float(scores[idx])
        if score < threshold:
            continue
        node_hits.append((kg.node_ids[idx], score))
        if len(node_hits) >= top_k_nodes:
            break

    bucket: dict[str, dict[str, Any]] = {}
    selected_nodes: list[dict[str, Any]] = []

    def add_from_node(node_id: str, node_score: float, source: str, edge: dict[str, Any] | None = None) -> None:
        node = kg.nodes.get(node_id)
        if not node:
            return
        selected_nodes.append(
            {
                "node_id": node_id,
                "title": node.get("title", ""),
                "node_type": node.get("node_type", ""),
                "score": round(node_score, 4),
                "source": source,
                "edge_id": edge.get("edge_id", "") if edge else "",
                "edge_type": edge.get("type", "") if edge else "",
            }
        )
        for mount in sorted(kg.node_cards.get(node_id, []), key=lambda row: row.get("score", 0), reverse=True)[:max_cards]:
            raw_factor = 0.72 if mount.get("source") == "kg_mount_raw" else 1.0
            candidate = kg_card_candidate(
                card=mount,
                node=node,
                card_by_id=rt.card_by_id,
                score=(node_score * 5.0 + float(mount.get("score", 0)) * 2.0) * raw_factor,
                source=source if mount.get("source") != "kg_mount_raw" else f"{source}_raw",
                query=query,
                edge=edge,
            )
            if not candidate:
                continue
            cid = candidate["card_id"]
            if cid in bucket:
                bucket[cid]["score"] = round(float(bucket[cid].get("score", 0)) + float(candidate["score"]) * 0.35, 4)
                bucket[cid].setdefault("sources", []).extend(candidate.get("sources", []))
                if candidate.get("source") not in str(bucket[cid].get("source", "")).split("+"):
                    bucket[cid]["source"] = f"{bucket[cid].get('source', '')}+{candidate.get('source', '')}".strip("+")
            else:
                bucket[cid] = candidate

    for node_id, node_score in node_hits:
        add_from_node(node_id, node_score, "kg_mount")
        for edge in sorted(
            kg.neighbors.get(node_id, []),
            key=lambda row: float(row.get("strength") or 0) if str(row.get("strength", "")).replace(".", "", 1).isdigit() else 0,
            reverse=True,
        )[:neighbor_limit]:
            neighbor_id = edge.get("node_id", "")
            neighbor_score = node_score * (0.82 if edge.get("source") == "hidden" else 0.9)
            add_from_node(neighbor_id, neighbor_score, "kg_neighbor", edge=edge)

    candidates = sorted(bucket.values(), key=lambda row: row.get("score", 0), reverse=True)[:max_cards]
    diagnostics = {
        "enabled": True,
        "query": query,
        "node_hits": selected_nodes[: top_k_nodes + top_k_nodes * neighbor_limit],
        "candidate_count": len(candidates),
        "candidate_ids": [item.get("card_id") for item in candidates],
    }
    return candidates, diagnostics


def kg_recall_summary(
    kg: KGRecallRuntime | None,
    *,
    requested: bool,
    work_dir: Path,
    node_top_k: int,
    max_cards_per_option: int,
    neighbor_limit: int,
    node_score_threshold: float,
) -> dict[str, Any]:
    return {
        "requested": requested,
        "enabled": kg is not None,
        "work_dir": str(kg.work_dir if kg is not None else work_dir),
        "node_top_k": node_top_k,
        "max_cards_per_option": max_cards_per_option,
        "neighbor_limit": neighbor_limit,
        "node_score_threshold": node_score_threshold,
        "node_count": len(kg.node_ids) if kg is not None else 0,
        "mounted_node_count": len(kg.node_cards) if kg is not None else 0,
        "source_stats": kg.source_stats if kg is not None else {},
    }




def merge_candidate_lists(*candidate_lists: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for candidates in candidate_lists:
        for item in candidates:
            cid = item.get("card_id")
            if not cid:
                continue
            if cid not in merged:
                merged[cid] = dict(item)
                merged[cid]["sources"] = list(item.get("sources", []) or [])
                merged[cid]["retrieval_types"] = list(item.get("retrieval_types", []) or [])
                continue
            row = merged[cid]
            row["score"] = round(float(row.get("score", 0)) + float(item.get("score", 0)) * 0.45, 4)
            row.setdefault("sources", []).extend(item.get("sources", []) or [])
            for source in str(item.get("source", "")).split("+"):
                if source and source not in str(row.get("source", "")).split("+"):
                    row["source"] = f"{row.get('source', '')}+{source}".strip("+")
            types = list(row.get("retrieval_types", []) or [])
            for typ in item.get("retrieval_types", []) or []:
                if typ not in types:
                    types.append(typ)
            row["retrieval_types"] = types
    return sorted(merged.values(), key=lambda row: row.get("score", 0), reverse=True)[:top_k]


def build_adjudicator_prompt(
    stem: str,
    options: dict[str, str],
    candidates_by_option: dict[str, list[dict[str, Any]]],
) -> str:
    """Simplified blind adjudicator prompt — no planner dependency (WeKnora-aligned).

    WeKnora has no LLM planner; the adjudicator sees only stem, options, and
    shared candidate cards. No "检索规划摘要" section.
    """
    opt_text = "\n".join(f"{label}. {text}" for label, text in options.items())
    # Shared candidate pool (WeKnora: no per-option retrieval) — format once.
    shared_candidates = next(iter(candidates_by_option.values()), [])
    candidate_text = agentic.format_candidate_block("", shared_candidates, max_cards=30)
    candidate_text = candidate_text.replace("### 选项  候选教材句卡", "### 候选教材句卡（所有选项共享）")
    candidate_text = candidate_text[:agentic.MAX_CANDIDATE_TEXT_CHARS]

    return f"""你是CAMS选项级证据裁判和解析员。

你只能看到题目、选项和候选教材句卡；你看不到标准答案，也看不到题库解析。

严禁：
1. 不要写"标准答案是"或"根据标准答案"。
2. 不要使用任何未提供的题库解析。
3. evidence_cards 只能引用下方候选教材句卡中出现过的 card_id。
4. direct 必须非常严格：句卡能直接判断选项关键事实。
5. 如果无法仅凭教材句卡判断，judgement 填 insufficient 或 needs_manual。
6. 教材术语：前台公司=空壳公司=壳公司=shell company。这几个词是同义词。

题目：{stem}
选项：
{opt_text}

候选教材句卡（所有选项共享同一候选池）：
{candidate_text}

输出严格JSON，不要Markdown，不要代码块：
{{
  "predicted_answer": ["A"],
  "predicted_answer_confidence": "high/medium/low/insufficient",
  "option_analysis": [
    {{
      "option": "A",
      "option_text": "选项全文",
      "judgement": "correct/incorrect/insufficient/needs_manual",
      "judgement_confidence": "high/medium/low/insufficient",
      "evidence_status": "direct/indirect/none/conflict/needs_manual",
      "evidence_cards": [
        {{
          "card_id": "v6_bXX_NXX",
          "support_type": "direct/indirect/context/negative",
          "source": "card_bge/bm25/exact_phrase/adjacent_card/relation_expand",
          "quote": "教材原文短摘，不超过120字",
          "reason": "为什么这张句卡能支撑或反驳该选项",
          "relevance": "high/medium/low"
        }}
      ],
      "explanation": "只基于题目、选项和教材句卡写为什么该选项更可能正确/错误；证据不足时明说不足。",
      "common_trap": "学生容易误解之处，无法推断则填空",
      "needs_teacher_review": false,
      "teacher_review_reason": ""
    }}
  ],
  "overall_notes": "整体证据质量说明",
  "cited_cards": ["v6_bXX_NXX"]
}}

必须逐一分析所有选项，共 {len(options)} 个。"""


def candidates_for_adjudicator_prompt(
    candidates_by_option: dict[str, list[dict[str, Any]]],
    rt: Any = None,
) -> dict[str, list[dict[str, Any]]]:
    """Return prompt-ready candidates with short neighbour context.

    Single-sentence citations (often < 100 chars) lack the surrounding paragraph
    context that the adjudicator needs to connect terminology variants (e.g.
    "欺诈" vs "诉讼").  When the expanded_text is a full parent block (too long)
    or absent, pull the immediate prev/next sibling citations along the card
    adjacency chain to build a compact ~300-500 char snippet.
    """
    prompt_candidates: dict[str, list[dict[str, Any]]] = {}
    for label, candidates in candidates_by_option.items():
        rows: list[dict[str, Any]] = []
        for candidate in candidates:
            row = dict(candidate)
            expanded = str(row.get("expanded_text", "") or "").strip()
            citation = str(row.get("citation", "") or "").strip()
            if expanded and expanded != citation and len(expanded) < 1200:
                row["citation"] = expanded
            elif citation:
                # Build compact neighbour context from sibling chain
                cid = row.get("card_id", "")
                if _card_adjacency and cid in _card_adjacency and rt is not None:
                    parts = []
                    cursor = _card_adjacency[cid].get("prev")
                    if cursor and cursor in rt.card_by_id:
                        parts.append(rt.card_by_id[cursor].get("citation", ""))
                    parts.append(citation)
                    cursor = _card_adjacency[cid].get("next")
                    if cursor and cursor in rt.card_by_id:
                        parts.append(rt.card_by_id[cursor].get("citation", ""))
                    row["citation"] = "\n".join(p for p in parts if p)
                else:
                    row["citation"] = citation
            # Append KG enrichment context (node definitions, neighbour cards)
            enrichment = str(row.get("enrichment_context", "") or "").strip()
            if enrichment:
                row["citation"] = str(row.get("citation", "")) + "\n[补充上下文]\n" + enrichment
            rows.append(row)
        prompt_candidates[label] = rows
    return prompt_candidates


def restore_original_evidence_quotes(
    option_analysis: list[dict[str, Any]],
    candidates_by_option: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Keep final evidence quote tied to the cited sentence card.

    Expanded passages are useful for judgement, but downstream bindings should
    remain anchored to the original textbook sentence/card whenever available.
    """
    original_quotes: dict[str, str] = {}
    for candidates in candidates_by_option.values():
        for candidate in candidates:
            cid = str(candidate.get("card_id", "") or "")
            quote = str(candidate.get("original_citation") or candidate.get("citation") or "").strip()
            if cid and quote:
                original_quotes.setdefault(cid, quote)

    for row in option_analysis:
        if not isinstance(row, dict):
            continue
        for card in row.get("evidence_cards", []) or []:
            if not isinstance(card, dict):
                continue
            cid = str(card.get("card_id", "") or "")
            quote = original_quotes.get(cid)
            if quote:
                card["quote"] = agentic.compact_text(quote, 220)
    return option_analysis


def _make_union_candidate(cid: str, score: float, source: str, card: dict[str, Any]) -> dict[str, Any]:
    text_parts = [
        card.get("context_before", ""),
        card.get("knowledge", ""),
        card.get("citation", ""),
        card.get("context_after", ""),
    ]
    return {
        "card_id": cid,
        "score": score,
        "_best_score": score,
        "source": source,
        "sources": [{"source": source, "score": round(score, 4)}],
        "type": card.get("type", ""),
        "knowledge": card.get("knowledge", ""),
        "citation": card.get("citation", ""),
        "context_before": card.get("context_before", ""),
        "context_after": card.get("context_after", ""),
        "text": " ".join(x for x in text_parts if x),
    }


def retrieve_for_question(
    rt: agentic.AgenticRuntime,
    stem: str,
    options: dict[str, str],
    *,
    top_k: int,
    kg: KGRecallRuntime | None,
    kg_node_top_k: int,
    kg_max_cards_per_option: int,
    kg_neighbor_limit: int,
    kg_node_score_threshold: float,
    use_card_expansion: bool = True,
    use_enrichment: bool = True,
    use_cross_encoder: bool = True,
    cross_encoder_url: str = CROSS_ENCODER_URL,
    use_llm_rerank: bool = True,
    use_parent_replace: bool = True,
    use_mmr: bool = True,
    mmr_lambda: float = 0.7,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """对标 WeKnora RAG pipeline: 单查询 → Vector+BM25 → RRF → append exact/adjacent/KG
    → enrich → cross-encoder → composite → MMR → parent replace → expand → sort.

    整题共享一个候选池，不做 per-option 分桶。
    """
    # Build queries from option texts only. Stem often contains noise like
    # "(多选)为什么..." or question framing that dilutes keyword precision.
    # Per-option queries give BM25/BGE a tight target for each option's claim.
    all_options_text = " ".join(str(v) for v in options.values())
    query_text = agentic.compact_text(all_options_text, 600)
    option_queries = [agentic.compact_text(v, 300) for v in options.values()]
    search_queries = [query_text] + option_queries

    must_terms = agentic.extract_phrases(stem, *options.values(), max_terms=28)
    must_terms = expand_terms(must_terms, max_per=4)
    query_plan: dict[str, Any] = {
        "search_queries": search_queries,
        "option_claim": " ".join(options.values())[:200],
        "evidence_need": stem,
        "must_terms": must_terms,
        "related_terms": [],
        "contrast_terms": [],
    }

    diagnostics: dict[str, Any] = {}

    # Phase A: Union-based retrieval (BGE ∪ BM25 ∪ exact_phrase ∪ adjacent_card).
    # RRF removed — 0.7/0.3 weights penalise BM25-only cards that are often
    # more relevant than BGE-only cards for single-sentence embeddings.
    candidates, base_diag, source_rankings = agentic.retrieve_for_option(
        rt, stem, " ".join(options.values())[:200], query_plan, top_k=max(top_k * 6, 120),
        return_source_rankings=True,
    )
    # Simple union: keep each card's best score across BGE and BM25,
    # boost if also found by exact_phrase or adjacent_card.
    merged: dict[str, dict[str, Any]] = {}
    for src_key in ("card_bge", "bm25"):
        for cid, score, _rank in source_rankings.get(src_key, []):
            if cid not in merged or score > merged[cid].get("_best_score", -999):
                card = rt.card_by_id.get(cid)
                if card is None:
                    continue
                merged[cid] = _make_union_candidate(cid, score, src_key, card)
    for src_key in ("exact_phrase", "adjacent_card"):
        for cid, score, _rank in source_rankings.get(src_key, []):
            if cid in merged:
                merged[cid]["score"] += score * 0.5
                merged[cid]["source"] += "+" + src_key
                merged[cid].setdefault("sources", []).append({"source": src_key, "score": round(score, 4)})
            else:
                card = rt.card_by_id.get(cid)
                if card is None:
                    continue
                merged[cid] = _make_union_candidate(cid, score, src_key, card)
    candidates = sorted(merged.values(), key=lambda c: c["score"], reverse=True)
    diagnostics["search"] = {
        "query": query_text,
        "base_candidates": len(candidates),
        "route_counts": base_diag.get("route_counts", {}),
    }

    # Phase B: KG recall append (WeKnora entity search — append + dedup)
    kg_candidates: list[dict[str, Any]] = []
    if kg is not None:
        kg_extra, kg_diag = kg_recall_for_option(
            kg=kg, rt=rt, stem=stem, option_text="", option_plan=query_plan,
            top_k_nodes=kg_node_top_k, max_cards=kg_max_cards_per_option,
            neighbor_limit=kg_neighbor_limit, threshold=kg_node_score_threshold,
        )
        # Merge KG candidates: append with score discount
        kg_by_id = {c["card_id"]: c for c in candidates}
        for kc in kg_extra:
            cid = kc.get("card_id", "")
            if cid in kg_by_id:
                kg_by_id[cid]["score"] = float(kg_by_id[cid].get("score", 0)) + float(kc.get("score", 0)) * 0.35
                kg_by_id[cid].setdefault("sources", []).extend(kc.get("sources", []))
            elif cid in rt.card_by_id:
                kg_candidates.append(kc)
        candidates = candidates + kg_candidates
        candidates.sort(key=lambda c: c.get("score", 0), reverse=True)
        diagnostics["kg_recall"] = kg_diag
    else:
        diagnostics["kg_recall"] = {"enabled": False}

    # Phase B.5: Neighbor expansion — pull in adjacent cards along sibling chain.
    # A single sentence card is too small for BGE/BM25 to match; expanding by
    # window=5 in each direction brings paragraph-level context into the pool.
    # Aligns with WeKnora collectEnrichmentChunkIDs nearby expansion.
    if _card_adjacency:
        candidates = expand_with_neighbors(candidates, _card_adjacency, rt.card_by_id, window=3)
        diagnostics["neighbor_expand"] = {"window": 5, "total_after": len(candidates)}

    # Phase C: Enrich (WeKnora collectEnrichmentChunkIDs)
    diagnostics["enrichment"] = {
        "enabled": bool(use_enrichment and kg is not None and _card_adjacency),
        "kg_available": kg is not None,
        "adjacency_available": bool(_card_adjacency),
    }
    if use_enrichment and kg is not None and _card_adjacency:
        candidates = enrich_candidates(
            candidates, _card_adjacency, rt.card_by_id,
            kg_nodes=getattr(kg, "nodes", None),
            card_to_nodes=getattr(kg, "card_to_nodes", None),
            node_cards=getattr(kg, "node_cards", None),
            neighbors=getattr(kg, "neighbors", None),
        )
        diagnostics["enrichment"]["enriched_count"] = sum(1 for c in candidates if c.get("enrichment_context"))

    # Phase D: Build CE passage (WeKnora getEnrichedPassage — 仅子块原始 content)
    for c in candidates:
        c.setdefault("original_citation", c.get("citation", ""))
        c["ce_passage"] = build_ce_passage(c)

    # Phase E: Rerank (WeKnora CHUNK_RERANK)
    # Flash bypass: replace CE scoring with llm_rerank, keep composite + MMR intact.
    diagnostics["cross_encoder"] = {
        "enabled": bool(use_cross_encoder or use_llm_rerank),
        "method": "llm_rerank" if use_llm_rerank else "cross_encoder",
        "candidate_count": len(candidates),
    }
    if (use_llm_rerank or use_cross_encoder) and candidates:
        passages = [str(c.get("ce_passage", "") or build_ce_passage(c)) for c in candidates]
        if use_llm_rerank:
            scores = llm_rerank(query_text, passages, client=rt.base.client)
        else:
            scores = cross_encoder_rerank(query_text, passages, url=cross_encoder_url, timeout=CROSS_ENCODER_TIMEOUT)
        for c, score in zip(candidates, scores):
            c["rerank_score"] = float(score)
        if scores:
            diagnostics["cross_encoder"].update({
                "score_min": round(min(scores), 6),
                "score_max": round(max(scores), 6),
                "score_avg": round(sum(scores) / len(scores), 6),
            })
    elif candidates:
        print("[reuse] WARNING: both --no-llm-rerank and --no-cross-encoder are set; "
              "rerank is disabled — candidates sorted by retrieval score only.")

    # Phase F: Composite score (WeKnora compositeScore).
    max_score = max((float(c.get("score", 0) or 0) for c in candidates), default=1.0)
    for c in candidates:
        c.setdefault("_raw_score", c.get("score", 0))
        c["score"] = float(c.get("score", 0) or 0) / max_score if max_score > 0 else 0
    for c in candidates:
        c["final_score"] = compute_composite_score(
            rerank_score=c.get("rerank_score"),
            retrieval_score=float(c.get("score", 0) or 0),
            retrieval_types=[],
        )

    # Phase G: MMR diversity (WeKnora applyMMR)
    diagnostics["mmr"] = {"enabled": bool(use_mmr), "lambda": mmr_lambda, "before_count": len(candidates)}
    if use_mmr:
        candidates = jaccard_mmr(candidates, lambda_=mmr_lambda, top_k=min(top_k * 4, len(candidates)))
    diagnostics["mmr"]["after_count"] = len(candidates)

    # Phase H: Parent block replace (WeKnora resolveParentChunks → CHUNK_MERGE Step 4)
    diagnostics["parent_replace"] = {
        "enabled": bool(use_parent_replace and _parent_blocks and _card_to_parent),
        "parent_blocks_available": bool(_parent_blocks),
        "card_to_parent_available": bool(_card_to_parent),
    }
    if use_parent_replace and _parent_blocks and _card_to_parent:
        candidates = resolve_parent_block(candidates, _parent_blocks, _card_to_parent)
        diagnostics["parent_replace"]["replaced_count"] = sum(1 for c in candidates if c.get("parent_id"))

    # Phase I: Expand short context (WeKnora expandShortContextWithNeighbors → CHUNK_MERGE Step 7)
    diagnostics["card_expansion"] = {
        "enabled": bool(use_card_expansion and _card_adjacency),
        "available": bool(_card_adjacency),
    }
    if use_card_expansion and _card_adjacency:
        candidates = expand_short_cards(
            candidates, _card_adjacency, rt.card_by_id,
            min_chars=350, target_chars=850, max_window=3,
        )
        diagnostics["card_expansion"]["expanded_count"] = sum(1 for c in candidates if c.get("expanded_text"))

    # Phase J: Final passage refresh (post-merge content update)
    for c in candidates:
        c.setdefault("original_citation", c.get("citation", ""))
        c["passage"] = build_passage(c)

    # Phase K: Final sort by composite score
    candidates.sort(key=lambda c: float(c.get("final_score", c.get("score", 0)) or 0), reverse=True)
    candidates = candidates[:top_k]

    diagnostics["final_candidate_count"] = len(candidates)
    return candidates, diagnostics


def select_questions(
    questions: list[dict[str, Any]],
    ids: list[str],
    limit: int | None,
    force: bool,
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if limit is not None and limit <= 0:
        return [], []
    wanted = set(ids)
    selected: list[dict[str, Any]] = []
    done: list[dict[str, Any]] = []
    for question in questions:
        qid = str(question.get("id") or question.get("question_id") or "")
        if wanted and qid not in wanted:
            continue
        if not force and question_output_path(qid, output_dir).exists():
            done.append(question)
            continue
        selected.append(question)
        if limit is not None and len(selected) >= limit:
            break
    return selected, done


def run_selected_question(
    rt: agentic.AgenticRuntime,
    question: dict[str, Any],
    *,
    top_k: int,
    max_followups: int,
    reviewer: bool,
    disagreement_reviewer: bool,
    kg: KGRecallRuntime | None,
    kg_node_top_k: int,
    kg_max_cards_per_option: int,
    kg_neighbor_limit: int,
    kg_node_score_threshold: float,
    repair_disagreements: bool,
    repair_max_rounds: int,
    repair_top_k: int,
    repair_max_followups: int,
    repair_kg_node_top_k: int,
    repair_kg_max_cards_per_option: int,
    repair_kg_neighbor_limit: int,
    repair_kg_node_score_threshold: float,
    use_card_expansion: bool = True,
    use_enrichment: bool = True,
    use_cross_encoder: bool = True,
    use_llm_rerank: bool = True,
    cross_encoder_url: str = CROSS_ENCODER_URL,
    use_parent_replace: bool = True,
    use_mmr: bool = True,
    mmr_lambda: float = 0.7,
) -> tuple[str, dict[str, Any]]:
    qid = str(question.get("id") or question.get("question_id") or "")
    try:
        result = run_question_with_optional_blind_repair(
            runtime_for_current_thread(rt),
            question,
            top_k=top_k,
            max_followups=max_followups,
            reviewer=reviewer,
            disagreement_reviewer=disagreement_reviewer,
            kg=kg,
            kg_node_top_k=kg_node_top_k,
            kg_max_cards_per_option=kg_max_cards_per_option,
            kg_neighbor_limit=kg_neighbor_limit,
            kg_node_score_threshold=kg_node_score_threshold,
            repair_disagreements=repair_disagreements,
            repair_max_rounds=repair_max_rounds,
            repair_top_k=repair_top_k,
            repair_max_followups=repair_max_followups,
            repair_kg_node_top_k=repair_kg_node_top_k,
            repair_kg_max_cards_per_option=repair_kg_max_cards_per_option,
            repair_kg_neighbor_limit=repair_kg_neighbor_limit,
            repair_kg_node_score_threshold=repair_kg_node_score_threshold,
            use_card_expansion=use_card_expansion,
            use_enrichment=use_enrichment,
            use_cross_encoder=use_cross_encoder,
            use_llm_rerank=use_llm_rerank,
            cross_encoder_url=cross_encoder_url,
            use_parent_replace=use_parent_replace,
            use_mmr=use_mmr,
            mmr_lambda=mmr_lambda,
        )
    except Exception as exc:
        model_plan = llm_stage_summary()
        result = {
            "schema_version": SCHEMA_VERSION,
            "question_id": qid,
            "status": "failed",
            "model": model_plan["adjudicator"]["model"],
            "model_field_note": "legacy compatibility field; use effective_model_plan/llm_stage_models for actual per-stage calls",
            "effective_model_plan": model_plan,
            "error": str(exc)[:1000],
            "created_at": _dt.datetime.now().isoformat(),
        }
    return qid, result


def stage_retry_reasons(
    result: dict[str, Any],
    *,
    reviewer: bool,
    disagreement_reviewer: bool,
) -> list[str]:
    """Return low-level LLM stage failures that are worth an automatic rerun."""
    reasons: list[str] = []
    if result.get("status") == "failed":
        reasons.append(f"question_failed:{str(result.get('error', ''))[:120]}")

    planner_error = str(result.get("planner_error", "") or "").strip()
    if planner_error:
        reasons.append(f"planner_error:{planner_error[:120]}")

    adjudicator_error = str(result.get("adjudicator_error", "") or "").strip()
    if adjudicator_error:
        reasons.append(f"adjudicator_error:{adjudicator_error[:120]}")

    raw_outputs = result.get("pipeline", {}).get("judge_answer", {}).get("raw_adjudicator_outputs", [])
    if isinstance(raw_outputs, list):
        for item in raw_outputs:
            if not isinstance(item, dict):
                continue
            if item.get("parsed_ok") is False:
                raw = str(item.get("raw", "") or "").strip()
                round_no = item.get("round", "")
                if raw:
                    reasons.append(f"adjudicator_json_parse_failed:round={round_no}")
                elif not adjudicator_error:
                    reasons.append(f"adjudicator_empty_output:round={round_no}")

    if reviewer:
        review = result.get("pipeline", {}).get("review_answer", {})
        if isinstance(review, dict) and review.get("review_status") == "error":
            err = str(review.get("review_error", "") or "").strip()
            reasons.append(f"reviewer_error:{err[:120]}")

    if disagreement_reviewer:
        llm_review = result.get("pipeline", {}).get("answer_disagreement_llm_review", {})
        if isinstance(llm_review, dict) and llm_review.get("review_status") == "error":
            err = str(llm_review.get("error", "") or "").strip()
            reasons.append(f"disagreement_reviewer_error:{err[:120]}")

    deduped: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped


def attach_stage_retry_metadata(
    result: dict[str, Any],
    *,
    retry_round: int,
    max_retries: int,
    trigger_reasons: list[str],
    previous_result: dict[str, Any] | None,
    final_reasons: list[str],
) -> dict[str, Any]:
    previous_meta = {}
    if isinstance(previous_result, dict):
        previous_meta = previous_result.get("pipeline", {}).get("stage_retry", {})
    history = list(previous_meta.get("history", [])) if isinstance(previous_meta, dict) else []
    history.append(
        {
            "round": retry_round,
            "trigger_reasons": trigger_reasons,
            "previous_status": previous_result.get("status") if isinstance(previous_result, dict) else "",
            "previous_ai_answer": previous_result.get("final", {}).get("ai_answer", []) if isinstance(previous_result, dict) else [],
            "after_status": result.get("status"),
            "after_ai_answer": result.get("final", {}).get("ai_answer", []),
            "after_retry_reasons": final_reasons,
            "finished_at": _dt.datetime.now().isoformat(),
        }
    )
    result.setdefault("pipeline", {})["stage_retry"] = {
        "enabled": True,
        "max_retries": max_retries,
        "retries_used": retry_round,
        "recovered": not final_reasons,
        "final_retry_reasons": final_reasons,
        "history": history,
    }
    return result


def summary_row_for_result(qid: str, path: Path, result: dict[str, Any], *, from_cache: bool = False) -> dict[str, Any]:
    validate = result.get("pipeline", {}).get("validate", {})
    row = {
        "question_id": qid,
        "path": str(path),
        "status": result.get("status"),
        "ai_answer": result.get("final", {}).get("ai_answer", []),
        "key_answer": normalize_answer(result.get("answer", ""), result.get("options", {})) if result.get("options") else [],
        "cited_cards": len(result.get("final", {}).get("evidence_cards", [])),
        "validation_status": validate.get("validation_status", ""),
        "needs_teacher_review": result.get("final", {}).get("needs_teacher_review", True),
    }
    if from_cache:
        row["from_cache"] = True
    if result.get("status") == "failed":
        row["error"] = result.get("error", "")
    blind_repair = result.get("pipeline", {}).get("blind_repair", {})
    if isinstance(blind_repair, dict) and blind_repair.get("enabled"):
        row["blind_repair_rounds_used"] = blind_repair.get("rounds_used", 0)
        row["blind_repair_trigger_reasons"] = [
            item.get("trigger_reason", "")
            for item in blind_repair.get("history", [])
            if isinstance(item, dict) and item.get("trigger_reason")
        ]
    retry_meta = result.get("pipeline", {}).get("stage_retry", {})
    if isinstance(retry_meta, dict) and retry_meta.get("enabled"):
        row["stage_retry_recovered"] = retry_meta.get("recovered")
        row["stage_retries_used"] = retry_meta.get("retries_used")
        row["stage_retry_reasons"] = retry_meta.get("final_retry_reasons", [])
    return row


def upsert_summary_output(summary: dict[str, Any], row: dict[str, Any]) -> None:
    qid = row.get("question_id")
    outputs = summary.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("question_id") == qid:
            outputs[index] = row
            return
    outputs.append(row)


def rebuild_bindings_jsonl(
    *,
    bindings_path: Path,
    questions: list[dict[str, Any]],
    results_by_qid: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if bindings_path.exists():
        bindings_path.unlink()
    all_rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for question in questions:
        qid = str(question.get("id") or question.get("question_id") or "")
        if qid in seen:
            continue
        seen.add(qid)
        result = results_by_qid.get(qid)
        if not result or result.get("status") != "done":
            continue
        rows = binding_rows(result)
        append_jsonl(bindings_path, rows)
        all_rows.extend(rows)
    return all_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Reuse 新题解析模块 to build question-option-card bindings.")
    parser.add_argument("--input-jsonl", type=Path, default=None, help="Optional JSONL input. Defaults to structured exercise MD files.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Output directory.")
    parser.add_argument("--scope", default="v6-sentence", choices=sorted(run_step1.EVIDENCE_FILES), help="Evidence scope.")
    parser.add_argument("--ids", nargs="*", default=[], help="Question ids to run, e.g. 2.1_19.")
    parser.add_argument("--limit", type=int, default=None, help="Max questions to run.")
    parser.add_argument("--top-k", type=int, default=30, help="Candidate cards per option.")
    parser.add_argument("--max-followups", type=int, default=0, help="Adjudicator follow-up retrieval rounds.")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_WORKERS, help="Question-level worker count.")
    parser.add_argument("--stage-retries", type=int, default=DEFAULT_STAGE_RETRIES, help="Automatic reruns for low-level LLM stage failures.")
    parser.add_argument("--stage-retry-concurrency", type=int, default=DEFAULT_STAGE_RETRY_CONCURRENCY, help="Worker count for failed-stage reruns.")
    parser.add_argument("--stage-retry-delay", type=float, default=DEFAULT_STAGE_RETRY_DELAY_SECONDS, help="Seconds to wait before each failed-stage rerun round.")
    parser.add_argument("--kg-work-dir", type=Path, default=DEFAULT_KG_WORK_DIR, help="KG work directory for sentence-card recall navigation.")
    parser.add_argument("--use-kg-recall", dest="use_kg_recall", action="store_true", default=True, help="Enable KG-assisted candidate recall.")
    parser.add_argument("--no-kg-recall", dest="use_kg_recall", action="store_false", help="Disable KG-assisted candidate recall for A/B tests.")
    parser.add_argument("--kg-node-top-k", type=int, default=DEFAULT_KG_NODE_TOP_K, help="KG nodes to recall per option.")
    parser.add_argument("--kg-max-cards-per-option", type=int, default=DEFAULT_KG_MAX_CARDS_PER_OPTION, help="Max KG-mounted card candidates per option.")
    parser.add_argument("--kg-neighbor-limit", type=int, default=DEFAULT_KG_NEIGHBOR_LIMIT, help="Neighbor KG nodes to expand per hit node.")
    parser.add_argument("--kg-node-score-threshold", type=float, default=DEFAULT_KG_NODE_SCORE_THRESHOLD, help="Minimum KG node semantic score.")
    parser.add_argument("--repair-disagreements", dest="repair_disagreements", action="store_true", default=DEFAULT_REPAIR_DISAGREEMENTS, help="After Pro disagreement review, rerun blind pipeline for retrieval/focus gaps.")
    parser.add_argument("--no-repair-disagreements", dest="repair_disagreements", action="store_false", help="Disable disagreement-triggered blind reruns.")
    parser.add_argument("--repair-max-rounds", type=int, default=DEFAULT_REPAIR_MAX_ROUNDS, help="Max blind rerun rounds after disagreement review.")
    parser.add_argument("--repair-top-k", type=int, default=DEFAULT_REPAIR_TOP_K, help="Candidate cards per option during blind repair reruns.")
    parser.add_argument("--repair-max-followups", type=int, default=DEFAULT_REPAIR_MAX_FOLLOWUPS, help="Follow-up retrieval rounds during blind repair reruns.")
    parser.add_argument("--repair-kg-node-top-k", type=int, default=DEFAULT_REPAIR_KG_NODE_TOP_K, help="KG nodes per option during repair.")
    parser.add_argument("--repair-kg-max-cards-per-option", type=int, default=DEFAULT_REPAIR_KG_MAX_CARDS_PER_OPTION, help="KG card candidates per option during repair.")
    parser.add_argument("--repair-kg-neighbor-limit", type=int, default=DEFAULT_REPAIR_KG_NEIGHBOR_LIMIT, help="KG neighbor expansion during repair.")
    parser.add_argument("--repair-kg-node-score-threshold", type=float, default=DEFAULT_REPAIR_KG_NODE_SCORE_THRESHOLD, help="KG node score threshold during repair.")
    parser.add_argument("--force", action="store_true", help="Re-run questions even if output already exists.")
    parser.add_argument("--no-reviewer", action="store_true", default=True,
                        help="Skip the LLM reviewer pass (default). Use --reviewer to enable.")
    parser.add_argument("--reviewer", dest="no_reviewer", action="store_false",
                        help="Enable the LLM reviewer pass.")
    parser.add_argument(
        "--review-disagreements",
        action="store_true",
        default=False,
        help="Run the post-hoc LLM disagreement reviewer for answer mismatches or weak convergence.",
    )
    parser.add_argument(
        "--no-review-disagreements",
        dest="review_disagreements",
        action="store_false",
        help="Skip the LLM disagreement reviewer.",
    )
    parser.add_argument(
        "--print-model-plan",
        action="store_true",
        default=True,
        help="Print the effective per-stage model configuration before running.",
    )
    parser.add_argument(
        "--require-stage-models",
        nargs="*",
        default=[],
        metavar="STAGE=MODEL",
        help=(
            "Fail before running if any effective stage model differs from the expected value, "
            "e.g. planner=deepseek-v4-pro adjudicator=deepseek-v4-flash."
        ),
    )
    # === New retrieval pipeline flags ===
    parser.add_argument("--use-card-expansion", dest="use_card_expansion", action="store_true", default=True,
                        help="Expand short cards along sibling chain.")
    parser.add_argument("--no-card-expansion", dest="use_card_expansion", action="store_false")
    parser.add_argument("--use-enrichment", dest="use_enrichment", action="store_true", default=True,
                        help="Enrich candidates with nearby cards and KG context.")
    parser.add_argument("--no-enrichment", dest="use_enrichment", action="store_false")
    parser.add_argument("--use-cross-encoder", dest="use_cross_encoder", action="store_true", default=True,
                        help="Re-rank candidates with cross-encoder model.")
    parser.add_argument("--no-cross-encoder", dest="use_cross_encoder", action="store_false")
    parser.add_argument("--precompute", action="store_true", default=False,
                        help="Only run retrieval + CE, save candidates to cache. Skip adjudicator.")
    parser.add_argument("--no-precompute", dest="precompute", action="store_false",
                        help="Skip candidate cache, run full pipeline including retrieval.")
    parser.add_argument("--adjudicate-only", action="store_true", default=False,
                        help="Skip retrieval+CE entirely, use precomputed candidates from cache.")
    parser.add_argument("--llm-rerank", action="store_true", default=True,
                        help="Use DeepSeek Flash for rerank (default). Use --no-llm-rerank for cross-encoder GPU.")
    parser.add_argument("--no-llm-rerank", dest="llm_rerank", action="store_false")
    parser.add_argument("--cross-encoder-url", type=str, default=CROSS_ENCODER_URL,
                        help="Cross-encoder server URL.")
    parser.add_argument("--use-parent-replace", dest="use_parent_replace", action="store_true", default=True,
                        help="Replace child card content with parent block after re-rank.")
    parser.add_argument("--no-parent-replace", dest="use_parent_replace", action="store_false")
    parser.add_argument("--use-mmr", dest="use_mmr", action="store_true", default=True,
                        help="Apply Jaccard MMR diversification.")
    parser.add_argument("--no-mmr", dest="use_mmr", action="store_false")
    parser.add_argument("--mmr-lambda", type=float, default=0.7,
                        help="MMR relevance-diversity trade-off (0-1).")
    parser.add_argument("--plan-b", action="store_true", default=False,
                        help="Enable Plan B: expand pool + reverse close-read for AI/key mismatches.")
    parser.add_argument("--no-plan-b", dest="plan_b", action="store_false")
    args = parser.parse_args()

    questions = load_questions_from_jsonl(args.input_jsonl) if args.input_jsonl else load_questions_from_md()
    output_dir = args.output_dir
    model_plan = llm_stage_summary()
    required_stage_models = parse_stage_model_requirements(args.require_stage_models)
    assert_stage_model_requirements(model_plan, required_stage_models)
    if args.print_model_plan:
        print_model_plan(model_plan)
    workers = max(1, int(args.concurrency or 1))
    stage_retries = max(0, int(args.stage_retries or 0))
    stage_retry_workers = max(1, int(args.stage_retry_concurrency or 1))
    stage_retry_delay = max(0.0, float(args.stage_retry_delay or 0.0))
    kg_node_top_k = max(1, int(args.kg_node_top_k or 1))
    kg_max_cards_per_option = max(1, int(args.kg_max_cards_per_option or 1))
    kg_neighbor_limit = max(0, int(args.kg_neighbor_limit or 0))
    kg_node_score_threshold = float(args.kg_node_score_threshold)
    repair_max_rounds = max(0, int(args.repair_max_rounds or 0))
    repair_top_k = max(int(args.top_k or 1), int(args.repair_top_k or 1))
    repair_max_followups = max(0, int(args.repair_max_followups or 0))
    repair_kg_node_top_k = max(1, int(args.repair_kg_node_top_k or 1))
    repair_kg_max_cards_per_option = max(1, int(args.repair_kg_max_cards_per_option or 1))
    repair_kg_neighbor_limit = max(0, int(args.repair_kg_neighbor_limit or 0))
    repair_kg_node_score_threshold = float(args.repair_kg_node_score_threshold)
    reviewer_enabled = not args.no_reviewer
    # Set pipeline feature flags from CLI
    global _use_card_expansion, _use_enrichment, _use_cross_encoder, _use_llm_rerank
    global _cross_encoder_url, _use_parent_replace, _use_mmr, _mmr_lambda, _use_plan_b
    _use_card_expansion = args.use_card_expansion
    _use_enrichment = args.use_enrichment
    _use_cross_encoder = args.use_cross_encoder
    _use_llm_rerank = args.llm_rerank
    _use_parent_replace = args.use_parent_replace
    _use_mmr = args.use_mmr
    _cross_encoder_url = args.cross_encoder_url
    _mmr_lambda = args.mmr_lambda
    _use_plan_b = args.plan_b
    retrieval_flags = {
        "use_card_expansion": args.use_card_expansion,
        "use_enrichment": args.use_enrichment,
        "use_cross_encoder": args.use_cross_encoder,
        "use_llm_rerank": args.llm_rerank,
        "cross_encoder_url": args.cross_encoder_url,
        "use_parent_replace": args.use_parent_replace,
        "use_mmr": args.use_mmr,
        "mmr_lambda": args.mmr_lambda,
    }
    selected, done = select_questions(questions, args.ids, args.limit, args.force, output_dir)
    skipped = len(done)
    print(
        f"[reuse] questions={len(questions)} selected={len(selected)} "
        f"skipped_done={skipped} scope={args.scope} concurrency={workers} "
        f"stage_retries={stage_retries} stage_retry_concurrency={stage_retry_workers} "
        f"kg_recall={bool(args.use_kg_recall)}"
    )
    if not selected and not done:
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Precompute mode: retrieval+CE only, save cache, no adjudicator ---
    if args.precompute and selected:
        CANDIDATE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        rt = load_reuse_runtime(evidence_scope=args.scope)
        kg = None
        if args.use_kg_recall:
            kg = load_kg_recall_runtime(work_dir=args.kg_work_dir, bge=rt.base.bge, valid_card_ids=rt.base.valid_card_ids)
        if rt is not None:
            cards = [rt.card_by_id[cid] for cid in rt.card_ids]
            globals()["_card_adjacency"] = build_card_adjacency(cards)
            globals()["_parent_blocks"] = build_parent_blocks(cards)
            globals()["_card_to_parent"] = build_card_to_parent(cards)
        _precompute_workers = max(1, int(args.concurrency or 1))
        print(f"[precompute] {len(selected)} questions, concurrency={_precompute_workers}")
        _precompute_count = [0]
        _precompute_lock = threading.Lock()

        def _precompute_one(question: dict[str, Any]) -> None:
            qid = str(question.get("id") or question.get("question_id") or "")
            cache_path = CANDIDATE_CACHE_DIR / f"{qid}.pkl"
            if cache_path.exists() and not args.force:
                with _precompute_lock:
                    _precompute_count[0] += 1
                print(f"[precompute] {_precompute_count[0]}/{len(selected)} {qid} (cached)")
                return
            stem = question.get("stem", "")
            options = question.get("options", {})
            if not (isinstance(options, dict) and stem and len(options) >= 2):
                return
            try:
                # Each thread needs its own runtime copy with a dedicated client
                _rt = runtime_for_current_thread(rt)
                candidates, diagnostics = retrieve_for_question(
                    _rt, stem, options, top_k=args.top_k, kg=kg,
                    kg_node_top_k=kg_node_top_k, kg_max_cards_per_option=kg_max_cards_per_option,
                    kg_neighbor_limit=kg_neighbor_limit, kg_node_score_threshold=kg_node_score_threshold,
                    **retrieval_flags,
                )
                with open(cache_path, "wb") as _f:
                    pickle.dump({"scope": args.scope, "qid": qid, "candidates": candidates, "diagnostics": diagnostics}, _f)
                with _precompute_lock:
                    _precompute_count[0] += 1
                print(f"[precompute] {_precompute_count[0]}/{len(selected)} {qid} ({len(candidates)} candidates)")
            except Exception as exc:
                with _precompute_lock:
                    _precompute_count[0] += 1
                print(f"[precompute] {_precompute_count[0]}/{len(selected)} {qid} FAILED: {exc}")

        with ThreadPoolExecutor(max_workers=_precompute_workers) as _pool:
            _futures = [_pool.submit(_precompute_one, q) for q in selected]
            for _f in as_completed(_futures):
                pass  # results printed inside _precompute_one
        print(f"[precompute] done. Cache in {CANDIDATE_CACHE_DIR}")
        return 0

    # --- Normal / adjudicate-only mode ---
    bindings_path = output_dir / BINDINGS_JSONL.name
    if bindings_path.exists():
        bindings_path.unlink()

    rt = load_reuse_runtime(evidence_scope=args.scope) if selected else None
    kg: KGRecallRuntime | None = None
    if args.use_kg_recall and rt is not None:
        kg = load_kg_recall_runtime(
            work_dir=args.kg_work_dir,
            bge=rt.base.bge,
            valid_card_ids=rt.base.valid_card_ids,
        )
        # P0: 初始化 WeKnora 式数据层（句卡链表 + 父块索引）
    global _card_adjacency, _parent_blocks, _card_to_parent
    if rt is not None:
        cards = [rt.card_by_id[cid] for cid in rt.card_ids]
        _card_adjacency = build_card_adjacency(cards)
        _parent_blocks = build_parent_blocks(cards)
        _card_to_parent = build_card_to_parent(cards)
        print(f"[reuse] card adjacency: {len(_card_adjacency)} cards linked, "
              f"parent blocks: {len(_parent_blocks)} H4 sections")
    disagreement_client = None
    if args.review_disagreements and done:
        disagreement_client = rt.base.client if rt is not None else make_openai_client()
    all_rows: list[dict[str, Any]] = []
    summary = {
        "schema_version": SCHEMA_VERSION,
        "started_at": _dt.datetime.now().isoformat(),
        "field_notes": FIELD_NOTES,
        "scope": args.scope,
        "model": model_plan["adjudicator"]["model"],
        "model_field_note": "legacy compatibility field; use effective_model_plan/llm_stage_models for actual per-stage calls",
        "llm_extra_body": model_plan["adjudicator"]["extra_body"],
        "effective_model_plan": model_plan,
        "llm_stage_models": model_plan,
        "concurrency": workers,
        "stage_retries": stage_retries,
        "stage_retry_concurrency": stage_retry_workers,
        "stage_retry_delay": stage_retry_delay,
        "blind_repair": {
            "enabled": bool(args.repair_disagreements and args.review_disagreements and repair_max_rounds > 0),
            "requires_review_disagreements": True,
            "max_rounds": repair_max_rounds,
            "top_k": repair_top_k,
            "max_followups": repair_max_followups,
            "kg_node_top_k": repair_kg_node_top_k,
            "kg_max_cards_per_option": repair_kg_max_cards_per_option,
            "kg_neighbor_limit": repair_kg_neighbor_limit,
            "kg_node_score_threshold": repair_kg_node_score_threshold,
            "leakage_guard": "standard answer is visible only to disagreement_reviewer; repair reruns planner/adjudicator/reviewer without answer injection",
        },
        "graph_mode": "kg_recall" if kg is not None else "disabled",
        "kg_recall": kg_recall_summary(
            kg,
            requested=bool(args.use_kg_recall),
            work_dir=args.kg_work_dir,
            node_top_k=kg_node_top_k,
            max_cards_per_option=kg_max_cards_per_option,
            neighbor_limit=kg_neighbor_limit,
            node_score_threshold=kg_node_score_threshold,
        ),
        "card_relations": "disabled",
        "total_questions": len(questions),
        "selected": len(selected),
        "skipped_done": skipped,
        "outputs": [],
    }
    results_by_qid: dict[str, dict[str, Any]] = {}
    processed_questions = done + selected
    question_by_qid = {
        str(question.get("id") or question.get("question_id") or ""): question
        for question in processed_questions
    }

    for question in done:
        qid = str(question.get("id") or question.get("question_id") or "")
        path = question_output_path(qid, output_dir)
        try:
            result = read_json(path)
            if result.get("status") == "done":
                result = refresh_cached_result(
                    result,
                    client=disagreement_client,
                    run_llm_disagreement_review=args.review_disagreements,
                )
                write_json(path, result)
            rows = binding_rows(result) if result.get("status") == "done" else []
            append_jsonl(bindings_path, rows)
            all_rows.extend(rows)
            results_by_qid[qid] = result
            upsert_summary_output(summary, summary_row_for_result(qid, path, result, from_cache=True))
        except Exception as exc:
            summary["outputs"].append(
                {
                    "question_id": qid,
                    "path": str(path),
                    "status": "cache_read_failed",
                    "from_cache": True,
                    "error": str(exc)[:500],
                }
            )

    if selected:
        assert rt is not None
        completed = 0
        if workers == 1:
            for index, question in enumerate(selected, start=1):
                qid = str(question.get("id") or question.get("question_id") or f"q{index}")
                print(f"[reuse] {index}/{len(selected)} {qid}")
                _, result = run_selected_question(
                    rt,
                    question,
                    top_k=args.top_k,
                    max_followups=args.max_followups,
                    reviewer=reviewer_enabled,
                    disagreement_reviewer=args.review_disagreements,
                    kg=kg,
                    kg_node_top_k=kg_node_top_k,
                    kg_max_cards_per_option=kg_max_cards_per_option,
                    kg_neighbor_limit=kg_neighbor_limit,
                    kg_node_score_threshold=kg_node_score_threshold,
                    repair_disagreements=bool(args.repair_disagreements),
                    repair_max_rounds=repair_max_rounds,
                    repair_top_k=repair_top_k,
                    repair_max_followups=repair_max_followups,
                    repair_kg_node_top_k=repair_kg_node_top_k,
                    repair_kg_max_cards_per_option=repair_kg_max_cards_per_option,
                    repair_kg_neighbor_limit=repair_kg_neighbor_limit,
                    repair_kg_node_score_threshold=repair_kg_node_score_threshold,
                    **retrieval_flags,
                )
                path = question_output_path(qid, output_dir)
                write_json(path, result)
                rows = binding_rows(result) if result.get("status") == "done" else []
                append_jsonl(bindings_path, rows)
                all_rows.extend(rows)
                results_by_qid[qid] = result
                upsert_summary_output(summary, summary_row_for_result(qid, path, result))
                write_json(output_dir / SUMMARY_JSON.name, summary)
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                future_to_question = {
                    pool.submit(
                        run_selected_question,
                        rt,
                        question,
                        top_k=args.top_k,
                        max_followups=args.max_followups,
                        reviewer=reviewer_enabled,
                        disagreement_reviewer=args.review_disagreements,
                        kg=kg,
                        kg_node_top_k=kg_node_top_k,
                        kg_max_cards_per_option=kg_max_cards_per_option,
                        kg_neighbor_limit=kg_neighbor_limit,
                        kg_node_score_threshold=kg_node_score_threshold,
                        repair_disagreements=bool(args.repair_disagreements),
                        repair_max_rounds=repair_max_rounds,
                        repair_top_k=repair_top_k,
                        repair_max_followups=repair_max_followups,
                        repair_kg_node_top_k=repair_kg_node_top_k,
                        repair_kg_max_cards_per_option=repair_kg_max_cards_per_option,
                        repair_kg_neighbor_limit=repair_kg_neighbor_limit,
                        repair_kg_node_score_threshold=repair_kg_node_score_threshold,
                        **retrieval_flags,
                    ): question
                    for question in selected
                }
                for future in as_completed(future_to_question):
                    question = future_to_question[future]
                    qid = str(question.get("id") or question.get("question_id") or "")
                    completed += 1
                    try:
                        qid, result = future.result()
                    except Exception as exc:
                        failed_model_plan = llm_stage_summary()
                        result = {
                            "schema_version": SCHEMA_VERSION,
                            "question_id": qid,
                            "status": "failed",
                            "model": failed_model_plan["adjudicator"]["model"],
                            "model_field_note": "legacy compatibility field; use effective_model_plan/llm_stage_models for actual per-stage calls",
                            "effective_model_plan": failed_model_plan,
                            "error": str(exc)[:1000],
                            "created_at": _dt.datetime.now().isoformat(),
                        }
                    path = question_output_path(qid, output_dir)
                    write_json(path, result)
                    rows = binding_rows(result) if result.get("status") == "done" else []
                    append_jsonl(bindings_path, rows)
                    all_rows.extend(rows)
                    results_by_qid[qid] = result
                    upsert_summary_output(summary, summary_row_for_result(qid, path, result))
                    print(f"[reuse] done {completed}/{len(selected)} {qid} status={result.get('status')}")
                    write_json(output_dir / SUMMARY_JSON.name, summary)

    if stage_retries > 0 and results_by_qid:
        for retry_round in range(1, stage_retries + 1):
            retry_items: list[tuple[str, dict[str, Any], list[str]]] = []
            for qid, result in results_by_qid.items():
                question = question_by_qid.get(qid)
                if not question:
                    continue
                reasons = stage_retry_reasons(
                    result,
                    reviewer=reviewer_enabled,
                    disagreement_reviewer=args.review_disagreements,
                )
                if reasons:
                    retry_items.append((qid, question, reasons))
            if not retry_items:
                break
            if rt is None:
                rt = load_reuse_runtime(evidence_scope=args.scope)
                if args.use_kg_recall:
                    kg = load_kg_recall_runtime(
                        work_dir=args.kg_work_dir,
                        bge=rt.base.bge,
                        valid_card_ids=rt.base.valid_card_ids,
                    )
                    summary["graph_mode"] = "kg_recall" if kg is not None else "disabled"
                    summary["kg_recall"] = kg_recall_summary(
                        kg,
                        requested=bool(args.use_kg_recall),
                        work_dir=args.kg_work_dir,
                        node_top_k=kg_node_top_k,
                        max_cards_per_option=kg_max_cards_per_option,
                        neighbor_limit=kg_neighbor_limit,
                        node_score_threshold=kg_node_score_threshold,
                    )
            print(f"[reuse] stage retry round {retry_round}/{stage_retries}: {len(retry_items)} question(s)")
            if stage_retry_delay:
                time.sleep(stage_retry_delay)
            completed_retry = 0

            def _finish_retry(qid: str, result: dict[str, Any], trigger_reasons: list[str]) -> None:
                previous = results_by_qid.get(qid, {})
                final_reasons = stage_retry_reasons(
                    result,
                    reviewer=reviewer_enabled,
                    disagreement_reviewer=args.review_disagreements,
                )
                result = attach_stage_retry_metadata(
                    result,
                    retry_round=retry_round,
                    max_retries=stage_retries,
                    trigger_reasons=trigger_reasons,
                    previous_result=previous,
                    final_reasons=final_reasons,
                )
                path = question_output_path(qid, output_dir)
                write_json(path, result)
                results_by_qid[qid] = result
                upsert_summary_output(summary, summary_row_for_result(qid, path, result))

            if stage_retry_workers == 1:
                for qid, question, trigger_reasons in retry_items:
                    print(f"[reuse] retry {retry_round}/{stage_retries} {qid} reasons={'; '.join(trigger_reasons[:3])}")
                    _, result = run_selected_question(
                        rt,
                        question,
                        top_k=args.top_k,
                        max_followups=args.max_followups,
                        reviewer=reviewer_enabled,
                        disagreement_reviewer=args.review_disagreements,
                        kg=kg,
                        kg_node_top_k=kg_node_top_k,
                        kg_max_cards_per_option=kg_max_cards_per_option,
                        kg_neighbor_limit=kg_neighbor_limit,
                        kg_node_score_threshold=kg_node_score_threshold,
                        repair_disagreements=bool(args.repair_disagreements),
                        repair_max_rounds=repair_max_rounds,
                        repair_top_k=repair_top_k,
                        repair_max_followups=repair_max_followups,
                    repair_kg_node_top_k=repair_kg_node_top_k,
                    repair_kg_max_cards_per_option=repair_kg_max_cards_per_option,
                    repair_kg_neighbor_limit=repair_kg_neighbor_limit,
                    repair_kg_node_score_threshold=repair_kg_node_score_threshold,
                    **retrieval_flags,
                )
                    _finish_retry(qid, result, trigger_reasons)
                    write_json(output_dir / SUMMARY_JSON.name, summary)
            else:
                with ThreadPoolExecutor(max_workers=stage_retry_workers) as pool:
                    future_to_retry = {
                        pool.submit(
                            run_selected_question,
                            rt,
                            question,
                            top_k=args.top_k,
                            max_followups=args.max_followups,
                            reviewer=reviewer_enabled,
                            disagreement_reviewer=args.review_disagreements,
                            kg=kg,
                            kg_node_top_k=kg_node_top_k,
                            kg_max_cards_per_option=kg_max_cards_per_option,
                            kg_neighbor_limit=kg_neighbor_limit,
                            kg_node_score_threshold=kg_node_score_threshold,
                            repair_disagreements=bool(args.repair_disagreements),
                            repair_max_rounds=repair_max_rounds,
                            repair_top_k=repair_top_k,
                            repair_max_followups=repair_max_followups,
                            repair_kg_node_top_k=repair_kg_node_top_k,
                            repair_kg_max_cards_per_option=repair_kg_max_cards_per_option,
                            repair_kg_neighbor_limit=repair_kg_neighbor_limit,
                            repair_kg_node_score_threshold=repair_kg_node_score_threshold,
                            **retrieval_flags,
                        ): (qid, trigger_reasons)
                        for qid, question, trigger_reasons in retry_items
                    }
                    for future in as_completed(future_to_retry):
                        qid, trigger_reasons = future_to_retry[future]
                        completed_retry += 1
                        try:
                            _, result = future.result()
                        except Exception as exc:
                            failed_model_plan = llm_stage_summary()
                            result = {
                                "schema_version": SCHEMA_VERSION,
                                "question_id": qid,
                                "status": "failed",
                                "model": failed_model_plan["adjudicator"]["model"],
                                "model_field_note": "legacy compatibility field; use effective_model_plan/llm_stage_models for actual per-stage calls",
                                "effective_model_plan": failed_model_plan,
                                "error": str(exc)[:1000],
                                "created_at": _dt.datetime.now().isoformat(),
                            }
                        _finish_retry(qid, result, trigger_reasons)
                        print(f"[reuse] retry done {completed_retry}/{len(retry_items)} {qid} status={result.get('status')}")
                        write_json(output_dir / SUMMARY_JSON.name, summary)

    if results_by_qid:
        all_rows = rebuild_bindings_jsonl(
            bindings_path=bindings_path,
            questions=processed_questions,
            results_by_qid=results_by_qid,
        )

    summary["finished_at"] = _dt.datetime.now().isoformat()
    summary["binding_rows"] = len(all_rows)
    write_json(output_dir / SUMMARY_JSON.name, summary)
    print(f"[reuse] wrote {len(all_rows)} option rows -> {bindings_path}")
    print(f"[reuse] summary -> {output_dir / SUMMARY_JSON.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
