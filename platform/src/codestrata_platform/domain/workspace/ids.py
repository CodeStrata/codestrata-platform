"""Workspace identity."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.shared.ids import PlatformId


@dataclass(frozen=True, slots=True)
class WorkspaceId:
    value: str

    def __post_init__(self) -> None:
        platform_id = PlatformId(self.value)
        object.__setattr__(self, "value", platform_id.value)

    @classmethod
    def generate(cls) -> WorkspaceId:
        return cls(PlatformId.generate(prefix="workspace").value)

    def __str__(self) -> str:
        return self.value
