"""Packaging boundary checks (Slice 10.9 completion)."""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.models import CheckResult, Defect


def check_packaging(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    checks.append(
        CheckResult(
            "packaging:completion_package_outside_engine_runtime",
            ok=(monorepo / "verification" / "anonymous_analytics_completion").is_dir()
            and not (monorepo / "engine" / "src" / "codestrata" / "verification").exists(),
            category="packaging",
        )
    )
    checks.append(
        CheckResult(
            "packaging:privacy_package_outside_engine_runtime",
            ok=(monorepo / "verification" / "anonymous_analytics_privacy").is_dir(),
            category="packaging",
        )
    )
    checks.append(
        CheckResult(
            "packaging:engine_analytics_package_present",
            ok=(
                monorepo
                / "engine" / "src" / "codestrata" / "telemetry" / "analytics" / "__init__.py"
            ).is_file(),
            category="packaging",
        )
    )
    checks.append(
        CheckResult(
            "packaging:vscode_analytics_package_present",
            ok=(
                monorepo / "vscode-plugin" / "src" / "telemetry" / "analytics" / "index.ts"
            ).is_file(),
            category="packaging",
        )
    )
    checks.append(
        CheckResult(
            "packaging:no_verification_package_under_engine_src",
            ok=not list(
                (monorepo / "engine" / "src").rglob("anonymous_analytics_completion")
            )
            and not list((monorepo / "engine" / "src").rglob("anonymous_analytics_privacy")),
            category="packaging",
        )
    )
    checks.append(
        CheckResult(
            "packaging:no_verification_package_under_vscode_src",
            ok=not list(
                (monorepo / "vscode-plugin" / "src").rglob("*anonymous_analytics_completion*")
            ),
            category="packaging",
        )
    )

    for item in checks:
        if not item.ok:
            defects.append(Defect("packaging/public-export defect", item.name, "pass", "fail"))
    return checks, defects
