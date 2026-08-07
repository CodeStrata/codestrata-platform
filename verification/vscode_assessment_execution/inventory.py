"""Initialization surface inventory (Slice 13.5)."""

from __future__ import annotations

ASSESSMENT_SURFACES: dict[str, str] = {
    "codestrata.assess": "authoritative_standard_command",
    "codestrata.assessWithAi": "authoritative_ai_command",
    "selectWorkspaceFolder": "workspace_boundary",
    "detectRepositoryInitState": "initialization_boundary",
    "planAssessmentReadiness": "initialization_boundary",
    "discoverCodeStrataCli": "cli_readiness",
    "runTelemetryConsentPrompt": "telemetry_consent_boundary",
    "createIsolationSession": "analytics_boundary",
    "runCodestrataCli(assess)": "product_cli_invocation",
    "--no-ai": "standard_only_argument",
    "--with-ai": "ai_only_argument",
    "--repo/--output/--quiet/--json-summary": "common_argument",
    "exitCode authority": "engine_result_authority",
    "report_missing postcondition": "report_postcondition",
    "AbortController cancel": "cancellation_boundary",
    "source remains local": "source_local_boundary",
    "no git ops": "git_forbidden",
    "applyArtifacts": "extension_side_effect",
    "withProgress Notification": "deferred_to_13_6_progress",
    "Open HTML Report": "deferred_to_13_7_report",
    "recovery categories": "recovery_framework_active_13_8",
    "defaultNoAi flipping assess": "stale_behavior",
}
