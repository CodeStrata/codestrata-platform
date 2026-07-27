"""Repository identity."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.shared.ids import PlatformId


@dataclass(frozen=True, slots=True)
class RepositoryId:
    value: str

    def __post_init__(self) -> None:
        platform_id = PlatformId(self.value)
        object.__setattr__(self, "value", platform_id.value)

    @classmethod
    def generate(cls) -> RepositoryId:
        return cls(PlatformId.generate(prefix="repo").value)

    @classmethod
    def from_platform_id(cls, platform_id: PlatformId) -> RepositoryId:
        if not isinstance(platform_id, PlatformId):
            raise InvalidValueError(
                "RepositoryId requires a PlatformId",
                reason_code="invalid_repository_id",
            )
        return cls(platform_id.value)

    def __str__(self) -> str:
        return self.value
