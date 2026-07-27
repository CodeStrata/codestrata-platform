"""Assessment intelligence identity types."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.shared.ids import PlatformId


@dataclass(frozen=True, slots=True)
class AssessmentIntelligenceId:
    value: str

    def __post_init__(self) -> None:
        platform_id = PlatformId(self.value)
        object.__setattr__(self, "value", platform_id.value)

    @classmethod
    def generate(cls) -> AssessmentIntelligenceId:
        return cls(PlatformId.generate(prefix="intelligence").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class FindingId:
    value: str

    def __post_init__(self) -> None:
        platform_id = PlatformId(self.value)
        object.__setattr__(self, "value", platform_id.value)

    @classmethod
    def generate(cls) -> FindingId:
        return cls(PlatformId.generate(prefix="finding").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EvidenceReferenceId:
    value: str

    def __post_init__(self) -> None:
        platform_id = PlatformId(self.value)
        object.__setattr__(self, "value", platform_id.value)

    @classmethod
    def generate(cls) -> EvidenceReferenceId:
        return cls(PlatformId.generate(prefix="evidence").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class RecommendationId:
    value: str

    def __post_init__(self) -> None:
        platform_id = PlatformId(self.value)
        object.__setattr__(self, "value", platform_id.value)

    @classmethod
    def generate(cls) -> RecommendationId:
        return cls(PlatformId.generate(prefix="recommendation").value)

    def __str__(self) -> str:
        return self.value
