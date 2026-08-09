"""Resource recovery classification checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.contract import (
    ALLOWED_RECOVERY_MODES,
    CLASSIFICATION_RELATIVE,
    CLASSIFICATION_SCHEMA,
    REQUIRED_CLASSIFICATION_COMPONENTS,
)
from verification.community_cloud_production_recovery.helpers import add_check, read_json
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_resource_classification(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    path = monorepo / CLASSIFICATION_RELATIVE
    add_check(checks, defects, "classification:exists", path.is_file(), CLASSIFICATION_RELATIVE, "resource_classification")
    data: dict[str, Any] = {}
    if path.is_file():
        data = read_json(path)
        add_check(
            checks,
            defects,
            "classification:schema",
            data.get("schema") == CLASSIFICATION_SCHEMA,
            str(data.get("schema")),
            "resource_classification",
        )
        components = data.get("components") or []
        names = {c.get("component") for c in components if isinstance(c, dict)}
        missing = [n for n in REQUIRED_CLASSIFICATION_COMPONENTS if n not in names]
        add_check(
            checks,
            defects,
            "classification:components_complete",
            not missing,
            "ok" if not missing else f"missing={missing}",
            "resource_classification",
        )
        modes_ok = True
        never_destroy = set()
        for c in components:
            if not isinstance(c, dict):
                modes_ok = False
                continue
            mode = c.get("recovery_mode")
            if mode not in ALLOWED_RECOVERY_MODES:
                modes_ok = False
            for key in (
                "rollback_mechanism",
                "destructive_allowed",
                "data_preservation_required",
                "operator_class",
                "verification_status",
            ):
                if key not in c:
                    modes_ok = False
            if mode == "NEVER_AUTOMATICALLY_DESTROY":
                never_destroy.add(c.get("component"))
            if c.get("destructive_allowed") is True:
                modes_ok = False
        add_check(checks, defects, "classification:fields_valid", modes_ok, "modes_and_fields", "resource_classification")
        add_check(
            checks,
            defects,
            "classification:data_lake_never_destroy",
            "Data Lake S3" in never_destroy,
            str(sorted(never_destroy)),
            "resource_classification",
        )
        add_check(
            checks,
            defects,
            "classification:remote_state_never_destroy",
            "remote-state S3" in never_destroy,
            str(sorted(never_destroy)),
            "resource_classification",
        )
        add_check(
            checks,
            defects,
            "classification:start_17_11",
            data.get("start_slice_17_11") is True,
            "true",
            "resource_classification",
        )
        add_check(
            checks,
            defects,
            "classification:start_17_12_false",
            data.get("start_slice_17_12") is False,
            "false",
            "resource_classification",
        )
    summary = {
        "schema": data.get("schema"),
        "component_count": len(data.get("components") or []),
        "complete": len(data.get("components") or []) == len(REQUIRED_CLASSIFICATION_COMPONENTS),
    }
    return checks, defects, summary
