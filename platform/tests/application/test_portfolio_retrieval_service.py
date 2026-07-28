"""Application tests for Portfolio Retrieval indexing and search."""

from __future__ import annotations

import pytest

from codestrata_platform.application.portfolio.commands import (
    AddRepositoryToPortfolioCommand,
    BuildPortfolioSnapshotCommand,
    CreatePortfolioCommand,
)
from codestrata_platform.application.portfolio.services import (
    PortfolioIntelligenceAggregationService,
    PortfolioManagementService,
)
from codestrata_platform.application.portfolio_retrieval.commands import (
    BuildPortfolioRetrievalIndexCommand,
)
from codestrata_platform.application.portfolio_retrieval.errors import (
    PortfolioRetrievalNotReadyError,
)
from codestrata_platform.application.portfolio_retrieval.policies import portfolio_retrieval_enabled
from codestrata_platform.application.portfolio_retrieval.queries import (
    BuildPortfolioRetrievalContextQuery,
    GetPortfolioRetrievalIndexStatisticsQuery,
    SearchPortfolioRetrievalIndexQuery,
)
from codestrata_platform.application.portfolio_retrieval.services import (
    PortfolioRetrievalIndexingService,
)
from codestrata_platform.domain.assessment import Assessment
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering import (
    EngineeringCategory,
    EngineeringFinding,
    EngineeringRecommendation,
    EngineeringSeverity,
    EngineeringSnapshot,
    EngineeringTechnology,
)
from codestrata_platform.domain.engineering.ids import (
    EngineeringFindingId,
    EngineeringRecommendationId,
    EngineeringSnapshotId,
    EngineeringTechnologyId,
)
from codestrata_platform.domain.organization import Organization
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.portfolio_retrieval.identifiers import PortfolioRetrievalIndexId
from codestrata_platform.domain.portfolio_retrieval.lifecycle import RepositoryBalanceMode
from codestrata_platform.domain.portfolio_retrieval.query import PortfolioRetrievalQuery
from codestrata_platform.domain.repository import Repository, RepositoryProvider
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode
from codestrata_platform.domain.workspace import Workspace
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.memory import (
    InMemoryAssessmentRepository,
    InMemoryEngineeringSnapshotRepository,
    InMemoryKnowledgeGraphRepository,
    InMemoryOrganizationRepository,
    InMemoryPortfolioRepository,
    InMemoryPortfolioRetrievalRepository,
    InMemoryPortfolioSnapshotRepository,
    InMemoryRepositoryRepository,
    InMemoryWorkspaceRepository,
)
from codestrata_platform.infrastructure.memory.portfolio_retrieval_sources import (
    DefaultPortfolioRetrievalSourceRepository,
)
from codestrata_platform.infrastructure.memory.portfolio_sources import (
    DefaultPortfolioSourceIntelligenceRepository,
)
from codestrata_platform.infrastructure.portfolio_retrieval import (
    create_portfolio_embedding_provider,
)


def _seed_stack() -> tuple[
    PortfolioManagementService,
    PortfolioIntelligenceAggregationService,
    PortfolioRetrievalIndexingService,
    OrganizationId,
    WorkspaceId,
    tuple[RepositoryId, RepositoryId],
]:
    organizations = InMemoryOrganizationRepository()
    workspaces = InMemoryWorkspaceRepository()
    repositories = InMemoryRepositoryRepository()
    assessments = InMemoryAssessmentRepository()
    engineering = InMemoryEngineeringSnapshotRepository()
    graphs = InMemoryKnowledgeGraphRepository()
    portfolios = InMemoryPortfolioRepository()
    snapshots = InMemoryPortfolioSnapshotRepository()
    embeddings = create_portfolio_embedding_provider()
    indexes = InMemoryPortfolioRetrievalRepository(embeddings=embeddings)

    org = Organization.create(name="Acme", organization_id=OrganizationId("org:pr-app"))
    organizations.save(org)
    workspace = Workspace.create(
        organization_id=org.organization_id,
        name="Main",
        workspace_id=WorkspaceId("workspace:pr-app"),
    )
    workspaces.save(workspace)

    repo_ids: list[RepositoryId] = []
    for idx in range(2):
        repo = Repository.register(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            display_name=f"repo-{idx}",
            provider=RepositoryProvider.GITHUB,
            repository_url=f"https://github.com/acme/pr-app-{idx}",
            repository_id=RepositoryId(f"repo:pr-app-{idx}"),
        )
        repositories.save(repo)
        repo_ids.append(repo.repository_id)
        assessment = Assessment.create(
            repository_id=repo.repository_id,
            workspace_id=workspace.workspace_id,
            engine_version="1.0.0",
            assessment_version="0.1.0",
            assessment_id=AssessmentId(f"assessment:pr-app-{idx}"),
        )
        assessment.start()
        assessment.complete()
        assessments.save(assessment)
        snapshot = EngineeringSnapshot.create(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            repository_id=repo.repository_id,
            assessment_id=assessment.assessment_id,
            assessment_intelligence_id=f"intel:pr-app-{idx}",
            assessment_revision=1,
            version=1,
            source_artifact_ids=("artifact:1",),
            snapshot_id=EngineeringSnapshotId(f"eng-snapshot:pr-app-{idx}"),
        )
        finding_id = EngineeringFindingId(f"eng-finding:pr-app-{idx}")
        snapshot.build(
            technologies=(
                EngineeringTechnology(
                    technology_id=EngineeringTechnologyId(f"eng-tech:pr-app-{idx}"),
                    canonical_key="java",
                    display_name="Java",
                    category=EngineeringCategory.OTHER,
                ),
            ),
            findings=(
                EngineeringFinding(
                    finding_id=finding_id,
                    source_finding_id=f"finding:pr-app-{idx}",
                    category=EngineeringCategory.TECHNICAL_DEBT,
                    severity=EngineeringSeverity.HIGH,
                    title="Debt hotspot",
                    summary="Debt",
                    rule_id="rule.debt",
                    confidence=0.8,
                ),
            ),
            recommendations=(
                EngineeringRecommendation(
                    recommendation_id=EngineeringRecommendationId(f"eng-rec:pr-app-{idx}"),
                    source_recommendation_id="rec:debt",
                    title="Reduce debt",
                    rationale="Refactor",
                    category=EngineeringCategory.TECHNICAL_DEBT,
                    severity=EngineeringSeverity.HIGH,
                    priority="p2",
                    related_finding_ids=(finding_id.value,),
                ),
            ),
        )
        snapshot.publish()
        engineering.save(snapshot)

    sources = DefaultPortfolioSourceIntelligenceRepository(
        assessments=assessments,
        snapshots=engineering,
        graphs=graphs,
    )
    management = PortfolioManagementService(
        portfolios=portfolios,
        organizations=organizations,
        workspaces=workspaces,
        repositories=repositories,
    )
    aggregation = PortfolioIntelligenceAggregationService(
        portfolios=portfolios,
        snapshots=snapshots,
        sources=sources,
        organizations=organizations,
        workspaces=workspaces,
    )
    service = PortfolioRetrievalIndexingService(
        indexes=indexes,
        portfolio_snapshots=snapshots,
        portfolios=portfolios,
        embeddings=embeddings,
        queries=indexes,
        sources=DefaultPortfolioRetrievalSourceRepository(snapshots),
    )
    return (
        management,
        aggregation,
        service,
        org.organization_id,
        workspace.workspace_id,
        (repo_ids[0], repo_ids[1]),
    )


def _build_portfolio_snapshot(
    management: PortfolioManagementService,
    aggregation: PortfolioIntelligenceAggregationService,
    *,
    organization_id: OrganizationId,
    workspace_id: WorkspaceId,
    repository_ids: tuple[RepositoryId, RepositoryId],
) -> PortfolioId:
    created = management.create_portfolio(
        CreatePortfolioCommand(
            organization_id=organization_id,
            workspace_id=workspace_id,
            name="Platform App",
        )
    )
    portfolio_id = PortfolioId(created.summary.portfolio_id)
    for repository_id in repository_ids:
        management.add_repository(
            AddRepositoryToPortfolioCommand(
                organization_id=organization_id,
                workspace_id=workspace_id,
                portfolio_id=portfolio_id,
                repository_id=repository_id,
            )
        )
    aggregation.build_snapshot(
        BuildPortfolioSnapshotCommand(
            organization_id=organization_id,
            workspace_id=workspace_id,
            portfolio_id=portfolio_id,
        )
    )
    return portfolio_id


def test_build_search_and_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    management, aggregation, service, org_id, workspace_id, repo_ids = _seed_stack()
    portfolio_id = _build_portfolio_snapshot(
        management,
        aggregation,
        organization_id=org_id,
        workspace_id=workspace_id,
        repository_ids=repo_ids,
    )
    result = service.build_index(
        BuildPortfolioRetrievalIndexCommand(
            portfolio_id=portfolio_id,
            organization_id=org_id,
            workspace_id=workspace_id,
        )
    )
    assert result.created is True
    assert result.index.status.value == "completed"
    assert result.index.document_count >= 1
    index_id = result.index.index_id

    again = service.build_index(
        BuildPortfolioRetrievalIndexCommand(
            portfolio_id=portfolio_id,
            organization_id=org_id,
            workspace_id=workspace_id,
        )
    )
    assert again.idempotent is True
    assert again.index.index_id == index_id

    search = service.search(
        SearchPortfolioRetrievalIndexQuery(
            index_id=PortfolioRetrievalIndexId(index_id),
            query=PortfolioRetrievalQuery(
                query_text="debt hotspot",
                mode=RetrievalMode.HYBRID,
                top_k=5,
                repository_balance_mode=RepositoryBalanceMode.DIVERSIFIED,
            ),
            organization_id=org_id,
            workspace_id=workspace_id,
        )
    )
    assert search.hits
    assert search.hits[0].score.final_score >= 0.0

    context = service.assemble_context(
        BuildPortfolioRetrievalContextQuery(
            index_id=PortfolioRetrievalIndexId(index_id),
            query_text="debt hotspot modernization",
            organization_id=org_id,
            workspace_id=workspace_id,
            mode=RetrievalMode.HYBRID,
            top_k=5,
            repository_balance_mode=RepositoryBalanceMode.DIVERSIFIED,
        )
    )
    assert context.items
    stats = service.statistics(
        GetPortfolioRetrievalIndexStatisticsQuery(
            index_id=PortfolioRetrievalIndexId(index_id),
        )
    )
    assert stats.embedded_chunk_count >= 1
    assert stats.repository_count == 2


def test_portfolio_retrieval_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", raising=False)
    assert portfolio_retrieval_enabled() is False
    management, aggregation, service, org_id, workspace_id, repo_ids = _seed_stack()
    portfolio_id = _build_portfolio_snapshot(
        management,
        aggregation,
        organization_id=org_id,
        workspace_id=workspace_id,
        repository_ids=repo_ids,
    )
    with pytest.raises(PortfolioRetrievalNotReadyError):
        service.build_index(
            BuildPortfolioRetrievalIndexCommand(
                portfolio_id=portfolio_id,
                organization_id=org_id,
                workspace_id=workspace_id,
            )
        )
