"""Boundary and negative-scenario tests for Slice 8.3 envelope structures.

Broad sweep across every nested dataclass's structural guards — complements
the narrower, single-concern test modules elsewhere in this package.
"""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.envelopes import (
    DataLakeEnvelope,
    EnvelopeAcceptance,
    EnvelopeClient,
    EnvelopeIdentity,
    EnvelopeValidationError,
    SourceContract,
    build_envelope,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

from ._envelope_test_helpers import DEFAULT_ACCEPTED_AT, make_envelope

# --- SourceContract -------------------------------------------------------


def test_source_contract_rejects_blank_schema_name() -> None:
    with pytest.raises(EnvelopeValidationError):
        SourceContract(schema_name="", schema_version="1.0", policy_id="p:1.0")


def test_source_contract_rejects_blank_policy_id() -> None:
    with pytest.raises(EnvelopeValidationError):
        SourceContract(schema_name="s", schema_version="1.0", policy_id="")


def test_source_contract_rejects_policy_id_without_colon() -> None:
    with pytest.raises(EnvelopeValidationError):
        SourceContract(schema_name="s", schema_version="1.0", policy_id="no-colon-here")


def test_source_contract_rejects_malformed_schema_version() -> None:
    with pytest.raises(EnvelopeValidationError):
        SourceContract(schema_name="s", schema_version="not-a-version", policy_id="p:1.0")


def test_source_contract_accepts_multi_segment_schema_version() -> None:
    contract = SourceContract(schema_name="s", schema_version="1.2.3", policy_id="p:1.0")
    assert contract.schema_version == "1.2.3"


# --- EnvelopeIdentity -------------------------------------------------------


def test_identity_rejects_blank_event_key() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeIdentity(event_key="", safe_event_reference="evt-aaaaaaaaaaaa")


def test_identity_rejects_event_key_without_scoped_prefix() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeIdentity(event_key="not-scoped", safe_event_reference="evt-aaaaaaaaaaaa")


def test_identity_rejects_blank_safe_event_reference() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeIdentity(event_key="event:abc", safe_event_reference="")


def test_identity_rejects_safe_event_reference_without_evt_prefix() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeIdentity(event_key="event:abc", safe_event_reference="not-scoped")


# --- EnvelopeAcceptance ------------------------------------------------------


def test_acceptance_rejects_partition_date_mismatched_with_accepted_at() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeAcceptance(accepted_at="2026-08-04T12:00:00Z", partition_date="2026-08-05")


def test_acceptance_rejects_malformed_accepted_at() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeAcceptance(accepted_at="not-a-timestamp", partition_date="2026-08-04")


def test_acceptance_rejects_accepted_at_missing_z_suffix() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeAcceptance(accepted_at="2026-08-04T12:00:00", partition_date="2026-08-04")


def test_acceptance_rejects_blank_partition_date() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeAcceptance(accepted_at="2026-08-04T12:00:00Z", partition_date="")


def test_acceptance_rejects_invalid_calendar_month() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeAcceptance(accepted_at="2026-13-04T12:00:00Z", partition_date="2026-13-04")


def test_acceptance_year_month_day_properties_are_derived_correctly() -> None:
    acceptance = EnvelopeAcceptance(accepted_at="2026-08-04T12:00:00Z", partition_date="2026-08-04")
    assert (acceptance.year, acceptance.month, acceptance.day) == ("2026", "08", "04")


# --- EnvelopeClient -----------------------------------------------------------


def test_client_rejects_blank_client_type() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeClient(client_type="")


def test_client_rejects_whitespace_only_client_type() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeClient(client_type="   ")


# --- DataLakeEnvelope structural guards ---------------------------------------


def test_envelope_rejects_blank_envelope_schema_version() -> None:
    with pytest.raises(EnvelopeValidationError):
        DataLakeEnvelope(
            envelope_schema_version="",
            event_stream="telemetry",
            source_contract=SourceContract(
                schema_name="community-telemetry",
                schema_version="1.0",
                policy_id="community-telemetry-policy:1.0",
            ),
            identity=EnvelopeIdentity(
                event_key="event:abc", safe_event_reference="evt-aaaaaaaaaaaa"
            ),
            acceptance=EnvelopeAcceptance(
                accepted_at=DEFAULT_ACCEPTED_AT, partition_date="2026-08-03"
            ),
            client=EnvelopeClient(client_type="codestrata_cli"),
            payload={},
        )


def test_envelope_rejects_unsupported_event_stream_at_construction() -> None:
    with pytest.raises(EnvelopeValidationError):
        DataLakeEnvelope(
            envelope_schema_version="1.0",
            event_stream="not_a_real_stream",
            source_contract=SourceContract(
                schema_name="community-telemetry",
                schema_version="1.0",
                policy_id="community-telemetry-policy:1.0",
            ),
            identity=EnvelopeIdentity(
                event_key="event:abc", safe_event_reference="evt-aaaaaaaaaaaa"
            ),
            acceptance=EnvelopeAcceptance(
                accepted_at=DEFAULT_ACCEPTED_AT, partition_date="2026-08-03"
            ),
            client=EnvelopeClient(client_type="codestrata_cli"),
            payload={},
        )


def test_envelope_rejects_non_mapping_payload() -> None:
    with pytest.raises(EnvelopeValidationError):
        DataLakeEnvelope(
            envelope_schema_version="1.0",
            event_stream="telemetry",
            source_contract=SourceContract(
                schema_name="community-telemetry",
                schema_version="1.0",
                policy_id="community-telemetry-policy:1.0",
            ),
            identity=EnvelopeIdentity(
                event_key="event:abc", safe_event_reference="evt-aaaaaaaaaaaa"
            ),
            acceptance=EnvelopeAcceptance(
                accepted_at=DEFAULT_ACCEPTED_AT, partition_date="2026-08-03"
            ),
            client=EnvelopeClient(client_type="codestrata_cli"),
            payload=["not", "a", "mapping"],  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("field_name", ["source_contract", "identity", "acceptance", "client"])
def test_envelope_rejects_wrong_type_for_each_nested_field(field_name: str) -> None:
    kwargs = dict(
        envelope_schema_version="1.0",
        event_stream="telemetry",
        source_contract=SourceContract(
            schema_name="community-telemetry",
            schema_version="1.0",
            policy_id="community-telemetry-policy:1.0",
        ),
        identity=EnvelopeIdentity(event_key="event:abc", safe_event_reference="evt-aaaaaaaaaaaa"),
        acceptance=EnvelopeAcceptance(accepted_at=DEFAULT_ACCEPTED_AT, partition_date="2026-08-03"),
        client=EnvelopeClient(client_type="codestrata_cli"),
        payload={},
    )
    kwargs[field_name] = "not-the-right-dataclass-type"
    with pytest.raises(EnvelopeValidationError):
        DataLakeEnvelope(**kwargs)  # type: ignore[arg-type]


# --- build_envelope() low-level guard sweep -----------------------------------


def test_build_envelope_rejects_accepted_at_not_matching_rfc3339_format() -> None:
    with pytest.raises(EnvelopeValidationError):
        build_envelope(
            event_stream="telemetry",
            schema_name="community-telemetry",
            schema_version="1.0",
            policy_id="community-telemetry-policy:1.0",
            event_key="event:abc",
            safe_event_reference="evt-aaaaaaaaaaaa",
            accepted_at="08/04/2026",
            client_type="codestrata_cli",
            payload={},
        )


def test_build_envelope_rejects_policy_disallowed_event_stream() -> None:
    restricted = CommunityDataLakePolicy(allowed_event_streams=("telemetry",))
    with pytest.raises(EnvelopeValidationError):
        build_envelope(
            event_stream="ai_usage",
            schema_name="community-ai-usage",
            schema_version="1.0",
            policy_id="community-ai-usage-policy:1.0",
            event_key="event:abc",
            safe_event_reference="evt-aaaaaaaaaaaa",
            accepted_at=DEFAULT_ACCEPTED_AT,
            client_type="codestrata_cli",
            payload={},
            policy=restricted,
        )


def test_build_envelope_rejects_envelope_schema_version_mismatch_via_validate_against_policy() -> None:
    envelope = make_envelope()
    object.__setattr__(envelope, "envelope_schema_version", "9.9")
    with pytest.raises(EnvelopeValidationError):
        envelope.validate_against_policy(CommunityDataLakePolicy.default())


def test_build_envelope_default_policy_is_used_when_none_given() -> None:
    envelope = build_envelope(
        event_stream="telemetry",
        schema_name="community-telemetry",
        schema_version="1.0",
        policy_id="community-telemetry-policy:1.0",
        event_key="event:abc",
        safe_event_reference="evt-aaaaaaaaaaaa",
        accepted_at=DEFAULT_ACCEPTED_AT,
        client_type="codestrata_cli",
        payload={},
    )
    assert envelope.envelope_schema_version == CommunityDataLakePolicy.default().envelope_schema_version


def test_frozen_envelope_rejects_direct_attribute_mutation() -> None:
    envelope = make_envelope()
    with pytest.raises(Exception):  # noqa: B017 - dataclasses.FrozenInstanceError subclasses AttributeError/TypeError depending on version
        envelope.event_stream = "cli_event"  # type: ignore[misc]


def test_frozen_nested_dataclass_rejects_direct_attribute_mutation() -> None:
    envelope = make_envelope()
    with pytest.raises(Exception):  # noqa: B017
        envelope.client.client_type = "cli_event"  # type: ignore[misc]


def test_empty_payload_is_valid() -> None:
    envelope = make_envelope(payload={})
    assert envelope.payload == {}


def test_deeply_nested_payload_serializes_without_error() -> None:
    deep_payload = {"level1": {"level2": {"level3": {"level4": "value"}}}}
    envelope = make_envelope(payload=deep_payload)
    blob = envelope.to_stable_dict()
    assert blob["payload"]["level1"]["level2"]["level3"]["level4"] == "value"
