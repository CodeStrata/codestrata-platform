"""Contract for Slice 13.15 Epic 13 completion verification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verification.vscode_epic13_completion import (
    VSCODE_EPIC13_COMPLETION_ID,
    VSCODE_EPIC13_COMPLETION_VERSION,
)

SCHEMA_NAME = "vscode-epic13-completion-verification"
SCHEMA_VERSION = "1.0.0"
SV1315_OUTPUT_RELATIVE = "reports/verification/sv13-15"
REPORT_JSON = "vscode-epic13-completion-verification.json"
REPORT_MD = "vscode-epic13-completion-verification.md"

EPIC = "13"
EPIC_TITLE = "VS Code Extension"
INTENDED_VSCODE_VERSION = "0.2.0"
ASSESSMENT_SCHEMA_VERSION = "1.2"
TOTAL_SLICES = 15

# Prior slice runners (13.1–13.14) invoked by completion.
PRIOR_SLICE_RUNNERS: tuple[tuple[str, str, str, str], ...] = (
    # slice, module, schema, title
    ("13.1", "verification.vscode_community_workflow.runner", "vscode-community-workflow-verification", "Finalize Community Extension Workflow"),
    ("13.2", "verification.vscode_cli_discovery.runner", "vscode-cli-discovery-verification", "Detect Compatible CodeStrata CLI"),
    ("13.3", "verification.vscode_cli_installation.runner", "vscode-cli-installation-verification", "Install or Guide CLI Installation"),
    ("13.4", "verification.vscode_repository_initialization.runner", "vscode-repository-initialization-verification", "Initialize Repository"),
    ("13.5", "verification.vscode_assessment_execution.runner", "vscode-assessment-execution-verification", "Run Assessment"),
    ("13.6", "verification.vscode_assessment_progress.runner", "vscode-assessment-progress-verification", "Show Assessment Progress"),
    ("13.7", "verification.vscode_html_report_opening.runner", "vscode-html-report-opening-verification", "Open Generated HTML Report"),
    ("13.8", "verification.vscode_failure_recovery.runner", "vscode-failure-recovery-verification", "Surface Clear Failures and Recovery Steps"),
    ("13.9", "verification.vscode_telemetry_consent_integration.runner", "vscode-telemetry-consent-integration-verification", "Integrate Telemetry Consent with Community Runtime"),
    ("13.10", "verification.vscode_source_locality.runner", "vscode-source-locality-verification", "Confirm Source Code Remains Local"),
    ("13.11", "verification.vscode_cli_compatibility.runner", "vscode-cli-compatibility-verification", "Add CLI and Extension Version Compatibility Checks"),
    ("13.12", "verification.vscode_marketplace_branding.runner", "vscode-marketplace-branding-verification", "Complete Marketplace Branding"),
    ("13.13", "verification.vscode_marketplace_docs.runner", "vscode-marketplace-documentation-verification", "Complete Marketplace Documentation"),
    ("13.14", "verification.vscode_clean_install.runner", "vscode-clean-install-verification", "Validate Clean Install and Update Flow"),
)

EPIC13_POLICIES: tuple[tuple[str, str, str], ...] = (
    # policy_id, version, source relative
    ("community-vscode-workflow-policy", "1.0", "vscode-plugin/src/communityWorkflow/policy.ts"),
    ("community-vscode-cli-discovery-policy", "1.0", "vscode-plugin/src/cliDiscovery/policy.ts"),
    ("community-vscode-cli-installation-policy", "1.0", "vscode-plugin/src/cliInstallation/policy.ts"),
    ("community-vscode-repository-initialization-policy", "1.0", "vscode-plugin/src/repositoryInitialization/policy.ts"),
    ("community-vscode-assessment-execution-policy", "1.0", "vscode-plugin/src/assessmentExecution/policy.ts"),
    ("community-vscode-assessment-progress-policy", "1.0", "vscode-plugin/src/assessmentProgress/policy.ts"),
    ("community-vscode-report-opening-policy", "1.0", "vscode-plugin/src/reportOpening/policy.ts"),
    ("community-vscode-recovery-policy", "1.0", "vscode-plugin/src/failureRecovery/policy.ts"),
    ("community-vscode-telemetry-integration-policy", "1.0", "vscode-plugin/src/telemetryConsentIntegration/policy.ts"),
    ("community-vscode-source-locality-policy", "1.0", "vscode-plugin/src/sourceLocality/policy.ts"),
    ("community-vscode-cli-compatibility-policy", "1.0", "vscode-plugin/src/cliCompatibility/policy.ts"),
    ("community-vscode-marketplace-branding-policy", "1.0", "vscode-plugin/src/marketplaceBranding/policy.ts"),
    ("community-vscode-marketplace-documentation-policy", "1.0", "vscode-plugin/src/marketplaceDocs/policy.ts"),
    ("community-vscode-clean-install-policy", "1.0", "vscode-plugin/src/cleanInstall/policy.ts"),
)

SLICE_DOCS: tuple[tuple[str, str], ...] = (
    ("13.1", "vscode-plugin/docs/community-workflow.md"),
    ("13.2", "vscode-plugin/docs/cli-discovery.md"),
    ("13.3", "vscode-plugin/docs/cli-installation.md"),
    ("13.4", "vscode-plugin/docs/repository-initialization.md"),
    ("13.5", "vscode-plugin/docs/assessment-execution.md"),
    ("13.6", "vscode-plugin/docs/assessment-progress.md"),
    ("13.7", "vscode-plugin/docs/html-report-opening.md"),
    ("13.8", "vscode-plugin/docs/failure-recovery.md"),
    ("13.9", "vscode-plugin/docs/telemetry-consent-integration.md"),
    ("13.10", "vscode-plugin/docs/source-locality.md"),
    ("13.11", "vscode-plugin/docs/cli-compatibility.md"),
    ("13.12", "vscode-plugin/docs/marketplace-branding.md"),
    ("13.13", "vscode-plugin/docs/marketplace-documentation.md"),
    ("13.14", "vscode-plugin/docs/clean-install-update.md"),
)

SLICE_PACKAGES: tuple[tuple[str, str], ...] = (
    ("13.1", "vscode-plugin/src/communityWorkflow"),
    ("13.2", "vscode-plugin/src/cliDiscovery"),
    ("13.3", "vscode-plugin/src/cliInstallation"),
    ("13.4", "vscode-plugin/src/repositoryInitialization"),
    ("13.5", "vscode-plugin/src/assessmentExecution"),
    ("13.6", "vscode-plugin/src/assessmentProgress"),
    ("13.7", "vscode-plugin/src/reportOpening"),
    ("13.8", "vscode-plugin/src/failureRecovery"),
    ("13.9", "vscode-plugin/src/telemetryConsentIntegration"),
    ("13.10", "vscode-plugin/src/sourceLocality"),
    ("13.11", "vscode-plugin/src/cliCompatibility"),
    ("13.12", "vscode-plugin/src/marketplaceBranding"),
    ("13.13", "vscode-plugin/src/marketplaceDocs"),
    ("13.14", "vscode-plugin/src/cleanInstall"),
)

ALLOWED_LIMITATIONS = frozenset(
    {
        "full_extension_host_ui_automation_unavailable",
        "one_os_clean_install_execution",
        "synthetic_prior_vsix_for_update_validation",
        "no_live_ai_provider_validation",
        "telemetry_production_collection_intentionally_unavailable",
        "marketplace_not_published",
        "vsce_pinned_to_2_32_0",
        "worktree_uncommitted",
        "epic_14_not_started",
    }
)


def monorepo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True, slots=True)
class Sv1315Contract:
    schema_name: str = SCHEMA_NAME
    schema_version: str = SCHEMA_VERSION
    package_id: str = VSCODE_EPIC13_COMPLETION_ID
    package_version: str = VSCODE_EPIC13_COMPLETION_VERSION
    start_epic_14: bool = False
    no_commit: bool = True
    no_tag: bool = True
    no_publish: bool = True
    no_deploy: bool = True
    marketplace_published: bool = False
    production_telemetry_operational: bool = False


def default_contract() -> Sv1315Contract:
    return Sv1315Contract()
