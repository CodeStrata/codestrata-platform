"""Portfolio retrieval citation value objects."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError


def _bounded(value: str, *, field_name: str, max_length: int) -> str:
    compact = value.strip()
    if not compact:
        raise InvalidValueError(
            f"{field_name} must be non-blank",
            reason_code=f"empty_{field_name}",
        )
    if len(compact) > max_length:
        raise InvalidValueError(
            f"{field_name} exceeds maximum length",
            reason_code=f"{field_name}_too_long",
        )
    return compact


@dataclass(frozen=True, slots=True)
class PortfolioRetrievalCitation:
    """Bounded provenance reference for portfolio retrieval content."""

    source_kind: str
    source_id: str
    repository_id: str | None = None
    engineering_snapshot_id: str | None = None
    portfolio_snapshot_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "source_kind",
            _bounded(self.source_kind, field_name="source_kind", max_length=64),
        )
        object.__setattr__(
            self,
            "source_id",
            _bounded(self.source_id, field_name="source_id", max_length=160),
        )
