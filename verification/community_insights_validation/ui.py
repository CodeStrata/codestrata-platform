"""Dashboard UI semantic checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_validation._common import add_check
from verification.community_insights_validation.inventory import read_text
from verification.community_insights_validation.models import CheckResult, Defect


def check_ui(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    dashboard = read_text(monorepo, "insights/src/pages/DashboardPage.tsx")
    labels = read_text(monorepo, "insights/src/dashboard/labels.ts")

    add_check(
        checks,
        defects,
        "ui:does_not_compute_metrics",
        "does not compute metric semantics" in dashboard,
        "present",
        "ui",
    )
    add_check(
        checks,
        defects,
        "ui:anonymous_installations_label",
        'total_anonymous_installations: "Anonymous installations"' in labels,
        "exact",
        "ui",
    )
    add_check(
        checks,
        defects,
        "ui:ai_model_family_label",
        'ai_model_adoption: "AI model family adoption"' in labels,
        "exact",
        "ui",
    )
    add_check(
        checks,
        defects,
        "ui:validation_dataset_size_label",
        'validation_dataset_growth: "Validation dataset size"' in labels,
        "exact",
        "ui",
    )
    add_check(
        checks,
        defects,
        "ui:no_users_label",
        '"Users"' not in labels and ">Users<" not in dashboard,
        "absent",
        "ui",
    )
    return checks, defects
