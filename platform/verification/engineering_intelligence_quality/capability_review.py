"""Capability comparison and assessment-head distribution review."""

from __future__ import annotations

from typing import Any

from verification.engineering_intelligence_quality.models import (
    DefectCandidate,
    EditorialObservation,
)

_SCORE_FRAGMENTS = (
    "maturity score",
    "health score",
    "readiness score",
    "composite score",
    "ranking",
    "best repository",
    "worst repository",
    "healthy",
)


def review_capability(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[EditorialObservation], list[DefectCandidate]]:
    observations: list[EditorialObservation] = []
    defects: list[DefectCandidate] = []
    caps = payload.get("capability_comparisons") or []
    if not isinstance(caps, list):
        caps = []
    blob = str(caps).lower()
    for frag in _SCORE_FRAGMENTS:
        if frag in blob and "not" not in blob[max(0, blob.find(frag) - 20) : blob.find(frag)]:
            # Soft: allow "not healthy" style; flag affirmative health ranking phrases
            if frag in {"healthy"} and "not labeled healthy" in blob:
                continue
            if frag == "healthy" and "zero findings" in blob:
                defects.append(
                    DefectCandidate(
                        classification="capability_comparison",
                        statement="zero Findings must not be labeled healthy",
                        section="capability_comparison",
                        release_impact="blocking",
                        recommended_handling="SV.13_product_fix",
                    )
                )
            elif frag != "healthy":
                defects.append(
                    DefectCandidate(
                        classification="capability_comparison",
                        statement=f"unsupported score/rank language: {frag}",
                        section="capability_comparison",
                        release_impact="blocking",
                        recommended_handling="SV.13_product_fix",
                    )
                )

    observations.append(
        EditorialObservation(
            observation_id="capability-factual",
            section="capability_comparison",
            classification="useful" if caps else "unclear",
            statement=(
                f"{len(caps)} capability comparison snapshots; "
                "activation/coverage/confidence should remain separate"
            ),
            recommended_handling="no_change",
        )
    )
    review = {
        "ok": not any(d.release_impact == "blocking" for d in defects),
        "snapshot_count": len(caps),
        "summary": "Capability comparisons reviewed for absence of rank/maturity/health scores",
    }
    return review, observations, defects


def review_assessment_heads(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[EditorialObservation], list[DefectCandidate]]:
    observations: list[EditorialObservation] = []
    defects: list[DefectCandidate] = []
    heads = payload.get("assessment_head_distributions") or []
    if not isinstance(heads, list):
        heads = []
    blob = str(heads).lower()
    if "average confidence" in blob or "confidence percentage" in blob:
        defects.append(
            DefectCandidate(
                classification="assessment_head_distribution",
                statement="average/percentage confidence not allowed",
                section="assessment_head_distribution",
                release_impact="blocking",
                recommended_handling="SV.13_product_fix",
            )
        )
    if "healthy head" in blob:
        defects.append(
            DefectCandidate(
                classification="assessment_head_distribution",
                statement="healthy head conclusion from zero Findings",
                section="assessment_head_distribution",
                release_impact="blocking",
                recommended_handling="SV.13_product_fix",
            )
        )
    # Duplication vs capability — editorial only
    if heads and payload.get("capability_comparisons"):
        observations.append(
            EditorialObservation(
                observation_id="head-vs-capability-overlap",
                section="assessment_head_distribution",
                classification="redundant",
                statement=(
                    "Head distributions may overlap CapabilityComparison; "
                    "acceptable if each remains factual and non-ranking"
                ),
                recommended_handling="no_change",
                release_impact="informational",
            )
        )
    observations.append(
        EditorialObservation(
            observation_id="head-dist-present",
            section="assessment_head_distribution",
            classification="useful" if heads else "unclear",
            statement=f"{len(heads)} assessment-head distributions present",
            recommended_handling="no_change",
        )
    )
    review = {
        "ok": not defects,
        "head_count": len(heads),
        "summary": "Assessment-head distributions reviewed for non-ranking semantics",
    }
    return review, observations, defects
