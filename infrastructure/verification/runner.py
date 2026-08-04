"""SV.9 Platform Deployment Foundation verification runner."""

from __future__ import annotations

import time
from pathlib import Path

from infrastructure.verification.api_gateway import check_api_gateway
from infrastructure.verification.configuration import check_configuration
from infrastructure.verification.contract import (
    AUTHENTICATION_MODE,
    AWS_PROVIDER_CONSTRAINT,
    DEPLOYMENT_MODE,
    ENVIRONMENT_NAME,
    LAMBDA_ARCHITECTURE_DEFAULT,
    MODULE_NAME,
    PACKAGING_STRATEGY,
    RATE_LIMIT_MODE,
    REQUIRED_OPENTOFU,
    API_GATEWAY_PROTOCOL,
    default_contract,
    infra_root,
)
from infrastructure.verification.ecr import check_ecr
from infrastructure.verification.extraction import check_extraction
from infrastructure.verification.iam import check_iam
from infrastructure.verification.lambda_config import check_lambda_config
from infrastructure.verification.logging_checks import check_logging
from infrastructure.verification.models import CheckResult, VerificationReport
from infrastructure.verification.module_contract import check_module_contract
from infrastructure.verification.opentofu import (
    check_opentofu_contract,
    detect_tools,
    run_opentofu_cli_validation,
)
from infrastructure.verification.packaging import check_packaging
from infrastructure.verification.production_root import check_production_root
from infrastructure.verification.reporting import write_verification_report
from infrastructure.verification.runtime_adapter import check_runtime_adapter
from infrastructure.verification.safety import check_safety
from infrastructure.verification.scenarios import check_scenarios
from infrastructure.verification.scripts import check_scripts
from infrastructure.verification.state import check_state
from infrastructure.verification.structure import check_structure


def run_platform_deployment_foundation_verification(
    *,
    output_dir: Path | None = None,
    run_opentofu_cli: bool = True,
) -> VerificationReport:
    started = time.perf_counter()
    contract = default_contract()
    out = (
        output_dir or (infra_root() / "reports" / "verification")
    ).resolve()
    out.mkdir(parents=True, exist_ok=True)

    tools = detect_tools()
    checks: list[CheckResult] = []
    checks.extend(check_structure())
    checks.extend(check_opentofu_contract(tools))
    if run_opentofu_cli:
        status, cli_checks = run_opentofu_cli_validation(tools)
    else:
        status, cli_checks = tools.opentofu_validation_status, []
    checks.extend(cli_checks)
    checks.extend(check_module_contract())
    checks.extend(check_production_root())
    checks.extend(check_api_gateway())
    checks.extend(check_lambda_config())
    checks.extend(check_ecr())
    checks.extend(check_iam())
    checks.extend(check_logging())
    checks.extend(check_configuration())
    checks.extend(check_scripts())
    checks.extend(check_state())
    checks.extend(check_packaging())
    checks.extend(check_runtime_adapter())
    checks.extend(check_safety())
    checks.extend(check_extraction())
    checks.extend(check_scenarios())

    # Determinism: re-run structure inventory fingerprint.
    again = check_structure()
    checks.append(
        CheckResult(
            name="determinism:structure_stable",
            ok=[c.ok for c in again] == [c.ok for c in check_structure()],
            detail="structure checks stable",
            category="determinism",
        )
    )

    failures = [f"{c.name}:{c.detail}" for c in checks if not c.ok]
    by_category: dict[str, int] = {}
    for item in checks:
        by_category[item.category] = by_category.get(item.category, 0) + (
            0 if item.ok else 1
        )

    warnings = list(tools.warnings)
    if status == "not_executed_tool_unavailable":
        warnings.append(
            "OpenTofu CLI validation not executed because tofu is unavailable"
        )

    # PASS is allowed with tool limitation when static/runtime checks pass.
    report = VerificationReport(
        ok=not failures,
        verdict="pass" if not failures else "fail",
        infrastructure_module=MODULE_NAME,
        environment_name=ENVIRONMENT_NAME,
        opentofu_required_version=REQUIRED_OPENTOFU,
        aws_provider_version_constraint=AWS_PROVIDER_CONSTRAINT,
        packaging_strategy=PACKAGING_STRATEGY,
        api_gateway_type=API_GATEWAY_PROTOCOL,
        lambda_count=1,
        lambda_architecture=LAMBDA_ARCHITECTURE_DEFAULT,
        deployment_mode=DEPLOYMENT_MODE,
        authentication_posture=AUTHENTICATION_MODE,
        rate_limit_posture=RATE_LIMIT_MODE,
        ingestion_posture="disabled_fail_closed",
        opentofu_validation_status=status,
        terraform_tool_status=tools.terraform_tool_status,
        checks=tuple(checks),
        scenario_summary={
            "total_checks": len(checks),
            "failed_checks": len(failures),
            **{f"failed_{k}": v for k, v in by_category.items() if v},
        },
        defects=tuple(failures),
        warnings=tuple(warnings),
        limitations=tuple(contract.notes)
        + (
            ("OpenTofu CLI validate was not executed (tool unavailable).",)
            if status == "not_executed_tool_unavailable"
            else ()
        ),
        elapsed_ms=(time.perf_counter() - started) * 1000,
    )
    write_verification_report(report, out)
    return report
