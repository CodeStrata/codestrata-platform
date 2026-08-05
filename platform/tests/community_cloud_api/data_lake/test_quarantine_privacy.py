"""Privacy boundary tests for quarantine (Slice 8.9)."""

from __future__ import annotations

import json

import pytest

from codestrata_platform.community_cloud_api.data_lake.quarantine_projection import (
    project_quarantine_storage_object,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_validation import (
    QuarantineValidationError,
    assert_no_forbidden_diagnostics_map,
    validate_quarantine_record,
)

from ._quarantine_test_helpers import make_quarantine_record

FORBIDDEN = (
    "body",
    "raw_body",
    "payload",
    "authorization",
    "cookie",
    "event_id",
    "installation_id",
    "request_id",
    "ip",
    "prompt",
    "source",
    "bucket",
    "object_key",
)


def test_stable_dict_never_includes_forbidden_fields() -> None:
    record = make_quarantine_record(
        safe_event_reference="evt-privacyaaaaaa",
        event_stream="telemetry",
    )
    blob = json.dumps(record.to_stable_dict())
    for name in FORBIDDEN:
        assert f'"{name}"' not in blob


def test_s3_metadata_never_includes_stream_or_event_id() -> None:
    result = project_quarantine_storage_object(
        make_quarantine_record(event_stream="cli_event", safe_event_reference="evt-privacybbbbbb")
    )
    metadata = result.storage_object.to_s3_metadata()
    joined = json.dumps(metadata)
    assert "event_id" not in joined
    assert "codestrata-stream" not in metadata
    assert "evt-" not in joined


def test_forbidden_field_names_rejected_in_diagnostics_map() -> None:
    with pytest.raises(QuarantineValidationError):
        assert_no_forbidden_diagnostics_map({"authorization": "Bearer x"})


def test_free_text_diagnostic_codes_rejected() -> None:
    record = make_quarantine_record(diagnostic_codes=("user said password is hunter2",))
    with pytest.raises(QuarantineValidationError):
        validate_quarantine_record(record)
