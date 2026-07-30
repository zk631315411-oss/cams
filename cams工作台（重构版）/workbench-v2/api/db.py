from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generator

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from .config import settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    source_path: Mapped[str] = mapped_column(Text)
    source_hash: Mapped[str] = mapped_column(String(64))
    current_path: Mapped[str] = mapped_column(Text)
    question_type: Mapped[str] = mapped_column(String(20), default="unknown")
    status: Mapped[str] = mapped_column(String(30), default="editing", index=True)
    needs_attention: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    current_version_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    published_version_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    primary_cp_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    supporting_cp_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_unit_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    versions: Mapped[list["Version"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", foreign_keys="Version.question_id"
    )


class Version(Base):
    __tablename__ = "versions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    parent_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    snapshot_path: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    parsed_content: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    option_ids: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    answer_option_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    bindings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    structured_changes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    note: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    is_import: Mapped[bool] = mapped_column(Boolean, default=False)

    question: Mapped[Question] = relationship(back_populates="versions", foreign_keys=[question_id])


class EditTask(Base):
    __tablename__ = "edit_tasks"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(Text)
    base_version_id: Mapped[str] = mapped_column(String(40))
    latest_version_id: Mapped[str] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(20), default="active", index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("versions.id"), index=True)
    submitted_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    state: Mapped[str] = mapped_column(String(20), default="submitted", index=True)
    comment: Mapped[str] = mapped_column(Text, default="")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PositionSnapshot(Base):
    __tablename__ = "position_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_key: Mapped[str] = mapped_column(String(50), index=True)
    bank_version: Mapped[str] = mapped_column(String(30), default="v7")
    source_docx: Mapped[str] = mapped_column(Text)
    source_hash: Mapped[str] = mapped_column(String(64))
    paper_title: Mapped[str] = mapped_column(String(200), default="")
    section_code: Mapped[str] = mapped_column(String(100), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    stem: Mapped[str] = mapped_column(Text)
    normalized_stem: Mapped[str] = mapped_column(Text, index=True)
    question_id: Mapped[str | None] = mapped_column(ForeignKey("questions.id"), nullable=True, index=True)
    confidence: Mapped[str] = mapped_column(String(20), default="unmatched")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Release(Base):
    __tablename__ = "releases"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    state: Mapped[str] = mapped_column(String(20), default="created")
    manifest_path: Mapped[str] = mapped_column(Text, default="")
    export_path: Mapped[str] = mapped_column(Text, default="")
    export_hash: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ReleaseItem(Base):
    __tablename__ = "release_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    release_id: Mapped[str] = mapped_column(ForeignKey("releases.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    version_id: Mapped[str] = mapped_column(ForeignKey("versions.id"))
    content_hash: Mapped[str] = mapped_column(String(64))
    publish_state: Mapped[str] = mapped_column(String(20), default="pending_entry", index=True)
    note: Mapped[str] = mapped_column(Text, default="")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    object_type: Mapped[str] = mapped_column(String(40))
    object_id: Mapped[str] = mapped_column(String(80), index=True)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SchemaMigration(Base):
    __tablename__ = "schema_migrations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        if not session.get(SchemaMigration, "001_initial"):
            session.add(SchemaMigration(id="001_initial"))
            session.commit()


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
