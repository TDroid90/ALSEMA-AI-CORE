import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette.requests import Request

from app.api.dependencies import get_current_user
from app.modules.identity.models import ApiKey, User
from app.modules.identity.security import (
    API_KEY_PREFIX,
    api_key_prefix,
    generate_api_key,
    hash_api_key,
)


class ApiKeySession:
    def __init__(self, key: ApiKey, user: User) -> None:
        self.key = key
        self.user = user
        self.commits = 0

    async def scalar(self, _statement: object) -> ApiKey:
        return self.key

    async def get(self, _model: object, _identifier: object) -> User:
        return self.user

    async def commit(self) -> None:
        self.commits += 1


def request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/api/v1/agents", "headers": []})


def credentials(raw_key: str) -> tuple[ApiKey, User, ApiKeySession]:
    user = User(
        id=uuid4(),
        email="service-owner@example.test",
        display_name="Service owner",
        password_hash="unused",
        status="active",
        is_system_admin=True,
    )
    key = ApiKey(
        id=uuid4(),
        user_id=user.id,
        name="instanews-rewriter",
        key_prefix=api_key_prefix(raw_key),
        key_hash=hash_api_key(raw_key),
        scopes=json.dumps(["agents:execute", "agents:read"]),
        enabled=True,
        expires_at=None,
        revoked_at=None,
        last_used_at=None,
        created_at=datetime.now(UTC),
    )
    return key, user, ApiKeySession(key, user)


def test_generated_api_key_has_required_format_and_only_hash_is_persistable() -> None:
    prefix, raw_key = generate_api_key()

    assert raw_key.startswith(API_KEY_PREFIX)
    assert len(raw_key) >= 50
    assert prefix == api_key_prefix(raw_key)
    assert raw_key not in hash_api_key(raw_key)
    assert len(hash_api_key(raw_key)) == 64


@pytest.mark.asyncio
@pytest.mark.parametrize("header", ["authorization", "x-api-key"])
async def test_api_key_authentication_accepts_both_supported_headers(header: str) -> None:
    _, raw_key = generate_api_key()
    key, user, session = credentials(raw_key)
    bearer = HTTPAuthorizationCredentials(scheme="Bearer", credentials=raw_key) if header == "authorization" else None
    x_api_key = raw_key if header == "x-api-key" else None
    http_request = request()

    authenticated = await get_current_user(http_request, bearer, x_api_key, session)  # type: ignore[arg-type]

    assert authenticated.id == user.id
    assert key.last_used_at is not None
    assert session.commits == 1
    assert http_request.state.api_key_scopes == {"agents:read", "agents:execute"}


@pytest.mark.asyncio
async def test_x_api_key_never_falls_back_to_jwt() -> None:
    _, raw_key = generate_api_key()
    _, _, session = credentials(raw_key)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(request(), None, "jwt-looking-but-not-an-api-key", session)  # type: ignore[arg-type]

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_disabled_expired_or_revoked_api_key_is_rejected() -> None:
    _, raw_key = generate_api_key()
    key, _, session = credentials(raw_key)
    bearer = HTTPAuthorizationCredentials(scheme="Bearer", credentials=raw_key)

    key.enabled = False
    with pytest.raises(HTTPException):
        await get_current_user(request(), bearer, None, session)  # type: ignore[arg-type]

    key.enabled = True
    key.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(HTTPException):
        await get_current_user(request(), bearer, None, session)  # type: ignore[arg-type]

    key.expires_at = None
    key.revoked_at = datetime.now(UTC)
    with pytest.raises(HTTPException):
        await get_current_user(request(), bearer, None, session)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_conflicting_authentication_headers_are_rejected() -> None:
    _, first_key = generate_api_key()
    _, second_key = generate_api_key()
    _, _, session = credentials(first_key)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(
            request(),
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=first_key),
            second_key,
            session,  # type: ignore[arg-type]
        )

    assert exc.value.status_code == 401
