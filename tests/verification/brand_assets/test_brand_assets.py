"""Slice 14.10 — brand asset standardization tests."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from verification.brand_assets.checks import check_all
from verification.brand_assets.contract import (
    ACTIVE_SVG_ASSETS,
    ASSET_CONTRACT,
    CONSUMER_COPIES,
    DOCS_CONFIG,
    DOCS_FAVICON,
    FORBIDDEN_EPIC_15_PATHS,
    GENERATOR,
    ICON_CONTRACT,
    LEGACY_BRAND_HEX,
    MARK_MONO,
    MARKETPLACE_ICON,
    MASTER_MARK,
    POLICY_RELATIVE,
    RETIRED_RASTER_REPORT_LOGO,
    VSCODE_ACTIVITY,
    monorepo_root_from_here,
)
from verification.brand_assets.runner import build_report, write_report

ROOT = monorepo_root_from_here()


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_brand_policy_declares_single_authority() -> None:
    policy = _json(POLICY_RELATIVE)
    assert policy["policy_id"] == "codestrata-brand-asset-policy"
    assert policy["policy_version"] == "1.0"
    assert policy["one_master_brand_authority_required"] is True
    assert policy["product_visual_authority"] == "design-system"
    assert policy["governance_assets_authoritative"] is False
    assert policy["legacy_amber_active_allowed"] is False
    assert policy["start_epic_15"] is False


def test_asset_and_icon_contracts_present() -> None:
    assets = _json(ASSET_CONTRACT)
    icons = _json(ICON_CONTRACT)
    assert assets["schema"] == "codestrata-brand-asset-contract"
    assert assets["authority"]["master_brand_mark"] == "codestrata-mark"
    masters = [a["id"] for a in assets["assets"] if a["authority"] == "master"]
    assert sorted(masters) == ["codestrata-mark", "codestrata-wordmark"]
    assert len(icons["custom_symbols"]) == 1


def test_master_mark_uses_design_system_palette() -> None:
    tokens = _json("design-system/tokens/catalog.json")["colors"]
    markup = _text(MASTER_MARK)
    fills = re.findall(r'fill="([^"]+)"', markup)
    assert fills == [tokens["muted"], tokens["teal_dark"], tokens["teal"], tokens["rust"]]
    assert 'viewBox="0 0 22 22"' in markup


def test_active_assets_have_no_legacy_identity() -> None:
    legacy = {value.lower() for value in LEGACY_BRAND_HEX}
    for relative in ACTIVE_SVG_ASSETS:
        fills = {f.lower() for f in re.findall(r'fill="(#[^"]+)"', _text(relative))}
        assert not fills & legacy, relative


def test_consumer_copies_match_master_bytes() -> None:
    for source, copy in CONSUMER_COPIES:
        assert (ROOT / source).read_bytes() == (ROOT / copy).read_bytes(), copy


def test_reports_share_one_mark_geometry() -> None:
    master = _text(MARK_MONO).strip()
    engine_copy = _text(
        "engine/src/codestrata/reporting/assets/codestrata-mark-mono.svg"
    ).strip()
    eir_renderer = _text(
        "platform/src/codestrata_platform/intelligence_reporting/"
        "presentation/static_html/renderer.py"
    )
    assert engine_copy == master
    for rect in re.findall(r"<rect [^/]+/>", master):
        assert rect in eir_renderer


def test_retired_raster_report_logo_is_gone() -> None:
    assert not (ROOT / RETIRED_RASTER_REPORT_LOGO).exists()
    branding = _text("engine/src/codestrata/reporting/branding.py")
    assert "logo_data_uri" not in branding
    assert "codestrata-mark-mono.svg" in branding


def test_favicon_and_docs_header_use_current_identity() -> None:
    config = _text(DOCS_CONFIG)
    assert '"/favicon.svg"' in config or "'/favicon.svg'" in config
    assert "/brand/lockup-horizontal-on-light.svg" in config
    assert _text(DOCS_FAVICON).strip() == _text(MASTER_MARK).strip()


def test_vscode_activity_icon_remains_theme_safe() -> None:
    svg = _text(VSCODE_ACTIVITY)
    assert "currentColor" in svg
    assert not re.findall(r'fill="#', svg)
    assert "<image" not in svg
    assert "<text" not in svg


def test_marketplace_icon_is_128_and_metadata_free() -> None:
    payload = (ROOT / MARKETPLACE_ICON).read_bytes()
    assert payload.startswith(b"\x89PNG\r\n\x1a\n")
    assert payload[16:24].hex() == "0000008000000080"
    assert b"Adobe" not in payload
    assert b"/Users/" not in payload


def test_active_svgs_are_safe_and_responsive() -> None:
    for relative in ACTIVE_SVG_ASSETS:
        markup = _text(relative)
        scanned = markup.replace('xmlns="http://www.w3.org/2000/svg"', "")
        assert "viewBox=" in markup, relative
        assert "<script" not in scanned.lower(), relative
        assert "http" not in scanned, relative
        assert "<foreignObject" not in scanned, relative


def test_generator_is_deterministic() -> None:
    result = subprocess.run(  # noqa: S603 - fixed local command
        [sys.executable, GENERATOR, "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_verifier_passes_without_defects() -> None:
    checks, defects, sizes = check_all(ROOT)
    failed = [c.name for c in checks if not c.ok]
    assert not failed, failed
    assert not defects
    assert sizes.master_brand_assets == 8


def test_report_is_byte_stable(tmp_path: Path) -> None:
    first = build_report(ROOT)
    second = build_report(ROOT)
    assert first.to_dict() == second.to_dict()
    path = write_report(ROOT, first)
    text = path.read_text(encoding="utf-8")
    assert "/Users/" not in text
    assert "/home/" not in text
    assert first.verdict in {"PASS", "PASS_WITH_LIMITATIONS"}


def test_slice_14_14_not_started() -> None:
    for relative in FORBIDDEN_EPIC_15_PATHS:
        assert not (ROOT / relative).exists(), relative
    policy = _json(POLICY_RELATIVE)
    assert policy["accessibility_certification_claimed"] is False
    assert policy["documentation_deployment_complete"] is True
