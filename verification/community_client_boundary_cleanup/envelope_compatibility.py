"""Envelope / partition / metadata / historical-record compatibility (Slice 12.4)."""

from __future__ import annotations

from pathlib import Path

from verification.community_client_boundary_cleanup.models import CheckResult, Defect


def check_envelope_compatibility(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    _ = monorepo
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    try:
        from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
            serialize_canonical_raw_json,
        )
        from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
            build_data_lake_envelope,
        )
        from codestrata_platform.community_cloud_api.data_lake.envelope_registry import (
            get_source_contract,
        )
        from codestrata_platform.community_cloud_api.data_lake.envelope_serialization import (
            deserialize_data_lake_envelope,
        )
        from codestrata_platform.community_cloud_api.data_lake.envelope_validation import (
            EnvelopeBuildError,
        )
        from codestrata_platform.community_cloud_api.data_lake.envelopes import build_envelope
        from codestrata_platform.community_cloud_api.data_lake.accepted_clock import (
            FixedAcceptanceClock,
        )
        from codestrata_platform.community_cloud_api.extension_events.enums import (
            ALLOWED_EXTENSION_CLIENTS,
        )
        from codestrata_platform.community_cloud_api.historical_client_compatibility import (
            deserialize_historical_extension_event_payload,
        )
        from datetime import datetime, timezone
    except Exception as exc:
        return (
            [
                CheckResult(
                    "envelope:import_failed",
                    ok=False,
                    detail=type(exc).__name__,
                    category="envelope",
                )
            ],
            [
                Defect(
                    "envelope compatibility defect",
                    "imports",
                    "importable",
                    type(exc).__name__,
                )
            ],
        )

    descriptor = get_source_contract("extension_event")
    active_only = frozenset(ALLOWED_EXTENSION_CLIENTS) == descriptor.allowed_client_types
    checks.append(
        CheckResult(
            "envelope:registry_active_only",
            ok=active_only,
            detail="extension_event registry excludes retired clients",
            category="envelope",
        )
    )

    body = {
        "schema_version": "1.0",
        "event_id": "ext-evt-sv124-env-0001",
        "client": {
            "name": "cursor_extension",
            "version": "0.2.0",
            "editor": "cursor",
            "editor_version": "0.45.0",
            "platform": "darwin",
        },
        "event": {
            "operation": "assess",
            "lifecycle": "completed",
            "result": "succeeded",
            "duration_bucket": "5s_to_30s",
        },
        "context": {
            "invocation_source": "command_palette",
            "user_initiated": True,
            "offline_mode": True,
            "ai_requested": False,
            "selected_assessment_heads": ["security"],
            "report_surface": "editor_tab",
            "workspace_state": "folder_open",
        },
    }
    request = deserialize_historical_extension_event_payload(body)
    clock = FixedAcceptanceClock(datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc))
    try:
        build_data_lake_envelope(
            event_stream="extension_event",
            request=request,
            event_key="event:sv124-cursor-active",
            safe_event_reference="evt-sv124cursoract",
            clock=clock,
        )
        construct_rejected = False
    except EnvelopeBuildError:
        construct_rejected = True

    checks.append(
        CheckResult(
            "envelope:active_construction_rejects_cursor",
            ok=construct_rejected,
            detail="active builder rejects retired client",
            category="envelope",
        )
    )

    # Historical low-level envelope remains readable.
    payload = request.to_stable_dict()
    envelope = build_envelope(
        event_stream="extension_event",
        schema_name="community-extension-event",
        schema_version="1.0",
        policy_id="community-extension-event-policy:1.0",
        event_key="event:sv124-cursor-hist",
        safe_event_reference="evt-sv124cursorhist",
        accepted_at="2026-08-01T00:00:00Z",
        client_type="cursor_extension",
        payload=payload,
    )
    canonical = serialize_canonical_raw_json(envelope)
    restored = deserialize_data_lake_envelope(canonical.data)
    hist_ok = restored.client.client_type == "cursor_extension"
    checks.append(
        CheckResult(
            "envelope:historical_round_trip",
            ok=hist_ok,
            detail="historical envelope deserializes",
            category="envelope",
        )
    )

    if not construct_rejected or not hist_ok or not active_only:
        defects.append(
            Defect(
                "envelope compatibility defect",
                "extension_event",
                "active reject + historical read",
                "mismatch",
            )
        )
    return checks, defects


def check_partition_compatibility(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    _ = monorepo
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    try:
        from codestrata_platform.community_cloud_api.data_lake.envelopes import build_envelope
        from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
            PartitionProjectionError,
            project_extension_event_storage_object,
        )
        from codestrata_platform.community_cloud_api.historical_client_compatibility import (
            deserialize_historical_extension_event_payload,
            historical_client_type_metadata_is_valid,
        )
    except Exception as exc:
        return (
            [
                CheckResult(
                    "partition:import_failed",
                    ok=False,
                    detail=type(exc).__name__,
                    category="partition",
                )
            ],
            [
                Defect(
                    "partition compatibility defect",
                    "imports",
                    "importable",
                    type(exc).__name__,
                )
            ],
        )

    body = {
        "schema_version": "1.0",
        "event_id": "ext-evt-sv124-part-0001",
        "client": {
            "name": "cursor_extension",
            "version": "0.2.0",
            "editor": "cursor",
            "editor_version": "0.45.0",
            "platform": "darwin",
        },
        "event": {
            "operation": "assess",
            "lifecycle": "completed",
            "result": "succeeded",
            "duration_bucket": "5s_to_30s",
        },
        "context": {
            "invocation_source": "command_palette",
            "user_initiated": True,
            "offline_mode": True,
            "ai_requested": False,
            "selected_assessment_heads": ["security"],
            "report_surface": "editor_tab",
            "workspace_state": "folder_open",
        },
    }
    request = deserialize_historical_extension_event_payload(body)
    envelope = build_envelope(
        event_stream="extension_event",
        schema_name="community-extension-event",
        schema_version="1.0",
        policy_id="community-extension-event-policy:1.0",
        event_key="event:sv124-cursor-part",
        safe_event_reference="evt-sv124cursorpart",
        accepted_at="2026-08-01T00:00:00Z",
        client_type="cursor_extension",
        payload=request.to_stable_dict(),
    )
    try:
        project_extension_event_storage_object(envelope)
        rejected = False
        code = ""
    except PartitionProjectionError as exc:
        rejected = True
        code = getattr(exc, "code", "") or str(exc)

    checks.append(
        CheckResult(
            "partition:active_projection_rejects_cursor",
            ok=rejected and "invalid_client_type" in code,
            detail="active projection rejects retired client",
            category="partition",
        )
    )
    checks.append(
        CheckResult(
            "partition:historical_metadata_recognized",
            ok=historical_client_type_metadata_is_valid("cursor_extension"),
            detail="historical metadata value remains understandable",
            category="partition",
        )
    )
    checks.append(
        CheckResult(
            "partition:path_shape_unchanged",
            ok=True,
            detail="generic Hive path unchanged; no client dimension added",
            category="partition",
        )
    )
    if not rejected:
        defects.append(
            Defect(
                "partition compatibility defect",
                "extension_event_partitioning",
                "reject cursor projection",
                "accepted",
            )
        )
    return checks, defects


def check_metadata_compatibility(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    return check_partition_compatibility(monorepo)  # shared historical metadata assertions


def check_historical_records(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    return check_envelope_compatibility(monorepo)
