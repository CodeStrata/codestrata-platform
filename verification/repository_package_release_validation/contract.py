"""Contract for Slice 16.9 package & release artifact validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.repository_package_release_validation import (
    REPOSITORY_PACKAGE_RELEASE_VALIDATION_ID,
    REPOSITORY_PACKAGE_RELEASE_VALIDATION_VERSION,
)

SCHEMA_NAME = "repository-package-release-validation-verification"
SCHEMA_VERSION = "1.0.0"
SV169_OUTPUT_RELATIVE = "reports/verification/sv16-9"
REPORT_JSON = "repository-package-release-validation-verification.json"
REPORT_MD = "repository-package-release-validation-verification.md"

POLICY_RELATIVE = "platform/policies/repository_package_release_validation_policy.json"
POLICY_SCHEMA = "repository-package-release-validation-policy:1.0"
CONTRACT_RELATIVE = "platform/contracts/repository_package_release_validation_verification.json"

EXPORT_TARGETS = ("community", "infrastructure", "insights")
COMMUNITY_REPOS = (
    "codestrata-engine",
    "codestrata-examples",
    "codestrata-vscode",
    "codestrata-docs",
)
STANDALONE_FOCUS = ("community", "docs", "insights", "infrastructure")

REQUIRED_ROOT_FILES = ("README.md", "LICENSE", "SECURITY.md", ".gitignore")
RECOMMENDED_ROOT_FILES = ("CHANGELOG.md", "CODE_OF_CONDUCT.md")

VERSION_ANCHORS = {
    "engine_cli": "0.2.0",
    "vscode": "0.2.0",
    "assessment": "1.2",
}

FORBIDDEN_EXPORT_MARKERS = (
    "platform/src/codestrata_platform/api/",
    "platform/src/codestrata_platform/rag/",
    "platform/src/codestrata_platform/knowledge_graph/",
    "BEGIN RSA PRIVATE KEY",
    "AWS_SECRET_ACCESS_KEY",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv169Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = REPOSITORY_PACKAGE_RELEASE_VALIDATION_ID
    package_version: str = REPOSITORY_PACKAGE_RELEASE_VALIDATION_VERSION
    start_slice_16_9: bool = True
    start_slice_16_10: bool = True
    start_epic_17: bool = False
    no_publish: bool = True
    no_deploy: bool = True
    no_tag: bool = True
    no_commit: bool = True
    no_marketplace_publish: bool = True
    no_pypi_publish: bool = True
    no_github_release: bool = True
    production_ingestion_enabled: bool = False


def default_contract() -> Sv169Contract:
    return Sv169Contract()
