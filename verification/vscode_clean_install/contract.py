"""Contract for Slice 13.14 clean-install verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_clean_install import (
    VSCODE_CLEAN_INSTALL_ID,
    VSCODE_CLEAN_INSTALL_VERSION,
)

SCHEMA_NAME = "vscode-clean-install-verification"
SCHEMA_VERSION = "1.0.0"
SV1314_OUTPUT_RELATIVE = ".codestrata-artifacts/validation/suites/sv13-14"
REPORT_JSON = "vscode-clean-install-verification.json"
REPORT_MD = "vscode-clean-install-verification.md"

CLEAN_POLICY_ID = "community-vscode-clean-install-policy"
CLEAN_POLICY_VERSION = "1.0"
INTENDED_VSCODE_VERSION = "0.2.2"
ASSESSMENT_SCHEMA_VERSION = "1.2"
CLEAN_PACKAGE = "vscode-plugin/src/cleanInstall"
PLUGIN_ROOT = "vscode-plugin"
VSIX_NAME = "codestrata-assessment-0.2.2.vsix"

STABLE_COMMAND_IDS = (
    "codestrata.assess",
    "codestrata.assessWithAi",
    "codestrata.init",
    "codestrata.openHtmlReport",
    "codestrata.installEngine",
    "codestrata.checkEnvironment",
    "codestrata.doctor",
)

STABLE_SETTING_KEYS = (
    "codestrata.engine.executable",
    "codestrata.assessment.outputDirectory",
    "codestrata.assessment.configPath",
    "codestrata.assessment.defaultNoAi",
    "codestrata.assessment.extraArgs",
    "codestrata.findings.groupBy",
    "codestrata.ai.providerHint",
)

REQUIRED_PACKAGE_ENTRIES = (
    "extension/package.json",
    "extension/out/extension.js",
    "extension/README.md",
    "extension/media/codestrata-icon.png",
)

FORBIDDEN_PACKAGE_SUBSTRINGS = (
    "verification/",
    "cursor-plugin",
    "/reports/",
    "sample-reports/",
    "testdata/",
    ".git/",
    "node_modules/",
    "src/",
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "full_extension_host_ui_automation_unavailable",
        "update_uses_synthetic_prior_package_when_no_historical_vsix",
        "uninstall_reinstall_automation_limited",
        "one_os_execution_with_cross_platform_static_coverage",
        "no_live_ai_provider_calls",
        "no_remote_marketplace_publish",
        "vsce_pinned_to_2_32_0_for_packaging_reliability",
        "epic_13_complete_via_13_15",
        "worktree_uncommitted",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1314Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_CLEAN_INSTALL_ID
    package_version: str = VSCODE_CLEAN_INSTALL_VERSION
    start_epic_14: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True


def default_contract() -> Sv1314Contract:
    return Sv1314Contract()
