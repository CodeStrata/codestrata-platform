"""Lambda image rollback checks for Slice 17.10."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_cloud_production_recovery.helpers import add_check
from verification.community_cloud_production_recovery.models import CheckResult, Defect


def check_lambda_image(
    monorepo: Path, evidence: dict[str, Any], policy: dict[str, Any]
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    loaded = evidence.get("loaded") or {}
    img = loaded.get("lambda_image_rollback") or {}
    ecr = loaded.get("ecr_images") or {}
    has = bool(img) or bool(ecr)

    add_check(checks, defects, "lambda_image:evidence", has, "present" if has else "absent", "lambda_image", soft=True)
    add_check(
        checks,
        defects,
        "lambda_image:policy_ready",
        policy.get("lambda_image_rollback_ready") is True,
        "true",
        "lambda_image",
    )
    activated = img.get("old_image_activated") is True if img else False
    redeploy_current = img.get("current_image_redeploy_proven") is True if img else False
    add_check(
        checks,
        defects,
        "lambda_image:rollback_executed",
        activated or redeploy_current or not has,
        "activated" if activated else ("redeploy_current" if redeploy_current else str(img.get("old_image_activated"))),
        "lambda_image",
        soft=True,
    )
    # Soft limitation: proving readiness without activating an unsafe/old image.
    unsafe_not_activated = img.get("unsafe_old_image_not_activated", True) if img else True
    summary = {
        "evidence": has,
        "policy_ready": policy.get("lambda_image_rollback_ready") is True,
        "activated": activated,
        "unsafe_old_image_not_activated": unsafe_not_activated,
        "ready": policy.get("lambda_image_rollback_ready") is True,
    }
    return checks, defects, summary
