"""Negative scenario posture checks (A–Z)."""

from __future__ import annotations

from verification.documentation_deployment.contract import ASSETS_DIR, FORBIDDEN_EPIC_15_PATHS
from verification.documentation_deployment.inventory import DeploymentInventory
from verification.documentation_deployment.models import CheckResult
from verification.documentation_deployment.output_alignment import compare_configured_vs_actual

_CATEGORY = "scenarios"


def check_negative_scenarios(inv: DeploymentInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    config_dir = inv.wrangler_config.get("assets", {}).get("directory", "")
    scripts = inv.package_json.get("scripts", {})
    aligned, _ = compare_configured_vs_actual(inv.docs_root, str(config_dir))

    scenarios: list[tuple[str, str, bool]] = [
        ("A", "wrong_assets_directory_docs_prefix", config_dir not in {"docs/.vitepress/dist", "./docs/.vitepress/dist"}),
        ("B", "assets_directory_not_package_relative", aligned),
        ("C", "npx_wrangler_dynamic_install", not any("npx wrangler" in str(v) for v in scripts.values())),
        ("D", "wrangler_auto_setup", "wrangler init" not in inv.wrangler_config_text),
        ("E", "deploy_upload_rebuilds", "build" not in scripts.get("deploy:upload", "").lower()),
        ("F", "deploy_script_rebuilds", "npm run build" not in scripts.get("deploy", "")),
        ("G", "worker_main_required", "main" not in inv.wrangler_config),
        ("H", "nodejs_compat_enabled", "nodejs_compat" not in (inv.wrangler_config.get("compatibility_flags") or [])),
        ("I", "credentials_in_wrangler", "CLOUDFLARE_API_TOKEN" not in inv.wrangler_config_text),
        ("J", "production_deploy_in_verifier", inv.policy.get("production_deploy_in_verification_allowed") is False),
        ("K", "missing_local_wrangler", inv.local_wrangler_version is not None),
        ("L", "custom_vitepress_outdir", "outDir" not in inv.vitepress_config_text),
        ("M", "monorepo_package_json", not (inv.monorepo / "package.json").is_file()),
        ("N", "dist_not_gitignored", ".vitepress/dist" in inv.gitignore_text),
        ("O", "platform_pages_in_dist", not any("platform/" in f for f in inv.dist_files)),
        ("P", "start_epic_15", not any((inv.monorepo / p).exists() for p in FORBIDDEN_EPIC_15_PATHS)),
        ("Q", "interactive_setup_allowed", inv.policy.get("interactive_setup_allowed") is False),
        ("R", "deployment_source_mutation", inv.policy.get("deployment_source_mutation_allowed") is False),
        ("S", "assets_directory_exact", config_dir == ASSETS_DIR),
        ("T", "build_once_violation", scripts.get("build", "").strip() == "vitepress build"),
        ("U", "missing_deploy_check", bool(inv.deploy_check_text)),
        ("V", "missing_wrangler_config", bool(inv.wrangler_config_text)),
        ("W", "missing_sitemap", (inv.dist_dir / "sitemap.xml").is_file() if inv.dist_dir.is_dir() else False),
        ("X", "missing_index", (inv.dist_dir / "index.html").is_file() if inv.dist_dir.is_dir() else False),
        ("Y", "design_system_version_drift", inv.policy.get("expected_unchanged", {}).get("design_system") == "1.0"),
        ("Z", "historical_failure_unguarded", "v0.1.0 failure class" in inv.deploy_check_text),
    ]

    for letter, slug, ok in scenarios:
        checks.append(
            CheckResult(
                name=f"scenario_{letter}_{slug}",
                ok=ok,
                detail="absent" if ok else "present",
                category=_CATEGORY,
            )
        )
    return checks
