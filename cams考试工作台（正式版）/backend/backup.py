"""Create recoverable backups of mutable CAMS workbench data."""
from __future__ import annotations

import argparse
import json
import os
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _default_backup_root() -> Path:
    configured = os.environ.get("CAMS_BACKUP_ROOT")
    return Path(configured).expanduser() if configured else Path.home() / "CAMS考试工作台备份"


def _prune(backup_root: Path, keep: int) -> None:
    archives = sorted(backup_root.glob("cams-backup-*.tar.gz"), key=lambda path: path.stat().st_mtime)
    for archive in archives[:-max(1, keep)]:
        archive.unlink(missing_ok=True)


def create_backup(workspace_root: str | Path, backup_root: str | Path | None = None,
                  *, reason: str = "manual", daily: bool = False, keep: int = 30) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    destination = Path(backup_root).expanduser().resolve() if backup_root else _default_backup_root().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    moment = datetime.now(timezone.utc)
    daily_prefix = f"cams-backup-{moment:%Y%m%d}-"
    if daily:
        existing = sorted(destination.glob(f"{daily_prefix}*.tar.gz"))
        if existing:
            return {"created": False, "path": str(existing[-1]), "reason": "daily_backup_exists"}

    safe_reason = "".join(char if char.isalnum() or char in "-_" else "-" for char in reason).strip("-") or "manual"
    target = destination / f"cams-backup-{moment:%Y%m%d-%H%M%S}-{safe_reason}.tar.gz"
    sources = [root / "data" / "questions", root / "data" / "control", root / "releases"]
    with tarfile.open(target, "w:gz") as archive:
        for source in sources:
            if source.exists():
                archive.add(source, arcname=source.relative_to(root))
        metadata = json.dumps({
            "created_at": moment.isoformat(),
            "reason": reason,
            "workspace": str(root),
        }, ensure_ascii=False, indent=2).encode("utf-8")
        info = tarfile.TarInfo("backup-manifest.json")
        info.size = len(metadata)
        info.mtime = int(moment.timestamp())
        import io
        archive.addfile(info, io.BytesIO(metadata))
    _prune(destination, keep)
    return {"created": True, "path": str(target), "reason": reason}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--backup-root", type=Path, default=None)
    parser.add_argument("--reason", default="manual")
    parser.add_argument("--daily", action="store_true")
    parser.add_argument("--keep", type=int, default=30)
    args = parser.parse_args()
    result = create_backup(args.workspace_root, args.backup_root, reason=args.reason, daily=args.daily, keep=args.keep)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
