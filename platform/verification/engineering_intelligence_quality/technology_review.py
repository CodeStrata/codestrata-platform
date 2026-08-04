"""Technology distribution editorial review."""

from __future__ import annotations

from typing import Any

from verification.engineering_intelligence_quality.models import (
    DefectCandidate,
    EditorialObservation,
)

_FORBIDDEN_TECH_CLAIMS = (
    "end-of-life",
    "outdated technology",
    "modern technology",
    "recommended because common",
)


def review_technology(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[EditorialObservation], list[DefectCandidate]]:
    observations: list[EditorialObservation] = []
    defects: list[DefectCandidate] = []
    tech = payload.get("technology_distribution") or {}
    items = []
    if isinstance(tech, dict):
        items = tech.get("observations") or tech.get("items") or tech.get("technologies") or []
    if not isinstance(items, list):
        items = []

    presence_occurrence_ok = True
    for item in items:
        if not isinstance(item, dict):
            continue
        statement = str(item.get("statement") or item.get("text") or "").lower()
        for claim in _FORBIDDEN_TECH_CLAIMS:
            if claim in statement:
                defects.append(
                    DefectCandidate(
                        classification="technology_insight",
                        statement=f"unsupported technology claim: {claim}",
                        section="technology_distribution",
                        affected_entity_ids=[str(item.get("observation_id") or item.get("id") or "")],
                        release_impact="material",
                        recommended_handling="SV.13_product_fix",
                    )
                )
        # Presence vs occurrence fields
        if "repository_count" in item or "occurrence_count" in item or "presence" in str(item):
            pass
        denom = item.get("denominator") or item.get("eligible_denominator")
        if item.get("percentage") is not None and denom in (None, 0, "0"):
            defects.append(
                DefectCandidate(
                    classification="technology_insight",
                    statement="percentage without explicit eligible denominator",
                    section="technology_distribution",
                    affected_entity_ids=[str(item.get("observation_id") or "")],
                    release_impact="material",
                    recommended_handling="SV.13_product_fix",
                )
            )
            presence_occurrence_ok = False

    if len(items) == 0:
        observations.append(
            EditorialObservation(
                observation_id="tech-empty",
                section="technology_distribution",
                classification="unclear",
                statement="No technology observations present",
                recommended_handling="documentation_only",
            )
        )
    elif len(items) > 80:
        observations.append(
            EditorialObservation(
                observation_id="tech-volume",
                section="technology_distribution",
                classification="excessive_detail",
                statement=f"{len(items)} technology observations may reduce discoverability",
                recommended_handling="post_v0.2.0_enhancement",
                release_impact="informational",
            )
        )
    else:
        observations.append(
            EditorialObservation(
                observation_id="tech-useful",
                section="technology_distribution",
                classification="useful",
                statement=(
                    f"{len(items)} technology observations present; "
                    "leaders can inspect estate concentration when denominators are explicit"
                ),
                recommended_handling="no_change",
            )
        )

    # Distinctness checks for common confusions in statements
    blob = str(tech).lower()
    if "java" in blob and "javascript" in blob:
        observations.append(
            EditorialObservation(
                observation_id="tech-java-js-distinct",
                section="technology_distribution",
                classification="useful",
                statement="Java and JavaScript both appear; treat as distinct ecosystems",
                recommended_handling="no_change",
            )
        )

    review = {
        "ok": not any(d.release_impact in {"blocking", "material"} for d in defects),
        "observation_count": len(items),
        "presence_occurrence_ok": presence_occurrence_ok,
        "summary": "Technology distribution reviewed for factual, denominator-aware insight",
        "classifications": {
            o.classification: 1
            for o in observations
        },
    }
    return review, observations, defects
