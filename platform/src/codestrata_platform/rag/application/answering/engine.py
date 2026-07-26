"""GroundedAnswerEngine — orchestrate retrieval + answer provider (Phase 5.6)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from codestrata.config.settings import KnowledgeAnsweringSettings, KnowledgeRetrievalSettings
from codestrata.security.database_url import sanitize_exception_message
from codestrata.services.artifact_serialization import dumps_stable_json
from codestrata_platform.rag.application.answering.confidence import calculate_answer_confidence
from codestrata_platform.rag.application.answering.protocol import (
    AnswerProvider,
    AnswerProviderRequest,
)
from codestrata_platform.rag.application.answering.validation import validate_and_filter_statements
from codestrata_platform.rag.application.retrieval import RepositoryRetriever
from codestrata_platform.rag.application.retrieval.query_preparation import (
    QueryPreparationError,
    prepare_retrieval_query,
)
from codestrata_platform.rag.domain.answering import (
    AnswerCoverage,
    AnswerDiagnostic,
    AnswerEvidence,
    AnswerLimitation,
    AnswerSection,
    AnswerStatementType,
    AnswerStatus,
    GroundedAnswer,
    GroundedAnswerRequest,
    GroundedAnswerResult,
    build_answer_fingerprint,
    build_request_fingerprint,
    grounded_answer_result_payload,
)
from codestrata_platform.rag.domain.identifiers import fingerprint_payload
from codestrata_platform.rag.domain.retrieval import RetrievalRequest, RetrievalStatus

ANSWER_ARTIFACT_FILENAME = "repository-grounded-answer.json"

ENGINE_LIMITATIONS = (
    "Grounded answers cite retrieved repository knowledge only.",
    "Deterministic extractive answering is not generative AI.",
    "Insufficient evidence yields an explicit non-answer; the engine does not guess.",
)


class GroundedAnswerEngine:
    """Orchestrate RepositoryRetriever + AnswerProvider with grounding validation.

    Receives existing retriever and provider instances. Does not create stores,
    embeddings, DB connections, or invoke production AI services.
    """

    def __init__(
        self,
        *,
        retriever: RepositoryRetriever,
        answer_provider: AnswerProvider,
        answering_settings: KnowledgeAnsweringSettings | None = None,
        retrieval_settings: KnowledgeRetrievalSettings | None = None,
    ) -> None:
        self._retriever = retriever
        self._provider = answer_provider
        self._settings = answering_settings or KnowledgeAnsweringSettings()
        self._retrieval_settings = retrieval_settings or KnowledgeRetrievalSettings()

    def answer(self, request: GroundedAnswerRequest) -> GroundedAnswerResult:
        settings = self._settings
        request_fp = build_request_fingerprint(request)
        if not settings.enabled:
            return GroundedAnswerResult(
                status=AnswerStatus.DISABLED,
                request_fingerprint=request_fp,
                diagnostics=(
                    AnswerDiagnostic(
                        code="answer_engine_disabled",
                        message="knowledge.answering.enabled is false",
                        severity="info",
                    ),
                ),
                limitations=(
                    AnswerLimitation(
                        code="disabled",
                        message="Grounded answering is disabled by configuration.",
                    ),
                ),
            )

        diagnostics: list[AnswerDiagnostic] = []
        try:
            prepared = prepare_retrieval_query(
                request.question,
                max_query_characters=request.max_query_characters,
            )
        except QueryPreparationError as exc:
            return GroundedAnswerResult(
                status=AnswerStatus.FAILED,
                request_fingerprint=request_fp,
                diagnostics=(
                    AnswerDiagnostic(
                        code=exc.code,
                        message=exc.message,
                        severity="error",
                    ),
                ),
            )

        if not self._retrieval_settings.enabled:
            return GroundedAnswerResult(
                status=AnswerStatus.FAILED,
                request_fingerprint=request_fp,
                diagnostics=(
                    AnswerDiagnostic(
                        code="retrieval_disabled",
                        message="knowledge.retrieval.enabled is false",
                        severity="error",
                    ),
                ),
            )

        retrieval_request = RetrievalRequest(
            query=prepared.normalized,
            scope=request.scope,
            filters=request.filters,
            top_k=request.top_k,
            candidate_limit=request.candidate_limit,
            minimum_score=request.minimum_score,
            max_query_characters=request.max_query_characters,
            max_context_characters=self._retrieval_settings.max_context_characters,
            max_chunks_per_document=self._retrieval_settings.max_chunks_per_document,
            max_chunks_per_file=self._retrieval_settings.max_chunks_per_file,
            max_chunks_per_source_type=self._retrieval_settings.max_chunks_per_source_type,
            include_content=True,
            include_metadata=True,
            include_traceability=True,
        )

        try:
            retrieval = self._retriever.retrieve(retrieval_request)
        except Exception as exc:  # noqa: BLE001
            return GroundedAnswerResult(
                status=AnswerStatus.FAILED,
                request_fingerprint=request_fp,
                diagnostics=(
                    AnswerDiagnostic(
                        code="retrieval_failure",
                        message=sanitize_exception_message(str(exc)),
                        severity="error",
                    ),
                ),
            )

        if retrieval.status == RetrievalStatus.FAILED:
            return GroundedAnswerResult(
                status=AnswerStatus.FAILED,
                request_fingerprint=request_fp,
                retrieval_status=retrieval.status.value,
                retrieval_fingerprint=retrieval.fingerprint,
                diagnostics=tuple(
                    AnswerDiagnostic(
                        code=item.code,
                        message=item.message,
                        severity=item.severity,
                    )
                    for item in retrieval.diagnostics
                )
                or (
                    AnswerDiagnostic(
                        code="retrieval_failure",
                        message="retrieval failed",
                        severity="error",
                    ),
                ),
            )

        if retrieval.status == RetrievalStatus.EMPTY or not retrieval.context.hits:
            return self._insufficient_or_empty(
                request=request,
                request_fp=request_fp,
                prepared_question=prepared.normalized,
                retrieval_status=retrieval.status.value,
                retrieval_fingerprint=retrieval.fingerprint,
                empty=True,
            )

        provider_request = AnswerProviderRequest(
            question=request.question,
            normalized_question=prepared.normalized,
            style=request.style,
            hits=retrieval.context.hits,
            citation_labels=retrieval.context.citation_labels,
            max_statements=request.max_statements,
            max_answer_characters=request.max_answer_characters,
            max_excerpt_characters=settings.deterministic_extractive.max_excerpt_characters,
            max_statements_per_source=(
                settings.deterministic_extractive.max_statements_per_source
            ),
            preserve_source_sentences=(
                settings.deterministic_extractive.preserve_source_sentences
            ),
        )

        try:
            provider_result = self._provider.generate(provider_request)
        except Exception as exc:  # noqa: BLE001
            return GroundedAnswerResult(
                status=AnswerStatus.FAILED,
                request_fingerprint=request_fp,
                retrieval_status=retrieval.status.value,
                retrieval_fingerprint=retrieval.fingerprint,
                diagnostics=(
                    AnswerDiagnostic(
                        code="answer_provider_failure",
                        message=sanitize_exception_message(str(exc)),
                        severity="error",
                    ),
                ),
            )

        for item in provider_result.diagnostics:
            diagnostics.append(
                AnswerDiagnostic(
                    code=item.code,
                    message=item.message,
                    severity=item.severity,
                )
            )

        proposed = len(provider_result.statements)
        accepted, citations, validation_diags, excluded = validate_and_filter_statements(
            provider_result.statements,
            provider_result.citations,
            hits=retrieval.context.hits,
            scope=request.scope,
            require_citations=request.require_citations,
        )
        diagnostics.extend(validation_diags)

        # Enforce max statements after validation.
        if len(accepted) > request.max_statements:
            diagnostics.append(
                AnswerDiagnostic(
                    code="statement_limit",
                    message="truncated statements to max_statements",
                    severity="info",
                )
            )
            excluded += len(accepted) - request.max_statements
            accepted = accepted[: request.max_statements]
            # resequence
            accepted = [
                item.model_copy(update={"sequence": index})
                for index, item in enumerate(accepted)
            ]

        factual = [
            item
            for item in accepted
            if item.statement_type
            not in {
                AnswerStatementType.INSUFFICIENT_EVIDENCE,
                AnswerStatementType.LIMITATION,
            }
        ]

        if provider_result.insufficient_evidence or not factual:
            if request.fail_on_insufficient_evidence:
                return GroundedAnswerResult(
                    status=AnswerStatus.FAILED,
                    request_fingerprint=request_fp,
                    retrieval_status=retrieval.status.value,
                    retrieval_fingerprint=retrieval.fingerprint,
                    diagnostics=tuple(diagnostics)
                    + (
                        AnswerDiagnostic(
                            code="insufficient_evidence",
                            message="fail_on_insufficient_evidence is enabled",
                            severity="error",
                        ),
                    ),
                )
            return self._insufficient_or_empty(
                request=request,
                request_fp=request_fp,
                prepared_question=prepared.normalized,
                retrieval_status=retrieval.status.value,
                retrieval_fingerprint=retrieval.fingerprint,
                empty=False,
                diagnostics=diagnostics,
                proposed=proposed,
                excluded=excluded,
                hits=retrieval.context.hits,
            )

        unique_labels = {label for stmt in accepted for label in stmt.citation_labels}
        if len(unique_labels) < request.minimum_supporting_sources:
            diagnostics.append(
                AnswerDiagnostic(
                    code="insufficient_evidence",
                    message=(
                        "fewer supporting sources than minimum_supporting_sources "
                        f"({len(unique_labels)} < {request.minimum_supporting_sources})"
                    ),
                    severity="warning",
                )
            )
            if request.fail_on_insufficient_evidence:
                return GroundedAnswerResult(
                    status=AnswerStatus.FAILED,
                    request_fingerprint=request_fp,
                    retrieval_status=retrieval.status.value,
                    retrieval_fingerprint=retrieval.fingerprint,
                    diagnostics=tuple(diagnostics),
                )
            return self._insufficient_or_empty(
                request=request,
                request_fp=request_fp,
                prepared_question=prepared.normalized,
                retrieval_status=retrieval.status.value,
                retrieval_fingerprint=retrieval.fingerprint,
                empty=False,
                diagnostics=diagnostics,
                proposed=proposed,
                excluded=excluded,
                hits=retrieval.context.hits,
            )

        confidence = calculate_answer_confidence(
            statements=accepted,
            citations_used=len(citations),
            hits=retrieval.context.hits,
            grounding_exclusions=excluded,
            minimum_supporting_sources=request.minimum_supporting_sources,
        )

        summary = provider_result.summary
        if not summary and accepted:
            summary = accepted[0].text
        answer_chars = sum(len(item.text) for item in accepted) + len(summary)
        if answer_chars > request.max_answer_characters:
            diagnostics.append(
                AnswerDiagnostic(
                    code="answer_size_limit",
                    message="answer exceeded max_answer_characters after validation",
                    severity="warning",
                )
            )
            # Trim statements from the end until within budget.
            while accepted and (
                sum(len(item.text) for item in accepted) + len(summary)
                > request.max_answer_characters
            ):
                removed = accepted.pop()
                excluded += 1
                diagnostics.append(
                    AnswerDiagnostic(
                        code="answer_size_limit",
                        message="dropped statement to satisfy max_answer_characters",
                        severity="info",
                        statement_id=removed.statement_id,
                    )
                )
            accepted = [
                item.model_copy(update={"sequence": index})
                for index, item in enumerate(accepted)
            ]
            if not any(
                item.statement_type
                not in {
                    AnswerStatementType.INSUFFICIENT_EVIDENCE,
                    AnswerStatementType.LIMITATION,
                }
                for item in accepted
            ):
                return self._insufficient_or_empty(
                    request=request,
                    request_fp=request_fp,
                    prepared_question=prepared.normalized,
                    retrieval_status=retrieval.status.value,
                    retrieval_fingerprint=retrieval.fingerprint,
                    empty=False,
                    diagnostics=diagnostics,
                    proposed=proposed,
                    excluded=excluded,
                    hits=retrieval.context.hits,
                )

        section = AnswerSection(
            section_id="sec:main",
            title=_section_title(request.style.value),
            sequence=0,
            statements=tuple(accepted),
        )
        answer_id = (
            "ga:"
            + fingerprint_payload(
                {
                    "question": prepared.fingerprint,
                    "scope": request.scope.model_dump(mode="json"),
                    "provider": self._provider.model_identity().model_dump(mode="json"),
                }
            )[:24]
        )
        fingerprint = build_answer_fingerprint(
            answer_id=answer_id,
            normalized_question=prepared.normalized,
            statement_ids=[item.statement_id for item in accepted],
            citation_labels=[item.citation_label for item in citations],
            status=AnswerStatus.SUCCESS if excluded == 0 else AnswerStatus.PARTIAL,
            confidence=confidence,
        )
        answer = GroundedAnswer(
            answer_id=answer_id,
            question=request.question,
            normalized_question=prepared.normalized,
            summary=summary or accepted[0].text,
            sections=(section,),
            statements=tuple(accepted),
            citations=tuple(citations),
            confidence=confidence,
            limitations=ENGINE_LIMITATIONS,
            retrieval_result_fingerprint=retrieval.fingerprint,
            provider=self._provider.model_identity(),
            fingerprint=fingerprint,
        )

        status = AnswerStatus.SUCCESS if excluded == 0 else AnswerStatus.PARTIAL
        coverage = _coverage(
            retrieval=retrieval,
            proposed=proposed,
            accepted=accepted,
            excluded=excluded,
            citations=citations,
            summary=answer.summary,
        )
        evidence: tuple[AnswerEvidence, ...] = ()
        if request.include_evidence:
            cited_labels = {item.citation_label for item in citations}
            evidence = tuple(
                AnswerEvidence(
                    citation_label=hit.citation_label,
                    record_id=hit.record_id,
                    score=hit.score,
                    content=hit.content,
                )
                for hit in retrieval.context.hits
                if hit.citation_label in cited_labels
            )

        out_diagnostics = tuple(diagnostics) if request.include_diagnostics else ()
        return GroundedAnswerResult(
            status=status,
            request_fingerprint=request_fp,
            answer=answer,
            evidence=evidence,
            retrieval_context=(
                retrieval.context if request.include_retrieval_context else None
            ),
            coverage=coverage,
            diagnostics=out_diagnostics,
            limitations=tuple(
                AnswerLimitation(code="engine", message=item) for item in ENGINE_LIMITATIONS
            ),
            retrieval_status=retrieval.status.value,
            retrieval_fingerprint=retrieval.fingerprint,
        )

    def _insufficient_or_empty(
        self,
        *,
        request: GroundedAnswerRequest,
        request_fp: str,
        prepared_question: str,
        retrieval_status: str | None,
        retrieval_fingerprint: str | None,
        empty: bool,
        diagnostics: list[AnswerDiagnostic] | None = None,
        proposed: int = 0,
        excluded: int = 0,
        hits: tuple[Any, ...] = (),
    ) -> GroundedAnswerResult:
        from codestrata_platform.rag.application.answering.deterministic import INSUFFICIENT_MESSAGE
        from codestrata_platform.rag.domain.answering import (
            AnswerConfidence,
            AnswerStatement,
        )

        diagnostics = list(diagnostics or [])
        diagnostics.append(
            AnswerDiagnostic(
                code="insufficient_evidence" if not empty else "empty_retrieval",
                message=(
                    "no eligible retrieval hits"
                    if empty
                    else "indexed repository evidence cannot support a grounded answer"
                ),
                severity="warning",
            )
        )
        statement = AnswerStatement(
            statement_id="stmt:insufficient:0",
            sequence=0,
            text=INSUFFICIENT_MESSAGE,
            citation_labels=(),
            confidence=AnswerConfidence.NONE,
            evidence_strength="none",
            statement_type=AnswerStatementType.INSUFFICIENT_EVIDENCE,
        )
        answer_id = "ga:insufficient:" + (request_fp[:16] if request_fp else "none")
        identity = self._provider.model_identity()
        status = AnswerStatus.EMPTY if empty else AnswerStatus.INSUFFICIENT_EVIDENCE
        fingerprint = build_answer_fingerprint(
            answer_id=answer_id,
            normalized_question=prepared_question,
            statement_ids=[statement.statement_id],
            citation_labels=(),
            status=status,
            confidence=AnswerConfidence.NONE,
        )
        answer = GroundedAnswer(
            answer_id=answer_id,
            question=request.question,
            normalized_question=prepared_question,
            summary=INSUFFICIENT_MESSAGE,
            sections=(
                AnswerSection(
                    section_id="sec:insufficient",
                    title="Insufficient evidence",
                    sequence=0,
                    statements=(statement,),
                ),
            ),
            statements=(statement,),
            citations=(),
            confidence=AnswerConfidence.NONE,
            limitations=ENGINE_LIMITATIONS,
            retrieval_result_fingerprint=retrieval_fingerprint,
            provider=identity,
            fingerprint=fingerprint,
        )
        return GroundedAnswerResult(
            status=status,
            request_fingerprint=request_fp,
            answer=answer,
            coverage=AnswerCoverage(
                retrieval_hits=len(hits),
                evidence_hits_considered=len(hits),
                statements_proposed=proposed or 1,
                statements_accepted=1,
                statements_excluded=excluded,
                uncited_statements=1,
                answer_characters_produced=len(INSUFFICIENT_MESSAGE),
            ),
            diagnostics=tuple(diagnostics) if request.include_diagnostics else (),
            limitations=tuple(
                AnswerLimitation(code="engine", message=item) for item in ENGINE_LIMITATIONS
            ),
            retrieval_status=retrieval_status,
            retrieval_fingerprint=retrieval_fingerprint,
        )


def _section_title(style: str) -> str:
    mapping = {
        "concise": "Answer",
        "detailed": "Detailed answer",
        "findings_summary": "Findings summary",
        "recommendation_summary": "Recommendations",
        "architecture_explanation": "Architecture",
        "evidence_only": "Evidence",
    }
    return mapping.get(style, "Answer")


def _coverage(
    *,
    retrieval: Any,
    proposed: int,
    accepted: list[Any],
    excluded: int,
    citations: list[Any],
    summary: str,
) -> AnswerCoverage:
    cited = sum(1 for item in accepted if item.citation_labels)
    uncited = len(accepted) - cited
    docs = {item.document_id for item in citations if item.document_id}
    files = {item.file_path for item in citations if item.file_path}
    findings = {item.finding_id for item in citations if item.finding_id}
    source_types = tuple(sorted({item.source_type for item in citations if item.source_type}))
    packs = tuple(
        sorted({item.intelligence_pack for item in citations if item.intelligence_pack})
    )
    return AnswerCoverage(
        retrieval_candidates=retrieval.coverage.candidates_requested,
        retrieval_hits=retrieval.coverage.final_hit_count,
        evidence_hits_considered=len(retrieval.context.hits),
        statements_proposed=proposed,
        statements_accepted=len(accepted),
        statements_excluded=excluded,
        cited_statements=cited,
        uncited_statements=uncited,
        citations_used=len(citations),
        unique_documents_cited=len(docs),
        unique_files_cited=len(files),
        unique_findings_cited=len(findings),
        source_types=source_types,
        intelligence_packs=packs,
        context_characters_used=retrieval.context.character_count,
        answer_characters_produced=sum(len(item.text) for item in accepted) + len(summary or ""),
    )


def write_grounded_answer_artifact(
    result: GroundedAnswerResult,
    run_directory: Path,
    *,
    enabled: bool,
    filename: str = ANSWER_ARTIFACT_FILENAME,
) -> Path | None:
    if not enabled:
        return None
    run_directory.mkdir(parents=True, exist_ok=True)
    path = run_directory / filename
    payload = grounded_answer_result_payload(result)
    _strip_secrets(payload)
    text = dumps_stable_json(payload)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)
    return path


def _strip_secrets(payload: Any) -> None:
    if isinstance(payload, dict):
        for key in ("embedding", "embeddings", "password", "connection_string"):
            payload.pop(key, None)
        for value in payload.values():
            _strip_secrets(value)
    elif isinstance(payload, list):
        for item in payload:
            _strip_secrets(item)
