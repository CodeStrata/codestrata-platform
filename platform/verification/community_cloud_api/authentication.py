"""Authentication and client-matching verification."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.authentication.models import (
    CREDENTIAL_STATUS_INACTIVE,
    CREDENTIAL_STATUS_REVOKED,
)
from codestrata_platform.community_cloud_api.errors import (
    ERROR_AUTHENTICATION_REQUIRED,
    ERROR_AUTHENTICATION_UNAVAILABLE,
    ERROR_CLIENT_NOT_AUTHORIZED,
    ERROR_INVALID_AUTHORIZATION_HEADER,
    ERROR_INVALID_CLIENT_CREDENTIAL,
)

from verification.community_cloud_api.app_factory import VerificationApp, build_verification_app
from verification.community_cloud_api.contract import (
    INGESTION_KINDS,
    INGESTION_PATHS,
    TEST_CLI_TOKEN,
    TEST_VSCODE_TOKEN,
)
from verification.community_cloud_api.credentials import auth_headers, build_test_verifier
from verification.community_cloud_api.models import CheckResult
from verification.community_cloud_api.requests import body_for, mismatched_client_body

_INACTIVE_TOKEN = "cscc_v1_TEST_ONLY_INACTIVE_TOKEN_DD"
_REVOKED_TOKEN = "cscc_v1_TEST_ONLY_REVOKED_TOKEN_EE"


def check_authentication(app: VerificationApp) -> list[CheckResult]:
    checks: list[CheckResult] = []
    for kind in INGESTION_KINDS:
        path = INGESTION_PATHS[kind]
        before = app.sink_count(kind)
        missing = app.client.post(path, json=body_for(kind, event_id=f"sv7-noauth-{kind}"))
        checks.append(
            CheckResult(
                name=f"auth:missing:{kind}",
                ok=(
                    missing.status_code == 401
                    and missing.json()["error"]["code"] == ERROR_AUTHENTICATION_REQUIRED
                    and missing.headers.get("WWW-Authenticate") == "Bearer"
                    and app.sink_count(kind) == before
                ),
                detail=f"status={missing.status_code}",
                category="authentication",
                scenario="C",
            )
        )
        malformed = app.client.post(
            path,
            json=body_for(kind, event_id=f"sv7-malauth-{kind}"),
            headers={"Authorization": "Basic abc"},
        )
        code = malformed.json().get("error", {}).get("code")
        checks.append(
            CheckResult(
                name=f"auth:malformed:{kind}",
                ok=malformed.status_code == 401
                and code
                in {ERROR_INVALID_AUTHORIZATION_HEADER, ERROR_AUTHENTICATION_REQUIRED, ERROR_INVALID_CLIENT_CREDENTIAL},
                detail=f"status={malformed.status_code} code={code}",
                category="authentication",
                scenario="D",
            )
        )
        unknown = app.client.post(
            path,
            json=body_for(kind, event_id=f"sv7-badcred-{kind}"),
            headers=auth_headers("cscc_v1_TEST_ONLY_UNKNOWN_TOKEN_ZZ"),
        )
        checks.append(
            CheckResult(
                name=f"auth:unknown_credential:{kind}",
                ok=unknown.status_code == 401
                and unknown.json()["error"]["code"] == ERROR_INVALID_CLIENT_CREDENTIAL
                and TEST_CLI_TOKEN not in unknown.text,
                detail=f"status={unknown.status_code}",
                category="authentication",
                scenario="E",
            )
        )

    inactive_verifier = build_test_verifier()
    inactive_verifier.register(
        _INACTIVE_TOKEN,
        client_id="client-test-inactive",
        client_type="codestrata_cli",
        rate_limit_scope_id="rlscope-inactive",
        credential_id="cred-test-inactive",
        status=CREDENTIAL_STATUS_INACTIVE,
    )
    inactive_verifier.register(
        _REVOKED_TOKEN,
        client_id="client-test-revoked",
        client_type="codestrata_cli",
        rate_limit_scope_id="rlscope-revoked",
        credential_id="cred-test-revoked",
        status=CREDENTIAL_STATUS_REVOKED,
    )
    status_app = build_verification_app(verifier=inactive_verifier)
    for label, token, scenario in (
        ("inactive", _INACTIVE_TOKEN, "F"),
        ("revoked", _REVOKED_TOKEN, "F"),
    ):
        response = status_app.client.post(
            INGESTION_PATHS["telemetry"],
            json=body_for("telemetry", event_id=f"sv7-{label}-cred"),
            headers=auth_headers(token),
        )
        checks.append(
            CheckResult(
                name=f"auth:{label}_credential",
                ok=(
                    response.status_code == 401
                    and response.json()["error"]["code"] == ERROR_INVALID_CLIENT_CREDENTIAL
                    and label not in response.text.lower()
                    and token not in response.text
                ),
                detail=f"status={response.status_code}",
                category="authentication",
                scenario=scenario,
            )
        )

    unavailable = build_verification_app(unavailable_verifier=True)
    blocked = unavailable.client.post(
        INGESTION_PATHS["telemetry"],
        json=body_for("telemetry", event_id="sv7-verifier-down"),
        headers=auth_headers(),
    )
    checks.append(
        CheckResult(
            name="auth:verifier_unavailable",
            ok=blocked.status_code == 503
            and blocked.json()["error"]["code"] == ERROR_AUTHENTICATION_UNAVAILABLE,
            detail=f"status={blocked.status_code}",
            category="authentication",
            scenario="G",
        )
    )
    return checks


def check_client_matching(app: VerificationApp) -> list[CheckResult]:
    checks: list[CheckResult] = []
    for kind in INGESTION_KINDS:
        path = INGESTION_PATHS[kind]
        before = app.sink_count(kind)
        if kind == "extension_events":
            # CLI principal cannot submit vscode_extension payload.
            headers = auth_headers(TEST_CLI_TOKEN)
            body = body_for(kind, event_id=f"sv7-mismatch-{kind}")
        elif kind == "cli_events":
            # VS Code principal cannot submit codestrata_cli CLI events.
            headers = auth_headers(TEST_VSCODE_TOKEN)
            body = body_for(kind, event_id=f"sv7-mismatch-{kind}")
        else:
            # CLI principal + vscode_extension client name in payload.
            headers = auth_headers(TEST_CLI_TOKEN)
            body = mismatched_client_body(kind)
            body["event_id"] = f"sv7-mismatch-{kind}"
        response = app.client.post(path, json=body, headers=headers)
        checks.append(
            CheckResult(
                name=f"client_match:mismatch:{kind}",
                ok=(
                    response.status_code == 403
                    and response.json()["error"]["code"] == ERROR_CLIENT_NOT_AUTHORIZED
                    and app.sink_count(kind) == before
                ),
                detail=f"status={response.status_code}",
                category="authorization",
                scenario="H",
            )
        )
    return checks
