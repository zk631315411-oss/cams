"""单章节端到端验证：解析 3.1 md → 跑前 2 题匹配 → 打印结果。

用法::

    cd 题目解析模块
    python -m tests.test_one_chapter
"""
from __future__ import annotations

import sys
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parents[1]
if str(_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULE_DIR))

from pipeline.evidence_pool import get_match_runtime
from pipeline.match_pipeline import match_one_question
from pipeline.question_loader import load_questions

_MD_DIR = (
    _MODULE_DIR.parent.parent
    / "教材、答疑记录、习题与参考文献"
    / "习题"
    / "习题结构化提取"
)


def main() -> int:
    print("=" * 60)
    print("单章节验证：3.1 前 2 题")
    print("=" * 60)

    print("\n[1] 解析 3.1_习题集.md ...")
    questions = load_questions(_MD_DIR, sections=["3.1"])
    print(f"    共 {len(questions)} 题")
    if not questions:
        print("    未加载到题目，检查 md 路径。")
        return 1

    print("\n[2] 加载全书句卡 runtime ...")
    rt = get_match_runtime()
    print(f"    {len(rt.card_ids)} 张句卡")

    sample = questions[:2]
    for q in sample:
        print(f"\n[3] 匹配 {q.id} | {q.knowledge_point[:30]}")
        print(f"    题干: {q.stem[:80]}")
        print(f"    选项: {list(q.options.keys())} | 答案: {q.answer}")

        result = match_one_question(q, rt=rt, use_planner=True, top_k=20)
        print(f"    status: {result['status']}")
        print(f"    matched_card_ids: {result['matched_card_ids'][:5]}")
        print(f"    evidence_count: {result['evidence_count']}")
        print(f"    elapsed_ms: {result['elapsed_ms']:.0f}")

        # 抽样打印一张证据
        if result["matched_card_ids"]:
            first_cid = result["matched_card_ids"][0]
            card = rt.card_by_id.get(first_cid, {})
            print(f"    样本证据 {first_cid}:")
            print(f"      knowledge: {card.get('knowledge', '')[:80]}")
            print(f"      citation:  {card.get('citation', '')[:80]}")
            print(f"      chapter_path: {card.get('chapter_path', '')}")

    print("\n验证完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
