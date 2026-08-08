"""Contract for Slice 16.2 repository documentation verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.repository_documentation import (
    REPOSITORY_DOCUMENTATION_ID,
    REPOSITORY_DOCUMENTATION_VERSION,
)

SCHEMA_NAME = "repository-documentation-verification"
SCHEMA_VERSION = "1.0.0"
SV162_OUTPUT_RELATIVE = "reports/verification/sv16-2"
REPORT_JSON = "repository-documentation-verification.json"
REPORT_MD = "repository-documentation-verification.md"

POLICY_ID = "repository-documentation-policy"
POLICY_VERSION = "1.0"
POLICY_RELATIVE = "platform/policies/repository_documentation_policy.json"
POLICY_SCHEMA = "repository-documentation-policy:1.0"
CLEANUP_GUIDE = "platform/docs/repository-cleanup/community-documentation-cleanup.md"

CLASSIFICATIONS: tuple[str, ...] = (
    "ACTIVE",
    "GENERATED",
    "HISTORICAL",
    "EXPORT_ONLY",
    "OWNER_REVIEW_REQUIRED",
    "DELETE_CANDIDATE",
    "ARCHIVE_CANDIDATE",
    "STALE",
)

DOC_SCAN_ROOTS: tuple[str, ...] = (
    "README.md",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "ARCHITECTURE.md",
    "CHANGELOG.md",
    "ROADMAP.md",
    "docs",
    "knowledge",
    "examples",
    "platform/docs",
    "engine/docs",
    "design-system/documentation",
    "vscode-plugin",
    "insights/docs",
    "insights/README.md",
)

ACTIVE_COMMUNITY_GLOBS: tuple[str, ...] = (
    "docs/getting-started/**/*.md",
    "docs/engine/**/*.md",
    "docs/assessments/**/*.md",
    "docs/reports/**/*.md",
    "docs/extensions/**/*.md",
    "docs/ai-providers/**/*.md",
    "docs/reference/**/*.md",
    "docs/security/**/*.md",
    "docs/troubleshooting/**/*.md",
    "docs/faq/**/*.md",
    "docs/community/examples.md",
    "docs/community/contributing.md",
    "docs/index.md",
)

FORBIDDEN_ACTIVE_IDENTITY_PATTERNS: tuple[str, ...] = (
    r"\bAIMF\b",
    r"AI Modernization Factory",
    r"Cursor Extension",
    r"cursor-plugin",
    r"CodeStrata Cursor",
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv162Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = REPOSITORY_DOCUMENTATION_ID
    package_version: str = REPOSITORY_DOCUMENTATION_VERSION
    documentation_only: bool = True
    runtime_behavior_change_forbidden: bool = True
    start_slice_16_3: bool = True
    start_slice_16_4: bool = True
    start_slice_16_5: bool = True
    start_slice_16_6: bool = True
    start_slice_16_7: bool = True
    start_slice_16_8: bool = True
    start_slice_16_9: bool = True
    start_slice_16_10: bool = True
    start_epic_17: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv162Contract:
    return Sv162Contract()
