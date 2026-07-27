"""Helpers to run Alembic migrations programmatically."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine


def _alembic_config(engine: Engine | None = None) -> Config:
    root = Path(__file__).resolve().parent
    config = Config()
    config.set_main_option("script_location", str(root))
    config.set_main_option("prepend_sys_path", ".")
    config.set_main_option("path_separator", "os")
    if engine is not None:
        # SQLAlchemy's str(url) redacts the password as "***", which breaks
        # password-authenticated Docker Compose databases.
        config.set_main_option(
            "sqlalchemy.url",
            engine.url.render_as_string(hide_password=False),
        )
    return config


def upgrade_head(engine: Engine) -> None:
    """Upgrade the bound database to the latest Platform revision."""

    command.upgrade(_alembic_config(engine), "head")


def downgrade_base(engine: Engine) -> None:
    """Downgrade the bound database to base (empty schema)."""

    command.downgrade(_alembic_config(engine), "base")


def current_revision(engine: Engine) -> str | None:
    from alembic.runtime.migration import MigrationContext

    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()
