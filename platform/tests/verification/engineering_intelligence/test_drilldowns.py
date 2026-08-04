"""Drill-down tests."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)

from verification.engineering_intelligence.drilldowns import check_drilldowns
from verification.engineering_intelligence.fixtures import make_public_input, synthetic_report
from verification.engineering_intelligence.ingestion import build_pipeline_from_inputs


def test_one_drilldown_per_repo() -> None:
    inputs = []
    source = InMemoryAssessmentReportSource()
    for i in range(2):
        report = synthetic_report(
            finding_id=f"finding:{i}",
            evidence_id=f"ev:{i}",
            recommendation_id=f"rec:{i}",
            action_id=f"pa:{i}",
            initiative_id=f"init:{i}",
        )
        item = make_public_input(
            repository_id=f"repo:d{i}",
            assessment_id=f"assessment:d{i}",
            assessment_run_id=f"run:d{i}",
            report=report,
        )
        source.put(item.report_reference, item.report_document)  # type: ignore[arg-type]
        inputs.append(item)
    pipeline = build_pipeline_from_inputs(inputs, report_source=source)
    assert all(c.ok for c in check_drilldowns(pipeline))
