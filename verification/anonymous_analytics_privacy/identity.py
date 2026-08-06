"""Anonymous installation identity privacy checks (Slice 10.2)."""

from __future__ import annotations

import uuid
from pathlib import Path

from codestrata.telemetry.analytics.errors import AnalyticsError
from codestrata.telemetry.analytics.installation_identity import (
    ensure_anonymous_installation_identity,
    is_uuid_v4,
    new_anonymous_installation_identity,
)
from codestrata.telemetry.analytics.installation_identity_diagnostics import (
    empty_installation_identity_diagnostics,
)
from verification.anonymous_analytics_privacy.engine_inputs import EngineAnalyticsInventory
from verification.anonymous_analytics_privacy.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.vscode_inputs import VsCodeAnalyticsInventory


def check_identity(
    engine: EngineAnalyticsInventory,
    vscode: VsCodeAnalyticsInventory,
    *,
    tmp_home: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    checks.append(
        CheckResult(
            name="identity:machine_fingerprint_forbidden",
            ok=engine.identity_machine_fingerprint_forbidden,
            category="identity",
            contract="identity",
        )
    )
    checks.append(
        CheckResult(
            name="identity:does_not_require_analytics_collection",
            ok=engine.extras.get("identity_analytics_collection_required") is False,
            category="identity",
            contract="identity",
        )
    )
    checks.append(
        CheckResult(
            name="identity:transmission_disallowed",
            ok=engine.extras.get("identity_transmission_allowed") is False,
            category="identity",
            contract="identity",
        )
    )

    first = new_anonymous_installation_identity()
    second = new_anonymous_installation_identity()
    checks.append(
        CheckResult(
            name="identity:uuid_v4",
            ok=is_uuid_v4(first.installation_id),
            category="identity",
            contract="identity",
        )
    )
    checks.append(
        CheckResult(
            name="identity:random_not_equal",
            ok=first.installation_id != second.installation_id,
            category="identity",
            contract="identity",
        )
    )
    # Not derived from fixed machine-like strings.
    for needle in ("hostname", "username", "machine", "mac"):
        checks.append(
            CheckResult(
                name=f"identity:not_derived_token:{needle}",
                ok=needle not in first.installation_id.lower(),
                category="identity",
                contract="identity",
            )
        )

    tmp_home.mkdir(parents=True, exist_ok=True)
    identity, created, _recovered = ensure_anonymous_installation_identity(home=tmp_home)
    identity2, created2, _ = ensure_anonymous_installation_identity(home=tmp_home)
    checks.append(
        CheckResult(
            name="identity:generate_once_reuse",
            ok=created is True and created2 is False
            and identity.installation_id == identity2.installation_id,
            category="identity",
            contract="identity",
        )
    )
    files = sorted(p.name for p in tmp_home.iterdir())
    checks.append(
        CheckResult(
            name="identity:persists_versioned_json_only",
            ok=files == ["anonymous-installation-identity.json"],
            detail=",".join(files),
            category="identity",
            contract="identity",
        )
    )

    diag = empty_installation_identity_diagnostics()
    diag_blob = str(diag.to_stable_dict() if hasattr(diag, "to_stable_dict") else diag)
    checks.append(
        CheckResult(
            name="identity:diagnostics_omit_value",
            ok=identity.installation_id not in diag_blob
            and '"installation_id"' not in diag_blob,
            category="identity",
            contract="identity",
        )
    )

    # VS Code must not read Engine identity files or generate IDs.
    checks.append(
        CheckResult(
            name="identity:vscode_no_engine_identity_file",
            ok=not vscode.has_engine_identity_reads,
            category="identity",
            contract="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="identity:vscode_no_uuid_generation",
            ok=not vscode.has_uuid_generation,
            category="identity",
            contract="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="identity:vscode_no_machine_id",
            ok=not vscode.has_machine_id_reads,
            category="identity",
            contract="vscode",
        )
    )

    # UUID format sanity (version nibble).
    try:
        parsed = uuid.UUID(first.installation_id)
        ok_version = parsed.version == 4
    except Exception:
        ok_version = False
    checks.append(
        CheckResult(
            name="identity:uuid_version_4",
            ok=ok_version,
            category="identity",
            contract="identity",
        )
    )

    for item in checks:
        if not item.ok:
            defects.append(
                Defect(
                    "identity defect",
                    item.name,
                    "pass",
                    "fail",
                    detail=item.detail,
                )
            )
    return checks, defects
