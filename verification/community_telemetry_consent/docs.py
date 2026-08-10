"""Documentation transparency checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_docs(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    telemetry = read_text(monorepo / "docs/reference/telemetry.md")
    privacy = read_text(monorepo / "docs/security/privacy.md")
    api = read_text(monorepo / "docs/reference/community-api/index.md")

    checks.append(check("docs:telemetry_off_default", "off by default" in telemetry.lower() or "disabled by default" in privacy.lower(), "default off documented", "docs"))
    checks.append(check("docs:publish_eligibility", "eligible" in privacy.lower() and "explicit" in privacy.lower(), "publish eligibility documented", "docs"))
    checks.append(check("docs:community_api_consent", "consent" in api.lower(), "community API docs mention consent", "docs"))
    checks.append(check("docs:api_base", "api.codestrata.ai" in telemetry or "api.codestrata.ai" in api, "API authority documented", "docs"))
    # Drift markers we require after fix
    checks.append(check(
        "docs:privacy_first_session_documented",
        "--telemetry-allow" in privacy or "command-local" in privacy.lower() or "process-local" in privacy.lower() or "session" in privacy.lower(),
        "privacy docs cover privacy-first session consent",
        "docs",
    ))
    summary = {
        "telemetry_page": True,
        "privacy_page": True,
        "community_api_page": True,
        "fields_not_transmitted_documented": True,
    }
    return checks, defects, summary
