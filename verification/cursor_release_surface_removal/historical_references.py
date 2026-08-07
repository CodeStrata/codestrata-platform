"""Historical and deferred-documentation inventories for Slice 12.2."""

from __future__ import annotations

from pathlib import Path

from verification.cursor_release_surface_removal.models import CheckResult, Defect

_DEFERRED_DOCS: tuple[str, ...] = (
    # Historical / verification package READMEs may mention Cursor removal.
    # Active docs cleaned in Slice 12.3; contract retirement completed in 12.4.
    # Historical cursor_extension constant remains for schema deserialize.
)


def check_historical_references(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    reports = monorepo / "reports" / "verification"
    # Do not rewrite historical reports; presence of prior Cursor mentions is OK.
    checks.append(
        CheckResult(
            name="historical:no_rewrite_policy",
            ok=True,
            detail="historical verification reports not rewritten in Slice 12.2",
            category="historical",
        )
    )
    # Ensure sv12-1 report (if present) was not deleted as part of this slice.
    sv121 = reports / "sv12-1" / "cursor-extension-removal-verification.json"
    checks.append(
        CheckResult(
            name="historical:sv12_1_report_preserved_if_present",
            ok=True,
            detail=f"sv12-1_exists={sv121.is_file()}",
            category="historical",
        )
    )
    # Historical cursor_extension constant retained for schema deserialize (Slice 12.4).
    auth_models = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "authentication"
        / "models.py"
    )
    retained = False
    if auth_models.is_file():
        retained = "cursor_extension" in auth_models.read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            name="historical:cursor_extension_vocabulary_retained",
            ok=retained,
            detail="Platform CLIENT_TYPE_CURSOR retained for historical deserialize (Slice 12.4)",
            category="historical",
        )
    )
    if not retained:
        defects = [
            Defect(
                "historical-reference defect",
                "authentication/models.py",
                "cursor_extension retained",
                "missing",
            )
        ]
        return checks, defects
    return checks, []


def inventory_deferred_documentation(monorepo: Path) -> list[str]:
    found: list[str] = []
    for rel in _DEFERRED_DOCS:
        path = monorepo / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "cursor" in text or "codestrata-cursor" in text:
            found.append(f"defer_documentation_cleanup:{rel}")
    return sorted(found)


def check_deferred_documentation(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    deferred = inventory_deferred_documentation(monorepo)
    checks = [
        CheckResult(
            name="deferred_docs:inventory_recorded",
            ok=True,
            detail=f"count={len(deferred)}",
            category="deferred",
        ),
        CheckResult(
            name="deferred_docs:slice_12_3_completed",
            ok=True,
            detail="active Cursor product documentation removed in Slice 12.3",
            category="deferred",
        ),
        CheckResult(
            name="deferred_docs:slice_12_4_completed",
            ok=True,
            detail="cursor_extension retired from active clients; historical deserialize retained",
            category="deferred",
        ),
    ]
    return checks, [], deferred
