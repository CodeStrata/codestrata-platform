"""Portfolio persistence migration smoke tests."""

from __future__ import annotations

from sqlalchemy import text

from codestrata_platform.infrastructure.persistence.migrations.runner import (
    current_revision,
    upgrade_head,
)


def test_portfolio_migration_creates_tables(postgres_url: str) -> None:
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
    expected = {
        "engineering_portfolios",
        "engineering_portfolio_memberships",
        "engineering_portfolio_snapshots",
        "engineering_portfolio_repository_snapshots",
        "engineering_portfolio_technologies",
        "engineering_portfolio_findings",
        "engineering_portfolio_recommendations",
        "engineering_portfolio_risks",
        "engineering_portfolio_modernization_candidates",
        "engineering_portfolio_analysis_runs",
        "engineering_portfolio_retrieval_indexes",
        "engineering_portfolio_retrieval_documents",
        "engineering_portfolio_retrieval_chunks",
        "engineering_portfolio_retrieval_index_runs",
        "engineering_portfolio_answer_runs",
        "engineering_portfolio_answer_citations",
        "engineering_portfolio_answer_feedback",
    }
    assert expected.issubset(tables)
