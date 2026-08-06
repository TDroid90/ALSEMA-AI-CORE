import json
from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.modules.identity.models import ApiKey, Permission, User, role_permissions, user_roles
from app.modules.identity.security import hash_api_key
from app.shared.database import get_session

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticación requerida.")
    if credentials.credentials.startswith("aas_"):
        parts = credentials.credentials.split("_", 3)
        if len(parts) != 4:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida.")
        key = await session.scalar(select(ApiKey).where(ApiKey.prefix == parts[2], ApiKey.secret_hash == hash_api_key(credentials.credentials)))
        if key is None or key.revoked_at is not None or (key.expires_at is not None and key.expires_at <= datetime.now(UTC)):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida o vencida.")
        user = await session.get(User, key.owner_user_id)
        if user is None or user.status != "active":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida.")
        key.last_used_at = datetime.now(UTC)
        await session.commit()
        request.state.api_key_scopes = set(json.loads(key.scopes))
        return user
    try:
        payload = jwt.decode(
            credentials.credentials,
            get_settings().app_secret_key.get_secret_value(),
            algorithms=["HS256"],
        )
        subject = payload.get("sub")
        if payload.get("type") != "access" or not subject:
            raise jwt.InvalidTokenError("Invalid token type")
        user_id = UUID(subject)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida o vencida.") from None
    user = await session.get(User, user_id)
    if user is None or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión inválida o vencida.")
    return user


async def require_system_admin(request: Request, user: User = Depends(get_current_user)) -> User:
    # API keys are never implicitly administrative, even when owned by an admin.
    # The request state is set only after a validated API key authentication.
    scopes: set[str] | None = getattr(request.state, "api_key_scopes", None)
    if not user.is_system_admin or (scopes is not None and "system:admin" not in scopes):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso de administrador requerido.")
    return user


def require_permission(code: str) -> Callable[..., object]:
    async def dependency(request: Request, session: AsyncSession = Depends(get_session), user: User = Depends(get_current_user)) -> User:
        scopes: set[str] | None = getattr(request.state, "api_key_scopes", None)
        if scopes is not None and code not in scopes and "*" not in scopes and "system:admin" not in scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Scope requerido: {code}")
        if user.is_system_admin:
            return user
        statement = select(Permission.code).join(role_permissions, role_permissions.c.permission_id == Permission.id).join(user_roles, user_roles.c.role_id == role_permissions.c.role_id).where(user_roles.c.user_id == user.id, Permission.code == code)
        if await session.scalar(statement) is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Permiso requerido: {code}")
        return user
    return dependency
