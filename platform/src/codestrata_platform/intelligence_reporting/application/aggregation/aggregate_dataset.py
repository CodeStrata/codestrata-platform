"""Build CrossRepositoryAggregation from an IntelligenceDataset."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from codestrata_platform.intelligence_reporting.application.aggregation.denominators import (
    build_standard_denominators,
)
from codestrata_platform.intelligence_reporting.application.aggregation.diagnostics import (
    build_diagnostics,
)
from codestrata_platform.intelligence_reporting.application.aggregation.indexes import (
    assert_unique_repositories,
    build_assessment_index,
)
from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    AggregateCounts,
    AggregatedTechnologyFact,
    CrossRepositoryAggregation,
    IntelligenceAggregationPolicy,
    LegacyAssessmentPolicy,
    VisibilityAggregationScope,
)
from codestrata_platform.intelligence_reporting.application.aggregation.repository_projection import (
    RepositoryProjection,
    project_repository,
)
from codestrata_platform.intelligence_reporting.application.aggregation.validation import (
    validate_aggregation,
    validate_no_embedded_reports,
)
from codestrata_platform.intelligence_reporting.application.comparability import (
    evaluate_comparability,
)
from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentComparability,
    NormalizedAssessmentSnapshot,
)
from codestrata_platform.intelligence_reporting.application.errors import (
    AggregationInvariantError,
    AggregationVisibilityError,
)
from codestrata_platform.intelligence_reporting.application.normalization import (
    stable_canonical_report_digest,
)
from codestrata_platform.intelligence_reporting.application.ports import (
    CanonicalAssessmentReportSource,
)
from codestrata_platform.intelligence_reporting.domain.dataset import IntelligenceDataset
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    InclusionStatus,
    SourceType,
)
from codestrata_platform.intelligence_reporting.domain.repository_snapshot import (
    RepositoryPopulation,
)


def build_aggregation_id(
    *,
    dataset_id: str,
    policy_token: str,
    digests: Sequence[str],
    repository_ids: Sequence[str],
    assessment_run_ids: Sequence[str],
) -> str:
    material = json.dumps(
        {
            "dataset_id": dataset_id,
            "policy": policy_token,
            "digests": sorted(digests),
            "repository_ids": sorted(repository_ids),
            "assessment_run_ids": sorted(assessment_run_ids),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]
    return f"aggregation:{digest}"


def aggregate_intelligence_dataset(
    *,
    dataset: IntelligenceDataset,
    snapshots: Sequence[NormalizedAssessmentSnapshot],
    report_source: CanonicalAssessmentReportSource,
    policy: IntelligenceAggregationPolicy | None = None,
    comparability: AssessmentComparability | None = None,
) -> CrossRepositoryAggregation:
    """Aggregate included canonical assessments into factual cross-repository inputs.

    Does not create recurring-pattern conclusions, portfolio recommendations,
    or industry benchmarks.
    """

    active_policy = policy or IntelligenceAggregationPolicy()
    included_refs = [
        item
        for item in dataset.repository_assessments
        if item.inclusion_status is InclusionStatus.INCLUDED
    ]
    snapshot_by_repo = {
        item.repository_id: item
        for item in snapshots
        if item.inclusion_status is InclusionStatus.INCLUDED
    }
    for ref in included_refs:
        if ref.repository_id not in snapshot_by_repo:
            raise AggregationInvariantError(
                f"missing normalized snapshot for included repository {ref.repository_id}",
                reason_code="missing_snapshot",
            )

    _enforce_visibility(dataset, snapshots=list(snapshot_by_repo.values()), policy=active_policy)

    if comparability is None:
        comparability = evaluate_comparability(
            list(snapshot_by_repo.values()),
            policy=_compat_policy_shim(dataset),
        )
    comparable_ids = set(comparability.compatible_repository_ids)

    projections: list[RepositoryProjection] = []
    excluded_count = len(dataset.excluded_repositories)
    limitations: list[str] = list(active_policy.limitations)

    for ref in sorted(included_refs, key=lambda item: item.repository_id):
        snapshot = snapshot_by_repo[ref.repository_id]
        legacy = (
            snapshot.traceability_status in {"legacy", "incomplete"}
            or "included_with_legacy_limitations" in snapshot.limitations
            or snapshot.assessment_schema_version != "1.2"
        )
        if legacy and active_policy.legacy_assessment_policy is LegacyAssessmentPolicy.REJECT:
            raise AggregationInvariantError(
                f"legacy assessment rejected by policy: {snapshot.repository_id}",
                reason_code="legacy_rejected",
            )
        if legacy and active_policy.legacy_assessment_policy is LegacyAssessmentPolicy.EXCLUDE:
            excluded_count += 1
            limitations.append(f"legacy_excluded:{snapshot.repository_id}")
            continue

        document = _load_and_verify(snapshot, report_source=report_source)
        comparable = (
            snapshot.repository_id in comparable_ids
            and snapshot.traceability_status == "complete"
            and not legacy
        )
        projection = project_repository(
            snapshot=snapshot,
            document=document,
            comparable=comparable,
            legacy_limited_marker=legacy
            and active_policy.legacy_assessment_policy is LegacyAssessmentPolicy.LIMITED,
        )
        projections.append(projection)

    repositories = tuple(item.repository for item in projections)
    assert_unique_repositories(repositories)

    technology_facts = _sorted_tech([f for p in projections for f in p.technology_facts])
    finding_facts = tuple(
        sorted(
            (f for p in projections for f in p.finding_facts),
            key=lambda row: (row.repository_id, row.finding_id),
        )
    )
    recommendation_facts = tuple(
        sorted(
            (f for p in projections for f in p.recommendation_facts),
            key=lambda row: (row.repository_id, row.recommendation_id),
        )
    )
    priority_action_facts = tuple(
        sorted(
            (f for p in projections for f in p.priority_action_facts),
            key=lambda row: (row.repository_id, row.priority_action_id),
        )
    )
    roadmap_facts = tuple(
        sorted(
            (f for p in projections for f in p.roadmap_facts),
            key=lambda row: (row.repository_id, row.initiative_id),
        )
    )
    correlation_facts = tuple(
        sorted(
            (f for p in projections for f in p.correlation_facts),
            key=lambda row: (row.repository_id, row.correlation_id),
        )
    )
    head_facts = tuple(
        sorted(
            (f for p in projections for f in p.assessment_head_facts),
            key=lambda row: (row.repository_id, row.assessment_head_id),
        )
    )
    coverage_facts = tuple(
        sorted(
            (f for p in projections for f in p.coverage_facts),
            key=lambda row: (row.repository_id, row.assessment_head_id),
        )
    )
    confidence_facts = tuple(
        sorted(
            (f for p in projections for f in p.confidence_facts),
            key=lambda row: (row.repository_id, row.assessment_head_id),
        )
    )
    evidence_refs = tuple(
        sorted(
            (f for p in projections for f in p.evidence_refs),
            key=lambda row: (row.repository_id, row.entity_id),
        )
    )

    report_refs = {
        item.repository.repository_id: item.repository.canonical_report_reference or ""
        for item in projections
    }
    assessment_index = build_assessment_index(
        finding_facts=finding_facts,
        recommendation_facts=recommendation_facts,
        priority_action_facts=priority_action_facts,
        roadmap_facts=roadmap_facts,
        correlation_facts=correlation_facts,
        technology_facts=technology_facts,
        evidence_refs=evidence_refs,
        canonical_report_references=report_refs,
    )

    denominators = build_standard_denominators(repositories, policy=active_policy)
    population = _build_population(repositories, technology_facts=technology_facts)

    tech_repos = {fact.repository_id for fact in technology_facts}
    counts = AggregateCounts(
        repository_count=len(repositories),
        technology_occurrence_count=len(technology_facts),
        technology_repository_presence_count=len(tech_repos),
        finding_count=len(finding_facts),
        recommendation_count=len(recommendation_facts),
        priority_action_count=len(priority_action_facts),
        roadmap_initiative_count=len(roadmap_facts),
        correlation_count=len(correlation_facts),
    )

    validate_aggregation(
        dataset=dataset,
        repositories=repositories,
        finding_facts=finding_facts,
        recommendation_facts=recommendation_facts,
        priority_action_facts=priority_action_facts,
        roadmap_facts=roadmap_facts,
        correlation_facts=correlation_facts,
        denominators=denominators,
        assessment_index_size=len(assessment_index),
    )

    diagnostics = build_diagnostics(
        repositories=repositories,
        excluded_repository_count=excluded_count,
        technology_fact_count=len(technology_facts),
        finding_fact_count=len(finding_facts),
        recommendation_fact_count=len(recommendation_facts),
        priority_action_fact_count=len(priority_action_facts),
        roadmap_fact_count=len(roadmap_facts),
        correlation_fact_count=len(correlation_facts),
        unresolved_reference_count=0,
        duplicate_reference_count=0,
        denominators=denominators,
        limitations=limitations,
    )

    aggregation_id = build_aggregation_id(
        dataset_id=dataset.dataset_id.value,
        policy_token=active_policy.policy_token,
        digests=[item.canonical_report_digest for item in repositories],
        repository_ids=[item.repository_id for item in repositories],
        assessment_run_ids=[item.assessment_run_id for item in repositories],
    )

    aggregation = CrossRepositoryAggregation(
        aggregation_id=aggregation_id,
        dataset_id=dataset.dataset_id.value,
        policy_id=active_policy.policy_id,
        policy_version=active_policy.policy_version,
        repository_population=population,
        repository_index=repositories,
        assessment_index=assessment_index,
        technology_facts=technology_facts,
        assessment_head_facts=head_facts,
        finding_facts=finding_facts,
        recommendation_facts=recommendation_facts,
        priority_action_facts=priority_action_facts,
        roadmap_facts=roadmap_facts,
        correlation_facts=correlation_facts,
        coverage_facts=coverage_facts,
        confidence_facts=confidence_facts,
        denominators=denominators,
        aggregate_counts=counts,
        comparability=comparability,
        comparability_status=comparability.status,
        limitations=tuple(sorted(set(limitations))),
        diagnostics=diagnostics,
    )
    validate_no_embedded_reports(aggregation)
    return aggregation


def _load_and_verify(
    snapshot: NormalizedAssessmentSnapshot,
    *,
    report_source: CanonicalAssessmentReportSource,
) -> Mapping[str, Any]:
    reference = snapshot.canonical_report_reference
    if not reference:
        raise AggregationInvariantError(
            f"missing canonical_report_reference for {snapshot.repository_id}",
            reason_code="missing_report_reference",
        )
    document = report_source.load(reference)
    digest = stable_canonical_report_digest(document)
    if digest != snapshot.canonical_report_digest:
        raise AggregationInvariantError(
            f"canonical report digest mismatch for {snapshot.repository_id}",
            reason_code="digest_mismatch",
        )
    return document


def _enforce_visibility(
    dataset: IntelligenceDataset,
    *,
    snapshots: Sequence[NormalizedAssessmentSnapshot],
    policy: IntelligenceAggregationPolicy,
) -> None:
    visibilities = {item.visibility for item in snapshots}
    if policy.visibility_policy is VisibilityAggregationScope.PUBLIC_OSS:
        if any(item is not DataVisibility.PUBLIC for item in visibilities):
            raise AggregationVisibilityError(
                "public OSS aggregation scope rejects non-public repositories",
                reason_code="visibility_policy_violation",
            )
        if any(item.source_type is not SourceType.PUBLIC_OSS for item in snapshots):
            raise AggregationVisibilityError(
                "public OSS aggregation scope requires public_oss source_type",
                reason_code="visibility_policy_violation",
            )
    if policy.visibility_policy is VisibilityAggregationScope.CUSTOMER_PRIVATE:
        if any(item is DataVisibility.PUBLIC for item in visibilities):
            # Private scope may still include anonymized; public is unexpected.
            pass
    _ = dataset


def _build_population(
    repositories: Sequence[object],
    *,
    technology_facts: Sequence[AggregatedTechnologyFact],
) -> RepositoryPopulation:
    source_counts: dict[str, int] = {}
    schema_counts: dict[str, int] = {}
    head_availability: dict[str, int] = {}
    language_counts: dict[str, int] = {}
    ecosystem_counts: dict[str, int] = {}
    visibility_safe: dict[str, int] = {}
    included_ids: list[str] = []

    for item in repositories:
        included_ids.append(item.repository_id)  # type: ignore[attr-defined]
        source_counts[item.source_type.value] = (  # type: ignore[attr-defined]
            source_counts.get(item.source_type.value, 0) + 1  # type: ignore[attr-defined]
        )
        schema_counts[item.assessment_schema_version] = (  # type: ignore[attr-defined]
            schema_counts.get(item.assessment_schema_version, 0) + 1  # type: ignore[attr-defined]
        )
        visibility_safe[item.visibility.value] = (  # type: ignore[attr-defined]
            visibility_safe.get(item.visibility.value, 0) + 1  # type: ignore[attr-defined]
        )
        for head in set(item.enabled_heads) | set(item.disabled_heads) | set(  # type: ignore[attr-defined]
            item.unavailable_heads  # type: ignore[attr-defined]
        ):
            head_availability[head] = head_availability.get(head, 0) + 1

    # Language/ecosystem presence from technology facts (distinct repos per name/category).
    lang_repos: dict[str, set[str]] = {}
    eco_repos: dict[str, set[str]] = {}
    for fact in technology_facts:
        category = fact.category.lower()
        if category in {"language", "runtime"}:
            lang_repos.setdefault(fact.normalized_name, set()).add(fact.repository_id)
        else:
            eco_repos.setdefault(fact.normalized_name, set()).add(fact.repository_id)
    language_counts = {name: len(repos) for name, repos in sorted(lang_repos.items())}
    ecosystem_counts = {name: len(repos) for name, repos in sorted(eco_repos.items())}

    limitations = []
    if not language_counts:
        limitations.append("language_presence_unavailable")
    if visibility_safe:
        # Visibility counts kept only as limitation note for public-safe consumers.
        limitations.append("visibility_counts_internal_only")

    return RepositoryPopulation(
        repository_count=len(included_ids),
        source_type_counts=source_counts,
        language_presence_counts=language_counts,
        ecosystem_presence_counts=ecosystem_counts,
        size_tier_counts={},
        assessment_head_availability_counts=head_availability,
        assessment_schema_version_counts=schema_counts,
        included_repository_ids=tuple(sorted(included_ids)),
        limitations=tuple(limitations),
    )


def _sorted_tech(
    facts: Sequence[AggregatedTechnologyFact],
) -> tuple[AggregatedTechnologyFact, ...]:
    return tuple(
        sorted(
            facts,
            key=lambda row: (
                row.normalized_name,
                row.repository_id,
                row.assessment_id,
                row.version or "",
            ),
        )
    )


def _compat_policy_shim(dataset: IntelligenceDataset):
    from codestrata_platform.intelligence_reporting.application.contracts import (
        IntelligenceDatasetSelectionPolicy,
    )

    return IntelligenceDatasetSelectionPolicy(
        policy_id="intelligence-dataset-selection",
        policy_version=dataset.selection_policy_version.split(":")[-1]
        if ":" in dataset.selection_policy_version
        else "v1",
    )
