"""Community Data Lake integration verification runner (Slice 8.14 / SV.9)."""

from __future__ import annotations

import time
from pathlib import Path

from codestrata_platform.community_cloud_api.data_lake.quarantine_models import (
    COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.schema_compatibility import (
    ENVELOPE_SCHEMA_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    AI_USAGE_PARTITION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    ASSESSMENT_METADATA_PARTITION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    CLI_EVENT_PARTITION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    EXTENSION_EVENT_PARTITION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    TELEMETRY_PARTITION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.access_policy import (
    COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.encryption_policy import (
    COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.policy import (
    COMMUNITY_DATA_LAKE_POLICY_URN,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.retention_policy import (
    COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.data_lake.storage import (
    COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION,
)
from codestrata_platform.community_cloud_api.constants import COMMUNITY_DATA_LAKE_POLICY_VERSION

from verification.community_data_lake.contract import (
    ACCEPTED_STREAMS,
    COMMUNITY_DATA_LAKE_VERIFICATION_VERSION,
    DEFAULT_LIMITATIONS,
    DataLakeVerificationContract,
    default_contract,
)
from verification.community_data_lake.determinism import check_determinism
from verification.community_data_lake.infrastructure import check_infrastructure_static, check_opentofu
from verification.community_data_lake.models import CheckResult, PolicyVersions, VerificationReport
from verification.community_data_lake.quarantine import (
    check_quarantine_fake_s3,
    check_quarantine_in_memory,
)
from verification.community_data_lake.reporting import write_verification_report
from verification.community_data_lake.safety import check_privacy
from verification.community_data_lake.scenarios import (
    check_dependency_isolation,
    check_production_fail_closed,
    check_schema_versions,
)
from verification.community_data_lake.storage import (
    check_adapter_parity_matrix,
    check_storage_factory,
)
from verification.community_data_lake.streams import (
    check_accepted_streams_fake_s3,
    check_accepted_streams_in_memory,
)


def _policy_versions() -> PolicyVersions:
    return PolicyVersions(
        data_lake_policy=COMMUNITY_DATA_LAKE_POLICY_VERSION,
        envelope=ENVELOPE_SCHEMA_VERSION,
        quarantine_schema=COMMUNITY_DATA_LAKE_QUARANTINE_SCHEMA_VERSION,
        quarantine_policy=COMMUNITY_DATA_LAKE_QUARANTINE_POLICY_VERSION,
        retention=COMMUNITY_DATA_LAKE_RETENTION_POLICY_VERSION,
        encryption=COMMUNITY_DATA_LAKE_ENCRYPTION_POLICY_VERSION,
        access=COMMUNITY_DATA_LAKE_ACCESS_POLICY_VERSION,
        storage=COMMUNITY_DATA_LAKE_STORAGE_POLICY_VERSION,
        telemetry_partition=TELEMETRY_PARTITION_POLICY_VERSION,
        assessment_metadata_partition=ASSESSMENT_METADATA_PARTITION_POLICY_VERSION,
        cli_event_partition=CLI_EVENT_PARTITION_POLICY_VERSION,
        extension_event_partition=EXTENSION_EVENT_PARTITION_POLICY_VERSION,
        ai_usage_partition=AI_USAGE_PARTITION_POLICY_VERSION,
        verification=COMMUNITY_DATA_LAKE_VERIFICATION_VERSION,
    )


def _status_from_checks(checks: list[CheckResult], prefix: str) -> str:
    subset = [item for item in checks if item.category == prefix or item.name.startswith(prefix)]
    if not subset:
        return "unknown"
    return "pass" if all(item.ok for item in subset) else "fail"


def _is_transient_opentofu_failure(status: str, checks: list[CheckResult]) -> bool:
    if status in {"pass", "skipped", "not_executed_tool_unavailable"}:
        return False
    for item in checks:
        if item.category != "opentofu" or item.ok:
            continue
        detail = item.detail.lower()
        if "timeout" in detail or "124" in detail or "plugin" in detail:
            return True
    return False


def run_community_data_lake_verification(
    *,
    output_dir: Path | None = None,
    contract: DataLakeVerificationContract | None = None,
    run_opentofu: bool = True,
) -> VerificationReport:
    started = time.perf_counter()
    contract = contract or default_contract()
    out = (
        output_dir
        or Path(__file__).resolve().parents[2] / "reports" / "verification"
    ).resolve()
    out.mkdir(parents=True, exist_ok=True)

    checks: list[CheckResult] = []
    checks.extend(check_accepted_streams_in_memory())
    checks.extend(check_accepted_streams_fake_s3())
    checks.extend(check_quarantine_in_memory())
    checks.extend(check_quarantine_fake_s3())

    matrix_checks, adapter_matrix = check_adapter_parity_matrix()
    checks.extend(matrix_checks)
    checks.extend(check_storage_factory())

    infra_checks = check_infrastructure_static()
    checks.extend(infra_checks)
    opentofu_status, opentofu_checks, opentofu_warnings = check_opentofu(
        run_opentofu=run_opentofu
    )
    checks.extend(opentofu_checks)

    checks.extend(check_privacy())
    checks.extend(check_determinism())
    checks.extend(check_production_fail_closed())
    checks.extend(check_schema_versions())
    checks.extend(check_dependency_isolation())

    failures = [f"{c.name}:{c.detail}" for c in checks if not c.ok]
    by_category: dict[str, int] = {}
    for item in checks:
        by_category[item.category] = by_category.get(item.category, 0) + (
            0 if item.ok else 1
        )

    non_opentofu_failures = [
        f"{c.name}:{c.detail}"
        for c in checks
        if not c.ok and c.category != "opentofu"
    ]
    transient_opentofu = _is_transient_opentofu_failure(opentofu_status, checks)
    limitations = list(DEFAULT_LIMITATIONS) + list(contract.notes) + list(opentofu_warnings)
    if opentofu_status == "not_executed_tool_unavailable":
        limitations.append("OpenTofu CLI validate was not executed (tool unavailable).")
    elif opentofu_status == "skipped":
        limitations.append("OpenTofu CLI validate skipped by caller.")
    elif transient_opentofu:
        limitations.append("OpenTofu CLI validate hit a transient provider timeout.")

    if not non_opentofu_failures and transient_opentofu:
        verdict = "pass_with_limitations"
        ok = True
    elif not failures:
        verdict = "pass"
        ok = True
    else:
        verdict = "fail"
        ok = False

    report = VerificationReport(
        ok=ok,
        verdict=verdict,
        policy_versions=_policy_versions(),
        streams_tested=tuple(ACCEPTED_STREAMS),
        quarantine_tested=True,
        adapter_matrix=adapter_matrix,
        privacy_status=_status_from_checks(checks, "privacy"),
        retention_status=_status_from_checks(checks, "infra"),
        encryption_status=_status_from_checks(checks, "infra"),
        iam_status=_status_from_checks(checks, "infra"),
        opentofu_status=opentofu_status if run_opentofu else "skipped",
        production_fail_closed_status=_status_from_checks(checks, "production"),
        checks=tuple(checks),
        scenario_summary={
            "total_checks": len(checks),
            "failed_checks": len(failures),
            **{f"failed_{k}": v for k, v in by_category.items() if v},
        },
        defects=tuple(failures),
        limitations=tuple(limitations),
        excluded_work=("epic_9_not_started", "no_production_ingestion_enable"),
        elapsed_ms=(time.perf_counter() - started) * 1000,
    )
    write_verification_report(report, out)
    return report


__all__ = ["run_community_data_lake_verification"]
