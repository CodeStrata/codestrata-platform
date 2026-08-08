"""Active final surface registry for Epic 14 completion."""

from __future__ import annotations

from pathlib import Path

from verification.unified_product_experience_completion.inventory import exists, load_json
from verification.unified_product_experience_completion.models import CheckResult, Defect

SURFACES: tuple[tuple[str, str, str], ...] = (
    (
        "community_docs",
        "docs",
        "design-system/contracts/consumer-mappings.json",
    ),
    (
        "assessment_html",
        "engine/src/codestrata/reporting/html_v2",
        "engine/policies/assessment_report_design_policy.json",
    ),
    (
        "commercial_eir_html",
        "platform/src/codestrata_platform/intelligence_reporting/presentation/static_html",
        "platform/policies/engineering_intelligence_report_design_policy.json",
    ),
    (
        "vscode",
        "vscode-plugin",
        "vscode-plugin/policies/vscode_visual_experience_policy.json",
    ),
    (
        "marketplace",
        "vscode-plugin",
        "vscode-plugin/policies/marketplace_visual_assets_policy.json",
    ),
    (
        "api_swagger_branding",
        "platform/api/openapi/swagger",
        "design-system/policies/brand_asset_policy.json",
    ),
)


def build_surface_registry(monorepo: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for surface_id, path, policy in SURFACES:
        rows.append(
            {
                "surface": surface_id,
                "path_present": exists(monorepo, path),
                "policy_present": exists(monorepo, policy),
                "design_system_relationship": "codestrata-visual-design-system:1.0",
                "brand_authority": "codestrata-brand-asset-policy:1.0",
                "accessibility_responsive": (
                    "codestrata-accessibility-responsive-policy:1.0"
                ),
                "active_legacy_identity": False,
            }
        )
    return sorted(rows, key=lambda r: str(r["surface"]))


def check_surface_registry(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    amber = "#d98a3d"
    for surface_id, path, policy in SURFACES:
        present = exists(monorepo, path) and exists(monorepo, policy)
        checks.append(
            CheckResult(
                f"surface_registry:{surface_id}:present",
                present,
                "present" if present else "missing",
                "surface_registry",
            )
        )
        if not present:
            defects.append(
                Defect("surface_registry", surface_id, "present", "missing")
            )

    # Active consumer mappings reference Design System.
    mappings = load_json(monorepo, "design-system/contracts/consumer-mappings.json")
    checks.append(
        CheckResult(
            "surface_registry:consumer_mappings_present",
            bool(mappings),
            "present" if mappings else "missing",
            "surface_registry",
        )
    )

    # Spot-check active docs tokens are not amber-primary.
    docs_tokens = (
        monorepo / "docs" / ".vitepress" / "theme" / "tokens.css"
    )
    if docs_tokens.is_file():
        text = docs_tokens.read_text(encoding="utf-8")
        # Amber may appear only as documented legacy alias, not as --cs-brand.
        brand_is_amber = "--cs-brand:" in text and amber in text.split("--cs-brand:", 1)[-1][
            :80
        ]
        checks.append(
            CheckResult(
                "surface_registry:docs_no_active_amber_brand",
                not brand_is_amber,
                "clean" if not brand_is_amber else "amber_brand",
                "surface_registry",
            )
        )
    else:
        checks.append(
            CheckResult(
                "surface_registry:docs_tokens_present",
                False,
                "missing",
                "surface_registry",
            )
        )
        defects.append(
            Defect("surface_registry", "community_docs", "tokens.css", "missing")
        )

    return checks, defects
