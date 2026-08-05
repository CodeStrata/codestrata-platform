"""Immutable Data Lake ingestion envelope — validated payloads only (Slice 8.1 / 8.3).

Slice 8.1 shipped a flat envelope shape. That shape was a **pre-persistence
foundation**: Slice 8.1/8.2 never wired any endpoint to storage, so nothing
was ever durably written in production. Slice 8.3 evolves the canonical
serialized shape to the nested contract below while remaining at envelope
schema **1.0** — this is a foundation refinement made before the first
durable write, not a runtime schema migration. See
``platform/docs/community-cloud-api/data-lake-event-envelope.md`` for the
full version-impact rationale.

Canonical serialized shape (``to_stable_dict()``)::

    {
      "acceptance": {"accepted_at": "...Z", "partition_date": "YYYY-MM-DD"},
      "client": {"client_type": "..."},
      "envelope_schema_version": "1.0",
      "event_stream": "telemetry",
      "identity": {"event_key": "event:...", "safe_event_reference": "evt-..."},
      "payload": {...allowlisted projected endpoint fields...},
      "source_contract": {"policy_id": "...", "schema_name": "...", "schema_version": "..."}
    }

``payload_fingerprint`` is intentionally never part of the storage envelope —
it is an identity-layer concern (see
:mod:`codestrata_platform.community_cloud_api.event_identity`), not a
storage-envelope field.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from codestrata_platform.community_cloud_api.data_lake.accepted_clock import (
    partition_date_from_accepted_at,
)
from codestrata_platform.community_cloud_api.data_lake.policy import CommunityDataLakePolicy
from codestrata_platform.community_cloud_api.data_lake.validation import (
    DataLakeValidationError,
    validate_event_stream,
    validate_partition_date,
    validate_schema_version,
)

# Raw-identity substrings that must never appear anywhere in a stored
# envelope's canonical JSON (keys and values, case-insensitive). Independent
# of (and in addition to) whatever field-level redaction the source domain
# (telemetry, ai_usage, ...) already performed — defense in depth for the
# archival boundary. Unchanged since Slice 8.1 for backward compatibility;
# see :data:`FORBIDDEN_ENVELOPE_KEY_NAMES` for the Slice 8.3 structural
# additions, which use exact key-name matching rather than blob substring
# matching (to avoid false positives on legitimate enum/hex values).
FORBIDDEN_ENVELOPE_KEYS: frozenset[str] = frozenset(
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

# Slice 8.3 additions: exact-match forbidden field NAMES, scanned structurally
# (as dict keys at any depth of the canonical envelope), never as a blob
# substring. This avoids false positives such as "authentication_failed"
# (a legitimate outcome enum) being rejected by a coarse "auth" substring
# scan the way a value/blob scan of the flatter Slice 8.1 list would.
FORBIDDEN_ENVELOPE_KEY_NAMES: frozenset[str] = frozenset(
    {
        "authorization",
        "cookie",
        "request_id",
        "ip",
        "remote_addr",
        "principal",
        "credential",
        "rate_limit_key",
        "aws_request_id",
        "lambda_request_id",
        "repository_name",
        "project_name",
        "file_path",
        "source_code",
        "prompt",
        "response",
    }
)


class EnvelopeValidationError(ValueError):
    """Raised when a Data Lake envelope fails structural or privacy validation."""


def _stable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _stable(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_stable(item) for item in value]
    return value


def _require_nonblank(value: str, message: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EnvelopeValidationError(message)
    return value


@dataclass(frozen=True, slots=True)
class SourceContract:
    """Identity of the endpoint contract that produced an envelope's payload."""

    schema_name: str
    schema_version: str
    policy_id: str

    def __post_init__(self) -> None:
        _require_nonblank(self.schema_name, "source_contract.schema_name is required")
        _require_nonblank(self.policy_id, "source_contract.policy_id is required")
        if ":" not in self.policy_id:
            raise EnvelopeValidationError(
                "source_contract.policy_id must be a full URN (id:version)"
            )
        try:
            validate_schema_version(self.schema_version)
        except DataLakeValidationError as exc:
            raise EnvelopeValidationError(str(exc)) from exc

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True, slots=True)
class EnvelopeIdentity:
    """Storage identity of one logical event — never present in an object key."""

    event_key: str
    safe_event_reference: str

    def __post_init__(self) -> None:
        if not self.event_key or not self.event_key.startswith("event:"):
            raise EnvelopeValidationError("identity.event_key must be a scoped 'event:' key")
        if not self.safe_event_reference or not self.safe_event_reference.startswith("evt-"):
            raise EnvelopeValidationError(
                "identity.safe_event_reference must be a safe 'evt-' reference"
            )

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "event_key": self.event_key,
            "safe_event_reference": self.safe_event_reference,
        }


@dataclass(frozen=True, slots=True)
class EnvelopeAcceptance:
    """Server-assigned acceptance time and its derived archival partition date."""

    accepted_at: str
    partition_date: str

    def __post_init__(self) -> None:
        try:
            derived = partition_date_from_accepted_at(self.accepted_at)
        except ValueError as exc:
            raise EnvelopeValidationError(str(exc)) from exc
        if not self.partition_date or not self.partition_date.strip():
            raise EnvelopeValidationError("acceptance.partition_date is required")
        if derived != self.partition_date:
            raise EnvelopeValidationError(
                "acceptance.partition_date must match the date component of accepted_at"
            )
        year, month, day = self.partition_date.split("-")
        try:
            validate_partition_date(year, month, day)
        except DataLakeValidationError as exc:
            raise EnvelopeValidationError(str(exc)) from exc

    @property
    def year(self) -> str:
        return self.partition_date[0:4]

    @property
    def month(self) -> str:
        return self.partition_date[5:7]

    @property
    def day(self) -> str:
        return self.partition_date[8:10]

    def to_stable_dict(self) -> dict[str, Any]:
        return {
            "accepted_at": self.accepted_at,
            "partition_date": self.partition_date,
        }


@dataclass(frozen=True, slots=True)
class EnvelopeClient:
    """Bounded client-type classification — never a full client descriptor."""

    client_type: str

    def __post_init__(self) -> None:
        _require_nonblank(self.client_type, "client.client_type is required")

    def to_stable_dict(self) -> dict[str, Any]:
        return {"client_type": self.client_type}


@dataclass(frozen=True, slots=True)
class DataLakeEnvelope:
    """Privacy-scoped, immutable archival unit for one validated source event.

    ``identity.event_key`` is storage identity only — it is carried inside
    the envelope body for idempotent conflict detection, but it (and
    ``identity.safe_event_reference``) must never appear in the S3 object
    key path. See
    :mod:`codestrata_platform.community_cloud_api.data_lake.partitions`.
    """

    envelope_schema_version: str
    event_stream: str
    source_contract: SourceContract
    identity: EnvelopeIdentity
    acceptance: EnvelopeAcceptance
    client: EnvelopeClient
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        _require_nonblank(self.envelope_schema_version, "envelope_schema_version is required")
        try:
            validate_event_stream(self.event_stream)
        except DataLakeValidationError as exc:
            raise EnvelopeValidationError(str(exc)) from exc
        if not isinstance(self.payload, Mapping):
            raise EnvelopeValidationError("payload must be a mapping")
        for field_name, expected_type in (
            ("source_contract", SourceContract),
            ("identity", EnvelopeIdentity),
            ("acceptance", EnvelopeAcceptance),
            ("client", EnvelopeClient),
        ):
            if not isinstance(getattr(self, field_name), expected_type):
                raise EnvelopeValidationError(f"{field_name} must be a {expected_type.__name__}")

    # -- Slice 8.1 / 8.2 compatibility properties -------------------------
    @property
    def source_schema_version(self) -> str:
        return self.source_contract.schema_version

    @property
    def source_policy_version(self) -> str:
        """The source contract's full policy URN (``id:version``).

        Named for Slice 8.1/8.2 compatibility; despite the name this is the
        URN, not a bare version fragment. :func:`~.identifiers.build_lake_object_id`
        deliberately keys off :attr:`source_schema_version`, not this
        property.
        """

        return self.source_contract.policy_id

    @property
    def event_key(self) -> str:
        return self.identity.event_key

    @property
    def safe_event_reference(self) -> str:
        return self.identity.safe_event_reference

    @property
    def client_type(self) -> str:
        return self.client.client_type

    @property
    def accepted_year(self) -> str:
        return self.acceptance.year

    @property
    def accepted_month(self) -> str:
        return self.acceptance.month

    @property
    def accepted_day(self) -> str:
        return self.acceptance.day

    def to_stable_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "acceptance": self.acceptance.to_stable_dict(),
            "client": self.client.to_stable_dict(),
            "envelope_schema_version": self.envelope_schema_version,
            "event_stream": self.event_stream,
            "identity": self.identity.to_stable_dict(),
            "payload": _stable(self.payload),
            "source_contract": self.source_contract.to_stable_dict(),
        }
        return {key: payload[key] for key in sorted(payload)}

    def validate_against_policy(self, policy: CommunityDataLakePolicy) -> None:
        if self.envelope_schema_version != policy.envelope_schema_version:
            raise EnvelopeValidationError(
                f"unsupported envelope schema version: {self.envelope_schema_version!r}"
            )
        if self.event_stream not in policy.allowed_event_streams:
            raise EnvelopeValidationError(
                f"event stream not permitted by policy: {self.event_stream!r}"
            )
        validate_envelope_privacy(self)
        serialized_size = len(
            json.dumps(self.to_stable_dict(), sort_keys=True, ensure_ascii=True).encode("utf-8")
        )
        if serialized_size > policy.max_envelope_bytes:
            raise EnvelopeValidationError(
                f"envelope exceeds max_envelope_bytes policy bound: {serialized_size} "
                f"> {policy.max_envelope_bytes}"
            )


# Slice 8.2 call sites and docs refer to "the envelope" generically; this
# alias lets Slice 8.3 modules use the more explicit event-envelope name
# without breaking any existing ``DataLakeEnvelope`` import.
DataLakeEventEnvelope = DataLakeEnvelope


def _scan_forbidden_key_names(value: Any, *, path: str = "$") -> None:
    """Recursively raise if any dict key (at any depth) is a forbidden field name.

    Exact, case-insensitive key-name matching only — never a substring scan
    — so legitimate enum values or hex fragments that happen to contain a
    forbidden token as a substring are never false-positived.
    """

    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            if key_text.strip().lower() in FORBIDDEN_ENVELOPE_KEY_NAMES:
                raise EnvelopeValidationError(
                    f"forbidden field name present in envelope at {path}.{key_text!r}"
                )
            _scan_forbidden_key_names(nested, path=f"{path}.{key_text}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _scan_forbidden_key_names(item, path=f"{path}[{index}]")


def validate_envelope_privacy(envelope: DataLakeEnvelope) -> None:
    """Fail-closed privacy scan of the stable envelope JSON.

    Two independent passes, both defense-in-depth over whatever redaction
    the source domain already performed:

    1. Structural: every dict key at any depth is checked against
       :data:`FORBIDDEN_ENVELOPE_KEY_NAMES` by exact (case-insensitive)
       name — never by substring — so this pass cannot false-positive on
       legitimate values.
    2. Coarse blob scan: the full canonical JSON text (keys and values) is
       checked for :data:`FORBIDDEN_ENVELOPE_KEYS` substrings, unchanged
       from Slice 8.1. Callers must keep test/production payload values
       free of these substrings (e.g. never encode a hex digest with the
       literal word "secret" in it).
    """

    stable = envelope.to_stable_dict()
    _scan_forbidden_key_names(stable)
    blob = json.dumps(stable, sort_keys=True, ensure_ascii=True).lower()
    for token in FORBIDDEN_ENVELOPE_KEYS:
        if token in blob:
            raise EnvelopeValidationError(f"forbidden material present in envelope: {token!r}")


def build_envelope(
    *,
    event_stream: str,
    schema_name: str,
    schema_version: str,
    policy_id: str,
    event_key: str,
    safe_event_reference: str,
    accepted_at: str,
    client_type: str,
    payload: Mapping[str, Any],
    policy: CommunityDataLakePolicy | None = None,
) -> DataLakeEnvelope:
    """Build and policy-validate a :class:`DataLakeEnvelope` in one step.

    Low-level builder: callers supply already-resolved leaf values. Typed,
    per-stream construction from an endpoint request model lives in
    :mod:`codestrata_platform.community_cloud_api.data_lake.envelope_builders`.
    """

    active = policy or CommunityDataLakePolicy.default()
    try:
        partition_date = partition_date_from_accepted_at(accepted_at)
    except ValueError as exc:
        raise EnvelopeValidationError(str(exc)) from exc
    envelope = DataLakeEnvelope(
        envelope_schema_version=active.envelope_schema_version,
        event_stream=event_stream,
        source_contract=SourceContract(
            schema_name=schema_name, schema_version=schema_version, policy_id=policy_id
        ),
        identity=EnvelopeIdentity(event_key=event_key, safe_event_reference=safe_event_reference),
        acceptance=EnvelopeAcceptance(accepted_at=accepted_at, partition_date=partition_date),
        client=EnvelopeClient(client_type=client_type),
        payload=payload,
    )
    envelope.validate_against_policy(active)
    return envelope
