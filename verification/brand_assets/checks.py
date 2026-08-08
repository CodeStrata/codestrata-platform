"""Deterministic checks for Slice 14.10 (brand assets).

No network. No timestamps. No absolute paths in emitted detail strings.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import struct
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from verification.brand_assets.contract import (
    ACTIVE_RASTER_ASSETS,
    ACTIVE_SVG_ASSETS,
    ASSET_CONTRACT,
    CONSUMER_COPIES,
    DOCS_CONFIG,
    DOCS_CUSTOM_CSS,
    DOCS_FAVICON,
    DOCS_HOME_LINK,
    DOCS_LOCKUP_DARK,
    DOCS_LOCKUP_LIGHT,
    DOCS_MARK,
    DOCS_TILE,
    DOCUMENTATION,
    EIR_RENDERER,
    EIR_STYLES,
    ENGINE_BRANDING,
    ENGINE_PYPROJECT,
    ENGINE_RENDERER,
    ENGINE_REPORT_MARK,
    ENGINE_RESOURCES,
    ENGINE_STYLES,
    EXPORT_MANIFEST,
    FORBIDDEN_15_7_PATHS,
    GENERATOR,
    GOVERNANCE_ARCHIVE,
    ICON_CONTRACT,
    LEGACY_BRAND_HEX,
    LOCKUP_ON_DARK,
    LOCKUP_ON_LIGHT,
    MARK_MONO,
    MARK_ON_DARK,
    MARK_SIMPLIFIED,
    MARK_TILE_ON_DARK,
    MARKETPLACE_ICON,
    MARKETPLACE_ICON_GOVERNANCE_COPY,
    MASTER_ASSETS,
    MASTER_FILL_TOKENS,
    MASTER_MARK,
    MASTER_MARK_BARS,
    MASTER_MARK_GRID,
    MASTER_WORDMARK,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    RASTER_GENERATOR,
    RETIRED_RASTER_REPORT_LOGO,
    SWAGGER_INDEX,
    TOKEN_CATALOG,
    VSCODE_ACTIVITY,
    VSCODE_PACKAGE,
)
from verification.brand_assets.models import AssetSizeInventory, CheckResult, Defect

IMAGE_SUFFIXES = {".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".gif"}
SCAN_EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".vscode-test",
    "build",
    "dist",
    ".export-staging",
    ".codestrata-examples",
    "visual-baselines",
    # Third-party repositories analysed as validation fixtures carry their own brands.
    "validation",
    "test-fixtures",
    "testdata",
    "fixtures",
}

SVG_NAMESPACE_DECLARATION = 'xmlns="http://www.w3.org/2000/svg"'

UNSAFE_SVG_PATTERNS: tuple[tuple[str, str], ...] = (
    ("<script", "script_element"),
    ("javascript:", "script_url"),
    ("<foreignObject", "foreign_object"),
    ("<iframe", "embedded_frame"),
    ("xlink:href", "external_link_attribute"),
    ("http://", "external_url"),
    ("https://", "external_url"),
    ("<image", "embedded_bitmap"),
    ("<text", "live_text"),
    ("font-family", "font_dependency"),
    ("<metadata", "editor_metadata"),
    ("sodipodi", "editor_metadata"),
    ("inkscape", "editor_metadata"),
    ("illustrator", "editor_metadata"),
    ("<!DOCTYPE", "doctype_declaration"),
    ("/Users/", "local_file_path"),
    ("/home/", "local_file_path"),
    ("C:\\", "local_file_path"),
    ("@", "contact_identifier"),
)
EVENT_HANDLER = re.compile(r"\son[a-z]+\s*=")

AIMF_VISUAL_TOKENS = ("aimf-logo", "aimf-icon", "aimf-mark", "ai-modernization-factory-logo")
CURSOR_VISUAL_TOKENS = ("cursor-logo", "cursor-icon", "cursor-mark", "cursor-brand")


def _add(checks: list[CheckResult], name: str, ok: bool, detail: str, category: str) -> None:
    checks.append(CheckResult(name=name, ok=ok, detail=detail, category=category))


def _read(monorepo: Path, relative: str) -> str:
    path = monorepo / relative
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _payload_without_namespace(markup: str) -> str:
    """Strip the SVG namespace declaration before scanning for external URLs."""

    return markup.replace(SVG_NAMESPACE_DECLARATION, "")


def _read_json(monorepo: Path, relative: str) -> dict[str, Any]:
    text = _read(monorepo, relative)
    return json.loads(text) if text else {}


def _bytes(monorepo: Path, relative: str) -> bytes:
    path = monorepo / relative
    return path.read_bytes() if path.is_file() else b""


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _rgb(value: str) -> tuple[int, int, int]:
    raw = value.lstrip("#")
    return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)


def _relative_luminance(value: str) -> float:
    def channel(component: int) -> float:
        ratio = component / 255.0
        return ratio / 12.92 if ratio <= 0.03928 else ((ratio + 0.055) / 1.055) ** 2.4

    red, green, blue = (channel(c) for c in _rgb(value))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast(foreground: str, background: str) -> float:
    first = _relative_luminance(foreground)
    second = _relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def _png_chunks(payload: bytes) -> list[str]:
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return []
    chunks: list[str] = []
    offset = 8
    while offset + 8 <= len(payload):
        (length,) = struct.unpack(">I", payload[offset : offset + 4])
        tag = payload[offset + 4 : offset + 8].decode("ascii", "replace")
        chunks.append(tag)
        offset += 12 + length
        if tag == "IEND":
            break
    return chunks


def _png_size(payload: bytes) -> tuple[int, int]:
    if len(payload) < 24:
        return (0, 0)
    width, height = struct.unpack(">II", payload[16:24])
    return int(width), int(height)


def _png_colors(monorepo: Path, relative: str) -> set[str]:
    """Return the distinct opaque colours in a packaged raster asset."""

    from PIL import Image

    path = monorepo / relative
    if not path.is_file():
        return set()
    with Image.open(path) as handle:
        image = handle.convert("RGBA")
        pixels = image.tobytes()
    return {
        f"#{pixels[i]:02x}{pixels[i + 1]:02x}{pixels[i + 2]:02x}"
        for i in range(0, len(pixels), 4)
        if pixels[i + 3] > 0
    }


def _svg_fills(markup: str) -> list[str]:
    return re.findall(r'fill="([^"]+)"', markup)


def _svg_hex_fills(markup: str) -> set[str]:
    return {fill.lower() for fill in _svg_fills(markup) if fill.startswith("#")}


def _scan_images(monorepo: Path) -> list[Path]:
    found: list[Path] = []
    for path in sorted(monorepo.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if SCAN_EXCLUDED_PARTS & set(path.relative_to(monorepo).parts):
            continue
        found.append(path)
    return found


def _mark_bars(markup: str) -> list[tuple[float, float, float, float]]:
    bars: list[tuple[float, float, float, float]] = []
    for match in re.finditer(r"<rect ([^/]+)/>", markup):
        attrs = dict(re.findall(r'(\w[\w-]*)="([^"]*)"', match.group(1)))
        if "x" not in attrs or "y" not in attrs:
            continue
        bars.append(
            (
                float(attrs["x"]),
                float(attrs["y"]),
                float(attrs["width"]),
                float(attrs["height"]),
            )
        )
    return bars


def check_all(  # noqa: PLR0912, PLR0915 - one deterministic check surface
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], AssetSizeInventory]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = _read_json(monorepo, POLICY_RELATIVE)
    contract = _read_json(monorepo, ASSET_CONTRACT)
    icons = _read_json(monorepo, ICON_CONTRACT)
    tokens = _read_json(monorepo, TOKEN_CATALOG)
    colors: dict[str, str] = dict(tokens.get("colors") or {})

    # --- 1. brand policy -----------------------------------------------------
    _add(
        checks,
        "policy:identity",
        policy.get("policy_id") == POLICY_ID and policy.get("policy_version") == POLICY_VERSION,
        f"{policy.get('policy_id')}:{policy.get('policy_version')}",
        "brand_asset_policy",
    )
    required_true = (
        "one_master_brand_authority_required",
        "surface_specific_derivatives_allowed",
        "universal_logo_authority_defined",
        "wordmark_authority_defined",
        "monochrome_variant_required",
        "light_background_variant_required",
        "dark_background_variant_required",
        "vscode_currentcolor_derivative_allowed",
        "marketplace_raster_derivative_allowed",
        "favicon_derivative_allowed",
    )
    missing_true = [key for key in required_true if policy.get(key) is not True]
    _add(
        checks,
        "policy:authority_fields",
        not missing_true,
        "complete" if not missing_true else ",".join(missing_true),
        "brand_asset_policy",
    )
    required_false = (
        "legacy_amber_active_allowed",
        "aimf_active_allowed",
        "cursor_active_allowed",
        "embedded_customer_identity_allowed",
        "external_asset_dependency_allowed",
        "runtime_behavior_change_allowed",
        "schema_change_allowed",
        "report_ia_change_allowed",
        "visualization_semantics_change_allowed",
        "marketplace_gallery_redesign_allowed",
        "design_system_palette_change_allowed",
        "start_slice_15_7",
    )
    wrong_false = [key for key in required_false if policy.get(key) is not False]
    _add(
        checks,
        "policy:prohibitions",
        not wrong_false,
        "complete" if not wrong_false else ",".join(wrong_false),
        "brand_asset_policy",
    )
    _add(
        checks,
        "policy:design_system_additive",
        policy.get("design_system_version") == "1.0"
        and policy.get("design_system_bump_required") is False
        and policy.get("additive_contract_under_design_system_1_0") is True,
        f"ds={policy.get('design_system_version')}",
        "brand_asset_policy",
    )
    _add(
        checks,
        "policy:versions_pinned",
        policy.get("extension_version") == "0.2.0"
        and policy.get("assessment_schema_version") == "1.2",
        f"ext={policy.get('extension_version')} schema={policy.get('assessment_schema_version')}",
        "brand_asset_policy",
    )
    policy_text = _read(monorepo, POLICY_RELATIVE)
    _add(
        checks,
        "policy:no_local_paths",
        "/Users/" not in policy_text and "/home/" not in policy_text,
        "clean",
        "brand_asset_policy",
    )
    _add(
        checks,
        "policy:limitations_declared",
        isinstance(policy.get("limitations"), list) and bool(policy.get("limitations")),
        f"count={len(policy.get('limitations') or [])}",
        "brand_asset_policy",
    )

    # --- 2. inventory --------------------------------------------------------
    images = _scan_images(monorepo)
    relatives = [path.relative_to(monorepo).as_posix() for path in images]
    _add(
        checks,
        "inventory:assets_discovered",
        len(relatives) > 0,
        f"count={len(relatives)}",
        "inventory",
    )
    missing_active = [
        rel for rel in (*ACTIVE_SVG_ASSETS, *ACTIVE_RASTER_ASSETS) if rel not in relatives
    ]
    _add(
        checks,
        "inventory:active_assets_present",
        not missing_active,
        "complete" if not missing_active else ",".join(missing_active),
        "inventory",
    )
    contract_paths = {entry.get("path") for entry in contract.get("assets") or []}
    unmapped = [rel for rel in (*ACTIVE_SVG_ASSETS, *ACTIVE_RASTER_ASSETS) if rel not in
                contract_paths]
    _add(
        checks,
        "inventory:active_assets_mapped",
        not unmapped,
        "mapped" if not unmapped else ",".join(unmapped),
        "inventory",
    )
    _add(
        checks,
        "inventory:contract_identity",
        contract.get("schema") == "codestrata-brand-asset-contract"
        and contract.get("schema_version") == "1.0.0"
        and contract.get("policy") == f"{POLICY_ID}:{POLICY_VERSION}",
        f"{contract.get('schema')}:{contract.get('schema_version')}",
        "inventory",
    )
    _add(
        checks,
        "inventory:generator_present",
        (monorepo / GENERATOR).is_file() and (monorepo / RASTER_GENERATOR).is_file(),
        "vector+raster generators present",
        "inventory",
    )

    # --- 3. authority --------------------------------------------------------
    authority = contract.get("authority") or {}
    _add(
        checks,
        "authority:single_master",
        authority.get("master_brand_mark") == "codestrata-mark"
        and authority.get("single_master_required") is True,
        str(authority.get("master_brand_mark")),
        "authority",
    )
    masters = [
        entry.get("id")
        for entry in contract.get("assets") or []
        if entry.get("authority") == "master"
    ]
    _add(
        checks,
        "authority:master_count",
        sorted(masters) == ["codestrata-mark", "codestrata-wordmark"],
        ",".join(sorted(masters)),
        "authority",
    )
    _add(
        checks,
        "authority:design_system_owns_product_visuals",
        policy.get("product_visual_authority") == "design-system"
        and policy.get("governance_assets_authoritative") is False,
        str(policy.get("product_visual_authority")),
        "authority",
    )
    governance_entry = authority.get("governance_package") or {}
    _add(
        checks,
        "authority:governance_archived",
        governance_entry.get("status") == "historical_archive"
        and governance_entry.get("authoritative") is False,
        str(governance_entry.get("status")),
        "authority",
    )
    derivatives_without_source = [
        entry.get("id")
        for entry in contract.get("assets") or []
        if entry.get("authority") != "master" and not entry.get("source")
    ]
    _add(
        checks,
        "authority:derivatives_trace_to_master",
        not derivatives_without_source,
        "traced" if not derivatives_without_source else ",".join(derivatives_without_source),
        "authority",
    )
    unknown_authority = [
        entry.get("id")
        for entry in contract.get("assets") or []
        if entry.get("authority")
        not in {
            "master",
            "approved_derivative",
            "consumer_copy",
            "embedded_copy",
            "authorized_duplicate",
            "gallery_asset",
        }
    ]
    _add(
        checks,
        "authority:classifications_known",
        not unknown_authority,
        "known" if not unknown_authority else ",".join(str(x) for x in unknown_authority),
        "authority",
    )

    # --- 4. master mark ------------------------------------------------------
    master = _read(monorepo, MASTER_MARK)
    _add(
        checks,
        "master_mark:present",
        bool(master.strip()),
        f"bytes={len(master)}",
        "master_mark",
    )
    _add(
        checks,
        "master_mark:viewbox",
        f'viewBox="0 0 {int(MASTER_MARK_GRID)} {int(MASTER_MARK_GRID)}"' in master,
        "viewBox present",
        "master_mark",
    )
    bars = _mark_bars(master)
    _add(
        checks,
        "master_mark:geometry",
        tuple(bars) == MASTER_MARK_BARS,
        f"bars={len(bars)}",
        "master_mark",
    )
    expected_fills = [colors.get(token, "").lower() for token in MASTER_FILL_TOKENS]
    actual_fills = [fill.lower() for fill in _svg_fills(master)]
    _add(
        checks,
        "master_mark:token_colors",
        actual_fills == expected_fills,
        ",".join(MASTER_FILL_TOKENS),
        "master_mark",
    )
    legacy_in_master = sorted(_svg_hex_fills(master) & {h.lower() for h in LEGACY_BRAND_HEX})
    _add(
        checks,
        "master_mark:no_legacy_identity",
        not legacy_in_master,
        "clean" if not legacy_in_master else ",".join(legacy_in_master),
        "master_mark",
    )
    contract_geometry = contract.get("geometry") or {}
    contract_bars = [
        (float(b["x"]), float(b["y"]), float(b["width"]), float(b["height"]))
        for b in contract_geometry.get("mark_bars") or []
    ]
    _add(
        checks,
        "master_mark:contract_geometry_matches",
        tuple(contract_bars) == MASTER_MARK_BARS,
        f"contract_bars={len(contract_bars)}",
        "master_mark",
    )

    # --- 5. wordmark ---------------------------------------------------------
    wordmark = _read(monorepo, MASTER_WORDMARK)
    _add(checks, "wordmark:present", bool(wordmark.strip()), "present", "wordmark")
    _add(
        checks,
        "wordmark:decision_recorded",
        policy.get("wordmark_decision")
        == "dedicated_outlined_asset_for_site_lockups_typography_on_product_surfaces",
        str(policy.get("wordmark_decision")),
        "wordmark",
    )
    _add(
        checks,
        "wordmark:outlined_no_font_dependency",
        "<text" not in wordmark and "font-family" not in wordmark and "<path" in wordmark,
        "outlined paths",
        "wordmark",
    )
    wordmark_entry = next(
        (e for e in contract.get("assets") or [] if e.get("id") == "codestrata-wordmark"), {}
    )
    _add(
        checks,
        "wordmark:contract_flags",
        wordmark_entry.get("outlined") is True
        and wordmark_entry.get("font_dependency") is False,
        "outlined=true font_dependency=false",
        "wordmark",
    )
    _add(
        checks,
        "wordmark:typography_on_product_surfaces",
        "brand-word" in _read(monorepo, ENGINE_RENDERER)
        and "report-product-name" in _read(monorepo, EIR_RENDERER),
        "reports render the name as text",
        "wordmark",
    )

    # --- 6. variants ---------------------------------------------------------
    missing_variants = [rel for rel in MASTER_ASSETS if not (monorepo / rel).is_file()]
    _add(
        checks,
        "variants:master_set_present",
        not missing_variants,
        "complete" if not missing_variants else ",".join(missing_variants),
        "variants",
    )
    mono = _read(monorepo, MARK_MONO)
    _add(
        checks,
        "variants:monochrome_current_color",
        "currentColor" in mono and not _svg_hex_fills(mono),
        "currentColor only",
        "variants",
    )
    on_dark = _read(monorepo, MARK_ON_DARK)
    night_ink = (colors.get("night_ink") or "").lower()
    _add(
        checks,
        "variants:dark_variant_uses_night_ink",
        bool(night_ink) and _svg_hex_fills(on_dark) == {night_ink},
        f"fills={sorted(_svg_hex_fills(on_dark))}",
        "variants",
    )
    _add(
        checks,
        "variants:no_full_color_dark_variant",
        policy.get("full_color_dark_background_variant_created") is False,
        "monochrome_light serves dark backgrounds",
        "variants",
    )
    simplified = _read(monorepo, MARK_SIMPLIFIED)
    simplified_bars = _mark_bars(simplified)
    _add(
        checks,
        "variants:simplified_reduction_declared",
        len(simplified_bars) == 3 and contract_geometry.get("simplified_bar_count") == 3,
        f"bars={len(simplified_bars)}",
        "variants",
    )
    consumers_by_asset: dict[str, list[str]] = defaultdict(list)
    for entry in contract.get("assets") or []:
        for surface in entry.get("surfaces") or []:
            consumers_by_asset[str(entry.get("id"))].append(surface)
    variants_without_consumer = [
        entry.get("id")
        for entry in contract.get("assets") or []
        if not (entry.get("surfaces") or [])
    ]
    _add(
        checks,
        "variants:every_variant_has_consumer",
        not variants_without_consumer,
        "all consumed"
        if not variants_without_consumer
        else ",".join(str(x) for x in variants_without_consumer),
        "variants",
    )
    _add(
        checks,
        "variants:clear_space_and_minimum_size_defined",
        bool(contract.get("clear_space")) and bool(contract.get("minimum_size")),
        "defined",
        "variants",
    )

    # --- 7. SVG safety -------------------------------------------------------
    for relative in ACTIVE_SVG_ASSETS:
        markup = _read(monorepo, relative)
        scanned = _payload_without_namespace(markup).lower()
        findings = sorted(
            {label for needle, label in UNSAFE_SVG_PATTERNS if needle.lower() in scanned}
        )
        if EVENT_HANDLER.search(markup):
            findings.append("event_handler")
        _add(
            checks,
            f"svg_safety:{relative}",
            not findings,
            "safe" if not findings else ",".join(sorted(set(findings))),
            "svg_safety",
        )
        _add(
            checks,
            f"svg_safety:{relative}_viewbox",
            "viewBox=" in markup,
            "viewBox present",
            "svg_safety",
        )
    docs_home = _read(monorepo, DOCS_HOME_LINK)
    _add(
        checks,
        "svg_safety:docs_inline_glyph",
        "<script" not in docs_home.split("<template>")[-1]
        and "xlink:href" not in docs_home
        and 'fill="currentColor"' in docs_home,
        "inline glyph safe",
        "svg_safety",
    )

    # --- 8. raster metadata --------------------------------------------------
    for relative in ACTIVE_RASTER_ASSETS:
        payload = _bytes(monorepo, relative)
        chunks = _png_chunks(payload)
        ancillary = [tag for tag in chunks if tag not in {"IHDR", "IDAT", "IEND"}]
        name = relative.rsplit("/", 1)[-1]
        _add(
            checks,
            f"raster_metadata:{name}",
            bool(chunks) and not ancillary,
            "critical chunks only" if not ancillary else ",".join(sorted(set(ancillary))),
            "raster_metadata",
        )
        for needle in (b"/Users/", b"/home/", b"Adobe", b"XML:com.adobe.xmp"):
            if needle in payload:
                _add(
                    checks,
                    f"raster_metadata:{name}_identity_free",
                    False,
                    "identity fragment present",
                    "raster_metadata",
                )
                break
        else:
            _add(
                checks,
                f"raster_metadata:{name}_identity_free",
                True,
                "no identity fragments",
                "raster_metadata",
            )
    _add(
        checks,
        "raster_metadata:retired_logo_removed",
        not (monorepo / RETIRED_RASTER_REPORT_LOGO).is_file(),
        "amber raster report logo absent",
        "raster_metadata",
    )

    # --- 9. duplicates -------------------------------------------------------
    by_hash: dict[str, list[str]] = defaultdict(list)
    for path in images:
        by_hash[_sha(path.read_bytes())].append(path.relative_to(monorepo).as_posix())
    duplicate_groups = [group for group in by_hash.values() if len(group) > 1]
    authorized_copies = {(source, copy) for source, copy in CONSUMER_COPIES}
    unauthorized: list[str] = []
    for group in duplicate_groups:
        inside_archive = all(item.startswith(GOVERNANCE_ARCHIVE) for item in group)
        pairs = {
            (a, b)
            for a in group
            for b in group
            if a != b and ((a, b) in authorized_copies or (b, a) in authorized_copies)
        }
        marketplace_pair = set(group) <= {MARKETPLACE_ICON, MARKETPLACE_ICON_GOVERNANCE_COPY}
        if inside_archive or pairs or marketplace_pair:
            continue
        unauthorized.append(",".join(sorted(group)))
    _add(
        checks,
        "duplicates:classified",
        not unauthorized,
        "all duplicates authorized" if not unauthorized else ";".join(unauthorized),
        "duplicates",
    )
    for source, copy in CONSUMER_COPIES:
        _add(
            checks,
            f"duplicates:copy_matches_master:{copy}",
            _sha(_bytes(monorepo, source)) == _sha(_bytes(monorepo, copy)),
            "checksum equal",
            "duplicates",
        )
    _add(
        checks,
        "duplicates:marketplace_copy_matches",
        _sha(_bytes(monorepo, MARKETPLACE_ICON))
        == _sha(_bytes(monorepo, MARKETPLACE_ICON_GOVERNANCE_COPY)),
        "checksum equal",
        "duplicates",
    )

    # --- 10. legacy amber ----------------------------------------------------
    legacy_lower = {h.lower() for h in LEGACY_BRAND_HEX}
    active_legacy: list[str] = []
    for relative in ACTIVE_SVG_ASSETS:
        hits = sorted(_svg_hex_fills(_read(monorepo, relative)) & legacy_lower)
        if hits:
            active_legacy.append(relative.rsplit("/", 1)[-1])
    _add(
        checks,
        "legacy_assets:no_amber_in_active_vectors",
        not active_legacy,
        "clean" if not active_legacy else ",".join(active_legacy),
        "legacy_assets",
    )
    icon_colors = _png_colors(monorepo, MARKETPLACE_ICON)
    legacy_rgb_present = sorted(icon_colors & legacy_lower)
    _add(
        checks,
        "legacy_assets:no_amber_in_marketplace_raster",
        not legacy_rgb_present,
        "clean" if not legacy_rgb_present else ",".join(legacy_rgb_present),
        "legacy_assets",
    )
    _add(
        checks,
        "legacy_assets:archive_retained",
        (monorepo / GOVERNANCE_ARCHIVE / "svg" / "icon.svg").is_file(),
        "history preserved",
        "legacy_assets",
    )
    _add(
        checks,
        "legacy_assets:archive_declared_non_authoritative",
        (contract.get("legacy_assets") or {}).get("amber_era", {}).get("classification")
        == "historical_archive",
        "declared",
        "legacy_assets",
    )
    docs_config = _read(monorepo, DOCS_CONFIG)
    _add(
        checks,
        "legacy_assets:docs_header_current_identity",
        "/brand/lockup-horizontal-on-light.svg" in docs_config
        and not (_svg_hex_fills(_read(monorepo, DOCS_LOCKUP_LIGHT)) & legacy_lower),
        "docs header uses current identity",
        "legacy_assets",
    )

    # --- 11. AIMF ------------------------------------------------------------
    aimf_assets = [rel for rel in relatives if any(t in rel.lower() for t in AIMF_VISUAL_TOKENS)]
    _add(
        checks,
        "aimf:no_visual_assets",
        not aimf_assets,
        "absent" if not aimf_assets else ",".join(aimf_assets),
        "aimf",
    )
    _add(
        checks,
        "aimf:contract_records_absence",
        (contract.get("legacy_assets") or {}).get("aimf", {}).get("visual_assets_present")
        is False,
        "recorded",
        "aimf",
    )
    aimf_in_active_svg = [
        relative
        for relative in ACTIVE_SVG_ASSETS
        if "aimf" in _read(monorepo, relative).lower()
    ]
    _add(
        checks,
        "aimf:not_in_active_vectors",
        not aimf_in_active_svg,
        "clean" if not aimf_in_active_svg else ",".join(aimf_in_active_svg),
        "aimf",
    )

    # --- 12. Cursor ----------------------------------------------------------
    cursor_assets = [
        rel for rel in relatives if any(t in rel.lower() for t in CURSOR_VISUAL_TOKENS)
    ]
    _add(
        checks,
        "cursor:no_visual_assets",
        not cursor_assets,
        "absent" if not cursor_assets else ",".join(cursor_assets),
        "cursor",
    )
    _add(
        checks,
        "cursor:contract_records_absence",
        (contract.get("legacy_assets") or {}).get("cursor", {}).get("visual_assets_present")
        is False,
        "recorded",
        "cursor",
    )
    _add(
        checks,
        "cursor:no_active_product_reference",
        "cursor" not in _read(monorepo, VSCODE_PACKAGE).lower()
        and "cursor" not in docs_config.lower(),
        "clean",
        "cursor",
    )

    # --- 13. website consumer ------------------------------------------------
    _add(
        checks,
        "website_consumer:token_authority_is_website",
        str(tokens.get("authority", "")).endswith("codestrata.ai"),
        str(tokens.get("authority")),
        "website_consumer",
    )
    _add(
        checks,
        "website_consumer:palette_unchanged",
        colors.get("teal") == "#16756a"
        and colors.get("canvas") == "#f4f6f3"
        and colors.get("rust") == "#a04b17",
        "teal/canvas/rust intact",
        "website_consumer",
    )
    _add(
        checks,
        "website_consumer:no_remote_asset_dependency",
        all(
            "http" not in _payload_without_namespace(_read(monorepo, relative))
            for relative in ACTIVE_SVG_ASSETS
        ),
        "all assets local",
        "website_consumer",
    )
    _add(
        checks,
        "website_consumer:site_link_preserved",
        "https://codestrata.ai/" in docs_config,
        "logo links to website",
        "website_consumer",
    )

    # --- 14. documentation consumer -----------------------------------------
    _add(
        checks,
        "documentation_consumer:lockups_referenced",
        "/brand/lockup-horizontal-on-light.svg" in docs_config
        and "/brand/lockup-horizontal-on-dark.svg" in docs_config,
        "light+dark lockups referenced",
        "documentation_consumer",
    )
    _add(
        checks,
        "documentation_consumer:logo_alt_text",
        'alt: "CodeStrata"' in docs_config,
        "alt text present",
        "documentation_consumer",
    )
    _add(
        checks,
        "documentation_consumer:favicon_referenced",
        '"/favicon.svg"' in docs_config or "'/favicon.svg'" in docs_config,
        "favicon link present",
        "documentation_consumer",
    )
    docs_asset_refs = re.findall(r'href: "(/[^"]+\.(?:svg|png|ico))"', docs_config)
    docs_asset_refs += re.findall(r'"(/brand/[^"]+\.svg)"', docs_config)
    dead_refs = [
        ref for ref in docs_asset_refs if not (monorepo / "docs" / "public" / ref.lstrip("/")).is_file()
    ]
    _add(
        checks,
        "documentation_consumer:no_dead_references",
        not dead_refs,
        "resolved" if not dead_refs else ",".join(dead_refs),
        "documentation_consumer",
    )
    _add(
        checks,
        "documentation_consumer:copies_match_master",
        all(
            _sha(_bytes(monorepo, source)) == _sha(_bytes(monorepo, copy))
            for source, copy in CONSUMER_COPIES
            if copy.startswith("docs/")
        ),
        "docs copies match master",
        "documentation_consumer",
    )

    swagger_index = _read(monorepo, SWAGGER_INDEX)
    _add(
        checks,
        "documentation_consumer:platform_api_portal_aligned",
        all(
            _sha(_bytes(monorepo, source)) == _sha(_bytes(monorepo, copy))
            for source, copy in CONSUMER_COPIES
            if copy.startswith("platform/api/")
        ),
        "API portal copies match master",
        "documentation_consumer",
    )
    _add(
        checks,
        "documentation_consumer:platform_api_portal_references_intact",
        "/api/docs/static/brand/icon.svg" in swagger_index
        and "/api/docs/static/brand/lockup-horizontal-on-light.svg" in swagger_index
        and "/api/docs/static/brand/lockup-horizontal-on-dark.svg" in swagger_index,
        "API portal asset references resolve",
        "documentation_consumer",
    )
    _add(
        checks,
        "documentation_consumer:platform_api_portal_alt_text",
        swagger_index.count('alt="CodeStrata"') >= 2,
        "API portal logos carry alt text",
        "documentation_consumer",
    )

    # --- 15. assessment consumer --------------------------------------------
    branding = _read(monorepo, ENGINE_BRANDING)
    renderer = _read(monorepo, ENGINE_RENDERER)
    engine_styles = _read(monorepo, ENGINE_STYLES)
    _add(
        checks,
        "assessment_consumer:packaged_vector_mark",
        (monorepo / ENGINE_REPORT_MARK).is_file()
        and "codestrata-mark-mono.svg" in branding,
        "packaged vector mark",
        "assessment_consumer",
    )
    _add(
        checks,
        "assessment_consumer:no_raster_data_uri",
        "data:image/png;base64" not in renderer and "logo_data_uri" not in renderer,
        "no embedded raster",
        "assessment_consumer",
    )
    _add(
        checks,
        "assessment_consumer:inline_mark_rendered",
        "brand_mark_svg()" in renderer and "brand-lockup" in renderer,
        "inline mark in product identity block",
        "assessment_consumer",
    )
    _add(
        checks,
        "assessment_consumer:mark_styled",
        ".brand-lockup" in engine_styles and ".cs-mark" in engine_styles,
        "styles present",
        "assessment_consumer",
    )
    _add(
        checks,
        "assessment_consumer:packaging_updated",
        'reporting/assets/*.svg' in _read(monorepo, ENGINE_PYPROJECT)
        and "codestrata-mark-mono.svg" in _read(monorepo, ENGINE_RESOURCES),
        "packaging and resource accessor aligned",
        "assessment_consumer",
    )

    # --- 16. EIR consumer ----------------------------------------------------
    eir_renderer = _read(monorepo, EIR_RENDERER)
    eir_styles = _read(monorepo, EIR_STYLES)
    master_mono_markup = _read(monorepo, MARK_MONO).strip()
    embedded = re.search(r"BRAND_MARK_SVG = (\(\n.*?\n\))", eir_renderer, re.DOTALL)
    embedded_markup = ""
    if embedded:
        try:
            embedded_markup = str(ast.literal_eval(embedded.group(1)))
        except (SyntaxError, ValueError):
            embedded_markup = ""
    _add(
        checks,
        "eir_consumer:embedded_mark_matches_master",
        embedded_markup == master_mono_markup,
        "identical markup" if embedded_markup == master_mono_markup else "markup diverged",
        "eir_consumer",
    )
    _add(
        checks,
        "eir_consumer:product_bar_renders_mark",
        "report-product-mark" in eir_renderer and "report-product-mark" in eir_styles,
        "mark rendered and styled",
        "eir_consumer",
    )
    _add(
        checks,
        "eir_consumer:no_external_asset",
        "http://" not in eir_renderer.split("CONTENT_SECURITY_POLICY")[0]
        and "<img" not in eir_renderer,
        "self-contained",
        "eir_consumer",
    )
    _add(
        checks,
        "eir_consumer:shared_geometry_with_assessment",
        embedded_markup == _read(monorepo, ENGINE_REPORT_MARK).strip(),
        "reports share one mark geometry",
        "eir_consumer",
    )

    # --- 17. VS Code consumer ------------------------------------------------
    activity = _read(monorepo, VSCODE_ACTIVITY)
    package_json = _read(monorepo, VSCODE_PACKAGE)
    _add(
        checks,
        "vscode_consumer:activity_current_color",
        "currentColor" in activity and not _svg_hex_fills(activity),
        "currentColor only",
        "vscode_consumer",
    )
    _add(
        checks,
        "vscode_consumer:activity_no_raster_or_wordmark",
        "<image" not in activity and "<text" not in activity,
        "vector monochrome mark",
        "vscode_consumer",
    )
    _add(
        checks,
        "vscode_consumer:activity_referenced",
        "media/codestrata-activity.svg" in package_json,
        "referenced by view container",
        "vscode_consumer",
    )
    _add(
        checks,
        "vscode_consumer:extension_version_unchanged",
        '"version": "0.2.0"' in package_json,
        "0.2.0",
        "vscode_consumer",
    )
    _add(
        checks,
        "vscode_consumer:generic_actions_use_codicons",
        '"$(refresh)"' in package_json,
        "codicons retained for generic actions",
        "vscode_consumer",
    )

    # --- 18. Marketplace consumer -------------------------------------------
    icon_payload = _bytes(monorepo, MARKETPLACE_ICON)
    width, height = _png_size(icon_payload)
    _add(
        checks,
        "marketplace_consumer:icon_dimensions",
        (width, height) == (128, 128),
        f"{width}x{height}",
        "marketplace_consumer",
    )
    _add(
        checks,
        "marketplace_consumer:icon_referenced",
        '"icon": "media/codestrata-icon.png"' in package_json,
        "package icon referenced",
        "marketplace_consumer",
    )
    token_pixels = [
        token
        for token in MASTER_FILL_TOKENS
        if colors.get(token, "").lower() in icon_colors
    ]
    _add(
        checks,
        "marketplace_consumer:icon_uses_master_palette",
        len(token_pixels) == len(MASTER_FILL_TOKENS),
        ",".join(token_pixels),
        "marketplace_consumer",
    )
    raster_generator = _read(monorepo, RASTER_GENERATOR)
    _add(
        checks,
        "marketplace_consumer:icon_geometry_from_master",
        "MASTER_MARK_BARS" in raster_generator and "draw.ellipse" not in raster_generator,
        "master bar projection",
        "marketplace_consumer",
    )
    _add(
        checks,
        "marketplace_consumer:gallery_not_redesigned",
        (contract.get("screenshot_assets") or {}).get("redesign_allowed_in_14_10") is False
        and (contract.get("screenshot_assets") or {}).get("owning_slice") == "14.6",
        "gallery owned by 14.6",
        "marketplace_consumer",
    )

    # --- 19. favicon ---------------------------------------------------------
    favicon = _read(monorepo, DOCS_FAVICON)
    favicon_outputs = contract.get("favicon_outputs") or {}
    _add(
        checks,
        "favicon:vector_primary",
        favicon.strip() == master.strip() and favicon_outputs.get("svg") == DOCS_FAVICON,
        "svg favicon derived from master",
        "favicon",
    )
    _add(
        checks,
        "favicon:no_unneeded_raster_matrix",
        favicon_outputs.get("png_fallbacks") == [] and favicon_outputs.get("ico") is None,
        "single declared output",
        "favicon",
    )
    _add(
        checks,
        "favicon:current_identity",
        not (_svg_hex_fills(favicon) & legacy_lower),
        "current identity",
        "favicon",
    )

    # --- 20. icon language ---------------------------------------------------
    _add(
        checks,
        "icons:contract_identity",
        icons.get("schema") == "codestrata-brand-icon-contract"
        and icons.get("policy") == f"{POLICY_ID}:{POLICY_VERSION}",
        str(icons.get("schema")),
        "icon_language",
    )
    custom_symbols = icons.get("custom_symbols") or []
    _add(
        checks,
        "icons:single_custom_symbol",
        len(custom_symbols) == 1
        and custom_symbols[0].get("id") == "product_identity",
        f"count={len(custom_symbols)}",
        "icon_language",
    )
    _add(
        checks,
        "icons:generic_actions_delegated",
        (icons.get("vscode") or {}).get("custom_icon_for_generic_action_allowed") is False
        and policy.get("host_native_icon_preferred_for_generic_actions") is True,
        "host-native preferred",
        "icon_language",
    )
    _add(
        checks,
        "icons:no_color_only_meaning",
        (icons.get("principles") or {}).get("meaning", "").startswith("never colour alone"),
        "labels accompany icons",
        "icon_language",
    )
    _add(
        checks,
        "icons:no_proprietary_library",
        policy.get("proprietary_generic_icon_library_allowed") is False,
        "library scope bounded",
        "icon_language",
    )
    _add(
        checks,
        "icons:visualization_authority_referenced",
        "codestrata-visualization-contract:1.0" in json.dumps(icons.get("semantic_roles") or {}),
        "severity semantics delegated",
        "icon_language",
    )

    # --- 21. export boundary -------------------------------------------------
    export_manifest = _read(monorepo, EXPORT_MANIFEST)
    _add(
        checks,
        "export_boundary:docs_copies_inside_export_root",
        all(copy.startswith("docs/") for _, copy in CONSUMER_COPIES if "docs" in copy),
        "docs assets self-contained",
        "export_boundary",
    )
    _add(
        checks,
        "export_boundary:no_monorepo_relative_reference",
        "design-system/assets" not in docs_config
        and "design-system/assets" not in package_json
        and "../../design-system" not in _read(monorepo, DOCS_CUSTOM_CSS),
        "consumers do not reach outside their export root",
        "export_boundary",
    )
    _add(
        checks,
        "export_boundary:vscode_icon_required_by_manifest",
        "media/codestrata-icon.png" in export_manifest,
        "icon required in exported extension",
        "export_boundary",
    )
    _add(
        checks,
        "export_boundary:engine_asset_packaged_under_src",
        ENGINE_REPORT_MARK.startswith("engine/src/"),
        "packaged inside exported source tree",
        "export_boundary",
    )
    _add(
        checks,
        "export_boundary:copy_reason_documented",
        all(
            entry.get("copy_reason")
            for entry in contract.get("assets") or []
            if entry.get("authority") in {"consumer_copy", "embedded_copy", "authorized_duplicate"}
            and entry.get("id") not in {"docs-lockup-on-light", "docs-lockup-on-dark"}
        ),
        "copies justified",
        "export_boundary",
    )

    # --- 22. asset sizes -----------------------------------------------------
    sizes = AssetSizeInventory()
    for relative in MASTER_ASSETS:
        sizes.master_brand_assets += 1
        sizes.master_brand_bytes += len(_bytes(monorepo, relative))
    generated_derivatives = [
        copy for _, copy in CONSUMER_COPIES
    ]
    for relative in generated_derivatives:
        sizes.generated_derivatives += 1
        sizes.generated_derivative_bytes += len(_bytes(monorepo, relative))
    for relative in ACTIVE_RASTER_ASSETS:
        sizes.packaged_marketplace_assets += 1
        sizes.packaged_marketplace_bytes += len(_bytes(monorepo, relative))
    for path in images:
        if path.relative_to(monorepo).as_posix().startswith(GOVERNANCE_ARCHIVE):
            sizes.archived_legacy_assets += 1
            sizes.archived_legacy_bytes += path.stat().st_size
    _add(
        checks,
        "asset_sizes:inventory_bounded",
        sizes.master_brand_assets == len(MASTER_ASSETS)
        and sizes.generated_derivatives == len(CONSUMER_COPIES),
        f"masters={sizes.master_brand_assets} derivatives={sizes.generated_derivatives}",
        "asset_sizes",
    )
    _add(
        checks,
        "asset_sizes:report_mark_small",
        0 < len(_bytes(monorepo, ENGINE_REPORT_MARK)) <= 1024,
        f"bytes={len(_bytes(monorepo, ENGINE_REPORT_MARK))}",
        "asset_sizes",
    )
    _add(
        checks,
        "asset_sizes:marketplace_icon_bounded",
        0 < len(icon_payload) <= 64 * 1024,
        f"bytes={len(icon_payload)}",
        "asset_sizes",
    )

    # --- 23. accessibility baseline -----------------------------------------
    canvas = colors.get("canvas", "#ffffff")
    paper = colors.get("paper", "#ffffff")
    night = colors.get("night", "#000000")
    weak_on_light = [
        token
        for token in MASTER_FILL_TOKENS
        if min(_contrast(colors[token], canvas), _contrast(colors[token], paper)) < 3.0
    ]
    _add(
        checks,
        "accessibility_baseline:mark_contrast_on_light",
        not weak_on_light,
        "all bars >= 3:1" if not weak_on_light else ",".join(weak_on_light),
        "accessibility_baseline",
    )
    _add(
        checks,
        "accessibility_baseline:mark_contrast_on_dark",
        _contrast(colors.get("night_ink", "#ffffff"), night) >= 3.0,
        "night_ink on night >= 3:1",
        "accessibility_baseline",
    )
    _add(
        checks,
        "accessibility_baseline:report_mark_decorative_with_text",
        'aria-hidden="true"' in master_mono_markup and "brand-word" in renderer,
        "decorative mark plus text name",
        "accessibility_baseline",
    )
    _add(
        checks,
        "accessibility_baseline:activity_icon_decorative",
        'aria-hidden="true"' in activity,
        "host provides the accessible name",
        "accessibility_baseline",
    )
    _add(
        checks,
        "accessibility_baseline:content_image_alt_contract",
        'alt: "CodeStrata"' in docs_config,
        "documentation logo has alt text",
        "accessibility_baseline",
    )
    _add(
        checks,
        "accessibility_baseline:not_certified_here",
        policy.get("accessibility_certification_claimed") is False,
        "acceptance owned by 14.11 policy",
        "accessibility_baseline",
    )

    # --- 24. responsive baseline --------------------------------------------
    missing_viewbox = [
        relative for relative in ACTIVE_SVG_ASSETS if "viewBox=" not in _read(monorepo, relative)
    ]
    _add(
        checks,
        "responsive_baseline:viewbox_everywhere",
        not missing_viewbox,
        "intrinsic scaling" if not missing_viewbox else ",".join(missing_viewbox),
        "responsive_baseline",
    )
    custom_css = _read(monorepo, DOCS_CUSTOM_CSS)
    _add(
        checks,
        "responsive_baseline:docs_logo_scales",
        "width: auto" in custom_css and ".VPNavBarTitle .logo" in custom_css,
        "logo height constrained, width auto",
        "responsive_baseline",
    )
    _add(
        checks,
        "responsive_baseline:report_mark_flex_safe",
        "flex: none" in engine_styles,
        "mark does not collapse in flex row",
        "responsive_baseline",
    )
    _add(
        checks,
        "responsive_baseline:final_validation_deferred",
        "no_browser_or_pixel_visual_validation" in (policy.get("limitations") or []),
        "pixel validation deferred",
        "responsive_baseline",
    )

    # --- 25. report IA boundary ---------------------------------------------
    from verification.report_navigation_ia.checks import render_assessment_html, render_eir_html
    from verification.report_navigation_ia.contract import (
        ASSESSMENT_SECTION_ORDER,
        EIR_SECTION_ORDER,
    )

    assessment_html = render_assessment_html()
    eir_html = render_eir_html(monorepo)
    assessment_ids = [
        match
        for match in re.findall(r'id="([^"]+)"', assessment_html)
        if match in ASSESSMENT_SECTION_ORDER
    ]
    _add(
        checks,
        "ia_boundary:assessment_section_order_unchanged",
        assessment_ids == [s for s in ASSESSMENT_SECTION_ORDER if s in assessment_ids],
        f"sections={len(assessment_ids)}",
        "ia_boundary",
    )
    eir_ids = [
        match
        for match in re.findall(r'id="(section-[^"]+)"', eir_html)
        if match in EIR_SECTION_ORDER
    ]
    _add(
        checks,
        "ia_boundary:eir_section_order_unchanged",
        eir_ids == [s for s in EIR_SECTION_ORDER if s in eir_ids],
        f"sections={len(eir_ids)}",
        "ia_boundary",
    )
    _add(
        checks,
        "ia_boundary:single_h1_per_report",
        assessment_html.count("<h1") == 1 and eir_html.count("<h1") == 1,
        "one h1 each",
        "ia_boundary",
    )
    toc_links = re.findall(r'<a href="#([^"]+)"', assessment_html)
    dead_toc = [anchor for anchor in toc_links if f'id="{anchor}"' not in assessment_html]
    _add(
        checks,
        "ia_boundary:assessment_links_resolve",
        not dead_toc,
        "resolved" if not dead_toc else ",".join(sorted(set(dead_toc))),
        "ia_boundary",
    )
    _add(
        checks,
        "ia_boundary:mark_is_not_a_heading",
        "<h" not in "".join(re.findall(r'<p class="brand-lockup">.*?</p>', assessment_html)),
        "identity block adds no heading",
        "ia_boundary",
    )
    _add(
        checks,
        "ia_boundary:policy_forbids_ia_change",
        policy.get("report_ia_change_allowed") is False,
        "declared",
        "ia_boundary",
    )

    # --- 26. visualization boundary -----------------------------------------
    viz_contract = _read_json(monorepo, "design-system/contracts/visualization.json")
    _add(
        checks,
        "visualization_boundary:contract_version_unchanged",
        viz_contract.get("schema_version") == "1.0.0",
        str(viz_contract.get("schema_version")),
        "visualization_boundary",
    )
    _add(
        checks,
        "visualization_boundary:risk_tokens_unchanged",
        (tokens.get("risk_colors") or {}).get("critical") == "#a04b17"
        and (tokens.get("risk_colors") or {}).get("low") == "#16756a",
        "risk palette intact",
        "visualization_boundary",
    )
    _add(
        checks,
        "visualization_boundary:no_custom_severity_icon",
        all(
            (role.get("custom_symbol") is not True)
            for role in (icons.get("semantic_roles") or {}).values()
        ),
        "severity markers unchanged",
        "visualization_boundary",
    )

    # --- 27. deployment boundary --------------------------------------------
    _add(
        checks,
        "deployment_boundary:14_12_complete",
        policy.get("documentation_deployment_complete") is True
        and (monorepo / "verification/documentation_deployment").exists(),
        "14.12 owns deployment",
        "deployment_boundary",
    )
    _add(
        checks,
        "deployment_boundary:asset_paths_static_relative",
        all(ref.startswith("/") for ref in docs_asset_refs),
        "site-root relative asset paths",
        "deployment_boundary",
    )
    forbidden_present = [
        relative for relative in FORBIDDEN_15_7_PATHS if (monorepo / relative).exists()
    ]
    _add(
        checks,
        "deployment_boundary:slice_slice_15_7_absent",
        not forbidden_present,
        "absent" if not forbidden_present else ",".join(forbidden_present),
        "deployment_boundary",
    )

    # --- 28. determinism ----------------------------------------------------
    generator_check = subprocess.run(  # noqa: S603 - fixed local command
        [sys.executable, GENERATOR, "--check"],
        cwd=monorepo,
        capture_output=True,
        text=True,
        check=False,
    )
    _add(
        checks,
        "determinism:generator_reproduces_assets",
        generator_check.returncode == 0,
        "no drift" if generator_check.returncode == 0 else "drift detected",
        "determinism",
    )
    _add(
        checks,
        "determinism:assessment_render_stable",
        render_assessment_html() == assessment_html,
        "stable",
        "determinism",
    )
    _add(
        checks,
        "determinism:eir_render_stable",
        render_eir_html(monorepo) == eir_html,
        "stable",
        "determinism",
    )
    generator_source = _read(monorepo, GENERATOR)
    _add(
        checks,
        "determinism:generators_offline",
        "requests" not in generator_source
        and "urllib" not in generator_source
        and "datetime" not in generator_source
        and "datetime" not in raster_generator,
        "no network or clock dependency",
        "determinism",
    )

    # --- 29. negative scenarios ---------------------------------------------
    scenarios: tuple[tuple[str, str, bool], ...] = (
        ("A", "single_master_authority", sorted(masters) == ["codestrata-mark", "codestrata-wordmark"]),
        ("B", "amber_not_active", not active_legacy and not legacy_rgb_present),
        ("C", "aimf_not_active", not aimf_assets),
        ("D", "cursor_not_active", not cursor_assets),
        (
            "E",
            "marketplace_not_master",
            next(
                (
                    e.get("authority")
                    for e in contract.get("assets") or []
                    if e.get("id") == "marketplace-icon"
                ),
                None,
            )
            == "approved_derivative",
        ),
        (
            "F",
            "vscode_icon_not_master",
            next(
                (
                    e.get("authority")
                    for e in contract.get("assets") or []
                    if e.get("id") == "vscode-activity-icon"
                ),
                None,
            )
            == "consumer_copy",
        ),
        (
            "G",
            "website_docs_marks_agree",
            _sha(_bytes(monorepo, DOCS_MARK)) == _sha(_bytes(monorepo, MASTER_MARK)),
        ),
        ("H", "reports_share_geometry", embedded_markup == _read(monorepo, ENGINE_REPORT_MARK).strip()),
        ("I", "favicon_current_identity", not (_svg_hex_fills(favicon) & legacy_lower)),
        (
            "J",
            "no_svg_script",
            all("<script" not in _read(monorepo, r).lower() for r in ACTIVE_SVG_ASSETS),
        ),
        (
            "K",
            "no_svg_external_url",
            all(
                "http" not in _payload_without_namespace(_read(monorepo, r))
                for r in ACTIVE_SVG_ASSETS
            ),
        ),
        (
            "L",
            "no_svg_foreign_object",
            all("<foreignobject" not in _read(monorepo, r).lower() for r in ACTIVE_SVG_ASSETS),
        ),
        (
            "M",
            "no_local_path_in_asset",
            all(
                "/Users/" not in _read(monorepo, r) and "/home/" not in _read(monorepo, r)
                for r in ACTIVE_SVG_ASSETS
            ),
        ),
        (
            "N",
            "raster_identity_metadata_absent",
            all(
                not [t for t in _png_chunks(_bytes(monorepo, r)) if t not in {"IHDR", "IDAT", "IEND"}]
                for r in ACTIVE_RASTER_ASSETS
            ),
        ),
        ("O", "duplicates_authorized", not unauthorized),
        (
            "P",
            "generic_action_has_no_brand_icon",
            (icons.get("vscode") or {}).get("custom_icon_for_generic_action_allowed") is False,
        ),
        (
            "Q",
            "icon_meaning_not_color_only",
            (icons.get("principles") or {}).get("meaning", "").startswith("never colour alone"),
        ),
        (
            "R",
            "mark_visible_on_dark",
            _contrast(colors.get("night_ink", "#ffffff"), night) >= 3.0,
        ),
        ("S", "mark_visible_on_light", not weak_on_light),
        (
            "T",
            "export_asset_references_intact",
            "media/codestrata-icon.png" in export_manifest and not dead_refs,
        ),
        (
            "U",
            "marketplace_gallery_untouched",
            (contract.get("screenshot_assets") or {}).get("redesign_allowed_in_14_10") is False,
        ),
        ("V", "report_ia_unchanged", not dead_toc and assessment_html.count("<h1") == 1),
        (
            "W",
            "visualization_semantics_unchanged",
            viz_contract.get("schema_version") == "1.0.0",
        ),
        ("X", "slice_slice_15_7_absent", not forbidden_present),
        ("Y", "verifier_deterministic", generator_check.returncode == 0),
        (
            "Z",
            "verification_free_of_identity_data",
            "/Users/" not in policy_text and "/Users/" not in _read(monorepo, ASSET_CONTRACT),
        ),
    )
    for letter, name, ok in scenarios:
        _add(checks, f"negative:{letter}_{name}", ok, "held" if ok else "violated", "negative")

    for check in checks:
        if check.ok:
            continue
        defects.append(
            Defect(
                classification=_classify(check.category),
                summary=f"{check.name}: {check.detail}",
            )
        )

    return checks, defects, sizes


def _classify(category: str) -> str:
    mapping = {
        "brand_asset_policy": "authority defect",
        "inventory": "authority defect",
        "authority": "authority defect",
        "master_mark": "master geometry defect",
        "wordmark": "master geometry defect",
        "variants": "variant defect",
        "svg_safety": "SVG safety defect",
        "raster_metadata": "raster metadata defect",
        "duplicates": "duplicate asset defect",
        "legacy_assets": "legacy identity defect",
        "aimf": "legacy identity defect",
        "cursor": "legacy identity defect",
        "website_consumer": "consumer mapping defect",
        "documentation_consumer": "consumer mapping defect",
        "assessment_consumer": "consumer mapping defect",
        "eir_consumer": "consumer mapping defect",
        "vscode_consumer": "consumer mapping defect",
        "marketplace_consumer": "consumer mapping defect",
        "favicon": "favicon defect",
        "icon_language": "icon language defect",
        "export_boundary": "export boundary defect",
        "asset_sizes": "harness defect",
        "accessibility_baseline": "accessibility baseline defect",
        "responsive_baseline": "accessibility baseline defect",
        "ia_boundary": "consumer mapping defect",
        "visualization_boundary": "consumer mapping defect",
        "deployment_boundary": "export boundary defect",
        "determinism": "harness defect",
        "negative": "harness defect",
    }
    return mapping.get(category, "harness defect")
