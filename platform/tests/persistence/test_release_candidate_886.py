"""Phase 8.8.6 release-candidate cleanup regressions."""

from __future__ import annotations

import pytest

from codestrata_platform.api.configuration.settings import ApiSettings
from codestrata_platform.infrastructure.persistence.database import get_database_url


def test_memory_settings_reject_sqlite_urls() -> None:
    with pytest.raises(RuntimeError, match="SQLite is not supported"):
        ApiSettings.from_env(use_memory=True, database_url="sqlite+pysqlite:///:memory:")


def test_platform_database_rejects_sqlite() -> None:
    with pytest.raises(Exception, match="SQLite is not supported"):
        get_database_url(override="sqlite+pysqlite:///:memory:")


def test_intentional_sqlite_is_engine_knowledge_store_only() -> None:
    """Commercial Platform must not ship a SQLite persistence adapter."""

    from pathlib import Path

    persistence = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "codestrata_platform"
        / "infrastructure"
        / "persistence"
    )
    offenders = [
        path.relative_to(persistence).as_posix()
        for path in persistence.rglob("*.py")
        if "sqlite" in path.name.lower()
    ]
    assert offenders == []
