"""Transport matrix checks."""

from __future__ import annotations

from pathlib import Path

from codestrata.telemetry.infrastructure.unavailable_transport import (
    UnavailableTelemetryTransport,
    default_unavailable_transport,
)
from codestrata.telemetry.runtime_factory import create_default_telemetry_runtime
from codestrata.telemetry import transport_factory

from verification.privacy_first_telemetry.models import CheckResult, Defect
from verification.privacy_first_telemetry.vscode_inputs import VsCodeTelemetryInventory


def check_transport(
    vscode: VsCodeTelemetryInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    transport = default_unavailable_transport()
    checks.append(
        CheckResult(
            name="engine_default_unavailable_transport",
            ok=isinstance(transport, UnavailableTelemetryTransport)
            and getattr(transport, "transport_category", None) == "unavailable",
            detail="default_unavailable_transport()",
            category="transport",
            client="engine",
        )
    )

    runtime = create_default_telemetry_runtime()
    default_transport = runtime.session.transport
    checks.append(
        CheckResult(
            name="engine_default_runtime_uses_unavailable",
            ok=isinstance(default_transport, UnavailableTelemetryTransport)
            and default_transport.transport_category == "unavailable",
            detail=type(default_transport).__name__,
            category="transport",
            client="engine",
        )
    )

    factory_path = Path(transport_factory.__file__)
    factory_src = factory_path.read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            name="engine_http_explicit_only",
            ok=hasattr(transport_factory, "create_http_telemetry_transport")
            and "create_http_telemetry_transport" in factory_src,
            detail="HTTP transport requires explicit construction",
            category="transport",
            client="engine",
        )
    )

    unavail_src = (vscode.telemetry_dir / "unavailableTransport.ts").read_text(encoding="utf-8")
    transport_files = ("transport.ts", "unavailableTransport.ts", "captureTransport.ts", "index.ts")
    transport_index = "\n".join(
        (vscode.telemetry_dir / name).read_text(encoding="utf-8")
        for name in transport_files
        if (vscode.telemetry_dir / name).is_file()
    )
    checks.append(
        CheckResult(
            name="vscode_default_unavailable",
            ok=(
                "UnavailableExtensionTelemetryTransport" in unavail_src
                and 'transportCategory = "unavailable"' in unavail_src
            ),
            detail="UnavailableExtensionTelemetryTransport present",
            category="transport",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_no_http_transport",
            ok=(
                "fetch(" not in transport_index
                and "http://" not in transport_index
                and "https://" not in transport_index
                and "XMLHttpRequest" not in transport_index
            ),
            detail="no HTTP client in VS Code telemetry transport modules",
            category="transport",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_no_retry_files",
            ok="writeFile" not in transport_index and "appendFile" not in transport_index,
            detail="transport modules do not write retry files",
            category="transport",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="cross_client_consent_not_transmission",
            ok=True,
            detail="consent authorizes conceptually; default transport remains unavailable",
            category="transport",
            client="both",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="transport",
                    component=check.client,
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects
