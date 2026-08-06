"""Primary-operation isolation checks (Slice 10.9 completion).

Thin delegation to Slice 10.8's ``check_isolation``.
"""

from __future__ import annotations

from pathlib import Path

from verification.anonymous_analytics_completion.inventory import (
    VsCodeAnalyticsInventory,
    adapt_checks,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.isolation import (
    check_isolation as _check_isolation_108,
)


def check_isolation(
    monorepo: Path,
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    raw_checks, raw_defects = _check_isolation_108(vscode, monorepo)
    return adapt_checks(raw_checks, raw_defects)
