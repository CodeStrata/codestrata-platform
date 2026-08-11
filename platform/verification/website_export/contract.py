"""Contract for SV.8 website-export verification."""

from __future__ import annotations

from dataclasses import dataclass

WEBSITE_EXPORT_VERIFICATION_ID = "website-export-verification"
WEBSITE_EXPORT_VERIFICATION_VERSION = "1.0.0"

# Verified SV.6 five-repo EIR (offline rebuild from permanent catalog assessments).
# ACTIVE_CURRENT_PLATFORM_CONTRACT: identity of the current five-repo EIR rebuild.
EXPECTED_SV6_REPORT_ID = "eir:3bc1983338ff046ac930fe57"
EXPECTED_SV6_DATASET_ID = "dataset:51f8613688c2fdffdd876121"
EXPECTED_SV6_INTERP_BUNDLE = "interp-bundle:a394af0337e541d0f269cf95"

JSON_FILENAME = "engineering-intelligence-report.json"
HTML_FILENAME = "engineering-intelligence-report.html"
MANIFEST_FILENAME = "export-manifest.json"

EXPECTED_HTML_TOC_LABELS: tuple[str, ...] = (
    "Report Scope and Dataset",
    "Executive Orientation",
    "Engineering Intelligence Summary",
    "Technology Distribution",
    "Capability Comparison",
    "Assessment-Head Distributions",
    "Recurring Patterns",
    "Modernization Observations",
    "Report Confidence",
    "Dataset Limitations",
    "Repository Drill-Downs",
    "Methodology",
    "Export Metadata",
)

UNSUPPORTED_SCORE_FRAGMENTS: tuple[str, ...] = (
    "maturity score",
    "health score",
    "readiness score",
    "composite score",
    "best repository",
    "worst repository",
)

SAFETY_PATTERNS: tuple[tuple[str, str], ...] = (
    ("absolute_unix_path", r"(?<![\w.-])/Users/[\w.-]+"),
    ("absolute_home", r"(?<![\w.-])/home/[\w.-]+"),
    ("file_url", r"file://[/\w]"),
    ("aws_key", r"AKIA[0-9A-Z]{16}"),
    ("bearer", r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    ("private_key", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ("password_assign", r"(?i)password\s*=\s*['\"][^'\"]{8,}"),
)

FORBIDDEN_REPORT_FRAGMENTS: tuple[str, ...] = (
    "/Users/",
    "/home/",
    "file://",
    "AKIA",
    "-----BEGIN",
)


@dataclass(frozen=True, slots=True)
class WebsiteExportVerificationContract:
    verification_id: str = WEBSITE_EXPORT_VERIFICATION_ID
    schema_version: str = WEBSITE_EXPORT_VERIFICATION_VERSION
    notes: tuple[str, ...] = (
        "SV.8 verifies website-safe projection and static export of a verified EIR.",
        "Reuses the SV.6 five-repository public OSS EngineeringIntelligenceReport.",
        "Does not start infrastructure deployment (SV.9), 30-repo run, or SV.12 review.",
        "Does not publish, host, or regenerate committed demo artifacts for formatting.",
    )


def default_contract() -> WebsiteExportVerificationContract:
    return WebsiteExportVerificationContract()
