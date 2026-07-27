"""Static checks for portfolio answering migration head (no live DB required)."""

from __future__ import annotations

from pathlib import Path

from alembic.script import ScriptDirectory

MIGRATIONS = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "codestrata_platform"
    / "infrastructure"
    / "persistence"
    / "migrations"
)


def test_alembic_head_is_executive_intelligence() -> None:
    script = ScriptDirectory(str(MIGRATIONS))
    assert script.get_heads() == ["0011_executive_intelligence"]


def test_portfolio_answering_migration_fk_targets() -> None:
    path = MIGRATIONS / "versions" / "0010_portfolio_answering.py"
    source = path.read_text(encoding="utf-8")
    assert "engineering_portfolios.portfolio_id" in source
    assert "engineering_portfolio_snapshots.portfolio_snapshot_id" in source
    assert "engineering_portfolio_retrieval_indexes.id" in source
    assert "engineering_portfolio_answer_runs" in source
    assert "engineering_portfolio_answer_citations" in source
    assert "engineering_portfolio_answer_feedback" in source
    assert 'down_revision: str | None = "0009_portfolio_retrieval"' in source
    assert "engineering_portfolios.id" not in source
    assert "engineering_portfolio_snapshots.id" not in source