"""Time value objects for audit and lifecycle metadata."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from codestrata_platform.domain.errors import InvalidValueError


def _ensure_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        raise InvalidValueError(
            "Timestamps must be timezone-aware (UTC preferred)",
            reason_code="naive_timestamp",
        )
    return moment.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class CreatedAt:
    value: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _ensure_utc(self.value))

    @classmethod
    def now(cls) -> CreatedAt:
        return cls(datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class UpdatedAt:
    value: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _ensure_utc(self.value))

    @classmethod
    def now(cls) -> UpdatedAt:
        return cls(datetime.now(UTC))

    @classmethod
    def from_created(cls, created: CreatedAt) -> UpdatedAt:
        return cls(created.value)
