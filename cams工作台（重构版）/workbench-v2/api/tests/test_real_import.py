from __future__ import annotations

from api.config import settings
from api.content import import_content, verify_import
from api.db import Base, SessionLocal, engine, init_db


def test_real_source_inventory_is_395():
    assert len(list(settings.source_markdown_root.glob("v7_q_*.md"))) == 395


def test_import_report_when_database_is_ready():
    init_db()
    with SessionLocal() as db:
        result = verify_import(db)
        if result["question_count"] != 395:
            import_content(db)
            result = verify_import(db)
        assert result["question_count"] == 395
        assert result["unique_count"] == 395
        assert result["source_hashes_unchanged"] is True
