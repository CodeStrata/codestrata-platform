"""Audit metadata shared across Commercial Platform aggregates."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.shared.time import CreatedAt, UpdatedAt


@dataclass(frozen=True, slots=True)
class AuditInfo:
    """Creation and update timestamps for aggregate lifecycle tracking."""

    created_at: CreatedAt
    updated_at: UpdatedAt

    @classmethod
    def create(cls, *, at: CreatedAt | None = None) -> AuditInfo:
        created = at or CreatedAt.now()
        return cls(created_at=created, updated_at=UpdatedAt.from_created(created))

    def touch(self, *, at: UpdatedAt | None = None) -> AuditInfo:
        return AuditInfo(
            created_at=self.created_at,
            updated_at=at or UpdatedAt.now(),
        )
