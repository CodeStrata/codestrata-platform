"""Application query models."""

from __future__ import annotations

from codestrata_platform.application.queries.assessment import AssessmentQuery
from codestrata_platform.application.queries.organization import OrganizationQuery
from codestrata_platform.application.queries.repository import RepositoryQuery
from codestrata_platform.application.queries.workspace import WorkspaceQuery

__all__ = [
    "AssessmentQuery",
    "OrganizationQuery",
    "RepositoryQuery",
    "WorkspaceQuery",
]
