"""Accepted-stream storage checks across in-memory and fake-S3 adapters (Slice 8.14)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.infrastructure.configuration import (
    S3DataLakeStoreConfiguration,
)
from codestrata_platform.community_cloud_api.data_lake.infrastructure.s3_store import (
    CommunityDataLakeS3Store,
)
from codestrata_platform.community_cloud_api.data_lake.objects import BASE_S3_METADATA_KEYS
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    ASSESSMENT_SCHEMA_METADATA_KEY,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    CLIENT_TYPE_METADATA_KEY,
)

from verification.community_data_lake.contract import ACCEPTED_STREAMS
from verification.community_data_lake.fake_s3 import FakeS3Client
from verification.community_data_lake.inputs import (
    project_conflict_peer,
    project_conflict_storage_object,
    project_stream_storage_object,
)
from verification.community_data_lake.models import CheckResult

POLICY = CommunityDataLakePolicy.default()
S3_CONFIG = S3DataLakeStoreConfiguration(bucket_name="valid-bucket-name")

_CLIENT_TYPE_STREAMS = frozenset({"telemetry", "extension_event", "ai_usage"})


def _expected_metadata_keys(stream: str) -> frozenset[str]:
    keys = set(BASE_S3_METADATA_KEYS)
    if stream == "assessment_metadata":
        keys.add(ASSESSMENT_SCHEMA_METADATA_KEY)
    elif stream in _CLIENT_TYPE_STREAMS:
        keys.add(CLIENT_TYPE_METADATA_KEY)
    return frozenset(keys)


def _partition_prefix(stream: str) -> str:
    return f"raw/stream={stream}/schema_version=1.0/year="


def _run_stream_scenario(
    store: InMemoryCommunityDataLakeStore | CommunityDataLakeS3Store,
    stream: str,
    *,
    adapter: str,
    client: FakeS3Client | None = None,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    obj = project_stream_storage_object(stream)
    prefix = _partition_prefix(stream)

    first = store.put_immutable_storage_object(obj)
    second = store.put_immutable_storage_object(obj)
    checks.extend(
        [
            CheckResult(
                name=f"streams:{adapter}:{stream}:first_write_stored",
                ok=first.status is StorageWriteStatus.STORED,
                detail=str(first.status.value),
                category="streams",
                scenario=stream,
            ),
            CheckResult(
                name=f"streams:{adapter}:{stream}:exact_retry_already_exists",
                ok=second.status is StorageWriteStatus.ALREADY_EXISTS,
                detail=str(second.status.value),
                category="streams",
                scenario=stream,
            ),
        ]
    )

    conflict_first = project_conflict_storage_object(stream)
    conflict_second = project_conflict_peer(stream)
    store.put_immutable_storage_object(conflict_first)
    conflict = store.put_immutable_storage_object(conflict_second)
    checks.append(
        CheckResult(
            name=f"streams:{adapter}:{stream}:conflict_detected",
            ok=conflict.status is StorageWriteStatus.CONFLICT,
            detail=str(conflict.status.value),
            category="streams",
            scenario=stream,
        )
    )

    checks.append(
        CheckResult(
            name=f"streams:{adapter}:{stream}:partition_prefix",
            ok=obj.object_key.startswith(prefix),
            detail="prefix ok" if obj.object_key.startswith(prefix) else "prefix mismatch",
            category="streams",
            scenario=stream,
        )
    )

    metadata = obj.to_s3_metadata()
    expected_keys = _expected_metadata_keys(stream)
    checks.append(
        CheckResult(
            name=f"streams:{adapter}:{stream}:metadata_keys",
            ok=set(metadata.keys()) == expected_keys,
            detail=f"keys={sorted(metadata.keys())}",
            category="streams",
            scenario=stream,
        )
    )

    if stream == "assessment_metadata":
        checks.append(
            CheckResult(
                name=f"streams:{adapter}:{stream}:assessment_schema_metadata",
                ok=metadata.get(ASSESSMENT_SCHEMA_METADATA_KEY) == "1.2",
                detail=metadata.get(ASSESSMENT_SCHEMA_METADATA_KEY, ""),
                category="streams",
                scenario=stream,
            )
        )
    elif stream in _CLIENT_TYPE_STREAMS:
        checks.append(
            CheckResult(
                name=f"streams:{adapter}:{stream}:client_type_metadata",
                ok=CLIENT_TYPE_METADATA_KEY in metadata and bool(metadata[CLIENT_TYPE_METADATA_KEY]),
                detail=metadata.get(CLIENT_TYPE_METADATA_KEY, ""),
                category="streams",
                scenario=stream,
            )
        )

    if client is not None and first.status is StorageWriteStatus.STORED:
        put_kwargs = client.last_put_kwargs()
        stored = client.objects[first.object_key]
        checks.extend(
            [
                CheckResult(
                    name=f"streams:{adapter}:{stream}:s3_if_none_match",
                    ok=put_kwargs.get("IfNoneMatch") == "*",
                    detail="IfNoneMatch=*",
                    category="streams",
                    scenario=stream,
                ),
                CheckResult(
                    name=f"streams:{adapter}:{stream}:s3_sse_aes256",
                    ok=put_kwargs.get("ServerSideEncryption") == "AES256",
                    detail=str(put_kwargs.get("ServerSideEncryption")),
                    category="streams",
                    scenario=stream,
                ),
                CheckResult(
                    name=f"streams:{adapter}:{stream}:s3_content_type",
                    ok=put_kwargs.get("ContentType") == "application/json",
                    detail=str(put_kwargs.get("ContentType")),
                    category="streams",
                    scenario=stream,
                ),
                CheckResult(
                    name=f"streams:{adapter}:{stream}:s3_checksum_sha256",
                    ok=bool(put_kwargs.get("ChecksumSHA256")),
                    detail="present" if put_kwargs.get("ChecksumSHA256") else "missing",
                    category="streams",
                    scenario=stream,
                ),
                CheckResult(
                    name=f"streams:{adapter}:{stream}:s3_body_exact",
                    ok=stored["Body"] == obj.canonical_json_bytes,
                    detail="bytes match",
                    category="streams",
                    scenario=stream,
                ),
            ]
        )

    return checks


def check_accepted_streams_in_memory() -> list[CheckResult]:
    checks: list[CheckResult] = []
    for stream in ACCEPTED_STREAMS:
        store = InMemoryCommunityDataLakeStore(policy=POLICY)
        checks.extend(_run_stream_scenario(store, stream, adapter="in_memory"))
    return checks


def check_accepted_streams_fake_s3() -> list[CheckResult]:
    checks: list[CheckResult] = []
    for stream in ACCEPTED_STREAMS:
        client = FakeS3Client()
        store = CommunityDataLakeS3Store(config=S3_CONFIG, policy=POLICY, client=client)
        checks.extend(
            _run_stream_scenario(store, stream, adapter="fake_s3", client=client)
        )
    return checks


__all__ = ["check_accepted_streams_fake_s3", "check_accepted_streams_in_memory"]
