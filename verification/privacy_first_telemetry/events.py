"""Event and field reconciliation matrix."""

from __future__ import annotations

from verification.privacy_first_telemetry.engine_inputs import EngineTelemetryInventory
from verification.privacy_first_telemetry.models import CheckResult, Defect
from verification.privacy_first_telemetry.vscode_inputs import VsCodeTelemetryInventory

# Conceptual shared fields (serialized names may differ intentionally).
_SHARED_CONCEPTS: tuple[tuple[str, str, str], ...] = (
    ("event_type", "event_type", "event_type"),
    ("client", "client_name", "client_name"),
    ("lifecycle", "lifecycle", "lifecycle"),
    ("result", "result", "result"),
    ("duration_bucket", "duration_bucket", "duration_bucket"),
    ("operation_category", "operation_category", "operation_category"),
    ("offline_mode", "offline_mode", "offline_mode"),
    ("ai_used", "ai_used", "ai_used"),
    ("schema_version", "schema_version", "schema_version"),
    ("policy_version", "runtime_policy_version", "runtime_policy_version"),
    ("os_family", "os_family", "os_family"),
)


def check_events(
    engine: EngineTelemetryInventory,
    vscode: VsCodeTelemetryInventory,
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    field_notes: list[str] = []

    engine_events = set(engine.approved_event_types)
    vscode_events = set(vscode.approved_event_types)
    shared_events = engine_events & vscode_events
    engine_only = engine_events - vscode_events
    vscode_only_events = vscode_events - engine_events

    checks.append(
        CheckResult(
            name="vscode_events_subset_of_engine",
            ok=vscode_events <= engine_events,
            detail=f"shared={sorted(shared_events)} engine_only={sorted(engine_only)}",
            category="events",
            client="both",
        )
    )
    checks.append(
        CheckResult(
            name="no_unexpected_vscode_only_events",
            ok=not vscode_only_events,
            detail=f"vscode_only={sorted(vscode_only_events)}",
            category="events",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="engine_application_events_intentional",
            ok=engine_only == {"application_started", "application_completed"},
            detail=f"engine_only={sorted(engine_only)}",
            category="events",
            client="engine",
        )
    )
    checks.append(
        CheckResult(
            name="schemas_independently_versioned",
            ok=(
                engine.event_schema_urn != f"{vscode.event_schema_name}:{vscode.event_schema_version}"
                and engine.runtime_policy_urn != vscode.runtime_policy_urn
            ),
            detail=(
                f"engine={engine.event_schema_urn}/{engine.runtime_policy_urn}; "
                f"vscode={vscode.event_schema_name}:{vscode.event_schema_version}/"
                f"{vscode.runtime_policy_urn}"
            ),
            category="events",
            client="both",
        )
    )
    checks.append(
        CheckResult(
            name="clients_differ_intentionally",
            ok=engine.client_name == "codestrata_cli" and vscode.client_name == "vscode_extension",
            detail=f"engine={engine.client_name} vscode={vscode.client_name}",
            category="events",
            client="both",
        )
    )

    for concept, eng_name, vs_name in _SHARED_CONCEPTS:
        eng_ok = eng_name in engine.approved_field_names
        vs_ok = vs_name in vscode.approved_field_names
        ok = eng_ok and vs_ok
        checks.append(
            CheckResult(
                name=f"shared_field_{concept}",
                ok=ok,
                detail=f"engine={eng_name}:{eng_ok} vscode={vs_name}:{vs_ok}",
                category="fields",
                client="both",
            )
        )
        field_notes.append(f"{concept}: engine={eng_name} vscode={vs_name}")

    # Engine-only / VS Code-only documentation checks
    checks.append(
        CheckResult(
            name="engine_only_cli_version_field",
            ok="cli_version" in engine.approved_field_names
            and "cli_version" not in vscode.approved_field_names,
            detail="cli_version is Engine-only",
            category="fields",
            client="engine",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_only_extension_version_field",
            ok="extension_version" in vscode.approved_field_names
            and "extension_version" not in engine.approved_field_names,
            detail="extension_version is VS Code-only",
            category="fields",
            client="vscode",
        )
    )

    mapping_ok = set(vscode.shared_conceptual_fields) <= {
        "event_type",
        "lifecycle",
        "result",
        "duration_bucket",
        "operation_category",
        "offline_mode",
        "ai_used",
        "os_family",
    }
    checks.append(
        CheckResult(
            name="catalog_mapping_shared_fields",
            ok=mapping_ok and bool(vscode.shared_conceptual_fields),
            detail=f"shared={list(vscode.shared_conceptual_fields)}",
            category="catalog",
            client="vscode",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="event-model-drift",
                    component=check.client,
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects, field_notes
