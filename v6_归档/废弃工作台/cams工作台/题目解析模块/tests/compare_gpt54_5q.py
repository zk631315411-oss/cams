"""跑 gpt5.4 5题（与flash同题），产物分开。

gpt5.4 走单独的 API endpoint，非 deepseek。
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import time
from pathlib import Path

# ==== 1. 加载工作区 .env（DEEPSEEK_API_KEY，虽然gpt5.4不用，但pipeline导入需要） ====
_MODULE_DIR = Path(__file__).resolve().parents[1]
_ENV_SETUP = _MODULE_DIR / "env_setup.py"
if _ENV_SETUP.exists():
    import importlib.util as _ilu
    _spec_env = _ilu.spec_from_file_location("_env_setup", _ENV_SETUP)
    _mod_env = _ilu.module_from_spec(_spec_env)
    _spec_env.loader.exec_module(_mod_env)
    _mod_env._load_env()

# ==== 2. 把四角色法目录加入 sys.path，monkey-patch gpt5.4 配置 ====
_FOUR_ROLE_DIR = _MODULE_DIR.parent.parent / "题目与kg关系建立流水线（四角色法）"
# _MODULE_DIR = 题目解析模块, parent = cams工作台, parent.parent = cams考试
if str(_FOUR_ROLE_DIR) not in sys.path:
    sys.path.insert(0, str(_FOUR_ROLE_DIR))

import run_step1  # noqa: E402

# gpt5.4 配置（用户提供的独立 endpoint）
_GPT_MODEL = "gpt5.4"
_GPT_KEY = os.environ.get("GPT54_API_KEY", "")
_GPT_BASE_URL = "http://120.224.38.132:7361/v1"

# monkey-patch run_step1：模型名 + 关闭思考（gpt5.4 走 empty dict）
run_step1.MODEL = _GPT_MODEL
run_step1.V4_NO_THINK = {}  # 非 deepseek 模型传空 dict

# 同时 patch get_deepseek_config，让 evidence_pool 用的 client 指向 gpt5.4 endpoint
_original_get_deepseek_config = run_step1.get_deepseek_config


def _patched_get_deepseek_config():
    return _GPT_KEY, _GPT_BASE_URL, "GPT54_KEY"


run_step1.get_deepseek_config = _patched_get_deepseek_config

print(f"[gpt54_compare] 模型={run_step1.MODEL} | V4_NO_THINK={run_step1.V4_NO_THINK} | base_url={_GPT_BASE_URL}")

# ==== 3. 导入 pipeline ====
from pipeline.evidence_pool import get_match_runtime  # noqa: E402
from pipeline.match_pipeline import match_one_question, to_question_card_map_entry  # noqa: E402
from pipeline.question_loader import load_questions  # noqa: E402

# ==== 4. 路径 ====
_EXERCISE_ROOT = _MODULE_DIR.parent.parent / "教材、答疑记录、习题与参考文献" / "习题"
_MD_DIRS = [
    _EXERCISE_ROOT / "习题结构化",
    _EXERCISE_ROOT / "习题结构化提取",
]
_OUT_DIR = _MODULE_DIR / "outputs" / "gpt54_5q_comparison"
_OUT_DIR.mkdir(parents=True, exist_ok=True)

# 与 flash 同样的5题（random.seed(42)）
_TARGET_IDS = {"2.8_2", "2.1_29", "2.1_7", "2.3_1", "2.2_13"}


def run_5q() -> int:
    print("[gpt54_compare] 加载第二章题目...")
    all_qs = load_questions(_MD_DIRS, sections=["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8"])
    sample = [q for q in all_qs if q.id in _TARGET_IDS]
    print(f"[gpt54_compare] 目标5题: {[q.id for q in sample]}")

    print("[gpt54_compare] 加载 runtime...")
    rt = get_match_runtime()
    print(f"[gpt54_compare] runtime 就绪：{len(rt.card_ids)} 张句卡")

    results: list[dict] = []
    t0 = time.time()
    for i, q in enumerate(sample, 1):
        print(f"\n[gpt54_compare] [{i}/5] {q.id}: {q.stem[:40]} | ans={q.answer}")
        qt0 = time.perf_counter()
        mr = match_one_question(q, rt=rt, top_k=30, use_planner=True, generate_analysis=True)
        elapsed_ms = round((time.perf_counter() - qt0) * 1000, 1)

        entry = to_question_card_map_entry(mr, q)
        status = mr.get("status", "ok")
        analysis_flag = "解析✓" if mr.get("analysis_generated") else "解析✗"
        print(f"  -> {status} | {len(entry['matched_card_ids'])} 张 | {elapsed_ms:.0f}ms | {analysis_flag}")
        if mr.get("analysis_error"):
            print(f"  -> 错误: {mr['analysis_error'][:150]}")

        oa = mr.get("option_analysis", [])
        for row in oa:
            label = row.get("option", "?")
            j = row.get("judgement", "?")
            ev_cards = row.get("evidence_cards", []) or []
            expl = (row.get("explanation", "") or "")[:70]
            print(f"     {label}({j}) cards={len(ev_cards)} | {expl}")

        results.append({
            "question_id": q.id,
            "section": q.section,
            "stem": q.stem,
            "answer": q.answer,
            "options": q.options,
            "elapsed_ms": elapsed_ms,
            "status": status,
            "analysis_generated": mr.get("analysis_generated", False),
            "analysis_error": mr.get("analysis_error", ""),
            "matched_card_ids": entry["matched_card_ids"],
            "option_analysis": oa,
            "overall_notes": mr.get("overall_notes", ""),
        })

    total_elapsed = time.time() - t0
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    payload = {
        "experiment": "gpt5.4 + thinking=disabled vs deepseek variants",
        "model": _GPT_MODEL,
        "thinking_mode": "disabled",
        "run_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "questions_count": 5,
        "total_elapsed_s": round(total_elapsed, 1),
        "avg_per_question_ms": round(total_elapsed * 1000 / 5, 1),
        "results": results,
    }
    out_path = _OUT_DIR / f"gpt54_5q_{stamp}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[gpt54_compare] 产物已写入: {out_path}")
    print(f"[gpt54_compare] 总耗时 {total_elapsed:.0f}s | 平均 {total_elapsed/5:.0f}s/题")
    ok = sum(1 for r in results if r["status"] == "ok")
    has_analysis = sum(1 for r in results if r["analysis_generated"])
    print(f"[gpt54_compare] 成功 {ok}/5 | 有解析 {has_analysis}/5")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_5q())
