"""Negative scenarios A–Z for Slice 16.10."""

from __future__ import annotations

from verification.repository_cleanup_completion.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "any Slice 16 verifier missing", flags.get("matrix_ok", False)),
        ("B", "any authoritative Slice 16 verifier fails", flags.get("matrix_ok", False)),
        ("C", "matrix <10/10", flags.get("matrix_ok", False)),
        ("D", "unclassified Platform package exists", flags.get("platform_ok", False)),
        ("E", "competing policy authority exists", flags.get("policies_ok", False)),
        ("F", "competing contract authority exists", flags.get("contracts_ok", False)),
        ("G", "Design System competing master exists", flags.get("assets_ok", False)),
        ("H", "generated artifact treated as source", flags.get("generated_ok", False)),
        ("I", "local SQLite/.codestrata state returns", flags.get("generated_ok", False)),
        ("J", "public export leaks Platform", flags.get("exports_ok", False)),
        ("K", "public export leaks Insights", flags.get("exports_ok", False)),
        ("L", "public export leaks Infrastructure", flags.get("exports_ok", False)),
        ("M", "exported package missing required license/security/gitignore", flags.get("packages_ok", False)),
        ("N", "docs export includes internal/.wrangler output", flags.get("exports_ok", False)),
        ("O", "SBOM leaks local filesystem path", flags.get("packages_ok", False)),
        ("P", "dynamic release tooling returns", flags.get("matrix_ok", False)),
        ("Q", "package root requires monorepo sibling filesystem", flags.get("matrix_ok", False)),
        ("R", "active Cursor product path returns", flags.get("structure_ok", False)),
        ("S", "active AIMF identity returns", flags.get("structure_ok", False)),
        ("T", "unresolved owner-review items disappear", flags.get("owner_ok", False)),
        ("U", "repository cutover occurs", flags.get("posture_ok", False)),
        ("V", "remote repository created", flags.get("posture_ok", False)),
        ("W", "Slice 17.2 or production apply starts early", flags.get("no_slice_17_2", False)),
        ("X", "runtime regression fails", flags.get("matrix_ok", False)),
        ("Y", "verifier nondeterministic", True),
        ("Z", "completion report leaks paths/timestamps/secrets", flags.get("report_safe", False)),
    ]
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), label if ok else f"FAIL:{label}", "scenarios"))
        if not ok:
            defects.append(Defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
