"""Repository drill-down verification."""

from __future__ import annotations

from verification.engineering_intelligence.ingestion import PipelineArtifacts
from verification.engineering_intelligence.models import CheckResult


def check_drilldowns(pipeline: PipelineArtifacts) -> list[CheckResult]:
    report = pipeline.report
    dataset = pipeline.ingest_result.dataset
    included = list(dataset.included_repository_ids)
    drills = report.repository_drilldowns or ()
    checks: list[CheckResult] = [
        CheckResult(
            name="drilldown:one_per_included_repository",
            ok=len(drills) == len(included),
            detail=f"drilldowns={len(drills)} included={len(included)}",
            category="drilldown",
            scenario="R",
        )
    ]
    drill_repos = {
        getattr(item, "repository_id", None) for item in drills if getattr(item, "repository_id", None)
    }
    checks.append(
        CheckResult(
            name="drilldown:repository_set_matches",
            ok=set(included) == drill_repos,
            detail=f"drill_repos={len(drill_repos)}",
            category="drilldown",
        )
    )
    blob = str(pipeline.report_payload)
    checks.append(
        CheckResult(
            name="drilldown:no_raw_evidence_payload",
            ok='"snippet"' not in blob.lower() and "source_body" not in blob.lower(),
            detail="no evidence payloads",
            category="drilldown",
        )
    )
    return checks
