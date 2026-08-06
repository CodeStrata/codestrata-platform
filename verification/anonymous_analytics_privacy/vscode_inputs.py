"""Static VS Code analytics inventory (parse TypeScript; no Python↔TS runtime dep)."""

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
class VsCodeAnalyticsInventory:
    analytics_dir: Path
    policy_id: str
    policy_version: str
    policy_urn: str
    schema_id: str
    schema_version: str
    schema_urn: str
    client_name: str
    editor: str
    approved_fields: tuple[str, ...]
    forbidden_fields: tuple[str, ...]
    operation_categories: tuple[str, ...]
    source_blob: str
    package_json_text: str
    has_http_imports: bool
    has_machine_id_reads: bool
    has_engine_identity_reads: bool
    has_uuid_generation: bool


def load_vscode_analytics_inventory(monorepo: Path) -> VsCodeAnalyticsInventory:
    analytics_dir = monorepo / "vscode-plugin" / "src" / "telemetry" / "analytics"
    sources: dict[str, str] = {}
    if analytics_dir.is_dir():
        for path in sorted(analytics_dir.glob("*.ts")):
            sources[path.name] = path.read_text(encoding="utf-8")
    blob = "\n".join(sources[name] for name in sorted(sources))

    policy_src = sources.get("runtimePolicy.ts", "")
    schema_src = sources.get("schema.ts", "")

    policy_id = (
        _extract_string_const(policy_src, "COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_ID")
        or ""
    )
    policy_version = (
        _extract_string_const(
            policy_src, "COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_POLICY_VERSION"
        )
        or ""
    )
    schema_id = (
        _extract_string_const(policy_src, "COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_ID")
        or _extract_string_const(schema_src, "COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_ID")
        or ""
    )
    schema_version = (
        _extract_string_const(
            policy_src, "COMMUNITY_VSCODE_ANONYMOUS_ANALYTICS_SCHEMA_VERSION"
        )
        or "1.0"
    )
    client = _extract_string_const(schema_src, "VSCODE_ANALYTICS_CLIENT_NAME") or ""
    editor = _extract_string_const(schema_src, "VSCODE_ANALYTICS_EDITOR") or ""

    package_json = monorepo / "vscode-plugin" / "package.json"
    package_text = package_json.read_text(encoding="utf-8") if package_json.is_file() else ""

    lower = blob.lower()
    return VsCodeAnalyticsInventory(
        analytics_dir=analytics_dir,
        policy_id=policy_id,
        policy_version=policy_version,
        policy_urn=f"{policy_id}:{policy_version}" if policy_id and policy_version else "",
        schema_id=schema_id,
        schema_version=schema_version,
        schema_urn=f"{schema_id}:{schema_version}" if schema_id and schema_version else "",
        client_name=client,
        editor=editor,
        approved_fields=_extract_string_array(schema_src, "APPROVED_ANALYTICS_FIELD_NAMES"),
        forbidden_fields=_extract_string_array(schema_src, "FORBIDDEN_ANALYTICS_FIELD_NAMES"),
        operation_categories=_extract_string_array(
            schema_src, "APPROVED_ANALYTICS_OPERATION_CATEGORIES"
        ),
        source_blob=blob,
        package_json_text=package_text,
        has_http_imports=any(
            token in blob
            for token in ("node:http", "node:https", "fetch(", "axios", "undici")
        ),
        # Forbidden-field allowlist entries are not reads. Detect API access only.
        has_machine_id_reads=bool(
            re.search(r"env\.machineId|\.machineId\b|telemetrySessionId\s*[,)]", blob)
        ),
        has_engine_identity_reads="anonymous-installation-identity" in blob,
        has_uuid_generation=bool(
            re.search(r"randomUUID\s*\(|uuid\.v4\s*\(|crypto\.randomUUID", blob)
        ),
    )
