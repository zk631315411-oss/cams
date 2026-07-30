from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_units(root: Path) -> tuple[str, list[dict[str, Any]]]:
    textbook = root / "data" / "infrastructure" / "textbook"
    manifest_path, units_path = textbook / "manifest.json", textbook / "units.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {"version": "uninitialized"}
    payload = json.loads(units_path.read_text(encoding="utf-8")) if units_path.exists() else {"units": []}
    return str(manifest.get("version", "uninitialized")), payload.get("units") or payload.get("items") or []
