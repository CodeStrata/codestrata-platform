"""Modernization Observation verification."""

from __future__ import annotations

from verification.engineering_intelligence.ingestion import PipelineArtifacts
from verification.engineering_intelligence.models import CheckResult

_FORBIDDEN_MODERNIZATION = (
    "delivery commitment",
    "exact cost",
    "staffing plan",
    "migration guaranteed",
)


def _flagged_absolute_claims(blob: str, fragments: tuple[str, ...]) -> list[str]:
    """Flag absolute claims while allowing explicit negations / disclaimers."""

    lowered = blob.lower()
    hits: list[str] = []
    for frag in fragments:
        start = 0
        while True:
            idx = lowered.find(frag, start)
            if idx < 0:
                break
            window = lowered[max(0, idx - 40) : idx]
            if any(
                marker in window
                for marker in ("not ", "no ", "never ", "without ", "are not", "is not")
            ):
                start = idx + len(frag)
                continue
            hits.append(frag)
            break
    return hits


def check_modernization(pipeline: PipelineArtifacts) -> list[CheckResult]:
    observations = pipeline.report.modernization_observations or ()
    included = len(pipeline.ingest_result.dataset.included_repository_ids)
    checks: list[CheckResult] = []

    if included < 2:
        checks.append(
            CheckResult(
                name="modernization:absent_without_recurrence",
                ok=len(observations) == 0,
                detail=f"observations={len(observations)}",
                category="modernization",
                scenario="B",
            )
        )
    else:
        bad_support = []
        for obs in observations:
            repos = getattr(obs, "repository_ids", ()) or ()
            recs = getattr(obs, "recommendation_ids", ()) or ()
            if len(set(repos)) < 2:
                bad_support.append("repos")
            if len(recs) < 1:
                bad_support.append("recs")
        checks.append(
            CheckResult(
                name="modernization:requires_recs_and_two_repos",
                ok=not bad_support,
                detail=f"observations={len(observations)} issues={bad_support[:5]}",
                category="modernization",
                scenario="P",
            )
        )

    blob = str(pipeline.report_payload).lower()
    hits = _flagged_absolute_claims(blob, _FORBIDDEN_MODERNIZATION)
    # Structural assurance: observations are not Recommendation entities.
    has_portfolio_rec_entity = any(
        "portfolio_recommendation_id" in str(obs).lower() for obs in observations
    )
    checks.append(
        CheckResult(
            name="modernization:no_roi_cost_portfolio_entities",
            ok=not hits and not has_portfolio_rec_entity,
            detail=f"hits={hits}" if hits or has_portfolio_rec_entity else "ok",
            category="modernization",
            scenario="P",
        )
    )
    return checks
