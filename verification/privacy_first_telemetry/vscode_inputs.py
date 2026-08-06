"""Static VS Code telemetry inventory (parse TypeScript; no Engine↔VS Code runtime dep)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_STR_RE = re.compile(r'["\']([a-zA-Z0-9_.:-]+)["\']')


def _extract_string_array(source: str, const_name: str) -> tuple[str, ...]:
    pattern = re.compile(
        rf"(?:export\s+)?const\s+{re.escape(const_name)}"
        rf"(?:\s*:\s*[^=]+)?\s*=\s*\[(.*?)\](?:\s*as\s+const)?\s*;",
        re.DOTALL,
    )
    match = pattern.search(source)
    if not match:
        return ()
    return tuple(_STR_RE.findall(match.group(1)))


def _extract_string_const(source: str, const_name: str) -> str | None:
    pattern = re.compile(
        rf"(?:export\s+)?const\s+{re.escape(const_name)}\s*=\s*[`'\"]([^`'\"]+)[`'\"]"
    )
    match = pattern.search(source)
    return match.group(1) if match else None


@dataclass(frozen=True, slots=True)
class VsCodeTelemetryInventory:
    telemetry_dir: Path
    runtime_policy_id: str
    runtime_policy_version: str
    runtime_policy_urn: str
    event_schema_name: str
    event_schema_version: str
    client_name: str
    approved_event_types: tuple[str, ...]
    approved_field_names: tuple[str, ...]
    eligible_commands: tuple[str, ...]
    excluded_commands: tuple[str, ...]
    forbidden_name_fragments: tuple[str, ...]
    shared_conceptual_fields: tuple[str, ...]
    engine_only_event_types: tuple[str, ...]
    vscode_only_fields: tuple[str, ...]
    source_blob: str


def load_vscode_inventory(monorepo: Path) -> VsCodeTelemetryInventory:
    telemetry_dir = monorepo / "vscode-plugin" / "src" / "telemetry"
    sources: dict[str, str] = {}
    for path in sorted(telemetry_dir.glob("*.ts")):
        sources[path.name] = path.read_text(encoding="utf-8")
    blob = "\n".join(sources[name] for name in sorted(sources))

    policy_src = sources.get("runtimePolicy.ts", "")
    events_src = sources.get("events.ts", "")
    privacy_src = sources.get("privacy.ts", "")
    prompt_src = sources.get("promptPolicy.ts", "")
    mapping_src = sources.get("catalogMapping.ts", "")
    consent_src = sources.get("consent.ts", "")

    policy_id = _extract_string_const(policy_src, "COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_ID") or ""
    policy_version = (
        _extract_string_const(policy_src, "COMMUNITY_VSCODE_TELEMETRY_RUNTIME_POLICY_VERSION") or ""
    )
    schema_name = _extract_string_const(policy_src, "VSCODE_TELEMETRY_EVENT_SCHEMA_NAME") or ""
    schema_version = (
        _extract_string_const(policy_src, "VSCODE_TELEMETRY_EVENT_SCHEMA_VERSION") or ""
    )
    client = _extract_string_const(events_src, "VSCODE_CLIENT_NAME") or ""

    # Intentional differences documented in catalogMapping.
    vscode_only = ("extension_version",)
    engine_only_events = ("application_started", "application_completed")

    return VsCodeTelemetryInventory(
        telemetry_dir=telemetry_dir,
        runtime_policy_id=policy_id,
        runtime_policy_version=policy_version,
        runtime_policy_urn=f"{policy_id}:{policy_version}" if policy_id and policy_version else "",
        event_schema_name=schema_name,
        event_schema_version=schema_version,
        client_name=client,
        approved_event_types=_extract_string_array(events_src, "APPROVED_EVENT_TYPES"),
        approved_field_names=_extract_string_array(events_src, "APPROVED_FIELD_NAMES"),
        eligible_commands=_extract_string_array(prompt_src, "ELIGIBLE_TELEMETRY_COMMANDS"),
        excluded_commands=_extract_string_array(prompt_src, "EXCLUDED_TELEMETRY_COMMANDS"),
        forbidden_name_fragments=_extract_string_array(privacy_src, "FORBIDDEN_NAME_FRAGMENTS"),
        shared_conceptual_fields=_extract_string_array(mapping_src, "SHARED_CONCEPTUAL_FIELDS"),
        engine_only_event_types=engine_only_events,
        vscode_only_fields=vscode_only,
        source_blob=blob + "\n" + consent_src,
    )


def vscode_source_mentions(inventory: VsCodeTelemetryInventory, token: str) -> bool:
    return token in inventory.source_blob
