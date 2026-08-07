"""Initialization surface inventory classification (Slice 13.4)."""

from __future__ import annotations

# Closed classification vocabulary from the slice brief.
SURFACE_CLASSES = (
    "authoritative_init_command",
    "workspace_validation",
    "cli_readiness",
    "engine_init_invocation",
    "initialized_state_detection",
    "local_config_mutation",
    "source_file_mutation",
    "idempotency",
    "overwrite_behavior",
    "partial_state_handling",
    "cancellation_boundary",
    "output_boundary",
    "telemetry_forbidden",
    "analytics_forbidden",
    "report_forbidden",
    "assessment_forbidden",
    "ai_forbidden",
    "compatibility_surface",
    "recovery_framework_active_13_8",
    "stale_behavior",
)

# Inventory of known surfaces → classification (path-free).
INIT_SURFACES: dict[str, str] = {
    "codestrata.init": "authoritative_init_command",
    "selectWorkspaceFolder": "workspace_validation",
    "discoverCodeStrataCli": "cli_readiness",
    "presentInstallationGuidance": "cli_readiness",
    "detectRepositoryInitState": "initialized_state_detection",
    "runCodestrataCli(init)": "engine_init_invocation",
    "codestrata.toml write (Engine)": "local_config_mutation",
    "source files": "source_file_mutation",
    "Approach A skip": "idempotency",
    "no --force": "overwrite_behavior",
    "empty codestrata.toml": "partial_state_handling",
    "cliRunner cancelled": "cancellation_boundary",
    "output channel redactSecrets": "output_boundary",
    "EXCLUDED_TELEMETRY_COMMANDS": "telemetry_forbidden",
    "analytics_allowed false": "analytics_forbidden",
    "report_open_allowed false": "report_forbidden",
    "assessment_allowed false": "assessment_forbidden",
    "ai_execution_allowed false": "ai_forbidden",
    "cli discovery policy": "compatibility_surface",
    "recovery categories": "recovery_framework_active_13_8",
    "extension-synthesized config": "stale_behavior",
}
