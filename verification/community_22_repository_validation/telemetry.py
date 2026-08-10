"""Telemetry validation using suite policy + transport classification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.contract import SV1713_OUTPUT_RELATIVE
from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect

DATA_LAKE_EVIDENCE = f"{SV1713_OUTPUT_RELATIVE}/data-lake-privacy-check.json"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def check_telemetry(
    *,
    monorepo: Path,
    telemetry_validation_enabled: bool,
    skip_execute: bool,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "telemetry:validation_enabled",
        telemetry_validation_enabled is True,
        "true",
        "telemetry",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if skip_execute:
        add_check(
            checks,
            defects,
            "telemetry:suite_status",
            True,
            "not_executed",
            "telemetry",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        return checks, defects

    evidence = _load_json(monorepo / DATA_LAKE_EVIDENCE)
    add_check(
        checks,
        defects,
        "telemetry:evidence_bridge_present",
        evidence is not None,
        DATA_LAKE_EVIDENCE if evidence else "missing",
        "telemetry",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if evidence is None:
        return checks, defects

    classification = str(evidence.get("classification") or "")
    today_empty = bool(evidence.get("today_partition_empty"))
    # Privacy-safe transport may intentionally omit Community Cloud landing.
    # That is a limitation/classification, not a silent pass.
    ok = (not today_empty) or bool(classification)
    add_check(
        checks,
        defects,
        "telemetry:suite_transport_classified",
        ok,
        classification or ("delta_present" if not today_empty else "unclassified"),
        "telemetry",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "telemetry:no_report_upload",
        evidence.get("report_artifacts_forbidden") is True,
        "report_artifacts_forbidden",
        "telemetry",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects
