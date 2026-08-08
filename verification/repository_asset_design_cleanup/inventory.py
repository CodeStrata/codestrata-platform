"""Inventory and classification helpers for Slice 16.4."""

from __future__ import annotations

import hashlib
from pathlib import Path

from verification.repository_asset_design_cleanup.contract import (
    ACTIVE_TOKEN_SURFACES,
    BRAND_MASTER,
    HISTORICAL_ARCHIVE,
    LEGACY_AMBER,
    TOKEN_AUTHORITY,
)


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def count_assets(monorepo: Path) -> dict[str, int]:
    counts = {
        "svg": 0,
        "png": 0,
        "jpg": 0,
        "webp": 0,
        "ico": 0,
        "css_tokens": 0,
        "total_scanned": 0,
    }
    roots = [
        monorepo / "design-system",
        monorepo / "docs" / "public",
        monorepo / "vscode-plugin" / "media",
        monorepo / "insights" / "public",
        monorepo / "governance" / "assets",
        monorepo / "platform" / "api" / "openapi" / "swagger",
    ]
    skip = {".git", ".venv", "node_modules", "dist", ".vitepress"}
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if skip & set(path.parts):
                continue
            suf = path.suffix.lower()
            counts["total_scanned"] += 1
            if suf == ".svg":
                counts["svg"] += 1
            elif suf == ".png":
                counts["png"] += 1
            elif suf in {".jpg", ".jpeg"}:
                counts["jpg"] += 1
            elif suf == ".webp":
                counts["webp"] += 1
            elif suf == ".ico":
                counts["ico"] += 1
            if path.name == "tokens.css":
                counts["css_tokens"] += 1
    return counts


def token_surface_status(monorepo: Path) -> list[dict[str, str]]:
    auth = sha256_file(monorepo / TOKEN_AUTHORITY)
    out: list[dict[str, str]] = []
    for rel in ACTIVE_TOKEN_SURFACES:
        path = monorepo / rel
        h = sha256_file(path)
        if not path.exists():
            cls = "OWNER_REVIEW_REQUIRED"
            note = "missing"
        elif rel == TOKEN_AUTHORITY:
            cls = "AUTHORITATIVE_MASTER"
            note = "authority"
        elif "theme/tokens.css" in rel:
            cls = "ACTIVE_CONSUMER_TOKEN_BRIDGE"
            note = "import_bridge"
        elif h == auth:
            cls = "GENERATED_COPY"
            note = "byte_match_authority"
        else:
            cls = "GENERATED_COPY"
            note = "packaging_mirror_with_aliases"
        out.append({"path": rel, "classification": cls, "note": note})
    return out


def active_css_has_amber(monorepo: Path) -> list[str]:
    hits: list[str] = []
    for rel in ACTIVE_TOKEN_SURFACES:
        path = monorepo / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if LEGACY_AMBER in text:
            hits.append(rel)
    # CLI landing
    landing = monorepo / "engine/src/codestrata/cli/landing.py"
    if landing.is_file() and LEGACY_AMBER in landing.read_text(encoding="utf-8", errors="ignore"):
        hits.append("engine/src/codestrata/cli/landing.py")
    return hits


def svg_safety_issues(monorepo: Path) -> list[str]:
    issues: list[str] = []
    roots = [
        monorepo / BRAND_MASTER,
        monorepo / "docs/public/brand",
        monorepo / "insights/public/brand",
        monorepo / "vscode-plugin/media",
    ]
    bad = ("<script", "onload=", "onclick=", "<foreignobject", "xlink:href=\"http")
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.svg"):
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for token in bad:
                if token in text:
                    issues.append(f"{path.relative_to(monorepo).as_posix()}:{token}")
            if "viewbox" not in text and path.parent.name in {"brand", "media"}:
                # activity icon etc should have viewBox; warn soft
                if "codestrata" in path.name:
                    if "viewbox" not in text:
                        issues.append(f"{path.relative_to(monorepo).as_posix()}:missing_viewbox")
    return issues


def marketplace_screenshots_present(monorepo: Path) -> bool:
    media = monorepo / "vscode-plugin/media"
    required = (
        "screenshot-assessment.png",
        "screenshot-ai-assessment.png",
        "screenshot-initialization.png",
        "screenshot-progress.png",
        "screenshot-report.png",
        "codestrata-icon.png",
    )
    return all((media / name).is_file() for name in required)


def retired_marketplace_absent(monorepo: Path) -> bool:
    media = monorepo / "vscode-plugin/media"
    retired = (
        "screenshot-findings.png",
        "screenshot-findings-light.png",
        "screenshot-activity.png",
        "screenshot-recommendations.png",
    )
    return all(not (media / name).exists() for name in retired)


def historical_archive_file_count(monorepo: Path) -> int:
    root = monorepo / HISTORICAL_ARCHIVE
    if not root.exists():
        return 0
    return sum(1 for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".svg", ".png", ".jpg", ".html", ".md"})
