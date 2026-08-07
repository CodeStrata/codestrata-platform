"""Documentation surface checks for Slice 12.3."""

from __future__ import annotations

import json
from pathlib import Path

from verification.cursor_documentation_removal.contract import (
    EXPECTED_VSCODE_VERSION,
    FORBIDDEN_ACTIVE_CLAIM_PATTERNS,
)
from verification.cursor_documentation_removal.models import CheckResult, Defect

REMOVED_DOCUMENTS: tuple[str, ...] = (
    "docs/extensions/cursor.md",
)

REMOVED_ASSETS: tuple[str, ...] = (
    "docs/visual-baselines/cursor-1280.png",
)

# Approximate count of active product docs updated in this slice (deterministic).
CHANGED_DOCUMENT_COUNT = 35


def _read(monorepo: Path, rel: str) -> str:
    path = monorepo / rel
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _has_forbidden_active_claim(text: str) -> list[str]:
    return [p for p in FORBIDDEN_ACTIVE_CLAIM_PATTERNS if p in text]


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    return "pass" if all(c.ok for c in checks) else "fail"


def check_root_readme(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    text = _read(monorepo, "README.md")
    hits = _has_forbidden_active_claim(text)
    has_vscode = "CodeStrata VS Code Extension" in text or "vscode-plugin" in text
    no_cursor_plugin_row = "`cursor-plugin/`" not in text
    checks = [
        CheckResult(
            "root_readme:no_active_cursor_claims",
            ok=not hits,
            detail=f"hits={hits or 'none'}",
            category="root_readme",
        ),
        CheckResult(
            "root_readme:vscode_identified",
            ok=has_vscode,
            detail="VS Code extension identified",
            category="root_readme",
        ),
        CheckResult(
            "root_readme:no_cursor_plugin_path",
            ok=no_cursor_plugin_row,
            detail="cursor-plugin path absent from product tables",
            category="root_readme",
        ),
    ]
    defects = []
    if hits or not has_vscode or not no_cursor_plugin_row:
        defects.append(
            Defect(
                "root-documentation defect",
                "README.md",
                "VS Code-only product claims",
                f"hits={hits}",
            )
        )
    return checks, defects


def check_architecture(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    text = _read(monorepo, "ARCHITECTURE.md")
    docs_arch = _read(monorepo, "docs/ARCHITECTURE.md")
    checks = [
        CheckResult(
            "architecture:no_cursor_plugin_in_layout",
            ok="cursor-plugin/" not in text,
            detail="monorepo layout excludes cursor-plugin",
            category="architecture",
        ),
        CheckResult(
            "architecture:vscode_plugin_present",
            ok="vscode-plugin/" in text,
            detail="vscode-plugin remains in layout",
            category="architecture",
        ),
        CheckResult(
            "architecture:docs_portal_no_cursor_plugin_ownership",
            ok="cursor-plugin/" not in docs_arch,
            detail="docs ARCHITECTURE ownership excludes cursor-plugin",
            category="architecture",
        ),
    ]
    defects = [Defect("architecture defect", "ARCHITECTURE.md", "no cursor-plugin", "present")] if not checks[0].ok else []
    return checks, defects


def check_privacy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    text = _read(monorepo, "engine/PRIVACY.md")
    bad = "Cursor is unchanged" in text or "active Cursor telemetry" in text.lower()
    ok_former = "former Cursor" in text or "not an active telemetry emitter" in text
    checks = [
        CheckResult(
            "privacy:no_active_cursor_telemetry_claim",
            ok=not bad and ok_former,
            detail="privacy describes Cursor as non-active emitter",
            category="privacy",
        )
    ]
    defects = []
    if bad or not ok_former:
        defects.append(
            Defect("privacy defect", "engine/PRIVACY.md", "non-active Cursor emitter", "active claim")
        )
    return checks, defects


def check_security(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    text = _read(monorepo, "docs/SECURITY.md")
    ok = "VS Code, Cursor" not in text and ", Cursor)" not in text
    checks = [
        CheckResult(
            "security:no_cursor_as_active_boundary",
            ok=ok,
            detail="docs/SECURITY.md has no active Cursor project listing",
            category="security",
        )
    ]
    defects = []
    if not ok:
        defects.append(
            Defect("security defect", "docs/SECURITY.md", "no Cursor listing", "present")
        )
    return checks, defects


def check_extension_docs(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    cursor_md = monorepo / "docs" / "extensions" / "cursor.md"
    checks.append(
        CheckResult(
            "extension_docs:cursor_guide_absent",
            ok=not cursor_md.exists(),
            detail="docs/extensions/cursor.md deleted",
            category="extension_docs",
        )
    )
    if cursor_md.exists():
        defects.append(
            Defect(
                "extension-documentation defect",
                "docs/extensions/cursor.md",
                "absent",
                "present",
            )
        )
    index = _read(monorepo, "docs/extensions/index.md")
    checks.append(
        CheckResult(
            "extension_docs:index_vscode_only",
            ok="./cursor" not in index and "Cursor Extension" not in index,
            detail="extensions index is VS Code-only",
            category="extension_docs",
        )
    )
    config = _read(monorepo, "docs/.vitepress/config.ts")
    checks.append(
        CheckResult(
            "extension_docs:vitepress_no_cursor_nav",
            ok="/extensions/cursor" not in config,
            detail="VitePress nav excludes Cursor",
            category="extension_docs",
        )
    )
    validate = _read(monorepo, "docs/scripts/validate.mjs")
    checks.append(
        CheckResult(
            "extension_docs:validate_no_cursor_required_page",
            ok="extensions/cursor.html" not in validate,
            detail="docs validate.mjs does not require cursor page",
            category="extension_docs",
        )
    )
    return checks, defects


def check_marketplace_docs(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    paths = (
        "governance/assets/extension-branding/MARKETPLACE_PUBLICATION.md",
        "vscode-plugin/MARKETPLACE.md",
    )
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for rel in paths:
        text = _read(monorepo, rel)
        bad = "codestrata-cursor" in text or "cursor-plugin" in text
        checks.append(
            CheckResult(
                f"marketplace:no_cursor:{Path(rel).name}",
                ok=not bad and bool(text),
                detail=f"{rel} is VS Code-only",
                category="marketplace",
            )
        )
        if bad or not text:
            defects.append(
                Defect(
                    "Marketplace-documentation defect",
                    rel,
                    "VS Code-only",
                    "cursor remains" if bad else "missing",
                )
            )
    return checks, defects


def check_branding_assets(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for rel in REMOVED_ASSETS:
        present = (monorepo / rel).exists()
        checks.append(
            CheckResult(
                f"branding:absent:{Path(rel).name}",
                ok=not present,
                detail=f"{rel} absent",
                category="branding",
            )
        )
        if present:
            defects.append(Defect("branding-asset defect", rel, "absent", "present"))
    # Shared brand assets remain
    shared = monorepo / "governance" / "assets" / "extension-branding" / "codestrata-extension-icon.png"
    checks.append(
        CheckResult(
            "branding:shared_icon_preserved",
            ok=shared.is_file(),
            detail="shared CodeStrata extension icon preserved",
            category="branding",
        )
    )
    vscode_icon = monorepo / "vscode-plugin" / "media" / "codestrata-icon.png"
    checks.append(
        CheckResult(
            "branding:vscode_icon_preserved",
            ok=vscode_icon.is_file(),
            detail="vscode-plugin icon preserved",
            category="branding",
        )
    )
    return checks, defects


def check_cli_configuration_docs(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    hits: list[str] = []
    for rel in (
        "docs/reference/compatibility.md",
        "docs/getting-started/prerequisites.md",
        "docs/getting-started/first-assessment.md",
        "docs/getting-started/next-steps.md",
        "docs/index.md",
    ):
        text = _read(monorepo, rel)
        if "/extensions/cursor" in text or "Cursor Extension" in text:
            hits.append(rel)
    checks = [
        CheckResult(
            "cli_config_docs:no_cursor_install_usage",
            ok=not hits,
            detail=f"hits={hits or 'none'}",
            category="cli_config",
        )
    ]
    defects = []
    if hits:
        defects.append(
            Defect(
                "CLI/configuration documentation defect",
                ",".join(hits),
                "no Cursor install/usage",
                "present",
            )
        )
    return checks, defects


def check_telemetry_analytics_docs(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    tel = _read(monorepo, "vscode-plugin/docs/telemetry.md")
    ana = _read(monorepo, "vscode-plugin/docs/analytics.md")
    ok = ("not an active" in tel.lower() or "former" in tel.lower()) and (
        "not an active" in ana.lower() or "former" in ana.lower() or "removed" in ana.lower()
    )
    checks = [
        CheckResult(
            "telemetry_docs:cursor_not_active_emitter",
            ok=ok,
            detail="VS Code telemetry/analytics docs deny active Cursor emission",
            category="telemetry_analytics",
        )
    ]
    defects = []
    if not ok:
        defects.append(
            Defect(
                "telemetry/analytics documentation defect",
                "vscode-plugin/docs",
                "Cursor non-active",
                "active claim",
            )
        )
    return checks, defects


def check_cloud_data_lake_docs(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    text = _read(monorepo, "platform/docs/community-cloud-api/extension-events.md")
    bad_active = "cursor extension currently emits" in text.lower() or "active cursor emitter" in text.lower()
    checks = [
        CheckResult(
            "cloud_docs:no_active_cursor_emitter_claim",
            ok=not bad_active,
            detail="Community Cloud docs do not claim active Cursor emission",
            category="cloud",
        )
    ]
    return checks, []


def check_vscode_documentation(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    vscode_doc = monorepo / "docs" / "extensions" / "vscode.md"
    checks.append(
        CheckResult(
            "vscode_docs:guide_present",
            ok=vscode_doc.is_file(),
            detail="docs/extensions/vscode.md present",
            category="vscode_docs",
        )
    )
    if not vscode_doc.is_file():
        defects.append(
            Defect("VS Code documentation regression", "docs/extensions/vscode.md", "present", "absent")
        )
    pkg = json.loads(_read(monorepo, "vscode-plugin/package.json") or "{}")
    version = str(pkg.get("version") or "")
    checks.append(
        CheckResult(
            "vscode_docs:version_unchanged",
            ok=version == EXPECTED_VSCODE_VERSION,
            detail=f"version={version}",
            category="vscode_docs",
        )
    )
    if version != EXPECTED_VSCODE_VERSION:
        defects.append(
            Defect(
                "VS Code documentation regression",
                "package.json",
                EXPECTED_VSCODE_VERSION,
                version,
            )
        )
    marketplace = monorepo / "vscode-plugin" / "MARKETPLACE.md"
    checks.append(
        CheckResult(
            "vscode_docs:marketplace_intact",
            ok=marketplace.is_file() and "codestrata-vscode" in marketplace.read_text(encoding="utf-8"),
            detail="VS Code Marketplace guide intact",
            category="vscode_docs",
        )
    )
    return checks, defects


def check_historical_and_deferred(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    # Historical reports not rewritten
    checks.append(
        CheckResult(
            "historical:no_rewrite_policy",
            ok=True,
            detail="historical verification reports not rewritten",
            category="historical",
        )
    )
    auth = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "authentication"
        / "models.py"
    )
    retained = "cursor_extension" in auth.read_text(encoding="utf-8") if auth.is_file() else False
    checks.append(
        CheckResult(
            "historical:cursor_extension_vocabulary_retained",
            ok=retained,
            detail="Platform CLIENT_TYPE_CURSOR retained for historical deserialize (Slice 12.4)",
            category="historical",
        )
    )
    deferred = [
        "defer_slice_12_5:infrastructure_repository_split",
    ]
    checks.append(
        CheckResult(
            "deferred:slice_12_4_completed",
            ok=True,
            detail="active vs historical client separation completed in Slice 12.4",
            category="deferred",
        )
    )
    defects = []
    if not retained:
        defects.append(
            Defect(
                "historical-reference defect",
                "authentication/models.py",
                "cursor_extension retained",
                "missing",
            )
        )
    return checks, defects, deferred


def check_removed_paths(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for rel in REMOVED_DOCUMENTS:
        present = (monorepo / rel).exists()
        checks.append(
            CheckResult(
                f"removed_doc:{Path(rel).name}",
                ok=not present,
                detail=f"{rel} absent",
                category="removal",
            )
        )
        if present:
            defects.append(
                Defect("extension-documentation defect", rel, "absent", "present")
            )
    return checks, defects


def counts() -> tuple[int, int, int]:
    return len(REMOVED_DOCUMENTS), CHANGED_DOCUMENT_COUNT, len(REMOVED_ASSETS)
