"""Answer citation and confidence value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.answering.identifiers import AnswerCitationId
from codestrata_platform.domain.answering.lifecycle import AnswerConfidenceLevel
from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.retrieval.document import sanitize_retrieval_text

_MAX_EXCERPT = 800


@dataclass(frozen=True, slots=True)
class AnswerCitation:
    citation_id: AnswerCitationId
    label: str
    document_id: str
    chunk_id: str
    content_type: str
    canonical_type: str
    canonical_id: str
    source_references: tuple[str, ...]
    graph_node_ids: tuple[str, ...]
    graph_edge_ids: tuple[str, ...]
    retrieval_score: float
    excerpt: str

    def __post_init__(self) -> None:
        label = self.label.strip()
        if not label.startswith("[") or not label.endswith("]"):
            raise InvalidValueError(
                "citation label must be bracketed, e.g. [C1]",
                reason_code="invalid_citation_label",
            )
        object.__setattr__(self, "label", label)
        object.__setattr__(
            self,
            "excerpt",
            sanitize_retrieval_text(self.excerpt, max_length=_MAX_EXCERPT),
        )
        if self.retrieval_score < 0:
            raise InvalidValueError(
                "retrieval_score must be >= 0",
                reason_code="invalid_citation_score",
            )


@dataclass(frozen=True, slots=True)
class AnswerConfidence:
    level: AnswerConfidenceLevel
    score: int
    factors: tuple[str, ...]
    policy_version: str

    def __post_init__(self) -> None:
        if self.score < 0 or self.score > 100:
            raise InvalidValueError(
                "confidence score must be between 0 and 100",
                reason_code="invalid_confidence_score",
            )
