"""Engineering Intelligence Report boundary for Slice 14.3 verification.

Slice 14.3 must not regress Assessment HTML. After Slice 14.4 begins, EIR
presentation files may change under the EIR redesign policy — that is expected
epic progression, not an Assessment regression.
"""

from __future__ import annotations

from pathlib import Path

from verification.assessment_report_redesign.contract import EIR_STATIC_HTML_ROOT
from verification.assessment_report_redesign.models import CheckResult, Defect


def check_eir_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    eir_root = monorepo / EIR_STATIC_HTML_ROOT
    checks.append(
        CheckResult(
            "eir:static_html_exists",
            eir_root.is_dir(),
            "present",
            "eir_boundary",
        )
    )
    # Assessment HTML tokens must remain Design System consumers (14.3 deliverable).
    assessment_styles = (
        monorepo / "engine/src/codestrata/reporting/html_v2/styles.py"
    ).read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            "eir:assessment_html_still_ds_consumer",
            "DESIGN_TOKENS_CSS" in assessment_styles
            and "codestrata.design_system.tokens" in assessment_styles,
            "assessment_ok",
            "eir_boundary",
        )
    )
    # Domain EIR schema constant remains 1.0 (presentation may evolve in 14.4).
    domain = (
        monorepo
        / "platform/src/codestrata_platform/intelligence_reporting/domain/report.py"
    ).read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            "eir:domain_schema_1_0",
            'ENGINEERING_INTELLIGENCE_REPORT_SCHEMA_VERSION = "1.0"' in domain,
            "1.0",
            "eir_boundary",
        )
    )
    # Slice 14.4 package may exist after epic progression; do not treat as defect.
    eir_14_4 = monorepo / "verification/engineering_intelligence_report_redesign"
    checks.append(
        CheckResult(
            "eir:slice_14_4_progression_allowed",
            True,
            "present" if eir_14_4.is_dir() else "absent_ok",
            "eir_boundary",
        )
    )
    return checks, defects
