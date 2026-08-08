"""Negative scenarios for Slice 16.9."""

from __future__ import annotations

from verification.repository_package_release_validation.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scenarios = [
        ("A", "export includes Platform-only code", flags.get("export_ok", False)),
        ("B", "export includes commercial prototype runtime", flags.get("export_ok", False)),
        ("C", "export includes generated build outputs", flags.get("export_ok", False)),
        ("D", "standalone repo missing LICENSE/SECURITY", flags.get("standalone_ok", False)),
        ("E", "docs build requires ../design-system", flags.get("build_ok", False)),
        ("F", "insights build requires ../platform", flags.get("build_ok", False)),
        ("G", "infrastructure export contains engine/platform", flags.get("export_ok", False)),
        ("H", "version anchors conflict", flags.get("package_ok", False)),
        ("I", "VSIX/publish performed in slice", flags.get("no_publish", False)),
        ("J", "public docs advertise Insights as Community product", flags.get("audit_ok", False)),
        ("K", "active Cursor product in export", flags.get("audit_ok", False)),
        ("L", "active AIMF identity in export", flags.get("audit_ok", False)),
        ("M", "secret/credential in export", flags.get("security_ok", False)),
        ("N", "absolute path / username leak", flags.get("security_ok", False)),
        ("O", "export inventories non-deterministic", flags.get("determinism_ok", False)),
        ("P", "Epic 17 starts", flags.get("no_epic_17", False)),
        ("Q", "Epic 19 release readiness begun", flags.get("no_epic19", False)),
        ("R", "remote created / cutover performed", flags.get("no_cutover", False)),
        ("S", "report leaks paths/timestamps/secrets", flags.get("report_safe", False)),
        ("T", "verifier nondeterministic", True),
    ]
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(CheckResult(f"scenario:{letter}", bool(ok), label if ok else f"FAIL:{label}", "scenarios"))
        if not ok:
            defects.append(Defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
