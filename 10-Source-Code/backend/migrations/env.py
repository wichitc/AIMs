import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.core.database import Base

# Import every module's models so Base.metadata is complete for autogenerate —
# each import registers that module's tables on the shared Base.
from app.modules.identity import models as identity_models  # noqa: F401
from app.modules.asset import models as asset_models  # noqa: F401
from app.modules.inspection import models as inspection_models  # noqa: F401
from app.modules.rbi import models as rbi_models  # noqa: F401
from app.modules.corrosion import models as corrosion_models  # noqa: F401
from app.modules.defect import models as defect_models  # noqa: F401
from app.modules.condition_monitoring import models as condition_monitoring_models  # noqa: F401
from app.modules.maintenance import models as maintenance_models  # noqa: F401
from app.modules.document import models as document_models  # noqa: F401
from app.modules.audit_log import models as audit_log_models  # noqa: F401
from app.modules.purchasing import models as purchasing_models  # noqa: F401
from app.modules.inventory import models as inventory_models  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# backend and ai-service share one physical database but migrate independently — each needs
# its own revision-tracking table, or ai-service's fresh migration chain can't find backend's
# revision IDs (and vice versa). See Deployment.md §3.
VERSION_TABLE = "alembic_version_core"


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=VERSION_TABLE,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, version_table=VERSION_TABLE)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(_do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
