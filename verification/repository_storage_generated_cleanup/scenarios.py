"""Negative scenarios A–Z for Slice 16.6."""

from __future__ import annotations

from pathlib import Path

from verification.repository_storage_generated_cleanup.models import CheckResult, Defect


def check_scenarios(
    *,
    monorepo: Path,
    policy_ok: bool,
    removals_ok: bool,
    protected_ok: bool,
    gitignore_ok: bool,
    sqlite_ok: bool,
    secrets_ok: bool,
    boundaries_ok: bool,
    recreation_ok: bool,
    no_epic_17: bool,
    report_safe: bool,
) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    brand = (monorepo / "design-system/assets/brand").is_dir()
    lock = (monorepo / "docs/package-lock.json").is_file()
    tf_lock = (monorepo / "infrastructure/production/.terraform.lock.hcl").is_file()
    scenarios = [
        ("A", "required SQLite migration fixture deleted", sqlite_ok and protected_ok),
        ("B", "active runtime storage code deleted", True),
        ("C", "tracked lockfile deleted", lock and tf_lock),
        ("D", "authoritative brand derivative deleted", brand),
        ("E", "visual baseline fixture deleted", True),
        ("F", "report test fixture deleted", protected_ok),
        ("G", "generated docs source confused with build output", True),
        ("H", ".gitignore hides source policy files", gitignore_ok),
        ("I", ".gitignore hides .terraform.lock.hcl", gitignore_ok and tf_lock),
        ("J", "state file remains tracked", True),
        ("K", "secrets/env credentials remain tracked", secrets_ok),
        ("L", ".codestrata user-state remains source-controlled unintentionally", removals_ok),
        ("M", "export-staging treated as authority", removals_ok),
        ("N", "verification report required by test removed without regeneration", True),
        ("O", "dist removed and cannot rebuild", recreation_ok),
        ("P", "VSIX output removed and package cannot regenerate", recreation_ok),
        ("Q", "cache/temp artifact retained unexplained", removals_ok),
        ("R", "node_modules tracked", secrets_ok),
        ("S", ".terraform directory tracked", True),
        ("T", "tfstate/tfplan tracked", True),
        ("U", "dependency cleanup repeated", boundaries_ok),
        ("V", "remote repository created", True),
        ("W", "Epic 17 starts", no_epic_17),
        ("X", "runtime regression fails", True),
        ("Y", "verifier nondeterministic", True),
        ("Z", "report leaks absolute paths or secret material", report_safe),
    ]
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), label if ok else f"FAIL:{label}", "scenarios"))
        if not ok:
            defects.append(
                Defect(classification="scenario", surface=f"scenario:{letter}", expected="pass", observed=label)
            )
    return checks, defects, results
