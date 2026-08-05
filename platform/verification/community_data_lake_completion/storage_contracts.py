"""Storage abstraction contract checks for completion verification (Slice 8.15)."""

from __future__ import annotations

import inspect

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.infrastructure.unavailable_store import (
    UnavailableCommunityDataLakeStore,
)
from codestrata_platform.community_cloud_api.data_lake.ports import CommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.storage import (
    CommunityDataLakeStoragePolicy,
    default_storage_policy,
)
from codestrata_platform.community_cloud_api.data_lake.storage_configuration import (
    DataLakeStorageConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.storage_factory import (
    create_community_data_lake_store,
)

from verification.community_data_lake.inputs import (
    project_quarantine_object,
    project_stream_storage_object,
)
from verification.community_data_lake_completion.models import CheckResult


def check_storage_contracts() -> list[CheckResult]:
    checks: list[CheckResult] = []
    protocol_source = inspect.getsource(CommunityDataLakeStore)
    checks.extend(
        [
            CheckResult(
                name="storage:protocol_put_immutable_storage_object",
                ok="put_immutable_storage_object" in protocol_source,
                detail="present",
                category="storage",
            ),
            CheckResult(
                name="storage:protocol_put_immutable_quarantine_object",
                ok="put_immutable_quarantine_object" in protocol_source,
                detail="present",
                category="storage",
            ),
            CheckResult(
                name="storage:protocol_no_list_delete_admin",
                ok=all(
                    token not in protocol_source.lower()
                    for token in ("list_objects", "delete_object", "delete_objects", "admin")
                ),
                detail="no list/delete/admin in Protocol",
                category="storage",
            ),
        ]
    )

    policy = default_storage_policy()
    checks.extend(
        [
            CheckResult(
                name="storage:policy_projected_object_authority",
                ok=policy.projected_object_authority is True,
                detail="projected_object_authority",
                category="storage",
            ),
            CheckResult(
                name="storage:policy_envelope_put_not_authoritative",
                ok=policy.envelope_put_authoritative is False,
                detail="envelope_put_authoritative",
                category="storage",
            ),
            CheckResult(
                name="storage:policy_no_list_delete",
                ok=not policy.list_allowed and not policy.delete_allowed,
                detail="list/delete false",
                category="storage",
            ),
        ]
    )

    unavailable = create_community_data_lake_store()
    accepted = unavailable.put_immutable_storage_object(
        project_stream_storage_object("telemetry")
    )
    quarantine = unavailable.put_immutable_quarantine_object(project_quarantine_object())
    in_memory = create_community_data_lake_store(
        DataLakeStorageConfiguration.in_memory_test()
    )
    type_mix = in_memory.put_immutable_storage_object(project_quarantine_object())  # type: ignore[arg-type]

    checks.extend(
        [
            CheckResult(
                name="storage:factory_default_unavailable",
                ok=isinstance(unavailable, UnavailableCommunityDataLakeStore),
                detail="unavailable adapter",
                category="storage",
            ),
            CheckResult(
                name="storage:unavailable_never_stored_accepted",
                ok=accepted.status != StorageWriteStatus.STORED,
                detail=accepted.status.value,
                category="storage",
            ),
            CheckResult(
                name="storage:unavailable_never_stored_quarantine",
                ok=quarantine.status != StorageWriteStatus.STORED,
                detail=quarantine.status.value,
                category="storage",
            ),
            CheckResult(
                name="storage:type_mix_rejected",
                ok=type_mix.status
                in {StorageWriteStatus.REJECTED, StorageWriteStatus.UNAVAILABLE},
                detail=type_mix.status.value,
                category="storage",
            ),
        ]
    )

    policy.validate()
    checks.append(
        CheckResult(
            name="storage:policy_validates",
            ok=isinstance(policy, CommunityDataLakeStoragePolicy),
            detail=policy.policy_token,
            category="storage",
        )
    )
    return checks


__all__ = ["check_storage_contracts"]
