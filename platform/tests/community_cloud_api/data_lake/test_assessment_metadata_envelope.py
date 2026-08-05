"""Assessment metadata event-stream envelope construction tests (Slice 8.3)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import FixedAcceptanceClock
from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
    build_data_lake_envelope,
)
from codestrata_platform.community_cloud_api.data_lake.envelope_models import EnvelopeErrorCode
from codestrata_platform.community_cloud_api.data_lake.envelope_registry import get_source_contract
from codestrata_platform.community_cloud_api.data_lake.envelope_validation import EnvelopeBuildError
from codestrata_platform.community_cloud_api.data_lake.streams.assessment_metadata import (
    SCHEMA_NAME,
    client_type_from_request,
    project_payload,
)

from ._request_test_helpers import make_assessment_metadata_request, make_telemetry_request

_CLOCK = FixedAcceptanceClock(datetime(2026, 8, 4, 0, 0, 0, tzinfo=timezone.utc))


def test_schema_name_is_the_stable_product_identifier() -> None:
    assert SCHEMA_NAME == "community-assessment-metadata"


def test_project_payload_returns_the_full_stable_dict() -> None:
    request = make_assessment_metadata_request()
    assert project_payload(request) == request.to_stable_dict()


def test_project_payload_preserves_event_id() -> None:
    request = make_assessment_metadata_request(event_id="amd-preserved1")
    assert project_payload(request)["event_id"] == "amd-preserved1"


def test_project_payload_preserves_optional_installation_id_when_present() -> None:
    request = make_assessment_metadata_request(installation_id="install-abcdef12")
    assert project_payload(request)["installation_id"] == "install-abcdef12"


def test_client_type_from_request_reads_client_name() -> None:
    request = make_assessment_metadata_request()
    assert client_type_from_request(request) == "codestrata_cli"


def test_registered_contract_matches_module_constants() -> None:
    descriptor = get_source_contract("assessment_metadata")
    assert descriptor.schema_name == SCHEMA_NAME
    assert descriptor.schema_version == "1.0"
    assert descriptor.policy_id == "community-assessment-metadata-policy:1.0"


def test_build_data_lake_envelope_end_to_end_for_assessment_metadata() -> None:
    envelope = build_data_lake_envelope(
        event_stream="assessment_metadata",
        request=make_assessment_metadata_request(),
        event_key="event:assessmentmeta0000000",
        safe_event_reference="evt-assessment0001",
        clock=_CLOCK,
    )
    assert envelope.payload["assessment"]["assessment_status"] == "completed"
    assert envelope.source_contract.schema_name == "community-assessment-metadata"


def test_build_data_lake_envelope_rejects_a_telemetry_request_for_assessment_stream() -> None:
    with pytest.raises(EnvelopeBuildError) as excinfo:
        build_data_lake_envelope(
            event_stream="assessment_metadata",
            request=make_telemetry_request(),
            event_key="event:assessmentmeta0000000",
            safe_event_reference="evt-assessment0001",
            clock=_CLOCK,
        )
    assert excinfo.value.code is EnvelopeErrorCode.STREAM_CONTRACT_MISMATCH
