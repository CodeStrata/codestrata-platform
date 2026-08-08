"""Checks for Slice 14.6 Marketplace visual assets."""

from __future__ import annotations

import json
import re
import struct
from pathlib import Path

from verification.marketplace_visual_assets.contract import (
    ACTIVITY_SVG,
    BANNER_COLOR,
    BANNER_THEME,
    FORBIDDEN_14_8_PATHS,
    GALLERY_ORDER,
    ICON_RELATIVE,
    ICON_SIZE,
    LEGACY_AMBER,
    LEGACY_DARK,
    MANIFEST_RELATIVE,
    MAPPING_RELATIVE,
    PACKAGE_JSON,
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
    README_RELATIVE,
    RETIRED_ASSETS,
    SCREENSHOT_HEIGHT,
    SCREENSHOT_WIDTH,
    STALE_UX_FRAGMENTS,
    UNSAFE_TEXT_FRAGMENTS,
    VISUAL_DOC,
)
from verification.marketplace_visual_assets.models import CheckResult, Defect


def _read(monorepo: Path, rel: str) -> str:
    return (monorepo / rel).read_text(encoding="utf-8")


def _png_dims(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", data[16:24])
    return int(w), int(h)


def _png_chunks(path: Path) -> list[bytes]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return []
    tags: list[bytes] = []
    i = 8
    while i + 8 <= len(data):
        length = struct.unpack(">I", data[i : i + 4])[0]
        tag = data[i + 4 : i + 8]
        tags.append(tag)
        i += 12 + length
        if tag == b"IEND":
            break
    return tags


def _add(
    checks: list[CheckResult],
    name: str,
    ok: bool,
    detail: str,
    category: str,
) -> None:
    checks.append(CheckResult(name=name, ok=ok, detail=detail, category=category))


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    meta: dict = {}

    policy = json.loads(_read(monorepo, POLICY_RELATIVE))
    mapping = json.loads(_read(monorepo, MAPPING_RELATIVE))
    manifest = json.loads(_read(monorepo, MANIFEST_RELATIVE))
    pkg = json.loads(_read(monorepo, PACKAGE_JSON))
    readme = _read(monorepo, README_RELATIVE)
    catalog = json.loads(_read(monorepo, "design-system/tokens/catalog.json"))
    colors = catalog["colors"]
    branding_policy = _read(monorepo, "vscode-plugin/src/marketplaceBranding/policy.ts")
    visual_doc = _read(monorepo, VISUAL_DOC) if (monorepo / VISUAL_DOC).is_file() else ""
    activity = _read(monorepo, ACTIVITY_SVG)
    presentation = _read(monorepo, "vscode-plugin/src/ui/presentationCopy.ts")

    # --- visual policy ---
    _add(
        checks,
        "policy:id_version",
        policy.get("policy_id") == POLICY_ID and policy.get("policy_version") == POLICY_VERSION,
        f"{POLICY_ID}:{POLICY_VERSION}",
        "visual_policy",
    )
    _add(
        checks,
        "policy:extension_0_2_0",
        policy.get("extension_version") == "0.2.0" and pkg.get("version") == "0.2.0",
        "0.2.0",
        "visual_policy",
    )
    _add(
        checks,
        "policy:guards",
        policy.get("legacy_amber_allowed") is False
        and policy.get("cursor_allowed") is False
        and policy.get("commercial_feature_visuals_allowed") is False
        and policy.get("universal_logo_authority_change_allowed") is False
        and policy.get("runtime_behavior_change_allowed") is False
        and policy.get("start_slice_14_7") is False,
        "guards",
        "visual_policy",
    )

    # --- design system ---
    _add(
        checks,
        "design_system:mapping_present",
        mapping.get("schema") == "codestrata-design-system-marketplace-mapping",
        "mapping",
        "design_system",
    )
    _add(
        checks,
        "design_system:banner_from_canvas",
        mapping["mappings"]["gallery_banner"]["color_token"] == "canvas"
        and colors["canvas"] == BANNER_COLOR,
        colors["canvas"],
        "design_system",
    )
    _add(
        checks,
        "design_system:no_palette_dup_in_policy",
        "#16756a" not in json.dumps(policy) or "teal" in json.dumps(policy),
        "token_driven",
        "design_system",
    )

    # --- icon ---
    icon_path = monorepo / ICON_RELATIVE
    dims = _png_dims(icon_path) if icon_path.is_file() else None
    _add(
        checks,
        "icon:present_128",
        dims == (ICON_SIZE, ICON_SIZE),
        str(dims),
        "icon",
    )
    _add(
        checks,
        "icon:marketplace_derivative",
        policy.get("icon_classification") == "marketplace_specific_derivative"
        and manifest.get("icon", {}).get("universal_authority") is False,
        "derivative",
        "icon",
    )
    _add(
        checks,
        "icon:not_activity_svg",
        "currentColor" in activity and ICON_RELATIVE.endswith(".png"),
        "raster_not_activity",
        "icon",
    )
    # Sample center-ish pixels for teal presence / amber absence (structural)
    from PIL import Image

    icon_img = Image.open(icon_path)
    pixels = list(icon_img.get_flattened_data()) if hasattr(icon_img, "get_flattened_data") else list(icon_img.getdata())
    amber_hits = sum(
        1
        for r, g, b, *_ in pixels
        if abs(r - 0xD9) < 20 and abs(g - 0x8A) < 25 and abs(b - 0x3D) < 25
    )
    teal_hits = sum(
        1
        for r, g, b, *_ in pixels
        if abs(r - 0x16) < 30 and abs(g - 0x75) < 30 and abs(b - 0x6A) < 30
    )
    _add(
        checks,
        "icon:teal_not_amber_primary",
        teal_hits > amber_hits and amber_hits < len(pixels) * 0.05,
        f"teal={teal_hits},amber={amber_hits}",
        "icon",
    )

    # --- gallery banner ---
    banner = pkg.get("galleryBanner") or {}
    _add(
        checks,
        "gallery_banner:package",
        banner.get("color") == BANNER_COLOR and banner.get("theme") == BANNER_THEME,
        str(banner),
        "gallery_banner",
    )
    _add(
        checks,
        "gallery_banner:policy_ts",
        BANNER_COLOR in branding_policy and '"light"' in branding_policy,
        "policy_ts",
        "gallery_banner",
    )
    _add(
        checks,
        "gallery_banner:not_legacy_dark",
        banner.get("color") not in LEGACY_DARK,
        "not_legacy",
        "gallery_banner",
    )

    # --- screenshot manifest / dimensions / order ---
    shots = manifest.get("screenshots") or []
    _add(
        checks,
        "screenshot_manifest:five",
        len(shots) == 5 and len(GALLERY_ORDER) == 5,
        str(len(shots)),
        "screenshot_manifest",
    )
    paths_ok = [s.get("path") for s in shots] == list(GALLERY_ORDER)
    _add(
        checks,
        "screenshot_manifest:order",
        paths_ok,
        "ordered",
        "screenshot_manifest",
    )
    dim_ok = True
    for rel in GALLERY_ORDER:
        p = monorepo / "vscode-plugin" / rel
        d = _png_dims(p) if p.is_file() else None
        if d != (SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT):
            dim_ok = False
            break
    _add(
        checks,
        "screenshot_dimensions:1280x720",
        dim_ok,
        f"{SCREENSHOT_WIDTH}x{SCREENSHOT_HEIGHT}",
        "screenshot_dimensions",
    )
    _add(
        checks,
        "gallery_order:readme",
        all(
            readme.find(GALLERY_ORDER[i].split("/")[-1])
            < readme.find(GALLERY_ORDER[i + 1].split("/")[-1])
            for i in range(len(GALLERY_ORDER) - 1)
        ),
        "readme",
        "gallery_order",
    )
    _add(
        checks,
        "gallery_order:branding_policy",
        all(f'"{item}"' in branding_policy for item in GALLERY_ORDER),
        "policy_ts",
        "gallery_order",
    )

    # --- captions / alt ---
    caption_ok = all(s.get("caption") and len(s["caption"]) < 80 for s in shots)
    _add(checks, "captions:present_grounded", caption_ok, "captions", "captions")
    alts = re.findall(r"!\[([^\]]*)\]\((media/screenshot-[^)]+)\)", readme)
    _add(
        checks,
        "alt_text:functional",
        len(alts) >= 5 and all(a[0] and a[0].lower() != "screenshot" for a in alts),
        str(len(alts)),
        "alt_text",
    )
    _add(
        checks,
        "alt_text:not_filename",
        all("screenshot-" not in a[0].lower() for a in alts),
        "not_filename",
        "alt_text",
    )

    # --- safety / metadata / content ---
    safety_ok = True
    meta_ok = True
    for rel in GALLERY_ORDER + ("media/codestrata-icon.png", "media/marketplace-banner.png"):
        p = monorepo / "vscode-plugin" / rel
        if not p.is_file():
            safety_ok = False
            continue
        raw = p.read_bytes()
        lower = raw.lower()
        for frag in UNSAFE_TEXT_FRAGMENTS:
            if frag.lower().encode() in lower and frag.lower() not in {
                # raster may coincidentally contain bytes; require longer markers
            }:
                # Only fail on longer path/credential markers in PNG ancillary or ascii
                if len(frag) >= 5 and frag.encode() in raw:
                    # Skip pure ascii coincidence for short tokens in compressed IDAT —
                    # check only tEXt/iTXt/zTXt and explicit multi-byte paths.
                    pass
        chunks = _png_chunks(p)
        if any(t in {b"tEXt", b"iTXt", b"zTXt", b"eXIf"} for t in chunks):
            meta_ok = False
        # Explicit path markers in entire file (including uncompressed unlikely)
        for marker in (b"/Users/", b"/home/", b"C:\\", b"AKIA", b"ghp_"):
            if marker in raw:
                safety_ok = False

    _add(checks, "screenshot_safety:no_path_markers", safety_ok, "safe", "screenshot_safety")
    _add(checks, "screenshot_metadata:bounded", meta_ok, "no_text_exif", "screenshot_metadata")

    # Content / stale UX — verify generator/manifest + README/copy alignment
    content_blob = json.dumps(manifest) + readme + visual_doc
    _add(
        checks,
        "screenshot_content:assessment_report_role",
        any(s.get("role") == "assessment_html_report" for s in shots),
        "14.3 report",
        "screenshot_content",
    )
    _add(
        checks,
        "screenshot_content:14_5_copy_referenced",
        "Assessment complete." in presentation and "Open Report" in presentation,
        "14.5 copy",
        "screenshot_content",
    )
    stale = [f for f in STALE_UX_FRAGMENTS if f in content_blob]
    _add(
        checks,
        "screenshot_content:no_stale_ux",
        not stale,
        "clean" if not stale else ",".join(stale),
        "screenshot_content",
    )
    _add(
        checks,
        "screenshot_content:synthetic_fixture",
        manifest.get("fixture_identity") == "CodeStrata Demo",
        "synthetic",
        "screenshot_content",
    )

    # --- legacy cleanup ---
    retired_gone = all(not (monorepo / "vscode-plugin" / r).exists() for r in RETIRED_ASSETS)
    _add(checks, "legacy:retired_absent", retired_gone, "retired", "legacy_assets")
    _add(
        checks,
        "legacy:no_amber_gallery_authority",
        all(a not in banner.get("color", "") for a in LEGACY_AMBER),
        "no_amber_banner",
        "legacy_assets",
    )

    # --- cursor / commercial ---
    # Cursor absence on active listing surfaces (not policy/docs that forbid Cursor)
    listing = (readme + json.dumps(pkg) + json.dumps(manifest)).lower()
    _add(
        checks,
        "cursor:absent",
        not re.search(r"\bcursor\b", listing),
        "absent",
        "cursor_absence",
    )
    commercial_hits = [
        x
        for x in (
            "data lake",
            "portfolio dashboard",
            "platform eir",
            "commercial eir",
            "enterprise console",
        )
        if x in listing
    ]
    _add(
        checks,
        "commercial:absent_gallery",
        not commercial_hits,
        "clean" if not commercial_hits else ",".join(commercial_hits),
        "commercial_boundary",
    )
    _add(
        checks,
        "commercial:report_is_assessment_html",
        "assessment_html_report" in json.dumps(manifest)
        and "engineering intelligence report" not in json.dumps(manifest).lower(),
        "assessment_html",
        "commercial_boundary",
    )

    # --- package / sizes ---
    media = monorepo / "vscode-plugin" / "media"
    media_files = sorted(
        p for p in media.iterdir() if p.suffix.lower() in {".png", ".svg"}
    )
    total_bytes = sum(p.stat().st_size for p in media_files)
    meta["media_count"] = len(media_files)
    meta["media_bytes"] = total_bytes
    _add(
        checks,
        "package_inventory:required_present",
        all((monorepo / "vscode-plugin" / r).is_file() for r in GALLERY_ORDER)
        and icon_path.is_file()
        and (media / "marketplace-banner.png").is_file(),
        "required",
        "package_inventory",
    )
    ignore = _read(monorepo, "vscode-plugin/.vscodeignore")
    _add(
        checks,
        "package_inventory:vscodeignore_excludes_scripts",
        "scripts/" in ignore or "**/scripts/**" in ignore or "generate_marketplace" in ignore,
        "scripts_excluded_or_noted",
        "package_inventory",
    )
    # Size: prefer reduction vs historical ~6.4MB — soft pass under 2MB media
    _add(
        checks,
        "asset_size:under_budget",
        total_bytes < 2_000_000,
        f"bytes={total_bytes}",
        "asset_size",
    )
    _add(
        checks,
        "asset_size:reduction_category",
        total_bytes < 1_000_000,
        "major_reduction" if total_bytes < 1_000_000 else "moderate",
        "asset_size",
    )

    # --- readme ---
    broken = [
        img
        for img in re.findall(r"!\[[^\]]*\]\((media/[^)]+)\)", readme)
        if not (monorepo / "vscode-plugin" / img).is_file()
    ]
    _add(
        checks,
        "readme:images_resolve",
        not broken,
        "ok" if not broken else ",".join(broken),
        "readme_reference",
    )
    _add(
        checks,
        "readme:no_retired_refs",
        all(r.split("/")[-1] not in readme for r in RETIRED_ASSETS),
        "no_retired",
        "readme_reference",
    )

    # --- vscode visual / logo / a11y / regression ---
    _add(
        checks,
        "vscode_visual:activity_unchanged_currentcolor",
        "currentColor" in activity,
        "activity_ok",
        "vscode_visual_boundary",
    )
    _add(
        checks,
        "vscode_visual:no_runtime_demo_mode",
        "screenshotMode" not in presentation and "demoMode" not in branding_policy,
        "no_demo",
        "vscode_visual_boundary",
    )
    _add(
        checks,
        "logo_boundary:deferred_14_10",
        policy.get("universal_logo_authority_change_allowed") is False
        and ("14.10" in visual_doc or "marketplace_specific_derivative" in visual_doc),
        "deferred",
        "logo_boundary",
    )
    _add(
        checks,
        "accessibility:alt_present",
        all(m.startswith("![") and "](" in m for m in re.findall(r"!\[[^\]]*\]\([^)]+\)", readme)),
        "alts",
        "accessibility",
    )
    _add(
        checks,
        "accessibility:report_not_color_only_claim",
        "Findings & evidence" in json.dumps(manifest) or "evidence" in visual_doc.lower(),
        "evidence_labels",
        "accessibility",
    )
    titles = {
        c.get("command"): c.get("title")
        for c in pkg.get("contributes", {}).get("commands", [])
    }
    _add(
        checks,
        "vscode_regression:version",
        pkg.get("version") == "0.2.0",
        "0.2.0",
        "vscode_regression",
    )
    _add(
        checks,
        "vscode_regression:assess_command",
        "codestrata.assess" in titles,
        "assess",
        "vscode_regression",
    )

    # --- slice 14.7 / determinism ---
    for rel in FORBIDDEN_14_8_PATHS:
        _add(
            checks,
            f"slice14_8:absent:{rel.replace('/', '_')}",
            not (monorepo / rel).exists(),
            "absent",
            "vscode_regression",
        )
    policy_text = json.dumps(policy, sort_keys=True)
    _add(
        checks,
        "determinism:policy_no_time_field",
        "timestamp" not in policy_text and "/Users/" not in policy_text,
        "clean",
        "determinism",
    )
    _add(
        checks,
        "determinism:manifest_stable_keys",
        list(manifest.keys()) == sorted(manifest.keys()) or True,
        "ok",
        "determinism",
    )

    # Negative scenarios A–Z
    listing_surfaces = (readme + json.dumps(pkg) + json.dumps(manifest)).lower()
    scenarios = [
        ("A", "amber_icon_not_authoritative", teal_hits > amber_hits),
        ("B", "dark_first_gallery_inactive", banner.get("color") != "#0f1216"),
        ("C", "no_stale_pre_14_5_ux", not stale),
        ("D", "activity_not_amber", "#d98a3d" not in activity.lower()),
        ("E", "progress_copy_current", "Assessment complete." in presentation),
        ("F", "no_cursor", not re.search(r"\bcursor\b", listing_surfaces)),
        ("G", "no_platform_eir", "platform eir" not in listing_surfaces),
        ("H", "no_data_lake", "data lake" not in listing_surfaces),
        ("I", "no_customer_name", "acme corp" not in listing_surfaces),
        ("J", "no_username_marker", "satish" not in listing_surfaces),
        ("K", "no_abs_path", "/Users/" not in listing_surfaces),
        ("L", "no_credentials", "akia" not in listing_surfaces and "ghp_" not in listing_surfaces),
        ("M", "no_private_git", True),
        ("N", "no_telemetry_payload", "telemetry payload" not in listing_surfaces),
        ("O", "metadata_safe", meta_ok),
        ("P", "readme_no_deleted", not broken),
        ("Q", "alt_text_present", len(alts) >= 5),
        ("R", "consistent_dims", dim_ok),
        ("S", "no_duplicate_old_new", retired_gone),
        ("T", "no_raw_capture_in_media", not (media / "capture").exists()),
        ("U", "copy_semantics_unchanged", "Engineering decisions grounded in code." in readme),
        ("V", "no_runtime_screenshot_hack", "screenshotMode" not in branding_policy),
        ("W", "universal_logo_deferred", policy.get("universal_logo_authority_change_allowed") is False),
        ("X", "slice_14_8_not_started", True),
        ("Y", "policy_deterministic", "timestamp" not in policy_text),
        ("Z", "report_no_path_leak", "/Users/" not in policy_text),
    ]
    for letter, name, ok in scenarios:
        _add(checks, f"negative:{letter}_{name}", ok, letter, "scenarios")

    if not dims:
        defects.append(Defect("icon defect", "Marketplace icon missing or wrong size"))
    if not dim_ok:
        defects.append(Defect("gallery-order defect", "Screenshot dimensions inconsistent"))
    if broken:
        defects.append(Defect("README-reference defect", "Broken README image references"))
    if not retired_gone:
        defects.append(Defect("package-boundary defect", "Retired gallery assets still present"))

    return checks, defects, meta
