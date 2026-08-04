"""Provenance tests."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)

from verification.engineering_intelligence.fixtures import make_public_input, synthetic_report
from verification.engineering_intelligence.ingestion import build_pipeline_from_inputs
from verification.engineering_intelligence.provenance import check_provenance


def test_provenance_links() -> None:
    item = make_public_input(
        repository_id="repo:prov",
        assessment_id="assessment:prov",
        assessment_run_id="run:prov",
        report=synthetic_report(),
    )
    source = InMemoryAssessmentReportSource()
    source.put(item.report_reference, item.report_document)  # type: ignore[arg-type]
    pipeline = build_pipeline_from_inputs([item], report_source=source)
    assert all(c.ok for c in check_provenance(pipeline))
