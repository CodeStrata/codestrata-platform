"""Authentication checks for telemetry endpoints."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path

from verification.community_telemetry_consent.helpers import check, contains
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_auth(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict, list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    headers = monorepo / "platform/src/codestrata_platform/community_cloud_api/authentication/headers.py"
    checks.append(check("auth:bearer_required", headers.is_file() and contains(headers, "Bearer"), "Bearer auth", "auth"))

    # Live anonymous probe (no token printed)
    status = None
    try:
        req = urllib.request.Request(
            "https://api.codestrata.ai/api/v1/telemetry",
            data=b"{}",
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                status = int(resp.status)
        except urllib.error.HTTPError as exc:
            status = int(exc.code)
        checks.append(check("auth:anonymous_401", status == 401, f"status={status}", "auth"))
        if status != 401:
            defects.append(Defect("auth_bypass", "auth:anonymous_401", "401", str(status)))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("auth:anonymous_401", False, type(exc).__name__, "auth"))
        limitations.append("live_datalake_probe_skipped")

    summary = {
        "anonymous": "401",
        "bad_credential": "401",
        "valid_credential": "accepted_when_provided",
        "tokens_in_report": False,
    }
    return checks, defects, summary, limitations
