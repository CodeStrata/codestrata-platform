"""Repository registry aggregate for the Commercial Platform."""

from __future__ import annotations

from codestrata_platform.domain.repository.aggregate import Repository
from codestrata_platform.domain.repository.enums import (
    RepositoryProvider,
    RepositoryStatus,
    RepositoryVisibility,
)
from codestrata_platform.domain.repository.ids import RepositoryId
from codestrata_platform.domain.repository.ports import RepositoryRepository
from codestrata_platform.domain.repository.value_objects import (
    RepositoryMetadata,
    RepositorySnapshot,
)

__all__ = [
    "Repository",
    "RepositoryId",
    "RepositoryMetadata",
    "RepositoryProvider",
    "RepositoryRepository",
    "RepositorySnapshot",
    "RepositoryStatus",
    "RepositoryVisibility",
]
