"""Comparability and schema/methodology inputs for report confidence."""

from __future__ import annotations

from dataclasses import dataclass

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    CrossRepositoryAggregation,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ComparabilityStatus,
    InclusionStatus,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.report import (
    EngineeringIntelligenceReport,
)


@dataclass(frozen=True, slots=True)
class ComparabilitySummary:
    included_repository_count: int
    comparable_repository_count: int
    canonical_repository_count: int
    legacy_repository_count: int
    schema_compatibility: ComparabilityStatus
    methodology_compatibility: ComparabilityStatus
    schema_versions: tuple[str, ...]
    methodology_versions: tuple[str, ...]
    missing_revision_repository_ids: tuple[str, ...]
    fixture_repository_ids: tuple[str, ...]
    excluded_repository_count: int


def summarize_comparability(
    report: EngineeringIntelligenceReport,
    aggregation: CrossRepositoryAggregation,
) -> ComparabilitySummary:
    included = set(report.dataset.included_repository_ids)
    index = {item.repository_id: item for item in aggregation.repository_index}

    comparable_ids: set[str] = set()
    canonical = 0
    legacy = 0
    schemas: set[str] = set()
    methodologies: set[str] = set()
    missing_rev: list[str] = []
    fixtures: list[str] = []

    for ref in report.dataset.repository_assessments:
        if ref.repository_id not in included:
            continue
        row = index.get(ref.repository_id)
        if row is None:
            continue
        schemas.add(row.assessment_schema_version)
        # Methodology version is not always present on index; use schema as proxy
        # when methodology is absent (explicit non-inference beyond structured fields).
        if getattr(row, "methodology_version", None):
            methodologies.add(str(row.methodology_version))
        if row.comparable:
            comparable_ids.add(ref.repository_id)
        if row.legacy_or_incomplete:
            legacy += 1
        else:
            canonical += 1
        pinned = (ref.pinned_revision or "").strip()
        if not pinned and ref.source_type in {
            SourceType.PUBLIC_OSS,
            SourceType.REMOTE,
        }:
            missing_rev.append(ref.repository_id)
        if ref.source_type is SourceType.FIXTURE or (
            ref.source_type is SourceType.INTERNAL_VALIDATION
            and "fixture" in " ".join(ref.limitations).lower()
        ):
            fixtures.append(ref.repository_id)
        # Controlled fixtures may also be marked via source_type FIXTURE only.

    excluded = sum(
        1
        for ref in report.dataset.repository_assessments
        if ref.inclusion_status is not InclusionStatus.INCLUDED
    )

    schema_compat = _compatibility_from_versions(schemas, aggregation.comparability_status)
    method_compat = (
        _compatibility_from_versions(methodologies, ComparabilityStatus.COMPARABLE)
        if methodologies
        else ComparabilityStatus.UNKNOWN
    )
    # Prefer aggregation-level comparability when available.
    if aggregation.comparability_status in {
        ComparabilityStatus.COMPARABLE,
        ComparabilityStatus.PARTIALLY_COMPARABLE,
        ComparabilityStatus.NOT_COMPARABLE,
    }:
        if len(schemas) > 1 and schema_compat is ComparabilityStatus.COMPARABLE:
            schema_compat = ComparabilityStatus.PARTIALLY_COMPARABLE
        if aggregation.comparability_status is ComparabilityStatus.NOT_COMPARABLE:
            schema_compat = ComparabilityStatus.NOT_COMPARABLE
        elif (
            aggregation.comparability_status is ComparabilityStatus.PARTIALLY_COMPARABLE
            and schema_compat is ComparabilityStatus.COMPARABLE
        ):
            schema_compat = ComparabilityStatus.PARTIALLY_COMPARABLE

    return ComparabilitySummary(
        included_repository_count=len(included),
        comparable_repository_count=len(comparable_ids),
        canonical_repository_count=canonical,
        legacy_repository_count=legacy,
        schema_compatibility=schema_compat,
        methodology_compatibility=method_compat,
        schema_versions=tuple(sorted(schemas)),
        methodology_versions=tuple(sorted(methodologies)),
        missing_revision_repository_ids=tuple(sorted(set(missing_rev))),
        fixture_repository_ids=tuple(sorted(set(fixtures))),
        excluded_repository_count=excluded,
    )


def _compatibility_from_versions(
    versions: set[str],
    fallback: ComparabilityStatus,
) -> ComparabilityStatus:
    if not versions:
        return ComparabilityStatus.UNAVAILABLE
    if len(versions) == 1:
        return ComparabilityStatus.COMPARABLE
    return ComparabilityStatus.PARTIALLY_COMPARABLE if fallback != ComparabilityStatus.NOT_COMPARABLE else fallback
