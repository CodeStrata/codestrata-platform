"""Workspace aggregate for isolated customer environments."""

from __future__ import annotations

from codestrata_platform.domain.workspace.aggregate import Workspace
from codestrata_platform.domain.workspace.enums import WorkspaceStatus
from codestrata_platform.domain.workspace.ids import WorkspaceId
from codestrata_platform.domain.workspace.ports import WorkspaceRepository

__all__ = [
    "Workspace",
    "WorkspaceId",
    "WorkspaceRepository",
    "WorkspaceStatus",
]
