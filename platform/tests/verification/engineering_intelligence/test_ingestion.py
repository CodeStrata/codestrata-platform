"""Ingestion / dataset checks."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)

from verification.engineering_intelligence.dataset import (
    check_dataset,
    check_ingestion_scenarios,
)
from verification.engineering_intelligence.fixtures import make_public_input, synthetic_report
from verification.engineering_intelligence.ingestion import build_pipeline_from_inputs


def test_ingestion_scenarios() -> None:
    checks = check_ingestion_scenarios()
    assert checks
    assert all(c.ok for c in checks)


def test_dataset_refs_only() -> None:
    item = make_public_input(
        repository_id="repo:one",
        assessment_id="assessment:one",
        assessment_run_id="run:one",
        report=synthetic_report(),
    )
    source = InMemoryAssessmentReportSource()
    source.put(item.report_reference, item.report_document)  # type: ignore[arg-type]
    pipeline = build_pipeline_from_inputs([item], report_source=source)
    assert all(c.ok for c in check_dataset(pipeline))
