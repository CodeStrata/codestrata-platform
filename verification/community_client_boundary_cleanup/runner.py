"""Slice 12.4 runner."""

from __future__ import annotations

import shutil
from pathlib import Path

from verification.community_client_boundary_cleanup import (
    COMMUNITY_CLIENT_BOUNDARY_CLEANUP_ID,
)
from verification.community_client_boundary_cleanup.active_clients import (
    active_client_inventory,
    check_active_clients,
    retired_client_inventory,
)
from verification.community_client_boundary_cleanup.api_contracts import check_api_contracts
from verification.community_client_boundary_cleanup.contract import (
    REPORT_JSON,
    SCHEMA_COMPATIBILITY_DECISION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SV124_OUTPUT_RELATIVE,
    default_contract,
    monorepo_root_from_here,
)
from verification.community_client_boundary_cleanup.data_lake_boundary import (
    check_data_lake_boundary,
)
from verification.community_client_boundary_cleanup.determinism import (
    check_determinism,
    check_report_safety,
)
from verification.community_client_boundary_cleanup.engine_analytics import (
    check_engine_analytics,
)
from verification.community_client_boundary_cleanup.engine_telemetry import (
    check_engine_telemetry,
)
from verification.community_client_boundary_cleanup.envelope_compatibility import (
    check_envelope_compatibility,
)
from verification.community_client_boundary_cleanup.inventory import check_inventory
from verification.community_client_boundary_cleanup.metadata_compatibility import (
    check_metadata_compatibility,
)
from verification.community_client_boundary_cleanup.models import (
    CheckResult,
    CommunityClientBoundaryCleanupReport,
    Defect,
    Verdict,
)
from verification.community_client_boundary_cleanup.partition_compatibility import (
    check_partition_compatibility,
)
from verification.community_client_boundary_cleanup.platform_boundary import (
    check_platform_boundary,
)
from verification.community_client_boundary_cleanup.privacy import check_privacy
from verification.community_client_boundary_cleanup.production_fail_closed import (
    check_production_fail_closed,
)
from verification.community_client_boundary_cleanup.quarantine import check_quarantine
from verification.community_client_boundary_cleanup.reporting import write_verification_outputs
from verification.community_client_boundary_cleanup.retired_clients import check_retired_policy
from verification.community_client_boundary_cleanup.scenarios import check_scenarios
from verification.community_client_boundary_cleanup.schema_decision import (
    check_schema_decision,
)
from verification.community_client_boundary_cleanup.vscode_runtime import check_vscode_runtime


def _status(checks: list[CheckResult]) -> str:
    if not checks:
        return "not_executed"
    return "pass" if all(c.ok for c in checks) else "fail"


def _decide(failed: int, defects: list[Defect], limitations: list[str]) -> Verdict:
    if failed or defects:
        return "FAIL"
    if limitations:
        return "PASS_WITH_LIMITATIONS"
    return "PASS"


def build_report(monorepo: Path) -> CommunityClientBoundaryCleanupReport:
    contract = default_contract()
    assert contract.start_slice_12_5 is False
    assert contract.no_s3_migration is True
    assert contract.no_stored_event_rewrite is True

    all_checks: list[CheckResult] = []
    all_defects: list[Defect] = []
    buckets: dict[str, list[CheckResult]] = {}

    def take(name: str, pair: tuple[list[CheckResult], list[Defect]]) -> None:
        c, d = pair
        buckets[name] = c
        all_checks.extend(c)
        all_defects.extend(d)

    take("inventory", check_inventory(monorepo))
    take("active", check_active_clients(monorepo))
    take("retired", check_retired_policy(monorepo))
    take("engine_telemetry", check_engine_telemetry(monorepo))
    take("engine_analytics", check_engine_analytics(monorepo))
    take("vscode", check_vscode_runtime(monorepo))
    take("api", check_api_contracts(monorepo))
    take("envelope", check_envelope_compatibility(monorepo))
    take("partition", check_partition_compatibility(monorepo))
    take("metadata", check_metadata_compatibility(monorepo))
    take("quarantine", check_quarantine(monorepo))
    take("privacy", check_privacy(monorepo))
    take("production", check_production_fail_closed(monorepo))
    take("schema", check_schema_decision(monorepo))
    take("platform", check_platform_boundary(monorepo))
    take("data_lake", check_data_lake_boundary(monorepo))
    take("scenarios", check_scenarios(monorepo))

    limitations = [
        "historical cursor_extension retained for schema 1.0 deserialize (Approach A)",
        "no live production ingestion validation",
        "no real stored-object migration test",
        "historical verification reports retain Cursor references",
        "Infrastructure repository work deferred to Slice 12.5",
        "telemetry other_extension remains on public telemetry contract",
    ]

    failed = sum(1 for c in all_checks if not c.ok)
    verdict = _decide(failed, all_defects, limitations)

    return CommunityClientBoundaryCleanupReport(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        verification_id=COMMUNITY_CLIENT_BOUNDARY_CLEANUP_ID,
        verdict=verdict,
        active_client_inventory=active_client_inventory(),
        retired_client_inventory=retired_client_inventory(),
        schema_compatibility_decision=SCHEMA_COMPATIBILITY_DECISION,
        engine_telemetry_status=_status(buckets.get("engine_telemetry", [])),
        engine_analytics_status=_status(buckets.get("engine_analytics", [])),
        vscode_runtime_status=_status(buckets.get("vscode", [])),
        current_api_status=_status(buckets.get("api", [])),
        historical_deserialization_status=_status(buckets.get("envelope", [])),
        envelope_compatibility_status=_status(buckets.get("envelope", [])),
        partition_compatibility_status=_status(buckets.get("partition", [])),
        metadata_compatibility_status=_status(buckets.get("metadata", [])),
        quarantine_status=_status(buckets.get("quarantine", [])),
        production_fail_closed_status=_status(buckets.get("production", [])),
        platform_boundary_status=_status(buckets.get("platform", [])),
        data_lake_boundary_status=_status(buckets.get("data_lake", [])),
        privacy_status=_status(buckets.get("privacy", [])),
        migration_required=False,
        rewrite_required=False,
        defects=all_defects,
        blockers=[],
        limitations=limitations,
        total_checks=len(all_checks),
        failed_checks=failed,
        checks=all_checks,
    )


def run_community_client_boundary_cleanup_verification(
    *,
    output_dir: Path | None = None,
    monorepo: Path | None = None,
) -> CommunityClientBoundaryCleanupReport:
    root = monorepo or monorepo_root_from_here()
    out = output_dir or (root / SV124_OUTPUT_RELATIVE)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    first = build_report(root)
    second = build_report(root)
    det_checks, det_defects = check_determinism(first, second)
    first.checks.extend(det_checks)
    first.defects.extend(det_defects)
    first.total_checks = len(first.checks)
    first.failed_checks = sum(1 for c in first.checks if not c.ok)
    if det_defects or first.failed_checks:
        first.verdict = "FAIL"
    elif first.limitations:
        first.verdict = "PASS_WITH_LIMITATIONS"

    json_path, _md = write_verification_outputs(first, out)
    safety_checks, safety_defects = check_report_safety(json_path)
    first.checks.extend(safety_checks)
    first.defects.extend(safety_defects)
    first.total_checks = len(first.checks)
    first.failed_checks = sum(1 for c in first.checks if not c.ok)
    if safety_defects or first.failed_checks:
        first.verdict = "FAIL"
    elif first.limitations and first.verdict != "FAIL":
        first.verdict = "PASS_WITH_LIMITATIONS"
    # Rewrite after safety so final report includes determinism/safety checks.
    write_verification_outputs(first, out)
    return first
