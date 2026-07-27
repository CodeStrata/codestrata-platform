"""PostgreSQL persistence smoke tests for Portfolio Retrieval indexes."""

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
from codestrata_platform.application.portfolio_retrieval.queries import (
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
from codestrata_platform.domain.portfolio.identifiers import PortfolioId
from codestrata_platform.domain.portfolio_retrieval.identifiers import PortfolioRetrievalIndexId
from codestrata_platform.domain.portfolio_retrieval.query import PortfolioRetrievalQuery
from codestrata_platform.domain.portfolio_retrieval.scope import PortfolioRetrievalScope
from codestrata_platform.domain.repository import Repository, RepositoryProvider
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.taxonomy import RetrievalMode
from codestrata_platform.domain.workspace import Workspace
from codestrata_platform.infrastructure.memory.portfolio_retrieval_sources import (
    DefaultPortfolioRetrievalSourceRepository,
)
from codestrata_platform.infrastructure.memory.portfolio_sources import (
    DefaultPortfolioSourceIntelligenceRepository,
)
from codestrata_platform.infrastructure.persistence.repositories import (
    SqlAlchemyAssessmentRepository,
    SqlAlchemyEngineeringSnapshotRepository,
    SqlAlchemyKnowledgeGraphRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyPortfolioRepository,
    SqlAlchemyPortfolioRetrievalRepository,
    SqlAlchemyPortfolioSnapshotRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyWorkspaceRepository,
)
from codestrata_platform.infrastructure.portfolio_retrieval import (
    create_portfolio_embedding_provider,
)

pytestmark = pytest.mark.usefixtures("session")


def test_portfolio_retrieval_round_trip(session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    embeddings = create_portfolio_embedding_provider()

    org_repo = SqlAlchemyOrganizationRepository(session)
    workspace_repo = SqlAlchemyWorkspaceRepository(session)
    repository_repo = SqlAlchemyRepositoryRepository(session)
    assessment_repo = SqlAlchemyAssessmentRepository(session)
    engineering_repo = SqlAlchemyEngineeringSnapshotRepository(session)
    graph_repo = SqlAlchemyKnowledgeGraphRepository(session)
    portfolio_repo = SqlAlchemyPortfolioRepository(session)
    snapshot_repo = SqlAlchemyPortfolioSnapshotRepository(session)
    retrieval_repo = SqlAlchemyPortfolioRetrievalRepository(session, embeddings=embeddings)

    org = Organization.create(name="Acme PR Persist")
    org_repo.save(org)
    workspace = Workspace.create(organization_id=org.organization_id, name="Main")
    workspace_repo.save(workspace)

    repo_ids: list[RepositoryId] = []
    for idx in range(2):
        repo = Repository.register(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            display_name=f"repo-{idx}",
            provider=RepositoryProvider.GITHUB,
            repository_url=f"https://github.com/acme/pr-persist-{idx}",
        )
        repository_repo.save(repo)
        repo_ids.append(repo.repository_id)
        assessment = Assessment.create(
            repository_id=repo.repository_id,
            workspace_id=workspace.workspace_id,
            engine_version="1.0.0",
            assessment_version="0.1.0",
            assessment_id=AssessmentId(f"assessment:pr-persist-{idx}"),
        )
        assessment.start()
        assessment.complete()
        assessment_repo.save(assessment)
        snapshot = EngineeringSnapshot.create(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            repository_id=repo.repository_id,
            assessment_id=assessment.assessment_id,
            assessment_intelligence_id=f"intel:pr-persist-{idx}",
            assessment_revision=1,
            version=1,
            source_artifact_ids=("artifact:1",),
            snapshot_id=EngineeringSnapshotId(f"eng-snapshot:pr-persist-{idx}"),
        )
        finding_id = EngineeringFindingId(f"eng-finding:pr-persist-{idx}")
        snapshot.build(
            technologies=(
                EngineeringTechnology(
                    technology_id=EngineeringTechnologyId(f"eng-tech:pr-persist-{idx}"),
                    canonical_key="java",
                    display_name="Java",
                    category=EngineeringCategory.OTHER,
                ),
            ),
            findings=(
                EngineeringFinding(
                    finding_id=finding_id,
                    source_finding_id=f"finding:pr-persist-{idx}",
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
                    recommendation_id=EngineeringRecommendationId(f"eng-rec:pr-persist-{idx}"),
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
        engineering_repo.save(snapshot)

    sources = DefaultPortfolioSourceIntelligenceRepository(
        assessments=assessment_repo,
        snapshots=engineering_repo,
        graphs=graph_repo,
    )
    management = PortfolioManagementService(
        portfolios=portfolio_repo,
        organizations=org_repo,
        workspaces=workspace_repo,
        repositories=repository_repo,
    )
    aggregation = PortfolioIntelligenceAggregationService(
        portfolios=portfolio_repo,
        snapshots=snapshot_repo,
        sources=sources,
        organizations=org_repo,
        workspaces=workspace_repo,
    )
    service = PortfolioRetrievalIndexingService(
        indexes=retrieval_repo,
        portfolio_snapshots=snapshot_repo,
        portfolios=portfolio_repo,
        embeddings=embeddings,
        queries=retrieval_repo,
        sources=DefaultPortfolioRetrievalSourceRepository(snapshot_repo),
    )

    created = management.create_portfolio(
        CreatePortfolioCommand(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            name="Persist Portfolio",
        )
    )
    portfolio_id = PortfolioId(created.summary.portfolio_id)
    for repository_id in repo_ids:
        management.add_repository(
            AddRepositoryToPortfolioCommand(
                organization_id=org.organization_id,
                workspace_id=workspace.workspace_id,
                portfolio_id=portfolio_id,
                repository_id=repository_id,
            )
        )
    aggregation.build_snapshot(
        BuildPortfolioSnapshotCommand(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            portfolio_id=portfolio_id,
        )
    )
    session.commit()

    result = service.build_index(
        BuildPortfolioRetrievalIndexCommand(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    session.commit()
    assert result.created is True
    index_id = PortfolioRetrievalIndexId(result.index.index_id)

    loaded = retrieval_repo.get(index_id)
    assert loaded is not None
    assert loaded.status.value == "completed"
    assert len(loaded.documents) >= 1
    assert len(loaded.chunks) >= 1

    search = service.search(
        SearchPortfolioRetrievalIndexQuery(
            index_id=index_id,
            query=PortfolioRetrievalQuery(
                query_text="debt hotspot",
                mode=RetrievalMode.HYBRID,
                top_k=5,
            ),
        )
    )
    assert search.hits

    scope = PortfolioRetrievalScope(
        organization_id=org.organization_id,
        workspace_id=workspace.workspace_id,
        portfolio_id=portfolio_id,
        portfolio_snapshot_id=loaded.portfolio_snapshot_id,
        repository_ids=loaded.repository_ids,
    )
    direct = retrieval_repo.search(
        index_id,
        PortfolioRetrievalQuery(query_text="debt", mode=RetrievalMode.LEXICAL, top_k=3),
        scope=scope,
    )
    assert direct.hits
