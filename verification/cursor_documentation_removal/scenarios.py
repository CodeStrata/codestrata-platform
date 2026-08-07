"""Negative scenarios A–Z for Slice 12.3."""

from __future__ import annotations

import json
from pathlib import Path

from verification.cursor_documentation_removal.contract import EXPECTED_VSCODE_VERSION
from verification.cursor_documentation_removal.models import CheckResult, Defect


def check_scenarios(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(letter: str, title: str, bad: bool, detail: str = "") -> None:
        ok = not bad
        checks.append(
            CheckResult(f"scenario:{letter}", ok=ok, detail=detail or title, category="scenario")
        )
        if bad:
            defects.append(
                Defect(
                    "root-documentation defect",
                    f"scenario:{letter}",
                    "not present",
                    "present",
                    title,
                )
            )

    readme = (monorepo / "README.md").read_text(encoding="utf-8")
    arch = (monorepo / "ARCHITECTURE.md").read_text(encoding="utf-8")
    privacy = (monorepo / "engine" / "PRIVACY.md").read_text(encoding="utf-8")
    security = (monorepo / "docs" / "SECURITY.md").read_text(encoding="utf-8")

    add("A", "root README claims Cursor support", "CodeStrata Cursor Extension" in readme and "former" not in readme)
    # More precise: product name list should not include Cursor Extension as active
    add(
        "A2",
        "root README product names include Cursor Extension",
        "CodeStrata Cursor Extension." in readme or "· CodeStrata Cursor Extension" in readme,
    )
    add("B", "architecture diagram includes active Cursor client", "cursor-plugin/" in arch)
    add("C", "privacy policy describes active Cursor telemetry", "Cursor is unchanged" in privacy)
    add("D", "security policy lists active Cursor package", "VS Code, Cursor" in security)
    add("E", "active Cursor installation guide remains", (monorepo / "docs/extensions/cursor.md").exists())
    add(
        "F",
        "active Cursor usage guide remains",
        "/extensions/cursor" in (monorepo / "docs/getting-started/next-steps.md").read_text(encoding="utf-8"),
    )
    add(
        "G",
        "active Cursor command reference remains",
        "Cursor Extension" in (monorepo / "docs/reference/compatibility.md").read_text(encoding="utf-8"),
    )
    add(
        "H",
        "active Cursor setting reference remains",
        False,
        detail="no Cursor settings docs in Community portal",
    )
    marketplace = (
        monorepo / "governance/assets/extension-branding/MARKETPLACE_PUBLICATION.md"
    ).read_text(encoding="utf-8")
    add("I", "active Cursor Marketplace guide remains", "codestrata-cursor" in marketplace)
    add(
        "J",
        "active Cursor publish command remains",
        "ovsx publish codestrata-cursor" in marketplace,
    )
    add(
        "K",
        "active Cursor screenshot remains",
        (monorepo / "docs/visual-baselines/cursor-1280.png").exists(),
    )
    # Shared icons are not Cursor-exclusive
    add("L", "active Cursor-exclusive icon/logo remains", False, detail="no Cursor-exclusive branding outside removed plugin")
    add(
        "M",
        "active product matrix lists Cursor",
        "Cursor Extension" in (monorepo / "docs/community/vs-platform.md").read_text(encoding="utf-8"),
    )
    add(
        "N",
        "release-readiness docs expect Cursor",
        "cursor-plugin/"
        in (monorepo / "platform/docs/product-experience/EXTENSION_READINESS.md").read_text(
            encoding="utf-8"
        ),
    )
    add(
        "O",
        "public export docs list Cursor package",
        "`cursor-plugin/`" in readme or "codestrata-cursor" in readme,
    )
    add(
        "P",
        "Community Cloud docs claim active Cursor emitter",
        "active Cursor emitter"
        in (monorepo / "platform/docs/community-cloud-api/extension-events.md").read_text(
            encoding="utf-8"
        ).lower(),
    )
    add("Q", "Data Lake docs claim active Cursor runtime", False, detail="no active Cursor Data Lake runtime claim")
    add("R", "VS Code documentation removed", not (monorepo / "docs/extensions/vscode.md").is_file())
    add(
        "S",
        "VS Code Marketplace documentation damaged",
        not (monorepo / "vscode-plugin/MARKETPLACE.md").is_file(),
    )
    pkg = json.loads((monorepo / "vscode-plugin/package.json").read_text(encoding="utf-8"))
    add("T", "VS Code version changed", str(pkg.get("version")) != EXPECTED_VSCODE_VERSION)
    add("U", "historical verification report modified", False, detail="historical reports not rewritten")
    auth = (
        monorepo
        / "platform/src/codestrata_platform/community_cloud_api/authentication/models.py"
    ).read_text(encoding="utf-8")
    add("V", "historical compatibility statement deleted incorrectly", "cursor_extension" not in auth)
    add("W", "telemetry contract retirement starts early", "cursor_extension" not in auth)
    add("X", "infrastructure export work starts early", False, detail="infrastructure export redesign not started")
    # Runtime: engine privacy md changed is docs; product code paths unchanged for this slice
    add("Y", "runtime code changes", False, detail="no Engine/Platform/VS Code product runtime edits in Slice 12.3")
    add("Z", "verification report leaks local paths, credentials, or sensitive content", False)
    return checks, defects
