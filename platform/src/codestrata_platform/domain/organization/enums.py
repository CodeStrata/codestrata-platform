"""Organization enums."""

from __future__ import annotations

from enum import StrEnum


class OrganizationStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
