from __future__ import annotations

import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .auth import (
    VALID_ROLES,
    current_user,
    ensure_admin,
    ensure_codex_user,
    hash_password,
    issue_token,
    require_roles,
    verify_password,
)
from .config import settings
from .content import (
    apply_content_patch,
    create_version,
    unified_diff,
    version_markdown,
)
from .db import (
    AuditEvent,
    EditTask,
    PositionSnapshot,
    Question,
    Release,
    ReleaseItem,
    Review,
    User,
    Version,
    get_db,
    init_db,
    SessionLocal,
    utcnow,
)
from .evidence import get_unit, render_source_page, search_kg
from .mcp_server import mcp
from .releases import create_release, export_release_docx


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        ensure_admin(db)
        ensure_codex_user(db)
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="CAMS 教研工作台", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginPayload(BaseModel):
    username: str
    password: str


class UserPayload(BaseModel):
    username: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8)
    role: str


class BeginTaskPayload(BaseModel):
    purpose: str = Field(min_length=2)
    base_version_id: str | None = None


class SavePayload(BaseModel):
    task_id: str
    content_patch: dict[str, Any] = Field(default_factory=dict)
    bindings_patch: dict[str, Any] = Field(default_factory=dict)
    note: str = ""


class FinishPayload(BaseModel):
    summary: str = ""


class ReviewSubmitPayload(BaseModel):
    version_id: str | None = None
    comment: str = ""


class ReviewDecisionPayload(BaseModel):
    decision: Literal["approved", "returned"]
    comment: str = ""


class ReleasePayload(BaseModel):
    title: str = Field(min_length=2)
    question_ids: list[str] = Field(min_length=1)


class ReleaseStatePayload(BaseModel):
    state: Literal["pending_entry", "entered", "verified", "published", "needs_rework"]
    note: str = ""


class RollbackPayload(BaseModel):
    task_id: str
    target_version_id: str
    note: str = "回滚到历史版本"


def _version_out(version: Version, include_markdown: bool = False) -> dict[str, Any]:
    result = {
        "id": version.id,
        "question_id": version.question_id,
        "sequence": version.sequence,
        "parent_id": version.parent_id,
        "task_id": version.task_id,
        "content_hash": version.content_hash,
        "content": version.parsed_content,
        "option_ids": version.option_ids,
        "answer_option_ids": version.answer_option_ids,
        "bindings": version.bindings,
        "structured_changes": version.structured_changes,
        "note": version.note,
        "created_by": version.created_by,
        "created_at": version.created_at,
        "is_import": version.is_import,
    }
    if include_markdown:
        result["markdown"] = version_markdown(version)
    return result


def _question_out(db: Session, question: Question, detail: bool = False) -> dict[str, Any]:
    version = db.get(Version, question.current_version_id)
    latest_snapshot = db.scalar(
        select(PositionSnapshot)
        .where(PositionSnapshot.question_id == question.id)
        .order_by(PositionSnapshot.id.desc())
    )
    result = {
        "question_id": question.id,
        "status": question.status,
        "needs_attention": question.needs_attention,
        "question_type": question.question_type,
        "current_version_id": question.current_version_id,
        "published_version_id": question.published_version_id,
        "primary_cp_id": question.primary_cp_id,
        "supporting_cp_ids": question.supporting_cp_ids,
        "evidence_unit_ids": question.evidence_unit_ids,
        "stem_zh": version.parsed_content.get("stem_zh", "") if version else "",
        "stem_en": version.parsed_content.get("stem_en", "") if version else "",
        "position": (
            {
                "snapshot_key": latest_snapshot.snapshot_key,
                "section_code": latest_snapshot.section_code,
                "ordinal": latest_snapshot.ordinal,
                "paper_title": latest_snapshot.paper_title,
            }
            if latest_snapshot
            else None
        ),
        "updated_at": question.updated_at,
    }
    if detail and version:
        result["current_version"] = _version_out(version, include_markdown=True)
        result["versions"] = [
            _version_out(item)
            for item in db.scalars(
                select(Version).where(Version.question_id == question.id).order_by(Version.sequence.desc())
            )
        ]
        result["active_task"] = _active_task_out(db, question.id)
    return result


def _active_task_out(db: Session, question_id: str) -> dict[str, Any] | None:
    task = db.scalar(
        select(EditTask).where(EditTask.question_id == question_id, EditTask.state == "active")
    )
    return _task_out(task) if task else None


def _task_out(task: EditTask) -> dict[str, Any]:
    return {
        "id": task.id,
        "question_id": task.question_id,
        "owner_id": task.owner_id,
        "purpose": task.purpose,
        "base_version_id": task.base_version_id,
        "latest_version_id": task.latest_version_id,
        "state": task.state,
        "summary": task.summary,
        "started_at": task.started_at,
        "finished_at": task.finished_at,
    }


def _audit(db: Session, user: User | None, action: str, object_type: str, object_id: str, details: dict | None = None) -> None:
    db.add(
        AuditEvent(
            actor_id=user.id if user else None,
            action=action,
            object_type=object_type,
            object_id=object_id,
            details=details or {},
        )
    )


@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> dict[str, Any]:
    return {
        "status": "ok",
        "questions": db.scalar(select(func.count()).select_from(Question)),
        "database": settings.database_url.split(":", 1)[0],
    }


@app.post("/api/auth/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = db.scalar(select(User).where(User.username == payload.username))
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    return {"access_token": issue_token(user), "token_type": "bearer", "user": {"id": user.id, "username": user.username, "role": user.role}}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)) -> dict[str, Any]:
    return {"id": user.id, "username": user.username, "role": user.role}


@app.get("/api/users")
def list_users(
    _: User = Depends(require_roles("admin")), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    return [
        {"id": item.id, "username": item.username, "role": item.role, "active": item.active}
        for item in db.scalars(select(User).order_by(User.username))
    ]


@app.post("/api/users")
def create_user(
    payload: UserPayload,
    actor: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if payload.role not in VALID_ROLES:
        raise HTTPException(422, "无效角色")
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(409, "用户名已存在")
    user = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.flush()
    _audit(db, actor, "user.create", "user", str(user.id), {"role": user.role})
    db.commit()
    return {"id": user.id, "username": user.username, "role": user.role}


@app.get("/api/dashboard")
def dashboard(_: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    statuses = dict(db.execute(select(Question.status, func.count()).group_by(Question.status)).all())
    return {
        "total": db.scalar(select(func.count()).select_from(Question)),
        "needs_attention": db.scalar(select(func.count()).select_from(Question).where(Question.needs_attention.is_(True))),
        "statuses": statuses,
        "open_locks": db.scalar(select(func.count()).select_from(EditTask).where(EditTask.state == "active")),
        "pending_reviews": db.scalar(select(func.count()).select_from(Review).where(Review.state.in_(["submitted", "in_review"]))),
    }


@app.get("/api/questions")
def list_questions(
    q: str = "",
    status: str | None = None,
    needs_attention: bool | None = None,
    section_code: str | None = None,
    ordinal: int | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    statement = select(Question)
    if status:
        statement = statement.where(Question.status == status)
    if needs_attention is not None:
        statement = statement.where(Question.needs_attention == needs_attention)
    if section_code or ordinal is not None:
        position_query = select(PositionSnapshot.question_id).where(PositionSnapshot.question_id.is_not(None))
        if section_code:
            position_query = position_query.where(PositionSnapshot.section_code == section_code)
        if ordinal is not None:
            position_query = position_query.where(PositionSnapshot.ordinal == ordinal)
        statement = statement.where(Question.id.in_(position_query))
    questions = list(db.scalars(statement.order_by(Question.id)))
    if q:
        query_cf = q.casefold()
        filtered = []
        for item in questions:
            version = db.get(Version, item.current_version_id)
            haystack = " ".join(
                [item.id, version.parsed_content.get("stem_zh", ""), version.parsed_content.get("stem_en", "")]
            ).casefold()
            if query_cf in haystack:
                filtered.append(item)
        questions = filtered
    total = len(questions)
    return {"total": total, "items": [_question_out(db, item) for item in questions[offset : offset + limit]]}


@app.get("/api/questions/{question_id}")
def get_question_api(
    question_id: str,
    version_id: str | None = None,
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    question = db.get(Question, question_id)
    if not question:
        raise HTTPException(404, "题目不存在")
    if version_id:
        version = db.get(Version, version_id)
        if not version or version.question_id != question_id:
            raise HTTPException(404, "版本不存在")
        result = _question_out(db, question)
        result["current_version"] = _version_out(version, include_markdown=True)
        return result
    return _question_out(db, question, detail=True)


@app.post("/api/questions/{question_id}/tasks")
def begin_edit_task(
    question_id: str,
    payload: BeginTaskPayload,
    user: User = Depends(require_roles("editor")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    question = db.get(Question, question_id)
    if not question:
        raise HTTPException(404, "题目不存在")
    active = db.scalar(select(EditTask).where(EditTask.question_id == question_id, EditTask.state == "active"))
    if active:
        raise HTTPException(409, f"题目已由用户 {active.owner_id} 锁定")
    base_id = payload.base_version_id or question.published_version_id or question.current_version_id
    version = db.get(Version, base_id)
    if not version or version.question_id != question_id:
        raise HTTPException(422, "基线版本无效")
    task = EditTask(
        id=f"task_{uuid.uuid4().hex}",
        question_id=question_id,
        owner_id=user.id,
        purpose=payload.purpose,
        base_version_id=base_id,
        latest_version_id=question.current_version_id,
    )
    db.add(task)
    question.status = "editing"
    _audit(db, user, "task.begin", "edit_task", task.id, {"question_id": question_id})
    db.commit()
    return _task_out(task)


@app.post("/api/questions/{question_id}/save")
def save_question_api(
    question_id: str,
    payload: SavePayload,
    user: User = Depends(require_roles("editor")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    question = db.get(Question, question_id)
    task = db.get(EditTask, payload.task_id)
    if not question or not task or task.question_id != question_id:
        raise HTTPException(404, "题目或编辑任务不存在")
    if task.state != "active" or task.owner_id != user.id:
        raise HTTPException(409, "必须持有当前题目的有效任务锁")
    current = db.get(Version, question.current_version_id)
    markdown = apply_content_patch(version_markdown(current), payload.content_patch)
    bindings = dict(current.bindings or {})
    bindings.update(payload.bindings_patch)
    version = create_version(
        db,
        question,
        markdown,
        task_id=task.id,
        actor_id=user.id,
        note=payload.note,
        bindings=bindings,
    )
    task.latest_version_id = version.id
    _audit(db, user, "question.save", "version", version.id, {"task_id": task.id})
    db.commit()
    return _version_out(version, include_markdown=True)


@app.post("/api/tasks/{task_id}/finish")
def finish_edit_task(
    task_id: str,
    payload: FinishPayload,
    user: User = Depends(require_roles("editor")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    task = db.get(EditTask, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    if task.owner_id != user.id or task.state != "active":
        raise HTTPException(409, "任务锁无效")
    task.state = "finished"
    task.summary = payload.summary
    task.finished_at = utcnow()
    _audit(db, user, "task.finish", "edit_task", task.id)
    db.commit()
    return _task_out(task)


@app.get("/api/tasks/{task_id}/diff")
def get_task_diff(
    task_id: str,
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    task = db.get(EditTask, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    before = db.get(Version, task.base_version_id)
    after = db.get(Version, task.latest_version_id)
    saves = list(db.scalars(select(Version).where(Version.task_id == task.id).order_by(Version.sequence)))
    return {
        "task": _task_out(task),
        "structured_changes": after.structured_changes if after else {},
        "diff": unified_diff(version_markdown(before), version_markdown(after), before.id, after.id),
        "saves": [_version_out(item) for item in saves],
    }


@app.get("/api/questions/{question_id}/diff")
def compare_versions(
    question_id: str,
    from_version_id: str | None = None,
    to_version_id: str | None = None,
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    question = db.get(Question, question_id)
    if not question:
        raise HTTPException(404, "题目不存在")
    default_base = question.published_version_id
    if not default_base:
        default_base = db.scalar(
            select(Version.id).where(Version.question_id == question_id, Version.is_import.is_(True)).order_by(Version.sequence)
        )
    before = db.get(Version, from_version_id or default_base)
    after = db.get(Version, to_version_id or question.current_version_id)
    if not before or not after or before.question_id != question_id or after.question_id != question_id:
        raise HTTPException(422, "比较版本无效")
    return {
        "from": _version_out(before),
        "to": _version_out(after),
        "diff": unified_diff(version_markdown(before), version_markdown(after), before.id, after.id),
    }


@app.post("/api/questions/{question_id}/rollback")
def rollback_question(
    question_id: str,
    payload: RollbackPayload,
    user: User = Depends(require_roles("editor")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    question = db.get(Question, question_id)
    task = db.get(EditTask, payload.task_id)
    target = db.get(Version, payload.target_version_id)
    if not question or not task or not target or target.question_id != question_id:
        raise HTTPException(404, "题目、任务或目标版本不存在")
    if task.owner_id != user.id or task.state != "active":
        raise HTTPException(409, "必须持有当前题目的有效任务锁")
    version = create_version(
        db,
        question,
        version_markdown(target),
        task_id=task.id,
        actor_id=user.id,
        note=payload.note,
        bindings=target.bindings,
    )
    task.latest_version_id = version.id
    _audit(db, user, "question.rollback", "version", version.id, {"target_version_id": target.id})
    db.commit()
    return _version_out(version, include_markdown=True)


@app.post("/api/questions/{question_id}/submit-review")
def submit_review(
    question_id: str,
    payload: ReviewSubmitPayload,
    user: User = Depends(require_roles("editor")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    question = db.get(Question, question_id)
    if not question:
        raise HTTPException(404, "题目不存在")
    if _active_task_out(db, question_id):
        raise HTTPException(409, "请先结束编辑任务")
    version_id = payload.version_id or question.current_version_id
    version = db.get(Version, version_id)
    if not version or version.question_id != question_id or version_id != question.current_version_id:
        raise HTTPException(422, "只能提交当前版本")
    review = Review(
        id=f"rev_{uuid.uuid4().hex}",
        question_id=question_id,
        version_id=version_id,
        submitted_by=user.id,
        comment=payload.comment,
    )
    db.add(review)
    question.status = "pending_review"
    _audit(db, user, "review.submit", "review", review.id)
    db.commit()
    return _review_out(review)


def _review_out(review: Review) -> dict[str, Any]:
    return {
        "id": review.id,
        "question_id": review.question_id,
        "version_id": review.version_id,
        "submitted_by": review.submitted_by,
        "reviewer_id": review.reviewer_id,
        "state": review.state,
        "comment": review.comment,
        "submitted_at": review.submitted_at,
        "decided_at": review.decided_at,
    }


@app.get("/api/reviews")
def list_reviews(
    state: str | None = None,
    _: User = Depends(require_roles("reviewer")),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    statement = select(Review)
    if state:
        statement = statement.where(Review.state == state)
    return [_review_out(item) for item in db.scalars(statement.order_by(Review.submitted_at.desc()))]


@app.post("/api/reviews/{review_id}/claim")
def claim_review(
    review_id: str,
    user: User = Depends(require_roles("reviewer")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    review = db.get(Review, review_id)
    if not review or review.state != "submitted":
        raise HTTPException(409, "审核任务当前不可领取")
    if review.submitted_by == user.id:
        raise HTTPException(403, "编辑者不能审核自己的修订")
    review.reviewer_id = user.id
    review.state = "in_review"
    db.get(Question, review.question_id).status = "in_review"
    _audit(db, user, "review.claim", "review", review.id)
    db.commit()
    return _review_out(review)


@app.post("/api/reviews/{review_id}/decide")
def decide_review(
    review_id: str,
    payload: ReviewDecisionPayload,
    user: User = Depends(require_roles("reviewer")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    review = db.get(Review, review_id)
    if not review or review.state != "in_review" or review.reviewer_id != user.id:
        raise HTTPException(409, "请先领取该审核任务")
    if review.submitted_by == user.id:
        raise HTTPException(403, "编辑者不能批准自己的修订")
    review.state = payload.decision
    review.comment = payload.comment
    review.decided_at = utcnow()
    question = db.get(Question, review.question_id)
    question.status = payload.decision
    _audit(db, user, f"review.{payload.decision}", "review", review.id)
    db.commit()
    return _review_out(review)


@app.get("/api/evidence/search")
def search_evidence(
    q: str = "",
    chapter_id: str | None = None,
    section_id: str | None = None,
    core_point_id: str | None = None,
    _: User = Depends(current_user),
) -> dict[str, Any]:
    return search_kg(q, chapter_id, section_id, core_point_id)


@app.get("/api/evidence/units/{unit_id}")
def unit_detail(unit_id: str, _: User = Depends(current_user)) -> dict[str, Any]:
    unit = get_unit(unit_id)
    if not unit:
        raise HTTPException(404, "教材单元不存在")
    return unit


@app.get("/api/evidence/pages/{page}.png")
def source_page(
    page: int,
    language: str = "zh",
    _: User = Depends(current_user),
) -> Response:
    try:
        content = render_source_page(page, language)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return Response(content=content, media_type="image/png")


@app.post("/api/releases")
def create_release_api(
    payload: ReleasePayload,
    user: User = Depends(require_roles("publisher")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        release = create_release(db, user.id, payload.title, payload.question_ids)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    _audit(db, user, "release.create", "release", release.id)
    db.commit()
    return _release_out(db, release)


def _release_out(db: Session, release: Release) -> dict[str, Any]:
    items = list(db.scalars(select(ReleaseItem).where(ReleaseItem.release_id == release.id).order_by(ReleaseItem.id)))
    return {
        "id": release.id,
        "title": release.title,
        "state": release.state,
        "manifest_path": release.manifest_path,
        "export_path": release.export_path,
        "export_hash": release.export_hash,
        "created_by": release.created_by,
        "created_at": release.created_at,
        "items": [
            {
                "id": item.id,
                "question_id": item.question_id,
                "version_id": item.version_id,
                "content_hash": item.content_hash,
                "publish_state": item.publish_state,
                "note": item.note,
            }
            for item in items
        ],
    }


@app.get("/api/releases")
def list_releases(
    _: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    return [_release_out(db, item) for item in db.scalars(select(Release).order_by(Release.created_at.desc()))]


@app.post("/api/releases/{release_id}/export")
def export_release_api(
    release_id: str,
    user: User = Depends(require_roles("publisher")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    release = db.get(Release, release_id)
    if not release:
        raise HTTPException(404, "发布批次不存在")
    path = export_release_docx(db, release)
    _audit(db, user, "release.export", "release", release.id, {"hash": release.export_hash})
    db.commit()
    return {"release_id": release.id, "path": str(path), "hash": release.export_hash}


@app.get("/api/releases/{release_id}/download")
def download_release(
    release_id: str,
    _: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    release = db.get(Release, release_id)
    if not release or not release.export_path or not Path(release.export_path).exists():
        raise HTTPException(404, "交付 DOCX 尚未生成")
    return FileResponse(release.export_path, filename=Path(release.export_path).name)


@app.patch("/api/releases/{release_id}/items/{item_id}")
def update_release_item(
    release_id: str,
    item_id: int,
    payload: ReleaseStatePayload,
    user: User = Depends(require_roles("publisher")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    item = db.get(ReleaseItem, item_id)
    if not item or item.release_id != release_id:
        raise HTTPException(404, "发布项不存在")
    transitions = {
        "pending_entry": {"entered", "needs_rework"},
        "entered": {"verified", "needs_rework"},
        "verified": {"published", "needs_rework"},
        "needs_rework": {"pending_entry"},
        "published": set(),
    }
    if payload.state != item.publish_state and payload.state not in transitions[item.publish_state]:
        raise HTTPException(409, f"不允许从 {item.publish_state} 跳到 {payload.state}")
    item.publish_state = payload.state
    item.note = payload.note
    question = db.get(Question, item.question_id)
    if payload.state == "published":
        question.published_version_id = item.version_id
        if question.current_version_id == item.version_id:
            question.status = "published"
    elif payload.state == "needs_rework":
        question.status = "returned"
    _audit(db, user, "release.item_state", "release_item", str(item.id), {"state": payload.state})
    db.commit()
    return {"id": item.id, "publish_state": item.publish_state, "note": item.note}


# REST aliases mirror the nine MCP tools and are useful for diagnostics.
@app.get("/api/mcp/find_question")
def mcp_find_question(
    query: str = "",
    section_code: str | None = None,
    ordinal: int | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return list_questions(query, None, None, section_code, ordinal, 0, 50, user, db)


@app.get("/api/mcp/get_question/{question_id}")
def mcp_get_question(question_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    return get_question_api(question_id, None, user, db)


@app.get("/api/mcp/search_kg")
def mcp_search_kg(q: str = "", user: User = Depends(current_user)) -> dict[str, Any]:
    return search_evidence(q, None, None, None, user)


@app.get("/api/mcp/get_unit/{unit_id}")
def mcp_get_unit(unit_id: str, user: User = Depends(current_user)) -> dict[str, Any]:
    return unit_detail(unit_id, user)


@app.get("/api/mcp/open_source_page/{unit_id}")
def mcp_open_source_page(unit_id: str, user: User = Depends(current_user)) -> dict[str, Any]:
    unit = unit_detail(unit_id, user)
    return {
        "unit_id": unit_id,
        "pdf_page": unit.get("pdf_page"),
        "printed_page": unit.get("printed_page"),
        "zh_url": f"/api/evidence/pages/{unit.get('pdf_page')}.png?language=zh",
        "en_url": f"/api/evidence/pages/{unit.get('pdf_page')}.png?language=en",
    }


# Keep this catch-all mount after the REST routes: the contained FastMCP app
# serves its Streamable HTTP endpoint at `/mcp`.
app.mount("/", mcp.streamable_http_app())
