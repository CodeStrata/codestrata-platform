"""Diagnostics privacy checks (Slice 10.8)."""

from __future__ import annotations

import re

from codestrata.telemetry.analytics.ai_analytics_diagnostics import (
    empty_ai_analytics_diagnostics,
)
from codestrata.telemetry.analytics.assessment_analytics_diagnostics import (
    empty_assessment_analytics_diagnostics,
)
from codestrata.telemetry.analytics.diagnostics import empty_analytics_diagnostics
from codestrata.telemetry.analytics.installation_identity import (
    new_anonymous_installation_identity,
)
from codestrata.telemetry.analytics.repository_aggregate_diagnostics import (
    empty_repository_aggregate_analytics_diagnostics,
)
from codestrata.telemetry.analytics.runtime_analytics_diagnostics import (
    empty_runtime_analytics_diagnostics,
)
from verification.anonymous_analytics_privacy.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.vscode_inputs import VsCodeAnalyticsInventory


def check_diagnostics(
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    identity = new_anonymous_installation_identity()

    blobs = [
        ("base", empty_analytics_diagnostics().to_stable_dict()),
        ("runtime", empty_runtime_analytics_diagnostics().to_stable_dict()),
        ("assessment", empty_assessment_analytics_diagnostics().to_stable_dict()),
        (
            "repository",
            empty_repository_aggregate_analytics_diagnostics().to_stable_dict(),
        ),
        ("ai", empty_ai_analytics_diagnostics().to_stable_dict()),
    ]
    for name, payload in blobs:
        text = str(payload)
        ok = (
            identity.installation_id not in text
            and '"installation_id"' not in text
            and "/Users/" not in text
            and "prompt" not in text
        )
        checks.append(
            CheckResult(
                name=f"diagnostics:{name}_payload_free",
                ok=ok,
                category="diagnostics",
                contract=name,
            )
        )

    checks.append(
        CheckResult(
            name="diagnostics:vscode_no_payload_logging",
            ok="installation_id" not in vscode.source_blob
            or "installationIdentityAllowed: false" in vscode.source_blob.replace(
                " ", ""
            )
            or "installationIdentityAllowed:false" in vscode.source_blob.replace(" ", ""),
            category="diagnostics",
            contract="vscode",
        )
    )
    # Stronger: analytics diagnostics module omits identity fields.
    checks.append(
        CheckResult(
            name="diagnostics:vscode_diag_module_identity_free",
            ok=(
                not re.search(r"\binstallationId\b", vscode.source_blob)
                and not re.search(
                    r"env\.machineId|\.machineId\b|telemetrySessionId\s*[,)]",
                    vscode.source_blob,
                )
            ),
            category="diagnostics",
            contract="vscode",
        )
    )

    for item in checks:
        if not item.ok:
            defects.append(Defect("diagnostics defect", item.name, "pass", "fail"))
    return checks, defects
