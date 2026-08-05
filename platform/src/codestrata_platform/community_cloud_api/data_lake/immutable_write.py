"""Build the immutable, storage-ready object for one accepted envelope (Slice 8.2).

This module composes :mod:`.canonical_json`, :mod:`.identifiers`,
:mod:`.partitions`, and :mod:`.objects` into the single entry point used by
every storage adapter (in-memory or S3): a validated envelope goes in, a
fully-resolved :class:`~.objects.ImmutableRawStorageObject` comes out — with
canonical bytes, digest, opaque key, and allowlisted metadata already
computed and self-validated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
    CONTENT_TYPE_APPLICATION_JSON,
    serialize_canonical_raw_json,
)
from codestrata_platform.community_cloud_api.data_lake.envelopes import DataLakeEnvelope
from codestrata_platform.community_cloud_api.data_lake.identifiers import build_lake_object_id
from codestrata_platform.community_cloud_api.data_lake.objects import ImmutableRawStorageObject
from codestrata_platform.community_cloud_api.data_lake.partitions import build_accepted_object_key
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy

if TYPE_CHECKING:  # pragma: no cover - typing only, avoids a runtime import cycle
    from codestrata_platform.community_cloud_api.data_lake.ports import (
        CommunityDataLakeStore,
        StorageWriteResult,
    )


def build_immutable_raw_storage_object(
    envelope: DataLakeEnvelope,
    policy: CommunityDataLakePolicy,
) -> ImmutableRawStorageObject:
    """Validate ``envelope`` against ``policy`` and resolve its storage object.

    Raises whatever the underlying steps raise on failure —
    :class:`~.envelopes.EnvelopeValidationError`,
    :class:`~.identifiers.LakeIdentifierError`,
    :class:`~.partitions.PartitionKeyError`,
    :class:`~.canonical_json.CanonicalJsonError`, or
    :class:`~.objects.StorageObjectError` — callers are expected to catch
    these (all ``ValueError`` subclasses) and translate them into a bounded
    ``REJECTED`` outcome.
    """

    envelope.validate_against_policy(policy)
    canonical = serialize_canonical_raw_json(envelope)
    lake_object_id = build_lake_object_id(
        policy.policy_token,
        envelope.event_stream,
        envelope.source_schema_version,
        envelope.event_key,
    )
    object_key = build_accepted_object_key(
        envelope, lake_object_id, hive_style=policy.hive_style_partitions
    )
    storage_object = ImmutableRawStorageObject(
        object_id=lake_object_id,
        event_stream=envelope.event_stream,
        object_key=object_key,
        envelope_schema_version=envelope.envelope_schema_version,
        source_schema_version=envelope.source_schema_version,
        canonical_json_bytes=canonical.data,
        content_sha256=canonical.content_sha256,
        content_length=canonical.content_length,
        content_type=CONTENT_TYPE_APPLICATION_JSON,
        accepted_year=envelope.accepted_year,
        accepted_month=envelope.accepted_month,
        accepted_day=envelope.accepted_day,
        safe_event_reference=envelope.safe_event_reference,
        storage_policy_token=policy.policy_token,
    )
    storage_object.validate()
    return storage_object


def put_envelope_via_store(
    store: "CommunityDataLakeStore",
    envelope: DataLakeEnvelope,
) -> "StorageWriteResult":
    """Thin convenience wrapper: ``store.put_immutable_event(envelope)``.

    Exists so call sites can depend on this module alone rather than
    reaching into :mod:`.ports` directly when they only need the one-shot
    write call.
    """

    return store.put_immutable_event(envelope)
