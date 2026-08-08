"""Production ingestion boundary checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.inventory import load_json
from verification.community_insights_validation.models import CheckResult, Defect

_POLICY_CHECKS: tuple[tuple[str, tuple[tuple[str, object], ...]], ...] = (
    (
        "platform/policies/community_insights_validation_policy.json",
        (("production_ingestion_enabled", False),),
    ),
    (
        "platform/policies/codestrata_insights_dashboard_policy.json",
        (("production_ingestion_enabled", False),),
    ),
    (
        "platform/policies/community_insights_ingestion_policy.json",
        (
            ("enable_ingestion_wire", False),
            ("production_transmission_enabled", False),
        ),
    ),
    (
        "platform/policies/community_insights_auth_policy.json",
        (("production_deployment_enabled", False),),
    ),
)


def check_production_ingestion_boundary(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    for rel, fields in _POLICY_CHECKS:
        policy = load_json(monorepo, rel)
        name = Path(rel).stem
        for field, expected in fields:
            add_check(
                checks,
                defects,
                f"ingestion:{name}_{field}",
                policy.get(field) is expected,
                str(policy.get(field)),
                "deployment_boundary",
            )
    return checks, defects
