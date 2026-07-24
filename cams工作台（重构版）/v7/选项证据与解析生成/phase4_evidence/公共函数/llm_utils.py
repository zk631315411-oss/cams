# -*- coding: utf-8 -*-
"""公共 LLM 工具 — call_llm、parse、strip_json_fence。"""

from __future__ import annotations

import json, re
from typing import Any

from 公共函数.index import get_llm_config


def call_llm(client: Any, prompt: str, model: str="deepseek-v4-pro",
             max_tokens: int=20000, timeout: float=120.0,
             reasoning_effort: str="high", enable_thinking: bool=True) -> str:
    kwargs: dict[str, Any] = {
        "model": model, "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens, "timeout": timeout,
    }
    if enable_thinking:
        kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
        kwargs["reasoning_effort"] = reasoning_effort
    else:
        kwargs["temperature"] = 0
    response = client.chat.completions.create(**kwargs)
    return (response.choices[0].message.content or "").strip()


def strip_json_fence(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def parse_llm_output(raw_text: str) -> dict[str, Any] | None:
    if not raw_text: return None
    cleaned = strip_json_fence(raw_text)
    try: return json.loads(cleaned)
    except json.JSONDecodeError: pass
    match = re.search(r"\{[\s\S]*\"option_analysis\"[\s\S]*\}", cleaned)
    if match:
        try: return json.loads(match.group(0))
        except json.JSONDecodeError: pass
    try:
        import json_repair
        return json.loads(json_repair.repair_json(cleaned))
    except Exception: pass
    return None
