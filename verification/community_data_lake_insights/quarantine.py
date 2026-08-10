"""Quarantine / HTTP reject-before-persist checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_data_lake_insights.contract import POLICY_RELATIVE
from verification.community_data_lake_insights.helpers import check, load_json
from verification.community_data_lake_insights.models import CheckResult, Defect


def check_quarantine(
    monorepo: Path,
    *,
    live_probe: dict[str, Any] | None = None,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy = load_json(monorepo / POLICY_RELATIVE)
    live = live_probe or {}

    behavior = policy.get("quarantine_behavior")
    policy_ok = behavior == "http_reject_before_persist"
    checks.append(
        check(
            "quarantine:policy_http_reject_before_persist",
            policy_ok,
            str(behavior),
            "quarantine",
        )
    )
    if not policy_ok:
        defects.append(
            Defect(
                "quarantine_policy",
                "quarantine:policy_http_reject_before_persist",
                "http_reject_before_persist",
                str(behavior),
            )
        )

    q_delta = int(live.get("quarantine_delta") or 0)
    live_ok = live.get("live_probe_completed") is True and q_delta == 0
    # If live probe not completed, still record expected contract.
    if live.get("live_probe_completed") is True:
        checks.append(
            check(
                "quarantine:live_http_reject_delta_zero",
                q_delta == 0,
                f"quarantine_delta={q_delta}",
                "quarantine",
            )
        )
        if q_delta != 0:
            defects.append(
                Defect(
                    "quarantine_grew_on_http_reject",
                    "quarantine:live_http_reject_delta_zero",
                    "0",
                    f"delta={q_delta}",
                )
            )
    else:
        checks.append(
            check(
                "quarantine:live_http_reject_delta_zero",
                False,
                "live probe incomplete",
                "quarantine",
            )
        )

    summary = {
        "quarantine_behavior": behavior,
        "quarantine_delta": q_delta,
        "http_reject_before_persist": policy_ok and (q_delta == 0 or not live),
        "live_ok": live_ok,
    }
    return checks, defects, summary
