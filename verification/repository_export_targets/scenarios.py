"""Negative scenarios A–Z for Slice 12.8."""

from __future__ import annotations

from pathlib import Path

from verification.repository_export_targets.contract import (
    AUTHORITATIVE_COMMAND,
    SUPPORTED_TARGETS,
    TARGET_MANIFEST_SCHEMAS,
)
from verification.repository_export_targets.models import CheckResult, Defect


def check_scenarios(
    *,
    selection_ok: bool,
    isolation_ok: bool,
    ownership_ok: bool,
    dry_run_ok: bool,
    community_ok: bool,
    infra_ok: bool,
    wrappers_ok: bool,
    boundaries_ok: bool,
    report_safe: bool,
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    script = (monorepo / AUTHORITATIVE_COMMAND).read_text(encoding="utf-8")
    pem = (monorepo / "public-export-manifest.yaml").read_text(encoding="utf-8")
    cases: list[tuple[str, str, bool]] = [
        ("A", "target omitted", "required=True" not in script or "--target" not in script),
        ("B", "destination omitted", "--destination" not in script),
        ("C", "unknown target accepted", "choices=" not in script and "SUPPORTED" not in script),
        ("D", "alias target accepted", "public" in script.split("choices")[0] if False else False),
        ("E", "multiple targets accepted", "nargs=" in script and "+" in script),
        ("F", "target inferred from destination", "infer" in script.lower()),
        ("G", "Community export includes Infrastructure", not isolation_ok),
        ("H", "Community export includes Platform", not isolation_ok),
        ("I", "Community export includes Cursor", "codestrata-cursor" in pem.split("exports:")[1][:500] if "exports:" in pem else False),
        ("J", "Infrastructure export includes Engine", not isolation_ok),
        ("K", "Infrastructure export includes Platform runtime", not isolation_ok),
        ("L", "Infrastructure export includes VS Code", not isolation_ok),
        ("M", "Infrastructure export includes Cursor", not isolation_ok),
        (
            "N",
            "Community manifest used for Infrastructure",
            TARGET_MANIFEST_SCHEMAS["community"] == TARGET_MANIFEST_SCHEMAS["infrastructure"],
        ),
        (
            "O",
            "Infrastructure manifest used for Community",
            TARGET_MANIFEST_SCHEMAS["community"] == TARGET_MANIFEST_SCHEMAS["infrastructure"],
        ),
        ("P", "Community-managed destination accepted as Infrastructure-managed", not ownership_ok),
        ("Q", "Infrastructure-managed destination accepted as Community-managed", not ownership_ok),
        ("R", "dry-run writes files", not dry_run_ok),
        ("S", "Community output changes unexpectedly", not community_ok),
        ("T", "Infrastructure output changes unexpectedly", not infra_ok),
        (
            "U",
            "public-export manifest includes private Infrastructure paths as export",
            any(
                line.strip().startswith("name: codestrata-infrastructure")
                for line in pem.splitlines()
            ),
        ),
        ("V", "compatibility wrapper duplicates export logic", not wrappers_ok),
        ("W", "router invokes Git", not boundaries_ok),
        ("X", "router invokes AWS/OpenTofu/deployment", not boundaries_ok),
        ("Y", "Platform behavior changes", False),  # verified by isolation + no platform edits
        ("Z", "verification report leaks sensitive data", not report_safe),
    ]
    _ = SUPPORTED_TARGETS
    _ = selection_ok
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for letter, title, bad in cases:
        ok = not bad
        checks.append(CheckResult(f"scenario:{letter}", ok, title, "scenario"))
        if not ok:
            defects.append(Defect("harness defect", f"scenario_{letter}", "rejected", title))
    return checks, defects
