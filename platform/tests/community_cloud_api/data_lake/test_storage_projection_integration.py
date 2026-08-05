"""Stream storage projection integration via put_immutable_storage_object (Slice 8.13)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.enums import StorageWriteStatus
from codestrata_platform.community_cloud_api.data_lake.ports import InMemoryCommunityDataLakeStore
from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    CLIENT_TYPE_METADATA_KEY as AI_CLIENT_TYPE_KEY,
    project_ai_usage_storage_object,
    store_projected_ai_usage,
)
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    ASSESSMENT_SCHEMA_METADATA_KEY,
    project_assessment_metadata_storage_object,
    store_projected_assessment_metadata,
)
from codestrata_platform.community_cloud_api.data_lake.streams.cli_event_partitioning import (
    project_cli_event_storage_object,
    store_projected_cli_event,
)
from codestrata_platform.community_cloud_api.data_lake.streams.extension_event_partitioning import (
    CLIENT_TYPE_METADATA_KEY as EXT_CLIENT_TYPE_KEY,
    project_extension_event_storage_object,
    store_projected_extension_event,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    CLIENT_TYPE_METADATA_KEY as TELEMETRY_CLIENT_TYPE_KEY,
    project_telemetry_storage_object,
    store_projected_telemetry,
)

from ._ai_usage_partitioning_test_helpers import ai_usage_envelope
from ._assessment_partitioning_test_helpers import assessment_envelope
from ._cli_event_partitioning_test_helpers import cli_event_envelope
from ._extension_event_partitioning_test_helpers import extension_event_envelope
from ._telemetry_partitioning_test_helpers import telemetry_envelope


def _assert_extra_metadata_preserved(
    store: InMemoryCommunityDataLakeStore,
    result: object,
    expected: dict[str, str],
) -> None:
    from codestrata_platform.community_cloud_api.data_lake.ports import StorageWriteResult

    assert isinstance(result, StorageWriteResult)
    assert result.status is StorageWriteStatus.STORED
    preserved = store.get_accepted_extra_s3_metadata(result.object_key)
    assert preserved == expected


def test_assessment_metadata_preserves_schema_version_metadata() -> None:
    store = InMemoryCommunityDataLakeStore()
    projection = project_assessment_metadata_storage_object(
        assessment_envelope(event_id="storage-proj-amd-001")
    )
    result = store_projected_assessment_metadata(store, projection)
    _assert_extra_metadata_preserved(
        store,
        result,
        {ASSESSMENT_SCHEMA_METADATA_KEY: "1.2"},
    )


def test_telemetry_preserves_client_type_metadata() -> None:
    store = InMemoryCommunityDataLakeStore()
    projection = project_telemetry_storage_object(
        telemetry_envelope(event_id="storage-proj-tel-001")
    )
    result = store_projected_telemetry(store, projection)
    _assert_extra_metadata_preserved(
        store,
        result,
        {TELEMETRY_CLIENT_TYPE_KEY: "codestrata_cli"},
    )


def test_extension_event_preserves_client_type_metadata() -> None:
    store = InMemoryCommunityDataLakeStore()
    projection = project_extension_event_storage_object(
        extension_event_envelope(event_id="storage-proj-ext-001")
    )
    result = store_projected_extension_event(store, projection)
    _assert_extra_metadata_preserved(
        store,
        result,
        {EXT_CLIENT_TYPE_KEY: "vscode_extension"},
    )


def test_ai_usage_preserves_client_type_metadata() -> None:
    store = InMemoryCommunityDataLakeStore()
    projection = project_ai_usage_storage_object(
        ai_usage_envelope(event_id="storage-proj-ai-001")
    )
    result = store_projected_ai_usage(store, projection)
    _assert_extra_metadata_preserved(
        store,
        result,
        {AI_CLIENT_TYPE_KEY: "codestrata_cli"},
    )


def test_cli_event_has_no_extra_metadata() -> None:
    store = InMemoryCommunityDataLakeStore()
    projection = project_cli_event_storage_object(
        cli_event_envelope(event_id="storage-proj-cli-001")
    )
    assert projection.storage_object.extra_s3_metadata == ()
    result = store_projected_cli_event(store, projection)
    _assert_extra_metadata_preserved(store, result, {})
