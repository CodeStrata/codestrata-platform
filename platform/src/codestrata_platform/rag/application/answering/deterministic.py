"""Deterministic extractive answer provider (tests / dogfood only)."""

from __future__ import annotations

import re
from typing import Any

from codestrata_platform.rag.application.answering.protocol import (
    AnswerProviderCapabilities,
    AnswerProviderDiagnostic,
    AnswerProviderHealth,
    AnswerProviderRequest,
    AnswerProviderResult,
    AnswerProviderUsage,
)
from codestrata_platform.rag.domain.answering import (
    AnswerCitation,
    AnswerConfidence,
    AnswerModelIdentity,
    AnswerStatement,
    AnswerStatementType,
    AnswerStyle,
)
from codestrata_platform.rag.domain.identifiers import fingerprint_payload
from codestrata_platform.rag.domain.retrieval import RetrievalHit

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WHITESPACE = re.compile(r"\s+")

INSUFFICIENT_MESSAGE = (
    "The indexed repository evidence is insufficient to answer this question."
)

DEFAULT_LIMITATIONS = (
    "DeterministicExtractiveAnswerProvider performs extractive grounding only; "
    "it is not generative AI and is not a production language model.",
)


def _normalize_text(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip().lower()


def _excerpt(text: str, *, max_chars: int) -> str:
    compact = _WHITESPACE.sub(" ", text).strip()
    if len(compact) <= max_chars:
        return compact
    cut = compact[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:")
    return cut or compact[:max_chars]


def _sentences(text: str, *, preserve: bool) -> list[str]:
    compact = _WHITESPACE.sub(" ", text).strip()
    if not compact:
        return []
    if not preserve:
        return [compact]
    parts = [part.strip() for part in _SENTENCE_SPLIT.split(compact) if part.strip()]
    return parts or [compact]


def _statement_type_for_style(style: AnswerStyle, source_type: str | None) -> AnswerStatementType:
    if style == AnswerStyle.FINDINGS_SUMMARY or (source_type or "") in {
        "finding",
        "security",
    }:
        return AnswerStatementType.FINDING
    if style == AnswerStyle.RECOMMENDATION_SUMMARY or (source_type or "") == "recommendation":
        return AnswerStatementType.RECOMMENDATION
    return AnswerStatementType.FACT


def _score_sentence(sentence: str, question_terms: set[str]) -> int:
    tokens = set(_normalize_text(sentence).split())
    return len(tokens & question_terms)


class DeterministicExtractiveAnswerProvider:
    """Extractive, citation-bound answers for tests and dogfood.

    Declares ``is_production_model=false`` and ``is_generative_ai=false``.
    Never invents facts outside retrieved hit content.
    """

    def __init__(
        self,
        *,
        max_excerpt_characters: int = 800,
        max_statements_per_source: int = 2,
        preserve_source_sentences: bool = True,
    ) -> None:
        self._max_excerpt = max(1, int(max_excerpt_characters))
        self._max_per_source = max(1, int(max_statements_per_source))
        self._preserve = bool(preserve_source_sentences)

    def model_identity(self) -> AnswerModelIdentity:
        return AnswerModelIdentity(
            provider_id="deterministic_extractive",
            model="deterministic-extractive",
            model_version="1.0.0",
            is_production_model=False,
            is_generative_ai=False,
        )

    def capabilities(self) -> AnswerProviderCapabilities:
        return AnswerProviderCapabilities(
            provider_id="deterministic_extractive",
            supports_freeform_synthesis=False,
            supports_streaming=False,
            is_generative_ai=False,
            is_production_model=False,
            extra={"extractive": True},
        )

    def health(self) -> AnswerProviderHealth:
        return AnswerProviderHealth(
            healthy=True,
            message="deterministic extractive answer provider ready",
            detail={"network": False, "ai": False},
        )

    def generate(self, request: AnswerProviderRequest) -> AnswerProviderResult:
        hits = list(request.hits)
        if not hits:
            statement = AnswerStatement(
                statement_id="stmt:insufficient:0",
                sequence=0,
                text=INSUFFICIENT_MESSAGE,
                citation_labels=(),
                confidence=AnswerConfidence.NONE,
                evidence_strength="none",
                statement_type=AnswerStatementType.INSUFFICIENT_EVIDENCE,
            )
            return AnswerProviderResult(
                summary=INSUFFICIENT_MESSAGE,
                statements=(statement,),
                citations=(),
                diagnostics=(
                    AnswerProviderDiagnostic(
                        code="insufficient_evidence",
                        message="no retrieval hits available for extraction",
                        severity="warning",
                    ),
                ),
                usage=AnswerProviderUsage(statements_proposed=1),
                insufficient_evidence=True,
            )

        question_terms = {
            token
            for token in _normalize_text(request.normalized_question).split()
            if len(token) > 2
        }
        max_excerpt = min(request.max_excerpt_characters, self._max_excerpt)
        max_per_source = min(request.max_statements_per_source, self._max_per_source)

        candidates: list[tuple[int, float, str, RetrievalHit, str]] = []
        for hit in hits:
            content = (hit.content or "").strip()
            if not content:
                continue
            preserve = self._preserve and request.preserve_source_sentences
            for sentence in _sentences(content, preserve=preserve):
                excerpt = _excerpt(sentence, max_chars=max_excerpt)
                overlap = _score_sentence(excerpt, question_terms)
                candidates.append(
                    (overlap, float(hit.score), hit.record_id, hit, excerpt)
                )

        candidates.sort(key=lambda item: (-item[0], -item[1], item[2], item[4]))

        statements: list[AnswerStatement] = []
        citations: dict[str, AnswerCitation] = {}
        per_source: dict[str, int] = {}
        used_chars = 0
        diagnostics: list[AnswerProviderDiagnostic] = []

        for overlap, _score, _record_id, hit, excerpt in candidates:
            if len(statements) >= request.max_statements:
                break
            source_key = hit.document_id or hit.chunk_id or hit.record_id
            if per_source.get(source_key, 0) >= max_per_source:
                continue
            if used_chars + len(excerpt) > request.max_answer_characters and statements:
                diagnostics.append(
                    AnswerProviderDiagnostic(
                        code="answer_size_limit",
                        message="skipped excerpt due to max_answer_characters",
                        severity="info",
                    )
                )
                continue
            if not excerpt:
                continue

            label = hit.citation_label
            stmt_type = _statement_type_for_style(request.style, hit.source_type)
            statement_id = (
                "stmt:"
                + fingerprint_payload(
                    {
                        "record_id": hit.record_id,
                        "excerpt": excerpt,
                        "sequence": len(statements),
                    }
                )[:16]
            )
            statements.append(
                AnswerStatement(
                    statement_id=statement_id,
                    sequence=len(statements),
                    text=excerpt,
                    citation_labels=(label,),
                    confidence=(
                        AnswerConfidence.HIGH
                        if overlap >= 3 or hit.score >= 0.6
                        else AnswerConfidence.MEDIUM
                        if overlap >= 1 or hit.score >= 0.2
                        else AnswerConfidence.LOW
                    ),
                    evidence_strength=(
                        "high" if overlap >= 3 else "medium" if overlap >= 1 else "low"
                    ),
                    statement_type=stmt_type,
                )
            )
            if label not in citations:
                citations[label] = AnswerCitation(
                    citation_label=label,
                    record_id=hit.record_id,
                    chunk_id=hit.chunk_id,
                    document_id=hit.document_id,
                    source_type=hit.source_type,
                    intelligence_pack=hit.intelligence_pack,
                    file_path=hit.file_path,
                    symbol_name=hit.symbol_name,
                    finding_id=hit.finding_id,
                    rule_id=hit.rule_id,
                    scan_id=hit.scan_id,
                    commit_sha=hit.commit_sha,
                    traceability=dict(hit.traceability),
                    excerpt=excerpt,
                )
            per_source[source_key] = per_source.get(source_key, 0) + 1
            used_chars += len(excerpt)

        if not statements:
            statement = AnswerStatement(
                statement_id="stmt:insufficient:0",
                sequence=0,
                text=INSUFFICIENT_MESSAGE,
                citation_labels=(),
                confidence=AnswerConfidence.NONE,
                evidence_strength="none",
                statement_type=AnswerStatementType.INSUFFICIENT_EVIDENCE,
            )
            return AnswerProviderResult(
                summary=INSUFFICIENT_MESSAGE,
                statements=(statement,),
                citations=(),
                diagnostics=tuple(diagnostics)
                + (
                    AnswerProviderDiagnostic(
                        code="insufficient_evidence",
                        message="hits present but no extractable grounded statements",
                        severity="warning",
                    ),
                ),
                usage=AnswerProviderUsage(statements_proposed=1),
                insufficient_evidence=True,
            )

        # Preserve retrieval citation ordering.
        ordered_labels = [hit.citation_label for hit in hits if hit.citation_label in citations]
        ordered_citations = tuple(citations[label] for label in ordered_labels)

        summary = statements[0].text
        if request.style == AnswerStyle.DETAILED and len(statements) > 1:
            summary = " ".join(item.text for item in statements[:3])
            summary = _excerpt(summary, max_chars=min(400, request.max_answer_characters))

        return AnswerProviderResult(
            summary=summary,
            statements=tuple(statements),
            citations=ordered_citations,
            diagnostics=tuple(diagnostics),
            usage=AnswerProviderUsage(
                statements_proposed=len(statements),
                citations_attached=len(ordered_citations),
                characters_produced=sum(len(item.text) for item in statements),
            ),
            insufficient_evidence=False,
        )


def create_deterministic_extractive_answer_provider(
    *,
    max_excerpt_characters: int = 800,
    max_statements_per_source: int = 2,
    preserve_source_sentences: bool = True,
    answering_settings: Any | None = None,
    **_: Any,
) -> DeterministicExtractiveAnswerProvider:
    if answering_settings is not None:
        det = getattr(answering_settings, "deterministic_extractive", None)
        if det is not None:
            max_excerpt_characters = int(
                getattr(det, "max_excerpt_characters", max_excerpt_characters)
            )
            max_statements_per_source = int(
                getattr(det, "max_statements_per_source", max_statements_per_source)
            )
            preserve_source_sentences = bool(
                getattr(det, "preserve_source_sentences", preserve_source_sentences)
            )
    return DeterministicExtractiveAnswerProvider(
        max_excerpt_characters=max_excerpt_characters,
        max_statements_per_source=max_statements_per_source,
        preserve_source_sentences=preserve_source_sentences,
    )
