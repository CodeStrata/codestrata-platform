"""Storage adapter factory and parity matrix checks (Slice 8.14)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.unavailable_store import (
    UnavailableCommunityDataLakeStore,
)
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.storage_configuration import (
    DataLakeStorageConfiguration,
    StorageAdapterType,
)
from codestrata_platform.community_cloud_api.data_lake.storage_factory import (
    create_community_data_lake_store,
)
from codestrata_platform.community_cloud_api.data_lake.storage_validation import (
    StorageValidationError,
)

from verification.community_data_lake.fake_s3 import FakeS3Client
from verification.community_data_lake.inputs import (
    project_conflict_peer,
    project_conflict_storage_object,
    project_quarantine_object,
    project_stream_storage_object,
)
from verification.community_data_lake.models import CheckResult

S3_CONFIG = S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name")


def _status_label(result_status: StorageWriteStatus) -> str:
    return result_status.value


def _run_accepted_first_write(store: Any) -> str:
    obj = project_stream_storage_object("telemetry")
    return _status_label(store.put_immutable_storage_object(obj).status)


def _run_accepted_exact_retry(store: Any) -> str:
    obj = project_stream_storage_object("cli_event")
    store.put_immutable_storage_object(obj)
    return _status_label(store.put_immutable_storage_object(obj).status)


def _run_accepted_conflict(store: Any) -> str:
    first = project_conflict_storage_object("telemetry")
    second = project_conflict_peer("telemetry")
    store.put_immutable_storage_object(first)
    return _status_label(store.put_immutable_storage_object(second).status)


def _run_invalid_type(store: Any) -> str:
    quarantine_obj = project_quarantine_object()
    return _status_label(store.put_immutable_storage_object(quarantine_obj).status)  # type: ignore[arg-type]


def _run_quarantine_first_write(store: Any) -> str:
    obj = project_quarantine_object()
    return _status_label(store.put_immutable_quarantine_object(obj).status)


def check_adapter_parity_matrix() -> tuple[list[CheckResult], dict[str, dict[str, str]]]:
    matrix: dict[str, dict[str, str]] = {}
    checks: list[CheckResult] = []

    unavailable = create_community_data_lake_store()
    in_memory = create_community_data_lake_store(DataLakeStorageConfiguration.in_memory_test())
    fake_s3 = create_community_data_lake_store(
        DataLakeStorageConfiguration.s3(),
        s3_config=S3_CONFIG,
        s3_client=FakeS3Client(),
    )

    scenarios = {
        "accepted_first_write": _run_accepted_first_write,
        "accepted_exact_retry": _run_accepted_exact_retry,
        "accepted_conflict": _run_accepted_conflict,
        "invalid_type": _run_invalid_type,
        "quarantine_first_write": _run_quarantine_first_write,
    }

    for adapter_name, store in (
        ("unavailable", unavailable),
        ("in_memory", in_memory),
        ("fake_s3", fake_s3),
    ):
        row: dict[str, str] = {}
        for scenario_name, runner in scenarios.items():
            outcome = runner(store)
            row[scenario_name] = outcome
        matrix[adapter_name] = row

    expected = {
        "unavailable": {
            "accepted_first_write": "unavailable",
            "accepted_exact_retry": "unavailable",
            "accepted_conflict": "unavailable",
            "invalid_type": "rejected",
            "quarantine_first_write": "unavailable",
        },
        "in_memory": {
            "accepted_first_write": "stored",
            "accepted_exact_retry": "already_exists",
            "accepted_conflict": "conflict",
            "invalid_type": "rejected",
            "quarantine_first_write": "stored",
        },
        "fake_s3": {
            "accepted_first_write": "stored",
            "accepted_exact_retry": "already_exists",
            "accepted_conflict": "conflict",
            "invalid_type": "rejected",
            "quarantine_first_write": "stored",
        },
    }

    for adapter, row in expected.items():
        for scenario, want in row.items():
            got = matrix[adapter][scenario]
            checks.append(
                CheckResult(
                    name=f"storage:matrix:{adapter}:{scenario}",
                    ok=got == want,
                    detail=f"got={got} want={want}",
                    category="storage",
                    scenario=scenario,
                )
            )

    return checks, matrix


def check_storage_factory() -> list[CheckResult]:
    checks: list[CheckResult] = []

    default_store = create_community_data_lake_store()
    checks.append(
        CheckResult(
            name="storage:factory:default_unavailable",
            ok=isinstance(default_store, UnavailableCommunityDataLakeStore),
            detail=type(default_store).__name__,
            category="storage",
        )
    )

    in_memory = create_community_data_lake_store(
        DataLakeStorageConfiguration.in_memory_test()
    )
    checks.append(
        CheckResult(
            name="storage:factory:in_memory_requires_allow",
            ok=isinstance(in_memory, InMemoryCommunityDataLakeStore),
            detail=type(in_memory).__name__,
            category="storage",
        )
    )

    blocked = SimpleNamespace(
        adapter_type=StorageAdapterType.IN_MEMORY_TEST,
        allow_in_memory_test=False,
    )
    blocked_ok = False
    try:
        create_community_data_lake_store(blocked)  # type: ignore[arg-type]
    except StorageValidationError:
        blocked_ok = True
    checks.append(
        CheckResult(
            name="storage:factory:in_memory_without_allow_fails",
            ok=blocked_ok,
            detail="StorageValidationError",
            category="storage",
        )
    )

    s3_missing_config_ok = False
    try:
        create_community_data_lake_store(DataLakeStorageConfiguration.s3())
    except StorageValidationError:
        s3_missing_config_ok = True
    checks.append(
        CheckResult(
            name="storage:factory:s3_requires_config",
            ok=s3_missing_config_ok,
            detail="StorageValidationError",
            category="storage",
        )
    )

    wrong_mode_ok = False
    bad = SimpleNamespace(adapter_type="not_a_mode", allow_in_memory_test=False)
    try:
        create_community_data_lake_store(bad)  # type: ignore[arg-type]
    except StorageValidationError:
        wrong_mode_ok = True
    checks.append(
        CheckResult(
            name="storage:factory:wrong_mode_fails",
            ok=wrong_mode_ok,
            detail="StorageValidationError",
            category="storage",
        )
    )

    s3_store = create_community_data_lake_store(
        DataLakeStorageConfiguration.s3(),
        s3_config=S3_CONFIG,
        s3_client=FakeS3Client(),
    )
    from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
        CommunityDataLakeS3Store,
    )

    checks.append(
        CheckResult(
            name="storage:factory:s3_with_injected_client",
            ok=isinstance(s3_store, CommunityDataLakeS3Store),
            detail=type(s3_store).__name__,
            category="storage",
        )
    )

    return checks


__all__ = ["check_adapter_parity_matrix", "check_storage_factory"]
