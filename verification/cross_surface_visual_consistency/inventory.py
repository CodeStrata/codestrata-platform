"""Inventory loader for Slice 14.13 cross-surface visual consistency."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from verification.cross_surface_visual_consistency.contract import (
    CONSISTENCY_CONTRACT,
    CONSUMER_MAPPINGS,
    POLICY_RELATIVE,
    PRESENTATION_CONTRACT,
    TOKEN_CATALOG,
    TOKEN_CSS,
)


def read_text(monorepo: Path, relative: str) -> str:
    path = monorepo / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def read_json(monorepo: Path, relative: str) -> dict:
    text = read_text(monorepo, relative)
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def _render_assessment(monorepo: Path, errors: list[str]) -> str:
    try:
        from codestrata.reporting.html_v2 import (
            HtmlReportRenderer,
            build_html_report_view_model,
        )
        from verification.assessment_report_redesign.fixtures import synthetic_report_input

        base = synthetic_report_input(monorepo / "verification-fixture")
        return HtmlReportRenderer().render(build_html_report_view_model(base))
    except Exception as exc:  # pragma: no cover
        errors.append(f"assessment_render:{type(exc).__name__}")
        return ""


def _render_eir(monorepo: Path, errors: list[str]) -> str:
    try:
        from codestrata_platform.intelligence_reporting.application.oss_demonstration import (
            build_oss_demonstration_report,
        )
        from codestrata_platform.intelligence_reporting.presentation.static_html.renderer import (
            render_website_safe_html,
        )

        result = build_oss_demonstration_report(
            catalog_path=monorepo / "platform/demo/catalog.json"
        )
        return render_website_safe_html(result.export_bundle.document)
    except Exception as exc:  # pragma: no cover
        errors.append(f"eir_render:{type(exc).__name__}")
        return ""


def ensure_docs_dist(monorepo: Path) -> bool:
    dist = monorepo / "docs" / ".vitepress" / "dist"
    if dist.is_dir() and any(dist.rglob("index.html")):
        return True
    docs = monorepo / "docs"
    if not (docs / "package.json").is_file():
        return False
    result = subprocess.run(  # noqa: S603
        ["npm", "run", "build"],
        cwd=docs,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and dist.is_dir()


@dataclass(slots=True)
class ConsistencyInventory:
    monorepo: Path
    policy: dict = field(default_factory=dict)
    consistency_contract: dict = field(default_factory=dict)
    presentation_contract: dict = field(default_factory=dict)
    consumer_mappings: dict = field(default_factory=dict)
    token_catalog: dict = field(default_factory=dict)
    token_css: str = ""
    docs_theme_tokens: str = ""
    docs_custom_css: str = ""
    docs_components_css: str = ""
    docs_config: str = ""
    public_tokens: str = ""
    swagger_tokens: str = ""
    swagger_css: str = ""
    assessment_styles: str = ""
    assessment_renderer: str = ""
    assessment_html: str = ""
    eir_styles: str = ""
    eir_renderer: str = ""
    eir_html: str = ""
    vscode_package: dict = field(default_factory=dict)
    vscode_mapping: str = ""
    marketplace_mapping: str = ""
    marketplace_generator: str = ""
    vscode_activity_svg: str = ""
    dist_exists: bool = False
    dist_files: list[str] = field(default_factory=list)
    dist_tokens: str = ""
    brand_masters: dict[str, str] = field(default_factory=dict)
    render_errors: list[str] = field(default_factory=list)


def build_inventory(monorepo: Path, *, build_docs: bool = True) -> ConsistencyInventory:
    errors: list[str] = []
    assessment_html = _render_assessment(monorepo, errors)
    eir_html = _render_eir(monorepo, errors)

    brand_masters: dict[str, str] = {}
    brand_dir = monorepo / "design-system" / "assets" / "brand"
    if brand_dir.is_dir():
        for path in sorted(brand_dir.glob("*.svg")):
            brand_masters[path.name] = path.read_text(encoding="utf-8")

    dist_exists = False
    dist_files: list[str] = []
    dist_tokens = ""
    dist = monorepo / "docs" / ".vitepress" / "dist"
    if build_docs:
        ensure_docs_dist(monorepo)
    if dist.is_dir():
        dist_exists = True
        dist_files = sorted(
            str(p.relative_to(dist)).replace("\\", "/")
            for p in dist.rglob("*")
            if p.is_file()
        )[:500]
        tokens_path = dist / "design-tokens" / "tokens.css"
        if tokens_path.is_file():
            dist_tokens = tokens_path.read_text(encoding="utf-8")

    return ConsistencyInventory(
        monorepo=monorepo,
        policy=read_json(monorepo, POLICY_RELATIVE),
        consistency_contract=read_json(monorepo, CONSISTENCY_CONTRACT),
        presentation_contract=read_json(monorepo, PRESENTATION_CONTRACT),
        consumer_mappings=read_json(monorepo, CONSUMER_MAPPINGS),
        token_catalog=read_json(monorepo, TOKEN_CATALOG),
        token_css=read_text(monorepo, TOKEN_CSS),
        docs_theme_tokens=read_text(monorepo, "docs/.vitepress/theme/tokens.css"),
        docs_custom_css=read_text(monorepo, "docs/.vitepress/theme/custom.css"),
        docs_components_css=read_text(monorepo, "docs/.vitepress/theme/components.css"),
        docs_config=read_text(monorepo, "docs/.vitepress/config.ts"),
        public_tokens=read_text(monorepo, "docs/public/design-tokens/tokens.css"),
        swagger_tokens=read_text(
            monorepo, "platform/api/openapi/swagger/design-tokens/tokens.css"
        ),
        swagger_css=read_text(
            monorepo, "platform/api/openapi/swagger/css/codestrata-swagger.css"
        ),
        assessment_styles=read_text(
            monorepo, "engine/src/codestrata/reporting/html_v2/styles.py"
        ),
        assessment_renderer=read_text(
            monorepo, "engine/src/codestrata/reporting/html_v2/renderer.py"
        ),
        assessment_html=assessment_html,
        eir_styles=read_text(
            monorepo,
            "platform/src/codestrata_platform/intelligence_reporting/presentation/static_html/styles.py",
        ),
        eir_renderer=read_text(
            monorepo,
            "platform/src/codestrata_platform/intelligence_reporting/presentation/static_html/renderer.py",
        ),
        eir_html=eir_html,
        vscode_package=read_json(monorepo, "vscode-plugin/package.json"),
        vscode_mapping=read_text(
            monorepo, "vscode-plugin/policies/design_system_vscode_mapping.json"
        ),
        marketplace_mapping=read_text(
            monorepo, "vscode-plugin/policies/design_system_marketplace_mapping.json"
        ),
        marketplace_generator=read_text(
            monorepo, "vscode-plugin/scripts/generate_marketplace_visuals.py"
        ),
        vscode_activity_svg=read_text(monorepo, "vscode-plugin/media/codestrata-activity.svg"),
        dist_exists=dist_exists,
        dist_files=dist_files,
        dist_tokens=dist_tokens,
        brand_masters=brand_masters,
        render_errors=errors,
    )
