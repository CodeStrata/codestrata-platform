"""Determinism guarantees for AI usage partition projection (Slice 8.8)."""

from __future__ import annotations

from codestrata_platform.community_cloud_api.data_lake.streams.ai_usage_partitioning import (
    CLIENT_TYPE_METADATA_KEY,
    default_ai_usage_partition_policy,
    project_ai_usage_storage_object,
)

from ._ai_usage_partitioning_test_helpers import DEFAULT_AI_USAGE_CLOCK, ai_usage_envelope
from ._request_test_helpers import make_ai_usage_request


def _usage(**overrides: object) -> dict[str, object]:
    usage = dict(make_ai_usage_request().usage.model_dump())
    usage.update(overrides)
    return usage


def test_repeated_projection_of_the_same_envelope_is_byte_identical() -> None:
    envelope = ai_usage_envelope(event_id="ai-usage-determinism-0001")
    first = project_ai_usage_storage_object(envelope)
    second = project_ai_usage_storage_object(envelope)
    assert first.storage_object.object_key == second.storage_object.object_key
    assert first.storage_object.object_id == second.storage_object.object_id
    assert first.storage_object.canonical_json_bytes == second.storage_object.canonical_json_bytes
    assert first.storage_object.content_sha256 == second.storage_object.content_sha256
    assert first.storage_object.to_s3_metadata() == second.storage_object.to_s3_metadata()


def test_repeated_projection_produces_identical_diagnostics() -> None:
    envelope = ai_usage_envelope(event_id="ai-usage-determinism-0002")
    first = project_ai_usage_storage_object(envelope)
    second = project_ai_usage_storage_object(envelope)
    assert first.diagnostics == second.diagnostics
    assert first.diagnostics.to_stable_dict() == second.diagnostics.to_stable_dict()


def test_different_event_keys_produce_different_object_ids_and_keys() -> None:
    first = project_ai_usage_storage_object(
        ai_usage_envelope(event_key="event:ai-usage-determinism-key-a")
    )
    second = project_ai_usage_storage_object(
        ai_usage_envelope(event_key="event:ai-usage-determinism-key-b")
    )
    assert first.storage_object.object_id != second.storage_object.object_id
    assert first.storage_object.object_key != second.storage_object.object_key


def test_capability_alias_and_canonical_produce_the_same_envelope_bytes() -> None:
    # "modernization-advisor" is a real catalog alias for the canonical
    # capability "modernization_advisor" — the model validator canonicalizes
    # before any storage, so both submissions must resolve to byte-identical
    # projected content once event_id and every other field match.
    canonical = project_ai_usage_storage_object(
        ai_usage_envelope(
            event_key="event:ai-usage-alias-canonical",
            event_id="ai-usage-alias-0001",
            usage=_usage(capability="modernization_advisor"),
        )
    )
    aliased = project_ai_usage_storage_object(
        ai_usage_envelope(
            event_key="event:ai-usage-alias-canonical",
            event_id="ai-usage-alias-0001",
            usage=_usage(capability="modernization-advisor"),
        )
    )
    assert canonical.storage_object.canonical_json_bytes == aliased.storage_object.canonical_json_bytes
    assert canonical.storage_object.object_key == aliased.storage_object.object_key
    assert canonical.storage_object.content_sha256 == aliased.storage_object.content_sha256


def test_cli_and_vscode_clients_produce_different_content() -> None:
    cli = project_ai_usage_storage_object(
        ai_usage_envelope(
            event_key="event:ai-usage-client-cli",
            event_id="ai-usage-client-0001",
        )
    )
    vscode = project_ai_usage_storage_object(
        ai_usage_envelope(
            event_key="event:ai-usage-client-vscode",
            event_id="ai-usage-client-0001",
            client={
                "name": "vscode_extension",
                "version": "0.2.0",
                "platform": "darwin",
            },
        )
    )
    assert cli.storage_object.canonical_json_bytes != vscode.storage_object.canonical_json_bytes
    assert cli.storage_object.to_s3_metadata()[CLIENT_TYPE_METADATA_KEY] == "codestrata_cli"
    assert vscode.storage_object.to_s3_metadata()[CLIENT_TYPE_METADATA_KEY] == "vscode_extension"


def test_meaningful_provider_change_changes_digest() -> None:
    # Only one canonical capability exists today; a meaningful private-payload
    # change (provider family) must still change the projected content digest.
    openai = project_ai_usage_storage_object(
        ai_usage_envelope(
            event_key="event:ai-usage-provider-change",
            event_id="ai-usage-provider-0001",
            usage=_usage(provider_family="openai", model_family="gpt_family"),
        )
    )
    bedrock = project_ai_usage_storage_object(
        ai_usage_envelope(
            event_key="event:ai-usage-provider-change",
            event_id="ai-usage-provider-0001",
            usage=_usage(provider_family="aws_bedrock", model_family="amazon_nova_family"),
        )
    )
    assert openai.storage_object.content_sha256 != bedrock.storage_object.content_sha256
    assert openai.storage_object.canonical_json_bytes != bedrock.storage_object.canonical_json_bytes


def test_safe_object_reference_is_deterministically_derived_from_object_id() -> None:
    result = project_ai_usage_storage_object(
        ai_usage_envelope(event_key="event:ai-usage-determinism-ref-key")
    )
    expected_fragment = result.storage_object.opaque_object_id_hex[:16]
    assert result.diagnostics.safe_object_reference == f"lake-ref:{expected_fragment}"


def test_default_policy_instances_are_value_equal_across_calls() -> None:
    first = default_ai_usage_partition_policy()
    second = default_ai_usage_partition_policy()
    assert first == second
    assert hash(first) == hash(second)


def test_partition_date_dimensions_track_the_envelope_acceptance_date_deterministically() -> None:
    result = project_ai_usage_storage_object(
        ai_usage_envelope(event_key="event:ai-usage-determinism-date-key")
    )
    key = result.storage_object.object_key
    assert "year=2026" in key
    assert "month=08" in key
    assert "day=04" in key


def test_object_key_prefix_is_stable_across_two_different_but_same_day_events() -> None:
    first = project_ai_usage_storage_object(
        ai_usage_envelope(event_key="event:ai-usage-determinism-prefix-a")
    )
    second = project_ai_usage_storage_object(
        ai_usage_envelope(event_key="event:ai-usage-determinism-prefix-b")
    )
    prefix = "raw/stream=ai_usage/schema_version=1.0/year=2026/month=08/day=04/"
    assert first.storage_object.object_key.startswith(prefix)
    assert second.storage_object.object_key.startswith(prefix)


def test_request_dict_key_order_does_not_affect_projected_bytes() -> None:
    first_request = make_ai_usage_request(event_id="ai-usage-order-0001")
    second_request = make_ai_usage_request(
        **{
            "schema_version": "1.0",
            "event_id": "ai-usage-order-0001",
            "context": first_request.context.model_dump(),
            "usage": first_request.usage.model_dump(),
            "client": first_request.client.model_dump(),
        }
    )
    assert first_request.model_dump() == second_request.model_dump()

    from codestrata_platform.community_cloud_api.data_lake.envelope_builders import (
        build_data_lake_envelope,
    )

    first = project_ai_usage_storage_object(
        build_data_lake_envelope(
            event_stream="ai_usage",
            request=first_request,
            event_key="event:ai-usage-order-key",
            safe_event_reference="evt-aiusageorder1",
            clock=DEFAULT_AI_USAGE_CLOCK,
        )
    )
    second = project_ai_usage_storage_object(
        build_data_lake_envelope(
            event_stream="ai_usage",
            request=second_request,
            event_key="event:ai-usage-order-key",
            safe_event_reference="evt-aiusageorder1",
            clock=DEFAULT_AI_USAGE_CLOCK,
        )
    )
    assert first.storage_object.canonical_json_bytes == second.storage_object.canonical_json_bytes
