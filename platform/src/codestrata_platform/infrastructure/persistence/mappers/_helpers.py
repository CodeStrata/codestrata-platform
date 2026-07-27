"""Shared mapping helpers for persistence timestamps and JSON bags."""

from __future__ import annotations

from datetime import UTC, datetime

from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.shared.time import CreatedAt, UpdatedAt


def ensure_utc(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def audit_from_record(*, created_at: datetime, updated_at: datetime) -> AuditInfo:
    return AuditInfo(
        created_at=CreatedAt(ensure_utc(created_at)),
        updated_at=UpdatedAt(ensure_utc(updated_at)),
    )


def normalize_repository_url(url: str) -> str:
    """Match Application duplicate-detection normalization (Infrastructure copy)."""

    return url.strip().rstrip("/").lower()
