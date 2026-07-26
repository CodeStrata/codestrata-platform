"""Grounded repository answer domain models (Phase 5.6)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aimf.domain.graph.validation import as_tuple, optional_nonblank, require_nonblank
from aimf.domain.knowledge.identifiers import fingerprint_payload
from aimf.domain.knowledge.retrieval import (
    RetrievalContext,
    RetrievalFilters,
    RetrievalScope,
)
from aimf.domain.knowledge.schemas import (
    ANSWER_CITATION_SCHEMA_NAME,
    ANSWER_CITATION_SCHEMA_VERSION,
    ANSWER_STATEMENT_SCHEMA_NAME,
    ANSWER_STATEMENT_SCHEMA_VERSION,
    GROUNDED_ANSWER_REQUEST_SCHEMA_NAME,
    GROUNDED_ANSWER_REQUEST_SCHEMA_VERSION,
    GROUNDED_ANSWER_RESULT_SCHEMA_NAME,
    GROUNDED_ANSWER_RESULT_SCHEMA_VERSION,
    GROUNDED_ANSWER_SCHEMA_NAME,
    GROUNDED_ANSWER_SCHEMA_VERSION,
)


class AnswerStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    EMPTY = "empty"
    FAILED = "failed"
    DISABLED = "disabled"


class AnswerConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class AnswerStyle(StrEnum):
    CONCISE = "concise"
    DETAILED = "detailed"
    FINDINGS_SUMMARY = "findings_summary"
    RECOMMENDATION_SUMMARY = "recommendation_summary"
    ARCHITECTURE_EXPLANATION = "architecture_explanation"
    EVIDENCE_ONLY = "evidence_only"


class AnswerStatementType(StrEnum):
    FACT = "fact"
    FINDING = "finding"
    RECOMMENDATION = "recommendation"
    LIMITATION = "limitation"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class AnswerCitation(BaseModel):
    """Citation bound to an existing retrieval SRC label."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_name: str = ANSWER_CITATION_SCHEMA_NAME
    schema_version: str = ANSWER_CITATION_SCHEMA_VERSION
    citation_label: str
    record_id: str
    chunk_id: str | None = None
    document_id: str | None = None
    source_type: str | None = None
    intelligence_pack: str | None = None
    file_path: str | None = None
    symbol_name: str | None = None
    finding_id: str | None = None
    rule_id: str | None = None
    scan_id: str | None = None
    commit_sha: str | None = None
    traceability: dict[str, Any] = Field(default_factory=dict)
    excerpt: str | None = None

    @field_validator("citation_label", "record_id", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="answer citation field")

    @field_validator(
        "chunk_id",
        "document_id",
        "source_type",
        "intelligence_pack",
        "file_path",
        "symbol_name",
        "finding_id",
        "rule_id",
        "scan_id",
        "commit_sha",
        "excerpt",
        mode="before",
    )
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="answer citation optional")

    @field_validator("traceability", mode="before")
    @classmethod
    def normalize_traceability(cls, value: object) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError("traceability must be a mapping")
        return dict(value)


class AnswerStatement(BaseModel):
    """One grounded answer statement with optional citations."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_name: str = ANSWER_STATEMENT_SCHEMA_NAME
    schema_version: str = ANSWER_STATEMENT_SCHEMA_VERSION
    statement_id: str
    sequence: int = Field(ge=0)
    text: str
    citation_labels: tuple[str, ...] = ()
    confidence: AnswerConfidence = AnswerConfidence.LOW
    evidence_strength: str = "low"
    statement_type: AnswerStatementType = AnswerStatementType.FACT

    @field_validator("statement_id", "text", "evidence_strength", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="answer statement field")

    @field_validator("citation_labels", mode="before")
    @classmethod
    def normalize_labels(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        return tuple(str(item) for item in as_tuple(value))


class AnswerSection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    section_id: str
    title: str
    sequence: int = Field(ge=0)
    statements: tuple[AnswerStatement, ...] = ()

    @field_validator("section_id", "title", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="answer section field")

    @field_validator("statements", mode="before")
    @classmethod
    def normalize_statements(cls, value: object) -> tuple[AnswerStatement, ...]:
        if value is None:
            return ()
        items = as_tuple(value)
        return tuple(
            item if isinstance(item, AnswerStatement) else AnswerStatement.model_validate(item)
            for item in items
        )


class AnswerEvidence(BaseModel):
    """Optional evidence payload referencing retrieval hits."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    citation_label: str
    record_id: str
    score: float | None = None
    content: str | None = None

    @field_validator("citation_label", "record_id", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="answer evidence field")


class AnswerCoverage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    retrieval_candidates: int = Field(default=0, ge=0)
    retrieval_hits: int = Field(default=0, ge=0)
    evidence_hits_considered: int = Field(default=0, ge=0)
    statements_proposed: int = Field(default=0, ge=0)
    statements_accepted: int = Field(default=0, ge=0)
    statements_excluded: int = Field(default=0, ge=0)
    cited_statements: int = Field(default=0, ge=0)
    uncited_statements: int = Field(default=0, ge=0)
    citations_used: int = Field(default=0, ge=0)
    unique_documents_cited: int = Field(default=0, ge=0)
    unique_files_cited: int = Field(default=0, ge=0)
    unique_findings_cited: int = Field(default=0, ge=0)
    source_types: tuple[str, ...] = ()
    intelligence_packs: tuple[str, ...] = ()
    context_characters_used: int = Field(default=0, ge=0)
    answer_characters_produced: int = Field(default=0, ge=0)

    @field_validator("source_types", "intelligence_packs", mode="before")
    @classmethod
    def normalize_tuples(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        return tuple(str(item) for item in as_tuple(value))


class AnswerDiagnostic(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    message: str
    severity: str = "info"
    statement_id: str | None = None
    citation_label: str | None = None

    @field_validator("code", "message", "severity", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="answer diagnostic field")

    @field_validator("statement_id", "citation_label", mode="before")
    @classmethod
    def normalize_optional(cls, value: object) -> str | None:
        if value is None:
            return None
        return optional_nonblank(str(value), label="answer diagnostic optional")


class AnswerLimitation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    message: str

    @field_validator("code", "message", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="answer limitation field")


class AnswerModelIdentity(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_id: str
    model: str
    model_version: str
    is_production_model: bool = False
    is_generative_ai: bool = False

    @field_validator("provider_id", "model", "model_version", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="answer model identity field")


class GroundedAnswer(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_name: str = GROUNDED_ANSWER_SCHEMA_NAME
    schema_version: str = GROUNDED_ANSWER_SCHEMA_VERSION
    answer_id: str
    question: str
    normalized_question: str
    summary: str
    sections: tuple[AnswerSection, ...] = ()
    statements: tuple[AnswerStatement, ...] = ()
    citations: tuple[AnswerCitation, ...] = ()
    confidence: AnswerConfidence = AnswerConfidence.NONE
    limitations: tuple[str, ...] = ()
    retrieval_result_fingerprint: str | None = None
    provider: AnswerModelIdentity
    fingerprint: str

    @field_validator(
        "answer_id",
        "question",
        "normalized_question",
        "summary",
        "fingerprint",
        mode="before",
    )
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="grounded answer field")

    @field_validator("limitations", mode="before")
    @classmethod
    def normalize_limitations(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        return tuple(str(item) for item in as_tuple(value))


class GroundedAnswerRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_name: str = GROUNDED_ANSWER_REQUEST_SCHEMA_NAME
    schema_version: str = GROUNDED_ANSWER_REQUEST_SCHEMA_VERSION
    question: str
    scope: RetrievalScope
    filters: RetrievalFilters = Field(default_factory=RetrievalFilters)
    top_k: int = Field(default=10, ge=1)
    candidate_limit: int = Field(default=30, ge=1)
    minimum_score: float = 0.0
    style: AnswerStyle = AnswerStyle.CONCISE
    max_answer_characters: int = Field(default=12_000, ge=1)
    max_statements: int = Field(default=20, ge=1)
    include_evidence: bool = True
    include_retrieval_context: bool = False
    include_diagnostics: bool = True
    require_citations: bool = True
    minimum_supporting_sources: int = Field(default=1, ge=1)
    fail_on_insufficient_evidence: bool = False
    max_query_characters: int = Field(default=4000, ge=1)

    @field_validator("question", mode="before")
    @classmethod
    def normalize_question(cls, value: object) -> str:
        return str(value)


class GroundedAnswerResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_name: str = GROUNDED_ANSWER_RESULT_SCHEMA_NAME
    schema_version: str = GROUNDED_ANSWER_RESULT_SCHEMA_VERSION
    status: AnswerStatus
    request_fingerprint: str | None = None
    answer: GroundedAnswer | None = None
    evidence: tuple[AnswerEvidence, ...] = ()
    retrieval_context: RetrievalContext | None = None
    coverage: AnswerCoverage = Field(default_factory=AnswerCoverage)
    diagnostics: tuple[AnswerDiagnostic, ...] = ()
    limitations: tuple[AnswerLimitation, ...] = ()
    retrieval_status: str | None = None
    retrieval_fingerprint: str | None = None

    @field_validator("diagnostics", mode="before")
    @classmethod
    def normalize_diagnostics(cls, value: object) -> tuple[AnswerDiagnostic, ...]:
        if value is None:
            return ()
        items = as_tuple(value)
        return tuple(
            item if isinstance(item, AnswerDiagnostic) else AnswerDiagnostic.model_validate(item)
            for item in items
        )

    @field_validator("limitations", mode="before")
    @classmethod
    def normalize_limitations(cls, value: object) -> tuple[AnswerLimitation, ...]:
        if value is None:
            return ()
        items = as_tuple(value)
        return tuple(
            item if isinstance(item, AnswerLimitation) else AnswerLimitation.model_validate(item)
            for item in items
        )

    @field_validator("evidence", mode="before")
    @classmethod
    def normalize_evidence(cls, value: object) -> tuple[AnswerEvidence, ...]:
        if value is None:
            return ()
        items = as_tuple(value)
        return tuple(
            item if isinstance(item, AnswerEvidence) else AnswerEvidence.model_validate(item)
            for item in items
        )


def grounded_answer_result_payload(result: GroundedAnswerResult) -> dict[str, Any]:
    return result.model_dump(mode="json")


def build_request_fingerprint(request: GroundedAnswerRequest) -> str:
    return fingerprint_payload(
        {
            "question": request.question,
            "scope": request.scope.model_dump(mode="json"),
            "filters": request.filters.model_dump(mode="json"),
            "top_k": request.top_k,
            "candidate_limit": request.candidate_limit,
            "minimum_score": request.minimum_score,
            "style": request.style.value,
            "max_answer_characters": request.max_answer_characters,
            "max_statements": request.max_statements,
            "require_citations": request.require_citations,
            "minimum_supporting_sources": request.minimum_supporting_sources,
        }
    )


def build_answer_fingerprint(
    *,
    answer_id: str,
    normalized_question: str,
    statement_ids: Sequence[str],
    citation_labels: Sequence[str],
    status: AnswerStatus,
    confidence: AnswerConfidence,
) -> str:
    return fingerprint_payload(
        {
            "answer_id": answer_id,
            "normalized_question": normalized_question,
            "statement_ids": list(statement_ids),
            "citation_labels": list(citation_labels),
            "status": status.value,
            "confidence": confidence.value,
        }
    )
