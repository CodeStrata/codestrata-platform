"""Data Lake boundary and privacy evidence checks for Slice 17.13."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.contract import SV1713_OUTPUT_RELATIVE
from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect

EVIDENCE_RELATIVE = f"{SV1713_OUTPUT_RELATIVE}/data-lake-privacy-check.json"


def _load_evidence(monorepo: Path) -> dict[str, Any] | None:
    path = monorepo / EVIDENCE_RELATIVE
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def check_data_lake(
    *,
    monorepo: Path,
    data_lake_report_storage: bool,
    skip_execute: bool,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "data_lake:report_storage_disabled",
        data_lake_report_storage is False,
        "false",
        "data_lake",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "data_lake:telemetry_only_boundary",
        data_lake_report_storage is False,
        "telemetry_only",
        "data_lake",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if skip_execute:
        add_check(
            checks,
            defects,
            "data_lake:suite_status",
            True,
            "not_executed",
            "data_lake",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        return checks, defects

    evidence = _load_evidence(monorepo)
    add_check(
        checks,
        defects,
        "data_lake:evidence_present",
        evidence is not None,
        EVIDENCE_RELATIVE if evidence else "missing",
        "data_lake",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if evidence is None:
        return checks, defects

    blob = json.dumps(evidence, sort_keys=True)
    add_check(
        checks,
        defects,
        "data_lake:object_keys_omitted",
        evidence.get("object_keys_omitted") is True
        and "s3://" not in blob.lower()
        and "/raw/stream=" not in blob,
        "keys_omitted",
        "data_lake",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "data_lake:report_artifacts_forbidden",
        evidence.get("report_artifacts_forbidden") is True,
        "true",
        "data_lake",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    # Suite-day delta may be empty when privacy-first transport does not land
    # Community Cloud events; classify explicitly rather than inventing ingestion.
    classification = str(evidence.get("classification") or "")
    today_empty = bool(evidence.get("today_partition_empty"))
    add_check(
        checks,
        defects,
        "data_lake:suite_delta_classified",
        (not today_empty)
        or classification
        in {
            "telemetry_transport_unavailable_or_no_suite_delta",
            "suite_delta_present",
            "privacy_safe_sample_ok",
        },
        classification or ("empty_unclassified" if today_empty else "delta_present"),
        "data_lake",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects
