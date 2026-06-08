from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings
from app.core.errors import AppError


def _password_bytes(password: str) -> bytes:
    raw = password.encode("utf-8")
    if len(raw) > 72:
        raise AppError(40002, "密码长度不能超过 72 字节")
    return raw


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, extra_claims: Dict[str, Any]) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.access_token_expire_seconds)).timestamp()),
    }
    payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError:
        raise AppError(40101, "未登录或 token 无效")
