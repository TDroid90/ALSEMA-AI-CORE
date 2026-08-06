import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.config.settings import get_settings

password_hash = PasswordHash.recommended()
API_KEY_PREFIX = "alsema_sk_"
API_KEY_LOOKUP_LENGTH = 20


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
    raw_key = f"{API_KEY_PREFIX}{secrets.token_urlsafe(36)}"
    return raw_key[:API_KEY_LOOKUP_LENGTH], raw_key


def api_key_prefix(token: str) -> str:
    return token[:API_KEY_LOOKUP_LENGTH]


def hash_api_key(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
