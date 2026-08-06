"""Privacy negative matrix for Engine (live) and VS Code (static + conceptual)."""

from __future__ import annotations

from codestrata.telemetry.errors import TelemetryRuntimeError
from codestrata.telemetry.projection import project_from_mapping

from verification.privacy_first_telemetry.models import CheckResult, Defect
from verification.privacy_first_telemetry.vscode_inputs import VsCodeTelemetryInventory

# Conceptual forbidden categories exercised against Engine projection.
_ENGINE_NEGATIVE_FIELDS: tuple[tuple[str, object], ...] = (
    ("repository_name", "acme-repo"),
    ("repository_url", "https://example.invalid/acme"),
    ("project_name", "acme"),
    ("organization", "acme-org"),
    ("username", "alice"),
    ("email", "alice@example.invalid"),
    ("hostname", "host.example"),
    ("cwd", "/tmp/workspace"),
    ("path", "/tmp/file.py"),
    ("output_path", "/tmp/out"),
    ("argv", ["codestrata", "assess"]),
    ("command_line", "codestrata assess"),
    ("source_code", "def secrets():\n  pass"),
    ("findings", [{"id": "f1"}]),
    ("evidence", [{"id": "e1"}]),
    ("recommendations", [{"id": "r1"}]),
    ("exception_message", "boom"),
    ("stack_trace", "Traceback"),
    ("credential", "secret"),
    ("api_key", "key"),
    ("authorization", "Bearer x"),
    ("prompt", "system prompt"),
    ("response", "model reply"),
    ("model_id", "gpt-x"),
    ("exact_token_count", 42),
    ("cost", 0.01),
    ("installation_id", "install-1"),
)

_BASE_SAFE = {
    "event_type": "feature_invoked",
    "client_name": "codestrata_cli",
    "cli_version": "0.2.0",
    "os_family": "posix",
    "arch_family": "x86_64",
    "lifecycle": "invoked",
    "schema_version": "1.0",
    "runtime_policy_version": "1.0",
}

_VSCODE_FORBIDDEN_CONCEPTS = (
    "workspace",
    "repository",
    "document",
    "path",
    "finding",
    "evidence",
    "prompt",
    "response",
    "credential",
    "installation",
    "machine",
    "argv",
    "model",
    "provider",
    "cost",
    "token",
)


def check_privacy(
    vscode: VsCodeTelemetryInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for field_name, value in _ENGINE_NEGATIVE_FIELDS:
        payload = dict(_BASE_SAFE)
        payload[field_name] = value
        rejected = False
        echoed = False
        try:
            project_from_mapping(payload)
        except TelemetryRuntimeError as exc:
            rejected = True
            # Error must not echo the raw value.
            msg = str(exc)
            echoed = str(value) in msg and field_name not in ("ai_used",)
        except Exception as exc:  # noqa: BLE001 — verification harness
            rejected = True
            echoed = str(value) in str(exc)
        ok = rejected and not echoed
        checks.append(
            CheckResult(
                name=f"engine_reject_{field_name}",
                ok=ok,
                detail="rejected_without_echo" if ok else "leak_or_accept",
                category="privacy",
                client="engine",
            )
        )
        if not ok:
            defects.append(
                Defect(
                    classification="privacy_projection",
                    component="engine",
                    expected="reject_without_echo",
                    actual=field_name,
                )
            )

    # Consent allow must not expand fields — still reject forbidden keys.
    allow_payload = dict(_BASE_SAFE)
    allow_payload["repository_name"] = "should-still-fail"
    allow_rejected = False
    try:
        project_from_mapping(allow_payload)
    except TelemetryRuntimeError:
        allow_rejected = True
    checks.append(
        CheckResult(
            name="engine_allow_cannot_bypass_privacy",
            ok=allow_rejected,
            detail="forbidden field rejected even on allow path projection",
            category="privacy",
            client="engine",
        )
    )

    # VS Code: forbidden fragments present; approved fields must not include them.
    missing_fragments = [
        frag for frag in _VSCODE_FORBIDDEN_CONCEPTS if frag not in vscode.forbidden_name_fragments
    ]
    checks.append(
        CheckResult(
            name="vscode_forbidden_fragments_present",
            ok=not missing_fragments,
            detail=f"missing={missing_fragments}" if missing_fragments else "all_present",
            category="privacy",
            client="vscode",
        )
    )
    leaked_fields = [
        name
        for name in vscode.approved_field_names
        if any(frag in name for frag in ("path", "workspace", "repository", "finding", "prompt"))
    ]
    checks.append(
        CheckResult(
            name="vscode_approved_fields_exclude_forbidden",
            ok=not leaked_fields,
            detail=f"leaked={leaked_fields}" if leaked_fields else "clean",
            category="privacy",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_projection_module_present",
            ok=(vscode.telemetry_dir / "projection.ts").is_file()
            and (vscode.telemetry_dir / "privacy.ts").is_file(),
            detail="mandatory projection modules exist",
            category="privacy",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_no_ai_provider_fields",
            ok="provider" not in vscode.approved_field_names
            and "model" not in vscode.approved_field_names
            and "cost" not in vscode.approved_field_names,
            detail="ai_used boolean only; no provider/model/cost fields",
            category="privacy",
            client="vscode",
        )
    )

    for check in checks:
        if not check.ok and not any(d.actual == check.name or d.actual in check.name for d in defects):
            if check.client == "vscode" or check.name.startswith("engine_allow"):
                defects.append(
                    Defect(
                        classification="privacy_projection",
                        component=check.client,
                        expected="pass",
                        actual=check.name,
                        detail=check.detail,
                    )
                )
    return checks, defects
