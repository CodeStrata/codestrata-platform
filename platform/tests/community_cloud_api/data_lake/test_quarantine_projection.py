"""Quarantine projection / storage-object tests (Slice 8.9)."""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    QuarantineStorageObjectError,
    project_quarantine_storage_object,
)

from ._quarantine_test_helpers import make_quarantine_record


def test_project_quarantine_storage_object_happy_path() -> None:
    result = project_quarantine_storage_object(make_quarantine_record())
    obj = result.storage_object
    assert obj.object_key.startswith("quarantine/reason=unsafe_payload/")
    assert not obj.object_key.startswith("raw/")
    assert obj.object_id.startswith("quarantine-object:")
    assert obj.content_type == "application/json"
    metadata = obj.to_s3_metadata()
    assert set(metadata) == {
        "codestrata-content-sha256",
        "codestrata-object-id",
        "codestrata-quarantine-reason",
        "codestrata-quarantine-schema",
    }
    assert result.diagnostics.projection_status == "projected"


def test_quarantine_object_rejects_raw_prefix() -> None:
    result = project_quarantine_storage_object(make_quarantine_record())
    obj = result.storage_object
    from dataclasses import replace

    tampered = replace(obj, object_key="raw/" + obj.object_key.split("/", 1)[1])
    with pytest.raises(QuarantineStorageObjectError):
        tampered.validate()
