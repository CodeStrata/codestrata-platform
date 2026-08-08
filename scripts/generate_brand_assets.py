#!/usr/bin/env python3
"""Deterministic CodeStrata brand asset generator (Slice 14.10).

Emits the authoritative master brand assets under ``design-system/assets/brand``
and the surface-specific derivative copies that independently exported
repositories require (documentation site, Assessment report package, VS Code
extension media).

Geometry lineage: the strata bar system and the outlined wordmark were authored
in the archived ``governance/assets/svg`` package. That archive is amber-era and
is not the colour authority; colours here come from the Design System token
catalog only.

No network. No timestamps. No user paths. No editor metadata.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOKEN_CATALOG = REPO / "design-system" / "tokens" / "catalog.json"
GEOMETRY_ARCHIVE = REPO / "governance" / "assets" / "svg"
LOCKUP_GEOMETRY = GEOMETRY_ARCHIVE / "lockup-horizontal-on-light.svg"
WORDMARK_GEOMETRY = GEOMETRY_ARCHIVE / "wordmark-on-light.svg"

BRAND_DIR = REPO / "design-system" / "assets" / "brand"
DOCS_PUBLIC = REPO / "docs" / "public"
ENGINE_REPORT_ASSETS = REPO / "engine" / "src" / "codestrata" / "reporting" / "assets"
VSCODE_MEDIA = REPO / "vscode-plugin" / "media"
SWAGGER_BRAND = REPO / "platform" / "api" / "openapi" / "swagger" / "brand"

SVG_OPEN = '<svg xmlns="http://www.w3.org/2000/svg"'

# Master strata geometry (22x22 mark grid), four bars, alternating inset.
MARK_BARS: tuple[tuple[float, float, float, float], ...] = (
    (1.0, 3.0, 20.0, 3.0),
    (4.0, 8.0, 17.0, 3.0),
    (1.0, 13.0, 14.0, 3.0),
    (6.0, 18.0, 12.0, 3.0),
)
MARK_RADIUS = 1.2
MARK_VIEWBOX = 22.0

# Dark-plate tile geometry (32x32 grid) — same bar system, inset for the plate.
TILE_BARS: tuple[tuple[float, float, float, float], ...] = (
    (6.0, 8.0, 20.0, 3.0),
    (9.0, 13.0, 17.0, 3.0),
    (6.0, 18.0, 14.0, 3.0),
    (11.0, 23.0, 12.0, 3.0),
)
TILE_VIEWBOX = 32.0
TILE_RADIUS = 7.0

# Simplified three-bar reduction for 16-24px host-tinted surfaces.
SIMPLIFIED_BARS: tuple[tuple[float, float, float, float], ...] = (
    (3.0, 5.0, 18.0, 3.0),
    (3.0, 10.5, 18.0, 3.0),
    (3.0, 16.0, 18.0, 3.0),
)
SIMPLIFIED_VIEWBOX = 24.0
SIMPLIFIED_RADIUS = 1.0

# Depth grading used by every monochrome derivative (no off-palette colours).
MONO_OPACITY: tuple[float, ...] = (1.0, 0.78, 0.56, 0.38)
SIMPLIFIED_OPACITY: tuple[float, ...] = (1.0, 0.72, 0.44)


def load_colors() -> dict[str, str]:
    catalog = json.loads(TOKEN_CATALOG.read_text(encoding="utf-8"))
    return dict(catalog["colors"])


def _num(value: float) -> str:
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text or "0"


def _bar(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str,
    radius: float = MARK_RADIUS,
    opacity: float | None = None,
) -> str:
    parts = [
        f'x="{_num(x)}"',
        f'y="{_num(y)}"',
        f'width="{_num(w)}"',
        f'height="{_num(h)}"',
        f'rx="{_num(radius)}"',
        f'fill="{fill}"',
    ]
    if opacity is not None and opacity < 1.0:
        parts.append(f'opacity="{_num(opacity)}"')
    return f"  <rect {' '.join(parts)}/>"


def _document(view: float, body: list[str], *, sized: bool = True) -> str:
    box = f'viewBox="0 0 {_num(view)} {_num(view)}"'
    dims = f' width="{_num(view)}" height="{_num(view)}"' if sized else ""
    return "\n".join([f"{SVG_OPEN} {box}{dims}>", *body, "</svg>", ""])


def mark_full_color(colors: dict[str, str]) -> str:
    fills = (colors["muted"], colors["teal_dark"], colors["teal"], colors["rust"])
    body = [_bar(*bar, fill=fill) for bar, fill in zip(MARK_BARS, fills)]
    return _document(MARK_VIEWBOX, body)


def mark_on_dark(colors: dict[str, str]) -> str:
    body = [
        _bar(*bar, fill=colors["night_ink"], opacity=opacity)
        for bar, opacity in zip(MARK_BARS, MONO_OPACITY)
    ]
    return _document(MARK_VIEWBOX, body)


def mark_monochrome() -> str:
    """Host-tinted mark: inherits ink from the surrounding surface."""
    body = [
        _bar(*bar, fill="currentColor", opacity=opacity)
        for bar, opacity in zip(MARK_BARS, MONO_OPACITY)
    ]
    box = f'viewBox="0 0 {_num(MARK_VIEWBOX)} {_num(MARK_VIEWBOX)}"'
    head = f'{SVG_OPEN} {box} class="cs-mark" aria-hidden="true" focusable="false">'
    return "\n".join([head, *body, "</svg>", ""])


def mark_simplified() -> str:
    """Three-bar reduction for 16-24px activity surfaces."""
    body = [
        _bar(*bar, fill="currentColor", radius=SIMPLIFIED_RADIUS, opacity=opacity)
        for bar, opacity in zip(SIMPLIFIED_BARS, SIMPLIFIED_OPACITY)
    ]
    box = f'viewBox="0 0 {_num(SIMPLIFIED_VIEWBOX)} {_num(SIMPLIFIED_VIEWBOX)}"'
    return "\n".join([f'{SVG_OPEN} {box} fill="none" aria-hidden="true">', *body, "</svg>", ""])


def mark_tile_on_dark(colors: dict[str, str]) -> str:
    plate = (
        f'  <rect width="{_num(TILE_VIEWBOX)}" height="{_num(TILE_VIEWBOX)}" '
        f'rx="{_num(TILE_RADIUS)}" fill="{colors["night"]}"/>'
    )
    bars = [
        _bar(*bar, fill=colors["night_ink"], opacity=opacity)
        for bar, opacity in zip(TILE_BARS, MONO_OPACITY)
    ]
    return _document(TILE_VIEWBOX, [plate, *bars])


def read_wordmark_geometry(source_path: Path) -> tuple[str, str, str]:
    """Return (transform, primary path data, accent path data) from the archive."""
    source = source_path.read_text(encoding="utf-8")
    group = re.search(r'<g transform="([^"]+)">(.*?)</g>', source, re.DOTALL)
    if group is None:
        raise SystemExit(f"wordmark geometry group not found in {source_path.name}")
    paths = re.findall(r'<path fill="[^"]*" d="([^"]+)"/>', group.group(2))
    if len(paths) != 2:
        raise SystemExit(f"expected two wordmark paths in {source_path.name}, found {len(paths)}")
    return group.group(1), paths[0], paths[1]


WORDMARK_VIEWBOX = (539.16, 93.12)
LOCKUP_VIEWBOX = (731.26, 150.95)
# Bar geometry as laid out inside the archived horizontal lockup.
LOCKUP_BARS: tuple[tuple[float, float, float, float], ...] = (
    (15.95, 27.86, 119.05, 17.86),
    (33.81, 57.62, 101.19, 17.86),
    (15.95, 87.38, 83.33, 17.86),
    (45.71, 117.14, 71.43, 17.86),
)
LOCKUP_BAR_RADIUS = 7.14


def wordmark(colors: dict[str, str]) -> str:
    transform, primary, accent = read_wordmark_geometry(WORDMARK_GEOMETRY)
    view = f'viewBox="0 0 {_num(WORDMARK_VIEWBOX[0])} {_num(WORDMARK_VIEWBOX[1])}"'
    dims = f' width="{_num(WORDMARK_VIEWBOX[0])}" height="{_num(WORDMARK_VIEWBOX[1])}"'
    return "\n".join(
        [
            f"{SVG_OPEN} {view}{dims}>",
            f'  <g transform="{transform}">',
            f'    <path fill="{colors["ink"]}" d="{primary}"/>',
            f'    <path fill="{colors["teal_dark"]}" d="{accent}"/>',
            "  </g>",
            "</svg>",
            "",
        ]
    )


def lockup(colors: dict[str, str], *, on_dark: bool) -> str:
    transform, primary, accent = read_wordmark_geometry(LOCKUP_GEOMETRY)
    if on_dark:
        bars = [
            _bar(*bar, fill=colors["night_ink"], radius=LOCKUP_BAR_RADIUS, opacity=opacity)
            for bar, opacity in zip(LOCKUP_BARS, MONO_OPACITY)
        ]
        primary_fill = colors["night_ink"]
        accent_fill = colors["night_ink"]
    else:
        fills = (colors["muted"], colors["teal_dark"], colors["teal"], colors["rust"])
        bars = [
            _bar(*bar, fill=fill, radius=LOCKUP_BAR_RADIUS)
            for bar, fill in zip(LOCKUP_BARS, fills)
        ]
        primary_fill = colors["ink"]
        accent_fill = colors["teal_dark"]
    view = f'viewBox="0 0 {_num(LOCKUP_VIEWBOX[0])} {_num(LOCKUP_VIEWBOX[1])}"'
    dims = f' width="{_num(LOCKUP_VIEWBOX[0])}" height="{_num(LOCKUP_VIEWBOX[1])}"'
    return "\n".join(
        [
            f"{SVG_OPEN} {view}{dims}>",
            *bars,
            f'  <g transform="{transform}">',
            f'    <path fill="{primary_fill}" d="{primary}"/>',
            f'    <path fill="{accent_fill}" d="{accent}"/>',
            "  </g>",
            "</svg>",
            "",
        ]
    )


def build_assets(colors: dict[str, str]) -> dict[Path, str]:
    master_mark = mark_full_color(colors)
    master_on_dark = mark_on_dark(colors)
    master_mono = mark_monochrome()
    master_tile = mark_tile_on_dark(colors)
    master_lockup_light = lockup(colors, on_dark=False)
    master_lockup_dark = lockup(colors, on_dark=True)
    activity = mark_simplified()

    return {
        # Master authority (Design System).
        BRAND_DIR / "codestrata-mark.svg": master_mark,
        BRAND_DIR / "codestrata-mark-on-dark.svg": master_on_dark,
        BRAND_DIR / "codestrata-mark-mono.svg": master_mono,
        BRAND_DIR / "codestrata-mark-simplified-mono.svg": activity,
        BRAND_DIR / "codestrata-mark-tile-on-dark.svg": master_tile,
        BRAND_DIR / "codestrata-wordmark.svg": wordmark(colors),
        BRAND_DIR / "codestrata-lockup-horizontal-on-light.svg": master_lockup_light,
        BRAND_DIR / "codestrata-lockup-horizontal-on-dark.svg": master_lockup_dark,
        # Documentation site derivatives (exported repository keeps its own copies).
        DOCS_PUBLIC / "favicon.svg": master_mark,
        DOCS_PUBLIC / "brand" / "icon.svg": master_mark,
        DOCS_PUBLIC / "brand" / "icon-tile-dark.svg": master_tile,
        DOCS_PUBLIC / "brand" / "lockup-horizontal-on-light.svg": master_lockup_light,
        DOCS_PUBLIC / "brand" / "lockup-horizontal-on-dark.svg": master_lockup_dark,
        # Platform API documentation portal derivatives (served as static files).
        SWAGGER_BRAND / "icon.svg": master_mark,
        SWAGGER_BRAND / "lockup-horizontal-on-light.svg": master_lockup_light,
        SWAGGER_BRAND / "lockup-horizontal-on-dark.svg": master_lockup_dark,
        # Assessment report derivative (packaged with the Engine distribution).
        ENGINE_REPORT_ASSETS / "codestrata-mark-mono.svg": master_mono,
        # VS Code activity derivative (theme-tinted, simplified).
        VSCODE_MEDIA / "codestrata-activity.svg": activity,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify on-disk assets match generated output without writing",
    )
    args = parser.parse_args()

    assets = build_assets(load_colors())
    drift: list[str] = []
    for path, content in sorted(assets.items()):
        relative = path.relative_to(REPO).as_posix()
        if args.check:
            current = path.read_text(encoding="utf-8") if path.is_file() else ""
            if current != content:
                drift.append(relative)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {relative}")

    if args.check:
        if drift:
            for relative in drift:
                print(f"drift {relative}")
            return 1
        print(f"checked {len(assets)} brand assets: no drift")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
