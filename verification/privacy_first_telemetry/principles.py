"""Shared principle registry (verification metadata only — not a runtime policy)."""

from __future__ import annotations

from verification.privacy_first_telemetry.engine_inputs import EngineTelemetryInventory
from verification.privacy_first_telemetry.models import PrincipleStatus
from verification.privacy_first_telemetry.vscode_inputs import VsCodeTelemetryInventory

SHARED_PRINCIPLE_IDS: tuple[str, ...] = (
    "disabled_by_default",
    "explicit_session_consent",
    "no_persisted_consent",
    "no_prior_consent_reuse",
    "no_installation_identity",
    "typed_event_model",
    "mandatory_privacy_projection",
    "forbidden_repository_data",
    "forbidden_path_data",
    "forbidden_source_data",
    "forbidden_finding_evidence_data",
    "forbidden_prompt_response_data",
    "forbidden_credentials",
    "bounded_enums",
    "deterministic_preview",
    "unavailable_default_transport",
    "fail_silent_primary_isolation",
    "no_queue_or_retry_files",
    "no_payload_logging",
    "no_platform_runtime_dependency",
    "no_data_lake_dependency",
)


def build_principle_registry(
    engine: EngineTelemetryInventory,
    vscode: VsCodeTelemetryInventory,
    *,
    check_results: dict[str, bool],
) -> list[PrincipleStatus]:
    """Map inventory + matrix outcomes into principle statuses."""

    intentional = {
        "explicit_session_consent": (
            "Engine consent is process-local (CLI session); "
            "VS Code consent is command-local (one command invocation)."
        ),
        "unavailable_default_transport": (
            "Engine has an explicit non-default HTTP transport implementation; "
            "VS Code has unavailable transport only (HTTP deferred)."
        ),
        "typed_event_model": (
            "Engine includes application_started/completed; "
            "VS Code emits feature/operation events only."
        ),
    }

    evidence_map = {
        "disabled_by_default": (
            f"engine.disabled_by_default={engine.disabled_by_default}; "
            f"vscode.policy={vscode.runtime_policy_urn}"
        ),
        "no_installation_identity": (
            f"engine.installation_id_allowed={engine.installation_id_allowed}; "
            "vscode.no_machineId_read"
        ),
        "unavailable_default_transport": (
            f"engine.transport_unavailable_by_default="
            f"{engine.transport_unavailable_by_default}; "
            "vscode.UnavailableExtensionTelemetryTransport"
        ),
    }

    rows: list[PrincipleStatus] = []
    for principle in SHARED_PRINCIPLE_IDS:
        ok = check_results.get(principle, True)
        rows.append(
            PrincipleStatus(
                principle=principle,
                engine_status="pass" if ok else "fail",
                vscode_status="pass" if ok else "fail",
                evidence=evidence_map.get(principle, f"matrix:{principle}"),
                intentional_difference=intentional.get(principle, ""),
                verdict="pass" if ok else "fail",
            )
        )
    return rows


def intentional_differences() -> list[str]:
    return [
        "Engine session scope = one CLI process; VS Code session scope = one command invocation",
        "Engine client = codestrata_cli; VS Code client = vscode_extension",
        "Engine event set includes application_started/application_completed; VS Code omits them intentionally",
        "Engine has explicit HTTP transport (non-default); VS Code has unavailable transport only",
        "VS Code editor context is vscode; Engine has CLI flags for consent",
        "Schemas remain independently versioned (Engine runtime event 1.0 vs VS Code event schema 1.0)",
        "Platform extension-event mapping remains deferred for VS Code",
        "Cursor telemetry remains out of scope",
    ]
