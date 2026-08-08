"""Detect whether a docs-local Playwright Chromium runtime is available."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class BrowserTooling:
    available: bool
    engine: str
    detail: str


def detect_browser_tooling(monorepo: Path | None = None) -> BrowserTooling:
    root = monorepo or Path.cwd()
    playwright_pkg = root / "docs" / "node_modules" / "playwright"
    if not playwright_pkg.is_dir():
        return BrowserTooling(False, "none", "docs_playwright_package_absent")
    harness = root / "verification" / "responsive_accessibility" / "browser_harness.mjs"
    if not harness.is_file():
        return BrowserTooling(False, "none", "browser_harness_absent")
    try:
        probe = subprocess.run(
            ["node", "-e", "require('./docs/node_modules/playwright')"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except Exception as exc:  # pragma: no cover
        return BrowserTooling(False, "chromium", f"node_probe:{type(exc).__name__}")
    if probe.returncode != 0:
        return BrowserTooling(False, "chromium", "node_playwright_require_failed")
    return BrowserTooling(True, "chromium", "node_playwright_available")


def run_node_harness(monorepo: Path, payload: dict) -> dict:
    import os

    harness = monorepo / "verification" / "responsive_accessibility" / "browser_harness.mjs"
    env = os.environ.copy()
    if not env.get("PLAYWRIGHT_BROWSERS_PATH"):
        default_cache = Path.home() / "Library/Caches/ms-playwright"
        if default_cache.is_dir():
            env["PLAYWRIGHT_BROWSERS_PATH"] = str(default_cache)
    completed = subprocess.run(
        ["node", str(harness)],
        cwd=str(monorepo),
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        env=env,
    )
    if completed.returncode != 0:
        return {
            "available": False,
            "detail": f"harness_exit_{completed.returncode}",
            "pages": [],
            "stderr": (completed.stderr or "")[:200],
        }
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "available": False,
            "detail": "harness_invalid_json",
            "pages": [],
        }
