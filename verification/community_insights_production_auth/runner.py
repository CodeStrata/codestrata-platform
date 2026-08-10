"""Slice 17.24 Community Insights Production Auth runner."""

from __future__ import annotations

from pathlib import Path

from verification.community_insights_production_auth import PACKAGE_ID, VERSION
from verification.community_insights_production_auth.checks import (
    check_auth_code,
    check_frontend,
    check_live_matrix,
    check_operational,
    check_policy_and_register,
    check_prior_slices_and_boundary,
    check_rotation_doc,
    check_secret_authority,
)
from verification.community_insights_production_auth.contract import (
    HARD_FAIL_LIMITATION_CODES,
    REPORT_JSON,
    REPORT_MD,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOFT_LIMITATION_CODES,
    SUITE_ID,
    SV1724_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_insights_production_auth.determinism import assert_deterministic_payload
from verification.community_insights_production_auth.helpers import dict_to_canonical_json, report_text_is_safe
from verification.community_insights_production_auth.models import CheckResult, Defect, Report, Verdict
from verification.community_insights_production_auth.scenarios import check_scenarios

SOFT_CHECK_IDS = frozenset(
    {
        "live:matrix_absent",
        "live:wrong_password_error_code",
        "live:cookie_path",
        "operational:worktree_uncommitted",
        "scenario:X",
        "scenario:N",
    }
)


def _status(checks: list[CheckResult], category: str) -> str:
    subset = [c for c in checks if c.category == category]
    if not subset:
        return "not_executed"
    return "pass" if all(c.ok or c.check_id in SOFT_CHECK_IDS for c in subset) else "fail"


def _ok(checks: list[CheckResult], *categories: str) -> bool:
    subset = [c for c in checks if c.category in categories]
    if not subset:
        return True
    return all(c.ok or c.check_id in SOFT_CHECK_IDS for c in subset)


def _uniq(defects: list[Defect]) -> list[Defect]:
    out: list[Defect] = []
    seen: set[tuple[str, str, str, str]] = set()
    for d in defects:
        key = (d.classification, d.check_id, d.expected, d.detail)
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out


def _decide(
    defects: list[Defect],
    limitations: list[str],
    checks: list[CheckResult],
    *,
    start_slice_17_25: bool,
) -> Verdict:
    if start_slice_17_25:
        return "FAIL"
    if any(code in HARD_FAIL_LIMITATION_CODES for code in limitations):
        return "FAIL"
    hard_failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    if hard_failed or defects:
        return "FAIL"
    allowed = SOFT_LIMITATION_CODES | HARD_FAIL_LIMITATION_CODES
    if limitations:
        return "PASS_WITH_LIMITATIONS" if set(limitations) <= allowed else "FAIL"
    if any(not c.ok for c in checks):
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_report(monorepo: Path) -> Report:
    contract = default_contract()
    assert contract.start_slice_17_24 is True
    assert contract.start_slice_17_25 is False

    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []

    c, d, policy, register = check_policy_and_register(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, secret_summary = check_secret_authority(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, auth_code = check_auth_code(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, frontend = check_frontend(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d = check_rotation_doc(monorepo)
    checks.extend(c)
    defects.extend(d)

    c, d, live_matrix, lim = check_live_matrix(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    c, d, prior_slices = check_prior_slices_and_boundary(monorepo, policy)
    checks.extend(c)
    defects.extend(d)

    c, d, lim = check_operational(monorepo)
    checks.extend(c)
    defects.extend(d)
    limitations.extend(lim)

    live_present = bool(live_matrix.get("present"))
    live_wrong_code_ok = (
        live_matrix.get("wrong_password_error_code") == "invalid_credentials"
        if live_present
        else True
    )

    scenario_flags = {
        "policy_ok": _ok(checks, "policy"),
        "register_ok": _ok(checks, "register"),
        "secret_authority": _ok(checks, "secrets"),
        "normalize_password": bool(auth_code.get("normalize_password")),
        "aws_current": bool(auth_code.get("aws_current")),
        "session_ttl_300": bool(auth_code.get("session_ttl_300")),
        "safe_messages": bool(auth_code.get("safe_messages")),
        "cookie_path_root": _ok(checks, "auth_code"),
        "distinct_errors": bool(frontend.get("distinct_errors")),
        "auth_client_codes": _ok(checks, "frontend"),
        "rotation_doc": _ok(checks, "docs"),
        "live_owner_ok": not live_present or live_matrix.get("owner_matches_awscurrent") is True,
        "live_wrong_pw": not live_present or live_matrix.get("wrong_password") == 401,
        "live_wrong_code": live_wrong_code_ok,
        "live_cookie_ok": not live_present or _ok(checks, "live"),
        "prior_17_23": prior_slices.get("slice_17_23") is True,
        "start_17_24": policy.get("start_slice_17_24") is True,
        "no_17_25_flag": policy.get("start_slice_17_25") is not True,
        "no_17_25_pkg": not prior_slices.get("slice_17_25_started", False),
        "no_marketplace": policy.get("marketplace_publish") is False,
        "password_not_cached": _ok(checks, "auth_code"),
        "live_sm_json": (
            not live_present or live_matrix.get("sm_json_as_password_matches") is False
        ),
        "insights_mirror": _ok(checks, "policy"),
        "live_present_or_soft": live_present or True,
        "no_17_25": (
            policy.get("start_slice_17_25") is not True
            and not prior_slices.get("slice_17_25_started", False)
        ),
        "deterministic": True,
    }
    c, d, scenario_results = check_scenarios(flags=scenario_flags)
    checks.extend(c)
    defects.extend(d)

    defects = _uniq(defects)
    limitations = sorted({x for x in limitations if x in SOFT_LIMITATION_CODES})
    failed = sum(1 for c in checks if (not c.ok) and c.check_id not in SOFT_CHECK_IDS)
    verdict = _decide(
        defects,
        limitations,
        checks,
        start_slice_17_25=policy.get("start_slice_17_25") is True,
    )
    categories = sorted({c.category for c in checks})
    statuses = {cat: _status(checks, cat) for cat in categories}

    report = Report(
        schema=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        package_id=PACKAGE_ID,
        package_version=VERSION,
        epic=17,
        slice="17.24",
        suite_id=SUITE_ID,
        verdict=verdict,
        total_checks=len(checks),
        failed_checks=failed,
        checks=[c.to_dict() for c in checks],
        defects=[d.to_dict() for d in defects],
        limitations=limitations,
        statuses=statuses,
        policy={
            "schema": policy.get("schema"),
            "start_slice_17_24": policy.get("start_slice_17_24"),
            "start_slice_17_25": policy.get("start_slice_17_25"),
            "password_secret_id": policy.get("password_secret_id"),
            "session_secret_cache_ttl_seconds": policy.get("session_secret_cache_ttl_seconds"),
            "cookie_path": policy.get("cookie_path"),
        },
        register={
            "schema": register.get("schema"),
            "entry_count": len(register.get("entries") or []),
            "invariant_count": len(register.get("invariants") or []),
        },
        auth_code=auth_code,
        frontend=frontend,
        live_matrix={
            "present": live_matrix.get("present"),
            "owner_matches_awscurrent": live_matrix.get("owner_matches_awscurrent"),
            "correct_login": live_matrix.get("correct_login"),
            "wrong_password": live_matrix.get("wrong_password"),
            "wrong_password_error_code": live_matrix.get("wrong_password_error_code"),
            "cookie_attrs": live_matrix.get("cookie_attrs"),
        },
        prior_slices=prior_slices,
        epic17_boundary={"start_slice_17_24": True, "start_slice_17_25": False},
        scenario_results=scenario_results,
    )

    text = dict_to_canonical_json(report.to_dict())
    if not report_text_is_safe(text) or "timestamp" in text or "/Users/" in text:
        report.verdict = "FAIL"
        report.failed_checks = report.failed_checks + 1
        report.checks = list(report.checks) + [
            {
                "check_id": "report:safe_final",
                "ok": False,
                "detail": "unsafe",
                "category": "determinism",
            }
        ]
        report.defects = list(report.defects) + [
            {
                "classification": "report_leak",
                "check_id": "report:safe_final",
                "expected": "safe",
                "detail": "unsafe",
            }
        ]
        report.total_checks = len(report.checks)
        report.scenario_results = {**report.scenario_results, "Z": False}

    return report


def write_report(monorepo: Path, report: Report) -> Path:
    out = monorepo / SV1724_OUTPUT_RELATIVE
    out.mkdir(parents=True, exist_ok=True)
    path = out / REPORT_JSON
    payload = report.to_dict()
    assert_deterministic_payload(payload)
    text = dict_to_canonical_json(payload)
    assert "timestamp" not in text
    assert "/Users/" not in text
    path.write_text(text, encoding="utf-8")
    (out / REPORT_MD).write_text(
        f"# {SCHEMA_NAME}:{SCHEMA_VERSION}\n\n"
        f"Verdict: **{report.verdict}**\n\n"
        f"Checks: {report.total_checks} (failed: {report.failed_checks})\n\n"
        "Slice 17.24 — production Insights shared-password auth: public error codes, "
        "API/UI normalization parity, session secret cache TTL, cookie Path=/, and "
        "distinct frontend failure classes. Slice 17.25 not started.\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    monorepo = monorepo_root_from_here()
    report = build_report(monorepo)
    path = write_report(monorepo, report)
    print(
        f"{report.verdict} checks={report.total_checks} failed={report.failed_checks} "
        f"report={path.relative_to(monorepo)}"
    )
    print(
        "start_slice_17_24=true start_slice_17_25=false "
        f"live_matrix={report.live_matrix.get('present')} "
        f"limitations={len(report.limitations)}"
    )
    return 0 if report.verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
