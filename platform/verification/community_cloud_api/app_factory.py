"""Build verification and production-foundation Community Cloud apps."""

from __future__ import annotations

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
from codestrata_platform.community_cloud_api.deployment import (
    create_production_foundation_app,
    load_deployment_settings,
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

from verification.community_cloud_api.credentials import build_test_verifier


@dataclass(slots=True)
class VerificationApp:
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
            self.sink_count(k)
            for k in (
                "telemetry",
                "assessment_metadata",
                "cli_events",
                "extension_events",
                "ai_usage",
            )
        )

    def identity_count(self) -> int:
        return len(self.identity._items)  # noqa: SLF001 — verification inspection only


def build_verification_app(
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
) -> VerificationApp:
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

    rl_store: object = (
        UnavailableRateLimitStore()
        if unavailable_rate_limit_store
        else InMemoryRateLimitStore()
    )

    if unavailable_identity or not include_identity:
        identity_lookup: object | None = None
        identity_recorder: object | None = None
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
    return VerificationApp(
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


def build_production_foundation_client() -> TestClient:
    app = create_production_foundation_app(settings=load_deployment_settings({}))
    return TestClient(app)
