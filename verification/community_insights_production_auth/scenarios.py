"""Negative scenarios A–Z for Slice 17.24."""

from __future__ import annotations

from verification.community_insights_production_auth.helpers import check, hard_defect
from verification.community_insights_production_auth.models import CheckResult, Defect


def check_scenarios(*, flags: dict[str, bool]) -> tuple[list[CheckResult], list[Defect], dict[str, bool]]:
    """Each scenario passes when the corresponding negative condition is absent."""

    scenarios = [
        ("A", "production auth policy missing or invalid", flags.get("policy_ok", False)),
        ("B", "register missing resolved auth defects", flags.get("register_ok", False)),
        ("C", "password secret id authority drift", flags.get("secret_authority", False)),
        ("D", "normalize_password absent", flags.get("normalize_password", False)),
        ("E", "AwsSecretsPort not pinned to AWSCURRENT", flags.get("aws_current", False)),
        ("F", "session secret cache TTL not 300s", flags.get("session_ttl_300", False)),
        ("G", "Insights auth codes remapped via _SAFE_PUBLIC_MESSAGES gap", flags.get("safe_messages", False)),
        ("H", "cookie Path not / in policy or defaults", flags.get("cookie_path_root", False)),
        ("I", "AuthContext conflates auth failures to Invalid password", flags.get("distinct_errors", False)),
        ("J", "authClient missing failure code mapping", flags.get("auth_client_codes", False)),
        ("K", "rotation doc missing normalization or plaintext guidance", flags.get("rotation_doc", False)),
        ("L", "live matrix owner_matches_awscurrent false when present", flags.get("live_owner_ok", True)),
        ("M", "live wrong_password not 401 when matrix present", flags.get("live_wrong_pw", True)),
        ("N", "live wrong_password_error_code not invalid_credentials", flags.get("live_wrong_code", True)),
        ("O", "live cookie attrs insecure when matrix present", flags.get("live_cookie_ok", True)),
        ("P", "prior slice 17.23 package absent", flags.get("prior_17_23", False)),
        ("Q", "start_slice_17_24 false in policy", flags.get("start_17_24", False)),
        ("R", "start_slice_17_25 true in policy", flags.get("no_17_25_flag", False)),
        ("S", "Slice 17.25 verification package present", flags.get("no_17_25_pkg", False)),
        ("T", "marketplace publish started", flags.get("no_marketplace", False)),
        ("U", "password verifier cached in Lambda", flags.get("password_not_cached", False)),
        ("V", "SM JSON accepted as login password (live)", flags.get("live_sm_json", True)),
        ("W", "insights policy mirror absent", flags.get("insights_mirror", False)),
        ("X", "live login matrix absent (soft)", flags.get("live_present_or_soft", True)),
        ("Y", "Slice 17.25 starts", flags.get("no_17_25", False)),
        ("Z", "verifier nondeterministic or report leaks secrets", flags.get("deterministic", False)),
    ]
    soft_letters = frozenset({"X", "N"})
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    results: dict[str, bool] = {}
    for letter, label, ok in scenarios:
        results[letter] = bool(ok)
        checks.append(check(f"scenario:{letter}", bool(ok), label, "scenarios"))
        if not ok and letter not in soft_letters:
            defects.append(hard_defect("scenario", f"scenario:{letter}", "pass", label))
    return checks, defects, results
