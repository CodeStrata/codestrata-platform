"""PortfolioAnswerRun ↔ persistence mapper."""

from __future__ import annotations

from datetime import UTC, datetime

from codestrata_platform.domain.answering.grounding import AnswerText, GroundingResult
from codestrata_platform.domain.answering.identifiers import (
    AnswerPolicyVersion,
    PromptTemplateVersion,
    ProviderRequestId,
)
from codestrata_platform.domain.answering.lifecycle import (
    AnswerConfidenceLevel,
    AnswerStatus,
    GroundingStatus,
)
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio_answering.answer import PortfolioAnswerRun
from codestrata_platform.domain.portfolio_answering.citation import (
    PortfolioAnswerCitation,
    PortfolioAnswerConfidence,
)
from codestrata_platform.domain.portfolio_answering.identifiers import (
    PortfolioAnswerCitationId,
    PortfolioAnswerProjectionKey,
    PortfolioAnswerRunId,
)
from codestrata_platform.domain.portfolio_answering.lifecycle import PortfolioQuestionType
from codestrata_platform.domain.portfolio_answering.question import (
    PortfolioQuestion,
    PortfolioQuestionScope,
)
from codestrata_platform.domain.portfolio_retrieval.identifiers import PortfolioRetrievalIndexId
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.infrastructure.persistence.mappers._helpers import (
    audit_from_record,
    ensure_utc,
)
from codestrata_platform.infrastructure.persistence.models.portfolio_answer_records import (
    EngineeringPortfolioAnswerCitationRecord,
    EngineeringPortfolioAnswerRunRecord,
)


class PortfolioAnswerRunMapper:
    @staticmethod
    def to_record(run: PortfolioAnswerRun) -> EngineeringPortfolioAnswerRunRecord:
        return EngineeringPortfolioAnswerRunRecord(
            id=run.answer_run_id.value,
            organization_id=run.organization_id.value,
            workspace_id=run.workspace_id.value,
            portfolio_id=run.portfolio_id.value,
            portfolio_snapshot_id=run.portfolio_snapshot_id.value,
            portfolio_retrieval_index_id=run.portfolio_retrieval_index_id.value,
            portfolio_retrieval_index_version=run.portfolio_retrieval_index_version,
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
    def apply_to_record(
        run: PortfolioAnswerRun,
        record: EngineeringPortfolioAnswerRunRecord,
    ) -> None:
        fresh = PortfolioAnswerRunMapper.to_record(run)
        for column in EngineeringPortfolioAnswerRunRecord.__table__.columns:
            if column.name == "id":
                continue
            setattr(record, column.name, getattr(fresh, column.name))

    @staticmethod
    def to_citation_records(
        run: PortfolioAnswerRun,
    ) -> list[EngineeringPortfolioAnswerCitationRecord]:
        now = datetime.now(UTC)
        return [
            EngineeringPortfolioAnswerCitationRecord(
                id=item.citation_id.value,
                answer_run_id=run.answer_run_id.value,
                label=item.label,
                retrieval_document_id=item.document_id,
                retrieval_chunk_id=item.chunk_id,
                content_type=item.content_type,
                canonical_type=item.canonical_type,
                canonical_id=item.canonical_id,
                source_references=list(item.source_references),
                repository_ids=list(item.repository_ids),
                portfolio_id=item.portfolio_id,
                portfolio_snapshot_id=item.portfolio_snapshot_id,
                retrieval_score=item.retrieval_score,
                excerpt=item.excerpt,
                created_at=now,
            )
            for item in run.citations
        ]

    @staticmethod
    def to_domain(
        record: EngineeringPortfolioAnswerRunRecord,
        citations: list[EngineeringPortfolioAnswerCitationRecord],
    ) -> PortfolioAnswerRun:
        domain_citations = tuple(
            PortfolioAnswerCitation(
                citation_id=PortfolioAnswerCitationId(item.id),
                label=item.label,
                document_id=item.retrieval_document_id,
                chunk_id=item.retrieval_chunk_id,
                content_type=item.content_type,
                canonical_type=item.canonical_type,
                canonical_id=item.canonical_id,
                source_references=tuple(item.source_references or ()),
                repository_ids=tuple(item.repository_ids or ()),
                portfolio_id=item.portfolio_id,
                portfolio_snapshot_id=item.portfolio_snapshot_id,
                retrieval_score=float(item.retrieval_score),
                excerpt=item.excerpt,
            )
            for item in citations
        )
        confidence = None
        if record.confidence_level is not None and record.confidence_score is not None:
            confidence = PortfolioAnswerConfidence(
                level=AnswerConfidenceLevel(record.confidence_level),
                score=record.confidence_score,
                factors=(),
                policy_version=record.answer_policy_version,
            )
        grounding = None
        if record.grounding_status is not None:
            grounding = GroundingResult(status=GroundingStatus(record.grounding_status))
        return PortfolioAnswerRun(
            answer_run_id=PortfolioAnswerRunId(record.id),
            organization_id=OrganizationId(record.organization_id),
            workspace_id=WorkspaceId(record.workspace_id),
            portfolio_id=PortfolioId(record.portfolio_id),
            portfolio_snapshot_id=PortfolioSnapshotId(record.portfolio_snapshot_id),
            portfolio_retrieval_index_id=PortfolioRetrievalIndexId(
                record.portfolio_retrieval_index_id
            ),
            portfolio_retrieval_index_version=record.portfolio_retrieval_index_version,
            question=PortfolioQuestion(
                text=record.question_text,
                scope=PortfolioQuestionScope(
                    organization_id=record.organization_id,
                    workspace_id=record.workspace_id,
                    portfolio_id=record.portfolio_id,
                    portfolio_retrieval_index_id=record.portfolio_retrieval_index_id,
                ),
            ),
            question_type=PortfolioQuestionType(record.question_type),
            normalized_question_hash=record.normalized_question_hash,
            status=AnswerStatus(record.status),
            projection_key=PortfolioAnswerProjectionKey(record.projection_key),
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
