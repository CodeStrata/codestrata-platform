"""Contract constants for Slice 12.7 export verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.infrastructure_repository_export import (
    INFRASTRUCTURE_REPOSITORY_EXPORT_ID,
    INFRASTRUCTURE_REPOSITORY_EXPORT_VERSION,
)

SCHEMA_NAME = "infrastructure-repository-export-verification"
SCHEMA_VERSION = "1.0.0"

SV127_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv12-7"
REPORT_JSON = "infrastructure-repository-export-verification.json"
REPORT_MD = "infrastructure-repository-export-verification.md"

MANIFEST_SCHEMA_NAME = "infrastructure-repository-export-manifest"
MANIFEST_SCHEMA_VERSION = "1.0.0"
REPOSITORY_NAME = "codestrata-infrastructure"
TARGET = "infrastructure"

VALIDATION_ROOTS = (
    "modules/community-cloud-api",
    "modules/community-data-lake",
    "production",
)

ALLOWED_OPENTOFU_COMMANDS = (
    "fmt -check -recursive",
    "init -backend=false",
    "validate",
    "version",
)

ASSESSMENT_SCHEMA_VERSION = "1.2"

REQUIRED_ROOT_ENTRIES = (
    "modules/community-cloud-api",
    "modules/community-data-lake",
    "production",
    "tests",
    "verification",
    "docs",
    "README.md",
    "SECURITY.md",
    "LICENSE",
    ".gitignore",
    ".editorconfig",
    "pyproject.toml",
    "export-manifest.json",
    "export-inventory.json",
    "SHA256SUMS",
)

ARTIFACT_FILENAMES = frozenset(
    {"export-manifest.json", "export-inventory.json", "SHA256SUMS"}
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv127Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = INFRASTRUCTURE_REPOSITORY_EXPORT_ID
    package_version: str = INFRASTRUCTURE_REPOSITORY_EXPORT_VERSION
    start_slice_12_8: bool = False
    no_git: bool = True
    no_aws: bool = True
    no_plan: bool = True
    no_apply: bool = True
    no_destroy: bool = True
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    no_real_destination_repo: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION


def default_contract() -> Sv127Contract:
    return Sv127Contract()
