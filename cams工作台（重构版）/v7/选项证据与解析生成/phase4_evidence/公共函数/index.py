# -*- coding: utf-8 -*-
"""公共索引 — 数据加载、BM25、BGE、分词器、路径常量。"""

from __future__ import annotations

import json, math, os, pickle, re
from collections import defaultdict
from pathlib import Path
from typing import Any

# ── 路径常量 ──

HERE = Path(__file__).resolve().parent
PHASE4 = HERE.parent
V7_ROOT = PHASE4.parent
PROJECT_ROOT = PHASE4.parents[1]

QUESTIONS_PATH = V7_ROOT / "phase3.5_questions" / "output" / "v7_questions.json"
INDEX_PKL = V7_ROOT / "phase3_index" / "output" / "index" / "v7_index_5614abb1c4bf.pkl"
KG_GRAPH_PATH = PROJECT_ROOT / "知识图谱提取" / "phases" / "phase06_kg_views" / "outputs" / "kg_retrieval_graph.json"
P5_ALIAS_INDEX_PATH = PROJECT_ROOT / "知识图谱提取" / "phases" / "phase05_terms" / "outputs" / "p5c_alias_index.json"
QUESTION_TEXT_OVERRIDES_PATH = HERE.parent / "盲判流程" / "question_text_overrides.jsonl"

API_KEY_ENV_NAMES = ("DEEPSEEK_API_KEY", "DS_API_KEY", "DS_KEY")
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

_KG_UNIT_CACHE: dict[str, dict[str, Any]] | None = None
_BGE_MODEL: Any = None

# ── 分词器 ──

def tokenize(text: str) -> list[str]:
    text = (text or "").lower()
    tokens: list[str] = []
    tokens.extend(re.findall(r"[a-z0-9][a-z0-9_\-/.]*", text))
    cjk_runs = re.findall(r"[一-鿿]+", text)
    for run in cjk_runs:
        if len(run) == 1:
            tokens.append(run); continue
        for n in (2, 3):
            if len(run) >= n:
                tokens.extend(run[i:i+n] for i in range(len(run)-n+1))
    return tokens

# ── BM25 ──

class BM25:
    def __init__(self, docs: list[dict], df: dict[str,int], avgdl: float, k1: float=1.5, b: float=0.75):
        self.docs, self.df, self.avgdl, self.k1, self.b = docs, df, avgdl, k1, b
        self.N = len(docs)
        self.doc_lens = [sum(doc.values()) for doc in docs]
        self.idf_cache: dict[str,float] = {}

    def idf(self, term: str) -> float:
        if term not in self.idf_cache:
            n = self.df.get(term, 0)
            self.idf_cache[term] = math.log((self.N - n + 0.5) / (n + 0.5) + 1.0)
        return self.idf_cache[term]

    def score(self, query_tokens: list[str], doc_idx: int) -> float:
        doc, doc_len = self.docs[doc_idx], self.doc_lens[doc_idx]
        score, qtf = 0.0, {}
        for term in query_tokens:
            qtf[term] = qtf.get(term, 0) + 1
        for term, qf in qtf.items():
            tf = doc.get(term, 0)
            if tf == 0: continue
            idf_val = self.idf(term)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
            score += idf_val * (numerator / denominator) * qf
        return score

    def search(self, query: str, top_k: int=20) -> list[tuple[int,float]]:
        q_tokens = tokenize(query)
        if not q_tokens: return []
        scores = [(i, self.score(q_tokens, i)) for i in range(self.N)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

# ── 数据加载 ──

def load_index(pkl_path: str|Path) -> dict[str,Any]:
    print(f"[load] 读取索引: {pkl_path}")
    with open(pkl_path, "rb") as f:
        idx = pickle.load(f)
    print(f"[load] 索引加载完成 | card_ids={len(idx['card_ids'])} | bge_vecs={idx['bge_vecs'].shape} | unit_lookup={len(idx['unit_lookup'])}")
    return idx

def load_question_text_overrides(jsonl_path: str|Path) -> dict[str,dict[str,Any]]:
    path = Path(jsonl_path)
    if not path.exists():
        print(f"  提示：题目文本 override 文件不存在，跳过（{path}）")
        return {}
    overrides: dict[str,dict[str,Any]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip(): continue
            try: row = json.loads(line)
            except json.JSONDecodeError as exc: raise RuntimeError(f"{path}:{line_no}: JSON 解析失败: {exc}") from exc
            qid = str(row.get("question_id","")).strip()
            if not qid: raise RuntimeError(f"{path}:{line_no}: 缺少 question_id")
            if qid in overrides: raise RuntimeError(f"题目文本 override question_id 重复: {qid}")
            overrides[qid] = row
    return overrides

def apply_question_text_overrides(items: list[dict[str,Any]], overrides: dict[str,dict[str,Any]], override_source: str|Path) -> list[dict[str,Any]]:
    item_ids = {str(item.get("question_id","")) for item in items}
    unknown_ids = sorted(set(overrides) - item_ids)
    if unknown_ids: raise RuntimeError("题目文本 override 指向不存在的题号: " + ", ".join(unknown_ids))
    applied: list[dict[str,Any]] = []
    for item in items:
        qid = str(item.get("question_id",""))
        override = overrides.get(qid)
        if not override: applied.append(item); continue
        normalized = dict(item)
        normalized["options"] = dict(item.get("options",{}) or {})
        normalized["options_en"] = dict(item.get("options_en",{}) or {})
        audit_options: dict[str,dict[str,Any]] = {}
        option_overrides = override.get("option_overrides",{}) or {}
        if not isinstance(option_overrides, dict) or not option_overrides:
            raise RuntimeError(f"{qid}: override 缺少 option_overrides")
        for raw_label, option_override in option_overrides.items():
            label = str(raw_label).upper()
            if not isinstance(option_override, dict): raise RuntimeError(f"{qid} {label}: option override 必须是对象")
            actual_zh = normalized["options"].get(label)
            actual_en = normalized["options_en"].get(label)
            expected_zh = option_override.get("expected_source_zh")
            expected_en = option_override.get("expected_source_en")
            if actual_zh != expected_zh or actual_en != expected_en:
                raise RuntimeError(f"{qid} {label}: 上游题源文本已变化，拒绝应用 override; 中文 actual={actual_zh!r} expected={expected_zh!r}; 英文 actual={actual_en!r} expected={expected_en!r}")
            display_zh = str(option_override.get("display_zh","")).strip()
            if not display_zh: raise RuntimeError(f"{qid} {label}: 缺少 display_zh")
            normalized["options"][label] = display_zh
            audit_options[label] = {"source_zh": actual_zh, "source_en": actual_en, "display_zh": display_zh, "flags": list(option_override.get("flags",[]) or []), "source_screenshots": dict(option_override.get("source_screenshots",{}) or {}), "reason": str(option_override.get("reason",""))}
        normalized["_question_text_override"] = {"override_source": str(Path(override_source).resolve()), "options": audit_options}
        applied.append(normalized)
    return applied

def load_questions(json_path: str|Path, overrides_path: str|Path|None=QUESTION_TEXT_OVERRIDES_PATH) -> list[dict[str,Any]]:
    print(f"[load] 读取题库: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f: data = json.load(f)
    items = data["items"]
    if overrides_path is not None:
        overrides = load_question_text_overrides(overrides_path)
        items = apply_question_text_overrides(items, overrides, overrides_path)
        print(f"[load] 题目文本 override 已应用 | 共 {len(overrides)} 题")
    print(f"[load] 题库加载完成 | 共 {len(items)} 题")
    return items

def load_chapter_mapping_index(jsonl_path: str|Path) -> dict[str,dict[str,Any]]:
    path = Path(jsonl_path)
    if not path.exists(): raise RuntimeError(f"章节映射文件不存在: {path}")
    index: dict[str,dict[str,Any]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip(): continue
            try: row = json.loads(line)
            except json.JSONDecodeError as exc: raise RuntimeError(f"{path}:{line_no}: JSON 解析失败: {exc}") from exc
            qid = str(row.get("question_id",""))
            if not qid: raise RuntimeError(f"{path}:{line_no}: 缺少 question_id")
            if qid in index: raise RuntimeError(f"章节映射 question_id 重复: {qid}")
            index[qid] = row
    return index

def _append_unique(bucket: list[str], value: str) -> None:
    if value and value not in bucket: bucket.append(value)


def collect_cited_unit_ids(explanation: dict[str, Any]) -> set[str]:
    """从解析结果中收集所有被引用的 unit_id。"""
    uids: set[str] = set()
    if not isinstance(explanation, dict):
        return uids
    core = explanation.get("core_analysis", {}) or {}
    for uid in (core.get("cited_unit_ids", []) or []):
        uids.add(str(uid))
    for row in (explanation.get("option_explanations", []) or []):
        if not isinstance(row, dict):
            continue
        for uid in (row.get("cited_unit_ids", []) or []):
            uids.add(str(uid))
        for sc in (row.get("source_claims", []) or []):
            if isinstance(sc, dict):
                uid = str(sc.get("unit_id", "") or "")
                if uid:
                    uids.add(uid)
    easy = explanation.get("easy_mistake", {}) or {}
    for uid in (easy.get("cited_unit_ids", []) or []):
        uids.add(str(uid))
    return uids


def load_kg_graph(json_path: str|Path) -> dict[str,Any]:
    json_path = Path(json_path)
    print(f"[kg] 读取 KG 母版: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f: kg = json.load(f)
    cp_meta: dict[str,dict[str,Any]] = {}
    unit_meta: dict[str,dict[str,Any]] = {}
    cp_to_units: dict[str,list[str]] = defaultdict(list)
    unit_to_cps: dict[str,list[str]] = defaultdict(list)
    relation_edges_by_cp: dict[str,list[dict[str,Any]]] = defaultdict(list)
    section_to_cps: dict[str,list[str]] = defaultdict(list)
    for unit in kg.get("units",[]):
        uid = unit.get("unit_id","")
        if uid: unit_meta[uid] = unit
    for cp in kg.get("core_points",[]):
        cp_id = cp.get("core_point_id","")
        if not cp_id: continue
        cp_meta[cp_id] = cp
        section_id = cp.get("section_id","")
        if section_id: _append_unique(section_to_cps[section_id], cp_id)
        for key in ("key_unit_ids","anchor_unit_ids","support_unit_ids"):
            for uid in cp.get(key,[]) or []:
                _append_unique(cp_to_units[cp_id], uid)
                _append_unique(unit_to_cps[uid], cp_id)
    relation_scopes = {"same_section_core_point","same_chapter_core_point","cross_chapter_core_point"}
    for edge in kg.get("edges",[]):
        scope, source_id, target_id = edge.get("edge_scope",""), edge.get("source_id",""), edge.get("target_id","")
        if scope == "core_point_unit": _append_unique(cp_to_units[source_id], target_id); _append_unique(unit_to_cps[target_id], source_id)
        elif scope == "section_core_point": _append_unique(section_to_cps[source_id], target_id)
        elif scope in relation_scopes: relation_edges_by_cp[source_id].append(edge); relation_edges_by_cp[target_id].append(edge)
    def unit_sort_key(uid): meta=unit_meta.get(uid,{}); return (meta.get("real_chapter") or meta.get("chapter_id",""), int(meta.get("unit_order") or 0), uid)
    for cp_id, unit_ids in list(cp_to_units.items()): cp_to_units[cp_id] = sorted(unit_ids, key=unit_sort_key)
    print(f"[kg] KG 导航索引就绪 | chapters={len(kg.get('chapters',[]))} | core_points={len(cp_meta)} | units={len(unit_meta)} | edges={len(kg.get('edges',[]))}")
    return {"raw":kg,"cp_meta":cp_meta,"unit_meta":unit_meta,"cp_to_units":dict(cp_to_units),"unit_to_cps":dict(unit_to_cps),"relation_edges_by_cp":dict(relation_edges_by_cp),"section_to_cps":dict(section_to_cps)}

def _normalize_term(text: str) -> str:
    return re.sub(r"\s+"," ",(text or "").strip().lower())

def _term_in_query(term: str, query: str) -> bool:
    term, query = _normalize_term(term), _normalize_term(query)
    if not term or not query: return False
    if re.fullmatch(r"[a-z0-9][a-z0-9_\-/. ]*", term):
        escaped = re.escape(term).replace(r"\ ",r"\s+")
        return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", query) is not None
    return term in query

def load_p5_alias_index(json_path: str|Path) -> dict[str,Any]:
    json_path = Path(json_path)
    print(f"[p5] 读取 P5 术语索引: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f: data = json.load(f)
    aliases: list[dict[str,Any]] = []
    for group in data.get("alias_groups",[]) or []:
        terms: list[str] = []
        for key in ("canonical_en","canonical_zh"):
            value = group.get(key,"")
            if value: terms.append(value)
        for key in ("aliases_en","aliases_zh","all_terms"): terms.extend(group.get(key,[]) or [])
        normalized_terms = sorted({_normalize_term(t) for t in terms if len(_normalize_term(t))>=2}, key=len, reverse=True)
        unit_ids = [uid for uid in group.get("evidence_unit_ids",[]) or [] if uid]
        if normalized_terms and unit_ids:
            aliases.append({"alias_group_id": group.get("alias_group_id",""), "canonical_en": group.get("canonical_en",""), "canonical_zh": group.get("canonical_zh",""), "terms": normalized_terms, "unit_ids": unit_ids, "alias_scope": group.get("alias_scope","")})
    print(f"[p5] P5 术语索引就绪 | alias_groups={len(aliases)}")
    return {"aliases":aliases,"raw":data}

def get_llm_config() -> tuple[str,str,str]:
    for env_name in API_KEY_ENV_NAMES:
        value = os.environ.get(env_name)
        if value:
            base_url = os.environ.get("DEEPSEEK_BASE_URL") or os.environ.get("DS_BASE_URL") or DEFAULT_DEEPSEEK_BASE_URL
            return value, base_url, env_name
    raise RuntimeError(f"{' / '.join(API_KEY_ENV_NAMES)} 环境变量均未设置，不能调用 LLM API。")

def build_queries(question: dict[str,Any]) -> tuple[str,str|None]:
    stem, options = question.get("stem",""), question.get("options",{})
    query_zh = f"{stem} {' '.join(options.values())}".strip()
    stem_en = question.get("stem_en","")
    if not stem_en: return query_zh, None
    options_en = question.get("options_en",{})
    query_en = f"{stem_en} {' '.join(options_en.values())}".strip()
    return query_zh, query_en

def get_bge_model():
    global _BGE_MODEL
    if _BGE_MODEL is not None: return _BGE_MODEL
    from sentence_transformers import SentenceTransformer
    os.environ.setdefault("HF_HUB_OFFLINE","1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE","1")
    _BGE_MODEL = SentenceTransformer("BAAI/bge-m3", local_files_only=True)
    print(f"[bge] BGE-M3 就绪 | dim={_BGE_MODEL.get_embedding_dimension()}")
    return _BGE_MODEL

def _load_kg_units() -> dict[str,dict[str,Any]]:
    global _KG_UNIT_CACHE
    if _KG_UNIT_CACHE is not None: return _KG_UNIT_CACHE
    if not KG_GRAPH_PATH.exists(): _KG_UNIT_CACHE = {}; return _KG_UNIT_CACHE
    with open(KG_GRAPH_PATH, "r", encoding="utf-8") as f: kg = json.load(f)
    _KG_UNIT_CACHE = {}
    for unit in kg.get("units",[]) or []:
        uid = str(unit.get("unit_id","")).strip()
        if uid: _KG_UNIT_CACHE[uid] = unit
    return _KG_UNIT_CACHE

def _compact_text(value: Any, max_len: int=520) -> str:
    text = re.sub(r"\s+"," ",str(value or "")).strip()
    if len(text) <= max_len: return text
    return text[:max_len-1].rstrip() + "…"

__all__ = [
    "BM25",
    "tokenize",
    "load_index", "load_question_text_overrides", "apply_question_text_overrides",
    "load_questions", "load_chapter_mapping_index", "load_kg_graph",
    "load_p5_alias_index",
    "_append_unique", "_normalize_term", "_term_in_query",
    "_load_kg_units", "_compact_text",
    "get_llm_config", "get_bge_model", "build_queries",
    "QUESTIONS_PATH", "INDEX_PKL", "KG_GRAPH_PATH", "P5_ALIAS_INDEX_PATH",
    "QUESTION_TEXT_OVERRIDES_PATH",
    "API_KEY_ENV_NAMES", "DEFAULT_DEEPSEEK_BASE_URL",
]
