"""Pagination contracts for application queries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PageRequest:
    """Offset/limit pagination request."""

    offset: int = 0
    limit: int = 50

    def __post_init__(self) -> None:
        if self.offset < 0:
            raise ValueError("page offset must be >= 0")
        if self.limit < 1:
            raise ValueError("page limit must be >= 1")
        if self.limit > 500:
            raise ValueError("page limit must be <= 500")


@dataclass(frozen=True, slots=True)
class PageResult[T]:
    """Paginated query result."""

    items: tuple[T, ...]
    total: int
    offset: int
    limit: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.items) < self.total
