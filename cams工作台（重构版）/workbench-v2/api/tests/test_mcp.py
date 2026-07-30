from __future__ import annotations

import json

from fastapi.testclient import TestClient

from api.app import app


def _streamable_json(response):
    payload = response.text
    if payload.startswith("event:"):
        payload = next(line[6:].strip() for line in payload.splitlines() if line.startswith("data:"))
    return json.loads(payload)


def test_mcp_exposes_all_nine_tools():
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    initialize = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "1"},
        },
    }
    with TestClient(app, base_url="http://127.0.0.1:8013") as client:
        response = client.post("/mcp", headers=headers, json=initialize)
        assert response.status_code == 200
        headers["mcp-session-id"] = response.headers["mcp-session-id"]
        response = client.post(
            "/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        )
    names = {item["name"] for item in _streamable_json(response)["result"]["tools"]}
    assert names == {
        "find_question",
        "get_question",
        "begin_edit_task",
        "search_kg",
        "get_unit",
        "open_source_page",
        "save_question",
        "get_task_diff",
        "finish_edit_task",
    }
