"""Publishing boundary / Data Lake separation for Slice 17.19."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_assessment_engineering_intelligence.contract import (
    ASSESSMENT_HTML,
    ASSESSMENT_JSON,
    EIR_HTML,
    EIR_JSON,
    INTELLIGENCE_RELATIVE,
    POLICY_RELATIVE,
    PORTFOLIO_ID,
)
from verification.community_assessment_engineering_intelligence.helpers import (
    check,
    hard_defect,
    load_json,
    read_text,
)
from verification.community_assessment_engineering_intelligence.models import (
    CheckResult,
    Defect,
)


def check_publishing_boundary(
    monorepo: Path,
    selection: dict[str, Any],
    *,
    eir_generation: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo / POLICY_RELATIVE)
    excluded = policy.get("reports_excluded_from_data_lake") is True
    checks.append(
        check(
            "publishing_boundary:reports_excluded_from_data_lake",
            excluded,
            str(policy.get("reports_excluded_from_data_lake")),
            "publishing_boundary",
        )
    )
    if not excluded:
        defects.append(
            hard_defect(
                "reports_in_lake",
                "publishing_boundary:reports_excluded_from_data_lake",
                "true",
                "false",
            )
        )

    assessment_ready = 0
    for item in selection.get("selected") or []:
        rel = item.get("current_relative")
        if not rel:
            continue
        current = monorepo / str(rel)
        if (current / ASSESSMENT_JSON).is_file() and (current / ASSESSMENT_HTML).is_file():
            assessment_ready += 1
    checks.append(
        check(
            "publishing_boundary:assessment_publish_files",
            assessment_ready >= 2,
            f"ready={assessment_ready}",
            "publishing_boundary",
        )
    )

    gen = eir_generation or {}
    portfolio_id = str(gen.get("portfolio_id") or PORTFOLIO_ID)
    eir_current = monorepo / INTELLIGENCE_RELATIVE / portfolio_id / "current"
    eir_ready = (eir_current / EIR_JSON).is_file() and (eir_current / EIR_HTML).is_file()
    checks.append(
        check(
            "publishing_boundary:eir_publish_files",
            eir_ready,
            "eir json+html",
            "publishing_boundary",
        )
    )

    # Structural dry check of report_publishing types (do not publish).
    publish_py = monorepo / "engine/src/codestrata/community_cloud/report_publishing.py"
    publish_ok = False
    if publish_py.is_file():
        text = read_text(publish_py)
        publish_ok = "def publish_local_assessment" in text and "def publish_local_eir" in text
    checks.append(
        check(
            "publishing_boundary:report_publishing_types",
            publish_ok,
            "publish_local_assessment/eir present",
            "publishing_boundary",
        )
    )

    summary = {
        "reports_excluded_from_data_lake": excluded,
        "assessment_ready": assessment_ready,
        "eir_ready": eir_ready,
        "published": False,
    }
    return checks, defects, summary
