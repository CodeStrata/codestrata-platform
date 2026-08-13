"""Decode lake envelopes into privacy-safe aggregation event views."""

from __future__ import annotations

import json
from typing import Any

from codestrata_platform.community_cloud_api.insights.policy import (
    ALLOWED_ASSESSMENT_HEADS,
    ALLOWED_MODEL_FAMILIES,
    ALLOWED_PACKAGE_ECOSYSTEMS,
    ALLOWED_PRIMARY_LANGUAGES,
    APPROVED_CLI_OPS,
    APPROVED_EXTENSION_OPS,
    APPROVED_TELEMETRY_TYPES,
    PROVIDER_ADOPTION_FAMILIES,
    PROVIDER_UNAVAILABLE,
)

SUPPORTED_ENVELOPE_SCHEMA = "1.0"
SUPPORTED_PAYLOAD_SCHEMAS = frozenset({"1.0", "1.1"})
ALLOWED_STREAMS = frozenset(
    {
        "telemetry",
        "assessment_metadata",
        "cli_event",
        "extension_event",
        "ai_usage",
    }
)


def decode_object_bytes(raw: bytes) -> dict[str, Any] | None:
    """Parse JSON object bytes. Returns None on malformed JSON (no body leak)."""

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def normalize_event(envelope: dict[str, Any]) -> dict[str, Any] | None:
    """Validate envelope shape and project approved fields only.

    Returns None for unsupported/malformed envelopes (caller counts malformed).
    """

    if envelope.get("envelope_schema_version") != SUPPORTED_ENVELOPE_SCHEMA:
        return None
    stream = envelope.get("event_stream")
    if stream not in ALLOWED_STREAMS:
        return None
    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        return None
    if str(payload.get("schema_version") or "") not in SUPPORTED_PAYLOAD_SCHEMAS:
        return None

    acceptance = envelope.get("acceptance") if isinstance(envelope.get("acceptance"), dict) else {}
    partition_date = acceptance.get("partition_date")
    installation_id = payload.get("installation_id")
    if installation_id is not None and not isinstance(installation_id, str):
        installation_id = None
    if isinstance(installation_id, str) and not installation_id.strip():
        installation_id = None

    client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
    client_name = client.get("name") if isinstance(client.get("name"), str) else None
    client_version = (
        client.get("version") if isinstance(client.get("version"), str) else None
    )

    event: dict[str, Any] = {
        "stream": stream,
        "partition_date": partition_date if isinstance(partition_date, str) else None,
        "event_id": payload.get("event_id") if isinstance(payload.get("event_id"), str) else None,
        "installation_id": installation_id,
        "client_name": client_name,
        "client_version": client_version,
        "occurred_at": _occurred_at(payload, acceptance),
    }

    if stream == "telemetry":
        et = payload.get("event_type")
        if et not in APPROVED_TELEMETRY_TYPES:
            return None
        event["event_type"] = et
        props = payload.get("properties") if isinstance(payload.get("properties"), dict) else {}
        feature = props.get("feature")
        outcome = props.get("outcome")
        operation = props.get("operation")
        if isinstance(feature, str) and feature.strip():
            event["feature"] = feature.strip()[:64]
        if isinstance(outcome, str) and outcome.strip():
            event["outcome"] = outcome.strip()[:32]
        if isinstance(operation, str) and operation.strip():
            event["operation"] = operation.strip()[:64]
        return event

    if stream in {"cli_event", "extension_event"}:
        ev = payload.get("event") if isinstance(payload.get("event"), dict) else {}
        op = ev.get("operation")
        allowed = APPROVED_CLI_OPS if stream == "cli_event" else APPROVED_EXTENSION_OPS
        if op not in allowed:
            return None
        event["operation"] = op
        return event

    if stream == "assessment_metadata":
        assessment = (
            payload.get("assessment") if isinstance(payload.get("assessment"), dict) else {}
        )
        execution = (
            payload.get("execution") if isinstance(payload.get("execution"), dict) else {}
        )
        repository = (
            payload.get("repository") if isinstance(payload.get("repository"), dict) else {}
        )
        status = assessment.get("assessment_status")
        result = execution.get("result")
        heads_raw = assessment.get("executed_heads") or []
        heads: list[str] = []
        if isinstance(heads_raw, list):
            seen: set[str] = set()
            for h in heads_raw:
                if isinstance(h, str) and h in ALLOWED_ASSESSMENT_HEADS and h not in seen:
                    seen.add(h)
                    heads.append(h)
        lang = repository.get("primary_language")
        if lang not in ALLOWED_PRIMARY_LANGUAGES:
            lang = "unknown"
        eco = repository.get("package_ecosystem")
        if eco is not None and eco not in ALLOWED_PACKAGE_ECOSYSTEMS:
            eco = "unknown"
        event["assessment_status"] = status if isinstance(status, str) else None
        event["execution_result"] = result if isinstance(result, str) else None
        event["executed_heads"] = heads
        event["primary_language"] = lang
        event["package_ecosystem"] = eco
        assessment_id = payload.get("assessment_id")
        if isinstance(assessment_id, str) and assessment_id.strip():
            event["assessment_id"] = assessment_id.strip()[:64]
        return event

    if stream == "ai_usage":
        usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
        provider = usage.get("provider_family")
        model = usage.get("model_family")
        if provider == PROVIDER_UNAVAILABLE:
            event["provider_family"] = PROVIDER_UNAVAILABLE
        elif provider in PROVIDER_ADOPTION_FAMILIES:
            event["provider_family"] = provider
        else:
            return None
        if model not in ALLOWED_MODEL_FAMILIES:
            model = "other_supported"
        event["model_family"] = model
        return event

    return None


def _occurred_at(payload: dict[str, Any], acceptance: dict[str, Any]) -> str | None:
    for key in ("occurred_at",):
        val = payload.get(key)
        if isinstance(val, str) and val:
            return val
    accepted = acceptance.get("accepted_at")
    if isinstance(accepted, str) and accepted:
        return accepted
    partition = acceptance.get("partition_date")
    if isinstance(partition, str) and partition:
        return f"{partition}T00:00:00Z"
    return None
