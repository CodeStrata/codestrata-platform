"""Modernization observation editorial review."""

from __future__ import annotations

from typing import Any

from verification.engineering_intelligence_quality.models import (
    DefectCandidate,
    EditorialObservation,
)

_FORBIDDEN = (
    "roi",
    "will save",
    "exact cost",
    "staffing plan",
    "rewrite required",
    "migration required",
    "guaranteed",
    "timeline:",
)


def review_modernization(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[EditorialObservation], list[DefectCandidate]]:
    observations: list[EditorialObservation] = []
    defects: list[DefectCandidate] = []
    items = payload.get("modernization_observations") or []
    if not isinstance(items, list):
        items = []

    for item in items:
        if not isinstance(item, dict):
            continue
        oid = str(item.get("observation_id") or item.get("id") or "")
        repos = [
            str(r).removeprefix("repo:")
            for r in (item.get("repository_ids") or item.get("supporting_repository_ids") or [])
        ]
        if len(set(repos)) < 2:
            defects.append(
                DefectCandidate(
                    classification="modernization_observation",
                    statement="observation supported by fewer than two repositories",
                    section="modernization_observations",
                    affected_entity_ids=[oid],
                    repository_scope=repos,
                    release_impact="blocking",
                    recommended_handling="SV.13_product_fix",
                )
            )
        recs = item.get("supporting_recommendation_ids") or item.get("recommendation_ids") or []
        if not recs:
            defects.append(
                DefectCandidate(
                    classification="modernization_observation",
                    statement="observation missing Recommendation support",
                    section="modernization_observations",
                    affected_entity_ids=[oid],
                    release_impact="blocking",
                    recommended_handling="SV.13_product_fix",
                )
            )
        statement = str(item.get("statement") or item.get("title") or "").lower()
        for frag in _FORBIDDEN:
            if frag in statement:
                defects.append(
                    DefectCandidate(
                        classification="modernization_observation",
                        statement=f"unsupported modernization language: {frag}",
                        section="modernization_observations",
                        affected_entity_ids=[oid],
                        release_impact="blocking",
                        recommended_handling="SV.13_product_fix",
                    )
                )
        # Imperative check — soft editorial
        if statement.startswith(("implement ", "migrate ", "rewrite ", "must ")):
            observations.append(
                EditorialObservation(
                    observation_id=f"mod-imperative-{oid or 'x'}",
                    section="modernization_observations",
                    classification="terminology_issue",
                    statement="Observation wording appears imperative rather than observational",
                    affected_entity_ids=[oid],
                    recommended_handling="documentation_only",
                )
            )

    # Ensure no portfolio Recommendation/PA/roadmap entity collections exist.
    if payload.get("portfolio_recommendations") or payload.get("portfolio_priority_actions"):
        defects.append(
            DefectCandidate(
                classification="modernization_observation",
                statement="portfolio Recommendation/PA entity must not be created",
                section="modernization_observations",
                release_impact="blocking",
                recommended_handling="SV.13_product_fix",
            )
        )
    if payload.get("portfolio_roadmap") or payload.get("portfolio_roadmaps"):
        defects.append(
            DefectCandidate(
                classification="modernization_observation",
                statement="portfolio roadmap entity must not be created",
                section="modernization_observations",
                release_impact="blocking",
                recommended_handling="SV.13_product_fix",
            )
        )

    observations.append(
        EditorialObservation(
            observation_id="mod-summary",
            section="modernization_observations",
            classification="useful" if items else "unclear",
            statement=f"{len(items)} modernization observations; Recommendation-backed observational themes only",
            recommended_handling="no_change",
        )
    )
    review = {
        "ok": not any(d.release_impact == "blocking" for d in defects),
        "observation_count": len(items),
        "summary": "Modernization observations reviewed for Recommendation support and non-imperative scope",
    }
    return review, observations, defects
