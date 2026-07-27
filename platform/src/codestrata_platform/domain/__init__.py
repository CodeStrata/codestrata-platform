"""Commercial Platform domain foundation (Phase 8.1.1).

Pure domain models with zero framework dependencies. The Community Engine
remains independent; this package never performs repository analysis.
"""

from __future__ import annotations

from codestrata_platform.domain.assessment import (
    Assessment,
    AssessmentId,
    AssessmentReference,
    AssessmentStatus,
    AssessmentVersion,
    GeneratedReport,
)
from codestrata_platform.domain.organization import (
    Organization,
    OrganizationId,
    OrganizationStatus,
)
from codestrata_platform.domain.repository import (
    Repository,
    RepositoryId,
    RepositoryMetadata,
    RepositoryProvider,
    RepositorySnapshot,
    RepositoryStatus,
    RepositoryVisibility,
)
from codestrata_platform.domain.shared import (
    AuditInfo,
    CreatedAt,
    PlatformId,
    PlatformVersion,
    UpdatedAt,
)
from codestrata_platform.domain.workspace import (
    Workspace,
    WorkspaceId,
    WorkspaceStatus,
)

__all__ = [
    "Assessment",
    "AssessmentId",
    "AssessmentReference",
    "AssessmentStatus",
    "AssessmentVersion",
    "AuditInfo",
    "CreatedAt",
    "GeneratedReport",
    "Organization",
    "OrganizationId",
    "OrganizationStatus",
    "PlatformId",
    "PlatformVersion",
    "Repository",
    "RepositoryId",
    "RepositoryMetadata",
    "RepositoryProvider",
    "RepositorySnapshot",
    "RepositoryStatus",
    "RepositoryVisibility",
    "UpdatedAt",
    "Workspace",
    "WorkspaceId",
    "WorkspaceStatus",
]
