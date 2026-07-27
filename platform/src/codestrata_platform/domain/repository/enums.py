"""Repository enums."""

from __future__ import annotations

from enum import StrEnum


class RepositoryStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class RepositoryProvider(StrEnum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    AZURE_DEVOPS = "azure_devops"
    OTHER = "other"


class RepositoryVisibility(StrEnum):
    PRIVATE = "private"
    INTERNAL = "internal"
    PUBLIC = "public"
