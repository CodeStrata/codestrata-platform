"""Platform preservation of Engine report.json traceability (Epic 2 Slice 2.8).

Pattern A: the uploaded ``report_json`` artifact remains the authoritative
document. Parsed findings/recommendations are projections. Assessment roadmap
from report.json is distinct from Platform Strategic Roadmap.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from codestrata.reporting.traceability.preservation import (
    CanonicalReportLoadError,
    assert_traceability_equivalent,
    classify_traceability_state,
    extract_assessment,
    load_report_document,
    lookup_entity,
    preserve_assessment_collections,
    schema_version_of,
    traceability_snapshot,
    validate_canonical_assessment,
)

from codestrata_platform.application.intelligence.parsers.contracts import (
    ParsedAssessmentIntelligence,
)

__all__ = [
    "CanonicalReportLoadError",
    "assert_traceability_equivalent",
    "classify_traceability_state",
    "export_preserved_assessment",
    "extract_assessment",
    "load_report_document",
    "lookup_entity",
    "preserve_assessment_collections",
    "round_trip_traceability",
    "schema_version_of",
    "traceability_snapshot",
    "validate_canonical_assessment",
]


def export_preserved_assessment(
    parsed: ParsedAssessmentIntelligence,
) -> dict[str, Any]:
    """Export preserved assessment collections from a parsed report_json ingest.

    Prefer the retained canonical document; fall back to projected collections.
    Does not regenerate relationships.
    """

    if parsed.canonical_report is not None:
        assessment = extract_assessment(parsed.canonical_report)
        return {
            "schema_version": schema_version_of(parsed.canonical_report),
            "traceability_status": parsed.traceability_status
            or classify_traceability_state(assessment),
            "assessment": preserve_assessment_collections(assessment),
            "canonical_interchange": "assessment_report_json",
            "assessment_roadmap_scope": "repository",
            "platform_strategic_roadmap": False,
        }
    return {
        "schema_version": parsed.schema_version,
        "traceability_status": parsed.traceability_status,
        "assessment": {
            "evidence": list(parsed.assessment_evidence),
            "priority_actions": list(parsed.priority_actions),
            "roadmap": parsed.assessment_roadmap,
        },
        "canonical_interchange": "assessment_report_json",
        "assessment_roadmap_scope": "repository",
        "platform_strategic_roadmap": False,
        "note": "partial_projection_without_canonical_document",
    }


def round_trip_traceability(
    source: str | bytes | Mapping[str, Any],
    *,
    parsed: ParsedAssessmentIntelligence | None = None,
) -> dict[str, Any]:
    """Compare source report vs exported preserved assessment for equivalence."""

    document = load_report_document(source)
    left = extract_assessment(document)
    if parsed is None:
        raise CanonicalReportLoadError("parsed intelligence required for round-trip")
    exported = export_preserved_assessment(parsed)
    right = exported["assessment"]
    assert_traceability_equivalent(left, right)
    return {
        "equivalent": True,
        "schema_version": schema_version_of(document),
        "traceability_status": exported["traceability_status"],
        "snapshot": traceability_snapshot(left),
    }
