from sqlalchemy import func, select

from app.config.settings import Settings
from app.modules.identity.models import Role, User, user_roles
from app.modules.identity.rbac import seed_rbac
from app.modules.identity.security import hash_password
from app.shared.database import SessionFactory


async def bootstrap_initial_admin(settings: Settings) -> None:
    """Create the configured administrator only for an untouched installation."""
    email = settings.initial_admin_email
    password = settings.initial_admin_password.get_secret_value() if settings.initial_admin_password else None
    if not email or not password:
        if email or password:
            raise RuntimeError("INITIAL_ADMIN_EMAIL e INITIAL_ADMIN_PASSWORD deben configurarse juntos.")

    async with SessionFactory() as session:
        await seed_rbac(session)
        if not email and not password:
            return
        assert password is not None
        user_count = await session.scalar(select(func.count()).select_from(User))
        if user_count:
            return
        user = User(email=email.lower(), display_name="System Administrator", password_hash=hash_password(password), is_system_admin=True)
        session.add(user)
        await session.flush()
        role = await session.scalar(select(Role).where(Role.slug == "system-admin"))
        if role is not None:
            await session.execute(user_roles.insert().values(user_id=user.id, role_id=role.id))
        await session.commit()
