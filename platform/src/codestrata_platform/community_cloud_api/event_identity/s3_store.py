"""S3-backed event identity lookup/recorder (Slice 17.7).

Stores opaque identity documents under ``identity/`` using a hash of the
event key as the object name. Never logs object keys that embed account
detail; exceptions raise with safe error codes only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from codestrata_platform.community_cloud_api.event_identity.identifiers import (
    build_safe_event_reference,
)
from codestrata_platform.community_cloud_api.event_identity.models import StoredEventIdentity

IDENTITY_PREFIX = "identity/"
_SAFE_ERROR_MISSING = "event_identity_object_missing"
_SAFE_ERROR_UNAVAILABLE = "event_identity_store_unavailable"
_SAFE_ERROR_CONFLICT = "conflicting_event_identity"
_SAFE_ERROR_MALFORMED = "event_identity_object_malformed"


class EventIdentityStoreError(RuntimeError):
    """Fail-closed identity store error — message is a safe code only."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _serialize_identity(
    identity: StoredEventIdentity,
    *,
    safe_event_reference: str,
    recorded_at: str,
) -> bytes:
    payload = {
        "client_type": identity.client_type,
        "event_key": identity.event_key,
        "event_type": identity.event_type,
        "identity_policy_version": identity.identity_policy_version,
        "payload_fingerprint": identity.payload_fingerprint,
        "recorded_at": recorded_at,
        "safe_event_reference": safe_event_reference,
        "updated_at": recorded_at,
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return text.encode("utf-8")


def _parse_identity(body: bytes | str) -> StoredEventIdentity:
    if isinstance(body, bytes):
        text = body.decode("utf-8")
    else:
        text = body
    try:
        data = json.loads(text)
    except (TypeError, ValueError, UnicodeDecodeError) as exc:
        raise EventIdentityStoreError(_SAFE_ERROR_MALFORMED) from exc
    if not isinstance(data, dict):
        raise EventIdentityStoreError(_SAFE_ERROR_MALFORMED)
    required = (
        "event_key",
        "payload_fingerprint",
        "event_type",
        "client_type",
        "identity_policy_version",
    )
    if any(not isinstance(data.get(key), str) or not data.get(key) for key in required):
        raise EventIdentityStoreError(_SAFE_ERROR_MALFORMED)
    return StoredEventIdentity(
        event_key=str(data["event_key"]),
        payload_fingerprint=str(data["payload_fingerprint"]),
        event_type=str(data["event_type"]),
        client_type=str(data["client_type"]),
        identity_policy_version=str(data["identity_policy_version"]),
    )


def _is_missing_error(exc: BaseException) -> bool:
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        code = (response.get("Error") or {}).get("Code")
        if code in {"404", "NoSuchKey", "NotFound", "NoSuchBucket"}:
            return True
    name = type(exc).__name__
    if name in {"NoSuchKey", "NotFound"}:
        return True
    message = str(exc)
    return "NoSuchKey" in message or "404" in message or "Not Found" in message


def _is_precondition_failed(exc: BaseException) -> bool:
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        code = (response.get("Error") or {}).get("Code")
        if code in {"PreconditionFailed", "412", "ConditionalRequestConflict"}:
            return True
    message = str(exc)
    return "PreconditionFailed" in message or "412" in message


@dataclass(slots=True)
class S3EventIdentityStore:
    """S3 EventIdentityLookup + EventIdentityRecorder for production ingestion."""

    bucket_name: str
    client: Any | None = None
    region_name: str | None = None
    prefix: str = IDENTITY_PREFIX

    def _s3(self) -> Any:
        if self.client is not None:
            return self.client
        import boto3

        kwargs: dict[str, str] = {}
        if self.region_name:
            kwargs["region_name"] = self.region_name
        self.client = boto3.client("s3", **kwargs)
        return self.client

    def _key(self, event_key: str) -> str:
        # Keep configured prefix but always use opaque hash suffix.
        digest = hashlib.sha256(event_key.encode("utf-8")).hexdigest()
        prefix = self.prefix if self.prefix.endswith("/") else f"{self.prefix}/"
        return f"{prefix}{digest}.json"

    def get(self, event_key: str) -> StoredEventIdentity | None:
        if not event_key or not str(event_key).strip():
            return None
        key = self._key(event_key)
        try:
            response = self._s3().get_object(Bucket=self.bucket_name, Key=key)
        except Exception as exc:  # noqa: BLE001
            if _is_missing_error(exc):
                return None
            raise EventIdentityStoreError(_SAFE_ERROR_UNAVAILABLE) from None
        body = response.get("Body")
        try:
            if hasattr(body, "read"):
                raw = body.read()
            else:
                raw = body
        except Exception as exc:  # noqa: BLE001
            raise EventIdentityStoreError(_SAFE_ERROR_UNAVAILABLE) from None
        try:
            return _parse_identity(raw)
        except EventIdentityStoreError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EventIdentityStoreError(_SAFE_ERROR_MALFORMED) from None

    def record(self, identity: StoredEventIdentity) -> None:
        existing = self.get(identity.event_key)
        if existing is not None:
            if existing.payload_fingerprint != identity.payload_fingerprint:
                raise EventIdentityStoreError(_SAFE_ERROR_CONFLICT)
            return

        safe_ref = build_safe_event_reference(identity.event_key)
        recorded_at = _utc_now_iso()
        body = _serialize_identity(
            identity,
            safe_event_reference=safe_ref,
            recorded_at=recorded_at,
        )
        key = self._key(identity.event_key)
        try:
            self._s3().put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=body,
                ContentType="application/json",
                IfNoneMatch="*",
            )
        except Exception as exc:  # noqa: BLE001
            if _is_precondition_failed(exc):
                # Concurrent create — re-read and classify.
                raced = self.get(identity.event_key)
                if raced is None:
                    raise EventIdentityStoreError(_SAFE_ERROR_UNAVAILABLE) from None
                if raced.payload_fingerprint != identity.payload_fingerprint:
                    raise EventIdentityStoreError(_SAFE_ERROR_CONFLICT) from None
                return
            raise EventIdentityStoreError(_SAFE_ERROR_UNAVAILABLE) from None


__all__ = [
    "IDENTITY_PREFIX",
    "EventIdentityStoreError",
    "S3EventIdentityStore",
]
