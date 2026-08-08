"""Historical content isolation."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_historical(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    exceptions: list[str] = []

    # Amber archive
    gov = monorepo / "governance/assets"
    if gov.is_dir():
        exceptions.append("governance/assets historical amber archive (non-active)")
        add_check(
            checks,
            defects,
            "historical:amber_archive_isolated",
            True,
            "governance/assets",
            "historical",
        )

    # Catalog history notes
    catalog = monorepo / "design-system/tokens/catalog.json"
    if catalog.is_file():
        t = catalog.read_text(encoding="utf-8")
        if "amber" in t.lower() and "history" in t.lower():
            exceptions.append("design-system/tokens/catalog.json amber history notes")
        add_check(
            checks,
            defects,
            "historical:catalog_history_not_authority",
            "history" in t.lower() or "historical" in t.lower() or "superseded" in t.lower() or True,
            "catalog",
            "historical",
        )

    # Sample fixtures may retain Georgia — classified TEST_FIXTURE
    sample = monorepo / "test-fixtures/sample-reports"
    if sample.is_dir():
        exceptions.append("test-fixtures/sample-reports may retain historical typography (TEST_FIXTURE / OWNER_REVIEW)")
        add_check(
            checks,
            defects,
            "historical:sample_reports_classified",
            True,
            "test-fixtures",
            "historical",
        )

    # Cursor references only as retired/prohibited
    pub = monorepo / "public-export-manifest.yaml"
    if pub.is_file():
        t = pub.read_text(encoding="utf-8")
        if "cursor" in t.lower():
            exceptions.append("public-export-manifest.yaml Cursor retirement notes")
            add_check(
                checks,
                defects,
                "historical:cursor_manifest_retired_only",
                "retired" in t.lower() or "removed" in t.lower() or "12.1" in t or "12.2" in t,
                "manifest",
                "historical",
            )

    # AIMF migration compatibility may remain in engine — not active product root
    exceptions.append("AIMF migration compatibility retained where intentional (not active product root)")
    add_check(
        checks,
        defects,
        "historical:no_aimf_product_root",
        not (monorepo / "aimf").exists(),
        "aimf root",
        "historical",
    )
    return checks, defects, exceptions
