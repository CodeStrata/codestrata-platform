"""Application tests for Portfolio Answering."""

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
from codestrata_platform.application.portfolio_answering.commands import (
    AskPortfolioQuestionCommand,
    GetPortfolioAnswerRunQuery,
    ListPortfolioAnswersQuery,
    SubmitPortfolioAnswerFeedbackCommand,
)
from codestrata_platform.application.portfolio_answering.errors import (
    PortfolioAnsweringDisabledError,
    PortfolioAnsweringGroundingError,
)
from codestrata_platform.application.portfolio_answering.policies import (
    portfolio_answering_enabled,
)
from codestrata_platform.application.portfolio_answering.services import (
    PortfolioAnswerOrchestrationService,
)
from codestrata_platform.application.portfolio_answering.validation import (
    PortfolioQuestionClassificationService,
)
from codestrata_platform.application.portfolio_retrieval.commands import (
    BuildPortfolioRetrievalIndexCommand,
)
from codestrata_platform.application.portfolio_retrieval.services import (
    PortfolioRetrievalIndexingService,
)
from codestrata_platform.domain.answering.lifecycle import GroundingStatus
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
from codestrata_platform.domain.portfolio_answering.lifecycle import PortfolioQuestionType
from codestrata_platform.domain.portfolio_answering.question import PortfolioQuestionScope
from codestrata_platform.domain.portfolio_retrieval.identifiers import PortfolioRetrievalIndexId
from codestrata_platform.domain.repository import Repository, RepositoryProvider
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace import Workspace
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.answering import DeterministicLLMProvider
from codestrata_platform.infrastructure.memory import (
    InMemoryAssessmentRepository,
    InMemoryEngineeringSnapshotRepository,
    InMemoryKnowledgeGraphRepository,
    InMemoryOrganizationRepository,
    InMemoryPortfolioAnswerRunRepository,
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


def _seed() -> tuple[
    PortfolioAnswerOrchestrationService,
    OrganizationId,
    WorkspaceId,
    PortfolioId,
    PortfolioRetrievalIndexId,
    DeterministicLLMProvider,
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
    answers = InMemoryPortfolioAnswerRunRepository()

    org = Organization.create(name="Acme", organization_id=OrganizationId("org:pa-app"))
    organizations.save(org)
    workspace = Workspace.create(
        organization_id=org.organization_id,
        name="Main",
        workspace_id=WorkspaceId("workspace:pa-app"),
    )
    workspaces.save(workspace)

    repo_ids: list[RepositoryId] = []
    for idx in range(2):
        repo = Repository.register(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            display_name=f"repo-{idx}",
            provider=RepositoryProvider.GITHUB,
            repository_url=f"https://github.com/acme/pa-app-{idx}",
            repository_id=RepositoryId(f"repo:pa-app-{idx}"),
        )
        repositories.save(repo)
        repo_ids.append(repo.repository_id)
        assessment = Assessment.create(
            repository_id=repo.repository_id,
            workspace_id=workspace.workspace_id,
            engine_version="1.0.0",
            assessment_version="0.1.0",
            assessment_id=AssessmentId(f"assessment:pa-app-{idx}"),
        )
        assessment.start()
        assessment.complete()
        assessments.save(assessment)
        snapshot = EngineeringSnapshot.create(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            repository_id=repo.repository_id,
            assessment_id=assessment.assessment_id,
            assessment_intelligence_id=f"intel:pa-app-{idx}",
            assessment_revision=1,
            version=1,
            source_artifact_ids=("artifact:1",),
            snapshot_id=EngineeringSnapshotId(f"eng-snapshot:pa-app-{idx}"),
        )
        finding_id = EngineeringFindingId(f"eng-finding:pa-app-{idx}")
        snapshot.build(
            technologies=(
                EngineeringTechnology(
                    technology_id=EngineeringTechnologyId(f"eng-tech:pa-app-{idx}"),
                    canonical_key="java",
                    display_name="Java",
                    category=EngineeringCategory.OTHER,
                ),
            ),
            findings=(
                EngineeringFinding(
                    finding_id=finding_id,
                    source_finding_id=f"finding:pa-app-{idx}",
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
                    recommendation_id=EngineeringRecommendationId(f"eng-rec:pa-app-{idx}"),
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

    management = PortfolioManagementService(
        portfolios=portfolios,
        organizations=organizations,
        workspaces=workspaces,
        repositories=repositories,
    )
    aggregation = PortfolioIntelligenceAggregationService(
        portfolios=portfolios,
        snapshots=snapshots,
        sources=DefaultPortfolioSourceIntelligenceRepository(
            assessments=assessments,
            snapshots=engineering,
            graphs=graphs,
        ),
        organizations=organizations,
        workspaces=workspaces,
    )
    retrieval = PortfolioRetrievalIndexingService(
        indexes=indexes,
        portfolio_snapshots=snapshots,
        portfolios=portfolios,
        embeddings=embeddings,
        queries=indexes,
        sources=DefaultPortfolioRetrievalSourceRepository(snapshots),
    )
    created = management.create_portfolio(
        CreatePortfolioCommand(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            name="Platform Ask",
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
    snap = aggregation.build_snapshot(
        BuildPortfolioSnapshotCommand(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            portfolio_id=portfolio_id,
        )
    )
    assert snap is not None
    index = retrieval.build_index(
        BuildPortfolioRetrievalIndexCommand(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            portfolio_id=portfolio_id,
        )
    )
    llm = DeterministicLLMProvider()
    answering = PortfolioAnswerOrchestrationService(
        answers=answers,
        portfolio_retrieval=retrieval,
        llm=llm,
    )
    return (
        answering,
        org.organization_id,
        workspace.workspace_id,
        portfolio_id,
        PortfolioRetrievalIndexId(index.index.index_id),
        llm,
    )


def test_portfolio_answering_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODESTRATA_PORTFOLIO_ANSWERING_ENABLED", raising=False)
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    assert portfolio_answering_enabled() is False
    answering, org_id, workspace_id, portfolio_id, index_id, _ = _seed()
    with pytest.raises(PortfolioAnsweringDisabledError):
        answering.ask(
            AskPortfolioQuestionCommand(
                question="What is the portfolio overview?",
                scope=PortfolioQuestionScope(
                    organization_id=org_id.value,
                    workspace_id=workspace_id.value,
                    portfolio_id=portfolio_id.value,
                ),
                portfolio_retrieval_index_id=index_id,
            )
        )


def test_classification_is_deterministic() -> None:
    classifier = PortfolioQuestionClassificationService()
    assert (
        classifier.classify("Where is technology fragmentation concentrated?")
        is PortfolioQuestionType.TECHNOLOGY_FRAGMENTATION
    )
    assert (
        classifier.classify("What systemic risks recur across repositories?")
        is PortfolioQuestionType.SYSTEMIC_RISK_EXPLANATION
    )
    assert (
        classifier.classify("Show modernization waves")
        is PortfolioQuestionType.MODERNIZATION_GUIDANCE
    )


def test_ask_grounded_answer_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_ANSWERING_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_LLM_PROVIDER", "deterministic")
    answering, org_id, workspace_id, portfolio_id, index_id, _ = _seed()
    result = answering.ask(
        AskPortfolioQuestionCommand(
            question="What is the portfolio overview and systemic risk landscape?",
            scope=PortfolioQuestionScope(
                organization_id=org_id.value,
                workspace_id=workspace_id.value,
                portfolio_id=portfolio_id.value,
            ),
            portfolio_retrieval_index_id=index_id,
            include_diagnostics=True,
        )
    )
    assert result.status.value == "completed"
    assert result.answer
    assert result.citations
    assert all(item.label.startswith("[P") for item in result.citations)
    assert all(item.portfolio_id == portfolio_id.value for item in result.citations)
    assert result.grounding_status in {
        GroundingStatus.GROUNDED,
        GroundingStatus.PARTIALLY_GROUNDED,
        GroundingStatus.INSUFFICIENT_CONTEXT,
    }
    assert result.confidence_score is not None
    assert result.portfolio_retrieval_index_id == index_id.value

    got = answering.get_answer(
        GetPortfolioAnswerRunQuery(
            answer_run_id=__import__(
                "codestrata_platform.domain.portfolio_answering.identifiers",
                fromlist=["PortfolioAnswerRunId"],
            ).PortfolioAnswerRunId(result.answer_run_id),
            organization_id=org_id,
            workspace_id=workspace_id,
        )
    )
    assert got.answer_run_id == result.answer_run_id
    listed = answering.list_portfolio_answers(
        ListPortfolioAnswersQuery(
            portfolio_id=portfolio_id,
            organization_id=org_id,
            workspace_id=workspace_id,
        )
    )
    assert any(item.answer_run_id == result.answer_run_id for item in listed)
    feedback = answering.submit_feedback(
        SubmitPortfolioAnswerFeedbackCommand(
            answer_run_id=__import__(
                "codestrata_platform.domain.portfolio_answering.identifiers",
                fromlist=["PortfolioAnswerRunId"],
            ).PortfolioAnswerRunId(result.answer_run_id),
            organization_id=org_id,
            workspace_id=workspace_id,
            rating=5,
            feedback_category="useful",
            comment="grounded",
        )
    )
    assert feedback["rating"] == 5


def test_ungrounded_provider_response_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_ANSWERING_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_LLM_PROVIDER", "deterministic")
    answering, org_id, workspace_id, portfolio_id, index_id, llm = _seed()
    llm._malformed_next = True
    with pytest.raises(PortfolioAnsweringGroundingError):
        answering.ask(
            AskPortfolioQuestionCommand(
                question="What recurring findings exist across repositories?",
                scope=PortfolioQuestionScope(
                    organization_id=org_id.value,
                    workspace_id=workspace_id.value,
                    portfolio_id=portfolio_id.value,
                ),
                portfolio_retrieval_index_id=index_id,
                use_cache=False,
            )
        )


def test_provider_failure_is_recorded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_ANSWERING_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_PORTFOLIO_RETRIEVAL_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_LLM_PROVIDER", "deterministic")
    answering, org_id, workspace_id, portfolio_id, index_id, llm = _seed()
    llm._fail_next = True
    with pytest.raises(ValidationError):
        answering.ask(
            AskPortfolioQuestionCommand(
                question="What is the portfolio technology landscape?",
                scope=PortfolioQuestionScope(
                    organization_id=org_id.value,
                    workspace_id=workspace_id.value,
                    portfolio_id=portfolio_id.value,
                ),
                portfolio_retrieval_index_id=index_id,
                use_cache=False,
            )
        )
