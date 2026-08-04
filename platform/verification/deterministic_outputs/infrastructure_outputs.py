"""Infrastructure verification (SV.9) repeated-run determinism."""

from __future__ import annotations

from pathlib import Path

from verification.deterministic_outputs.models import CheckResult


def check_infrastructure_outputs(monorepo: Path) -> list[CheckResult]:
    try:
        from infrastructure.verification.runner import (
            run_platform_deployment_foundation_verification,
        )
    except Exception as exc:  # noqa: BLE001
        return [
            CheckResult(
                name="infrastructure_import",
                ok=False,
                detail=type(exc).__name__,
                category="infrastructure",
            )
        ]

    # Skip OpenTofu CLI to keep offline/static and avoid tool-path noise.
    left = run_platform_deployment_foundation_verification(
        output_dir=monorepo / "platform/reports/verification/sv15/infra-a",
        run_opentofu_cli=False,
    )
    right = run_platform_deployment_foundation_verification(
        output_dir=monorepo / "platform/reports/verification/sv15/infra-b",
        run_opentofu_cli=False,
    )
    checks = [
        CheckResult(
            name="infrastructure_verdict_stable",
            ok=left.verdict == right.verdict,
            detail=f"verdict={left.verdict}",
            category="infrastructure",
        ),
        CheckResult(
            name="infrastructure_ok_stable",
            ok=bool(left.ok) == bool(right.ok),
            detail=f"ok={left.ok}",
            category="infrastructure",
        ),
        CheckResult(
            name="infrastructure_defects_stable",
            ok=list(left.defects or []) == list(right.defects or []),
            detail=f"defects={len(left.defects or [])}",
            category="infrastructure",
        ),
    ]
    # Operator home / harness tmp must not appear; OSS /home/runner is ignored.
    from verification.deterministic_outputs.fingerprints import (
        contains_forbidden_environment,
    )

    for label, report in (("a", left), ("b", right)):
        try:
            blob = str(report.to_dict())
        except Exception:
            blob = str(getattr(report, "__dict__", ""))
        hits = contains_forbidden_environment(blob)
        checks.append(
            CheckResult(
                name=f"infrastructure_no_home_path_{label}",
                ok=not hits,
                detail=f"hits={hits or 'none'}",
                category="infrastructure",
            )
        )
    return checks
