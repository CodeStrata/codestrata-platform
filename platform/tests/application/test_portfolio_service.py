"""Application tests for portfolio aggregation."""

from __future__ import annotations

from codestrata_platform.application.portfolio.commands import (
    AddRepositoryToPortfolioCommand,
    BuildPortfolioSnapshotCommand,
    CreatePortfolioCommand,
)
from codestrata_platform.application.portfolio.queries import (
    GetLatestPortfolioSnapshotQuery,
    PortfolioInventoryQuery,
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
from codestrata_platform.domain.organization import Organization
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio.lifecycle import (
    DependencySignalType,
    RepositoryAvailabilityStatus,
    TechnologyStandardizationStatus,
)
from codestrata_platform.domain.repository import Repository, RepositoryProvider
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace import Workspace
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.memory import (
    InMemoryAssessmentRepository,
    InMemoryEngineeringSnapshotRepository,
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
    tech_capability: str,
    rule_id: str = "rule.shared.security",
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
                category=EngineeringCategory.CLOUD,
                metadata={"capability": tech_capability},
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
                rule_id=rule_id,
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
                metadata={"linked_finding_rule": rule_id, "technology_key": tech_key},
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
    snapshots = InMemoryPortfolioSnapshotRepository()

    org = Organization.create(name="Acme", organization_id=OrganizationId("org:1"))
    workspace = Workspace.create(
        organization_id=org.organization_id,
        name="Main",
        workspace_id=WorkspaceId("workspace:1"),
    )
    orgs.save(org)
    workspaces.save(workspace)

    repo_ids = []
    for idx, (tech, capability) in enumerate(
        (("docker", "runtime"), ("podman", "runtime"), ("docker", "runtime")),
        start=1,
    ):
        repo = Repository.register(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            display_name=f"repo-{idx}",
            provider=RepositoryProvider.GITHUB,
            repository_url=f"https://github.com/acme/repo-{idx}",
            repository_id=RepositoryId(f"repo:{idx}"),
        )
        repos.save(repo)
        repo_ids.append(repo.repository_id)
        assessment, snapshot = _published(
            org=org.organization_id,
            workspace=workspace.workspace_id,
            repo=repo.repository_id,
            assessment_id=f"assessment:{idx}",
            snapshot_id=f"eng-snapshot:{idx}",
            tech_key=tech,
            tech_capability=capability,
        )
        assessments.save(assessment)
        engineering.save(snapshot)

    empty = Repository.register(
        organization_id=org.organization_id,
        workspace_id=workspace.workspace_id,
        display_name="repo-empty",
        provider=RepositoryProvider.GITHUB,
        repository_url="https://github.com/acme/repo-empty",
        repository_id=RepositoryId("repo:empty"),
    )
    repos.save(empty)
    repo_ids.append(empty.repository_id)

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
    aggregation = PortfolioIntelligenceAggregationService(
        portfolios=portfolios,
        snapshots=snapshots,
        sources=sources,
        organizations=orgs,
        workspaces=workspaces,
    )
    return management, aggregation, org, workspace, repo_ids


def test_portfolio_build_aggregates_deterministically() -> None:
    management, aggregation, org, workspace, repo_ids = _stack()
    created = management.create_portfolio(
        CreatePortfolioCommand(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            name="Platform",
        )
    )
    portfolio_id = PortfolioId(created.summary.portfolio_id)
    for repo_id in repo_ids:
        management.add_repository(
            AddRepositoryToPortfolioCommand(
                portfolio_id=portfolio_id,
                organization_id=org.organization_id,
                workspace_id=workspace.workspace_id,
                repository_id=repo_id,
            )
        )

    first = aggregation.build_snapshot(
        BuildPortfolioSnapshotCommand(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    second = aggregation.build_snapshot(
        BuildPortfolioSnapshotCommand(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    assert first.summary.portfolio_snapshot_id == second.summary.portfolio_snapshot_id
    assert first.summary.unavailable_repository_count == 1
    assert first.summary.available_repository_count == 3
    unavailable = [
        item
        for item in first.repository_selections
        if item.availability_status is RepositoryAvailabilityStatus.UNAVAILABLE
    ]
    assert len(unavailable) == 1
    assert unavailable[0].repository_id.value == "repo:empty"

    snapshot_id = PortfolioSnapshotId(first.summary.portfolio_snapshot_id)
    techs = aggregation.get_technologies(
        PortfolioInventoryQuery(
            portfolio_snapshot_id=snapshot_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    by_key = {item.canonical_key: item for item in techs.items}
    assert "docker" in by_key
    assert by_key["docker"].repository_count == 2
    assert (
        by_key["docker"].standardization_status is TechnologyStandardizationStatus.FRAGMENTED
        or by_key["podman"].standardization_status is TechnologyStandardizationStatus.FRAGMENTED
    )

    findings = aggregation.get_findings(
        PortfolioInventoryQuery(
            portfolio_snapshot_id=snapshot_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    assert findings.summary.recurring_patterns
    assert findings.summary.recurring_patterns[0].repository_count >= 2

    overview = aggregation.get_overview(
        PortfolioInventoryQuery(
            portfolio_snapshot_id=snapshot_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    assert overview.coverage.repositories_unavailable == 1
    shared = [
        signal
        for signal in overview.dependencies.signals
        if signal.signal_type is DependencySignalType.SHARED_TECHNOLOGY
    ]
    explicit = [
        signal
        for signal in overview.dependencies.signals
        if signal.signal_type is DependencySignalType.EXPLICIT_REPOSITORY_DEPENDENCY
    ]
    assert shared
    assert not explicit
    assert overview.risk.systemic_risks
    assert overview.modernization.candidates

    latest = aggregation.get_latest_snapshot(
        GetLatestPortfolioSnapshotQuery(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    assert latest.summary.portfolio_snapshot_id == first.summary.portfolio_snapshot_id
