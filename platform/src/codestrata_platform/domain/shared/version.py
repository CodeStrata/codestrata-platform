"""Platform version value object."""

from __future__ import annotations

import re
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError

_VERSION_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


@dataclass(frozen=True, slots=True)
class PlatformVersion:
    """Semantic version string for Platform releases and contracts."""

    value: str

    def __post_init__(self) -> None:
        text = self.value.strip()
        if not _VERSION_PATTERN.match(text):
            raise InvalidValueError(
                "Platform version must be a semantic version string",
                reason_code="invalid_platform_version",
            )
        object.__setattr__(self, "value", text)

    def __str__(self) -> str:
        return self.value
