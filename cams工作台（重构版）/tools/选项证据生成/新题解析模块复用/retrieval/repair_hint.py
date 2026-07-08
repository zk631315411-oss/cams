"""盲判修复提示：为盲判修复重跑生成扩展检索引导信息。

旧管线中，LLM 二审发现答案分歧后可触发盲判修复重跑（broaden_recall）。
重新跑之前，此函数为裁判生成提示词——指示需要扩大召回的证据类型，
同时确保不准参考题库答案。

当前管线已砍掉 LLM 二审和盲判修复。保留此模块作为未来需要
"分歧驱动的盲判修复"场景的备用。
"""
from __future__ import annotations

from typing import Any


def blind_repair_hint(repair_reason: str) -> dict[str, Any]:
    """Build a hint dict for blind repair rerun.

    The hint tells the re-run adjudicator which evidence types to broaden
    recall for, without revealing which option is the correct answer.
    """
    reason = str(repair_reason or "retrieval_gap").strip()
    hint: dict[str, Any] = {
        "repair_reason": reason,
        "standard_answer_visible": False,
        "recommended_answer_visible": False,
        "instructions": [
            "do_not_guess_answer",
            "do_not_use_standard_answer",
            "broaden_recall_without_answer_leakage",
        ],
    }
    if reason in {"retrieval_gap", "focus_misdirected", "weak_convergence"}:
        hint["needed_evidence_types"] = [
            "bridge_queries",
            "negative_queries",
            "sufficiency_queries",
        ]
        hint["focus"] = (
            "补充上位原则、流程桥接、反证/限制条件、单一因素是否足够的检索；"
            "不要透露或暗示哪个选项是题库答案。"
        )
    return hint
