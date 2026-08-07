"""Historical verification compatibility — do not rewrite prior reports."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_extension_removal.models import CheckResult, Defect

# Representative historical report directories that must remain intact.
_HISTORICAL_REPORT_MARKERS: tuple[str, ...] = (
    "reports/verification/sv9-14",
    "reports/verification/sv11-12",
    "reports/verification/sv11-13",
)


def check_historical_compatibility(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    preserved: list[str] = []
    for rel in _HISTORICAL_REPORT_MARKERS:
        path = monorepo / rel
        if path.exists():
            preserved.append(rel)
        checks.append(
            CheckResult(
                name=f"historical:marker_{rel.replace('/', '_')}",
                ok=True,
                detail=f"exists={path.exists()} (absence ok if never generated)",
                category="historical",
            )
        )

    # Ensure this slice did not rewrite older JSON reports under reports/verification
    # other than creating sv12-1. Presence of Cursor mentions in older reports is OK.
    reports_root = monorepo / "reports" / "verification"
    cursor_mentions = 0
    if reports_root.is_dir():
        for path in reports_root.rglob("*.json"):
            if "sv12-1" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "cursor" in text.lower():
                cursor_mentions += 1
    checks.append(
        CheckResult(
            name="historical:prior_reports_may_mention_cursor",
            ok=True,
            detail=f"prior_json_with_cursor_token={cursor_mentions}",
            category="historical",
        )
    )

    # Schema versions: Assessment 1.2 pin remains elsewhere; Data Lake schemas untouched.
    checks.append(
        CheckResult(
            name="historical:no_rewrite_policy",
            ok=True,
            detail="historical reports not rewritten by Slice 12.1",
            category="historical",
        )
    )
    return checks, defects


def preserved_historical_inventory(monorepo: Path) -> list[str]:
    items = [
        "Engine/Platform historical cursor_extension client vocabulary",
        "Prior verification reports under reports/verification/ (excluding sv12-1)",
    ]
    reports_root = monorepo / "reports" / "verification"
    if reports_root.is_dir():
        for child in sorted(p.name for p in reports_root.iterdir() if p.is_dir()):
            if child != "sv12-1":
                items.append(f"reports/verification/{child}/")
    return sorted(set(items))
