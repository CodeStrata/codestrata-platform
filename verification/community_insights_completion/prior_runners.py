"""Invoke prior Slice 15.1–15.11 authoritative runners."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from verification.community_insights_completion.contract import PRIOR_SLICE_RUNNERS
from verification.community_insights_completion.models import CheckResult, Defect


def run_prior_slice_verifiers(
    monorepo: Path,
) -> tuple[dict[str, dict[str, Any]], list[CheckResult], list[Defect]]:
    results: dict[str, dict[str, Any]] = {}
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    for slice_id, module_name, schema, title, policy in PRIOR_SLICE_RUNNERS:
        try:
            mod = importlib.import_module(module_name)
            report = mod.build_report(monorepo)
            verdict = getattr(report, "verdict", "FAIL")
            total = int(getattr(report, "total_checks", 0))
            failed = int(getattr(report, "failed_checks", 0))
            limitations = list(getattr(report, "limitations", []) or [])
            blockers = list(getattr(report, "blockers", []) or [])
            results[slice_id] = {
                "verdict": verdict,
                "total_checks": total,
                "failed_checks": failed,
                "schema": schema,
                "title": title,
                "policy": policy,
                "limitations": [str(x) for x in limitations],
                "blockers": [str(x) for x in blockers],
            }
            ok = verdict in {"PASS", "PASS_WITH_LIMITATIONS"} and failed == 0
            checks.append(
                CheckResult(
                    name=f"prior:{slice_id}:verdict",
                    ok=ok,
                    detail=f"{verdict}:{total}:{failed}",
                    category="prior_verification",
                )
            )
            if not ok:
                defects.append(
                    Defect(
                        classification="prior-slice verification defect",
                        surface=slice_id,
                        expected="PASS or PASS_WITH_LIMITATIONS with 0 failed",
                        observed=f"{verdict}/{failed}",
                    )
                )
        except Exception as exc:  # noqa: BLE001 — surface as failure
            results[slice_id] = {
                "verdict": "ERROR",
                "total_checks": 0,
                "failed_checks": 1,
                "schema": schema,
                "title": title,
                "policy": policy,
                "limitations": [],
                "blockers": [type(exc).__name__],
            }
            checks.append(
                CheckResult(
                    name=f"prior:{slice_id}:verdict",
                    ok=False,
                    detail=type(exc).__name__,
                    category="prior_verification",
                )
            )
            defects.append(
                Defect(
                    classification="prior-slice verification defect",
                    surface=slice_id,
                    expected="build_report success",
                    observed=type(exc).__name__,
                )
            )

    return results, checks, defects
