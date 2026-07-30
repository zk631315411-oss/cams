from __future__ import annotations

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Callable

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import User, get_db


bearer = HTTPBearer(auto_error=False)
VALID_ROLES = {"editor", "reviewer", "publisher", "admin"}


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210_000)
    return f"pbkdf2_sha256$210000${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(rounds)
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def issue_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user.id), "role": user.role, "iat": now, "exp": now + timedelta(hours=12)},
        settings.jwt_secret,
        algorithm="HS256",
    )


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(401, "请先登录")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        user = db.get(User, int(payload["sub"]))
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise HTTPException(401, "登录已过期") from None
    if not user or not user.active:
        raise HTTPException(401, "账号不可用")
    return user


def require_roles(*roles: str) -> Callable:
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role != "admin" and user.role not in roles:
            raise HTTPException(403, "当前角色无权执行此操作")
        return user

    return dependency


def ensure_admin(db: Session) -> User:
    admin = db.scalar(select(User).where(User.username == settings.admin_username))
    if not admin:
        admin = User(
            username=settings.admin_username,
            password_hash=hash_password(settings.admin_password),
            role="admin",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    return admin


def ensure_codex_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.username == "codex"))
    if not user:
        user = User(username="codex", password_hash=hash_password(os.urandom(24).hex()), role="editor")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
