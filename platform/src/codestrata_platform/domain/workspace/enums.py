"""Workspace enums."""

from __future__ import annotations

from enum import StrEnum


class WorkspaceStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
