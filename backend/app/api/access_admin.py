from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_permission
from app.modules.identity.audit import record_audit
from app.modules.identity.models import Role, User, user_roles
from app.modules.identity.security import hash_password
from app.shared.database import get_session

router = APIRouter(prefix="/api/v1/access", tags=["access"])


class UserCreate(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=12, max_length=256)
    roles: list[str] = Field(min_length=1)


class RolesUpdate(BaseModel):
    roles: list[str] = Field(min_length=1)


class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(active|suspended|disabled)$")


async def roles_by_slug(session: AsyncSession, slugs: list[str]) -> list[Role]:
    normalized = sorted(set(slugs))
    roles = (await session.scalars(select(Role).where(Role.slug.in_(normalized)))).all()
    if len(roles) != len(normalized):
        raise HTTPException(status_code=422, detail="Uno o más roles no existen.")
    return list(roles)


async def ensure_admin_remains(session: AsyncSession, target: User, role_slugs: list[str], target_status: str) -> None:
    removes_admin = target.is_system_admin and ("system-admin" not in role_slugs or target_status != "active")
    if not removes_admin:
        return
    remaining = await session.scalar(select(func.count()).select_from(User).where(User.is_system_admin.is_(True), User.status == "active", User.id != target.id))
    if not remaining:
        raise HTTPException(status_code=409, detail="Debe permanecer al menos un administrador activo.")


def serialize_user(user: User, role_names: list[str]) -> dict[str, object]:
    return {"id": str(user.id), "email": user.email, "display_name": user.display_name, "status": user.status, "is_system_admin": user.is_system_admin, "roles": role_names, "created_at": user.created_at.isoformat()}


@router.get("/roles")
async def list_roles(session: AsyncSession = Depends(get_session), actor: User = Depends(require_permission("users:manage"))) -> dict[str, object]:
    roles = (await session.scalars(select(Role).order_by(Role.slug))).all()
    return {"items": [{"slug": role.slug, "name": role.name, "system": role.is_system_role} for role in roles]}


@router.get("/users")
async def list_users(session: AsyncSession = Depends(get_session), actor: User = Depends(require_permission("users:manage"))) -> dict[str, object]:
    users = (await session.scalars(select(User).order_by(User.created_at))).all()
    mappings = (await session.execute(select(user_roles.c.user_id, Role.slug).join(Role, Role.id == user_roles.c.role_id))).all()
    indexed: dict[UUID, list[str]] = {user.id: [] for user in users}
    for user_id, slug in mappings: indexed[user_id].append(slug)
    return {"items": [serialize_user(user, indexed[user.id]) for user in users]}


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, session: AsyncSession = Depends(get_session), actor: User = Depends(require_permission("users:manage"))) -> dict[str, object]:
    if await session.scalar(select(User).where(User.email == str(payload.email).lower())):
        raise HTTPException(status_code=409, detail="El email ya existe.")
    roles = await roles_by_slug(session, payload.roles)
    user = User(email=str(payload.email).lower(), display_name=payload.display_name, password_hash=hash_password(payload.password), is_system_admin=any(role.slug == "system-admin" for role in roles))
    session.add(user); await session.flush()
    for role in roles: await session.execute(user_roles.insert().values(user_id=user.id, role_id=role.id))
    await record_audit(session, actor.id, "user.created", "user", str(user.id), {"roles": payload.roles})
    await session.commit()
    return serialize_user(user, [role.slug for role in roles])


@router.put("/users/{user_id}/roles")
async def update_roles(user_id: UUID, payload: RolesUpdate, session: AsyncSession = Depends(get_session), actor: User = Depends(require_permission("users:manage"))) -> dict[str, object]:
    user = await session.get(User, user_id)
    if user is None: raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    roles = await roles_by_slug(session, payload.roles)
    await ensure_admin_remains(session, user, payload.roles, user.status)
    await session.execute(user_roles.delete().where(user_roles.c.user_id == user.id))
    for role in roles: await session.execute(user_roles.insert().values(user_id=user.id, role_id=role.id))
    user.is_system_admin = any(role.slug == "system-admin" for role in roles)
    await record_audit(session, actor.id, "user.roles_updated", "user", str(user.id), {"roles": payload.roles})
    await session.commit()
    return serialize_user(user, [role.slug for role in roles])


@router.patch("/users/{user_id}/status")
async def update_status(user_id: UUID, payload: StatusUpdate, session: AsyncSession = Depends(get_session), actor: User = Depends(require_permission("users:manage"))) -> dict[str, object]:
    user = await session.get(User, user_id)
    if user is None: raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    await ensure_admin_remains(session, user, ["system-admin"] if user.is_system_admin else [], payload.status)
    user.status = payload.status
    await record_audit(session, actor.id, "user.status_updated", "user", str(user.id), {"status": payload.status})
    await session.commit()
    role_names = list((await session.scalars(select(Role.slug).join(user_roles, user_roles.c.role_id == Role.id).where(user_roles.c.user_id == user.id))).all())
    return serialize_user(user, role_names)
