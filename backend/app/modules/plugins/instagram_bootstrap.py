from sqlalchemy import select

from app.config.settings import Settings
from app.modules.identity.models import User
from app.modules.plugins.instagram_models import InstagramAccount
from app.shared.database import SessionFactory
from app.shared.secrets import SecretCipher


async def bootstrap_instagram_account(settings: Settings) -> None:
    values = (
        settings.instagram_app_id,
        settings.instagram_app_secret.get_secret_value(),
        settings.instagram_access_token.get_secret_value(),
        settings.instagram_user_id,
    )
    if not any(values):
        return
    if not all(values):
        raise RuntimeError("Las variables INSTAGRAM_APP_ID, INSTAGRAM_APP_SECRET, INSTAGRAM_ACCESS_TOKEN e INSTAGRAM_USER_ID deben configurarse juntas.")
    async with SessionFactory() as session:
        existing = await session.scalar(
            select(InstagramAccount).where(
                InstagramAccount.account_label == settings.instagram_account_label
            )
        )
        if existing is not None:
            return
        admin = await session.scalar(
            select(User).where(User.is_system_admin.is_(True)).order_by(User.created_at)
        )
        if admin is None:
            return
        cipher = SecretCipher(settings)
        session.add(
            InstagramAccount(
                account_label=settings.instagram_account_label,
                app_id=settings.instagram_app_id,
                app_secret_encrypted=cipher.encrypt(settings.instagram_app_secret.get_secret_value()),
                instagram_user_id=settings.instagram_user_id,
                access_token_encrypted=cipher.encrypt(settings.instagram_access_token.get_secret_value()),
                api_version=settings.instagram_api_version,
                enabled=True,
                created_by_user_id=admin.id,
            )
        )
        await session.commit()
