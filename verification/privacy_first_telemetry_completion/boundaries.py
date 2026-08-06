"""Boundary and Epic 10 absence checks."""

from __future__ import annotations

from pathlib import Path

from verification.privacy_first_telemetry.boundaries import check_boundaries as check_914_boundaries
from verification.privacy_first_telemetry.vscode_inputs import load_vscode_inventory
from verification.privacy_first_telemetry_completion.models import CheckResult, Defect

_EPIC10_GLOBS = (
    "**/epic10/**",
    "**/epic_10/**",
    "**/analytics_dashboard/**",
    "**/telemetry_aggregation/**",
    "**/release_adoption/**",
)


def check_boundaries(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, str]]:
    vscode = load_vscode_inventory(monorepo)
    raw_checks, raw_defects = check_914_boundaries(monorepo, vscode)
    checks = [
        CheckResult(name=c.name, ok=c.ok, detail=c.detail, category=c.category)
        for c in raw_checks
    ]
    defects = [
        Defect(
            classification=d.classification,
            component=d.component,
            expected=d.expected,
            actual=d.actual,
            detail=d.detail,
        )
        for d in raw_defects
    ]

    statuses = {
        "platform_boundary_status": (
            "pass"
            if all(c.ok for c in checks if "platform" in c.name or "aws" in c.name)
            else "fail"
        ),
        "data_lake_boundary_status": (
            "pass"
            if all(c.ok for c in checks if "data_lake" in c.name or "aws" in c.name)
            else "fail"
        ),
        "cursor_boundary_status": (
            "pass" if all(c.ok for c in checks if "cursor" in c.name) else "fail"
        ),
    }
    # Strengthen data-lake: ensure no data_lake import in engine telemetry.
    engine_tel = monorepo / "engine" / "src" / "codestrata" / "telemetry"
    lake_hits = []
    for path in sorted(engine_tel.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("#"):
                continue
            if s.startswith(("import ", "from ")) and (
                "data_lake" in s or "community_data_lake" in s
            ):
                lake_hits.append(path.name)
    checks.append(
        CheckResult(
            name="engine_no_data_lake_imports",
            ok=not lake_hits,
            detail=str(lake_hits[:3]) if lake_hits else "clean",
            category="boundary",
        )
    )
    if lake_hits:
        statuses["data_lake_boundary_status"] = "fail"
        defects.append(
            Defect(
                classification="boundary defect",
                component="engine",
                expected="no data_lake imports",
                actual=str(lake_hits[:3]),
            )
        )
    return checks, defects, statuses


def check_epic10_absence(monorepo: Path) -> tuple[str, list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    hits: list[str] = []
    for pattern in _EPIC10_GLOBS:
        for path in monorepo.glob(pattern):
            # Ignore docs mentioning epic 10 in filenames under docs if any
            rel = str(path.relative_to(monorepo))
            if rel.startswith(("docs/", "engine/docs/", "verification/")) and path.is_file():
                # Allow documentation references only for files under docs that are .md
                if path.suffix == ".md":
                    continue
            hits.append(Path(rel).as_posix())

    # Also search for package directories that look like Epic 10 product work.
    for candidate in (
        "platform/src/codestrata_platform/analytics_dashboard",
        "platform/src/codestrata_platform/telemetry_aggregation",
        "engine/src/codestrata/telemetry/installation_identity_v2.py",
        "engine/src/codestrata/telemetry/anonymous_analytics.py",
    ):
        if (monorepo / candidate).exists():
            hits.append(candidate)

    checks.append(
        CheckResult(
            name="epic10_packages_absent",
            ok=not hits,
            detail=str(hits[:5]) if hits else "absent",
            category="epic10",
        )
    )
    # Privacy-first must not reintroduce installation ID generation on product path.
    from codestrata.telemetry.runtime_policy import default_runtime_policy

    checks.append(
        CheckResult(
            name="epic10_no_installation_identity_runtime",
            ok=default_runtime_policy().installation_id_allowed is False,
            detail="installation_id_allowed=False",
            category="epic10",
        )
    )

    status = "pass" if all(c.ok for c in checks) else "fail"
    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="boundary defect",
                    component="epic10",
                    expected="absent",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return status, checks, defects
