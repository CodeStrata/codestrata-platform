"""FastAPI dependency wiring for Application Services."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from codestrata_platform.application.answering import EngineeringAnswerOrchestrationService
from codestrata_platform.application.artifact import DefaultArtifactService
from codestrata_platform.application.assessment import DefaultAssessmentService
from codestrata_platform.application.engineering import EngineeringNormalizationService
from codestrata_platform.application.intelligence import DefaultAssessmentIntelligenceService
from codestrata_platform.application.intelligence.service import DefaultAssessmentArtifactReader
from codestrata_platform.application.knowledge_graph import EngineeringGraphProjectionService
from codestrata_platform.application.knowledge_graph.intelligence import GraphIntelligenceFacade
from codestrata_platform.application.organization import DefaultOrganizationService
from codestrata_platform.application.portfolio import (
    PortfolioIntelligenceAggregationService,
    PortfolioManagementService,
    PortfolioServiceFacade,
)
from codestrata_platform.application.portfolio.policies import portfolio_auto_refresh_enabled
from codestrata_platform.application.portfolio_answering import PortfolioAnswerOrchestrationService
from codestrata_platform.application.portfolio_retrieval import PortfolioRetrievalIndexingService
from codestrata_platform.application.repository import DefaultRepositoryService
from codestrata_platform.application.retrieval import EngineeringRetrievalIndexingService
from codestrata_platform.application.workspace import DefaultWorkspaceService
from codestrata_platform.domain.artifact import ArtifactStorage
from codestrata_platform.infrastructure.answering import create_llm_provider
from codestrata_platform.infrastructure.memory import (
    InMemoryAnswerRunRepository,
    InMemoryArtifactRepository,
    InMemoryAssessmentIntelligenceRepository,
    InMemoryAssessmentRepository,
    InMemoryEngineeringSnapshotRepository,
    InMemoryFindingRepository,
    InMemoryGraphIntelligenceRepository,
    InMemoryKnowledgeGraphRepository,
    InMemoryMetricRepository,
    InMemoryOrganizationRepository,
    InMemoryPortfolioAnswerRunRepository,
    InMemoryPortfolioRepository,
    InMemoryPortfolioRetrievalRepository,
    InMemoryPortfolioSnapshotRepository,
    InMemoryRecommendationRepository,
    InMemoryRepositoryRepository,
    InMemoryRetrievalRepository,
    InMemoryWorkspaceRepository,
)
from codestrata_platform.infrastructure.memory.portfolio_retrieval_sources import (
    DefaultPortfolioRetrievalSourceRepository,
)
from codestrata_platform.infrastructure.memory.portfolio_sources import (
    DefaultPortfolioSourceIntelligenceRepository,
)
from codestrata_platform.infrastructure.persistence.repositories import (
    SqlAlchemyAnswerRunRepository,
    SqlAlchemyAssessmentArtifactRepository,
    SqlAlchemyAssessmentIntelligenceRepository,
    SqlAlchemyAssessmentRepository,
    SqlAlchemyEngineeringSnapshotRepository,
    SqlAlchemyFindingRepository,
    SqlAlchemyGraphIntelligenceRepository,
    SqlAlchemyKnowledgeGraphRepository,
    SqlAlchemyMetricRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyPortfolioAnswerRunRepository,
    SqlAlchemyPortfolioRepository,
    SqlAlchemyPortfolioRetrievalRepository,
    SqlAlchemyPortfolioSnapshotRepository,
    SqlAlchemyRecommendationRepository,
    SqlAlchemyRepositoryRepository,
    SqlAlchemyRetrievalIndexRepository,
    SqlAlchemyWorkspaceRepository,
)
from codestrata_platform.infrastructure.portfolio_retrieval import (
    create_portfolio_embedding_provider,
)
from codestrata_platform.infrastructure.retrieval import create_embedding_provider
from codestrata_platform.infrastructure.storage import (
    FileSystemArtifactStorage,
    InMemoryArtifactStorage,
)


@dataclass(slots=True)
class ApiServices:
    """Request-scoped Application service bundle."""

    organizations: DefaultOrganizationService
    workspaces: DefaultWorkspaceService
    repositories: DefaultRepositoryService
    assessments: DefaultAssessmentService
    artifacts: DefaultArtifactService
    intelligence: DefaultAssessmentIntelligenceService
    engineering: EngineeringNormalizationService
    knowledge_graphs: EngineeringGraphProjectionService
    graph_intelligence: GraphIntelligenceFacade
    retrieval: EngineeringRetrievalIndexingService
    answering: EngineeringAnswerOrchestrationService
    portfolio: PortfolioServiceFacade
    portfolio_retrieval: PortfolioRetrievalIndexingService
    portfolio_answering: PortfolioAnswerOrchestrationService
    _session: Session | None = None
    _committed: bool = False

    def commit(self) -> None:
        if self._session is not None and not self._committed:
            self._session.commit()
            self._committed = True

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()


def _build_portfolio_facade(
    *,
    portfolios,
    snapshots,
    assessments,
    engineering,
    knowledge_graphs,
    retrieval_indexes,
    organizations,
    workspaces,
    repositories,
    on_snapshot_completed=None,
) -> PortfolioServiceFacade:
    sources = DefaultPortfolioSourceIntelligenceRepository(
        assessments=assessments,
        snapshots=engineering,
        graphs=knowledge_graphs,
        retrieval_indexes=retrieval_indexes,
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
        auto_refresh_enabled=portfolio_auto_refresh_enabled(),
        on_snapshot_completed=on_snapshot_completed,
    )
    return PortfolioServiceFacade(management=management, aggregation=aggregation)


def _chain_snapshot_published(*, knowledge_graphs, retrieval, portfolio=None, engineering=None):
    def _on_published(snapshot_id):
        try:
            knowledge_graphs.maybe_auto_project_for_snapshot(snapshot_id)
        except Exception:
            # Graph auto-project failures must not invalidate CEIM publish.
            pass
        try:
            retrieval.maybe_auto_index_for_snapshot(snapshot_id)
        except Exception:
            # Retrieval failures leave snapshot/graph intact.
            pass
        if portfolio is not None and engineering is not None and portfolio_auto_refresh_enabled():
            try:
                snap = engineering.get(snapshot_id)
                if snap is not None:
                    portfolio.aggregation.mark_stale_for_repository(snap.repository_id)
            except Exception:
                # Portfolio refresh candidate marking must not affect repository publish.
                pass

    return _on_published


def get_api_services(request: Request) -> Iterator[ApiServices]:
    """Yield Application services for one request; commit on success."""

    state = request.app.state
    storage: ArtifactStorage = state.artifact_storage
    max_bytes = int(getattr(state, "max_artifact_bytes", 10_485_760))
    embeddings = create_embedding_provider()
    portfolio_embeddings = create_portfolio_embedding_provider()
    llm = create_llm_provider()

    if getattr(state, "use_memory", False):
        org_store = state.memory_organizations
        workspace_store = state.memory_workspaces
        repository_store = state.memory_repositories
        assessment_store = state.memory_assessments
        artifact_store = state.memory_artifacts
        intelligence_store = state.memory_intelligence
        finding_store = state.memory_findings
        metric_store = state.memory_metrics
        recommendation_store = state.memory_recommendations
        engineering_store = state.memory_engineering
        knowledge_graph_store = state.memory_knowledge_graphs
        retrieval_store = getattr(state, "memory_retrieval_indexes", None)
        if retrieval_store is None:
            retrieval_store = InMemoryRetrievalRepository(embeddings=embeddings)
            state.memory_retrieval_indexes = retrieval_store
        else:
            retrieval_store._embeddings = embeddings
        answer_store = getattr(state, "memory_answer_runs", None)
        if answer_store is None:
            answer_store = InMemoryAnswerRunRepository()
            state.memory_answer_runs = answer_store
        portfolio_answer_store = getattr(state, "memory_portfolio_answer_runs", None)
        if portfolio_answer_store is None:
            portfolio_answer_store = InMemoryPortfolioAnswerRunRepository()
            state.memory_portfolio_answer_runs = portfolio_answer_store
        portfolio_store = getattr(state, "memory_portfolios", None)
        if portfolio_store is None:
            portfolio_store = InMemoryPortfolioRepository()
            state.memory_portfolios = portfolio_store
        portfolio_snapshot_store = getattr(state, "memory_portfolio_snapshots", None)
        if portfolio_snapshot_store is None:
            portfolio_snapshot_store = InMemoryPortfolioSnapshotRepository()
            state.memory_portfolio_snapshots = portfolio_snapshot_store
        portfolio_retrieval_store = getattr(state, "memory_portfolio_retrieval_indexes", None)
        if portfolio_retrieval_store is None:
            portfolio_retrieval_store = InMemoryPortfolioRetrievalRepository(
                embeddings=portfolio_embeddings
            )
            state.memory_portfolio_retrieval_indexes = portfolio_retrieval_store
        else:
            portfolio_retrieval_store._embeddings = portfolio_embeddings
        graph_intelligence_store = InMemoryGraphIntelligenceRepository(knowledge_graph_store)
        knowledge_graphs = EngineeringGraphProjectionService(
            graphs=knowledge_graph_store,
            snapshots=engineering_store,
            queries=knowledge_graph_store,
        )
        retrieval = EngineeringRetrievalIndexingService(
            indexes=retrieval_store,
            snapshots=engineering_store,
            graphs=knowledge_graph_store,
            embeddings=embeddings,
            queries=retrieval_store,
        )
        answering = EngineeringAnswerOrchestrationService(
            answers=answer_store,
            retrieval=retrieval,
            llm=llm,
        )
        portfolio_retrieval = PortfolioRetrievalIndexingService(
            indexes=portfolio_retrieval_store,
            portfolio_snapshots=portfolio_snapshot_store,
            portfolios=portfolio_store,
            embeddings=portfolio_embeddings,
            queries=portfolio_retrieval_store,
            sources=DefaultPortfolioRetrievalSourceRepository(portfolio_snapshot_store),
        )
        portfolio_answering = PortfolioAnswerOrchestrationService(
            answers=portfolio_answer_store,
            portfolio_retrieval=portfolio_retrieval,
            llm=llm,
        )
        portfolio = _build_portfolio_facade(
            portfolios=portfolio_store,
            snapshots=portfolio_snapshot_store,
            assessments=assessment_store,
            engineering=engineering_store,
            knowledge_graphs=knowledge_graph_store,
            retrieval_indexes=retrieval_store,
            organizations=org_store,
            workspaces=workspace_store,
            repositories=repository_store,
            on_snapshot_completed=portfolio_retrieval.maybe_auto_index_for_portfolio_snapshot,
        )
        services = ApiServices(
            organizations=DefaultOrganizationService(organizations=org_store),
            workspaces=DefaultWorkspaceService(
                workspaces=workspace_store,
                organizations=org_store,
            ),
            repositories=DefaultRepositoryService(
                repositories=repository_store,
                workspaces=workspace_store,
                organizations=org_store,
            ),
            assessments=DefaultAssessmentService(
                assessments=assessment_store,
                repositories=repository_store,
                workspaces=workspace_store,
            ),
            artifacts=DefaultArtifactService(
                artifacts=artifact_store,
                storage=storage,
                assessments=assessment_store,
                repositories=repository_store,
                max_artifact_bytes=max_bytes,
            ),
            intelligence=DefaultAssessmentIntelligenceService(
                intelligence=intelligence_store,
                findings=finding_store,
                metrics=metric_store,
                recommendations=recommendation_store,
                assessments=assessment_store,
                repositories=repository_store,
                artifacts=artifact_store,
                storage=storage,
                artifact_reader=DefaultAssessmentArtifactReader(
                    artifacts=artifact_store,
                    storage=storage,
                ),
            ),
            engineering=EngineeringNormalizationService(
                snapshots=engineering_store,
                intelligence=intelligence_store,
                on_snapshot_published=_chain_snapshot_published(
                    knowledge_graphs=knowledge_graphs,
                    retrieval=retrieval,
                    portfolio=portfolio,
                    engineering=engineering_store,
                ),
            ),
            knowledge_graphs=knowledge_graphs,
            graph_intelligence=GraphIntelligenceFacade(
                graphs=knowledge_graph_store,
                intelligence=graph_intelligence_store,
            ),
            retrieval=retrieval,
            answering=answering,
            portfolio=portfolio,
            portfolio_retrieval=portfolio_retrieval,
            portfolio_answering=portfolio_answering,
            _session=None,
        )
        try:
            yield services
        except Exception:
            raise
        return

    session: Session = state.session_factory()
    org_repo = SqlAlchemyOrganizationRepository(session)
    workspace_repo = SqlAlchemyWorkspaceRepository(session)
    repository_repo = SqlAlchemyRepositoryRepository(session)
    assessment_repo = SqlAlchemyAssessmentRepository(session)
    artifact_repo = SqlAlchemyAssessmentArtifactRepository(session)
    intelligence_repo = SqlAlchemyAssessmentIntelligenceRepository(session)
    finding_repo = SqlAlchemyFindingRepository(session)
    metric_repo = SqlAlchemyMetricRepository(session)
    recommendation_repo = SqlAlchemyRecommendationRepository(session)
    engineering_repo = SqlAlchemyEngineeringSnapshotRepository(session)
    knowledge_graph_repo = SqlAlchemyKnowledgeGraphRepository(session)
    graph_intelligence_repo = SqlAlchemyGraphIntelligenceRepository(knowledge_graph_repo)
    retrieval_repo = SqlAlchemyRetrievalIndexRepository(session, embeddings=embeddings)
    answer_repo = SqlAlchemyAnswerRunRepository(session)
    portfolio_answer_repo = SqlAlchemyPortfolioAnswerRunRepository(session)
    portfolio_repo = SqlAlchemyPortfolioRepository(session)
    portfolio_snapshot_repo = SqlAlchemyPortfolioSnapshotRepository(session)
    portfolio_retrieval_repo = SqlAlchemyPortfolioRetrievalRepository(
        session,
        embeddings=portfolio_embeddings,
    )
    knowledge_graphs = EngineeringGraphProjectionService(
        graphs=knowledge_graph_repo,
        snapshots=engineering_repo,
        queries=knowledge_graph_repo,
    )
    retrieval = EngineeringRetrievalIndexingService(
        indexes=retrieval_repo,
        snapshots=engineering_repo,
        graphs=knowledge_graph_repo,
        embeddings=embeddings,
        queries=retrieval_repo,
    )
    answering = EngineeringAnswerOrchestrationService(
        answers=answer_repo,
        retrieval=retrieval,
        llm=llm,
    )
    portfolio_retrieval = PortfolioRetrievalIndexingService(
        indexes=portfolio_retrieval_repo,
        portfolio_snapshots=portfolio_snapshot_repo,
        portfolios=portfolio_repo,
        embeddings=portfolio_embeddings,
        queries=portfolio_retrieval_repo,
        sources=DefaultPortfolioRetrievalSourceRepository(portfolio_snapshot_repo),
    )
    portfolio_answering = PortfolioAnswerOrchestrationService(
        answers=portfolio_answer_repo,
        portfolio_retrieval=portfolio_retrieval,
        llm=llm,
    )
    portfolio = _build_portfolio_facade(
        portfolios=portfolio_repo,
        snapshots=portfolio_snapshot_repo,
        assessments=assessment_repo,
        engineering=engineering_repo,
        knowledge_graphs=knowledge_graph_repo,
        retrieval_indexes=retrieval_repo,
        organizations=org_repo,
        workspaces=workspace_repo,
        repositories=repository_repo,
        on_snapshot_completed=portfolio_retrieval.maybe_auto_index_for_portfolio_snapshot,
    )
    services = ApiServices(
        organizations=DefaultOrganizationService(organizations=org_repo),
        workspaces=DefaultWorkspaceService(
            workspaces=workspace_repo,
            organizations=org_repo,
        ),
        repositories=DefaultRepositoryService(
            repositories=repository_repo,
            workspaces=workspace_repo,
            organizations=org_repo,
        ),
        assessments=DefaultAssessmentService(
            assessments=assessment_repo,
            repositories=repository_repo,
            workspaces=workspace_repo,
        ),
        artifacts=DefaultArtifactService(
            artifacts=artifact_repo,
            storage=storage,
            assessments=assessment_repo,
            repositories=repository_repo,
            max_artifact_bytes=max_bytes,
        ),
        intelligence=DefaultAssessmentIntelligenceService(
            intelligence=intelligence_repo,
            findings=finding_repo,
            metrics=metric_repo,
            recommendations=recommendation_repo,
            assessments=assessment_repo,
            repositories=repository_repo,
            artifacts=artifact_repo,
            storage=storage,
            artifact_reader=DefaultAssessmentArtifactReader(
                artifacts=artifact_repo,
                storage=storage,
            ),
        ),
        engineering=EngineeringNormalizationService(
            snapshots=engineering_repo,
            intelligence=intelligence_repo,
            on_snapshot_published=_chain_snapshot_published(
                knowledge_graphs=knowledge_graphs,
                retrieval=retrieval,
                portfolio=portfolio,
                engineering=engineering_repo,
            ),
        ),
        knowledge_graphs=knowledge_graphs,
        graph_intelligence=GraphIntelligenceFacade(
            graphs=knowledge_graph_repo,
            intelligence=graph_intelligence_repo,
        ),
        retrieval=retrieval,
        answering=answering,
        portfolio=portfolio,
        portfolio_retrieval=portfolio_retrieval,
        portfolio_answering=portfolio_answering,
        _session=session,
    )
    try:
        yield services
        services.commit()
    except Exception:
        services.rollback()
        raise
    finally:
        session.close()


ServicesDep = Annotated[ApiServices, Depends(get_api_services)]


def install_memory_stores(
    app_state: object,
    *,
    artifact_storage: ArtifactStorage | None = None,
) -> None:
    app_state.use_memory = True  # type: ignore[attr-defined]
    app_state.memory_organizations = InMemoryOrganizationRepository()  # type: ignore[attr-defined]
    app_state.memory_workspaces = InMemoryWorkspaceRepository()  # type: ignore[attr-defined]
    app_state.memory_repositories = InMemoryRepositoryRepository()  # type: ignore[attr-defined]
    app_state.memory_assessments = InMemoryAssessmentRepository()  # type: ignore[attr-defined]
    app_state.memory_artifacts = InMemoryArtifactRepository()  # type: ignore[attr-defined]
    app_state.memory_intelligence = InMemoryAssessmentIntelligenceRepository()  # type: ignore[attr-defined]
    app_state.memory_findings = InMemoryFindingRepository()  # type: ignore[attr-defined]
    app_state.memory_metrics = InMemoryMetricRepository()  # type: ignore[attr-defined]
    app_state.memory_recommendations = InMemoryRecommendationRepository()  # type: ignore[attr-defined]
    app_state.memory_engineering = InMemoryEngineeringSnapshotRepository()  # type: ignore[attr-defined]
    app_state.memory_knowledge_graphs = InMemoryKnowledgeGraphRepository()  # type: ignore[attr-defined]
    app_state.memory_retrieval_indexes = InMemoryRetrievalRepository()  # type: ignore[attr-defined]
    app_state.memory_answer_runs = InMemoryAnswerRunRepository()  # type: ignore[attr-defined]
    app_state.memory_portfolio_answer_runs = InMemoryPortfolioAnswerRunRepository()  # type: ignore[attr-defined]
    app_state.memory_portfolios = InMemoryPortfolioRepository()  # type: ignore[attr-defined]
    app_state.memory_portfolio_snapshots = InMemoryPortfolioSnapshotRepository()  # type: ignore[attr-defined]
    app_state.memory_portfolio_retrieval_indexes = InMemoryPortfolioRetrievalRepository()  # type: ignore[attr-defined]
    app_state.artifact_storage = artifact_storage or InMemoryArtifactStorage()  # type: ignore[attr-defined]


def install_artifact_storage(
    app_state: object,
    *,
    root: Path | None = None,
    use_memory: bool = False,
) -> None:
    if use_memory or root is None:
        app_state.artifact_storage = InMemoryArtifactStorage()  # type: ignore[attr-defined]
    else:
        app_state.artifact_storage = FileSystemArtifactStorage(root)  # type: ignore[attr-defined]
