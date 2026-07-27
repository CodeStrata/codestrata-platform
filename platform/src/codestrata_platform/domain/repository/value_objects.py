"""Repository value objects."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.shared.time import CreatedAt


@dataclass(frozen=True, slots=True)
class RepositoryMetadata:
    """Extensible, immutable metadata bag for a registered repository."""

    attributes: Mapping[str, str]

    def __post_init__(self) -> None:
        normalized: dict[str, str] = {}
        for key, value in dict(self.attributes).items():
            compact_key = key.strip()
            compact_value = value.strip()
            if not compact_key:
                raise InvalidValueError(
                    "Repository metadata keys must be non-blank",
                    reason_code="empty_metadata_key",
                )
            if not compact_value:
                raise InvalidValueError(
                    "Repository metadata values must be non-blank",
                    reason_code="empty_metadata_value",
                )
            normalized[compact_key] = compact_value
        object.__setattr__(self, "attributes", dict(sorted(normalized.items())))

    @classmethod
    def empty(cls) -> RepositoryMetadata:
        return cls({})

    def merge(self, updates: Mapping[str, str]) -> RepositoryMetadata:
        merged = dict(self.attributes)
        merged.update(dict(updates))
        return RepositoryMetadata(merged)


@dataclass(frozen=True, slots=True)
class RepositorySnapshot:
    """Point-in-time identity snapshot for an assessed repository revision.

    This is not a clone and does not contain source contents.
    """

    commit_sha: str
    captured_at: CreatedAt
    ref_name: str | None = None

    def __post_init__(self) -> None:
        sha = self.commit_sha.strip().lower()
        if len(sha) < 7:
            raise InvalidValueError(
                "Repository snapshot commit SHA must be at least 7 characters",
                reason_code="invalid_commit_sha",
            )
        if any(ch not in "0123456789abcdef" for ch in sha):
            raise InvalidValueError(
                "Repository snapshot commit SHA must be hexadecimal",
                reason_code="invalid_commit_sha",
            )
        ref = self.ref_name.strip() if self.ref_name else None
        if self.ref_name is not None and not ref:
            raise InvalidValueError(
                "Repository snapshot ref name must be non-blank when provided",
                reason_code="empty_ref_name",
            )
        object.__setattr__(self, "commit_sha", sha)
        object.__setattr__(self, "ref_name", ref)
