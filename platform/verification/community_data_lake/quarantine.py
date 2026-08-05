"""Quarantine storage checks across in-memory and fake-S3 adapters (Slice 8.14)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
    CommunityDataLakeS3Store,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore

from verification.community_data_lake.fake_s3 import FakeS3Client
from verification.community_data_lake.inputs import (
    project_quarantine_object,
    project_stream_storage_object,
)
from verification.community_data_lake.models import CheckResult

POLICY = CommunityDataLakePolicy.default()
S3_CONFIG = S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name")


def _run_quarantine_scenario(
    store: InMemoryCommunityDataLakeStore | CommunityDataLakeS3Store,
    *,
    adapter: str,
    client: FakeS3Client | None = None,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    obj = project_quarantine_object()
    first = store.put_immutable_quarantine_object(obj)
    second = store.put_immutable_quarantine_object(obj)
    checks.extend(
        [
            CheckResult(
                name=f"quarantine:{adapter}:first_write_stored",
                ok=first.status is StorageWriteStatus.STORED,
                detail=str(first.status.value),
                category="quarantine",
            ),
            CheckResult(
                name=f"quarantine:{adapter}:exact_retry_already_exists",
                ok=second.status is StorageWriteStatus.ALREADY_EXISTS,
                detail=str(second.status.value),
                category="quarantine",
            ),
            CheckResult(
                name=f"quarantine:{adapter}:key_under_quarantine_prefix",
                ok=obj.object_key.startswith("quarantine/"),
                detail="prefix ok" if obj.object_key.startswith("quarantine/") else "bad prefix",
                category="quarantine",
            ),
            CheckResult(
                name=f"quarantine:{adapter}:no_raw_prefix",
                ok=not obj.object_key.startswith("raw/"),
                detail="not raw/",
                category="quarantine",
            ),
        ]
    )

    conflict_obj = project_quarantine_object(limitations=("different",))
    conflict = store.put_immutable_quarantine_object(conflict_obj)
    checks.append(
        CheckResult(
            name=f"quarantine:{adapter}:conflict_detected",
            ok=conflict.status is StorageWriteStatus.CONFLICT,
            detail=str(conflict.status.value),
            category="quarantine",
        )
    )

    type_store = InMemoryCommunityDataLakeStore(policy=POLICY)
    if isinstance(store, CommunityDataLakeS3Store):
        type_store = CommunityDataLakeS3Store(
            config=S3_CONFIG, policy=POLICY, client=FakeS3Client()
        )
    quarantine_obj = project_quarantine_object()
    accepted_obj = project_stream_storage_object("telemetry")
    rejected_accepted = type_store.put_immutable_storage_object(quarantine_obj)  # type: ignore[arg-type]
    rejected_quarantine = type_store.put_immutable_quarantine_object(accepted_obj)  # type: ignore[arg-type]
    checks.extend(
        [
            CheckResult(
                name=f"quarantine:{adapter}:reject_quarantine_via_accepted_method",
                ok=rejected_accepted.status is StorageWriteStatus.REJECTED,
                detail=str(rejected_accepted.status.value),
                category="quarantine",
            ),
            CheckResult(
                name=f"quarantine:{adapter}:reject_accepted_via_quarantine_method",
                ok=rejected_quarantine.status is StorageWriteStatus.REJECTED,
                detail=str(rejected_quarantine.status.value),
                category="quarantine",
            ),
        ]
    )

    if client is not None and first.status is StorageWriteStatus.STORED:
        put_kwargs = client.last_put_kwargs()
        stored = client.objects[first.object_key]
        checks.extend(
            [
                CheckResult(
                    name=f"quarantine:{adapter}:s3_if_none_match",
                    ok=put_kwargs.get("IfNoneMatch") == "*",
                    detail="IfNoneMatch=*",
                    category="quarantine",
                ),
                CheckResult(
                    name=f"quarantine:{adapter}:s3_body_exact",
                    ok=stored["Body"] == obj.canonical_json_bytes,
                    detail="bytes match",
                    category="quarantine",
                ),
            ]
        )

    return checks


def check_quarantine_in_memory() -> list[CheckResult]:
    store = InMemoryCommunityDataLakeStore(policy=POLICY)
    return _run_quarantine_scenario(store, adapter="in_memory")


def check_quarantine_fake_s3() -> list[CheckResult]:
    client = FakeS3Client()
    store = CommunityDataLakeS3Store(config=S3_CONFIG, policy=POLICY, client=client)
    return _run_quarantine_scenario(store, adapter="fake_s3", client=client)


__all__ = ["check_quarantine_fake_s3", "check_quarantine_in_memory"]
