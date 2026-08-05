"""Typed endpoint-request construction helpers for Slice 8.3 envelope tests.

Not a ``test_*`` module — pytest does not collect it. Builds validated
endpoint request models directly (bypassing HTTP/``app.py`` entirely) using
the same body shapes as each endpoint's own ``valid_*_body`` test helper, so
these tests never import ``app.py`` or any deployment wiring.
"""

from __future__ import annotations

from typing import Any

from codestrata_platform.community_cloud_api.ai_usage.models import AiUsageRequest
from codestrata_platform.community_cloud_api.assessment_metadata.models import (
    AssessmentMetadataRequest,
)
from codestrata_platform.community_cloud_api.cli_events.models import CliEventRequest
from codestrata_platform.community_cloud_api.extension_events.models import (
    ExtensionEventRequest,
)
from codestrata_platform.community_cloud_api.telemetry.models import TelemetryIngestionRequest

from ..ai_usage_helpers import valid_ai_usage_body
from ..assessment_metadata_helpers import valid_assessment_metadata_body
from ..cli_event_helpers import valid_cli_event_body
from ..extension_event_helpers import valid_extension_event_body
from ..telemetry_helpers import valid_telemetry_body


def make_telemetry_request(**overrides: Any) -> TelemetryIngestionRequest:
    return TelemetryIngestionRequest.model_validate(valid_telemetry_body(**overrides))


def make_assessment_metadata_request(**overrides: Any) -> AssessmentMetadataRequest:
    return AssessmentMetadataRequest.model_validate(valid_assessment_metadata_body(**overrides))


def make_cli_event_request(**overrides: Any) -> CliEventRequest:
    return CliEventRequest.model_validate(valid_cli_event_body(**overrides))


def make_extension_event_request(**overrides: Any) -> ExtensionEventRequest:
    return ExtensionEventRequest.model_validate(valid_extension_event_body(**overrides))


def make_ai_usage_request(**overrides: Any) -> AiUsageRequest:
    return AiUsageRequest.model_validate(valid_ai_usage_body(**overrides))


__all__ = [
    "make_ai_usage_request",
    "make_assessment_metadata_request",
    "make_cli_event_request",
    "make_extension_event_request",
    "make_telemetry_request",
]
