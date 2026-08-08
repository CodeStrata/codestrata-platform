"""Code posture consistency (16.3)."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_code(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    add_check(
        checks,
        defects,
        "code:no_cursor_plugin_root",
        not (monorepo / "cursor-plugin").exists(),
        "cursor-plugin",
        "code",
    )
    add_check(
        checks,
        defects,
        "code:no_codestrata_cursor_root",
        not (monorepo / "codestrata-cursor").exists(),
        "codestrata-cursor",
        "code",
    )

    # Dead duplicate suppressed in 16.3
    add_check(
        checks,
        defects,
        "code:no_engine_suppression_module",
        not any((monorepo / "engine").rglob("**/suppression.py")),
        "engine suppression.py absent",
        "code",
    )
    add_check(
        checks,
        defects,
        "code:no_generate_slice_413",
        not (monorepo / "engine/scripts/generate_slice_413.py").exists(),
        "generate_slice_413.py",
        "code",
    )

    # Public API intact: engine package exists
    add_check(
        checks,
        defects,
        "code:engine_package_present",
        (monorepo / "engine/src/codestrata").is_dir(),
        "engine/src/codestrata",
        "code",
    )
    add_check(
        checks,
        defects,
        "code:vscode_package_present",
        (monorepo / "vscode-plugin/package.json").is_file(),
        "vscode-plugin/package.json",
        "code",
    )

    # AIMF active identity in package names
    aimf_pkgs = []
    for p in (monorepo / "engine").rglob("pyproject.toml"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        if re_search_aimf_active(t):
            aimf_pkgs.append(str(p.relative_to(monorepo)))
    add_check(
        checks,
        defects,
        "code:no_aimf_active_package_identity",
        not aimf_pkgs,
        ",".join(aimf_pkgs) or "none",
        "code",
    )
    return checks, defects


def re_search_aimf_active(text: str) -> bool:
    import re

    if re.search(r'(?m)^name\s*=\s*["\']aimf', text, re.I):
        return True
    if re.search(r"(?i)aimf-cli|aimf-engine", text):
        return True
    return False
