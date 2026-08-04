"""Dataset identity tests."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)

from verification.engineering_intelligence.fixtures import make_public_input, synthetic_report
from verification.engineering_intelligence.ingestion import build_pipeline_from_inputs


def test_dataset_id_stable_for_same_inputs() -> None:
    def build():
        item = make_public_input(
            repository_id="repo:stable",
            assessment_id="assessment:stable",
            assessment_run_id="run:stable",
            report=synthetic_report(),
            pinned_revision="3333333333333333333333333333333333333333",
        )
        source = InMemoryAssessmentReportSource()
        source.put(item.report_reference, item.report_document)  # type: ignore[arg-type]
        return build_pipeline_from_inputs([item], report_source=source)

    left = build()
    right = build()
    assert left.report.dataset.dataset_id.value == right.report.dataset.dataset_id.value
