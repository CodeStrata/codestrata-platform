"""Engineering answering orchestration service."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.application.answering.citations import ContextSufficiencyPolicy
from codestrata_platform.application.answering.commands import (
    AskEngineeringQuestionCommand,
    GetAnswerRunQuery,
    ListRepositoryAnswersQuery,
    SubmitAnswerFeedbackCommand,
)
from codestrata_platform.application.answering.errors import (
    AnsweringConfigurationError,
    AnsweringDisabledError,
    AnsweringGroundingError,
    AnsweringNotReadyError,
)
from codestrata_platform.application.answering.grounding import AnswerGroundingValidator
from codestrata_platform.application.answering.models import EngineeringAnswerModel
from codestrata_platform.application.answering.orchestration import DefaultAnswerRetrievalStrategy
from codestrata_platform.application.answering.policies import (
    answering_enabled,
    configured_llm_model,
    configured_llm_provider,
    default_answering_policy,
)
from codestrata_platform.application.answering.prompting import DefaultPromptRenderer
from codestrata_platform.application.answering.validation import QuestionClassificationService
from codestrata_platform.application.common.errors import NotFoundError, ValidationError
from codestrata_platform.application.retrieval.models import RetrievalIndexDetails
from codestrata_platform.application.retrieval.queries import (
    AssembleRetrievalContextQuery,
    GetLatestRepositoryRetrievalIndexQuery,
    GetRetrievalIndexQuery,
)
from codestrata_platform.application.retrieval.services import EngineeringRetrievalIndexingService
from codestrata_platform.domain.answering.answer import EngineeringAnswerRun
from codestrata_platform.domain.answering.grounding import AnswerText, GroundingResult
from codestrata_platform.domain.answering.identifiers import (
    AnswerProjectionKey,
    deterministic_answer_run_id,
    normalize_question_hash,
)
from codestrata_platform.domain.answering.lifecycle import (
    AnswerStatus,
    ContextSufficiencyStatus,
    GroundingStatus,
)
from codestrata_platform.domain.answering.ports import LLMGenerateRequest, LLMProvider
from codestrata_platform.domain.answering.question import EngineeringQuestion, QuestionScope
from codestrata_platform.domain.answering.repository import AnswerRunRepository
from codestrata_platform.domain.assessment.ids import AssessmentId
from codestrata_platform.domain.engineering.ids import EngineeringSnapshotId
from codestrata_platform.domain.knowledge_graph.identifiers import KnowledgeGraphId
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.retrieval.identifiers import RetrievalIndexId
from codestrata_platform.domain.retrieval.lifecycle import RetrievalIndexStatus
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class _ResolvedIndex:
    details: RetrievalIndexDetails
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    repository_id: RepositoryId
    assessment_id: AssessmentId
    snapshot_id: EngineeringSnapshotId
    graph_id: KnowledgeGraphId
    index_id: RetrievalIndexId


class EngineeringAnswerOrchestrationService:
    """Orchestrate retrieval-context grounded LLM answering."""

    def __init__(
        self,
        *,
        answers: AnswerRunRepository,
        retrieval: EngineeringRetrievalIndexingService,
        llm: LLMProvider,
        classifier: QuestionClassificationService | None = None,
        strategy: DefaultAnswerRetrievalStrategy | None = None,
        prompt_renderer: DefaultPromptRenderer | None = None,
        sufficiency: ContextSufficiencyPolicy | None = None,
        grounding: AnswerGroundingValidator | None = None,
    ) -> None:
        self._answers = answers
        self._retrieval = retrieval
        self._llm = llm
        self._classifier = classifier or QuestionClassificationService()
        self._strategy = strategy or DefaultAnswerRetrievalStrategy()
        self._prompts = prompt_renderer or DefaultPromptRenderer()
        self._sufficiency = sufficiency or ContextSufficiencyPolicy()
        self._grounding = grounding or AnswerGroundingValidator()
        self._feedback: dict[str, list[dict[str, object]]] = {}

    def ask(self, command: AskEngineeringQuestionCommand) -> EngineeringAnswerModel:
        if not answering_enabled():
            raise AnsweringDisabledError(
                "Engineering answering is disabled",
                reason_code="answering_disabled",
            )
        try:
            policy = default_answering_policy()
            provider = configured_llm_provider()
            _ = configured_llm_model()
        except ValueError as error:
            raise AnsweringConfigurationError(
                "Invalid answering configuration",
                reason_code="invalid_answering_configuration",
            ) from error
        if provider != self._llm.provider_id():
            raise AnsweringConfigurationError(
                "Configured LLM provider does not match wired provider",
                reason_code="llm_provider_mismatch",
            )

        resolved = self._resolve_index(command)
        question_type = self._classifier.classify(
            command.question,
            override=command.question_type,
        )
        scope = QuestionScope(
            organization_id=resolved.organization_id.value,
            workspace_id=resolved.workspace_id.value,
            repository_id=resolved.repository_id.value,
            retrieval_index_id=resolved.index_id.value,
            canonical_ids=command.scope.canonical_ids,
            graph_node_ids=command.scope.graph_node_ids,
            content_types=command.scope.content_types,
            severity=command.scope.severity,
            category=command.scope.category,
        )
        if (
            command.scope.organization_id != resolved.organization_id.value
            or command.scope.workspace_id != resolved.workspace_id.value
            or command.scope.repository_id != resolved.repository_id.value
        ):
            raise ValidationError(
                "Question scope does not match retrieval index ownership",
                reason_code="answer_scope_mismatch",
            )
        question = EngineeringQuestion(
            text=command.question,
            scope=scope,
            question_type=question_type,
        )
        question_hash = normalize_question_hash(question.text)
        projection_key = AnswerProjectionKey.from_parts(
            organization_id=scope.organization_id,
            workspace_id=scope.workspace_id,
            repository_id=scope.repository_id,
            retrieval_index_id=resolved.index_id.value,
            retrieval_index_version=resolved.details.index_version,
            normalized_question_hash=question_hash,
            question_type=question_type.value,
            retrieval_policy_version=policy.retrieval_policy_version,
            prompt_template_version=policy.prompt_template_version.value,
            answer_policy_version=policy.answer_policy_version.value,
            provider_id=self._llm.provider_id(),
            model_id=self._llm.model_id(),
            temperature=policy.generation.temperature,
            max_output_tokens=policy.generation.max_output_tokens,
        )
        if command.use_cache and policy.cache_enabled:
            cached = self._answers.find_by_projection_key(projection_key.value)
            if cached is not None and cached.status is AnswerStatus.COMPLETED:
                return EngineeringAnswerModel.from_aggregate(
                    cached,
                    cache_hit=True,
                    include_diagnostics=command.include_diagnostics,
                )

        run = EngineeringAnswerRun.create_pending(
            answer_run_id=deterministic_answer_run_id(
                repository_id=scope.repository_id,
                retrieval_index_id=resolved.index_id.value,
                projection_key=projection_key.value,
            ),
            organization_id=resolved.organization_id,
            workspace_id=resolved.workspace_id,
            repository_id=resolved.repository_id,
            assessment_id=resolved.assessment_id,
            retrieval_index_id=resolved.index_id,
            retrieval_index_version=resolved.details.index_version,
            engineering_snapshot_id=resolved.snapshot_id,
            knowledge_graph_id=resolved.graph_id,
            question=question,
            question_type=question_type,
            normalized_question_hash=question_hash,
            projection_key=projection_key,
            provider_id=self._llm.provider_id(),
            model_id=self._llm.model_id(),
            prompt_template_version=policy.prompt_template_version,
            answer_policy_version=policy.answer_policy_version,
        )
        run.begin_retrieval()
        try:
            plan = self._strategy.plan(question_type=question_type, scope=scope)
            context = self._retrieval.assemble_context(
                AssembleRetrievalContextQuery(
                    index_id=resolved.index_id,
                    query_text=question.text,
                    mode=plan.mode,
                    top_k=plan.top_k,
                    content_types=plan.content_types,
                )
            )
            sufficiency = self._sufficiency.evaluate(
                question_type=question_type,
                context=context,
            )
            run.attach_context(
                diagnostics={
                    "chunk_count": str(len(context.items)),
                    "token_estimate": str(context.token_estimate),
                    "sufficiency": sufficiency.status.value,
                }
            )
            if sufficiency.status is ContextSufficiencyStatus.INSUFFICIENT:
                limitation = (
                    "Insufficient retrieved context to answer safely. "
                    "Run a newer assessment or refine the question."
                )
                from codestrata_platform.domain.answering.citation import AnswerConfidence
                from codestrata_platform.domain.answering.lifecycle import AnswerConfidenceLevel

                run.validate_grounding(
                    answer_text=AnswerText(limitation),
                    citations=(),
                    grounding=GroundingResult(status=GroundingStatus.INSUFFICIENT_CONTEXT),
                    confidence=AnswerConfidence(
                        level=AnswerConfidenceLevel.LOW,
                        score=20,
                        factors=("insufficient_context",),
                        policy_version=policy.answer_policy_version.value,
                    ),
                    limitations=(limitation, *sufficiency.missing),
                )
                run.complete()
                self._answers.save(run)
                return EngineeringAnswerModel.from_aggregate(
                    run,
                    include_diagnostics=command.include_diagnostics,
                )

            rendered = self._prompts.render(
                question=question.text,
                question_type=question_type,
                context=context,
            )
            if rendered.injection_flags:
                run.diagnostics = {
                    **run.diagnostics,
                    "injection_flags": ",".join(rendered.injection_flags)[:500],
                }
            run.begin_generation()
            provider_result = self._llm.generate(
                LLMGenerateRequest(
                    system_instruction=rendered.system_instruction,
                    user_question=rendered.user_prompt,
                    retrieval_context="<see user prompt>",
                    parameters=policy.generation,
                    metadata={"question_type": question_type.value},
                )
            )
            run.attach_provider_response(
                provider_request_id=provider_result.provider_request_id,
                usage_metadata=dict(provider_result.usage_metadata),
            )
            answer_text, citations, grounding, confidence = self._grounding.validate(
                generated_text=provider_result.generated_text,
                context=context,
                sufficiency=sufficiency.status,
            )
            if grounding.status is GroundingStatus.UNGROUNDED:
                run.validate_grounding(
                    answer_text=answer_text,
                    citations=citations,
                    grounding=grounding,
                    confidence=confidence,
                    limitations=("Generated answer failed grounding validation.",),
                )
                run.reject(
                    "ungrounded_answer",
                    limitations=("Generated answer failed grounding validation.",),
                )
                self._answers.save(run)
                raise AnsweringGroundingError(
                    "Generated answer was ungrounded and rejected",
                    reason_code="ungrounded_answer",
                )
            limitations: list[str] = []
            if sufficiency.status is ContextSufficiencyStatus.PARTIAL:
                limitations.append("Context was only partially sufficient for this question.")
            if grounding.status is GroundingStatus.PARTIALLY_GROUNDED:
                limitations.append("Answer is only partially grounded in retrieved citations.")
            if rendered.injection_flags:
                limitations.append(
                    "Retrieved context contained prompt-injection phrases treated as data only."
                )
            follow_ups = (
                "Which finding has the strongest evidence?",
                "What recommendations address the highest-risk findings?",
                "Which components are most impacted?",
            )
            run.validate_grounding(
                answer_text=answer_text,
                citations=citations,
                grounding=grounding,
                confidence=confidence,
                limitations=tuple(limitations),
                follow_up_questions=follow_ups,
            )
            run.complete()
            self._answers.save(run)
            return EngineeringAnswerModel.from_aggregate(
                run,
                include_diagnostics=command.include_diagnostics,
            )
        except AnsweringGroundingError:
            raise
        except Exception as error:  # noqa: BLE001 - orchestration boundary
            if run.status not in {AnswerStatus.FAILED, AnswerStatus.REJECTED}:
                try:
                    run.fail(str(error)[:1000])
                    self._answers.save(run)
                except Exception:  # noqa: BLE001
                    pass
            raise ValidationError(
                f"Answering failed: {error}",
                reason_code="answering_failed",
            ) from error

    def get_answer(self, query: GetAnswerRunQuery) -> EngineeringAnswerModel:
        run = self._answers.get(query.answer_run_id)
        if run is None:
            raise NotFoundError(
                f"Answer run not found: {query.answer_run_id.value}",
                reason_code="answer_run_not_found",
            )
        return EngineeringAnswerModel.from_aggregate(run)

    def list_repository_answers(
        self,
        query: ListRepositoryAnswersQuery,
    ) -> tuple[EngineeringAnswerModel, ...]:
        items = self._answers.list_by_repository(query.repository_id, limit=query.limit)
        return tuple(EngineeringAnswerModel.from_aggregate(item) for item in items)

    def submit_feedback(self, command: SubmitAnswerFeedbackCommand) -> dict[str, object]:
        run = self._answers.get(command.answer_run_id)
        if run is None:
            raise NotFoundError(
                f"Answer run not found: {command.answer_run_id.value}",
                reason_code="answer_run_not_found",
            )
        if command.rating < 1 or command.rating > 5:
            raise ValidationError(
                "rating must be between 1 and 5",
                reason_code="invalid_answer_feedback_rating",
            )
        category = command.feedback_category.strip()
        if not category:
            raise ValidationError(
                "feedback_category must be non-blank",
                reason_code="empty_feedback_category",
            )
        payload: dict[str, object] = {
            "answer_run_id": command.answer_run_id.value,
            "rating": command.rating,
            "feedback_category": category[:64],
            "comment": command.comment.strip()[:1000],
        }
        self._feedback.setdefault(command.answer_run_id.value, []).append(payload)
        return payload

    def _resolve_index(self, command: AskEngineeringQuestionCommand) -> _ResolvedIndex:
        if command.retrieval_index_id is not None:
            details = self._retrieval.get_retrieval_index(
                GetRetrievalIndexQuery(index_id=command.retrieval_index_id)
            )
        else:
            details = self._retrieval.get_latest_repository_index(
                GetLatestRepositoryRetrievalIndexQuery(
                    repository_id=RepositoryId(command.scope.repository_id)
                )
            )
        if details.status is not RetrievalIndexStatus.COMPLETED:
            raise AnsweringNotReadyError(
                "Answering requires a completed retrieval index",
                reason_code="retrieval_index_not_completed",
            )
        return _ResolvedIndex(
            details=details,
            organization_id=OrganizationId(details.organization_id),
            workspace_id=WorkspaceId(details.workspace_id),
            repository_id=RepositoryId(details.repository_id),
            assessment_id=AssessmentId(details.assessment_id),
            snapshot_id=EngineeringSnapshotId(details.engineering_snapshot_id),
            graph_id=KnowledgeGraphId(details.knowledge_graph_id),
            index_id=RetrievalIndexId(details.index_id),
        )
