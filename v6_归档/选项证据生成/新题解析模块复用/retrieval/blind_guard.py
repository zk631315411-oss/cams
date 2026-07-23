"""盲判辅助工具：为盲判 LLM 阶段准备不含答案的题目副本。

旧管线中，搜索规划器（planner）需要读取题目文本生成检索策略，
但规划器不能看到题库答案——需要先过一遍此函数删掉所有答案相关字段。

当前管线已砍掉规划器，裁判直接收 prompt（stem + options + candidates），
题目字典本身不传入裁判。保留此模块作为未来需要"脱敏题目"场景的备用。
"""
from __future__ import annotations

from typing import Any


def answerless_question_for_blind(question: dict[str, Any]) -> dict[str, Any]:
    """Return a copy suitable for blind parsing/planning, with answer fields removed."""
    clean = dict(question)
    clean.pop("answer", None)
    clean.pop("detected_answer", None)
    clean.pop("standard_answer", None)
    clean.pop("key_answer", None)
    clean.pop("analysis", None)
    clean.pop("explanation", None)
    clean.pop("题库答案", None)
    clean.pop("标准答案", None)
    clean.pop("解析", None)
    return clean
