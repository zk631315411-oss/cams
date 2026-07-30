"""Dependency-free stdio MCP server for the CAMS formal workbench."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from drafting.deepseek import request_opinion
from retrieval.assets import AssetError
from retrieval.service import retrieve_question_evidence, search_evidence
from storage import LockError, STORE, WorkspaceError, WorkspaceStore


READ_ONLY_TOOLS = {
    "list_questions", "search_evidence", "retrieve_question_evidence",
    "read_active_context", "read_question", "read_evidence_catalog", "read_audit",
}
CRITICAL_TOOLS = {"update_question", "request_ds_opinion", "build_release"}

TOOLS: list[dict[str, Any]] = [
    {"name": "create_question_intake", "description": "从 Codex 建立新题档案：自动编号、复制 PNG/JPG/PDF 原件、记录哈希并生成重复候选。无法归档原件时只建立待补原件记录。",
     "properties": {"content": "object", "intake": "object", "source_paths": "array", "actor": "string", "reason": "string"},
     "required": ["content", "intake", "source_paths", "reason"]},
    {"name": "resolve_duplicate_check", "description": "记录 Codex 的重复题判断。只有 new 可进入证据研究。",
     "properties": {"question_id": "string", "decision": "string", "rationale": "string", "actor": "string", "reason": "string", "expected_archive_revision": "integer"},
     "required": ["question_id", "decision", "rationale", "reason", "expected_archive_revision"]},
    {"name": "list_questions", "description": "列出题目，可按状态或关键词筛选，用于确定下一道待处理题。",
     "properties": {"status": "string", "query": "string", "offset": "integer", "limit": "integer"}, "required": []},
    {"name": "read_active_context", "description": "读取网页当前选中的题目、正式阶段和建议下一步。收到‘整理证据’、‘处理当前题’或‘继续’时先调用此工具。",
     "properties": {}, "required": []},
    {"name": "search_evidence", "description": "一般检索：RAG 与 KG 图谱扩展，只读。",
     "properties": {"query": "string", "top_k": "integer", "language": "string", "config": "object"}, "required": ["query"]},
    {"name": "retrieve_question_evidence", "description": "题目检索：检索头、P5、RAG、选项补充池与 KG 图谱扩展，只读。",
     "properties": {"question_id": "string", "config": "object"}, "required": ["question_id"]},
    {"name": "register_evidence", "description": "将 RAG、KG、grep、直接翻页或外部搜索发现统一登记到去重证据目录。自由检索结果只有登记后才能成为正式候选。",
     "properties": {"question_id": "string", "payload": "object", "discovery_method": "string", "actor": "string", "reason": "string", "expected_question_version": "integer", "expected_archive_revision": "integer"},
     "required": ["question_id", "payload", "discovery_method", "reason", "expected_question_version", "expected_archive_revision"]},
    {"name": "read_question", "description": "读取题目、正式流程、当前任务、精选证据、解析和审核记录。",
     "properties": {"question_id": "string"}, "required": ["question_id"]},
    {"name": "read_evidence_catalog", "description": "分页读取证据目录，可查看 all、curated 或 suggested。",
     "properties": {"question_id": "string", "scope": "string", "source_kind": "string", "method": "string", "option": "string", "run_id": "string", "offset": "integer", "limit": "integer"}, "required": ["question_id"]},
    {"name": "read_audit", "description": "读取题目的追加式审计记录。",
     "properties": {"question_id": "string"}, "required": ["question_id"]},
    {"name": "curate_evidence", "description": "维护 Codex 精选池。每条采用证据必须标明 support_answer、exclude_option 或 background。",
     "properties": {"question_id": "string", "updates": "object_array", "actor": "string", "reason": "string", "expected_question_version": "integer", "expected_archive_revision": "integer"},
     "required": ["question_id", "updates", "reason", "expected_question_version", "expected_archive_revision"]},
    {"name": "submit_evidence_candidate", "description": "将当前 Codex 精选池提交给教研确认。提交后只能等待网页确认或退回。",
     "properties": {"question_id": "string", "actor": "string", "reason": "string", "expected_question_version": "integer", "expected_archive_revision": "integer"},
     "required": ["question_id", "reason", "expected_question_version", "expected_archive_revision"]},
    {"name": "write_analysis_version", "description": "基于已确认依据生成或修改固定模板正式解析，并逐条回应教研批注。",
     "properties": {"question_id": "string", "analysis": "object", "feedback_responses": "object_array", "actor": "string", "reason": "string", "expected_question_version": "integer", "expected_archive_revision": "integer"},
     "required": ["question_id", "analysis", "reason", "expected_question_version", "expected_archive_revision"]},
    {"name": "write_final_check", "description": "在教研标记润色完成后，对固定题面、证据和解析版本写入最终核验。",
     "properties": {"question_id": "string", "check": "object", "actor": "string", "reason": "string", "expected_question_version": "integer", "expected_archive_revision": "integer"},
     "required": ["question_id", "check", "reason", "expected_question_version", "expected_archive_revision"]},
    {"name": "reopen_evidence", "description": "发现证据不足时正式重开证据阶段，使后续解析、核验和批准版本失效但保留历史。",
     "properties": {"question_id": "string", "actor": "string", "reason": "string", "expected_question_version": "integer", "expected_archive_revision": "integer"},
     "required": ["question_id", "reason", "expected_question_version", "expected_archive_revision"]},
    {"name": "set_task_state", "description": "记录 Codex 当前任务、运行状态、等待对象和下一步；不推进正式里程碑。",
     "properties": {"question_id": "string", "task_type": "string", "status": "string", "waiting_for": "string", "next_step": "string", "error": "string", "summary": "string", "actor": "string", "reason": "string", "expected_question_version": "integer", "expected_archive_revision": "integer"},
     "required": ["question_id", "task_type", "status", "reason", "expected_question_version", "expected_archive_revision"]},
    {"name": "request_ds_opinion", "description": "可选的 DeepSeek 独立第二意见。只有教研明确确认后调用；成功或失败都不推进正式流程。",
     "properties": {"question_id": "string", "actor": "string", "reason": "string", "expected_question_version": "integer", "expected_archive_revision": "integer", "confirmed": "boolean"},
     "required": ["question_id", "reason", "expected_question_version", "expected_archive_revision", "confirmed"]},
    {"name": "update_question", "description": "修改正式题目。仅在用户明确确认后调用，且必须提供当前版本、档案修订号和 confirmed=true。",
     "properties": {"question_id": "string", "content": "object", "actor": "string", "reason": "string", "expected_question_version": "integer", "expected_archive_revision": "integer", "confirmed": "boolean"},
     "required": ["question_id", "content", "reason", "expected_question_version", "expected_archive_revision", "confirmed"]},
    {"name": "build_release", "description": "构建不可变发布包。仅在用户明确确认后调用。",
     "properties": {"release_id": "string", "actor": "string", "reason": "string", "confirmed": "boolean"},
     "required": ["release_id", "reason", "confirmed"]},
]


def schema(tool: dict[str, Any]) -> dict[str, Any]:
    types = {"string": {"type": "string"}, "integer": {"type": "integer"}, "object": {"type": "object"}, "array": {"type": "array", "items": {"type": "string"}}, "object_array": {"type": "array", "items": {"type": "object"}}, "boolean": {"type": "boolean"}}
    return {"type": "object", "properties": {key: types[value] for key, value in tool["properties"].items()}, "required": tool["required"]}


def tool_payload(tool: dict[str, Any]) -> dict[str, Any]:
    name = tool["name"]
    return {
        "name": name,
        "description": tool["description"],
        "inputSchema": schema(tool),
        "annotations": {
            "readOnlyHint": name in READ_ONLY_TOOLS,
            "destructiveHint": name in CRITICAL_TOOLS,
            "idempotentHint": name in READ_ONLY_TOOLS,
        },
    }


def _required_revision(args: dict[str, Any]) -> tuple[int, int]:
    version, revision = args.get("expected_question_version"), args.get("expected_archive_revision")
    if not isinstance(version, int) or not isinstance(revision, int):
        raise WorkspaceError("写入前必须先 read_question，并提供当前 expected_question_version 和 expected_archive_revision")
    return version, revision


def _critical_confirmation(name: str, args: dict[str, Any]) -> None:
    if args.get("confirmed") is not True:
        raise WorkspaceError(f"{name} 需要用户明确确认后，传入 confirmed=true")
    if not str(args.get("reason") or "").strip():
        raise WorkspaceError(f"{name} 必须记录确认原因")


def invoke(name: str, args: dict[str, Any]) -> Any:
    actor, reason = str(args.get("actor") or "codex"), str(args.get("reason") or "").strip()
    qid = str(args.get("question_id") or "")
    if name == "create_question_intake":
        if not reason:
            raise WorkspaceError("建档必须记录原因")
        return STORE.create_question_intake(args.get("content") or {}, args.get("intake") or {},
                                            args.get("source_paths") or [], actor, "codex", reason)
    if name == "resolve_duplicate_check":
        revision = args.get("expected_archive_revision")
        if not isinstance(revision, int):
            raise WorkspaceError("重复判断前必须 read_question 并提供当前 expected_archive_revision")
        if not reason or not str(args.get("rationale") or "").strip():
            raise WorkspaceError("重复判断必须记录理由")
        return STORE.resolve_duplicate_check(qid, str(args.get("decision") or ""),
                                             str(args.get("rationale") or ""), actor, "codex", reason, revision)
    if name == "list_questions":
        status, query = str(args.get("status") or ""), str(args.get("query") or "")
        offset, limit = max(0, int(args.get("offset") or 0)), min(200, max(1, int(args.get("limit") or 50)))
        all_rows = STORE.list_questions(status=status, query=query)
        return {"items": all_rows[offset:offset + limit], "total": len(all_rows), "offset": offset, "limit": limit}
    if name == "read_active_context":
        return STORE.read_active_context()
    if name == "search_evidence":
        return search_evidence(STORE.root, str(args.get("query") or ""), int(args.get("top_k") or 20), language=str(args.get("language") or "auto"), config=args.get("config") or {})
    if name == "retrieve_question_evidence":
        return retrieve_question_evidence(STORE.root, STORE.assert_ds_ready(qid)["content"], config=args.get("config") or {})
    if name == "read_question":
        return STORE.workflow_detail(qid)
    if name == "read_evidence_catalog":
        return STORE.read_evidence_catalog(qid, scope=str(args.get("scope") or "all"),
                                           source_kind=str(args.get("source_kind") or ""),
                                           method=str(args.get("method") or ""), option=str(args.get("option") or ""),
                                           run_id=str(args.get("run_id") or ""),
                                           offset=max(0, int(args.get("offset") or 0)),
                                           limit=min(100, max(1, int(args.get("limit") or 20))))
    if name == "read_audit":
        return STORE.read_audit(qid)
    if name == "register_evidence":
        version, revision = _required_revision(args)
        if not reason: raise WorkspaceError("登记证据必须记录原因")
        return STORE.register_evidence_run(qid, args.get("payload") or {}, str(args.get("discovery_method") or ""),
                                           actor, "codex", reason, version, revision)

    version, revision = _required_revision(args) if name != "build_release" else (None, None)
    if name in CRITICAL_TOOLS:
        _critical_confirmation(name, args)
    if not reason and name != "build_release": raise WorkspaceError("写入操作必须记录原因")
    if name == "curate_evidence":
        return STORE.curate_evidence(qid, args.get("updates") or [], actor, "codex", reason,
                                     expected_question_version=version, expected_archive_revision=revision)
    if name == "submit_evidence_candidate":
        return STORE.submit_evidence_candidate(qid, actor, "codex", reason, version, revision)
    if name == "write_analysis_version":
        return STORE.write_analysis_version(qid, args.get("analysis") or {}, actor, "codex", reason,
                                            args.get("feedback_responses") or [], version, revision)
    if name == "write_final_check":
        return STORE.write_final_check(qid, args.get("check") or {}, actor, "codex", reason, version, revision)
    if name == "reopen_evidence":
        return STORE.reopen_evidence(qid, actor, "codex", reason, version, revision)
    if name == "set_task_state":
        return STORE.set_task_state(qid, str(args.get("task_type") or ""), str(args.get("status") or ""), actor,
                                    reason, waiting_for=str(args.get("waiting_for") or "") or None,
                                    next_step=str(args.get("next_step") or ""), error=str(args.get("error") or ""),
                                    summary=str(args.get("summary") or ""), expected_question_version=version,
                                    expected_archive_revision=revision)
    if name == "request_ds_opinion":
        return request_opinion(STORE, qid, actor, reason, version, revision)
    if name == "update_question":
        return STORE.write_question(qid, args.get("content") or {}, actor, "codex", reason, version, revision)
    if name == "build_release":
        return STORE.build_release(str(args.get("release_id") or ""), actor)
    raise WorkspaceError("未知工具")


def respond(message_id: Any, result: Any = None, error: str | None = None) -> None:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": message_id}
    payload["error" if error else "result"] = {"code": -32000, "message": error} if error else result
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def main() -> None:
    global STORE
    parser = argparse.ArgumentParser(description="CAMS 正式版 MCP")
    parser.add_argument("--workspace-root", type=Path, default=None)
    args = parser.parse_args()
    root = args.workspace_root or (Path(os.environ["CAMS_WORKSPACE_ROOT"]) if os.environ.get("CAMS_WORKSPACE_ROOT") else None)
    if root:
        STORE = WorkspaceStore(root.resolve())
    for line in sys.stdin:
        message_id: Any = None
        try:
            request = json.loads(line)
            method, message_id = request.get("method"), request.get("id")
            if method == "initialize":
                respond(message_id, {"protocolVersion": request.get("params", {}).get("protocolVersion", "2024-11-05"), "capabilities": {"tools": {}}, "serverInfo": {"name": "cams-formal-workbench", "version": "2.1.0"}})
            elif method == "tools/list":
                respond(message_id, {"tools": [tool_payload(tool) for tool in TOOLS]})
            elif method == "tools/call":
                params = request.get("params", {})
                result = invoke(params.get("name", ""), params.get("arguments") or {})
                respond(message_id, {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}], "structuredContent": result})
            elif message_id is not None:
                respond(message_id, error="不支持的方法")
        except (WorkspaceError, AssetError, LockError, ValueError, KeyError) as exc:
            if message_id is not None:
                respond(message_id, error=str(exc))


if __name__ == "__main__":
    main()
