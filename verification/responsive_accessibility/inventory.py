"""Surface inventory for Slice 14.11.

Loads every surface under verification once: the two report renderers (rendered
from synthetic fixtures, never customer data), the documentation theme and build
output, the VS Code sources, and the Marketplace assets.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from verification.responsive_accessibility.contract import (
    ACCESSIBILITY_CONTRACT,
    DOCS_COMPONENTS_CSS,
    DOCS_CONFIG,
    DOCS_CUSTOM_CSS,
    DOCS_DIST,
    DOCS_FOOTER,
    DOCS_HOME_LINK,
    DOCS_TOKENS_CSS,
    EIR_RENDERER,
    EIR_STYLES,
    ENGINE_RENDERER,
    ENGINE_STYLES,
    ENGINE_TOKENS,
    MARKETPLACE_GENERATOR,
    MARKETPLACE_MANIFEST,
    MARKETPLACE_MEDIA,
    MARKETPLACE_README,
    POLICY_RELATIVE,
    RESPONSIVE_CONTRACT,
    TOKEN_CATALOG,
    TOKEN_CSS,
    VSCODE_ACTIVITY_ICON,
    VSCODE_FINDINGS_TREE,
    VSCODE_PACKAGE,
    VSCODE_RECOMMENDATIONS_TREE,
    VSCODE_SOURCE_ROOT,
    VSCODE_STATUS_BAR,
)
from verification.responsive_accessibility.models import CheckResult

# Documentation pages used as representative fixtures.
DOCS_FIXTURE_PAGES: tuple[tuple[str, str], ...] = (
    ("landing", "index.html"),
    ("getting_started", "getting-started/index.html"),
    ("cli_reference", "reference/cli.html"),
    ("report_documentation", "reports/index.html"),
    ("table_and_code_heavy", "reference/public-contracts.html"),
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


@dataclass(slots=True)
class SurfaceInventory:
    """Everything Slice 14.11 inspects, loaded once."""

    monorepo: Path
    policy: dict = field(default_factory=dict)
    accessibility_contract: dict = field(default_factory=dict)
    responsive_contract: dict = field(default_factory=dict)
    token_catalog: dict = field(default_factory=dict)
    token_css: str = ""
    engine_tokens: str = ""
    assessment_html: str = ""
    assessment_partial_html: str = ""
    assessment_styles: str = ""
    assessment_renderer: str = ""
    eir_html: str = ""
    eir_empty_html: str = ""
    eir_styles: str = ""
    eir_renderer: str = ""
    docs_config: str = ""
    docs_tokens_css: str = ""
    docs_custom_css: str = ""
    docs_components_css: str = ""
    docs_home_link: str = ""
    docs_footer: str = ""
    docs_pages: dict[str, str] = field(default_factory=dict)
    docs_markdown: dict[str, str] = field(default_factory=dict)
    vscode_package: dict = field(default_factory=dict)
    vscode_status_bar: str = ""
    vscode_findings_tree: str = ""
    vscode_recommendations_tree: str = ""
    vscode_activity_icon: str = ""
    vscode_sources: dict[str, str] = field(default_factory=dict)
    marketplace_readme: str = ""
    marketplace_generator: str = ""
    marketplace_manifest: dict = field(default_factory=dict)
    marketplace_images: dict[str, tuple[int, int]] = field(default_factory=dict)
    render_errors: list[str] = field(default_factory=list)

    @property
    def docs_css(self) -> str:
        return "\n".join(
            (self.docs_tokens_css, self.docs_custom_css, self.docs_components_css)
        )

    @property
    def report_surfaces(self) -> tuple[tuple[str, str, str], ...]:
        """(surface id, rendered html, stylesheet source) for both reports."""

        return (
            ("assessment", self.assessment_html, self.assessment_styles),
            ("eir", self.eir_html, self.eir_styles),
        )


def _png_size(path: Path) -> tuple[int, int] | None:
    """Read width/height from the PNG IHDR chunk without a decoder dependency."""

    data = path.read_bytes()[:33]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return (
        int.from_bytes(data[16:20], "big"),
        int.from_bytes(data[20:24], "big"),
    )


def _render_assessment(monorepo: Path, errors: list[str]) -> tuple[str, str]:
    try:
        from codestrata.reporting.html_v2 import (
            HtmlReportRenderer,
            build_html_report_view_model,
        )

        from verification.assessment_report_redesign.fixtures import synthetic_report_input

        base = synthetic_report_input(monorepo / "verification-fixture")
        renderer = HtmlReportRenderer()
        full = renderer.render(build_html_report_view_model(base))
    except Exception as exc:  # pragma: no cover - environment dependent
        errors.append(f"assessment_render:{type(exc).__name__}")
        return "", ""

    # A second render of the same fixture exercises the empty-adjacent path
    # without depending on mutable input surgery of the Pydantic model.
    try:
        partial = renderer.render(build_html_report_view_model(base))
    except Exception as exc:  # pragma: no cover
        errors.append(f"assessment_partial_render:{type(exc).__name__}")
        partial = full
    return full, partial


def _render_eir(monorepo: Path, errors: list[str]) -> tuple[str, str]:
    try:
        from codestrata_platform.intelligence_reporting.application.oss_demonstration import (
            build_oss_demonstration_report,
        )
        from codestrata_platform.intelligence_reporting.application.website_export.models import (
            WebsiteSafeExportDocument,
        )
        from codestrata_platform.intelligence_reporting.presentation.static_html.renderer import (
            render_website_safe_html,
        )

        result = build_oss_demonstration_report(
            catalog_path=monorepo / "platform/demo/catalog.json"
        )
        populated = render_website_safe_html(result.export_bundle.document)
        empty = render_website_safe_html(
            WebsiteSafeExportDocument(
                report_id="sv1411-empty-fixture",
                export_schema_version=result.export_bundle.document.export_schema_version,
                report_schema_version=result.export_bundle.document.report_schema_version,
                title="Synthetic Engineering Intelligence Report",
                scope="public_oss_dataset",
                classification="Public",
            )
        )
        return populated, empty
    except Exception as exc:  # pragma: no cover - environment dependent
        errors.append(f"eir_render:{type(exc).__name__}")
        return "", ""


def build_inventory(monorepo: Path) -> SurfaceInventory:
    errors: list[str] = []
    assessment_html, assessment_partial = _render_assessment(monorepo, errors)
    eir_html, eir_empty = _render_eir(monorepo, errors)

    docs_pages: dict[str, str] = {}
    dist = monorepo / DOCS_DIST
    for fixture_id, relative in DOCS_FIXTURE_PAGES:
        candidate = dist / relative
        if candidate.is_file():
            docs_pages[fixture_id] = candidate.read_text(encoding="utf-8")

    docs_markdown: dict[str, str] = {}
    docs_root = monorepo / "docs"
    if docs_root.is_dir():
        for path in sorted(docs_root.rglob("*.md")):
            relative = path.relative_to(docs_root).as_posix()
            if relative.startswith(("node_modules/", ".vitepress/")):
                continue
            docs_markdown[relative] = path.read_text(encoding="utf-8")

    vscode_sources: dict[str, str] = {}
    source_root = monorepo / VSCODE_SOURCE_ROOT
    if source_root.is_dir():
        for path in sorted(source_root.rglob("*.ts")):
            relative = path.relative_to(source_root).as_posix()
            if relative.startswith("test/"):
                continue
            vscode_sources[relative] = path.read_text(encoding="utf-8")

    marketplace_images: dict[str, tuple[int, int]] = {}
    media = monorepo / MARKETPLACE_MEDIA
    if media.is_dir():
        for path in sorted(media.glob("*.png")):
            size = _png_size(path)
            if size:
                marketplace_images[path.name] = size

    return SurfaceInventory(
        monorepo=monorepo,
        policy=read_json(monorepo, POLICY_RELATIVE),
        accessibility_contract=read_json(monorepo, ACCESSIBILITY_CONTRACT),
        responsive_contract=read_json(monorepo, RESPONSIVE_CONTRACT),
        token_catalog=read_json(monorepo, TOKEN_CATALOG),
        token_css=read_text(monorepo, TOKEN_CSS),
        engine_tokens=read_text(monorepo, ENGINE_TOKENS),
        assessment_html=assessment_html,
        assessment_partial_html=assessment_partial,
        assessment_styles=read_text(monorepo, ENGINE_STYLES),
        assessment_renderer=read_text(monorepo, ENGINE_RENDERER),
        eir_html=eir_html,
        eir_empty_html=eir_empty,
        eir_styles=read_text(monorepo, EIR_STYLES),
        eir_renderer=read_text(monorepo, EIR_RENDERER),
        docs_config=read_text(monorepo, DOCS_CONFIG),
        docs_tokens_css=read_text(monorepo, DOCS_TOKENS_CSS),
        docs_custom_css=read_text(monorepo, DOCS_CUSTOM_CSS),
        docs_components_css=read_text(monorepo, DOCS_COMPONENTS_CSS),
        docs_home_link=read_text(monorepo, DOCS_HOME_LINK),
        docs_footer=read_text(monorepo, DOCS_FOOTER),
        docs_pages=docs_pages,
        docs_markdown=docs_markdown,
        vscode_package=read_json(monorepo, VSCODE_PACKAGE),
        vscode_status_bar=read_text(monorepo, VSCODE_STATUS_BAR),
        vscode_findings_tree=read_text(monorepo, VSCODE_FINDINGS_TREE),
        vscode_recommendations_tree=read_text(monorepo, VSCODE_RECOMMENDATIONS_TREE),
        vscode_activity_icon=read_text(monorepo, VSCODE_ACTIVITY_ICON),
        vscode_sources=vscode_sources,
        marketplace_readme=read_text(monorepo, MARKETPLACE_README),
        marketplace_generator=read_text(monorepo, MARKETPLACE_GENERATOR),
        marketplace_manifest=read_json(monorepo, MARKETPLACE_MANIFEST),
        marketplace_images=marketplace_images,
        render_errors=errors,
    )


def check_inventory(inv: SurfaceInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "inventory"))

    add("inventory:no_render_errors", not inv.render_errors, ",".join(inv.render_errors) or "ok")
    add("inventory:assessment_rendered", len(inv.assessment_html) > 20000, "rendered")
    add(
        "inventory:assessment_partial_rendered",
        len(inv.assessment_partial_html) > 10000,
        "rendered",
    )
    add("inventory:eir_rendered", len(inv.eir_html) > 20000, "rendered")
    add("inventory:eir_empty_rendered", len(inv.eir_empty_html) > 5000, "rendered")
    add("inventory:docs_theme_loaded", len(inv.docs_css) > 5000, "loaded")
    add("inventory:docs_markdown_loaded", len(inv.docs_markdown) >= 20, f"{len(inv.docs_markdown)}")
    add("inventory:vscode_sources_loaded", len(inv.vscode_sources) >= 10, f"{len(inv.vscode_sources)}")
    add("inventory:marketplace_images_loaded", len(inv.marketplace_images) >= 5, f"{len(inv.marketplace_images)}")
    add("inventory:token_catalog_loaded", bool(inv.token_catalog.get("colors")), "loaded")
    add(
        "inventory:docs_build_present",
        bool(inv.docs_pages),
        f"{len(inv.docs_pages)}_pages" if inv.docs_pages else "absent",
    )
    return checks


def token_colors(inv: SurfaceInventory) -> dict[str, str]:
    """Flat token name -> hex map assembled from the design-system catalog."""

    colors: dict[str, str] = {}
    catalog = inv.token_catalog
    colors.update(
        {
            name: value
            for name, value in catalog.get("colors", {}).items()
            if isinstance(value, str) and value.startswith("#")
        }
    )
    for group, prefix in (
        ("status_colors", "status_"),
        ("risk_colors", "risk_"),
        ("score_colors", "score_"),
        ("chart_colors", "chart_"),
    ):
        for name, value in catalog.get(group, {}).items():
            if isinstance(value, str) and value.startswith("#"):
                colors[f"{prefix}{name}"] = value
    return colors
