"""Grounding and answer text value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.answering.errors import AnsweringLimitError
from codestrata_platform.domain.answering.lifecycle import GroundingStatus
from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.retrieval.document import sanitize_retrieval_text

HARD_MAX_ANSWER_CHARS = 12_000


@dataclass(frozen=True, slots=True)
class GroundingIssue:
    code: str
    message: str
    severity: str = "warning"

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", self.code.strip())
        object.__setattr__(self, "message", self.message.strip()[:500])
        if not self.code or not self.message:
            raise InvalidValueError(
                "grounding issue requires code and message",
                reason_code="invalid_grounding_issue",
            )


@dataclass(frozen=True, slots=True)
class AnswerText:
    value: str

    def __post_init__(self) -> None:
        compact = sanitize_retrieval_text(self.value, max_length=HARD_MAX_ANSWER_CHARS)
        if not compact:
            raise InvalidValueError(
                "answer text must be non-blank",
                reason_code="empty_answer_text",
            )
        if len(compact) > HARD_MAX_ANSWER_CHARS:
            raise AnsweringLimitError(
                "answer text exceeds maximum length",
                reason_code="answer_too_long",
            )
        object.__setattr__(self, "value", compact)


@dataclass(frozen=True, slots=True)
class GroundingResult:
    status: GroundingStatus
    issues: tuple[GroundingIssue, ...] = ()
    cited_labels: tuple[str, ...] = ()
