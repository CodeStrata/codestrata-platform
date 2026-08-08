"""Image alt text checks."""

from __future__ import annotations

import re

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "image_alt"
_MD_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
_IMG_TAG = re.compile(r"<img\b[^>]*>", re.IGNORECASE)


def check_images(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    for surface, html in (("assessment", inv.assessment_html), ("eir", inv.eir_html)):
        add(
            f"image_alt:{surface}_mark_hidden",
            'aria-hidden="true"' in html and "cs-mark" in html,
            "decorative",
        )
        imgs = _IMG_TAG.findall(html)
        if imgs:
            alts_ok = all('alt="' in tag.lower() and 'alt=""' not in tag.lower() for tag in imgs)
            add(f"image_alt:{surface}_img_alts", alts_ok, f"{len(imgs)}")
        else:
            add(f"image_alt:{surface}_no_raster", True, "svg_only")

    md_images: list[tuple[str, str]] = []
    for text in inv.docs_markdown.values():
        md_images.extend(_MD_IMAGE.findall(text))
    if md_images:
        bad = [
            alt
            for alt, url in md_images
            if not alt.strip() or alt.strip() == url.rsplit("/", 1)[-1]
        ]
        add(
            "image_alt:docs_markdown",
            not bad,
            f"{len(md_images)}_images",
        )
    else:
        add("image_alt:docs_markdown", True, "no_content_images")

    readme_images = _MD_IMAGE.findall(inv.marketplace_readme)
    good = [
        alt
        for alt, _url in readme_images
        if alt.strip() and "screenshot-" not in alt.lower()
    ]
    add(
        "image_alt:marketplace_readme",
        len(good) >= 5,
        f"{len(good)}",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("image_alt", "image alternative text requirements not met"))
    return checks, defects
