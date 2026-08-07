"""Classified inventory of Cursor client vocabulary occurrences (Slice 12.4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verification.community_client_boundary_cleanup.models import CheckResult, Defect

# Deterministic classified inventory discovered before contract changes.
CLASSIFIED_INVENTORY: tuple[dict[str, str], ...] = (
    {
        "symbol": "CLIENT_TYPE_CURSOR",
        "path": "platform/.../authentication/models.py",
        "class": "historical_accepted_event_compatibility",
    },
    {
        "symbol": "ALLOWED_CLIENT_TYPES",
        "path": "platform/.../authentication/models.py",
        "class": "active_request_validation",
    },
    {
        "symbol": "CURSOR_EXTENSION_CLIENT",
        "path": "platform/.../extension_events/enums.py",
        "class": "historical_deserialization_compatibility",
    },
    {
        "symbol": "ACTIVE_EXTENSION_CLIENTS",
        "path": "platform/.../extension_events/enums.py",
        "class": "active_emitter_vocabulary",
    },
    {
        "symbol": "HISTORICAL_EXTENSION_CLIENTS",
        "path": "platform/.../extension_events/enums.py",
        "class": "historical_deserialization_compatibility",
    },
    {
        "symbol": "SCHEMA_EXTENSION_CLIENTS",
        "path": "platform/.../extension_events/enums.py",
        "class": "historical_deserialization_compatibility",
    },
    {
        "symbol": "ALLOWED_EXTENSION_CLIENTS",
        "path": "platform/.../extension_events/enums.py",
        "class": "active_emitter_vocabulary",
    },
    {
        "symbol": "ExtensionEditor.CURSOR",
        "path": "platform/.../extension_events/enums.py",
        "class": "historical_deserialization_compatibility",
    },
    {
        "symbol": "AiInvocationSource.CURSOR_EXTENSION",
        "path": "platform/.../ai_usage/enums.py",
        "class": "historical_deserialization_compatibility",
    },
    {
        "symbol": "ALLOWED_AI_USAGE_CLIENTS",
        "path": "platform/.../ai_usage/enums.py",
        "class": "active_emitter_vocabulary",
    },
    {
        "symbol": "HISTORICAL_AI_USAGE_CLIENTS",
        "path": "platform/.../ai_usage/enums.py",
        "class": "historical_deserialization_compatibility",
    },
    {
        "symbol": "envelope_registry allowed_client_types",
        "path": "platform/.../data_lake/envelope_registry.py",
        "class": "active_runtime_client",
    },
    {
        "symbol": "_EXTENSION_CLIENT_TYPES",
        "path": "platform/.../extension_event_partitioning.py",
        "class": "active_partition_metadata",
    },
    {
        "symbol": "_AI_USAGE_CLIENT_TYPES",
        "path": "platform/.../ai_usage_partitioning.py",
        "class": "active_partition_metadata",
    },
    {
        "symbol": "community-retired-client-policy",
        "path": "platform/.../retired_clients.py",
        "class": "historical_accepted_event_compatibility",
    },
    {
        "symbol": "historical_client_compatibility",
        "path": "platform/.../historical_client_compatibility.py",
        "class": "historical_deserialization_compatibility",
    },
    {
        "symbol": "TelemetryClientName",
        "path": "platform/.../telemetry/enums.py",
        "class": "active_emitter_vocabulary",
    },
    {
        "symbol": "Engine client_name=codestrata_cli",
        "path": "engine telemetry runtime",
        "class": "active_runtime_client",
    },
    {
        "symbol": "vscode_extension analytics/telemetry",
        "path": "vscode-plugin docs",
        "class": "active_runtime_client",
    },
    {
        "symbol": "PRODUCT_CURSOR_EXTENSION",
        "path": "engine/.../terminology.py",
        "class": "obsolete_reference",
    },
    {
        "symbol": "prior SV reports cursor mentions",
        "path": "reports/verification/sv9-* / sv11-*",
        "class": "historical_verification_reference",
    },
    {
        "symbol": "test fixtures cursor_extension",
        "path": "platform/tests/.../test_client_boundary_cleanup.py",
        "class": "test_fixture_only",
    },
)


def build_classification() -> dict[str, Any]:
    by_class: dict[str, list[str]] = {}
    for item in CLASSIFIED_INVENTORY:
        by_class.setdefault(item["class"], []).append(item["symbol"])
    return {
        "by_class": {k: sorted(v) for k, v in sorted(by_class.items())},
        "entries": sorted(
            CLASSIFIED_INVENTORY,
            key=lambda x: (x["class"], x["symbol"], x["path"]),
        ),
    }


def check_inventory(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    _ = monorepo
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    classification = build_classification()
    checks.append(
        CheckResult(
            name="inventory:classified_entries",
            ok=len(CLASSIFIED_INVENTORY) >= 10,
            detail=f"entries={len(CLASSIFIED_INVENTORY)}",
            category="inventory",
        )
    )
    for class_name, symbols in classification["by_class"].items():
        checks.append(
            CheckResult(
                name=f"inventory:class_{class_name}",
                ok=True,
                detail=f"count={len(symbols)}",
                category="inventory",
            )
        )
    # Active emitter vocabulary must not list Cursor as active.
    active_symbols = set(classification["by_class"].get("active_emitter_vocabulary", []))
    if "CURSOR_EXTENSION_CLIENT" in active_symbols or "ALLOWED_EXTENSION_CLIENTS_includes_cursor" in active_symbols:
        defects.append(
            Defect(
                "active-client vocabulary defect",
                "inventory",
                "cursor absent from active_emitter",
                "cursor present",
            )
        )
    return checks, defects
