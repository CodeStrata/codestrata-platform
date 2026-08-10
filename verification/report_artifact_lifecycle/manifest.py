"""Manifest checks for Slice 17.15."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.contract import ENGINE_MANIFEST
from verification.report_artifact_lifecycle.helpers import add_check, read_text
from verification.report_artifact_lifecycle.models import CheckResult, Defect


def check_manifest(monorepo: Path, policy: dict[str, Any]) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"run_id_in_manifest": False}

    add_check(
        checks,
        defects,
        "manifest:run_ids_are_metadata",
        policy.get("run_ids_are_metadata") is True,
        str(policy.get("run_ids_are_metadata")),
        "manifest",
    )

    path = monorepo / ENGINE_MANIFEST
    add_check(checks, defects, "manifest:module_exists", path.is_file(), ENGINE_MANIFEST, "manifest")
    if path.is_file():
        text = read_text(path)
        summary["run_id_in_manifest"] = "run_id" in text or "assessment_id" in text
        add_check(
            checks,
            defects,
            "manifest:run_id_field",
            summary["run_id_in_manifest"],
            "run_id or assessment_id in manifest builder",
            "manifest",
            soft=True,
        )
        add_check(
            checks,
            defects,
            "manifest:data_lake_forbidden",
            "DATA_LAKE_UPLOAD_FORBIDDEN" in text or "data_lake_upload_forbidden" in text,
            "data lake upload forbidden marker",
            "manifest",
        )

    return checks, defects, summary
