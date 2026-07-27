"""Gap-closure tests for Phase 8.6.2 Portfolio Retrieval audit findings."""

from __future__ import annotations

import pytest

from codestrata_platform.application.common.errors import ValidationError
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
    RebuildPortfolioRetrievalIndexCommand,
)
from codestrata_platform.application.portfolio_retrieval.context import (
    PortfolioRetrievalContextAssembler,
)
from codestrata_platform.application.portfolio_retrieval.errors import (
    PortfolioRetrievalConfigurationError,
)
from codestrata_platform.application.portfolio_retrieval.queries import (
    SearchPortfolioRetrievalIndexQuery,
)
from codestrata_platform.application.portfolio_retrieval.ranking import apply_repository_balance
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
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio_retrieval.citation import PortfolioRetrievalCitation
from codestrata_platform.domain.portfolio_retrieval.document import PortfolioRetrievalDocument
from codestrata_platform.domain.portfolio_retrieval.errors import PortfolioRetrievalInvariantError
from codestrata_platform.domain.portfolio_retrieval.identifiers import (
    EmbeddingDimension,
    EmbeddingModelId,
    EmbeddingProviderId,
    PortfolioContextId,
    PortfolioRetrievalIndexId,
    PortfolioRetrievalProjectionKey,
    deterministic_portfolio_chunk_id,
    deterministic_portfolio_document_id,
    deterministic_portfolio_index_id,
)
from codestrata_platform.domain.portfolio_retrieval.index import PortfolioRetrievalIndex
from codestrata_platform.domain.portfolio_retrieval.lifecycle import (
    PortfolioRetrievalIndexStatus,
    RepositoryBalanceMode,
)
from codestrata_platform.domain.portfolio_retrieval.query import (
    PortfolioRetrievalQuery,
    PortfolioRetrievalScore,
)
from codestrata_platform.domain.portfolio_retrieval.result import PortfolioRetrievalHit
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType
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


def _stack(*, auto_index: bool = False):
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

    org = Organization.create(name="Acme", organization_id=OrganizationId("org:gap"))
    workspace = Workspace.create(
        organization_id=org.organization_id,
        name="Main",
        workspace_id=WorkspaceId("workspace:gap"),
    )
    organizations.save(org)
    workspaces.save(workspace)

    repo_ids: list[RepositoryId] = []
    for idx in range(2):
        repo = Repository.register(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            display_name=f"repo-{idx}",
            provider=RepositoryProvider.GITHUB,
            repository_url=f"https://github.com/acme/gap-{idx}",
            repository_id=RepositoryId(f"repo:gap-{idx}"),
        )
        repositories.save(repo)
        repo_ids.append(repo.repository_id)
        assessment = Assessment.create(
            repository_id=repo.repository_id,
            workspace_id=workspace.workspace_id,
            engine_version="1.0.0",
            assessment_version="0.1.0",
            assessment_id=AssessmentId(f"assessment:gap-{idx}"),
        )
        assessment.start()
        assessment.complete()
        assessments.save(assessment)
        snapshot = EngineeringSnapshot.create(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            repository_id=repo.repository_id,
            assessment_id=assessment.assessment_id,
            assessment_intelligence_id=f"intel:gap-{idx}",
            assessment_revision=1,
            version=1,
            source_artifact_ids=("artifact:1",),
            snapshot_id=EngineeringSnapshotId(f"eng-snapshot:gap-{idx}"),
        )
        finding_id = EngineeringFindingId(f"eng-finding:gap-{idx}")
        snapshot.build(
            technologies=(
                EngineeringTechnology(
                    technology_id=EngineeringTechnologyId(f"eng-tech:gap-{idx}"),
                    canonical_key="java",
                    display_name="Java",
                    category=EngineeringCategory.OTHER,
                ),
            ),
            findings=(
                EngineeringFinding(
                    finding_id=finding_id,
                    source_finding_id=f"finding:gap-{idx}",
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
                    recommendation_id=EngineeringRecommendationId(f"eng-rec:gap-{idx}"),
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

    retrieval = PortfolioRetrievalIndexingService(
        indexes=indexes,
        portfolio_snapshots=snapshots,
        portfolios=portfolios,
        embeddings=embeddings,
        queries=indexes,
        sources=DefaultPortfolioRetrievalSourceRepository(snapshots),
    )
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
        on_snapshot_completed=(
            retrieval.maybe_auto_index_for_portfolio_snapshot if auto_index else None
        ),
    )
    return (
        management,
        aggregation,
        retrieval,
        indexes,
        org.organization_id,
        workspace.workspace_id,
        (repo_ids[0], repo_ids[1]),
        embeddings,
    )


def _create_portfolio_snapshot(management, aggregation, org_id, workspace_id, repo_ids):
    created = management.create_portfolio(
        CreatePortfolioCommand(
            organization_id=org_id,
            workspace_id=workspace_id,
            name="Gap Portfolio",
        )
    )
    portfolio_id = PortfolioId(created.summary.portfolio_id)
    for repository_id in repo_ids:
        management.add_repository(
            AddRepositoryToPortfolioCommand(
                organization_id=org_id,
                workspace_id=workspace_id,
                portfolio_id=portfolio_id,
                repository_id=repository_id,
            )
        )
    details = aggregation.build_snapshot(
        BuildPortfolioSnapshotCommand(
            organization_id=org_id,
            workspace_id=workspace_id,
            portfolio_id=portfolio_id,
        )
    )
    return portfolio_id, PortfolioSnapshotId(details.summary.portfolio_snapshot_id)


def test_failed_rebuild_preserves_prior_completed_index(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    management, aggregation, service, indexes, org_id, workspace_id, repo_ids, embeddings = _stack()
    portfolio_id, _ = _create_portfolio_snapshot(
        management, aggregation, org_id, workspace_id, repo_ids
    )
    first = service.build_index(
        BuildPortfolioRetrievalIndexCommand(
            portfolio_id=portfolio_id,
            organization_id=org_id,
            workspace_id=workspace_id,
        )
    )
    assert first.created is True
    prior_id = first.index.index_id

    def _boom(_texts):
        raise RuntimeError("embedding failure")

    monkeypatch.setattr(embeddings, "embed_batch", _boom)
    with pytest.raises(ValidationError):
        service.build_index(
            BuildPortfolioRetrievalIndexCommand(
                portfolio_id=portfolio_id,
                organization_id=org_id,
                workspace_id=workspace_id,
                force=True,
            )
        )
    latest = indexes.get_latest_completed(portfolio_id)
    assert latest is not None
    assert latest.index_id.value == prior_id
    assert latest.status is PortfolioRetrievalIndexStatus.COMPLETED


def test_repository_filter_rejects_outside_portfolio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    management, aggregation, service, _, org_id, workspace_id, repo_ids, _ = _stack()
    portfolio_id, _ = _create_portfolio_snapshot(
        management, aggregation, org_id, workspace_id, repo_ids
    )
    built = service.build_index(
        BuildPortfolioRetrievalIndexCommand(
            portfolio_id=portfolio_id,
            organization_id=org_id,
            workspace_id=workspace_id,
        )
    )
    with pytest.raises(ValidationError) as exc:
        service.search(
            SearchPortfolioRetrievalIndexQuery(
                index_id=PortfolioRetrievalIndexId(built.index.index_id),
                query=PortfolioRetrievalQuery(
                    query_text="debt",
                    repository_ids=(RepositoryId("repo:outside"),),
                ),
            )
        )
    assert exc.value.reason_code == "portfolio_retrieval_repository_outside_portfolio"


def test_frozen_supporting_context_and_citations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    management, aggregation, service, indexes, org_id, workspace_id, repo_ids, _ = _stack()
    portfolio_id, _ = _create_portfolio_snapshot(
        management, aggregation, org_id, workspace_id, repo_ids
    )
    built = service.build_index(
        BuildPortfolioRetrievalIndexCommand(
            portfolio_id=portfolio_id,
            organization_id=org_id,
            workspace_id=workspace_id,
        )
    )
    index = indexes.get(PortfolioRetrievalIndexId(built.index.index_id))
    assert index is not None
    supporting = [
        item
        for item in index.documents
        if item.content_type is PortfolioRetrievalContentType.REPOSITORY_SUPPORTING_CONTEXT
    ]
    assert len(supporting) == 2
    for document in supporting:
        assert document.citations
        assert document.citations[0].engineering_snapshot_id
        assert document.citations[0].repository_id
        assert document.structured_content["engineering_snapshot_id"]


def test_balance_applied_once_and_contributions_present(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    management, aggregation, service, _, org_id, workspace_id, repo_ids, _ = _stack()
    portfolio_id, _ = _create_portfolio_snapshot(
        management, aggregation, org_id, workspace_id, repo_ids
    )
    built = service.build_index(
        BuildPortfolioRetrievalIndexCommand(
            portfolio_id=portfolio_id,
            organization_id=org_id,
            workspace_id=workspace_id,
        )
    )
    result = service.search(
        SearchPortfolioRetrievalIndexQuery(
            index_id=PortfolioRetrievalIndexId(built.index.index_id),
            query=PortfolioRetrievalQuery(
                query_text="debt hotspot",
                mode=RetrievalMode.HYBRID,
                top_k=10,
                repository_balance_mode=RepositoryBalanceMode.DIVERSIFIED,
            ),
        )
    )
    assert result.hits
    assert result.hits[0].repository_contributions
    assert all(hit.score.balance_adjustment <= 0.0 for hit in result.hits)


def test_embedding_provider_mismatch_fails_clearly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    management, aggregation, service, _, org_id, workspace_id, repo_ids, _ = _stack()
    portfolio_id, _ = _create_portfolio_snapshot(
        management, aggregation, org_id, workspace_id, repo_ids
    )
    with pytest.raises(PortfolioRetrievalConfigurationError):
        service.build_index(
            BuildPortfolioRetrievalIndexCommand(
                portfolio_id=portfolio_id,
                organization_id=org_id,
                workspace_id=workspace_id,
                embedding_provider="openai",
            )
        )


def test_cross_portfolio_document_rejected() -> None:
    projection = PortfolioRetrievalProjectionKey.from_parts(
        portfolio_id="portfolio:1",
        portfolio_snapshot_id="portfolio-snapshot:1",
        portfolio_snapshot_version=1,
        selected_repository_snapshot_identities=("repo:1:eng:1:1::0",),
        retrieval_schema_version="1.0",
        chunking_policy_version="1.0.0",
        ranking_policy_version="1.0.0",
        embedding_provider_id="deterministic",
        embedding_model_id="deterministic-test-embedding",
        embedding_dimension=384,
    )
    index = PortfolioRetrievalIndex.create_pending(
        index_id=deterministic_portfolio_index_id(
            portfolio_id="portfolio:1",
            portfolio_snapshot_id="portfolio-snapshot:1",
            projection_key=projection.value,
        ),
        organization_id=OrganizationId("org:1"),
        workspace_id=WorkspaceId("workspace:1"),
        portfolio_id=PortfolioId("portfolio:1"),
        portfolio_snapshot_id=PortfolioSnapshotId("portfolio-snapshot:1"),
        portfolio_snapshot_version=1,
        index_version=1,
        projection_key=projection,
        retrieval_schema_version="1.0",
        chunking_policy_version="1.0.0",
        ranking_policy_version="1.0.0",
        embedding_provider_id=EmbeddingProviderId("deterministic"),
        embedding_model_id=EmbeddingModelId("deterministic-test-embedding"),
        embedding_dimension=EmbeddingDimension(384),
    )
    index.begin_indexing()
    citation = PortfolioRetrievalCitation(
        source_kind="portfolio_snapshot",
        source_id="portfolio-snapshot:2",
        portfolio_snapshot_id="portfolio-snapshot:2",
    )
    foreign = PortfolioRetrievalDocument(
        document_id=deterministic_portfolio_document_id(
            index_id=index.index_id.value,
            content_type=PortfolioRetrievalContentType.PORTFOLIO_SUMMARY.value,
            canonical_id="foreign",
        ),
        index_id=index.index_id,
        portfolio_id=PortfolioId("portfolio:other"),
        portfolio_snapshot_id=PortfolioSnapshotId("portfolio-snapshot:2"),
        content_type=PortfolioRetrievalContentType.PORTFOLIO_SUMMARY,
        canonical_type="portfolio",
        canonical_id="foreign",
        title="Foreign",
        summary="Foreign portfolio document",
        citations=(citation,),
    )
    with pytest.raises(PortfolioRetrievalInvariantError):
        index.add_document(foreign)


def test_context_discloses_unavailable_and_limits() -> None:
    hit = PortfolioRetrievalHit(
        result_id=PortfolioContextId("portfolio-retrieval-hit:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
        chunk_id=deterministic_portfolio_chunk_id(
            document_id="portfolio-retrieval-doc:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            ordinal=0,
            checksum="b" * 64,
        ),
        document_id=deterministic_portfolio_document_id(
            index_id="portfolio-retrieval:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            content_type=PortfolioRetrievalContentType.SYSTEMIC_RISK.value,
            canonical_id="risk:1",
        ),
        content_type=PortfolioRetrievalContentType.SYSTEMIC_RISK,
        canonical_type="systemic_risk",
        canonical_id="risk:1",
        title="Systemic risk",
        text="Systemic risk across repositories.",
        score=PortfolioRetrievalScore(final_score=0.9, systemic_score=1.0),
        repository_ids=(RepositoryId("repo:1"), RepositoryId("repo:2")),
        primary_repository_id=RepositoryId("repo:1"),
        citations=(
            PortfolioRetrievalCitation(
                source_kind="portfolio_snapshot",
                source_id="portfolio-snapshot:1",
                portfolio_snapshot_id="portfolio-snapshot:1",
            ),
        ),
    )
    context = PortfolioRetrievalContextAssembler().assemble(
        (hit,),
        max_tokens=50,
        max_repositories=1,
        unavailable_repos=("repo:2",),
        stale_repos=("repo:1",),
    )
    kinds = {item.kind for item in context.diagnostics}
    assert "unavailable_repository" in kinds
    assert "stale_repository" in kinds
    assert "excluded_repository" in kinds or context.truncated is True


def test_force_rebuild_replaces_completed_index(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    management, aggregation, service, indexes, org_id, workspace_id, repo_ids, _ = _stack()
    portfolio_id, _ = _create_portfolio_snapshot(
        management, aggregation, org_id, workspace_id, repo_ids
    )
    first = service.build_index(
        BuildPortfolioRetrievalIndexCommand(
            portfolio_id=portfolio_id,
            organization_id=org_id,
            workspace_id=workspace_id,
        )
    )
    rebuilt = service.rebuild_index(
        RebuildPortfolioRetrievalIndexCommand(
            index_id=PortfolioRetrievalIndexId(first.index.index_id),
            force=True,
        )
    )
    assert rebuilt.created is True
    latest = indexes.get_latest_completed(portfolio_id)
    assert latest is not None
    assert latest.index_id.value == rebuilt.index.index_id


def test_auto_index_success_and_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", raising=False)
    management, aggregation, service, indexes, org_id, workspace_id, repo_ids, _ = _stack(
        auto_index=True
    )
    portfolio_id, snapshot_id = _create_portfolio_snapshot(
        management, aggregation, org_id, workspace_id, repo_ids
    )
    assert indexes.get_latest_completed(portfolio_id) is None
    assert service.maybe_auto_index_for_portfolio_snapshot(snapshot_id) is None

    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    result = service.maybe_auto_index_for_portfolio_snapshot(snapshot_id)
    assert result is not None
    assert result.created is True


def test_repository_balance_is_idempotent() -> None:
    hit = PortfolioRetrievalHit(
        result_id=PortfolioContextId("portfolio-retrieval-hit:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
        chunk_id=deterministic_portfolio_chunk_id(
            document_id="portfolio-retrieval-doc:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            ordinal=0,
            checksum="c" * 64,
        ),
        document_id=deterministic_portfolio_document_id(
            index_id="portfolio-retrieval:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            content_type=PortfolioRetrievalContentType.REPOSITORY_PROFILE.value,
            canonical_id="repo:1",
        ),
        content_type=PortfolioRetrievalContentType.REPOSITORY_PROFILE,
        canonical_type="repository",
        canonical_id="repo:1",
        title="Repo",
        text="Repository profile",
        score=PortfolioRetrievalScore(final_score=0.8, repository_score=1.0),
        repository_ids=(RepositoryId("repo:1"),),
        primary_repository_id=RepositoryId("repo:1"),
        citations=(
            PortfolioRetrievalCitation(
                source_kind="repository_profile",
                source_id="repo:1",
                repository_id="repo:1",
            ),
        ),
    )
    once = apply_repository_balance((hit,), RepositoryBalanceMode.DIVERSIFIED)
    twice = apply_repository_balance(once, RepositoryBalanceMode.DIVERSIFIED)
    # Second application on already-adjusted scores should not double-penalize the first hit.
    assert once[0].score.balance_adjustment == 0.0
    assert twice[0].score.balance_adjustment == 0.0
