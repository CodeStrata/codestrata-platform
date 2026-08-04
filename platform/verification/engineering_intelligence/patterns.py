"""Recurring Intelligence Pattern verification."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.infrastructure.assessment_report_source import (
    InMemoryAssessmentReportSource,
)

from verification.engineering_intelligence.fixtures import make_public_input, synthetic_report
from verification.engineering_intelligence.ingestion import (
    PipelineArtifacts,
    build_pipeline_from_inputs,
)
from verification.engineering_intelligence.models import CheckResult


def check_patterns(pipeline: PipelineArtifacts) -> list[CheckResult]:
    patterns = pipeline.report.recurring_patterns or ()
    included = len(pipeline.ingest_result.dataset.included_repository_ids)
    checks: list[CheckResult] = []
    if included < 2:
        checks.append(
            CheckResult(
                name="patterns:empty_when_single_repo",
                ok=len(patterns) == 0,
                detail=f"patterns={len(patterns)} repos={included}",
                category="patterns",
                scenario="B",
            )
        )
    else:
        # When patterns exist, each must cite >= 2 repositories.
        bad = []
        for pattern in patterns:
            repos = getattr(pattern, "repository_ids", None) or getattr(
                pattern, "supporting_repository_ids", ()
            )
            if repos is not None and len(set(repos)) < 2:
                bad.append(getattr(pattern, "pattern_id", "?"))
        checks.append(
            CheckResult(
                name="patterns:min_two_repositories",
                ok=not bad,
                detail=f"patterns={len(patterns)} bad={len(bad)}",
                category="patterns",
                scenario="O",
            )
        )
    checks.append(
        CheckResult(
            name="patterns:no_portfolio_recommendation",
            ok=not any(
                hasattr(p, "recommendation_id") and getattr(p, "recommendation_id")
                for p in patterns
            ),
            detail="patterns remain observational",
            category="patterns",
        )
    )
    return checks


def check_single_repo_repeat_not_recurrence() -> list[CheckResult]:
    """Scenario C/O: repeated findings in one repository do not establish recurrence."""

    report = synthetic_report(rule_id="rule.shared")
    # Duplicate finding ids would fail traceability; use one finding with same rule only.
    inputs = [
        make_public_input(
            repository_id="repo:solo",
            assessment_id="assessment:solo",
            assessment_run_id="run:solo",
            report=report,
            pinned_revision="dddddddddddddddddddddddddddddddddddddddd",
        )
    ]
    source = InMemoryAssessmentReportSource()
    for item in inputs:
        if item.report_reference and item.report_document is not None:
            source.put(item.report_reference, item.report_document)
    pipeline = build_pipeline_from_inputs(inputs, report_source=source, title="solo")
    return [
        CheckResult(
            name="scenario:B_single_repo_no_recurrence",
            ok=len(pipeline.report.recurring_patterns or ()) == 0,
            detail=f"patterns={len(pipeline.report.recurring_patterns or ())}",
            category="scenario",
            scenario="B",
        )
    ]
