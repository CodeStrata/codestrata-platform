"""Report publish eligibility matrix checks (updated Slice 18.7 journey)."""

from __future__ import annotations

from pathlib import Path

from verification.community_telemetry_consent.helpers import check, load_json, read_text
from verification.community_telemetry_consent.models import CheckResult, Defect


def check_report_publish(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    publishing = monorepo / "engine/src/codestrata/community_cloud/report_publishing.py"
    report_cli = monorepo / "engine/src/codestrata/cli/report.py"
    public_client = monorepo / "engine/src/codestrata/community_cloud/public_client_credential.py"
    policy = load_json(monorepo / "platform/policies/community_report_publishing_policy.json")

    text = read_text(publishing)
    cli = read_text(report_cli)
    checks.append(
        check(
            "report_publish:explicit_confirm",
            "confirm_public_publish" in text and "--confirm-public-publish" in cli,
            "explicit confirm required",
            "report_publish",
        )
    )
    checks.append(
        check(
            "report_publish:no_auto",
            policy.get("automatic_publish_after_assessment") is False,
            "policy forbids auto publish",
            "report_publish",
        )
    )
    checks.append(
        check(
            "report_publish:opt_in_not_required_policy",
            policy.get("telemetry_opt_in_required_for_cloud_publish") is False,
            "telemetry opt-in not required for cloud publish",
            "report_publish",
        )
    )
    checks.append(
        check(
            "report_publish:no_hidden_telemetry_env_gate",
            "CODESTRATA_TELEMETRY_OPT_IN" not in cli,
            "CLI publish does not require TELEMETRY_OPT_IN",
            "report_publish",
        )
    )
    checks.append(
        check(
            "report_publish:packaged_public_client",
            public_client.is_file()
            and "packaged_public_community_client_credential" in read_text(public_client),
            "packaged public client present",
            "report_publish",
        )
    )
    checks.append(
        check(
            "report_publish:interactive_prompt",
            "typer.confirm" in cli and "Publish report?" in cli,
            "interactive one-confirmation flow",
            "report_publish",
        )
    )
    try:
        from codestrata.community_cloud.report_publishing import telemetry_eligible_for_publish
        from codestrata.telemetry.consent import allow_session_consent, deny_session_consent
        from codestrata.telemetry.session import TelemetrySession

        off = telemetry_eligible_for_publish(
            TelemetrySession(consent=deny_session_consent())
        )
        on = telemetry_eligible_for_publish(
            TelemetrySession(consent=allow_session_consent())
        )
        # Publish eligibility is independent of telemetry session.
        checks.append(
            check(
                "report_publish:matrix_off_still_eligible",
                off is True,
                "telemetry OFF still publish-eligible",
                "report_publish",
            )
        )
        checks.append(
            check(
                "report_publish:matrix_on_eligible",
                on is True,
                "telemetry ON publish-eligible",
                "report_publish",
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(
            check("report_publish:matrix_off_still_eligible", False, type(exc).__name__, "report_publish")
        )
        checks.append(
            check("report_publish:matrix_on_eligible", False, type(exc).__name__, "report_publish")
        )

    failed = [c for c in checks if not c.ok]
    for item in failed:
        defects.append(
            Defect(
                classification="DEFECT",
                check_id=item.check_id,
                expected="pass",
                detail=item.detail,
            )
        )
    return checks, defects, {"report_publish_checks": len(checks)}
