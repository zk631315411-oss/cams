"""唯一文件存储层：原子写入、题目锁、审计和发布构建。"""
from __future__ import annotations

import contextlib
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time
import unicodedata
from difflib import SequenceMatcher
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

QUESTION_ID_RE = re.compile(r"^v7_q_\d{6}$")
RELEASE_ID_RE = re.compile(r"^v7-[A-Za-z0-9._-]+$")
WORKFLOW_STAGES = {
    "intake", "duplicate_check", "evidence_research", "evidence_confirmation",
    "analysis_drafting", "analysis_revision", "final_verification",
    "human_approval", "release_ready", "released",
}
DISPOSITIONS = {"active", "needs_source_clarification", "merged", "held", "rejected"}
EVIDENCE_ROLES = {"support_answer", "exclude_option", "background"}
DISCOVERY_METHODS = {
    "question_rag", "general_rag", "kg_expand", "grep_keyword",
    "direct_page_review", "external_search", "legacy_import",
}
_BGE_MODEL: Any = None
_BGE_MODEL_PATH: str | None = None


class WorkspaceError(RuntimeError):
    pass


class LockError(WorkspaceError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class WorkspaceStore:
    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()
        self.data = self.root / "data"
        self.questions = self.data / "questions"
        self.control = self.data / "control"
        self.locks = self.control / "locks"
        self.releases = self.root / "releases"
        self.ensure_layout()

    def ensure_layout(self) -> None:
        for path in (
            self.data / "infrastructure" / "textbook",
            self.data / "infrastructure" / "kg",
            self.data / "infrastructure" / "index",
            self.questions,
            self.locks,
            self.releases,
        ):
            path.mkdir(parents=True, exist_ok=True)

    @contextlib.contextmanager
    def question_id_lock(self, actor: str) -> Iterator[None]:
        """Serialize automatic question-number allocation across MCP/API processes."""
        path = self.control / "question-id-lock.json"
        deadline = time.monotonic() + 5
        while True:
            try:
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                break
            except FileExistsError as exc:
                if time.monotonic() >= deadline:
                    raise LockError("题号分配锁等待超时，请稍后重试") from exc
                time.sleep(0.02)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump({"actor": actor, "started_at": now()}, stream, ensure_ascii=False)
            yield
        finally:
            path.unlink(missing_ok=True)

    def _next_question_id_unlocked(self) -> str:
        maximum = 0
        for directory in self.questions.glob("v7_q_*"):
            match = re.fullmatch(r"v7_q_(\d{6})", directory.name)
            if match:
                maximum = max(maximum, int(match.group(1)))
        return f"v7_q_{maximum + 1:06d}"

    def _question_dir(self, question_id: str) -> Path:
        if not QUESTION_ID_RE.fullmatch(question_id):
            raise WorkspaceError("question_id 必须为 v7_q_000001 格式")
        return self.questions / question_id

    @staticmethod
    def _read_json(path: Path, default: Any = None) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise WorkspaceError(f"JSON 损坏：{path}") from exc

    @staticmethod
    def _write_json(path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(value, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def _append_jsonl(path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, ensure_ascii=False) + "\n")

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    @contextlib.contextmanager
    def question_lock(self, question_id: str, actor: str, operation: str) -> Iterator[None]:
        self._question_dir(question_id)
        path = self.locks / f"{question_id}.json"
        payload = {"question_id": question_id, "actor": actor, "operation": operation, "started_at": now()}
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            current = self._read_json(path, {})
            raise LockError(f"题目正被处理：{current.get('actor', 'unknown')} / {current.get('operation', 'unknown')}") from exc
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False)
            yield
        finally:
            path.unlink(missing_ok=True)

    @contextlib.contextmanager
    def release_lock(self, actor: str) -> Iterator[None]:
        path = self.control / "release-lock.json"
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise LockError("已有发布构建正在执行") from exc
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump({"actor": actor, "started_at": now()}, stream, ensure_ascii=False)
            yield
        finally:
            path.unlink(missing_ok=True)

    def _audit(self, question_id: str, actor: str, channel: str, operation: str, reason: str, before: Any, after: Any) -> None:
        path = self._question_dir(question_id) / "audit.jsonl"
        event = {
            "at": now(), "actor": actor, "channel": channel, "operation": operation,
            "reason": reason, "before_hash": sha256(before) if before is not None else None,
            "after_hash": sha256(after) if after is not None else None,
        }
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")

    @staticmethod
    def _assert_expected(question: dict[str, Any], expected_question_version: int | None = None,
                         expected_archive_revision: int | None = None) -> None:
        if expected_question_version is not None and question.get("version") != expected_question_version:
            raise WorkspaceError(
                f"题目版本已变化：预期 v{expected_question_version}，当前 v{question.get('version')}"
            )
        current_revision = int(question.get("archive_revision", 0))
        if expected_archive_revision is not None and current_revision != expected_archive_revision:
            raise WorkspaceError(
                f"题目档案已变化：预期 r{expected_archive_revision}，当前 r{current_revision}"
            )

    def _touch_question(self, question: dict[str, Any]) -> dict[str, Any]:
        question["archive_revision"] = int(question.get("archive_revision", 0)) + 1
        question["updated_at"] = now()
        self._write_json(self._question_dir(question["question_id"]) / "question.json", question)
        return question

    @staticmethod
    def _legacy_workflow(question: dict[str, Any]) -> dict[str, Any]:
        status = str(question.get("status") or "")
        stage_map = {
            "received": "intake", "needs_source_clarification": "intake",
            "duplicate_pending": "duplicate_check", "merged": "duplicate_check",
            "ready_for_ds": "evidence_research", "needs_revalidation": "evidence_research",
            "ds_draft": "evidence_research", "needs_evidence": "evidence_research",
            "reviewable": "human_approval", "needs_human_review": "human_approval",
            "external_only": "evidence_confirmation", "question_conflict": "duplicate_check",
            "approved": "release_ready", "returned": "analysis_revision",
            "hold": "human_approval", "rejected": "human_approval",
        }
        disposition = "active"
        if status == "needs_source_clarification": disposition = "needs_source_clarification"
        if status == "merged": disposition = "merged"
        if status == "hold": disposition = "held"
        if status == "rejected": disposition = "rejected"
        return {
            "schema_version": "cams-workflow/v2",
            "question_id": question["question_id"],
            "stage": stage_map.get(status, "evidence_research"),
            "disposition": disposition,
            "question_version": question.get("version"),
            "duplicate_check": "not_applicable" if not status.startswith("duplicate") else "pending",
            "references": {},
            "legacy_status": status,
            "updated_at": question.get("updated_at") or now(),
        }

    def read_workflow(self, question_id: str) -> dict[str, Any]:
        path = self._question_dir(question_id) / "workflow.json"
        item = self._read_json(path)
        if item:
            return item
        return self._legacy_workflow(self.read_question(question_id))

    def _write_workflow_locked(self, question_id: str, stage: str | None = None,
                               disposition: str | None = None, **updates: Any) -> dict[str, Any]:
        workflow = dict(self.read_workflow(question_id))
        if stage is not None:
            if stage not in WORKFLOW_STAGES:
                raise WorkspaceError(f"不支持的工作流阶段：{stage}")
            workflow["stage"] = stage
        if disposition is not None:
            if disposition not in DISPOSITIONS:
                raise WorkspaceError(f"不支持的处置状态：{disposition}")
            workflow["disposition"] = disposition
        workflow.update(updates)
        workflow["schema_version"] = "cams-workflow/v2"
        workflow["question_id"] = question_id
        workflow["question_version"] = self.read_question(question_id).get("version")
        workflow["updated_at"] = now()
        self._write_json(self._question_dir(question_id) / "workflow.json", workflow)
        return workflow

    def read_task_state(self, question_id: str) -> dict[str, Any]:
        return self._read_json(self._question_dir(question_id) / "task_state.json", {
            "question_id": question_id, "status": "idle", "task_type": None,
            "actor": None, "waiting_for": None, "next_step": "等待开始处理",
            "updated_at": None,
        })

    def _record_task_locked(self, question_id: str, task_type: str, status: str, actor: str,
                            waiting_for: str | None = None, next_step: str = "",
                            error: str = "", summary: str = "") -> dict[str, Any]:
        if status not in {"idle", "running", "waiting", "completed", "failed"}:
            raise WorkspaceError("任务状态必须是 idle/running/waiting/completed/failed")
        previous = self.read_task_state(question_id)
        task = {
            "question_id": question_id, "task_type": task_type, "status": status,
            "actor": actor, "waiting_for": waiting_for, "next_step": next_step,
            "error": error, "summary": summary, "started_at": previous.get("started_at")
            if previous.get("task_type") == task_type and previous.get("status") == "running" else now(),
            "updated_at": now(),
        }
        self._write_json(self._question_dir(question_id) / "task_state.json", task)
        self._append_jsonl(self._question_dir(question_id) / "task_history.jsonl", task)
        return task

    def set_task_state(self, question_id: str, task_type: str, status: str, actor: str,
                       reason: str, waiting_for: str | None = None, next_step: str = "",
                       error: str = "", summary: str = "",
                       expected_question_version: int | None = None,
                       expected_archive_revision: int | None = None) -> dict[str, Any]:
        with self.question_lock(question_id, actor, "set_task_state"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            before = self.read_task_state(question_id)
            task = self._record_task_locked(question_id, task_type, status, actor, waiting_for,
                                            next_step, error, summary)
            self._touch_question(question)
            self._audit(question_id, actor, "codex", "set_task_state", reason, before, task)
            return {"question": question, "workflow": self.read_workflow(question_id), "task": task}

    def read_task_history(self, question_id: str) -> list[dict[str, Any]]:
        return self._read_jsonl(self._question_dir(question_id) / "task_history.jsonl")

    def initialize_workflow_v2(self, question_id: str, actor: str = "workflow-migration") -> dict[str, Any]:
        with self.question_lock(question_id, actor, "initialize_workflow_v2"):
            path = self._question_dir(question_id) / "workflow.json"
            if path.exists(): return {"changed": False, "workflow": self.read_workflow(question_id)}
            question = self.read_question(question_id)
            workflow = self._legacy_workflow(question)
            legacy_import = (self._question_dir(question_id) / "source" / "legacy_question.json").exists()
            if legacy_import:
                workflow.update({"stage": "evidence_research", "disposition": "active",
                                 "duplicate_check": "not_applicable", "migration_status": "migrated"})
            self._write_json(path, workflow)
            task = self._record_task_locked(question_id, workflow["stage"], "waiting", actor,
                                            waiting_for="codex" if workflow["disposition"] == "active" else "educator",
                                            next_step="从证据研究开始复核" if legacy_import else "按当前正式阶段继续处理")
            self._touch_question(question)
            self._audit(question_id, actor, "migration", "initialize_workflow_v2",
                        "升级到证据驱动工作流；保留全部旧记录", None, workflow)
            return {"changed": True, "question": question, "workflow": workflow, "task": task}

    def list_questions(self, status: str = "", query: str = "", offset: int = 0,
                       limit: int | None = None) -> list[dict[str, Any]]:
        rows = []
        needle = query.strip().casefold()
        for directory in sorted(self.questions.glob("v7_q_*")):
            item = self._read_json(directory / "question.json")
            if not item:
                continue
            workflow = self.read_workflow(item["question_id"])
            if status and status not in {workflow.get("stage"), workflow.get("disposition"), item.get("status")}:
                continue
            if needle:
                searchable = json.dumps(
                    {"question_id": item.get("question_id"), "content": item.get("content", {})},
                    ensure_ascii=False,
                ).casefold()
                if needle not in searchable:
                    continue
            rows.append({
                "question_id": item.get("question_id"),
                "version": item.get("version"),
                "archive_revision": int(item.get("archive_revision", 0)),
                "status": item.get("status"),
                "workflow_stage": workflow.get("stage"),
                "disposition": workflow.get("disposition"),
                "stem": (item.get("content") or {}).get("stem") or (item.get("content") or {}).get("stem_cn") or "",
                "updated_at": item.get("updated_at"),
            })
        start = max(0, int(offset))
        return rows[start:] if limit is None else rows[start:start + max(0, int(limit))]

    def read_question(self, question_id: str) -> dict[str, Any]:
        item = self._read_json(self._question_dir(question_id) / "question.json")
        if not item:
            raise WorkspaceError("题目不存在")
        item.setdefault("archive_revision", 0)
        return item

    @staticmethod
    def _suggested_action(stage: str) -> str:
        return {
            "intake": "整理题源",
            "duplicate_check": "检查重复题",
            "evidence_research": "整理证据",
            "evidence_confirmation": "检查证据结论",
            "analysis_drafting": "生成正式解析",
            "analysis_revision": "修改正式解析",
            "final_verification": "完成最终核验",
            "human_approval": "等待教研批准",
            "release_ready": "准备发布",
            "released": "已发布",
        }.get(stage, "处理当前题")

    def write_active_context(self, question_id: str) -> dict[str, Any]:
        """Record browser selection without changing the question archive."""
        self.read_question(question_id)
        workflow = self.read_workflow(question_id)
        context = {
            "schema_version": "cams-active-context/v1",
            "question_id": question_id,
            "workflow_stage": workflow.get("stage"),
            "disposition": workflow.get("disposition"),
            "suggested_action": self._suggested_action(str(workflow.get("stage") or "")),
            "selected_at": now(),
        }
        self._write_json(self.control / "active-context.json", context)
        return context

    def read_active_context(self) -> dict[str, Any]:
        context = self._read_json(self.control / "active-context.json", {})
        question_id = str(context.get("question_id") or "")
        if not question_id:
            return {"question_id": None, "workflow_stage": None, "disposition": None,
                    "suggested_action": "请先在网页选择题目", "selected_at": None}
        self.read_question(question_id)
        workflow = self.read_workflow(question_id)
        return {**context, "workflow_stage": workflow.get("stage"),
                "disposition": workflow.get("disposition"),
                "suggested_action": self._suggested_action(str(workflow.get("stage") or ""))}

    def assert_ds_ready(self, question_id: str) -> dict[str, Any]:
        question = self.read_question(question_id)
        workflow = self.read_workflow(question_id)
        if workflow.get("disposition") != "active" or workflow.get("stage") in {"intake", "duplicate_check"}:
            raise WorkspaceError("题目尚未通过原件和重复题准入，不能取证或进入 DS")
        intake = self.read_record(question_id, "intake")
        if intake:
            duplicate = self.read_record(question_id, "duplicate_check") or {}
            if not intake.get("attachments") or intake.get("errors") or intake.get("missing_fields"):
                raise WorkspaceError("新题原件或结构化题面不完整，不能取证或进入 DS")
            if duplicate.get("decision") not in {"new", "确为新题"} or duplicate.get("question_version") != question.get("version"):
                raise WorkspaceError("当前题面版本尚未完成“确为新题”判断")
        return question

    def read_record(self, question_id: str, name: str) -> dict[str, Any] | None:
        if name not in {"intake", "duplicate_check", "evidence_review", "ds_draft", "codex_review", "decision"}:
            raise WorkspaceError("不支持的记录类型")
        path = self._question_dir(question_id) / (f"source/{name}.json" if name == "intake" else f"{name}.json")
        return self._read_json(path)

    @staticmethod
    def _evidence_items(retrieval: dict[str, Any]) -> list[dict[str, Any]]:
        raw_items: list[dict[str, Any]] = []
        for key in ("main_candidates", "kg_candidates"):
            raw_items.extend(item for item in (retrieval.get(key) or []) if isinstance(item, dict))
        supplements = retrieval.get("option_supplements") or {}
        if isinstance(supplements, dict):
            for option, items in supplements.items():
                for item in items or []:
                    if isinstance(item, dict):
                        copy = dict(item)
                        copy["option"] = str(option)
                        raw_items.append(copy)
        items: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in raw_items:
            unit_id = str(item.get("unit_id") or "").strip()
            if not unit_id:
                continue
            identity = sha256({"unit_id": unit_id, "route": item.get("route"), "language": item.get("language"),
                               "knowledge_zh": item.get("knowledge_zh"), "knowledge_en": item.get("knowledge_en"),
                               "en_quote": item.get("en_quote")})[:20]
            if identity in seen:
                continue
            seen.add(identity)
            items.append({
                "evidence_id": f"ev_{identity}",
                "unit_id": unit_id,
                "knowledge_zh": item.get("knowledge_zh", ""),
                "knowledge_en": item.get("knowledge_en", ""),
                "en_quote": item.get("en_quote", ""),
                "heading_context": item.get("heading_context", []),
                "printed_page": item.get("printed_page", ""),
                "pdf_page": item.get("pdf_page", ""),
                "route": item.get("route", ""),
                "score": item.get("score"),
                "type": item.get("type", ""),
                "option": item.get("option"),
                "status": "pending",
                "note": "",
                "exclusion_reason": "",
            })
        return items

    def save_evidence_results(self, question_id: str, retrieval: dict[str, Any], actor: str, channel: str,
                              reason: str, expected_question_version: int | None = None,
                              expected_archive_revision: int | None = None) -> dict[str, Any]:
        if not isinstance(retrieval, dict):
            raise WorkspaceError("检索结果必须是对象")
        with self.question_lock(question_id, actor, "save_evidence_results"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            if question.get("status") in {"received", "needs_source_clarification", "duplicate_pending", "merged"}:
                raise WorkspaceError("题目尚未通过准入，不能保存教材依据")
            previous = self.read_record(question_id, "evidence_review")
            old_by_id = {item.get("evidence_id"): item for item in (previous or {}).get("items", [])}
            items = self._evidence_items(retrieval)
            for item in items:
                old = old_by_id.get(item["evidence_id"])
                if old:
                    item["status"] = old.get("status", "pending")
                    item["note"] = old.get("note", "")
                    item["exclusion_reason"] = old.get("exclusion_reason", "")
            record = {"question_id": question_id, "version": int((previous or {}).get("version", 0)) + 1,
                      "question_version": question["version"], "updated_at": now(),
                      "retrieval": retrieval, "items": items}
            self._write_json(self._question_dir(question_id) / "evidence_review.json", record)
            question["status"] = "ready_for_ds"
            self._touch_question(question)
            record["archive_revision"] = question["archive_revision"]
            self._audit(question_id, actor, channel, "save_evidence_results", reason, previous, record)
            return {"question": question, "evidence_review": record}

    def update_evidence_review(self, question_id: str, updates: list[dict[str, Any]], actor: str, channel: str,
                               reason: str, expected_question_version: int | None = None,
                               expected_archive_revision: int | None = None) -> dict[str, Any]:
        if not isinstance(updates, list) or not updates:
            raise WorkspaceError("至少提交一条教材依据决定")
        with self.question_lock(question_id, actor, "update_evidence_review"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            previous = self.read_record(question_id, "evidence_review")
            if not previous:
                raise WorkspaceError("当前题目没有可审阅的教材依据")
            by_id = {item.get("evidence_id"): item for item in previous.get("items", [])}
            for update in updates:
                evidence_id = str(update.get("evidence_id") or "")
                status = str(update.get("status") or "")
                if evidence_id not in by_id:
                    raise WorkspaceError(f"教材依据不存在：{evidence_id}")
                if status not in {"pending", "adopted", "excluded"}:
                    raise WorkspaceError("教材依据状态必须是 pending/adopted/excluded")
                if status == "excluded" and not str(update.get("exclusion_reason") or "").strip():
                    raise WorkspaceError("排除教材依据必须填写理由")
                item = by_id[evidence_id]
                item["status"] = status
                item["note"] = str(update.get("note") or "")
                item["exclusion_reason"] = str(update.get("exclusion_reason") or "")
            record = dict(previous)
            record["version"] = int(previous.get("version", 0)) + 1
            record["question_version"] = question["version"]
            record["updated_at"] = now()
            self._write_json(self._question_dir(question_id) / "evidence_review.json", record)
            question["status"] = "ready_for_ds"
            self._touch_question(question)
            record["archive_revision"] = question["archive_revision"]
            self._audit(question_id, actor, channel, "update_evidence_review", reason, previous, record)
            return {"question": question, "evidence_review": record}

    @staticmethod
    def _discovery_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        items.extend(item for item in (payload.get("items") or []) if isinstance(item, dict))
        for key in ("main_candidates", "kg_candidates"):
            items.extend(item for item in (payload.get(key) or []) if isinstance(item, dict))
        for option, rows in (payload.get("option_supplements") or {}).items():
            for row in rows or []:
                if isinstance(row, dict):
                    item = dict(row); item.setdefault("option", str(option)); items.append(item)
        return items

    @staticmethod
    def _evidence_identity(item: dict[str, Any], textbook_version: str) -> str:
        source_kind = str(item.get("source_kind") or ("external" if item.get("url") else "textbook"))
        unit_id = str(item.get("unit_id") or "").strip()
        quote = item.get("quote") or item.get("en_quote") or item.get("knowledge_zh") or item.get("knowledge_en") or ""
        if source_kind == "textbook" and unit_id:
            identity = {"source_kind": source_kind, "textbook_version": textbook_version, "unit_id": unit_id}
        elif source_kind == "external":
            url = str(item.get("url") or item.get("link") or "").strip().rstrip("/").casefold()
            identity = {"source_kind": source_kind, "url": url, "quote": WorkspaceStore._canonical_text(quote)}
        else:
            identity = {"source_kind": source_kind, "textbook_version": textbook_version,
                        "pdf_page": item.get("pdf_page"), "quote": WorkspaceStore._canonical_text(quote)}
        return f"ev_{sha256(identity)[:20]}"

    def read_evidence_catalog(self, question_id: str, scope: str = "all", source_kind: str = "",
                              method: str = "", option: str = "", run_id: str = "", offset: int = 0,
                              limit: int = 20) -> dict[str, Any]:
        catalog = self._read_json(self._question_dir(question_id) / "evidence_catalog.json", {
            "question_id": question_id, "version": 0, "question_version": self.read_question(question_id)["version"],
            "items": [], "updated_at": None,
        })
        all_items = list(catalog.get("items") or [])
        available_runs = sorted({hit.get("run_id") for row in all_items for hit in row.get("discoveries", []) if hit.get("run_id")})
        rows = list(all_items)
        if scope == "curated": rows = [row for row in rows if (row.get("curation") or {}).get("selected")]
        if scope == "suggested": rows = [row for row in rows if (row.get("educator_suggestion") or {}).get("selected")]
        if source_kind: rows = [row for row in rows if row.get("source_kind") == source_kind]
        if option: rows = [row for row in rows if str((row.get("curation") or {}).get("target_option") or row.get("option") or "") == option]
        if method:
            rows = [row for row in rows if any(hit.get("method") == method for hit in row.get("discoveries", []))]
        if run_id:
            rows = [row for row in rows if any(hit.get("run_id") == run_id for hit in row.get("discoveries", []))]
        start, size = max(0, int(offset)), min(100, max(1, int(limit)))
        return {"question_id": question_id, "version": catalog.get("version", 0), "items": rows[start:start + size],
                "total": len(rows), "offset": start, "limit": size, "available_runs": available_runs,
                "counts": {"all": len(catalog.get("items") or []),
                           "curated": sum(1 for row in catalog.get("items") or [] if (row.get("curation") or {}).get("selected"))}}

    def register_evidence_run(self, question_id: str, payload: dict[str, Any], discovery_method: str,
                              actor: str, channel: str, reason: str,
                              expected_question_version: int | None = None,
                              expected_archive_revision: int | None = None) -> dict[str, Any]:
        if discovery_method not in DISCOVERY_METHODS:
            raise WorkspaceError("不支持的证据发现方式")
        incoming = self._discovery_items(payload)
        if not incoming:
            raise WorkspaceError("本轮没有可登记的证据")
        with self.question_lock(question_id, actor, "register_evidence_run"):
            question = self.assert_ds_ready(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            workflow = self.read_workflow(question_id)
            if workflow.get("disposition") != "active" or workflow.get("stage") != "evidence_research":
                raise WorkspaceError("当前阶段不能登记新证据；如已确认依据，请先正式重开证据")
            catalog_path = self._question_dir(question_id) / "evidence_catalog.json"
            previous = self._read_json(catalog_path, {"question_id": question_id, "version": 0, "items": []})
            by_id = {row["evidence_id"]: dict(row) for row in previous.get("items", [])}
            run_id = f"run_{len(self._read_jsonl(self._question_dir(question_id) / 'retrieval_runs.jsonl')) + 1:04d}"
            textbook_version = str((payload.get("asset_versions") or {}).get("textbook") or payload.get("textbook_version") or "unknown")
            evidence_ids: list[str] = []
            for rank, raw in enumerate(incoming, 1):
                evidence_id = self._evidence_identity(raw, textbook_version)
                evidence_ids.append(evidence_id)
                row = by_id.get(evidence_id, {
                    "evidence_id": evidence_id,
                    "source_kind": raw.get("source_kind") or ("external" if raw.get("url") else "textbook"),
                    "unit_id": raw.get("unit_id"), "textbook_version": textbook_version,
                    "quote": raw.get("quote") or raw.get("en_quote") or raw.get("knowledge_zh") or raw.get("knowledge_en") or "",
                    "knowledge_zh": raw.get("knowledge_zh", ""), "knowledge_en": raw.get("knowledge_en", ""),
                    "heading_context": raw.get("heading_context") or raw.get("chapter") or [],
                    "printed_page": raw.get("printed_page", ""), "pdf_page": raw.get("pdf_page", ""),
                    "institution": raw.get("institution", ""), "title": raw.get("title", ""),
                    "published_at": raw.get("published_at", ""), "url": raw.get("url") or raw.get("link") or "",
                    "archived_path": raw.get("archived_path", ""), "option": raw.get("option"),
                    "discoveries": [], "curation": {"selected": False},
                })
                discoveries = row.setdefault("discoveries", [])
                hits = raw.get("retrieval_hits") or [{}]
                for hit in hits:
                    discovery = {"run_id": run_id, "method": discovery_method,
                                 "route": hit.get("route") or raw.get("route") or discovery_method,
                                 "query": hit.get("query") or payload.get("query") or "",
                                 "rank": hit.get("rank") or rank, "score": hit.get("raw_score", raw.get("score")),
                                 "actor": actor, "at": now()}
                    key = sha256({key: discovery.get(key) for key in ("run_id", "method", "route", "query", "rank")})
                    if not any(item.get("discovery_key") == key for item in discoveries):
                        discovery["discovery_key"] = key; discoveries.append(discovery)
                by_id[evidence_id] = row
            catalog = {"schema_version": "cams-evidence-catalog/v2", "question_id": question_id,
                       "version": int(previous.get("version", 0)) + 1, "question_version": question["version"],
                       "updated_at": now(), "items": list(by_id.values())}
            run = {"schema_version": "cams-retrieval-run/v2", "run_id": run_id, "question_id": question_id,
                   "question_version": question["version"], "method": discovery_method,
                   "query": payload.get("query") or "", "config": payload.get("config") or {},
                   "asset_versions": payload.get("asset_versions") or {}, "evidence_ids": evidence_ids,
                   "raw_result": payload, "actor": actor, "created_at": now()}
            self._write_json(catalog_path, catalog)
            self._append_jsonl(self._question_dir(question_id) / "retrieval_runs.jsonl", run)
            workflow = self._write_workflow_locked(question_id, "evidence_research", references={**(workflow.get("references") or {}), "evidence_catalog_version": catalog["version"]})
            task = self._record_task_locked(question_id, "evidence_research", "completed", actor,
                                            next_step="Codex 核对、去重并整理精选依据",
                                            summary=f"本轮登记 {len(evidence_ids)} 条发现，目录共 {len(catalog['items'])} 条")
            self._touch_question(question)
            self._audit(question_id, actor, channel, "register_evidence_run", reason, previous, catalog)
            return {"question": question, "workflow": workflow, "task": task, "run": run,
                    "catalog": {"version": catalog["version"], "total": len(catalog["items"]), "added_or_seen": len(evidence_ids)}}

    def curate_evidence(self, question_id: str, updates: list[dict[str, Any]], actor: str, channel: str,
                        reason: str, educator_suggestion: bool = False,
                        expected_question_version: int | None = None,
                        expected_archive_revision: int | None = None) -> dict[str, Any]:
        if not updates:
            raise WorkspaceError("至少提交一条证据选择")
        with self.question_lock(question_id, actor, "curate_evidence"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            if self.read_workflow(question_id).get("stage") != "evidence_research":
                raise WorkspaceError("只有证据研究阶段可以调整精选或提交教研建议")
            path = self._question_dir(question_id) / "evidence_catalog.json"
            previous = self._read_json(path)
            if not previous: raise WorkspaceError("当前没有证据目录")
            by_id = {row["evidence_id"]: row for row in previous.get("items", [])}
            target_key = "educator_suggestion" if educator_suggestion else "curation"
            for update in updates:
                evidence_id = str(update.get("evidence_id") or "")
                if evidence_id not in by_id: raise WorkspaceError(f"证据不存在：{evidence_id}")
                selected = bool(update.get("selected"))
                role = str(update.get("role") or "")
                if selected and role not in EVIDENCE_ROLES: raise WorkspaceError("精选证据必须标明作用")
                if role == "exclude_option" and not str(update.get("target_option") or "").strip():
                    raise WorkspaceError("排除选项的证据必须指定选项")
                by_id[evidence_id][target_key] = {"selected": selected, "role": role if selected else None,
                                                  "target_option": update.get("target_option") if selected else None,
                                                  "note": str(update.get("note") or ""), "actor": actor, "updated_at": now()}
            catalog = dict(previous); catalog["version"] = int(previous.get("version", 0)) + 1
            catalog["items"] = list(by_id.values()); catalog["updated_at"] = now()
            self._write_json(path, catalog)
            workflow = self._write_workflow_locked(question_id, "evidence_research",
                references={**(self.read_workflow(question_id).get("references") or {}), "evidence_catalog_version": catalog["version"]})
            self._touch_question(question)
            self._audit(question_id, actor, channel, "suggest_evidence" if educator_suggestion else "curate_evidence", reason, previous, catalog)
            return {"question": question, "workflow": workflow,
                    "catalog": self.read_evidence_catalog(question_id, "curated" if not educator_suggestion else "suggested", limit=100)}

    def read_evidence_candidates(self, question_id: str) -> list[dict[str, Any]]:
        return self._read_jsonl(self._question_dir(question_id) / "evidence_candidates.jsonl")

    def submit_evidence_candidate(self, question_id: str, actor: str, channel: str, reason: str,
                                  expected_question_version: int | None = None,
                                  expected_archive_revision: int | None = None) -> dict[str, Any]:
        with self.question_lock(question_id, actor, "submit_evidence_candidate"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            workflow = self.read_workflow(question_id)
            if workflow.get("stage") != "evidence_research" or workflow.get("disposition") != "active":
                raise WorkspaceError("只有证据研究阶段可以提交最终证据候选")
            catalog = self._read_json(self._question_dir(question_id) / "evidence_catalog.json")
            selected = [row for row in (catalog or {}).get("items", []) if (row.get("curation") or {}).get("selected")]
            if not selected: raise WorkspaceError("Codex 至少精选一条证据后才能提交")
            candidates = self.read_evidence_candidates(question_id)
            record = {"schema_version": "cams-evidence-candidate/v2", "question_id": question_id,
                      "version": len(candidates) + 1, "question_version": question["version"],
                      "catalog_version": catalog["version"], "status": "pending_educator",
                      "entries": [{"evidence_id": row["evidence_id"], **(row.get("curation") or {})} for row in selected],
                      "actor": actor, "reason": reason, "created_at": now()}
            self._append_jsonl(self._question_dir(question_id) / "evidence_candidates.jsonl", record)
            references = {**(workflow.get("references") or {}), "evidence_candidate_version": record["version"],
                          "evidence_catalog_version": catalog["version"]}
            workflow = self._write_workflow_locked(question_id, "evidence_confirmation", references=references)
            task = self._record_task_locked(question_id, "evidence_confirmation", "waiting", actor,
                                            waiting_for="educator", next_step="请教研确认依据，或带理由退回补证")
            self._touch_question(question)
            self._audit(question_id, actor, channel, "submit_evidence_candidate", reason, None, record)
            return {"question": question, "workflow": workflow, "task": task, "candidate": record}

    def review_evidence_candidate(self, question_id: str, action: str, actor: str, channel: str,
                                  reason: str, expected_question_version: int | None = None,
                                  expected_archive_revision: int | None = None) -> dict[str, Any]:
        if action not in {"confirm", "return"}: raise WorkspaceError("证据决定必须是 confirm 或 return")
        if action == "return" and not reason.strip(): raise WorkspaceError("退回补证必须填写理由")
        with self.question_lock(question_id, actor, "review_evidence_candidate"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            workflow = self.read_workflow(question_id)
            if workflow.get("stage") != "evidence_confirmation": raise WorkspaceError("当前没有待教研确认的证据候选")
            candidates = self.read_evidence_candidates(question_id)
            if not candidates: raise WorkspaceError("证据候选不存在")
            candidate = candidates[-1]
            previous = self._read_json(self._question_dir(question_id) / "evidence_confirmation.json")
            version = int((previous or {}).get("version", 0)) + 1
            record = {"schema_version": "cams-evidence-confirmation/v2", "question_id": question_id,
                      "version": version, "question_version": question["version"],
                      "candidate_version": candidate["version"], "catalog_version": candidate["catalog_version"],
                      "status": "confirmed" if action == "confirm" else "returned",
                      "reason": reason, "actor": actor, "updated_at": now()}
            if previous: self._append_jsonl(self._question_dir(question_id) / "evidence_confirmation_history.jsonl", previous)
            self._write_json(self._question_dir(question_id) / "evidence_confirmation.json", record)
            references = {**(workflow.get("references") or {}), "confirmed_evidence_version": version if action == "confirm" else None}
            stage = "analysis_drafting" if action == "confirm" else "evidence_research"
            workflow = self._write_workflow_locked(question_id, stage, references=references)
            task = self._record_task_locked(question_id, "evidence_confirmation", "completed" if action == "confirm" else "waiting", actor,
                                            waiting_for="codex", next_step="请 Codex 按固定模板生成正式解析" if action == "confirm" else "请 Codex 根据退回理由继续补证",
                                            summary="教研已确认最终证据" if action == "confirm" else "教研已退回补证")
            self._touch_question(question)
            self._audit(question_id, actor, channel, "confirm_evidence" if action == "confirm" else "return_evidence", reason, previous, record)
            return {"question": question, "workflow": workflow, "task": task, "confirmation": record}

    def reopen_evidence(self, question_id: str, actor: str, channel: str, reason: str,
                        expected_question_version: int | None = None,
                        expected_archive_revision: int | None = None) -> dict[str, Any]:
        if not reason.strip(): raise WorkspaceError("重开证据必须填写理由")
        with self.question_lock(question_id, actor, "reopen_evidence"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            workflow = self.read_workflow(question_id)
            confirmation = self._read_json(self._question_dir(question_id) / "evidence_confirmation.json")
            if not confirmation or confirmation.get("status") != "confirmed": raise WorkspaceError("当前没有可重开的已确认依据")
            self._append_jsonl(self._question_dir(question_id) / "evidence_confirmation_history.jsonl", confirmation)
            invalidated = dict(confirmation); invalidated.update({"status": "reopened", "reopened_at": now(), "reopen_reason": reason})
            self._write_json(self._question_dir(question_id) / "evidence_confirmation.json", invalidated)
            references = {**(workflow.get("references") or {}), "confirmed_evidence_version": None,
                          "analysis_version": None, "final_check_version": None, "decision_version": None}
            workflow = self._write_workflow_locked(question_id, "evidence_research", references=references)
            task = self._record_task_locked(question_id, "evidence_research", "waiting", actor,
                                            waiting_for="codex", next_step="根据重开理由继续补证", summary=reason)
            self._touch_question(question)
            self._audit(question_id, actor, channel, "reopen_evidence", reason, confirmation, invalidated)
            return {"question": question, "workflow": workflow, "task": task}

    def read_analysis_versions(self, question_id: str) -> list[dict[str, Any]]:
        return self._read_jsonl(self._question_dir(question_id) / "analysis_versions.jsonl")

    def read_analysis_feedback(self, question_id: str) -> list[dict[str, Any]]:
        return self._read_jsonl(self._question_dir(question_id) / "analysis_feedback.jsonl")

    @staticmethod
    def _validate_analysis(analysis: dict[str, Any]) -> None:
        required = {"exam_point", "core_analysis", "option_analysis", "pitfall", "evidence"}
        missing = sorted(key for key in required if key not in analysis)
        if missing: raise WorkspaceError(f"正式解析缺少模板板块：{', '.join(missing)}")
        if not isinstance(analysis.get("option_analysis"), (dict, list)):
            raise WorkspaceError("错误项分析必须是对象或数组")
        if not isinstance(analysis.get("evidence"), list): raise WorkspaceError("教材依据必须是数组")

    def write_analysis_version(self, question_id: str, analysis: dict[str, Any], actor: str, channel: str,
                               reason: str, feedback_responses: list[dict[str, Any]] | None = None,
                               expected_question_version: int | None = None,
                               expected_archive_revision: int | None = None) -> dict[str, Any]:
        self._validate_analysis(analysis)
        with self.question_lock(question_id, actor, "write_analysis_version"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            workflow = self.read_workflow(question_id)
            if workflow.get("stage") not in {"analysis_drafting", "analysis_revision"}:
                raise WorkspaceError("当前阶段不能生成或修改正式解析")
            confirmation = self._read_json(self._question_dir(question_id) / "evidence_confirmation.json")
            if not confirmation or confirmation.get("status") != "confirmed": raise WorkspaceError("正式解析必须基于教研确认的证据")
            responses = feedback_responses or []
            feedback_ids = {row.get("feedback_id") for row in self.read_analysis_feedback(question_id)}
            for response in responses:
                if response.get("feedback_id") not in feedback_ids: raise WorkspaceError("解析反馈编号不存在")
                if response.get("status") not in {"addressed", "not_addressed"} or not str(response.get("response") or "").strip():
                    raise WorkspaceError("每条反馈必须记录处理结果和说明")
            versions = self.read_analysis_versions(question_id)
            record = {"schema_version": "cams-analysis/v2", "question_id": question_id,
                      "version": len(versions) + 1, "question_version": question["version"],
                      "evidence_confirmation_version": confirmation["version"], "analysis": analysis,
                      "feedback_responses": responses, "actor": actor, "reason": reason, "created_at": now()}
            self._append_jsonl(self._question_dir(question_id) / "analysis_versions.jsonl", record)
            references = {**(workflow.get("references") or {}), "analysis_version": record["version"],
                          "final_check_version": None, "decision_version": None}
            workflow = self._write_workflow_locked(question_id, "analysis_revision", references=references)
            task = self._record_task_locked(question_id, "analysis_revision", "waiting", actor,
                                            waiting_for="educator", next_step="请教研审阅并批注，或标记润色完成")
            self._touch_question(question)
            self._audit(question_id, actor, channel, "write_analysis_version", reason, versions[-1] if versions else None, record)
            return {"question": question, "workflow": workflow, "task": task, "analysis": record}

    def add_analysis_feedback(self, question_id: str, section: str, comment: str, actor: str,
                              channel: str, reason: str, expected_question_version: int | None = None,
                              expected_archive_revision: int | None = None) -> dict[str, Any]:
        if not comment.strip(): raise WorkspaceError("解析批注不能为空")
        with self.question_lock(question_id, actor, "add_analysis_feedback"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            if self.read_workflow(question_id).get("stage") != "analysis_revision":
                raise WorkspaceError("只有解析润色阶段可以提交教研批注")
            versions = self.read_analysis_versions(question_id)
            if not versions: raise WorkspaceError("当前没有可批注的正式解析")
            history = self.read_analysis_feedback(question_id)
            feedback = {"feedback_id": f"fb_{len(history) + 1:04d}", "question_id": question_id,
                        "analysis_version": versions[-1]["version"], "section": section or "overall",
                        "comment": comment, "actor": actor, "created_at": now()}
            self._append_jsonl(self._question_dir(question_id) / "analysis_feedback.jsonl", feedback)
            workflow = self._write_workflow_locked(question_id, "analysis_revision")
            task = self._record_task_locked(question_id, "analysis_revision", "waiting", actor,
                                            waiting_for="codex", next_step="请 Codex 根据教研批注生成新版本")
            self._touch_question(question)
            self._audit(question_id, actor, channel, "add_analysis_feedback", reason, None, feedback)
            return {"question": question, "workflow": workflow, "task": task, "feedback": feedback}

    def mark_polishing_complete(self, question_id: str, actor: str, channel: str, reason: str,
                                expected_question_version: int | None = None,
                                expected_archive_revision: int | None = None) -> dict[str, Any]:
        with self.question_lock(question_id, actor, "mark_polishing_complete"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            if self.read_workflow(question_id).get("stage") != "analysis_revision":
                raise WorkspaceError("只有解析润色阶段可以标记润色完成")
            versions = self.read_analysis_versions(question_id)
            if not versions: raise WorkspaceError("当前没有正式解析")
            latest = versions[-1]
            answered = {row.get("feedback_id") for row in latest.get("feedback_responses", [])}
            unresolved = [row["feedback_id"] for row in self.read_analysis_feedback(question_id) if row["feedback_id"] not in answered]
            if unresolved: raise WorkspaceError(f"仍有批注未由 Codex 回应：{', '.join(unresolved)}")
            workflow = self._write_workflow_locked(question_id, "final_verification")
            task = self._record_task_locked(question_id, "final_verification", "waiting", actor,
                                            waiting_for="codex", next_step="请 Codex 对固定版本执行最终核验")
            self._touch_question(question)
            self._audit(question_id, actor, channel, "mark_polishing_complete", reason, None, latest)
            return {"question": question, "workflow": workflow, "task": task}

    def read_final_checks(self, question_id: str) -> list[dict[str, Any]]:
        return self._read_jsonl(self._question_dir(question_id) / "final_checks.jsonl")

    def write_final_check(self, question_id: str, check: dict[str, Any], actor: str, channel: str,
                          reason: str, expected_question_version: int | None = None,
                          expected_archive_revision: int | None = None) -> dict[str, Any]:
        status = str(check.get("status") or "")
        if status not in {"passed", "needs_analysis", "needs_evidence", "needs_question"}:
            raise WorkspaceError("最终核验状态不合法")
        if not isinstance(check.get("checks"), list): raise WorkspaceError("最终核验必须包含 checks 数组")
        with self.question_lock(question_id, actor, "write_final_check"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            workflow = self.read_workflow(question_id)
            if workflow.get("stage") != "final_verification": raise WorkspaceError("只有最终核验阶段可以写入总检")
            analyses = self.read_analysis_versions(question_id)
            confirmation = self._read_json(self._question_dir(question_id) / "evidence_confirmation.json")
            if not analyses or not confirmation or confirmation.get("status") != "confirmed":
                raise WorkspaceError("最终核验缺少有效解析或已确认依据")
            history = self.read_final_checks(question_id)
            record = {"schema_version": "cams-final-check/v2", "question_id": question_id,
                      "version": len(history) + 1, "question_version": question["version"],
                      "evidence_confirmation_version": confirmation["version"],
                      "analysis_version": analyses[-1]["version"], "status": status,
                      "checks": check["checks"], "summary": str(check.get("summary") or ""),
                      "actor": actor, "created_at": now()}
            self._append_jsonl(self._question_dir(question_id) / "final_checks.jsonl", record)
            references = {**(workflow.get("references") or {}), "final_check_version": record["version"], "decision_version": None}
            if status == "passed":
                stage, waiting_for, next_step = "human_approval", "educator", "请教研批准、退回或暂缓"
            elif status == "needs_analysis":
                stage, waiting_for, next_step = "analysis_revision", "codex", "根据最终核验意见修改解析"
            elif status == "needs_evidence":
                stage, waiting_for, next_step = "evidence_research", "codex", "根据最终核验意见重新补证"
                references.update({"confirmed_evidence_version": None, "analysis_version": None})
                if confirmation:
                    self._append_jsonl(self._question_dir(question_id) / "evidence_confirmation_history.jsonl", confirmation)
                    invalidated = dict(confirmation); invalidated.update({"status": "reopened", "reopened_at": now(), "reopen_reason": reason})
                    self._write_json(self._question_dir(question_id) / "evidence_confirmation.json", invalidated)
            else:
                stage, waiting_for, next_step = "duplicate_check", "educator", "核对并修正题面后重新检查重复题"
            workflow = self._write_workflow_locked(question_id, stage, references=references)
            task = self._record_task_locked(question_id, "final_verification", "completed" if status == "passed" else "waiting",
                                            actor, waiting_for=waiting_for, next_step=next_step, summary=record["summary"])
            self._touch_question(question)
            self._audit(question_id, actor, channel, "write_final_check", reason, history[-1] if history else None, record)
            return {"question": question, "workflow": workflow, "task": task, "final_check": record}

    def record_workflow_decision(self, question_id: str, decision: str, actor: str, channel: str,
                                 reason: str, expected_question_version: int | None = None,
                                 expected_archive_revision: int | None = None) -> dict[str, Any]:
        if decision not in {"approved", "returned", "hold", "rejected"}:
            raise WorkspaceError("人工决定必须是 approved/returned/hold/rejected")
        if decision != "approved" and not reason.strip(): raise WorkspaceError("退回、暂缓或不收录必须填写理由")
        with self.question_lock(question_id, actor, "record_workflow_decision"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            workflow = self.read_workflow(question_id)
            if workflow.get("stage") != "human_approval": raise WorkspaceError("当前题目尚未进入教研批准阶段")
            checks = self.read_final_checks(question_id)
            analyses = self.read_analysis_versions(question_id)
            confirmation = self._read_json(self._question_dir(question_id) / "evidence_confirmation.json")
            if not checks or checks[-1].get("status") != "passed" or not analyses or not confirmation or confirmation.get("status") != "confirmed":
                raise WorkspaceError("批准前必须具备有效的证据确认、正式解析和通过的最终核验")
            previous = self._read_json(self._question_dir(question_id) / "decision.json")
            record = {"schema_version": "cams-decision/v2", "question_id": question_id,
                      "version": int((previous or {}).get("version", 0)) + 1,
                      "question_version": question["version"], "evidence_confirmation_version": confirmation["version"],
                      "analysis_version": analyses[-1]["version"], "final_check_version": checks[-1]["version"],
                      "decision": decision, "reason": reason, "actor": actor, "updated_at": now()}
            self._write_json(self._question_dir(question_id) / "decision.json", record)
            if decision == "approved": stage, disposition, waiting_for, next_step = "release_ready", "active", None, "可构建发布包"
            elif decision == "returned": stage, disposition, waiting_for, next_step = "analysis_revision", "active", "codex", "根据教研退回理由修改解析"
            elif decision == "hold": stage, disposition, waiting_for, next_step = "human_approval", "held", "educator", "等待教研恢复处理"
            else: stage, disposition, waiting_for, next_step = "human_approval", "rejected", None, "保留档案，不进入发布"
            references = {**(workflow.get("references") or {}), "decision_version": record["version"]}
            workflow = self._write_workflow_locked(question_id, stage, disposition, references=references)
            task = self._record_task_locked(question_id, "human_approval", "completed" if decision == "approved" else "waiting",
                                            actor, waiting_for=waiting_for, next_step=next_step, summary=reason)
            question["status"] = decision
            self._touch_question(question)
            self._audit(question_id, actor, channel, "record_workflow_decision", reason, previous, record)
            return {"question": question, "workflow": workflow, "task": task, "decision": record}

    def workflow_detail(self, question_id: str) -> dict[str, Any]:
        analyses, candidates, checks = (self.read_analysis_versions(question_id),
                                        self.read_evidence_candidates(question_id),
                                        self.read_final_checks(question_id))
        return {"question": self.read_question(question_id), "workflow": self.read_workflow(question_id),
                "task": self.read_task_state(question_id), "intake": self.read_record(question_id, "intake"),
                "duplicate_check": self.read_record(question_id, "duplicate_check"),
                "evidence_summary": self.read_evidence_catalog(question_id, "curated", limit=100),
                "evidence_candidate": candidates[-1] if candidates else None,
                "evidence_confirmation": self._read_json(self._question_dir(question_id) / "evidence_confirmation.json"),
                "analysis": analyses[-1] if analyses else None,
                "analysis_feedback": self.read_analysis_feedback(question_id),
                "final_check": checks[-1] if checks else None,
                "decision": self._read_json(self._question_dir(question_id) / "decision.json")}

    @staticmethod
    def deepseek_settings_path() -> Path:
        if os.name == "nt":
            base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
        return base / "CAMSWorkbench" / "settings.local.json"

    def read_deepseek_settings(self, masked: bool = True) -> dict[str, Any]:
        settings = self._read_json(self.deepseek_settings_path(), {})
        result = {"enabled": bool(settings.get("enabled", False)),
                  "base_url": settings.get("base_url") or "https://api.deepseek.com/v1",
                  "model": settings.get("model") or "deepseek-v4-pro",
                  "configured": bool(settings.get("api_key"))}
        if not masked: result["api_key"] = settings.get("api_key", "")
        return result

    def write_deepseek_settings(self, enabled: bool, base_url: str, model: str,
                                api_key: str | None = None) -> dict[str, Any]:
        path = self.deepseek_settings_path()
        previous = self._read_json(path, {})
        value = {"enabled": bool(enabled),
                 "base_url": str(base_url or "https://api.deepseek.com/v1").rstrip("/"),
                 "model": str(model or "deepseek-v4-pro"),
                 "api_key": str(api_key) if api_key else str(previous.get("api_key") or "")}
        self._write_json(path, value)
        return self.read_deepseek_settings(masked=True)

    def prepare_ds_opinion_input(self, question_id: str) -> dict[str, Any]:
        question = self.assert_ds_ready(question_id)
        content = dict(question.get("content") or {})
        for key in ("answer", "reference_answer", "source_answer", "source_reference_answer", "answer_source"):
            content.pop(key, None)
        curated = self.read_evidence_catalog(question_id, "curated", limit=100)
        if not curated.get("items"): raise WorkspaceError("至少精选一条证据后才能请求 DS 辅助研判")
        return {"question": {"question_id": question_id, "version": question["version"], "content": content},
                "evidence_snapshot": {"catalog_version": curated["version"], "items": curated["items"]}}

    def save_ds_opinion(self, question_id: str, input_snapshot: dict[str, Any], result: dict[str, Any] | None,
                        model: str, status: str, actor: str, reason: str, error: str = "",
                        expected_question_version: int | None = None,
                        expected_archive_revision: int | None = None) -> dict[str, Any]:
        if status not in {"completed", "failed"}: raise WorkspaceError("DS 辅助研判状态不合法")
        with self.question_lock(question_id, actor, "save_ds_opinion"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            history = self._read_jsonl(self._question_dir(question_id) / "ds_opinions.jsonl")
            record = {"schema_version": "cams-ds-opinion/v1", "question_id": question_id,
                      "version": len(history) + 1, "question_version": question["version"],
                      "input_snapshot": input_snapshot, "model": model, "status": status,
                      "result": result, "error": error, "actor": actor, "reason": reason, "created_at": now()}
            self._append_jsonl(self._question_dir(question_id) / "ds_opinions.jsonl", record)
            task = self._record_task_locked(question_id, "ds_opinion", status, actor,
                                            next_step="返回正式证据研究流程",
                                            error=error, summary="DS 独立第二意见已记录" if status == "completed" else "DS 调用失败，不影响正式流程")
            self._touch_question(question)
            self._audit(question_id, actor, "codex", "request_ds_opinion", reason, None, record)
            return {"question": question, "workflow": self.read_workflow(question_id), "task": task, "opinion": record}

    @staticmethod
    def _canonical_text(value: Any) -> str:
        text = unicodedata.normalize("NFKC", str(value or "")).casefold()
        return re.sub(r"\s+|[\W_]+", "", text, flags=re.UNICODE)

    @staticmethod
    def _search_tokens(value: str) -> list[str]:
        normalized = unicodedata.normalize("NFKC", value).casefold()
        words = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", normalized)
        cjk = "".join(token for token in words if len(token) == 1 and "\u4e00" <= token <= "\u9fff")
        return words + [cjk[index:index + 2] for index in range(max(0, len(cjk) - 1))]

    def _bm25_scores(self, query: str, documents: list[str]) -> list[float]:
        query_tokens = self._search_tokens(query)
        docs = [self._search_tokens(value) for value in documents]
        if not query_tokens or not docs:
            return [0.0] * len(documents)
        average_length = sum(len(doc) for doc in docs) / max(1, len(docs))
        document_frequency = {token: sum(token in doc for doc in docs) for token in set(query_tokens)}
        scores: list[float] = []
        for doc in docs:
            score = 0.0
            for token in query_tokens:
                frequency = doc.count(token)
                if not frequency:
                    continue
                inverse_frequency = math.log(1 + (len(docs) - document_frequency[token] + 0.5) / (document_frequency[token] + 0.5))
                denominator = frequency + 1.5 * (1 - 0.75 + 0.75 * len(doc) / max(1.0, average_length))
                score += inverse_frequency * frequency * 2.5 / denominator
            scores.append(score)
        maximum = max(scores, default=0.0)
        return [value / maximum if maximum else 0.0 for value in scores]

    def _bge_scores(self, query: str, documents: list[str]) -> list[float] | None:
        global _BGE_MODEL, _BGE_MODEL_PATH
        model_path = self.root / "runtime" / "models" / "bge-m3"
        if not model_path.exists():
            return None
        try:
            from sentence_transformers import SentenceTransformer
            if _BGE_MODEL is None or _BGE_MODEL_PATH != str(model_path):
                _BGE_MODEL = SentenceTransformer(str(model_path), local_files_only=True)
                _BGE_MODEL_PATH = str(model_path)
            vectors = _BGE_MODEL.encode([query, *documents], normalize_embeddings=True, show_progress_bar=False)
            return [max(0.0, float(vectors[0] @ vectors[index + 1])) for index in range(len(documents))]
        except Exception:
            return None

    def _duplicate_candidates(self, content: dict[str, Any], exclude_question_id: str = "") -> list[dict[str, Any]]:
        stem = content.get("stem") or content.get("stem_cn") or ""
        options = content.get("options") or {}
        canonical = self._canonical_text(stem) + "|" + "|".join(
            self._canonical_text(options[key]) for key in sorted(options)
        )
        candidates: list[tuple[dict[str, Any], str, str]] = []
        for directory in sorted(self.questions.glob("v7_q_*")):
            item = self._read_json(directory / "question.json")
            if not item:
                continue
            if item.get("question_id") == exclude_question_id:
                continue
            other = item.get("content") or {}
            other_stem = other.get("stem") or other.get("stem_cn") or ""
            other_options = other.get("options") or {}
            other_canonical = self._canonical_text(other_stem) + "|" + "|".join(
                self._canonical_text(other_options[key]) for key in sorted(other_options)
            )
            if canonical and canonical == other_canonical:
                candidates.append((item, other_canonical, "exact"))
                continue
            left = " ".join([str(stem), *[str(value) for value in options.values()]])
            right = " ".join([str(other_stem), *[str(value) for value in other_options.values()]])
            candidates.append((item, right, left))
        query = " ".join([str(stem), *[str(value) for value in options.values()]])
        documents = [text for _, text, marker in candidates if marker != "exact"]
        bm25 = self._bm25_scores(query, documents)
        bge = self._bge_scores(query, documents)
        rows: list[dict[str, Any]] = []
        score_index = 0
        for item, text, marker in candidates:
            if marker == "exact":
                rows.append({"question_id": item["question_id"], "method": "exact_normalized", "score": 1.0, "confidence": "high"})
                continue
            lexical = SequenceMatcher(None, self._canonical_text(query), self._canonical_text(text)).ratio()
            if bge is not None:
                score = 0.6 * bge[score_index] + 0.3 * bm25[score_index] + 0.1 * lexical
                method = "bge_m3+bm25"
            else:
                score = 0.65 * bm25[score_index] + 0.35 * lexical
                method = "bm25+lexical_fallback"
            score_index += 1
            if score > 0:
                rows.append({"question_id": item["question_id"], "method": method, "score": round(score, 6), "confidence": "candidate"})
        rows.sort(key=lambda row: (-row["score"], row["question_id"]))
        return rows[:5]

    def create_question_intake(self, content: dict[str, Any], intake: dict[str, Any],
                               source_paths: list[str] | None, actor: str, channel: str,
                               reason: str) -> dict[str, Any]:
        """Create a new immutable source archive and put it behind the intake gates."""
        with self.question_id_lock(actor):
            question_id = self._next_question_id_unlocked()
            directory = self.questions / question_id
            directory.mkdir(parents=True, exist_ok=False)
        source_dir = directory / "source"
        files_dir = source_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)
        source_paths = [str(value) for value in (source_paths or []) if str(value).strip()]
        copied: list[dict[str, Any]] = []
        errors: list[str] = []
        for raw_path in source_paths:
            source = Path(raw_path).expanduser()
            allowed = {".png", ".jpg", ".jpeg", ".pdf"}
            try:
                if not source.exists() or not source.is_file():
                    errors.append(f"原件不存在: {raw_path}"); continue
                if source.suffix.casefold() not in allowed:
                    errors.append(f"不支持的原件格式: {source.name}"); continue
                if source.stat().st_size > 20 * 1024 * 1024:
                    errors.append(f"原件超过20MB: {source.name}"); continue
                target = files_dir / source.name
                sequence = 2
                while target.exists():
                    target = files_dir / f"{source.stem}-{sequence}{source.suffix.lower()}"
                    sequence += 1
                shutil.copy2(source, target)
                digest = hashlib.sha256(target.read_bytes()).hexdigest()
                source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
                if digest != source_digest:
                    target.unlink(missing_ok=True)
                    errors.append(f"原件哈希校验失败: {source.name}"); continue
                copied.append({"name": target.name, "sha256": digest, "size": target.stat().st_size})
            except OSError as exc:
                errors.append(f"复制原件失败 {source.name}: {exc}")
        status = "duplicate_pending"
        if not copied or errors:
            status = "needs_source_clarification"
        missing = []
        if not (content.get("stem") or content.get("stem_cn")): missing.append("stem")
        if not isinstance(content.get("options"), dict) or not content.get("options"): missing.append("options")
        if missing and status != "needs_source_clarification": status = "needs_source_clarification"
        answer_status = intake.get("answer_status") or ("known" if content.get("answer") else "unknown")
        question = {"question_id": question_id, "version": 1, "archive_revision": 1,
                    "status": status, "content": content, "updated_at": now()}
        intake_record = {"question_id": question_id, "source_type": intake.get("source_type", "unknown"),
                         "source_description": intake.get("source_description", ""),
                         "original_source_id": intake.get("original_source_id", ""),
                         "original_link": intake.get("original_link", ""), "received_at": now(),
                         "answer_status": answer_status, "raw_text": intake.get("raw_text", ""),
                         "attachments": copied, "source_paths_received": len(source_paths),
                         "missing_fields": missing, "errors": errors}
        self._write_json(directory / "question.json", question)
        self._write_json(source_dir / "intake.json", intake_record)
        duplicate = {"question_id": question_id, "question_version": 1, "status": "pending",
                     "candidates": self._duplicate_candidates(content, question_id) if status == "duplicate_pending" else [],
                     "decision": None, "rationale": "", "actor": None, "updated_at": now()}
        self._write_json(directory / "duplicate_check.json", duplicate)
        workflow = {"schema_version": "cams-workflow/v2", "question_id": question_id,
                    "stage": "intake" if status == "needs_source_clarification" else "duplicate_check",
                    "disposition": "needs_source_clarification" if status == "needs_source_clarification" else "active",
                    "question_version": 1, "duplicate_check": "pending", "references": {}, "updated_at": now()}
        self._write_json(directory / "workflow.json", workflow)
        self._record_task_locked(question_id, "intake", "waiting", actor,
                                 waiting_for="educator" if status == "needs_source_clarification" else "codex",
                                 next_step="补充可归档原件或完整题面" if status == "needs_source_clarification" else "请 Codex 完成重复题判断")
        self._audit(question_id, actor, channel, "create_question_intake", reason, None, {"question": question, "intake": intake_record, "duplicate_check": duplicate})
        return {"question": question, "workflow": workflow, "intake": intake_record, "duplicate_check": duplicate}

    def resolve_duplicate_check(self, question_id: str, decision: str, rationale: str,
                                actor: str, channel: str, reason: str,
                                expected_archive_revision: int | None = None) -> dict[str, Any]:
        if decision not in {"new", "merge", "hold", "确为新题", "合并既有题", "待人工判断"}:
            raise WorkspaceError("重复判断必须是 new/merge/hold")
        with self.question_lock(question_id, actor, "resolve_duplicate_check"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_archive_revision=expected_archive_revision)
            if question.get("status") != "duplicate_pending":
                raise WorkspaceError("只有原件和题面完整的待判重题可以提交重复判断")
            duplicate = self.read_record(question_id, "duplicate_check") or {"candidates": []}
            duplicate.update({"status": "resolved" if decision in {"new", "确为新题", "merge", "合并既有题"} else "pending",
                              "question_version": question["version"], "decision": decision,
                              "rationale": rationale, "actor": actor, "updated_at": now()})
            self._write_json(self._question_dir(question_id) / "duplicate_check.json", duplicate)
            normalized = {"new": "new", "确为新题": "new", "merge": "merge", "合并既有题": "merge", "hold": "hold", "待人工判断": "hold"}[decision]
            question["status"] = "ready_for_ds" if normalized == "new" else ("merged" if normalized == "merge" else "duplicate_pending")
            if normalized == "new":
                workflow = self._write_workflow_locked(question_id, "evidence_research", "active", duplicate_check="resolved")
                task = self._record_task_locked(question_id, "evidence_research", "waiting", actor,
                                                waiting_for="codex", next_step="开始教材证据研究")
            elif normalized == "merge":
                workflow = self._write_workflow_locked(question_id, "duplicate_check", "merged", duplicate_check="resolved")
                task = self._record_task_locked(question_id, "duplicate_check", "completed", actor,
                                                next_step="保留题源档案，不再进入取证")
            else:
                workflow = self._write_workflow_locked(question_id, "duplicate_check", "active", duplicate_check="pending")
                task = self._record_task_locked(question_id, "duplicate_check", "waiting", actor,
                                                waiting_for="educator", next_step="等待教研判断疑似重复题")
            self._touch_question(question)
            self._audit(question_id, actor, channel, "resolve_duplicate_check", reason, None, duplicate)
            return {"question": question, "workflow": workflow, "task": task, "duplicate_check": duplicate}

    def read_audit(self, question_id: str) -> list[dict[str, Any]]:
        path = self._question_dir(question_id) / "audit.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def write_question(self, question_id: str, content: dict[str, Any], actor: str, channel: str,
                       reason: str, expected_question_version: int | None = None,
                       expected_archive_revision: int | None = None) -> dict[str, Any]:
        with self.question_lock(question_id, actor, "write_question"):
            directory = self._question_dir(question_id)
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "source").mkdir(exist_ok=True)
            previous = self._read_json(directory / "question.json")
            if previous:
                self._assert_expected(previous, expected_question_version, expected_archive_revision)
                if previous.get("content", {}) == content:
                    return previous
            changed = previous is None or previous.get("content", {}) != content
            item = {
                "question_id": question_id,
                "version": int((previous or {}).get("version", 0)) + 1,
                "archive_revision": int((previous or {}).get("archive_revision", 0)) + 1,
                "status": "needs_revalidation" if changed else (previous or {}).get("status", "draft"),
                "content": content,
                "updated_at": now(),
            }
            self._write_json(directory / "question.json", item)
            intake = self.read_record(question_id, "intake") if previous else None
            if intake and changed:
                item["status"] = "duplicate_pending"
                self._write_json(directory / "question.json", item)
                old_duplicate = self.read_record(question_id, "duplicate_check")
                new_duplicate = {"question_id": question_id, "question_version": item["version"], "status": "pending",
                                 "candidates": self._duplicate_candidates(content, question_id), "decision": None,
                                 "rationale": "", "actor": None, "updated_at": now()}
                self._write_json(directory / "duplicate_check.json", new_duplicate)
                self._audit(question_id, actor, channel, "reset_duplicate_check", reason, old_duplicate, new_duplicate)
                self._write_workflow_locked(question_id, "duplicate_check", "active", duplicate_check="pending",
                                            references={}, invalidated_at=now(), invalidation_reason=reason)
                self._record_task_locked(question_id, "duplicate_check", "waiting", actor,
                                         waiting_for="codex", next_step="题面已变化，请重新检查重复题")
            elif changed:
                self._write_workflow_locked(question_id, "evidence_research", "active", duplicate_check="not_applicable",
                                            references={}, invalidated_at=now(), invalidation_reason=reason)
                self._record_task_locked(question_id, "evidence_research", "waiting", actor,
                                         waiting_for="codex", next_step="题面已变化，请重新研究证据")
            self._audit(question_id, actor, channel, "write_question", reason, previous, item)
            return item

    def write_ds_draft(self, question_id: str, draft: dict[str, Any], actor: str, channel: str,
                       reason: str, expected_question_version: int | None = None,
                       expected_archive_revision: int | None = None) -> dict[str, Any]:
        with self.question_lock(question_id, actor, "write_ds_draft"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            if question.get("status") in {"received", "needs_source_clarification", "duplicate_pending", "merged"}:
                raise WorkspaceError("题目尚未通过原件和重复题准入，不能写入 DS 草稿")
            if not isinstance(draft.get("evidence"), list):
                raise WorkspaceError("DS 草稿必须包含 evidence 数组")
            evidence_review = self.read_record(question_id, "evidence_review")
            if evidence_review:
                adopted_ids = {item.get("evidence_id") for item in evidence_review.get("items", []) if item.get("status") == "adopted"}
                draft_ids = {item.get("evidence_id") for item in draft.get("evidence", []) if isinstance(item, dict) and item.get("evidence_id")}
                if not adopted_ids:
                    raise WorkspaceError("至少采用一条教材依据后才能写入 DS 草稿")
                if draft_ids - adopted_ids:
                    raise WorkspaceError("DS 草稿只能引用已采用的教材依据")
            previous = self.read_record(question_id, "ds_draft")
            item = {"question_id": question_id, "version": int((previous or {}).get("version", 0)) + 1,
                    "question_version": question["version"], "evidence_review_version": evidence_review.get("version") if evidence_review else None,
                    "status": "draft", "updated_at": now(), "draft": draft}
            self._write_json(self._question_dir(question_id) / "ds_draft.json", item)
            question["status"] = "ds_draft"
            self._touch_question(question)
            self._audit(question_id, actor, channel, "write_ds_draft", reason, previous, item)
            item["archive_revision"] = question["archive_revision"]
            return item

    def write_codex_review(self, question_id: str, review: dict[str, Any], actor: str, channel: str,
                           reason: str, expected_question_version: int | None = None,
                           expected_archive_revision: int | None = None) -> dict[str, Any]:
        with self.question_lock(question_id, actor, "write_codex_review"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            if review.get("status") not in {"reviewable", "needs_evidence", "needs_human_review", "external_only", "question_conflict", "rejected"}:
                raise WorkspaceError("Codex 核验 status 不合法")
            if not isinstance(review.get("textbook_evidence"), list):
                raise WorkspaceError("Codex 核验必须包含 textbook_evidence 数组")
            evidence_review = self.read_record(question_id, "evidence_review")
            previous = self.read_record(question_id, "codex_review")
            item = {"question_id": question_id, "version": int((previous or {}).get("version", 0)) + 1,
                    "question_version": question["version"], "evidence_review_version": evidence_review.get("version") if evidence_review else None,
                    "updated_at": now(), "review": review}
            self._write_json(self._question_dir(question_id) / "codex_review.json", item)
            question["status"] = "reviewable" if review["status"] == "reviewable" else review["status"]
            self._touch_question(question)
            self._audit(question_id, actor, channel, "write_codex_review", reason, previous, item)
            item["archive_revision"] = question["archive_revision"]
            return item

    def record_decision(self, question_id: str, decision: dict[str, Any], actor: str, channel: str,
                        reason: str, expected_question_version: int | None = None,
                        expected_archive_revision: int | None = None) -> dict[str, Any]:
        with self.question_lock(question_id, actor, "record_decision"):
            question = self.read_question(question_id)
            self._assert_expected(question, expected_question_version, expected_archive_revision)
            review = self.read_record(question_id, "codex_review")
            evidence_review = self.read_record(question_id, "evidence_review")
            value = decision.get("status")
            if value not in {"approved", "returned", "hold", "rejected", "retracted"}:
                raise WorkspaceError("人工决定 status 不合法")
            if value == "approved" and (not review or review.get("question_version") != question["version"] or review.get("review", {}).get("status") != "reviewable"):
                raise WorkspaceError("批准前必须有与当前题目版本一致的 reviewable Codex 核验")
            previous = self.read_record(question_id, "decision")
            item = {"question_id": question_id, "version": int((previous or {}).get("version", 0)) + 1,
                    "question_version": question["version"], "codex_review_version": review.get("version") if review else None,
                    "evidence_review_version": evidence_review.get("version") if evidence_review else None,
                    "updated_at": now(), "decision": decision}
            self._write_json(self._question_dir(question_id) / "decision.json", item)
            question["status"] = value
            self._touch_question(question)
            self._audit(question_id, actor, channel, "record_decision", reason, previous, item)
            item["archive_revision"] = question["archive_revision"]
            return item

    def build_release(self, release_id: str, actor: str) -> dict[str, Any]:
        if not RELEASE_ID_RE.fullmatch(release_id):
            raise WorkspaceError("release_id 必须以 v7- 开头")
        with self.release_lock(actor):
            target = self.releases / release_id
            if target.exists():
                raise WorkspaceError("发布包已存在，不可覆盖")
            approved, questions, evidence, locked = [], [], [], []
            try:
                for row in self.list_questions():
                    qid = row["question_id"]
                    lock = self.question_lock(qid, actor, "build_release")
                    lock.__enter__(); locked.append(lock)
                    question = self.read_question(qid)
                    workflow_path = self._question_dir(qid) / "workflow.json"
                    workflow = self.read_workflow(qid)
                    if workflow_path.exists():
                        if workflow.get("stage") != "release_ready" or workflow.get("disposition") != "active":
                            continue
                        decision = self._read_json(self._question_dir(qid) / "decision.json")
                        confirmation = self._read_json(self._question_dir(qid) / "evidence_confirmation.json")
                        analyses, checks = self.read_analysis_versions(qid), self.read_final_checks(qid)
                        if not decision or decision.get("schema_version") != "cams-decision/v2" or decision.get("decision") != "approved":
                            continue
                        if not confirmation or confirmation.get("status") != "confirmed" or not analyses or not checks or checks[-1].get("status") != "passed":
                            continue
                        exact = (decision.get("question_version") == question.get("version")
                                 and decision.get("evidence_confirmation_version") == confirmation.get("version")
                                 and decision.get("analysis_version") == analyses[-1].get("version")
                                 and decision.get("final_check_version") == checks[-1].get("version"))
                        if not exact: continue
                        catalog = self._read_json(self._question_dir(qid) / "evidence_catalog.json", {"items": []})
                        chosen = {entry.get("evidence_id") for entry in (self.read_evidence_candidates(qid)[-1].get("entries") or [])}
                        questions.append({"question": question, "analysis": analyses[-1]["analysis"]})
                        evidence.append({"question_id": qid, "confirmation": confirmation,
                                         "items": [item for item in catalog.get("items", []) if item.get("evidence_id") in chosen]})
                        approved.append({"question_id": qid, "question_version": question["version"],
                                         "evidence_confirmation_version": confirmation["version"],
                                         "analysis_version": analyses[-1]["version"],
                                         "final_check_version": checks[-1]["version"],
                                         "decision_version": decision["version"]})
                        continue
                    review, decision = self.read_record(qid, "codex_review"), self.read_record(qid, "decision")
                    if question["status"] != "approved" or not review or not decision:
                        continue
                    if review["question_version"] != question["version"] or decision["question_version"] != question["version"]:
                        continue
                    evidence_review = self.read_record(qid, "evidence_review")
                    if evidence_review and (review.get("evidence_review_version") != evidence_review.get("version") or decision.get("evidence_review_version") != evidence_review.get("version")):
                        continue
                    if review["review"].get("status") != "reviewable" or decision["decision"].get("status") != "approved":
                        continue
                    questions.append(question)
                    evidence.append(review["review"])
                    approved.append({"question_id": qid, "question_version": question["version"], "codex_review_version": review["version"], "decision_version": decision["version"]})
                temporary = Path(tempfile.mkdtemp(prefix=f".{release_id}.", dir=self.releases))
                self._write_json(temporary / "questions.json", {"items": questions})
                self._write_json(temporary / "evidence.json", {"items": evidence})
                self._write_json(temporary / "approved_questions.json", {"items": approved})
                manifest = {"release_id": release_id, "created_at": now(), "actor": actor, "counts": {"approved_questions": len(approved)},
                            "files": {name: sha256(self._read_json(temporary / name)) for name in ("questions.json", "evidence.json", "approved_questions.json")}}
                self._write_json(temporary / "manifest.json", manifest)
                os.replace(temporary, target)
                for item in approved:
                    qid = item["question_id"]
                    if (self._question_dir(qid) / "workflow.json").exists():
                        before = self.read_workflow(qid)
                        after = self._write_workflow_locked(qid, "released", release_id=release_id)
                        question = self.read_question(qid); self._touch_question(question)
                        self._audit(qid, actor, "release", "build_release", f"构建发布包 {release_id}", before, after)
                return manifest
            finally:
                for lock in reversed(locked):
                    lock.__exit__(None, None, None)

    def list_releases(self) -> list[dict[str, Any]]:
        return [self._read_json(path / "manifest.json") for path in sorted(self.releases.glob("v7-*")) if (path / "manifest.json").exists()]


ROOT = Path(__file__).resolve().parents[1]
STORE = WorkspaceStore(ROOT)
