"""Typed identifiers for the Canonical Engineering Intelligence Model."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.domain.shared.ids import PlatformId


@dataclass(frozen=True, slots=True)
class EngineeringSnapshotId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> EngineeringSnapshotId:
        return cls(PlatformId.generate(prefix="eng-snapshot").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EngineeringComponentId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> EngineeringComponentId:
        return cls(PlatformId.generate(prefix="eng-component").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EngineeringTechnologyId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> EngineeringTechnologyId:
        return cls(PlatformId.generate(prefix="eng-technology").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EngineeringFindingId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> EngineeringFindingId:
        return cls(PlatformId.generate(prefix="eng-finding").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EngineeringRecommendationId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> EngineeringRecommendationId:
        return cls(PlatformId.generate(prefix="eng-recommendation").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EngineeringMetricId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> EngineeringMetricId:
        return cls(PlatformId.generate(prefix="eng-metric").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EngineeringEvidenceId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> EngineeringEvidenceId:
        return cls(PlatformId.generate(prefix="eng-evidence").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class EngineeringRelationshipId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> EngineeringRelationshipId:
        return cls(PlatformId.generate(prefix="eng-relationship").value)

    def __str__(self) -> str:
        return self.value
