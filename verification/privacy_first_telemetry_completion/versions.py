"""Policy, schema, and verification version registries."""

from __future__ import annotations

from codestrata.reporting.contract.constants import ASSESSMENT_JSON_SCHEMA_VERSION
from codestrata.telemetry.assessment_isolation_policy import (
    COMMUNITY_TELEMETRY_ASSESSMENT_ISOLATION_POLICY_URN,
)
from codestrata.telemetry.catalog_policy import (
    PRIVACY_FIRST_TELEMETRY_CATALOG_SCHEMA_VERSION,
    COMMUNITY_TELEMETRY_PUBLIC_CATALOG_POLICY_URN,
)
from codestrata.telemetry.cli_consent_policy import COMMUNITY_TELEMETRY_CLI_CONSENT_POLICY_URN
from codestrata.telemetry.consent_policy import COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_URN
from codestrata.telemetry.non_interactive_policy import (
    COMMUNITY_TELEMETRY_NON_INTERACTIVE_POLICY_URN,
)
from codestrata.telemetry.pre_transport_policy import (
    COMMUNITY_TELEMETRY_PRE_TRANSPORT_PRIVACY_POLICY_URN,
)
from codestrata.telemetry.preview_policy import (
    COMMUNITY_TELEMETRY_PREVIEW_POLICY_URN,
    PRIVACY_FIRST_TELEMETRY_PREVIEW_SCHEMA_VERSION,
)
from codestrata.telemetry.prompt_policy import (
    COMMUNITY_TELEMETRY_INTERACTIVE_CONSENT_POLICY_URN,
)
from codestrata.telemetry.runtime_policy import (
    COMMUNITY_TELEMETRY_RUNTIME_POLICY_URN,
    PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_URN,
    PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_VERSION,
)
from codestrata.telemetry.status_policy import (
    COMMUNITY_TELEMETRY_STATUS_POLICY_URN,
    PRIVACY_FIRST_TELEMETRY_STATUS_SCHEMA_VERSION,
)
from codestrata.telemetry.transport_errors import (
    COMMUNITY_TELEMETRY_TRANSPORT_EVENT_IDENTITY_POLICY_URN,
)
from codestrata.telemetry.transport_policy import COMMUNITY_TELEMETRY_TRANSPORT_POLICY_URN

from verification.privacy_first_telemetry import (
    PRIVACY_FIRST_TELEMETRY_VERIFICATION_VERSION,
)
from verification.privacy_first_telemetry.contract import SCHEMA_VERSION as CROSS_CLIENT_SCHEMA_VERSION
from verification.privacy_first_telemetry_completion import (
    PRIVACY_FIRST_TELEMETRY_COMPLETION_VERSION,
)
from verification.privacy_first_telemetry_completion.contract import SCHEMA_VERSION
from verification.privacy_first_telemetry_completion.models import CheckResult, Defect

VSCODE_RUNTIME_POLICY = "community-vscode-telemetry-runtime-policy:1.0"
VSCODE_EVENT_SCHEMA = "community-vscode-telemetry-event-schema:1.0"


def build_policy_registry() -> dict[str, str]:
    return {
        "engine.runtime_policy": COMMUNITY_TELEMETRY_RUNTIME_POLICY_URN,
        "engine.session_consent_policy": COMMUNITY_TELEMETRY_SESSION_CONSENT_POLICY_URN,
        "engine.interactive_consent_policy": COMMUNITY_TELEMETRY_INTERACTIVE_CONSENT_POLICY_URN,
        "engine.non_interactive_policy": COMMUNITY_TELEMETRY_NON_INTERACTIVE_POLICY_URN,
        "engine.cli_consent_policy": COMMUNITY_TELEMETRY_CLI_CONSENT_POLICY_URN,
        "engine.status_policy": COMMUNITY_TELEMETRY_STATUS_POLICY_URN,
        "engine.catalog_policy": COMMUNITY_TELEMETRY_PUBLIC_CATALOG_POLICY_URN,
        "engine.preview_policy": COMMUNITY_TELEMETRY_PREVIEW_POLICY_URN,
        "engine.pre_transport_privacy_policy": COMMUNITY_TELEMETRY_PRE_TRANSPORT_PRIVACY_POLICY_URN,
        "engine.transport_policy": COMMUNITY_TELEMETRY_TRANSPORT_POLICY_URN,
        "engine.transport_event_identity_policy": COMMUNITY_TELEMETRY_TRANSPORT_EVENT_IDENTITY_POLICY_URN,
        "engine.assessment_isolation_policy": COMMUNITY_TELEMETRY_ASSESSMENT_ISOLATION_POLICY_URN,
        "vscode.runtime_policy": VSCODE_RUNTIME_POLICY,
    }


def build_schema_registry() -> dict[str, str]:
    return {
        "engine.runtime_event_schema": PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_URN,
        "engine.runtime_event_schema_version": PRIVACY_SAFE_RUNTIME_EVENT_SCHEMA_VERSION,
        "engine.status_schema_version": PRIVACY_FIRST_TELEMETRY_STATUS_SCHEMA_VERSION,
        "engine.catalog_schema_version": PRIVACY_FIRST_TELEMETRY_CATALOG_SCHEMA_VERSION,
        "engine.preview_schema_version": PRIVACY_FIRST_TELEMETRY_PREVIEW_SCHEMA_VERSION,
        "vscode.event_schema": VSCODE_EVENT_SCHEMA,
        "product.assessment_schema": ASSESSMENT_JSON_SCHEMA_VERSION,
        "product.community_cloud_api": "1.0",
        "product.telemetry_endpoint": "1.0",
        "product.extension_event_endpoint": "1.0",
        "product.data_lake_contracts": "1.0",
    }


def build_verification_registry() -> dict[str, str]:
    return {
        "cross_client_privacy_verification": CROSS_CLIENT_SCHEMA_VERSION,
        "cross_client_package_version": PRIVACY_FIRST_TELEMETRY_VERIFICATION_VERSION,
        "completion_verification": SCHEMA_VERSION,
        "completion_package_version": PRIVACY_FIRST_TELEMETRY_COMPLETION_VERSION,
    }


def check_versions() -> tuple[dict[str, str], dict[str, str], dict[str, str], list[CheckResult], list[Defect]]:
    policies = build_policy_registry()
    schemas = build_schema_registry()
    verification = build_verification_registry()
    checks: list[CheckResult] = []
    defects: list[Defect] = []

    expected_policy_count = 13
    checks.append(
        CheckResult(
            name="policy_registry_count",
            ok=len(policies) == expected_policy_count,
            detail=f"count={len(policies)}",
            category="versions",
        )
    )
    for key, urn in sorted(policies.items()):
        ok = urn.endswith(":1.0") or urn.endswith(":1.0.0")
        # All product policies are 1.0
        ok = ":1.0" in urn and not urn.endswith(":2.0")
        checks.append(
            CheckResult(
                name=f"policy_{key.replace('.', '_')}",
                ok=bool(urn) and ok,
                detail=urn,
                category="versions",
            )
        )

    checks.append(
        CheckResult(
            name="assessment_schema_unchanged_1_2",
            ok=schemas["product.assessment_schema"] == "1.2",
            detail=schemas["product.assessment_schema"],
            category="versions",
        )
    )
    checks.append(
        CheckResult(
            name="engine_runtime_event_schema_1_0",
            ok=schemas["engine.runtime_event_schema_version"] == "1.0",
            detail=schemas["engine.runtime_event_schema_version"],
            category="versions",
        )
    )
    checks.append(
        CheckResult(
            name="verification_schemas_1_0_0",
            ok=(
                verification["cross_client_privacy_verification"] == "1.0.0"
                and verification["completion_verification"] == "1.0.0"
            ),
            detail=str(verification),
            category="versions",
        )
    )
    # No duplicate URN values across policies
    urns = list(policies.values())
    checks.append(
        CheckResult(
            name="policy_urns_unique",
            ok=len(urns) == len(set(urns)),
            detail=f"unique={len(set(urns))}",
            category="versions",
        )
    )

    for check in checks:
        if not check.ok:
            defects.append(
                Defect(
                    classification="version registry defect",
                    component="versions",
                    expected="pass",
                    actual=check.name,
                    detail=check.detail,
                )
            )
    return policies, schemas, verification, checks, defects
