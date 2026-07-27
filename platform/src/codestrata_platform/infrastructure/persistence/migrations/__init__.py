"""PostgreSQL schema migrations for the Commercial Platform.

Production and CI use Alembic upgrades — not ``metadata.create_all``.
"""

from __future__ import annotations

from codestrata_platform.infrastructure.persistence.migrations.runner import (
    current_revision,
    downgrade_base,
    upgrade_head,
)

__all__ = [
    "current_revision",
    "downgrade_base",
    "upgrade_head",
]
