"""Dataset population and scope review."""

from __future__ import annotations

from typing import Any

from verification.engineering_intelligence_quality.contract import (
    KNOWN_ISSUES_REPOS,
    SUBMODULE_LIMITATION_REPOS,
    TARGET_REPOSITORY_COUNT,
)
from verification.engineering_intelligence_quality.models import (
    DefectCandidate,
    EditorialObservation,
)


def review_dataset(
    payload: dict[str, Any],
    *,
    expected_ids: list[str],
    sv10_limitations: dict[str, list[str]],
) -> tuple[dict[str, Any], list[EditorialObservation], list[DefectCandidate]]:
    observations: list[EditorialObservation] = []
    defects: list[DefectCandidate] = []

    population = payload.get("repository_population") or {}
    dataset = payload.get("dataset") or {}
    included_norm: list[str] = []
    if isinstance(population, dict):
        raw_ids = population.get("included_repository_ids") or []
        if isinstance(raw_ids, list) and raw_ids:
            included_norm = [str(i).removeprefix("repo:") for i in raw_ids if i]
        count_field = population.get("repository_count")
    else:
        count_field = None
    if not included_norm and isinstance(population, dict):
        included_norm = [
            str(r.get("repository_id") or r.get("id") or "").removeprefix("repo:")
            for r in (population.get("repositories") or population.get("items") or [])
            if isinstance(r, dict)
        ]
    if not included_norm and isinstance(dataset, dict):
        included_norm = [
            str(r.get("repository_id") or r.get("id") or "").removeprefix("repo:")
            for r in (dataset.get("repositories") or [])
            if isinstance(r, dict)
        ]
    if not included_norm:
        included_norm = [
            str(d.get("repository_id") or "").removeprefix("repo:")
            for d in (payload.get("repository_drilldowns") or [])
            if isinstance(d, dict)
        ]
    included_norm = sorted({i for i in included_norm if i})

    count_ok = len(included_norm) == TARGET_REPOSITORY_COUNT
    membership_ok = set(included_norm) == set(expected_ids)
    missing = sorted(set(expected_ids) - set(included_norm))
    if not count_ok or not membership_ok:
        defects.append(
            DefectCandidate(
                classification="data_population",
                statement=(
                    f"EIR included {len(included_norm)}/{TARGET_REPOSITORY_COUNT} repositories; "
                    f"missing={missing}"
                ),
                section="dataset",
                repository_scope=missing,
                expected=f"{TARGET_REPOSITORY_COUNT} catalog release_validation repositories",
                actual=f"included={included_norm}",
                release_impact="blocking",
                recommended_handling="SV.13_product_fix",
            )
        )

    limitations = payload.get("limitations") or []
    lim_text = " ".join(
        str(x.get("statement") or x.get("text") or x if isinstance(x, str) else x)
        for x in limitations
    ).lower()

    required_themes = [
        ("curated", "curated dataset"),
        ("benchmark", "not an industry benchmark"),
        ("pinned", "pinned revisions"),
    ]
    for needle, label in required_themes:
        if needle not in lim_text and label.split()[0] not in lim_text:
            observations.append(
                EditorialObservation(
                    observation_id=f"dataset-limitation-{needle}",
                    section="dataset",
                    classification="limitation_needed",
                    statement=f"Expected limitation theme not clearly visible: {label}",
                    recommended_handling="documentation_only",
                    release_impact="minor",
                )
            )

    # Known Issues disclosure
    if not any(r in lim_text for r in ("vulnerable", "known issues", "intentionally", "demo")):
        # Check if any known-issues repo is in dataset — should disclose
        if set(included_norm) & KNOWN_ISSUES_REPOS:
            observations.append(
                EditorialObservation(
                    observation_id="dataset-known-issues-disclosure",
                    section="dataset",
                    classification="limitation_needed",
                    statement=(
                        "Intentionally vulnerable/demo repositories are included; "
                        "ensure dataset limitations disclose that risk prevalence "
                        "is not representative of ordinary software."
                    ),
                    repository_scope=sorted(set(included_norm) & KNOWN_ISSUES_REPOS),
                    recommended_handling="documentation_only",
                    customer_impact="material",
                    release_impact="material",
                )
            )

    for rid in sorted(set(included_norm) & SUBMODULE_LIMITATION_REPOS):
        notes = " ".join(sv10_limitations.get(rid) or []).lower()
        if "submodule" in notes:
            observations.append(
                EditorialObservation(
                    observation_id=f"dataset-submodule-{rid}",
                    section="dataset",
                    classification="useful",
                    statement=f"{rid}: submodule-not-initialized limitation retained from SV.10",
                    repository_scope=[rid],
                    recommended_handling="no_change",
                )
            )

    # Forbidden implications in executive summary / methodology
    blob = " ".join(
        str(payload.get(k) or "")
        for k in ("executive_summary", "methodology", "title")
    ).lower()
    for phrase in (
        "all open-source software",
        "industry trends",
        "market-wide",
        "product-wide accuracy",
    ):
        if phrase in blob and "not" not in blob:
            defects.append(
                DefectCandidate(
                    classification="wording",
                    statement=f"possible over-claim: {phrase}",
                    section="dataset",
                    release_impact="material",
                    recommended_handling="SV.13_product_fix",
                )
            )

    review = {
        "ok": not any(d.release_impact == "blocking" for d in defects),
        "repository_count": len(set(included_norm)),
        "included_repository_ids": sorted(set(included_norm)),
        "reconciles_with_catalog": membership_ok,
        "schema_version": payload.get("schema_version"),
        "report_scope": payload.get("report_scope"),
        "summary": (
            "Dataset population reconciles with 22 curated pinned repositories"
            if membership_ok
            else "Dataset population mismatch"
        ),
    }
    return review, observations, defects
