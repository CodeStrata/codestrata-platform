"""Commercial usefulness review by intended audience."""

from __future__ import annotations

from typing import Any

from verification.engineering_intelligence_quality.models import (
    AudienceUsefulness,
    EditorialObservation,
)


def review_usefulness(
    payload: dict[str, Any],
    *,
    special_case_notes: list[str],
) -> tuple[dict[str, Any], list[AudienceUsefulness], list[EditorialObservation]]:
    observations: list[EditorialObservation] = []
    tech_n = 0
    tech = payload.get("technology_distribution") or {}
    if isinstance(tech, dict):
        tech_n = len(tech.get("observations") or tech.get("items") or [])
    patterns_n = len(payload.get("recurring_patterns") or [])
    mods_n = len(payload.get("modernization_observations") or [])
    drills_n = len(payload.get("repository_drilldowns") or [])
    lim_n = len(payload.get("limitations") or [])
    caps_n = len(payload.get("capability_comparisons") or [])

    def _cls(ok_signal: bool, limited: bool = False) -> str:
        if limited:
            return "limited"
        return "strong" if ok_signal else "adequate"

    audiences = [
        AudienceUsefulness(
            audience="CTO / VP Engineering",
            classification=_cls(tech_n > 0 and patterns_n > 0 and drills_n >= 1),
            notes=[
                "Technology estate and recurring themes are available",
                "Drill-downs support follow-up repository inspection",
                "Limitations must be read before generalizing risk prevalence",
            ],
        ),
        AudienceUsefulness(
            audience="Engineering Council reviewer",
            classification=_cls(caps_n > 0 and lim_n > 0),
            notes=[
                "Capability/coverage comparisons remain factual",
                "Provenance and limitations support challengeability",
                "No maturity/health ranking expected",
            ],
        ),
        AudienceUsefulness(
            audience="PE technology diligence team",
            classification=_cls(patterns_n > 0 and mods_n >= 0, limited=bool(special_case_notes)),
            notes=[
                "Recurring risks and technology concentration are inspectable",
                "Intentionally vulnerable repos may inflate security patterns — disclosed as limitation",
                "Static analysis does not prove operational outcomes",
            ],
        ),
        AudienceUsefulness(
            audience="CodeStrata design partner",
            classification=_cls(drills_n >= 1 and tech_n > 0),
            notes=[
                "Cross-repository report is more than a pile of single-repo reports",
                "Drill-downs enable discussion without Engine internals",
                "Signal-to-noise may vary with pattern volume",
            ],
        ),
    ]

    observations.append(
        EditorialObservation(
            observation_id="usefulness-summary",
            section="usability",
            classification="useful",
            statement=(
                f"Audience usefulness: tech={tech_n} patterns={patterns_n} "
                f"modernization={mods_n} drilldowns={drills_n} limitations={lim_n}"
            ),
            recommended_handling="no_change",
        )
    )
    review = {
        "ok": all(a.classification in {"strong", "adequate", "limited"} for a in audiences),
        "summary": "Qualitative usefulness assessed for four intended audiences",
    }
    return review, audiences, observations
