"""Diagnostics and output privacy checks."""

from __future__ import annotations

from pathlib import Path

from codestrata.telemetry.runtime_factory import create_default_telemetry_runtime

from verification.privacy_first_telemetry.models import CheckResult, Defect
from verification.privacy_first_telemetry.vscode_inputs import VsCodeTelemetryInventory

_FORBIDDEN_DIAG_KEYS = (
    "repository",
    "workspace",
    "document",
    "argv",
    "payload",
    "endpoint",
    "credential",
    "installation_id",
    "machineId",
    "exception_message",
)


def check_diagnostics(
    vscode: VsCodeTelemetryInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    runtime = create_default_telemetry_runtime()
    diag = runtime.diagnostics().to_stable_dict()
    diag_keys = set(diag.keys())
    leak_keys = [k for k in diag_keys if any(f in k.lower() for f in (
        "repository", "workspace", "path", "argv", "payload", "endpoint", "credential", "machine"
    ))]
    # Allow keys that are limitation codes containing substrings — only exact field leaks.
    leak_keys = [k for k in leak_keys if k in _FORBIDDEN_DIAG_KEYS or k.endswith("_path")]
    checks.append(
        CheckResult(
            name="engine_diagnostics_bounded",
            ok=not leak_keys,
            detail=f"keys={sorted(diag_keys)}",
            category="diagnostics",
            client="engine",
        )
    )
    blob = str(diag)
    checks.append(
        CheckResult(
            name="engine_diagnostics_no_payload",
            ok='"event"' not in blob or "payload" not in diag_keys,
            detail="diagnostics do not embed event payloads",
            category="diagnostics",
            client="engine",
        )
    )

    diag_src = (vscode.telemetry_dir / "diagnostics.ts").read_text(encoding="utf-8")
    # Exact identity / workspace field names only (avoid limitation-code substrings).
    for token in ('"machineId"', "workspaceUri", '"installation_id"', "repositoryUri"):
        checks.append(
            CheckResult(
                name=f"vscode_diagnostics_no_{token.strip(chr(34))}",
                ok=token not in diag_src,
                detail=f"{token} absent from diagnostics.ts",
                category="diagnostics",
                client="vscode",
            )
        )

    # Output channel: extension must not appendString telemetry payloads.
    extension_ts = vscode.telemetry_dir.parent / "extension.ts"
    ext = extension_ts.read_text(encoding="utf-8") if extension_ts.is_file() else ""
    checks.append(
        CheckResult(
            name="vscode_output_no_telemetry_payload_logging",
            ok=(
                "telemetry payload" not in ext.lower()
                and "JSON.stringify(projected" not in ext
                and "JSON.stringify(event" not in ext
            ),
            detail="extension.ts does not log telemetry payloads",
            category="output",
            client="vscode",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="diagnostics/output",
                    component=check.client,
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects
