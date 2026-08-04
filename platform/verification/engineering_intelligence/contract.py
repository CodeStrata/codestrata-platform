"""Contract for SV.6 Engineering Intelligence pipeline verification."""

from __future__ import annotations

from dataclasses import dataclass

ENGINEERING_INTELLIGENCE_VERIFICATION_ID = "engineering-intelligence-verification"
ENGINEERING_INTELLIGENCE_VERIFICATION_VERSION = "1.0.0"

# Permanent catalog path relative to monorepo root (never a second list).
CATALOG_RELATIVE_PATH = "validation/repository-catalog/catalog.json"

# Deterministic preferred five-language subset (catalog IDs only).
# C# / JavaScript / Python / PHP / Java — all must be qualified pinned commits.
PREFERRED_FIVE_LANGUAGE_SUBSET: tuple[str, ...] = (
    "cleanarchitecture",
    "express",
    "flask",
    "slim",
    "spring-petclinic",
)

# Expected language groups for the preferred subset (documentation / checks).
SUBSET_LANGUAGE_GROUPS: dict[str, str] = {
    "cleanarchitecture": "C#/.NET",
    "express": "JS/TS",
    "flask": "Python",
    "slim": "PHP",
    "spring-petclinic": "Java",
}

EIR_SCHEMA_VERSION = "1.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"

UNSUPPORTED_SCORE_FRAGMENTS: tuple[str, ...] = (
    "maturity score",
    "maturity_level",
    "health score",
    "readiness score",
    "composite score",
    "rank:",
    "ranking",
    "best repository",
    "worst repository",
    "production ready",
    "cloud ready",
    "ai ready",
    "industry leading",
    "roi",
    "will save",
    "exact cost",
    "staffing plan",
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


@dataclass(frozen=True, slots=True)
class EiVerificationContract:
    verification_id: str = ENGINEERING_INTELLIGENCE_VERIFICATION_ID
    schema_version: str = ENGINEERING_INTELLIGENCE_VERIFICATION_VERSION
    preferred_subset: tuple[str, ...] = PREFERRED_FIVE_LANGUAGE_SUBSET
    notes: tuple[str, ...] = (
        "SV.6 verifies the Platform Engineering Intelligence pipeline.",
        "Uses permanent catalog qualified pinned revisions only.",
        "Does not start website export (SV.8), Community Cloud (SV.7), or SV.12 review.",
        "Does not tune aggregation rules, patterns, or assessment analyzers.",
    )


def default_contract() -> EiVerificationContract:
    return EiVerificationContract()
