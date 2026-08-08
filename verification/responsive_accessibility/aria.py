"""ARIA usage boundary checks."""

from __future__ import annotations

from verification.responsive_accessibility.inventory import SurfaceInventory
from verification.responsive_accessibility.models import CheckResult, Defect

_CATEGORY = "aria"


def check_aria(inv: SurfaceInventory) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append(CheckResult(name, ok, detail, _CATEGORY))

    add(
        "aria:assessment_no_severity_label",
        'aria-label="Severity:' not in inv.assessment_html,
        "sr_only_instead",
    )
    add(
        "aria:eir_no_severity_label",
        'aria-label="Severity:' not in inv.eir_html,
        "sr_only_instead",
    )
    add(
        "aria:assessment_no_report_edition_label",
        'aria-label="Report edition"' not in inv.assessment_html,
        "absent",
    )
    add(
        "aria:eir_summary_kpis_group",
        'class="summary-kpis"' in inv.eir_html and 'role="group"' in inv.eir_html,
        "group",
    )
    add(
        "aria:brand_mark_hidden",
        'aria-hidden="true"' in inv.assessment_html and "cs-mark" in inv.assessment_html,
        "mark",
    )
    add(
        "aria:assessment_no_anchor_hidden",
        'class="section-anchor-only" aria-hidden="true"' not in inv.assessment_html,
        "anchors_visible",
    )

    if any(not c.ok for c in checks):
        defects.append(Defect("aria", "ARIA usage violates accessibility contract"))
    return checks, defects
