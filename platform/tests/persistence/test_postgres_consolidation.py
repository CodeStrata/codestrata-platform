"""PostgreSQL consolidation and migration tests."""

from __future__ import annotations

import warnings

import pytest
from sqlalchemy import text

from codestrata_platform.infrastructure.persistence.database import (
    DatabaseConfigurationError,
    get_database_url,
)
from codestrata_platform.infrastructure.persistence.migrations.runner import (
    current_revision,
    downgrade_base,
    upgrade_head,
)


def test_sqlite_urls_are_rejected() -> None:
    with pytest.raises(DatabaseConfigurationError):
        get_database_url(override="sqlite+pysqlite:///:memory:")


def test_canonical_url_wins_over_deprecated(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "CODESTRATA_DATABASE_URL",
        "postgresql+psycopg://canonical:pw@127.0.0.1:5432/codestrata",
    )
    monkeypatch.setenv(
        "CODESTRATA_PLATFORM_DATABASE_URL",
        "postgresql+psycopg://deprecated:pw@127.0.0.1:5432/codestrata",
    )
    assert get_database_url().startswith("postgresql+psycopg://canonical:")


def test_deprecated_platform_url_warns(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODESTRATA_DATABASE_URL", raising=False)
    monkeypatch.setenv(
        "CODESTRATA_PLATFORM_DATABASE_URL",
        "postgresql+psycopg://deprecated:pw@127.0.0.1:5432/codestrata",
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        url = get_database_url()
    assert "deprecated" in url
    assert any(issubclass(item.category, DeprecationWarning) for item in caught)


def test_missing_database_url_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODESTRATA_DATABASE_URL", raising=False)
    monkeypatch.delenv("CODESTRATA_PLATFORM_DATABASE_URL", raising=False)
    monkeypatch.delenv("CODESTRATA_PGVECTOR_URL", raising=False)
    with pytest.raises(DatabaseConfigurationError):
        get_database_url()


def test_alembic_runner_preserves_password_in_url() -> None:
    from codestrata_platform.infrastructure.persistence import create_engine_from_url
    from codestrata_platform.infrastructure.persistence.migrations.runner import (
        _alembic_config,
    )

    engine = create_engine_from_url(
        "postgresql+psycopg://codestrata:codestrata@127.0.0.1:5432/codestrata"
    )
    config = _alembic_config(engine)
    url = config.get_main_option("sqlalchemy.url") or ""
    assert "***" not in url
    assert "codestrata@" in url or "codestrata:" in url
    engine.dispose()


def test_migrations_upgrade_and_downgrade(postgres_url: str) -> None:
    from codestrata_platform.infrastructure.persistence import create_engine_from_url

    engine = create_engine_from_url(postgres_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    upgrade_head(engine)
    assert current_revision(engine) == "0010_portfolio_answering"
    with engine.connect() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
        }
    assert "organizations" in tables
    assert "assessment_artifacts" in tables
    assert "assessment_intelligence" in tables
    assert "findings" in tables
    assert "engineering_snapshots" in tables
    assert "engineering_technologies" in tables
    assert "engineering_taxonomy" in tables
    assert "engineering_knowledge_graphs" in tables
    assert "engineering_graph_projections" in tables
    assert "engineering_graph_nodes" in tables
    assert "engineering_graph_edges" in tables
    assert "graph_intelligence_runs" in tables
    assert "graph_integrity_results" in tables
    assert "engineering_retrieval_indexes" in tables
    assert "engineering_retrieval_documents" in tables
    assert "engineering_retrieval_chunks" in tables
    assert "engineering_retrieval_index_runs" in tables
    assert "engineering_portfolios" in tables
    assert "engineering_portfolio_snapshots" in tables
    assert "engineering_portfolio_retrieval_indexes" in tables
    assert "engineering_portfolio_retrieval_documents" in tables
    assert "engineering_portfolio_retrieval_chunks" in tables
    assert "engineering_portfolio_retrieval_index_runs" in tables
    assert "engineering_answer_runs" in tables
    assert "engineering_answer_citations" in tables
    assert "engineering_answer_feedback" in tables
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            row = connection.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            ).first()
        if row is None:
            pytest.skip("pgvector extension unavailable on this PostgreSQL instance")
    except Exception as error:  # noqa: BLE001 - Homebrew PG without pgvector
        pytest.skip(f"pgvector extension unavailable: {error}")
    downgrade_base(engine)
    assert current_revision(engine) is None
    engine.dispose()
