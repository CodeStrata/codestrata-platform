"""Recommendation → Finding traceability helpers (Epic 2 Slice 2.3).

Keeps EvidenceRef out of recommendation identity. Primary finding selection
uses severity → confidence → deterministic ordering → finding ID.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from codestrata.domain.findings import Finding
from codestrata.domain.findings.enums import FindingSeverity
from codestrata.domain.recommendations.enums import RecommendationType
from codestrata.domain.recommendations.models import Recommendation
from codestrata.domain.rules.enums import RuleConfidence
from codestrata.domain.traceability import EvidenceCompleteness
from codestrata.domain.traceability.validators import merge_unique_sorted, normalize_limitations

_SEVERITY_RANK = {
    FindingSeverity.INFORMATIONAL: 0,
    FindingSeverity.LOW: 1,
    FindingSeverity.MEDIUM: 2,
    FindingSeverity.HIGH: 3,
    FindingSeverity.CRITICAL: 4,
}

_CONFIDENCE_RANK = {
    RuleConfidence.LOW: 0,
    RuleConfidence.MEDIUM: 1,
    RuleConfidence.HIGH: 2,
    RuleConfidence.CERTAIN: 3,
}


def select_primary_finding_id(
    findings: Sequence[Finding],
    *,
    candidate_ids: Sequence[str] | None = None,
) -> str | None:
    """Select primary finding: severity → confidence → rule_id → finding ID."""

    allowed = (
        {str(item) for item in candidate_ids}
        if candidate_ids is not None
        else None
    )
    candidates = [
        item
        for item in findings
        if allowed is None or item.id in allowed
    ]
    if not candidates:
        if candidate_ids:
            ordered = tuple(sorted({str(item) for item in candidate_ids if str(item).strip()}))
            return ordered[0] if ordered else None
        return None

    def sort_key(finding: Finding) -> tuple[object, ...]:
        confidence_raw = str(finding.metadata.get("confidence", "medium")).lower()
        try:
            confidence = RuleConfidence(confidence_raw)
        except ValueError:
            confidence = RuleConfidence.MEDIUM
        return (
            -_SEVERITY_RANK.get(finding.severity, 0),
            -_CONFIDENCE_RANK.get(confidence, 1),
            finding.rule_id,
            finding.id,
        )

    return sorted(candidates, key=sort_key)[0].id


def synthesize_recommendation_traceability(
    finding_ids: Sequence[str],
    *,
    findings: Sequence[Finding] = (),
    recommendation_type: RecommendationType | None = None,
    limitations: Sequence[str] = (),
    expected_finding_count: int | None = None,
) -> tuple[
    tuple[str, ...],
    str | None,
    RecommendationType,
    EvidenceCompleteness,
    tuple[str, ...],
]:
    """Normalize supporting finding IDs and derive primary / completeness."""

    supporting = tuple(sorted({str(item).strip() for item in finding_ids if str(item).strip()}))
    findings_by_id = {item.id: item for item in findings}
    known = tuple(item for item in supporting if item in findings_by_id)
    unknown = tuple(item for item in supporting if item not in findings_by_id)

    limits = list(normalize_limitations(limitations))
    if findings and unknown:
        limits.append("unknown_supporting_finding_ids")
        supporting = known

    primary = select_primary_finding_id(
        tuple(findings_by_id[item] for item in supporting if item in findings_by_id),
        candidate_ids=supporting,
    )
    if primary is None and supporting:
        primary = supporting[0]

    if recommendation_type is None:
        recommendation_type = (
            RecommendationType.FINDING_BACKED if supporting else RecommendationType.LEGACY
        )

    if not supporting:
        completeness = EvidenceCompleteness.UNAVAILABLE
        if recommendation_type is RecommendationType.LEGACY:
            completeness = EvidenceCompleteness.LEGACY
    elif expected_finding_count is not None and expected_finding_count > len(supporting):
        completeness = EvidenceCompleteness.PARTIAL
        limits.append("some_supporting_findings_unmapped")
    elif findings and unknown:
        completeness = EvidenceCompleteness.PARTIAL
    else:
        completeness = EvidenceCompleteness.COMPLETE

    return (
        supporting,
        primary,
        recommendation_type,
        completeness,
        tuple(sorted(set(limits))),
    )


def attach_recommendation_traceability(
    recommendation: Recommendation,
    *,
    findings: Sequence[Finding] = (),
    recommendation_type: RecommendationType | None = None,
    limitations: Sequence[str] = (),
) -> Recommendation:
    """Populate additive traceability fields without changing recommendation ID."""

    source_ids = recommendation.supporting_finding_ids or recommendation.related_finding_ids
    (
        supporting,
        primary,
        rec_type,
        completeness,
        limits,
    ) = synthesize_recommendation_traceability(
        source_ids,
        findings=findings,
        recommendation_type=recommendation_type or recommendation.recommendation_type,
        limitations=(*recommendation.limitations, *limitations),
    )
    return recommendation.model_copy(
        update={
            "related_finding_ids": supporting,
            "supporting_finding_ids": supporting,
            "primary_finding_id": primary,
            "recommendation_type": rec_type,
            "evidence_completeness": completeness,
            "limitations": limits,
        }
    )


def merge_recommendation_traceability(
    preferred: Recommendation,
    other: Recommendation,
    *,
    findings: Sequence[Finding] = (),
) -> Recommendation:
    """Union finding traceability from two recommendations that share identity.

    Does not alter ``preferred.id``. Dual-writes related/supporting finding IDs.
    """

    combined_ids = merge_unique_sorted(
        preferred.supporting_finding_ids or preferred.related_finding_ids,
        other.supporting_finding_ids or other.related_finding_ids,
    )
    (
        supporting,
        primary,
        _rec_type,
        completeness,
        limits,
    ) = synthesize_recommendation_traceability(
        combined_ids,
        findings=findings,
        recommendation_type=RecommendationType.MERGED,
        limitations=(*preferred.limitations, *other.limitations),
    )
    # Prefer COMPLETE when either side already had complete coverage of the union.
    if preferred.evidence_completeness is EvidenceCompleteness.COMPLETE and other.evidence_completeness is EvidenceCompleteness.COMPLETE:
        completeness = EvidenceCompleteness.COMPLETE
    return preferred.model_copy(
        update={
            "related_finding_ids": supporting,
            "supporting_finding_ids": supporting,
            "primary_finding_id": primary,
            "recommendation_type": RecommendationType.MERGED,
            "evidence_completeness": completeness,
            "limitations": limits,
        }
    )


def findings_lookup(findings: Sequence[Finding]) -> Mapping[str, Finding]:
    return {item.id: item for item in findings}
