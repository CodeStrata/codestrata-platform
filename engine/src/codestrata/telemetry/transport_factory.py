"""Explicit HTTP telemetry transport factory (Slice 9.11).

Never reads environment variables. Never becomes the product default.
"""

from __future__ import annotations

from codestrata.telemetry.infrastructure.http_client import TelemetryHttpClient
from codestrata.telemetry.infrastructure.http_transport import HttpTelemetryTransport
from codestrata.telemetry.transport_configuration import TelemetryTransportConfiguration


def create_http_telemetry_transport(
    configuration: TelemetryTransportConfiguration,
    *,
    client: TelemetryHttpClient | None = None,
) -> HttpTelemetryTransport:
    """Build an HTTP transport from validated configuration.

    Callers must inject this transport explicitly into a session/runtime.
    ``create_default_telemetry_runtime()`` does not call this factory.
    """

    return HttpTelemetryTransport(configuration, client=client)


__all__ = ["create_http_telemetry_transport"]
