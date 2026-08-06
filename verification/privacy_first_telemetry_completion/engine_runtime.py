"""Engine and VS Code runtime completion checks."""

from __future__ import annotations

from pathlib import Path

from codestrata.telemetry.runtime_factory import create_default_telemetry_runtime
from codestrata.telemetry.runtime_policy import default_runtime_policy
from codestrata.telemetry.infrastructure.unavailable_transport import (
    UnavailableTelemetryTransport,
)
from codestrata.telemetry.transport_factory import create_http_telemetry_transport

from verification.privacy_first_telemetry.consent import check_consent
from verification.privacy_first_telemetry.identity import check_identity
from verification.privacy_first_telemetry.isolation import check_isolation
from verification.privacy_first_telemetry.persistence import check_persistence
from verification.privacy_first_telemetry.privacy import check_privacy
from verification.privacy_first_telemetry.transport import check_transport
from verification.privacy_first_telemetry.engine_inputs import load_engine_inventory
from verification.privacy_first_telemetry.vscode_inputs import load_vscode_inventory
from verification.privacy_first_telemetry_completion.models import CheckResult, Defect


def check_engine_runtime(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    inventory = load_engine_inventory()
    policy = default_runtime_policy()
    runtime = create_default_telemetry_runtime()

    checks.append(
        CheckResult(
            name="engine_disabled_by_default",
            ok=inventory.disabled_by_default and policy.disabled_by_default,
            detail="runtime policy disabled_by_default",
            category="engine",
        )
    )
    checks.append(
        CheckResult(
            name="engine_default_transport_unavailable",
            ok=isinstance(runtime.session.transport, UnavailableTelemetryTransport),
            detail=type(runtime.session.transport).__name__,
            category="engine",
        )
    )
    checks.append(
        CheckResult(
            name="engine_installation_id_disallowed",
            ok=policy.installation_id_allowed is False,
            detail="installation_id_allowed=False",
            category="engine",
        )
    )
    checks.append(
        CheckResult(
            name="engine_http_factory_exists",
            ok=callable(create_http_telemetry_transport),
            detail="create_http_telemetry_transport present",
            category="engine",
        )
    )
    # Normal default construction does not use HTTP.
    checks.append(
        CheckResult(
            name="engine_default_not_http",
            ok=runtime.session.transport.transport_category == "unavailable",
            detail=runtime.session.transport.transport_category,
            category="engine",
        )
    )

    tel_root = monorepo / "engine" / "src" / "codestrata" / "telemetry"
    for module in (
        "assessment_isolation.py",
        "pre_transport_gate.py",
        "catalog.py",
        "preview_builder.py",
    ):
        checks.append(
            CheckResult(
                name=f"engine_module_{module.replace('.', '_')}",
                ok=(tel_root / module).is_file(),
                detail=module,
                category="engine",
            )
        )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="isolation defect" if "transport" in check.name else "consent defect",
                    component="engine",
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects


def check_vscode_runtime(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    vscode = load_vscode_inventory(monorepo)

    checks.append(
        CheckResult(
            name="vscode_runtime_policy_1_0",
            ok=vscode.runtime_policy_urn.endswith(":1.0"),
            detail=vscode.runtime_policy_urn,
            category="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_client_name",
            ok=vscode.client_name == "vscode_extension",
            detail=vscode.client_name,
            category="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_eligible_assess_only",
            ok=set(vscode.eligible_commands)
            == {"codestrata.assess", "codestrata.assessWithAi"},
            detail=str(list(vscode.eligible_commands)),
            category="vscode",
        )
    )
    required = (
        "runtimePolicy.ts",
        "consent.ts",
        "projection.ts",
        "unavailableTransport.ts",
        "isolation.ts",
        "preview.ts",
        "catalogMapping.ts",
    )
    for name in required:
        checks.append(
            CheckResult(
                name=f"vscode_module_{name.replace('.', '_')}",
                ok=(vscode.telemetry_dir / name).is_file(),
                detail=name,
                category="vscode",
            )
        )
    checks.append(
        CheckResult(
            name="vscode_no_http_in_telemetry",
            ok="fetch(" not in vscode.source_blob and "https://" not in vscode.source_blob,
            detail="no HTTP client in telemetry sources",
            category="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_capture_not_default_export_as_product",
            ok="defaultUnavailableTransport" in vscode.source_blob,
            detail="unavailable transport is the product default factory",
            category="vscode",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="boundary defect",
                    component="vscode",
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects


def check_reused_privacy_matrices(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    """Reuse Slice 9.14 matrices and summarize status fields."""

    vscode = load_vscode_inventory(monorepo)
    engine = load_engine_inventory()
    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []

    for fn in (
        lambda: check_consent(vscode),
        lambda: check_privacy(vscode),
        lambda: check_persistence(monorepo, vscode),
        lambda: check_identity(engine, vscode),
        lambda: check_transport(vscode),
        lambda: check_isolation(vscode),
    ):
        c, d = fn()
        # Adapt CheckResult from 9.14 (has client field) to 9.15 model
        for item in c:
            all_checks.append(
                CheckResult(
                    name=item.name,
                    ok=item.ok,
                    detail=item.detail,
                    category=item.category,
                )
            )
        for item in d:
            all_defects.append(
                Defect(
                    classification=item.classification,
                    component=item.component,
                    expected=item.expected,
                    actual=item.actual,
                    detail=item.detail,
                )
            )

    def _status(category: str) -> str:
        subset = [c for c in all_checks if c.category == category]
        if not subset:
            return "unknown"
        return "pass" if all(c.ok for c in subset) else "fail"

    statuses = {
        "consent_status": _status("consent"),
        "privacy_status": _status("privacy"),
        "identity_status": _status("identity"),
        "persistence_status": _status("persistence"),
        "transport_status": _status("transport"),
        "assessment_isolation_status": (
            "pass"
            if all(c.ok for c in all_checks if c.category == "isolation" and "engine" in c.name)
            else "fail"
            if any(not c.ok for c in all_checks if c.category == "isolation" and "engine" in c.name)
            else "pass"
        ),
        "extension_isolation_status": (
            "pass"
            if all(c.ok for c in all_checks if c.category == "isolation" and "vscode" in c.name)
            else "fail"
            if any(not c.ok for c in all_checks if c.category == "isolation" and "vscode" in c.name)
            else "pass"
        ),
    }
    return all_checks, all_defects, statuses
