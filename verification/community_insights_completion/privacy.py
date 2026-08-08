"""Privacy boundary gate."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_completion.inventory import add_check, exists, read_text
from verification.community_insights_completion.models import CheckResult, Defect

FORBIDDEN = ("installation_id", "repository_name", "source_code", "prompt", "credential")


def check_privacy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(checks, defects, "privacy:metrics_policy", exists(monorepo, "platform/policies/community_insights_metrics_policy.json"), "present", "privacy")
    add_check(checks, defects, "privacy:validation_policy", exists(monorepo, "platform/policies/community_insights_validation_policy.json"), "present", "privacy")
    labels = read_text(monorepo, "insights/src/dashboard/labels.ts")
    for field in FORBIDDEN:
        add_check(checks, defects, f"privacy:labels_no_{field}", field not in labels.lower(), "absent", "privacy")
    return checks, defects
