import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.config.settings import get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)


def create_access_token(user_id: UUID) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    return jwt.encode({"sub": str(user_id), "type": "access", "iat": now, "exp": now + timedelta(minutes=15)}, settings.app_secret_key.get_secret_value(), algorithm="HS256")


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_api_key() -> tuple[str, str]:
    prefix = secrets.token_hex(4)
    return prefix, f"aas_local_{prefix}_{secrets.token_urlsafe(32)}"


def hash_api_key(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
