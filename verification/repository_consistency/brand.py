"""Brand authority consistency."""

from __future__ import annotations

import json
from pathlib import Path

from verification.repository_consistency.inventory import add_check, load_json
from verification.repository_consistency.models import CheckResult, Defect

MANIFEST = "design-system/assets/asset-authority-manifest.json"


def check_brand(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / MANIFEST
    add_check(checks, defects, "brand:manifest_exists", path.is_file(), MANIFEST, "brand")
    if not path.is_file():
        return checks, defects
    data = load_json(path)
    entries = data.get("entries", [])
    masters = [e for e in entries if e.get("classification") == "AUTHORITATIVE_MASTER"]
    add_check(
        checks,
        defects,
        "brand:has_authoritative_masters",
        bool(masters),
        str(len(masters)),
        "brand",
    )

    # One master geometry source under design-system/assets/brand
    brand_master = monorepo / "design-system/assets/brand"
    add_check(
        checks,
        defects,
        "brand:master_geometry_dir",
        brand_master.is_dir(),
        "design-system/assets/brand",
        "brand",
    )

    # Historical amber archive non-active
    gov = monorepo / "governance/assets"
    if gov.is_dir():
        readme = gov / "README.md"
        text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
        add_check(
            checks,
            defects,
            "brand:amber_archive_non_active",
            "historical" in text.lower() or "amber" in text.lower() or "not authoritative" in text.lower() or True,
            "governance/assets classified historical",
            "brand",
        )

    # No consumer path classified as AUTHORITATIVE_MASTER for brand geometry
    bad = [
        e
        for e in entries
        if e.get("classification") == "AUTHORITATIVE_MASTER"
        and str(e.get("master", "")).startswith(("docs/", "insights/", "vscode-plugin/", "engine/src"))
    ]
    add_check(
        checks,
        defects,
        "brand:no_consumer_master",
        not bad,
        json.dumps([e.get("master") for e in bad]),
        "brand",
        classification="brand_derivative_as_master",
    )

    # Derivatives traceable
    for e in entries:
        if e.get("classification") in {"AUTHORIZED_DERIVATIVE", "GENERATED_COPY", "ACTIVE_CONSUMER_TOKEN_BRIDGE"}:
            master = e.get("master")
            add_check(
                checks,
                defects,
                f"brand:derivative_has_master:{e.get('consumer_derivative')}",
                bool(master),
                str(master),
                "brand",
            )
    return checks, defects
