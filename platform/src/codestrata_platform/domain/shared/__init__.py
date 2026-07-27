"""Shared kernel for the Commercial Platform domain."""

from __future__ import annotations

from codestrata_platform.domain.shared.audit import AuditInfo
from codestrata_platform.domain.shared.ids import PlatformId
from codestrata_platform.domain.shared.time import CreatedAt, UpdatedAt
from codestrata_platform.domain.shared.version import PlatformVersion

__all__ = [
    "AuditInfo",
    "CreatedAt",
    "PlatformId",
    "PlatformVersion",
    "UpdatedAt",
]
