"""Engineering question value objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.domain.answering.errors import AnsweringLimitError, AnsweringRejectionError
from codestrata_platform.domain.answering.lifecycle import QuestionType
from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.retrieval.taxonomy import RetrievalContentType

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
class QuestionScope:
    organization_id: str
    workspace_id: str
    repository_id: str
    retrieval_index_id: str | None = None
    canonical_ids: tuple[str, ...] = ()
    graph_node_ids: tuple[str, ...] = ()
    content_types: tuple[RetrievalContentType, ...] = ()
    severity: str | None = None
    category: str | None = None

    def __post_init__(self) -> None:
        for name in ("organization_id", "workspace_id", "repository_id"):
            value = getattr(self, name).strip()
            if not value:
                raise InvalidValueError(
                    f"{name} must be non-blank",
                    reason_code=f"empty_{name}",
                )
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class EngineeringQuestion:
    text: str
    scope: QuestionScope
    question_type: QuestionType | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        compact = self.text.strip()
        if not compact:
            raise InvalidValueError(
                "question must be non-blank",
                reason_code="empty_engineering_question",
            )
        if len(compact) > HARD_MAX_QUESTION_LENGTH:
            raise AnsweringLimitError(
                f"question exceeds hard maximum of {HARD_MAX_QUESTION_LENGTH} characters",
                reason_code="question_too_long",
            )
        if len(compact) > DEFAULT_MAX_QUESTION_LENGTH:
            raise AnsweringLimitError(
                f"question exceeds maximum of {DEFAULT_MAX_QUESTION_LENGTH} characters",
                reason_code="question_too_long",
            )
        lowered = compact.lower()
        if any(marker in lowered for marker in _SECRET_MARKERS):
            raise AnsweringRejectionError(
                "Questions requesting credentials or secrets are rejected",
                reason_code="secret_request_rejected",
            )
        if any(marker in lowered for marker in _PROMPT_LEAK_MARKERS):
            raise AnsweringRejectionError(
                "Requests for hidden prompts or instruction overrides are rejected",
                reason_code="prompt_leak_request_rejected",
            )
        if any(marker in lowered for marker in _SOURCE_EXTRACTION_MARKERS):
            raise AnsweringRejectionError(
                "Unrestricted source-code extraction requests are rejected",
                reason_code="source_extraction_rejected",
            )
        object.__setattr__(self, "text", compact)
