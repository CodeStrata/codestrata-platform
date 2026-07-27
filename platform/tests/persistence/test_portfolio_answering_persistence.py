"""PostgreSQL persistence tests for Portfolio Answering."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

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
from codestrata_platform.application.portfolio_retrieval.services import (
    PortfolioRetrievalIndexingService,
)
from codestrata_platform.domain.answering.grounding import AnswerText, GroundingResult
from codestrata_platform.domain.answering.identifiers import (
    AnswerPolicyVersion,
    PromptTemplateVersion,
    ProviderRequestId,
)
from codestrata_platform.domain.answering.lifecycle import AnswerStatus, GroundingStatus
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
from codestrata_platform.domain.portfolio_answering.answer import PortfolioAnswerRun
from codestrata_platform.domain.portfolio_answering.citation import (
    PortfolioAnswerCitation,
    PortfolioAnswerConfidence,
)
from codestrata_platform.domain.portfolio_answering.identifiers import (
    PortfolioAnswerCitationId,
    PortfolioAnswerProjectionKey,
    PortfolioAnswerRunId,
    normalize_portfolio_question_hash,
)
from codestrata_platform.domain.portfolio_answering.lifecycle import (
    AnswerConfidenceLevel,
    PortfolioQuestionType,
)
from codestrata_platform.domain.portfolio_answering.question import (
    PortfolioQuestion,
    PortfolioQuestionScope,
)
from codestrata_platform.domain.portfolio_retrieval.identifiers import PortfolioRetrievalIndexId
from codestrata_platform.domain.repository import Repository, RepositoryProvider
from codestrata_platform.domain.repository.ids import RepositoryId
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
    SqlAlchemyPortfolioAnswerRunRepository,
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


def _seed_completed_index(session, monkeypatch: pytest.MonkeyPatch):
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

    org = Organization.create(name="Acme PA Persist")
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
            repository_url=f"https://github.com/acme/pa-persist-{idx}",
        )
        repository_repo.save(repo)
        repo_ids.append(repo.repository_id)
        assessment = Assessment.create(
            repository_id=repo.repository_id,
            workspace_id=workspace.workspace_id,
            engine_version="1.0.0",
            assessment_version="0.1.0",
            assessment_id=AssessmentId(f"assessment:pa-persist-{idx}"),
        )
        assessment.start()
        assessment.complete()
        assessment_repo.save(assessment)
        snapshot = EngineeringSnapshot.create(
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
            repository_id=repo.repository_id,
            assessment_id=assessment.assessment_id,
            assessment_intelligence_id=f"intel:pa-persist-{idx}",
            assessment_revision=1,
            version=1,
            source_artifact_ids=("artifact:1",),
            snapshot_id=EngineeringSnapshotId(f"eng-snapshot:pa-persist-{idx}"),
        )
        finding_id = EngineeringFindingId(f"eng-finding:pa-persist-{idx}")
        snapshot.build(
            technologies=(
                EngineeringTechnology(
                    technology_id=EngineeringTechnologyId(f"eng-tech:pa-persist-{idx}"),
                    canonical_key="java",
                    display_name="Java",
                    category=EngineeringCategory.OTHER,
                ),
            ),
            findings=(
                EngineeringFinding(
                    finding_id=finding_id,
                    source_finding_id=f"finding:pa-persist-{idx}",
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
                    recommendation_id=EngineeringRecommendationId(
                        f"eng-rec:pa-persist-{idx}"
                    ),
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

    management = PortfolioManagementService(
        portfolios=portfolio_repo,
        organizations=org_repo,
        workspaces=workspace_repo,
        repositories=repository_repo,
    )
    aggregation = PortfolioIntelligenceAggregationService(
        portfolios=portfolio_repo,
        snapshots=snapshot_repo,
        sources=DefaultPortfolioSourceIntelligenceRepository(
            assessments=assessment_repo,
            snapshots=engineering_repo,
            graphs=graph_repo,
        ),
        organizations=org_repo,
        workspaces=workspace_repo,
    )
    retrieval = PortfolioRetrievalIndexingService(
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
            name="PA Persist Portfolio",
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
    index = retrieval.build_index(
        BuildPortfolioRetrievalIndexCommand(
            portfolio_id=portfolio_id,
            organization_id=org.organization_id,
            workspace_id=workspace.workspace_id,
        )
    )
    session.commit()
    loaded = retrieval_repo.get(PortfolioRetrievalIndexId(index.index.index_id))
    assert loaded is not None
    return org, workspace, portfolio_id, loaded


def _complete_run(
    *,
    org,
    workspace,
    portfolio_id: PortfolioId,
    index,
    suffix: str,
) -> PortfolioAnswerRun:
    question = PortfolioQuestion(
        text=f"What systemic risks exist across repositories? {suffix}",
        scope=PortfolioQuestionScope(
            organization_id=org.organization_id.value,
            workspace_id=workspace.workspace_id.value,
            portfolio_id=portfolio_id.value,
        ),
    )
    run = PortfolioAnswerRun.create_pending(
        answer_run_id=PortfolioAnswerRunId(
            f"portfolio-answer:{suffix.ljust(32, 'a')[:32]}"
        ),
        organization_id=org.organization_id,
        workspace_id=workspace.workspace_id,
        portfolio_id=portfolio_id,
        portfolio_snapshot_id=index.portfolio_snapshot_id,
        portfolio_retrieval_index_id=index.index_id,
        portfolio_retrieval_index_version=index.index_version.value,
        question=question,
        question_type=PortfolioQuestionType.SYSTEMIC_RISK_EXPLANATION,
        normalized_question_hash=normalize_portfolio_question_hash(question.text),
        projection_key=PortfolioAnswerProjectionKey((suffix * 8)[:64]),
        provider_id="deterministic",
        model_id="deterministic-test-answer",
        prompt_template_version=PromptTemplateVersion("1.0.0"),
        answer_policy_version=AnswerPolicyVersion("1.0.0"),
    )
    run.begin_retrieval()
    run.attach_context(diagnostics={"chunk_count": "2"})
    run.begin_generation()
    run.attach_provider_response(provider_request_id=ProviderRequestId(f"req:{suffix}"))
    citations = (
        PortfolioAnswerCitation(
            citation_id=PortfolioAnswerCitationId(f"portfolio-answer-cite:{suffix}:1"),
            label="[P1]",
            document_id=index.documents[0].document_id.value,
            chunk_id=index.chunks[0].chunk_id.value,
            content_type="systemic_risk",
            canonical_type="risk",
            canonical_id="risk:1",
            source_references=("portfolio_risk:risk:1",),
            repository_ids=tuple(item.value for item in index.repository_ids[:2]),
            portfolio_id=portfolio_id.value,
            portfolio_snapshot_id=index.portfolio_snapshot_id.value,
            retrieval_score=0.9,
            excerpt="Systemic risk across repositories",
        ),
        PortfolioAnswerCitation(
            citation_id=PortfolioAnswerCitationId(f"portfolio-answer-cite:{suffix}:2"),
            label="[P2]",
            document_id=index.documents[0].document_id.value,
            chunk_id=index.chunks[0].chunk_id.value,
            content_type="systemic_risk",
            canonical_type="risk",
            canonical_id="risk:2",
            source_references=("portfolio_risk:risk:2",),
            repository_ids=tuple(item.value for item in index.repository_ids[:1]),
            portfolio_id=portfolio_id.value,
            portfolio_snapshot_id=index.portfolio_snapshot_id.value,
            retrieval_score=0.8,
            excerpt="Secondary risk signal",
        ),
    )
    run.validate_grounding(
        answer_text=AnswerText("Systemic risk is present [P1] and secondary [P2]."),
        citations=citations,
        grounding=GroundingResult(
            status=GroundingStatus.GROUNDED,
            cited_labels=("[P1]", "[P2]"),
        ),
        confidence=PortfolioAnswerConfidence(
            level=AnswerConfidenceLevel.HIGH,
            score=80,
            factors=("grounded", "citation_coverage"),
            policy_version="1.0.0",
        ),
        limitations=("Context may omit unavailable repositories.",),
    )
    run.complete()
    return run


def test_portfolio_answer_round_trip_and_feedback(session, monkeypatch: pytest.MonkeyPatch) -> None:
    org, workspace, portfolio_id, index = _seed_completed_index(session, monkeypatch)
    answers = SqlAlchemyPortfolioAnswerRunRepository(session)
    run = _complete_run(
        org=org,
        workspace=workspace,
        portfolio_id=portfolio_id,
        index=index,
        suffix="completed01",
    )
    answers.save(run)
    session.commit()

    loaded = answers.get(run.answer_run_id)
    assert loaded is not None
    assert loaded.status is AnswerStatus.COMPLETED
    assert loaded.provider_id == "deterministic"
    assert loaded.model_id == "deterministic-test-answer"
    assert loaded.prompt_template_version.value == "1.0.0"
    assert loaded.answer_policy_version.value == "1.0.0"
    assert loaded.confidence is not None
    assert loaded.confidence.score == 80
    assert loaded.grounding is not None
    assert loaded.grounding.status is GroundingStatus.GROUNDED
    assert [item.label for item in loaded.citations] == ["[P1]", "[P2]"]
    assert loaded.portfolio_id == portfolio_id
    assert loaded.portfolio_snapshot_id == index.portfolio_snapshot_id
    assert loaded.portfolio_retrieval_index_id == index.index_id
    assert "unavailable" in " ".join(loaded.limitations).lower()

    before_status = loaded.status
    feedback = answers.save_feedback(
        answer_run_id=run.answer_run_id,
        rating=5,
        feedback_category="helpful",
        comment="Useful portfolio answer",
    )
    session.commit()
    listed_feedback = answers.list_feedback(run.answer_run_id)
    assert any(item["id"] == feedback["id"] for item in listed_feedback)
    after = answers.get(run.answer_run_id)
    assert after is not None
    assert after.status is before_status
    assert after.answer_text is not None
    assert after.answer_text.value == loaded.answer_text.value

    cached = answers.find_by_projection_key(run.projection_key.value)
    assert cached is not None
    assert cached.answer_run_id == run.answer_run_id


def test_failed_and_rejected_are_not_completed_projection_hits(
    session, monkeypatch: pytest.MonkeyPatch
) -> None:
    org, workspace, portfolio_id, index = _seed_completed_index(session, monkeypatch)
    answers = SqlAlchemyPortfolioAnswerRunRepository(session)

    rejected = _complete_run(
        org=org,
        workspace=workspace,
        portfolio_id=portfolio_id,
        index=index,
        suffix="rejected01",
    )
    # Rebuild as rejected without completing
    question = rejected.question
    pending = PortfolioAnswerRun.create_pending(
        answer_run_id=PortfolioAnswerRunId("portfolio-answer:rejected01aaaaaaaaaaaaaaaa"),
        organization_id=org.organization_id,
        workspace_id=workspace.workspace_id,
        portfolio_id=portfolio_id,
        portfolio_snapshot_id=index.portfolio_snapshot_id,
        portfolio_retrieval_index_id=index.index_id,
        portfolio_retrieval_index_version=index.index_version.value,
        question=question,
        question_type=PortfolioQuestionType.SYSTEMIC_RISK_EXPLANATION,
        normalized_question_hash=normalize_portfolio_question_hash(question.text),
        projection_key=PortfolioAnswerProjectionKey("r" * 64),
        provider_id="deterministic",
        model_id="deterministic-test-answer",
        prompt_template_version=PromptTemplateVersion("1.0.0"),
        answer_policy_version=AnswerPolicyVersion("1.0.0"),
    )
    pending.begin_retrieval()
    pending.attach_context()
    pending.begin_generation()
    pending.reject("unsupported_claim", limitations=("Invented claim rejected.",))
    answers.save(pending)

    failed = PortfolioAnswerRun.create_pending(
        answer_run_id=PortfolioAnswerRunId("portfolio-answer:failed001aaaaaaaaaaaaaaaaa"),
        organization_id=org.organization_id,
        workspace_id=workspace.workspace_id,
        portfolio_id=portfolio_id,
        portfolio_snapshot_id=index.portfolio_snapshot_id,
        portfolio_retrieval_index_id=index.index_id,
        portfolio_retrieval_index_version=index.index_version.value,
        question=question,
        question_type=PortfolioQuestionType.SYSTEMIC_RISK_EXPLANATION,
        normalized_question_hash=normalize_portfolio_question_hash(question.text + "-fail"),
        projection_key=PortfolioAnswerProjectionKey("f" * 64),
        provider_id="deterministic",
        model_id="deterministic-test-answer",
        prompt_template_version=PromptTemplateVersion("1.0.0"),
        answer_policy_version=AnswerPolicyVersion("1.0.0"),
    )
    failed.begin_retrieval()
    failed.fail("provider_timeout")
    answers.save(failed)
    session.commit()

    assert answers.find_by_projection_key("r" * 64) is None
    assert answers.find_by_projection_key("f" * 64) is None
    listed = answers.list_by_portfolio(portfolio_id)
    statuses = {item.status for item in listed}
    assert AnswerStatus.REJECTED in statuses
    assert AnswerStatus.FAILED in statuses
    assert AnswerStatus.COMPLETED not in statuses or all(
        item.status is not AnswerStatus.COMPLETED or item.answer_text is not None
        for item in listed
    )


def test_portfolio_answer_restart_persistence(
    postgres_engine, session, monkeypatch: pytest.MonkeyPatch
) -> None:
    org, workspace, portfolio_id, index = _seed_completed_index(session, monkeypatch)
    answers = SqlAlchemyPortfolioAnswerRunRepository(session)
    run = _complete_run(
        org=org,
        workspace=workspace,
        portfolio_id=portfolio_id,
        index=index,
        suffix="restart01",
    )
    answers.save(run)
    session.commit()
    answer_id = run.answer_run_id.value

    factory = sessionmaker(bind=postgres_engine, expire_on_commit=False)
    restarted = factory()
    try:
        repo = SqlAlchemyPortfolioAnswerRunRepository(restarted)
        loaded = repo.get(PortfolioAnswerRunId(answer_id))
        assert loaded is not None
        assert loaded.status is AnswerStatus.COMPLETED
        assert [item.label for item in loaded.citations] == ["[P1]", "[P2]"]
    finally:
        restarted.close()


def test_portfolio_answer_transaction_rollback(
    session, monkeypatch: pytest.MonkeyPatch
) -> None:
    org, workspace, portfolio_id, index = _seed_completed_index(session, monkeypatch)
    answers = SqlAlchemyPortfolioAnswerRunRepository(session)
    run = _complete_run(
        org=org,
        workspace=workspace,
        portfolio_id=portfolio_id,
        index=index,
        suffix="rollback1",
    )
    answers.save(run)
    session.flush()
    session.rollback()
    if not session.in_transaction():
        session.begin()

    missing = answers.get(run.answer_run_id)
    assert missing is None
    count = session.execute(
        text("SELECT COUNT(*) FROM engineering_portfolio_answer_runs WHERE id = :id"),
        {"id": run.answer_run_id.value},
    ).scalar_one()
    assert count == 0
