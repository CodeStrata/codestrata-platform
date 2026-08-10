"""Portfolio identity checks for Slice 17.15."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from verification.report_artifact_lifecycle.contract import ENGINE_PORTFOLIO_IDENTITY
from verification.report_artifact_lifecycle.helpers import add_check, read_text, try_import_engine_module
from verification.report_artifact_lifecycle.models import CheckResult, Defect

_PORTFOLIO_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_TIMESTAMP_PORTFOLIO = re.compile(r"portfolio-sv\d+-\d", re.I)


def check_portfolio_identity(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {"module_present": False, "api_exercised": False}

    path = monorepo / ENGINE_PORTFOLIO_IDENTITY
    present = path.is_file()
    summary["module_present"] = present
    add_check(
        checks,
        defects,
        "portfolio_identity:module_exists",
        present,
        ENGINE_PORTFOLIO_IDENTITY,
        "portfolio_identity",
        soft=not present,
    )

    if present:
        text = read_text(path)
        add_check(
            checks,
            defects,
            "portfolio_identity:human_readable",
            "release-validation" in text or "human" in text.lower(),
            "human-readable portfolio id",
            "portfolio_identity",
            soft=True,
        )
        add_check(
            checks,
            defects,
            "portfolio_identity:no_run_stamped_ids",
            "portfolio-sv" not in text.lower() or "not" in text.lower(),
            "no run-stamped portfolio ids",
            "portfolio_identity",
            soft=True,
        )

    module, err = try_import_engine_module("codestrata.artifacts.portfolio_identity")
    if module is not None:
        for fn_name in ("build_portfolio_id", "resolve_portfolio_id", "validate_portfolio_id"):
            fn = getattr(module, fn_name, None)
            if callable(fn):
                try:
                    if fn_name == "build_portfolio_id":
                        pid = fn(name="release-validation")
                    else:
                        pid = fn("release-validation")
                    pid_str = str(pid)
                    ok = bool(_PORTFOLIO_ID.match(pid_str)) and not _TIMESTAMP_PORTFOLIO.search(pid_str)
                    add_check(
                        checks,
                        defects,
                        f"portfolio_identity:{fn_name}",
                        ok,
                        pid_str,
                        "portfolio_identity",
                        soft=False if present else True,
                    )
                    summary["api_exercised"] = summary["api_exercised"] or ok
                except Exception as exc:  # noqa: BLE001
                    add_check(
                        checks,
                        defects,
                        f"portfolio_identity:{fn_name}",
                        False,
                        str(exc),
                        "portfolio_identity",
                        soft=True,
                    )
    elif present:
        add_check(
            checks,
            defects,
            "portfolio_identity:import",
            False,
            err or "import failed",
            "portfolio_identity",
            soft=True,
        )

    return checks, defects, summary
