"""Slice 14.11 — responsive and accessible experience tests."""

from __future__ import annotations

import json
import re
from pathlib import Path

from verification.responsive_accessibility.checks import check_all
from verification.responsive_accessibility.contract import (
    ACCESSIBILITY_CONTRACT,
    FORBIDDEN_EPIC_15_PATHS,
    POLICY_RELATIVE,
    RESPONSIVE_CONTRACT,
    VIEWPORT_MATRIX_PX,
    monorepo_root_from_here,
)
from verification.responsive_accessibility.contrast import contrast_ratio
from verification.responsive_accessibility.inventory import build_inventory, token_colors
from verification.responsive_accessibility.runner import build_report, write_report

ROOT = monorepo_root_from_here()


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_policy_declares_wcag_oriented_baseline() -> None:
    policy = _json(POLICY_RELATIVE)
    assert policy["policy_id"] == "codestrata-accessibility-responsive-policy"
    assert policy["policy_version"] == "1.0"
    assert policy["wcag_target"] == "2.2_AA_oriented"
    assert policy["formal_certification_claimed"] is False
    assert policy["color_only_meaning_allowed"] is False
    assert policy["prohibited"]["start_epic_15"] is True


def test_accessibility_and_responsive_contracts_present() -> None:
    accessibility = _json(ACCESSIBILITY_CONTRACT)
    responsive = _json(RESPONSIVE_CONTRACT)
    assert accessibility["contract_id"] == "codestrata-accessibility-contract"
    assert responsive["contract_id"] == "codestrata-responsive-contract"
    assert "#" not in json.dumps(accessibility.get("contrast", {}).get("required_pairs", {}))
    assert tuple(responsive["viewport_matrix_px"]) == VIEWPORT_MATRIX_PX


def test_contrast_math_reference_values() -> None:
    assert abs(contrast_ratio("#000000", "#ffffff") - 21.0) < 0.01
    assert abs(contrast_ratio("#16756a", "#16756a") - 1.0) < 0.001
    assert contrast_ratio("#111815", "#f4f6f3") >= 4.5


def test_dark_theme_status_inks_are_retuned() -> None:
    tokens = _text("engine/src/codestrata/design_system/tokens.py")
    assert "--cs-teal-light: #35b3a4" in tokens
    assert "--cs-rust-light: #e5822f" in tokens
    assert "--cs-blue-light: #8fb0d4" in tokens
    assert "--cs-risk-critical: var(--cs-rust-light)" in tokens
    assert "--cs-focus: var(--cs-teal-light)" in tokens
    catalog = _json("design-system/tokens/catalog.json")
    assert catalog["colors"]["teal_light"] == "#35b3a4"
    assert "dark_theme_colors" in catalog


def test_assessment_skip_targets_main_and_tables_are_scoped() -> None:
    inv = build_inventory(ROOT)
    assert 'href="#main-content"' in inv.assessment_html
    assert 'id="main-content"' in inv.assessment_html
    assert inv.assessment_html.count("<h1") == 1
    assert len(re.findall(r'<th scope="col"', inv.assessment_html)) >= 1
    assert 'tabindex="0"' in inv.assessment_html
    assert 'aria-label="Severity:' not in inv.assessment_html
    assert "forced-colors: active" in inv.assessment_html


def test_eir_landmarks_and_dark_safe_disclaimer() -> None:
    inv = build_inventory(ROOT)
    assert inv.eir_html.count('role="banner"') == 1
    assert '<section class="cover"' in inv.eir_html
    assert 'href="#main"' in inv.eir_html
    assert "color: var(--ink)" in inv.eir_styles
    assert "forced-colors: active" in inv.eir_styles
    assert 'font-size: 16px' not in inv.eir_styles


def test_docs_theme_restores_table_scroll_and_focus_token() -> None:
    components = _text("docs/.vitepress/theme/components.css")
    tokens = _text("docs/.vitepress/theme/tokens.css")
    custom = _text("docs/.vitepress/theme/custom.css")
    assert "overflow-x: auto" in components
    assert "forced-colors: active" in components
    assert "var(--cs-focus)" in tokens
    assert "min-height: 44px" in custom


def test_vscode_remains_native_host_without_webview() -> None:
    package = _json("vscode-plugin/package.json")
    assert package["version"] == "0.2.0"
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "vscode-plugin/src").rglob("*.ts")
        if "test" not in path.parts
    )
    assert "createWebviewPanel" not in sources
    assert "WebviewView" not in sources
    assert "accessibilityInformation" in _text("vscode-plugin/src/ui/statusBar.ts")


def test_marketplace_readme_alts_are_present() -> None:
    readme = _text("vscode-plugin/README.md")
    alts = re.findall(r"!\[([^\]]+)\]\(media/screenshot-", readme)
    assert len(alts) >= 5
    assert all(alt.strip() and "screenshot-" not in alt for alt in alts)


def test_slice_14_14_has_not_started() -> None:
    for relative in FORBIDDEN_EPIC_15_PATHS:
        assert not (ROOT / relative).exists(), relative


def test_static_verification_passes() -> None:
    inv = build_inventory(ROOT)
    checks, defects, measurements, _viewports, _ = check_all(ROOT, inventory=inv)
    assert not defects
    assert all(check.ok for check in checks)
    assert len(measurements) >= 30
    colors = token_colors(inv)
    assert contrast_ratio(colors["teal_light"], colors["teal_soft_dark"]) >= 4.5
    assert contrast_ratio(colors["rust_light"], colors["rust_soft_dark"]) >= 4.5


def test_runner_is_deterministic() -> None:
    first = build_report(ROOT)
    second = build_report(ROOT)
    first_path = write_report(ROOT, first)
    second_path = write_report(ROOT, second)
    assert first_path.read_bytes() == second_path.read_bytes()
    payload = json.loads(first_path.read_text(encoding="utf-8"))
    assert payload["schema_name"] == "responsive-accessibility-verification"
    assert payload["schema_version"] == "1.0.0"
    assert payload["verdict"] in {"PASS", "PASS_WITH_LIMITATIONS"}
    assert payload["release_posture"]["start_epic_15"] is False
    assert payload["wcag_posture"]["certified"] is False
    assert "/Users/" not in first_path.read_text(encoding="utf-8")
