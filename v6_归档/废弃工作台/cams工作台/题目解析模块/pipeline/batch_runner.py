"""批量匹配入口：解析习题 md → 逐题证据检索 → 合并写回 question_card_map.json。

用法
----
单章节验证（推荐先跑一个章节）::

    cd 题目解析模块
    python -m pipeline.batch_runner --sections 3.1

多章节批量::

    python -m pipeline.batch_runner --sections 3.1 3.2 3.3 4.1

全教材（第 3/4/5/6 章）::

    python -m pipeline.batch_runner --all

只迁移/重建第二章（用 v6s 全书句卡重跑第二章）::

    python -m pipeline.batch_runner --sections 2.1 2.2 2.3 2.4 2.5 2.6 2.7 2.8

合并策略
--------
读旧 question_card_map.json 的 mappings → 按 question_id 覆盖/追加新匹配 → 写回。
第二章旧映射（v6_b##_N##）会被重跑后的 v6s_* 覆盖，自动完成 ID 迁移。
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import sys
import threading
import time
from pathlib import Path
from typing import Any

# 加载工作区 .env（DEEPSEEK_API_KEY），必须在任何 pipeline 导入之前
_MODULE_DIR_PRE = Path(__file__).resolve().parents[1]
_ENV_SETUP = _MODULE_DIR_PRE / "env_setup.py"
if _ENV_SETUP.exists():
    import importlib.util as _ilu
    _spec_env = _ilu.spec_from_file_location("_env_setup", _ENV_SETUP)
    _mod_env = _ilu.module_from_spec(_spec_env)
    _spec_env.loader.exec_module(_mod_env)
    _mod_env._load_env()

from pipeline.evidence_pool import get_match_runtime
from pipeline.match_pipeline import match_one_question, to_question_card_map_entry, refine_match_with_llm
from pipeline.question_loader import Question, load_questions

_MODULE_DIR = Path(__file__).resolve().parents[1]
_WORKBENCH = _MODULE_DIR.parent
_TEACHING_ASSETS = _WORKBENCH / "data" / "teaching_assets"
_EXERCISE_ROOT = _WORKBENCH.parent / "教材、答疑记录、习题与参考文献" / "习题"
# 全部习题 md（2_1_习题.md / 3.1_习题集.md / 6.xxx_习题集.md）均在"习题结构化"目录。
# 兼容旧布局：若"习题结构化提取"存在也一并扫描。
_MD_DIRS = [d for d in [
    _EXERCISE_ROOT / "习题结构化",
    _EXERCISE_ROOT / "习题结构化提取",
] if d.exists()]
_QUESTION_CARD_MAP = _TEACHING_ASSETS / "question_card_map.json"
_OPTION_EVIDENCE_MAP = _TEACHING_ASSETS / "option_evidence_map.json"
_REPORTS_DIR = _MODULE_DIR / "outputs" / "reports"

ALL_CHAPTER_SECTIONS = [
    "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8",
    "3.1", "3.2", "3.3", "3.4", "3.5", "3.6",
    "4.1", "4.2", "4.3", "4.4", "4.5",
    "5.1", "5.2", "5.3",
    "6.",  # 第6章所有主题（6.KYC/6.空壳银行/...）
]


def _load_existing_mappings() -> dict[str, Any]:
    """读旧 question_card_map.json，返回 mappings 字典（不存在则空）。"""
    if not _QUESTION_CARD_MAP.exists():
        return {}
    payload = json.loads(_QUESTION_CARD_MAP.read_text(encoding="utf-8"))
    return payload.get("mappings", {}) if isinstance(payload, dict) else {}


def _save_question_card_map(mappings: dict[str, Any], run_meta: dict[str, Any]) -> None:
    """合并写回 question_card_map.json，保留 asset_note 并追加 migrations 记录。"""
    _TEACHING_ASSETS.mkdir(parents=True, exist_ok=True)
    asset_note = (
        "题目级候选考点映射（v6s 全书句卡坐标系）。由题目解析模块批量匹配生成，"
        "matched_card_ids 为 v6s_N##### 格式。可作考点/高频考点生成的输入池。"
    )
    payload: dict[str, Any] = {
        "asset_note": asset_note,
        "mappings": mappings,
    }
    if _QUESTION_CARD_MAP.exists():
        old = json.loads(_QUESTION_CARD_MAP.read_text(encoding="utf-8"))
        if isinstance(old, dict) and isinstance(old.get("migrations"), list):
            payload["migrations"] = old["migrations"]
        else:
            payload["migrations"] = []
    else:
        payload["migrations"] = []
    payload["migrations"].append(run_meta)

    tmp = _QUESTION_CARD_MAP.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(_QUESTION_CARD_MAP)


def _load_existing_option_items() -> list[dict[str, Any]]:
    """读旧 option_evidence_map.json 的 items 列表（不存在则空）。"""
    if not _OPTION_EVIDENCE_MAP.exists():
        return []
    payload = json.loads(_OPTION_EVIDENCE_MAP.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        items = payload.get("items", [])
        return items if isinstance(items, list) else []
    return []


def _build_option_evidence_item(
    question: Question,
    match_result: dict[str, Any],
) -> dict[str, Any] | None:
    """把 match_one_question 的 option_analysis 转成 option_evidence_map.json 的 item 格式。

    与现有 option_evidence_map.json 兼容（schema_version: question_option_card_map_v1）。
    """
    option_analysis = match_result.get("option_analysis", [])
    if not option_analysis:
        return None

    options_payload: list[dict[str, Any]] = []
    for row in option_analysis:
        label = row.get("option", "")
        ev_cards = row.get("evidence_cards", []) or []
        options_payload.append({
            "option": label,
            "option_text": row.get("option_text", question.options.get(label, "")),
            "is_correct_answer": row.get("judgement") == "correct",
            "judgement": row.get("judgement", "needs_manual"),
            "judgement_confidence": row.get("judgement_confidence", ""),
            "evidence_status": row.get("evidence_status", "none"),
            "card_ids": [c.get("card_id", "") for c in ev_cards if c.get("card_id")],
            "evidence_cards": [
                {
                    "card_id": c.get("card_id", ""),
                    "support_type": c.get("support_type", ""),
                    "source": c.get("source", ""),
                    "quote": c.get("quote", ""),
                    "reason": c.get("reason", ""),
                    "relevance": c.get("relevance", ""),
                }
                for c in ev_cards
            ],
            "explanation": row.get("explanation", ""),
            "common_trap": row.get("common_trap", ""),
        })

    return {
        "question_id": question.id,
        "stem": question.stem,
        "answer": question.answer,
        "status": "answered" if question.answer else "unanswered",
        "evidence_scope": "v6_sentence",
        "evidence_file": str(_TEACHING_ASSETS / "cards_v6_sentence.json"),
        "source": "题目解析模块",
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "options": options_payload,
    }


def _save_option_evidence_map(
    new_items: list[dict[str, Any]],
    run_meta: dict[str, Any],
) -> tuple[int, int]:
    """合并写回 option_evidence_map.json。

    Returns
    -------
    (total_items, new_count)
    """
    _TEACHING_ASSETS.mkdir(parents=True, exist_ok=True)
    existing_items = _load_existing_option_items()
    existing_by_qid = {it.get("question_id"): it for it in existing_items if isinstance(it, dict)}

    overwritten = 0
    for item in new_items:
        qid = item.get("question_id", "")
        if qid in existing_by_qid:
            overwritten += 1
        existing_by_qid[qid] = item
    merged_items = list(existing_by_qid.values())

    old_payload = {}
    if _OPTION_EVIDENCE_MAP.exists():
        old = json.loads(_OPTION_EVIDENCE_MAP.read_text(encoding="utf-8"))
        if isinstance(old, dict):
            old_payload = old

    payload: dict[str, Any] = {
        "asset_note": "选项级教材证据绑定（v6s 全书句卡坐标系）。含 AI 解析、易错点、证据句卡。",
        "schema_version": "question_option_card_map_v1",
        "items": merged_items,
    }
    migrations = old_payload.get("migrations", [])
    if not isinstance(migrations, list):
        migrations = []
    migrations.append(run_meta)
    payload["migrations"] = migrations

    tmp = _OPTION_EVIDENCE_MAP.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(_OPTION_EVIDENCE_MAP)
    return len(merged_items), overwritten


def _save_report(report: dict[str, Any], sections: list[str]) -> Path:
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"batch_match_{'-'.join(sections)}_{stamp}.json" if sections else f"batch_match_all_{stamp}.json"
    path = _REPORTS_DIR / name
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run_batch(
    sections: list[str] | None = None,
    use_planner: bool = True,
    top_k: int = 30,
    dry_run: bool = False,
    generate_analysis: bool = False,
    max_workers: int = 4,
    match_only: bool = False,
) -> dict[str, Any]:
    """批量匹配入口。

    Parameters
    ----------
    sections : list[str] | None
        指定小节（如 ["3.1"]）。None 表示全部（ALL_CHAPTER_SECTIONS）。
    use_planner : bool
        True=调 LLM planner（慢、质量高）；False=简单 plan（快、无 LLM）。
    top_k : int
        每选项最多召回候选数。
    dry_run : bool
        True=只检索不写回，输出报告供检查。
    generate_analysis : bool
        True=在检索后追加 LLM 调用，基于已知答案生成选项级解析
        （explanation/common_trap/evidence_cards），写回 option_evidence_map.json。
    max_workers : int
        并发线程数。每题主要是 LLM 调用（IO 密集），线程并发可大幅提速。
        建议值：4-8。太高可能触发 API 限流。
    match_only : bool
        True=三段式拼装模式，只跑 planner+检索（1次LLM/题），不调 adjudicator。
        explanation 用教研解析，evidence_cards 用检索候选，common_trap 留空待补。
        与 generate_analysis 互斥；match_only=True 时 generate_analysis 被忽略。

    Returns
    -------
    dict  批量匹配报告
    """
    if sections is None:
        sections = ALL_CHAPTER_SECTIONS

    print(f"[batch_runner] 加载习题 md | sections={sections} | md_dirs={_MD_DIRS}")
    questions = load_questions(_MD_DIRS, sections=sections)
    if not questions:
        print("[batch_runner] 未加载到任何题目，检查 md 目录与小节前缀。")
        return {"status": "no_questions", "sections": sections}

    print(
        f"[batch_runner] 共 {len(questions)} 题 | planner={use_planner} | "
        f"top_k={top_k} | match_only={match_only} | generate_analysis={generate_analysis} | workers={max_workers}"
    )
    print("[batch_runner] 加载全书句卡 runtime（首次约 30-60 秒）...")
    rt = get_match_runtime()
    print(f"[batch_runner] runtime 就绪：{len(rt.card_ids)} 张句卡")

    existing_mappings = _load_existing_mappings()
    new_mappings: dict[str, Any] = {}
    new_option_items: list[dict[str, Any]] = []
    print_lock = threading.Lock()
    progress = {"done": 0}

    def _process_one(idx_q: tuple[int, Question]) -> tuple[int, Question, dict[str, Any]]:
        i, q = idx_q
        match_result = match_one_question(
            q, rt=rt, top_k=top_k, use_planner=use_planner,
            generate_analysis=generate_analysis,
            match_only=match_only,
        )
        with print_lock:
            progress["done"] += 1
            done = progress["done"]
            entry = to_question_card_map_entry(match_result, q)
            status = match_result.get("status", "ok")
            n_cards = len(entry["matched_card_ids"])
            elapsed = match_result.get("elapsed_ms", 0)
            analysis_flag = "解析✓" if match_result.get("analysis_generated") else "解析✗"
            print(
                f"  [{done}/{len(questions)}] {q.id} | {status} | {n_cards} 张 | "
                f"{elapsed:.0f}ms | {analysis_flag} | kp={entry['knowledge_point'][:25]}"
            )
        return i, q, match_result

    t0 = time.time()
    write_option_evidence = generate_analysis or match_only
    if max_workers > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_process_one, (i, q)): i
                for i, q in enumerate(questions, 1)
            }
            for future in concurrent.futures.as_completed(futures):
                i, q, match_result = future.result()
                entry = to_question_card_map_entry(match_result, q)
                new_mappings[q.id] = entry
                if write_option_evidence:
                    item = _build_option_evidence_item(q, match_result)
                    if item:
                        new_option_items.append(item)
    else:
        for i, q in enumerate(questions, 1):
            i, q, match_result = _process_one((i, q))
            entry = to_question_card_map_entry(match_result, q)
            new_mappings[q.id] = entry
            if write_option_evidence:
                item = _build_option_evidence_item(q, match_result)
                if item:
                    new_option_items.append(item)

    total_elapsed = time.time() - t0

    # ---- 合并：旧 mappings + 新 mappings（新覆盖旧） ----
    merged_mappings = dict(existing_mappings)
    overwritten = 0
    for qid, entry in new_mappings.items():
        if qid in merged_mappings:
            overwritten += 1
        merged_mappings[qid] = entry

    # 统计 ID 前缀
    all_ids = [cid for entry in merged_mappings.values() for cid in entry.get("matched_card_ids", [])]
    id_prefix_stats = {
        "v6s": sum(1 for cid in all_ids if cid.startswith("v6s_")),
        "v6_b": sum(1 for cid in all_ids if cid.startswith("v6_b")),
        "ch2s": sum(1 for cid in all_ids if cid.startswith("ch2s_")),
        "other": sum(1 for cid in all_ids if not any(cid.startswith(p) for p in ("v6s_", "v6_b", "ch2s_"))),
    }

    questions_with_match = sum(1 for e in new_mappings.values() if e.get("matched_card_ids"))
    total_card_links = sum(len(e.get("matched_card_ids", [])) for e in new_mappings.values())
    questions_with_analysis = len(new_option_items)

    report = {
        "run_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "sections": sections,
        "use_planner": use_planner,
        "top_k": top_k,
        "dry_run": dry_run,
        "generate_analysis": generate_analysis,
        "match_only": match_only,
        "questions_loaded": len(questions),
        "questions_matched": questions_with_match,
        "questions_with_analysis": questions_with_analysis,
        "total_card_links_new": total_card_links,
        "overwrote_existing": overwritten,
        "total_mappings_after_merge": len(merged_mappings),
        "id_prefix_stats_after_merge": id_prefix_stats,
        "elapsed_s": round(total_elapsed, 1),
        "avg_per_question_ms": round(total_elapsed * 1000 / max(len(questions), 1), 1),
    }

    if dry_run:
        print("[batch_runner] dry_run=True，不写回 question_card_map.json / option_evidence_map.json")
    else:
        run_meta = {
            "name": "题目解析模块批量匹配",
            "generated_at": report["run_at"],
            "scope": f"sections={sections}",
            "use_planner": use_planner,
            "generate_analysis": generate_analysis,
            "match_only": match_only,
            "questions": len(questions),
            "overwrote_existing": overwritten,
        }
        _save_question_card_map(merged_mappings, run_meta)
        print(f"[batch_runner] 已写回 {_QUESTION_CARD_MAP.name} | 合并后 {len(merged_mappings)} 条映射")
        # match_only 和 generate_analysis 都写回 option_evidence_map
        if (match_only or generate_analysis) and new_option_items:
            total_items, opt_overwritten = _save_option_evidence_map(new_option_items, run_meta)
            print(
                f"[batch_runner] 已写回 {_OPTION_EVIDENCE_MAP.name} | "
                f"合并后 {total_items} 条 item（本次新增/覆盖 {len(new_option_items)} 条）"
            )
            report["option_evidence_total"] = total_items
            report["option_evidence_overwritten"] = opt_overwritten

    report_path = _save_report(report, sections)
    print(f"[batch_runner] 报告 → {report_path}")
    print(
        f"[batch_runner] 完成：{questions_with_match}/{len(questions)} 题有匹配 | "
        f"{questions_with_analysis} 题有解析 | "
        f"新增 {total_card_links} 条卡链接 | 覆盖 {overwritten} 条旧映射 | "
        f"耗时 {total_elapsed:.0f}s"
    )
    print(f"[batch_runner] 合并后 ID 前缀统计：{id_prefix_stats}")
    return report


def run_refine(
    sections: list[str] | None = None,
    max_workers: int = 4,
    max_candidates: int = 60,
    dry_run: bool = False,
) -> dict[str, Any]:
    """LLM 二次筛选降噪：从现有 question_card_map.json 的候选池中，用 LLM 挑出真正相关的 5-15 张。

    不重新检索，只调 LLM 筛选。每题 1 次 LLM 调用（ds pro 关思考）。
    原候选保留到 raw_matched_card_ids，精简版写回 matched_card_ids，便于回滚。

    Parameters
    ----------
    sections : list[str] | None
        指定小节；None 表示全部。
    max_workers : int
        并发线程数。
    max_candidates : int
        候选超过此数时只取前 N 张（检索排序靠前的优先），控制 prompt 长度。
    dry_run : bool
        True=只跑不写回。
    """
    print(f"[refine] 加载习题 md | sections={sections or '全部'} | md_dirs={_MD_DIRS}")
    questions = load_questions(_MD_DIRS, sections=sections)
    if not questions:
        print("[refine] 未加载到题目")
        return {"status": "no_questions"}

    existing = _load_existing_mappings()
    if not existing:
        print("[refine] question_card_map.json 不存在或为空，无候选可降噪")
        return {"status": "no_mappings"}

    # 只处理既有题目又有现有候选的
    refine_tasks: list[tuple[Question, list[str]]] = []
    for q in questions:
        entry = existing.get(q.id)
        if not entry:
            continue
        cands = entry.get("matched_card_ids", [])
        if not cands:
            continue
        refine_tasks.append((q, cands))

    if not refine_tasks:
        print("[refine] 没有需要降噪的题目（题目与映射未对齐，或候选均为空）")
        return {"status": "no_tasks"}

    print(
        f"[refine] 待降噪 {len(refine_tasks)} 题 | workers={max_workers} | "
        f"max_candidates={max_candidates}"
    )
    print("[refine] 加载全书句卡 runtime（取句卡原文，不检索）...")
    rt = get_match_runtime()
    print(f"[refine] runtime 就绪：{len(rt.card_ids)} 张句卡")

    print_lock = threading.Lock()
    progress = {"done": 0}
    results: dict[str, dict[str, Any]] = {}

    def _refine_one(idx_q_cands: tuple[int, Question, list[str]]) -> tuple[str, dict[str, Any]]:
        i, q, cands = idx_q_cands
        res = refine_match_with_llm(q, cands, rt=rt, max_candidates=max_candidates)
        with print_lock:
            progress["done"] += 1
            done = progress["done"]
            print(
                f"  [{done}/{len(refine_tasks)}] {q.id} | {res['raw_candidate_count']}→{res['refined_count']} 张 | "
                f"{res['elapsed_ms']:.0f}ms | {res['status']}"
            )
        return q.id, res

    t0 = time.time()
    if max_workers > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_refine_one, (i, q, cands)): i
                for i, (q, cands) in enumerate(refine_tasks, 1)
            }
            for future in concurrent.futures.as_completed(futures):
                qid, res = future.result()
                results[qid] = res
    else:
        for i, (q, cands) in enumerate(refine_tasks, 1):
            qid, res = _refine_one((i, q, cands))
            results[qid] = res

    total_elapsed = time.time() - t0

    # 统计
    refined_counts = [r["refined_count"] for r in results.values()]
    raw_counts = [r["raw_candidate_count"] for r in results.values()]
    ok_count = sum(1 for r in results.values() if r["status"] == "ok")
    failed_count = sum(1 for r in results.values() if r["status"] == "failed")
    raw_total = sum(raw_counts)
    refined_total = sum(refined_counts)
    raw_avg = round(raw_total / max(len(raw_counts), 1), 1)
    refined_avg = round(refined_total / max(len(refined_counts), 1), 1)
    reduction_pct = round(100 * (1 - refined_total / max(raw_total, 1)), 1)

    report: dict[str, Any] = {
        "run_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": "refine",
        "sections": sections,
        "max_candidates": max_candidates,
        "questions_refined": len(refine_tasks),
        "ok_count": ok_count,
        "failed_count": failed_count,
        "raw_total": raw_total,
        "refined_total": refined_total,
        "raw_avg": raw_avg,
        "refined_avg": refined_avg,
        "reduction_pct": reduction_pct,
        "elapsed_s": round(total_elapsed, 1),
    }

    # 写回：matched_card_ids = refined，raw_matched_card_ids = 原候选
    if dry_run:
        print("[refine] dry_run=True，不写回 question_card_map.json")
    else:
        for qid, res in results.items():
            entry = existing.get(qid)
            if not entry:
                continue
            if res["status"] == "ok" and res["refined_card_ids"]:
                entry["raw_matched_card_ids"] = entry.get("matched_card_ids", [])
                entry["matched_card_ids"] = res["refined_card_ids"]
                entry["num_candidates"] = len(res["refined_card_ids"])
                entry["refine_reason"] = (res.get("reason", "") or "")[:500]
                entry["refined_at"] = report["run_at"]

        run_meta = {
            "name": "LLM二次筛选降噪",
            "generated_at": report["run_at"],
            "scope": f"sections={sections}",
            "max_candidates": max_candidates,
            "questions": len(refine_tasks),
            "raw_avg": raw_avg,
            "refined_avg": refined_avg,
            "reduction_pct": reduction_pct,
        }
        _save_question_card_map(existing, run_meta)
        print(f"[refine] 已写回 {_QUESTION_CARD_MAP.name} | 降噪 {len(refine_tasks)} 题")

    report_path = _save_report(report, sections or ["all"])
    print(f"[refine] 报告 → {report_path}")
    print(
        f"[refine] 完成：{ok_count} 成功 / {failed_count} 失败 | "
        f"平均 {raw_avg}→{refined_avg} 张/题 | 降噪率 {reduction_pct}% | 耗时 {total_elapsed:.0f}s"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="批量匹配题目与全书句卡，写回 question_card_map.json"
    )
    parser.add_argument(
        "--sections", nargs="*", default=None,
        help="指定小节，如 --sections 3.1 3.2。不传则跑全教材。",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="跑全教材（第 2/3/4/5/6 章）。",
    )
    parser.add_argument(
        "--no-planner", action="store_true",
        help="不调 LLM planner，用简单 plan（快、无 LLM、质量略低）。",
    )
    parser.add_argument(
        "--top-k", type=int, default=30,
        help="每选项最多召回候选数（默认 30）。",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="只检索不写回，输出报告供检查。",
    )
    parser.add_argument(
        "--generate-analysis", action="store_true",
        help="在检索后追加 LLM 调用，基于已知答案生成选项级解析"
        "（explanation/common_trap/evidence_cards），写回 option_evidence_map.json。",
    )
    parser.add_argument(
        "--match-only", action="store_true",
        help="三段式拼装模式：只跑 planner+检索（1次LLM/题），不调 adjudicator。"
        "explanation 用教研解析，evidence_cards 用检索候选，common_trap 留空待补。"
        "与 --generate-analysis 互斥。",
    )
    parser.add_argument(
        "--max-workers", type=int, default=4,
        help="并发线程数（默认 4）。每题主要是 LLM 调用（IO 密集），"
        "线程并发可大幅提速。建议 4-8，太高可能触发 API 限流。",
    )
    parser.add_argument(
        "--refine", action="store_true",
        help="LLM二次筛选降噪：从现有 question_card_map.json 的候选池中，"
        "用 LLM 挑出真正相关的 5-15 张。不重新检索，每题 1 次 LLM 调用。"
        "原候选保留到 raw_matched_card_ids，精简版写回 matched_card_ids，便于回滚。",
    )
    parser.add_argument(
        "--max-candidates", type=int, default=0,
        help="refine 模式下，候选超过此数时只取前 N 张。0=不截断，全部送进 prompt（默认）。"
        "之前截断会漏掉排序靠后的直接证据。",
    )
    args = parser.parse_args()

    if args.all:
        sections = None
    elif args.sections:
        sections = args.sections
    else:
        # 默认交互式提示
        print("未指定 --sections 或 --all。示例：")
        print("  python -m pipeline.batch_runner --sections 3.1")
        print("  python -m pipeline.batch_runner --all --match-only --max-workers 20")
        print("  python -m pipeline.batch_runner --refine --max-workers 20  # 降噪")
        return 1

    # refine 模式：不重新检索，只跑 LLM 二次筛选
    if args.refine:
        report = run_refine(
            sections=sections,
            max_workers=args.max_workers,
            max_candidates=args.max_candidates,
            dry_run=args.dry_run,
        )
        return 0 if report.get("status") not in ("no_questions", "no_mappings", "no_tasks") else 2

    report = run_batch(
        sections=sections,
        use_planner=not args.no_planner,
        top_k=args.top_k,
        dry_run=args.dry_run,
        generate_analysis=args.generate_analysis,
        max_workers=args.max_workers,
        match_only=args.match_only,
    )
    return 0 if report.get("status") != "no_questions" else 2


if __name__ == "__main__":
    raise SystemExit(main())
