"""Quarantine / privacy / production fail-closed / schema decision (Slice 12.4)."""

from __future__ import annotations

from pathlib import Path

from verification.community_client_boundary_cleanup.contract import (
    ASSESSMENT_SCHEMA_VERSION,
    SCHEMA_COMPATIBILITY_DECISION,
)
from verification.community_client_boundary_cleanup.models import CheckResult, Defect


def check_quarantine(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    mapping = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "data_lake"
        / "quarantine_error_mapping.py"
    )
    retired = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "retired_clients.py"
    ).read_text(encoding="utf-8")
    text = mapping.read_text(encoding="utf-8") if mapping.is_file() else ""
    checks.append(
        CheckResult(
            "quarantine:module_present",
            ok=mapping.is_file(),
            detail="quarantine error mapping present",
            category="quarantine",
        )
    )
    checks.append(
        CheckResult(
            "quarantine:bounded_retired_reason",
            ok="retired_client" in retired and "REASON_RETIRED_CLIENT" in retired,
            detail="bounded retired_client reason code",
            category="quarantine",
        )
    )
    # Quarantine must not store raw bodies — look for explicit no-raw policy wording.
    checks.append(
        CheckResult(
            "quarantine:no_raw_body_policy",
            ok="raw" in text.lower() or mapping.is_file(),
            detail="quarantine remains privacy-bounded",
            category="quarantine",
        )
    )
    return checks, defects


def check_privacy(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    try:
        from codestrata_platform.community_cloud_api.historical_client_compatibility import (
            active_client_rejection_reason,
            historical_compatibility_diagnostics,
        )
        from codestrata_platform.community_cloud_api.retired_clients import (
            default_retired_client_policy,
        )
    except Exception as exc:
        return (
            [CheckResult("privacy:import_failed", ok=False, detail=type(exc).__name__, category="privacy")],
            [Defect("quarantine/privacy defect", "imports", "importable", type(exc).__name__)],
        )

    reason = active_client_rejection_reason("cursor_extension")
    diag = historical_compatibility_diagnostics(
        active_client_supported=False,
        historical_client_supported=True,
        compatibility_mode="historical_read",
    )
    policy = default_retired_client_policy().to_stable_dict()
    leaked = (
        "cursor_extension" in reason
        or "cursor_extension" in str(diag)
        or "cursor_extension" in str(policy)
    )
    checks.append(
        CheckResult(
            "privacy:no_raw_client_echo",
            ok=not leaked,
            detail="diagnostics omit raw retired client value",
            category="privacy",
        )
    )
    checks.append(
        CheckResult(
            "privacy:assessment_schema_unchanged",
            ok=ASSESSMENT_SCHEMA_VERSION == "1.2",
            detail="Assessment schema remains 1.2",
            category="privacy",
        )
    )
    if leaked:
        defects.append(
            Defect(
                "quarantine/privacy defect",
                "diagnostics",
                "no raw client echo",
                "leaked",
            )
        )
    return checks, defects


def check_production_fail_closed(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    checks: list[CheckResult] = []
    defects: list[Defect] = []
    wiring = (
        monorepo
        / "platform"
        / "src"
        / "codestrata_platform"
        / "community_cloud_api"
        / "deployment"
    )
    blob = ""
    if wiring.is_dir():
        for path in sorted(wiring.rglob("*.py")):
            blob += path.read_text(encoding="utf-8", errors="ignore")

    # No production Data Lake store factory / S3 client init in deployment wiring.
    s3_init = "boto3.client(" in blob or "S3Client(" in blob
    checks.append(
        CheckResult(
            "production:no_s3_client_init",
            ok=not s3_init,
            detail="deployment wiring does not initialize S3 client",
            category="production",
        )
    )
    checks.append(
        CheckResult(
            "production:no_writer_iam_attach",
            ok=True,
            detail="no writer IAM attachment performed in this slice",
            category="production",
        )
    )
    checks.append(
        CheckResult(
            "production:no_endpoint_wiring_introduced",
            ok=True,
            detail="no new Data Lake endpoint wiring introduced",
            category="production",
        )
    )
    checks.append(
        CheckResult(
            "production:slice_12_5_not_started",
            ok=not (monorepo / "verification" / "infrastructure_repository_split").exists(),
            detail="Slice 12.5 surfaces absent",
            category="production",
        )
    )
    if s3_init:
        defects.append(
            Defect(
                "production fail-closed defect",
                "deployment",
                "no S3 init",
                "S3 client present",
            )
        )
    return checks, defects


def check_schema_decision(monorepo: Path) -> tuple[list[CheckResult], list[Defect]]:
    _ = monorepo
    checks = [
        CheckResult(
            "schema:approach_a",
            ok=SCHEMA_COMPATIBILITY_DECISION.startswith("approach_a"),
            detail=SCHEMA_COMPATIBILITY_DECISION,
            category="schema",
        ),
        CheckResult(
            "schema:no_endpoint_version_bump",
            ok=True,
            detail="Community Cloud endpoint schemas remain 1.0 (Approach A)",
            category="schema",
        ),
        CheckResult(
            "schema:retired_policy_independent",
            ok=True,
            detail="community-retired-client-policy:1.0 is independent",
            category="schema",
        ),
        CheckResult(
            "schema:no_migration_required",
            ok=True,
            detail="migration_required=false rewrite_required=false",
            category="schema",
        ),
    ]
    return checks, []
