"""OpenTofu validation for release artifact verification (never plan/apply)."""

from __future__ import annotations

from verification.release_artifacts.models import Blocker, CheckResult, Defect

try:
    from infrastructure.verification.opentofu import (
        check_opentofu_contract,
        detect_tools,
        run_opentofu_cli_validation,
    )
except ImportError:  # pragma: no cover
    detect_tools = None  # type: ignore[assignment,misc]
    check_opentofu_contract = None  # type: ignore[assignment,misc]
    run_opentofu_cli_validation = None  # type: ignore[assignment,misc]


def _map_check(name: str, ok: bool, detail: str, category: str = "opentofu") -> CheckResult:
    return CheckResult(name=name, ok=ok, detail=detail, category=category)


def check_opentofu(*, waiver: bool = False) -> tuple[list[CheckResult], list[Defect], list[Blocker], str]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    blockers: list[Blocker] = []
    status = "not_executed"

    if detect_tools is None or check_opentofu_contract is None:
        blockers.append(
            Blocker(
                code="opentofu_module_unavailable",
                detail="infrastructure.verification.opentofu not importable",
            )
        )
        checks.append(
            CheckResult(
                name="opentofu:import",
                ok=False,
                detail="module unavailable",
                category="opentofu",
                status="BLOCKED",
            )
        )
        return checks, defects, blockers, "BLOCKED"

    tools = detect_tools()
    infra_checks = check_opentofu_contract(tools)
    for item in infra_checks:
        checks.append(
            _map_check(
                name=item.name,
                ok=item.ok,
                detail=item.detail,
                category=item.category,
            )
        )

    if tools.terraform_available and not tools.tofu_available:
        checks.append(
            CheckResult(
                name="opentofu:terraform_not_substitute",
                ok=True,
                detail=f"terraform={tools.terraform_version} ignored",
                category="opentofu",
            )
        )

    if not tools.tofu_available:
        checks.append(
            CheckResult(
                name="opentofu:tool_available",
                ok=False,
                detail=tools.opentofu_validation_status,
                category="opentofu",
                status="BLOCKED",
            )
        )
        if not waiver:
            blockers.append(
                Blocker(
                    code="opentofu_unavailable",
                    detail="OpenTofu (tofu) CLI required; terraform is never a substitute",
                )
            )
        return checks, defects, blockers, "BLOCKED"

    checks.append(
        CheckResult(
            name="opentofu:tool_available",
            ok=True,
            detail=f"tofu_version={tools.tofu_version}",
            category="opentofu",
        )
    )
    checks.append(
        CheckResult(
            name="opentofu:version_satisfies_1_6",
            ok=bool(tools.tofu_version)
            and tuple(int(p) for p in str(tools.tofu_version).split(".")[:2]) >= (1, 6),
            detail=f"tofu_version={tools.tofu_version}",
            category="opentofu",
        )
    )

    if run_opentofu_cli_validation is not None:
        try:
            status, cli_checks = run_opentofu_cli_validation(tools)
        except Exception as exc:  # noqa: BLE001 — surface as blocker, do not crash runner
            status = "BLOCKED"
            blockers.append(
                Blocker(
                    code="opentofu_cli_execution_error",
                    detail=type(exc).__name__,
                )
            )
            checks.append(
                CheckResult(
                    name="opentofu:cli_validation",
                    ok=False,
                    detail=type(exc).__name__,
                    category="opentofu",
                    status="BLOCKED",
                )
            )
            cli_checks = []
        for item in cli_checks:
            checks.append(
                _map_check(
                    name=item.name,
                    ok=item.ok,
                    detail=item.detail,
                    category=item.category,
                )
            )
        if status == "fail":
            defects.append(
                Defect(
                    classification="opentofu_validation",
                    component="infrastructure",
                    expected="tofu fmt/validate pass",
                    actual=status,
                )
            )
        elif status == "pass":
            checks.append(
                CheckResult(
                    name="opentofu:blocker_closed",
                    ok=True,
                    detail="opentofu_unavailable closed; fmt/init/validate passed",
                    category="opentofu",
                )
            )
            checks.append(
                CheckResult(
                    name="opentofu:terraform_0_11_not_invoked",
                    ok=True,
                    detail="OpenTofu used; Terraform not substituted",
                    category="opentofu",
                )
            )

    checks.append(
        CheckResult(
            name="opentofu:no_plan_or_apply",
            ok=True,
            detail="SV.16 never runs tofu plan/apply",
            category="opentofu",
        )
    )
    return checks, defects, blockers, status
