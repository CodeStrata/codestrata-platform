"""Immutable raw storage object model for Community Data Lake writes (Slice 8.2).

An :class:`ImmutableRawStorageObject` is the fully-resolved, storage-ready
unit for a single accepted write: canonical JSON bytes, their digest, the
opaque object key, and only the allowlisted metadata that may accompany the
object in S3. No raw identity material (``event_key``, ``safe_event_reference``,
request ids, IP addresses) is ever present in the key or in metadata.

Slice 8.4 adds the optional :attr:`ImmutableRawStorageObject.extra_s3_metadata`
field: a small, allowlisted set of additional metadata pairs a stream-specific
partition projector (e.g. assessment metadata's
``codestrata-assessment-schema``) may attach on top of the five base keys
below. It defaults to empty, so every object built by
:func:`~.immutable_write.build_immutable_raw_storage_object` alone is
unaffected and still exposes exactly the five base keys.

Slice 8.5 adds one more optional allowlisted key,
``codestrata-client-type`` — the ``telemetry`` stream's bounded
:class:`~codestrata_platform.community_cloud_api.telemetry.enums.TelemetryClientName`
value, attached only by
:func:`~.streams.telemetry_partitioning.project_telemetry_storage_object`.

Slice 8.6 (``cli_event``) adds no new allowlisted key — its partition
policy deliberately reuses :data:`BASE_S3_METADATA_KEYS` (the five keys
below) unchanged as its *entire* ``s3_metadata_allowlist``, since the CLI
client is always ``codestrata_cli`` (a redundant metadata value) and
``operation``/``lifecycle``/``result`` remain private-payload-only. See
:mod:`~.streams.cli_event_partitioning`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256

from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
    CONTENT_TYPE_APPLICATION_JSON,
    CanonicalJsonError,
    content_digest_hex,
    validate_utf8_json_object_bytes,
)
from codestrata_platform.community_cloud_api.data_lake.identifiers import (
    LAKE_OBJECT_ID_HEX_LENGTH,
    LAKE_OBJECT_ID_PREFIX,
)
from codestrata_platform.community_cloud_api.data_lake.partitions import (
    assert_key_excludes_identity_material,
)

# Only these keys may ever be sent as S3 object user-metadata. Values are
# bounded, opaque identity/version tokens only — never raw payload, event
# keys, safe event references, or request/IP identifiers.
ALLOWED_S3_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "codestrata-content-sha256",
        "codestrata-envelope-schema",
        "codestrata-source-schema",
        "codestrata-stream",
        "codestrata-object-id",
        # Slice 8.4: optional, stream-specific. Engine assessment report
        # contract version (e.g. "1.2") — never the endpoint/envelope schema.
        "codestrata-assessment-schema",
        # Slice 8.5: optional, stream-specific. The telemetry stream's
        # bounded client-type classification (e.g. "codestrata_cli") — never
        # the full client descriptor (version, platform) or event type.
        "codestrata-client-type",
    }
)

# The five keys every :class:`ImmutableRawStorageObject` always carries,
# regardless of :attr:`ImmutableRawStorageObject.extra_s3_metadata`. A
# stream-specific projector's extra metadata may never override one of these.
# Public since Slice 8.6, so a stream partition policy (e.g. the
# ``cli_event`` stream's, which allowlists exactly these five keys and no
# more) can reference it directly instead of duplicating the literal set.
BASE_S3_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "codestrata-content-sha256",
        "codestrata-envelope-schema",
        "codestrata-source-schema",
        "codestrata-stream",
        "codestrata-object-id",
    }
)

# Backward-compatible private alias — pre-Slice-8.6 internal call sites in
# this module used this name.
_BASE_S3_METADATA_KEYS = BASE_S3_METADATA_KEYS

# Defense-in-depth: metadata keys that must never be constructed, even if a
# future change accidentally introduces them.
FORBIDDEN_S3_METADATA_KEYS: frozenset[str] = frozenset(
    {
        "codestrata-event-key",
        "codestrata-safe-event-reference",
        "codestrata-request-id",
        "codestrata-ip-address",
        "codestrata-client-ip",
        "authorization",
        "cookie",
    }
)

_FORBIDDEN_METADATA_VALUE_SUBSTRINGS: tuple[str, ...] = (
    "event:",
    "evt-",
    "lake-object:",
    "request_id",
    "ip_address",
    "client_ip",
    "authorization",
    "cookie",
    "password",
    "secret",
    "bearer",
)


class StorageObjectError(ValueError):
    """Raised when an immutable storage object fails structural validation."""


@dataclass(frozen=True, slots=True)
class ImmutableRawStorageObject:
    """A fully-resolved, storage-ready immutable object for one accepted write."""

    object_id: str
    event_stream: str
    object_key: str
    envelope_schema_version: str
    source_schema_version: str
    canonical_json_bytes: bytes
    content_sha256: str
    content_length: int
    content_type: str
    accepted_year: str
    accepted_month: str
    accepted_day: str
    safe_event_reference: str
    storage_policy_token: str
    # Slice 8.4: optional stream-specific S3 metadata pairs (e.g. the
    # assessment metadata stream's ``codestrata-assessment-schema``). A tuple
    # of pairs (not a ``Mapping``) so the frozen/slotted dataclass stays
    # hashable. Every key must already be in :data:`ALLOWED_S3_METADATA_KEYS`
    # and must not duplicate one of the five base keys above — enforced by
    # :meth:`validate` and, redundantly, by :meth:`to_s3_metadata`.
    extra_s3_metadata: tuple[tuple[str, str], ...] = field(default=())

    @property
    def opaque_object_id_hex(self) -> str:
        if not self.object_id.startswith(LAKE_OBJECT_ID_PREFIX):
            raise StorageObjectError("object_id missing lake-object prefix")
        return self.object_id[len(LAKE_OBJECT_ID_PREFIX) :]

    def validate(self) -> None:
        """Raise :class:`StorageObjectError` when any structural invariant is violated."""

        if self.content_type != CONTENT_TYPE_APPLICATION_JSON:
            raise StorageObjectError("content_type must be application/json")
        if not isinstance(self.canonical_json_bytes, (bytes, bytearray)):
            raise StorageObjectError("canonical_json_bytes must be bytes")
        raw_bytes = bytes(self.canonical_json_bytes)
        if self.content_length != len(raw_bytes):
            raise StorageObjectError("content_length does not match canonical bytes")

        expected_digest_hex = sha256(raw_bytes).hexdigest()
        try:
            stored_digest_hex = content_digest_hex(self.content_sha256).lower()
        except CanonicalJsonError as exc:
            raise StorageObjectError("content_sha256 is not a well-formed digest") from exc
        if stored_digest_hex != expected_digest_hex:
            raise StorageObjectError("content_sha256 does not match canonical bytes")

        try:
            validate_utf8_json_object_bytes(raw_bytes)
        except CanonicalJsonError as exc:
            raise StorageObjectError(str(exc)) from exc

        hex_id = self.opaque_object_id_hex
        if len(hex_id) != LAKE_OBJECT_ID_HEX_LENGTH or any(
            ch not in "0123456789abcdef" for ch in hex_id
        ):
            raise StorageObjectError("object_id hex fragment is invalid")

        key = self.object_key
        if not key or key.startswith("/"):
            raise StorageObjectError("object_key must be non-empty without a leading '/'")
        if not key.startswith("raw/"):
            raise StorageObjectError("object_key must start with 'raw/'")
        if ".." in key or "\\" in key:
            raise StorageObjectError("object_key contains forbidden path material")
        if not key.endswith(".json"):
            raise StorageObjectError("object_key must end with '.json'")
        expected_filename = f"{hex_id}.json"
        if not key.endswith(f"/{expected_filename}"):
            raise StorageObjectError("object_key filename does not match object_id")
        assert_key_excludes_identity_material(key)
        self._validate_extra_s3_metadata()

    def _validate_extra_s3_metadata(self) -> None:
        if not isinstance(self.extra_s3_metadata, tuple):
            raise StorageObjectError("extra_s3_metadata must be a tuple of (key, value) pairs")
        seen_keys: set[str] = set()
        for item in self.extra_s3_metadata:
            if not (
                isinstance(item, tuple)
                and len(item) == 2
                and isinstance(item[0], str)
                and isinstance(item[1], str)
            ):
                raise StorageObjectError("extra_s3_metadata entries must be (str, str) pairs")
            extra_key, _extra_value = item
            if extra_key in seen_keys:
                raise StorageObjectError(f"duplicate extra_s3_metadata key: {extra_key!r}")
            seen_keys.add(extra_key)
            if extra_key in _BASE_S3_METADATA_KEYS:
                raise StorageObjectError(
                    f"extra_s3_metadata may not override a base metadata key: {extra_key!r}"
                )
            if extra_key not in ALLOWED_S3_METADATA_KEYS or extra_key in FORBIDDEN_S3_METADATA_KEYS:
                raise StorageObjectError(f"extra metadata key not allowlisted: {extra_key!r}")

    def to_s3_metadata(self) -> dict[str, str]:
        """Return the allowlisted S3 object metadata for this object.

        Raises :class:`StorageObjectError` if any candidate key is not
        allowlisted or any value contains forbidden identity material — a
        defense-in-depth guard, since this method always builds the same
        fixed key set from validated fields.
        """

        self._validate_extra_s3_metadata()
        metadata = {
            "codestrata-content-sha256": self.content_sha256,
            "codestrata-envelope-schema": self.envelope_schema_version,
            "codestrata-source-schema": self.source_schema_version,
            "codestrata-stream": self.event_stream,
            "codestrata-object-id": self.opaque_object_id_hex,
        }
        for extra_key, extra_value in self.extra_s3_metadata:
            metadata[extra_key] = extra_value
        for key, value in metadata.items():
            if key not in ALLOWED_S3_METADATA_KEYS or key in FORBIDDEN_S3_METADATA_KEYS:
                raise StorageObjectError(f"metadata key not allowlisted: {key!r}")
            lowered = str(value).lower()
            for token in _FORBIDDEN_METADATA_VALUE_SUBSTRINGS:
                if token in lowered:
                    raise StorageObjectError(f"metadata value contains forbidden material: {token!r}")
        return dict(sorted(metadata.items()))
