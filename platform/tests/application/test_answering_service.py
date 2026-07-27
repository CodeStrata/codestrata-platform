"""Application tests for engineering answering."""

from __future__ import annotations

import pytest

from codestrata_platform.application.answering.commands import AskEngineeringQuestionCommand
from codestrata_platform.application.answering.errors import AnsweringDisabledError
from codestrata_platform.application.answering.policies import answering_enabled
from codestrata_platform.application.answering.services import EngineeringAnswerOrchestrationService
from codestrata_platform.application.answering.validation import QuestionClassificationService
from codestrata_platform.application.knowledge_graph.commands import BuildKnowledgeGraphCommand
from codestrata_platform.application.knowledge_graph.services import (
    EngineeringGraphProjectionService,
)
from codestrata_platform.application.retrieval.commands import BuildRetrievalIndexCommand
from codestrata_platform.application.retrieval.services import EngineeringRetrievalIndexingService
from codestrata_platform.domain.answering.lifecycle import QuestionType
from codestrata_platform.domain.answering.question import QuestionScope
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering import (
    EngineeringCategory,
    EngineeringEvidence,
    EngineeringFinding,
    EngineeringMetric,
    EngineeringMetricKind,
    EngineeringRecommendation,
    EngineeringRelationship,
    EngineeringRelationshipType,
    EngineeringSeverity,
    EngineeringSnapshot,
    EngineeringTechnology,
    EvidenceKind,
)
from codestrata_platform.domain.engineering.ids import (
    EngineeringEvidenceId,
    EngineeringFindingId,
    EngineeringMetricId,
    EngineeringRecommendationId,
    EngineeringRelationshipId,
    EngineeringSnapshotId,
    EngineeringTechnologyId,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.answering import DeterministicLLMProvider
from codestrata_platform.infrastructure.memory import (
    InMemoryAnswerRunRepository,
    InMemoryEngineeringSnapshotRepository,
    InMemoryKnowledgeGraphRepository,
    InMemoryRetrievalRepository,
)
from codestrata_platform.infrastructure.retrieval.embeddings import DeterministicEmbeddingProvider


def _published_snapshot() -> EngineeringSnapshot:
    snapshot = EngineeringSnapshot.create(
        organization_id=OrganizationId("org:1"),
        workspace_id=WorkspaceId("workspace:1"),
        repository_id=RepositoryId("repo:1"),
        assessment_id=AssessmentId("assessment:1"),
        assessment_intelligence_id="intelligence:1",
        assessment_revision=1,
        version=1,
        source_artifact_ids=("artifact:1",),
        snapshot_id=EngineeringSnapshotId("eng-snapshot:answer1"),
    )
    finding_id = EngineeringFindingId("eng-finding:1")
    evidence_id = EngineeringEvidenceId("eng-evidence:1")
    recommendation_id = EngineeringRecommendationId("eng-recommendation:1")
    technology = EngineeringTechnology(
        technology_id=EngineeringTechnologyId("eng-tech:1"),
        canonical_key="docker",
        display_name="Docker",
        category=EngineeringCategory.CLOUD,
    )
    finding = EngineeringFinding(
        finding_id=finding_id,
        source_finding_id="finding:1",
        category=EngineeringCategory.SECURITY,
        severity=EngineeringSeverity.CRITICAL,
        title="Privileged container",
        summary="Runs privileged.",
        rule_id="rule.docker.hardening",
        confidence=0.95,
        evidence_ids=(evidence_id.value,),
    )
    evidence = EngineeringEvidence(
        evidence_id=evidence_id,
        kind=EvidenceKind.FILE,
        reference="deploy/compose.yml",
        line_start=4,
    )
    recommendation = EngineeringRecommendation(
        recommendation_id=recommendation_id,
        source_recommendation_id="recommendation:1",
        title="Drop privileged mode",
        rationale="Remove privileged true from compose.",
        category=EngineeringCategory.SECURITY,
        severity=EngineeringSeverity.HIGH,
        priority="p1",
        related_finding_ids=("finding:1",),
    )
    metric = EngineeringMetric(
        metric_id=EngineeringMetricId("eng-metric:1"),
        name="security.findings.critical",
        kind=EngineeringMetricKind.COUNT,
        value="1",
    )
    relationship = EngineeringRelationship(
        relationship_id=EngineeringRelationshipId("eng-rel:1"),
        relationship_type=EngineeringRelationshipType.USES,
        source_type="repository",
        source_id=snapshot.repository_id.value,
        target_type="technology",
        target_id="docker",
    )
    snapshot.build(
        technologies=(technology,),
        findings=(finding,),
        evidence=(evidence,),
        recommendations=(recommendation,),
        metrics=(metric,),
        relationships=(relationship,),
    )
    snapshot.publish()
    return snapshot


def _answering_stack():
    snapshots = InMemoryEngineeringSnapshotRepository()
    graphs = InMemoryKnowledgeGraphRepository()
    embeddings = DeterministicEmbeddingProvider()
    indexes = InMemoryRetrievalRepository(embeddings=embeddings)
    answers = InMemoryAnswerRunRepository()
    snapshot = _published_snapshot()
    snapshots.save(snapshot)
    EngineeringGraphProjectionService(
        graphs=graphs,
        snapshots=snapshots,
        queries=graphs,
    ).build_knowledge_graph(BuildKnowledgeGraphCommand(snapshot_id=snapshot.snapshot_id))
    retrieval = EngineeringRetrievalIndexingService(
        indexes=indexes,
        snapshots=snapshots,
        graphs=graphs,
        embeddings=embeddings,
        queries=indexes,
    )
    retrieval.build_retrieval_index(BuildRetrievalIndexCommand(snapshot_id=snapshot.snapshot_id))
    answering = EngineeringAnswerOrchestrationService(
        answers=answers,
        retrieval=retrieval,
        llm=DeterministicLLMProvider(),
    )
    return answering, snapshot


def test_classification_rules() -> None:
    service = QuestionClassificationService()
    assert (
        service.classify("What is the impact of this technology?")
        is QuestionType.TECHNOLOGY_IMPACT
    )
    assert service.classify("Explain this finding severity") is QuestionType.FINDING_EXPLANATION
    assert service.classify("Why is this recommendation important?") is (
        QuestionType.RECOMMENDATION_EXPLANATION
    )


def test_ask_returns_grounded_cited_answer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODESTRATA_ANSWERING_ENABLED", "true")
    monkeypatch.setenv("CODESTRATA_LLM_PROVIDER", "deterministic")
    answering, snapshot = _answering_stack()
    result = answering.ask(
        AskEngineeringQuestionCommand(
            question="What are the highest-risk findings?",
            scope=QuestionScope(
                organization_id=snapshot.organization_id.value,
                workspace_id=snapshot.workspace_id.value,
                repository_id=snapshot.repository_id.value,
            ),
        )
    )
    assert result.answer
    assert result.citations
    assert result.grounding_status is not None
    assert "[C" in result.answer or result.citations
    again = answering.ask(
        AskEngineeringQuestionCommand(
            question="What are the highest-risk findings?",
            scope=QuestionScope(
                organization_id=snapshot.organization_id.value,
                workspace_id=snapshot.workspace_id.value,
                repository_id=snapshot.repository_id.value,
            ),
            use_cache=True,
        )
    )
    assert again.cache_hit is True


def test_answering_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CODESTRATA_ANSWERING_ENABLED", raising=False)
    assert answering_enabled() is False
    answering, snapshot = _answering_stack()
    with pytest.raises(AnsweringDisabledError):
        answering.ask(
            AskEngineeringQuestionCommand(
                question="What are the highest-risk findings?",
                scope=QuestionScope(
                    organization_id=snapshot.organization_id.value,
                    workspace_id=snapshot.workspace_id.value,
                    repository_id=snapshot.repository_id.value,
                ),
            )
        )
