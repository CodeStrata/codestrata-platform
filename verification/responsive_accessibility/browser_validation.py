"""Optional real-browser overflow and landmark validation via Node Playwright."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from verification.responsive_accessibility.browser_tooling import (
    detect_browser_tooling,
    run_node_harness,
)
from verification.responsive_accessibility.contract import (
    BROWSER_ARTIFACT,
    DOCS_DIST,
    SV1411_OUTPUT_RELATIVE,
    VIEWPORT_MATRIX_PX,
)
from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect, ViewportOutcome

_DOCS_ROUTES: tuple[tuple[str, str], ...] = (
    ("docs_landing", "index.html"),
    ("docs_getting_started", "getting-started/index.html"),
    ("docs_cli_reference", "reference/cli.html"),
    ("docs_public_contracts", "reference/public-contracts.html"),
)


def run_browser_validation(
    monorepo: Path, inv: SurfaceInventory
) -> tuple[list[CheckResult], list[Defect], list[ViewportOutcome], dict]:
    tooling = detect_browser_tooling(monorepo)
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    viewports: list[ViewportOutcome] = []
    artifact: dict = {
        "engine": tooling.engine,
        "available": tooling.available,
        "detail": tooling.detail,
        "pages": [],
    }

    checks.append(
        CheckResult(
            "browser:tooling_detected",
            True,
            tooling.detail,
            "browser_validation",
        )
    )
    if not tooling.available:
        checks.append(
            CheckResult(
                "browser:validation_skipped",
                True,
                "playwright_unavailable_static_checks_authoritative",
                "browser_validation",
            )
        )
        return checks, defects, viewports, artifact

    if not inv.assessment_html or not inv.eir_html:
        checks.append(
            CheckResult(
                "browser:fixtures_missing",
                False,
                "report_html_absent",
                "browser_validation",
            )
        )
        defects.append(Defect("harness/tooling", "browser fixtures missing"))
        return checks, defects, viewports, artifact

    with tempfile.TemporaryDirectory(prefix="sv1411-browser-") as tmp:
        root = Path(tmp)
        (root / "assessment.html").write_text(inv.assessment_html, encoding="utf-8")
        (root / "eir.html").write_text(inv.eir_html, encoding="utf-8")
        pages = [
            {"surface": "assessment", "route": "assessment.html", "docs": False},
            {"surface": "eir", "route": "eir.html", "docs": False},
        ]
        docs_dist = monorepo / DOCS_DIST
        docs_dist_arg = None
        if docs_dist.is_dir():
            docs_dist_arg = str(docs_dist)
            for surface, route in _DOCS_ROUTES:
                if (docs_dist / route).is_file():
                    pages.append({"surface": surface, "route": route, "docs": True})

        result = run_node_harness(
            monorepo,
            {
                "baseAssessmentDir": str(root),
                "docsDist": docs_dist_arg,
                "pages": pages,
                "widths": list(VIEWPORT_MATRIX_PX),
            },
        )

    artifact["available"] = bool(result.get("available"))
    artifact["detail"] = str(result.get("detail") or tooling.detail)
    artifact["engine"] = str(result.get("engine") or tooling.engine)
    # Drop stderr from the persisted artifact — may contain local paths.
    artifact["pages"] = [
        {
            "surface": page.get("surface"),
            "route": page.get("route"),
            "width_px": page.get("width_px"),
            "page_overflow": page.get("page_overflow"),
            "scroll_width": page.get("scroll_width"),
            "client_width": page.get("client_width"),
            "has_skip": page.get("has_skip"),
            "has_main": page.get("has_main"),
            "h1_count": page.get("h1_count"),
        }
        for page in result.get("pages", [])
    ]

    if not artifact["available"]:
        checks.append(
            CheckResult(
                "browser:validation_skipped",
                True,
                artifact["detail"],
                "browser_validation",
            )
        )
        return checks, defects, viewports, artifact

    for page in artifact["pages"]:
        surface = str(page["surface"])
        width = int(page["width_px"])
        overflow = bool(page["page_overflow"])
        viewports.append(
            ViewportOutcome(
                surface=surface,
                width_px=width,
                page_overflow=overflow,
                measured_in_browser=True,
            )
        )
        ok = not overflow
        checks.append(
            CheckResult(
                f"browser:overflow:{surface}:{width}",
                ok,
                "fits" if ok else "page_overflow",
                "browser_validation",
            )
        )
        if not ok:
            defects.append(
                Defect("responsive overflow", f"{surface} overflows at {width}px")
            )
        if width == 1280:
            checks.append(
                CheckResult(
                    f"browser:landmarks:{surface}",
                    bool(page.get("has_skip"))
                    and bool(page.get("has_main"))
                    and int(page.get("h1_count") or 0) == 1,
                    "skip+main+h1",
                    "browser_validation",
                )
            )

    checks.append(
        CheckResult(
            "browser:pages_measured",
            bool(viewports),
            f"{len(viewports)}",
            "browser_validation",
        )
    )
    return checks, defects, viewports, artifact


def write_browser_artifact(monorepo: Path, artifact: dict) -> Path:
    out_dir = monorepo / SV1411_OUTPUT_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / BROWSER_ARTIFACT
    text = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
    assert "/Users/" not in text
    assert "/home/" not in text
    path.write_text(text, encoding="utf-8")
    return path
