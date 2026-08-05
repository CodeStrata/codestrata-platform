"""Stream metadata preservation integration tests (Slice 8.14)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.objects import BASE_S3_METADATA_KEYS
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata_partitioning import (
    ASSESSMENT_SCHEMA_METADATA_KEY,
)
from codestrata_platform.community_cloud_api.data_lake.streams.telemetry_partitioning import (
    CLIENT_TYPE_METADATA_KEY,
)

from verification.community_data_lake.contract import ACCEPTED_STREAMS
from verification.community_data_lake.inputs import project_all_streams


def test_stream_metadata_preservation() -> None:
    objects = project_all_streams()
    assert set(objects) == set(ACCEPTED_STREAMS)
    for stream, obj in objects.items():
        metadata = obj.to_s3_metadata()
        assert BASE_S3_METADATA_KEYS <= set(metadata.keys())
        if stream == "assessment_metadata":
            assert metadata[ASSESSMENT_SCHEMA_METADATA_KEY] == "1.2"
        elif stream in {"telemetry", "extension_event", "ai_usage"}:
            assert CLIENT_TYPE_METADATA_KEY in metadata
        elif stream == "cli_event":
            assert set(metadata.keys()) == set(BASE_S3_METADATA_KEYS)
