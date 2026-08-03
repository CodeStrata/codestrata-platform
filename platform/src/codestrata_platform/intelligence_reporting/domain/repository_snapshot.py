"""Repository population summary model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.domain._safety import (
    optional_sorted_ids,
    unique_sorted_ids,
)


@dataclass(frozen=True, slots=True)
class RepositoryPopulation:
    repository_count: int = 0
    source_type_counts: Mapping[str, int] = field(default_factory=dict)
    language_presence_counts: Mapping[str, int] = field(default_factory=dict)
    ecosystem_presence_counts: Mapping[str, int] = field(default_factory=dict)
    size_tier_counts: Mapping[str, int] = field(default_factory=dict)
    assessment_head_availability_counts: Mapping[str, int] = field(default_factory=dict)
    assessment_schema_version_counts: Mapping[str, int] = field(default_factory=dict)
    included_repository_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.repository_count < 0:
            raise InvalidValueError(
                "repository_count must be non-negative",
                reason_code="negative_repository_count",
            )
        ids = unique_sorted_ids(self.included_repository_ids, label="included_repository_id")
        if ids and len(ids) != self.repository_count:
            raise InvalidValueError(
                "included_repository_ids length must equal repository_count",
                reason_code="population_count_mismatch",
            )
        object.__setattr__(self, "included_repository_ids", ids)
        object.__setattr__(
            self, "limitations", optional_sorted_ids(self.limitations, label="limitation")
        )
        for attr in (
            "source_type_counts",
            "language_presence_counts",
            "ecosystem_presence_counts",
            "size_tier_counts",
            "assessment_head_availability_counts",
            "assessment_schema_version_counts",
        ):
            raw = getattr(self, attr)
            object.__setattr__(
                self,
                attr,
                dict(sorted((str(k), int(v)) for k, v in dict(raw).items())),
            )
