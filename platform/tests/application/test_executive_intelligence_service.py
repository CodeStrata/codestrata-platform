"""Application tests for Executive Intelligence aggregation."""

from __future__ import annotations

import pytest

from codestrata_platform.application.common.errors import ValidationError
from codestrata_platform.application.executive_intelligence.commands import (
    BuildExecutiveIntelligenceCommand,
)
from codestrata_platform.application.executive_intelligence.errors import (
    ExecutiveIntelligenceDisabledError,
    ExecutiveIntelligenceNotReadyError,
)
from codestrata_platform.application.executive_intelligence.queries import (
    GetExecutiveIntelligenceQuery,
    GetLatestExecutiveIntelligenceQuery,
    ListExecutiveIntelligenceQuery,
)
from codestrata_platform.application.executive_intelligence.services import (
    ExecutiveIntelligenceAggregationService,
)
from codestrata_platform.application.portfolio.commands import (
    AddRepositoryToPortfolioCommand,
    BuildPortfolioSnapshotCommand,
    CreatePortfolioCommand,
    RebuildPortfolioSnapshotCommand,
)
from codestrata_platform.application.portfolio.services import (
    PortfolioIntelligenceAggregationService,
    PortfolioManagementService,
)
from codestrata_platform.domain.assessment import Assessment
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering import (
    EngineeringCategory,
    EngineeringEvidence,
    EngineeringFinding,
    EngineeringRecommendation,
    EngineeringSeverity,
    EngineeringSnapshot,
    EngineeringTechnology,
    EvidenceKind,
)
from codestrata_platform.domain.engineering.ids import (
    EngineeringEvidenceId,
    EngineeringFindingId,
    EngineeringRecommendationId,
    EngineeringSnapshotId,
    EngineeringTechnologyId,
)
from codestrata_platform.domain.executive_intelligence.identifiers import ExecutiveIntelligenceId
from codestrata_platform.domain.executive_intelligence.lifecycle import ExecutiveMetricKey
from codestrata_platform.domain.organization import Organization
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.repository import Repository, RepositoryProvider
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace import Workspace
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.memory import (
    InMemoryAssessmentRepository,
    InMemoryEngineeringSnapshotRepository,
    InMemoryExecutiveIntelligenceRepository,
    InMemoryKnowledgeGraphRepository,
    InMemoryOrganizationRepository,
    InMemoryRepositoryRepository,
    InMemoryWorkspaceRepository,
)
from codestrata_platform.infrastructure.memory.portfolio_sources import (
    DefaultPortfolioSourceIntelligenceRepository,
)
from codestrata_platform.infrastructure.memory.portfolios import (
    InMemoryPortfolioRepository,
    InMemoryPortfolioSnapshotRepository,
)


def _published(
    *,
    org: OrganizationId,
    workspace: WorkspaceId,
    repo: RepositoryId,
    assessment_id: str,
    snapshot_id: str,
    tech_key: str,
    category: EngineeringCategory = EngineeringCategory.CLOUD,
) -> tuple[Assessment, EngineeringSnapshot]:
    assessment = Assessment.create(
        repository_id=repo,
        workspace_id=workspace,
        engine_version="1.0.0",
        assessment_version="0.1.0",
        assessment_id=AssessmentId(assessment_id),
    )
    assessment.start()
    assessment.complete()
    snapshot = EngineeringSnapshot.create(
        organization_id=org,
        workspace_id=workspace,
        repository_id=repo,
        assessment_id=assessment.assessment_id,
        assessment_intelligence_id=f"intel:{assessment_id}",
        assessment_revision=1,
        version=1,
        source_artifact_ids=("artifact:1",),
        snapshot_id=EngineeringSnapshotId(snapshot_id),
    )
    finding_id = EngineeringFindingId(f"eng-finding:{snapshot_id}")
    evidence_id = EngineeringEvidenceId(f"eng-evidence:{snapshot_id}")
    recommendation_id = EngineeringRecommendationId(f"eng-rec:{snapshot_id}")
    snapshot.build(
        technologies=(
            EngineeringTechnology(
                technology_id=EngineeringTechnologyId(f"eng-tech:{snapshot_id}"),
                canonical_key=tech_key,
                display_name=tech_key.title(),
                category=category,
                metadata={"capability": "runtime"},
            ),
        ),
        findings=(
            EngineeringFinding(
                finding_id=finding_id,
                source_finding_id=f"finding:{snapshot_id}",
                category=EngineeringCategory.SECURITY,
                severity=EngineeringSeverity.CRITICAL,
                title="Shared hardening gap",
                summary="Hardening missing",
                rule_id="rule.shared.security",
                confidence=0.9,
                evidence_ids=(evidence_id.value,),
                technology_keys=(tech_key,),
            ),
        ),
        evidence=(
            EngineeringEvidence(
                evidence_id=evidence_id,
                kind=EvidenceKind.FILE,
                reference="deploy.yml",
            ),
        ),
        recommendations=(
            EngineeringRecommendation(
                recommendation_id=recommendation_id,
                source_recommendation_id="rec:shared",
                title="Harden runtime",
                rationale="Apply hardening baseline",
                category=EngineeringCategory.SECURITY,
                severity=EngineeringSeverity.HIGH,
                priority="p1",
                related_finding_ids=(finding_id.value,),
                metadata={
                    "linked_finding_rule": "rule.shared.security",
                    "technology_key": tech_key,
                },
            ),
        ),
    )
    snapshot.publish()
    return assessment, snapshot


def _stack():
    orgs = InMemoryOrganizationRepository()
    workspaces = InMemoryWorkspaceRepository()
    repos = InMemoryRepositoryRepository()
    assessments = InMemoryAssessmentRepository()
    engineering = InMemoryEngineeringSnapshotRepository()
    graphs = InMemoryKnowledgeGraphRepository()
    portfolios = InMemoryPortfolioRepository()
    portfolio_snapshots = InMemoryPortfolioSnapshotRepository()
    executive_intelligence = InMemoryExecutiveIntelligenceRepository()

    org = Organization.create(name="Acme", organization_id=OrganizationId("org:1"))
    workspace = Workspace.create(
        organization_id=org.organization_id,
        name="Main",
        workspace_id=WorkspaceId("workspace:1"),
    )
    orgs.save(org)
    workspaces.save(workspace)

    sources = DefaultPortfolioSourceIntelligenceRepository(
        assessments=assessments,
        snapshots=engineering,
        graphs=graphs,
    )
    management = PortfolioManagementService(
        portfolios=portfolios,
        organizations=orgs,
        workspaces=workspaces,
        repositories=repos,
    )
    portfolio_aggregation = PortfolioIntelligenceAggregationService(
        portfolios=portfolios,
        snapshots=portfolio_snapshots,
        sources=sources,
        organizations=orgs,
        workspaces=workspaces,
    )
    exec_service = ExecutiveIntelligenceAggregationService(
        executive_intelligence=executive_intelligence,
        portfolio_snapshots=portfolio_snapshots,
        portfolios=portfolios,
        organizations=orgs,
        workspaces=workspaces,
    )
    return {
        "org": org,
        "workspace": workspace,
        "repos": repos,
        "assessments": assessments,
        "engineering": engineering,
        "management": management,
        "portfolio_aggregation": portfolio_aggregation,
        "portfolio_snapshots": portfolio_snapshots,
        "executive_intelligence": executive_intelligence,
        "exec_service": exec_service,
    }


def _seed_repository(
    stack,
    *,
    idx: int,
    tech_key: str,
    category: EngineeringCategory = EngineeringCategory.CLOUD,
) -> RepositoryId:
    repo = Repository.register(
        organization_id=stack["org"].organization_id,
        workspace_id=stack["workspace"].workspace_id,
        display_name=f"repo-{idx}",
        provider=RepositoryProvider.GITHUB,
        repository_url=f"https://github.com/acme/repo-{idx}",
        repository_id=RepositoryId(f"repo:{idx}"),
    )
    stack["repos"].save(repo)
    assessment, snapshot = _published(
        org=stack["org"].organization_id,
        workspace=stack["workspace"].workspace_id,
        repo=repo.repository_id,
        assessment_id=f"assessment:{idx}",
        snapshot_id=f"eng-snapshot:{idx}",
        tech_key=tech_key,
        category=category,
    )
    stack["assessments"].save(assessment)
    stack["engineering"].save(snapshot)
    return repo.repository_id


def _build_portfolio(stack, *, repo_ids: list[RepositoryId]) -> PortfolioId:
    created = stack["management"].create_portfolio(
        CreatePortfolioCommand(
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
            name="Platform",
        )
    )
    portfolio_id = PortfolioId(created.summary.portfolio_id)
    for repo_id in repo_ids:
        stack["management"].add_repository(
            AddRepositoryToPortfolioCommand(
                portfolio_id=portfolio_id,
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
                repository_id=repo_id,
            )
        )
    stack["portfolio_aggregation"].build_snapshot(
        BuildPortfolioSnapshotCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    return portfolio_id


def _enable_executive_intelligence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", "true")


def test_disabled_flag_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODESTRATA_EXECUTIVE_INTELLIGENCE_ENABLED", raising=False)
    stack = _stack()
    portfolio_id = _build_portfolio(stack, repo_ids=[])
    with pytest.raises(ExecutiveIntelligenceDisabledError):
        stack["exec_service"].build_intelligence(
            BuildExecutiveIntelligenceCommand(
                portfolio_id=portfolio_id,
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )


def test_empty_portfolio_emits_all_metrics_with_low_confidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    portfolio_id = _build_portfolio(stack, repo_ids=[])

    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    assert {item.key for item in details.metrics} == set(ExecutiveMetricKey)
    for metric in details.metrics:
        assert metric.confidence <= 0.15
    assert details.limitations


def test_single_repo_portfolio_produces_grounded_metrics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="docker")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])

    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    assert {item.key for item in details.metrics} == set(ExecutiveMetricKey)
    risk_metric = next(
        item for item in details.metrics if item.key is ExecutiveMetricKey.PORTFOLIO_RISK
    )
    assert risk_metric.confidence > 0.15


def test_mixed_portfolio_findings_and_recommendations_are_grounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    repo_ids = [
        _seed_repository(stack, idx=1, tech_key="docker"),
        _seed_repository(stack, idx=2, tech_key="podman"),
        _seed_repository(stack, idx=3, tech_key="docker"),
    ]
    portfolio_id = _build_portfolio(stack, repo_ids=repo_ids)

    details = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    known_repo_ids = {item.value for item in repo_ids}
    for finding in details.findings:
        for affected in finding.affected_repository_ids:
            assert affected in known_repo_ids
        assert finding.source_references
        assert finding.evidence or finding.summary

    for recommendation in details.recommendations:
        assert recommendation.rationale
        assert 0.0 <= recommendation.confidence <= 1.0
        assert 0 <= recommendation.priority_score <= 100


def test_tenant_mismatch_raises_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    portfolio_id = _build_portfolio(stack, repo_ids=[])

    other_workspace = WorkspaceId("workspace:other")
    with pytest.raises(ValidationError):
        stack["exec_service"].build_intelligence(
            BuildExecutiveIntelligenceCommand(
                portfolio_id=portfolio_id,
                organization_id=stack["org"].organization_id,
                workspace_id=other_workspace,
            )
        )


def test_build_intelligence_requires_completed_portfolio_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    created = stack["management"].create_portfolio(
        CreatePortfolioCommand(
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
            name="No Snapshot Yet",
        )
    )
    portfolio_id = PortfolioId(created.summary.portfolio_id)
    with pytest.raises(ExecutiveIntelligenceNotReadyError):
        stack["exec_service"].build_intelligence(
            BuildExecutiveIntelligenceCommand(
                portfolio_id=portfolio_id,
                organization_id=stack["org"].organization_id,
                workspace_id=stack["workspace"].workspace_id,
            )
        )


def test_build_intelligence_is_idempotent_for_same_projection_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="docker")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])

    first = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    second = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    assert first.summary.executive_intelligence_id == second.summary.executive_intelligence_id
    assert first.summary.version == second.summary.version


def test_rebuild_supersedes_prior_completed_when_snapshot_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_executive_intelligence(monkeypatch)
    stack = _stack()
    repo_id = _seed_repository(stack, idx=1, tech_key="docker")
    portfolio_id = _build_portfolio(stack, repo_ids=[repo_id])

    first = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )

    other_repo_id = _seed_repository(stack, idx=2, tech_key="podman")
    stack["management"].add_repository(
        AddRepositoryToPortfolioCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
            repository_id=other_repo_id,
        )
    )
    stack["portfolio_aggregation"].rebuild_snapshot(
        RebuildPortfolioSnapshotCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )

    second = stack["exec_service"].build_intelligence(
        BuildExecutiveIntelligenceCommand(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    assert second.summary.executive_intelligence_id != first.summary.executive_intelligence_id

    prior = stack["exec_service"].get(
        GetExecutiveIntelligenceQuery(
            executive_intelligence_id=ExecutiveIntelligenceId(
                first.summary.executive_intelligence_id
            ),
        )
    )
    assert prior.summary.status.value == "superseded"

    latest = stack["exec_service"].get_latest(
        GetLatestExecutiveIntelligenceQuery(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    assert latest.summary.executive_intelligence_id == second.summary.executive_intelligence_id

    listing = stack["exec_service"].list_by_portfolio(
        ListExecutiveIntelligenceQuery(
            portfolio_id=portfolio_id,
            organization_id=stack["org"].organization_id,
            workspace_id=stack["workspace"].workspace_id,
        )
    )
    assert listing.total == 2
