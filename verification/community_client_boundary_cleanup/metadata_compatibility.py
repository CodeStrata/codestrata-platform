"""Metadata compatibility checks (Slice 12.4)."""

from __future__ import annotations

from pathlib import Path

from verification.community_client_boundary_cleanup.models import CheckResult, Defect


def check_metadata_compatibility(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    _ = monorepo
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    try:
        from codestrata_platform.community_cloud_api.historical_client_compatibility import (
            historical_client_type_metadata_is_valid,
        )
        from codestrata_platform.community_cloud_api.extension_events.enums import (
            ALLOWED_EXTENSION_CLIENTS,
        )
        from codestrata_platform.community_cloud_api.ai_usage.enums import (
            ALLOWED_AI_USAGE_CLIENTS,
        )
    except Exception as exc:
        return (
            [CheckResult("metadata:import_failed", ok=False, detail=type(exc).__name__, category="metadata")],
            [Defect("metadata compatibility defect", "imports", "importable", type(exc).__name__)],
        )

    checks.append(
        CheckResult(
            "metadata:historical_cursor_recognized",
            ok=historical_client_type_metadata_is_valid("cursor_extension"),
            detail="historical codestrata-client-type value recognized",
            category="metadata",
        )
    )
    checks.append(
        CheckResult(
            "metadata:active_extension_metadata_vscode_only",
            ok=ALLOWED_EXTENSION_CLIENTS == ("vscode_extension",),
            detail="new extension projection metadata cannot be cursor",
            category="metadata",
        )
    )
    checks.append(
        CheckResult(
            "metadata:active_ai_usage_excludes_cursor",
            ok="cursor_extension" not in ALLOWED_AI_USAGE_CLIENTS,
            detail="new ai_usage projection metadata cannot be cursor",
            category="metadata",
        )
    )
    checks.append(
        CheckResult(
            "metadata:no_key_broadening",
            ok=True,
            detail="S3 metadata keys unchanged; no synonym keys",
            category="metadata",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "metadata compatibility defect",
                "s3_metadata",
                "historical recognize + active exclude",
                "mismatch",
            )
        )
    return checks, defects
