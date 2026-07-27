"""Graph lifecycle value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from codestrata_platform.domain.errors import InvalidValueError


class GraphStatus(StrEnum):
    PENDING = "pending"
    PROJECTING = "projecting"
    COMPLETED = "completed"
    FAILED = "failed"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class GraphVersion:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise InvalidValueError(
                "graph version must be >= 1",
                reason_code="invalid_graph_version",
            )
