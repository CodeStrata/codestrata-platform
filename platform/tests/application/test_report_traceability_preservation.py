"""Epic 2 Slice 2.8 — Platform ingestion preserves report.json traceability."""

from __future__ import annotations

import json

import pytest

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata.reporting.traceability.preservation import assert_traceability_equivalent

from codestrata_platform.application.common.errors import ValidationError
from codestrata_platform.application.intelligence.parsers.report_json_parser import (
    ReportJsonParser,
)
from codestrata_platform.application.intelligence.service import (
    PARSER_VERSION,
    _to_domain_finding,
)
from codestrata_platform.application.intelligence.traceability_preservation import (
    export_preserved_assessment,
    round_trip_traceability,
)
from codestrata_platform.domain.assessment.ids import AssessmentId


def _bytes(payload: object) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _full_engine_report() -> dict:
    return {
        "schema_version": ASSESSMENT_JSON_SCHEMA_VERSION,
        "assessment": {
            "evidence": [
                {
                    "evidence_id": "ev:alpha",
                    "kind": "other",
                    "production_mode": "direct",
                    "location": {"path": "src/a.py", "line_start": 3, "line_end": 4},
                    "limitations": [],
                }
            ],
            "findings": [
                {
                    "id": "finding:1",
                    "rule_id": "rule.demo",
                    "title": "Demo finding",
                    "description": "Observed issue",
                    "category": "security",
                    "severity": "high",
                    "confidence": 0.9,
                    "evidence_refs": [{"evidence_id": "ev:alpha"}],
                    "primary_evidence_id": "ev:alpha",
                    "synthesized_from_evidence_ids": ["ev:alpha"],
                    "evidence_completeness": "complete",
                    "limitations": ["demo-limit"],
                }
            ],
            "deterministic_recommendations": [
                {
                    "id": "rec:1",
                    "title": "Fix demo",
                    "summary": "Address the finding",
                    "priority": "high",
                    "category": "security",
                    "supporting_finding_ids": ["finding:1"],
                    "related_finding_ids": ["finding:1"],
                    "primary_finding_id": "finding:1",
                    "recommendation_type": "remediation",
                    "evidence_completeness": "complete",
                    "limitations": [],
                }
            ],
            "priority_actions": [
                {
                    "action_id": "rec:1",
                    "title": "Fix demo",
                    "supporting_recommendation_ids": ["rec:1"],
                    "primary_recommendation_id": "rec:1",
                    "supporting_finding_ids": ["finding:1"],
                    "evidence_completeness": "complete",
                    "limitations": [],
                    "action_type": "remediation",
                }
            ],
            "roadmap": {
                "initiatives": [
                    {
                        "initiative_id": "init:1",
                        "title": "Secure baseline",
                        "supporting_priority_action_ids": ["rec:1"],
                        "primary_priority_action_id": "rec:1",
                        "supporting_recommendation_ids": ["rec:1"],
                        "supporting_finding_ids": ["finding:1"],
                        "initiative_type": "priority_action_backed",
                        "evidence_completeness": "complete",
                        "limitations": [],
                        "depends_on_initiative_ids": [],
                    }
                ]
            },
            "summary": {
                "evidence_count": 1,
                "priority_action_count": 1,
                "roadmap_initiative_count": 1,
            },
        },
    }


def test_platform_ingests_full_slice_26_report() -> None:
    report = _full_engine_report()
    parsed = ReportJsonParser().parse(
        schema_version=ASSESSMENT_JSON_SCHEMA_VERSION,
        content=_bytes(report),
        source_artifact_id="artifact:report",
    )
    assert parsed.schema_version == ASSESSMENT_JSON_SCHEMA_VERSION
    assert parsed.traceability_status == "complete"
    assert parsed.canonical_report is not None
    assert len(parsed.assessment_evidence) == 1
    assert parsed.assessment_evidence[0]["evidence_id"] == "ev:alpha"
    assert len(parsed.priority_actions) == 1
    assert parsed.assessment_roadmap is not None
    assert parsed.assessment_roadmap["initiatives"][0]["supporting_priority_action_ids"] == [
        "rec:1"
    ]
    assert parsed.findings[0].primary_evidence_id == "ev:alpha"
    assert parsed.findings[0].evidence_completeness == "complete"
    assert parsed.recommendations[0].supporting_finding_ids == ("finding:1",)
    assert any(d.startswith("traceability_status:") for d in parsed.diagnostics)
    assert "assessment_roadmap:repository_scoped_not_platform_strategic" in parsed.diagnostics


def test_platform_round_trip_preserves_traceability() -> None:
    report = _full_engine_report()
    parsed = ReportJsonParser().parse(
        schema_version=ASSESSMENT_JSON_SCHEMA_VERSION,
        content=_bytes(report),
        source_artifact_id="artifact:report",
    )
    result = round_trip_traceability(report, parsed=parsed)
    assert result["equivalent"] is True
    exported = export_preserved_assessment(parsed)
    assert exported["platform_strategic_roadmap"] is False
    assert exported["assessment_roadmap_scope"] == "repository"
    assert_traceability_equivalent(
        report["assessment"],
        exported["assessment"],
    )


def test_platform_preserves_canonical_evidence_ids() -> None:
    report = _full_engine_report()
    # Include thin evidence with canonical id for projection.
    report["assessment"]["findings"][0]["evidence"] = [
        {
            "evidence_id": "ev:alpha",
            "path_reference": "src/a.py",
            "line_start": 3,
        }
    ]
    parsed = ReportJsonParser().parse(
        schema_version=ASSESSMENT_JSON_SCHEMA_VERSION,
        content=_bytes(report),
        source_artifact_id="artifact:report",
    )
    finding = _to_domain_finding(
        parsed.findings[0],
        assessment_id=AssessmentId.generate(),
    )
    assert finding.evidence_references[0].evidence_id.value == "ev:alpha"


def test_platform_rejects_unresolved_core_references() -> None:
    broken = _full_engine_report()
    broken["assessment"]["priority_actions"][0]["supporting_recommendation_ids"] = [
        "rec:missing"
    ]
    with pytest.raises(ValidationError) as exc:
        ReportJsonParser().parse(
            schema_version=ASSESSMENT_JSON_SCHEMA_VERSION,
            content=_bytes(broken),
            source_artifact_id="artifact:report",
        )
    assert exc.value.reason_code == "traceability_validation_failed"


def test_platform_legacy_schema_12_without_evidence_accepted() -> None:
    legacy = {
        "schema_version": ASSESSMENT_JSON_SCHEMA_VERSION,
        "assessment": {
            "findings": [
                {
                    "id": "finding:legacy",
                    "rule_id": "rule.x",
                    "title": "Legacy",
                    "description": "Inline only",
                    "category": "security",
                    "severity": "low",
                    "confidence": 0.5,
                    "evidence": [{"file_path": "a.py", "line_number": 1}],
                }
            ],
            "deterministic_recommendations": [
                {
                    "id": "rec:legacy",
                    "title": "Legacy rec",
                    "summary": "Related only",
                    "priority": "medium",
                    "category": "security",
                    "related_finding_ids": ["finding:legacy"],
                }
            ],
        },
    }
    parsed = ReportJsonParser().parse(
        schema_version=ASSESSMENT_JSON_SCHEMA_VERSION,
        content=_bytes(legacy),
        source_artifact_id="artifact:report",
    )
    assert parsed.traceability_status in {"legacy", "incomplete"}
    assert parsed.assessment_evidence == ()
    assert parsed.priority_actions == ()
    assert parsed.recommendations[0].related_finding_ids == ("finding:legacy",)
    # Do not fabricate PA / evidence indexes.
    assert "priority_actions" not in (parsed.canonical_report or {}).get("assessment", {})


def test_platform_legacy_recommendation_grouped_roadmap_preserved() -> None:
    legacy = {
        "schema_version": ASSESSMENT_JSON_SCHEMA_VERSION,
        "assessment": {
            "findings": [],
            "deterministic_recommendations": [],
            "roadmap": {
                "initiatives": [
                    {
                        "initiative_id": "init:legacy",
                        "title": "Legacy wave",
                        "related_recommendation_ids": ["rec:old"],
                        "initiative_type": "legacy",
                    }
                ]
            },
        },
    }
    parsed = ReportJsonParser().parse(
        schema_version=ASSESSMENT_JSON_SCHEMA_VERSION,
        content=_bytes(legacy),
        source_artifact_id="artifact:report",
    )
    assert parsed.assessment_roadmap is not None
    assert parsed.assessment_roadmap["initiatives"][0]["related_recommendation_ids"] == [
        "rec:old"
    ]
    assert parsed.assessment_roadmap["initiatives"][0].get("supporting_priority_action_ids") is None


def test_parser_version_bumped_additively() -> None:
    assert PARSER_VERSION.startswith("1.")
    assert PARSER_VERSION != "1.0.0"


def test_flat_legacy_platform_payload_still_parses() -> None:
    """Existing Platform flat fixtures remain compatible."""
    report = ReportJsonParser().parse(
        schema_version="1.0",
        content=_bytes(
            {
                "findings": [],
                "recommendations": [
                    {
                        "recommendation_id": "rec:1",
                        "title": "Rotate secrets",
                        "description": "Use a secret manager.",
                        "priority": "high",
                        "category": "security",
                        "related_finding_ids": ["finding:1"],
                        "dependencies": ["infra.vault"],
                    }
                ],
            }
        ),
        source_artifact_id="artifact:report",
    )
    assert len(report.recommendations) == 1
    assert report.recommendations[0].recommendation_id == "rec:1"
