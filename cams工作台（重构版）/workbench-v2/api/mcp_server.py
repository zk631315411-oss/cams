"""Codex-facing MCP server.

Run independently with `python -m api.mcp_server`, or point Codex at the
streamable HTTP endpoint on port 8011. The MCP identity is the local `codex`
editor account; all writes still require the task lock returned by
`begin_edit_task`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from .auth import ensure_codex_user
from .content import apply_content_patch, create_version, unified_diff, version_markdown
from .db import EditTask, PositionSnapshot, Question, SessionLocal, Version, init_db, utcnow
from .evidence import get_unit as lookup_unit
from .evidence import search_kg as lookup_kg


mcp = FastMCP("cams-workbench", host="127.0.0.1", port=8011)


def _question_payload(db: SessionLocal, question: Question, version: Version) -> dict[str, Any]:
    return {
        "question_id": question.id,
        "status": question.status,
        "version_id": version.id,
        "markdown": version_markdown(version),
        "content": version.parsed_content,
        "option_ids": version.option_ids,
        "answer_option_ids": version.answer_option_ids,
        "bindings": version.bindings,
    }


@mcp.tool()
def find_question(
    query: str = "", bank_version: str = "v7", position: str = "", text_fragment: str = ""
) -> dict[str, Any]:
    """Locate permanent question IDs by ID, historical section/number, or stem fragment."""
    with SessionLocal() as db:
        questions = list(db.scalars(select(Question).order_by(Question.id)))
        needle = (text_fragment or query).casefold().strip()
        results = []
        for question in questions:
            version = db.get(Version, question.current_version_id)
            haystack = " ".join([question.id, version.parsed_content.get("stem_zh", ""), version.parsed_content.get("stem_en", "")]).casefold()
            if needle and needle not in haystack:
                continue
            if position:
                parts = position.replace(" ", "").split(":", 1)
                position_statement = select(PositionSnapshot).where(
                    PositionSnapshot.question_id == question.id,
                    PositionSnapshot.section_code == parts[0],
                )
                if len(parts) == 2 and parts[1].isdigit():
                    position_statement = position_statement.where(PositionSnapshot.ordinal == int(parts[1]))
                row = db.scalar(position_statement)
                if not row:
                    continue
            results.append({"question_id": question.id, "stem_zh": version.parsed_content.get("stem_zh"), "status": question.status})
            if len(results) >= 50:
                break
        return {"items": results}


@mcp.tool()
def get_question(question_id: str, version_id: str = "") -> dict[str, Any]:
    """Read formal Markdown, stable options, answer IDs, bindings, and state."""
    with SessionLocal() as db:
        question = db.get(Question, question_id)
        if not question:
            raise ValueError("question not found")
        version = db.get(Version, version_id or question.current_version_id)
        if not version or version.question_id != question_id:
            raise ValueError("version not found")
        return _question_payload(db, question, version)


@mcp.tool()
def begin_edit_task(question_id: str, purpose: str, base_version_id: str = "") -> dict[str, Any]:
    """Acquire the exclusive question lock and start a grouped Codex edit task."""
    with SessionLocal() as db:
        user = ensure_codex_user(db)
        question = db.get(Question, question_id)
        if not question:
            raise ValueError("question not found")
        active = db.scalar(select(EditTask).where(EditTask.question_id == question_id, EditTask.state == "active"))
        if active:
            raise ValueError(f"question locked by user {active.owner_id}, task {active.id}")
        base = base_version_id or question.published_version_id or question.current_version_id
        import uuid
        task = EditTask(
            id=f"task_{uuid.uuid4().hex}", question_id=question_id, owner_id=user.id,
            purpose=purpose, base_version_id=base, latest_version_id=question.current_version_id,
        )
        db.add(task)
        question.status = "editing"
        db.commit()
        return {"task_id": task.id, "question_id": task.question_id, "base_version_id": task.base_version_id}


@mcp.tool()
def search_kg(
    query: str = "", chapter_id: str = "", section_id: str = "", core_point_id: str = ""
) -> dict[str, Any]:
    """Search the read-only KG for CPs and source evidence units."""
    return lookup_kg(query, chapter_id or None, section_id or None, core_point_id or None)


@mcp.tool()
def get_unit(unit_id: str) -> dict[str, Any]:
    """Read one immutable source unit with quote and page metadata."""
    unit = lookup_unit(unit_id)
    if not unit:
        raise ValueError("unit not found")
    return unit


@mcp.tool()
def open_source_page(unit_id: str) -> dict[str, Any]:
    """Return the workbench URLs that render the unit's Chinese and English source page."""
    unit = lookup_unit(unit_id)
    if not unit:
        raise ValueError("unit not found")
    page = unit.get("pdf_page")
    return {
        "unit_id": unit_id,
        "pdf_page": page,
        "printed_page": unit.get("printed_page"),
        "zh_url": f"http://127.0.0.1:8010/api/evidence/pages/{page}.png?language=zh",
        "en_url": f"http://127.0.0.1:8010/api/evidence/pages/{page}.png?language=en",
    }


@mcp.tool()
def save_question(
    task_id: str,
    content_patch: dict[str, Any],
    bindings_patch: dict[str, Any] | None = None,
    note: str = "",
) -> dict[str, Any]:
    """Save an immutable Markdown version. Requires the active Codex task lock."""
    with SessionLocal() as db:
        user = ensure_codex_user(db)
        task = db.get(EditTask, task_id)
        if not task or task.state != "active" or task.owner_id != user.id:
            raise ValueError("valid active task lock required")
        question = db.get(Question, task.question_id)
        current = db.get(Version, question.current_version_id)
        markdown = apply_content_patch(version_markdown(current), content_patch)
        bindings = dict(current.bindings or {})
        bindings.update(bindings_patch or {})
        version = create_version(db, question, markdown, task_id=task.id, actor_id=user.id, note=note, bindings=bindings)
        task.latest_version_id = version.id
        db.commit()
        return {"question_id": question.id, "version_id": version.id, "content_hash": version.content_hash, "structured_changes": version.structured_changes}


@mcp.tool()
def get_task_diff(task_id: str, detail_level: str = "merged") -> dict[str, Any]:
    """Compare a task's base to latest save; optionally include each underlying save."""
    with SessionLocal() as db:
        task = db.get(EditTask, task_id)
        if not task:
            raise ValueError("task not found")
        before = db.get(Version, task.base_version_id)
        after = db.get(Version, task.latest_version_id)
        payload = {"task_id": task.id, "diff": unified_diff(version_markdown(before), version_markdown(after), before.id, after.id)}
        if detail_level == "saves":
            payload["saves"] = [
                {"version_id": item.id, "sequence": item.sequence, "changes": item.structured_changes, "note": item.note}
                for item in db.scalars(select(Version).where(Version.task_id == task.id).order_by(Version.sequence))
            ]
        return payload


@mcp.tool()
def finish_edit_task(task_id: str, summary: str = "") -> dict[str, Any]:
    """Release the lock. This deliberately does not submit the revision for review."""
    with SessionLocal() as db:
        user = ensure_codex_user(db)
        task = db.get(EditTask, task_id)
        if not task or task.state != "active" or task.owner_id != user.id:
            raise ValueError("valid active task lock required")
        task.state = "finished"
        task.summary = summary
        task.finished_at = utcnow()
        db.commit()
        return {"task_id": task.id, "state": task.state, "question_status": "editing"}


if __name__ == "__main__":
    init_db()
    mcp.run(transport="streamable-http")
