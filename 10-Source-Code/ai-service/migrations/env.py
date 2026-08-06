import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.core.database import Base

# Import read-only mirrors (Asset, Equipment, RiskAssessment, Finding, CorrosionRecord — owned
# by the backend service) so Base.metadata knows about them for FK resolution, and this
# service's own tables (AIPrediction, DocumentEmbedding) which it actually migrates.
from app.core import read_models  # noqa: F401
from app.modules.copilot import models as copilot_models  # noqa: F401
from app.rag import vector_store  # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# This service must NEVER generate migrations for tables the backend service owns and
# migrates (see Deployment.md §3) — only ai_prediction and document_embedding are ours.
OWNED_TABLES = {"ai_prediction", "document_embedding"}


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        return name in OWNED_TABLES
    # For columns/indexes, only include objects belonging to an owned table.
    table_name = getattr(getattr(object, "table", None), "name", None)
    if table_name is not None:
        return table_name in OWNED_TABLES
    return True


# backend and ai-service share one physical database but migrate independently — each needs
# its own revision-tracking table, or this service's fresh migration chain can't find the
# backend's revision IDs (and vice versa). See Deployment.md §3.
VERSION_TABLE = "alembic_version_ai"


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        version_table=VERSION_TABLE,
    )
    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        version_table=VERSION_TABLE,
    )
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
