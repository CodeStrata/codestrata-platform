"""Anonymous installation identity contract presence (Slice 10.2) — completion checks."""

from __future__ import annotations

import tempfile
from pathlib import Path

from verification.anonymous_analytics_completion.inventory import (
    EngineAnalyticsInventory,
    VsCodeAnalyticsInventory,
    adapt_checks,
)
from verification.anonymous_analytics_completion.models import CheckResult, Defect
from verification.anonymous_analytics_privacy.identity import (
    check_identity as _check_identity_108,
)

_REQUIRED_MODULES: tuple[str, ...] = (
    "installation_identity.py",
    "installation_identity_policy.py",
    "installation_identity_storage.py",
    "installation_identity_diagnostics.py",
    "installation_identity_errors.py",
    "installation_identity_validation.py",
    "installation_identity_compatibility.py",
)


def check_identity(
    monorepo: Path,
    engine: EngineAnalyticsInventory,
    vscode: VsCodeAnalyticsInventory,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    root = monorepo / "engine" / "src" / "codestrata" / "telemetry" / "analytics"

    for name in _REQUIRED_MODULES:
        ok = (root / name).is_file()
        checks.append(
            CheckResult(f"identity:module_present:{name}", ok=ok, category="identity")
        )
        if not ok:
            defects.append(Defect("identity defect", name, "present", "missing"))

    with tempfile.TemporaryDirectory(prefix="cs-sv109-identity-") as tmp:
        tmp_home = Path(tmp) / "codestrata-home"
        raw_checks, raw_defects = _check_identity_108(engine, vscode, tmp_home=tmp_home)
        adapted_checks, adapted_defects = adapt_checks(raw_checks, raw_defects)
        checks.extend(adapted_checks)
        defects.extend(adapted_defects)

    return checks, defects
