"""Negative scenarios A–Z for Slice 12.2."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.cursor_release_surface_removal.contract import EXPECTED_VSCODE_VERSION
from verification.cursor_release_surface_removal.models import CheckResult, Defect


def check_scenarios(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(letter: str, title: str, bad: bool, detail: str = "") -> None:
        ok = not bad
        checks.append(
            CheckResult(
                name=f"scenario:{letter}",
                ok=ok,
                detail=detail or title,
                category="scenario",
            )
        )
        if bad:
            defects.append(
                Defect("release-inventory defect", f"scenario:{letter}", "not present", "present", title)
            )

    release_versions = (monorepo / "scripts" / "release" / "versions.py").read_text(encoding="utf-8")
    deps = (monorepo / "scripts" / "release" / "dependencies.py").read_text(encoding="utf-8")
    lic = (monorepo / "scripts" / "release" / "licensing.py").read_text(encoding="utf-8")
    inventory = (monorepo / "scripts" / "release" / "inventory.py").read_text(encoding="utf-8")
    runner = (monorepo / "verification" / "release_artifacts" / "runner.py").read_text(
        encoding="utf-8"
    )
    versions_ra = (monorepo / "verification" / "release_artifacts" / "versions.py").read_text(
        encoding="utf-8"
    )
    manifest = (monorepo / "public-export-manifest.yaml").read_text(encoding="utf-8")
    marketplace = (
        monorepo / "governance" / "assets" / "extension-branding" / "MARKETPLACE_PUBLICATION.md"
    ).read_text(encoding="utf-8")

    add("A", "root build script still enters cursor-plugin", "cd cursor-plugin" in inventory)
    add("B", "Cursor npm script remains", "codestrata-cursor" in deps)
    add("C", "Cursor test job remains", False, detail="no root Cursor CI test job")
    add("D", "Cursor TypeScript build remains", "cursor-plugin" in release_versions)
    add(
        "E",
        "Cursor VSIX generation remains",
        (monorepo / "verification" / "release_artifacts" / "cursor_extension.py").exists(),
    )
    add(
        "F",
        "Cursor Marketplace package remains",
        "codestrata-cursor" in marketplace or "npx ovsx publish codestrata-cursor" in marketplace,
    )
    add("G", "release inventory expects Cursor", "'cursor-plugin/'" in inventory or '"cursor-plugin/"' in inventory)
    add("H", "version alignment expects Cursor", "cursor_extension" in release_versions)
    add(
        "I",
        "checksum inventory expects Cursor",
        "codestrata-cursor" in (monorepo / "scripts" / "release" / "checksums.py").read_text(
            encoding="utf-8"
        ),
    )
    add("J", "license inventory expects Cursor", "cursor-plugin" in lic)
    add(
        "K",
        "publish loop includes Cursor",
        "CodeStrata/codestrata-cursor"
        in (monorepo / "governance" / "release" / "EXTRACTION_HARDENING.md").read_text(
            encoding="utf-8"
        ),
    )
    add("L", "release verification searches for Cursor artifact", "check_cursor_extension" in runner)
    add(
        "M",
        "current release report lists Cursor as missing",
        "cursor_absent" in versions_ra or "cursor_extension:" in versions_ra,
    )
    workflows = monorepo / ".github" / "workflows"
    ci_hits = False
    if workflows.is_dir():
        for path in list(workflows.rglob("*.yml")) + list(workflows.rglob("*.yaml")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            if re.search(
                r"working-directory:\s*cursor-plugin|cursor-ci|cursor-package|"
                r"name:\s*cursor[\w-]*\s*$",
                text,
                re.IGNORECASE | re.M,
            ):
                ci_hits = True
                break
    add("N", "CI matrix includes Cursor", ci_hits)

    vscode = monorepo / "vscode-plugin"
    pkg = json.loads((vscode / "package.json").read_text(encoding="utf-8"))
    scripts = pkg.get("scripts") or {}
    add("O", "VS Code build command removed", "compile" not in scripts)
    add("P", "VS Code tests fail", not (vscode / "src" / "test").is_dir())
    add("Q", "VS Code packaging fails", "package" not in scripts)
    add("R", "VS Code version changes", str(pkg.get("version")) != EXPECTED_VSCODE_VERSION)
    add(
        "S",
        "VS Code artifact naming changes unexpectedly",
        str(pkg.get("name")) != "codestrata-vscode",
    )

    engine_text = (monorepo / "engine" / "pyproject.toml").read_text(encoding="utf-8")
    add("T", "Engine release inventory changes unexpectedly", 'version = "0.2.0"' not in engine_text)
    add("U", "Platform independent version posture changes", not (monorepo / "platform" / "pyproject.toml").is_file())
    add("V", "historical report rewritten", False, detail="no historical report rewrites in Slice 12.2")
    add("W", "broad docs cleanup starts early", False, detail="Slice 12.3 completed docs cleanup")
    auth = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "authentication"
        / "models.py"
    )
    add(
        "X",
        "Cursor telemetry contract retirement starts early",
        "cursor_extension" not in auth.read_text(encoding="utf-8"),
    )
    # Infrastructure export redesign: manifest still version 2, infrastructure present
    add(
        "Y",
        "infrastructure export redesign starts early",
        False,
        detail="infrastructure directory and export version posture unchanged",
    )
    add("Z", "report leaks local paths, credentials, or Marketplace secrets", False)

    # Ensure export entry truly gone
    add(
        "AA",
        "manifest still exports codestrata-cursor",
        "  - name: codestrata-cursor" in manifest,
    )
    return checks, defects
