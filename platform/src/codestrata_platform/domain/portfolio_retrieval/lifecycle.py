"""Portfolio retrieval index lifecycle value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from codestrata_platform.domain.errors import InvalidValueError


class PortfolioRetrievalIndexStatus(StrEnum):
    PENDING = "pending"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalIndexVersion:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise InvalidValueError(
                "portfolio retrieval index version must be >= 1",
                reason_code="invalid_portfolio_retrieval_index_version",
            )


class PortfolioRetrievalStalenessReason(StrEnum):
    PORTFOLIO_SNAPSHOT_CHANGED = "portfolio_snapshot_changed"
    REPOSITORY_SELECTION_CHANGED = "repository_selection_changed"
    EMBEDDING_MODEL_CHANGED = "embedding_model_changed"
    CHUNKING_POLICY_CHANGED = "chunking_policy_changed"
    RANKING_POLICY_CHANGED = "ranking_policy_changed"
    RETRIEVAL_SCHEMA_CHANGED = "retrieval_schema_changed"


class RepositoryBalanceMode(StrEnum):
    NONE = "none"
    DIVERSIFIED = "diversified"
    PROPORTIONAL = "proportional"
    CRITICALITY_AWARE = "criticality_aware"
