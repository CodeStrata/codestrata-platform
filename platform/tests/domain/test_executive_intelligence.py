"""Domain tests for Executive Intelligence."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.errors import InvalidStateTransitionError
from codestrata_platform.domain.executive_intelligence.errors import (
    ExecutiveIntelligenceInvariantError,
)
from codestrata_platform.domain.executive_intelligence.identifiers import (
    ExecutiveIntelligenceId,
    ExecutiveMetricId,
    ExecutiveProjectionKey,
)
from codestrata_platform.domain.executive_intelligence.lifecycle import (
    ExecutiveConfidenceBand,
    ExecutiveIntelligenceStatus,
    ExecutiveMetricKey,
)
from codestrata_platform.domain.executive_intelligence.models import ExecutiveMetric
from codestrata_platform.domain.executive_intelligence.snapshot import ExecutiveIntelligenceSnapshot
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.workspace.ids import WorkspaceId


def _pending_snapshot(*, version: int = 1) -> ExecutiveIntelligenceSnapshot:
    return ExecutiveIntelligenceSnapshot.create_pending(
        organization_id=OrganizationId("org:1"),
        workspace_id=WorkspaceId("ws:1"),
        portfolio_id=PortfolioId("portfolio:1"),
        portfolio_snapshot_id=PortfolioSnapshotId("portfolio-snapshot:1"),
        portfolio_snapshot_version=1,
        version=version,
        projection_key=ExecutiveProjectionKey.from_parts(
            organization_id="org:1",
            workspace_id="ws:1",
            portfolio_id="portfolio:1",
            portfolio_snapshot_id="portfolio-snapshot:1",
            portfolio_snapshot_version=1,
            policy_version="executive-aggregation-v1",
            schema_version="executive-schema-v1",
        ),
    )


def _metric(snapshot_id: str, key: ExecutiveMetricKey) -> ExecutiveMetric:
    return ExecutiveMetric(
        metric_id=ExecutiveMetricId.for_metric(snapshot_id, key.value),
        key=key,
        score=50,
        confidence=0.6,
        confidence_band=ExecutiveConfidenceBand.MEDIUM,
        coverage=0.5,
        inputs=("risk_summary.overall_score",),
        calculation_rule="deterministic test rule",
        limitations=(),
        policy_version="executive-aggregation-v1",
    )


def test_executive_intelligence_lifecycle_and_immutability() -> None:
    snapshot = _pending_snapshot()
    assert snapshot.status is ExecutiveIntelligenceStatus.PENDING
    snapshot.begin_aggregation()
    assert snapshot.status is ExecutiveIntelligenceStatus.AGGREGATING

    metrics = (
        _metric(snapshot.executive_intelligence_id.value, ExecutiveMetricKey.PORTFOLIO_RISK),
    )
    snapshot.complete(
        metrics=metrics,
        findings=(),
        recommendations=(),
        observations=(),
        limitations=("test limitation",),
    )
    assert snapshot.status is ExecutiveIntelligenceStatus.COMPLETED
    assert snapshot.completed_at is not None
    assert snapshot.metrics == metrics

    with pytest.raises(InvalidStateTransitionError):
        snapshot.begin_aggregation()
    with pytest.raises(InvalidStateTransitionError):
        snapshot.complete(metrics=metrics, findings=(), recommendations=(), observations=())
    with pytest.raises(InvalidStateTransitionError):
        snapshot.fail("boom")

    snapshot.supersede()
    assert snapshot.status is ExecutiveIntelligenceStatus.SUPERSEDED
    assert snapshot.superseded_at is not None
    with pytest.raises(InvalidStateTransitionError):
        snapshot.supersede()


def test_executive_intelligence_failure_clears_inventory() -> None:
    snapshot = _pending_snapshot()
    snapshot.begin_aggregation()
    snapshot.fail("aggregation exploded")
    assert snapshot.status is ExecutiveIntelligenceStatus.FAILED
    assert snapshot.failure_reason == "aggregation exploded"
    assert snapshot.metrics == ()
    with pytest.raises(InvalidStateTransitionError):
        snapshot.begin_aggregation()


def test_completed_executive_intelligence_requires_metrics() -> None:
    snapshot = _pending_snapshot()
    snapshot.begin_aggregation()
    with pytest.raises(ExecutiveIntelligenceInvariantError):
        snapshot.complete(metrics=(), findings=(), recommendations=(), observations=())


def test_completed_executive_intelligence_rejects_duplicate_metric_keys() -> None:
    snapshot = _pending_snapshot()
    snapshot.begin_aggregation()
    exec_id = snapshot.executive_intelligence_id.value
    duplicated = (
        _metric(exec_id, ExecutiveMetricKey.PORTFOLIO_RISK),
        _metric(exec_id, ExecutiveMetricKey.PORTFOLIO_RISK),
    )
    with pytest.raises(ExecutiveIntelligenceInvariantError):
        snapshot.complete(
            metrics=duplicated,
            findings=(),
            recommendations=(),
            observations=(),
        )


def test_projection_key_is_deterministic() -> None:
    kwargs = dict(
        organization_id="org:1",
        workspace_id="ws:1",
        portfolio_id="portfolio:1",
        portfolio_snapshot_id="portfolio-snapshot:1",
        portfolio_snapshot_version=3,
        policy_version="executive-aggregation-v1",
        schema_version="executive-schema-v1",
    )
    first = ExecutiveProjectionKey.from_parts(**kwargs)
    second = ExecutiveProjectionKey.from_parts(**kwargs)
    assert first.value == second.value

    changed = ExecutiveProjectionKey.from_parts(
        **{**kwargs, "portfolio_snapshot_version": 4},
    )
    assert changed.value != first.value


def test_executive_intelligence_id_generation_is_prefixed() -> None:
    generated = ExecutiveIntelligenceId.generate()
    assert generated.value.startswith("exec-intel")
