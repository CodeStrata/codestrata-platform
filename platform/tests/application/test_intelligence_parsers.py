"""Parser tests for assessment intelligence ingestion."""

from __future__ import annotations

import json

import pytest

from codestrata_platform.application.common.errors import PayloadTooLargeError, ValidationError
from codestrata_platform.application.intelligence.parsers.findings_parser import (
    FindingsArtifactParser,
)
from codestrata_platform.application.intelligence.parsers.merge import merge_parsed_intelligence
from codestrata_platform.application.intelligence.parsers.orchestrator import parse_artifacts
from codestrata_platform.application.intelligence.parsers.report_json_parser import ReportJsonParser
from codestrata_platform.application.intelligence.parsers.summary_parser import (
    AssessmentSummaryParser,
)
from codestrata_platform.domain.artifact.enums import ArtifactType


def _bytes(payload: object) -> bytes:
    return json.dumps(payload).encode("utf-8")


def test_findings_parser_parses_engine_shape() -> None:
    content = _bytes(
        {
            "findings": [
                {
                    "id": "finding:1",
                    "rule_id": "rule.security.token",
                    "title": "Hard-coded token",
                    "description": "Token found in source.",
                    "category": "security",
                    "severity": "high",
                    "confidence": 0.85,
                    "evidence": [
                        {
                            "file_path": "src/auth.py",
                            "line_number": 10,
                            "symbol": "API_TOKEN",
                        }
                    ],
                }
            ]
        }
    )
    parsed = FindingsArtifactParser().parse(
        schema_version="1.0",
        content=content,
        source_artifact_id="artifact:findings",
    )
    assert len(parsed.findings) == 1
    assert parsed.findings[0].finding_id == "finding:1"
    assert parsed.findings[0].evidence_references[0].path_reference == "src/auth.py"


def test_summary_and_report_json_parsers() -> None:
    summary = AssessmentSummaryParser().parse(
        schema_version="1.0",
        content=_bytes(
            {
                "metrics": {"security.findings.critical": 2},
                "scores": {"overall": 82.5},
            }
        ),
        source_artifact_id="artifact:summary",
    )
    assert any(metric.name == "assessment.security.findings.critical" for metric in summary.metrics)
    assert any(metric.name == "assessment.scores.overall" for metric in summary.metrics)

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


def test_merge_priority_prefers_findings_over_report_json() -> None:
    findings = FindingsArtifactParser().parse(
        schema_version="1.0",
        content=_bytes(
            {
                "findings": [
                    {
                        "finding_id": "finding:1",
                        "rule_id": "rule.security.token",
                        "title": "Authoritative finding",
                        "summary": "From findings artifact.",
                        "category": "security",
                        "severity": "critical",
                    }
                ]
            }
        ),
        source_artifact_id="artifact:findings",
    )
    report = ReportJsonParser().parse(
        schema_version="1.0",
        content=_bytes(
            {
                "findings": [
                    {
                        "finding_id": "finding:1",
                        "rule_id": "rule.security.token",
                        "title": "Lower priority finding",
                        "summary": "From report json.",
                        "category": "security",
                        "severity": "low",
                    }
                ]
            }
        ),
        source_artifact_id="artifact:report",
    )
    merged = merge_parsed_intelligence(
        (
            (ArtifactType.REPORT_JSON, report),
            (ArtifactType.FINDINGS, findings),
        )
    )
    assert merged.findings[0].title == "Authoritative finding"
    assert merged.findings[0].severity == "critical"


def test_orchestrator_rejects_secrets_and_malformed_json() -> None:
    with pytest.raises(ValidationError):
        parse_artifacts(
            [
                (
                    ArtifactType.FINDINGS,
                    "1.0",
                    _bytes({"findings": [{"metadata": {"api_key": "secret"}}]}),
                    "artifact:1",
                )
            ]
        )
    with pytest.raises(ValidationError):
        parse_artifacts(
            [
                (
                    ArtifactType.FINDINGS,
                    "1.0",
                    b"{not-json",
                    "artifact:1",
                )
            ]
        )


def test_orchestrator_skips_html_artifacts() -> None:
    parsed = parse_artifacts(
        [
            (
                ArtifactType.ASSESSMENT_SUMMARY,
                "1.0",
                _bytes({"metrics": {"assessment.status": "ready"}}),
                "artifact:summary",
            ),
            (
                ArtifactType.REPORT_HTML,
                "1.0",
                b"<html></html>",
                "artifact:html",
            ),
        ]
    )
    assert len(parsed.metrics) == 1


def test_parser_rejects_excessive_nesting() -> None:
    nested: dict[str, object] = {"findings": []}
    current: dict[str, object] = nested
    for _ in range(25):
        inner: dict[str, object] = {"findings": []}
        current["child"] = inner
        current = inner
    with pytest.raises(PayloadTooLargeError):
        FindingsArtifactParser().parse(
            schema_version="1.0",
            content=json.dumps(nested).encode("utf-8"),
            source_artifact_id="artifact:deep",
        )
