"""Immutable application command models."""

from __future__ import annotations

from codestrata_platform.application.commands.assessment import (
    CompleteAssessmentCommand,
    FailAssessmentCommand,
    RegisterAssessmentCommand,
    StartAssessmentCommand,
)
from codestrata_platform.application.commands.organization import (
    ActivateOrganizationCommand,
    CreateOrganizationCommand,
    DeactivateOrganizationCommand,
    RenameOrganizationCommand,
)
from codestrata_platform.application.commands.repository import (
    ArchiveRepositoryCommand,
    RegisterRepositoryCommand,
    RenameRepositoryCommand,
    UpdateRepositoryMetadataCommand,
)
from codestrata_platform.application.commands.workspace import (
    ActivateWorkspaceCommand,
    CreateWorkspaceCommand,
    DeactivateWorkspaceCommand,
    RenameWorkspaceCommand,
)

__all__ = [
    "ActivateOrganizationCommand",
    "ActivateWorkspaceCommand",
    "ArchiveRepositoryCommand",
    "CompleteAssessmentCommand",
    "CreateOrganizationCommand",
    "CreateWorkspaceCommand",
    "DeactivateOrganizationCommand",
    "DeactivateWorkspaceCommand",
    "FailAssessmentCommand",
    "RegisterAssessmentCommand",
    "RegisterRepositoryCommand",
    "RenameOrganizationCommand",
    "RenameRepositoryCommand",
    "RenameWorkspaceCommand",
    "StartAssessmentCommand",
    "UpdateRepositoryMetadataCommand",
]
