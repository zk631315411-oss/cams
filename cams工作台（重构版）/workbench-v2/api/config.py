from __future__ import annotations

import os
from pathlib import Path


WORKBENCH_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = WORKBENCH_ROOT.parent


class Settings:
    database_url = os.getenv(
        "DATABASE_URL", f"sqlite:///{(WORKBENCH_ROOT / 'workbench.db').as_posix()}"
    )
    content_root = Path(os.getenv("CONTENT_ROOT", str(PROJECT_ROOT / "content"))).resolve()
    source_markdown_root = Path(
        os.getenv(
            "SOURCE_MARKDOWN_ROOT",
            str(
                PROJECT_ROOT
                / "v7/选项证据与解析生成/phase4_evidence/output/explanations"
            ),
        )
    ).resolve()
    source_docx_root = Path(
        os.getenv(
            "SOURCE_DOCX_ROOT",
            str(
                PROJECT_ROOT
                / "v7/选项证据与解析生成/phase4_evidence/output/software_export/sections/docx"
            ),
        )
    ).resolve()
    kg_path = Path(
        os.getenv(
            "KG_PATH",
            str(
                PROJECT_ROOT
                / "v7/知识图谱提取/phases/phase06_kg_views/outputs/kg_retrieval_graph.json"
            ),
        )
    ).resolve()
    textbook_release_root = Path(
        os.getenv("TEXTBOOK_RELEASE_ROOT", str(PROJECT_ROOT / "frontend/data/releases/v7"))
    ).resolve()
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin-local-only")
    jwt_secret = os.getenv("JWT_SECRET", "cams-local-development-secret-change-me")
    cors_origins = [
        item.strip()
        for item in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5174").split(",")
        if item.strip()
    ]


settings = Settings()
