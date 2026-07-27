"""Deterministic portfolio aggregation and freshness policies."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime

from codestrata_platform.domain.engineering.enums import EngineeringCategory, EngineeringSeverity
from codestrata_platform.domain.portfolio.lifecycle import (
    AssessmentFreshnessStatus,
    ModernizationTheme,
    ModernizationWave,
    PriorityBand,
    RepositoryCriticality,
    TechnologyStandardizationStatus,
)
from codestrata_platform.domain.portfolio.snapshot import DEFAULT_AGGREGATION_POLICY_VERSION

PORTFOLIO_AGGREGATION_POLICY_VERSION = DEFAULT_AGGREGATION_POLICY_VERSION
PORTFOLIO_FRESHNESS_POLICY_VERSION = "portfolio-freshness-v1"
PORTFOLIO_STANDARDIZATION_POLICY_VERSION = "portfolio-standardization-v1"
PORTFOLIO_PRIORITY_POLICY_VERSION = "portfolio-priority-v1"
PORTFOLIO_MODERNIZATION_POLICY_VERSION = "portfolio-modernization-v1"
PORTFOLIO_AUTO_REFRESH_ENV = "CODESTRATA_PORTFOLIO_AUTO_REFRESH"


def portfolio_auto_refresh_enabled() -> bool:
    raw = os.environ.get(PORTFOLIO_AUTO_REFRESH_ENV, "false").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def priority_band(score: int) -> PriorityBand:
    clamped = max(0, min(100, score))
    if clamped >= 80:
        return PriorityBand.CRITICAL
    if clamped >= 50:
        return PriorityBand.HIGH
    if clamped >= 20:
        return PriorityBand.MEDIUM
    return PriorityBand.LOW


@dataclass(frozen=True, slots=True)
class TechnologyStandardizationPolicy:
    """Deterministic technology standardization thresholds."""

    version: str = PORTFOLIO_STANDARDIZATION_POLICY_VERSION
    standard_threshold: float = 0.75
    preferred_threshold: float = 0.60
    common_threshold: float = 0.40

    def __post_init__(self) -> None:
        for name, value in (
            ("standard_threshold", self.standard_threshold),
            ("preferred_threshold", self.preferred_threshold),
            ("common_threshold", self.common_threshold),
        ):
            if value < 0.05 or value > 0.95:
                raise ValueError(f"{name} must be within [0.05, 0.95]")
        if not (
            self.standard_threshold
            >= self.preferred_threshold
            >= self.common_threshold
        ):
            raise ValueError("standardization thresholds must be ordered")

    def classify(
        self,
        *,
        usage_ratio: float,
        repository_count: int,
        fragmented: bool,
    ) -> TechnologyStandardizationStatus:
        if fragmented:
            return TechnologyStandardizationStatus.FRAGMENTED
        if repository_count <= 0:
            return TechnologyStandardizationStatus.UNKNOWN
        if repository_count == 1:
            return TechnologyStandardizationStatus.ISOLATED
        if usage_ratio >= self.standard_threshold:
            return TechnologyStandardizationStatus.STANDARD
        if usage_ratio >= self.preferred_threshold:
            return TechnologyStandardizationStatus.PREFERRED
        if usage_ratio >= self.common_threshold:
            return TechnologyStandardizationStatus.COMMON
        return TechnologyStandardizationStatus.ISOLATED


@dataclass(frozen=True, slots=True)
class AssessmentFreshnessPolicy:
    version: str = PORTFOLIO_FRESHNESS_POLICY_VERSION
    current_days: int = 30
    aging_days: int = 90

    def classify(
        self,
        *,
        published_at: datetime | None,
        evaluated_at: datetime | None = None,
    ) -> tuple[AssessmentFreshnessStatus, int | None]:
        if published_at is None:
            return AssessmentFreshnessStatus.UNKNOWN, None
        now = evaluated_at or datetime.now(UTC)
        age = max(0, int((now - published_at).total_seconds() // 86400))
        if age <= self.current_days:
            return AssessmentFreshnessStatus.CURRENT, age
        if age <= self.aging_days:
            return AssessmentFreshnessStatus.AGING, age
        return AssessmentFreshnessStatus.STALE, age


DefaultAssessmentFreshnessPolicy = AssessmentFreshnessPolicy


@dataclass(frozen=True, slots=True)
class RecommendationPriorityPolicy:
    """Explicit weighted recommendation priority scoring (0–100)."""

    version: str = PORTFOLIO_PRIORITY_POLICY_VERSION
    repository_weight: int = 25
    severity_weight: int = 30
    production_weight: int = 15
    recurrence_weight: int = 15
    coverage_gap_weight: int = 10
    criticality_weight: int = 5

    def score(
        self,
        *,
        repository_count: int,
        selected_repository_count: int,
        highest_severity: EngineeringSeverity,
        production_count: int,
        recurring_finding_count: int,
        coverage_gap: bool,
        max_criticality: RepositoryCriticality,
    ) -> tuple[int, PriorityBand, tuple[str, ...]]:
        factors: list[str] = []
        repo_ratio = (
            min(1.0, repository_count / max(1, selected_repository_count))
            if selected_repository_count
            else 0.0
        )
        repo_score = int(round(repo_ratio * self.repository_weight))
        factors.append(f"repositories_affected:{repository_count}->{repo_score}")

        severity_map = {
            EngineeringSeverity.CRITICAL: 1.0,
            EngineeringSeverity.HIGH: 0.8,
            EngineeringSeverity.MEDIUM: 0.5,
            EngineeringSeverity.LOW: 0.25,
            EngineeringSeverity.INFO: 0.1,
            EngineeringSeverity.UNKNOWN: 0.0,
        }
        sev_score = int(round(severity_map.get(highest_severity, 0.0) * self.severity_weight))
        factors.append(f"highest_severity:{highest_severity.value}->{sev_score}")

        prod_score = self.production_weight if production_count > 0 else 0
        factors.append(f"production_scope:{production_count}->{prod_score}")

        rec_ratio = min(1.0, recurring_finding_count / max(1, repository_count))
        rec_score = int(round(rec_ratio * self.recurrence_weight))
        factors.append(f"recurring_findings:{recurring_finding_count}->{rec_score}")

        gap_score = self.coverage_gap_weight if coverage_gap else 0
        factors.append(f"coverage_gap:{coverage_gap}->{gap_score}")

        criticality_map = {
            RepositoryCriticality.MISSION_CRITICAL: 1.0,
            RepositoryCriticality.HIGH: 0.75,
            RepositoryCriticality.MEDIUM: 0.4,
            RepositoryCriticality.LOW: 0.15,
            RepositoryCriticality.UNSPECIFIED: 0.0,
        }
        crit_score = int(
            round(criticality_map.get(max_criticality, 0.0) * self.criticality_weight)
        )
        factors.append(f"criticality:{max_criticality.value}->{crit_score}")

        total = min(
            100,
            repo_score + sev_score + prod_score + rec_score + gap_score + crit_score,
        )
        return total, priority_band(total), tuple(factors)


@dataclass(frozen=True, slots=True)
class ModernizationWavePolicy:
    version: str = PORTFOLIO_MODERNIZATION_POLICY_VERSION

    def assign(
        self,
        *,
        priority_score: int,
        systemic: bool,
        blocked: bool,
        evidence_coverage: float,
    ) -> tuple[ModernizationWave, tuple[str, ...]]:
        factors: list[str] = []
        if evidence_coverage < 0.25 or blocked:
            factors.append("insufficient_evidence_or_blocked")
            return ModernizationWave.DEFERRED, tuple(factors)
        if systemic and priority_score >= 50:
            factors.append("critical_or_high_systemic_risk")
            factors.append("blocking_dependencies_absent")
            return ModernizationWave.WAVE_1, tuple(factors)
        if priority_score >= 50:
            factors.append("high_value_modernization")
            factors.append("may_depend_on_wave_1")
            return ModernizationWave.WAVE_2, tuple(factors)
        if priority_score >= 20:
            factors.append("medium_priority_improvement")
            return ModernizationWave.WAVE_3, tuple(factors)
        factors.append("unclassified_low_signal")
        return ModernizationWave.UNCLASSIFIED, tuple(factors)


def theme_for_category(category: EngineeringCategory) -> ModernizationTheme | None:
    mapping = {
        EngineeringCategory.TECHNICAL_DEBT: ModernizationTheme.REDUCE_TECHNICAL_DEBT,
        EngineeringCategory.SECURITY: ModernizationTheme.REMEDIATE_SECURITY_RISK,
        EngineeringCategory.ARCHITECTURE: ModernizationTheme.IMPROVE_ARCHITECTURE,
        EngineeringCategory.DEPENDENCY: ModernizationTheme.UPGRADE_DEPENDENCIES,
        EngineeringCategory.CLOUD: ModernizationTheme.IMPROVE_CLOUD_READINESS,
        EngineeringCategory.OBSERVABILITY: ModernizationTheme.IMPROVE_OBSERVABILITY,
        EngineeringCategory.DOCUMENTATION: ModernizationTheme.IMPROVE_DOCUMENTATION,
        EngineeringCategory.COMPLIANCE: ModernizationTheme.ADDRESS_COMPLIANCE_GAPS,
    }
    return mapping.get(category)


def normalize_title_id(title: str) -> str:
    return "-".join(title.strip().lower().split())[:160]
