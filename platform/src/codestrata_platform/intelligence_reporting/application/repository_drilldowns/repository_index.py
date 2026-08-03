"""Select included repositories and resolve display names / visibility."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from codestrata_platform.domain.errors import InvalidValueError
from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    AggregatedRepositoryRecord,
    CrossRepositoryAggregation,
)
from codestrata_platform.intelligence_reporting.application.repository_drilldowns.policy import (
    AnonymizationPolicy,
    LegacyDrilldownPolicy,
    RepositoryDrilldownPolicy,
)
from codestrata_platform.intelligence_reporting.domain.dataset import (
    IntelligenceDataset,
    RepositoryAssessmentReference,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    InclusionStatus,
    ReportScope,
)


@dataclass(frozen=True, slots=True)
class SelectedRepository:
    record: AggregatedRepositoryRecord
    reference: RepositoryAssessmentReference
    display_name: str
    legacy_limited: bool


def select_included_repositories(
    dataset: IntelligenceDataset,
    aggregation: CrossRepositoryAggregation,
    *,
    policy: RepositoryDrilldownPolicy,
    report_scope: ReportScope,
) -> tuple[SelectedRepository, ...]:
    included = set(dataset.included_repository_ids)
    refs = {
        item.repository_id: item
        for item in dataset.repository_assessments
        if item.repository_id in included
        and item.inclusion_status is InclusionStatus.INCLUDED
    }
    index = {item.repository_id: item for item in aggregation.repository_index}
    selected: list[SelectedRepository] = []
    seen: set[str] = set()
    for repository_id in sorted(included):
        if repository_id in seen:
            raise InvalidValueError(
                f"duplicate included repository: {repository_id}",
                reason_code="duplicate_included_repository",
            )
        seen.add(repository_id)
        ref = refs.get(repository_id)
        record = index.get(repository_id)
        if ref is None or record is None:
            raise InvalidValueError(
                f"included repository missing assessment index: {repository_id}",
                reason_code="missing_repository_index",
            )
        legacy = bool(record.legacy_or_incomplete)
        if legacy and policy.legacy_policy is LegacyDrilldownPolicy.EXCLUDE:
            continue
        if legacy and policy.legacy_policy is LegacyDrilldownPolicy.REJECT:
            raise InvalidValueError(
                f"legacy repository rejected by drilldown policy: {repository_id}",
                reason_code="legacy_repository_rejected",
            )
        display = resolve_display_name(
            ref,
            report_scope=report_scope,
            policy=policy,
        )
        selected.append(
            SelectedRepository(
                record=record,
                reference=ref,
                display_name=display,
                legacy_limited=legacy,
            )
        )
    return tuple(selected)


def resolve_display_name(
    ref: RepositoryAssessmentReference,
    *,
    report_scope: ReportScope,
    policy: RepositoryDrilldownPolicy,
) -> str:
    """Resolve a visibility-safe display name. Never derive visibility from URL."""

    provided = (ref.display_name or "").strip()
    alias = _stable_alias(ref.repository_id)

    if ref.visibility is DataVisibility.ANONYMIZED:
        return alias
    if report_scope is ReportScope.PUBLIC_OSS_DATASET:
        if ref.visibility is DataVisibility.PUBLIC:
            if ref.source_reference_publication_permitted and provided:
                return provided
            return alias
        # Private/internal must not leak into public-scope display names.
        return alias
    if ref.visibility in {DataVisibility.CUSTOMER_PRIVATE, DataVisibility.INTERNAL}:
        if policy.anonymization_policy is AnonymizationPolicy.USE_STABLE_ALIAS:
            return alias
        return provided or alias
    if provided:
        return provided
    return alias


def _stable_alias(repository_id: str) -> str:
    digest = hashlib.sha256(repository_id.encode("utf-8")).hexdigest()[:8]
    return f"repository-{digest}"
