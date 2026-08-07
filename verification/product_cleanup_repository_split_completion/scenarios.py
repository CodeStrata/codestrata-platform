"""Negative scenarios A–Z for Slice 12.10."""

from __future__ import annotations

from pathlib import Path

from verification.product_cleanup_repository_split_completion.models import (
    CheckResult,
    Defect,
)


def check_scenarios(
    *,
    monorepo: Path,
    slices_complete: int,
    cursor_ok: bool,
    release_ok: bool,
    docs_ok: bool,
    retired_ok: bool,
    vscode_ok: bool,
    infra_contract_ok: bool,
    exporter_ok: bool,
    export_ok: bool,
    targets_ok: bool,
    ci_ok: bool,
    schema_ok: bool,
    epic13_ok: bool,
    report_safe: bool,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "fewer than 10 slices complete", slices_complete == 10),
        ("B", "Cursor directory exists", cursor_ok and not (monorepo / "cursor-plugin").exists()),
        ("C", "Cursor build/package/release surface exists", release_ok),
        ("D", "current docs claim Cursor support", docs_ok),
        ("E", "Cursor remains active client", retired_ok),
        ("F", "historical Cursor record cannot deserialize", retired_ok),
        ("G", "VS Code missing or version changed", vscode_ok),
        ("H", "Infrastructure contract missing", infra_contract_ok),
        ("I", "Infrastructure exporter missing", exporter_ok),
        ("J", "Infrastructure export nondeterministic", export_ok),
        ("K", "Infrastructure export contains Engine/Platform/VS Code/Cursor", export_ok),
        ("L", "Infrastructure export contains state/plan/credential", export_ok),
        ("M", "exported tests require monorepo runtime", export_ok),
        ("N", "OpenTofu validation fails", export_ok),
        ("O", "third export target present", targets_ok),
        ("P", "Community contains Infrastructure", targets_ok),
        ("Q", "Infrastructure contains Community product source", targets_ok),
        ("R", "target ownership can cross", targets_ok),
        ("S", "Cursor CI/release job remains", ci_ok and release_ok),
        ("T", "CI configures AWS credentials", ci_ok),
        ("U", "CI runs plan/apply/destroy", ci_ok),
        ("V", "CI publishes/deploys", ci_ok),
        ("W", "Infrastructure tied automatically to Engine version/tag", schema_ok),
        ("X", "product schema changed", schema_ok),
        ("Y", "Epic 13 implementation exists", epic13_ok),
        ("Z", "completion report leaks sensitive data", report_safe),
    ]
    for letter, title, ok in scenarios:
        checks.append(
            CheckResult(f"scenario:{letter}", bool(ok), title, "scenarios")
        )
    if not all(c.ok for c in checks):
        failed = [c.name for c in checks if not c.ok]
        defects.append(
            Defect(
                "harness defect",
                "scenarios",
                "all pass",
                ",".join(failed),
            )
        )
    return checks, defects
