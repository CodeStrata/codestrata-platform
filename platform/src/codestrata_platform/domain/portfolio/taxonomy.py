"""Cross-repository dependency and shared-exposure signals."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.portfolio.lifecycle import DependencySignalType
from codestrata_platform.domain.repository.ids import RepositoryId


@dataclass(frozen=True, slots=True)
class CrossRepositoryDependencySignal:
    signal_key: str
    signal_type: DependencySignalType
    is_explicit_dependency: bool
    is_shared_exposure: bool
    repository_ids: tuple[RepositoryId, ...]
    shared_key: str
    description: str
    source_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SharedDependencySummary:
    signals: tuple[CrossRepositoryDependencySignal, ...]
    explicit_dependency_count: int
    shared_exposure_count: int
