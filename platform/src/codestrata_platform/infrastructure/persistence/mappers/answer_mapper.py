"""EngineeringAnswerRun ↔ persistence mapper."""

from __future__ import annotations

from datetime import UTC, datetime

from codestrata_platform.domain.answering.answer import EngineeringAnswerRun
from codestrata_platform.domain.answering.citation import AnswerCitation, AnswerConfidence
from codestrata_platform.domain.answering.grounding import AnswerText, GroundingResult
from codestrata_platform.domain.answering.identifiers import (
    AnswerCitationId,
    AnswerPolicyVersion,
    AnswerProjectionKey,
    AnswerRunId,
    PromptTemplateVersion,
    ProviderRequestId,
)
from codestrata_platform.domain.answering.lifecycle import (
    AnswerConfidenceLevel,
    AnswerStatus,
    GroundingStatus,
    QuestionType,
)
from codestrata_platform.domain.answering.question import EngineeringQuestion, QuestionScope
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.identifiers import RetrievalIndexId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers._helpers import (
    audit_from_record,
    ensure_utc,
)
from codestrata_platform.infrastructure.persistence.models.answer_records import (
    EngineeringAnswerCitationRecord,
    EngineeringAnswerRunRecord,
)


class AnswerRunMapper:
    @staticmethod
    def to_record(run: EngineeringAnswerRun) -> EngineeringAnswerRunRecord:
        return EngineeringAnswerRunRecord(
            id=run.answer_run_id.value,
            organization_id=run.organization_id.value,
            workspace_id=run.workspace_id.value,
            repository_id=run.repository_id.value,
            assessment_id=run.assessment_id.value if run.assessment_id else None,
            retrieval_index_id=run.retrieval_index_id.value,
            retrieval_index_version=run.retrieval_index_version,
            engineering_snapshot_id=run.engineering_snapshot_id.value,
            knowledge_graph_id=run.knowledge_graph_id.value,
            question_type=run.question_type.value,
            question_text=run.question.text,
            normalized_question_hash=run.normalized_question_hash,
            status=run.status.value,
            projection_key=run.projection_key.value,
            provider_id=run.provider_id,
            model_id=run.model_id,
            prompt_template_version=run.prompt_template_version.value,
            answer_policy_version=run.answer_policy_version.value,
            grounding_status=run.grounding.status.value if run.grounding else None,
            confidence_level=run.confidence.level.value if run.confidence else None,
            confidence_score=run.confidence.score if run.confidence else None,
            answer_text=run.answer_text.value if run.answer_text else None,
            limitations=list(run.limitations),
            follow_up_questions=list(run.follow_up_questions),
            diagnostics=dict(run.diagnostics),
            usage_metadata=dict(run.usage_metadata),
            provider_request_id=(
                run.provider_request_id.value if run.provider_request_id else None
            ),
            created_at=run.audit.created_at.value,
            updated_at=run.audit.updated_at.value,
            completed_at=run.completed_at,
            failure_reason=run.failure_reason,
            optimistic_version=run._version,
        )

    @staticmethod
    def apply_to_record(run: EngineeringAnswerRun, record: EngineeringAnswerRunRecord) -> None:
        fresh = AnswerRunMapper.to_record(run)
        for column in EngineeringAnswerRunRecord.__table__.columns:
            if column.name == "id":
                continue
            setattr(record, column.name, getattr(fresh, column.name))

    @staticmethod
    def to_citation_records(
        run: EngineeringAnswerRun,
    ) -> list[EngineeringAnswerCitationRecord]:
        now = datetime.now(UTC)
        return [
            EngineeringAnswerCitationRecord(
                id=item.citation_id.value,
                answer_run_id=run.answer_run_id.value,
                label=item.label,
                retrieval_document_id=item.document_id,
                retrieval_chunk_id=item.chunk_id,
                content_type=item.content_type,
                canonical_type=item.canonical_type,
                canonical_id=item.canonical_id,
                source_references=list(item.source_references),
                graph_node_ids=list(item.graph_node_ids),
                graph_edge_ids=list(item.graph_edge_ids),
                retrieval_score=item.retrieval_score,
                excerpt=item.excerpt,
                created_at=now,
            )
            for item in run.citations
        ]

    @staticmethod
    def to_domain(
        record: EngineeringAnswerRunRecord,
        citations: list[EngineeringAnswerCitationRecord],
    ) -> EngineeringAnswerRun:
        domain_citations = tuple(
            AnswerCitation(
                citation_id=AnswerCitationId(item.id),
                label=item.label,
                document_id=item.retrieval_document_id,
                chunk_id=item.retrieval_chunk_id,
                content_type=item.content_type,
                canonical_type=item.canonical_type,
                canonical_id=item.canonical_id,
                source_references=tuple(item.source_references or ()),
                graph_node_ids=tuple(item.graph_node_ids or ()),
                graph_edge_ids=tuple(item.graph_edge_ids or ()),
                retrieval_score=float(item.retrieval_score),
                excerpt=item.excerpt,
            )
            for item in citations
        )
        confidence = None
        if record.confidence_level is not None and record.confidence_score is not None:
            confidence = AnswerConfidence(
                level=AnswerConfidenceLevel(record.confidence_level),
                score=record.confidence_score,
                factors=(),
                policy_version=record.answer_policy_version,
            )
        grounding = None
        if record.grounding_status is not None:
            grounding = GroundingResult(status=GroundingStatus(record.grounding_status))
        return EngineeringAnswerRun(
            answer_run_id=AnswerRunId(record.id),
            organization_id=OrganizationId(record.organization_id),
            workspace_id=WorkspaceId(record.workspace_id),
            repository_id=RepositoryId(record.repository_id),
            assessment_id=(
                AssessmentId(record.assessment_id) if record.assessment_id else None
            ),
            retrieval_index_id=RetrievalIndexId(record.retrieval_index_id),
            retrieval_index_version=record.retrieval_index_version,
            engineering_snapshot_id=EngineeringSnapshotId(record.engineering_snapshot_id),
            knowledge_graph_id=KnowledgeGraphId(record.knowledge_graph_id),
            question=EngineeringQuestion(
                text=record.question_text,
                scope=QuestionScope(
                    organization_id=record.organization_id,
                    workspace_id=record.workspace_id,
                    repository_id=record.repository_id,
                    retrieval_index_id=record.retrieval_index_id,
                ),
            ),
            question_type=QuestionType(record.question_type),
            normalized_question_hash=record.normalized_question_hash,
            status=AnswerStatus(record.status),
            projection_key=AnswerProjectionKey(record.projection_key),
            provider_id=record.provider_id,
            model_id=record.model_id,
            prompt_template_version=PromptTemplateVersion(record.prompt_template_version),
            answer_policy_version=AnswerPolicyVersion(record.answer_policy_version),
            citations=domain_citations,
            confidence=confidence,
            grounding=grounding,
            answer_text=AnswerText(record.answer_text) if record.answer_text else None,
            limitations=tuple(record.limitations or ()),
            follow_up_questions=tuple(record.follow_up_questions or ()),
            diagnostics=dict(record.diagnostics or {}),
            usage_metadata={
                str(key): int(value) for key, value in dict(record.usage_metadata or {}).items()
            },
            provider_request_id=(
                ProviderRequestId(record.provider_request_id)
                if record.provider_request_id
                else None
            ),
            audit=audit_from_record(
                created_at=record.created_at,
                updated_at=record.updated_at,
            ),
            completed_at=ensure_utc(record.completed_at) if record.completed_at else None,
            failure_reason=record.failure_reason,
            _version=record.optimistic_version,
        )
