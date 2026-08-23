import argparse
import asyncio

from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy import select

from app.config.settings import get_settings
from app.modules.identity.models import User
from app.modules.tasks.models import Task
from app.shared.database import SessionFactory


async def enqueue_import(source: str) -> None:
    async with SessionFactory() as session:
        owner = await session.scalar(
            select(User).where(User.is_system_admin.is_(True), User.status == "active")
        )
        if owner is None:
            raise RuntimeError("No existe un administrador activo para auditar la importación")
        task = Task(
            type="creative.import",
            owner_user_id=owner.id,
            result=source,
            progress_total=5,
            progress_message="Importación en cola",
        )
        session.add(task)
        await session.commit()
        task_id = str(task.id)
    pool = await create_pool(RedisSettings.from_dsn(get_settings().redis_url))
    await pool.enqueue_job("import_creativosur_data", task_id)
    await pool.aclose()
    print(task_id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Creative module operations")
    parser.add_argument("command", choices=["enqueue-import"])
    parser.add_argument("--source", default="/data/creative/import-source")
    arguments = parser.parse_args()
    if arguments.command == "enqueue-import":
        asyncio.run(enqueue_import(arguments.source))


if __name__ == "__main__":
    main()
