"""Installation-identity matrix checks."""

from __future__ import annotations

from codestrata.telemetry.privacy import FORBIDDEN_FIELD_NAMES
from codestrata.telemetry.runtime_policy import default_runtime_policy

from verification.privacy_first_telemetry.engine_inputs import EngineTelemetryInventory
from verification.privacy_first_telemetry.models import CheckResult, Defect
from verification.privacy_first_telemetry.vscode_inputs import (
    VsCodeTelemetryInventory,
    vscode_source_mentions,
)


def check_identity(
    engine: EngineTelemetryInventory,
    vscode: VsCodeTelemetryInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = default_runtime_policy()
    checks.append(
        CheckResult(
            name="engine_installation_id_disallowed",
            ok=policy.installation_id_allowed is False
            and engine.installation_id_allowed is False,
            detail="installation_id_allowed=False",
            category="identity",
            client="engine",
        )
    )
    checks.append(
        CheckResult(
            name="engine_installation_id_forbidden_field",
            ok="installation_id" in FORBIDDEN_FIELD_NAMES,
            detail="installation_id in FORBIDDEN_FIELD_NAMES",
            category="identity",
            client="engine",
        )
    )

    # VS Code must not read machineId / telemetrySessionId / generate UUIDs for identity.
    forbidden_reads = (
        "machineId",
        "telemetrySessionId",
        "vscode.env.machineId",
        "env.machineId",
    )
    hits = [token for token in forbidden_reads if vscode_source_mentions(vscode, token)]
    checks.append(
        CheckResult(
            name="vscode_no_machine_identity_reads",
            ok=not hits,
            detail=f"hits={hits}" if hits else "clean",
            category="identity",
            client="vscode",
        )
    )
    # Allow "uuid" only if clearly not used for installation identity — fail on crypto.randomUUID in telemetry
    checks.append(
        CheckResult(
            name="vscode_no_random_uuid_identity",
            ok="randomUUID" not in vscode.source_blob and "uuidv4" not in vscode.source_blob.lower(),
            detail="no UUID generation in telemetry runtime",
            category="identity",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_policy_no_installation_identity",
            ok="no_installation_identity" in vscode.source_blob,
            detail="policy limitation documents no installation identity",
            category="identity",
            client="vscode",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="identity",
                    component=check.client,
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects
