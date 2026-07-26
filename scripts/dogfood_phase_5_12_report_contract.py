#!/usr/bin/env python3
"""Dogfood Phase 5.12 report contract determinism across three profiles."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine" / "src"))

from codestrata.models import (  # noqa: E402
    AnalysisResult,
    Effort,
    Evidence,
    Finding,
    FindingCategory,
    FindingSource,
    Priority,
    Recommendation,
    RecommendationCategory,
    Repository,
    RepositoryFacts,
    Risk,
    Severity,
    StructureFacts,
    Technology,
    TechnologyCategory,
)
from codestrata.reporting.assessment_json import build_assessment_json_document  # noqa: E402
from codestrata.reporting.contract import reports_structurally_equal  # noqa: E402
from codestrata.reporting.html_v2.builder import build_html_report_view_model  # noqa: E402
from codestrata.reporting.html_v2.renderer import HtmlReportRenderer  # noqa: E402
from codestrata.reporting.modernization_models import (  # noqa: E402
    AssessmentMode,
    ModernizationReportInput,
)

PROFILES = {
    "codestrata": {
        "name": "codestrata",
        "languages": [("Python", "3.12")],
        "frameworks": [("Typer", None)],
        "finding": ("ARCH001", FindingCategory.ARCHITECTURE, Severity.MEDIUM),
    },
    "spring-petclinic": {
        "name": "spring-petclinic",
        "languages": [("Java", "17")],
        "frameworks": [("Spring", None)],
        "finding": ("DEP001", FindingCategory.DEPENDENCY, Severity.LOW),
    },
    "synthetic-multilang": {
        "name": "synthetic-multilang",
        "languages": [("JavaScript", None), ("Python", None)],
        "frameworks": [],
        "finding": ("DOC001", FindingCategory.OTHER, Severity.INFO),
    },
}


def _build(profile: str, *, moment: datetime) -> dict:
    cfg = PROFILES[profile]
    techs = [
        Technology(
            name=name,
            category=TechnologyCategory.LANGUAGE,
            version=version,
            confidence=1.0,
            source="dogfood",
        )
        for name, version in cfg["languages"]
    ] + [
        Technology(
            name=name,
            category=TechnologyCategory.FRAMEWORK,
            version=version,
            confidence=1.0,
            source="dogfood",
        )
        for name, version in cfg["frameworks"]
    ]
    rule_id, category, severity = cfg["finding"]
    analysis = AnalysisResult(
        repository=Repository(
            name=cfg["name"],
            path=ROOT / cfg["name"],
            default_branch="main",
            files=["README.md"],
            total_files=1,
        ),
        technologies=techs,
        facts=RepositoryFacts(
            structure=StructureFacts(file_count=1, source_file_count=1, test_file_count=0)
        ),
        findings=[
            Finding(
                rule_id=rule_id,
                title=f"{profile} finding",
                description="dogfood",
                category=category,
                severity=severity,
                source=FindingSource.DETERMINISTIC,
                evidence=[Evidence(file_path="README.md", description="root")],
            )
        ],
        recommendations=[
            Recommendation(
                rule_id=f"REC-{rule_id}",
                title=f"Address {profile}",
                description="dogfood",
                rationale="dogfood",
                priority=Priority.MEDIUM,
                category=RecommendationCategory.TESTING,
                effort=Effort.SMALL,
                risk=Risk.LOW,
                related_finding_ids=[],
                actions=["review"],
            )
        ],
    )
    report_input = ModernizationReportInput(
        analysis_result=analysis,
        assessment_mode=AssessmentMode.DETERMINISTIC,
        generated_at_utc=moment,
        knowledge_repository_id=f"repo:{profile}",
        knowledge_run_id=f"run:{profile}",
    )
    document = build_assessment_json_document(report_input)
    html = HtmlReportRenderer().render(build_html_report_view_model(report_input))
    return {"document": document, "html": html}


def main() -> None:
    out = ROOT / "reports" / "dogfood-phase-5-12"
    out.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {}
    for profile in sorted(PROFILES):
        first = _build(profile, moment=datetime(2026, 7, 25, 10, 0, tzinfo=UTC))
        second = _build(profile, moment=datetime(2026, 7, 25, 18, 0, tzinfo=UTC))
        equal = reports_structurally_equal(first["document"], second["document"])
        (out / f"{profile}.report.json").write_text(
            json.dumps(first["document"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (out / f"{profile}.report.html").write_text(first["html"], encoding="utf-8")
        summary[profile] = {
            "structurally_equal": equal,
            "schema_version": first["document"]["schema_version"],
            "has_manifest": "manifest" in first["document"],
            "finding_count": len(first["document"]["assessment"]["findings"]),
            "html_has_executive": 'id="executive"' in first["html"],
        }
        print(f"{profile}: equal={equal} manifest={summary[profile]['has_manifest']}")
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {out / 'summary.json'}")


if __name__ == "__main__":
    main()
