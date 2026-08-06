import json
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_system_admin
from app.modules.identity.audit import record_audit
from app.modules.identity.models import ApiKey, RefreshToken, Role, User, user_roles
from app.modules.identity.security import (
    create_access_token,
    generate_api_key,
    generate_refresh_token,
    hash_api_key,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1", tags=["identity"])
MACHINE_API_KEY_SCOPES = {"agents:read", "agents:execute", "models:read", "tasks:read"}


class SetupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)
    display_name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ApiKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    scopes: list[str] = Field(min_length=1)
    expires_at: datetime | None = None


def serialize_api_key(key: ApiKey) -> dict[str, object]:
    return {
        "id": str(key.id),
        "name": key.name,
        "key_prefix": key.key_prefix,
        "user_id": str(key.user_id),
        "scopes": json.loads(key.scopes),
        "enabled": key.enabled,
        "expires_at": key.expires_at.isoformat() if key.expires_at else None,
        "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
        "created_at": key.created_at.isoformat(),
        "revoked_at": key.revoked_at.isoformat() if key.revoked_at else None,
    }


@router.get("/setup/status")
async def setup_status(session: AsyncSession = Depends(get_session)) -> dict[str, bool]:
    count = await session.scalar(select(func.count()).select_from(User))
    return {"setup_required": count == 0}


@router.post("/setup/initialize", status_code=status.HTTP_201_CREATED)
async def initialize_setup(payload: SetupRequest, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    count = await session.scalar(select(func.count()).select_from(User))
    if count:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La instalación ya fue inicializada.")
    user = User(email=str(payload.email).lower(), display_name=payload.display_name, password_hash=hash_password(payload.password), is_system_admin=True)
    session.add(user)
    await session.flush()
    role = await session.scalar(select(Role).where(Role.slug == "system-admin"))
    if role is not None:
        await session.execute(user_roles.insert().values(user_id=user.id, role_id=role.id))
    await session.commit()
    return {"id": str(user.id), "email": user.email}


async def create_session(user: User, session: AsyncSession) -> dict[str, str]:
    raw_token = generate_refresh_token()
    session.add(RefreshToken(user_id=user.id, token_hash=hash_refresh_token(raw_token), expires_at=datetime.now(UTC) + timedelta(days=30)))
    await session.commit()
    return {"access_token": create_access_token(user.id), "refresh_token": raw_token, "token_type": "bearer"}


@router.post("/auth/login")
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    user = await session.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash) or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas.")
    return await create_session(user, session)


@router.post("/auth/refresh")
async def refresh(payload: RefreshRequest, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    token = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(payload.refresh_token)))
    if token is None or token.revoked_at is not None or token.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida o vencida.")
    user = await session.get(User, token.user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida.")
    token.revoked_at = datetime.now(UTC)
    return await create_session(user, session)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, session: AsyncSession = Depends(get_session)) -> None:
    token = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(payload.refresh_token)))
    if token is not None and token.revoked_at is None:
        token.revoked_at = datetime.now(UTC)
        await session.commit()


@router.get("/api-keys")
async def list_api_keys(session: AsyncSession = Depends(get_session), user: User = Depends(require_system_admin)) -> dict[str, object]:
    keys = (await session.scalars(select(ApiKey).where(ApiKey.user_id == user.id).order_by(ApiKey.created_at.desc()))).all()
    return {"items": [serialize_api_key(key) for key in keys], "available_scopes": sorted(MACHINE_API_KEY_SCOPES)}


@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(payload: ApiKeyRequest, session: AsyncSession = Depends(get_session), user: User = Depends(require_system_admin)) -> dict[str, object]:
    scopes = sorted(set(payload.scopes))
    unsupported_scopes = set(scopes) - MACHINE_API_KEY_SCOPES
    if unsupported_scopes:
        raise HTTPException(status_code=422, detail=f"Scopes no permitidos: {', '.join(sorted(unsupported_scopes))}")
    expires_at = payload.expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at is not None and expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=422, detail="La expiración debe ser futura.")
    prefix, raw_key = generate_api_key()
    key = ApiKey(user_id=user.id, name=payload.name, key_prefix=prefix, key_hash=hash_api_key(raw_key), scopes=json.dumps(scopes), enabled=True, expires_at=expires_at)
    session.add(key)
    await session.flush()
    await record_audit(session, user.id, "api_key.created", "api_key", str(key.id), {"name": key.name, "scopes": scopes, "key_prefix": key.key_prefix})
    await session.commit()
    await session.refresh(key)
    return {**serialize_api_key(key), "api_key": raw_key}


@router.post("/api-keys/{key_id}/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(key_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(require_system_admin)) -> None:
    key = await session.get(ApiKey, key_id)
    if key is None or key.user_id != user.id:
        raise HTTPException(status_code=404, detail="API key no encontrada.")
    if key.revoked_at is None:
        key.revoked_at = datetime.now(UTC)
        key.enabled = False
        await record_audit(session, user.id, "api_key.revoked", "api_key", str(key.id), {"key_prefix": key.key_prefix})
        await session.commit()


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(key_id: UUID, session: AsyncSession = Depends(get_session), user: User = Depends(require_system_admin)) -> None:
    key = await session.get(ApiKey, key_id)
    if key is None or key.user_id != user.id:
        raise HTTPException(status_code=404, detail="API key no encontrada.")
    await record_audit(session, user.id, "api_key.deleted", "api_key", str(key.id), {"name": key.name, "key_prefix": key.key_prefix})
    await session.delete(key)
    await session.commit()
