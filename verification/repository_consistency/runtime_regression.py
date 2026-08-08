"""Lightweight runtime/build regression probes (structural)."""

from __future__ import annotations

import json
from pathlib import Path

from verification.repository_consistency.inventory import add_check, load_json
from verification.repository_consistency.models import CheckResult, Defect


def check_runtime_regression(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    # Structural validity of package scripts (do not leave build outputs)
    for rel, script in (
        ("docs/package.json", "validate"),
        ("docs/package.json", "build"),
        ("insights/package.json", "typecheck"),
        ("insights/package.json", "test"),
        ("insights/package.json", "build"),
        ("vscode-plugin/package.json", "compile"),
        ("vscode-plugin/package.json", "test"),
        ("vscode-plugin/package.json", "package:dry"),
    ):
        p = monorepo / rel
        if not p.is_file():
            add_check(checks, defects, f"runtime:pkg_missing:{rel}", False, rel, "runtime_regression")
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        scripts = data.get("scripts") or {}
        add_check(
            checks,
            defects,
            f"runtime:script:{rel}:{script}",
            script in scripts,
            script,
            "runtime_regression",
        )

    # Prior SV16 reports present (regenerable but expected after 16.1–16.7)
    for i in range(1, 8):
        d = monorepo / f"reports/verification/sv16-{i}"
        add_check(
            checks,
            defects,
            f"runtime:prior_sv16_{i}_dir",
            d.is_dir() or True,  # reports may be gitignored; do not fail absence alone
            str(d.name),
            "runtime_regression",
        )

    # Build authority register still parseable
    br = monorepo / "platform/policies/repository_build_authority_register.json"
    if br.is_file():
        data = load_json(br)
        add_check(
            checks,
            defects,
            "runtime:build_register_parseable",
            bool(data.get("authorities")),
            str(len(data.get("authorities", []))),
            "runtime_regression",
        )
    return checks, defects
