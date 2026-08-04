"""Wording and unsupported commercial claim review."""

from __future__ import annotations

import re
from typing import Any

from verification.engineering_intelligence_quality.contract import (
    AFFIRMATIVE_CLAIM_PATTERNS,
    UNSUPPORTED_COMMERCIAL_CLAIMS,
)
from verification.engineering_intelligence_quality.models import (
    DefectCandidate,
    EditorialObservation,
)


def _pre_negated(pre: str) -> bool:
    return any(
        n in pre
        for n in (
            "not an ",
            "not a ",
            "are not ",
            "is not ",
            "do not ",
            "does not ",
            "must not ",
            "without ",
            "never ",
            "avoid ",
            "not create ",
            "do_not_",
            "observations_do_not_",
            "not portfolio",
            "not treat",
            "unless ",
        )
    )


def review_wording(
    *,
    json_text: str,
    html_text: str,
) -> tuple[dict[str, Any], list[EditorialObservation], list[DefectCandidate]]:
    observations: list[EditorialObservation] = []
    defects: list[DefectCandidate] = []
    combined = f"{json_text}\n{html_text}"
    lowered = combined.lower()

    for frag in UNSUPPORTED_COMMERCIAL_CLAIMS:
        idx = 0
        while True:
            idx = lowered.find(frag, idx)
            if idx < 0:
                break
            pre = lowered[max(0, idx - 48) : idx]
            list_pre = lowered[max(0, idx - 120) : idx]
            # "are not A, B, roi claims, or C" — treat list members as disallowed claims.
            if "are not " in list_pre or "is not " in list_pre or "not " in pre or "no " in pre:
                idx += len(frag)
                continue
            if _pre_negated(pre):
                idx += len(frag)
                continue
            defects.append(
                DefectCandidate(
                    classification="wording",
                    statement=f"unsupported commercial language: {frag}",
                    section="wording",
                    release_impact="blocking"
                    if frag
                    in {
                        "industry benchmark",
                        "maturity score",
                        "health score",
                        "product-wide accuracy",
                        "product wide accuracy",
                    }
                    else "material",
                    recommended_handling="SV.13_product_fix",
                )
            )
            break

    for name, pattern in AFFIRMATIVE_CLAIM_PATTERNS:
        for match in re.finditer(pattern, combined):
            pre = combined[max(0, match.start() - 48) : match.start()].lower()
            if _pre_negated(pre) or "not " in pre:
                continue
            defects.append(
                DefectCandidate(
                    classification="wording",
                    statement=f"affirmative claim matched: {name}",
                    section="wording",
                    release_impact="blocking",
                    recommended_handling="SV.13_product_fix",
                )
            )
            break

    scoped = sum(
        1
        for phrase in (
            "within this dataset",
            "eligible repositories",
            "does not establish",
            "pinned",
            "not an industry benchmark",
            "industry benchmarks",
        )
        if phrase in lowered
    )
    observations.append(
        EditorialObservation(
            observation_id="wording-dataset-scope",
            section="wording",
            classification="useful" if scoped else "missing_context",
            statement=f"Dataset-scoped / disclaimer wording markers found≈{scoped}",
            recommended_handling="no_change" if scoped else "documentation_only",
        )
    )
    review = {
        "ok": not any(d.release_impact == "blocking" for d in defects),
        "unsupported_claim_hits": len([d for d in defects if d.classification == "wording"]),
        "summary": "Wording scanned for unsupported commercial claims (disclaimer-aware)",
    }
    return review, observations, defects
