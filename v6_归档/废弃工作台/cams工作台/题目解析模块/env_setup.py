"""工作区环境加载：把 .env 里的 DEEPSEEK_API_KEY 注入 os.environ。

本模块在 pipeline 包初始化时自动加载，确保后续 run_step1.get_deepseek_config()
能读到 key。.env 文件与本模块同级。
"""
from __future__ import annotations

import os
from pathlib import Path

_ENV_FILE = Path(__file__).resolve().parent / ".env"


def _load_env() -> None:
    if not _ENV_FILE.exists():
        return
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


_load_env()
