"""Typed platform identity primitives."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


@dataclass(frozen=True, slots=True)
class PlatformId:
    """Opaque, non-blank platform identity string.

    Aggregate-specific ids specialize this type with prefixes for clarity
    without coupling the shared kernel to every aggregate.
    """

    value: str

    def __post_init__(self) -> None:
        text = self.value.strip()
        if not text:
            raise InvalidValueError(
                "Platform id must be non-blank",
                reason_code="empty_platform_id",
            )
        if not _ID_PATTERN.match(text):
            raise InvalidValueError(
                "Platform id contains unsupported characters",
                reason_code="invalid_platform_id",
            )
        object.__setattr__(self, "value", text)

    @classmethod
    def generate(cls, *, prefix: str | None = None) -> PlatformId:
        token = uuid.uuid4().hex
        if prefix:
            compact = prefix.strip().lower().rstrip(":")
            if not compact:
                raise InvalidValueError(
                    "Platform id prefix must be non-blank when provided",
                    reason_code="empty_platform_id_prefix",
                )
            return cls(f"{compact}:{token}")
        return cls(token)

    def __str__(self) -> str:
        return self.value
