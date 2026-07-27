"""Artifact value objects."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError

_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
_SECRET_KEY_MARKERS = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "credential",
)


@dataclass(frozen=True, slots=True)
class ArtifactChecksum:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip().lower()
        if not compact:
            raise InvalidValueError(
                "Artifact checksum must be non-blank",
                reason_code="empty_checksum",
            )
        if not _SHA256_RE.match(compact):
            raise InvalidValueError(
                "Artifact checksum must be a SHA-256 hex digest",
                reason_code="invalid_checksum",
            )
        object.__setattr__(self, "value", compact)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ArtifactSize:
    bytes: int

    def __post_init__(self) -> None:
        if self.bytes <= 0:
            raise InvalidValueError(
                "Artifact size must be positive",
                reason_code="invalid_artifact_size",
            )


@dataclass(frozen=True, slots=True)
class ArtifactVersion:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise InvalidValueError(
                "Artifact version must be >= 1",
                reason_code="invalid_artifact_version",
            )

    def next(self) -> ArtifactVersion:
        return ArtifactVersion(self.value + 1)


@dataclass(frozen=True, slots=True)
class ArtifactMetadata:
    attributes: Mapping[str, str]

    def __post_init__(self) -> None:
        normalized: dict[str, str] = {}
        for key, value in dict(self.attributes).items():
            compact_key = key.strip()
            compact_value = value.strip()
            if not compact_key or not compact_value:
                raise InvalidValueError(
                    "Artifact metadata keys and values must be non-blank",
                    reason_code="invalid_artifact_metadata",
                )
            lowered = compact_key.lower()
            if any(marker in lowered for marker in _SECRET_KEY_MARKERS):
                raise InvalidValueError(
                    f"Artifact metadata key '{compact_key}' is not allowed",
                    reason_code="secret_bearing_metadata",
                )
            normalized[compact_key] = compact_value
        object.__setattr__(self, "attributes", dict(sorted(normalized.items())))

    @classmethod
    def empty(cls) -> ArtifactMetadata:
        return cls({})


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    """Opaque storage locator — never a raw filesystem user path."""

    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "Artifact storage reference must be non-blank",
                reason_code="empty_storage_reference",
            )
        if ".." in compact.replace("\\", "/").split("/"):
            raise InvalidValueError(
                "Artifact storage reference must not contain path traversal",
                reason_code="path_traversal",
            )
        object.__setattr__(self, "value", compact)

    def __str__(self) -> str:
        return self.value
