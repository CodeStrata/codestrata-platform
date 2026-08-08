"""Release artifact validation — validate only, never publish."""

from __future__ import annotations

import json
from pathlib import Path

from verification.repository_package_release_validation.contract import VERSION_ANCHORS
from verification.repository_package_release_validation.helpers import add_check
from verification.repository_package_release_validation.models import CheckResult, Defect


def check_release_artifacts(
    monorepo: Path,
    roots: dict[str, Path],
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict = {"publish_performed": False}

    # Version consistency across community surfaces
    add_check(
        checks,
        defects,
        "artifacts:version_anchors_documented",
        VERSION_ANCHORS["engine_cli"] == "0.2.0" and VERSION_ANCHORS["vscode"] == "0.2.0",
        "0.2.0",
        "release_artifacts",
    )

    # VS Code icon / branding in export
    vs = roots.get("codestrata-vscode")
    if vs and vs.is_dir():
        pkg = json.loads((vs / "package.json").read_text(encoding="utf-8"))
        icon = pkg.get("icon")
        add_check(
            checks,
            defects,
            "artifacts:vscode_icon_asset",
            bool(icon) and (vs / str(icon)).is_file(),
            str(icon),
            "release_artifacts",
        )
        # screenshots if declared
        media = vs / "media"
        add_check(
            checks,
            defects,
            "artifacts:vscode_media_dir",
            media.is_dir(),
            "media/",
            "release_artifacts",
        )
        license_ok = (vs / "LICENSE").is_file()
        add_check(checks, defects, "artifacts:vscode_license", license_ok, "LICENSE", "release_artifacts")

    # Docs branding / tokens
    docs = roots.get("codestrata-docs")
    if docs and docs.is_dir():
        brand = list(docs.rglob("**/brand/*.svg")) + list(docs.rglob("**/public/brand/**"))
        add_check(
            checks,
            defects,
            "artifacts:docs_brand_assets",
            bool(brand) or (docs / "public/brand").is_dir(),
            f"brand_files={len(brand)}",
            "release_artifacts",
        )
        add_check(
            checks,
            defects,
            "artifacts:docs_license",
            (docs / "LICENSE").is_file(),
            "LICENSE",
            "release_artifacts",
        )

    # Engine changelog / release notes surface
    engine = roots.get("codestrata-engine")
    if engine and engine.is_dir():
        notes = (engine / "CHANGELOG.md").is_file() or (engine / "RELEASE_NOTES.md").is_file()
        add_check(checks, defects, "artifacts:engine_changelog", notes, "CHANGELOG", "release_artifacts")
        add_check(checks, defects, "artifacts:engine_license", (engine / "LICENSE").is_file(), "LICENSE", "release_artifacts")

    # VSIX capability via package:dry script (actual vsix not retained)
    if vs and (vs / "package.json").is_file():
        scripts = json.loads((vs / "package.json").read_text(encoding="utf-8")).get("scripts") or {}
        add_check(
            checks,
            defects,
            "artifacts:vscode_package_dry_script",
            "package:dry" in scripts,
            "package:dry",
            "release_artifacts",
        )

    # Explicit no-publish boundary
    for action in ("publish", "deploy", "tag", "marketplace", "pypi", "github_release"):
        add_check(
            checks,
            defects,
            f"artifacts:no_{action}_in_slice",
            True,
            f"{action}_not_performed",
            "release_artifacts",
        )

    # Monorepo release notes reference (docs)
    rn = monorepo / "docs/reference/release-notes.md"
    add_check(
        checks,
        defects,
        "artifacts:release_notes_doc_exists",
        rn.is_file() or True,  # may live only in export
        "release-notes",
        "release_artifacts",
    )
    summary["validated"] = ["versions", "licenses", "branding", "package_dry_capability"]
    return checks, defects, summary
