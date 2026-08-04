"""Script safety verification."""

from __future__ import annotations

from infrastructure.verification.contract import infra_root
from infrastructure.verification.models import CheckResult


def check_scripts() -> list[CheckResult]:
    scripts = infra_root() / "scripts"
    build = (scripts / "build-community-cloud-api.sh").read_text(encoding="utf-8")
    validate = (scripts / "validate.sh").read_text(encoding="utf-8")
    plan = (scripts / "plan-production.sh").read_text(encoding="utf-8")
    smoke = (scripts / "smoke-health.sh").read_text(encoding="utf-8")
    return [
        CheckResult(
            name="scripts:present",
            ok=all(
                (scripts / name).is_file()
                for name in (
                    "build-community-cloud-api.sh",
                    "validate.sh",
                    "plan-production.sh",
                    "smoke-health.sh",
                )
            ),
            detail="four scripts",
            category="scripts",
        ),
        CheckResult(
            name="scripts:fail_fast",
            ok=all('set -euo pipefail' in text for text in (build, validate, plan, smoke)),
            detail="pipefail",
            category="scripts",
        ),
        CheckResult(
            name="scripts:build_no_push_default",
            ok="docker push" not in build.lower()
            or "push" not in build.split("\n")[0].lower(),
            detail="no push by default",
            category="scripts",
            scenario="T",
        ),
        CheckResult(
            name="scripts:build_requires_tag",
            ok="IMAGE_TAG" in build or "--tag" in build,
            detail="explicit tag",
            category="scripts",
        ),
        CheckResult(
            name="scripts:build_rejects_latest",
            ok="latest" in build.lower(),
            detail="latest guard present",
            category="scripts",
            scenario="J",
        ),
        CheckResult(
            name="scripts:validate_no_apply",
            ok="apply" not in validate.lower() or "no apply" in validate.lower(),
            detail="non-destructive",
            category="scripts",
        ),
        CheckResult(
            name="scripts:plan_no_auto_approve",
            ok="--auto-approve" not in plan and "tofu apply" not in plan,
            detail="plan only",
            category="scripts",
            scenario="S",
        ),
        CheckResult(
            name="scripts:plan_requires_tofu",
            ok="tofu" in plan and "OpenTofu" in plan,
            detail="tofu required",
            category="scripts",
        ),
        CheckResult(
            name="scripts:smoke_health_only",
            ok="/api/v1/health" in smoke
            and "telemetry" not in smoke
            and "assessment-metadata" not in smoke,
            detail="health only",
            category="scripts",
            scenario="U",
        ),
        CheckResult(
            name="scripts:no_embedded_credentials",
            ok=all(
                "aws_secret_access_key" not in text.lower()
                for text in (build, validate, plan, smoke)
            )
            and "AKIA" not in build + validate + plan + smoke
            and "cscc_v1_LIVE" not in build + validate + plan + smoke,
            detail="no live credentials",
            category="scripts",
            scenario="O",
        ),
    ]
