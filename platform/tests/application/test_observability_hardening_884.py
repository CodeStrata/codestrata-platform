"""Application-level observability diagnostics regressions (Phase 8.8.4)."""

from __future__ import annotations

import pytest

from codestrata_platform.application.common.diagnostics import safe_failure_summary
from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_intelligence.errors import (
    ExecutiveIntelligenceDisabledError,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveIntelligenceStatus,
)
from codestrata_platform.domain.portfolio.identifiers import PortfolioId

from .test_executive_intelligence_service import (
    _build_portfolio,
    _enable_executive_intelligence,
    _seed_repository,
)
from .test_executive_intelligence_service import (
    _stack as _exec_stack,
)


def test_executive_intelligence_failure_reason_is_sanitized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _exec_stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="python")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])

    def boom(_snapshot):
        raise RuntimeError(
            "aggregation failed postgresql+psycopg://codestrata:leakpass@db/codestrata"
        )

    monkeypatch.setattr(
        "codestrata_platform.application.executive_intelligence.services.run_executive_aggregation",
        boom,
    )
    with pytest.raises(RuntimeError):
        stack["exec_service"].build_intelligence(
            BuildExecutiveIntelligenceCommand(
                portfolio_id=portfolio_id,
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )
    items = stack["executive_intelligence"].list_by_portfolio(portfolio_id, limit=10)
    failed = [
        item
        for item in items
        if item.status is ExecutiveIntelligenceStatus.FAILED and item.failure_reason
    ]
    assert failed
    assert "leakpass" not in (failed[0].failure_reason or "")


def test_disabled_executive_intelligence_raises_before_snapshot_work(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", raising=False)
    stack = _exec_stack()
    calls = {"n": 0}
    real = stack["portfolio_snapshots"].get_latest_completed

    def counting(portfolio_id):
        calls["n"] += 1
        return real(portfolio_id)

    monkeypatch.setattr(stack["portfolio_snapshots"], "get_latest_completed", counting)
    with pytest.raises(ExecutiveIntelligenceDisabledError) as exc_info:
        stack["exec_service"].build_intelligence(
            BuildExecutiveIntelligenceCommand(
                portfolio_id=PortfolioId("portfolio:disabled-check"),
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )
    assert exc_info.value.reason_code == "executive_intelligence_disabled"
    assert calls["n"] == 0


def test_safe_failure_summary_bounds_length() -> None:
    summary = safe_failure_summary("x" * 5000, limit=100)
    assert len(summary) == 100
