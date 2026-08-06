from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config.settings import get_settings
from app.modules.agents import models as _agent_models  # noqa: F401
from app.modules.conversations import models as _conversation_models  # noqa: F401
from app.modules.identity.models import Base
from app.modules.memory import models as _memory_models  # noqa: F401
from app.modules.plugins import facebook_models as _facebook_models  # noqa: F401
from app.modules.plugins import instagram_models as _instagram_models  # noqa: F401
from app.modules.tasks import models as _task_models  # noqa: F401
from app.modules.workflows import models as _workflow_models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", str(get_settings().database_url).replace("+asyncpg", "+psycopg"))


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section) or {}, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
