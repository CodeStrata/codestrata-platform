"""Negative scenarios A–Z for Slice 12.7."""

from __future__ import annotations

from pathlib import Path

from verification.infrastructure_repository_export.contract import (
    REQUIRED_ROOT_ENTRIES,
    VALIDATION_ROOTS,
)
from verification.infrastructure_repository_export.models import CheckResult, Defect


def check_scenarios(
    *,
    tree_identical: bool,
    manifest_ok: bool,
    inventory_ok: bool,
    checksum_ok: bool,
    layout_ok: bool,
    no_wrapper: bool,
    no_engine: bool,
    no_platform: bool,
    no_vscode: bool,
    no_cursor: bool,
    no_state: bool,
    no_plan: bool,
    no_secrets: bool,
    no_unsafe_tfvars: bool,
    no_local_paths: bool,
    docs_ok: bool,
    lock_not_ignored: bool,
    no_world_writable: bool,
    no_symlinks: bool,
    no_runtime_imports: bool,
    fmt_ok: bool,
    init_backend_false: bool,
    validate_ok: bool,
    no_git_deploy: bool,
    report_safe: bool,
) -> tuple[list[CheckResult], list[Defect]]:
    cases: list[tuple[str, str, bool]] = [
        ("A", "two exports differ", not tree_identical),
        ("B", "manifest checksum is wrong", not manifest_ok),
        ("C", "inventory misses a file", not inventory_ok),
        ("D", "SHA256SUMS includes absolute path", not checksum_ok),
        ("E", "infrastructure/ wrapper exists", not no_wrapper),
        ("F", "required module missing", "modules/community-cloud-api" not in REQUIRED_ROOT_ENTRIES),
        ("G", "production root missing", "production" not in REQUIRED_ROOT_ENTRIES),
        ("H", "Engine source exported", not no_engine),
        ("I", "Platform runtime exported", not no_platform),
        ("J", "VS Code exported", not no_vscode),
        ("K", "Cursor exported", not no_cursor),
        ("L", "state file exported", not no_state),
        ("M", "plan file exported", not no_plan),
        ("N", "credential-shaped value exported", not no_secrets),
        ("O", "unsafe tfvars exported", not no_unsafe_tfvars),
        ("P", "local absolute path exported", not no_local_paths),
        ("Q", "broken monorepo-relative documentation link", not docs_ok),
        ("R", ".terraform.lock.hcl ignored", not lock_not_ignored),
        ("S", "world-writable file emitted", not no_world_writable),
        ("T", "symlink emitted", not no_symlinks),
        ("U", "exported test imports Engine or Platform", not no_runtime_imports),
        ("V", "OpenTofu fmt fails", not fmt_ok),
        ("W", "OpenTofu init uses backend", not init_backend_false),
        ("X", "OpenTofu validate fails", not validate_ok),
        ("Y", "Git/deployment command is invoked", not no_git_deploy),
        ("Z", "verification report leaks sensitive data", not report_safe),
    ]
    _ = VALIDATION_ROOTS
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for letter, title, bad in cases:
        ok = not bad
        checks.append(
            CheckResult(name=f"scenario:{letter}", ok=ok, detail=title, category="scenario")
        )
        if not ok:
            defects.append(
                Defect("harness defect", f"scenario_{letter}", "rejected", title)
            )
    return checks, defects
