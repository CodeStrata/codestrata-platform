"""Production-foundation and production-ingestion wiring for Community Cloud Lambda."""

from __future__ import annotations

from fastapi import FastAPI

from codestrata_platform.community_cloud_api.app import create_community_cloud_app
from codestrata_platform.community_cloud_api.authentication import (
    UnavailableCommunityCredentialVerifier,
    default_authentication_policy,
)
from codestrata_platform.community_cloud_api.deployment.diagnostics import (
    deployment_wiring_diagnostic,
)
from codestrata_platform.community_cloud_api.deployment.settings import (
    DeploymentSettings,
    load_deployment_settings,
)
from codestrata_platform.community_cloud_api.rate_limiting import (
    default_rate_limit_policy,
)


def create_production_foundation_app(
    *,
    settings: DeploymentSettings | None = None,
) -> FastAPI:
    """Build the Community Cloud app for production foundation or ingestion.

    When ``CODESTRATA_INGESTION_ENABLED`` is false (default):

    - authentication enabled with unavailable verifier (no credentials)
    - rate limiting enabled (process-local store retained as defense-in-depth)
    - all event sinks default to unavailable
    - event identity lookup/recorder remain unset (fail-closed)
    - Insights auth uses AWS Secrets Manager when
      CODESTRATA_INSIGHTS_SECRETS_BACKEND=aws (Slice 17.6+); otherwise fail-closed
    - no test adapters, no-op sinks, or hardcoded tokens

    When ingestion is enabled (requires bucket + wire flags):

    - Community Data Lake S3 store + all five Data Lake sinks
    - S3 event identity store (``identity/`` prefix)
    - AwsCommunityCredentialVerifier (Secrets Manager fingerprints)
    - SystemAcceptanceClock for envelope acceptance time

    Health remains operational. Foundation mode returns 503 for ingestion
    without durable backends.
    """

    active = settings or load_deployment_settings()
    if not active.authentication_enabled:
        raise RuntimeError("authentication must remain enabled")
    if not active.rate_limit_enabled:
        raise RuntimeError("rate limiting must remain enabled")

    if active.ingestion_enabled:
        return _create_production_ingestion_app(active)

    app = create_community_cloud_app(
        authentication_policy=default_authentication_policy(),
        credential_verifier=UnavailableCommunityCredentialVerifier(),
        rate_limit_policy=default_rate_limit_policy(),
        # Sinks and identity ports intentionally omitted → unavailable/fail-closed.
        # rate_limit_store omitted → process-local InMemoryRateLimitStore.
        insights_auth_service=_build_insights_auth_service(),
        report_publishing_service=_build_report_publishing_service(active),
    )
    app.state.community_cloud_deployment_settings = active
    app.state.community_cloud_deployment_diagnostic = deployment_wiring_diagnostic(
        active,
        credential_verifier="unavailable",
        event_sinks="unavailable",
        event_identity_store="unavailable",
        durable_ingestion=False,
    )
    return app


# Alias for clarity at Lambda entrypoints (same builder).
create_production_app = create_production_foundation_app


def _create_production_ingestion_app(active: DeploymentSettings) -> FastAPI:
    if not active.data_lake_bucket:
        raise RuntimeError("production ingestion requires CODESTRATA_DATA_LAKE_BUCKET")
    if not active.ingestion_wire:
        raise RuntimeError(
            "production ingestion requires CODESTRATA_INGESTION_WIRE=true "
            "or CODESTRATA_DATA_LAKE_ADAPTER=s3"
        )

    import os

    from codestrata_platform.community_cloud_api.authentication.aws_credentials import (
        build_production_credential_verifier,
    )
    from codestrata_platform.community_cloud_api.data_lake.accepted_clock import (
        SystemAcceptanceClock,
    )
    from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
        S3DataLakeStoreConfiguration,
    )
    from codestrata_platform.community_cloud_api.data_lake.sinks import (
        DataLakeAiUsageSink,
        DataLakeAssessmentMetadataSink,
        DataLakeCliEventSink,
        DataLakeExtensionEventSink,
        DataLakeTelemetryEventSink,
    )
    from codestrata_platform.community_cloud_api.data_lake.storage_configuration import (
        DataLakeStorageConfiguration,
    )
    from codestrata_platform.community_cloud_api.data_lake.storage_factory import (
        create_community_data_lake_store,
    )
    from codestrata_platform.community_cloud_api.event_identity.s3_store import (
        S3EventIdentityStore,
    )

    region = (
        os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or ""
    ).strip() or None

    s3_config = S3DataLakeStoreConfiguration(bucket_name=active.data_lake_bucket)
    store = create_community_data_lake_store(
        DataLakeStorageConfiguration.s3(),
        s3_config=s3_config,
    )
    clock = SystemAcceptanceClock()
    identity = S3EventIdentityStore(
        bucket_name=active.data_lake_bucket,
        region_name=region,
    )
    verifier = build_production_credential_verifier(
        environ={
            **dict(os.environ),
            "CODESTRATA_COMMUNITY_CREDENTIALS_SECRET_ID": (
                active.community_credentials_secret_id
            ),
        }
    )

    report_publishing_service = _build_report_publishing_service(active)
    app = create_community_cloud_app(
        authentication_policy=default_authentication_policy(),
        credential_verifier=verifier,
        rate_limit_policy=default_rate_limit_policy(),
        telemetry_sink=DataLakeTelemetryEventSink(store=store, clock=clock),
        assessment_metadata_sink=DataLakeAssessmentMetadataSink(store=store, clock=clock),
        cli_event_sink=DataLakeCliEventSink(store=store, clock=clock),
        extension_event_sink=DataLakeExtensionEventSink(store=store, clock=clock),
        ai_usage_sink=DataLakeAiUsageSink(store=store, clock=clock),
        event_identity_lookup=identity,
        event_identity_recorder=identity,
        insights_auth_service=_build_insights_auth_service(),
        insights_aggregation_service=_build_insights_aggregation_service(
            bucket_name=active.data_lake_bucket,
            region_name=region,
            report_service=report_publishing_service,
        ),
        report_publishing_service=report_publishing_service,
    )
    app.state.community_cloud_deployment_settings = active
    app.state.community_cloud_deployment_diagnostic = deployment_wiring_diagnostic(
        active,
        credential_verifier="aws_secrets_manager",
        event_sinks="data_lake_s3",
        event_identity_store="s3_identity",
        durable_ingestion=True,
    )
    return app


def _build_insights_aggregation_service(
    *,
    bucket_name: str,
    region_name: str | None,
    report_service: object | None = None,
):
    """Wire privacy-safe Insights aggregation to bounded Data Lake reads."""

    import boto3

    from codestrata_platform.community_cloud_api.insights.external_metrics import (
        count_published_from_registry,
    )
    from codestrata_platform.community_cloud_api.insights.service import (
        InsightsAggregationService,
    )
    from codestrata_platform.community_cloud_api.insights_storage.reader import (
        BoundedS3Reader,
    )
    from codestrata_platform.community_cloud_api.reports.service import (
        ReportPublishingService,
    )

    client = boto3.client("s3", region_name=region_name)
    reader = BoundedS3Reader(bucket=bucket_name, client=client)

    published_port = None
    sentiment_port = None
    if isinstance(report_service, ReportPublishingService):

        class _PublishedPort:
            def count_published_reports(self) -> int:
                registry = report_service.list_published_registry()
                return count_published_from_registry(registry)

        class _SentimentPort:
            def community_sentiment_summary(self) -> dict:
                return report_service.community_sentiment_summary()

        published_port = _PublishedPort()
        sentiment_port = _SentimentPort()

    return InsightsAggregationService(
        reader=reader,
        published_reports_port=published_port,
        community_sentiment_port=sentiment_port,
    )


def _build_report_publishing_service(active: DeploymentSettings):
    """Wire private report artifact store when bucket is configured."""

    from codestrata_platform.community_cloud_api.reports.service import (
        ReportPublishingService,
    )
    from codestrata_platform.community_cloud_api.reports.store import (
        S3ReportArtifactStore,
    )

    if not active.report_publishing_enabled or not active.report_artifacts_bucket:
        return ReportPublishingService(available=False)

    import os

    region = (
        os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or ""
    ).strip() or None
    store = S3ReportArtifactStore(
        bucket_name=active.report_artifacts_bucket,
        region_name=region,
    )
    return ReportPublishingService(store=store, available=True)


def _build_insights_auth_service():
    import os
    from dataclasses import replace

    from codestrata_platform.community_cloud_api.insights_auth.policy import (
        default_insights_auth_policy,
    )
    from codestrata_platform.community_cloud_api.insights_auth.secrets import (
        build_production_secrets_port,
    )
    from codestrata_platform.community_cloud_api.insights_auth.service import (
        InsightsAuthService,
    )

    base = default_insights_auth_policy()
    password_id = (
        os.environ.get("CODESTRATA_INSIGHTS_PASSWORD_SECRET_ID") or base.password_secret_id
    ).strip()
    session_id = (
        os.environ.get("CODESTRATA_INSIGHTS_SESSION_SECRET_ID") or base.session_secret_id
    ).strip()
    aws_backend = (
        (os.environ.get("CODESTRATA_INSIGHTS_SECRETS_BACKEND") or "").strip().lower() == "aws"
    )
    policy = replace(
        base,
        password_secret_id=password_id,
        session_secret_id=session_id,
        production_deployment_enabled=aws_backend,
    )
    return InsightsAuthService(
        policy=policy,
        secrets=build_production_secrets_port(),
    )
