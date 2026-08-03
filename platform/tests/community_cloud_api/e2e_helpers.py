"""Shared harness for Slice 7.15 end-to-end Community Cloud verification."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from fastapi.testclient import TestClient

from codestrata_platform.community_cloud_api.ai_usage.ports import (
    InMemoryAiUsageSink,
    UnavailableAiUsageSink,
)
from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.assessment_metadata.ports import (
    InMemoryAssessmentMetadataSink,
    UnavailableAssessmentMetadataSink,
)
from codestrata_platform.community_cloud_api.authentication import (
    UnavailableCommunityCredentialVerifier,
)
from codestrata_platform.community_cloud_api.cli_events.ports import (
    InMemoryCliEventSink,
    UnavailableCliEventSink,
)
from codestrata_platform.community_cloud_api.event_identity import InMemoryEventIdentityStore
from codestrata_platform.community_cloud_api.extension_events.ports import (
    InMemoryExtensionEventSink,
    UnavailableExtensionEventSink,
)
from codestrata_platform.community_cloud_api.logging.context import SequenceClock
from codestrata_platform.community_cloud_api.logging.logger import (
    CommunityCloudLogger,
    MemoryLogSink,
)
from codestrata_platform.community_cloud_api.payload_limits import PayloadLimitPolicy
from codestrata_platform.community_cloud_api.rate_limiting import (
    CommunityRateLimitPolicy,
    InMemoryRateLimitStore,
    UnavailableRateLimitStore,
)
from codestrata_platform.community_cloud_api.telemetry.ports import (
    InMemoryTelemetryEventSink,
    UnavailableTelemetryEventSink,
)

from .ai_usage_helpers import valid_ai_usage_body
from .assessment_metadata_helpers import valid_assessment_metadata_body
from .auth_test_support import (
    TEST_CLI_TOKEN,
    TEST_CURSOR_TOKEN,
    TEST_VSCODE_TOKEN,
    auth_headers,
    build_test_verifier,
)
from .cli_event_helpers import valid_cli_event_body
from .extension_event_helpers import valid_extension_event_body
from .rate_limit_helpers import tight_rate_limit_policy
from .telemetry_helpers import valid_telemetry_body

# Production ingestion routes exercised by the verification suite.
INGESTION_ROUTES: tuple[tuple[str, str], ...] = (
    ("/api/v1/telemetry", "telemetry"),
    ("/api/v1/assessment-metadata", "assessment_metadata"),
    ("/api/v1/cli-events", "cli_events"),
    ("/api/v1/extension-events", "extension_events"),
    ("/api/v1/ai-usage", "ai_usage"),
)


@dataclass(slots=True)
class VerificationHarness:
    """Fully wired in-memory Community Cloud app for pipeline verification."""

    client: TestClient
    telemetry: InMemoryTelemetryEventSink
    assessment_metadata: InMemoryAssessmentMetadataSink
    cli_events: InMemoryCliEventSink
    extension_events: InMemoryExtensionEventSink
    ai_usage: InMemoryAiUsageSink
    identity: InMemoryEventIdentityStore
    rate_limit_store: object
    log_sink: MemoryLogSink
    verifier: object
    clock: SequenceClock

    def identity_count(self) -> int:
        return len(self.identity._items)  # noqa: SLF001 — test-only inspection

    def sink_count(self, kind: str) -> int:
        mapping = {
            "telemetry": self.telemetry.events,
            "assessment_metadata": self.assessment_metadata.events,
            "cli_events": self.cli_events.events,
            "extension_events": self.extension_events.events,
            "ai_usage": self.ai_usage.events,
        }
        return len(mapping[kind])

    def total_sink_events(self) -> int:
        return sum(
            self.sink_count(kind)
            for kind in (
                "telemetry",
                "assessment_metadata",
                "cli_events",
                "extension_events",
                "ai_usage",
            )
        )


def body_for(kind: str, **overrides: object) -> dict[str, object]:
    builders: dict[str, Callable[..., dict[str, object]]] = {
        "telemetry": valid_telemetry_body,
        "assessment_metadata": valid_assessment_metadata_body,
        "cli_events": valid_cli_event_body,
        "extension_events": valid_extension_event_body,
        "ai_usage": valid_ai_usage_body,
    }
    return builders[kind](**overrides)


def token_for(kind: str) -> str:
    if kind == "extension_events":
        return TEST_VSCODE_TOKEN
    return TEST_CLI_TOKEN


def conflict_body_for(kind: str) -> dict[str, object]:
    """Same event_id / scope, different fingerprint field."""

    if kind == "telemetry":
        return body_for(kind, properties={"feature": "other", "outcome": "failed"})
    if kind == "assessment_metadata":
        body = body_for(kind)
        body["assessment"] = {**body["assessment"], "finding_count": 99}  # type: ignore[dict-item]
        return body
    if kind == "cli_events":
        body = body_for(kind)
        body["event"] = {**body["event"], "operation": "doctor"}  # type: ignore[dict-item]
        return body
    if kind == "extension_events":
        body = body_for(kind)
        body["event"] = {**body["event"], "operation": "open_report"}  # type: ignore[dict-item]
        return body
    body = body_for(kind)
    body["usage"] = {**body["usage"], "provider_family": "aws_bedrock"}  # type: ignore[dict-item]
    return body


def auth_for(kind: str, *, request_id: str | None = None) -> dict[str, str]:
    headers = auth_headers(token_for(kind))
    if request_id is not None:
        headers["X-Request-Id"] = request_id
    return headers


def build_verification_harness(
    *,
    rate_limit_policy: CommunityRateLimitPolicy | None = None,
    payload_policy: PayloadLimitPolicy | None = None,
    verifier: object | None = None,
    unavailable_verifier: bool = False,
    unavailable_rate_limit_store: bool = False,
    unavailable_identity: bool = False,
    unavailable_sinks: bool = False,
    include_identity: bool = True,
    clock: SequenceClock | None = None,
) -> VerificationHarness:
    """Build one app with auth enabled and all five sinks injected."""

    identity = InMemoryEventIdentityStore()
    telemetry = InMemoryTelemetryEventSink()
    assessment = InMemoryAssessmentMetadataSink()
    cli = InMemoryCliEventSink()
    extension = InMemoryExtensionEventSink()
    ai = InMemoryAiUsageSink()
    log_sink = MemoryLogSink()
    logger = CommunityCloudLogger.create(sink=log_sink)
    active_clock = clock or SequenceClock(start_ms=1_700_000_000_000, step_ms=0)

    if unavailable_verifier:
        active_verifier: object = UnavailableCommunityCredentialVerifier()
    elif verifier is not None:
        active_verifier = verifier
    else:
        active_verifier = build_test_verifier()

    if unavailable_rate_limit_store:
        rl_store: object = UnavailableRateLimitStore()
    else:
        rl_store = InMemoryRateLimitStore()

    identity_lookup: object | None
    identity_recorder: object | None
    if unavailable_identity or not include_identity:
        identity_lookup = None
        identity_recorder = None
    else:
        identity_lookup = identity
        identity_recorder = identity

    if unavailable_sinks:
        tel_sink: object = UnavailableTelemetryEventSink()
        meta_sink: object = UnavailableAssessmentMetadataSink()
        cli_sink: object = UnavailableCliEventSink()
        ext_sink: object = UnavailableExtensionEventSink()
        ai_sink: object = UnavailableAiUsageSink()
    else:
        tel_sink = telemetry
        meta_sink = assessment
        cli_sink = cli
        ext_sink = extension
        ai_sink = ai

    app = create_community_cloud_app(
        telemetry_sink=tel_sink,
        assessment_metadata_sink=meta_sink,
        cli_event_sink=cli_sink,
        extension_event_sink=ext_sink,
        ai_usage_sink=ai_sink,
        event_identity_lookup=identity_lookup,
        event_identity_recorder=identity_recorder,
        credential_verifier=active_verifier,
        rate_limit_policy=rate_limit_policy,
        rate_limit_store=rl_store,  # type: ignore[arg-type]
        rate_limit_clock_ms=active_clock,
        payload_policy=payload_policy,
        logger=logger,
    )
    return VerificationHarness(
        client=TestClient(app),
        telemetry=telemetry,
        assessment_metadata=assessment,
        cli_events=cli,
        extension_events=extension,
        ai_usage=ai,
        identity=identity,
        rate_limit_store=rl_store,
        log_sink=log_sink,
        verifier=active_verifier,
        clock=active_clock,
    )


__all__ = [
    "INGESTION_ROUTES",
    "TEST_CLI_TOKEN",
    "TEST_CURSOR_TOKEN",
    "TEST_VSCODE_TOKEN",
    "VerificationHarness",
    "auth_for",
    "body_for",
    "build_test_verifier",
    "build_verification_harness",
    "conflict_body_for",
    "tight_rate_limit_policy",
    "token_for",
]
