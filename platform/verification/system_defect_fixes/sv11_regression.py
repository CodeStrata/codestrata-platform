"""SV.11 EI-readiness regression after Platform safety alignment."""

from __future__ import annotations

from pathlib import Path

from verification.engineering_intelligence.catalog import monorepo_root_from_here
from verification.system_defect_fixes.contract import (
    TARGET_REPOSITORY_COUNT,
)
from verification.system_defect_fixes.models import CheckResult


def check_sv11_ei_ready(monorepo: Path | None = None) -> CheckResult:
    """Re-run SV.11 EI readiness logic against preserved SV.10 bundles."""

    root = (monorepo or monorepo_root_from_here()).resolve()
    engine = root / "engine"
    import sys

    if str(engine) not in sys.path:
        sys.path.insert(0, str(engine))

    from verification.assessment_consistency.inputs import (
        default_sv10_dir,
        load_all_bundles,
    )
    from verification.assessment_consistency.reporting import (
        check_engineering_intelligence_input_ready,
    )

    final_report, records, bundles = load_all_bundles(default_sv10_dir(engine))
    _ = final_report, records
    ready, _checks, defects = check_engineering_intelligence_input_ready(bundles)
    ready_count = sum(1 for ok in ready.values() if ok)
    return CheckResult(
        name="sv11_ei_input_ready_22",
        ok=ready_count == TARGET_REPOSITORY_COUNT and not defects,
        detail=f"ready={ready_count}/{len(ready)} defects={len(defects)}",
    )
