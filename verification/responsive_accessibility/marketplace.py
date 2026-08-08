"""Marketplace visual asset checks."""

from __future__ import annotations

import re

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "marketplace"
_MD_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def check_marketplace(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    images = _MD_IMAGE.findall(inv.marketplace_readme)
    screenshots = [
        (alt, url)
        for alt, url in images
        if alt.strip() and "screenshot" in url.lower()
    ]
    add(
        "marketplace:readme_screenshot_alts",
        len(screenshots) >= 5,
        f"{len(screenshots)}",
    )

    generator = inv.marketplace_generator
    add(
        "marketplace:generator_tokens",
        "catalog.json" in generator or "TOKEN_CATALOG" in generator or "BRAND" in generator,
        "design_system",
    )

    icon_size = inv.marketplace_images.get("codestrata-icon.png")
    if icon_size:
        add(
            "marketplace:icon_128",
            icon_size == (128, 128),
            f"{icon_size[0]}x{icon_size[1]}",
        )
    else:
        add("marketplace:icon_absent", True, "not_present")

    screenshot_sizes = [
        size
        for name, size in inv.marketplace_images.items()
        if name.startswith("screenshot-")
    ]
    add(
        "marketplace:screenshots_1280x720",
        all(size == (1280, 720) for size in screenshot_sizes) if screenshot_sizes else True,
        f"{len(screenshot_sizes)}",
    )

    if inv.marketplace_manifest:
        captions = [
            item.get("caption", "")
            for item in inv.marketplace_manifest.get("screenshots", [])
            if isinstance(item, dict)
        ]
        add(
            "marketplace:manifest_captions",
            bool(captions) and all(c.strip() for c in captions),
            f"{len(captions)}",
        )
    else:
        add("marketplace:manifest_absent", True, "not_loaded")

    bad_alts = [
        alt
        for alt, url in images
        if alt.strip() == url.rsplit("/", 1)[-1]
    ]
    add(
        "marketplace:alts_not_filenames",
        not bad_alts,
        "descriptive",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("marketplace", "marketplace visual asset contract not met"))
    return checks, defects
