"""Project quarantine records into immutable quarantine storage objects (Slice 8.9).

:class:`ImmutableQuarantineStorageObject` is deliberately separate from
:class:`~.objects.ImmutableRawStorageObject`: quarantine objects live under
``quarantine/`` (never ``raw/``) and carry quarantine-only S3 metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.canonical_json import (
    CONTENT_TYPE_APPLICATION_JSON,
    CanonicalJsonError,
    content_digest_hex,
    validate_utf8_json_object_bytes,
)
from codestrata_platform.community_cloud_api.data_lake.identifiers import (
    LAKE_OBJECT_ID_HEX_LENGTH,
    build_opaque_object_filename,
)
from codestrata_platform.community_cloud_api.data_lake.partitions import (
    assert_key_excludes_identity_material,
    build_quarantine_object_key,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.quarantine_diagnostics import (
    QuarantineProjectionDiagnostics,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_identity import (
    QUARANTINE_OBJECT_ID_PREFIX,
    build_quarantine_object_id,
    opaque_quarantine_hex,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_models import QuarantineRecord
from codestrata_platform.community_cloud_api.data_lake.quarantine_policy import (
    QUARANTINE_S3_METADATA_ALLOWLIST,
    CommunityDataLakeQuarantinePolicy,
    default_quarantine_policy,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_serialization import (
    serialize_quarantine_record,
)
from codestrata_platform.community_cloud_api.data_lake.quarantine_validation import (
    validate_quarantine_record,
)

_FORBIDDEN_METADATA_VALUE_SUBSTRINGS: tuple[str, ...] = (
    "event:",
    "evt-",
    "lake-object:",
    "quarantine-object:",
    "request_id",
    "ip_address",
    "client_ip",
    "authorization",
    "cookie",
    "password",
    "secret",
    "bearer",
)


class QuarantineStorageObjectError(ValueError):
    """Raised when an immutable quarantine storage object fails structural validation."""


@dataclass(frozen=True, slots=True)
class ImmutableQuarantineStorageObject:
    """Fully-resolved, storage-ready immutable object for one quarantine write."""

    object_id: str
    object_key: str
    canonical_json_bytes: bytes
    content_sha256: str
    content_length: int
    content_type: str
    quarantine_reason: str
    year: str
    month: str
    day: str
    quarantine_schema_version: str
    quarantine_policy_token: str
    quarantine_reference: str
    extra_s3_metadata: tuple[tuple[str, str], ...] = field(default=())

    @property
    def opaque_object_id_hex(self) -> str:
        return opaque_quarantine_hex(self.object_id)

    def validate(self) -> None:
        if self.content_type != CONTENT_TYPE_APPLICATION_JSON:
            raise QuarantineStorageObjectError("content_type must be application/json")
        if not isinstance(self.canonical_json_bytes, (bytes, bytearray)):
            raise QuarantineStorageObjectError("canonical_json_bytes must be bytes")
        raw_bytes = bytes(self.canonical_json_bytes)
        if self.content_length != len(raw_bytes):
            raise QuarantineStorageObjectError("content_length does not match canonical bytes")

        expected_digest_hex = sha256(raw_bytes).hexdigest()
        try:
            stored_digest_hex = content_digest_hex(self.content_sha256).lower()
        except CanonicalJsonError as exc:
            raise QuarantineStorageObjectError("content_sha256 is not a well-formed digest") from exc
        if stored_digest_hex != expected_digest_hex:
            raise QuarantineStorageObjectError("content_sha256 does not match canonical bytes")

        try:
            validate_utf8_json_object_bytes(raw_bytes)
        except CanonicalJsonError as exc:
            raise QuarantineStorageObjectError(str(exc)) from exc

        if not self.object_id.startswith(QUARANTINE_OBJECT_ID_PREFIX):
            raise QuarantineStorageObjectError("object_id missing quarantine-object prefix")
        hex_id = self.opaque_object_id_hex
        if len(hex_id) != LAKE_OBJECT_ID_HEX_LENGTH:
            raise QuarantineStorageObjectError("object_id hex fragment is invalid")

        key = self.object_key
        if not key or key.startswith("/"):
            raise QuarantineStorageObjectError("object_key must be non-empty without a leading '/'")
        if not key.startswith("quarantine/"):
            raise QuarantineStorageObjectError("object_key must start with 'quarantine/'")
        if key.startswith("raw/"):
            raise QuarantineStorageObjectError("quarantine object_key must not start with 'raw/'")
        if ".." in key or "\\" in key:
            raise QuarantineStorageObjectError("object_key contains forbidden path material")
        if not key.endswith(".json"):
            raise QuarantineStorageObjectError("object_key must end with '.json'")
        expected_filename = f"{hex_id}.json"
        if not key.endswith(f"/{expected_filename}"):
            raise QuarantineStorageObjectError("object_key filename does not match object_id")
        assert_key_excludes_identity_material(key)
        self._validate_extra_s3_metadata()

    def _validate_extra_s3_metadata(self) -> None:
        if not isinstance(self.extra_s3_metadata, tuple):
            raise QuarantineStorageObjectError(
                "extra_s3_metadata must be a tuple of (key, value) pairs"
            )
        seen_keys: set[str] = set()
        for item in self.extra_s3_metadata:
            if not (
                isinstance(item, tuple)
                and len(item) == 2
                and isinstance(item[0], str)
                and isinstance(item[1], str)
            ):
                raise QuarantineStorageObjectError(
                    "extra_s3_metadata entries must be (str, str) pairs"
                )
            extra_key, _extra_value = item
            if extra_key in seen_keys:
                raise QuarantineStorageObjectError(
                    f"duplicate extra_s3_metadata key: {extra_key!r}"
                )
            seen_keys.add(extra_key)
            if extra_key not in QUARANTINE_S3_METADATA_ALLOWLIST:
                raise QuarantineStorageObjectError(
                    f"extra metadata key not allowlisted for quarantine: {extra_key!r}"
                )

    def to_s3_metadata(self) -> dict[str, str]:
        """Return quarantine-only allowlisted S3 object metadata."""

        self._validate_extra_s3_metadata()
        metadata = {
            "codestrata-content-sha256": self.content_sha256,
            "codestrata-quarantine-schema": self.quarantine_schema_version,
            "codestrata-quarantine-reason": self.quarantine_reason,
            "codestrata-object-id": self.opaque_object_id_hex,
        }
        for extra_key, extra_value in self.extra_s3_metadata:
            if extra_key in metadata:
                raise QuarantineStorageObjectError(
                    f"extra_s3_metadata may not override a base metadata key: {extra_key!r}"
                )
            metadata[extra_key] = extra_value
        for key, value in metadata.items():
            if key not in QUARANTINE_S3_METADATA_ALLOWLIST:
                raise QuarantineStorageObjectError(f"metadata key not allowlisted: {key!r}")
            lowered = str(value).lower()
            for token in _FORBIDDEN_METADATA_VALUE_SUBSTRINGS:
                if token in lowered:
                    raise QuarantineStorageObjectError(
                        f"metadata value contains forbidden material: {token!r}"
                    )
        return dict(sorted(metadata.items()))


@dataclass(frozen=True, slots=True)
class QuarantineProjectionResult:
    """A resolved quarantine storage object plus its diagnostics."""

    storage_object: ImmutableQuarantineStorageObject
    diagnostics: QuarantineProjectionDiagnostics

    def to_stable_dict(self) -> dict[str, Any]:
        return {"diagnostics": self.diagnostics.to_stable_dict()}


def build_quarantine_storage_object(
    record: QuarantineRecord,
    *,
    quarantine_policy: CommunityDataLakeQuarantinePolicy | None = None,
    data_lake_policy: CommunityDataLakePolicy | None = None,
) -> ImmutableQuarantineStorageObject:
    """Validate, serialize, and resolve the quarantine storage object for ``record``."""

    q_policy = quarantine_policy or default_quarantine_policy()
    lake_policy = data_lake_policy or CommunityDataLakePolicy.default()
    validate_quarantine_record(record, quarantine_policy=q_policy)
    canonical = serialize_quarantine_record(record, quarantine_policy=q_policy)
    object_id = build_quarantine_object_id(record, policy_token=q_policy.policy_token)
    # Ensure filename extraction accepts quarantine-object: via opaque helper.
    _ = build_opaque_object_filename(object_id)
    object_key = build_quarantine_object_key(
        record.quarantine_reason,
        record.year,
        record.month,
        record.day,
        object_id,
        hive_style=lake_policy.hive_style_partitions,
    )
    storage_object = ImmutableQuarantineStorageObject(
        object_id=object_id,
        object_key=object_key,
        canonical_json_bytes=canonical.data,
        content_sha256=canonical.content_sha256,
        content_length=canonical.content_length,
        content_type=CONTENT_TYPE_APPLICATION_JSON,
        quarantine_reason=record.quarantine_reason,
        year=record.year,
        month=record.month,
        day=record.day,
        quarantine_schema_version=record.quarantine_schema_version,
        quarantine_policy_token=q_policy.policy_token,
        quarantine_reference=record.quarantine_reference,
    )
    storage_object.validate()
    return storage_object


def project_quarantine_storage_object(
    record: QuarantineRecord,
    *,
    quarantine_policy: CommunityDataLakeQuarantinePolicy | None = None,
    data_lake_policy: CommunityDataLakePolicy | None = None,
) -> QuarantineProjectionResult:
    """Project ``record`` into a storage object plus bounded diagnostics."""

    q_policy = quarantine_policy or default_quarantine_policy()
    storage_object = build_quarantine_storage_object(
        record, quarantine_policy=q_policy, data_lake_policy=data_lake_policy
    )
    diagnostics = QuarantineProjectionDiagnostics(
        projection_status="projected",
        quarantine_reason=record.quarantine_reason,
        validation_stage=record.validation_stage,
        quarantine_schema_version=record.quarantine_schema_version,
        quarantine_policy_version=q_policy.policy_version,
        quarantine_reference=record.quarantine_reference,
        safe_event_reference=record.safe_event_reference,
        safe_object_reference=record.safe_object_reference,
        event_stream=record.event_stream,
        envelope_schema_version=record.envelope_schema_version,
        source_schema_version=record.source_schema_version,
        limitations=record.limitations or q_policy.limitations,
    )
    return QuarantineProjectionResult(storage_object=storage_object, diagnostics=diagnostics)
