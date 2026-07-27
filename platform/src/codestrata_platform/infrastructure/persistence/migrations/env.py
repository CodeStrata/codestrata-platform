"""Alembic migration environment for Commercial Platform PostgreSQL."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from codestrata_platform.infrastructure.persistence import models as _models  # noqa: F401
from codestrata_platform.infrastructure.persistence.database import get_database_url
from codestrata_platform.infrastructure.persistence.models.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    override = config.get_main_option("sqlalchemy.url")
    if override and override.strip() and "driver://" not in override:
        return override.strip()
    return get_database_url()


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
        connect_args={"options": "-csearch_path=public"},
    )
    with connectable.connect() as connection:
        connection.exec_driver_sql("SET search_path TO public, codestrata")
        try:
            connection.exec_driver_sql(
                "CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public"
            )
        except Exception:  # noqa: BLE001 - may already exist in another schema
            connection.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
