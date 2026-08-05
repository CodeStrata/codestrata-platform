"""Data Lake envelope construction and policy validation tests (Slice 8.1 / 8.3).

Slice 8.3 evolved the canonical serialized shape from Slice 8.1's flat
fields to the nested ``acceptance``/``client``/``identity``/
``source_contract`` contract while remaining at envelope schema ``1.0`` (a
pre-persistence foundation refinement — see
``platform/docs/community-cloud-api/data-lake-event-envelope.md``). This
module now exercises the nested dataclasses directly plus the
:func:`build_envelope` low-level builder.
"""

from __future__ import annotations

import pytest

from codestrata_platform.community_cloud_api.data_lake.envelopes import (
    FORBIDDEN_ENVELOPE_KEYS,
    DataLakeEnvelope,
    EnvelopeAcceptance,
    EnvelopeClient,
    EnvelopeIdentity,
    EnvelopeValidationError,
    SourceContract,
    build_envelope,
    validate_envelope_privacy,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

from ._envelope_test_helpers import DEFAULT_ACCEPTED_AT, make_envelope


def _kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        event_stream="telemetry",
        schema_name="community-telemetry",
        schema_version="1.0",
        policy_id="community-telemetry-policy:1.0",
        event_key="event:abcdef123456",
        safe_event_reference="evt-aaaaaaaaaaaa",
        accepted_at=DEFAULT_ACCEPTED_AT,
        client_type="codestrata_cli",
        payload={"duration_bucket": "1s_to_5s"},
    )
    base.update(overrides)
    return base


def test_build_envelope_success_round_trips_stable_dict() -> None:
    envelope = build_envelope(**_kwargs())
    blob = envelope.to_stable_dict()
    assert list(blob) == sorted(blob)
    assert blob["event_stream"] == "telemetry"
    assert blob["envelope_schema_version"] == "1.0"
    assert blob["payload"] == {"duration_bucket": "1s_to_5s"}
    assert blob["source_contract"] == {
        "policy_id": "community-telemetry-policy:1.0",
        "schema_name": "community-telemetry",
        "schema_version": "1.0",
    }
    assert blob["identity"] == {
        "event_key": "event:abcdef123456",
        "safe_event_reference": "evt-aaaaaaaaaaaa",
    }
    assert blob["client"] == {"client_type": "codestrata_cli"}
    assert blob["acceptance"] == {
        "accepted_at": DEFAULT_ACCEPTED_AT,
        "partition_date": "2026-08-03",
    }
    assert "payload_fingerprint" not in blob


def test_envelope_never_includes_payload_fingerprint_field() -> None:
    # Slice 8.3 decision: payload_fingerprint is an identity-layer concern,
    # never part of the storage envelope.
    envelope = build_envelope(**_kwargs())
    assert "payload_fingerprint" not in envelope.to_stable_dict()
    assert not hasattr(envelope, "payload_fingerprint")


def test_build_envelope_uses_default_policy_when_none_given() -> None:
    envelope = build_envelope(**_kwargs())
    default_policy = CommunityDataLakePolicy.default()
    assert envelope.envelope_schema_version == default_policy.envelope_schema_version


# --- compatibility properties (Slice 8.1/8.2 call sites) -------------------


def test_compatibility_properties_expose_nested_fields() -> None:
    envelope = build_envelope(**_kwargs())
    assert envelope.source_schema_version == "1.0"
    assert envelope.source_policy_version == "community-telemetry-policy:1.0"
    assert envelope.event_key == "event:abcdef123456"
    assert envelope.safe_event_reference == "evt-aaaaaaaaaaaa"
    assert envelope.client_type == "codestrata_cli"
    assert envelope.accepted_year == "2026"
    assert envelope.accepted_month == "08"
    assert envelope.accepted_day == "03"


def test_data_lake_event_envelope_is_an_alias() -> None:
    from codestrata_platform.community_cloud_api.data_lake.envelopes import (
        DataLakeEventEnvelope,
    )

    assert DataLakeEventEnvelope is DataLakeEnvelope


# --- SourceContract ----------------------------------------------------


def test_source_contract_requires_urn_policy_id() -> None:
    with pytest.raises(EnvelopeValidationError):
        SourceContract(
            schema_name="community-telemetry", schema_version="1.0", policy_id="not-a-urn"
        )


def test_source_contract_rejects_blank_schema_name() -> None:
    with pytest.raises(EnvelopeValidationError):
        SourceContract(
            schema_name="  ", schema_version="1.0", policy_id="community-telemetry-policy:1.0"
        )


def test_source_contract_rejects_bad_schema_version() -> None:
    with pytest.raises(EnvelopeValidationError):
        SourceContract(
            schema_name="community-telemetry",
            schema_version="not-a-version",
            policy_id="community-telemetry-policy:1.0",
        )


def test_source_contract_to_stable_dict_is_sorted() -> None:
    contract = SourceContract(
        schema_name="community-telemetry",
        schema_version="1.0",
        policy_id="community-telemetry-policy:1.0",
    )
    blob = contract.to_stable_dict()
    assert list(blob) == sorted(blob)


# --- EnvelopeIdentity ----------------------------------------------------


def test_identity_rejects_event_key_without_prefix() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeIdentity(event_key="not-an-event-key", safe_event_reference="evt-aaaaaaaaaaaa")


def test_identity_rejects_safe_reference_without_prefix() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeIdentity(event_key="event:abc", safe_event_reference="not-an-evt-ref")


# --- EnvelopeAcceptance ----------------------------------------------------


def test_acceptance_rejects_malformed_accepted_at() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeAcceptance(accepted_at="not-a-timestamp", partition_date="2026-08-03")


@pytest.mark.parametrize(
    "accepted_at",
    [
        "2026-08-03T00:00:00.123Z",  # sub-second precision not permitted
        "2026-08-03T00:00:00+00:00",  # must be literal Z, not offset
        "2026-08-03",  # missing time component
    ],
)
def test_acceptance_rejects_non_canonical_accepted_at_formats(accepted_at: str) -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeAcceptance(accepted_at=accepted_at, partition_date="2026-08-03")


def test_acceptance_rejects_partition_date_mismatched_with_accepted_at() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeAcceptance(accepted_at=DEFAULT_ACCEPTED_AT, partition_date="2026-08-04")


@pytest.mark.parametrize(
    "accepted_at",
    [
        "2026-13-01T00:00:00Z",
        "2026-00-01T00:00:00Z",
        "2026-08-32T00:00:00Z",
        "2026-08-00T00:00:00Z",
    ],
)
def test_acceptance_rejects_invalid_calendar_dates(accepted_at: str) -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeAcceptance(accepted_at=accepted_at, partition_date=accepted_at[:10])


def test_acceptance_year_month_day_properties() -> None:
    acceptance = EnvelopeAcceptance(accepted_at=DEFAULT_ACCEPTED_AT, partition_date="2026-08-03")
    assert (acceptance.year, acceptance.month, acceptance.day) == ("2026", "08", "03")


# --- EnvelopeClient ----------------------------------------------------


def test_client_rejects_blank_client_type() -> None:
    with pytest.raises(EnvelopeValidationError):
        EnvelopeClient(client_type="   ")


# --- DataLakeEnvelope-level invariants -------------------------------------


def test_envelope_rejects_unsupported_event_stream() -> None:
    with pytest.raises(EnvelopeValidationError):
        build_envelope(**_kwargs(event_stream="not_a_stream"))


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


def test_envelope_rejects_blank_envelope_schema_version() -> None:
    with pytest.raises(EnvelopeValidationError):
        DataLakeEnvelope(
            envelope_schema_version="  ",
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


def test_validate_against_policy_rejects_unsupported_envelope_schema_version() -> None:
    envelope = build_envelope(**_kwargs())
    # Bypass the frozen dataclass to simulate drift from the active policy.
    object.__setattr__(envelope, "envelope_schema_version", "2.0")
    with pytest.raises(EnvelopeValidationError):
        envelope.validate_against_policy(CommunityDataLakePolicy.default())


def test_validate_against_policy_rejects_disallowed_stream() -> None:
    restricted = CommunityDataLakePolicy(allowed_event_streams=("telemetry",))
    # build_envelope validates against the policy at construction time, so
    # a disallowed stream must raise immediately rather than build silently.
    with pytest.raises(EnvelopeValidationError):
        build_envelope(**_kwargs(event_stream="ai_usage"), policy=restricted)


def test_validate_against_policy_rejects_disallowed_stream_called_directly() -> None:
    restricted = CommunityDataLakePolicy(allowed_event_streams=("telemetry",))
    envelope = build_envelope(**_kwargs(event_stream="ai_usage"))
    with pytest.raises(EnvelopeValidationError):
        envelope.validate_against_policy(restricted)


def test_validate_against_policy_rejects_oversized_envelope() -> None:
    tight_policy = CommunityDataLakePolicy(max_envelope_bytes=1024)
    huge_payload = {"blob": "x" * 5000}
    with pytest.raises(EnvelopeValidationError):
        build_envelope(**_kwargs(payload=huge_payload), policy=tight_policy)


# --- privacy -----------------------------------------------------------


@pytest.mark.parametrize("forbidden_key", sorted(FORBIDDEN_ENVELOPE_KEYS))
def test_validate_envelope_privacy_detects_each_forbidden_token(forbidden_key: str) -> None:
    # build_envelope validates privacy at construction time, so a forbidden
    # token anywhere in the payload must raise immediately.
    with pytest.raises(EnvelopeValidationError):
        build_envelope(**_kwargs(payload={"nested": {forbidden_key: "value"}}))


def test_validate_envelope_privacy_passes_for_clean_payload() -> None:
    envelope = build_envelope(**_kwargs())
    validate_envelope_privacy(envelope)  # must not raise


def test_forbidden_envelope_keys_is_a_frozenset_of_expected_tokens() -> None:
    assert FORBIDDEN_ENVELOPE_KEYS == frozenset(
        {
            "authorization",
            "cookie",
            "ip_address",
            "client_ip",
            "request_id",
            "password",
            "secret",
            "bearer",
            "cscc_v1_",
            "aws_secret",
            "private_key",
            "access_key",
        }
    )


def test_make_envelope_helper_produces_a_valid_envelope() -> None:
    # Sanity check on the shared test helper itself.
    envelope = make_envelope()
    envelope.validate_against_policy(CommunityDataLakePolicy.default())
