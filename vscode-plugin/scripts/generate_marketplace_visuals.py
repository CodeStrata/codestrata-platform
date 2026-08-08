#!/usr/bin/env python3
"""Deterministic Marketplace visual asset generator (Slice 14.6).

Reads Design System token catalog. No network. No timestamps in outputs.
Marketplace-specific icon is a derivative until Slice 14.10 owns universal assets.
"""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[2]
TOKEN_CATALOG = REPO / "design-system" / "tokens" / "catalog.json"
MEDIA = REPO / "vscode-plugin" / "media"
POLICY = REPO / "vscode-plugin" / "policies" / "marketplace_visual_assets_policy.json"
GOVERNANCE_DERIV = (
    REPO
    / "governance"
    / "assets"
    / "extension-branding"
    / "codestrata-marketplace-icon-derivative-128.png"
)

# Synthetic fixture identity only — Community Marketplace safe.
FIXTURE_NAME = "CodeStrata Demo"
SYNTHETIC_FINDING = "Missing continuous integration configuration"
SYNTHETIC_RULE = "ci.pipeline.missing"
SYNTHETIC_REC = "Add a minimal CI workflow for pull requests"

CAPTIONS = {
    "screenshot-assessment.png": "Run an assessment from VS Code",
    "screenshot-report.png": "Review evidence-backed findings",
    "screenshot-progress.png": "Track assessment progress",
    "screenshot-initialization.png": "Initialize a repository",
    "screenshot-ai-assessment.png": "Run an optional AI-assisted assessment",
}

ALT_TEXT = {
    "screenshot-assessment.png": (
        "CodeStrata VS Code extension showing findings for a synthetic Demo repository"
    ),
    "screenshot-report.png": (
        "CodeStrata Assessment HTML report with executive summary and evidence-backed findings"
    ),
    "screenshot-progress.png": (
        "CodeStrata assessment progress notification with Assessment complete and Open Report"
    ),
    "screenshot-initialization.png": (
        "CodeStrata Initialize Repository guidance for a synthetic Demo workspace"
    ),
    "screenshot-ai-assessment.png": (
        "CodeStrata optional AI-assisted assessment progress in VS Code"
    ),
}

# Master brand mark geometry (Slice 14.10) — 22-unit grid, four strata bars.
MASTER_MARK_GRID = 22.0
MASTER_MARK_COVERAGE = 0.66
MASTER_MARK_BARS: tuple[tuple[float, float, float, float], ...] = (
    (1.0, 3.0, 20.0, 3.0),
    (4.0, 8.0, 17.0, 3.0),
    (1.0, 13.0, 14.0, 3.0),
    (6.0, 18.0, 12.0, 3.0),
)
MASTER_MARK_FILL_TOKENS = ("muted", "teal_dark", "teal", "rust")

FORBIDDEN_SCAN = (
    "/Users/",
    "/home/",
    "C:\\",
    "cursor",
    "Cursor",
    "@",
    "AKIA",
    "sk-",
    "ghp_",
    "engineering intelligence report",
    "Data Lake",
    "portfolio dashboard",
)


def load_colors() -> dict[str, str]:
    catalog = json.loads(TOKEN_CATALOG.read_text(encoding="utf-8"))
    return dict(catalog["colors"])


def load_radius_px() -> dict[str, int]:
    catalog = json.loads(TOKEN_CATALOG.read_text(encoding="utf-8"))
    radius = catalog.get("radius") or {}

    def _px(key: str, default: int) -> int:
        raw = str(radius.get(key, f"{default}px"))
        return int("".join(ch for ch in raw if ch.isdigit()) or default)

    return {
        "small": _px("button", 4),
        "standard": _px("card", 6),
        "large": _px("large", 8),
    }


def load_status_colors() -> dict[str, str]:
    catalog = json.loads(TOKEN_CATALOG.read_text(encoding="utf-8"))
    return dict(catalog["status_colors"])


def _font(size: int) -> ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _save_png(img: Image.Image, path: Path) -> None:
    """Write PNG without ancillary identity metadata chunks."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Convert via bytes to strip info dict
    clean = img.convert("RGBA") if img.mode != "RGBA" else img
    buf = []

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    w, h = clean.size
    raw = b""
    pixels = clean.tobytes()
    stride = w * 4
    for y in range(h):
        raw += b"\x00" + pixels[y * stride : (y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    buf.append(b"\x89PNG\r\n\x1a\n")
    buf.append(chunk(b"IHDR", ihdr))
    buf.append(chunk(b"IDAT", zlib.compress(raw, 9)))
    buf.append(chunk(b"IEND", b""))
    path.write_bytes(b"".join(buf))


def generate_icon(colors: dict[str, str], size: int = 128) -> Image.Image:
    """Marketplace raster derivative of the master brand mark (Slice 14.10).

    Bar geometry is projected from ``design-system/assets/brand/codestrata-mark.svg``
    so the Marketplace tile and the vector master share one strata system.
    """
    canvas = _hex(colors["canvas"])
    paper = _hex(colors["paper"])

    img = Image.new("RGBA", (size, size), (*canvas, 255))
    draw = ImageDraw.Draw(img)
    pad = size // 16
    draw.rounded_rectangle(
        [pad, pad, size - pad - 1, size - pad - 1],
        radius=size // 5,
        fill=(*paper, 255),
        outline=(*_hex(colors["line"]), 255),
        width=max(1, size // 64),
    )
    scale = size * MASTER_MARK_COVERAGE / MASTER_MARK_GRID
    origin = (size - MASTER_MARK_GRID * scale) / 2.0
    fills = [colors[token] for token in MASTER_MARK_FILL_TOKENS]
    for (x, y, w, h), fill in zip(MASTER_MARK_BARS, fills):
        x0 = round(origin + x * scale)
        y0 = round(origin + y * scale)
        x1 = round(origin + (x + w) * scale)
        y1 = round(origin + (y + h) * scale)
        draw.rounded_rectangle(
            [x0, y0, x1, y1],
            radius=max(1, (y1 - y0) // 2),
            fill=(*_hex(fill), 255),
        )
    return img


def generate_banner(
    colors: dict[str, str], radii: dict[str, int], w: int = 1280, h: int = 640
) -> Image.Image:
    canvas = _hex(colors["canvas"])
    teal = _hex(colors["teal"])
    teal_dark = _hex(colors["teal_dark"])
    ink = _hex(colors["ink"])
    muted = _hex(colors["muted"])
    paper = _hex(colors["paper"])
    r_large = radii["large"]
    r_small = radii["small"]

    img = Image.new("RGBA", (w, h), (*canvas, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, w, 12], fill=(*teal, 255))
    draw.rounded_rectangle(
        [64, 120, w - 64, h - 120],
        radius=r_large,
        fill=(*paper, 255),
        outline=(*_hex(colors["line"]), 255),
        width=2,
    )
    draw.text((96, 180), "CodeStrata", font=_font(56), fill=(*ink, 255))
    draw.text(
        (96, 260),
        "Engineering decisions grounded in code.",
        font=_font(28),
        fill=(*muted, 255),
    )
    draw.rounded_rectangle(
        [96, 340, 280, 390],
        radius=r_small,
        fill=(*teal_dark, 255),
    )
    draw.text((120, 352), "Community", font=_font(22), fill=(255, 255, 255, 255))
    # Decorative strata
    for i, fill in enumerate([teal_dark, teal, muted]):
        y = h - 80 + i * 14
        draw.rectangle([w - 320, y, w - 80 - i * 40, y + 8], fill=(*fill, 255))
    return img


def _frame(
    colors: dict[str, str], radii: dict[str, int], w: int, h: int, title: str
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    canvas = _hex(colors["canvas"])
    paper = _hex(colors["paper"])
    ink = _hex(colors["ink"])
    muted = _hex(colors["muted"])
    teal = _hex(colors["teal"])
    line = _hex(colors["line"])
    r = radii["large"]

    img = Image.new("RGBA", (w, h), (*canvas, 255))
    draw = ImageDraw.Draw(img)
    margin = 36
    draw.rounded_rectangle(
        [margin, margin, w - margin, h - margin],
        radius=r,
        fill=(*paper, 255),
        outline=(*line, 255),
        width=2,
    )
    draw.rectangle([margin, margin, w - margin, margin + 48], fill=(*_hex(colors["teal_soft"]), 255))
    draw.text((margin + 20, margin + 12), "CodeStrata", font=_font(22), fill=(*teal, 255))
    draw.text((margin + 160, margin + 16), title, font=_font(16), fill=(*muted, 255))
    draw.text((margin + 20, h - margin - 28), FIXTURE_NAME, font=_font(14), fill=(*ink, 255))
    return img, draw


def shot_assessment(colors: dict[str, str], radii: dict[str, int], w: int, h: int) -> Image.Image:
    img, draw = _frame(colors, radii, w, h, "VS Code · Findings")
    ink = _hex(colors["ink"])
    muted = _hex(colors["muted"])
    teal = _hex(colors["teal"])
    rust = _hex(colors["rust"])
    r_small = radii["small"]
    x, y = 72, 110
    draw.text((x, y), "Findings", font=_font(28), fill=(*ink, 255))
    draw.text((x, y + 40), "Run Assessment · Community Edition", font=_font(16), fill=(*muted, 255))
    draw.rectangle([x, y + 80, x + 18, y + 98], fill=(*ink, 255))
    draw.text((x + 28, y + 80), "CodeStrata", font=_font(16), fill=(*ink, 255))
    rows = [
        ("High", SYNTHETIC_FINDING, rust),
        ("Medium", "Dependency lockfile drift", _hex(colors["blue"])),
        ("Low", "README lacks contribution guide", teal),
    ]
    yy = y + 120
    for sev, title, color in rows:
        draw.rounded_rectangle([x, yy, x + 70, yy + 24], radius=r_small, fill=(*color, 255))
        draw.text((x + 10, yy + 4), sev, font=_font(12), fill=(255, 255, 255, 255))
        draw.text((x + 86, yy + 4), title, font=_font(16), fill=(*ink, 255))
        draw.text((x + 86, yy + 28), SYNTHETIC_RULE if sev == "High" else "fixture.rule", font=_font(12), fill=(*muted, 255))
        yy += 64
    draw.text((x, yy + 10), "3 findings · synthetic fixture", font=_font(14), fill=(*muted, 255))
    return img


def shot_report(
    colors: dict[str, str], status: dict[str, str], radii: dict[str, int], w: int, h: int
) -> Image.Image:
    img, draw = _frame(colors, radii, w, h, "Assessment report")
    ink = _hex(colors["ink"])
    muted = _hex(colors["muted"])
    teal = _hex(colors["teal"])
    paper_soft = _hex(colors["paper_soft"])
    line = _hex(colors["line"])
    r = radii["standard"]
    x, y = 72, 110
    draw.text((x, y), "Executive summary", font=_font(26), fill=(*ink, 255))
    draw.text(
        (x, y + 40),
        f"{FIXTURE_NAME} — local Engineering Assessment",
        font=_font(16),
        fill=(*muted, 255),
    )
    for i, (label, value, token) in enumerate(
        (
            ("Score", "72", "success"),
            ("Findings", "3", "info"),
            ("Risk", "Medium", "warning"),
        )
    ):
        bx = x + i * 220
        by = y + 90
        draw.rounded_rectangle(
            [bx, by, bx + 200, by + 100],
            radius=r,
            fill=(*paper_soft, 255),
            outline=(*line, 255),
            width=1,
        )
        draw.text((bx + 16, by + 16), label, font=_font(14), fill=(*muted, 255))
        draw.text((bx + 16, by + 44), value, font=_font(28), fill=(*_hex(status[token]), 255))
    draw.text((x, y + 220), "Findings & evidence", font=_font(22), fill=(*ink, 255))
    draw.text((x, y + 260), SYNTHETIC_FINDING, font=_font(16), fill=(*ink, 255))
    draw.text((x, y + 288), f"Evidence · {SYNTHETIC_RULE}", font=_font(14), fill=(*muted, 255))
    draw.text((x, y + 320), SYNTHETIC_REC, font=_font(14), fill=(*teal, 255))
    draw.text((x, y + 380), "Assessment HTML · Design System 1.0", font=_font(12), fill=(*muted, 255))
    return img


def shot_progress(colors: dict[str, str], radii: dict[str, int], w: int, h: int) -> Image.Image:
    img, draw = _frame(colors, radii, w, h, "Assessment progress")
    ink = _hex(colors["ink"])
    muted = _hex(colors["muted"])
    teal_dark = _hex(colors["teal_dark"])
    paper_soft = _hex(colors["paper_soft"])
    line = _hex(colors["line"])
    r = radii["large"]
    r_small = radii["small"]
    cx, cy = 340, 220
    draw.rounded_rectangle(
        [cx, cy, cx + 600, cy + 200],
        radius=r,
        fill=(*paper_soft, 255),
        outline=(*line, 255),
        width=2,
    )
    draw.text((cx + 24, cy + 24), "Running CodeStrata assessment…", font=_font(18), fill=(*muted, 255))
    draw.text((cx + 24, cy + 64), "Assessment complete.", font=_font(24), fill=(*ink, 255))
    draw.rounded_rectangle([cx + 24, cy + 120, cx + 180, cy + 160], radius=r_small, fill=(*teal_dark, 255))
    draw.text((cx + 44, cy + 130), "Open Report", font=_font(16), fill=(255, 255, 255, 255))
    draw.text((cx + 200, cy + 130), "Dismiss", font=_font(16), fill=(*muted, 255))
    return img


def shot_initialization(colors: dict[str, str], radii: dict[str, int], w: int, h: int) -> Image.Image:
    img, draw = _frame(colors, radii, w, h, "Repository initialization")
    ink = _hex(colors["ink"])
    muted = _hex(colors["muted"])
    teal = _hex(colors["teal"])
    x, y = 72, 130
    draw.text((x, y), "Initialize Repository", font=_font(28), fill=(*ink, 255))
    draw.text(
        (x, y + 48),
        "Create local CodeStrata configuration when needed.",
        font=_font(16),
        fill=(*muted, 255),
    )
    draw.text((x, y + 100), f"Workspace: {FIXTURE_NAME}", font=_font(16), fill=(*ink, 255))
    draw.text((x, y + 140), "codestrata.toml · Engine CLI ready", font=_font(16), fill=(*teal, 255))
    draw.text(
        (x, y + 200),
        "Welcome to CodeStrata. CodeStrata CLI is ready.",
        font=_font(16),
        fill=(*ink, 255),
    )
    draw.text(
        (x, y + 236),
        "Initialize this repository before running an assessment when needed.",
        font=_font(14),
        fill=(*muted, 255),
    )
    return img


def shot_ai(colors: dict[str, str], radii: dict[str, int], w: int, h: int) -> Image.Image:
    img, draw = _frame(colors, radii, w, h, "Optional AI assessment")
    ink = _hex(colors["ink"])
    muted = _hex(colors["muted"])
    blue = _hex(colors["blue"])
    paper_soft = _hex(colors["paper_soft"])
    line = _hex(colors["line"])
    r = radii["large"]
    cx, cy = 300, 240
    draw.rounded_rectangle(
        [cx, cy, cx + 680, cy + 160],
        radius=r,
        fill=(*paper_soft, 255),
        outline=(*line, 255),
        width=2,
    )
    draw.text(
        (cx + 24, cy + 40),
        "Running CodeStrata assessment with AI…",
        font=_font(22),
        fill=(*ink, 255),
    )
    draw.text(
        (cx + 24, cy + 90),
        "Optional · Engine-owned providers · Community Edition",
        font=_font(14),
        fill=(*blue, 255),
    )
    draw.text((cx + 24, cy + 120), FIXTURE_NAME, font=_font(14), fill=(*muted, 255))
    return img


def build_manifest(colors: dict[str, str]) -> dict[str, Any]:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    return {
        "schema": "codestrata-marketplace-visual-manifest",
        "schema_version": "1.0.0",
        "design_system_version": "1.0",
        "extension_version": "0.2.0",
        "fixture_identity": FIXTURE_NAME,
        "icon": {
            "path": "media/codestrata-icon.png",
            "classification": "marketplace_specific_derivative",
            "width": 128,
            "height": 128,
            "universal_authority": False,
        },
        "gallery_banner": {
            "color_token": "canvas",
            "color": colors["canvas"],
            "theme": "light",
            "art": "media/marketplace-banner.png",
            "art_width": 1280,
            "art_height": 640,
        },
        "screenshots": [
            {
                "order": 1,
                "path": "media/screenshot-assessment.png",
                "role": "assessment_workflow",
                "caption": CAPTIONS["screenshot-assessment.png"],
                "alt": ALT_TEXT["screenshot-assessment.png"],
                "width": policy["screenshot_width"],
                "height": policy["screenshot_height"],
            },
            {
                "order": 2,
                "path": "media/screenshot-report.png",
                "role": "assessment_html_report",
                "caption": CAPTIONS["screenshot-report.png"],
                "alt": ALT_TEXT["screenshot-report.png"],
                "width": policy["screenshot_width"],
                "height": policy["screenshot_height"],
            },
            {
                "order": 3,
                "path": "media/screenshot-progress.png",
                "role": "assessment_progress",
                "caption": CAPTIONS["screenshot-progress.png"],
                "alt": ALT_TEXT["screenshot-progress.png"],
                "width": policy["screenshot_width"],
                "height": policy["screenshot_height"],
            },
            {
                "order": 4,
                "path": "media/screenshot-initialization.png",
                "role": "repository_initialization",
                "caption": CAPTIONS["screenshot-initialization.png"],
                "alt": ALT_TEXT["screenshot-initialization.png"],
                "width": policy["screenshot_width"],
                "height": policy["screenshot_height"],
            },
            {
                "order": 5,
                "path": "media/screenshot-ai-assessment.png",
                "role": "optional_ai_assessment",
                "caption": CAPTIONS["screenshot-ai-assessment.png"],
                "alt": ALT_TEXT["screenshot-ai-assessment.png"],
                "width": policy["screenshot_width"],
                "height": policy["screenshot_height"],
            },
        ],
        "retired_active_assets": [
            "media/screenshot-findings.png",
            "media/screenshot-findings-light.png",
            "media/screenshot-activity.png",
            "media/screenshot-recommendations.png",
        ],
        "limitations": sorted(policy["limitations"]),
    }


def generate_all() -> dict[str, Any]:
    colors = load_colors()
    radii = load_radius_px()
    status = load_status_colors()
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    w = int(policy["screenshot_width"])
    h = int(policy["screenshot_height"])

    icon = generate_icon(colors, 128)
    _save_png(icon, MEDIA / "codestrata-icon.png")
    _save_png(icon, GOVERNANCE_DERIV)

    banner = generate_banner(colors, radii)
    _save_png(banner, MEDIA / "marketplace-banner.png")

    shots = {
        "screenshot-assessment.png": shot_assessment(colors, radii, w, h),
        "screenshot-report.png": shot_report(colors, status, radii, w, h),
        "screenshot-progress.png": shot_progress(colors, radii, w, h),
        "screenshot-initialization.png": shot_initialization(colors, radii, w, h),
        "screenshot-ai-assessment.png": shot_ai(colors, radii, w, h),
    }
    for name, img in shots.items():
        _save_png(img, MEDIA / name)

    # Remove retired active gallery assets from media/
    for retired in (
        "screenshot-findings.png",
        "screenshot-findings-light.png",
        "screenshot-activity.png",
        "screenshot-recommendations.png",
    ):
        p = MEDIA / retired
        if p.is_file():
            p.unlink()

    manifest = build_manifest(colors)
    manifest_path = (
        REPO / "vscode-plugin" / "policies" / "marketplace_visual_manifest.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    m = generate_all()
    print(json.dumps({"ok": True, "screenshots": len(m["screenshots"])}, sort_keys=True))
