"""Optional DeepSeek second opinion; it never advances the formal workflow."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from storage import WorkspaceError, WorkspaceStore


SYSTEM_PROMPT = """你是独立的考试题研判助手。只根据提供的题面和证据判断，不推测题源答案。
返回 JSON 对象，字段为 suggested_answer、option_analysis、evidence_gaps、conflicts、confidence。
证据不足时必须明确说明，不得编造教材原文或页码。"""


def _parse_content(content: str) -> dict[str, Any]:
    text = content.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise WorkspaceError("DeepSeek 未返回可解析的 JSON 结果") from exc
    if not isinstance(value, dict):
        raise WorkspaceError("DeepSeek 结果必须是 JSON 对象")
    return value


def request_opinion(store: WorkspaceStore, question_id: str, actor: str, reason: str,
                    expected_question_version: int, expected_archive_revision: int) -> dict[str, Any]:
    settings = store.read_deepseek_settings(masked=False)
    if not settings.get("enabled") or not settings.get("api_key"):
        raise WorkspaceError("DS 辅助研判尚未启用，请先在网页设置中配置")
    packet = store.prepare_ds_opinion_input(question_id)
    body = {"model": settings["model"], "temperature": 0.1, "stream": False,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": json.dumps(packet, ensure_ascii=False)}],
            "response_format": {"type": "json_object"}}
    request = urllib.request.Request(
        f"{str(settings['base_url']).rstrip('/')}/chat/completions",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {settings['api_key']}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        result = _parse_content(content)
        return store.save_ds_opinion(question_id, packet, result, settings["model"], "completed",
                                     actor, reason, expected_question_version=expected_question_version,
                                     expected_archive_revision=expected_archive_revision)
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, WorkspaceError) as exc:
        return store.save_ds_opinion(question_id, packet, None, settings["model"], "failed",
                                     actor, reason, error=str(exc),
                                     expected_question_version=expected_question_version,
                                     expected_archive_revision=expected_archive_revision)
