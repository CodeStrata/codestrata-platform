"""Project one repository assessment into aggregation facts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from codestrata_platform.intelligence_reporting.application.aggregation.models import (
    AggregatedAssessmentHeadFact,
    AggregatedConfidenceFact,
    AggregatedCorrelationFact,
    AggregatedCoverageFact,
    AggregatedEntityRef,
    AggregatedFindingFact,
    AggregatedPriorityActionFact,
    AggregatedRecommendationFact,
    AggregatedRepositoryRecord,
    AggregatedRoadmapFact,
    AggregatedTechnologyFact,
)
from codestrata_platform.intelligence_reporting.application.contracts import (
    NormalizedAssessmentSnapshot,
)
from codestrata_platform.intelligence_reporting.application.errors import (
    AggregationUnresolvedReferenceError,
)
from codestrata_platform.intelligence_reporting.application.normalization import (
    CANONICAL_ASSESSMENT_HEADS,
    extract_assessment_mapping,
)
from codestrata_platform.intelligence_reporting.domain._safety import reject_unsafe_text
from codestrata_platform.intelligence_reporting.domain.enums import (
    ActivationStatus,
    ConfidenceLevel,
    CoverageStatus,
    VersionState,
)

_CATEGORY_TO_HEAD: dict[str, str] = {
    "security": "security_intelligence",
    "dependency": "dependency_intelligence",
    "technical_debt": "technical_debt_intelligence",
    "maintainability": "technical_debt_intelligence",
    "architecture": "architecture_intelligence",
    "cloud": "cloud_readiness",
    "cloud_readiness": "cloud_readiness",
    "ai_readiness": "ai_readiness",
    "modernization": "modernization_assessment",
    "technology": "technology_inventory",
    "testing": "technical_debt_intelligence",
}

_RULE_PREFIX_TO_HEAD: tuple[tuple[str, str], ...] = (
    ("technical_debt.", "technical_debt_intelligence"),
    ("ai_readiness.", "ai_readiness"),
    ("ai-readiness.", "ai_readiness"),
    ("architecture.", "architecture_intelligence"),
    ("dependency.", "dependency_intelligence"),
    ("security.", "security_intelligence"),
    ("cloud.", "cloud_readiness"),
    ("modernization.", "modernization_assessment"),
)

_SEVERITY_RANK = {
    "informational": 0,
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


@dataclass(frozen=True, slots=True)
class RepositoryProjection:
    repository: AggregatedRepositoryRecord
    evidence_refs: tuple[AggregatedEntityRef, ...]
    technology_facts: tuple[AggregatedTechnologyFact, ...]
    assessment_head_facts: tuple[AggregatedAssessmentHeadFact, ...]
    finding_facts: tuple[AggregatedFindingFact, ...]
    recommendation_facts: tuple[AggregatedRecommendationFact, ...]
    priority_action_facts: tuple[AggregatedPriorityActionFact, ...]
    roadmap_facts: tuple[AggregatedRoadmapFact, ...]
    correlation_facts: tuple[AggregatedCorrelationFact, ...]
    coverage_facts: tuple[AggregatedCoverageFact, ...]
    confidence_facts: tuple[AggregatedConfidenceFact, ...]


def project_repository(
    *,
    snapshot: NormalizedAssessmentSnapshot,
    document: Mapping[str, Any],
    comparable: bool,
    legacy_limited_marker: bool,
) -> RepositoryProjection:
    assessment = extract_assessment_mapping(document)
    report_ref = snapshot.canonical_report_reference
    limitations = list(snapshot.limitations)
    if legacy_limited_marker:
        limitations.append("legacy_limited")

    evidence_ids = _collect_ids(assessment.get("evidence"), ("evidence_id", "id"))
    finding_ids = _collect_ids(assessment.get("findings"), ("id", "finding_id"))
    recommendation_ids = _collect_ids(
        assessment.get("deterministic_recommendations") or assessment.get("recommendations"),
        ("id", "recommendation_id"),
    )
    action_ids = _collect_ids(assessment.get("priority_actions"), ("action_id", "id"))

    evidence_refs = tuple(
        AggregatedEntityRef(
            repository_id=snapshot.repository_id,
            assessment_id=snapshot.assessment_id,
            entity_type="evidence",
            entity_id=eid,
            canonical_report_reference=report_ref,
        )
        for eid in sorted(evidence_ids)
    )

    finding_facts = _project_findings(
        assessment=assessment,
        snapshot=snapshot,
        evidence_ids=evidence_ids,
        limitations=limitations,
    )
    recommendation_facts = _project_recommendations(
        assessment=assessment,
        snapshot=snapshot,
        finding_ids=finding_ids,
        limitations=limitations,
    )
    priority_action_facts = _project_priority_actions(
        assessment=assessment,
        snapshot=snapshot,
        recommendation_ids=recommendation_ids,
        finding_ids=finding_ids,
        limitations=limitations,
    )
    roadmap_facts = _project_roadmap(
        assessment=assessment,
        snapshot=snapshot,
        action_ids=action_ids,
        recommendation_ids=recommendation_ids,
        finding_ids=finding_ids,
        limitations=limitations,
    )
    correlation_facts = _project_correlations(
        assessment=assessment,
        snapshot=snapshot,
        finding_ids=finding_ids,
        limitations=limitations,
    )
    technology_facts = _project_technologies(
        assessment=assessment,
        snapshot=snapshot,
        limitations=limitations,
    )
    coverage_facts, confidence_facts = _project_coverage_confidence(
        snapshot=snapshot,
        limitations=limitations,
    )
    head_facts = _project_head_facts(
        snapshot=snapshot,
        finding_facts=finding_facts,
        recommendation_facts=recommendation_facts,
        priority_action_facts=priority_action_facts,
        limitations=limitations,
    )

    repository = AggregatedRepositoryRecord(
        repository_id=snapshot.repository_id,
        assessment_id=snapshot.assessment_id,
        assessment_run_id=snapshot.assessment_run_id,
        canonical_report_digest=snapshot.canonical_report_digest,
        source_type=snapshot.source_type,
        visibility=snapshot.visibility,
        assessment_schema_version=snapshot.assessment_schema_version,
        enabled_heads=snapshot.enabled_assessment_heads,
        disabled_heads=snapshot.disabled_assessment_heads,
        unavailable_heads=snapshot.unavailable_assessment_heads,
        missing_heads=snapshot.missing_assessment_heads,
        legacy_or_incomplete=legacy_limited_marker
        or snapshot.traceability_status in {"legacy", "incomplete"},
        comparable=comparable,
        canonical_report_reference=report_ref,
        limitations=tuple(sorted(set(limitations))),
    )
    return RepositoryProjection(
        repository=repository,
        evidence_refs=evidence_refs,
        technology_facts=technology_facts,
        assessment_head_facts=head_facts,
        finding_facts=finding_facts,
        recommendation_facts=recommendation_facts,
        priority_action_facts=priority_action_facts,
        roadmap_facts=roadmap_facts,
        correlation_facts=correlation_facts,
        coverage_facts=coverage_facts,
        confidence_facts=confidence_facts,
    )


def classify_assessment_head(*, category: str | None, rule_id: str | None) -> str | None:
    normalized = (category or "").strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in _CATEGORY_TO_HEAD:
        return _CATEGORY_TO_HEAD[normalized]
    if normalized in CANONICAL_ASSESSMENT_HEADS:
        return normalized
    rid = (rule_id or "").strip().lower()
    for prefix, head in _RULE_PREFIX_TO_HEAD:
        if rid.startswith(prefix):
            return head
    return None


def _project_findings(
    *,
    assessment: Mapping[str, Any],
    snapshot: NormalizedAssessmentSnapshot,
    evidence_ids: set[str],
    limitations: Sequence[str],
) -> tuple[AggregatedFindingFact, ...]:
    rows = assessment.get("findings")
    if not isinstance(rows, list):
        return ()
    facts: list[AggregatedFindingFact] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        finding_id = str(item.get("id") or item.get("finding_id") or "").strip()
        if not finding_id:
            continue
        reject_unsafe_text(finding_id, label="finding_id")
        primary = str(item.get("primary_evidence_id") or "").strip() or None
        if primary and primary not in evidence_ids:
            raise AggregationUnresolvedReferenceError(
                f"finding {finding_id} references unknown evidence {primary}",
                reason_code="unresolved_evidence_ref",
            )
        head = classify_assessment_head(
            category=str(item.get("assessment_head") or item.get("category") or ""),
            rule_id=str(item.get("rule_id") or ""),
        )
        facts.append(
            AggregatedFindingFact(
                repository_id=snapshot.repository_id,
                assessment_id=snapshot.assessment_id,
                finding_id=finding_id,
                rule_id=str(item.get("rule_id") or ""),
                rule_version=str(item.get("rule_version") or "") or None,
                assessment_head_id=head,
                severity=str(item.get("severity") or "informational").lower(),
                finding_confidence=str(item.get("confidence") or "unavailable"),
                evidence_completeness=str(item.get("evidence_completeness") or "") or None,
                primary_evidence_id=primary,
                correlation_ids=(),
                limitations=tuple(limitations),
                unclassified=head is None,
            )
        )
    return tuple(sorted(facts, key=lambda row: (row.repository_id, row.finding_id)))


def _project_recommendations(
    *,
    assessment: Mapping[str, Any],
    snapshot: NormalizedAssessmentSnapshot,
    finding_ids: set[str],
    limitations: Sequence[str],
) -> tuple[AggregatedRecommendationFact, ...]:
    rows = assessment.get("deterministic_recommendations") or assessment.get("recommendations")
    if not isinstance(rows, list):
        return ()
    facts: list[AggregatedRecommendationFact] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        rid = str(item.get("id") or item.get("recommendation_id") or "").strip()
        if not rid:
            continue
        supporting = _id_tuple(
            item.get("supporting_finding_ids") or item.get("related_finding_ids") or []
        )
        for fid in supporting:
            if fid not in finding_ids:
                raise AggregationUnresolvedReferenceError(
                    f"recommendation {rid} references unknown finding {fid}",
                    reason_code="unresolved_finding_ref",
                )
        primary = str(item.get("primary_finding_id") or "").strip() or None
        if primary and primary not in finding_ids:
            raise AggregationUnresolvedReferenceError(
                f"recommendation {rid} primary finding unknown: {primary}",
                reason_code="unresolved_finding_ref",
            )
        provider = None
        rule_id = str(item.get("rule_id") or "")
        if rule_id.startswith("provider:"):
            provider = rule_id.split(":", 1)[1]
        facts.append(
            AggregatedRecommendationFact(
                repository_id=snapshot.repository_id,
                assessment_id=snapshot.assessment_id,
                recommendation_id=rid,
                provider_id=provider or (str(item.get("provider_id") or "") or None),
                category=str(item.get("category") or ""),
                priority=str(item.get("priority") or ""),
                priority_score=str(item.get("priority_score") or "") or None,
                recommendation_confidence=str(
                    item.get("confidence") or item.get("recommendation_confidence") or "unavailable"
                ),
                supporting_finding_ids=supporting,
                primary_finding_id=primary,
                limitations=tuple(limitations),
            )
        )
    return tuple(sorted(facts, key=lambda row: (row.repository_id, row.recommendation_id)))


def _project_priority_actions(
    *,
    assessment: Mapping[str, Any],
    snapshot: NormalizedAssessmentSnapshot,
    recommendation_ids: set[str],
    finding_ids: set[str],
    limitations: Sequence[str],
) -> tuple[AggregatedPriorityActionFact, ...]:
    rows = assessment.get("priority_actions")
    if not isinstance(rows, list):
        return ()
    facts: list[AggregatedPriorityActionFact] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        aid = str(item.get("action_id") or item.get("id") or "").strip()
        if not aid:
            continue
        recs = _id_tuple(item.get("supporting_recommendation_ids") or [])
        finds = _id_tuple(item.get("supporting_finding_ids") or [])
        for rid in recs:
            if rid not in recommendation_ids:
                raise AggregationUnresolvedReferenceError(
                    f"priority action {aid} references unknown recommendation {rid}",
                    reason_code="unresolved_recommendation_ref",
                )
        for fid in finds:
            if fid not in finding_ids:
                raise AggregationUnresolvedReferenceError(
                    f"priority action {aid} references unknown finding {fid}",
                    reason_code="unresolved_finding_ref",
                )
        facts.append(
            AggregatedPriorityActionFact(
                repository_id=snapshot.repository_id,
                assessment_id=snapshot.assessment_id,
                priority_action_id=aid,
                priority=str(item.get("priority") or ""),
                priority_score=str(item.get("priority_score") or "") or None,
                presentation_bucket=str(item.get("presentation_bucket") or item.get("bucket") or "")
                or None,
                supporting_recommendation_ids=recs,
                supporting_finding_ids=finds,
                limitations=tuple(limitations),
            )
        )
    return tuple(sorted(facts, key=lambda row: (row.repository_id, row.priority_action_id)))


def _project_roadmap(
    *,
    assessment: Mapping[str, Any],
    snapshot: NormalizedAssessmentSnapshot,
    action_ids: set[str],
    recommendation_ids: set[str],
    finding_ids: set[str],
    limitations: Sequence[str],
) -> tuple[AggregatedRoadmapFact, ...]:
    roadmap = assessment.get("roadmap")
    if not isinstance(roadmap, Mapping):
        return ()
    rows = roadmap.get("initiatives")
    if not isinstance(rows, list):
        return ()
    facts: list[AggregatedRoadmapFact] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        iid = str(item.get("initiative_id") or item.get("id") or "").strip()
        if not iid:
            continue
        pas = _id_tuple(item.get("supporting_priority_action_ids") or [])
        recs = _id_tuple(item.get("supporting_recommendation_ids") or [])
        finds = _id_tuple(item.get("supporting_finding_ids") or [])
        for aid in pas:
            if aid not in action_ids:
                raise AggregationUnresolvedReferenceError(
                    f"roadmap initiative {iid} references unknown priority action {aid}",
                    reason_code="unresolved_priority_action_ref",
                )
        for rid in recs:
            if rid not in recommendation_ids:
                raise AggregationUnresolvedReferenceError(
                    f"roadmap initiative {iid} references unknown recommendation {rid}",
                    reason_code="unresolved_recommendation_ref",
                )
        for fid in finds:
            if fid not in finding_ids:
                raise AggregationUnresolvedReferenceError(
                    f"roadmap initiative {iid} references unknown finding {fid}",
                    reason_code="unresolved_finding_ref",
                )
        facts.append(
            AggregatedRoadmapFact(
                repository_id=snapshot.repository_id,
                assessment_id=snapshot.assessment_id,
                initiative_id=iid,
                phase=str(item.get("phase") or "") or None,
                initiative_type=str(item.get("initiative_type") or "") or None,
                supporting_priority_action_ids=pas,
                supporting_recommendation_ids=recs,
                supporting_finding_ids=finds,
                limitations=tuple(limitations),
            )
        )
    return tuple(sorted(facts, key=lambda row: (row.repository_id, row.initiative_id)))


def _project_correlations(
    *,
    assessment: Mapping[str, Any],
    snapshot: NormalizedAssessmentSnapshot,
    finding_ids: set[str],
    limitations: Sequence[str],
) -> tuple[AggregatedCorrelationFact, ...]:
    rows = assessment.get("finding_correlations")
    if not isinstance(rows, list):
        return ()
    facts: list[AggregatedCorrelationFact] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        cid = str(item.get("correlation_id") or item.get("id") or "").strip()
        if not cid:
            continue
        members = _id_tuple(item.get("finding_ids") or item.get("related_finding_ids") or [])
        for fid in members:
            if fid not in finding_ids:
                raise AggregationUnresolvedReferenceError(
                    f"correlation {cid} references unknown finding {fid}",
                    reason_code="unresolved_correlation_finding_ref",
                )
        facts.append(
            AggregatedCorrelationFact(
                repository_id=snapshot.repository_id,
                assessment_id=snapshot.assessment_id,
                correlation_id=cid,
                correlation_type=str(item.get("correlation_type") or item.get("type") or ""),
                finding_ids=members,
                assessment_head_ids=_id_tuple(item.get("assessment_head_ids") or []),
                confidence=str(item.get("confidence") or "") or None,
                basis=str(item.get("basis") or "") or None,
                limitations=tuple(limitations),
            )
        )
    return tuple(sorted(facts, key=lambda row: (row.repository_id, row.correlation_id)))


def _project_technologies(
    *,
    assessment: Mapping[str, Any],
    snapshot: NormalizedAssessmentSnapshot,
    limitations: Sequence[str],
) -> tuple[AggregatedTechnologyFact, ...]:
    rows = assessment.get("technologies")
    if not isinstance(rows, list):
        return ()
    facts: list[AggregatedTechnologyFact] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        name = str(item.get("name") or item.get("normalized_name") or "").strip()
        if not name:
            continue
        reject_unsafe_text(name, label="technology_name")
        version = item.get("version")
        version_text = str(version).strip() if version not in (None, "") else None
        if version_text is None:
            state = VersionState.UNAVAILABLE
        else:
            state = VersionState.KNOWN
        tid = str(item.get("technology_id") or item.get("id") or "").strip()
        if not tid:
            tid = f"{name}@{version_text or 'unavailable'}"
        # Occurrence rows for the same name/version must remain distinct composites.
        conf_raw = str(item.get("confidence") or "unavailable").lower()
        try:
            confidence = ConfidenceLevel(conf_raw)
        except ValueError:
            confidence = ConfidenceLevel.UNAVAILABLE
        facts.append(
            AggregatedTechnologyFact(
                normalized_name=name,
                category=str(item.get("category") or "unknown"),
                version_state=state,
                version=version_text,
                repository_id=snapshot.repository_id,
                assessment_id=snapshot.assessment_id,
                source_entity_ref=AggregatedEntityRef(
                    repository_id=snapshot.repository_id,
                    assessment_id=snapshot.assessment_id,
                    entity_type="technology",
                    entity_id=tid,
                    canonical_report_reference=snapshot.canonical_report_reference,
                    category=str(item.get("category") or ""),
                ),
                confidence=confidence,
                limitations=tuple(limitations),
            )
        )
    # Detect conflicting versions for same name within one repository.
    by_name: dict[str, set[str | None]] = {}
    for fact in facts:
        by_name.setdefault(fact.normalized_name, set()).add(fact.version)
    adjusted: list[AggregatedTechnologyFact] = []
    for fact in facts:
        versions = by_name[fact.normalized_name]
        if len({v for v in versions if v is not None}) > 1:
            adjusted.append(
                AggregatedTechnologyFact(
                    normalized_name=fact.normalized_name,
                    category=fact.category,
                    version_state=VersionState.CONFLICTING,
                    version=fact.version,
                    repository_id=fact.repository_id,
                    assessment_id=fact.assessment_id,
                    source_entity_ref=fact.source_entity_ref,
                    confidence=fact.confidence,
                    limitations=tuple(
                        sorted(set(fact.limitations + ("conflicting_versions",)))
                    ),
                )
            )
        else:
            adjusted.append(fact)
    return tuple(
        sorted(adjusted, key=lambda row: (row.normalized_name, row.repository_id, row.version or ""))
    )


def _project_coverage_confidence(
    *,
    snapshot: NormalizedAssessmentSnapshot,
    limitations: Sequence[str],
) -> tuple[tuple[AggregatedCoverageFact, ...], tuple[AggregatedConfidenceFact, ...]]:
    coverage = tuple(
        AggregatedCoverageFact(
            repository_id=snapshot.repository_id,
            assessment_id=snapshot.assessment_id,
            assessment_head_id=head,
            coverage_status=status,
            limitations=tuple(limitations),
        )
        for head, status in sorted(snapshot.assessment_coverage.items())
    )
    confidence = tuple(
        AggregatedConfidenceFact(
            repository_id=snapshot.repository_id,
            assessment_id=snapshot.assessment_id,
            assessment_head_id=head,
            confidence_level=level,
            limitations=tuple(limitations),
        )
        for head, level in sorted(snapshot.assessment_head_confidence.items())
    )
    return coverage, confidence


def _project_head_facts(
    *,
    snapshot: NormalizedAssessmentSnapshot,
    finding_facts: Sequence[AggregatedFindingFact],
    recommendation_facts: Sequence[AggregatedRecommendationFact],
    priority_action_facts: Sequence[AggregatedPriorityActionFact],
    limitations: Sequence[str],
) -> tuple[AggregatedAssessmentHeadFact, ...]:
    heads = set(CANONICAL_ASSESSMENT_HEADS) | set(snapshot.enabled_assessment_heads) | set(
        snapshot.disabled_assessment_heads
    ) | set(snapshot.unavailable_assessment_heads) | set(snapshot.assessment_coverage) | set(
        snapshot.assessment_head_confidence
    )
    facts: list[AggregatedAssessmentHeadFact] = []
    for head in sorted(heads):
        if head in snapshot.disabled_assessment_heads:
            activation = ActivationStatus.DISABLED
            coverage = CoverageStatus.DISABLED
        elif head in snapshot.unavailable_assessment_heads:
            activation = ActivationStatus.UNAVAILABLE
            coverage = CoverageStatus.UNAVAILABLE
        elif head in snapshot.missing_assessment_heads or (
            head not in snapshot.enabled_assessment_heads
            and head not in snapshot.available_assessment_heads
            and head not in snapshot.assessment_coverage
        ):
            activation = ActivationStatus.UNAVAILABLE
            coverage = CoverageStatus.UNAVAILABLE
        elif head in snapshot.enabled_assessment_heads:
            activation = ActivationStatus.ACTIVATED
            coverage = _coverage_enum(snapshot.assessment_coverage.get(head))
        else:
            activation = ActivationStatus.AVAILABLE
            coverage = _coverage_enum(snapshot.assessment_coverage.get(head))

        head_findings = [f for f in finding_facts if f.assessment_head_id == head]
        # Unclassified findings remain outside head counts.
        finding_count = len(head_findings)
        highest = None
        if head_findings:
            highest = max(
                head_findings,
                key=lambda row: _SEVERITY_RANK.get(row.severity.lower(), -1),
            ).severity

        # Recommendation/PA counts by category/head mapping — conservative.
        rec_count = sum(
            1
            for rec in recommendation_facts
            if classify_assessment_head(category=rec.category, rule_id=None) == head
        )
        # PAs inherit from supporting findings when possible.
        pa_count = 0
        for action in priority_action_facts:
            linked = [
                f
                for f in finding_facts
                if f.finding_id in action.supporting_finding_ids and f.assessment_head_id == head
            ]
            if linked:
                pa_count += 1

        facts.append(
            AggregatedAssessmentHeadFact(
                repository_id=snapshot.repository_id,
                assessment_id=snapshot.assessment_id,
                assessment_head_id=head,
                activation_status=activation,
                coverage_status=coverage,
                confidence_level=_confidence_enum(
                    snapshot.assessment_head_confidence.get(head)
                ),
                finding_count=finding_count,
                recommendation_count=rec_count,
                priority_action_count=pa_count,
                highest_severity=highest,
                limitations=tuple(limitations),
            )
        )
    return tuple(facts)


def _coverage_enum(raw: str | None) -> CoverageStatus:
    if not raw:
        return CoverageStatus.UNAVAILABLE
    try:
        return CoverageStatus(str(raw).lower())
    except ValueError:
        return CoverageStatus.UNAVAILABLE


def _confidence_enum(raw: str | None) -> ConfidenceLevel:
    if not raw:
        return ConfidenceLevel.UNAVAILABLE
    try:
        return ConfidenceLevel(str(raw).lower())
    except ValueError:
        return ConfidenceLevel.UNAVAILABLE


def _collect_ids(rows: object, keys: tuple[str, ...]) -> set[str]:
    if not isinstance(rows, list):
        return set()
    out: set[str] = set()
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        for key in keys:
            value = str(item.get(key) or "").strip()
            if value:
                out.add(value)
                break
    return out


def _id_tuple(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)):
        return ()
    return tuple(sorted({str(item).strip() for item in raw if str(item).strip()}))
