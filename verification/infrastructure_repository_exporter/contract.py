"""Contract constants for Slice 12.6 exporter verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.infrastructure_repository_exporter import (
    INFRASTRUCTURE_REPOSITORY_EXPORTER_ID,
    INFRASTRUCTURE_REPOSITORY_EXPORTER_VERSION,
)

SCHEMA_NAME = "infrastructure-repository-exporter-verification"
SCHEMA_VERSION = "1.0.0"

SV126_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv12-6"
REPORT_JSON = "infrastructure-repository-exporter-verification.json"
REPORT_MD = "infrastructure-repository-exporter-verification.md"

IMPLEMENTATION_COMMAND = (
    "python scripts/export_infrastructure_repository.py "
    "--destination <outside-monorepo-path> [--dry-run]"
)

MANIFEST_SCHEMA = "infrastructure-repository-export-manifest:1.0.0"

ASSESSMENT_SCHEMA_VERSION = "1.2"


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv126Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = INFRASTRUCTURE_REPOSITORY_EXPORTER_ID
    package_version: str = INFRASTRUCTURE_REPOSITORY_EXPORTER_VERSION
    start_slice_12_7: bool = False
    no_destination_repo: bool = True
    no_git: bool = True
    no_aws: bool = True
    no_opentofu_exec: bool = True
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    assessment_schema_version: str = ASSESSMENT_SCHEMA_VERSION
    implementation_command: str = IMPLEMENTATION_COMMAND
    manifest_schema: str = MANIFEST_SCHEMA


def default_contract() -> Sv126Contract:
    return Sv126Contract()
