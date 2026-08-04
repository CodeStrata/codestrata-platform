"""Contract for SV.7 Community Cloud API verification."""

from __future__ import annotations

from dataclasses import dataclass

COMMUNITY_CLOUD_API_VERIFICATION_ID = "community-cloud-api-verification"
COMMUNITY_CLOUD_API_VERIFICATION_VERSION = "1.0.0"

EXPECTED_ROUTE_IDENTITIES: tuple[str, ...] = (
    "health.get",
    "telemetry.ingest",
    "assessment_metadata.ingest",
    "cli_events.ingest",
    "extension_events.ingest",
    "ai_usage.ingest",
)

INGESTION_KINDS: tuple[str, ...] = (
    "telemetry",
    "assessment_metadata",
    "cli_events",
    "extension_events",
    "ai_usage",
)

INGESTION_PATHS: dict[str, str] = {
    "telemetry": "/api/v1/telemetry",
    "assessment_metadata": "/api/v1/assessment-metadata",
    "cli_events": "/api/v1/cli-events",
    "extension_events": "/api/v1/extension-events",
    "ai_usage": "/api/v1/ai-usage",
}

# Obviously fake — never commit as production config; never emit in reports/logs.
TEST_CLI_TOKEN = "cscc_v1_TEST_ONLY_CLI_TOKEN_AAAA"
TEST_VSCODE_TOKEN = "cscc_v1_TEST_ONLY_VSCODE_TOKEN_BB"
TEST_CURSOR_TOKEN = "cscc_v1_TEST_ONLY_CURSOR_TOKEN_CC"

FORBIDDEN_REPORT_FRAGMENTS: tuple[str, ...] = (
    TEST_CLI_TOKEN,
    TEST_VSCODE_TOKEN,
    TEST_CURSOR_TOKEN,
    "cscc_v1_TEST_ONLY_INACTIVE_TOKEN_DD",
    "cscc_v1_TEST_ONLY_REVOKED_TOKEN_EE",
    "Authorization:",
    "Bearer cscc_v1_",
    "/Users/",
    "/home/",
    "file://",
)


@dataclass(frozen=True, slots=True)
class CcVerificationContract:
    verification_id: str = COMMUNITY_CLOUD_API_VERIFICATION_ID
    schema_version: str = COMMUNITY_CLOUD_API_VERIFICATION_VERSION
    notes: tuple[str, ...] = (
        "SV.7 verifies the Community Cloud API as one coherent pipeline.",
        "Uses in-memory adapters only; no AWS, OpenTofu, Docker, or durable stores.",
        "Does not start website export (SV.8) or Data Lake work.",
        "Does not add endpoints, emitters, or credential issuance.",
    )


def default_contract() -> CcVerificationContract:
    return CcVerificationContract()
