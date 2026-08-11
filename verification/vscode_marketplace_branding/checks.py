"""Focused static checks for Slice 13.12 Marketplace branding."""

from __future__ import annotations

import json
import re
import struct
from pathlib import Path

from verification.vscode_marketplace_branding.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    BRANDING_PACKAGE,
    BRANDING_POLICY_ID,
    BRANDING_POLICY_VERSION,
    DISPLAY_NAME,
    FORBIDDEN_CLAIM_FRAGMENTS,
    GALLERY_COLOR,
    GALLERY_ORDER,
    GALLERY_THEME,
    ICON_RELATIVE,
    INTENDED_VSCODE_VERSION,
    PACKAGE_NAME,
    PRIVATE_URL_FRAGMENTS,
    PUBLISHER,
    VSCODE_CATEGORIES,
)
from verification.vscode_marketplace_branding.inventory import (
    asset_inventory_stable,
    icon_ok,
    marketplace_asset_total_bytes,
    png_dimensions,
    required_assets_present,
)
from verification.vscode_marketplace_branding.models import CheckResult, Defect


def _read(monorepo: Path, relative: str) -> str:
    return (monorepo / relative).read_text(encoding="utf-8")


def _pkg(monorepo: Path) -> dict:
    return json.loads(_read(monorepo, "vscode-plugin/package.json"))


def _png_text_chunks(path: Path) -> list[str]:
    """Extract tEXt/iTXt/zTXt keyword+text as latin1 strings for safety scans."""
    data = path.read_bytes()
    texts: list[str] = []
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return texts
    offset = 8
    while offset + 8 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        ctype = data[offset + 4 : offset + 8]
        start = offset + 8
        end = start + length
        chunk = data[start:end]
        offset = end + 4
        if ctype in {b"tEXt", b"iTXt", b"zTXt"}:
            texts.append(chunk.decode("latin-1", errors="replace"))
        if ctype == b"IEND":
            break
    return texts


def _ascii_strings(data: bytes, min_len: int = 8) -> str:
    parts: list[str] = []
    current: list[int] = []
    for b in data:
        if 32 <= b < 127:
            current.append(b)
        else:
            if len(current) >= min_len:
                parts.append(bytes(current).decode("ascii"))
            current = []
    if len(current) >= min_len:
        parts.append(bytes(current).decode("ascii"))
    return "\n".join(parts)


def _screenshot_unsafe(path: Path) -> list[str]:
    hits: list[str] = []
    data = path.read_bytes()
    blob = "\n".join(_png_text_chunks(path) + [_ascii_strings(data)])
    lower = blob.lower()
    patterns = [
        (r"/users/[a-z0-9._-]+", "local_username_path"),
        (r"/home/[a-z0-9._-]+", "home_path"),
        (r"c:\\users\\", "windows_user_path"),
        (r"file://", "file_uri"),
        (r"akia[0-9a-z]{16}", "aws_key_like"),
        (r"sk-[a-z0-9]{20,}", "openai_key_like"),
        (r"api[_-]?key\s*[:=]", "api_key_assignment"),
        (r"password\s*[:=]", "password_assignment"),
        (r"bearer [a-z0-9._\-]{20,}", "bearer_token"),
    ]
    for pattern, label in patterns:
        if re.search(pattern, lower):
            hits.append(label)
    if re.search(r"\bcursor\b", lower) and "cli-cursor" not in lower:
        hits.append("cursor_word")
    return hits


def check_all(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    policy = _read(monorepo, f"{BRANDING_PACKAGE}/policy.ts")
    claims = _read(monorepo, f"{BRANDING_PACKAGE}/claims.ts")
    docs = _read(monorepo, "vscode-plugin/docs/marketplace-branding.md")
    readme = _read(monorepo, "vscode-plugin/README.md")
    marketplace_md = _read(monorepo, "vscode-plugin/MARKETPLACE.md")
    vscodeignore = _read(monorepo, "vscode-plugin/.vscodeignore")
    pkg = _pkg(monorepo)
    ext = _read(monorepo, "vscode-plugin/src/extension.ts")
    ds_tokens = _read(monorepo, "design-system/tokens/tokens.css")
    gallery_banner = pkg.get("galleryBanner") or {}

    missing = required_assets_present(monorepo)
    inventory = asset_inventory_stable(monorepo)
    total_asset_bytes = marketplace_asset_total_bytes(monorepo)

    marketplace_surfaces = "\n".join(
        [
            str(pkg.get("displayName", "")),
            str(pkg.get("description", "")),
            " ".join(str(k) for k in pkg.get("keywords", [])),
            # Hero only (before first H2) — listing body is owned by Slice 13.13.
            readme.split("\n## ", 1)[0],
        ]
    ).lower()

    claim_hits = [
        frag for frag in FORBIDDEN_CLAIM_FRAGMENTS if frag in marketplace_surfaces
    ]

    private_hits = [
        frag
        for frag in PRIVATE_URL_FRAGMENTS
        if frag in str(pkg.get("repository", {})).lower()
        or frag in str(pkg.get("homepage", "")).lower()
        or frag in str(pkg.get("bugs", {})).lower()
    ]

    categories = list(pkg.get("categories") or [])
    categories_ok = bool(categories) and all(c in VSCODE_CATEGORIES for c in categories)

    # Cursor absence in Marketplace packaging surfaces (not historical docs)
    cursor_package_surfaces = "\n".join(
        [
            json.dumps(pkg, sort_keys=True).lower(),
            readme.lower(),
            marketplace_md.lower(),
            docs.lower(),
        ]
    )
    # Allow historical "Cursor" mentions only outside active Marketplace short-form —
    # README/MARKETPLACE/docs branding must not promote Cursor product.
    cursor_active_hits = []
    for label, text in (
        ("package.json", json.dumps(pkg, sort_keys=True).lower()),
        ("readme_header", readme.split("\n## ", 1)[0].lower()),
        ("marketplace_md_branding", marketplace_md.lower()),
        ("branding_docs", docs.lower()),
    ):
        if "cursor" in text and "historical" not in text:
            # MARKETPLACE.md may mention Cursor removal historically — allow if "former"/"removed"
            if label == "marketplace_md_branding" and (
                "former" in text or "removed" in text or "slice 12" in text
            ):
                continue
            if re.search(r"\bcursor\b", text):
                cursor_active_hits.append(label)

    screenshot_hits: dict[str, list[str]] = {}
    for rel in GALLERY_ORDER:
        path = monorepo / "vscode-plugin" / rel
        if path.is_file():
            unsafe = _screenshot_unsafe(path)
            if unsafe:
                screenshot_hits[rel] = unsafe

    # README image paths
    readme_images = re.findall(r"!\[[^\]]*\]\((media/[^)]+)\)", readme)
    broken_readme_images = [
        img
        for img in readme_images
        if not (monorepo / "vscode-plugin" / img).is_file()
    ]

    # package dry inventory expectation: icon + screenshots referenced
    ignore_lines = {
        line.strip()
        for line in vscodeignore.splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    ignore_ok = "src/**" in ignore_lines and "out/test/**" in ignore_lines
    # Ensure verification reports are not under vscode-plugin package root
    packaged_reports = (monorepo / "vscode-plugin" / "reports").exists()

    # Soft-gate: 13.14 clean install not started
    slice_1314_absent = not (
        monorepo / "verification" / "vscode_epic14_product_experience"
    ).exists() and "startEpic14ProductExperience" not in ext

    policy_gallery = all(f'"{item}"' in policy for item in GALLERY_ORDER)

    checks.extend(
        [
            CheckResult(
                "policy:id_version",
                BRANDING_POLICY_ID in policy and BRANDING_POLICY_VERSION in policy,
                f"{BRANDING_POLICY_ID}:{BRANDING_POLICY_VERSION}",
                "branding_policy",
            ),
            CheckResult(
                "policy:website_reference",
                'visual_reference: "current_codestrata_website"' in policy
                and "codestrata.ai" in docs,
                "website visual reference",
                "website_reference",
            ),
            CheckResult(
                "policy:cursor_forbidden",
                "cursor_branding_allowed: false" in policy,
                "cursor branding forbidden",
                "branding_policy",
            ),
            CheckResult(
                "naming:displayName",
                pkg.get("displayName") == DISPLAY_NAME
                and DISPLAY_NAME in policy,
                DISPLAY_NAME,
                "product_naming",
            ),
            CheckResult(
                "naming:publisher_package",
                pkg.get("publisher") == PUBLISHER
                and pkg.get("name") == PACKAGE_NAME,
                f"{PUBLISHER}/{PACKAGE_NAME}",
                "product_naming",
            ),
            CheckResult(
                "metadata:version",
                pkg.get("version") == INTENDED_VSCODE_VERSION,
                str(pkg.get("version")),
                "metadata",
            ),
            CheckResult(
                "metadata:icon_field",
                pkg.get("icon") == ICON_RELATIVE,
                str(pkg.get("icon")),
                "metadata",
            ),
            CheckResult(
                "metadata:galleryBanner",
                gallery_banner.get("color") == GALLERY_COLOR
                and gallery_banner.get("theme") == GALLERY_THEME,
                f"{gallery_banner}",
                "gallery_banner",
            ),
            CheckResult(
                "metadata:categories",
                categories_ok and "Other" in categories,
                str(categories),
                "metadata",
            ),
            CheckResult(
                "metadata:keywords_bounded",
                isinstance(pkg.get("keywords"), list)
                and 5 <= len(pkg["keywords"]) <= 12
                and "cursor" not in " ".join(pkg["keywords"]).lower(),
                str(len(pkg.get("keywords") or [])),
                "metadata",
            ),
            CheckResult(
                "metadata:links_public",
                "github.com/CodeStrata/codestrata-vscode"
                not in json.dumps(pkg)
                and "docs.codestrata.ai/extensions/vscode"
                in str(pkg.get("homepage", ""))
                and not private_hits,
                "public docs/homepage links; private GitHub source omitted",
                "link_inventory",
            ),
            CheckResult(
                "icon:present_128",
                icon_ok(monorepo) and not missing,
                "128x128 icon" if icon_ok(monorepo) else f"missing={missing}",
                "icon",
            ),
            CheckResult(
                "icon:governance_sync",
                (
                    monorepo
                    / "governance/assets/extension-branding/codestrata-marketplace-icon-derivative-128.png"
                ).read_bytes()
                == (monorepo / "vscode-plugin" / ICON_RELATIVE).read_bytes(),
                "matches marketplace derivative 128",
                "icon",
            ),
            CheckResult(
                "screenshots:present",
                all(
                    (monorepo / "vscode-plugin" / rel).is_file()
                    for rel in GALLERY_ORDER
                ),
                f"gallery={len(GALLERY_ORDER)}",
                "screenshot",
            ),
            CheckResult(
                "screenshots:dimensions",
                all(
                    (dims := png_dimensions(monorepo / "vscode-plugin" / rel))
                    and dims[0] == 1280
                    and dims[1] in {720, 853}
                    for rel in GALLERY_ORDER
                ),
                "1280x720/853",
                "screenshot",
            ),
            CheckResult(
                "screenshots:safe",
                not screenshot_hits,
                "safe" if not screenshot_hits else str(sorted(screenshot_hits)),
                "asset_safety",
            ),
            CheckResult(
                "gallery_order:policy",
                policy_gallery
                and GALLERY_ORDER[0].endswith("screenshot-assessment.png")
                and GALLERY_ORDER[1].endswith("screenshot-report.png"),
                "assessment then report first",
                "gallery_order",
            ),
            CheckResult(
                "gallery_order:readme",
                readme.find("screenshot-assessment.png")
                < readme.find("screenshot-report.png")
                < readme.find("screenshot-progress.png"),
                "readme order",
                "gallery_order",
            ),
            CheckResult(
                "claims:clean",
                not claim_hits and "FORBIDDEN_MARKETPLACE_CLAIM_PATTERNS" in claims,
                "clean" if not claim_hits else str(claim_hits),
                "claim_review",
            ),
            CheckResult(
                "cursor:absent_active",
                not cursor_active_hits,
                "absent" if not cursor_active_hits else str(cursor_active_hits),
                "cursor_absence",
            ),
            CheckResult(
                "accessibility:alt_text",
                all(
                    m.startswith("![") and "](" in m
                    for m in re.findall(r"!\[[^\]]*\]\([^)]+\)", readme)
                )
                and "![CodeStrata" in readme,
                "readme alts present",
                "accessibility",
            ),
            CheckResult(
                "website:tokens",
                "#f4f6f3" in ds_tokens
                and "#16756a" in ds_tokens
                and GALLERY_COLOR in policy,
                "design system canvas/teal",
                "website_reference",
            ),
            CheckResult(
                "package:vscodeignore",
                ignore_ok and not packaged_reports,
                "src/tests excluded; no plugin reports/",
                "package_inventory",
            ),
            CheckResult(
                "package:required_in_media",
                len(inventory) >= 8 and total_asset_bytes > 0,
                f"assets={len(inventory)} bytes={total_asset_bytes}",
                "package_inventory",
            ),
            CheckResult(
                "readme:images_resolve",
                not broken_readme_images,
                "ok" if not broken_readme_images else str(broken_readme_images),
                "package_inventory",
            ),
            CheckResult(
                "docs:present",
                (monorepo / "vscode-plugin/docs/marketplace-branding.md").is_file()
                and "marketplace-documentation.md" in docs
                and "0.2.0" in docs,
                "branding docs",
                "deferred_marketplace_documentation",
            ),
            CheckResult(
                "epic_14:not_started",
                slice_1314_absent,
                "Epic 14 deferred",
                "deferred_marketplace_documentation",
            ),
            CheckResult(
                "vscode:version",
                pkg.get("version") == INTENDED_VSCODE_VERSION,
                INTENDED_VSCODE_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "schema:assessment_1_2",
                ASSESSMENT_SCHEMA_VERSION == "1.2",
                ASSESSMENT_SCHEMA_VERSION,
                "vscode_regression",
            ),
            CheckResult(
                "prior:compat_1_0",
                'CLI_COMPATIBILITY_POLICY_VERSION = "1.0"'
                in _read(monorepo, "vscode-plugin/src/cliCompatibility/policy.ts"),
                "13.11 policy 1.0",
                "vscode_regression",
            ),
            CheckResult(
                "package:test_wired",
                "marketplaceBranding.test.js"
                in _read(monorepo, "vscode-plugin/package.json"),
                "unit test wired",
                "vscode_regression",
            ),
            CheckResult(
                "commands:ids_stable",
                all(
                    cid in json.dumps(pkg)
                    for cid in (
                        "codestrata.assess",
                        "codestrata.assessWithAi",
                        "codestrata.init",
                        "codestrata.openHtmlReport",
                        "codestrata.checkEnvironment",
                    )
                ),
                "command IDs unchanged",
                "vscode_regression",
            ),
            CheckResult(
                "commands:titles_branded",
                '"title": "Run Assessment"' in json.dumps(pkg)
                and '"title": "Initialize Repository"' in json.dumps(pkg)
                and '"title": "Open HTML Report"' in json.dumps(pkg)
                and '"title": "CodeStrata Doctor"' in json.dumps(pkg),
                "human titles aligned",
                "product_naming",
            ),
            CheckResult(
                "determinism:inventory",
                asset_inventory_stable(monorepo) == inventory,
                "stable inventory",
                "vscode_regression",
            ),
        ]
    )

    if claim_hits:
        defects.append(
            Defect(
                "claims defect",
                "marketplace_copy",
                "no forbidden claims",
                ",".join(claim_hits),
            )
        )
    if cursor_active_hits:
        defects.append(
            Defect(
                "Cursor-removal regression",
                "marketplace_surfaces",
                "no Cursor branding",
                ",".join(cursor_active_hits),
            )
        )
    if screenshot_hits:
        defects.append(
            Defect(
                "screenshot defect",
                "media",
                "safe synthetic screenshots",
                str(sorted(screenshot_hits)),
            )
        )
    if missing:
        defects.append(
            Defect("icon defect", "media", "required assets present", str(missing))
        )

    return checks, defects
