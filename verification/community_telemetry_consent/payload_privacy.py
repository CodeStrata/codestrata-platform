"""Payload privacy gate checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check, contains, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect

FORBIDDEN_MARKERS = (
    "source_code",
    "file_contents",
    "absolute_path",
    "assessment.html",
    "findings",
    "prompt",
    "api_key",
    "machineId",
)


def check_payload_privacy(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    pre = monorepo / "engine/src/codestrata/telemetry/pre_transport_policy.py"
    constants = monorepo / "engine/src/codestrata/telemetry/constants.py"
    sanitizer = monorepo / "platform/src/codestrata_platform/community_cloud_api/reports/sanitizer.py"
    checks.append(check("payload:pre_transport_policy", pre.is_file(), "pre-transport privacy policy", "payload_privacy"))
    if constants.is_file():
        ctext = read_text(constants)
        checks.append(check(
            "payload:forbidden_substrings",
            "FORBIDDEN" in ctext or "forbidden" in ctext.lower(),
            "forbidden substring guards present",
            "payload_privacy",
        ))
    docs = monorepo / "docs/security/privacy.md"
    dtext = read_text(docs)
    checks.append(check(
        "payload:docs_never_collected",
        "Never collected" in dtext or "never collected" in dtext.lower(),
        "privacy docs list never-collected fields",
        "payload_privacy",
    ))
    for marker in ("Source code", "credentials", "prompts"):
        checks.append(check(
            f"payload:docs_forbids_{marker.split()[0].lower()}",
            marker.lower() in dtext.lower(),
            f"docs mention {marker}",
            "payload_privacy",
        ))
    # report publishing path sanitizer separate from telemetry
    checks.append(check("payload:report_sanitizer_exists", sanitizer.is_file(), "report sanitizer module", "payload_privacy"))
    summary = {
        "forbidden_categories": [
            "source_code",
            "repo_file_contents",
            "local_absolute_paths",
            "findings_evidence",
            "assessment_html_json",
            "eir_content",
            "prompts_responses",
            "credentials",
            "git_userinfo",
            "vscode_machine_id",
        ],
        "broadened_fields": False,
    }
    return checks, defects, summary
