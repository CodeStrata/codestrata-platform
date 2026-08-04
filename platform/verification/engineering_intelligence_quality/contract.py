"""Contract for SV.12 Engineering Intelligence quality review."""

from __future__ import annotations

from dataclasses import dataclass

from verification.engineering_intelligence.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    CATALOG_RELATIVE_PATH,
    EIR_SCHEMA_VERSION,
    SAFETY_PATTERNS,
    UNSUPPORTED_SCORE_FRAGMENTS,
)
from verification.engineering_intelligence_quality import (
    ENGINEERING_INTELLIGENCE_QUALITY_ID,
    ENGINEERING_INTELLIGENCE_QUALITY_VERSION,
)

SCHEMA_NAME = "engineering-intelligence-quality-review"
SCHEMA_VERSION = "1.0.0"
TARGET_REPOSITORY_COUNT = 22
WEBSITE_EXPORT_SCHEMA_VERSION = "1.0"

SV10_OUTPUT_RELATIVE = "engine/reports/verification/sv10"
SV11_REPORT_RELATIVE = (
    "engine/reports/verification/sv11/assessment-consistency-verification.json"
)
SV12_OUTPUT_RELATIVE = "platform/reports/verification/sv12"

REPORT_JSON = "engineering-intelligence-report.json"
REPORT_HTML = "engineering-intelligence-report.html"
EXPORT_MANIFEST = "export-manifest.json"
REVIEW_JSON = "engineering-intelligence-quality-review.json"
REVIEW_MD = "engineering-intelligence-quality-review.md"

# Intentionally vulnerable / demo repositories requiring disclosure.
KNOWN_ISSUES_REPOS: frozenset[str] = frozenset(
    {
        "juice-shop",
        "nodegoat",
        "vulnerable-app-nodejs-express",
        "verademo",
    }
)
SUBMODULE_LIMITATION_REPOS: frozenset[str] = frozenset({"aspnetcore", "doris"})
SLOW_RUNTIME_REPOS: frozenset[str] = frozenset({"bookstack"})

UNSUPPORTED_COMMERCIAL_CLAIMS: tuple[str, ...] = tuple(
    frag
    for frag in (
        *UNSUPPORTED_SCORE_FRAGMENTS,
        "industry benchmark",
        "market standard",
        "best in class",
        "worst performing",
        "mature engineering organization",
        "immature organization",
        "healthy portfolio",
        "unhealthy portfolio",
        "guaranteed",
        "cost savings",
        "exact roi",
        "rewrite required",
        "migration required",
        "modernization completed",
        "technical debt will cause failure",
        "product-wide accuracy",
        "product wide accuracy",
        "roi claim",
    )
    if frag != "roi"  # too short; matches disclaimer lists like "not ... roi claims"
)

# Affirmative claims only — disclaimer/negation-aware scans handle separately.
AFFIRMATIVE_CLAIM_PATTERNS: tuple[tuple[str, str], ...] = (
    ("industry_benchmark", r"(?i)\bis an industry benchmark\b|\bare industry benchmarks\b"),
    ("product_wide_accuracy", r"(?i)\bproduct[- ]wide accuracy\b"),
    ("healthy_portfolio", r"(?i)\bhealthy portfolio\b"),
    ("maturity_score", r"(?i)\bmaturity score\b"),
    ("health_score", r"(?i)\bhealth score\b"),
    ("readiness_score", r"(?i)\breadiness score\b"),
)

DATASET_DISCLAIMER = (
    "SV.12 reviews one Engineering Intelligence Report built from the 22 curated "
    "v0.2.0 release-validation repositories only. It is not an industry benchmark "
    "or product-wide accuracy claim."
)

OBSERVATION_CLASSIFICATIONS: tuple[str, ...] = (
    "useful",
    "redundant",
    "unclear",
    "misleading",
    "insufficient_support",
    "excessive_detail",
    "missing_context",
    "limitation_needed",
    "terminology_issue",
    "presentation_issue",
    "product_defect_candidate",
)

HANDLING_OPTIONS: tuple[str, ...] = (
    "no_change",
    "documentation_only",
    "verification_harness_fix",
    "SV.13_product_fix",
    "post_v0.2.0_enhancement",
)

DEFECT_CLASSIFICATIONS: tuple[str, ...] = (
    "data_population",
    "technology_insight",
    "capability_comparison",
    "assessment_head_distribution",
    "recurring_pattern",
    "modernization_observation",
    "report_confidence",
    "dataset_limitation",
    "repository_drilldown",
    "provenance",
    "wording",
    "usability",
    "website_safety",
    "determinism",
)


@dataclass(frozen=True, slots=True)
class QualityReviewContract:
    verification_id: str = ENGINEERING_INTELLIGENCE_QUALITY_ID
    verification_version: str = ENGINEERING_INTELLIGENCE_QUALITY_VERSION
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    catalog_relative_path: str = CATALOG_RELATIVE_PATH
    target_repository_count: int = TARGET_REPOSITORY_COUNT
    eir_schema_version: str = EIR_SCHEMA_VERSION
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION
    website_export_schema_version: str = WEBSITE_EXPORT_SCHEMA_VERSION
    reassess_by_default: bool = False
    clone_by_default: bool = False
    start_sv13: bool = False
    redesign_report: bool = False
    notes: tuple[str, ...] = (
        DATASET_DISCLAIMER,
        "Reuses SV.6 pipeline builders and SV.8 website-safe export.",
        "Does not overwrite platform/demo/.",
        "Editorial observations are separated from product defects.",
    )


def default_contract() -> QualityReviewContract:
    return QualityReviewContract()


# Re-export for safety scanners.
__all_safety__ = (SAFETY_PATTERNS, UNSUPPORTED_COMMERCIAL_CLAIMS)
