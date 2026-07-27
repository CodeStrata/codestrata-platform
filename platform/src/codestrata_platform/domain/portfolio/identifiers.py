"""Portfolio identity and projection-key value objects."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.domain.shared.ids import PlatformId


@dataclass(frozen=True, slots=True)
class PortfolioId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> PortfolioId:
        return cls(PlatformId.generate(prefix="portfolio").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PortfolioMembershipId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> PortfolioMembershipId:
        return cls(PlatformId.generate(prefix="pmem").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PortfolioSnapshotId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def generate(cls) -> PortfolioSnapshotId:
        return cls(PlatformId.generate(prefix="psnap").value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PortfolioSnapshotVersion:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise InvalidValueError(
                "Portfolio snapshot version must be >= 1",
                reason_code="invalid_portfolio_snapshot_version",
            )


@dataclass(frozen=True, slots=True)
class PortfolioPolicyVersion:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "Portfolio policy version must be non-blank",
                reason_code="empty_portfolio_policy_version",
            )
        object.__setattr__(self, "value", compact[:64])


@dataclass(frozen=True, slots=True)
class PortfolioProjectionKey:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact or len(compact) > 128:
            raise InvalidValueError(
                "Portfolio projection key is invalid",
                reason_code="invalid_portfolio_projection_key",
            )
        object.__setattr__(self, "value", compact)

    @classmethod
    def from_parts(
        cls,
        *,
        portfolio_id: str,
        membership_repository_ids: tuple[str, ...],
        selected_snapshots: tuple[tuple[str, int], ...],
        selected_graphs: tuple[tuple[str, int], ...],
        aggregation_policy_version: str,
        portfolio_schema_version: str,
    ) -> PortfolioProjectionKey:
        membership = ",".join(sorted(item.strip() for item in membership_repository_ids))
        snaps = ",".join(
            f"{sid}:{ver}" for sid, ver in sorted(selected_snapshots, key=lambda item: item[0])
        )
        graphs = ",".join(
            f"{gid}:{ver}" for gid, ver in sorted(selected_graphs, key=lambda item: item[0])
        )
        digest = hashlib.sha256(
            "|".join(
                [
                    portfolio_id.strip(),
                    membership,
                    snaps,
                    graphs,
                    aggregation_policy_version.strip(),
                    portfolio_schema_version.strip(),
                ]
            ).encode("utf-8")
        ).hexdigest()
        return cls(digest)


@dataclass(frozen=True, slots=True)
class PortfolioTechnologyId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", PlatformId(self.value).value)

    @classmethod
    def from_canonical(
        cls,
        *,
        portfolio_snapshot_id: str,
        canonical_key: str,
    ) -> PortfolioTechnologyId:
        token = hashlib.sha256(
            f"{portfolio_snapshot_id}|{canonical_key}".encode()
        ).hexdigest()[:32]
        return cls(f"ptech:{token}")


@dataclass(frozen=True, slots=True)
class PortfolioName:
    value: str

    def __post_init__(self) -> None:
        compact = self.value.strip()
        if not compact:
            raise InvalidValueError(
                "Portfolio name must be non-blank",
                reason_code="empty_portfolio_name",
            )
        if len(compact) > 256:
            raise InvalidValueError(
                "Portfolio name exceeds maximum length",
                reason_code="portfolio_name_too_long",
            )
        object.__setattr__(self, "value", compact)


@dataclass(frozen=True, slots=True)
class PortfolioDescription:
    value: str | None

    def __post_init__(self) -> None:
        if self.value is None:
            return
        compact = self.value.strip()
        if len(compact) > 4000:
            raise InvalidValueError(
                "Portfolio description exceeds maximum length",
                reason_code="portfolio_description_too_long",
            )
        object.__setattr__(self, "value", compact or None)
