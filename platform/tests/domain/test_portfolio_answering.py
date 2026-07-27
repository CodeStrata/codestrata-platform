"""Domain tests for Portfolio Answering."""

from __future__ import annotations

import pytest

from codestrata_platform.domain.answering.grounding import AnswerText, GroundingResult
from codestrata_platform.domain.answering.identifiers import (
    AnswerPolicyVersion,
    PromptTemplateVersion,
)
from codestrata_platform.domain.answering.lifecycle import AnswerStatus, GroundingStatus
from codestrata_platform.domain.errors import InvalidStateTransitionError
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio_answering.answer import PortfolioAnswerRun
from codestrata_platform.domain.portfolio_answering.citation import (
    PortfolioAnswerCitation,
    PortfolioAnswerConfidence,
)
from codestrata_platform.domain.portfolio_answering.errors import PortfolioAnsweringInvariantError
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
from codestrata_platform.domain.workspace.ids import WorkspaceId


def _pending_run() -> PortfolioAnswerRun:
    question = PortfolioQuestion(
        text="What systemic risks exist across repositories?",
        scope=PortfolioQuestionScope(
            organization_id="org:1",
            workspace_id="ws:1",
            portfolio_id="portfolio:1",
        ),
    )
    return PortfolioAnswerRun.create_pending(
        answer_run_id=PortfolioAnswerRunId("portfolio-answer:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
        organization_id=OrganizationId("org:1"),
        workspace_id=WorkspaceId("ws:1"),
        portfolio_id=PortfolioId("portfolio:1"),
        portfolio_snapshot_id=PortfolioSnapshotId("portfolio-snapshot:1"),
        portfolio_retrieval_index_id=PortfolioRetrievalIndexId(
            "portfolio-retrieval:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        ),
        portfolio_retrieval_index_version=1,
        question=question,
        question_type=PortfolioQuestionType.SYSTEMIC_RISK_EXPLANATION,
        normalized_question_hash=normalize_portfolio_question_hash(question.text),
        projection_key=PortfolioAnswerProjectionKey("a" * 64),
        provider_id="deterministic",
        model_id="deterministic-test-answer",
        prompt_template_version=PromptTemplateVersion("1.0.0"),
        answer_policy_version=AnswerPolicyVersion("1.0.0"),
    )


def test_portfolio_answer_lifecycle_and_immutability() -> None:
    run = _pending_run()
    run.begin_retrieval()
    run.attach_context(diagnostics={"chunk_count": "2"})
    run.begin_generation()
    run.attach_provider_response(
        provider_request_id=__import__(
            "codestrata_platform.domain.answering.identifiers",
            fromlist=["ProviderRequestId"],
        ).ProviderRequestId("req:1"),
    )
    citation = PortfolioAnswerCitation(
        citation_id=PortfolioAnswerCitationId("portfolio-answer-cite:abc:1"),
        label="[P1]",
        document_id="portfolio-retrieval-doc:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        chunk_id="portfolio-retrieval-chunk:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        content_type="systemic_risk",
        canonical_type="risk",
        canonical_id="risk:1",
        source_references=("portfolio_risk:risk:1",),
        repository_ids=("repo:1", "repo:2"),
        portfolio_id="portfolio:1",
        portfolio_snapshot_id="portfolio-snapshot:1",
        retrieval_score=0.9,
        excerpt="Systemic risk across repositories",
    )
    run.validate_grounding(
        answer_text=AnswerText("Systemic risk is present [P1]."),
        citations=(citation,),
        grounding=GroundingResult(status=GroundingStatus.GROUNDED, cited_labels=("[P1]",)),
        confidence=PortfolioAnswerConfidence(
            level=AnswerConfidenceLevel.HIGH,
            score=80,
            factors=("grounded",),
            policy_version="1.0.0",
        ),
        limitations=("Context may omit unavailable repositories.",),
    )
    run.complete()
    assert run.status is AnswerStatus.COMPLETED
    with pytest.raises(InvalidStateTransitionError):
        run.begin_retrieval()


def test_ungrounded_answer_cannot_complete() -> None:
    run = _pending_run()
    run.begin_retrieval()
    run.attach_context()
    run.validate_grounding(
        answer_text=AnswerText("Invented claim without citations."),
        citations=(),
        grounding=GroundingResult(status=GroundingStatus.UNGROUNDED),
        confidence=PortfolioAnswerConfidence(
            level=AnswerConfidenceLevel.LOW,
            score=10,
            factors=("ungrounded",),
            policy_version="1.0.0",
        ),
    )
    with pytest.raises(PortfolioAnsweringInvariantError):
        run.complete()


def test_projection_key_is_deterministic() -> None:
    kwargs = dict(
        organization_id="org:1",
        workspace_id="ws:1",
        portfolio_id="portfolio:1",
        portfolio_retrieval_index_id="portfolio-retrieval:1",
        portfolio_retrieval_index_version=2,
        normalized_question_hash="abc",
        question_type="portfolio_overview",
        retrieval_policy_version="1.0.0",
        prompt_template_version="1.0.0",
        answer_policy_version="1.0.0",
        provider_id="deterministic",
        model_id="deterministic-test-answer",
        temperature=0.1,
        max_output_tokens=1200,
    )
    first = PortfolioAnswerProjectionKey.from_parts(**kwargs)
    second = PortfolioAnswerProjectionKey.from_parts(**kwargs)
    assert first.value == second.value
