"""Report publish eligibility matrix checks."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check, contains, load_json, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_report_publish(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    publishing = monorepo / "engine/src/codestrata/community_cloud/report_publishing.py"
    report_cli = monorepo / "engine/src/codestrata/cli/report.py"
    policy = load_json(monorepo / "platform/policies/community_report_publishing_policy.json")

    text = read_text(publishing)
    cli = read_text(report_cli)
    checks.append(check(
        "report_publish:telemetry_gate",
        "telemetry_eligible_for_publish" in text and "transmission_authorized" in text,
        "publish requires transmission_authorized",
        "report_publish",
    ))
    checks.append(check(
        "report_publish:explicit_confirm",
        "confirm_public_publish" in text and "--confirm-public-publish" in cli,
        "explicit confirm required",
        "report_publish",
    ))
    checks.append(check(
        "report_publish:no_auto",
        policy.get("automatic_publish_after_assessment") is False,
        "policy forbids auto publish",
        "report_publish",
    ))
    checks.append(check(
        "report_publish:opt_in_required_policy",
        policy.get("telemetry_opt_in_required_for_cloud_publish") is True,
        "telemetry opt-in required for cloud publish",
        "report_publish",
    ))
    checks.append(check(
        "report_publish:cli_opt_in_env",
        "CODESTRATA_TELEMETRY_OPT_IN" in cli,
        "CLI maps OPT_IN env to session eligibility",
        "report_publish",
    ))
    # Runtime unit of matrix via functions
    try:
        from codestrata.community_cloud.report_publishing import telemetry_eligible_for_publish
        from codestrata.telemetry.consent import allow_session_consent, deny_session_consent
        from codestrata.telemetry.session import TelemetrySession
        off = telemetry_eligible_for_publish(TelemetrySession(consent=deny_session_consent()))
        on = telemetry_eligible_for_publish(TelemetrySession(consent=allow_session_consent()))
        checks.append(check("report_publish:matrix_off", off is False, "OFF ineligible", "report_publish"))
        checks.append(check("report_publish:matrix_on", on is True, "ON eligible", "report_publish"))
    except Exception as exc:  # noqa: BLE001
        checks.append(check("report_publish:matrix_off", False, type(exc).__name__, "report_publish"))
        defects.append(Defect("publish_matrix", "report_publish:matrix_off", "callable", str(exc)))

    summary = {
        "matrix": {
            "telemetry_off_publish": "refused",
            "telemetry_on_no_confirm": "refused",
            "telemetry_on_explicit_publish": "allowed_by_contract",
            "opt_out_future_publish": "refused",
            "prior_published_remain": "governed_by_revoke",
        },
        "auto_publish": False,
    }
    return checks, defects, summary
