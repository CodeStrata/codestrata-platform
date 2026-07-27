"""Assessment query models."""

from __future__ import annotations

from dataclasses import dataclass, field

from codestrata_platform.application.common.pagination import PageRequest
from codestrata_platform.domain.assessment import AssessmentStatus
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.workspace.ids import WorkspaceId


@dataclass(frozen=True, slots=True)
class AssessmentQuery:
    repository_id: RepositoryId | None = None
    workspace_id: WorkspaceId | None = None
    status: AssessmentStatus | None = None
    page: PageRequest = field(default_factory=PageRequest)
