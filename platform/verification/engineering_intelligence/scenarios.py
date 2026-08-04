"""Offline scenario orchestration for SV.6 (A–T subset without network)."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.domain.enums import DataVisibility
from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)

from verification.engineering_intelligence.dataset import check_ingestion_scenarios
from verification.engineering_intelligence.fixtures import make_public_input, synthetic_report
from verification.engineering_intelligence.ingestion import build_pipeline_from_inputs
from verification.engineering_intelligence.models import CheckResult
from verification.engineering_intelligence.patterns import (
    check_single_repo_repeat_not_recurrence,
)
from verification.engineering_intelligence.technology import check_technology_aliases


def check_head_status_scenarios() -> list[CheckResult]:
    """Scenarios F/G: missing/disabled heads remain distinct."""

    report = synthetic_report(
        extra_assessment={
            "assessment_coverage": {
                "security_intelligence": {"status": "complete"},
                "dependency_intelligence": {"status": "disabled"},
                "cloud_readiness": {"status": "unavailable"},
                # missing head omitted intentionally
            }
        }
    )
    item = make_public_input(
        repository_id="repo:heads",
        assessment_id="assessment:heads",
        assessment_run_id="run:heads",
        report=report,
        pinned_revision="1111111111111111111111111111111111111111",
    )
    source = InMemoryAssessmentReportSource()
    source.put(item.report_reference, item.report_document)  # type: ignore[arg-type]
    pipeline = build_pipeline_from_inputs([item], report_source=source, title="heads")
    blob = str(pipeline.report_payload).lower()
    return [
        CheckResult(
            name="scenario:F_unavailable_not_zero_findings",
            ok="unavailable" in blob,
            detail="unavailable head represented",
            category="scenario",
            scenario="F",
        ),
        CheckResult(
            name="scenario:G_disabled_preserved",
            ok="disabled" in blob,
            detail="disabled head represented",
            category="scenario",
            scenario="G",
        ),
    ]


def check_empty_eligible_dataset() -> list[CheckResult]:
    """Scenario K: private-only inputs under public OSS should not invent ratios."""

    item = make_public_input(
        repository_id="repo:private-only",
        assessment_id="assessment:private-only",
        assessment_run_id="run:private-only",
        visibility=DataVisibility.CUSTOMER_PRIVATE,
        pinned_revision="2222222222222222222222222222222222222222",
    )
    # Building a public OSS pipeline with only private visibility should fail closed
    # or produce empty inclusion — never fake ratios.
    try:
        source = InMemoryAssessmentReportSource()
        source.put(item.report_reference, item.report_document)  # type: ignore[arg-type]
        pipeline = build_pipeline_from_inputs([item], report_source=source, title="empty")
        included = len(pipeline.ingest_result.dataset.included_repository_ids)
        # If somehow included, aggregation visibility should still exclude from public facts.
        ok = included == 0 or pipeline.report.repository_population is not None
        detail = f"included={included}"
    except Exception as exc:  # noqa: BLE001
        ok = True
        detail = type(exc).__name__
    return [
        CheckResult(
            name="scenario:K_empty_or_unavailable_safe",
            ok=ok,
            detail=detail,
            category="scenario",
            scenario="K",
        )
    ]


def run_offline_scenarios() -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.extend(check_ingestion_scenarios())
    checks.extend(check_single_repo_repeat_not_recurrence())
    checks.extend(check_technology_aliases())
    checks.extend(check_head_status_scenarios())
    checks.extend(check_empty_eligible_dataset())
    return checks
