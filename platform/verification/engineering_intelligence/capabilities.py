"""Capability Comparison and Assessment-Head Distribution verification."""

from __future__ import annotations

from verification.engineering_intelligence.contract import UNSUPPORTED_SCORE_FRAGMENTS
from verification.engineering_intelligence.ingestion import PipelineArtifacts
from verification.engineering_intelligence.models import CheckResult


def check_capabilities(pipeline: PipelineArtifacts) -> list[CheckResult]:
    report = pipeline.report
    comps = report.capability_comparisons or ()
    heads = report.assessment_head_distributions or ()
    checks: list[CheckResult] = [
        CheckResult(
            name="capability:comparisons_present",
            ok=len(comps) > 0,
            detail=f"count={len(comps)}",
            category="capability",
        ),
        CheckResult(
            name="capability:head_distributions_present",
            ok=len(heads) > 0,
            detail=f"count={len(heads)}",
            category="capability",
        ),
    ]
    blob = str(pipeline.report_payload).lower()
    banned = [frag for frag in UNSUPPORTED_SCORE_FRAGMENTS if frag in blob]
    # "ranking" may appear in methodology disclaimers — only hard-fail absolute score phrases.
    hard = [
        f
        for f in banned
        if f
        in {
            "maturity score",
            "health score",
            "readiness score",
            "composite score",
            "best repository",
            "worst repository",
        }
    ]
    checks.append(
        CheckResult(
            name="capability:no_rank_maturity_health",
            ok=not hard,
            detail=f"hits={hard}" if hard else "ok",
            category="capability",
            scenario="N",
        )
    )

    # Zero findings must not become healthy.
    healthy_inference = "healthy" in blob and "zero finding" in blob
    checks.append(
        CheckResult(
            name="capability:zero_findings_not_healthy",
            ok=not healthy_inference,
            detail="no zero→healthy inference",
            category="capability",
        )
    )
    return checks
