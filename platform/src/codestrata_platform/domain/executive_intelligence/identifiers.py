"""Executive & CTO Intelligence identity value objects."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.shared.ids import PlatformId


@dataclass(frozen=True, slots=True)
class ExecutiveIntelligenceId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> ExecutiveIntelligenceId:
        return cls(PlatformId.generate(prefix="exec-intel").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ExecutiveIntelligenceVersion:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise InvalidValueError(
                "Executive intelligence version must be >= 1",
                reason_code="invalid_executive_intelligence_version",
            )


@dataclass(frozen=True, slots=True)
class ExecutivePolicyVersion:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "Executive policy version must be non-blank",
                reason_code="empty_executive_policy_version",
            )
        object.__setattr__(self, "value", compact[:64])


@dataclass(frozen=True, slots=True)
class ExecutiveProjectionKey:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or len(compact) > 128:
            raise InvalidValueError(
                "Executive projection key is invalid",
                reason_code="invalid_executive_projection_key",
            )
        object.__setattr__(self, "value", compact)

    @classmethod
    def from_parts(
        cls,
        *,
        organization_id: str,
        workspace_id: str,
        portfolio_id: str,
        portfolio_snapshot_id: str,
        portfolio_snapshot_version: int,
        policy_version: str,
        schema_version: str,
    ) -> ExecutiveProjectionKey:
        digest = hashlib.sha256(
            "|".join(
                [
                    organization_id.strip(),
                    workspace_id.strip(),
                    portfolio_id.strip(),
                    portfolio_snapshot_id.strip(),
                    str(portfolio_snapshot_version),
                    policy_version.strip(),
                    schema_version.strip(),
                ]
            ).encode("utf-8")
        ).hexdigest()
        return cls(digest)


@dataclass(frozen=True, slots=True)
class ExecutiveMetricId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "Executive metric id must be non-blank",
                reason_code="empty_executive_metric_id",
            )
        object.__setattr__(self, "value", compact[:128])

    @classmethod
    def for_metric(cls, snapshot_id: str, metric_key: str) -> ExecutiveMetricId:
        token = hashlib.sha256(f"{snapshot_id}|{metric_key}".encode()).hexdigest()[:32]
        return cls(f"exec-metric:{token}")


@dataclass(frozen=True, slots=True)
class ExecutiveFindingId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "Executive finding id must be non-blank",
                reason_code="empty_executive_finding_id",
            )
        object.__setattr__(self, "value", compact[:128])

    @classmethod
    def for_finding(cls, snapshot_id: str, finding_key: str) -> ExecutiveFindingId:
        token = hashlib.sha256(f"{snapshot_id}|{finding_key}".encode()).hexdigest()[:32]
        return cls(f"exec-finding:{token}")


@dataclass(frozen=True, slots=True)
class ExecutiveRecommendationId:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "Executive recommendation id must be non-blank",
                reason_code="empty_executive_recommendation_id",
            )
        object.__setattr__(self, "value", compact[:128])

    @classmethod
    def for_recommendation(
        cls,
        snapshot_id: str,
        recommendation_key: str,
    ) -> ExecutiveRecommendationId:
        token = hashlib.sha256(
            f"{snapshot_id}|{recommendation_key}".encode()
        ).hexdigest()[:32]
        return cls(f"exec-rec:{token}")
