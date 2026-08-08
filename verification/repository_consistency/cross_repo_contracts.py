"""Cross-repository contract mechanisms."""

from __future__ import annotations

from pathlib import Path

from verification.repository_consistency.inventory import add_check
from verification.repository_consistency.models import CheckResult, Defect


def check_cross_repo_contracts(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], list[dict[str, str]]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    matrix: list[dict[str, str]] = []

    pairs = [
        (
            "vscode_cli",
            "VS Code ↔ CLI",
            [
                "vscode-plugin/src/engine",
                "vscode-plugin/package.json",
            ],
            "compatibility/version contract via discovery + package version",
        ),
        (
            "insights_platform",
            "Insights ↔ Platform",
            [
                "platform/policies/community_insights_query_contract.json",
                "platform/policies/codestrata_insights_dashboard_contract.json",
            ],
            "HTTP + MetricResult / dashboard contracts",
        ),
        (
            "docs_design_system",
            "Docs ↔ Design System",
            [
                "docs/public/design-tokens/tokens.css",
                "docs/.vitepress/theme/tokens.css",
            ],
            "generated/public token copy + bridge",
        ),
        (
            "reports_design_system",
            "Reports ↔ Design System",
            [
                "engine/src/codestrata/reporting",
                "design-system/tokens/tokens.css",
            ],
            "embedded deterministic tokens / reporting assets",
        ),
        (
            "marketplace_brand",
            "Marketplace ↔ brand",
            [
                "vscode-plugin/media",
                "design-system/assets/brand",
                "scripts/generate_brand_assets.py",
            ],
            "generated brand assets",
        ),
        (
            "infra_platform_engine",
            "Infrastructure ↔ Platform/Engine",
            [
                "infrastructure",
                "scripts/repository_export",
            ],
            "no runtime source imports; export/IaC only",
        ),
    ]

    for key, label, paths, mechanism in pairs:
        missing = [p for p in paths if not (monorepo / p).exists()]
        ok = not missing
        add_check(
            checks,
            defects,
            f"cross_repo:{key}",
            ok,
            ",".join(missing) or mechanism,
            "cross_repo_contracts",
        )
        matrix.append(
            {
                "pair": label,
                "mechanism": mechanism,
                "status": "ok" if ok else f"missing:{','.join(missing)}",
            }
        )

    # Explicit: no future repo should require sibling filesystem imports for docs tokens
    bridge = monorepo / "docs/.vitepress/theme/tokens.css"
    if bridge.is_file():
        t = bridge.read_text(encoding="utf-8")
        sibling = any(
            marker in t
            for marker in (
                "../design-system/",
                "../../design-system/",
                "../../../design-system/",
                "/design-system/",
            )
        )
        add_check(
            checks,
            defects,
            "cross_repo:docs_no_sibling_design_system",
            not sibling,
            "packaged copy only",
            "cross_repo_contracts",
            classification="docs_requires_sibling_design_system",
        )
    return checks, defects, matrix
