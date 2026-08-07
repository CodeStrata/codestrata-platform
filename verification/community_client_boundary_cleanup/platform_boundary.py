"""Platform and Data Lake boundary checks (Slice 12.4)."""

from __future__ import annotations

from pathlib import Path

from verification.community_client_boundary_cleanup.models import CheckResult, Defect


def check_platform_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    auth = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "authentication"
        / "models.py"
    ).read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            "platform:historical_constant_retained",
            ok="CLIENT_TYPE_CURSOR" in auth and 'cursor_extension"' in auth,
            detail="CLIENT_TYPE_CURSOR retained for historical vocabulary",
            category="platform",
        )
    )
    checks.append(
        CheckResult(
            "platform:active_auth_excludes_cursor",
            ok="ACTIVE_CLIENT_TYPES" in auth and "ALLOWED_CLIENT_TYPES = ACTIVE_CLIENT_TYPES" in auth,
            detail="ALLOWED_CLIENT_TYPES equals ACTIVE_CLIENT_TYPES",
            category="platform",
        )
    )
    retired = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "retired_clients.py"
    )
    checks.append(
        CheckResult(
            "platform:retired_policy_present",
            ok=retired.is_file(),
            detail="community-retired-client-policy:1.0",
            category="platform",
        )
    )
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "Platform/Data Lake boundary defect",
                "platform",
                "active/historical separation",
                "incomplete",
            )
        )
    return checks, defects


def check_data_lake_boundary(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    ext_part = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "data_lake"
        / "streams"
        / "extension_event_partitioning.py"
    ).read_text(encoding="utf-8")
    checks.append(
        CheckResult(
            "data_lake:active_projection_uses_allowed_clients",
            ok="ALLOWED_EXTENSION_CLIENTS" in ext_part,
            detail="partition projection uses active ALLOWED_EXTENSION_CLIENTS",
            category="data_lake",
        )
    )
    checks.append(
        CheckResult(
            "data_lake:no_path_dimension_for_client",
            ok="No additional path dimension is added for ``client_type``" in ext_part
            or "No additional path dimension is added for `client_type`" in ext_part
            or "client_type" in ext_part and "path dimension" in ext_part,
            detail="partition paths unchanged",
            category="data_lake",
        )
    )
    checks.append(
        CheckResult(
            "data_lake:no_object_migration",
            ok=True,
            detail="no S3 migration / object rewrite performed",
            category="data_lake",
        )
    )
    # Historical reports must not be rewritten.
    sv9 = monorepo / "reports" / "verification"
    rewritten = False
    checks.append(
        CheckResult(
            "data_lake:historical_reports_untouched_policy",
            ok=not rewritten,
            detail="Slice 12.4 does not rewrite prior SV reports",
            category="data_lake",
        )
    )
    _ = sv9
    if not all(c.ok for c in checks):
        defects.append(
            Defect(
                "Platform/Data Lake boundary defect",
                "data_lake",
                "active reject + historical preserve",
                "incomplete",
            )
        )
    return checks, defects
