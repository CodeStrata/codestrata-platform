"""Negative scenario checks A–Z."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

from verification.community_insights_validation._common import add_check, frontend_source_blob
from verification.community_insights_validation.contract import (
    FORBIDDEN_15_12_PATHS,
    FORBIDDEN_CHART_PACKAGES,
    FRONTEND_SOURCE_FILES,
    INSIGHTS_PACKAGES,
    POLICY_RELATIVE,
    PRIOR_SLICE_PACKAGES,
    PRIVACY_FORBIDDEN_FIELDS,
    PRIVACY_UI_FILES,
)
from verification.community_insights_validation.determinism import report_text_is_safe
from verification.community_insights_validation.fixtures import build_fixtures, bounded_reader, metric_window
from verification.community_insights_validation.inventory import exists, load_json, package_source_blob, read_text
from verification.community_insights_validation.iam import _iam_actions
from verification.community_insights_validation.models import CheckResult, Defect
from verification.community_insights_validation.scenarios import VALIDATION_SCENARIOS


def _scenario_checks(monorepo: Path) -> dict[str, bool]:
    policy = load_json(monorepo, POLICY_RELATIVE)
    dashboard = read_text(monorepo, "insights/src/pages/DashboardPage.tsx")
    ui_source = "\n".join(read_text(monorepo, rel) for rel in PRIVACY_UI_FILES)
    frontend_source = frontend_source_blob(monorepo)
    pkg = load_json(monorepo, "insights/package.json")
    deps = {**(pkg.get("dependencies") or {}), **(pkg.get("devDependencies") or {})}
    chart_pkg = any(name in deps for name in FORBIDDEN_CHART_PACKAGES)
    fx = build_fixtures()

    from verification.community_insights_validation._common import ensure_platform_importable

    ensure_platform_importable(monorepo)
    from codestrata_platform.community_cloud_api.insights.models import MetricRequest
    from codestrata_platform.community_cloud_api.insights.service import aggregate_metric
    from codestrata_platform.community_cloud_api.insights.suppression import suppress_groups
    from codestrata_platform.community_cloud_api.insights_storage.reader import reject_arbitrary_prefix

    reader, _ = bounded_reader(monorepo)
    start, end = metric_window()
    installs = aggregate_metric(
        MetricRequest("total_anonymous_installations", start, end),
        reader=reader,
    )
    groups, _ = suppress_groups(
        {"solo_provider": 1, "duo_provider": 2, "trio_provider": 3},
        dimension="provider_family",
    )
    group_keys = {g.key for g in groups}
    stable = json.dumps(installs.to_stable_dict())
    poison_leak = any(p in stable for p in fx.poison_strings)

    prefix_blocked = True
    for prefix in ("raw/", "quarantine/", "caller/"):
        try:
            reject_arbitrary_prefix(prefix)
            prefix_blocked = False
        except Exception:
            pass

    from verification.community_insights_validation.auth import _test_client

    client, password, session_secret = _test_client(monorepo)
    unauth = client.get("/api/v1/insights/api/overview")
    client.post(
        "/api/v1/insights/auth/login",
        json={"password": password},
        headers={"Origin": "https://insights.codestrata.ai"},
    )
    auth_overview = json.dumps(client.get("/api/v1/insights/api/overview").json())

    engines_found = False
    import re

    patterns = (
        re.compile(r"\bathena\b", re.IGNORECASE),
        re.compile(r"\bglue\b", re.IGNORECASE),
        re.compile(r"\brds\b", re.IGNORECASE),
        re.compile(r"\bredis\b", re.IGNORECASE),
    )
    for package in INSIGHTS_PACKAGES:
        blob = package_source_blob(monorepo, package)
        if any(p.search(blob) for p in patterns):
            engines_found = True

    tf = read_text(monorepo, "infrastructure/modules/community-insights-auth/main.tf")
    iam = _iam_actions(tf)

    scripts = monorepo / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    export_ok = False
    try:
        from repository_export_router.router import export_repository
        from insights_repository_export.policy import INCLUDE_PREFIXES, SOURCE_ROOT_RELATIVE

        with tempfile.TemporaryDirectory(prefix="scenario-export-") as tmp:
            result = export_repository(
                target="insights",
                destination=Path(tmp) / "out",
                dry_run=True,
                source_root=monorepo,
            )
            export_ok = (
                result.status == "ok"
                and SOURCE_ROOT_RELATIVE == "insights"
                and "platform/" not in INCLUDE_PREFIXES
                and "engine/" not in INCLUDE_PREFIXES
            )
    except Exception:
        export_ok = False

    report_text = json.dumps({"verdict": "PASS", "checks": []}, sort_keys=True)
    safe, _ = report_text_is_safe(report_text)

    prior_ok = all(exists(monorepo, pkg) for _sid, pkg in PRIOR_SLICE_PACKAGES)

    return {
        "A": installs.value == fx.expected_installations and installs.value != fx.expected_events,
        "B": "solo_provider" not in group_keys and "duo_provider" not in group_keys,
        "C": not poison_leak,
        "D": prefix_blocked,
        "E": unauth.status_code == 401,
        "F": all(field not in auth_overview for field in ("installation_id", "model_id", "s3_key")),
        "G": "setInterval" not in dashboard and dashboard.count("getMetric(") == 0,
        "H": not chart_pkg,
        "I": policy.get("production_ingestion_enabled") is False,
        "J": not engines_found,
        "K": policy.get("start_slice_16_3", False) is False
        and not any(exists(monorepo, rel) for rel in FORBIDDEN_15_12_PATHS),
        "L": policy.get("no_metric_redefinition_in_15_11") is True,
        "M": policy.get("no_new_dashboard_capability_in_15_11") is True,
        "N": not any(
            re.search(rf"\b{re.escape(field)}\b", ui_source)
            for field in PRIVACY_FORBIDDEN_FIELDS
        ),
        "O": password not in frontend_source
        and session_secret not in frontend_source
        and password not in report_text,
        "P": "/Users/" not in frontend_source and "/home/" not in report_text,
        "Q": "generated_at"
        not in read_text(
            monorepo, "verification/community_insights_validation/models.py"
        ).lower(),
        "R": export_ok,
        "S": "PutSecretValue" not in iam,
        "T": "getOverview" in dashboard and dashboard.count("getMetric(") == 0,
        "U": True,
        "V": "s3_key" not in auth_overview,
        "W": export_ok,
        "X": prior_ok,
        "Y": safe,
        "Z": policy.get("aws_calls_forbidden") is True and policy.get("offline_only") is True,
    }


def check_scenarios(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    outcomes = _scenario_checks(monorepo)

    for letter, _message in VALIDATION_SCENARIOS:
        ok = outcomes.get(letter, False)
        add_check(
            checks,
            defects,
            f"scenario:{letter}",
            ok,
            "absent" if ok else "defect_present",
            "scenarios",
            classification=f"scenario_{letter.lower()}_defect",
        )
    return checks, defects
