"""Derive routes and request fields from Community Cloud API runtime."""

from __future__ import annotations

from typing import Any, get_args, get_origin, Union

from pydantic import BaseModel


def _type_name(ann: object) -> str:
    if ann is None:
        return "Any"
    origin = get_origin(ann)
    if origin is Union:
        args = list(get_args(ann))
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and type(None) in args:
            return f"optional[{_type_name(non_none[0])}]"
        return " | ".join(_type_name(a) for a in args)
    if origin is list:
        args = get_args(ann)
        return f"list[{_type_name(args[0]) if args else 'Any'}]"
    if origin is dict:
        return "object"
    if isinstance(ann, type) and issubclass(ann, BaseModel):
        return ann.__name__
    return getattr(ann, "__name__", str(ann).replace("typing.", ""))


def _walk_model(
    model: type[BaseModel],
    *,
    prefix: str = "",
    api: str,
    stream: str,
    seen: set[int] | None = None,
) -> list[dict[str, Any]]:
    seen = seen or set()
    if id(model) in seen:
        return []
    seen.add(id(model))
    out: list[dict[str, Any]] = []
    for name, field in model.model_fields.items():
        path = f"{prefix}.{name}" if prefix else name
        ann = field.annotation
        out.append(
            {
                "api": api,
                "stream": stream,
                "field_name": path,
                "type": _type_name(ann),
                "required": field.is_required(),
                "source_model": model.__name__,
            }
        )
        candidates: list[type[BaseModel]] = []
        origin = get_origin(ann)
        if isinstance(ann, type) and issubclass(ann, BaseModel):
            candidates = [ann]
        elif origin is Union:
            for a in get_args(ann):
                if isinstance(a, type) and issubclass(a, BaseModel):
                    candidates.append(a)
        elif origin is list:
            for a in get_args(ann):
                if isinstance(a, type) and issubclass(a, BaseModel):
                    candidates.append(a)
        for child in candidates:
            out.extend(
                _walk_model(child, prefix=path, api=api, stream=stream, seen=seen)
            )
    return out


def derive_runtime_fields() -> list[dict[str, Any]]:
    from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
    from codestrata_platform.community_cloud_api.assessment_metadata.models import (
        AssessmentMetadataRequest,
    )
    from codestrata_platform.community_cloud_api.cli_events.models import CliEventRequest
    from codestrata_platform.community_cloud_api.extension_events.models import (
        ExtensionEventRequest,
    )
    from codestrata_platform.community_cloud_api.reports.models import (
        ReportPublishRequest,
        ReportUploadIntentRequest,
    )
    from codestrata_platform.community_cloud_api.telemetry.models import (
        TelemetryIngestionRequest,
    )

    models: dict[str, tuple[str, type[BaseModel]]] = {
        "POST /api/v1/telemetry": ("telemetry", TelemetryIngestionRequest),
        "POST /api/v1/assessment-metadata": (
            "assessment_metadata",
            AssessmentMetadataRequest,
        ),
        "POST /api/v1/cli-events": ("cli_event", CliEventRequest),
        "POST /api/v1/extension-events": ("extension_event", ExtensionEventRequest),
        "POST /api/v1/ai-usage": ("ai_usage", AiUsageRequest),
        "POST /api/v1/reports/upload-intents": (
            "reports.upload_intent",
            ReportUploadIntentRequest,
        ),
        "POST /api/v1/reports": ("reports.publish", ReportPublishRequest),
    }
    fields: list[dict[str, Any]] = []
    for api, (stream, model) in models.items():
        fields.extend(_walk_model(model, api=api, stream=stream))
    return fields


def derive_runtime_routes() -> list[dict[str, Any]]:
    from codestrata_platform.community_cloud_api.community_status.routes import (
        register_community_status_routes,
    )
    from codestrata_platform.community_cloud_api.community_status.service import (
        CommunityStatusService,
    )
    from codestrata_platform.community_cloud_api.insights.service import (
        InsightsAggregationService,
    )
    from codestrata_platform.community_cloud_api.insights_auth.policy import (
        default_insights_auth_policy,
    )
    from codestrata_platform.community_cloud_api.insights_auth.routes import (
        register_insights_auth_routes,
    )
    from codestrata_platform.community_cloud_api.insights_auth.service import (
        InsightsAuthService,
    )
    from codestrata_platform.community_cloud_api.registry import RouteRegistry
    from codestrata_platform.community_cloud_api.reports.routes import register_report_routes
    from codestrata_platform.community_cloud_api.reports.service import (
        ReportPublishingService,
    )

    reg = RouteRegistry.foundation_v1()
    register_report_routes(reg, service=ReportPublishingService(available=False))
    register_insights_auth_routes(
        reg,
        auth=InsightsAuthService(policy=default_insights_auth_policy()),
        aggregation=InsightsAggregationService(),
        report_service=ReportPublishingService(available=False),
    )
    register_community_status_routes(reg, service=CommunityStatusService())
    out: list[dict[str, Any]] = []
    for spec in sorted(reg.list_routes(), key=lambda s: (s.absolute_path, s.method)):
        out.append(
            {
                "route_id": spec.name,
                "method": spec.method,
                "path": spec.absolute_path,
                "authentication_group": spec.authentication_group,
            }
        )
    return out
