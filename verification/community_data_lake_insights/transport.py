"""Default production HTTP telemetry transport checks."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from verification.community_data_lake_insights.contract import (
    PRODUCT_TRANSPORT_PY,
    PROMPT_RUNTIME_FACTORY_PY,
    RUNTIME_FACTORY_PY,
)
from verification.community_data_lake_insights.helpers import check, contains, read_text
from verification.community_data_lake_insights.models import CheckResult, Defect

# Synthetic credential shape only — never a real production secret.
_SYNTHETIC_CREDENTIAL = "cscc_v1_" + ("a" * 32)


def check_transport(
    monorepo: Path,
) -> tuple[list[CheckResult], list[Defect], dict]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    summary: dict = {
        "production_http_transport_available_after_opt_in": False,
        "product_transport_exists": False,
        "prompt_factory_wired": False,
        "unauthorized_unavailable": False,
        "default_runtime_no_http": False,
        "runtime_allow_with_credential_http": False,
        "runtime_without_credential_unavailable": False,
        "runtime_deny_unavailable": False,
    }

    transport_path = monorepo / PRODUCT_TRANSPORT_PY
    exists = transport_path.is_file()
    summary["product_transport_exists"] = exists
    checks.append(
        check(
            "transport:product_transport_exists",
            exists,
            PRODUCT_TRANSPORT_PY,
            "transport",
        )
    )
    if not exists:
        defects.append(
            Defect(
                "missing_product_transport",
                "transport:product_transport_exists",
                "present",
                PRODUCT_TRANSPORT_PY,
            )
        )
        return checks, defects, summary

    text = read_text(transport_path)
    uses_url = "production_telemetry_ingest_url" in text
    uses_cred = "CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL" in text or "CREDENTIAL_ENV" in text
    checks.append(
        check(
            "transport:uses_production_ingest_url",
            uses_url,
            "production_telemetry_ingest_url",
            "transport",
        )
    )
    checks.append(
        check(
            "transport:uses_community_client_credential",
            uses_cred,
            "CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL",
            "transport",
        )
    )
    if not uses_url or not uses_cred:
        defects.append(
            Defect(
                "transport_wiring",
                "transport:production_symbols",
                "production_telemetry_ingest_url+credential",
                "missing symbols",
            )
        )

    prompt_path = monorepo / PROMPT_RUNTIME_FACTORY_PY
    prompt_ok = prompt_path.is_file() and contains(
        prompt_path, "resolve_product_telemetry_transport"
    )
    summary["prompt_factory_wired"] = prompt_ok
    checks.append(
        check(
            "transport:prompt_runtime_factory_imports_resolve",
            prompt_ok,
            "resolve_product_telemetry_transport",
            "transport",
        )
    )
    if not prompt_ok:
        defects.append(
            Defect(
                "prompt_factory_unwired",
                "transport:prompt_runtime_factory_imports_resolve",
                "imports resolve_product_telemetry_transport",
                "missing",
            )
        )

    # Unauthorized consent stays Unavailable (source contract).
    unauth_ok = (
        "transmission_authorized" in text
        and "UnavailableTelemetryTransport" in text
    )
    summary["unauthorized_unavailable"] = unauth_ok
    checks.append(
        check(
            "transport:unauthorized_remains_unavailable",
            unauth_ok,
            "Unauthorized → UnavailableTelemetryTransport",
            "transport",
        )
    )
    if not unauth_ok:
        defects.append(
            Defect(
                "unauthorized_not_unavailable",
                "transport:unauthorized_remains_unavailable",
                "UnavailableTelemetryTransport",
                "contract missing",
            )
        )

    runtime_path = monorepo / RUNTIME_FACTORY_PY
    runtime_text = read_text(runtime_path) if runtime_path.is_file() else ""
    default_no_http = (
        "create_default_telemetry_runtime" in runtime_text
        and "create_http_telemetry_transport" not in runtime_text
    )
    summary["default_runtime_no_http"] = default_no_http
    checks.append(
        check(
            "transport:default_runtime_no_http_factory",
            default_no_http,
            "create_default_telemetry_runtime does not call create_http_telemetry_transport",
            "transport",
        )
    )
    if not default_no_http:
        defects.append(
            Defect(
                "default_runtime_http",
                "transport:default_runtime_no_http_factory",
                "no create_http_telemetry_transport",
                "found or missing factory",
            )
        )

    # Runtime import classification with synthetic credential.
    allow_http = False
    no_cred_unavail = False
    deny_unavail = False
    try:
        from codestrata.telemetry.consent import (
            allow_session_consent,
            deny_session_consent,
        )
        from codestrata.telemetry.infrastructure.http_transport import (
            HttpTelemetryTransport,
        )
        from codestrata.telemetry.infrastructure.unavailable_transport import (
            UnavailableTelemetryTransport,
        )
        from codestrata.telemetry.product_transport import (
            resolve_product_telemetry_transport,
        )

        with patch.dict(
            os.environ,
            {"CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL": _SYNTHETIC_CREDENTIAL},
            clear=False,
        ):
            t_allow = resolve_product_telemetry_transport(allow_session_consent())
            allow_http = isinstance(t_allow, HttpTelemetryTransport)

        env = {k: v for k, v in os.environ.items() if k != "CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL"}
        with patch.dict(os.environ, env, clear=True):
            t_no = resolve_product_telemetry_transport(allow_session_consent())
            no_cred_unavail = isinstance(t_no, UnavailableTelemetryTransport)

        with patch.dict(
            os.environ,
            {"CODESTRATA_COMMUNITY_CLIENT_CREDENTIAL": _SYNTHETIC_CREDENTIAL},
            clear=False,
        ):
            t_deny = resolve_product_telemetry_transport(deny_session_consent())
            deny_unavail = isinstance(t_deny, UnavailableTelemetryTransport)
    except Exception as exc:  # noqa: BLE001
        checks.append(
            check(
                "transport:runtime_import",
                False,
                f"runtime import failed: {type(exc).__name__}",
                "transport",
            )
        )
        defects.append(
            Defect(
                "transport_runtime_import",
                "transport:runtime_import",
                "resolvable",
                type(exc).__name__,
            )
        )

    summary["runtime_allow_with_credential_http"] = allow_http
    summary["runtime_without_credential_unavailable"] = no_cred_unavail
    summary["runtime_deny_unavailable"] = deny_unavail

    checks.append(
        check(
            "transport:allow_with_credential_is_http",
            allow_http,
            "allow+credential → HttpTelemetryTransport",
            "transport",
        )
    )
    checks.append(
        check(
            "transport:allow_without_credential_unavailable",
            no_cred_unavail,
            "allow without credential → Unavailable",
            "transport",
        )
    )
    checks.append(
        check(
            "transport:deny_unavailable",
            deny_unavail,
            "deny → Unavailable",
            "transport",
        )
    )
    if not allow_http:
        defects.append(
            Defect(
                "product_default_http_transport_unavailable",
                "transport:allow_with_credential_is_http",
                "HttpTelemetryTransport",
                "not resolved after opt-in",
            )
        )
    if not no_cred_unavail:
        defects.append(
            Defect(
                "missing_credential_not_unavailable",
                "transport:allow_without_credential_unavailable",
                "UnavailableTelemetryTransport",
                "unexpected transport",
            )
        )
    if not deny_unavail:
        defects.append(
            Defect(
                "deny_not_unavailable",
                "transport:deny_unavailable",
                "UnavailableTelemetryTransport",
                "unexpected transport",
            )
        )

    wired = (
        exists
        and uses_url
        and uses_cred
        and prompt_ok
        and unauth_ok
        and default_no_http
        and allow_http
        and no_cred_unavail
        and deny_unavail
    )
    summary["production_http_transport_available_after_opt_in"] = wired
    checks.append(
        check(
            "transport:production_http_transport_available_after_opt_in",
            wired,
            "classification=production_http_transport_available_after_opt_in",
            "transport",
        )
    )
    if not wired:
        defects.append(
            Defect(
                "production_http_transport_unavailable",
                "transport:production_http_transport_available_after_opt_in",
                "available after opt-in",
                "not fully wired",
            )
        )
    return checks, defects, summary
