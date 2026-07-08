"""对比新旧 prompt 的 refine 结果：抽 2 题展示 reason + 保留/剔除的句卡。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_MODULE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_MODULE_DIR))

from pipeline.evidence_pool import get_match_runtime
from pipeline.match_pipeline import refine_match_with_llm
from pipeline.question_loader import load_questions

_WORKBENCH = _MODULE_DIR.parent
_QUESTION_CARD_MAP = _WORKBENCH / "data" / "teaching_assets" / "question_card_map.json"

TARGET_QIDS = ["3.1_1", "3.1_11"]  # 验证折中口径：3.1_1的推理式排除依据能留，3.1_11的PEP定义能删


def main() -> int:
    print("[compare] 加载习题 md ...")
    questions = load_questions(
        _WORKBENCH.parent / "教材、答疑记录、习题与参考文献" / "习题" / "习题结构化",
        sections=["3.1"],
    )
    q_by_id = {q.id: q for q in questions}
    print(f"[compare] 共 {len(questions)} 题，目标: {TARGET_QIDS}")

    print("[compare] 加载 question_card_map.json ...")
    payload = json.loads(_QUESTION_CARD_MAP.read_text(encoding="utf-8"))
    mappings = payload.get("mappings", {})

    print("[compare] 加载 runtime（取句卡原文）...")
    rt = get_match_runtime()
    print(f"[compare] runtime 就绪：{len(rt.card_ids)} 张句卡")

    out_lines: list[str] = []
    for qid in TARGET_QIDS:
        q = q_by_id.get(qid)
        if not q:
            print(f"[compare] {qid} 题目未找到")
            continue
        entry = mappings.get(qid)
        if not entry:
            print(f"[compare] {qid} 映射未找到")
            continue
        raw_cids = entry.get("matched_card_ids", [])
        if not raw_cids:
            print(f"[compare] {qid} 无候选")
            continue

        print(f"\n[compare] ===== {qid} =====")
        print(f"  候选数: {len(raw_cids)}")
        res = refine_match_with_llm(q, raw_cids, rt=rt, max_candidates=0)
        refined = res["refined_card_ids"]
        dropped = [c for c in raw_cids if c not in set(refined)]
        print(f"  精简后: {len(refined)} | 剔除: {len(dropped)} | status: {res['status']}")
        print(f"  reason: {res['reason']}")

        # 取教研解析前200字
        explanation = (q.explanation or "")[:200]
        out_lines.append(f"\n{'='*70}")
        out_lines.append(f"题目 {qid}: {q.stem[:80]}")
        out_lines.append(f"标准答案: {q.answer}")
        out_lines.append(f"候选数: {len(raw_cids)} → 精简后: {len(refined)} | 剔除: {len(dropped)}")
        out_lines.append(f"教研解析: {explanation}")
        out_lines.append(f"\nLLM reason:")
        out_lines.append(res["reason"])
        out_lines.append(f"\n--- 保留的句卡 ({len(refined)}张) ---")
        for cid in refined:
            card = rt.card_by_id.get(cid, {})
            text = (card.get("text") or card.get("citation") or "")[:120]
            out_lines.append(f"  {cid}: {text}")
        out_lines.append(f"\n--- 剔除的句卡 ({len(dropped)}张，前20张采样) ---")
        for cid in dropped[:20]:
            card = rt.card_by_id.get(cid, {})
            text = (card.get("text") or card.get("citation") or "")[:120]
            out_lines.append(f"  {cid}: {text}")
        if len(dropped) > 20:
            out_lines.append(f"  ... 还有 {len(dropped)-20} 张未显示")

    out_path = _MODULE_DIR / "outputs" / "refine_compare_3.1_1_11_v4.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"\n[compare] 详情 → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
