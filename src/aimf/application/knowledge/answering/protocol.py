"""Answer provider protocol models (Phase 5.6)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, field_validator

from aimf.domain.graph.validation import as_tuple, require_nonblank
from aimf.domain.knowledge.answering import (
    AnswerCitation,
    AnswerModelIdentity,
    AnswerStatement,
    AnswerStyle,
)
from aimf.domain.knowledge.retrieval import RetrievalHit


class AnswerProviderUsage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    statements_proposed: int = Field(default=0, ge=0)
    citations_attached: int = Field(default=0, ge=0)
    characters_produced: int = Field(default=0, ge=0)


class AnswerProviderDiagnostic(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    message: str
    severity: str = "info"

    @field_validator("code", "message", "severity", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="answer provider diagnostic")


class AnswerProviderHealth(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    healthy: bool
    message: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)


class AnswerProviderCapabilities(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    provider_id: str
    supports_freeform_synthesis: bool = False
    supports_streaming: bool = False
    is_generative_ai: bool = False
    is_production_model: bool = False
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("provider_id", mode="before")
    @classmethod
    def normalize_provider_id(cls, value: object) -> str:
        return require_nonblank(str(value), label="provider_id").strip().lower()


class AnswerProviderRequest(BaseModel):
    """Bounded request passed to an AnswerProvider (no secrets / embeddings)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    question: str
    normalized_question: str
    style: AnswerStyle
    hits: tuple[RetrievalHit, ...] = ()
    citation_labels: tuple[str, ...] = ()
    max_statements: int = Field(default=20, ge=1)
    max_answer_characters: int = Field(default=12_000, ge=1)
    max_excerpt_characters: int = Field(default=800, ge=1)
    max_statements_per_source: int = Field(default=2, ge=1)
    preserve_source_sentences: bool = True
    constraints: dict[str, Any] = Field(default_factory=dict)

    @field_validator("question", "normalized_question", mode="before")
    @classmethod
    def normalize_required(cls, value: object) -> str:
        return require_nonblank(str(value), label="answer provider request field")

    @field_validator("hits", mode="before")
    @classmethod
    def normalize_hits(cls, value: object) -> tuple[RetrievalHit, ...]:
        if value is None:
            return ()
        items = as_tuple(value)
        return tuple(
            item if isinstance(item, RetrievalHit) else RetrievalHit.model_validate(item)
            for item in items
        )

    @field_validator("citation_labels", mode="before")
    @classmethod
    def normalize_labels(cls, value: object) -> tuple[str, ...]:
        if value is None:
            return ()
        return tuple(str(item) for item in as_tuple(value))

    @field_validator("constraints", mode="before")
    @classmethod
    def normalize_constraints(cls, value: object) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise ValueError("constraints must be a mapping")
        return dict(value)


class AnswerProviderResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: str
    statements: tuple[AnswerStatement, ...] = ()
    citations: tuple[AnswerCitation, ...] = ()
    diagnostics: tuple[AnswerProviderDiagnostic, ...] = ()
    usage: AnswerProviderUsage = Field(default_factory=AnswerProviderUsage)
    insufficient_evidence: bool = False

    @field_validator("summary", mode="before")
    @classmethod
    def normalize_summary(cls, value: object) -> str:
        return str(value)

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

    @field_validator("citations", mode="before")
    @classmethod
    def normalize_citations(cls, value: object) -> tuple[AnswerCitation, ...]:
        if value is None:
            return ()
        items = as_tuple(value)
        return tuple(
            item if isinstance(item, AnswerCitation) else AnswerCitation.model_validate(item)
            for item in items
        )


@runtime_checkable
class AnswerProvider(Protocol):
    """Provider-neutral grounded answer generation contract."""

    def generate(self, request: AnswerProviderRequest) -> AnswerProviderResult:
        """Produce a draft grounded answer from retrieved hits."""

    def health(self) -> AnswerProviderHealth:
        """Return provider readiness."""

    def capabilities(self) -> AnswerProviderCapabilities:
        """Advertise provider capabilities."""

    def model_identity(self) -> AnswerModelIdentity:
        """Return stable provider/model identity."""
