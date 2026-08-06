"""Primary-operation isolation matrix."""

from __future__ import annotations

from codestrata.telemetry.assessment_isolation import run_assessment_with_telemetry_isolation
from codestrata.telemetry.disabled_service import DisabledTelemetryFacade
from codestrata.telemetry.runtime_factory import create_default_telemetry_runtime

from verification.privacy_first_telemetry.models import CheckResult, Defect
from verification.privacy_first_telemetry.vscode_inputs import VsCodeTelemetryInventory


class _BoomTelemetry(DisabledTelemetryFacade):
    """Telemetry facade that fails every record attempt."""

    def __init__(self) -> None:
        super().__init__(create_default_telemetry_runtime())

    def record_assessment_started(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("telemetry_boom")

    def record_assessment_completed(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("telemetry_boom")


def check_isolation(
    vscode: VsCodeTelemetryInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    result, _meta = run_assessment_with_telemetry_isolation(
        lambda: "assess-ok",
        telemetry=_BoomTelemetry(),
        ai_enabled=False,
    )
    checks.append(
        CheckResult(
            name="engine_success_survives_telemetry_failure",
            ok=result == "assess-ok",
            detail=f"primary={result!r}",
            category="isolation",
            client="engine",
        )
    )

    class PrimaryError(RuntimeError):
        pass

    raised: Exception | None = None
    try:
        run_assessment_with_telemetry_isolation(
            lambda: (_ for _ in ()).throw(PrimaryError("primary_failed")),
            telemetry=_BoomTelemetry(),
            ai_enabled=False,
        )
    except PrimaryError as exc:
        raised = exc
    except Exception as exc:  # noqa: BLE001
        raised = exc

    checks.append(
        CheckResult(
            name="engine_primary_error_not_replaced",
            ok=isinstance(raised, PrimaryError) and "primary_failed" in str(raised),
            detail=type(raised).__name__ if raised else "none",
            category="isolation",
            client="engine",
        )
    )

    isolation_src = (vscode.telemetry_dir / "isolation.ts").read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            name="vscode_isolation_helper_present",
            ok="runCommandWithTelemetryIsolation" in isolation_src,
            detail="command isolation helper exists",
            category="isolation",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_isolation_swallows_telemetry_errors",
            ok="catch {" in isolation_src or "catch{" in isolation_src,
            detail="telemetry failures caught inside recordSafely",
            category="isolation",
            client="vscode",
        )
    )
    checks.append(
        CheckResult(
            name="vscode_isolation_rethrows_primary",
            ok="throw error" in isolation_src,
            detail="primary exceptions rethrown",
            category="isolation",
            client="vscode",
        )
    )

    extension_ts = vscode.telemetry_dir.parent / "extension.ts"
    ext_src = extension_ts.read_text(encoding="utf-8") if extension_ts.is_file() else ""
    checks.append(
        CheckResult(
            name="vscode_cli_args_unchanged_by_telemetry",
            ok="--telemetry-allow" not in ext_src and "--telemetry-deny" not in ext_src,
            detail="assess CLI spawn does not inject Engine telemetry flags",
            category="isolation",
            client="vscode",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="primary-operation isolation",
                    component=check.client,
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return checks, defects
