from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.models import Permission, Role, role_permissions

PERMISSIONS = ("conversations:read", "conversations:write", "agents:read", "agents:execute", "agents:write", "agents:publish", "models:read", "tasks:read", "memory:read", "memory:write", "workflows:run", "plugins:manage", "providers:manage", "tools:execute", "users:manage", "system:admin")


async def seed_rbac(session: AsyncSession) -> None:
    existing = {item.code for item in (await session.scalars(select(Permission))).all()}
    for code in PERMISSIONS:
        if code not in existing: session.add(Permission(code=code))
    roles = {item.slug for item in (await session.scalars(select(Role))).all()}
    for slug, name in (("system-admin", "System Administrator"), ("operator", "Operator"), ("viewer", "Viewer")):
        if slug not in roles: session.add(Role(slug=slug, name=name, is_system_role=True))
    await session.commit()
    permissions = {item.code: item for item in (await session.scalars(select(Permission))).all()}
    roles_by_slug = {item.slug: item for item in (await session.scalars(select(Role))).all()}
    grants = {"system-admin": set(PERMISSIONS), "operator": {"conversations:read", "conversations:write", "agents:read", "agents:execute", "models:read", "tasks:read", "workflows:run"}, "viewer": {"conversations:read", "agents:read", "models:read", "tasks:read"}}
    for slug, codes in grants.items():
        existing_codes = set((await session.execute(select(Permission.code).join(role_permissions, role_permissions.c.permission_id == Permission.id).where(role_permissions.c.role_id == roles_by_slug[slug].id))).scalars())
        for code in codes - existing_codes:
            await session.execute(role_permissions.insert().values(role_id=roles_by_slug[slug].id, permission_id=permissions[code].id))
    await session.commit()
