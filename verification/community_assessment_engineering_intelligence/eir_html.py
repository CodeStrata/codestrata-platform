"""EIR HTML privacy and portfolio marker checks for Slice 17.19."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import (
    EIR_HTML,
    INTELLIGENCE_RELATIVE,
    PORTFOLIO_ID,
)
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
    read_text,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_eir_html(
    monorepo: Path,
    *,
    eir_generation: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    gen = eir_generation or {}
    portfolio_id = str(gen.get("portfolio_id") or PORTFOLIO_ID)
    path = monorepo / INTELLIGENCE_RELATIVE / portfolio_id / "current" / EIR_HTML
    exists = path.is_file() and path.stat().st_size > 0
    checks.append(
        check("eir_html:exists", exists, f"bytes={path.stat().st_size if path.is_file() else 0}", "eir_html")
    )
    if not exists:
        defects.append(
            hard_defect("missing_eir_html", "eir_html:exists", "present", "absent")
        )
        return checks, defects, {"ok": False}

    text = read_text(path)
    privacy_ok = not any(
        needle in text for needle in ("/Users/", "arn:aws:", "cscc_v1_", "raw/stream=", "Bearer ")
    )
    checks.append(check("eir_html:privacy", privacy_ok, "no secrets", "eir_html"))
    if not privacy_ok:
        defects.append(
            hard_defect("eir_html_privacy", "eir_html:privacy", "clean", "forbidden")
        )

    portfolio_ok = (
        portfolio_id in text
        or "portfolio" in text.lower()
        or "engineering intelligence" in text.lower()
        or "codestrata" in text.lower()
    )
    checks.append(
        check("eir_html:portfolio_markers", portfolio_ok, "portfolio markers", "eir_html")
    )

    summary = {
        "bytes": path.stat().st_size,
        "privacy_ok": privacy_ok,
        "portfolio_markers": portfolio_ok,
    }
    return checks, defects, summary
