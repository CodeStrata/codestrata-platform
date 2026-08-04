"""Repository drill-down and provenance reviews."""

from __future__ import annotations

from typing import Any

from verification.engineering_intelligence_quality.contract import TARGET_REPOSITORY_COUNT
from verification.engineering_intelligence_quality.models import (
    DefectCandidate,
    EditorialObservation,
)


def review_drilldowns(
    payload: dict[str, Any],
    *,
    expected_ids: list[str],
) -> tuple[dict[str, Any], list[EditorialObservation], list[DefectCandidate]]:
    observations: list[EditorialObservation] = []
    defects: list[DefectCandidate] = []
    drills = payload.get("repository_drilldowns") or []
    if not isinstance(drills, list):
        drills = []
    ids = [
        str(d.get("repository_id") or "").removeprefix("repo:")
        for d in drills
        if isinstance(d, dict)
    ]
    ids = [i for i in ids if i]
    missing = sorted(set(expected_ids) - set(ids))
    if len(ids) != TARGET_REPOSITORY_COUNT or set(ids) != set(expected_ids):
        defects.append(
            DefectCandidate(
                classification="repository_drilldown",
                statement=(
                    f"drill-downs cover {len(ids)}/{TARGET_REPOSITORY_COUNT} repositories; "
                    f"missing={missing}"
                ),
                section="repository_drilldowns",
                repository_scope=missing,
                expected=str(sorted(expected_ids)),
                actual=str(sorted(ids)),
                release_impact="blocking",
                recommended_handling="SV.13_product_fix",
            )
        )
    for d in drills:
        if not isinstance(d, dict):
            continue
        blob = str(d).lower()
        for bad in ("evidence_body", "source_snippet", "graph_payload", "/users/", "file://"):
            if bad in blob:
                defects.append(
                    DefectCandidate(
                        classification="repository_drilldown",
                        statement=f"unsafe field/marker in drill-down: {bad}",
                        section="repository_drilldowns",
                        affected_entity_ids=[str(d.get("repository_id") or "")],
                        release_impact="blocking",
                        recommended_handling="SV.13_product_fix",
                    )
                )
    observations.append(
        EditorialObservation(
            observation_id="drilldown-bounded",
            section="repository_drilldowns",
            classification="useful",
            statement=f"{len(drills)} drill-downs; bounded refs expected without Evidence bodies",
            recommended_handling="no_change",
        )
    )
    review = {
        "ok": not any(d.release_impact == "blocking" for d in defects),
        "drilldown_count": len(drills),
        "summary": "Drill-downs reviewed for membership, safety, and bounded refs",
    }
    return review, observations, defects


def review_provenance(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[EditorialObservation], list[DefectCandidate]]:
    observations: list[EditorialObservation] = []
    defects: list[DefectCandidate] = []

    # Patterns: repository refs + identity
    for item in payload.get("recurring_patterns") or []:
        if not isinstance(item, dict):
            continue
        repos = item.get("repository_ids") or item.get("supporting_repository_ids") or []
        identity = item.get("rule_id") or item.get("provider_id") or item.get("identity")
        if repos and not identity:
            observations.append(
                EditorialObservation(
                    observation_id=f"prov-pattern-{item.get('pattern_id') or 'x'}",
                    section="provenance",
                    classification="insufficient_support",
                    statement="Pattern lacks explicit rule/provider identity field in payload",
                    recommended_handling="documentation_only",
                )
            )

    for item in payload.get("modernization_observations") or []:
        if not isinstance(item, dict):
            continue
        recs = item.get("supporting_recommendation_ids") or item.get("recommendation_ids") or []
        if not recs:
            defects.append(
                DefectCandidate(
                    classification="provenance",
                    statement="modernization observation missing recommendation provenance",
                    section="provenance",
                    affected_entity_ids=[str(item.get("observation_id") or "")],
                    release_impact="blocking",
                    recommended_handling="SV.13_product_fix",
                )
            )

    observations.append(
        EditorialObservation(
            observation_id="prov-summary",
            section="provenance",
            classification="useful",
            statement="Provenance chains reviewed structurally against payload fields",
            recommended_handling="no_change",
        )
    )
    review = {
        "ok": not any(d.release_impact == "blocking" for d in defects),
        "summary": "Provenance reviewed for pattern/modernization support identities",
    }
    return review, observations, defects
