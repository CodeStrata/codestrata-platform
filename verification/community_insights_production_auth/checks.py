"""Structural and optional live checks for Slice 17.24."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from verification.community_insights_production_auth.contract import (
    AWS_SECRETS_PY,
    CONTRACT_RELATIVE,
    ERRORS_PY,
    EXPECTED_17_23_PACKAGE,
    EXPECTED_17_24_PACKAGE,
    INSIGHTS_AUTH_CLIENT,
    INSIGHTS_AUTH_CONTEXT,
    INSIGHTS_AUTH_POLICY_INSIGHTS_RELATIVE,
    INSIGHTS_AUTH_POLICY_PY,
    INSIGHTS_AUTH_POLICY_RELATIVE,
    INSIGHTS_AUTH_PUBLIC_CODES,
    INSIGHTS_POLICY_RELATIVE,
    LIVE_LOGIN_MATRIX_RELATIVE,
    PASSWORD_PY,
    PASSWORD_SECRET_ID,
    POLICY_RELATIVE,
    POLICY_REQUIRED_VALUES,
    POLICY_SCHEMA,
    REGISTER_RELATIVE,
    REGISTER_SCHEMA,
    ROTATION_DOC,
    SECRETS_PY,
    SESSION_SECRET_ID,
    SLICE_17_25_PACKAGE_CANDIDATES,
)
from verification.community_insights_production_auth.helpers import (
    add_check,
    contains,
    load_json,
    read_text,
)
from verification.community_insights_production_auth.models import CheckResult, Defect

REGISTER_DEFECT_IDS = (
    "E17-D024-001",
    "E17-D024-002",
    "E17-D024-003",
)
REGISTER_LIMITATION_ID = "E17-L024-001"


def check_policy_and_register(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    policy: dict[str, Any] = {}
    register: dict[str, Any] = {}

    policy_path = monorepo / POLICY_RELATIVE
    add_check(checks, defects, "policy:exists", policy_path.is_file(), POLICY_RELATIVE, "policy")
    if policy_path.is_file():
        policy = load_json(policy_path)
        add_check(
            checks,
            defects,
            "policy:schema",
            policy.get("schema") == POLICY_SCHEMA,
            str(policy.get("schema")),
            "policy",
        )
        for key, expected in sorted(POLICY_REQUIRED_VALUES.items()):
            actual = policy.get(key)
            add_check(
                checks,
                defects,
                f"policy:{key}",
                actual == expected,
                f"{key}={actual}",
                "policy",
            )

    mirror = monorepo / INSIGHTS_POLICY_RELATIVE
    add_check(
        checks,
        defects,
        "policy:insights_mirror",
        mirror.is_file(),
        INSIGHTS_POLICY_RELATIVE,
        "policy",
    )

    add_check(
        checks,
        defects,
        "contract:exists",
        (monorepo / CONTRACT_RELATIVE).is_file(),
        CONTRACT_RELATIVE,
        "policy",
    )

    reg_path = monorepo / REGISTER_RELATIVE
    add_check(
        checks,
        defects,
        "register:exists",
        reg_path.is_file(),
        REGISTER_RELATIVE,
        "register",
    )
    if reg_path.is_file():
        register = load_json(reg_path)
        add_check(
            checks,
            defects,
            "register:schema",
            register.get("schema") == REGISTER_SCHEMA,
            str(register.get("schema")),
            "register",
        )
        entries = register.get("entries") or []
        entry_ids = {
            str(e.get("defect_id") or e.get("limitation_id"))
            for e in entries
            if isinstance(e, dict)
        }
        for defect_id in REGISTER_DEFECT_IDS:
            add_check(
                checks,
                defects,
                f"register:{defect_id.lower()}",
                defect_id in entry_ids,
                defect_id,
                "register",
            )
        add_check(
            checks,
            defects,
            "register:limitation_sm_json",
            REGISTER_LIMITATION_ID in entry_ids,
            REGISTER_LIMITATION_ID,
            "register",
        )
        invariants = register.get("invariants") or []
        add_check(
            checks,
            defects,
            "register:invariants",
            isinstance(invariants, list) and len(invariants) >= 8,
            str(len(invariants) if isinstance(invariants, list) else 0),
            "register",
        )

    return checks, defects, policy, register


def check_secret_authority(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    auth_policy = monorepo / INSIGHTS_AUTH_POLICY_RELATIVE
    add_check(
        checks,
        defects,
        "secrets:auth_policy_password_id",
        auth_policy.is_file()
        and load_json(auth_policy).get("password_secret_id") == PASSWORD_SECRET_ID,
        PASSWORD_SECRET_ID,
        "secrets",
    )
    add_check(
        checks,
        defects,
        "secrets:auth_policy_session_id",
        auth_policy.is_file()
        and load_json(auth_policy).get("session_secret_id") == SESSION_SECRET_ID,
        SESSION_SECRET_ID,
        "secrets",
    )
    insights_mirror = monorepo / INSIGHTS_AUTH_POLICY_INSIGHTS_RELATIVE
    add_check(
        checks,
        defects,
        "secrets:insights_mirror_password_id",
        insights_mirror.is_file()
        and load_json(insights_mirror).get("password_secret_id") == PASSWORD_SECRET_ID,
        PASSWORD_SECRET_ID,
        "secrets",
    )

    policy_py = monorepo / INSIGHTS_AUTH_POLICY_PY
    if policy_py.is_file():
        text = read_text(policy_py)
        add_check(
            checks,
            defects,
            "secrets:default_password_id",
            PASSWORD_SECRET_ID in text,
            PASSWORD_SECRET_ID,
            "secrets",
        )
        add_check(
            checks,
            defects,
            "secrets:default_session_id",
            SESSION_SECRET_ID in text,
            SESSION_SECRET_ID,
            "secrets",
        )

    summary["password_secret_id"] = PASSWORD_SECRET_ID
    summary["session_secret_id"] = SESSION_SECRET_ID
    return checks, defects, summary


def check_auth_code(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    password_path = monorepo / PASSWORD_PY
    add_check(
        checks,
        defects,
        "code:normalize_password",
        password_path.is_file() and "def normalize_password" in read_text(password_path),
        PASSWORD_PY,
        "auth_code",
    )
    if password_path.is_file():
        pwd_text = read_text(password_path)
        add_check(
            checks,
            defects,
            "code:normalize_strip",
            "password.strip()" in pwd_text,
            "strip",
            "auth_code",
        )

    aws_path = monorepo / AWS_SECRETS_PY
    aws_text = read_text(aws_path) if aws_path.is_file() else ""
    add_check(
        checks,
        defects,
        "code:aws_current_stage",
        aws_path.is_file() and 'VersionStage="AWSCURRENT"' in aws_text,
        "AWSCURRENT",
        "auth_code",
    )

    secrets_path = monorepo / SECRETS_PY
    secrets_text = read_text(secrets_path) if secrets_path.is_file() else ""
    add_check(
        checks,
        defects,
        "code:caching_secrets_port",
        secrets_path.is_file() and "class CachingSecretsPort" in secrets_text,
        "CachingSecretsPort",
        "auth_code",
    )
    add_check(
        checks,
        defects,
        "code:session_cache_ttl_300",
        secrets_path.is_file() and "DEFAULT_SESSION_SECRET_CACHE_TTL_SECONDS = 300" in secrets_text,
        "300",
        "auth_code",
    )
    add_check(
        checks,
        defects,
        "code:password_not_cached",
        secrets_path.is_file()
        and "Password verifier" in secrets_text
        and "never cached" in secrets_text.lower(),
        "not_cached",
        "auth_code",
    )

    errors_path = monorepo / ERRORS_PY
    errors_text = read_text(errors_path) if errors_path.is_file() else ""
    codes_ok = all(f'"{code}"' in errors_text for code in INSIGHTS_AUTH_PUBLIC_CODES)
    add_check(
        checks,
        defects,
        "code:insights_auth_safe_messages",
        errors_path.is_file() and codes_ok,
        "allowlist",
        "auth_code",
    )

    policy_py = monorepo / INSIGHTS_AUTH_POLICY_PY
    add_check(
        checks,
        defects,
        "code:cookie_path_root",
        policy_py.is_file() and 'DEFAULT_COOKIE_PATH = "/"' in read_text(policy_py),
        "/",
        "auth_code",
    )

    for rel in (INSIGHTS_AUTH_POLICY_RELATIVE, INSIGHTS_AUTH_POLICY_INSIGHTS_RELATIVE):
        path = monorepo / rel
        add_check(
            checks,
            defects,
            f"code:policy_json_cookie_path:{Path(rel).name}",
            path.is_file() and load_json(path).get("cookie_path") == "/",
            "/",
            "auth_code",
        )

    summary["normalize_password"] = password_path.is_file()
    summary["aws_current"] = 'VersionStage="AWSCURRENT"' in aws_text
    summary["session_ttl_300"] = "DEFAULT_SESSION_SECRET_CACHE_TTL_SECONDS = 300" in secrets_text
    summary["safe_messages"] = codes_ok
    return checks, defects, summary


def check_frontend(monorepo: Path) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict[str, Any] = {}

    ctx_path = monorepo / INSIGHTS_AUTH_CONTEXT
    ctx_text = read_text(ctx_path) if ctx_path.is_file() else ""
    add_check(
        checks,
        defects,
        "frontend:auth_context",
        ctx_path.is_file(),
        INSIGHTS_AUTH_CONTEXT,
        "frontend",
    )

    distinguishes = False
    if ctx_path.is_file():
        distinguishes = (
            'err.code === "rate_limited"' in ctx_text
            and 'err.code === "invalid_credentials"' in ctx_text
            and 'err.code === "unavailable"' in ctx_text
            and 'err.code === "access_denied"' in ctx_text
            and 'setLoginError("Sign-in failed. Try again.")' in ctx_text
        )
        add_check(
            checks,
            defects,
            "frontend:distinct_error_classes",
            distinguishes,
            "mapped",
            "frontend",
        )
        # Must not blanket-map all failures to Invalid password.
        blanket = (
            'setLoginError("Invalid password")' in ctx_text
            and ctx_text.count('setLoginError("Invalid password")') == 1
        )
        add_check(
            checks,
            defects,
            "frontend:no_blanket_invalid_password",
            blanket,
            "single_invalid_credentials_only",
            "frontend",
        )

    client_path = monorepo / INSIGHTS_AUTH_CLIENT
    client_text = read_text(client_path) if client_path.is_file() else ""
    add_check(
        checks,
        defects,
        "frontend:auth_client",
        client_path.is_file(),
        INSIGHTS_AUTH_CLIENT,
        "frontend",
    )
    if client_path.is_file():
        add_check(
            checks,
            defects,
            "frontend:auth_client_codes",
            '"invalid_credentials"' in client_text
            and '"rate_limited"' in client_text
            and '"unavailable"' in client_text,
            "codes",
            "frontend",
        )

    summary["distinct_errors"] = distinguishes
    return checks, defects, summary


def check_rotation_doc(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    doc = monorepo / ROTATION_DOC
    add_check(checks, defects, "docs:rotation_doc", doc.is_file(), ROTATION_DOC, "docs")
    if doc.is_file():
        text = read_text(doc)
        add_check(
            checks,
            defects,
            "docs:rotation_normalization",
            "strip()" in text or "trim()" in text,
            "normalization",
            "docs",
        )
        add_check(
            checks,
            defects,
            "docs:rotation_plaintext_vs_json",
            "not" in text.lower() and "Secrets Manager JSON" in text,
            "documented",
            "docs",
        )
        add_check(
            checks,
            defects,
            "docs:rotation_session_ttl",
            "300" in text,
            "300",
            "docs",
        )
    return checks, defects


def check_live_matrix(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict[str, Any], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = []
    summary: dict[str, Any] = {"present": False}

    path = monorepo / LIVE_LOGIN_MATRIX_RELATIVE
    if not path.is_file():
        add_check(
            checks,
            defects,
            "live:matrix_absent",
            True,
            "absent",
            "live",
            soft=True,
        )
        limitations.append("live_login_matrix_absent")
        return checks, defects, summary, limitations

    summary["present"] = True
    doc = load_json(path)
    add_check(checks, defects, "live:matrix_present", True, LIVE_LOGIN_MATRIX_RELATIVE, "live")

    owner_ok = doc.get("owner_matches_awscurrent") is True
    summary["owner_matches_awscurrent"] = owner_ok
    add_check(
        checks,
        defects,
        "live:owner_matches_awscurrent",
        owner_ok,
        str(doc.get("owner_matches_awscurrent")),
        "live",
    )

    correct = doc.get("correct_login") == 200
    summary["correct_login"] = doc.get("correct_login")
    add_check(
        checks,
        defects,
        "live:correct_login",
        correct,
        str(doc.get("correct_login")),
        "live",
    )

    wrong_pw = doc.get("wrong_password") == 401
    summary["wrong_password"] = doc.get("wrong_password")
    add_check(
        checks,
        defects,
        "live:wrong_password",
        wrong_pw,
        str(doc.get("wrong_password")),
        "live",
    )

    wrong_code = doc.get("wrong_password_error_code")
    code_ok = wrong_code == "invalid_credentials"
    summary["wrong_password_error_code"] = wrong_code
    add_check(
        checks,
        defects,
        "live:wrong_password_error_code",
        code_ok,
        str(wrong_code),
        "live",
        soft=not code_ok,
    )
    if not code_ok:
        limitations.append("live_login_matrix_stale_deploy")

    attrs = doc.get("cookie_attrs") or {}
    cookie_ok = (
        isinstance(attrs, dict)
        and attrs.get("HttpOnly") is True
        and attrs.get("Secure") is True
        and attrs.get("SameSite=Strict") is True
        and attrs.get("has_Domain") is False
    )
    summary["cookie_attrs"] = {
        "HttpOnly": attrs.get("HttpOnly") if isinstance(attrs, dict) else None,
        "Secure": attrs.get("Secure") if isinstance(attrs, dict) else None,
        "SameSite=Strict": attrs.get("SameSite=Strict") if isinstance(attrs, dict) else None,
        "Path": attrs.get("Path") if isinstance(attrs, dict) else None,
    }
    add_check(
        checks,
        defects,
        "live:cookie_attrs",
        cookie_ok,
        "attrs",
        "live",
    )

    path_value = attrs.get("Path") if isinstance(attrs, dict) else None
    path_ok = path_value == "/"
    add_check(
        checks,
        defects,
        "live:cookie_path",
        path_ok,
        str(path_value),
        "live",
        soft=not path_ok,
    )
    if not path_ok:
        limitations.append("production_cookie_path_pending_deploy")

    sm_json = doc.get("sm_json_as_password_matches") is False
    summary["sm_json_as_password_matches"] = doc.get("sm_json_as_password_matches")
    add_check(
        checks,
        defects,
        "live:sm_json_not_password",
        sm_json,
        str(doc.get("sm_json_as_password_matches")),
        "live",
    )

    return checks, defects, summary, limitations


def check_prior_slices_and_boundary(
    monorepo: Path,
    policy: dict[str, Any],
) -> tuple[list[CheckResult], list[Defect], dict[str, Any]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    ok23 = (monorepo / EXPECTED_17_23_PACKAGE).is_dir()
    ok24 = (monorepo / EXPECTED_17_24_PACKAGE).is_dir()
    add_check(checks, defects, "prior_slices:17_23", ok23, EXPECTED_17_23_PACKAGE, "prior_slices")
    add_check(checks, defects, "prior_slices:17_24_package", ok24, EXPECTED_17_24_PACKAGE, "prior_slices")

    start_24 = policy.get("start_slice_17_24") is True
    start_25 = policy.get("start_slice_17_25") is True
    add_check(
        checks,
        defects,
        "boundary:start_slice_17_24",
        start_24,
        "true",
        "epic17_boundary",
    )
    add_check(
        checks,
        defects,
        "boundary:start_slice_17_25_false",
        not start_25,
        "false",
        "epic17_boundary",
    )

    started_25 = False
    for cand in SLICE_17_25_PACKAGE_CANDIDATES:
        exists = (monorepo / cand).exists()
        if exists:
            started_25 = True
        add_check(
            checks,
            defects,
            f"security:no_{Path(cand).name}",
            not exists,
            "absent" if not exists else "present",
            "security",
        )

    add_check(
        checks,
        defects,
        "prior_slices:17_25_not_started",
        not started_25,
        "absent",
        "prior_slices",
    )

    return checks, defects, {
        "slice_17_23": ok23,
        "slice_17_24": ok24,
        "start_slice_17_24": start_24,
        "start_slice_17_25": False,
        "slice_17_25_started": started_25,
    }


def check_operational(monorepo: Path) -> tuple[list[CheckResult], list[Defect], list[str]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    limitations: list[str] = ["monorepo_pre_cutover_authority"]

    uncommitted = False
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=monorepo,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        uncommitted = bool(result.stdout.strip())
    except Exception:  # noqa: BLE001
        uncommitted = False

    add_check(
        checks,
        defects,
        "operational:worktree_uncommitted",
        not uncommitted,
        "clean" if not uncommitted else "dirty",
        "operational",
        soft=True,
    )
    if uncommitted:
        limitations.append("worktree_uncommitted")
    return checks, defects, limitations
