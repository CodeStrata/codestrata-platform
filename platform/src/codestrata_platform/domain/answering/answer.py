"""EngineeringAnswerRun aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime

from codestrata_platform.domain.answering.citation import AnswerCitation, AnswerConfidence
from codestrata_platform.domain.answering.errors import AnsweringInvariantError
from codestrata_platform.domain.answering.grounding import AnswerText, GroundingResult
from codestrata_platform.domain.answering.identifiers import (
    AnswerPolicyVersion,
    AnswerProjectionKey,
    AnswerRunId,
    PromptTemplateVersion,
    ProviderRequestId,
)
from codestrata_platform.domain.answering.lifecycle import (
    AnswerStatus,
    GroundingStatus,
    QuestionType,
)
from codestrata_platform.domain.answering.question import EngineeringQuestion
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.errors import InvalidStateTransitionError, InvalidValueError
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.identifiers import RetrievalIndexId
from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(slots=True)
class EngineeringAnswerRun:
    """Immutable completed answer run over a Retrieval Index."""

    answer_run_id: AnswerRunId
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId
    assessment_id: AssessmentId | None
    retrieval_index_id: RetrievalIndexId
    retrieval_index_version: int
    engineering_snapshot_id: EngineeringSnapshotId
    knowledge_graph_id: KnowledgeGraphId
    question: EngineeringQuestion
    question_type: QuestionType
    normalized_question_hash: str
    status: AnswerStatus
    projection_key: AnswerProjectionKey
    provider_id: str
    model_id: str
    prompt_template_version: PromptTemplateVersion
    answer_policy_version: AnswerPolicyVersion
    citations: tuple[AnswerCitation, ...]
    confidence: AnswerConfidence | None
    grounding: GroundingResult | None
    answer_text: AnswerText | None
    limitations: tuple[str, ...]
    follow_up_questions: tuple[str, ...]
    diagnostics: dict[str, str]
    usage_metadata: dict[str, int]
    provider_request_id: ProviderRequestId | None
    audit: AuditInfo
    completed_at: datetime | None = None
    failure_reason: str | None = None
    _version: int = field(default=0, repr=False)

    @classmethod
    def create_pending(
        cls,
        *,
        answer_run_id: AnswerRunId,
        organization_id: OrganizationId,
        workspace_id: WorkspaceId,
        repository_id: RepositoryId,
        assessment_id: AssessmentId | None,
        retrieval_index_id: RetrievalIndexId,
        retrieval_index_version: int,
        engineering_snapshot_id: EngineeringSnapshotId,
        knowledge_graph_id: KnowledgeGraphId,
        question: EngineeringQuestion,
        question_type: QuestionType,
        normalized_question_hash: str,
        projection_key: AnswerProjectionKey,
        provider_id: str,
        model_id: str,
        prompt_template_version: PromptTemplateVersion,
        answer_policy_version: AnswerPolicyVersion,
    ) -> EngineeringAnswerRun:
        return cls(
            answer_run_id=answer_run_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            repository_id=repository_id,
            assessment_id=assessment_id,
            retrieval_index_id=retrieval_index_id,
            retrieval_index_version=retrieval_index_version,
            engineering_snapshot_id=engineering_snapshot_id,
            knowledge_graph_id=knowledge_graph_id,
            question=question,
            question_type=question_type,
            normalized_question_hash=normalized_question_hash,
            status=AnswerStatus.PENDING,
            projection_key=projection_key,
            provider_id=provider_id.strip(),
            model_id=model_id.strip(),
            prompt_template_version=prompt_template_version,
            answer_policy_version=answer_policy_version,
            citations=(),
            confidence=None,
            grounding=None,
            answer_text=None,
            limitations=(),
            follow_up_questions=(),
            diagnostics={},
            usage_metadata={},
            provider_request_id=None,
            audit=AuditInfo.create(),
        )

    def begin_retrieval(self) -> None:
        self._require_mutable()
        if self.status is not AnswerStatus.PENDING:
            raise InvalidStateTransitionError(
                f"Cannot begin retrieval from {self.status.value}",
                reason_code="invalid_begin_retrieval",
            )
        self.status = AnswerStatus.RETRIEVING
        self._touch()

    def attach_context(self, *, diagnostics: dict[str, str] | None = None) -> None:
        self._require_mutable()
        if self.status is not AnswerStatus.RETRIEVING:
            raise InvalidStateTransitionError(
                f"Cannot attach context from {self.status.value}",
                reason_code="invalid_attach_context",
            )
        self.status = AnswerStatus.CONTEXT_ATTACHED
        if diagnostics:
            self.diagnostics = {**self.diagnostics, **diagnostics}
        self._touch()

    def begin_generation(self) -> None:
        self._require_mutable()
        if self.status is not AnswerStatus.CONTEXT_ATTACHED:
            raise InvalidStateTransitionError(
                f"Cannot begin generation from {self.status.value}",
                reason_code="invalid_begin_generation",
            )
        self.status = AnswerStatus.GENERATING
        self._touch()

    def attach_provider_response(
        self,
        *,
        provider_request_id: ProviderRequestId,
        usage_metadata: dict[str, int] | None = None,
    ) -> None:
        self._require_mutable()
        if self.status is not AnswerStatus.GENERATING:
            raise InvalidStateTransitionError(
                f"Cannot attach provider response from {self.status.value}",
                reason_code="invalid_attach_provider_response",
            )
        self.provider_request_id = provider_request_id
        if usage_metadata:
            self.usage_metadata = dict(usage_metadata)
        self.status = AnswerStatus.VALIDATING
        self._touch()

    def validate_grounding(
        self,
        *,
        answer_text: AnswerText,
        citations: tuple[AnswerCitation, ...],
        grounding: GroundingResult,
        confidence: AnswerConfidence,
        limitations: tuple[str, ...] = (),
        follow_up_questions: tuple[str, ...] = (),
    ) -> None:
        self._require_mutable()
        if self.status not in {AnswerStatus.VALIDATING, AnswerStatus.CONTEXT_ATTACHED}:
            raise InvalidStateTransitionError(
                f"Cannot validate grounding from {self.status.value}",
                reason_code="invalid_validate_grounding",
            )
        self.answer_text = answer_text
        self.citations = citations
        self.grounding = grounding
        self.confidence = confidence
        self.limitations = tuple(item.strip() for item in limitations if item.strip())
        self.follow_up_questions = tuple(
            item.strip()[:240] for item in follow_up_questions if item.strip()
        )[:5]
        self.status = AnswerStatus.VALIDATING
        self._touch()

    def complete(self) -> None:
        self._require_mutable()
        if self.status is not AnswerStatus.VALIDATING:
            raise InvalidStateTransitionError(
                f"Cannot complete from {self.status.value}",
                reason_code="invalid_complete_answer",
            )
        if self.answer_text is None or self.grounding is None or self.confidence is None:
            raise AnsweringInvariantError(
                "Completed answers require text, grounding, and confidence",
                reason_code="incomplete_answer_payload",
            )
        if self.grounding.status is GroundingStatus.UNGROUNDED:
            raise AnsweringInvariantError(
                "Ungrounded answers cannot complete",
                reason_code="ungrounded_answer_blocked",
            )
        self.status = AnswerStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.failure_reason = None
        self._touch()

    def fail(self, reason: str) -> None:
        self._require_mutable()
        compact = reason.strip()
        if not compact:
            raise InvalidValueError(
                "failure reason must be non-blank",
                reason_code="empty_failure_reason",
            )
        self.status = AnswerStatus.FAILED
        self.failure_reason = compact[:1000]
        self.answer_text = None
        self.citations = ()
        self._touch()

    def reject(self, reason: str, *, limitations: tuple[str, ...] = ()) -> None:
        self._require_mutable()
        if self.status in {AnswerStatus.GENERATING, AnswerStatus.VALIDATING}:
            # Allowed: reject after generation due to grounding failure.
            pass
        elif self.status not in {
            AnswerStatus.PENDING,
            AnswerStatus.RETRIEVING,
            AnswerStatus.CONTEXT_ATTACHED,
        }:
            raise InvalidStateTransitionError(
                f"Cannot reject from {self.status.value}",
                reason_code="invalid_reject_answer",
            )
        compact = reason.strip()
        if not compact:
            raise InvalidValueError(
                "rejection reason must be non-blank",
                reason_code="empty_rejection_reason",
            )
        self.status = AnswerStatus.REJECTED
        self.failure_reason = compact[:1000]
        self.limitations = tuple(item.strip() for item in limitations if item.strip())
        self.answer_text = None
        self.citations = ()
        self.grounding = GroundingResult(status=GroundingStatus.INSUFFICIENT_CONTEXT)
        self._touch()

    def snapshot(self) -> EngineeringAnswerRun:
        return replace(self)

    def _require_mutable(self) -> None:
        if self.status is AnswerStatus.COMPLETED:
            raise InvalidStateTransitionError(
                "Completed answers are immutable",
                reason_code="answer_immutable",
            )
        if self.status in {AnswerStatus.FAILED, AnswerStatus.REJECTED}:
            raise InvalidStateTransitionError(
                f"Answer in status {self.status.value} is immutable",
                reason_code="answer_immutable",
            )

    def _touch(self) -> None:
        self.audit = self.audit.touch()
        self._version += 1
