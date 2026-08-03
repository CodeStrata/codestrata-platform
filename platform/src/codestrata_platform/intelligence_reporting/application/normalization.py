"""Normalize canonical assessment reports into bounded snapshots (no SoT copy)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

from codestrata.reporting.traceability.preservation import (
    CanonicalReportLoadError,
    extract_assessment,
)

from codestrata_platform.intelligence_reporting.application.contracts import (
    AssessmentDatasetInput,
    DisplayNamePolicy,
    EntityReference,
    IngestionStatus,
    NormalizedAssessmentSnapshot,
    WebsiteExportEligibility,
)
from codestrata_platform.intelligence_reporting.domain.enums import (
    DataVisibility,
    InclusionStatus,
)

# Canonical assessment-head IDs from Engine customer report contract.
CANONICAL_ASSESSMENT_HEADS: tuple[str, ...] = (
    "engineering_intelligence",
    "technology_inventory",
    "architecture_intelligence",
    "technical_debt_intelligence",
    "dependency_intelligence",
    "security_intelligence",
    "cloud_readiness",
    "ai_readiness",
    "modernization_assessment",
)

_CANONICAL_SECTIONS = (
    "evidence",
    "findings",
    "deterministic_recommendations",
    "priority_actions",
    "roadmap",
    "assessment_head_confidence",
    "assessment_coverage",
    "finding_correlations",
    "technologies",
    "summary",
)


def stable_canonical_report_digest(document: Mapping[str, Any]) -> str:
    """SHA-256 of stable canonical JSON (sorted keys; no transport metadata added)."""

    material = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def extract_assessment_mapping(document: Mapping[str, Any]) -> dict[str, Any]:
    try:
        assessment = extract_assessment(dict(document))
    except CanonicalReportLoadError:
        assessment = dict(document) if isinstance(document, Mapping) else {}
    return assessment if isinstance(assessment, dict) else {}


def available_canonical_sections(assessment: Mapping[str, Any]) -> tuple[str, ...]:
    present: list[str] = []
    for name in _CANONICAL_SECTIONS:
        value = assessment.get(name)
        if value is None:
            continue
        if isinstance(value, (list, tuple, dict)) and not value:
            continue
        present.append(name)
    return tuple(sorted(set(present)))


# Engine activation pack IDs → commercial assessment-head IDs.
# Used only when assessment_coverage is absent (common in community report.json).
_ACTIVATION_PACK_TO_HEAD: dict[str, str] = {
    "security": "security_intelligence",
    "dependency": "dependency_intelligence",
    "architecture": "architecture_intelligence",
    "technical_debt": "technical_debt_intelligence",
    "cloud": "cloud_readiness",
    "ai_readiness": "ai_readiness",
    "roadmap": "modernization_assessment",
}


def normalize_assessment_heads(
    assessment: Mapping[str, Any],
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    dict[str, str],
    dict[str, str],
]:
    """Return enabled, available, disabled, unavailable, missing, confidence, coverage.

    Does not convert disabled→unavailable or invent completeness from empty findings.
    When ``assessment_coverage`` is absent, derive activation from Engine
    ``activation.packs`` and treat enabled packs as ``partial`` coverage (not complete).
    """

    coverage_raw = assessment.get("assessment_coverage")
    confidence_raw = assessment.get("assessment_head_confidence")
    coverage_map = _string_status_map(coverage_raw)
    confidence_map = _string_status_map(confidence_raw)

    enabled: set[str] = set()
    available: set[str] = set()
    disabled: set[str] = set()
    unavailable: set[str] = set()

    for head_id, status in coverage_map.items():
        lowered = status.lower()
        available.add(head_id)
        if lowered in {"disabled"}:
            disabled.add(head_id)
        elif lowered in {"unavailable", "not_applicable", "absent"}:
            unavailable.add(head_id)
        elif lowered in {"complete", "partial", "insufficient_evidence", "activated", "enabled"}:
            enabled.add(head_id)
        else:
            # Preserve honest unknown status as available but not enabled.
            available.add(head_id)

    # Explicit enablement lists if present (do not invent).
    for key, target in (
        ("enabled_assessment_heads", enabled),
        ("available_assessment_heads", available),
        ("disabled_assessment_heads", disabled),
        ("unavailable_assessment_heads", unavailable),
    ):
        raw = assessment.get(key)
        if isinstance(raw, (list, tuple)):
            for item in raw:
                text = str(item).strip()
                if text:
                    target.add(text)
                    available.add(text)

    if not coverage_map:
        _apply_activation_pack_heads(
            assessment,
            enabled=enabled,
            available=available,
            disabled=disabled,
            unavailable=unavailable,
            coverage_map=coverage_map,
        )

    known = enabled | available | disabled | unavailable | set(coverage_map) | set(confidence_map)
    missing = tuple(sorted(h for h in CANONICAL_ASSESSMENT_HEADS if h not in known))
    # Heads present only via confidence without coverage stay available, not enabled.
    for head_id in confidence_map:
        available.add(head_id)

    return (
        tuple(sorted(enabled)),
        tuple(sorted(available)),
        tuple(sorted(disabled)),
        tuple(sorted(unavailable)),
        missing,
        dict(sorted(confidence_map.items())),
        dict(sorted(coverage_map.items())),
    )


def _apply_activation_pack_heads(
    assessment: Mapping[str, Any],
    *,
    enabled: set[str],
    available: set[str],
    disabled: set[str],
    unavailable: set[str],
    coverage_map: dict[str, str],
) -> None:
    """Map Engine activation packs to commercial heads when coverage is absent."""

    activation = assessment.get("activation")
    packs = activation.get("packs") if isinstance(activation, Mapping) else None
    if isinstance(packs, list):
        for pack in packs:
            if not isinstance(pack, Mapping):
                continue
            pack_id = str(pack.get("pack_id") or "").strip().lower()
            head = _ACTIVATION_PACK_TO_HEAD.get(pack_id)
            if head is None:
                continue
            available.add(head)
            decision = str(pack.get("decision") or "").strip().lower()
            pack_enabled = bool(pack.get("enabled"))
            if pack_enabled or decision in {"enabled", "activated"}:
                enabled.add(head)
                coverage_map.setdefault(head, "partial")
            elif decision in {"skipped", "disabled"}:
                disabled.add(head)
                coverage_map.setdefault(head, "disabled")
            else:
                unavailable.add(head)
                coverage_map.setdefault(head, "unavailable")

    technologies = assessment.get("technologies")
    if isinstance(technologies, list) and technologies:
        head = "technology_inventory"
        available.add(head)
        enabled.add(head)
        coverage_map.setdefault(head, "partial")


def extract_entity_references(
    *,
    assessment: Mapping[str, Any],
    repository_id: str,
    assessment_id: str,
) -> dict[str, tuple[EntityReference, ...]]:
    evidence_refs = _evidence_refs(assessment, repository_id, assessment_id)
    finding_refs = _finding_refs(assessment, repository_id, assessment_id)
    recommendation_refs = _recommendation_refs(assessment, repository_id, assessment_id)
    priority_action_refs = _priority_action_refs(assessment, repository_id, assessment_id)
    roadmap_refs = _roadmap_refs(assessment, repository_id, assessment_id)
    correlation_refs = _correlation_refs(assessment, repository_id, assessment_id)
    technology_refs = _technology_refs(assessment, repository_id, assessment_id)
    return {
        "evidence_refs": evidence_refs,
        "finding_refs": finding_refs,
        "recommendation_refs": recommendation_refs,
        "priority_action_refs": priority_action_refs,
        "roadmap_refs": roadmap_refs,
        "correlation_refs": correlation_refs,
        "technology_refs": technology_refs,
    }


def evaluate_website_export_eligibility(
    item: AssessmentDatasetInput,
    *,
    limitations: Sequence[str] = (),
) -> WebsiteExportEligibility:
    blocking: list[str] = []
    requires_anonymization = item.visibility is not DataVisibility.PUBLIC
    if item.visibility in {DataVisibility.CUSTOMER_PRIVATE, DataVisibility.INTERNAL}:
        blocking.append("private_repository_identity")
        requires_anonymization = True
    if item.visibility is DataVisibility.PUBLIC and (
        not item.source_reference_publication_permitted
    ):
        blocking.append("missing_publication_permission")
    if item.source_reference and (
        item.source_reference.startswith("file://")
        or item.source_reference.startswith("/")
        or item.source_reference.startswith("\\")
    ):
        blocking.append("unsafe_source_reference")
    # Never infer eligibility from URL shape alone.
    eligible = not blocking and item.visibility is DataVisibility.PUBLIC
    return WebsiteExportEligibility(
        eligible=eligible,
        requires_anonymization=requires_anonymization,
        blocking_reasons=tuple(sorted(set(blocking))),
        limitations=tuple(sorted(set(limitations))),
    )


def resolve_display_name(item: AssessmentDatasetInput) -> str | None:
    if item.display_name_policy is DisplayNamePolicy.OMIT:
        return None
    if item.display_name_policy is DisplayNamePolicy.ANONYMIZE:
        digest = hashlib.sha256(item.repository_id.encode("utf-8")).hexdigest()[:8]
        return f"repository-{digest}"
    return item.display_name


def build_normalized_snapshot(
    *,
    item: AssessmentDatasetInput,
    document: Mapping[str, Any],
    schema_version: str,
    is_legacy: bool,
    traceability_status: str,
    canonical_report_reference: str | None,
    inclusion_status: InclusionStatus,
    ingestion_status: IngestionStatus,
    limitations: Sequence[str] = (),
    exclusion_reason: str | None = None,
    diagnostics: Sequence[str] = (),
) -> NormalizedAssessmentSnapshot:
    assessment = extract_assessment_mapping(document)
    digest = stable_canonical_report_digest(document)
    (
        enabled,
        available,
        disabled,
        unavailable,
        missing,
        confidence,
        coverage,
    ) = normalize_assessment_heads(assessment)
    refs = extract_entity_references(
        assessment=assessment,
        repository_id=item.repository_id,
        assessment_id=item.assessment_id,
    )
    timestamp = None
    for key in ("assessed_at", "assessment_timestamp", "generated_at", "timestamp"):
        raw = document.get(key)
        if raw is None and isinstance(assessment.get("summary"), Mapping):
            raw = assessment["summary"].get(key)
        if isinstance(raw, str) and raw.strip():
            timestamp = raw.strip()
            break
    website = evaluate_website_export_eligibility(item, limitations=limitations)
    return NormalizedAssessmentSnapshot(
        repository_id=item.repository_id,
        assessment_id=item.assessment_id,
        assessment_run_id=item.assessment_run_id,
        workspace_id=item.workspace_id,
        organization_id=item.organization_id,
        assessment_schema_version=schema_version,
        assessment_timestamp=timestamp,
        source_type=item.source_type,
        source_reference=item.source_reference,
        pinned_revision=item.pinned_revision,
        visibility=item.visibility,
        display_name=resolve_display_name(item),
        source_reference_publication_permitted=item.source_reference_publication_permitted,
        enabled_assessment_heads=enabled,
        available_assessment_heads=available,
        disabled_assessment_heads=disabled,
        unavailable_assessment_heads=unavailable,
        missing_assessment_heads=missing,
        assessment_head_confidence=confidence,
        assessment_coverage=coverage,
        technology_refs=refs["technology_refs"],
        finding_refs=refs["finding_refs"],
        recommendation_refs=refs["recommendation_refs"],
        priority_action_refs=refs["priority_action_refs"],
        roadmap_refs=refs["roadmap_refs"],
        correlation_refs=refs["correlation_refs"],
        evidence_refs=refs["evidence_refs"],
        canonical_report_reference=canonical_report_reference,
        canonical_report_digest=digest,
        ingestion_status=ingestion_status,
        inclusion_status=inclusion_status,
        traceability_status=traceability_status,
        available_canonical_sections=available_canonical_sections(assessment),
        website_export_eligibility=website,
        limitations=tuple(sorted(set(limitations))),
        exclusion_reason=exclusion_reason,
        diagnostics=tuple(diagnostics),
    )


def _string_status_map(raw: object) -> dict[str, str]:
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, str] = {}
    for key, value in raw.items():
        head = str(key).strip()
        if not head:
            continue
        if isinstance(value, Mapping):
            status = (
                value.get("status")
                or value.get("coverage_status")
                or value.get("level")
                or value.get("confidence")
            )
            out[head] = str(status or "unavailable")
        else:
            out[head] = str(value)
    return out


def _ref(
    *,
    entity_id: str,
    entity_kind: str,
    assessment_id: str,
    repository_id: str,
    metadata: Mapping[str, str] | None = None,
) -> EntityReference:
    return EntityReference(
        entity_id=entity_id,
        entity_kind=entity_kind,
        assessment_id=assessment_id,
        repository_id=repository_id,
        metadata=dict(sorted((metadata or {}).items())),
    )


def _evidence_refs(
    assessment: Mapping[str, Any], repository_id: str, assessment_id: str
) -> tuple[EntityReference, ...]:
    rows = assessment.get("evidence")
    if not isinstance(rows, list):
        return ()
    refs: list[EntityReference] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        eid = str(item.get("evidence_id") or item.get("id") or "").strip()
        if not eid:
            continue
        kind = str(item.get("kind") or item.get("evidence_type") or "evidence")
        # Never copy excerpts/snippets into refs.
        refs.append(
            _ref(
                entity_id=eid,
                entity_kind="evidence",
                assessment_id=assessment_id,
                repository_id=repository_id,
                metadata={"kind": kind},
            )
        )
    return tuple(sorted(refs, key=lambda r: r.entity_id))


def _finding_refs(
    assessment: Mapping[str, Any], repository_id: str, assessment_id: str
) -> tuple[EntityReference, ...]:
    rows = assessment.get("findings")
    if not isinstance(rows, list):
        return ()
    refs: list[EntityReference] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        fid = str(item.get("id") or item.get("finding_id") or "").strip()
        if not fid:
            continue
        evidence_ids = _id_list(
            item.get("synthesized_from_evidence_ids")
            or [
                ref.get("evidence_id")
                for ref in (item.get("evidence_refs") or [])
                if isinstance(ref, Mapping)
            ]
        )
        refs.append(
            _ref(
                entity_id=fid,
                entity_kind="finding",
                assessment_id=assessment_id,
                repository_id=repository_id,
                metadata={
                    "rule_id": str(item.get("rule_id") or ""),
                    "assessment_head": str(
                        item.get("assessment_head") or item.get("category") or ""
                    ),
                    "severity": str(item.get("severity") or ""),
                    "confidence": str(item.get("confidence") or ""),
                    "evidence_ids": ",".join(evidence_ids),
                },
            )
        )
    return tuple(sorted(refs, key=lambda r: r.entity_id))


def _recommendation_refs(
    assessment: Mapping[str, Any], repository_id: str, assessment_id: str
) -> tuple[EntityReference, ...]:
    rows = assessment.get("deterministic_recommendations") or assessment.get(
        "recommendations"
    )
    if not isinstance(rows, list):
        return ()
    refs: list[EntityReference] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        rid = str(item.get("id") or item.get("recommendation_id") or "").strip()
        if not rid:
            continue
        finding_ids = _id_list(
            item.get("supporting_finding_ids") or item.get("related_finding_ids") or []
        )
        refs.append(
            _ref(
                entity_id=rid,
                entity_kind="recommendation",
                assessment_id=assessment_id,
                repository_id=repository_id,
                metadata={
                    "category": str(item.get("category") or ""),
                    "priority": str(item.get("priority") or ""),
                    "confidence": str(
                        item.get("confidence") or item.get("recommendation_confidence") or ""
                    ),
                    "supporting_finding_ids": ",".join(finding_ids),
                },
            )
        )
    return tuple(sorted(refs, key=lambda r: r.entity_id))


def _priority_action_refs(
    assessment: Mapping[str, Any], repository_id: str, assessment_id: str
) -> tuple[EntityReference, ...]:
    rows = assessment.get("priority_actions")
    if not isinstance(rows, list):
        return ()
    refs: list[EntityReference] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        aid = str(item.get("action_id") or item.get("id") or "").strip()
        if not aid:
            continue
        refs.append(
            _ref(
                entity_id=aid,
                entity_kind="priority_action",
                assessment_id=assessment_id,
                repository_id=repository_id,
                metadata={
                    "priority": str(item.get("priority") or ""),
                    "supporting_recommendation_ids": ",".join(
                        _id_list(item.get("supporting_recommendation_ids") or [])
                    ),
                    "supporting_finding_ids": ",".join(
                        _id_list(item.get("supporting_finding_ids") or [])
                    ),
                },
            )
        )
    return tuple(sorted(refs, key=lambda r: r.entity_id))


def _roadmap_refs(
    assessment: Mapping[str, Any], repository_id: str, assessment_id: str
) -> tuple[EntityReference, ...]:
    roadmap = assessment.get("roadmap")
    if not isinstance(roadmap, Mapping):
        return ()
    rows = roadmap.get("initiatives")
    if not isinstance(rows, list):
        return ()
    refs: list[EntityReference] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        iid = str(item.get("initiative_id") or item.get("id") or "").strip()
        if not iid:
            continue
        refs.append(
            _ref(
                entity_id=iid,
                entity_kind="roadmap_initiative",
                assessment_id=assessment_id,
                repository_id=repository_id,
                metadata={
                    "phase": str(item.get("phase") or ""),
                    "initiative_type": str(item.get("initiative_type") or ""),
                    "supporting_priority_action_ids": ",".join(
                        _id_list(item.get("supporting_priority_action_ids") or [])
                    ),
                    "supporting_recommendation_ids": ",".join(
                        _id_list(item.get("supporting_recommendation_ids") or [])
                    ),
                    "supporting_finding_ids": ",".join(
                        _id_list(item.get("supporting_finding_ids") or [])
                    ),
                },
            )
        )
    return tuple(sorted(refs, key=lambda r: r.entity_id))


def _correlation_refs(
    assessment: Mapping[str, Any], repository_id: str, assessment_id: str
) -> tuple[EntityReference, ...]:
    rows = assessment.get("finding_correlations")
    if not isinstance(rows, list):
        return ()
    refs: list[EntityReference] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        cid = str(item.get("correlation_id") or item.get("id") or "").strip()
        if not cid:
            continue
        refs.append(
            _ref(
                entity_id=cid,
                entity_kind="finding_correlation",
                assessment_id=assessment_id,
                repository_id=repository_id,
                metadata={
                    "correlation_type": str(
                        item.get("correlation_type") or item.get("type") or ""
                    ),
                    "confidence": str(item.get("confidence") or ""),
                    "finding_ids": ",".join(
                        _id_list(item.get("finding_ids") or item.get("related_finding_ids") or [])
                    ),
                },
            )
        )
    return tuple(sorted(refs, key=lambda r: r.entity_id))


def _technology_refs(
    assessment: Mapping[str, Any], repository_id: str, assessment_id: str
) -> tuple[EntityReference, ...]:
    rows = assessment.get("technologies")
    if not isinstance(rows, list):
        # Some reports nest technology facts elsewhere; do not invent.
        return ()
    refs: list[EntityReference] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        tid = str(item.get("technology_id") or item.get("id") or item.get("name") or "").strip()
        if not tid:
            continue
        refs.append(
            _ref(
                entity_id=tid,
                entity_kind="technology",
                assessment_id=assessment_id,
                repository_id=repository_id,
                metadata={
                    "normalized_name": str(item.get("name") or item.get("normalized_name") or ""),
                    "category": str(item.get("category") or ""),
                },
            )
        )
    return tuple(sorted(refs, key=lambda r: r.entity_id))


def _id_list(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)):
        return ()
    values = [str(item).strip() for item in raw if str(item).strip()]
    return tuple(sorted(set(values)))
