from __future__ import annotations

import argparse
import json
import sys

from .auth import ensure_admin, ensure_codex_user, hash_password
from .content import import_content, verify_import
from .db import Release, SessionLocal, User, init_db
from .positions import import_positions
from .releases import export_release_docx


def main() -> int:
    parser = argparse.ArgumentParser(description="CAMS 教研工作台维护命令")
    subparsers = parser.add_subparsers(dest="command", required=True)
    import_parser = subparsers.add_parser("import-content", help="复制导入395份Markdown")
    import_parser.add_argument("--force", action="store_true")
    subparsers.add_parser("import-positions", help="严格匹配DOCX位置快照")
    subparsers.add_parser("verify", help="验证导入及源文件哈希")
    user_parser = subparsers.add_parser("create-user")
    user_parser.add_argument("username")
    user_parser.add_argument("password")
    user_parser.add_argument("role", choices=["editor", "reviewer", "publisher", "admin"])
    export_parser = subparsers.add_parser("export-release")
    export_parser.add_argument("release_id")
    args = parser.parse_args()

    init_db()
    with SessionLocal() as db:
        ensure_admin(db)
        ensure_codex_user(db)
        if args.command == "import-content":
            result = import_content(db, force=args.force)
        elif args.command == "import-positions":
            result = import_positions(db)
        elif args.command == "verify":
            result = verify_import(db)
        elif args.command == "create-user":
            user = User(username=args.username, password_hash=hash_password(args.password), role=args.role)
            db.add(user)
            db.commit()
            result = {"id": user.id, "username": user.username, "role": user.role}
        elif args.command == "export-release":
            release = db.get(Release, args.release_id)
            if not release:
                parser.error("release not found")
            path = export_release_docx(db, release)
            result = {"path": str(path), "hash": release.export_hash}
        else:
            parser.error("unknown command")
            return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
