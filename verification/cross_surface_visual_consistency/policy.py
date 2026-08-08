"""Policy checks for Slice 14.13."""

from __future__ import annotations

from verification.cross_surface_visual_consistency._helpers import add
from verification.cross_surface_visual_consistency.contract import POLICY_ID, POLICY_VERSION
from verification.cross_surface_visual_consistency.inventory import ConsistencyInventory
from verification.cross_surface_visual_consistency.models import CheckResult


def check_policy(inv: ConsistencyInventory) -> list[CheckResult]:
    checks: list[CheckResult] = []
    policy = inv.policy

    add(
        checks,
        "policy:id_version",
        policy.get("policy_id") == POLICY_ID
        and policy.get("policy_version") == POLICY_VERSION,
        f"{POLICY_ID}:{POLICY_VERSION}",
        "policy",
    )
    add(
        checks,
        "policy:design_system_1_0",
        policy.get("design_system_version") == "1.0",
        "design_system_1_0",
        "policy",
    )
    add(
        checks,
        "policy:semantic_consistency",
        policy.get("semantic_consistency_required") is True
        and policy.get("active_legacy_branding_allowed") is False,
        "semantic_consistency",
        "policy",
    )
    add(
        checks,
        "policy:surfaces",
        set(policy.get("surfaces") or [])
        >= {
            "documentation",
            "assessment_report",
            "eir",
            "vscode",
            "marketplace",
            "api_portal",
        },
        "six_surfaces",
        "policy",
    )
    add(
        checks,
        "policy:prohibited_epic_15",
        policy.get("prohibited", {}).get("start_epic_15") is True
        and policy.get("prohibited", {}).get("wholesale_redesign") is True,
        "epic_15_prohibited",
        "policy",
    )
    add(
        checks,
        "policy:no_runtime_change",
        policy.get("runtime_behavior_change_allowed") is False,
        "runtime_unchanged",
        "policy",
    )
    return checks
