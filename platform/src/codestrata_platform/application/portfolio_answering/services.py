"""Portfolio answering orchestration service."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.application.common.diagnostics import safe_failure_summary
from codestrata_platform.application.common.errors import NotFoundError, ValidationError
from codestrata_platform.application.portfolio_answering.citations import (
    PortfolioContextSufficiencyPolicy,
)
from codestrata_platform.application.portfolio_answering.commands import (
    AskPortfolioQuestionCommand,
    GetPortfolioAnswerRunQuery,
    ListPortfolioAnswersQuery,
    SubmitPortfolioAnswerFeedbackCommand,
)
from codestrata_platform.application.portfolio_answering.errors import (
    PortfolioAnsweringConfigurationError,
    PortfolioAnsweringDisabledError,
    PortfolioAnsweringGroundingError,
    PortfolioAnsweringNotReadyError,
)
from codestrata_platform.application.portfolio_answering.grounding import (
    PortfolioAnswerGroundingValidator,
)
from codestrata_platform.application.portfolio_answering.models import PortfolioAnswerModel
from codestrata_platform.application.portfolio_answering.orchestration import (
    DefaultPortfolioAnswerRetrievalStrategy,
)
from codestrata_platform.application.portfolio_answering.policies import (
    configured_llm_model,
    configured_llm_provider,
    default_portfolio_answering_policy,
    portfolio_answering_enabled,
)
from codestrata_platform.application.portfolio_answering.prompting import (
    DefaultPortfolioPromptRenderer,
)
from codestrata_platform.application.portfolio_answering.validation import (
    PortfolioQuestionClassificationService,
)
from codestrata_platform.application.portfolio_retrieval.models import (
    PortfolioRetrievalIndexDetails,
)
from codestrata_platform.application.portfolio_retrieval.queries import (
    BuildPortfolioRetrievalContextQuery,
    GetLatestPortfolioRetrievalIndexQuery,
    GetPortfolioRetrievalIndexQuery,
)
from codestrata_platform.application.portfolio_retrieval.services import (
    PortfolioRetrievalIndexingService,
)
from codestrata_platform.domain.answering.grounding import AnswerText, GroundingResult
from codestrata_platform.domain.answering.lifecycle import (
    AnswerStatus,
    ContextSufficiencyStatus,
    GroundingStatus,
)
from codestrata_platform.domain.answering.ports import LLMGenerateRequest, LLMProvider
from codestrata_platform.domain.organization.ids import OrganizationId
from codestrata_platform.domain.portfolio.identifiers import PortfolioId, PortfolioSnapshotId
from codestrata_platform.domain.portfolio_answering.answer import PortfolioAnswerRun
from codestrata_platform.domain.portfolio_answering.citation import PortfolioAnswerConfidence
from codestrata_platform.domain.portfolio_answering.identifiers import (
    PortfolioAnswerProjectionKey,
    deterministic_portfolio_answer_run_id,
    normalize_portfolio_question_hash,
)
from codestrata_platform.domain.portfolio_answering.lifecycle import AnswerConfidenceLevel
from codestrata_platform.domain.portfolio_answering.question import (
    PortfolioQuestion,
    PortfolioQuestionScope,
)
from codestrata_platform.domain.portfolio_answering.repository import PortfolioAnswerRunRepository
from codestrata_platform.domain.portfolio_retrieval.identifiers import PortfolioRetrievalIndexId
from codestrata_platform.domain.portfolio_retrieval.lifecycle import PortfolioRetrievalIndexStatus
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class _ResolvedIndex:
    details: PortfolioRetrievalIndexDetails
    organization_id: OrganizationId
    workspace_id: WorkspaceId
    portfolio_id: PortfolioId
    snapshot_id: PortfolioSnapshotId
    index_id: PortfolioRetrievalIndexId


class PortfolioAnswerOrchestrationService:
    """Orchestrate Portfolio Retrieval Context grounded LLM answering."""

    def __init__(
        self,
        *,
        answers: PortfolioAnswerRunRepository,
        portfolio_retrieval: PortfolioRetrievalIndexingService,
        llm: LLMProvider,
        classifier: PortfolioQuestionClassificationService | None = None,
        strategy: DefaultPortfolioAnswerRetrievalStrategy | None = None,
        prompt_renderer: DefaultPortfolioPromptRenderer | None = None,
        sufficiency: PortfolioContextSufficiencyPolicy | None = None,
        grounding: PortfolioAnswerGroundingValidator | None = None,
    ) -> None:
        self._answers = answers
        self._portfolio_retrieval = portfolio_retrieval
        self._llm = llm
        self._classifier = classifier or PortfolioQuestionClassificationService()
        self._strategy = strategy or DefaultPortfolioAnswerRetrievalStrategy()
        self._prompts = prompt_renderer or DefaultPortfolioPromptRenderer()
        self._sufficiency = sufficiency or PortfolioContextSufficiencyPolicy()
        self._grounding = grounding or PortfolioAnswerGroundingValidator()

    def ask(self, command: AskPortfolioQuestionCommand) -> PortfolioAnswerModel:
        if not portfolio_answering_enabled():
            raise PortfolioAnsweringDisabledError(
                "Portfolio answering is disabled",
                reason_code="portfolio_answering_disabled",
            )
        try:
            policy = default_portfolio_answering_policy()
            provider = configured_llm_provider()
            _ = configured_llm_model()
        except ValueError as error:
            raise PortfolioAnsweringConfigurationError(
                "Invalid portfolio answering configuration",
                reason_code="invalid_portfolio_answering_configuration",
            ) from error
        if provider != self._llm.provider_id():
            raise PortfolioAnsweringConfigurationError(
                "Configured LLM provider does not match wired provider",
                reason_code="llm_provider_mismatch",
            )

        resolved = self._resolve_index(command)
        question_type = self._classifier.classify(
            command.question,
            override=command.question_type,
        )
        scope = PortfolioQuestionScope(
            organization_id=resolved.organization_id.value,
            workspace_id=resolved.workspace_id.value,
            portfolio_id=resolved.portfolio_id.value,
            portfolio_retrieval_index_id=resolved.index_id.value,
            repository_ids=command.scope.repository_ids,
            content_types=command.scope.content_types,
        )
        if (
            command.scope.organization_id != resolved.organization_id.value
            or command.scope.workspace_id != resolved.workspace_id.value
            or command.scope.portfolio_id != resolved.portfolio_id.value
        ):
            raise NotFoundError(
                f"Portfolio '{command.scope.portfolio_id}' was not found",
                reason_code="portfolio_not_found",
            )
        question = PortfolioQuestion(
            text=command.question,
            scope=scope,
            question_type=question_type,
        )
        question_hash = normalize_portfolio_question_hash(question.text)
        projection_key = PortfolioAnswerProjectionKey.from_parts(
            organization_id=scope.organization_id,
            workspace_id=scope.workspace_id,
            portfolio_id=scope.portfolio_id,
            portfolio_retrieval_index_id=resolved.index_id.value,
            portfolio_retrieval_index_version=resolved.details.index_version,
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
                return PortfolioAnswerModel.from_aggregate(
                    cached,
                    cache_hit=True,
                    include_diagnostics=command.include_diagnostics,
                )

        run = PortfolioAnswerRun.create_pending(
            answer_run_id=deterministic_portfolio_answer_run_id(
                portfolio_id=scope.portfolio_id,
                portfolio_retrieval_index_id=resolved.index_id.value,
                projection_key=projection_key.value,
            ),
            organization_id=resolved.organization_id,
            workspace_id=resolved.workspace_id,
            portfolio_id=resolved.portfolio_id,
            portfolio_snapshot_id=resolved.snapshot_id,
            portfolio_retrieval_index_id=resolved.index_id,
            portfolio_retrieval_index_version=resolved.details.index_version,
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
            context = self._portfolio_retrieval.assemble_context(
                BuildPortfolioRetrievalContextQuery(
                    index_id=resolved.index_id,
                    query_text=question.text,
                    organization_id=resolved.organization_id,
                    workspace_id=resolved.workspace_id,
                    mode=plan.mode,
                    top_k=plan.top_k,
                    content_types=plan.content_types,
                    repository_balance_mode=plan.repository_balance_mode,
                    repository_ids=plan.repository_ids,
                )
            )
            sufficiency = self._sufficiency.evaluate(
                question_type=question_type,
                context=context,
            )
            limitation_notes = tuple(
                f"{item.kind}: {item.detail}" for item in context.diagnostics
            )
            run.attach_context(
                diagnostics={
                    "chunk_count": str(len(context.items)),
                    "token_estimate": str(context.token_estimate),
                    "repository_count": str(context.repository_count),
                    "sufficiency": sufficiency.status.value,
                    "truncated": str(context.truncated).lower(),
                }
            )
            if sufficiency.status is ContextSufficiencyStatus.INSUFFICIENT:
                limitation = (
                    "Insufficient portfolio retrieval context to answer safely. "
                    "Build a newer portfolio snapshot/index or refine the question."
                )
                run.validate_grounding(
                    answer_text=AnswerText(limitation),
                    citations=(),
                    grounding=GroundingResult(status=GroundingStatus.INSUFFICIENT_CONTEXT),
                    confidence=PortfolioAnswerConfidence(
                        level=AnswerConfidenceLevel.LOW,
                        score=20,
                        factors=("insufficient_context",),
                        policy_version=policy.answer_policy_version.value,
                    ),
                    limitations=(limitation, *sufficiency.missing, *limitation_notes),
                )
                run.complete()
                self._answers.save(run)
                return PortfolioAnswerModel.from_aggregate(
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
                    metadata={"question_type": question_type.value, "scope": "portfolio"},
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
                portfolio_id=resolved.portfolio_id.value,
                portfolio_snapshot_id=resolved.snapshot_id.value,
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
                raise PortfolioAnsweringGroundingError(
                    "Generated portfolio answer was ungrounded and rejected",
                    reason_code="ungrounded_portfolio_answer",
                )
            limitations: list[str] = list(limitation_notes)
            if sufficiency.status is ContextSufficiencyStatus.PARTIAL:
                limitations.append(
                    "Portfolio context was only partially sufficient for this question."
                )
            if grounding.status is GroundingStatus.PARTIALLY_GROUNDED:
                limitations.append(
                    "Answer is only partially grounded in retrieved portfolio citations."
                )
            if rendered.injection_flags:
                limitations.append(
                    "Retrieved context contained prompt-injection phrases treated as data only."
                )
            follow_ups = (
                "What systemic risks recur across repositories?",
                "Where is technology fragmentation concentrated?",
                "Which modernization waves should be prioritized?",
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
            return PortfolioAnswerModel.from_aggregate(
                run,
                include_diagnostics=command.include_diagnostics,
            )
        except PortfolioAnsweringGroundingError:
            raise
        except ValidationError:
            terminal = {
                AnswerStatus.FAILED,
                AnswerStatus.REJECTED,
                AnswerStatus.COMPLETED,
            }
            if run.status not in terminal:
                try:
                    run.fail("validation_error")
                    self._answers.save(run)
                except Exception:  # noqa: BLE001
                    pass
            raise
        except Exception as error:  # noqa: BLE001 - orchestration boundary
            if run.status not in {AnswerStatus.FAILED, AnswerStatus.REJECTED}:
                try:
                    run.fail(safe_failure_summary(error, limit=1000))
                    self._answers.save(run)
                except Exception:  # noqa: BLE001
                    pass
            raise ValidationError(
                f"Portfolio answering failed: {safe_failure_summary(error)}",
                reason_code="portfolio_answering_failed",
            ) from error

    def get_answer(self, query: GetPortfolioAnswerRunQuery) -> PortfolioAnswerModel:
        run = self._answers.get(query.answer_run_id)
        if run is None or (
            run.organization_id != query.organization_id
            or run.workspace_id != query.workspace_id
        ):
            raise NotFoundError(
                f"Portfolio answer run not found: {query.answer_run_id.value}",
                reason_code="portfolio_answer_run_not_found",
            )
        return PortfolioAnswerModel.from_aggregate(run)

    def list_portfolio_answers(
        self,
        query: ListPortfolioAnswersQuery,
    ) -> tuple[PortfolioAnswerModel, ...]:
        items = self._answers.list_by_portfolio(query.portfolio_id, limit=query.limit)
        owned = tuple(
            item
            for item in items
            if item.organization_id == query.organization_id
            and item.workspace_id == query.workspace_id
        )
        return tuple(PortfolioAnswerModel.from_aggregate(item) for item in owned)

    def submit_feedback(
        self,
        command: SubmitPortfolioAnswerFeedbackCommand,
    ) -> dict[str, object]:
        run = self._answers.get(command.answer_run_id)
        if run is None or (
            run.organization_id != command.organization_id
            or run.workspace_id != command.workspace_id
        ):
            raise NotFoundError(
                f"Portfolio answer run not found: {command.answer_run_id.value}",
                reason_code="portfolio_answer_run_not_found",
            )
        if command.rating < 1 or command.rating > 5:
            raise ValidationError(
                "rating must be between 1 and 5",
                reason_code="invalid_portfolio_answer_feedback_rating",
            )
        category = command.feedback_category.strip()
        if not category:
            raise ValidationError(
                "feedback_category must be non-blank",
                reason_code="empty_feedback_category",
            )
        payload = self._answers.save_feedback(
            answer_run_id=command.answer_run_id,
            rating=command.rating,
            feedback_category=category[:64],
            comment=command.comment.strip()[:1000],
        )
        return payload

    def _resolve_index(self, command: AskPortfolioQuestionCommand) -> _ResolvedIndex:
        organization_id = OrganizationId(command.scope.organization_id)
        workspace_id = WorkspaceId(command.scope.workspace_id)
        if command.portfolio_retrieval_index_id is not None:
            details = self._portfolio_retrieval.get(
                GetPortfolioRetrievalIndexQuery(
                    index_id=command.portfolio_retrieval_index_id,
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                )
            )
        else:
            details = self._portfolio_retrieval.get_latest(
                GetLatestPortfolioRetrievalIndexQuery(
                    portfolio_id=PortfolioId(command.scope.portfolio_id),
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                )
            )
        if details.status is not PortfolioRetrievalIndexStatus.COMPLETED:
            raise PortfolioAnsweringNotReadyError(
                "Portfolio answering requires a completed portfolio retrieval index",
                reason_code="portfolio_retrieval_index_not_completed",
            )
        return _ResolvedIndex(
            details=details,
            organization_id=OrganizationId(details.organization_id),
            workspace_id=WorkspaceId(details.workspace_id),
            portfolio_id=PortfolioId(details.portfolio_id),
            snapshot_id=PortfolioSnapshotId(details.portfolio_snapshot_id),
            index_id=PortfolioRetrievalIndexId(details.index_id),
        )
