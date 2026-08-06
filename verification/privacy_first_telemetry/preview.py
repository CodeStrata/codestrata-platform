"""Preview matrix checks."""

from __future__ import annotations

from codestrata.telemetry.preview_builder import build_privacy_first_telemetry_preview

from verification.privacy_first_telemetry.models import CheckResult, Defect
from verification.privacy_first_telemetry.vscode_inputs import VsCodeTelemetryInventory


def check_preview(
    vscode: VsCodeTelemetryInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    preview = build_privacy_first_telemetry_preview()
    stable = preview.to_stable_dict()
    blob = preview.to_stable_json()
    again = build_privacy_first_telemetry_preview().to_stable_json()

    checks.append(
        CheckResult(
            name="engine_preview_deterministic",
            ok=blob == again,
            detail="preview JSON identical across builds",
            category="preview",
            client="engine",
        )
    )
    checks.append(
        CheckResult(
            name="engine_preview_no_transport",
            ok=(
                stable.get("transmission_performed") is False
                and stable.get("transport_status") == "unavailable"
            ),
            detail="preview remains local / unavailable",
            category="preview",
            client="engine",
        )
    )
    checks.append(
        CheckResult(
            name="engine_preview_no_identity",
            ok=stable.get("installation_identity_used") is False
            and '"installation_id"' not in blob,
            detail="no installation identity in preview",
            category="preview",
            client="engine",
        )
    )

    preview_src = (vscode.telemetry_dir / "preview.ts").read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            name="vscode_preview_builder_present",
            ok=(
                "buildVsCodeTelemetryPreview" in preview_src
                and "transmissionPerformed: false" in preview_src
                and "projectRuntimeEvent" in preview_src
            ),
            detail="internal preview builder with projection; no transmission",
            category="preview",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_preview_no_public_command_required",
            ok="registerCommand" not in preview_src,
            detail="preview is internal only",
            category="preview",
            client="vscode",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="preview",
                    component=check.client,
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects
