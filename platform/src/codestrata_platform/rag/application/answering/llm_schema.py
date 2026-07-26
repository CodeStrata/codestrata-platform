"""Provider-neutral structured LLM answer schema (Phase 5.8)."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from codestrata.domain.graph.validation import as_tuple, require_nonblank
from codestrata_platform.rag.application.answering.protocol import (
    AnswerProviderDiagnostic,
    AnswerProviderResult,
    AnswerProviderUsage,
)
from codestrata_platform.rag.application.answering.validation import citation_from_hit
from codestrata_platform.rag.domain.answering import (
    AnswerCitation,
    AnswerConfidence,
    AnswerStatement,
    AnswerStatementType,
)
from codestrata_platform.rag.domain.identifiers import fingerprint_payload
from codestrata_platform.rag.domain.retrieval import RetrievalHit

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


class LlmAnswerStatement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    citation_labels: tuple[str, ...] = ()
    statement_type: AnswerStatementType = AnswerStatementType.FACT
    confidence: AnswerConfidence = AnswerConfidence.MEDIUM

    @field_validator("text", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> str:
        return require_nonblank(str(value), label="statement text")

    @field_validator("citation_labels", mode="before")
    @classmethod
    def normalize_labels(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        return tuple(str(item) for item in as_tuple(value))


class LlmAnswerCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_label: str
    excerpt: str | None = None

    @field_validator("citation_label", mode="before")
    @classmethod
    def normalize_label(cls, value: object) -> str:
        return require_nonblank(str(value), label="citation_label")


class LlmGroundedAnswerPayload(BaseModel):
    """Structured answer returned by production LLM answer providers."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    statements: tuple[LlmAnswerStatement, ...] = ()
    citations: tuple[LlmAnswerCitation, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    confidence: AnswerConfidence = AnswerConfidence.LOW
    insufficient_evidence: bool = False

    @field_validator("summary", mode="before")
    @classmethod
    def normalize_summary(cls, value: object) -> str:
        return str(value)

    @field_validator("limitations", "evidence_ids", mode="before")
    @classmethod
    def normalize_string_tuples(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        return tuple(str(item) for item in as_tuple(value))

    @model_validator(mode="after")
    def validate_citations_against_field(self) -> LlmGroundedAnswerPayload:
        # Unknown citation checks happen against the allowed set in parse_llm_answer.
        return self


class StructuredAnswerValidationError(ValueError):
    """Raised when LLM structured output fails schema or citation checks."""


def extract_json_object(text: str) -> dict[str, Any]:
    compact = text.strip()
    match = _JSON_FENCE.search(compact)
    if match:
        compact = match.group(1).strip()
    try:
        payload = json.loads(compact)
    except json.JSONDecodeError as exc:
        start = compact.find("{")
        end = compact.rfind("}")
        if start < 0 or end <= start:
            raise StructuredAnswerValidationError(
                f"response is not valid JSON: {exc}"
            ) from exc
        try:
            payload = json.loads(compact[start : end + 1])
        except json.JSONDecodeError as nested:
            raise StructuredAnswerValidationError(
                f"response is not valid JSON: {nested}"
            ) from nested
    if not isinstance(payload, dict):
        raise StructuredAnswerValidationError("JSON root must be an object")
    return payload


def parse_llm_answer(
    text: str,
    *,
    hits: Sequence[RetrievalHit],
    allowed_citations: Sequence[str],
) -> AnswerProviderResult:
    """Parse and validate LLM JSON into an AnswerProviderResult."""

    raw = extract_json_object(text)
    try:
        payload = LlmGroundedAnswerPayload.model_validate(raw)
    except Exception as exc:  # noqa: BLE001 - pydantic boundary
        raise StructuredAnswerValidationError(str(exc)) from exc

    allowed = set(allowed_citations)
    hits_by_label = {hit.citation_label: hit for hit in hits}
    allowed_evidence = {hit.record_id for hit in hits}

    for statement in payload.statements:
        for label in statement.citation_labels:
            if label not in allowed:
                raise StructuredAnswerValidationError(
                    f"unknown citation label {label!r}; allowed={sorted(allowed)}"
                )
        factual = statement.statement_type not in {
            AnswerStatementType.INSUFFICIENT_EVIDENCE,
            AnswerStatementType.LIMITATION,
        }
        if factual and not statement.citation_labels and not payload.insufficient_evidence:
            raise StructuredAnswerValidationError(
                "factual statements require at least one citation label"
            )

    for citation in payload.citations:
        if citation.citation_label not in allowed:
            raise StructuredAnswerValidationError(
                f"unknown citation label {citation.citation_label!r}"
            )

    for evidence_id in payload.evidence_ids:
        if evidence_id not in allowed_evidence:
            raise StructuredAnswerValidationError(
                f"unknown evidence id {evidence_id!r}; "
                f"allowed={sorted(allowed_evidence)}"
            )

    statements: list[AnswerStatement] = []
    for index, item in enumerate(payload.statements):
        statement_id = (
            "stmt:"
            + fingerprint_payload(
                {"text": item.text, "citations": list(item.citation_labels), "i": index}
            )[:16]
        )
        statements.append(
            AnswerStatement(
                statement_id=statement_id,
                sequence=index,
                text=item.text,
                citation_labels=item.citation_labels,
                confidence=item.confidence,
                evidence_strength=item.confidence.value,
                statement_type=item.statement_type,
            )
        )

    citations_out: list[AnswerCitation] = []
    seen: set[str] = set()
    for citation_item in payload.citations:
        if citation_item.citation_label in seen:
            continue
        seen.add(citation_item.citation_label)
        hit = hits_by_label.get(citation_item.citation_label)
        if hit is None:
            raise StructuredAnswerValidationError(
                f"citation {citation_item.citation_label!r} missing from retrieval hits"
            )
        citations_out.append(
            citation_from_hit(
                hit, excerpt=citation_item.excerpt or hit.content
            )
        )

    # Ensure statement citations are represented.
    for built_statement in statements:
        for label in built_statement.citation_labels:
            if label in seen:
                continue
            hit = hits_by_label[label]
            citations_out.append(citation_from_hit(hit))
            seen.add(label)

    # Preserve retrieval citation ordering.
    ordered: list[AnswerCitation] = []
    for hit in hits:
        if hit.citation_label in seen:
            ordered.append(
                next(
                    c
                    for c in citations_out
                    if c.citation_label == hit.citation_label
                )
            )

    diagnostics: list[AnswerProviderDiagnostic] = []
    if payload.insufficient_evidence:
        diagnostics.append(
            AnswerProviderDiagnostic(
                code="insufficient_evidence",
                message="provider reported insufficient evidence",
                severity="warning",
            )
        )
    for limitation in payload.limitations:
        diagnostics.append(
            AnswerProviderDiagnostic(
                code="limitation",
                message=limitation,
                severity="info",
            )
        )

    return AnswerProviderResult(
        summary=payload.summary
        or (statements[0].text if statements else "Insufficient evidence."),
        statements=tuple(statements),
        citations=tuple(ordered),
        diagnostics=tuple(diagnostics),
        usage=AnswerProviderUsage(
            statements_proposed=len(statements),
            citations_attached=len(ordered),
            characters_produced=sum(len(item.text) for item in statements),
        ),
        insufficient_evidence=payload.insufficient_evidence or not statements,
    )
