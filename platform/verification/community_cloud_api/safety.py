"""Privacy / secret safety scans for SV.7 artifacts."""

from __future__ import annotations

import re

from verification.community_cloud_api.app_factory import VerificationApp
from verification.community_cloud_api.contract import (
    FORBIDDEN_REPORT_FRAGMENTS,
    INGESTION_PATHS,
    TEST_CLI_TOKEN,
)
from verification.community_cloud_api.credentials import auth_headers
from verification.community_cloud_api.models import CheckResult
from verification.community_cloud_api.requests import body_for

_PATTERNS = (
    ("aws_key", r"AKIA[0-9A-Z]{16}"),
    ("private_key", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ("file_url", r"file://[/\w]"),
    ("home_path", r"(?<![\w.-])/Users/[\w.-]+"),
)


def check_safety(app: VerificationApp, report_text: str = "") -> list[CheckResult]:
    responses: list[str] = []
    health = app.client.get("/api/v1/health")
    responses.append(health.text)
    responses.extend(f"{k}:{v}" for k, v in health.headers.items())
    ingest = app.client.post(
        INGESTION_PATHS["telemetry"],
        json=body_for("telemetry", event_id="sv7-safe-1"),
        headers=auth_headers(),
    )
    responses.append(ingest.text)
    responses.extend(f"{k}:{v}" for k, v in ingest.headers.items())

    logs = "".join(app.log_sink.lines)
    blob = "\n".join(responses) + "\n" + logs + "\n" + report_text

    hits = [frag for frag in FORBIDDEN_REPORT_FRAGMENTS if frag in blob and frag != "Bearer cscc_v1_"]
    # Authorization header key in responses would be bad; WWW-Authenticate Bearer is ok.
    if TEST_CLI_TOKEN in blob:
        hits.append("test_credential")

    pattern_hits = [name for name, pat in _PATTERNS if re.search(pat, blob)]
    return [
        CheckResult(
            name="safety:no_credentials_or_secrets",
            ok=not hits and not pattern_hits,
            detail=f"hits={hits} patterns={pattern_hits}" if hits or pattern_hits else "ok",
            category="safety",
        ),
        CheckResult(
            name="safety:no_installation_id_echo",
            ok="installation_id" not in ingest.text.lower(),
            detail="response excludes installation_id",
            category="safety",
        ),
    ]
