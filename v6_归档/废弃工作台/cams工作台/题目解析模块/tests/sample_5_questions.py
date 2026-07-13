"""抽 5 题跑匹配 + 解析，人工评估质量。

从 3.1 章抽 5 题，跑完整匹配+选项级解析，打印：
- 题干 + 选项 + 答案
- 匹配到的句卡（card_id / knowledge / citation / chapter_path）
- 每个选项的 AI 解析（explanation / common_trap / evidence_cards）

用法::

    cd 题目解析模块
    python -m tests.sample_5_questions
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parents[1]
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from env_setup import _load_env
_load_env()

from pipeline.evidence_pool import get_match_runtime
from pipeline.match_pipeline import match_one_question
from pipeline.question_loader import load_questions

_MD_DIR = (
    _MODULE_DIR.parent.parent
    / "教材、答疑记录、习题与参考文献"
    / "习题"
    / "习题结构化提取"
)

# 固定抽 5 题
SAMPLE_INDICES = [0, 5, 12, 25, 40]


def main() -> int:
    print("=" * 70)
    print("抽 5 题质量检查（3.1 章）— 匹配 + 选项级解析")
    print("=" * 70)

    print("\n[1] 解析 3.1_习题集.md ...")
    questions = load_questions(_MD_DIR, sections=["3.1"])
    print(f"    共 {len(questions)} 题，抽样索引：{SAMPLE_INDICES}")

    print("\n[2] 加载全书句卡 runtime（首次约 30-60 秒）...")
    rt = get_match_runtime()
    print(f"    {len(rt.card_ids)} 张句卡就绪")

    results = []
    for idx in SAMPLE_INDICES:
        if idx >= len(questions):
            continue
        q = questions[idx]
        print("\n" + "=" * 70)
        print(f"[题 {idx+1}] {q.id} | 知识点: {q.knowledge_point}")
        print(f"  题干: {q.stem}")
        print(f"  选项:")
        for label, text in q.options.items():
            mark = " <-答案" if label in q.answer.split(",") else ""
            print(f"    {label}. {text}{mark}")
        print(f"  答案: {q.answer}")

        print(f"\n[匹配+解析中] planner 检索 + adjudicator 解析 ...")
        result = match_one_question(q, rt=rt, use_planner=True, top_k=20, generate_analysis=True)
        print(f"  status: {result['status']} | 解析: {'生成' if result.get('analysis_generated') else '未生成'} | 耗时: {result['elapsed_ms']:.0f}ms")
        print(f"  matched_card_ids: {result['evidence_count']} 张")

        # 选项级解析
        if result.get("option_analysis"):
            print(f"\n  --- 选项级解析 ---")
            for row in result["option_analysis"]:
                label = row.get("option", "")
                judge = row.get("judgement", "")
                ev_status = row.get("evidence_status", "")
                explanation = (row.get("explanation") or "")[:150]
                common_trap = (row.get("common_trap") or "")[:100]
                ev_cards = row.get("evidence_cards", []) or []
                print(f"  选项{label} [{judge}] [证据:{ev_status}]")
                print(f"    解析: {explanation}")
                if common_trap:
                    print(f"    易错点: {common_trap}")
                if ev_cards:
                    print(f"    证据句卡:")
                    for c in ev_cards[:3]:
                        cid = c.get("card_id", "")
                        quote = (c.get("quote") or "")[:80]
                        reason = (c.get("reason") or "")[:60]
                        print(f"      - {cid}: {quote}")
                        print(f"        理由: {reason}")
        else:
            print(f"\n  [未生成选项级解析]")

        # 题目级证据前 5 张
        if result["matched_card_ids"]:
            print(f"\n  --- 题目级证据（前5张）---")
            for i, cid in enumerate(result["matched_card_ids"][:5], 1):
                card = rt.card_by_id.get(cid, {})
                knowledge = (card.get("knowledge") or "")[:60]
                chapter = card.get("chapter_path") or ""
                print(f"    [{i}] {cid} | {chapter}")
                print(f"        knowledge: {knowledge}")

        results.append({
            "question": q.to_dict(),
            "match": {k: v for k, v in result.items() if k != "option_evidence"},
        })

    # 保存完整结果
    out = _MODULE_DIR / "outputs" / "reports" / "sample_5_questions.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{'=' * 70}")
    print(f"完整结果已保存: {out}")
    print(f"\n请人工检查：1) 句卡相关性 2) 解析是否正确说明对错 3) 易错点是否合理")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
