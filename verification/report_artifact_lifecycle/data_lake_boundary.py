"""Data Lake boundary checks for Slice 17.15."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.helpers import add_check, read_text
from verification.report_artifact_lifecycle.models import CheckResult, Defect

TELEMETRY_POLICY = "platform/policies/community_insights_ingestion_policy.json"
ENGINE_MANIFEST = "engine/src/codestrata/artifacts/manifest.py"


def check_data_lake_boundary(
    monorepo: Path, policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"telemetry_only": True}

    add_check(
        checks,
        defects,
        "data_lake:no_report_retention",
        policy.get("telemetry_data_lake_uses_report_retention") is False,
        str(policy.get("telemetry_data_lake_uses_report_retention")),
        "data_lake_boundary",
    )
    add_check(
        checks,
        defects,
        "data_lake:validation_no_retention",
        policy.get("validation_artifacts_use_report_retention") is False,
        str(policy.get("validation_artifacts_use_report_retention")),
        "data_lake_boundary",
    )

    tel_path = monorepo / TELEMETRY_POLICY
    if tel_path.is_file():
        text = read_text(tel_path)
        no_reports = "not_repository_identity" in text or "telemetry" in text.lower()
        add_check(
            checks,
            defects,
            "data_lake:telemetry_policy_boundary",
            no_reports,
            "telemetry policy preserves boundary",
            "data_lake_boundary",
        )

    manifest_path = monorepo / ENGINE_MANIFEST
    if manifest_path.is_file():
        text = read_text(manifest_path)
        add_check(
            checks,
            defects,
            "data_lake:manifest_forbidden_upload",
            "DATA_LAKE_UPLOAD_FORBIDDEN" in text,
            "DATA_LAKE_UPLOAD_FORBIDDEN constant",
            "data_lake_boundary",
        )

    repo22 = monorepo / "platform/policies/community_22_repository_validation_policy.json"
    if repo22.is_file():
        data = __import__("json").loads(repo22.read_text(encoding="utf-8"))
        add_check(
            checks,
            defects,
            "data_lake:sv17_13_no_report_storage",
            data.get("data_lake_report_storage") is False,
            str(data.get("data_lake_report_storage")),
            "data_lake_boundary",
        )

    return checks, defects, summary
