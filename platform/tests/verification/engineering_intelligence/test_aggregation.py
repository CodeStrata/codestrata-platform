"""Aggregation tests."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)

from verification.engineering_intelligence.aggregation import check_aggregation
from verification.engineering_intelligence.fixtures import make_public_input, synthetic_report
from verification.engineering_intelligence.ingestion import build_pipeline_from_inputs


def _two_repo_pipeline():
    inputs = []
    source = InMemoryAssessmentReportSource()
    for i in range(2):
        report = synthetic_report(
            finding_id=f"finding:{i}",
            evidence_id=f"ev:{i}",
            recommendation_id=f"rec:{i}",
            action_id=f"pa:{i}",
            initiative_id=f"init:{i}",
            rule_id="rule.shared",
        )
        item = make_public_input(
            repository_id=f"repo:r{i}",
            assessment_id=f"assessment:r{i}",
            assessment_run_id=f"run:r{i}",
            report=report,
        )
        source.put(item.report_reference, item.report_document)  # type: ignore[arg-type]
        inputs.append(item)
    return build_pipeline_from_inputs(inputs, report_source=source)


def test_aggregation_one_record_per_repo() -> None:
    pipeline = _two_repo_pipeline()
    assert all(c.ok for c in check_aggregation(pipeline))
