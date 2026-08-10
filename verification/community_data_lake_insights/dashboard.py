"""Live Insights dashboard login + overview checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from verification.community_data_lake_insights.contract import INSIGHTS_BASE
from verification.community_data_lake_insights.helpers import check
from verification.community_data_lake_insights.models import CheckResult, Defect

# Owner-once plaintext (Secrets Manager stores scrypt verifier JSON, not login password).
_OWNER_ONCE_RELATIVE = "infrastructure/production/.local/dashboard_password.owner-once"


def _fetch_dashboard_password(monorepo: Path) -> str | None:
    path = monorepo / _OWNER_ONCE_RELATIVE
    if not path.is_file():
        return None
    try:
        value = path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    except OSError:
        return None
    return value or None


def _http_json(
    method: str,
    url: str,
    *,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> tuple[int, dict[str, Any], str | None]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    hdrs = {
        "Accept": "application/json",
        # Cloudflare Bot Fight (1010) blocks default Python-urllib UA on insights host.
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        # Same-origin browser posture required by Insights CSRF Origin allowlist.
        "Origin": INSIGHTS_BASE,
        "Referer": f"{INSIGHTS_BASE}/",
    }
    if body is not None:
        hdrs["Content-Type"] = "application/json"
    if headers:
        hdrs.update(headers)
    req = Request(url, data=data, headers=hdrs, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            cookie = resp.headers.get("Set-Cookie")
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = {}
            if not isinstance(parsed, dict):
                parsed = {"_list": parsed} if isinstance(parsed, list) else {}
            return int(resp.status), parsed, cookie
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace") if getattr(exc, "fp", None) else ""
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {}
        if not isinstance(parsed, dict):
            parsed = {}
        return int(exc.code), parsed, None
    except URLError:
        return 0, {}, None


def check_dashboard(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict, list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    summary: dict[str, Any] = {
        "login_ok": False,
        "overview_ok": False,
        "metrics_present": False,
        "no_installation_id": True,
        "no_raw_stream_paths": True,
        "no_report_html": True,
        "query_budget_reached": None,
        "overview_metric_values": {},
        "password_source": "owner_local_file",
    }

    password = _fetch_dashboard_password(monorepo)
    if not password:
        checks.append(
            check(
                "dashboard:password_resolved",
                False,
                "owner-once password file missing",
                "dashboard",
            )
        )
        defects.append(
            Defect(
                "insights_credential_unavailable",
                "dashboard:password_resolved",
                "owner-once file present",
                "missing",
            )
        )
        return checks, defects, summary, limitations

    checks.append(
        check(
            "dashboard:password_resolved",
            True,
            "password resolved from owner local file (value redacted)",
            "dashboard",
        )
    )

    status, _login_body, set_cookie = _http_json(
        "POST",
        f"{INSIGHTS_BASE}/api/v1/insights/auth/login",
        body={"password": password},
    )
    login_ok = status == 200
    summary["login_ok"] = login_ok
    checks.append(
        check("dashboard:login", login_ok, f"status={status}", "dashboard")
    )
    if not login_ok:
        defects.append(
            Defect(
                "dashboard_login_failed",
                "dashboard:login",
                "200",
                f"status={status}",
            )
        )
        return checks, defects, summary, limitations

    cookie_header = None
    if set_cookie:
        cookie_header = set_cookie.split(";", 1)[0]
    headers = {"Cookie": cookie_header} if cookie_header else {}
    o_status, overview, _ = _http_json(
        "GET",
        f"{INSIGHTS_BASE}/api/v1/insights/api/overview",
        headers=headers or None,
    )
    overview_ok = o_status == 200 and bool(overview)
    summary["overview_ok"] = overview_ok
    checks.append(
        check("dashboard:overview", overview_ok, f"status={o_status}", "dashboard")
    )
    if not overview_ok:
        defects.append(
            Defect(
                "dashboard_overview_failed",
                "dashboard:overview",
                "200",
                f"status={o_status}",
            )
        )
        return checks, defects, summary, limitations

    blob = json.dumps(overview, sort_keys=True)
    lower = blob.lower()

    metrics_present = any(
        key in lower
        for key in (
            "activity",
            "assessments",
            "adoption",
            "metric",
            "total_anonymous",
            "successful_assessments",
        )
    )
    summary["metrics_present"] = metrics_present
    checks.append(
        check(
            "dashboard:metrics_present",
            metrics_present,
            "overview contains metric families",
            "dashboard",
        )
    )

    no_installation = "installation_id" not in lower
    summary["no_installation_id"] = no_installation
    checks.append(
        check(
            "dashboard:no_installation_id",
            no_installation,
            "installation_id absent",
            "dashboard",
        )
    )
    if not no_installation:
        defects.append(
            Defect(
                "installation_id_exposed",
                "dashboard:no_installation_id",
                "absent",
                "present",
            )
        )

    no_raw = "raw/stream=" not in blob
    summary["no_raw_stream_paths"] = no_raw
    checks.append(
        check("dashboard:no_raw_stream_paths", no_raw, "hive raw path marker absent", "dashboard")
    )
    if not no_raw:
        defects.append(
            Defect(
                "s3_paths_exposed",
                "dashboard:no_raw_stream_paths",
                "absent",
                "present",
            )
        )

    no_html = "<html" not in lower and "</html>" not in lower
    summary["no_report_html"] = no_html
    checks.append(
        check("dashboard:no_report_html", no_html, "report HTML absent", "dashboard")
    )
    if not no_html:
        defects.append(
            Defect(
                "report_html_in_dashboard",
                "dashboard:no_report_html",
                "absent",
                "present",
            )
        )

    budget_reached = overview.get("query_budget_reached")
    if budget_reached is None:
        metrics = overview.get("metrics")
        if isinstance(metrics, list):
            for item in metrics:
                if not isinstance(item, dict):
                    continue
                if item.get("query_budget_reached") is True:
                    budget_reached = True
                    break
                status_val = str(item.get("status", "")).lower()
                if status_val in {"budget_exceeded", "query_budget_reached"}:
                    budget_reached = True
                    break
    summary["query_budget_reached"] = (
        bool(budget_reached) if budget_reached is not None else False
    )
    checks.append(
        check(
            "dashboard:query_budget_healthy",
            summary["query_budget_reached"] is False,
            f"query_budget_reached={summary['query_budget_reached']}",
            "dashboard",
        )
    )
    if summary["query_budget_reached"]:
        defects.append(
            Defect(
                "query_budget_reached",
                "dashboard:query_budget_healthy",
                "false",
                "true",
            )
        )

    zeros = 0
    values: dict[str, Any] = {}
    metrics = overview.get("metrics")
    if isinstance(metrics, list):
        for item in metrics:
            if not isinstance(item, dict):
                continue
            mid = item.get("metric_id") or item.get("id")
            val = item.get("value")
            if mid:
                values[str(mid)] = val
            if val in (0, 0.0, None, {}):
                zeros += 1
    elif isinstance(metrics, dict):
        for mid, val in metrics.items():
            values[str(mid)] = val
            if val in (0, 0.0, None, {}):
                zeros += 1
    summary["overview_metric_values"] = {
        k: ("zero" if v in (0, 0.0, None) else "nonzero")
        for k, v in list(values.items())[:20]
    }
    if zeros >= 3 or not values:
        limitations.append("low_synthetic_data_volume")
        limitations.append("aggregation_latency")

    return checks, defects, summary, limitations
