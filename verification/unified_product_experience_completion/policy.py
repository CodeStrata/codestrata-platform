"""Completion policy checks for Slice 14.14."""

from __future__ import annotations

from pathlib import Path

from verification.unified_product_experience_completion.contract import (
    POLICY_ID,
    POLICY_RELATIVE,
    POLICY_VERSION,
)
from verification.unified_product_experience_completion.inventory import load_json
from verification.unified_product_experience_completion.models import CheckResult, Defect


def check_completion_policy(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo, POLICY_RELATIVE)

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, "completion_policy"))
        if not ok:
            defects.append(
                Defect("completion_policy", name, "required", detail)
            )

    add("policy:present", bool(policy), "present" if policy else "missing")
    add("policy:id", policy.get("policy_id") == POLICY_ID, str(policy.get("policy_id")))
    add(
        "policy:version",
        policy.get("policy_version") == POLICY_VERSION,
        str(policy.get("policy_version")),
    )
    add("policy:epic", policy.get("epic") == 14, str(policy.get("epic")))
    add(
        "policy:slice_count",
        policy.get("slice_count") == 14,
        str(policy.get("slice_count")),
    )
    for flag in (
        "design_system_complete",
        "community_docs_complete",
        "assessment_report_complete",
        "eir_report_complete",
        "vscode_visual_complete",
        "marketplace_visual_complete",
        "presentation_standard_complete",
        "visualization_standard_complete",
        "report_ia_complete",
        "brand_assets_complete",
        "accessibility_responsive_complete",
        "documentation_deployment_ready",
        "cross_surface_consistency_complete",
    ):
        add(f"policy:{flag}", policy.get(flag) is True, str(policy.get(flag)))
    for flag in (
        "production_deploy_complete",
        "release_tag_created",
        "marketplace_published",
        "docs_production_deployed",
        "commit_created",
        "published",
        "deployed",
        "start_slice_15_7",
    ):
        add(f"policy:{flag}_false", policy.get(flag) is False, str(policy.get(flag)))
    add(
        "policy:prohibited_start_slice_15_7",
        policy.get("prohibited", {}).get("start_slice_15_7") is True,
        "forbidden",
    )
    return checks, defects
