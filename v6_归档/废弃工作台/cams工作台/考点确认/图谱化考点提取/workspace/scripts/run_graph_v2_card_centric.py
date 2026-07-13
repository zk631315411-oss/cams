"""v2 图谱化考点提取：以句卡为中心的聚类。

用法：
    python run_graph_v2_card_centric.py --step all        # 跑全流程
    python run_graph_v2_card_centric.py --step edges      # 只构建全量边表
    python run_graph_v2_card_centric.py --step embed      # 只向量化
    python run_graph_v2_card_centric.py --step recall     # 只召回+裁判
    python run_graph_v2_card_centric.py --step cluster    # 只连通分组+组审核
    python run_graph_v2_card_centric.py --step output     # 只命名+回挂+输出

每步会读取上一步的产物，失败可单独重跑。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

# ============================================================
# 路径配置
# ============================================================
# 数据目录（D 盘正式资产，只读）
DATA_DIR = Path(r"D:\守正公司工作区\cams考试\cams工作台\data\teaching_assets")
PAGE_MAP_PATH = Path(r"D:\守正公司工作区\cams考试\cams工作台\data\page_maps\card_page_map_v6.json")

# 工作区根目录（输出到 worktree 内，避免 D 盘沙箱限制）
WORKSPACE_DIR = Path(__file__).resolve().parent.parent  # .../图谱化考点提取/workspace
OUTPUT_DIR = WORKSPACE_DIR / "outputs" / "graph_v2_card_centric"
INTERMEDIATE_DIR = WORKSPACE_DIR / "intermediate" / "graph_v2_card_centric"
REPORTS_DIR = WORKSPACE_DIR / "reports" / "graph_v2_card_centric"
PROMPTS_DIR = WORKSPACE_DIR / "prompts"

# 模型配置
DEFAULT_EMBED_MODEL = "BAAI/bge-large-zh-v1.5"  # 已缓存，立即可用；可换 BAAI/bge-m3
DEFAULT_LLM_MODEL = "deepseek-v4-pro"
DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_API_KEY = "sk-c3bddb398abd4a12bdbb92f421744a88"  # 新 key，已验证可用
RECALL_THRESHOLD = 0.80  # 余弦相似度召回阈值


# ============================================================
# 工具函数
# ============================================================
def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def compact(text: Any, limit: int = 600) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "..."


def slug(text: Any, prefix: str = "id") -> str:
    value = re.sub(r"[^0-9A-Za-z_\-.]+", "_", str(text or "").strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or prefix


def normalize_cards(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("cards", "items", "data"):
            if isinstance(payload.get(key), list):
                return payload[key]
    if isinstance(payload, list):
        return payload
    raise ValueError("Unsupported cards payload")


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


def client_from_env(model_arg: str | None = None) -> tuple[OpenAI, str]:
    # 优先使用脚本内默认配置（已验证可用），环境变量仅作为覆盖选项
    api_key = DEFAULT_API_KEY
    base_url = DEFAULT_BASE_URL
    model = model_arg or DEFAULT_LLM_MODEL
    return OpenAI(api_key=api_key, base_url=base_url), model


def extract_json(text: str) -> Any:
    value = (text or "").strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?\s*", "", value)
        value = re.sub(r"\s*```$", "", value)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        start_obj = value.find("{")
        end_obj = value.rfind("}")
        start_arr = value.find("[")
        end_arr = value.rfind("]")
        if start_obj >= 0 and end_obj > start_obj:
            return json.loads(value[start_obj : end_obj + 1])
        if start_arr >= 0 and end_arr > start_arr:
            return json.loads(value[start_arr : end_arr + 1])
        raise


def call_json(client: OpenAI, model: str, system_prompt: str, user_payload: dict[str, Any], max_tokens: int = 3000) -> tuple[Any, str]:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, indent=2)},
    ]
    # deepseek-v4-pro 关闭思考模式
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": max_tokens,
        "extra_body": {"thinking": {"type": "disabled"}},
    }
    last_exc: Exception | None = None
    for attempt in range(5):  # 增加重试次数到 5
        try:
            response = client.chat.completions.create(**kwargs, response_format={"type": "json_object"})
            text = response.choices[0].message.content or ""
            return extract_json(text), text
        except Exception as primary_exc:
            # 503 时先等待重试，不立即降级
            if "503" in str(primary_exc) and attempt < 4:
                wait = 10 * (attempt + 1)  # 10, 20, 30, 40 秒
                time.sleep(wait)
                continue
            try:
                # 关闭思考模式不支持 response_format 时，回退到普通调用
                response = client.chat.completions.create(**kwargs)
                text = response.choices[0].message.content or ""
                return extract_json(text), text
            except Exception as fallback_exc:
                last_exc = fallback_exc
                if attempt < 4:
                    wait = 10 * (attempt + 1)
                    time.sleep(wait)
    assert last_exc is not None
    raise last_exc


def canonical_card_id(evidence_card: dict[str, Any]) -> str:
    migration = evidence_card.get("card_id_migration") or {}
    to_id = migration.get("to")
    if isinstance(to_id, str) and to_id.startswith("v6s_"):
        return to_id
    card_id = evidence_card.get("card_id") or ""
    return str(card_id)


def fallback_evidence_cards(option: dict[str, Any], cards_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    cards = option.get("evidence_cards") or []
    if cards:
        return [card for card in cards if isinstance(card, dict)]
    result = []
    for cid in option.get("card_ids") or []:
        card = cards_by_id.get(str(cid))
        if card:
            result.append(
                {
                    "card_id": cid,
                    "support_type": option.get("evidence_status") or "",
                    "source": "option.card_ids_fallback",
                    "quote": card.get("citation") or card.get("quote") or "",
                    "reason": "由 option.card_ids 回退生成。",
                    "relevance": "",
                    "knowledge": card.get("knowledge") or "",
                    "citation": card.get("citation") or "",
                    "type": card.get("type") or "",
                    "chapter_path": card.get("chapter_path") or "",
                }
            )
    return result


# ============================================================
# Step 1: 构建全量边表
# ============================================================
def build_full_edges() -> dict[str, Any]:
    """从 option_evidence_map.json 构建全量选项证据边表。"""
    print("[Step 1] 构建全量边表...")
    questions_payload = read_json(DATA_DIR / "questions.json")
    option_evidence = read_json(DATA_DIR / "option_evidence_map.json")
    cards = normalize_cards(read_json(DATA_DIR / "cards_v6_sentence.json"))
    cards_by_id = {card["card_id"]: card for card in cards if card.get("card_id")}
    questions = questions_payload.get("questions") or []
    questions_by_id = {q["id"]: q for q in questions if q.get("id")}
    items = option_evidence.get("items") or []

    all_edges = []
    gaps = []
    seen = set()
    for item in items:
        qid = item.get("question_id")
        question = questions_by_id.get(qid, {})
        for option in item.get("options") or []:
            opt = str(option.get("option") or "")
            is_correct = bool(option.get("is_correct_answer"))
            for evidence_card in fallback_evidence_cards(option, cards_by_id):
                cid = canonical_card_id(evidence_card)
                card = cards_by_id.get(cid)
                if not cid or not card:
                    gaps.append({
                        "question_id": qid, "option": opt,
                        "option_text": option.get("option_text") or "",
                        "original_card_id": evidence_card.get("card_id") or "",
                        "canonical_card_id": cid,
                        "reason": "evidence card cannot be resolved to cards_v6_sentence.json",
                    })
                    continue
                edge_key = (qid, opt, cid)
                if edge_key in seen:
                    continue
                seen.add(edge_key)
                edge_id = slug(f"{qid}_{opt}_{cid}", "edge")
                all_edges.append({
                    "edge_id": edge_id,
                    "question_id": qid,
                    "stem": item.get("stem") or question.get("stem") or "",
                    "answer": item.get("answer") or question.get("answer") or "",
                    "option": opt,
                    "option_text": option.get("option_text") or "",
                    "is_correct_answer": is_correct,
                    "judgement": option.get("judgement") or "",
                    "evidence_status": option.get("evidence_status") or "",
                    "support_type": evidence_card.get("support_type") or option.get("evidence_status") or "",
                    "edge_role": "correct_option_evidence" if is_correct else "incorrect_option_evidence",
                    "canonical_card_id": cid,
                    "original_card_id": evidence_card.get("card_id") or cid,
                    "source": evidence_card.get("source") or "",
                    "relevance": evidence_card.get("relevance") or "",
                    "match_confidence": (evidence_card.get("card_id_migration") or {}).get("confidence", ""),
                    "quote": evidence_card.get("quote") or card.get("citation") or "",
                    "knowledge": evidence_card.get("knowledge") or card.get("knowledge") or "",
                    "citation": evidence_card.get("citation") or card.get("citation") or "",
                    "chapter_path": evidence_card.get("chapter_path") or card.get("chapter_path") or "",
                    "evidence_reason": evidence_card.get("reason") or "",
                    "option_explanation": compact(option.get("explanation"), 500),
                    "common_trap": compact(option.get("common_trap"), 320),
                })

    # 统计
    linked_card_ids = sorted({e["canonical_card_id"] for e in all_edges})
    linked_question_ids = sorted({e["question_id"] for e in all_edges})
    correct_edges = sum(1 for e in all_edges if e["is_correct_answer"])
    incorrect_edges = sum(1 for e in all_edges if not e["is_correct_answer"])

    # 找出无证据边的题目
    all_question_ids = {q["id"] for q in questions if q.get("id")}
    no_evidence_questions = sorted(all_question_ids - set(linked_question_ids))

    summary = {
        "generated_at": now(),
        "total_questions": len(questions),
        "questions_with_edges": len(linked_question_ids),
        "questions_without_edges": len(no_evidence_questions),
        "no_evidence_question_ids": no_evidence_questions,
        "total_edges": len(all_edges),
        "correct_edges": correct_edges,
        "incorrect_edges": incorrect_edges,
        "linked_card_count": len(linked_card_ids),
        "gaps_count": len(gaps),
    }

    write_json(OUTPUT_DIR / "option_evidence_edges.json", {"generated_at": now(), "items": all_edges, "summary": summary})
    write_json(REPORTS_DIR / "evidence_gaps.json", {"generated_at": now(), "items": gaps})
    write_json(INTERMEDIATE_DIR / "linked_card_ids.json", {"generated_at": now(), "card_ids": linked_card_ids})

    print(f"  边表: {len(all_edges)} 条 (正确 {correct_edges} / 错误 {incorrect_edges})")
    print(f"  被链接句卡: {len(linked_card_ids)} 张")
    print(f"  有边题目: {len(linked_question_ids)} / {len(questions)}")
    print(f"  无边题目: {no_evidence_questions}")
    print(f"  回表失败: {len(gaps)}")
    return {"edges": all_edges, "summary": summary, "linked_card_ids": linked_card_ids, "no_evidence_questions": no_evidence_questions}


# ============================================================
# Step 2: 6 题补链接
# ============================================================
def supplement_6q(edges: list[dict[str, Any]], no_evidence_questions: list[str]) -> list[dict[str, Any]]:
    """对无证据边的题目，用向量+BM25 召回 + LLM 裁判补链接。"""
    if not no_evidence_questions:
        print("[Step 2] 无需补链接")
        return edges

    print(f"[Step 2] 补链接 {len(no_evidence_questions)} 题: {no_evidence_questions}")
    questions_payload = read_json(DATA_DIR / "questions.json")
    cards = normalize_cards(read_json(DATA_DIR / "cards_v6_sentence.json"))
    cards_by_id = {c["card_id"]: c for c in cards if c.get("card_id")}
    questions = {q["id"]: q for q in questions_payload.get("questions") or [] if q.get("id")}

    # 向量化所有句卡（用于召回）
    print("  向量化句卡库用于召回...")
    embed_model = load_embedder()
    card_texts = [f"{c.get('knowledge', '')} {c.get('citation', '')}" for c in cards]
    card_ids = [c["card_id"] for c in cards]
    card_vectors = embed_model.encode(card_texts, normalize_embeddings=True, show_progress_bar=False)

    # BM25（可选）
    bm25 = build_bm25(card_texts)

    client, model = client_from_env()
    supplement_prompt = load_prompt("supplement_judge.md")

    new_edges = []
    supplement_results = []
    for qid in no_evidence_questions:
        question = questions.get(qid, {})
        stem = question.get("stem") or ""
        answer = question.get("answer") or ""
        options_raw = question.get("options") or {}
        if isinstance(options_raw, dict):
            options = [{"option": k, "text": v} for k, v in sorted(options_raw.items())]
        elif isinstance(options_raw, list):
            options = [{"option": o.get("option") or o.get("label"), "text": o.get("text") or o.get("option_text", "")} for o in options_raw]
        else:
            options = []

        if not options:
            print(f"    {qid} 无选项，跳过")
            continue

        # 对每个选项，用题干+选项文本召回 top-K 句卡
        for opt in options:
            opt_label = str(opt.get("option") or "")
            opt_text = str(opt.get("text") or "")
            query = f"{stem} {opt_text}"
            query_vec = embed_model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]

            # 向量召回 top-10
            scores_vec = card_vectors @ query_vec
            top_vec = sorted(enumerate(scores_vec), key=lambda x: -x[1])[:10]

            # BM25 召回 top-10
            top_bm25 = []
            if bm25 is not None:
                tokenized_query = list(query)
                bm25_scores = bm25.get_scores(tokenized_query)
                top_bm25 = sorted(enumerate(bm25_scores), key=lambda x: -x[1])[:10]

            # 合并召回
            recall_ids = set()
            recall_candidates = []
            for idx, score in top_vec:
                recall_ids.add(card_ids[idx])
                recall_candidates.append({"card_id": card_ids[idx], "source": "vector", "score": float(score)})
            for idx, score in top_bm25:
                if card_ids[idx] not in recall_ids:
                    recall_ids.add(card_ids[idx])
                    recall_candidates.append({"card_id": card_ids[idx], "source": "bm25", "score": float(score)})

            # 取 top-8 给 LLM 裁判
            recall_candidates = recall_candidates[:8]
            if not recall_candidates:
                continue

            # LLM 裁判
            payload = {
                "question_id": qid,
                "stem": stem,
                "answer": answer,
                "option": opt_label,
                "option_text": opt_text,
                "is_correct_answer": (opt_label == answer),
                "recall_candidates": [
                    {
                        "card_id": rc["card_id"],
                        "knowledge": compact(cards_by_id.get(rc["card_id"], {}).get("knowledge", ""), 200),
                        "citation": compact(cards_by_id.get(rc["card_id"], {}).get("citation", ""), 300),
                        "chapter_path": cards_by_id.get(rc["card_id"], {}).get("chapter_path", ""),
                        "recall_source": rc["source"],
                        "recall_score": round(rc["score"], 4),
                    }
                    for rc in recall_candidates
                ],
            }
            try:
                parsed, raw = call_json(client, model, supplement_prompt, payload, max_tokens=2000)
            except Exception as exc:
                print(f"    {qid} {opt_label} LLM 裁判失败: {exc}")
                continue

            accepted = parsed.get("accepted_cards") or []
            for acc in accepted:
                cid = acc.get("card_id")
                if not cid or cid not in cards_by_id:
                    continue
                card = cards_by_id[cid]
                edge_id = slug(f"{qid}_{opt_label}_{cid}_supp", "edge")
                is_correct = (opt_label == answer)
                new_edges.append({
                    "edge_id": edge_id,
                    "question_id": qid,
                    "stem": stem,
                    "answer": answer,
                    "option": opt_label,
                    "option_text": opt_text,
                    "is_correct_answer": is_correct,
                    "judgement": "correct" if is_correct else "incorrect",
                    "evidence_status": "supplemented",
                    "support_type": acc.get("support_type", "indirect"),
                    "edge_role": "correct_option_evidence" if is_correct else "incorrect_option_evidence",
                    "canonical_card_id": cid,
                    "original_card_id": cid,
                    "source": "supplement_vector_bm25_llm",
                    "relevance": acc.get("relevance", "medium"),
                    "match_confidence": acc.get("confidence", "medium"),
                    "quote": card.get("citation") or "",
                    "knowledge": card.get("knowledge") or "",
                    "citation": card.get("citation") or "",
                    "chapter_path": card.get("chapter_path") or "",
                    "evidence_reason": acc.get("reason", ""),
                    "option_explanation": "",
                    "common_trap": "",
                })

            supplement_results.append({
                "question_id": qid,
                "option": opt_label,
                "recall_count": len(recall_candidates),
                "accepted_count": len(accepted),
                "result": parsed,
            })
            print(f"    {qid} {opt_label}: 召回 {len(recall_candidates)} / 接受 {len(accepted)}")

    # 合并补链接边到全量边表
    all_edges = edges + new_edges
    write_json(OUTPUT_DIR / "option_evidence_edges.json", {"generated_at": now(), "items": all_edges, "supplemented_edges": len(new_edges)})
    write_json(REPORTS_DIR / "supplement_results.json", {"generated_at": now(), "items": supplement_results})

    # 更新被链接句卡列表
    linked_card_ids = sorted({e["canonical_card_id"] for e in all_edges})
    write_json(INTERMEDIATE_DIR / "linked_card_ids.json", {"generated_at": now(), "card_ids": linked_card_ids})

    print(f"  补链接边: {len(new_edges)} 条")
    print(f"  全量边表: {len(all_edges)} 条")
    print(f"  被链接句卡: {len(linked_card_ids)} 张")
    return all_edges


# ============================================================
# Step 3: 句卡向量化
# ============================================================
def load_embedder():
    """加载向量模型。"""
    # 离线模式，避免 HuggingFace Hub 网络检查超时
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    from sentence_transformers import SentenceTransformer
    model_name = os.environ.get("EMBED_MODEL_NAME") or DEFAULT_EMBED_MODEL
    print(f"  加载向量模型: {model_name}")
    return SentenceTransformer(model_name)


def build_bm25(corpus: list[str]):
    """构建 BM25 索引（可选，失败返回 None）。"""
    try:
        from rank_bm25 import BM25Okapi
        tokenized = [list(doc) for doc in corpus]
        return BM25Okapi(tokenized)
    except ImportError:
        print("  [warn] rank_bm25 未安装，跳过 BM25，仅用向量召回")
        return None


def embed_cards(linked_card_ids: list[str]) -> dict[str, Any]:
    """对被链接的句卡向量化。"""
    print(f"[Step 3] 向量化 {len(linked_card_ids)} 张句卡...")
    cards = normalize_cards(read_json(DATA_DIR / "cards_v6_sentence.json"))
    cards_by_id = {c["card_id"]: c for c in cards if c.get("card_id")}

    embed_model = load_embedder()
    card_texts = []
    card_meta = []
    for cid in linked_card_ids:
        card = cards_by_id.get(cid, {})
        text = f"{card.get('knowledge', '')} {card.get('citation', '')}".strip()
        card_texts.append(text)
        card_meta.append({
            "card_id": cid,
            "knowledge": compact(card.get("knowledge", ""), 200),
            "citation": compact(card.get("citation", ""), 300),
            "chapter_path": card.get("chapter_path", ""),
        })

    vectors = embed_model.encode(card_texts, normalize_embeddings=True, show_progress_bar=True)
    print(f"  向量维度: {vectors.shape}")

    # 保存向量（numpy 格式 + JSON 元数据）
    import numpy as np
    np.save(INTERMEDIATE_DIR / "card_vectors.npy", vectors)
    write_json(INTERMEDIATE_DIR / "card_meta.json", {"generated_at": now(), "items": card_meta})
    write_json(INTERMEDIATE_DIR / "card_vectors.json", {
        "generated_at": now(),
        "model": DEFAULT_EMBED_MODEL,
        "dimension": int(vectors.shape[1]),
        "card_ids": linked_card_ids,
    })
    print(f"  向量已保存")
    return {"vectors": vectors, "card_ids": linked_card_ids, "card_meta": card_meta}


# ============================================================
# Step 4: 句卡对召回 + LLM 裁判
# ============================================================
def recall_and_judge(vectors, card_ids: list[str], card_meta: list[dict]) -> dict[str, Any]:
    """句卡对余弦相似度召回 + LLM 裁判。"""
    import numpy as np
    print(f"[Step 4] 句卡对召回 (阈值 ≥ {RECALL_THRESHOLD})...")
    n = len(card_ids)
    sim_matrix = vectors @ vectors.T

    # 召回相似对（上三角，不含对角线）
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            score = float(sim_matrix[i, j])
            if score >= RECALL_THRESHOLD:
                pairs.append({
                    "pair_id": f"{card_ids[i]}__{card_ids[j]}",
                    "card_a_id": card_ids[i],
                    "card_b_id": card_ids[j],
                    "cosine_similarity": round(score, 4),
                })

    pairs.sort(key=lambda x: -x["cosine_similarity"])
    print(f"  召回句卡对: {len(pairs)}")

    if not pairs:
        write_json(INTERMEDIATE_DIR / "card_merge_pairs.json", {"generated_at": now(), "items": [], "recall_threshold": RECALL_THRESHOLD})
        return {"pairs": [], "decisions": []}

    # LLM 裁判
    print(f"  LLM 裁判 {len(pairs)} 对...")
    client, model = client_from_env()
    judge_prompt = load_prompt("card_pair_judge.md")

    meta_by_id = {m["card_id"]: m for m in card_meta}
    decisions = []
    raw_rows = []
    for idx, pair in enumerate(pairs):
        a_meta = meta_by_id.get(pair["card_a_id"], {})
        b_meta = meta_by_id.get(pair["card_b_id"], {})
        payload = {
            "pair_id": pair["pair_id"],
            "card_a": {
                "card_id": pair["card_a_id"],
                "knowledge": a_meta.get("knowledge", ""),
                "citation": a_meta.get("citation", ""),
                "chapter_path": a_meta.get("chapter_path", ""),
            },
            "card_b": {
                "card_id": pair["card_b_id"],
                "knowledge": b_meta.get("knowledge", ""),
                "citation": b_meta.get("citation", ""),
                "chapter_path": b_meta.get("chapter_path", ""),
            },
            "cosine_similarity": pair["cosine_similarity"],
        }
        try:
            parsed, raw = call_json(client, model, judge_prompt, payload, max_tokens=800)
        except Exception as exc:
            print(f"    [{idx+1}/{len(pairs)}] {pair['pair_id']} 裁判失败: {exc}")
            # Fallback：LLM 不可用时，相似度 ≥ 0.85 自动合并
            if pair["cosine_similarity"] >= 0.85:
                parsed = {"merge": True, "confidence": "auto_high_sim", "reason": f"LLM 不可用，相似度 {pair['cosine_similarity']} ≥ 0.85 自动合并"}
            else:
                parsed = {"merge": False, "confidence": "low", "reason": f"LLM 调用失败: {exc}"}
            raw = ""

        decision = {**pair, "decision": parsed}
        decisions.append(decision)
        raw_rows.append({"pair_id": pair["pair_id"], "raw_response": raw})

        if (idx + 1) % 20 == 0:
            print(f"    [{idx+1}/{len(pairs)}] 已裁判")
            # 增量保存
            write_json(INTERMEDIATE_DIR / "card_merge_pairs.json", {"generated_at": now(), "items": decisions, "recall_threshold": RECALL_THRESHOLD})
            write_jsonl(INTERMEDIATE_DIR / "raw_pair_judge_responses.jsonl", raw_rows)

    write_json(INTERMEDIATE_DIR / "card_merge_pairs.json", {"generated_at": now(), "items": decisions, "recall_threshold": RECALL_THRESHOLD})
    write_jsonl(INTERMEDIATE_DIR / "raw_pair_judge_responses.jsonl", raw_rows)

    merge_count = sum(1 for d in decisions if (d.get("decision") or {}).get("merge") is True)
    print(f"  裁判完成: {merge_count}/{len(decisions)} 对判为合并")
    return {"pairs": pairs, "decisions": decisions}


# ============================================================
# Step 5: 连通分组
# ============================================================
class UnionFind:
    def __init__(self, items: list[str]) -> None:
        self.parent = {item: item for item in items}

    def find(self, item: str) -> str:
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]

    def union(self, a: str, b: str) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def groups(self) -> list[list[str]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for item in self.parent:
            grouped[self.find(item)].append(item)
        return list(grouped.values())


def connected_groups(decisions: list[dict[str, Any]], all_card_ids: list[str]) -> list[list[str]]:
    """根据 LLM 裁判结果做连通分组。"""
    print("[Step 5] 连通分组...")
    uf = UnionFind(all_card_ids)
    for decision in decisions:
        result = decision.get("decision") or {}
        if result.get("merge") is True and result.get("confidence") in {"high", "medium", "auto_high_sim"}:
            uf.union(decision["card_a_id"], decision["card_b_id"])

    groups = uf.groups()
    # 按组大小降序
    groups.sort(key=lambda g: -len(g))

    # 统计
    sizes = [len(g) for g in groups]
    print(f"  考点组数: {len(groups)}")
    print(f"  组大小分布: min={min(sizes)}, max={max(sizes)}, avg={sum(sizes)/len(sizes):.1f}")
    print(f"  单句卡组: {sum(1 for s in sizes if s == 1)}")
    print(f"  多句卡组: {sum(1 for s in sizes if s > 1)}")

    write_json(INTERMEDIATE_DIR / "card_clusters.json", {"generated_at": now(), "groups": groups, "group_count": len(groups)})
    return groups


# ============================================================
# Step 6: LLM 组整体审核
# ============================================================
def llm_group_review(groups: list[list[str]], card_meta: list[dict]) -> list[list[str]]:
    """LLM 对多句卡组做整体审核，剔除明显不属于的句卡。"""
    multi_groups = [g for g in groups if len(g) > 1]
    if not multi_groups:
        print("[Step 6] 无多句卡组，跳过组审核")
        return groups

    print(f"[Step 6] LLM 组审核 {len(multi_groups)} 个多句卡组...")
    client, model = client_from_env()
    review_prompt = load_prompt("group_review.md")
    meta_by_id = {m["card_id"]: m for m in card_meta}

    reviewed_groups = []
    review_results = []
    raw_rows = []
    for idx, group in enumerate(groups):
        if len(group) <= 1:
            reviewed_groups.append(group)
            continue

        payload = {
            "group_id": f"group_{idx+1}",
            "cards": [
                {
                    "card_id": cid,
                    "knowledge": meta_by_id.get(cid, {}).get("knowledge", ""),
                    "citation": meta_by_id.get(cid, {}).get("citation", ""),
                    "chapter_path": meta_by_id.get(cid, {}).get("chapter_path", ""),
                }
                for cid in group
            ],
        }
        try:
            parsed, raw = call_json(client, model, review_prompt, payload, max_tokens=1500)
        except Exception as exc:
            print(f"    [{idx+1}] 组审核失败: {exc}")
            parsed = {"keep_cards": group, "remove_cards": [], "reason": "LLM 调用失败，保留原组"}
            raw = ""

        keep = parsed.get("keep_cards") or group
        remove = parsed.get("remove_cards") or []
        reviewed_groups.append(keep)

        review_results.append({
            "group_id": f"group_{idx+1}",
            "original_size": len(group),
            "kept_size": len(keep),
            "removed_cards": remove,
            "reason": parsed.get("reason", ""),
        })
        raw_rows.append({"group_id": f"group_{idx+1}", "raw_response": raw})

        if (idx + 1) % 10 == 0:
            print(f"    [{idx+1}/{len(groups)}] 已审核")

    write_json(INTERMEDIATE_DIR / "group_review_results.json", {"generated_at": now(), "items": review_results})
    write_jsonl(INTERMEDIATE_DIR / "raw_group_review_responses.jsonl", raw_rows)

    # 重新分组（被剔除的句卡成为单句卡组）
    final_groups = [g for g in reviewed_groups if g]
    final_groups.sort(key=lambda g: -len(g))
    print(f"  审核后组数: {len(final_groups)}")

    # 保存审核后的分组（覆盖 card_clusters.json）
    write_json(INTERMEDIATE_DIR / "card_clusters.json", {
        "generated_at": now(),
        "groups": final_groups,
        "group_count": len(final_groups),
        "reviewed": True,
    })
    return final_groups


# ============================================================
# Step 7: LLM 考点命名 + 题目回挂 + 高频统计
# ============================================================
def build_final_output(groups: list[list[str]], card_meta: list[dict], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """LLM 命名 + 题目回挂 + 高频统计。"""
    print("[Step 7] LLM 考点命名 + 题目回挂...")
    client, model = client_from_env()
    name_prompt = load_prompt("group_title_v2.md")
    meta_by_id = {m["card_id"]: m for m in card_meta}

    # 边表按句卡分组，便于回挂
    edges_by_card = defaultdict(list)
    for edge in edges:
        edges_by_card[edge["canonical_card_id"]].append(edge)

    exam_points = []
    raw_rows = []
    for idx, group in enumerate(groups, start=1):
        # 收集组内所有边
        group_edges = []
        for cid in group:
            group_edges.extend(edges_by_card.get(cid, []))

        # 收集组内题目和选项
        linked_question_ids = sorted({e["question_id"] for e in group_edges})
        linked_options = []
        for edge in group_edges:
            linked_options.append({
                "question_id": edge["question_id"],
                "option": edge["option"],
                "option_text": edge["option_text"],
                "is_correct_answer": edge["is_correct_answer"],
                "card_id": edge["canonical_card_id"],
                "edge_role": edge["edge_role"],
            })

        # LLM 命名（单句卡组跳过 LLM，直接用 knowledge 做标题）
        if len(group) == 1:
            fallback_title = meta_by_id.get(group[0], {}).get("knowledge", "") or f"考点 {idx}"
            parsed = {"title": compact(fallback_title, 60), "teaching_focus": "", "reason": "单句卡组，直接用 knowledge 做标题"}
            raw = ""
        else:
            payload = {
                "group_id": f"gep_{idx}",
                "cards": [
                    {
                        "card_id": cid,
                        "knowledge": meta_by_id.get(cid, {}).get("knowledge", ""),
                        "citation": compact(meta_by_id.get(cid, {}).get("citation", ""), 200),
                        "chapter_path": meta_by_id.get(cid, {}).get("chapter_path", ""),
                    }
                    for cid in group
                ],
                "linked_questions": [
                    {"question_id": qid, "stem": compact(next((e["stem"] for e in group_edges if e["question_id"] == qid), ""), 150)}
                    for qid in linked_question_ids
                ],
                "linked_options": linked_options[:20],
            }
            try:
                parsed, raw = call_json(client, model, name_prompt, payload, max_tokens=1000)
            except Exception as exc:
                print(f"    [{idx}] 命名失败: {exc}")
                # Fallback：用组内第一张句卡的 knowledge 做标题
                fallback_title = meta_by_id.get(group[0], {}).get("knowledge", "") or f"考点 {idx}"
                parsed = {"title": compact(fallback_title, 60), "teaching_focus": "", "reason": f"LLM 调用失败，使用句卡 knowledge 做标题: {exc}"}
                raw = ""

        title = parsed.get("title") or f"考点 {idx}"
        point = {
            "id": f"gep_{idx}",
            "title": title,
            "teaching_object_kind": "exam_point",
            "is_exam_point": True,
            "is_high_frequency": len(linked_question_ids) >= 3,
            "linked_question_ids": linked_question_ids,
            "linked_question_count": len(linked_question_ids),
            "source_card_ids": sorted(group),
            "source_card_count": len(group),
            "source_edge_ids": sorted({e["edge_id"] for e in group_edges}),
            "option_bindings": linked_options,
            "teaching_focus": parsed.get("teaching_focus", ""),
            "reason": parsed.get("reason", ""),
            "confidence": parsed.get("confidence", "medium"),
            "generation_source": "graph_v2_card_centric",
            "updated_at": now(),
        }
        exam_points.append(point)
        raw_rows.append({"group_id": f"gep_{idx}", "raw_response": raw})

        if idx % 10 == 0:
            print(f"    [{idx}/{len(groups)}] 已命名")

    # 按题目数降序
    exam_points.sort(key=lambda p: (-p["linked_question_count"], p["title"]))

    write_json(OUTPUT_DIR / "exam_points_graph_v2.json", {"generated_at": now(), "items": exam_points})
    write_jsonl(INTERMEDIATE_DIR / "raw_title_responses_v2.jsonl", raw_rows)

    hf_count = sum(1 for p in exam_points if p["is_high_frequency"])
    print(f"  考点总数: {len(exam_points)}")
    print(f"  高频考点: {hf_count}")
    print(f"  单题考点: {sum(1 for p in exam_points if p['linked_question_count'] == 1)}")
    return exam_points


# ============================================================
# Step 8: 构建报告
# ============================================================
def build_report(exam_points: list[dict[str, Any]], edges: list[dict[str, Any]], groups: list[list[str]], decisions: list[dict[str, Any]]) -> str:
    """生成构建报告。"""
    print("[Step 8] 生成构建报告...")
    hf_points = [p for p in exam_points if p["is_high_frequency"]]
    multi_q_points = [p for p in exam_points if p["linked_question_count"] > 1]
    single_q_points = [p for p in exam_points if p["linked_question_count"] == 1]
    multi_card_points = [p for p in exam_points if p["source_card_count"] > 1]

    sizes = [p["source_card_count"] for p in exam_points]
    merge_count = sum(1 for d in decisions if (d.get("decision") or {}).get("merge") is True)

    lines = [
        "# v2 图谱化考点提取报告（以句卡为中心）",
        "",
        f"- 生成时间：{now()}",
        f"- 方法：v2 以句卡为中心的聚类",
        f"- 向量模型：{DEFAULT_EMBED_MODEL}",
        f"- 召回阈值：余弦相似度 ≥ {RECALL_THRESHOLD}",
        "",
        "## 总体统计",
        "",
        f"- 选项证据边：{len(edges)}",
        f"- 被链接句卡（节点）：{len(set(e['canonical_card_id'] for e in edges))}",
        f"- 句卡对召回：{len(decisions)}",
        f"- LLM 判为合并：{merge_count}",
        f"- 考点组数：{len(exam_points)}",
        f"- 高频考点（≥3题）：{len(hf_points)}",
        f"- 多题考点（>1题）：{len(multi_q_points)}",
        f"- 单题考点：{len(single_q_points)}",
        f"- 多句卡考点（>1句卡）：{len(multi_card_points)}",
        f"- 组大小分布：min={min(sizes)}, max={max(sizes)}, avg={sum(sizes)/len(sizes):.1f}",
        "",
        "## 高频考点",
        "",
    ]
    for p in hf_points[:20]:
        lines += [
            f"### {p['title']}",
            f"- 题目数：{p['linked_question_count']}",
            f"- 题目：{', '.join(p['linked_question_ids'][:10])}",
            f"- 句卡数：{p['source_card_count']}",
            f"- 教学焦点：{p.get('teaching_focus', '')}",
            "",
        ]

    lines += ["## 多题考点（非高频）", ""]
    for p in multi_q_points:
        if not p["is_high_frequency"]:
            lines += [
                f"### {p['title']}",
                f"- 题目数：{p['linked_question_count']}",
                f"- 题目：{', '.join(p['linked_question_ids'])}",
                f"- 句卡数：{p['source_card_count']}",
                "",
            ]

    lines += ["## 单句卡考点（前 30）", ""]
    for p in single_q_points[:30]:
        lines += [
            f"- {p['title']}（{p['linked_question_ids'][0] if p['linked_question_ids'] else '?'}）",
        ]

    report = "\n".join(lines) + "\n"
    (REPORTS_DIR / "build_report.md").write_text(report, encoding="utf-8")
    print(f"  报告已保存: {REPORTS_DIR / 'build_report.md'}")
    return report


# ============================================================
# Prompt 加载
# ============================================================
def load_prompt(name: str) -> str:
    """加载提示词，如果不存在则用内置默认。"""
    path = PROMPTS_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return DEFAULT_PROMPTS.get(name, "")


DEFAULT_PROMPTS = {
    "card_pair_judge.md": """你是教材知识单元裁判。判断两张句卡是否属于同一教学知识单元（即是否应合并为同一个考点）。

裁判标准：
1. 是否指向同一条教材知识。
2. 是否属于同一使用场景或判断逻辑。
3. 教研是否会把它们放在同一个考点下讲。
4. 不能仅因为都属于反洗钱大主题就合并。
5. 如果两张句卡只是同一章节但不指向同一知识点，不合并。

输出 JSON：
{
  "merge": true/false,
  "confidence": "high/medium/low",
  "reason": "判断理由（一句话）"
}""",

    "group_review.md": """你是教材知识单元审核员。给定一个句卡组（可能合并为一个考点），检查组内是否有明显不属于的句卡。

审核标准：
1. 组内句卡应指向同一教学知识单元。
2. 如果某张句卡明显偏离组的核心主题，应剔除。
3. 保守原则：宁可保留，不可误删。只有明显不属于的才剔除。
4. 单句卡组无需审核。

输出 JSON：
{
  "keep_cards": ["card_id1", "card_id2", ...],
  "remove_cards": ["card_id3"],
  "reason": "审核说明"
}""",

    "group_title_v2.md": """你是教研专家。给定一个句卡组（已合并为一个考点）及其关联的题目和选项，生成一个教研可读的考点标题。

标题风格：
- 洗钱处置阶段的典型手法识别
- 第三方关系建立前的反腐败红旗识别
- 代理银行业务中的嵌套关系风险辨析

要求：
1. 标题不应直接照抄某个选项。
2. 标题不应大到"反洗钱基础知识"。
3. 标题应概括组内句卡和题目共同指向的知识点。

输出 JSON：
{
  "title": "考点标题",
  "teaching_focus": "教学焦点（一句话）",
  "reason": "命名理由",
  "confidence": "high/medium/low"
}""",

    "supplement_judge.md": """你是教材证据裁判。给定一道题的一个选项，以及从句卡库召回的候选句卡，判断哪些句卡可以作为该选项的教材证据。

裁判标准：
1. 句卡内容是否与选项表述相关。
2. 句卡是否能支撑或反驳选项的观点。
3. 正确选项：句卡应能直接或间接支撑选项。
4. 错误选项：句卡应能说明选项为何错误（对比证据）。
5. 不相关的句卡不要接受。

输出 JSON：
{
  "accepted_cards": [
    {
      "card_id": "v6s_N00001",
      "support_type": "direct/indirect/negative",
      "relevance": "high/medium/low",
      "confidence": "high/medium/low",
      "reason": "接受理由"
    }
  ],
  "rejected_cards": ["card_id2"],
  "overall_note": "总体说明"
}""",
}


# ============================================================
# 主流程
# ============================================================
def run_step(step: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if step == "edges":
        build_full_edges()
        return

    if step == "supplement":
        edges_data = read_json(OUTPUT_DIR / "option_evidence_edges.json")
        edges = edges_data.get("items") or []
        no_evidence = edges_data.get("summary", {}).get("no_evidence_question_ids") or []
        supplement_6q(edges, no_evidence)
        return

    if step == "embed":
        linked_data = read_json(INTERMEDIATE_DIR / "linked_card_ids.json")
        linked_card_ids = linked_data.get("card_ids") or []
        embed_cards(linked_card_ids)
        return

    if step == "recall":
        import numpy as np
        vectors = np.load(INTERMEDIATE_DIR / "card_vectors.npy")
        linked_data = read_json(INTERMEDIATE_DIR / "linked_card_ids.json")
        linked_card_ids = linked_data.get("card_ids") or []
        meta_data = read_json(INTERMEDIATE_DIR / "card_meta.json")
        card_meta = meta_data.get("items") or []
        recall_and_judge(vectors, linked_card_ids, card_meta)
        return

    if step == "cluster":
        pairs_data = read_json(INTERMEDIATE_DIR / "card_merge_pairs.json")
        decisions = pairs_data.get("items") or []
        linked_data = read_json(INTERMEDIATE_DIR / "linked_card_ids.json")
        linked_card_ids = linked_data.get("card_ids") or []
        groups = connected_groups(decisions, linked_card_ids)
        meta_data = read_json(INTERMEDIATE_DIR / "card_meta.json")
        card_meta = meta_data.get("items") or []
        llm_group_review(groups, card_meta)
        return

    if step == "output":
        clusters_data = read_json(INTERMEDIATE_DIR / "card_clusters.json")
        groups = clusters_data.get("groups") or []
        edges_data = read_json(OUTPUT_DIR / "option_evidence_edges.json")
        edges = edges_data.get("items") or []
        meta_data = read_json(INTERMEDIATE_DIR / "card_meta.json")
        card_meta = meta_data.get("items") or []
        pairs_data = read_json(INTERMEDIATE_DIR / "card_merge_pairs.json")
        decisions = pairs_data.get("items") or []
        exam_points = build_final_output(groups, card_meta, edges)
        build_report(exam_points, edges, groups, decisions)
        return

    # step == "all"：顺序执行全部
    result = build_full_edges()
    edges = result["edges"]
    no_evidence = result["no_evidence_questions"]
    edges = supplement_6q(edges, no_evidence)
    linked_card_ids = sorted({e["canonical_card_id"] for e in edges})
    embed_result = embed_cards(linked_card_ids)
    recall_result = recall_and_judge(embed_result["vectors"], linked_card_ids, embed_result["card_meta"])
    groups = connected_groups(recall_result["decisions"], linked_card_ids)
    groups = llm_group_review(groups, embed_result["card_meta"])
    exam_points = build_final_output(groups, embed_result["card_meta"], edges)
    build_report(exam_points, edges, groups, recall_result["decisions"])
    print("\n完成。")


def main() -> None:
    parser = argparse.ArgumentParser(description="v2 图谱化考点提取：以句卡为中心")
    parser.add_argument("--step", default="all",
                        choices=["all", "edges", "supplement", "embed", "recall", "cluster", "output"],
                        help="执行到哪一步")
    parser.add_argument("--model", default=None, help="LLM 模型名")
    args = parser.parse_args()
    if args.model:
        os.environ["LLM_MODEL_NAME"] = args.model
    run_step(args.step)


if __name__ == "__main__":
    main()
