#!/usr/bin/env python3
"""Dogfood Phase 5.10 modernization roadmap on three repository profiles.

Uses synthetic findings/recommendations approximating CodeStrata, Spring
Petclinic, and synthetic-multilang. Does not re-run assessments.
"""

from __future__ import annotations

import json
from pathlib import Path

from aimf.application.roadmap import (
    ModernizationRoadmapEngine,
    RoadmapSourceFinding,
    RoadmapSourceRecommendation,
)
from aimf.reporting.roadmap.adapter import RoadmapReportAdapter

PROFILES: dict[str, dict[str, object]] = {
    "codestrata": {
        "recommendations": [
            ("cs-test", "Expand graph rule tests", "testing", "high", ("f-cs-test",), 3),
            ("cs-sec", "Tighten secret hygiene", "security", "critical", ("f-cs-sec",), 2),
            ("cs-arch", "Reduce cross-module coupling", "architecture", "high", ("f-cs-arch",), 4),
            ("cs-dep", "Align dependency declarations", "dependency", "medium", ("f-cs-dep",), 2),
            ("cs-perf", "Trim hot-path diagnostics", "performance", "low", ("f-cs-perf",), 1),
        ],
        "findings": [
            ("f-cs-test", "testing", "medium"),
            ("f-cs-sec", "security", "high"),
            ("f-cs-arch", "architecture", "medium"),
            ("f-cs-dep", "dependency", "low"),
            ("f-cs-perf", "performance", "low"),
        ],
    },
    "spring-petclinic": {
        "recommendations": [
            ("pc-build", "Keep Maven wrapper current", "build", "medium", ("f-pc-build",), 1),
            ("pc-test", "Stabilize controller tests", "testing", "high", ("f-pc-test",), 2),
            ("pc-dep", "Review Spring Boot starters", "dependency", "medium", ("f-pc-dep",), 3),
            ("pc-mod", "Modernize persistence patterns", "modernization", "medium", ("f-pc-mod",), 5),
        ],
        "findings": [
            ("f-pc-build", "build", "low"),
            ("f-pc-test", "testing", "medium"),
            ("f-pc-dep", "dependency", "medium"),
            ("f-pc-mod", "modernization", "medium"),
        ],
    },
    "synthetic-multilang": {
        "recommendations": [
            ("ml-docs", "Add root language README", "documentation", "low", ("f-ml-docs",), 1),
            ("ml-gov", "Declare CODEOWNERS", "governance", "medium", (), 1),
            ("ml-cloud", "Containerize services", "cloud", "high", ("f-ml-cloud",), 4),
        ],
        "findings": [
            ("f-ml-docs", "documentation", "informational"),
            ("f-ml-cloud", "cloud", "medium"),
        ],
    },
}


def _build(
    profile: str,
) -> tuple[list[RoadmapSourceRecommendation], list[RoadmapSourceFinding]]:
    data = PROFILES[profile]
    recommendations = [
        RoadmapSourceRecommendation(
            id=rec_id,
            title=title,
            summary=title,
            priority=priority,
            category=category,
            related_finding_ids=findings,
            action_count=actions,
        )
        for rec_id, title, category, priority, findings, actions in data["recommendations"]  # type: ignore[misc]
    ]
    findings = [
        RoadmapSourceFinding(
            id=finding_id,
            title=finding_id,
            category=category,
            severity=severity,
        )
        for finding_id, category, severity in data["findings"]  # type: ignore[misc]
    ]
    return recommendations, findings


def main() -> None:
    engine = ModernizationRoadmapEngine()
    adapter = RoadmapReportAdapter()
    out: dict[str, object] = {}
    for profile in sorted(PROFILES):
        recs, findings = _build(profile)
        first = engine.generate(recommendations=recs, findings=findings)
        second = engine.generate(
            recommendations=list(reversed(recs)),
            findings=list(reversed(findings)),
        )
        assert first.model_dump(mode="json") == second.model_dump(mode="json")
        report = adapter.adapt(first)
        out[profile] = {
            "status": report.status,
            "phase_count": len(report.phases),
            "initiative_count": report.initiatives_total,
            "phases": [item.phase for item in report.phases],
            "initiative_ids": [item.initiative_id for item in report.initiatives],
            "deterministic": True,
        }
        print(
            f"{profile}: status={report.status} phases={len(report.phases)} "
            f"initiatives={report.initiatives_total}"
        )
    target = Path("reports/dogfood-phase-5-10-roadmap.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
