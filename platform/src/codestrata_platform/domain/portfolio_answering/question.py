"""Portfolio question value objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.portfolio_answering.errors import (
    PortfolioAnsweringLimitError,
    PortfolioAnsweringRejectionError,
)
from codestrata_platform.domain.portfolio_answering.lifecycle import PortfolioQuestionType
from codestrata_platform.domain.portfolio_retrieval.taxonomy import PortfolioRetrievalContentType

DEFAULT_MAX_QUESTION_LENGTH = 2_000
HARD_MAX_QUESTION_LENGTH = 5_000

_SECRET_MARKERS = (
    "password",
    "api_key",
    "private_key",
    "credential",
    "secret token",
    "authorization header",
)
_PROMPT_LEAK_MARKERS = (
    "reveal system prompt",
    "show system prompt",
    "ignore previous instructions",
    "hidden instructions",
)
_SOURCE_EXTRACTION_MARKERS = (
    "dump source code",
    "raw repository file",
    "print entire file",
    "cat the source",
)


@dataclass(frozen=True, slots=True)
class PortfolioQuestionScope:
    organization_id: str
    workspace_id: str
    portfolio_id: str
    portfolio_retrieval_index_id: str | None = None
    repository_ids: tuple[str, ...] = ()
    content_types: tuple[PortfolioRetrievalContentType, ...] = ()

    def __post_init__(self) -> None:
        for name in ("organization_id", "workspace_id", "portfolio_id"):
            value = getattr(self, name).strip()
            if not value:
                raise InvalidValueError(
                    f"{name} must be non-blank",
                    reason_code=f"empty_{name}",
                )
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class PortfolioQuestion:
    text: str
    scope: PortfolioQuestionScope
    question_type: PortfolioQuestionType | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        compact = self.text.strip()
        if not compact:
            raise InvalidValueError(
                "question must be non-blank",
                reason_code="empty_portfolio_question",
            )
        if len(compact) > HARD_MAX_QUESTION_LENGTH:
            raise PortfolioAnsweringLimitError(
                f"question exceeds hard maximum of {HARD_MAX_QUESTION_LENGTH} characters",
                reason_code="portfolio_question_too_long",
            )
        if len(compact) > DEFAULT_MAX_QUESTION_LENGTH:
            raise PortfolioAnsweringLimitError(
                f"question exceeds maximum of {DEFAULT_MAX_QUESTION_LENGTH} characters",
                reason_code="portfolio_question_too_long",
            )
        lowered = compact.lower()
        if any(marker in lowered for marker in _SECRET_MARKERS):
            raise PortfolioAnsweringRejectionError(
                "Questions requesting credentials or secrets are rejected",
                reason_code="secret_request_rejected",
            )
        if any(marker in lowered for marker in _PROMPT_LEAK_MARKERS):
            raise PortfolioAnsweringRejectionError(
                "Requests for hidden prompts or instruction overrides are rejected",
                reason_code="prompt_leak_request_rejected",
            )
        if any(marker in lowered for marker in _SOURCE_EXTRACTION_MARKERS):
            raise PortfolioAnsweringRejectionError(
                "Unrestricted source-code extraction requests are rejected",
                reason_code="source_extraction_rejected",
            )
        object.__setattr__(self, "text", compact)
