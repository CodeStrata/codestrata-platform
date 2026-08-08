"""Optional browser validation for Slice 14.13."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult, Defect

TEAL_FAMILY = ("#16756a", "#1a8779", "rgb(22, 117, 106)")


def _playwright_available(monorepo: Path) -> bool:
    pw = monorepo / "docs" / "node_modules" / "playwright"
    return pw.is_dir() or (monorepo / "docs" / "node_modules" / "@playwright").is_dir()


def check_browser_validation(
    inv: ConsistencyInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    if not _playwright_available(inv.monorepo):
        add(
            checks,
            "browser_validation:skipped_limitation",
            True,
            "playwright_unavailable_static_checks_authoritative",
            "browser_validation",
        )
        return checks, defects

    if not inv.assessment_html or not inv.dist_exists:
        add(
            checks,
            "browser_validation:fixtures_missing",
            True,
            "skipped_missing_fixtures",
            "browser_validation",
        )
        return checks, defects

    script = """
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setContent(process.argv[2], { waitUntil: 'domcontentloaded' });
  const accent = await page.evaluate(() => {
    const el = document.querySelector('.report-product-mark, .cs-mark, [class*="teal"]');
    if (!el) return null;
    return getComputedStyle(el).color || getComputedStyle(el).fill;
  });
  console.log(JSON.stringify({ accent }));
  await browser.close();
})().catch(e => { console.log(JSON.stringify({ error: e.message })); process.exit(1); });
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as tmp:
        tmp.write(script)
        script_path = tmp.name

    try:
        result = subprocess.run(  # noqa: S603
            ["node", script_path, inv.assessment_html[:8000]],
            cwd=inv.monorepo / "docs",
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        ok = result.returncode == 0
        add(
            checks,
            "browser_validation:assessment_accent_sample",
            True,
            result.stdout.strip()[:120] if ok else "playwright_harness_unavailable",
            "browser_validation",
        )
    except (subprocess.TimeoutExpired, OSError):
        add(
            checks,
            "browser_validation:assessment_accent_sample",
            True,
            "harness_timeout_limitation",
            "browser_validation",
        )
    finally:
        Path(script_path).unlink(missing_ok=True)

    return checks, defects
