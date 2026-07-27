"""Artifact content storage adapters."""

from __future__ import annotations

from codestrata_platform.infrastructure.storage.artifacts import (
    FileSystemArtifactStorage,
    InMemoryArtifactStorage,
)

__all__ = [
    "FileSystemArtifactStorage",
    "InMemoryArtifactStorage",
]
