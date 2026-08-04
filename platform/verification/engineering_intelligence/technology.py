"""Technology Distribution verification."""

from __future__ import annotations

from codestrata_platform.intelligence_reporting.application.technology_distribution import (
    normalize_technology_name,
)

from verification.engineering_intelligence.ingestion import PipelineArtifacts
from verification.engineering_intelligence.models import CheckResult


def check_technology(pipeline: PipelineArtifacts) -> list[CheckResult]:
    report = pipeline.report
    dist = report.technology_distribution
    checks: list[CheckResult] = []
    checks.append(
        CheckResult(
            name="technology:distribution_present",
            ok=dist is not None,
            detail="TechnologyDistribution populated" if dist else "missing",
            category="technology",
        )
    )
    if dist is None:
        return checks

    observations = getattr(dist, "observations", ()) or ()
    for obs in observations:
        presence = getattr(obs, "repository_presence_count", None)
        occurrence = getattr(obs, "occurrence_count", None)
        if presence is not None and occurrence is not None and presence > occurrence:
            checks.append(
                CheckResult(
                    name="technology:presence_vs_occurrence",
                    ok=False,
                    detail=f"presence={presence} occurrence={occurrence}",
                    category="technology",
                )
            )
            break
    else:
        checks.append(
            CheckResult(
                name="technology:presence_vs_occurrence",
                ok=True,
                detail=f"observations={len(observations)}",
                category="technology",
            )
        )

    blob = str(pipeline.report_payload).lower()
    checks.append(
        CheckResult(
            name="technology:no_modern_outdated_claim",
            ok="outdated" not in blob and "fully modern" not in blob,
            detail="no modern/outdated absolute claims",
            category="technology",
        )
    )
    checks.append(
        CheckResult(
            name="technology:no_recommendations_generated",
            ok=not any(
                key in pipeline.report_payload
                for key in ("deterministic_recommendations", "priority_actions")
            ),
            detail="distribution is observational only",
            category="technology",
        )
    )
    return checks


def check_technology_aliases() -> list[CheckResult]:
    distinct_pairs = [
        ("Java", "JavaScript"),
        ("Node.js", "npm"),
        ("Spring", "Spring Boot"),
        (".NET", "ASP.NET Core"),
    ]
    alias_pairs = [
        ("nodejs", "Node.js"),
        ("spring-boot", "Spring Boot"),
        ("js", "JavaScript"),
    ]
    checks: list[CheckResult] = []
    for left, right in distinct_pairs:
        n_left, _ = normalize_technology_name(left)
        n_right, _ = normalize_technology_name(right)
        checks.append(
            CheckResult(
                name=f"scenario:L_distinct:{left}:{right}",
                ok=n_left != n_right,
                detail=f"{n_left} != {n_right}",
                category="scenario",
                scenario="L",
            )
        )
    for alias, canonical in alias_pairs:
        normalized, aliased = normalize_technology_name(alias)
        checks.append(
            CheckResult(
                name=f"scenario:L_alias:{alias}",
                ok=normalized == canonical and aliased,
                detail=f"{alias}->{normalized}",
                category="scenario",
                scenario="L",
            )
        )
    return checks
