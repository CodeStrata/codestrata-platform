"""Insights validation using suite evidence (no raw keys/IDs)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from verification.community_22_repository_validation.contract import SV1713_OUTPUT_RELATIVE
from verification.community_22_repository_validation.helpers import add_check
from verification.community_22_repository_validation.models import CheckResult, Defect

EVIDENCE_RELATIVE = f"{SV1713_OUTPUT_RELATIVE}/insights-dashboard-check.json"


def _load_evidence(monorepo: Path) -> dict[str, Any] | None:
    path = monorepo / EVIDENCE_RELATIVE
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _budget_defect_classified(evidence: dict[str, Any]) -> bool:
    classification = str(evidence.get("query_budget_classification") or "")
    root_cause = str(evidence.get("root_cause") or "")
    return any(
        token in f"{classification} {root_cause}".lower()
        for token in (
            "planner",
            "list_budget",
            "miscalibration",
            "efficiency",
            "fixed",
            "resolved",
        )
    )


def check_insights(
    *,
    monorepo: Path,
    insights_validation: bool,
    skip_execute: bool,
) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    add_check(
        checks,
        defects,
        "insights:validation_enabled",
        insights_validation is True,
        "true",
        "insights",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if skip_execute:
        add_check(
            checks,
            defects,
            "insights:suite_status",
            True,
            "not_executed",
            "insights",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        return checks, defects

    evidence = _load_evidence(monorepo)
    add_check(
        checks,
        defects,
        "insights:evidence_present",
        evidence is not None,
        EVIDENCE_RELATIVE if evidence else "missing",
        "insights",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    if evidence is None:
        return checks, defects

    overview_http = evidence.get("overview_http")
    login_http = evidence.get("login_http")
    budget_hit = bool(evidence.get("query_budget_reached"))
    metrics = evidence.get("overview_sanitized", {}).get("metrics") if isinstance(
        evidence.get("overview_sanitized"), dict
    ) else evidence.get("metrics")
    metric_rows = metrics if isinstance(metrics, list) else []
    usable = [
        m
        for m in metric_rows
        if isinstance(m, dict)
        and m.get("status") != "error"
        and "query_budget_reached" not in (m.get("limitations") or [])
    ]

    add_check(
        checks,
        defects,
        "insights:login_ok",
        login_http == 200,
        str(login_http),
        "insights",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    add_check(
        checks,
        defects,
        "insights:overview_http_ok",
        overview_http == 200,
        str(overview_http),
        "insights",
        CheckResult=CheckResult,
        Defect=Defect,
    )

    if budget_hit and not usable:
        classified = _budget_defect_classified(evidence)
        add_check(
            checks,
            defects,
            "insights:query_budget_classified",
            classified,
            evidence.get("query_budget_classification")
            or evidence.get("root_cause")
            or "unclassified",
            "insights",
            CheckResult=CheckResult,
            Defect=Defect,
        )
        # Unusable aggregation after classification remains a FAIL for this slice
        # unless the evidence marks the defect as fixed/redeployed.
        fixed = str(evidence.get("status") or "").lower() in {"ok", "pass", "fixed"}
        add_check(
            checks,
            defects,
            "insights:aggregation_usable",
            fixed,
            "query_budget_reached_unusable" if not fixed else "fixed",
            "insights",
            CheckResult=CheckResult,
            Defect=Defect,
        )
    else:
        add_check(
            checks,
            defects,
            "insights:aggregation_usable",
            bool(usable) or not budget_hit,
            f"usable_metrics={len(usable)};budget_hit={budget_hit}",
            "insights",
            CheckResult=CheckResult,
            Defect=Defect,
        )

    # Privacy: evidence must not embed installation IDs or S3 keys.
    blob = json.dumps(evidence, sort_keys=True)
    add_check(
        checks,
        defects,
        "insights:evidence_sanitized",
        "installation_id" not in blob.lower()
        and "s3://" not in blob.lower()
        and "arn:aws" not in blob.lower(),
        "no_installation_id_or_s3",
        "insights",
        CheckResult=CheckResult,
        Defect=Defect,
    )
    return checks, defects
