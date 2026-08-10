"""Privacy scan across assessment + EIR artifacts for Slice 17.19."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import (
    ASSESSMENT_HTML,
    ASSESSMENT_JSON,
    EIR_HTML,
    EIR_JSON,
    INTELLIGENCE_RELATIVE,
    PORTFOLIO_ID,
)
from verification.community_assessment_engineering_intelligence.helpers import (
    artifact_text_is_safe,
    check,
    hard_defect,
    read_text,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_privacy(
    monorepo: Path,
    selection: dict[str, Any],
    *,
    eir_generation: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    scanned = 0
    dirty = 0

    paths: list[Path] = []
    for item in selection.get("selected") or []:
        rel = item.get("current_relative")
        if not rel:
            continue
        current = monorepo / str(rel)
        for name in (ASSESSMENT_JSON, ASSESSMENT_HTML):
            path = current / name
            if path.is_file():
                paths.append(path)

    gen = eir_generation or {}
    portfolio_id = str(gen.get("portfolio_id") or PORTFOLIO_ID)
    eir_current = monorepo / INTELLIGENCE_RELATIVE / portfolio_id / "current"
    for name in (EIR_JSON, EIR_HTML):
        path = eir_current / name
        if path.is_file():
            paths.append(path)

    for path in paths:
        scanned += 1
        text = read_text(path)
        ok = artifact_text_is_safe(text)
        if not ok:
            dirty += 1
            defects.append(
                hard_defect(
                    "privacy_leak",
                    f"privacy:scan:{path.name}",
                    "safe",
                    path.name,
                )
            )
        checks.append(
            check(
                f"privacy:scan:{path.parent.parent.name if path.parent.name in {'current','previous'} else path.stem}:{path.name}",
                ok,
                path.name,
                "privacy",
            )
        )

    summary = {"scanned": scanned, "dirty": dirty, "ok": dirty == 0}
    return checks, defects, summary
