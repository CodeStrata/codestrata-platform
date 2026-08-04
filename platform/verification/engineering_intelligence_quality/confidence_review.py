"""Report confidence and limitation reviews."""

from __future__ import annotations

from typing import Any

from verification.engineering_intelligence_quality.contract import (
    KNOWN_ISSUES_REPOS,
    SUBMODULE_LIMITATION_REPOS,
)
from verification.engineering_intelligence_quality.models import (
    DefectCandidate,
    EditorialObservation,
)


def review_confidence(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], list[EditorialObservation], list[DefectCandidate]]:
    observations: list[EditorialObservation] = []
    defects: list[DefectCandidate] = []
    conf = payload.get("confidence") or {}
    blob = str(conf).lower()
    if isinstance(conf, dict):
        for key in ("score", "average", "percentage", "numeric_score"):
            if key in conf and isinstance(conf.get(key), (int, float)):
                defects.append(
                    DefectCandidate(
                        classification="report_confidence",
                        statement=f"numeric confidence field present: {key}",
                        section="confidence",
                        release_impact="blocking",
                        recommended_handling="SV.13_product_fix",
                    )
                )
    if "accuracy" in blob and "not" not in blob:
        defects.append(
            DefectCandidate(
                classification="report_confidence",
                statement="confidence presented as product accuracy",
                section="confidence",
                release_impact="blocking",
                recommended_handling="SV.13_product_fix",
            )
        )
    level = ""
    if isinstance(conf, dict):
        level = str(conf.get("level") or conf.get("confidence_level") or "")
    observations.append(
        EditorialObservation(
            observation_id="confidence-presentation",
            section="confidence",
            classification="useful",
            statement=(
                f"Report confidence level={level or 'present'}; "
                "expect weakest-material-support derivation without numeric averaging"
            ),
            recommended_handling="no_change",
        )
    )
    if level.lower() == "high":
        observations.append(
            EditorialObservation(
                observation_id="confidence-high-rare",
                section="confidence",
                classification="missing_context",
                statement="High confidence should be rare and justified for curated OSS snapshots",
                recommended_handling="documentation_only",
                release_impact="informational",
            )
        )
    review = {
        "ok": not any(d.release_impact == "blocking" for d in defects),
        "confidence_level": level or None,
        "summary": "Confidence reviewed for non-numeric, non-accuracy presentation",
    }
    return review, observations, defects


def review_limitations(
    payload: dict[str, Any],
    *,
    included_ids: list[str],
) -> tuple[dict[str, Any], list[EditorialObservation], list[DefectCandidate]]:
    observations: list[EditorialObservation] = []
    defects: list[DefectCandidate] = []
    limitations = payload.get("limitations") or []
    if not isinstance(limitations, list):
        limitations = []
    texts = []
    for item in limitations:
        if isinstance(item, dict):
            texts.append(str(item.get("statement") or item.get("text") or item.get("title") or ""))
        else:
            texts.append(str(item))
    blob = " ".join(texts).lower()

    required = [
        ("curated", "curated dataset"),
        ("benchmark", "not an industry benchmark / no benchmark claim"),
        ("pinned", "pinned revisions"),
    ]
    for needle, label in required:
        if needle not in blob:
            observations.append(
                EditorialObservation(
                    observation_id=f"lim-missing-{needle}",
                    section="limitations",
                    classification="limitation_needed",
                    statement=f"Limitation theme may be missing or weakly worded: {label}",
                    recommended_handling="documentation_only",
                    release_impact="minor",
                )
            )

    if set(included_ids) & KNOWN_ISSUES_REPOS:
        if not any(x in blob for x in ("vulnerable", "intentionally", "demo", "known")):
            observations.append(
                EditorialObservation(
                    observation_id="lim-known-issues",
                    section="limitations",
                    classification="limitation_needed",
                    statement="Disclose intentionally vulnerable/demo repositories in limitations",
                    repository_scope=sorted(set(included_ids) & KNOWN_ISSUES_REPOS),
                    recommended_handling="documentation_only",
                    release_impact="material",
                    customer_impact="material",
                )
            )

    if set(included_ids) & SUBMODULE_LIMITATION_REPOS:
        if "submodule" not in blob:
            observations.append(
                EditorialObservation(
                    observation_id="lim-submodules",
                    section="limitations",
                    classification="limitation_needed",
                    statement="aspnetcore/doris submodule-not-initialized should remain visible",
                    repository_scope=sorted(set(included_ids) & SUBMODULE_LIMITATION_REPOS),
                    recommended_handling="documentation_only",
                    release_impact="material",
                )
            )

    if len(limitations) > 40:
        observations.append(
            EditorialObservation(
                observation_id="lim-boilerplate",
                section="limitations",
                classification="excessive_detail",
                statement=f"{len(limitations)} limitations may overwhelm conclusions",
                recommended_handling="post_v0.2.0_enhancement",
            )
        )

    # Privacy: no absolute paths in limitations
    if "/users/" in blob or "/home/" in blob or "file://" in blob:
        defects.append(
            DefectCandidate(
                classification="dataset_limitation",
                statement="limitation text contains path-like markers",
                section="limitations",
                release_impact="blocking",
                recommended_handling="SV.13_product_fix",
            )
        )

    review = {
        "ok": not any(d.release_impact == "blocking" for d in defects),
        "limitation_count": len(limitations),
        "summary": "Limitations reviewed for mandatory themes and privacy",
    }
    return review, observations, defects
