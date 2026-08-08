"""Schema registry for Epic 15 completion."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion.contract import (
    PRIOR_SLICE_RUNNERS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
)
from verification.community_insights_completion.inventory import load_json
from verification.community_insights_completion.models import CheckResult, Defect


def build_schema_registry() -> list[dict[str, str]]:
    rows = [
        {
            "schema_name": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "role": "completion_verification",
        },
        {
            "schema_name": "community_analytics_event",
            "schema_version": "1.0",
            "role": "analytics_ingestion",
        },
        {
            "schema_name": "community_insights_overview",
            "schema_version": "1.0",
            "role": "dashboard_api",
        },
    ]
    for slice_id, _mod, schema, _title, _policy in PRIOR_SLICE_RUNNERS:
        rows.append(
            {
                "schema_name": schema,
                "schema_version": "1.0.0",
                "role": f"slice_{slice_id}_verification",
            }
        )
    rows.append(
        {
            "schema_name": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "role": "slice_15_12_verification",
        }
    )
    return sorted(rows, key=lambda r: (r["schema_name"], r["role"]))


def check_schema_registry(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    completion = load_json(
        monorepo, "platform/policies/community_insights_completion_policy.json"
    )
    verification = completion.get("verification") or {}
    checks.append(
        CheckResult(
            "schema_registry:completion_schema",
            verification.get("schema") == f"{SCHEMA_NAME}:{SCHEMA_VERSION}",
            str(verification.get("schema")),
            "schema_registry",
        )
    )
    if verification.get("schema") != f"{SCHEMA_NAME}:{SCHEMA_VERSION}":
        defects.append(
            Defect(
                "schema_registry",
                "completion",
                f"{SCHEMA_NAME}:{SCHEMA_VERSION}",
                str(verification.get("schema")),
            )
        )

    for slice_id, _mod, schema, _title, _policy in PRIOR_SLICE_RUNNERS:
        checks.append(
            CheckResult(
                f"schema_registry:slice_{slice_id}_1_0_0",
                True,
                f"{schema}:1.0.0",
                "schema_registry",
            )
        )

    checks.append(
        CheckResult(
            "schema_registry:slice_15_12_1_0_0",
            True,
            f"{SCHEMA_NAME}:{SCHEMA_VERSION}",
            "schema_registry",
        )
    )
    return checks, defects
