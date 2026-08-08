"""Synthetic Assessment report fixtures for Slice 14.3 verification (no customer data)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from codestrata.domain.findings import Finding as Phase3Finding
from codestrata.domain.findings import FindingCategory, FindingSeverity, RuleEvaluationResult
from codestrata.domain.recommendations import (
    Recommendation as Phase3Recommendation,
)
from codestrata.domain.recommendations import (
    RecommendationAction,
    RecommendationCategory,
    RecommendationPriority,
    RecommendationResult,
)
from codestrata.models import (
    AnalysisResult,
    Finding,
    FindingSource,
    Repository,
    RepositoryFacts,
    Severity,
    StructureFacts,
    Technology,
    TechnologyCategory,
)
from codestrata.models import (
    FindingCategory as Phase1FindingCategory,
)
from codestrata.reporting.html_v2 import default_report_artifacts
from codestrata.reporting.modernization_models import (
    AIExecutionStatus,
    AssessmentMode,
    HighlightedVersionInput,
    ModernizationReportInput,
)


def synthetic_report_input(tmp_path: Path) -> ModernizationReportInput:
    """Deterministic synthetic assessment input for presentation verification."""

    analysis = AnalysisResult(
        repository=Repository(
            name="sv143-fixture",
            path=tmp_path / "sv143-fixture",
            files=["README.md", "src/main.java"],
            total_files=2,
        ),
        technologies=[
            Technology(
                name="Java",
                category=TechnologyCategory.LANGUAGE,
                confidence=1.0,
                source="test",
                version="17",
            )
        ],
        facts=RepositoryFacts(
            structure=StructureFacts(file_count=2, source_file_count=1, test_file_count=0)
        ),
        findings=[
            Finding(
                rule_id="SEC001",
                title="Credential hygiene signal",
                description="Synthetic critical finding for presentation coverage.",
                category=Phase1FindingCategory.SECURITY,
                severity=Severity.CRITICAL,
                source=FindingSource.DETERMINISTIC,
                evidence=[],
            )
        ],
    )
    finding = Phase3Finding.create(
        rule_id="missing-lockfile",
        title="Missing lockfile",
        description="No package-lock.json",
        severity=FindingSeverity.HIGH,
        category=FindingCategory.DEPENDENCY,
    )
    evaluation = RuleEvaluationResult.from_findings(
        findings=[finding],
        rules_evaluated=["missing-lockfile"],
    )
    recommendation = Phase3Recommendation.create(
        provider_id="builtin:lockfile",
        title="Add a lockfile",
        summary="Commit a lockfile for reproducible installs.",
        rationale="Finding indicates missing lockfile.",
        priority=RecommendationPriority.HIGH,
        category=RecommendationCategory.DEPENDENCY,
        related_finding_ids=[finding.id],
        actions=[
            RecommendationAction(
                order=1,
                title="Generate lockfile",
                description="Run the package manager install command.",
            )
        ],
    )
    recommendations = RecommendationResult.from_recommendations(
        recommendations=[recommendation],
        providers_evaluated=["builtin:lockfile"],
    )
    return ModernizationReportInput(
        analysis_result=analysis,
        assessment_mode=AssessmentMode.DETERMINISTIC,
        ai_status=AIExecutionStatus.NOT_REQUESTED,
        generated_at_utc=datetime(2026, 7, 22, 12, 0, tzinfo=UTC),
        report_title="Engineering Assessment",
        assessment_rule_evaluation=evaluation,
        assessment_recommendation_result=recommendations,
        ai_enrichment=None,
        highlighted_versions=(
            HighlightedVersionInput(label="Java language level", value="17", kind="runtime"),
        ),
        report_artifacts=default_report_artifacts(
            include_ai_enrichment=False,
            include_ai_execution=False,
        ),
        assessment_activation={
            "mode": "default",
            "packs": [
                {
                    "pack_id": "security",
                    "enabled": True,
                    "decision": "enabled",
                    "reason": "Security hygiene is enabled by default",
                    "evidence": [],
                },
                {
                    "pack_id": "performance",
                    "enabled": False,
                    "decision": "skipped",
                    "reason": "Performance remains opt-in under default activation",
                    "evidence": [],
                },
            ],
        },
    )
