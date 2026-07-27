"""Cross-repository ranking contribution value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.repository.ids import RepositoryId

HARD_MAX_CONTRIBUTING_REPOSITORIES = 100


@dataclass(frozen=True, slots=True)
class RepositoryContribution:
    """A single repository's contribution to a portfolio-level retrieval hit."""

    repository_id: RepositoryId
    contribution_score: float
    finding_count: int = 0
    is_primary: bool = False

    def __post_init__(self) -> None:
        score = float(self.contribution_score)
        if score != score or score in {float("inf"), float("-inf")} or score < 0 or score > 1:
            raise InvalidValueError(
                "contribution_score must be between 0 and 1",
                reason_code="invalid_repository_contribution_score",
            )
        if self.finding_count < 0:
            raise InvalidValueError(
                "finding_count must be >= 0",
                reason_code="invalid_repository_contribution_finding_count",
            )
