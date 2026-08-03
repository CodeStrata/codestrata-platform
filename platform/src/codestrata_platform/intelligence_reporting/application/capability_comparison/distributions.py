"""Build CapabilityDistribution and AssessmentHeadDistribution from snapshots."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Sequence

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    AggregatedFindingFact,
)
from codestrata_platform.intelligence_reporting.domain.capability import (
    AssessmentHeadDistribution,
    CapabilityDistribution,
    RepositoryCapabilitySnapshot,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    ConfidenceLevel,
    CoverageStatus,
)


def build_capability_distribution(
    snapshots: Sequence[RepositoryCapabilitySnapshot],
) -> CapabilityDistribution:
    complete = partial = insufficient = unavailable = disabled = 0
    high = moderate = limited = unavailable_conf = 0
    missing = legacy = comparable = 0
    for item in snapshots:
        if item.coverage_status is CoverageStatus.COMPLETE:
            complete += 1
        elif item.coverage_status is CoverageStatus.PARTIAL:
            partial += 1
        elif item.coverage_status is CoverageStatus.INSUFFICIENT_EVIDENCE:
            insufficient += 1
        elif item.coverage_status is CoverageStatus.DISABLED:
            disabled += 1
        else:
            unavailable += 1
        if item.confidence_level is ConfidenceLevel.HIGH:
            high += 1
        elif item.confidence_level is ConfidenceLevel.MODERATE:
            moderate += 1
        elif item.confidence_level is ConfidenceLevel.LIMITED:
            limited += 1
        else:
            unavailable_conf += 1
        if item.legacy_limited:
            legacy += 1
        if item.comparable:
            comparable += 1
        if (
            item.activation_status is ActivationStatus.UNAVAILABLE
            and item.coverage_status is CoverageStatus.UNAVAILABLE
            and "missing" in " ".join(item.limitations)
        ):
            missing += 1
    return CapabilityDistribution(
        complete_count=complete,
        partial_count=partial,
        insufficient_evidence_count=insufficient,
        unavailable_count=unavailable,
        disabled_count=disabled,
        high_confidence_count=high,
        moderate_confidence_count=moderate,
        limited_confidence_count=limited,
        unavailable_confidence_count=unavailable_conf,
        missing_count=missing,
        legacy_limited_count=legacy,
        comparable_count=comparable,
    )


def build_severity_occurrence_distribution(
    findings: Sequence[AggregatedFindingFact],
    *,
    head_id: str,
    repository_ids: set[str],
) -> tuple[tuple[str, int], ...]:
    """Occurrence counts of calibrated severities for findings on this head."""

    counts: Counter[str] = Counter()
    for item in findings:
        if item.repository_id not in repository_ids:
            continue
        if item.assessment_head_id != head_id or item.unclassified:
            continue
        counts[item.severity.lower()] += 1
    return tuple(sorted((severity, count) for severity, count in counts.items()))


def build_severity_repository_presence(
    findings: Sequence[AggregatedFindingFact],
    *,
    head_id: str,
    repository_ids: set[str],
) -> dict[str, set[str]]:
    presence: dict[str, set[str]] = defaultdict(set)
    for item in findings:
        if item.repository_id not in repository_ids:
            continue
        if item.assessment_head_id != head_id or item.unclassified:
            continue
        presence[item.severity.lower()].add(item.repository_id)
    return {key: value for key, value in sorted(presence.items())}


def build_assessment_head_distribution(
    *,
    head_id: str,
    snapshots: Sequence[RepositoryCapabilitySnapshot],
    findings: Sequence[AggregatedFindingFact],
    limitations: Sequence[str] = (),
) -> AssessmentHeadDistribution:
    repo_ids = {item.repository_id for item in snapshots}
    activated = sum(
        1 for item in snapshots if item.activation_status is ActivationStatus.ACTIVATED
    )
    complete = sum(1 for item in snapshots if item.coverage_status is CoverageStatus.COMPLETE)
    partial = sum(1 for item in snapshots if item.coverage_status is CoverageStatus.PARTIAL)
    insufficient = sum(
        1
        for item in snapshots
        if item.coverage_status is CoverageStatus.INSUFFICIENT_EVIDENCE
    )
    unavailable = sum(
        1 for item in snapshots if item.coverage_status is CoverageStatus.UNAVAILABLE
    )
    disabled = sum(1 for item in snapshots if item.coverage_status is CoverageStatus.DISABLED)
    finding_total = sum(item.finding_count for item in snapshots)
    rec_total = sum(item.recommendation_count for item in snapshots)
    pa_total = sum(item.priority_action_count for item in snapshots)
    with_findings = sum(1 for item in snapshots if item.finding_count > 0)
    conf: Counter[str] = Counter(item.confidence_level.value for item in snapshots)
    severity = build_severity_occurrence_distribution(
        findings, head_id=head_id, repository_ids=repo_ids
    )
    return AssessmentHeadDistribution(
        assessment_head_id=head_id,
        repository_count=len(snapshots),
        activated_count=activated,
        complete_coverage_count=complete,
        partial_coverage_count=partial,
        insufficient_evidence_count=insufficient,
        unavailable_count=unavailable,
        disabled_count=disabled,
        finding_count=finding_total,
        recommendation_count=rec_total,
        priority_action_count=pa_total,
        repositories_with_findings_count=with_findings,
        severity_distribution=severity,
        confidence_distribution=tuple(sorted(conf.items())),
        limitations=tuple(sorted(set(limitations))),
    )
