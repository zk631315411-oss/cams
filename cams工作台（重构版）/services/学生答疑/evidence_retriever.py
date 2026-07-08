from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_WORKBENCH_DIR = _HERE.parent  # services/
_NEW_QUESTION_DIR = _HERE.parent / "新题解析"
if str(_NEW_QUESTION_DIR) not in sys.path:
    sys.path.insert(0, str(_NEW_QUESTION_DIR))

_EVIDENCE_POOL_MODULE: Any | None = None
_AGENTIC_MODULE: Any | None = None
_RUN_STEP1_MODULE: Any | None = None


def retrieve_evidence(
    parsed_input: dict[str, Any],
    question_match: dict[str, Any],
    top_k: int = 16,
    max_evidence: int = 18,
) -> dict[str, Any]:
    rt = get_runtime()
    agentic = get_agentic_module()

    matched_question = _matched_question(question_match)
    stem = matched_question.get("stem") or parsed_input.get("stem", "")
    options = matched_question.get("options") or parsed_input.get("options", {}) or {}
    student_question = parsed_input.get("student_question", "")
    answer_labels = _answer_labels(matched_question.get("answer", ""), set(options))
    mentioned_labels = [label for label in parsed_input.get("mentioned_options", []) if label in options]

    target_labels = _dedupe(mentioned_labels + answer_labels)
    if not target_labels:
        target_labels = list(options)[:4]
    if not target_labels:
        target_labels = ["GENERAL"]

    candidates_by_target: dict[str, list[dict[str, Any]]] = {}
    diagnostics: list[dict[str, Any]] = []
    for label in target_labels:
        option_text = options.get(label, "") if label != "GENERAL" else ""
        plan = _build_option_plan(
            stem=stem,
            option_label=label,
            option_text=option_text,
            student_question=student_question,
            answer_labels=answer_labels,
            options=options,
        )
        query_text = " ".join(part for part in [student_question, option_text, stem] if part)
        candidates, diag = agentic.retrieve_for_option(rt, stem, query_text, plan, top_k=top_k)
        hint_candidates = _stage_hint_direct_candidates(rt, agentic, option_text, student_question)
        if hint_candidates:
            candidates = _merge_candidate_lists(candidates, hint_candidates, top_k=top_k)
            diag["stage_hint_direct_ids"] = [row.get("card_id") for row in hint_candidates]
        candidates_by_target[label] = candidates
        diagnostics.append({"target": label, "diagnostics": diag, "candidate_ids": [c.get("card_id") for c in candidates]})

    evidence = _flatten_candidates(candidates_by_target)[:max_evidence]
    return {
        "targets": target_labels,
        "answer_labels": answer_labels,
        "mentioned_labels": mentioned_labels,
        "candidates_by_target": {
            label: [_serializable_card(row, include_text=False) for row in rows]
            for label, rows in candidates_by_target.items()
        },
        "evidence": [_serializable_card(row, include_text=True) for row in evidence],
        "evidence_count": len(evidence),
        "diagnostics": diagnostics,
    }


def retrieve_evidence_for_claims(
    parsed_input: dict[str, Any],
    question_match: dict[str, Any],
    claim_plan: dict[str, Any],
    top_k: int = 12,
    max_total_cards: int = 40,
) -> dict[str, Any]:
    rt = get_runtime()
    agentic = get_agentic_module()
    matched_question = _matched_question(question_match)
    stem = matched_question.get("stem") or parsed_input.get("stem", "")

    candidates_by_claim: dict[str, list[dict[str, Any]]] = {}
    diagnostics: list[dict[str, Any]] = []
    for claim in claim_plan.get("claims", []):
        claim_id = str(claim.get("claim_id", "")).strip()
        if not claim_id:
            continue
        option_text = " ".join(
            str(part or "")
            for part in [
                claim.get("claim", ""),
                claim.get("success_criteria", ""),
                " ".join(claim.get("must_terms", []) or []),
            ]
        )
        plan = _build_claim_option_plan(stem, claim)
        candidates, diag = agentic.retrieve_for_option(rt, stem, option_text, plan, top_k=top_k)
        candidates_by_claim[claim_id] = [_attach_claim(row, claim_id) for row in candidates]
        diagnostics.append({"claim_id": claim_id, "diagnostics": diag, "candidate_ids": [c.get("card_id") for c in candidates]})

    evidence = _flatten_claim_candidates(candidates_by_claim)[:max_total_cards]
    return {
        "claims": claim_plan.get("claims", []),
        "candidates_by_claim": {
            claim_id: [_serializable_card(row, include_text=True) for row in rows]
            for claim_id, rows in candidates_by_claim.items()
        },
        "evidence": [_serializable_card(row, include_text=True) for row in evidence],
        "evidence_count": len(evidence),
        "diagnostics": diagnostics,
        "top_k_per_claim": top_k,
        "max_total_cards": max_total_cards,
    }


def get_runtime() -> Any:
    pool = _load_evidence_pool_module()
    return pool.get_agentic_runtime()


def get_agentic_module() -> Any:
    global _AGENTIC_MODULE
    if _AGENTIC_MODULE is None:
        _load_evidence_pool_module()
        import run_agentic_search_experiment as agentic

        _AGENTIC_MODULE = agentic
    return _AGENTIC_MODULE


def get_run_step1_module() -> Any:
    global _RUN_STEP1_MODULE
    if _RUN_STEP1_MODULE is None:
        _load_evidence_pool_module()
        import run_step1

        _RUN_STEP1_MODULE = run_step1
    return _RUN_STEP1_MODULE


def _load_evidence_pool_module() -> Any:
    global _EVIDENCE_POOL_MODULE
    if _EVIDENCE_POOL_MODULE is not None:
        return _EVIDENCE_POOL_MODULE

    evidence_pool_path = _find_new_question_evidence_pool()
    spec = importlib.util.spec_from_file_location("student_qa_new_question_evidence_pool", evidence_pool_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import evidence_pool from {evidence_pool_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _EVIDENCE_POOL_MODULE = module
    return module


def _find_new_question_evidence_pool() -> Path:
    path = _NEW_QUESTION_DIR / "evidence_pool.py"
    if not path.exists():
        raise FileNotFoundError(f"Cannot find evidence_pool.py at {path}")
    return path


def _matched_question(question_match: dict[str, Any]) -> dict[str, Any]:
    best = question_match.get("best") if question_match.get("matched") else None
    if not best:
        return {}
    question = best.get("question", {})
    return question if isinstance(question, dict) else {}


def _answer_labels(answer: str, valid_labels: set[str]) -> list[str]:
    labels = []
    for label in str(answer or "").upper():
        if label in valid_labels and label not in labels:
            labels.append(label)
    return labels


def _build_option_plan(
    stem: str,
    option_label: str,
    option_text: str,
    student_question: str,
    answer_labels: list[str],
    options: dict[str, str],
) -> dict[str, Any]:
    correct_option_text = " ".join(options.get(label, "") for label in answer_labels if options.get(label, ""))
    stage_queries = _stage_hint_queries(option_text, student_question)
    queries = _dedupe(
        stage_queries
        + [
            student_question,
            f"{option_text} {student_question}",
            option_text,
            f"{stem} {student_question}",
            f"{correct_option_text} {student_question}",
            correct_option_text,
            stem,
        ]
    )
    return {
        "option": option_label,
        "option_claim": option_text or student_question,
        "evidence_need": f"解释学生疑问：{student_question}",
        "search_queries": [query for query in queries if query],
        "must_terms": _keywords(" ".join([student_question, option_text, correct_option_text])),
        "related_terms": _keywords(stem)[:6],
        "contrast_terms": [],
        "avoid_confusions": [],
    }


def _build_claim_option_plan(stem: str, claim: dict[str, Any]) -> dict[str, Any]:
    claim_text = str(claim.get("claim", "")).strip()
    queries = _dedupe(
        [str(query).strip() for query in claim.get("search_queries", []) or []]
        + [
            claim_text,
            str(claim.get("success_criteria", "")).strip(),
            f"{stem} {claim_text}",
            " ".join(str(term).strip() for term in claim.get("must_terms", []) or []),
        ]
    )
    return {
        "option": str(claim.get("option", "")).strip(),
        "option_claim": claim_text,
        "evidence_need": str(claim.get("success_criteria", "") or claim_text).strip(),
        "search_queries": [query for query in queries if query],
        "must_terms": [str(term).strip() for term in claim.get("must_terms", []) or [] if str(term).strip()],
        "related_terms": _keywords(stem)[:6],
        "contrast_terms": [],
        "avoid_confusions": [],
    }


def _keywords(text: str, limit: int = 10) -> list[str]:
    agentic = get_agentic_module()
    phrases = agentic.extract_phrases(text or "")
    return [str(item) for item in phrases[:limit]]


def _stage_hint_queries(option_text: str, student_question: str) -> list[str]:
    text = f"{option_text} {student_question}"
    queries: list[str] = []
    if any(token in text for token in ("存入", "存款", "账户", "现金", "放入", "投入金融系统")):
        queries.extend(
            [
                "处置 阶段 洗钱 非法所得 投入 金融系统",
                "处置交易 现金 存入 银行账户",
            ]
        )
    if any(token in text for token in ("转到", "转账", "转移", "多层", "多笔", "多家银行")):
        queries.append("离析 阶段 洗钱 资金转移 多层交易 掩盖来源")
    if any(token in text for token in ("购买", "豪车", "奢侈", "房产", "不动产", "投资")):
        queries.extend(
            [
                "融合 阶段 投资 不动产 奢侈资产 合法财富",
                "融合阶段 将资金重新投入经济活动 表面合法性",
            ]
        )
    if any(token in text for token in ("前沿公司", "空壳公司", "公司", "信托", "复杂法律安排")):
        queries.append("空壳公司 复杂法律安排 模糊 犯罪所得 受益所有人")
    return queries


def _stage_hint_direct_candidates(rt: Any, agentic: Any, option_text: str, student_question: str, top_k: int = 8) -> list[dict[str, Any]]:
    phrases = _stage_hint_phrases(option_text, student_question)
    if not phrases:
        return []
    rows: list[dict[str, Any]] = []
    for rank, (cid, score) in enumerate(agentic.exact_phrase_search(rt, phrases, top_k=top_k), start=1):
        card = rt.card_by_id.get(cid)
        if not card:
            continue
        rows.append(
            {
                "card_id": cid,
                "score": round(220.0 + float(score) + 1 / rank, 4),
                "source": "stage_hint_exact",
                "sources": [{"source": "stage_hint_exact", "score": score, "query": " | ".join(phrases[:4])}],
                "type": card.get("type", ""),
                "knowledge": card.get("knowledge", ""),
                "citation": card.get("citation", ""),
                "context_before": card.get("context_before", ""),
                "context_after": card.get("context_after", ""),
                "text": agentic.card_text(card),
            }
        )
    return rows


def _stage_hint_phrases(option_text: str, student_question: str) -> list[str]:
    text = f"{option_text} {student_question}"
    phrases: list[str] = []
    if any(token in text for token in ("存入", "存款", "账户", "现金", "放入", "投入金融系统")):
        phrases.extend(
            [
                "阶段一：处置",
                "洗钱者将非法所得投入金融系统中",
                "现金拆分：将现金分为多笔小数额，存入多个银行账户",
            ]
        )
    if any(token in text for token in ("转到", "转账", "转移", "多层", "多笔", "多家银行")):
        phrases.extend(["阶段二：离析", "通过制造复杂的金融交易层次"])
    if any(token in text for token in ("购买", "豪车", "奢侈", "房产", "不动产", "投资")):
        phrases.extend(["阶段三：融合", "将资金重新投入到经济活动中", "投资于不动产、风险投资或奢侈资产"])
    if any(token in text for token in ("前沿公司", "空壳公司", "公司", "信托", "复杂法律安排")):
        phrases.extend(["利用空壳公司，掩盖最终受益所有人和资产", "创建并管理公司及其他复杂的法律安排"])
    return _dedupe(phrases)


def _merge_candidate_lists(existing: list[dict[str, Any]], extra: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {row.get("card_id"): dict(row) for row in existing if row.get("card_id")}
    for row in extra:
        cid = row.get("card_id")
        if not cid:
            continue
        if cid in merged:
            merged[cid]["score"] = max(float(merged[cid].get("score", 0)), float(row.get("score", 0)))
            merged[cid]["source"] = "+".join(_dedupe([str(merged[cid].get("source", "")), str(row.get("source", ""))]))
            merged[cid].setdefault("sources", []).extend(row.get("sources", []))
        else:
            merged[cid] = row
    return sorted(merged.values(), key=lambda item: float(item.get("score", 0)), reverse=True)[:top_k]


def _flatten_candidates(candidates_by_target: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for target, rows in candidates_by_target.items():
        for row in rows:
            cid = row.get("card_id")
            if not cid:
                continue
            if cid not in seen:
                item = dict(row)
                item["target_labels"] = [target]
                seen[cid] = item
            else:
                seen[cid]["score"] = max(float(seen[cid].get("score", 0)), float(row.get("score", 0)))
                seen[cid].setdefault("target_labels", []).append(target)
    return sorted(seen.values(), key=lambda item: float(item.get("score", 0)), reverse=True)


def _attach_claim(row: dict[str, Any], claim_id: str) -> dict[str, Any]:
    item = dict(row)
    item["claim_ids"] = [claim_id]
    return item


def _flatten_claim_candidates(candidates_by_claim: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for claim_id, rows in candidates_by_claim.items():
        for row in rows:
            cid = row.get("card_id")
            if not cid:
                continue
            if cid not in seen:
                item = dict(row)
                item["claim_ids"] = [claim_id]
                seen[cid] = item
            else:
                seen[cid]["score"] = max(float(seen[cid].get("score", 0)), float(row.get("score", 0)))
                seen[cid].setdefault("claim_ids", []).append(claim_id)
    return sorted(seen.values(), key=lambda item: float(item.get("score", 0)), reverse=True)


def _serializable_card(row: dict[str, Any], include_text: bool) -> dict[str, Any]:
    keys = [
        "card_id",
        "score",
        "source",
        "type",
        "knowledge",
        "citation",
        "context_before",
        "context_after",
        "target_labels",
        "claim_ids",
    ]
    if include_text:
        keys.append("text")
    return {key: row.get(key) for key in keys if key in row}


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        item = str(item or "").strip()
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
