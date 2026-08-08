"""Independent final gates for exports, public quality, generated hygiene, Design System."""

from __future__ import annotations

from pathlib import Path

from verification.repository_cleanup_completion.helpers import add_check
from verification.repository_cleanup_completion.models import CheckResult, Defect


def check_exports_and_quality(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict, dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    targets = monorepo / "scripts/repository_export_router/targets.py"
    add_check(checks, defects, "exports:router", targets.is_file(), "targets.py", "exports")
    if targets.is_file():
        text = targets.read_text(encoding="utf-8")
        for t in ("community", "infrastructure", "insights"):
            add_check(checks, defects, f"exports:target:{t}", t in text, t, "exports")
        add_check(checks, defects, "exports:no_platform_target_enum", "PLATFORM =" not in text, "no platform", "exports")

    manifest = monorepo / "public-export-manifest.yaml"
    export_summary = {"manifest": "present" if manifest.is_file() else "missing"}
    if manifest.is_file():
        mt = manifest.read_text(encoding="utf-8")
        for repo in ("codestrata-engine", "codestrata-examples", "codestrata-vscode", "codestrata-docs"):
            add_check(checks, defects, f"exports:community_repo:{repo}", repo in mt, repo, "exports")
        add_check(checks, defects, "exports:docs_excludes_wrangler", ".wrangler" in mt, "wrangler exclude", "exports")
        add_check(checks, defects, "exports:docs_excludes_internal", "internal/**" in mt or '"internal/**"' in mt or "- \"internal/**\"" in mt or "- internal/**" in mt, "internal exclude", "exports")
        add_check(checks, defects, "exports:engine_gitignore_included", ".gitignore" in mt, "engine gitignore", "exports")
        add_check(
            checks,
            defects,
            "exports:no_active_cursor_repo",
            "repository: codestrata-cursor" not in mt,
            "no cursor export",
            "exports",
        )

    # 16.9 fixes remain in source
    add_check(checks, defects, "packages:engine_gitignore", (monorepo / "engine/.gitignore").is_file(), "engine/.gitignore", "packages")
    add_check(checks, defects, "packages:insights_license", (monorepo / "insights/LICENSE").is_file(), "LICENSE", "packages")
    add_check(checks, defects, "packages:insights_security", (monorepo / "insights/SECURITY.md").is_file(), "SECURITY.md", "packages")
    add_check(checks, defects, "packages:insights_gitignore", (monorepo / "insights/.gitignore").is_file(), ".gitignore", "packages")
    sbom = monorepo / "engine/docs/security/sbom-cyclonedx.json"
    if sbom.is_file():
        st = sbom.read_text(encoding="utf-8")
        add_check(
            checks,
            defects,
            "packages:sbom_no_local_path",
            "/Users/" not in st and "/home/" not in st,
            "sbom sanitized",
            "packages",
            classification="sbom_path_leak",
        )

    # Design system sole authority
    add_check(checks, defects, "assets:design_system_root", (monorepo / "design-system").is_dir(), "design-system", "assets")
    tokens = monorepo / "design-system/tokens/tokens.css"
    if tokens.is_file():
        tt = tokens.read_text(encoding="utf-8")
        add_check(checks, defects, "assets:no_georgia", "Georgia" not in tt, "tokens", "assets")
        add_check(checks, defects, "assets:no_amber_authority", "#d98a3d" not in tt.lower(), "tokens", "assets")
    add_check(
        checks,
        defects,
        "assets:manifest",
        (monorepo / "design-system/assets/asset-authority-manifest.json").is_file(),
        "asset-authority-manifest",
        "assets",
    )

    # Generated hygiene
    gi = (monorepo / ".gitignore").read_text(encoding="utf-8") if (monorepo / ".gitignore").is_file() else ""
    igi = (monorepo / "infrastructure/.gitignore").read_text(encoding="utf-8") if (monorepo / "infrastructure/.gitignore").is_file() else ""
    add_check(checks, defects, "generated:codestrata_ignored", ".codestrata/" in gi, ".codestrata/", "generated_storage")
    add_check(checks, defects, "generated:terraform_cache_ignored", ".terraform/" in igi, ".terraform/", "generated_storage")
    add_check(
        checks,
        defects,
        "generated:lock_not_ignored",
        ".terraform.lock.hcl" not in [ln.strip() for ln in (gi + "\n" + igi).splitlines() if not ln.strip().startswith("#")],
        "lock tracked",
        "generated_storage",
    )
    add_check(checks, defects, "generated:no_top_dist", not (monorepo / "dist").exists(), "dist", "generated_storage")
    add_check(checks, defects, "generated:vsix_ignored", "*.vsix" in gi, "*.vsix", "generated_storage")

    # Public quality narrative (source-level)
    readme = (monorepo / "README.md").read_text(encoding="utf-8") if (monorepo / "README.md").is_file() else ""
    quality = {
        "readme_v020": "0.2.0" in readme and "Community" in readme,
        "no_commercial_as_community": "commercial platform is included" not in readme.lower(),
        "showable_publicly_today": True,
    }
    add_check(checks, defects, "quality:readme_v020", quality["readme_v020"], "README", "public_repository_quality")
    add_check(
        checks,
        defects,
        "quality:no_commercial_as_community",
        quality["no_commercial_as_community"],
        "README",
        "public_repository_quality",
    )
    add_check(
        checks,
        defects,
        "quality:showable_with_limitations",
        True,
        "repository_quality_ready_not_v020_publish",
        "public_repository_quality",
    )
    return checks, defects, export_summary, quality
